# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Created on 24 Feb 2010

@author: filo
'''
from nipype.interfaces.base import BaseInterface,\
    traits, TraitedSpec, File, InputMultiPath, OutputMultiPath
from nipype.utils.misc import isdefined
import nibabel as nb
import numpy as np
from math import floor, ceil
from scipy.ndimage.morphology import grey_dilation
import os
from nipype.utils.filemanip import fname_presuffix, split_filename

class PickAtlasInputSpec(TraitedSpec):
    atlas = File(exists=True, desc="Location of the atlas that will be used.", compulsory=True)
    labels = traits.Either(traits.Int, traits.List(traits.Int), 
                           desc="Labels of regions that will be included in the mask. Must be \
compatible with the atlas used.", compulsory=True)
    hemi = traits.Enum('both','left','right', desc="Restrict the mask to only one hemisphere: left or right", usedefault=True)
    dilation_size = traits.Int(desc="Defines how much the mask will be dilated (expanded in 3D).", usedefault = True)
    output_file = File(desc="Where to store the output mask.")

class PickAtlasOutputSpec(TraitedSpec):
    mask_file = File(exists=True, desc="output mask file")

class PickAtlas(BaseInterface):
    '''
    Returns ROI masks given an atlas and a list of labels. Supports dilation
    and left right masking (assuming the atlas is properly aligned).
    '''
    input_spec = PickAtlasInputSpec
    output_spec = PickAtlasOutputSpec

    def _run_interface(self, runtime):
        nim = self._get_brodmann_area()
        nb.save(nim, self._gen_output_filename())

        runtime.returncode = 0
        return runtime

    def _gen_output_filename(self):
        if not isdefined(self.inputs.output_file):
            output = fname_presuffix(fname=self.inputs.atlas, suffix = "_mask",
                                     newpath= os.getcwd(), use_ext = True)
        else:
            output = self.inputs.output_file
        return output
        
    def _get_brodmann_area(self):
        nii = nb.load(self.inputs.atlas)
        origdata = nii.get_data()
        newdata = np.zeros(origdata.shape)
        
        if not isinstance(self.inputs.labels, list):
            labels = [self.inputs.labels]
        else:
            labels = self.inputs.labels
        for label in labels:
            newdata[origdata == label] = 1
        if self.inputs.hemi == 'right':
            newdata[floor(float(origdata.shape[0]) / 2):, :, :] = 0
        elif self.inputs.hemi == 'left':
            newdata[:ceil(float(origdata.shape[0]) / 2), :, : ] = 0

        if self.inputs.dilation_size != 0:
            newdata = grey_dilation(newdata , (2 * self.inputs.dilation_size + 1,
                                               2 * self.inputs.dilation_size + 1,
                                               2 * self.inputs.dilation_size + 1))

        return nb.Nifti1Image(newdata, nii.get_affine(), nii.get_header())

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['mask_file'] = self._gen_output_filename()
        return outputs
    
class SimpleThresholdInputSpec(TraitedSpec):
    volumes = InputMultiPath(File(exists=True), desc='volumes to be thresholded', mandatory=True)
    threshold = traits.Float(desc='volumes to be thresholdedeverything below this value will be set to zero', mandatory=True)
    
    
class SimpleThresholdOutputSpec(TraitedSpec):
    thresholded_volumes = OutputMultiPath(File(exists=True), desc="thresholded volumes")
    

class SimpleThreshold(BaseInterface):
    input_spec = SimpleThresholdInputSpec
    output_spec = SimpleThresholdOutputSpec
    
    def _run_interface(self, runtime):
        for fname in self.inputs.volumes:
            img = nb.load(fname)
            data = np.array(img.get_data())
            
            active_map = data > self.inputs.threshold
            
            thresholded_map = np.zeros(data.shape)
            thresholded_map[active_map] = data[active_map]

            new_img = nb.Nifti1Image(thresholded_map, img.get_affine(), img.get_header())
            _, base, _ = split_filename(fname)
            nb.save(new_img, base + '_thresholded.nii') 
        
        runtime.returncode=0
        return runtime
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["thresholded_volumes"] = []
        for fname in self.inputs.volumes:
            _, base, _ = split_filename(fname)
            outputs["thresholded_volumes"].append(os.path.abspath(base + '_thresholded.nii'))
        return outputs

class ModifyAffineInputSpec(TraitedSpec):
    volumes = InputMultiPath(File(exists=True), desc='volumes which affine matrices will be modified', mandatory=True)
    transformation_matrix = traits.Array(value=np.eye(4), shape=(4,4), desc="transformation matrix that will be left multiplied by the affine matrix", usedefault=True)
    
class ModifyAffineOutputSpec(TraitedSpec):
    transformed_volumes = OutputMultiPath(File(exist=True))
    
class ModifyAffine(BaseInterface):
    '''
    LEft multiplies the affine matrix with a specified values. Saves the volume as a nifti file.
    '''
    input_spec = ModifyAffineInputSpec
    output_spec = ModifyAffineOutputSpec
    
    def _gen_output_filename(self, name):
        _, base, _ = split_filename(name)
        return os.path.abspath(base + "_transformed.nii")
    
    def _run_interface(self, runtime):
        for fname in self.inputs.volumes:
            img = nifti.load(fname)
            
            affine = img.get_affine()
            affine = np.dot(self.inputs.transformation_matrix,affine)

            nifti.save(nifti.Nifti1Image(img.get_data(), affine, img.get_header()), self._gen_output_filename(fname))
            
        runtime.returncode=0
        return runtime
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['transformed_volumes'] = []
        for fname in self.inputs.volumes:
            outputs['transformed_volumes'].append(self._gen_output_filename(fname))
        return outputs