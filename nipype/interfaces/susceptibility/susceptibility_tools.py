# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    The maths module provides higher-level interfaces to some of the operations
    that can be performed with the niftysegmaths (seg_maths) command-line program.
"""
import os
import numpy as np
from nipype.interfaces.base import traits
from traits.api import Enum, HasTraits, Str
from nipype.interfaces.niftyseg.base import  NIFTYSEGCommandInputSpec as SusceptibilityToolsCommandInputSpec
#from nipype.interfaces.niftyseg.base import NIFTYSEGCommand as SusceptibilityToolsCommand
from nipype.interfaces.fsl.base import FSLCommand as SusceptibilityToolsCommand
from nipype.interfaces.base import (TraitedSpec, File, traits, InputMultiPath,
                                    isdefined)

# A custom trait class for positive float values
class PositiveFloat (traits.BaseFloat):
    # Define the default value
    default_value = 1.0
    # Describe the trait type
    info_text = 'A positive float'
    
    def validate ( self, object, name, value ):
        #value = super(OddInt, self).validate(object, name, value)
        if (value >= 0.0) == 1:
            return value
        self.error( object, name, value )


class PmScaleInput(SusceptibilityToolsCommandInputSpec):
    in_pm = File(argstr="-i %s", exists=True, mandatory=True, desc="Original phase image")
    out_pm = File(genfile = True,argstr="-o %s", exists=False, desc="Scaled phase image")

class PmScaleOutput(TraitedSpec):
    out_pm = File(exists=True, desc="Scaled phase image written after calculations")

class PmScale(SusceptibilityToolsCommand):
    _cmd = "pm_scale"
    input_spec = PmScaleInput
    output_spec = PmScaleOutput
    
    def _gen_filename(self, name):
        if name == 'out_pm':
            return self._gen_fname(self.inputs.in_pm,
                                       suffix='_scaled')
        return None
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_pm): 
            outputs['out_pm'] = self.inputs.out_pm
        else:
            outputs['out_pm'] = self._gen_filename('out_pm')
        
        return outputs


#phase_unwrap -p $fmScale -m $fmBetMask -a $fmMag -o $fmUnwrap
class PhaseUnwrapInput(SusceptibilityToolsCommandInputSpec):
    in_fm = File(argstr="-p %s", exists=True, mandatory=True, desc="Scaled field map image")
    in_mask = File(argstr="-m %s", exists=True, mandatory=True, desc="Mask of fieldmap image")
    in_mag = File(argstr="-a %s", exists=True, mandatory=True, desc="Fieldmap magnitude image")
    out_fm = File(genfile = True, argstr="-o %s", exists=False, desc="Unwrapped  field map image")

class PhaseUnwrapOutput(TraitedSpec):
    out_fm = File(exists=True, desc="Unrwapped phase image written after calculation")

class PhaseUnwrap(SusceptibilityToolsCommand):
    
    _cmd = "phase_unwrap"
    input_spec = PhaseUnwrapInput
    output_spec = PhaseUnwrapOutput
    
    def _gen_filename(self, name):
        if name == 'out_fm':
            return self._gen_fname(self.inputs.in_fm,
                                       suffix='_unwrapped')
        return None
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        
        if isdefined(self.inputs.out_fm): 
            outputs['out_fm'] = self.inputs.out_fm
        else:
            outputs['out_fm'] = self._gen_filename('out_fm')
        
        return outputs

#gen_fm -p $fmUnwrap -m $fmBetMask -etd $epiparams->{ETD} "."-rot $epiparams->{ROT} -ped $epiparams->{PED} "	"-defo $fmDef -fmo $fmFm";
class GenFmInput(SusceptibilityToolsCommandInputSpec):
    #Input the EPI image
    in_epi = File(argstr="-e %s", exists=True, mandatory=True,
                desc="EPI image")
    #Input the unwrapped field map image
    in_ufm = File(argstr="-p %s", exists=True, mandatory=True,
                desc="Unwrapped field map image")
    # Input the echo time difference used to create the phase image as a positive float
    in_etd  = traits.Float(argstr="-etd %f", mandatory=True, desc="Echo time difference")
    
    # Mask image
    in_mask = File(argstr="-m %s", exists=True, mandatory=True,
                   desc="Brain mask image")
                   
    # Input the read out time as a positive float
    in_rot =  traits.Float(argstr="-rot %f", mandatory=True, desc="Read out time (taking into account any acceleration factors)")
    
    # Input the phase encode direction as an enum of the possible axes
    _directions = ["x", "-x", "y", "-y", "z", "-z"]
    in_ped = traits.Enum(*_directions, argstr="-ped %s", desc="phase encoding direction of the EPI sequence", mandatory=True)
    
    # Output the deformation field
    out_field = File(genfile=True, argstr="-defo %s", desc="output deformation field", hash_files=False, exists=False)
    
    #Output the final field map image
    out_fm = File(genfile=True, argstr="-fmo %s", desc="field map output file", hash_files=False, exists=False)


class GenFmOutput(TraitedSpec):
    out_field = File(exists=True, desc="field map image written after calculations")
    out_fm = File(exists=True, desc="field map output file")


class GenFm(SusceptibilityToolsCommand):
    _cmd = "gen_fm"
    input_spec = GenFmInput
    output_spec = GenFmOutput

    def _gen_filename(self, name):
        if name == 'out_field':
            return self._gen_fname(self.inputs.in_ufm,
                                       suffix='_field')
                                       
        if name == 'out_fm':
            return self._gen_fname(self.inputs.in_ufm,
                                       suffix='_out_fm')
        return None
        
    # Returns a dictionary containing names of generated files that are expected
    # after gen_fm completes execution
    def _list_outputs(self):
        outputs = self.output_spec().get()
        # If the output field is defined with non-zero value, it's an output
        if isdefined(self.inputs.out_fm): 
            outputs['out_fm'] = self.inputs.out_fm
        else:
            outputs['out_fm'] = self._gen_filename('out_fm')
        
        if isdefined(self.inputs.out_field): 
            outputs['out_field'] = self.inputs.out_field
        else:
            outputs['out_field'] = self._gen_filename('out_field')
            
        return outputs



