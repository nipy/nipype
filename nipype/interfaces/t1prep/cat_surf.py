# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Nipype interfaces for the full ``cat_surf`` / ``t1prep.cat_surf`` Python API.

Every public function in ``cat_surf`` that T1Prep exposes is wrapped as a
separate :class:`~nipype.interfaces.base.BaseInterface` sub-class so that
each operation can be used as an independent node inside a Nipype workflow.

Interfaces
----------

**I/O**

* :class:`CatSurfReadSurface`  – ``cat_surf.read_surface``
* :class:`CatSurfWriteSurface` – ``cat_surf.write_surface``
* :class:`CatSurfReadValues`   – ``cat_surf.read_values``
* :class:`CatSurfWriteValues`  – ``cat_surf.write_values``

**Surface geometry**

* :class:`CatSurfGetArea`                  – ``cat_surf.get_area``
* :class:`CatSurfGetAreaNormalized`        – ``cat_surf.get_area_normalized``
* :class:`CatSurfEulerCharacteristic`      – ``cat_surf.euler_characteristic``
* :class:`CatSurfSphereRadius`             – ``cat_surf.sphere_radius``
* :class:`CatSurfHausdorffDistance`        – ``cat_surf.hausdorff_distance``
* :class:`CatSurfPointDistance`            – ``cat_surf.point_distance``
* :class:`CatSurfPointDistanceMean`        – ``cat_surf.point_distance_mean``
* :class:`CatSurfCountIntersections`       – ``cat_surf.count_intersections``
* :class:`CatSurfRemoveIntersections`      – ``cat_surf.remove_intersections``
* :class:`CatSurfReduceMesh`               – ``cat_surf.reduce_mesh``

**Surface processing / deformation**

* :class:`CatSurfSurfDeform`           – ``cat_surf.surf_deform``
* :class:`CatSurfSurfToPialWhite`      – ``cat_surf.surf_to_pial_white``
* :class:`CatSurfSurfToSphere`         – ``cat_surf.surf_to_sphere``
* :class:`CatSurfSurfWarp`             – ``cat_surf.surf_warp``
* :class:`CatSurfSurfAverage`          – ``cat_surf.surf_average``
* :class:`CatSurfResampleToSphere`     – ``cat_surf.resample_to_sphere``
* :class:`CatSurfResampleAnnot`        – ``cat_surf.resample_annot``

**Per-vertex data smoothing / curvature**

* :class:`CatSurfSmoothHeatkernel`     – ``cat_surf.smooth_heatkernel``
* :class:`CatSurfSmoothMesh`           – ``cat_surf.smooth_mesh``
* :class:`CatSurfSmoothedCurvatures`   – ``cat_surf.smoothed_curvatures``
* :class:`CatSurfSurfCurvature`        – ``cat_surf.surf_curvature``
* :class:`CatSurfSulcusDepth`          – ``cat_surf.sulcus_depth``
* :class:`CatSurfCorrectThicknessFolding` – ``cat_surf.correct_thickness_folding``

**Volume operations**

* :class:`CatSurfVolSanlm`                 – ``cat_surf.vol_sanlm``
* :class:`CatSurfVolMarchingCubes`         – ``cat_surf.vol_marching_cubes``
* :class:`CatSurfVol2Surf`                 – ``cat_surf.vol2surf``
* :class:`CatSurfVolThicknessPbt`          – ``cat_surf.vol_thickness_pbt``
* :class:`CatSurfVolAmap`                  – ``cat_surf.vol_amap``
* :class:`CatSurfVolBloodVesselCorrection` – ``cat_surf.vol_blood_vessel_correction``

**Registration**

* :class:`CatSurfBbreg`                 – ``cat_surf.bbreg``
* :class:`CatSurfBbregDetectContrast`   – ``cat_surf.bbreg_detect_contrast``
* :class:`CatSurfVolumeRegisterNmi`     – ``cat_surf.volume_register_nmi``
* :class:`CatSurfVolumeRegisterRobust`  – ``cat_surf.volume_register_robust``

