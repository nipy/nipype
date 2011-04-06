# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import warnings

import numpy as np

from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec
from nipype.interfaces.base import (TraitedSpec, File, InputMultiPath,
                                    OutputMultiPath, Undefined, traits)
from nipype.utils.filemanip import split_filename
from nipype.utils.misc import isdefined

from nibabel import load


warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class FslPspecInputSpec(FSLCommandInputSpec):
    """"""
    # We use position args here as list indices - so a negative number
    # will put something on the end
    in_file = File(exists=True,
                  desc="input 4D file to estimate the power spectrum",
                  argstr='%s', position=0, mandatory=True)
    out_file = File(desc = 'name of output 4D file for power spectrum',
                   argstr='%s', position=1, genfile=True)
    

class FslPspecOutputSpec(TraitedSpec):
    out_file = File(desc="path/name of the output 4D power spectrum file")

class FslPspec(FSLCommand):
    """Use FSL FslPspec command for power spectrum estimation.

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import  example_data
    >>> pspec = fsl.FslPspec()
    >>> pspec.inputs.in_file = example_data('functional.nii')
    >>> res = pspec.run() # doctest: +SKIP

    """

    _cmd = 'fslpspec'
    input_spec = FslPspecInputSpec
    output_spec = FslPspecOutputSpec

    def _gen_outfilename(self):
        out_file = self.inputs.out_file
        if not isdefined(out_file) and isdefined(self.inputs.in_file):
            out_file = self._gen_fname(self.inputs.in_file,
                                       suffix = '_ps')
        return out_file

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self._gen_outfilename()
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._gen_outfilename()
        return None
