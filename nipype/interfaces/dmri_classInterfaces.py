# -*- coding: utf-8 -*-
"""
Created on Thu May 16 18:43:39 2013

@author: bao
"""

from nipype.interfaces.base import BaseInterface, BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.filemanip import split_filename

from preprocessing import brain_extraction, eddy_correction, resample_voxel_size
from tracking import tensor_model, tracking

from nipype import logging
iflogger = logging.getLogger('interface')

import nibabel as nb
import numpy as np
from sys import stdout
import os

class BrainExtractionInputSpec(BaseInterfaceInputSpec):                                                     
    input_filename = File(exists=True,desc="Nifti file to be processed",mandatory=True)
    output_filename = File(exists=False,desc="Output file name",mandatory=False)
  
class BrainExtractionOutputSpec(TraitedSpec):
    bet_file = File(exists=True ,desc="Output file name")
    

class BrainExtraction(BaseInterface):
    input_spec = BrainExtractionInputSpec
    output_spec = BrainExtractionOutputSpec
    
    def _run_interface(self, runtime):
        self._out_file = brain_extraction(self.inputs.input_filename,self.inputs.output_filename)
        return runtime
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["bet_file"] = os.path.abspath(self._out_file)
        return outputs

###

class EddyCorrectionInputSpec(BaseInterfaceInputSpec):                                                     
    input_filename = File(exists=True,desc="Nifti file to be processed",mandatory=True)
    output_filename = File(exists=False,desc="Output file name",mandatory=False)
  
class EddyCorrectionOutputSpec(TraitedSpec):
    eddy_current_correction_file = File(exists=True ,desc="Output file name")
    

class EddyCorrection(BaseInterface):
    input_spec = EddyCorrectionInputSpec
    output_spec = EddyCorrectionOutputSpec
    
    def _run_interface(self, runtime):
        self._out_file =eddy_correction(self.inputs.input_filename,self.inputs.output_filename)
        return runtime
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["eddy_current_correction_file"] = os.path.abspath(self._out_file)
        return outputs

###

class ResampleVoxelSizeInputSpec(BaseInterfaceInputSpec):                                                     
    input_filename = File(exists=True,desc="Nifti file to be processed",mandatory=True)
    output_filename = File(exists=False,desc="Output file name",mandatory=False)
  
class ResampleVoxelSizeOutputSpec(TraitedSpec):
    resample_file = File(exists=True ,desc="Output file name")
    

class ResampleVoxelSize(BaseInterface):
    input_spec = ResampleVoxelSizeInputSpec
    output_spec = ResampleVoxelSizeOutputSpec
    
    def _run_interface(self, runtime):
        self._out_file = resample_voxel_size(self.inputs.input_filename,self.inputs.output_filename)
        return runtime
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["resample_file"] = os.path.abspath(self._out_file)
        return outputs

###

class TensorModelInputSpec(BaseInterfaceInputSpec):                                                     
    input_filename_data = File(exists=True,desc="Nifti file to be processed",mandatory=True)
    input_filename_bvecs = File(exists=True,desc="bvec file",mandatory=True)
    input_filename_bvals = File(exists=True,desc="bval file",mandatory=True) 
    output_filename_fa = File(exists=False,desc="Output fa file name",mandatory=False)
    output_filename_evecs = File(exists=False,desc="Output evecs file name",mandatory=False)
  
class TensorModelOutputSpec(TraitedSpec):
    tensor_fa_file = File(exists=True ,desc="Output fa file name")
    tensor_evecs_file = File(exists=True ,desc="Output evecs file name")
    

class TensorModel(BaseInterface):
    input_spec = TensorModelInputSpec
    output_spec = TensorModelOutputSpec
    
    def _run_interface(self, runtime):
        (self.fa_file,self.evecs_file)  = tensor_model(self.inputs.input_filename_data, self.inputs.input_filename_bvecs,
                                      self.inputs.input_filename_bvals, self.inputs.output_filename_fa,
                                      self.inputs.output_filename_evecs)
        return runtime
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['tensor_fa_file'] = os.path.abspath(self.fa_file)
        outputs['tensor_evecs_file'] = os.path.abspath(self.evecs_file)
        return outputs

###

class TrackingInputSpec(BaseInterfaceInputSpec):                                                     
    input_filename_fa = File(exists=True,desc="FA file to be processed",mandatory=True)
    input_filename_evecs = File(exists=True,desc="Evecs file to be processed",mandatory=True)
    num_seeds = traits.Long(desc="Num of seeds for initializing the position of tracks",mandatory=False)
    low_thresh = traits.Float(desc="Lower threshold for  FA, typical 0.2 ",mandatory=False)
    output_filename = File(exists=False,desc="Output file name",mandatory=False)
  
class TrackingOutputSpec(TraitedSpec):
    tracks_file = File(exists=True ,desc="Output file name")
    

class Tracking(BaseInterface):
    input_spec = TrackingInputSpec
    output_spec = TrackingOutputSpec
    
    def _run_interface(self, runtime):
        self._out_file = tracking(self.inputs.input_filename_fa, self.inputs.input_filename_evecs,
                                  self.inputs.num_seeds, self.inputs.low_thresh, 
                                  self.inputs.output_filename)
        return runtime
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["tracks_file"] = os.path.abspath(self._out_file)
        return outputs

###