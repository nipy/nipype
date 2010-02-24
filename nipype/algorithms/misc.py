'''
Created on 24 Feb 2010

@author: filo
'''
from nipype.interfaces.base import Interface, Bunch, InterfaceResult
import nipype.externals.pynifti as nifti
import numpy as np
from math import floor, ceil
from scipy.ndimage.morphology import grey_dilation
from copy import deepcopy
import os
from nipype.utils.filemanip import fname_presuffix

class PickAtlas(Interface):
    '''
    Returns ROI masks given an atlas and a list of labels. Supports dilation
    and left right masking (assuming the atlas is properly aligned).
    '''
    
    def __init__(self, *args, **inputs):
        self.inputs = Bunch(atlas=None,
                            labels=None,
                            hemi='both',
                            dilation_size=0,
                            output_file=None)
        self.inputs.update(**inputs)
        
        def inputs_help(self):
            """
            Parameters
            ----------
            atlas : filename string
                Location of the atlas that will be used.
            labels : int or list of ints
                Labels of regions that will be included in the mask. Must be
                compatible with the atlas used.
            hemi : string 'both', 'left' or 'right'
                Restrict the mask to only one hemisphere. Optional.
            dilation_size : int
                Defines how much the mask will be dilated (expanded in 3D). Optional.
            output_file : string
                Where to store the output mask. Optional.
            """
            print self.inputs_help.__doc__

    def run(self, cwd=None):
        nim = self._get_brodmann_area()
        nifti.save(nim, self._gen_output_filename())

        runtime = Bunch(returncode=0,
                        messages=None,
                        errmessages=None)
        outputs = self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)

    def _gen_output_filename(self):
        if self.inputs.output_file is None:
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

    def outputs(self):
        return Bunch(mask_file=None)

    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.mask_file = self._gen_output_filename()
        return outputs
