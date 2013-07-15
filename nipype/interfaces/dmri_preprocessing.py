# -*- coding: utf-8 -*-
"""
Created on Thu May 16 13:23:24 2013

@author: bao
Pre-processing dMRI data, including 03 steps
1. Brain extraction
2. Eddy current correction
3. Resample data to isotrophy, usually to voxel size (2.,2.,2.)
"""
import os

import nibabel as nib
from dipy.external.fsl import bet, eddy_correct
from dipy.align.aniso2iso import resample



def brain_extraction(input_filename, output_filename=None):
    
    print 'Brain extraction ...'
    
    if output_filename == None:
        filename_save = input_filename.split('.')[0]+'_bet.nii.gz'
    else:
        filename_save = os.path.abspath(output_filename)
    
    bet(input_filename, filename_save,options=' -R -F -f .2 -g 0')
    
    print "Saving to:", filename_save    
    
    return filename_save
    
def eddy_correction(input_filename, output_filename=None): 
    
    print 'Eddy current correction ...'
    
    if output_filename == None:
        filename_save = input_filename.split('.')[0]+'_ecc.nii.gz'
    else:
        filename_save = os.path.abspath(output_filename)
        
    eddy_correct(input_filename,filename_save)
    
    print "Saving to:", filename_save    
    
    return filename_save
    
def resample_voxel_size(input_filename, output_filename=None): 
    
    print("Loading data: %s" % input_filename)
    img = nib.load(input_filename)

    old_data = img.get_data()
    old_affine = img.get_affine()
    
    zooms=img.get_header().get_zooms()[:3]
    print 'Old zooms:', zooms
    new_zooms=(2.,2.,2.)
    print 'New zoom', new_zooms  
    
    print 'Resample data and affine ...'      
    data,affine=resample(old_data,old_affine,zooms,new_zooms)
    
    if output_filename == None:
        filename_save = input_filename.split('.')[0]+'_iso.nii.gz'
    else:
        filename_save = os.path.abspath(output_filename)       

    print "Saving data after resapling to ", filename_save
    data_img = nib.Nifti1Image(data=data, affine=affine)
    nib.save(data_img, filename_save)
    
    return filename_save
        
        
    
    