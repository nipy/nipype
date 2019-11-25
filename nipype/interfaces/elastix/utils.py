# -*- coding: utf-8 -*-
# coding: utf-8
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Generic interfaces to manipulate registration parameters files, including
transform files (to configure warpings)

"""
import os.path as op

from ... import logging
from ..base import (
    BaseInterface,
    BaseInterfaceInputSpec,
    isdefined,
    TraitedSpec,
    File,
    traits,
)

iflogger = logging.getLogger("nipype.interface")


class EditTransformInputSpec(BaseInterfaceInputSpec):
    transform_file = File(
        exists=True, mandatory=True, desc="transform-parameter file, only 1"
    )
    reference_image = File(
        exists=True,
        desc=("set a new reference image to change the " "target coordinate system."),
    )
    interpolation = traits.Enum(
        "cubic",
        "linear",
        "nearest",
        usedefault=True,
        argstr="FinalBSplineInterpolationOrder",
        desc="set a new interpolator for transformation",
    )

    output_type = traits.Enum(
        "float",
        "unsigned char",
        "unsigned short",
        "short",
        "unsigned long",
        "long",
        "double",
        argstr="ResultImagePixelType",
        desc="set a new output pixel type for resampled images",
    )
    output_format = traits.Enum(
        "nii.gz",
        "nii",
        "mhd",
        "hdr",
        "vtk",
        argstr="ResultImageFormat",
        desc="set a new image format for resampled images",
    )
    output_file = File(desc="the filename for the resulting transform file")


class EditTransformOutputSpec(TraitedSpec):
    output_file = File(exists=True, desc="output transform file")


class EditTransform(BaseInterface):
    """
    Manipulates an existing transform file generated with elastix

    Example
    -------

    >>> from nipype.interfaces.elastix import EditTransform
    >>> tfm = EditTransform()
    >>> tfm.inputs.transform_file = 'TransformParameters.0.txt'  # doctest: +SKIP
    >>> tfm.inputs.reference_image = 'fixed1.nii'  # doctest: +SKIP
    >>> tfm.inputs.output_type = 'unsigned char'
    >>> tfm.run() # doctest: +SKIP

    """

    input_spec = EditTransformInputSpec
    output_spec = EditTransformOutputSpec
    _out_file = ""
    _pattern = r'\((?P<entry>%s\s"?)([-\.\s\w]+)("?\))'

    _interp = {"nearest": 0, "linear": 1, "cubic": 3}

    def _run_interface(self, runtime):
        import re
        import nibabel as nb
        import numpy as np

        contents = ""

        with open(self.inputs.transform_file, "r") as f:
            contents = f.read()

        if isdefined(self.inputs.output_type):
            p = re.compile(
                (self._pattern % "ResultImagePixelType").decode("string-escape")
            )
            rep = r"(\g<entry>%s\g<3>" % self.inputs.output_type
            contents = p.sub(rep, contents)

        if isdefined(self.inputs.output_format):
            p = re.compile(
                (self._pattern % "ResultImageFormat").decode("string-escape")
            )
            rep = r"(\g<entry>%s\g<3>" % self.inputs.output_format
            contents = p.sub(rep, contents)

        if isdefined(self.inputs.interpolation):
            p = re.compile(
                (self._pattern % "FinalBSplineInterpolationOrder").decode(
                    "string-escape"
                )
            )
            rep = r"(\g<entry>%s\g<3>" % self._interp[self.inputs.interpolation]
            contents = p.sub(rep, contents)

        if isdefined(self.inputs.reference_image):
            im = nb.load(self.inputs.reference_image)

            if len(im.header.get_zooms()) == 4:
                im = nb.func.four_to_three(im)[0]

            size = " ".join(["%01d" % s for s in im.shape])
            p = re.compile((self._pattern % "Size").decode("string-escape"))
            rep = r"(\g<entry>%s\g<3>" % size
            contents = p.sub(rep, contents)

            index = " ".join(["0" for s in im.shape])
            p = re.compile((self._pattern % "Index").decode("string-escape"))
            rep = r"(\g<entry>%s\g<3>" % index
            contents = p.sub(rep, contents)

            spacing = " ".join(["%0.4f" % f for f in im.header.get_zooms()])
            p = re.compile((self._pattern % "Spacing").decode("string-escape"))
            rep = r"(\g<entry>%s\g<3>" % spacing
            contents = p.sub(rep, contents)

            itkmat = np.eye(4)
            itkmat[0, 0] = -1
            itkmat[1, 1] = -1

            affine = np.dot(itkmat, im.affine)
            dirs = " ".join(["%0.4f" % f for f in affine[0:3, 0:3].reshape(-1)])
            orig = " ".join(["%0.4f" % f for f in affine[0:3, 3].reshape(-1)])

            # p = re.compile((self._pattern % 'Direction').decode('string-escape'))
            # rep = '(\g<entry>%s\g<3>' % dirs
            # contents = p.sub(rep, contents)

            p = re.compile((self._pattern % "Origin").decode("string-escape"))
            rep = r"(\g<entry>%s\g<3>" % orig
            contents = p.sub(rep, contents)

        with open(self._get_outfile(), "w") as of:
            of.write(contents)

        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["output_file"] = getattr(self, "_out_file")
        return outputs

    def _get_outfile(self):
        val = getattr(self, "_out_file")
        if val is not None and val != "":
            return val

        if isdefined(self.inputs.output_file):
            setattr(self, "_out_file", self.inputs.output_file)
            return self.inputs.output_file

        out_file = op.abspath(op.basename(self.inputs.transform_file))
        setattr(self, "_out_file", out_file)
        return out_file
