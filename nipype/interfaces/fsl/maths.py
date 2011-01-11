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

from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec
from nipype.interfaces.base import TraitedSpec, File, traits
from nipype.utils.filemanip import fname_presuffix
from nipype.utils.misc import isdefined


class MathsInput(FSLCommandInputSpec):
    
    in_file = File(position=2, argstr="%s", desc="image to operate on")
    internal_datatype = traits.Enum("float","char","int","short","double","input",
                                    position=1, argstr="%s",
                                    desc="datatype to use for calculations (default is float)")
    output_datatype = traits.Enum("float","char","int","short","double","input",
                                    position=-1, argstr="%s",
                                    desc="datatype to use for output (default uses input type)")
    out_file = File(genfile=True, position=-2, desc="image to write")

class MathsOutput(TraitedSpec):

    out_file = File(exists=True, desc="image written after calculations")

class MathsCommand(FSLCommand):

    _cmd = "fslmaths"
    output_spec = MathsOutput
    _suffix = "_maths"

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None

class ChangeDataType(MathsCommand):

    input_spec = MathsInput
    _suffix = "_chdt"

class ThresholdInputSpec(MathsInput):

    thresh = traits.Float(desc="threshold value")
    direction = traits.Enum("below", "above", use_default=True, default_value="below",
                            desc="zero-out either below or above thresh value")
    use_robust_range = traits.Bool(desc="inteperet thresh as percentage (0-100) of robust range")
    use_nonzero_voxels = traits.Bool(desc="use nonzero voxels to caluclate robust range")

class Threshold(MathsCommand):

    input_spec = ThresholdInputSpec
    _suffix = "_thresh"

class MeanImageInput(MathsInput):

    dimension = traits.Enum("T","X","Y","Z", use_default=True, default_value="T",
                            desc="dimension to mean across")

class MeanImage(MathsCommand):

    input_spec = MeanImageInput
    _suffix = "_mean"

class ApplyMaskInput(MathsInput):

    mask_image = File(exists=True,required=True,argstr="-mas %s", position=3,
                      desc="binary image defining mask space")

class ApplyMask(MathsCommand):

    input_spec = ApplyMaskInput
    _suffix = "_mask"

class IsotropicSmooth(MathsCommand):

    pass

class TemporalFilter(MathsCommand):

    _suffix = "_filt"

class TensorDecomposition(MathsCommand):

    pass
