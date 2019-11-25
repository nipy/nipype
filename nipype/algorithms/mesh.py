# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Miscellaneous algorithms for 2D contours and 3D triangularized meshes handling
"""
import os.path as op
import numpy as np
from numpy import linalg as nla

from .. import logging
from ..interfaces.base import (
    BaseInterface,
    traits,
    TraitedSpec,
    File,
    BaseInterfaceInputSpec,
)
from ..interfaces.vtkbase import tvtk
from ..interfaces import vtkbase as VTKInfo

IFLOGGER = logging.getLogger("nipype.interface")


class TVTKBaseInterface(BaseInterface):
    """ A base class for interfaces using VTK """

    _redirect_x = True

    def __init__(self, **inputs):
        if VTKInfo.no_tvtk():
            raise ImportError("This interface requires tvtk to run.")
        super(TVTKBaseInterface, self).__init__(**inputs)


class WarpPointsInputSpec(BaseInterfaceInputSpec):
    points = File(exists=True, mandatory=True, desc="file containing the point set")
    warp = File(
        exists=True, mandatory=True, desc="dense deformation field to be applied"
    )
    interp = traits.Enum(
        "cubic",
        "nearest",
        "linear",
        usedefault=True,
        mandatory=True,
        desc="interpolation",
    )
    out_points = File(
        name_source="points",
        name_template="%s_warped",
        output_name="out_points",
        keep_extension=True,
        desc="the warped point set",
    )


class WarpPointsOutputSpec(TraitedSpec):
    out_points = File(desc="the warped point set")


class WarpPoints(TVTKBaseInterface):
    """
    Applies a displacement field to a point set given in vtk format.
    Any discrete deformation field, given in physical coordinates and
    which volume covers the extent of the vtk point set, is a valid
    ``warp`` file. FSL interfaces are compatible, for instance any
    field computed with :class:`nipype.interfaces.fsl.utils.ConvertWarp`.

    Example::

        from nipype.algorithms.mesh import WarpPoints
        wp = WarpPoints()
        wp.inputs.points = 'surf1.vtk'
        wp.inputs.warp = 'warpfield.nii'
        res = wp.run()

    """

    input_spec = WarpPointsInputSpec
    output_spec = WarpPointsOutputSpec

    def _gen_fname(self, in_file, suffix="generated", ext=None):
        fname, fext = op.splitext(op.basename(in_file))

        if fext == ".gz":
            fname, fext2 = op.splitext(fname)
            fext = fext2 + fext

        if ext is None:
            ext = fext

        if ext[0] == ".":
            ext = ext[1:]
        return op.abspath("%s_%s.%s" % (fname, suffix, ext))

    def _run_interface(self, runtime):
        import nibabel as nb
        from scipy import ndimage

        r = tvtk.PolyDataReader(file_name=self.inputs.points)
        r.update()
        mesh = VTKInfo.vtk_output(r)
        points = np.array(mesh.points)
        warp_dims = nb.funcs.four_to_three(nb.load(self.inputs.warp))

        affine = warp_dims[0].affine
        # voxsize = warp_dims[0].header.get_zooms()
        vox2ras = affine[0:3, 0:3]
        ras2vox = np.linalg.inv(vox2ras)
        origin = affine[0:3, 3]
        voxpoints = np.array([np.dot(ras2vox, (p - origin)) for p in points])

        warps = []
        for axis in warp_dims:
            wdata = axis.dataobj  # four_to_three ensures this is an array
            if np.any(wdata != 0):
                warp = ndimage.map_coordinates(wdata, voxpoints.transpose())
            else:
                warp = np.zeros((points.shape[0],))

            warps.append(warp)

        disps = np.squeeze(np.dstack(warps))
        newpoints = [p + d for p, d in zip(points, disps)]
        mesh.points = newpoints
        w = tvtk.PolyDataWriter()
        VTKInfo.configure_input_data(w, mesh)
        w.file_name = self._gen_fname(self.inputs.points, suffix="warped", ext=".vtk")
        w.write()
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_points"] = self._gen_fname(
            self.inputs.points, suffix="warped", ext=".vtk"
        )
        return outputs


class ComputeMeshWarpInputSpec(BaseInterfaceInputSpec):
    surface1 = File(
        exists=True,
        mandatory=True,
        desc=("Reference surface (vtk format) to which compute " "distance."),
    )
    surface2 = File(
        exists=True,
        mandatory=True,
        desc=("Test surface (vtk format) from which compute " "distance."),
    )
    metric = traits.Enum(
        "euclidean", "sqeuclidean", usedefault=True, desc="norm used to report distance"
    )
    weighting = traits.Enum(
        "none",
        "area",
        usedefault=True,
        desc=(
            '"none": no weighting is performed, surface": edge distance is '
            "weighted by the corresponding surface area"
        ),
    )
    out_warp = File(
        "surfwarp.vtk",
        usedefault=True,
        desc="vtk file based on surface1 and warpings mapping it " "to surface2",
    )
    out_file = File(
        "distance.npy",
        usedefault=True,
        desc="numpy file keeping computed distances and weights",
    )


class ComputeMeshWarpOutputSpec(TraitedSpec):
    distance = traits.Float(desc="computed distance")
    out_warp = File(
        exists=True,
        desc=("vtk file with the vertex-wise " "mapping of surface1 to surface2"),
    )
    out_file = File(
        exists=True, desc="numpy file keeping computed distances and weights"
    )


class ComputeMeshWarp(TVTKBaseInterface):
    """
    Calculates a the vertex-wise warping to get surface2 from surface1.
    It also reports the average distance of vertices, using the norm specified
    as input.

    .. warning:

      A point-to-point correspondence between surfaces is required


    Example::

        import nipype.algorithms.mesh as m
        dist = m.ComputeMeshWarp()
        dist.inputs.surface1 = 'surf1.vtk'
        dist.inputs.surface2 = 'surf2.vtk'
        res = dist.run()

    """

    input_spec = ComputeMeshWarpInputSpec
    output_spec = ComputeMeshWarpOutputSpec

    def _triangle_area(self, A, B, C):
        A = np.array(A)
        B = np.array(B)
        C = np.array(C)
        ABxAC = nla.norm(A - B) * nla.norm(A - C)
        prod = np.dot(B - A, C - A)
        angle = np.arccos(prod / ABxAC)
        area = 0.5 * ABxAC * np.sin(angle)
        return area

    def _run_interface(self, runtime):
        r1 = tvtk.PolyDataReader(file_name=self.inputs.surface1)
        r2 = tvtk.PolyDataReader(file_name=self.inputs.surface2)
        vtk1 = VTKInfo.vtk_output(r1)
        vtk2 = VTKInfo.vtk_output(r2)
        r1.update()
        r2.update()
        assert len(vtk1.points) == len(vtk2.points)

        points1 = np.array(vtk1.points)
        points2 = np.array(vtk2.points)

        diff = points2 - points1
        weights = np.ones(len(diff))

        try:
            errvector = nla.norm(diff, axis=1)
        except TypeError:  # numpy < 1.9
            errvector = np.apply_along_axis(nla.norm, 1, diff)

        if self.inputs.metric == "sqeuclidean":
            errvector **= 2

        if self.inputs.weighting == "area":
            faces = vtk1.polys.to_array().reshape(-1, 4).astype(int)[:, 1:]

            for i, p1 in enumerate(points2):
                # compute surfaces, set in weight
                w = 0.0
                point_faces = faces[(faces[:, :] == i).any(axis=1)]

                for idset in point_faces:
                    fp1 = points1[int(idset[0])]
                    fp2 = points1[int(idset[1])]
                    fp3 = points1[int(idset[2])]
                    w += self._triangle_area(fp1, fp2, fp3)
                weights[i] = w

        result = np.vstack([errvector, weights])
        np.save(op.abspath(self.inputs.out_file), result.transpose())

        out_mesh = tvtk.PolyData()
        out_mesh.points = vtk1.points
        out_mesh.polys = vtk1.polys
        out_mesh.point_data.vectors = diff
        out_mesh.point_data.vectors.name = "warpings"
        writer = tvtk.PolyDataWriter(file_name=op.abspath(self.inputs.out_warp))
        VTKInfo.configure_input_data(writer, out_mesh)
        writer.write()

        self._distance = np.average(errvector, weights=weights)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        outputs["out_warp"] = op.abspath(self.inputs.out_warp)
        outputs["distance"] = self._distance
        return outputs


class MeshWarpMathsInputSpec(BaseInterfaceInputSpec):
    in_surf = File(
        exists=True,
        mandatory=True,
        desc=(
            "Input surface in vtk format, with associated warp "
            "field as point data (ie. from ComputeMeshWarp"
        ),
    )
    float_trait = traits.Either(
        traits.Float(1.0),
        traits.Tuple(traits.Float(1.0), traits.Float(1.0), traits.Float(1.0)),
    )

    operator = traits.Either(
        float_trait,
        File(exists=True),
        default=1.0,
        usedefault=True,
        mandatory=True,
        desc="image, float or tuple of floats to act as operator",
    )

    operation = traits.Enum(
        "sum", "sub", "mul", "div", usedefault=True, desc="operation to be performed"
    )

    out_warp = File(
        "warp_maths.vtk",
        usedefault=True,
        desc="vtk file based on in_surf and warpings mapping it " "to out_file",
    )
    out_file = File("warped_surf.vtk", usedefault=True, desc="vtk with surface warped")


class MeshWarpMathsOutputSpec(TraitedSpec):
    out_warp = File(
        exists=True,
        desc=("vtk file with the vertex-wise " "mapping of surface1 to surface2"),
    )
    out_file = File(exists=True, desc="vtk with surface warped")


class MeshWarpMaths(TVTKBaseInterface):
    """
    Performs the most basic mathematical operations on the warping field
    defined at each vertex of the input surface. A surface with scalar
    or vector data can be used as operator for non-uniform operations.

    .. warning:

      A point-to-point correspondence between surfaces is required


    Example::

        import nipype.algorithms.mesh as m
        mmath = m.MeshWarpMaths()
        mmath.inputs.in_surf = 'surf1.vtk'
        mmath.inputs.operator = 'surf2.vtk'
        mmath.inputs.operation = 'mul'
        res = mmath.run()

    """

    input_spec = MeshWarpMathsInputSpec
    output_spec = MeshWarpMathsOutputSpec

    def _run_interface(self, runtime):
        r1 = tvtk.PolyDataReader(file_name=self.inputs.in_surf)
        vtk1 = VTKInfo.vtk_output(r1)
        r1.update()
        points1 = np.array(vtk1.points)

        if vtk1.point_data.vectors is None:
            raise RuntimeError("No warping field was found in in_surf")

        operator = self.inputs.operator
        opfield = np.ones_like(points1)

        if isinstance(operator, (str, bytes)):
            r2 = tvtk.PolyDataReader(file_name=self.inputs.surface2)
            vtk2 = VTKInfo.vtk_output(r2)
            r2.update()
            assert len(points1) == len(vtk2.points)

            opfield = vtk2.point_data.vectors

            if opfield is None:
                opfield = vtk2.point_data.scalars

            if opfield is None:
                raise RuntimeError("No operator values found in operator file")

            opfield = np.array(opfield)

            if opfield.shape[1] < points1.shape[1]:
                opfield = np.array([opfield.tolist()] * points1.shape[1]).T
        else:
            operator = np.atleast_1d(operator)
            opfield *= operator

        warping = np.array(vtk1.point_data.vectors)

        if self.inputs.operation == "sum":
            warping += opfield
        elif self.inputs.operation == "sub":
            warping -= opfield
        elif self.inputs.operation == "mul":
            warping *= opfield
        elif self.inputs.operation == "div":
            warping /= opfield

        vtk1.point_data.vectors = warping
        writer = tvtk.PolyDataWriter(file_name=op.abspath(self.inputs.out_warp))
        VTKInfo.configure_input_data(writer, vtk1)
        writer.write()

        vtk1.point_data.vectors = None
        vtk1.points = points1 + warping
        writer = tvtk.PolyDataWriter(file_name=op.abspath(self.inputs.out_file))
        VTKInfo.configure_input_data(writer, vtk1)
        writer.write()
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        outputs["out_warp"] = op.abspath(self.inputs.out_warp)
        return outputs


class P2PDistance(ComputeMeshWarp):
    """
    Calculates a point-to-point (p2p) distance between two corresponding
    VTK-readable meshes or contours.

    A point-to-point correspondence between nodes is required

    .. deprecated:: 1.0-dev
       Use :py:class:`ComputeMeshWarp` instead.
    """

    def __init__(self, **inputs):
        super(P2PDistance, self).__init__(**inputs)
        IFLOGGER.warning(
            "This interface has been deprecated since 1.0, please "
            "use ComputeMeshWarp"
        )
