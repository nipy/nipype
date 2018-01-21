# -*- coding: utf-8 -*-
"""
Created on Thu May 16 14:00:54 2013

@author: bao
Create and save the tractography from the iso-data (size of voxel must be isotrophy)

"""
import os

import nibabel as nib
import numpy as np

from dipy.io.dpy import Dpy
from dipy.io.gradients import read_bvals_bvecs
from dipy.data import get_sphere
from dipy.reconst.dti import quantize_evecs
from dipy.reconst.dti import TensorModel
from dipy.reconst.dti import fractional_anisotropy
from dipy.core.gradients import gradient_table
from dipy.tracking.eudx import EuDX



'''
Create the Tensor Model for data
input:  data file name, bvecs file name and bvals file name
output: tensor_fa and tensor_evecs
'''
def tensor_model(input_filename_data, input_filename_bvecs, input_filename_bvals, output_filename_fa=None, output_filename_evecs=None):
    
    print 'Tensor model ...'
    
    print 'Loading data ...'    
    img = nib.load(input_filename_data)
    data = img.get_data()
    affine = img.get_affine()
    
    bvals, bvecs = read_bvals_bvecs(input_filename_bvals, input_filename_bvecs)
    gtab = gradient_table(bvals, bvecs)
    
    mask = data[..., 0] > 50
    tenmodel = TensorModel(gtab)
    tenfit = tenmodel.fit(data, mask)
    
    FA = fractional_anisotropy(tenfit.evals)
    FA[np.isnan(FA)] = 0
    
    if output_filename_fa == None:
        filename_save_fa = input_filename_data.split('.')[0]+'_tensor_fa.nii.gz'
    else:
        filename_save_fa = os.path.abspath(output_filename_fa)    
    
    fa_img = nib.Nifti1Image(FA, img.get_affine())
    nib.save(fa_img, filename_save_fa)    
    print "Saving fa to:", filename_save_fa   
    
    if output_filename_evecs == None:
        filename_save_evecs = input_filename_data.split('.')[0]+'_tensor_evecs.nii.gz'
    else:
        filename_save_evecs = os.path.abspath(output_filename_evecs) 
    
    evecs_img = nib.Nifti1Image(tenfit.evecs, img.get_affine())
    nib.save(evecs_img, filename_save_evecs)
    print "Saving evecs to:", filename_save_evecs
    
    return filename_save_fa,filename_save_evecs
    

def create_tracks(anisotropy, indices, vertices , seeds, low_thresh):
    
    eu = EuDX(anisotropy, indices, odf_vertices = vertices, seeds = seeds, a_low=low_thresh)
    print eu.seed_no    
    #stop
    tensor_tracks_old = [streamline for streamline in eu]
    print len(tensor_tracks_old)
        
    #remove one point tracks
    tracks = [track for track in tensor_tracks_old if track.shape[0]>1]    
    
    return tracks

'''
Tracking to reconstruct the tractography
input:  tensor_fa and tensor_evecs file name
        num of seeds        
output: tractography file name
'''
def tracking(input_filename_fa, input_filename_evecs, num_seeds=10000, low_thresh = .2, output_filename=None):
    
    print 'Tracking ...'
    
    print 'Loading data ...'    
    
    fa_img = nib.load(input_filename_fa)
    FA = fa_img.get_data()
    
    evecs_img = nib.load(input_filename_evecs)
    evecs = evecs_img.get_data()
    
    FA[np.isnan(FA)] = 0    
    
    sphere = get_sphere('symmetric724')    
    peak_indices = quantize_evecs(evecs, sphere.vertices)        

    eu = EuDX(FA, peak_indices, seeds = num_seeds, odf_vertices = sphere.vertices,  a_low=low_thresh)

    tensor_tracks_old = [streamline for streamline in eu]   
        
    #remove one point tracks
    tracks = [track for track in tensor_tracks_old if track.shape[0]>1]     
    #tracks =  create_tracks(FA, peak_indices,sphere.vertices, num_seeds, low_thresh)  
    
    if output_filename == None:
        filename_save = 'tracks_dti.dpy'
    else:
        filename_save = os.path.abspath(output_filename) 
       
    print 'Saving tracks to:', filename_save 
    dpw = Dpy(filename_save, 'w')
    dpw.write_tracks(tracks)
    dpw.close()
    
    return filename_save

    
      
    
    
