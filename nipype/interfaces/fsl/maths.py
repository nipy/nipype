# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    The maths module provides higher-level interfaces to some of the operations
    that can be performed with the fslmaths command-line program.

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""

import numpy as np

from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec
from nipype.interfaces.base import TraitedSpec, File, traits
from nipype.utils.misc import isdefined


class MathsInput(FSLCommandInputSpec):
    
    in_file = File(position=2, argstr="%s", exists=True, mandatory=True,
                desc="image to operate on")
    out_file = File(genfile=True, position=-2, argstr="%s", desc="image to write")
    _dtypes = ["float","char","int","short","double","input"]
    internal_datatype = traits.Enum(*_dtypes, position=1, argstr="-dt %s",
                                    desc="datatype to use for calculations (default is float)")
    output_datatype = traits.Enum(*_dtypes,
                                  position=-1, argstr="-odt %s",
                                  desc="datatype to use for output (default uses input type)")

class MathsOutput(TraitedSpec):

    out_file = File(exists=True, desc="image written after calculations")

class MathsCommand(FSLCommand):

    _cmd = "fslmaths"
    input_spec = MathsInput
    output_spec = MathsOutput
    _suffix = "_maths"

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] =  self._gen_fname(self.inputs.in_file, suffix=self._suffix)
        return outputs


    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None

class ChangeDataTypeInput(MathsInput):

    _dtypes = ["float","char","int","short","double","input"]
    output_datatype = traits.Enum(*_dtypes,
                                  position=-1, argstr="-odt %s", mandatory=True,
                                  desc="output data type")

class ChangeDataType(MathsCommand):

    input_spec = ChangeDataTypeInput
    _suffix = "_chdt"

class ThresholdInputSpec(MathsInput):

    thresh = traits.Float(mandatory=True, position=3, argstr="%s",
                          desc="threshold value")
    direction = traits.Enum("below", "above", usedefault=True,
                            desc="zero-out either below or above thresh value")
    use_robust_range = traits.Bool(desc="inteperet thresh as percentage (0-100) of robust range")
    use_nonzero_voxels = traits.Bool(desc="use nonzero voxels to caluclate robust range",
                                     requires=["use_robust_range"])

class Threshold(MathsCommand):

    input_spec = ThresholdInputSpec
    _suffix = "_thresh"

    def _format_arg(self, name, spec, value):
        if name == "thresh":
            arg = "-"
            _si = self.inputs
            if self.inputs.direction == "above":
                arg += "u"
            arg += "thr"
            if isdefined(_si.use_robust_range) and _si.use_robust_range:
                if isdefined(_si.use_nonzero_voxels) and _si.use_nonzero_voxels:
                    arg += "P"
                else:
                    arg += "p"
            arg += " %.10f"%value
            return arg
        return super(Threshold, self)._format_arg(name,spec,value)

class MeanImageInput(MathsInput):

    dimension = traits.Enum("T","X","Y","Z", usedefault=True, argstr="-%smean", position=3,
                            desc="dimension to mean across")

class MeanImage(MathsCommand):

    input_spec = MeanImageInput
    _suffix = "_mean"

class IsotropicSmoothInput(MathsInput):

    fwhm = traits.Float(mandatory=True,xor=["sigma"],position=3,argstr="-s %.5f",
                        desc="fwhm of smoothing kernel")
    sigma = traits.Float(mandatory=True,xor=["fwhm"],position=3,argstr="-s %.5f",
                         desc="sigma of smoothing kernel")

class IsotropicSmooth(MathsCommand):

    input_spec = IsotropicSmoothInput
    _suffix = "_smooth"

    def _format_arg(self, name, spec, value):
        if name == "fwhm":
            sigma = float(value)/np.sqrt(8 * np.log(2))
            return spec.argstr%sigma
        return super(IsotropicSmooth, self)._format_arg(name, spec, value)

class ApplyMaskInput(MathsInput):

    mask_file = File(exists=True,mandatory=True,argstr="-mas %s", position=3,
                      desc="binary image defining mask space")

class ApplyMask(MathsCommand):

    input_spec = ApplyMaskInput
    _suffix = "_mask"

class MultiImageMaths(MathsCommand):

    pass

class DilateImage(MathsCommand):

    pass

class TemporalFilter(MathsCommand):

    _suffix = "_filt"

class TensorDecomposition(MathsCommand):

    pass
