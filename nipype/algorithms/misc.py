'''
Created on 24 Feb 2010

@author: filo
'''
from nipype.interfaces.base import BaseInterface,\
    traits, TraitedSpec, File
from nipype.utils.misc import isdefined
import nipype.externals.pynifti as nifti
import numpy as np
from math import floor, ceil
from scipy.ndimage.morphology import grey_dilation
from copy import deepcopy
import os
from nipype.utils.filemanip import fname_presuffix

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
        nifti.save(nim, self._gen_output_filename())

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
        nii = nifti.load(self.inputs.atlas)
        origdata = nii.get_data()
        newdata = np.zeros(origdata.shape)
        
        if not isinstance(self.inputs.labels, list):
            labels = [self.inputs.labels]
        else:
            labels = self.inputs.labels
        for label in labels:
            newdata[origdata == label] = 1
        if self.inputs.hemi == 'left':
            newdata[floor(float(origdata.shape[0]) / 2):, :, :] = 0
        elif self.inputs.hemi == 'right':
            newdata[:ceil(float(origdata.shape[0]) / 2), :, : ] = 0

        if self.inputs.dilation_size != 0:
            newdata = grey_dilation(newdata , (2 * self.inputs.dilation_size + 1,
                                               2 * self.inputs.dilation_size + 1,
                                               2 * self.inputs.dilation_size + 1))

        return nifti.Nifti1Image(newdata, nii.get_affine(), nii.get_header())

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['mask_file'] = self._gen_output_filename()
        return outputs