References
----------
https://github.com/ChristianGaser/CAT-Surface
https://github.com/ChristianGaser/T1Prep
"""

import os

import numpy as np

from ..base import (
    BaseInterface,
    BaseInterfaceInputSpec,
    TraitedSpec,
    File,
    Directory,
    traits,
    isdefined,
)
from .base import import_cat_surf as _import_cat_surf

__docformat__ = "restructuredtext"


# ===========================================================================
# Helper: numpy array trait (stored as object)
# ===========================================================================

_arr = traits.Any  # placeholder for numpy array inputs/outputs


# ===========================================================================
# I/O interfaces
# ===========================================================================


class CatSurfReadSurfaceInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc="Surface file to read (.gii, FreeSurfer, or .obj).")


class CatSurfReadSurfaceOutputSpec(TraitedSpec):
    vertices = traits.Any(desc="Vertex array (N, 3) float32.")
    faces = traits.Any(desc="Face/triangle array (M, 3) int32.")


class CatSurfReadSurface(BaseInterface):
    """Read a surface mesh from disk.

    Wraps ``cat_surf.read_surface(filename) → (vertices, faces)``.

    Examples
    --------
    >>> node = CatSurfReadSurface()
    >>> node.inputs.in_file = 'lh.central.sub-01.gii'  # doctest: +SKIP
    >>> res = node.run()  # doctest: +SKIP
    >>> v, fcs = res.outputs.vertices, res.outputs.faces  # doctest: +SKIP
    """

    input_spec = CatSurfReadSurfaceInputSpec
    output_spec = CatSurfReadSurfaceOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        v, fcs = cs.read_surface(self.inputs.in_file)
        self._v = v
        self._fcs = fcs
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["vertices"] = self._v
        outputs["faces"] = self._fcs
        return outputs


# ---------------------------------------------------------------------------


class CatSurfWriteSurfaceInputSpec(BaseInterfaceInputSpec):
    out_file = File(mandatory=True, desc="Output surface file path.")
    vertices = traits.Any(mandatory=True, desc="Vertex array (N, 3) float32.")
    faces = traits.Any(mandatory=True, desc="Face/triangle array (M, 3) int32.")


class CatSurfWriteSurfaceOutputSpec(TraitedSpec):
    out_file = File(desc="Written surface file path.")


class CatSurfWriteSurface(BaseInterface):
    """Write a surface mesh to disk.

    Wraps ``cat_surf.write_surface(filename, vertices, faces)``.

    Examples
    --------
    >>> node = CatSurfWriteSurface()
    >>> node.inputs.out_file = 'lh.central.sub-01.gii'
    >>> node.inputs.vertices = v   # doctest: +SKIP
    >>> node.inputs.faces = fcs    # doctest: +SKIP
    """

    input_spec = CatSurfWriteSurfaceInputSpec
    output_spec = CatSurfWriteSurfaceOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        cs.write_surface(self.inputs.out_file, self.inputs.vertices, self.inputs.faces)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


# ---------------------------------------------------------------------------


class CatSurfReadValuesInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc="Per-vertex scalar file to read.")


class CatSurfReadValuesOutputSpec(TraitedSpec):
    values = traits.Any(desc="Per-vertex scalar array (N,) float32.")


class CatSurfReadValues(BaseInterface):
    """Read per-vertex scalar data from disk.

    Wraps ``cat_surf.read_values(filename) → array``.

    Examples
    --------
    >>> node = CatSurfReadValues()
    >>> node.inputs.in_file = 'lh.thickness.sub-01'  # doctest: +SKIP
    >>> res = node.run()  # doctest: +SKIP
    """

    input_spec = CatSurfReadValuesInputSpec
    output_spec = CatSurfReadValuesOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._values = cs.read_values(self.inputs.in_file)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["values"] = self._values
        return outputs


# ---------------------------------------------------------------------------


class CatSurfWriteValuesInputSpec(BaseInterfaceInputSpec):
    out_file = File(mandatory=True, desc="Output per-vertex scalar file path.")
    values = traits.Any(mandatory=True, desc="Per-vertex scalar array (N,) float32.")


class CatSurfWriteValuesOutputSpec(TraitedSpec):
    out_file = File(desc="Written per-vertex scalar file path.")


class CatSurfWriteValues(BaseInterface):
    """Write per-vertex scalar data to disk.

    Wraps ``cat_surf.write_values(filename, values)``.

    Examples
    --------
    >>> node = CatSurfWriteValues()
    >>> node.inputs.out_file = 'lh.thickness.sub-01'
    >>> node.inputs.values = arr   # doctest: +SKIP
    """

    input_spec = CatSurfWriteValuesInputSpec
    output_spec = CatSurfWriteValuesOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        cs.write_values(self.inputs.out_file, self.inputs.values)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


# ===========================================================================
# Surface geometry
# ===========================================================================


class CatSurfGetAreaInputSpec(BaseInterfaceInputSpec):
    vertices = traits.Any(mandatory=True, desc="Vertex array (N, 3) float32.")
    faces = traits.Any(mandatory=True, desc="Face/triangle array (M, 3) int32.")


class CatSurfGetAreaOutputSpec(TraitedSpec):
    area = traits.Any(desc="Per-vertex area array (N,) float32.")
    total_area = traits.Float(desc="Total surface area (mm²).")


class CatSurfGetArea(BaseInterface):
    """Compute per-vertex surface area.

    Wraps ``cat_surf.get_area(vertices, faces) → (area, total_area)``.

    Each vertex receives the sum of one-third of the areas of its adjacent
    triangles (the standard Voronoi tessellation-based area).

    Examples
    --------
    >>> node = CatSurfGetArea()
    >>> node.inputs.vertices = v    # doctest: +SKIP
    >>> node.inputs.faces = fcs     # doctest: +SKIP
    >>> res = node.run()            # doctest: +SKIP
    >>> per_vertex_area = res.outputs.area  # doctest: +SKIP
    """

    input_spec = CatSurfGetAreaInputSpec
    output_spec = CatSurfGetAreaOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._area, self._total = cs.get_area(self.inputs.vertices, self.inputs.faces)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["area"] = self._area
        outputs["total_area"] = float(self._total)
        return outputs


# ---------------------------------------------------------------------------


class CatSurfGetAreaNormalizedInputSpec(BaseInterfaceInputSpec):
    vertices = traits.Any(mandatory=True, desc="Vertex array (N, 3) float32.")
    faces = traits.Any(mandatory=True, desc="Face/triangle array (M, 3) int32.")
    reference_area = traits.Float(desc="Reference total area for normalisation (mm²). Defaults to total surface area.")


class CatSurfGetAreaNormalizedOutputSpec(TraitedSpec):
    area_normalized = traits.Any(desc="Normalised per-vertex area array (N,) float32.")


class CatSurfGetAreaNormalized(BaseInterface):
    """Compute normalised per-vertex surface area.

    Wraps ``cat_surf.get_area_normalized(vertices, faces[, reference_area])``
    → normalised area array.

    Examples
    --------
    >>> node = CatSurfGetAreaNormalized()
    >>> node.inputs.vertices = v   # doctest: +SKIP
    >>> node.inputs.faces = fcs    # doctest: +SKIP
    """

    input_spec = CatSurfGetAreaNormalizedInputSpec
    output_spec = CatSurfGetAreaNormalizedOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        kwargs = {}
        if isdefined(self.inputs.reference_area):
            kwargs["reference_area"] = self.inputs.reference_area
        self._area_norm = cs.get_area_normalized(
            self.inputs.vertices, self.inputs.faces, **kwargs
        )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["area_normalized"] = self._area_norm
        return outputs


# ---------------------------------------------------------------------------


class CatSurfEulerCharacteristicInputSpec(BaseInterfaceInputSpec):
    vertices = traits.Any(mandatory=True, desc="Vertex array (N, 3) float32.")
    faces = traits.Any(mandatory=True, desc="Face/triangle array (M, 3) int32.")


class CatSurfEulerCharacteristicOutputSpec(TraitedSpec):
    euler_number = traits.Int(desc="Euler characteristic χ = V − E + F. For a genus-0 surface: χ = 2.")
    defects = traits.Int(desc="Number of topological defects (holes+handles).")


class CatSurfEulerCharacteristic(BaseInterface):
    """Compute the Euler characteristic of a surface mesh.

    Wraps ``cat_surf.euler_characteristic(vertices, faces) → (euler, defects)``.

    The Euler number of a topologically sphere-like (genus-0) surface is 2.
    Each topological defect reduces it by 2.

    Examples
    --------
    >>> node = CatSurfEulerCharacteristic()
    >>> node.inputs.vertices = v   # doctest: +SKIP
    >>> node.inputs.faces = fcs    # doctest: +SKIP
    >>> res = node.run()           # doctest: +SKIP
    >>> res.outputs.euler_number   # doctest: +SKIP
    2
    """

    input_spec = CatSurfEulerCharacteristicInputSpec
    output_spec = CatSurfEulerCharacteristicOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        result = cs.euler_characteristic(self.inputs.vertices, self.inputs.faces)
        if isinstance(result, (tuple, list)):
            self._euler, self._defects = result[0], result[1]
        else:
            self._euler = int(result)
            self._defects = max(0, (2 - self._euler) // 2)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["euler_number"] = int(self._euler)
        outputs["defects"] = int(self._defects)
        return outputs


# ---------------------------------------------------------------------------


class CatSurfSphereRadiusInputSpec(BaseInterfaceInputSpec):
    vertices = traits.Any(mandatory=True, desc="Vertex array (N, 3) float32 of a sphere mesh.")
    faces = traits.Any(mandatory=True, desc="Face/triangle array (M, 3) int32.")


class CatSurfSphereRadiusOutputSpec(TraitedSpec):
    radius = traits.Float(desc="Estimated sphere radius (mm).")


class CatSurfSphereRadius(BaseInterface):
    """Estimate the radius of an approximately spherical surface mesh.

    Wraps ``cat_surf.sphere_radius(vertices, faces) → radius``.

    Examples
    --------
    >>> node = CatSurfSphereRadius()
    >>> node.inputs.vertices = sv   # doctest: +SKIP
    >>> node.inputs.faces = sf      # doctest: +SKIP
    """

    input_spec = CatSurfSphereRadiusInputSpec
    output_spec = CatSurfSphereRadiusOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._radius = float(cs.sphere_radius(self.inputs.vertices, self.inputs.faces))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["radius"] = self._radius
        return outputs


# ---------------------------------------------------------------------------


class CatSurfHausdorffDistanceInputSpec(BaseInterfaceInputSpec):
    vertices1 = traits.Any(mandatory=True, desc="Vertices of the first surface (N, 3).")
    faces1 = traits.Any(mandatory=True, desc="Faces of the first surface (M, 3).")
    vertices2 = traits.Any(mandatory=True, desc="Vertices of the second surface (N, 3).")
    faces2 = traits.Any(mandatory=True, desc="Faces of the second surface (K, 3).")


class CatSurfHausdorffDistanceOutputSpec(TraitedSpec):
    distance = traits.Float(desc="Hausdorff distance between the two surfaces (mm).")


class CatSurfHausdorffDistance(BaseInterface):
    """Compute the Hausdorff distance between two surface meshes.

    Wraps ``cat_surf.hausdorff_distance(v1, f1, v2, f2) → distance``.

    The Hausdorff distance is the maximum of the one-sided directed distances
    in both directions.

    Examples
    --------
    >>> node = CatSurfHausdorffDistance()
    >>> node.inputs.vertices1 = pv   # doctest: +SKIP
    >>> node.inputs.faces1 = pf      # doctest: +SKIP
    >>> node.inputs.vertices2 = wv   # doctest: +SKIP
    >>> node.inputs.faces2 = wf      # doctest: +SKIP
    """

    input_spec = CatSurfHausdorffDistanceInputSpec
    output_spec = CatSurfHausdorffDistanceOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._dist = float(
            cs.hausdorff_distance(
                self.inputs.vertices1, self.inputs.faces1,
                self.inputs.vertices2, self.inputs.faces2,
            )
        )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["distance"] = self._dist
        return outputs


# ---------------------------------------------------------------------------


class CatSurfPointDistanceInputSpec(BaseInterfaceInputSpec):
    vertices1 = traits.Any(mandatory=True, desc="Source surface vertices (N, 3).")
    faces1 = traits.Any(mandatory=True, desc="Source surface faces (M, 3).")
    vertices2 = traits.Any(mandatory=True, desc="Target surface vertices (N, 3).")
    faces2 = traits.Any(mandatory=True, desc="Target surface faces (K, 3).")


class CatSurfPointDistanceOutputSpec(TraitedSpec):
    distances = traits.Any(desc="Per-vertex distance array (N,) float32.")


class CatSurfPointDistance(BaseInterface):
    """Compute per-vertex nearest-point distances from one surface to another.

    Wraps ``cat_surf.point_distance(v1, f1, v2, f2) → distances``.

    Examples
    --------
    >>> node = CatSurfPointDistance()
    >>> node.inputs.vertices1 = pv   # doctest: +SKIP
    >>> node.inputs.faces1 = pf      # doctest: +SKIP
    >>> node.inputs.vertices2 = wv   # doctest: +SKIP
    >>> node.inputs.faces2 = wf      # doctest: +SKIP
    """

    input_spec = CatSurfPointDistanceInputSpec
    output_spec = CatSurfPointDistanceOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._dists = cs.point_distance(
            self.inputs.vertices1, self.inputs.faces1,
            self.inputs.vertices2, self.inputs.faces2,
        )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["distances"] = self._dists
        return outputs


# ---------------------------------------------------------------------------


class CatSurfPointDistanceMeanInputSpec(BaseInterfaceInputSpec):
    vertices1 = traits.Any(mandatory=True, desc="Source surface vertices (N, 3).")
    faces1 = traits.Any(mandatory=True, desc="Source surface faces (M, 3).")
    vertices2 = traits.Any(mandatory=True, desc="Target surface vertices (N, 3).")
    faces2 = traits.Any(mandatory=True, desc="Target surface faces (K, 3).")
    symmetric = traits.Bool(
        False,
        usedefault=True,
        desc="If True, return the average of both directed distances.",
    )
    max_dist = traits.Float(
        6.0,
        usedefault=True,
        desc="Clamp distances to this maximum value (mm).",
    )


class CatSurfPointDistanceMeanOutputSpec(TraitedSpec):
    distances = traits.Any(desc="Per-vertex distance array (N,) float32.")
    mean_distance = traits.Float(desc="Mean across all per-vertex distances.")


class CatSurfPointDistanceMean(BaseInterface):
    """Compute mean per-vertex distances between two surface meshes.

    Wraps
    ``cat_surf.point_distance_mean(v1, f1, v2, f2, symmetric, max_dist)
    → (distances, mean_distance)``.

    This is used by T1Prep's surface estimation to compute pial-to-white
    (Tfs) cortical thickness when ``thickness_method=2``.

    Examples
    --------
    >>> node = CatSurfPointDistanceMean()
    >>> node.inputs.vertices1 = pv    # doctest: +SKIP
    >>> node.inputs.faces1 = pf       # doctest: +SKIP
    >>> node.inputs.vertices2 = wv    # doctest: +SKIP
    >>> node.inputs.faces2 = wf       # doctest: +SKIP
    >>> node.inputs.symmetric = False
    >>> node.inputs.max_dist = 6.0
    """

    input_spec = CatSurfPointDistanceMeanInputSpec
    output_spec = CatSurfPointDistanceMeanOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        d, mean = cs.point_distance_mean(
            self.inputs.vertices1, self.inputs.faces1,
            self.inputs.vertices2, self.inputs.faces2,
            symmetric=self.inputs.symmetric,
            max_dist=self.inputs.max_dist,
        )
        self._d = d
        self._mean = float(mean)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["distances"] = self._d
        outputs["mean_distance"] = self._mean
        return outputs


# ---------------------------------------------------------------------------


class CatSurfCountIntersectionsInputSpec(BaseInterfaceInputSpec):
    vertices = traits.Any(mandatory=True, desc="Vertex array (N, 3) float32.")
    faces = traits.Any(mandatory=True, desc="Face/triangle array (M, 3) int32.")


class CatSurfCountIntersectionsOutputSpec(TraitedSpec):
    n_intersections = traits.Int(desc="Number of self-intersecting triangle pairs.")


class CatSurfCountIntersections(BaseInterface):
    """Count the number of self-intersecting triangle pairs in a mesh.

    Wraps ``cat_surf.count_intersections(vertices, faces) → n_intersections``.

    Examples
    --------
    >>> node = CatSurfCountIntersections()
    >>> node.inputs.vertices = v   # doctest: +SKIP
    >>> node.inputs.faces = fcs    # doctest: +SKIP
    """

    input_spec = CatSurfCountIntersectionsInputSpec
    output_spec = CatSurfCountIntersectionsOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._n = int(cs.count_intersections(self.inputs.vertices, self.inputs.faces))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["n_intersections"] = self._n
        return outputs


# ---------------------------------------------------------------------------


class CatSurfRemoveIntersectionsInputSpec(BaseInterfaceInputSpec):
    vertices = traits.Any(mandatory=True, desc="Vertex array (N, 3) float32.")
    faces = traits.Any(mandatory=True, desc="Face/triangle array (M, 3) int32.")
    verbose = traits.Bool(False, usedefault=True, desc="Print diagnostic output.")


class CatSurfRemoveIntersectionsOutputSpec(TraitedSpec):
    vertices = traits.Any(desc="Updated vertex array after intersection removal.")
    faces = traits.Any(desc="Updated face array after intersection removal.")


class CatSurfRemoveIntersections(BaseInterface):
    """Remove self-intersecting triangles from a surface mesh.

    Wraps
    ``cat_surf.remove_intersections(vertices, faces[, verbose])
    → (vertices, faces)``.

    Examples
    --------
    >>> node = CatSurfRemoveIntersections()
    >>> node.inputs.vertices = v   # doctest: +SKIP
    >>> node.inputs.faces = fcs    # doctest: +SKIP
    """

    input_spec = CatSurfRemoveIntersectionsInputSpec
    output_spec = CatSurfRemoveIntersectionsOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._v, self._fcs = cs.remove_intersections(
            self.inputs.vertices, self.inputs.faces,
            verbose=self.inputs.verbose,
        )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["vertices"] = self._v
        outputs["faces"] = self._fcs
        return outputs


# ---------------------------------------------------------------------------


class CatSurfReduceMeshInputSpec(BaseInterfaceInputSpec):
    vertices = traits.Any(mandatory=True, desc="Vertex array (N, 3) float32.")
    faces = traits.Any(mandatory=True, desc="Face/triangle array (M, 3) int32.")
    target_faces = traits.Int(
        mandatory=True,
        desc="Target number of triangles after reduction.",
    )
    aggressiveness = traits.Float(
        7.0,
        usedefault=True,
        desc="Decimation aggressiveness (higher = more aggressive; default 7.0).",
    )
    preserve_sharp = traits.Bool(
        True,
        usedefault=True,
        desc="Preserve sharp edges during decimation.",
    )
    verbose = traits.Bool(False, usedefault=True, desc="Print diagnostic output.")


class CatSurfReduceMeshOutputSpec(TraitedSpec):
    vertices = traits.Any(desc="Decimated vertex array.")
    faces = traits.Any(desc="Decimated face array.")


class CatSurfReduceMesh(BaseInterface):
    """Decimate a surface mesh to a target face count.

    Wraps
    ``cat_surf.reduce_mesh(vertices, faces, target_faces, aggressiveness,
    preserve_sharp, verbose) → (vertices, faces)``.

    T1Prep uses a ratio of 0.25 with ``aggressiveness=7.0`` by default
    to downsample the initial marching-cubes surface before deformation.

    Examples
    --------
    >>> node = CatSurfReduceMesh()
    >>> node.inputs.vertices = v          # doctest: +SKIP
    >>> node.inputs.faces = fcs           # doctest: +SKIP
    >>> node.inputs.target_faces = 40000
    >>> node.inputs.aggressiveness = 7.0
    """

    input_spec = CatSurfReduceMeshInputSpec
    output_spec = CatSurfReduceMeshOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._v, self._fcs = cs.reduce_mesh(
            self.inputs.vertices, self.inputs.faces,
            target_faces=self.inputs.target_faces,
            aggressiveness=self.inputs.aggressiveness,
            preserve_sharp=self.inputs.preserve_sharp,
            verbose=self.inputs.verbose,
        )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["vertices"] = self._v
        outputs["faces"] = self._fcs
        return outputs


# ===========================================================================
# Surface processing / deformation
# ===========================================================================


class CatSurfSurfDeformInputSpec(BaseInterfaceInputSpec):
    vertices = traits.Any(mandatory=True, desc="Input surface vertices (N, 3) float32.")
    faces = traits.Any(mandatory=True, desc="Input surface faces (M, 3) int32.")
    volume_file = File(
        mandatory=True,
        desc="NIfTI volume used to drive the deformation (e.g. PPM volume).",
    )
    w1 = traits.Float(0.1, usedefault=True, desc="Weight for the image force term.")
    w2 = traits.Float(0.1, usedefault=True, desc="Weight for the balloon force term.")
    w3 = traits.Float(1.0, usedefault=True, desc="Weight for the regularisation term.")
    sigma = traits.Float(0.2, usedefault=True, desc="Gaussian smoothing sigma for the gradient force (mm).")
    isovalue = traits.Float(0.5, usedefault=True, desc="Iso-surface value in the driving volume.")
    iterations = traits.Int(75, usedefault=True, desc="Number of deformation iterations.")
    remove_intersect = traits.Bool(
        True, usedefault=True,
        desc="Remove self-intersections after each deformation step.",
    )
    verbose = traits.Bool(False, usedefault=True, desc="Print diagnostic output.")


class CatSurfSurfDeformOutputSpec(TraitedSpec):
    vertices = traits.Any(desc="Deformed surface vertices.")
    faces = traits.Any(desc="Updated face array.")


class CatSurfSurfDeform(BaseInterface):
    """Deform a surface mesh towards an iso-surface in a driving volume.

    Wraps
    ``cat_surf.surf_deform(vertices, faces, volume_file, w1, w2, w3,
    sigma, isovalue, iterations, remove_intersect, verbose)
    → (vertices, faces)``.

    This is the core surface-deformation step in T1Prep's surface estimation
    pipeline (step 3: ``CAT_SurfDeform``).

    Examples
    --------
    >>> node = CatSurfSurfDeform()
    >>> node.inputs.vertices = v              # doctest: +SKIP
    >>> node.inputs.faces = fcs               # doctest: +SKIP
    >>> node.inputs.volume_file = 'ppm.nii.gz'
    >>> node.inputs.iterations = 75
    """

    input_spec = CatSurfSurfDeformInputSpec
    output_spec = CatSurfSurfDeformOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._v, self._fcs = cs.surf_deform(
            self.inputs.vertices, self.inputs.faces,
            self.inputs.volume_file,
            w1=self.inputs.w1,
            w2=self.inputs.w2,
            w3=self.inputs.w3,
            sigma=self.inputs.sigma,
            isovalue=self.inputs.isovalue,
            iterations=self.inputs.iterations,
            remove_intersect=self.inputs.remove_intersect,
            verbose=self.inputs.verbose,
        )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["vertices"] = self._v
        outputs["faces"] = self._fcs
        return outputs


# ---------------------------------------------------------------------------


class CatSurfSurfToPialWhiteInputSpec(BaseInterfaceInputSpec):
    vertices = traits.Any(mandatory=True, desc="Central surface vertices (N, 3) float32.")
    faces = traits.Any(mandatory=True, desc="Central surface faces (M, 3) int32.")
    thickness = traits.Any(mandatory=True, desc="Per-vertex cortical thickness (N,) float32.")
    volume_file = File(mandatory=True, desc="Hemi-partition NIfTI volume used to drive pial/white estimation.")
    w1 = traits.Float(0.05, usedefault=True, desc="Image-force weight.")
    w2 = traits.Float(0.05, usedefault=True, desc="Balloon-force weight.")
    w3 = traits.Float(0.05, usedefault=True, desc="Regularisation weight.")
    sigma = traits.Float(0.2, usedefault=True, desc="Gaussian smoothing sigma (mm).")
    iterations = traits.Int(100, usedefault=True, desc="Number of deformation iterations.")
    gradient_iterations = traits.Int(0, usedefault=True, desc="Number of gradient-descent iterations.")
    method = traits.Int(2, usedefault=True, desc="Pial/white estimation method (default 2).")
    verbose = traits.Bool(False, usedefault=True, desc="Print diagnostic output.")


class CatSurfSurfToPialWhiteOutputSpec(TraitedSpec):
    pial_vertices = traits.Any(desc="Pial surface vertex array (N, 3).")
    pial_faces = traits.Any(desc="Pial surface face array (M, 3).")
    white_vertices = traits.Any(desc="White matter surface vertex array (N, 3).")
    white_faces = traits.Any(desc="White matter surface face array (M, 3).")


class CatSurfSurfToPialWhite(BaseInterface):
    """Estimate pial and white matter surfaces from a central surface.

    Wraps
    ``cat_surf.surf_to_pial_white(vertices, faces, thickness, volume_file,
    w1, w2, w3, sigma, iterations, gradient_iterations, method, verbose)
    → (pial_vertices, pial_faces, white_vertices, white_faces)``.

    This is T1Prep's surface estimation step 5 (``CAT_Surf2PialWhite``).

    Examples
    --------
    >>> node = CatSurfSurfToPialWhite()
    >>> node.inputs.vertices = v              # doctest: +SKIP
    >>> node.inputs.faces = fcs              # doctest: +SKIP
    >>> node.inputs.thickness = t           # doctest: +SKIP
    >>> node.inputs.volume_file = 'hemi.nii.gz'
    """

    input_spec = CatSurfSurfToPialWhiteInputSpec
    output_spec = CatSurfSurfToPialWhiteOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        pv, pf, wv, wf = cs.surf_to_pial_white(
            self.inputs.vertices, self.inputs.faces,
            self.inputs.thickness, self.inputs.volume_file,
            w1=self.inputs.w1,
            w2=self.inputs.w2,
            w3=self.inputs.w3,
            sigma=self.inputs.sigma,
            iterations=self.inputs.iterations,
            gradient_iterations=self.inputs.gradient_iterations,
            method=self.inputs.method,
            verbose=self.inputs.verbose,
        )
        self._pv, self._pf, self._wv, self._wf = pv, pf, wv, wf
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["pial_vertices"] = self._pv
        outputs["pial_faces"] = self._pf
        outputs["white_vertices"] = self._wv
        outputs["white_faces"] = self._wf
        return outputs


# ---------------------------------------------------------------------------


class CatSurfSurfToSphereInputSpec(BaseInterfaceInputSpec):
    vertices = traits.Any(mandatory=True, desc="Input surface vertices (N, 3) float32.")
    faces = traits.Any(mandatory=True, desc="Input surface faces (M, 3) int32.")
    stop_at = traits.Int(
        6,
        usedefault=True,
        desc=(
            "Stop inflation at this step (1–6). "
            "Higher values approach a perfect sphere. "
            "Default 6 for full spherical inflation; use 2 for partial inflation."
        ),
    )
    verbose = traits.Bool(False, usedefault=True, desc="Print diagnostic output.")


class CatSurfSurfToSphereOutputSpec(TraitedSpec):
    sphere_vertices = traits.Any(desc="Inflated sphere vertex array (N, 3).")
    sphere_faces = traits.Any(desc="Sphere face array (M, 3).")


class CatSurfSurfToSphere(BaseInterface):
    """Inflate a cortical surface mesh to a sphere.

    Wraps
    ``cat_surf.surf_to_sphere(vertices, faces, stop_at, verbose)
    → (sphere_vertices, sphere_faces)``.

    This is T1Prep's surface estimation step 10a (``CAT_Surf2Sphere``).
    Use ``stop_at=6`` for full spherical inflation (needed for DARTEL
    registration) and ``stop_at=2`` for partial inflation (fMRIPrep mode).

    Examples
    --------
    >>> node = CatSurfSurfToSphere()
    >>> node.inputs.vertices = v   # doctest: +SKIP
    >>> node.inputs.faces = fcs    # doctest: +SKIP
    >>> node.inputs.stop_at = 6
    """

    input_spec = CatSurfSurfToSphereInputSpec
    output_spec = CatSurfSurfToSphereOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        sv, sf = cs.surf_to_sphere(
            self.inputs.vertices, self.inputs.faces,
            stop_at=self.inputs.stop_at,
            verbose=self.inputs.verbose,
        )
        self._sv, self._sf = sv, sf
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["sphere_vertices"] = self._sv
        outputs["sphere_faces"] = self._sf
        return outputs


# ---------------------------------------------------------------------------


class CatSurfSurfWarpInputSpec(BaseInterfaceInputSpec):
    source_file = File(mandatory=True, desc="Source surface file (central surface).")
    source_sphere_file = File(mandatory=True, desc="Source sphere file.")
    target_file = File(mandatory=True, desc="Target (average) surface file used as registration template.")
    target_sphere_file = File(mandatory=True, desc="Target (average) sphere file.")
    output_sphere_file = File(mandatory=True, desc="Output registered sphere file path.")
    n_steps = traits.Int(2, usedefault=True, desc="Number of DARTEL warp steps (default 2).")
    avg = traits.Bool(True, usedefault=True, desc="Use average-shape regularisation during warp.")
    verbose = traits.Bool(False, usedefault=True, desc="Print diagnostic output.")


class CatSurfSurfWarpOutputSpec(TraitedSpec):
    output_sphere_file = File(desc="Registered sphere file.")


class CatSurfSurfWarp(BaseInterface):
    """Perform DARTEL-based spherical surface registration.

    Wraps
    ``cat_surf.surf_warp(source_file, source_sphere_file, target_file,
    target_sphere_file, output_sphere_file, n_steps, avg, verbose)``.

    This is T1Prep's surface estimation step 10b (``CAT_SurfWarp``).

    Examples
    --------
    >>> node = CatSurfSurfWarp()
    >>> node.inputs.source_file = 'lh.central.sub-01.gii'
    >>> node.inputs.source_sphere_file = 'lh.sphere.sub-01.gii'
    >>> node.inputs.target_file = 'lh.central.freesurfer.gii'
    >>> node.inputs.target_sphere_file = 'lh.sphere.freesurfer.gii'
    >>> node.inputs.output_sphere_file = 'lh.sphere.reg.sub-01.gii'
    """

    input_spec = CatSurfSurfWarpInputSpec
    output_spec = CatSurfSurfWarpOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        cs.surf_warp(
            source_file=self.inputs.source_file,
            source_sphere_file=self.inputs.source_sphere_file,
            target_file=self.inputs.target_file,
            target_sphere_file=self.inputs.target_sphere_file,
            output_sphere_file=self.inputs.output_sphere_file,
            n_steps=self.inputs.n_steps,
            avg=self.inputs.avg,
            verbose=self.inputs.verbose,
        )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["output_sphere_file"] = os.path.abspath(self.inputs.output_sphere_file)
        return outputs


# ---------------------------------------------------------------------------


class CatSurfSurfAverageInputSpec(BaseInterfaceInputSpec):
    out_file = File(mandatory=True, desc="Output (averaged) surface file path.")
    in_files = traits.List(
        File(exists=True),
        mandatory=True,
        desc="List of input surface files to average (typically pial + white).",
    )


class CatSurfSurfAverageOutputSpec(TraitedSpec):
    out_file = File(desc="Averaged surface file path.")


class CatSurfSurfAverage(BaseInterface):
    """Average two or more surface meshes vertex-wise.

    Wraps ``cat_surf.surf_average(out_file, *in_files)``.

    T1Prep uses this to recompute the central surface as the average of the
    estimated pial and white matter surfaces (step 5b, ``CAT_SurfAverage``).

    Examples
    --------
    >>> node = CatSurfSurfAverage()
    >>> node.inputs.out_file = 'lh.central.sub-01.gii'
    >>> node.inputs.in_files = ['lh.pial.sub-01.gii', 'lh.white.sub-01.gii']  # doctest: +SKIP
    """

    input_spec = CatSurfSurfAverageInputSpec
    output_spec = CatSurfSurfAverageOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        cs.surf_average(self.inputs.out_file, *self.inputs.in_files)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


# ---------------------------------------------------------------------------


class CatSurfResampleToSphereInputSpec(BaseInterfaceInputSpec):
    source_surface_file = File(mandatory=True, desc="Source surface file.")
    source_sphere_file = File(mandatory=True, desc="Source sphere file.")
    target_sphere_file = File(mandatory=True, desc="Target sphere file (defines the resampling grid).")
    output_surface_file = File(mandatory=True, desc="Output resampled surface file path.")
    input_values_file = File(desc="Optional per-vertex input values file to also resample.")
    output_values_file = File(desc="Optional output resampled values file path.")


class CatSurfResampleToSphereOutputSpec(TraitedSpec):
    output_surface_file = File(desc="Resampled surface file.")
    output_values_file = File(desc="Resampled values file (if requested).")


class CatSurfResampleToSphere(BaseInterface):
    """Resample a surface mesh and optional per-vertex data to a target sphere.

    Wraps ``cat_surf.resample_to_sphere(source_surface_file,
    source_sphere_file, target_sphere_file, output_surface_file,
    [input_values_file, output_values_file])``.

    Examples
    --------
    >>> node = CatSurfResampleToSphere()
    >>> node.inputs.source_surface_file = 'lh.central.sub-01.gii'
    >>> node.inputs.source_sphere_file = 'lh.sphere.sub-01.gii'
    >>> node.inputs.target_sphere_file = 'lh.sphere.freesurfer.gii'
    >>> node.inputs.output_surface_file = 'lh.central.resampled.gii'
    """

    input_spec = CatSurfResampleToSphereInputSpec
    output_spec = CatSurfResampleToSphereOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        kwargs = {
            "source_surface_file": self.inputs.source_surface_file,
            "source_sphere_file": self.inputs.source_sphere_file,
            "target_sphere_file": self.inputs.target_sphere_file,
            "output_surface_file": self.inputs.output_surface_file,
        }
        if isdefined(self.inputs.input_values_file):
            kwargs["input_values_file"] = self.inputs.input_values_file
        if isdefined(self.inputs.output_values_file):
            kwargs["output_values_file"] = self.inputs.output_values_file
        cs.resample_to_sphere(**kwargs)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["output_surface_file"] = os.path.abspath(self.inputs.output_surface_file)
        if isdefined(self.inputs.output_values_file):
            outputs["output_values_file"] = os.path.abspath(self.inputs.output_values_file)
        return outputs


# ---------------------------------------------------------------------------


class CatSurfResampleAnnotInputSpec(BaseInterfaceInputSpec):
    source_surface_file = File(mandatory=True, desc="Source (average) surface file.")
    source_sphere_file = File(mandatory=True, desc="Source (average) sphere file.")
    target_sphere_file = File(mandatory=True, desc="Target subject sphere file (registered).")
    annot_in_file = File(mandatory=True, desc="Input atlas annotation (.annot) file.")
    annot_out_file = File(mandatory=True, desc="Output resampled annotation file path.")


class CatSurfResampleAnnotOutputSpec(TraitedSpec):
    annot_out_file = File(desc="Resampled annotation file.")


class CatSurfResampleAnnot(BaseInterface):
    """Resample a FreeSurfer-style atlas annotation to a subject's sphere.

    Wraps ``cat_surf.resample_annot(source_surface_file,
    source_sphere_file, target_sphere_file, annot_in_file, annot_out_file)``.

    This is used in T1Prep's surface estimation step 10c to project surface
    atlas parcellations onto the subject's sphere (``CAT_SurfResample -label``).

    Examples
    --------
    >>> node = CatSurfResampleAnnot()
    >>> node.inputs.source_surface_file = 'lh.central.freesurfer.gii'
    >>> node.inputs.source_sphere_file = 'lh.sphere.freesurfer.gii'
    >>> node.inputs.target_sphere_file = 'lh.sphere.reg.sub-01.gii'
    >>> node.inputs.annot_in_file = 'lh.aparc_DK40.freesurfer.annot'
    >>> node.inputs.annot_out_file = 'lh.aparc_DK40.sub-01.annot'
    """

    input_spec = CatSurfResampleAnnotInputSpec
    output_spec = CatSurfResampleAnnotOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        cs.resample_annot(
            source_surface_file=self.inputs.source_surface_file,
            source_sphere_file=self.inputs.source_sphere_file,
            target_sphere_file=self.inputs.target_sphere_file,
            annot_in_file=self.inputs.annot_in_file,
            annot_out_file=self.inputs.annot_out_file,
        )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["annot_out_file"] = os.path.abspath(self.inputs.annot_out_file)
        return outputs


# ===========================================================================
# Per-vertex data smoothing / curvature
# ===========================================================================


class CatSurfSmoothHeatkernel(BaseInterface):
    """Smooth per-vertex scalar data on a surface using a heat kernel.

    Wraps
    ``cat_surf.smooth_heatkernel(vertices, faces, values, fwhm)
    → smoothed_values``.

    The heat-kernel smoother is the CAT12 / T1Prep standard for spatial
    smoothing of cortical surface data (thickness, area, curvature, etc.).

    Examples
    --------
    >>> node = CatSurfSmoothHeatkernel()
    >>> node.inputs.vertices = v      # doctest: +SKIP
    >>> node.inputs.faces = fcs       # doctest: +SKIP
    >>> node.inputs.values = thickness  # doctest: +SKIP
    >>> node.inputs.fwhm = 20.0
    """

    class input_spec(BaseInterfaceInputSpec):
        vertices = traits.Any(mandatory=True, desc="Vertex array (N, 3) float32.")
        faces = traits.Any(mandatory=True, desc="Face array (M, 3) int32.")
        values = traits.Any(mandatory=True, desc="Per-vertex scalar data (N,) float32.")
        fwhm = traits.Float(20.0, usedefault=True, desc="FWHM of the heat kernel (mm).")

    class output_spec(TraitedSpec):
        smoothed = traits.Any(desc="Smoothed per-vertex scalar array (N,) float32.")

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._out = cs.smooth_heatkernel(
            self.inputs.vertices, self.inputs.faces,
            self.inputs.values, fwhm=self.inputs.fwhm,
        )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["smoothed"] = self._out
        return outputs


# ---------------------------------------------------------------------------


class CatSurfSmoothMesh(BaseInterface):
    """Smooth a surface mesh by displacing vertices.

    Wraps
    ``cat_surf.smooth_mesh(vertices, faces[, iterations, lambda_])
    → (vertices, faces)``.

    Examples
    --------
    >>> node = CatSurfSmoothMesh()
    >>> node.inputs.vertices = v    # doctest: +SKIP
    >>> node.inputs.faces = fcs     # doctest: +SKIP
    >>> node.inputs.iterations = 10
    """

    class input_spec(BaseInterfaceInputSpec):
        vertices = traits.Any(mandatory=True, desc="Input vertex array (N, 3).")
        faces = traits.Any(mandatory=True, desc="Input face array (M, 3).")
        iterations = traits.Int(10, usedefault=True, desc="Number of smoothing iterations.")
        lambda_ = traits.Float(0.5, usedefault=True, desc="Laplacian smoothing weight (lambda).")

    class output_spec(TraitedSpec):
        vertices = traits.Any(desc="Smoothed vertex array.")
        faces = traits.Any(desc="Face array (unchanged).")

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._v, self._fcs = cs.smooth_mesh(
            self.inputs.vertices, self.inputs.faces,
            iterations=self.inputs.iterations,
        )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["vertices"] = self._v
        outputs["faces"] = self._fcs
        return outputs


# ---------------------------------------------------------------------------


class CatSurfSmoothedCurvatures(BaseInterface):
    """Compute smoothed curvatures of a surface mesh.

    Wraps
    ``cat_surf.smoothed_curvatures(vertices, faces[, fwhm])
    → curvatures``.

    Examples
    --------
    >>> node = CatSurfSmoothedCurvatures()
    >>> node.inputs.vertices = v   # doctest: +SKIP
    >>> node.inputs.faces = fcs    # doctest: +SKIP
    >>> node.inputs.fwhm = 3.0
    """

    class input_spec(BaseInterfaceInputSpec):
        vertices = traits.Any(mandatory=True, desc="Vertex array (N, 3).")
        faces = traits.Any(mandatory=True, desc="Face array (M, 3).")
        fwhm = traits.Float(3.0, usedefault=True, desc="FWHM for curvature smoothing (mm).")

    class output_spec(TraitedSpec):
        curvatures = traits.Any(desc="Per-vertex curvature array (N,) float32.")

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._out = cs.smoothed_curvatures(
            self.inputs.vertices, self.inputs.faces,
            fwhm=self.inputs.fwhm,
        )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["curvatures"] = self._out
        return outputs


# ---------------------------------------------------------------------------


class CatSurfSurfCurvature(BaseInterface):
    """Compute curvature-based per-vertex values for a surface mesh.

    Wraps
    ``cat_surf.surf_curvature(vertices, faces, curvtype[, fwhm,
    use_abs_values, invert_values]) → values``.

    The ``curvtype`` parameter selects the curvature measure
    (e.g. 11 = sulcal depth index as used by T1Prep's fmriprep mode).

    Examples
    --------
    >>> node = CatSurfSurfCurvature()
    >>> node.inputs.vertices = v   # doctest: +SKIP
    >>> node.inputs.faces = fcs    # doctest: +SKIP
    >>> node.inputs.curvtype = 11
    >>> node.inputs.invert_values = True
    """

    class input_spec(BaseInterfaceInputSpec):
        vertices = traits.Any(mandatory=True, desc="Vertex array (N, 3).")
        faces = traits.Any(mandatory=True, desc="Face array (M, 3).")
        curvtype = traits.Int(
            0, usedefault=True,
            desc=(
                "Curvature type (integer code): "
                "0 = mean, 1 = Gaussian, 11 = sulcal depth index."
            ),
        )
        fwhm = traits.Float(0.0, usedefault=True, desc="FWHM for post-smoothing (0 = no smoothing).")
        use_abs_values = traits.Bool(False, usedefault=True, desc="Take absolute values before returning.")
        invert_values = traits.Bool(False, usedefault=True, desc="Negate values before returning.")

    class output_spec(TraitedSpec):
        values = traits.Any(desc="Per-vertex curvature-based scalar array (N,).")

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._out = cs.surf_curvature(
            self.inputs.vertices, self.inputs.faces,
            curvtype=self.inputs.curvtype,
            fwhm=self.inputs.fwhm,
            use_abs_values=self.inputs.use_abs_values,
            invert_values=self.inputs.invert_values,
        )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["values"] = self._out
        return outputs


# ---------------------------------------------------------------------------


class CatSurfSulcusDepth(BaseInterface):
    """Compute sulcal depth (depth potential) on a cortical surface.

    Wraps ``cat_surf.sulcus_depth(vertices, faces) → depth``.

    The sulcal depth map assigns positive values in sulci (inward-folded
    regions) and negative values on gyri.

    Examples
    --------
    >>> node = CatSurfSulcusDepth()
    >>> node.inputs.vertices = v   # doctest: +SKIP
    >>> node.inputs.faces = fcs    # doctest: +SKIP
    """

    class input_spec(BaseInterfaceInputSpec):
        vertices = traits.Any(mandatory=True, desc="Vertex array (N, 3) float32.")
        faces = traits.Any(mandatory=True, desc="Face array (M, 3) int32.")

    class output_spec(TraitedSpec):
        depth = traits.Any(desc="Per-vertex sulcal depth array (N,) float32.")

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._out = cs.sulcus_depth(self.inputs.vertices, self.inputs.faces)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["depth"] = self._out
        return outputs


# ---------------------------------------------------------------------------


class CatSurfCorrectThicknessFolding(BaseInterface):
    """Apply a folding-based correction to cortical thickness estimates.

    Wraps
    ``cat_surf.correct_thickness_folding(vertices, faces, thickness,
    slope, max_dist) → corrected_thickness``.

    This is T1Prep's step 7 (``CAT_SurfCorrectThicknessFolding``).
    The correction reduces systematic overestimation of thickness in
    highly folded regions.

    Examples
    --------
    >>> node = CatSurfCorrectThicknessFolding()
    >>> node.inputs.vertices = v    # doctest: +SKIP
    >>> node.inputs.faces = fcs     # doctest: +SKIP
    >>> node.inputs.thickness = t   # doctest: +SKIP
    >>> node.inputs.slope = 1.0
    >>> node.inputs.max_dist = 6.0
    """

    class input_spec(BaseInterfaceInputSpec):
        vertices = traits.Any(mandatory=True, desc="Vertex array (N, 3) float32.")
        faces = traits.Any(mandatory=True, desc="Face array (M, 3) int32.")
        thickness = traits.Any(mandatory=True, desc="Per-vertex thickness array (N,) float32.")
        slope = traits.Float(1.0, usedefault=True, desc="Correction slope parameter (default 1.0).")
        max_dist = traits.Float(6.0, usedefault=True, desc="Maximum thickness value to correct (mm).")

    class output_spec(TraitedSpec):
        thickness = traits.Any(desc="Corrected per-vertex thickness array (N,).")

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._out = cs.correct_thickness_folding(
            self.inputs.vertices, self.inputs.faces,
            self.inputs.thickness,
            slope=self.inputs.slope,
            max_dist=self.inputs.max_dist,
        )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["thickness"] = self._out
        return outputs


# ===========================================================================
# Volume operations
# ===========================================================================


class CatSurfVolSanlm(BaseInterface):
    """Apply SANLM (Spatially Adaptive Non-Local Means) denoising to a volume.

    Wraps ``cat_surf.vol_sanlm(volume) → denoised_volume``.

    T1Prep applies SANLM denoising as the first preprocessing step on the
    raw T1w data before segmentation.  The input and output are NumPy
    float32 arrays (not NIfTI objects).

    Examples
    --------
    >>> import nibabel as nib
    >>> import numpy as np
    >>> node = CatSurfVolSanlm()
    >>> node.inputs.volume = nib.load('sub-01_T1w.nii.gz').get_fdata().astype(np.float32)  # doctest: +SKIP
    """

    class input_spec(BaseInterfaceInputSpec):
        volume = traits.Any(mandatory=True, desc="3-D float32 numpy array to denoise.")

    class output_spec(TraitedSpec):
        denoised = traits.Any(desc="Denoised 3-D float32 numpy array.")

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._out = cs.vol_sanlm(self.inputs.volume)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["denoised"] = self._out
        return outputs


# ---------------------------------------------------------------------------


class CatSurfVolMarchingCubes(BaseInterface):
    """Extract a surface mesh from a NIfTI volume using marching cubes.

    Wraps
    ``cat_surf.vol_marching_cubes(volume_file, label, threshold, pre_fwhm,
    iter_laplacian, n_median_filter, strength_gyri_mask, verbose)
    → (vertices, faces)``.

    This is T1Prep's surface estimation step 2 (``CAT_VolMarchingCubes``).

    Examples
    --------
    >>> node = CatSurfVolMarchingCubes()
    >>> node.inputs.volume_file = 'ppm.nii.gz'
    >>> node.inputs.label_file = 'hemi.nii.gz'
    >>> node.inputs.threshold = 0.5
    >>> node.inputs.pre_fwhm = 1.0
    """

    class input_spec(BaseInterfaceInputSpec):
        volume_file = File(
            mandatory=True,
            desc="NIfTI volume from which to extract the surface (e.g. PPM probability map).",
        )
        label_file = File(
            mandatory=True,
            desc="NIfTI label volume used as a mask (e.g. hemisphere partition map).",
        )
        threshold = traits.Float(0.5, usedefault=True, desc="Iso-surface threshold (default 0.5).")
        pre_fwhm = traits.Float(1.0, usedefault=True, desc="Pre-smoothing FWHM before marching cubes (mm).")
        iter_laplacian = traits.Int(50, usedefault=True, desc="Laplacian smoothing iterations after extraction.")
        n_median_filter = traits.Int(0, usedefault=True, desc="Number of median filter passes applied before extraction.")
        strength_gyri_mask = traits.Float(0.1, usedefault=True, desc="Strength of gyral mask applied to the volume.")
        verbose = traits.Bool(False, usedefault=True, desc="Print diagnostic output.")

    class output_spec(TraitedSpec):
        vertices = traits.Any(desc="Extracted surface vertex array (N, 3).")
        faces = traits.Any(desc="Extracted surface face array (M, 3).")

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._v, self._fcs = cs.vol_marching_cubes(
            self.inputs.volume_file,
            label=self.inputs.label_file,
            threshold=self.inputs.threshold,
            pre_fwhm=self.inputs.pre_fwhm,
            iter_laplacian=self.inputs.iter_laplacian,
            n_median_filter=self.inputs.n_median_filter,
            strength_gyri_mask=self.inputs.strength_gyri_mask,
            verbose=self.inputs.verbose,
        )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["vertices"] = self._v
        outputs["faces"] = self._fcs
        return outputs


# ---------------------------------------------------------------------------


class CatSurfVol2Surf(BaseInterface):
    """Project a volumetric image onto a surface mesh.

    Wraps
    ``cat_surf.vol2surf(volume_file, vertices, faces, grid_start, grid_end,
    grid_steps, map_func) → (values, grid_points)``.

    Used in T1Prep's surface estimation steps 4 and 8 (``CAT_Vol2Surf``).

    The ``map_func`` parameter controls how multiple sampling positions along
    the surface normal are combined:

    * ``"mean"``     – arithmetic mean
    * ``"waverage"`` – weighted average (Gaussian along normal)
    * ``"median"``   – median
    * ``"max"``      – maximum

    Examples
    --------
    Map GMT thickness volume onto central surface:

    >>> node = CatSurfVol2Surf()
    >>> node.inputs.volume_file = 'gmt.nii.gz'
    >>> node.inputs.vertices = v      # doctest: +SKIP
    >>> node.inputs.faces = fcs       # doctest: +SKIP
    >>> node.inputs.grid_start = -0.4
    >>> node.inputs.grid_end = 0.4
    >>> node.inputs.grid_steps = 5
    >>> node.inputs.map_func = 'waverage'
    """

    class input_spec(BaseInterfaceInputSpec):
        volume_file = File(mandatory=True, desc="NIfTI volume to project onto the surface.")
        vertices = traits.Any(mandatory=True, desc="Surface vertex array (N, 3) float32.")
        faces = traits.Any(mandatory=True, desc="Surface face array (M, 3) int32.")
        grid_start = traits.Float(
            -0.4, usedefault=True,
            desc="Start of the sampling grid along the surface normal (relative to vertex, in mm).",
        )
        grid_end = traits.Float(
            0.4, usedefault=True,
            desc="End of the sampling grid along the surface normal (mm).",
        )
        grid_steps = traits.Int(
            5, usedefault=True,
            desc="Number of equally spaced sampling positions along the normal.",
        )
        map_func = traits.Enum(
            "waverage", "mean", "median", "max",
            usedefault=True,
            desc="Aggregation function for values along the normal ('waverage', 'mean', 'median', 'max').",
        )

    class output_spec(TraitedSpec):
        values = traits.Any(desc="Per-vertex scalar array (N,) float32.")
        grid_points = traits.Any(desc="Sampling grid coordinates (N, grid_steps, 3).")

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._values, self._grid = cs.vol2surf(
            self.inputs.volume_file,
            self.inputs.vertices, self.inputs.faces,
            grid_start=self.inputs.grid_start,
            grid_end=self.inputs.grid_end,
            grid_steps=self.inputs.grid_steps,
            map_func=self.inputs.map_func,
        )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["values"] = self._values
        outputs["grid_points"] = self._grid
        return outputs


# ---------------------------------------------------------------------------


class CatSurfVolThicknessPbt(BaseInterface):
    """Estimate cortical thickness via the Projection-Based Thickness method.

    Wraps
    ``cat_surf.vol_thickness_pbt(volume, voxelsize, n_avgs, n_median_filter,
    median_subsample, range_val, correct_voxelsize, sulcal_width, verbose)
    → (gmt, ppm, dcsf, dwm)``.

    This is T1Prep's surface estimation step 1 (``CAT_VolThicknessPbt``).
    Returns the GMT (grey matter thickness), PPM (pial probability map),
    and DCSF/DWM distance maps.

    Examples
    --------
    >>> import nibabel as nib, numpy as np
    >>> node = CatSurfVolThicknessPbt()
    >>> img = nib.load('hemi.nii.gz')  # doctest: +SKIP
    >>> node.inputs.volume = img.get_fdata().astype(np.float32)  # doctest: +SKIP
    >>> node.inputs.voxelsize = img.header.get_zooms()[:3]       # doctest: +SKIP
    """

    class input_spec(BaseInterfaceInputSpec):
        volume = traits.Any(mandatory=True, desc="3-D float32 hemisphere partition volume.")
        voxelsize = traits.Any(mandatory=True, desc="Voxel dimensions in mm (length-3 array or tuple).")
        n_avgs = traits.Int(2, usedefault=True, desc="Number of averaging passes during PBT.")
        n_median_filter = traits.Int(2, usedefault=True, desc="Number of median filter passes.")
        median_subsample = traits.Int(2, usedefault=True, desc="Subsampling factor for median filter.")
        range_val = traits.Float(0.45, usedefault=True, desc="Range value for PBT.")
        correct_voxelsize = traits.Float(-0.75, usedefault=True, desc="Voxel-size correction factor.")
        sulcal_width = traits.Float(5.0, usedefault=True, desc="Sulcal width parameter (mm).")
        verbose = traits.Bool(False, usedefault=True, desc="Print diagnostic output.")

    class output_spec(TraitedSpec):
        gmt = traits.Any(desc="GM thickness volume (float32 array, same shape as input).")
        ppm = traits.Any(desc="Pial probability map volume (float32 array).")
        dcsf = traits.Any(desc="Distance to CSF volume (float32 array).")
        dwm = traits.Any(desc="Distance to WM volume (float32 array).")

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        gmt, ppm, dcsf, dwm = cs.vol_thickness_pbt(
            self.inputs.volume,
            voxelsize=self.inputs.voxelsize,
            n_avgs=self.inputs.n_avgs,
            n_median_filter=self.inputs.n_median_filter,
            median_subsample=self.inputs.median_subsample,
            range_val=self.inputs.range_val,
            correct_voxelsize=self.inputs.correct_voxelsize,
            sulcal_width=self.inputs.sulcal_width,
            verbose=self.inputs.verbose,
        )
        self._gmt, self._ppm, self._dcsf, self._dwm = gmt, ppm, dcsf, dwm
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["gmt"] = self._gmt
        outputs["ppm"] = self._ppm
        outputs["dcsf"] = self._dcsf
        outputs["dwm"] = self._dwm
        return outputs


# ---------------------------------------------------------------------------


class CatSurfVolAmap(BaseInterface):
    """Apply AMAP (Adaptive Maximum A Posteriori) tissue segmentation.

    Wraps
    ``cat_surf.vol_amap(volume, label, voxelsize, weight_mrf, sub,
    use_multistep, pve, verbose) → (probability_maps, label_out, means)``.

    The output ``probability_maps`` has shape (X, Y, Z, 3) with uint8 values
    in [0, 255]; channel order is CSF=0, GM=1, WM=2.

    T1Prep uses AMAP (when ``--amap`` is specified) to refine the initial
    DeepMriPrep tissue classification.

    Examples
    --------
    >>> node = CatSurfVolAmap()
    >>> node.inputs.volume = brain_data   # doctest: +SKIP
    >>> node.inputs.label = seg_data      # doctest: +SKIP
    >>> node.inputs.voxelsize = (1.0, 1.0, 1.0)
    """

    class input_spec(BaseInterfaceInputSpec):
        volume = traits.Any(mandatory=True, desc="3-D float32 bias-corrected intensity volume.")
        label = traits.Any(mandatory=True, desc="3-D uint8 tissue label map (1=CSF, 2=GM, 3=WM).")
        voxelsize = traits.Any(mandatory=True, desc="Voxel dimensions in mm (length-3 array or tuple).")
        weight_mrf = traits.Float(0.0, usedefault=True, desc="MRF (Markov Random Field) regularisation weight.")
        sub = traits.Int(64, usedefault=True, desc="Sub-volume size for AMAP tiling.")
        use_multistep = traits.Bool(True, usedefault=True, desc="Use multi-step AMAP estimation.")
        pve = traits.Bool(False, usedefault=True, desc="Output partial volume estimates.")
        verbose = traits.Bool(False, usedefault=True, desc="Print diagnostic output.")

    class output_spec(TraitedSpec):
        probability_maps = traits.Any(
            desc="Probability map array (X, Y, Z, 3) uint8 [0–255]; channels: CSF=0, GM=1, WM=2."
        )
        label_out = traits.Any(desc="Hard tissue label map after AMAP (uint8).")
        means = traits.Any(desc="Per-class intensity means (length-3 array).")

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        prob, lab_out, means = cs.vol_amap(
            self.inputs.volume,
            self.inputs.label,
            voxelsize=self.inputs.voxelsize,
            weight_mrf=self.inputs.weight_mrf,
            sub=self.inputs.sub,
            use_multistep=self.inputs.use_multistep,
            pve=self.inputs.pve,
            verbose=self.inputs.verbose,
        )
        self._prob, self._lab, self._means = prob, lab_out, means
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["probability_maps"] = self._prob
        outputs["label_out"] = self._lab
        outputs["means"] = self._means
        return outputs


# ---------------------------------------------------------------------------


class CatSurfVolBloodVesselCorrection(BaseInterface):
    """Apply blood-vessel intensity correction to a T1w volume.

    Wraps
    ``cat_surf.vol_blood_vessel_correction(volume, voxelsize)
    → corrected_volume``.

    Reduces the intensity artefacts caused by large blood vessels
    in the hemisphere partition volume before surface extraction.
    T1Prep applies this in step 1 when ``vessel > 0``.

    Examples
    --------
    >>> node = CatSurfVolBloodVesselCorrection()
    >>> node.inputs.volume = hemi_data   # doctest: +SKIP
    >>> node.inputs.voxelsize = (0.5, 0.5, 0.5)
    """

    class input_spec(BaseInterfaceInputSpec):
        volume = traits.Any(mandatory=True, desc="3-D float32 hemisphere partition volume.")
        voxelsize = traits.Any(mandatory=True, desc="Voxel dimensions in mm (length-3 array or tuple).")

    class output_spec(TraitedSpec):
        corrected = traits.Any(desc="Blood-vessel-corrected 3-D float32 volume.")

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._out = cs.vol_blood_vessel_correction(
            self.inputs.volume,
            voxelsize=self.inputs.voxelsize,
        )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["corrected"] = self._out
        return outputs


# ===========================================================================
# Registration
# ===========================================================================


class CatSurfBbreg(BaseInterface):
    """Register a functional/diffusion image to a T1w using boundary-based registration.

    Wraps ``cat_surf.bbreg(moving_file, fixed_file, ...) → transform``.

    Boundary-based registration (BBR) aligns a moving volume to a fixed
    anatomical image by maximising the gradient magnitude at GM/WM
    boundaries projected onto the registered surface.

    Examples
    --------
    >>> node = CatSurfBbreg()
    >>> node.inputs.moving_file = 'bold_ref.nii.gz'
    >>> node.inputs.fixed_file = 'sub-01_T1w.nii.gz'
    >>> node.inputs.surface_file = 'lh.white.sub-01.gii'
    """

    class input_spec(BaseInterfaceInputSpec):
        moving_file = File(mandatory=True, desc="Moving (source) NIfTI image.")
        fixed_file = File(mandatory=True, desc="Fixed (reference) T1w NIfTI image.")
        surface_file = File(desc="White-matter surface file used for BBR cost calculation.")
        init_matrix = File(desc="Initial 4×4 affine transform matrix file (.mat or .txt).")
        out_matrix_file = File(desc="Output affine transform file path.")
        dof = traits.Enum(
            6, 9, 12,
            usedefault=False,
            desc="Degrees of freedom for the registration (6, 9, or 12).",
        )
        verbose = traits.Bool(False, usedefault=True, desc="Print diagnostic output.")

    class output_spec(TraitedSpec):
        out_matrix_file = File(desc="Output affine transform matrix file.")

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        kwargs = {
            "moving_file": self.inputs.moving_file,
            "fixed_file": self.inputs.fixed_file,
        }
        for opt in ("surface_file", "init_matrix", "out_matrix_file", "dof"):
            val = getattr(self.inputs, opt)
            if isdefined(val):
                kwargs[opt] = val
        kwargs["verbose"] = self.inputs.verbose
        self._result = cs.bbreg(**kwargs)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.out_matrix_file):
            outputs["out_matrix_file"] = os.path.abspath(self.inputs.out_matrix_file)
        return outputs


# ---------------------------------------------------------------------------


class CatSurfBbregDetectContrast(BaseInterface):
    """Automatically detect the image contrast type for BBR registration.

    Wraps ``cat_surf.bbreg_detect_contrast(volume_file) → contrast_type``.

    Returns a string indicating the detected contrast (e.g. ``'T1'``, ``'T2'``,
    ``'PD'``) which is passed to :class:`CatSurfBbreg`.

    Examples
    --------
    >>> node = CatSurfBbregDetectContrast()
    >>> node.inputs.volume_file = 'bold_ref.nii.gz'
    """

    class input_spec(BaseInterfaceInputSpec):
        volume_file = File(mandatory=True, desc="NIfTI volume file to analyse.")

    class output_spec(TraitedSpec):
        contrast_type = traits.Str(desc="Detected contrast type string (e.g. 'T1', 'T2', 'PD').")

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        self._contrast = str(cs.bbreg_detect_contrast(self.inputs.volume_file))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["contrast_type"] = self._contrast
        return outputs


# ---------------------------------------------------------------------------


class CatSurfVolumeRegisterNmi(BaseInterface):
    """Register two volumes by maximising Normalised Mutual Information.

    Wraps
    ``cat_surf.volume_register_nmi(moving_file, fixed_file, out_matrix_file,
    [dof, verbose]) → out_matrix_file``.

    Examples
    --------
    >>> node = CatSurfVolumeRegisterNmi()
    >>> node.inputs.moving_file = 'sub-01_T1w.nii.gz'
    >>> node.inputs.fixed_file = 'template_T1.nii.gz'
    >>> node.inputs.out_matrix_file = 'sub-01_to_template.mat'
    """

    class input_spec(BaseInterfaceInputSpec):
        moving_file = File(mandatory=True, desc="Moving (source) NIfTI image.")
        fixed_file = File(mandatory=True, desc="Fixed (reference) NIfTI image.")
        out_matrix_file = File(mandatory=True, desc="Output affine matrix file path.")
        dof = traits.Enum(
            12, 6, 9,
            usedefault=False,
            desc="Degrees of freedom (6, 9, or 12).",
        )
        verbose = traits.Bool(False, usedefault=True, desc="Print diagnostic output.")

    class output_spec(TraitedSpec):
        out_matrix_file = File(desc="Output affine matrix file.")

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        kwargs = {
            "moving_file": self.inputs.moving_file,
            "fixed_file": self.inputs.fixed_file,
            "out_matrix_file": self.inputs.out_matrix_file,
        }
        if isdefined(self.inputs.dof):
            kwargs["dof"] = self.inputs.dof
        kwargs["verbose"] = self.inputs.verbose
        cs.volume_register_nmi(**kwargs)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_matrix_file"] = os.path.abspath(self.inputs.out_matrix_file)
        return outputs


# ---------------------------------------------------------------------------


class CatSurfVolumeRegisterRobust(BaseInterface):
    """Register two volumes using robust (outlier-resistant) optimisation.

    Wraps
    ``cat_surf.volume_register_robust(moving_file, fixed_file, out_matrix_file,
    [dof, verbose]) → out_matrix_file``.

    Robust registration is less sensitive to intensity outliers (e.g. lesions)
    than standard NMI registration.

    Examples
    --------
    >>> node = CatSurfVolumeRegisterRobust()
    >>> node.inputs.moving_file = 'sub-01_T1w.nii.gz'
    >>> node.inputs.fixed_file = 'template_T1.nii.gz'
    >>> node.inputs.out_matrix_file = 'sub-01_to_template_robust.mat'
    """

    class input_spec(BaseInterfaceInputSpec):
        moving_file = File(mandatory=True, desc="Moving (source) NIfTI image.")
        fixed_file = File(mandatory=True, desc="Fixed (reference) NIfTI image.")
        out_matrix_file = File(mandatory=True, desc="Output affine matrix file path.")
        dof = traits.Enum(
            12, 6, 9,
            usedefault=False,
            desc="Degrees of freedom (6, 9, or 12).",
        )
        verbose = traits.Bool(False, usedefault=True, desc="Print diagnostic output.")

    class output_spec(TraitedSpec):
        out_matrix_file = File(desc="Output affine matrix file.")

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        kwargs = {
            "moving_file": self.inputs.moving_file,
            "fixed_file": self.inputs.fixed_file,
            "out_matrix_file": self.inputs.out_matrix_file,
        }
        if isdefined(self.inputs.dof):
            kwargs["dof"] = self.inputs.dof
        kwargs["verbose"] = self.inputs.verbose
        cs.volume_register_robust(**kwargs)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_matrix_file"] = os.path.abspath(self.inputs.out_matrix_file)
        return outputs
