# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    The maths module provides higher-level interfaces to some of the operations
    that can be performed with the niftysegmaths command-line program.
"""
import os
import numpy as np

from nipype.interfaces.niftyseg.base import NIFTYSEGCommand, NIFTYSEGCommandInputSpec
from nipype.interfaces.base import (TraitedSpec, File, traits, InputMultiPath,
                                    isdefined)

class MathsInput(NIFTYSEGCommandInputSpec):
    
    in_file = File(position=2, argstr="%s", exists=True, mandatory=True,
                desc="image to operate on")
    out_file = File(genfile=True, position=-2, argstr="%s", desc="image to write", hash_files=False)
    _dtypes = ["float", "char", "int", "short", "double", "input"]
    output_datatype = traits.Enum(*_dtypes,
                                  position=-1, argstr="-odt %s",
                                  desc="datatype to use for output (default uses input type)")
    
class MathsOutput(TraitedSpec):

    out_file = File(exists=True, desc="image written after calculations")

class MathsCommand(NIFTYSEGCommand):

    _cmd = "seg_maths"
    input_spec = MathsInput
    output_spec = MathsOutput
    _suffix = "_maths"

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] = self._gen_fname(self.inputs.in_file, suffix=self._suffix)
        outputs["out_file"] = os.path.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None

class UnaryMathsInput(MathsInput):

    operation = traits.Enum("exp", "log", "sin", "cos", "tan", "asin", "acos", "atan", "sqr", "sqrt",
                            "recip", "abs", "bin", "binv", "fillh", "fillh26", "index", "edge", "nan",
                            "nanm", "rand", "randn", "range",
                            argstr="-%s", position=4, mandatory=True,
                            desc="operation to perform")


class UnaryMaths(MathsCommand):

    """Use niftysegmaths to perorm a variety of mathematical operations on an image.

    Examples
    --------
    from nipype.interfaces.niftyseg.maths import MaxImage
    maxer = MaxImage()
    maxer.inputs.in_file = "functional.nii"
    maxer.dimension = "T"
    maths.cmdline
    niftysegmaths functional.nii -Tmax functional_max.nii

    """
    input_spec = UnaryMathsInput

    def _list_outputs(self):
        self._suffix = "_" + self.inputs.operation
        return super(UnaryMaths, self)._list_outputs()


class BinaryMathsInput(MathsInput):

    operation = traits.Enum("add", "sub", "mul", "div", "rem", "max", "min",
                            mandatory=True, argstr="-%s", position=4,
                            desc="operation to perform")
    operand_file = File(exists=True, argstr="%s", mandatory=True, position=5, xor=["operand_value"],
                        desc="second image to perform operation with")
    operand_value = traits.Float(argstr="%.8f", mandatory=True, position=5, xor=["operand_file"],
                                 desc="value to perform operation with")


class BinaryMaths(MathsCommand):

    """Use niftysegmaths to perform mathematical operations using a second image or a numeric value.

    Examples
    --------
    from nipype.interfaces.niftyseg.maths import MaxImage
    maxer = MaxImage()
    maxer.inputs.in_file = "functional.nii"
    maxer.dimension = "T"
    maths.cmdline
    niftysegmaths functional.nii -Tmax functional_max.nii

    """

    input_spec = BinaryMathsInput

