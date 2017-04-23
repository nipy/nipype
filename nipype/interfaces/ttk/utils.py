# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    TTK-UTILS command-line program.
"""

import os
from nipype.interfaces.ttk.base import TTKCommandInputSpec, TTKCommand
from nipype.interfaces.base import (TraitedSpec, File, traits)

class TensorLogInputSpec(TTKCommandInputSpec):
    
    in_file = File(argstr='%s', 
                   exists=True, 
                   mandatory=True,
                   desc='Input tensor filename',
                   position = 0)
    
    out_file = File(argstr='%s',
                    desc='Output tensor filename',
                    name_source = ['in_file'], 
                    name_template = '%s_log',
                    position = 1)
    
    use_fsl_style = traits.Int(argstr='%d',
                               desc = 'Use 4D nifti format for writing (vs. 5D)', 
                               position = 2)

class TensorLogOutputSpec(TraitedSpec):

    out_file = File(desc='Output tensor file',
                    exists = True)

class TensorLog(TTKCommand):

    _cmd = 'ttk-utils log'
    input_spec = TensorLogInputSpec  
    output_spec = TensorLogOutputSpec
