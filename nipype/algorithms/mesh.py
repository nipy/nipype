# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Miscellaneous algorithms for 2D contours and 3D triangularized meshes handling

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
    >>> os.chdir(datadir)

'''


import numpy as np
import os.path as op
from scipy.spatial.distance import euclidean

from .. import logging

from ..interfaces.base import (BaseInterface, traits, TraitedSpec, File,
                               BaseInterfaceInputSpec)
iflogger = logging.getLogger('interface')


class ComputeMeshWarpInputSpec(BaseInterfaceInputSpec):
    surface1 = File(exists=True, mandatory=True,
                    desc=('Reference surface (vtk format) to which compute '
                          'distance.'))
    surface2 = File(exists=True, mandatory=True,
                    desc=('Test surface (vtk format) from which compute '
                          'distance.'))
    metric = traits.Enum('euclidean', 'sqeuclidean', usedefault=True,
                         desc=('norm used to report distance'))
    weighting = traits.Enum(
        'none', 'area', usedefault=True,
        desc=('"none": no weighting is performed, surface": edge distance is '
              'weighted by the corresponding surface area'))
    out_warp = File('surfwarp.vtk', usedefault=True,
                    desc='vtk file based on surface1 and warpings mapping it '
                    'to surface2')
    out_file = File('distance.npy', usedefault=True,
                    desc='numpy file keeping computed distances and weights')


class ComputeMeshWarpOutputSpec(TraitedSpec):
    distance = traits.Float(desc="computed distance")
    out_warp = File(exists=True, desc=('vtk file with the vertex-wise '
                                       'mapping of surface1 to surface2'))
    out_file = File(exists=True,
                    desc='numpy file keeping computed distances and weights')


class ComputeMeshWarp(BaseInterface):

    """
    Calculates a the vertex-wise warping to get surface2 from surface1.
    It also reports the average distance of vertices, using the norm specified
    as input.

    .. warning:

      A point-to-point correspondence between surfaces is required


    Example
    -------

    >>> import nipype.algorithms.mesh as mesh
    >>> dist = mesh.ComputeMeshWarp()
    >>> dist.inputs.surface1 = 'surf1.vtk'
    >>> dist.inputs.surface2 = 'surf2.vtk'
    >>> res = dist.run() # doctest: +SKIP

    """

    input_spec = ComputeMeshWarpInputSpec
    output_spec = ComputeMeshWarpOutputSpec

    def _triangle_area(self, A, B, C):
        ABxAC = euclidean(A, B) * euclidean(A, C)
        prod = np.dot(np.array(B) - np.array(A), np.array(C) - np.array(A))
        angle = np.arccos(prod / ABxAC)
        area = 0.5 * ABxAC * np.sin(angle)
        return area

    def _run_interface(self, runtime):
        from numpy import linalg as nla
        try:
            from tvtk.api import tvtk, write_data
        except ImportError:
            raise ImportError('Interface ComputeMeshWarp requires tvtk')

        try:
            from enthought.etsconfig.api import ETSConfig
            ETSConfig.toolkit = 'null'
        except ImportError:
            iflogger.warn(('ETS toolkit could not be imported'))
            pass
        except ValueError:
            iflogger.warn(('ETS toolkit is already set'))
            pass

        r1 = tvtk.PolyDataReader(file_name=self.inputs.surface1)
        r2 = tvtk.PolyDataReader(file_name=self.inputs.surface2)
        vtk1 = r1.output
        vtk2 = r2.output
        r1.update()
        r2.update()
        assert(len(vtk1.points) == len(vtk2.points))

        points1 = np.array(vtk1.points)
        points2 = np.array(vtk2.points)

        diff = points2 - points1
        weights = np.ones(len(diff))

        errvector = nla.norm(diff, axis=1)
        if self.inputs.metric == 'sqeuclidean':
            errvector = errvector ** 2

        if (self.inputs.weighting == 'area'):
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
        out_mesh.point_data.warpings = [tuple(d) for d in diff]

        write_data(out_mesh, op.abspath(self.inputs.out_warp))

        self._distance = np.average(errvector, weights=weights)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        outputs['distance'] = self._distance
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
        warnings.warn(("This interface has been deprecated since 1.0,"
                       " please use nipype.algorithms.metrics.Distance"),
                      DeprecationWarning)
