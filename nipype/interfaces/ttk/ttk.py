# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    The gif module provides higher-level interfaces to some of the operations
    that can be performed with the niftyseggif (seg_gif) command-line program.
"""
import os
import numpy as np
from nibabel import load
import os.path as op
import warnings

from nipype.interfaces.ttk.base import TTKCommandInputSpec, TTKCommand
from nipype.interfaces.base import (TraitedSpec, File, Directory, traits, OutputMultiPath,
                                    isdefined)


warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class Tensor2DwiInputSpec(TTKCommandInputSpec):
    
    in_file = File(argstr='-i %s', exists=True, mandatory=True,
                   desc='Input tensor filename')

    in_b0_file = File(argstr='-x %s', exists=True,
                      desc='Input B0 image file')
    
    in_max_value = traits.Float(argstr='-m %s',
                   desc='Maximum B0 value if B0 image not provided')

    in_bval_file = File(argstr='-b %s', exists=True, mandatory=True,
                        desc='Input bval file')

    in_bvec_file = File(argstr='-g %s', exists=True, mandatory=True,
                        desc='Input bvec file')

    in_B0_file = File(argstr='-x %s', exists=True,
                      desc='Input B0 image file')

    out_basename = traits.String(argstr='-o %s',
                                 desc='Output basename to use')
    out_extension = traits.String(argstr='-e %s',
                                  desc='Output extension to use')

class Tensor2DwiOutputSpec(TraitedSpec):

    out_files = OutputMultiPath(desc='Output DWI Image files')

class Tensor2Dwi(TTKCommand):


    """

    """

    _cmd = 'ttk tensors_to_dwis'
    _suffix = '_dwi_'
    input_spec = Tensor2DwiInputSpec  
    output_spec = Tensor2DwiOutputSpec


    def _get_basename_without_extension(self, in_file):
        ret = os.path.basename(in_file)
        if ret.endswith('.nii.gz'):
            ret = ret[:-7]
        if ret.endswith('.nii'):
            ret = ret[:-4]
        return ret
        

    def _gen_output_filenames(self, tensor_file, bval_file):
        gtab = gradients.gradient_table(bval_file)
        b0_list = list(gtab.b0s_mask)
        base = _get_basename_without_extension(tensor_file)
        if isdefined(self.inputs.out_basename):
            base = self.inputs.out_basename
        ext = '.nii.gz'
        if isdefined(self.inputs.out_extension):
            ext = self.inputs.out_extension

        outfilenames = []        
        for i in range(len(b0_list)):
            outfile = base + self._suffix + str(i) + ext
            outfilenames.append(outfile)

        return outfilenames
        

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outfilenames = _gen_output_filenames(self.inputs.in_tensors_file, self.inputs.in_bval_file)
        out_files = []
        for item in outfilenames:
            out_files.append(os.abspath(item))
        outputs['out_files'] = out_files
        return outputs
       
