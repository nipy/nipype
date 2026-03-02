# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Interfaces to perform image registrations and to apply the resulting
displacement maps to images and points.

"""
import os.path as op
import re

from ... import logging
from .base import ElastixBaseInputSpec
from ..base import CommandLine, TraitedSpec, File, traits, InputMultiPath

iflogger = logging.getLogger("nipype.interface")


class RegistrationInputSpec(ElastixBaseInputSpec):
    fixed_image = File(exists=True, mandatory=True, argstr="-f %s", desc="fixed image")
    moving_image = File(
        exists=True, mandatory=True, argstr="-m %s", desc="moving image"
    )
    parameters = InputMultiPath(
        File(exists=True),
        mandatory=True,
        argstr="-p %s...",
        desc="parameter file, elastix handles 1 or more -p",
    )
    fixed_mask = File(exists=True, argstr="-fMask %s", desc="mask for fixed image")
    moving_mask = File(exists=True, argstr="-mMask %s", desc="mask for moving image")
    initial_transform = File(
        exists=True, argstr="-t0 %s", desc="parameter file for initial transform"
    )


class RegistrationOutputSpec(TraitedSpec):
    transform = InputMultiPath(File(exists=True), desc="output transform")
    warped_file = File(desc="input moving image warped to fixed image")
    warped_files = InputMultiPath(
        File(exists=False),
        desc=("input moving image warped to fixed image at each level"),
    )
    warped_files_flags = traits.List(
        traits.Bool(False), desc="flag indicating if warped image was generated"
    )


class Registration(CommandLine):
    """
    Elastix nonlinear registration interface

    Example
    -------

    >>> from nipype.interfaces.elastix import Registration
    >>> reg = Registration()
    >>> reg.inputs.fixed_image = 'fixed1.nii'
    >>> reg.inputs.moving_image = 'moving1.nii'
    >>> reg.inputs.parameters = ['elastix.txt']
    >>> reg.cmdline
    'elastix -f fixed1.nii -m moving1.nii -threads 1 -out ./ -p elastix.txt'


    """

    _cmd = "elastix"
    input_spec = RegistrationInputSpec
    output_spec = RegistrationOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()

        out_dir = op.abspath(self.inputs.output_path)

        regex = re.compile(r"^\((\w+)\s(.+)\)$")

        outputs["transform"] = []
        outputs["warped_files"] = []
        outputs["warped_files_flags"] = []

        for i, params in enumerate(self.inputs.parameters):
            config = {}

            with open(params) as f:
                for line in f:
                    line = line.strip()
                    if not line.startswith("//") and line:
                        m = regex.search(line)
                        if m:
                            value = self._cast(m.group(2).strip())
                            config[m.group(1).strip()] = value

            outputs["transform"].append(
                op.join(out_dir, "TransformParameters.%01d.txt" % i)
            )

            warped_file = None
            if config["WriteResultImage"]:
                warped_file = op.join(
                    out_dir, "result.%01d.%s" % (i, config["ResultImageFormat"])
                )

            outputs["warped_files"].append(warped_file)
            outputs["warped_files_flags"].append(config["WriteResultImage"])

        if outputs["warped_files_flags"][-1]:
            outputs["warped_file"] = outputs["warped_files"][-1]

        return outputs

    def _cast(self, val):
        if val.startswith('"') and val.endswith('"'):
            if val == '"true"':
                return True
            elif val == '"false"':
                return False
            else:
                return val[1:-1]

        try:
            return int(val)
        except ValueError:
            try:
                return float(val)
            except ValueError:
                return val


class ApplyWarpInputSpec(ElastixBaseInputSpec):
    transform_file = File(
        exists=True,
        mandatory=True,
        argstr="-tp %s",
        desc="transform-parameter file, only 1",
    )

    moving_image = File(
        exists=True, argstr="-in %s", mandatory=True, desc="input image to deform"
    )


class ApplyWarpOutputSpec(TraitedSpec):
    warped_file = File(desc="input moving image warped to fixed image")


class ApplyWarp(CommandLine):
    """
    Use ``transformix`` to apply a transform on an input image.
    The transform is specified in the transform-parameter file.

    Example
    -------

    >>> from nipype.interfaces.elastix import ApplyWarp
    >>> reg = ApplyWarp()
    >>> reg.inputs.moving_image = 'moving1.nii'
    >>> reg.inputs.transform_file = 'TransformParameters.0.txt'
    >>> reg.cmdline
    'transformix -in moving1.nii -threads 1 -out ./ -tp TransformParameters.0.txt'


    """

    _cmd = "transformix"
    input_spec = ApplyWarpInputSpec
    output_spec = ApplyWarpOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        out_dir = op.abspath(self.inputs.output_path)
        outputs["warped_file"] = op.join(out_dir, "result.nii.gz")
        return outputs


class AnalyzeWarpInputSpec(ApplyWarpInputSpec):
    points = traits.Enum(
        "all",
        usedefault=True,
        position=0,
        argstr="-def %s",
        desc="transform all points from the input-image, which effectively"
        " generates a deformation field.",
    )
    jac = traits.Enum(
        "all",
        usedefault=True,
        argstr="-jac %s",
        desc="generate an image with the determinant of the spatial Jacobian",
    )
    jacmat = traits.Enum(
        "all",
        usedefault=True,
        argstr="-jacmat %s",
        desc="generate an image with the spatial Jacobian matrix at each voxel",
    )
    moving_image = File(
        exists=True, argstr="-in %s", desc="input image to deform (not used)"
    )


class AnalyzeWarpOutputSpec(TraitedSpec):
    disp_field = File(desc="displacements field")
    jacdet_map = File(desc="det(Jacobian) map")
    jacmat_map = File(desc="Jacobian matrix map")


class AnalyzeWarp(ApplyWarp):
    """
    Use transformix to get details from the input transform (generate
    the corresponding deformation field, generate the determinant of the
    Jacobian map or the Jacobian map itself)

    Example
    -------

    >>> from nipype.interfaces.elastix import AnalyzeWarp
    >>> reg = AnalyzeWarp()
    >>> reg.inputs.transform_file = 'TransformParameters.0.txt'
    >>> reg.cmdline
    'transformix -def all -jac all -jacmat all -threads 1 -out ./ -tp TransformParameters.0.txt'


    """

    input_spec = AnalyzeWarpInputSpec
    output_spec = AnalyzeWarpOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        out_dir = op.abspath(self.inputs.output_path)
        outputs["disp_field"] = op.join(out_dir, "deformationField.nii.gz")
        outputs["jacdet_map"] = op.join(out_dir, "spatialJacobian.nii.gz")
        outputs["jacmat_map"] = op.join(out_dir, "fullSpatialJacobian.nii.gz")
        return outputs


class PointsWarpInputSpec(ElastixBaseInputSpec):
    points_file = File(
        exists=True,
        argstr="-def %s",
        mandatory=True,
        desc="input points (accepts .vtk triangular meshes).",
    )
    transform_file = File(
        exists=True,
        mandatory=True,
        argstr="-tp %s",
        desc="transform-parameter file, only 1",
    )


class PointsWarpOutputSpec(TraitedSpec):
    warped_file = File(desc="input points displaced in fixed image domain")


class PointsWarp(CommandLine):
    """Use ``transformix`` to apply a transform on an input point set.
    The transform is specified in the transform-parameter file.

    Example
    -------

    >>> from nipype.interfaces.elastix import PointsWarp
    >>> reg = PointsWarp()
    >>> reg.inputs.points_file = 'surf1.vtk'
    >>> reg.inputs.transform_file = 'TransformParameters.0.txt'
    >>> reg.cmdline
    'transformix -threads 1 -out ./ -def surf1.vtk -tp TransformParameters.0.txt'


    """

    _cmd = "transformix"
    input_spec = PointsWarpInputSpec
    output_spec = PointsWarpOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        out_dir = op.abspath(self.inputs.output_path)

        fname, ext = op.splitext(op.basename(self.inputs.points_file))

        outputs["warped_file"] = op.join(out_dir, "outputpoints%s" % ext)
        return outputs
