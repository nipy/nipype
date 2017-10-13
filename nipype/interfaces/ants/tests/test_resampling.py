# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:                                                                                                                 

from nipype.interfaces.ants import WarpImageMultiTransform, WarpTimeSeriesImageMultiTransform
import os
import pytest, pdb


@pytest.fixture()
def change_dir(request):
   orig_dir = os.getcwd()
   filepath = os.path.dirname( os.path.realpath( __file__ ) )
   datadir = os.path.realpath(os.path.join(filepath, '../../../testing/data'))
   os.chdir(datadir)

   def move2orig():
      os.chdir(orig_dir)

   request.addfinalizer(move2orig)



def test_WarpImageMultiTransform(change_dir):
   wimt = WarpImageMultiTransform()
   wimt.inputs.input_image = 'diffusion_weighted.nii'
   wimt.inputs.reference_image = 'functional.nii'
   wimt.inputs.transformation_series = ['func2anat_coreg_Affine.txt','func2anat_InverseWarp.nii.gz', \
                                           'dwi2anat_Warp.nii.gz','dwi2anat_coreg_Affine.txt']
   assert wimt.cmdline == 'WarpImageMultiTransform 3 diffusion_weighted.nii diffusion_weighted_wimt.nii -R functional.nii \
func2anat_coreg_Affine.txt func2anat_InverseWarp.nii.gz dwi2anat_Warp.nii.gz dwi2anat_coreg_Affine.txt'


def test_WarpImageMultiTransform_invaffine_1(change_dir):
   wimt = WarpImageMultiTransform() 
   wimt.inputs.input_image = 'diffusion_weighted.nii'
   wimt.inputs.reference_image = 'functional.nii'
   wimt.inputs.transformation_series = ['func2anat_coreg_Affine.txt','func2anat_InverseWarp.nii.gz', \
                                           'dwi2anat_Warp.nii.gz','dwi2anat_coreg_Affine.txt']  
   wimt.inputs.invert_affine = [1]
   assert wimt.cmdline == 'WarpImageMultiTransform 3 diffusion_weighted.nii diffusion_weighted_wimt.nii -R functional.nii \
-i func2anat_coreg_Affine.txt func2anat_InverseWarp.nii.gz dwi2anat_Warp.nii.gz dwi2anat_coreg_Affine.txt'


def test_WarpImageMultiTransform_invaffine_2(change_dir):
   wimt = WarpImageMultiTransform()
   wimt.inputs.input_image = 'diffusion_weighted.nii'
   wimt.inputs.reference_image = 'functional.nii'
   wimt.inputs.transformation_series = ['func2anat_coreg_Affine.txt','func2anat_InverseWarp.nii.gz', \
                                           'dwi2anat_Warp.nii.gz','dwi2anat_coreg_Affine.txt']
   wimt.inputs.invert_affine = [2]
   assert wimt.cmdline == 'WarpImageMultiTransform 3 diffusion_weighted.nii diffusion_weighted_wimt.nii -R functional.nii func2anat_coreg_Affine.txt func2anat_InverseWarp.nii.gz dwi2anat_Warp.nii.gz -i dwi2anat_coreg_Affine.txt'


@pytest.mark.xfail(reason="dj: should it fail?")
def test_WarpImageMultiTransform_invaffine_wrong(change_dir):
   wimt = WarpImageMultiTransform()
   wimt.inputs.input_image = 'diffusion_weighted.nii'
   wimt.inputs.reference_image = 'functional.nii'
   wimt.inputs.transformation_series = ['func2anat_coreg_Affine.txt','func2anat_InverseWarp.nii.gz', \
                                           'dwi2anat_Warp.nii.gz','dwi2anat_coreg_Affine.txt']
   wimt.inputs.invert_affine = [3]
   with pytest.raises(Exception):
      assert wimt.cmdline


def test_WarpTimeSeriesImageMultiTransform(change_dir):
   wtsimt = WarpTimeSeriesImageMultiTransform()                                                        
   wtsimt.inputs.input_image = 'resting.nii'                                                           
   wtsimt.inputs.reference_image = 'ants_deformed.nii.gz'                                              
   wtsimt.inputs.transformation_series = ['ants_Warp.nii.gz','ants_Affine.txt']
   assert wtsimt.cmdline == 'WarpTimeSeriesImageMultiTransform 4 resting.nii resting_wtsimt.nii \
-R ants_deformed.nii.gz ants_Warp.nii.gz ants_Affine.txt'                                                                                            


def test_WarpTimeSeriesImageMultiTransform_invaffine(change_dir):
   wtsimt = WarpTimeSeriesImageMultiTransform()
   wtsimt.inputs.input_image = 'resting.nii'
   wtsimt.inputs.reference_image = 'ants_deformed.nii.gz'
   wtsimt.inputs.transformation_series = ['ants_Warp.nii.gz','ants_Affine.txt']
   wtsimt.inputs.invert_affine = [1]
   assert wtsimt.cmdline == 'WarpTimeSeriesImageMultiTransform 4 resting.nii resting_wtsimt.nii \
-R ants_deformed.nii.gz ants_Warp.nii.gz -i ants_Affine.txt'


@pytest.mark.xfail(reason="dj: should it fail?")
def test_WarpTimeSeriesImageMultiTransform_invaffine_wrong(change_dir):
   wtsimt = WarpTimeSeriesImageMultiTransform()
   wtsimt.inputs.input_image = 'resting.nii'
   wtsimt.inputs.reference_image = 'ants_deformed.nii.gz'
   wtsimt.inputs.transformation_series = ['ants_Warp.nii.gz','ants_Affine.txt']
   wtsimt.inputs.invert_affine = [0]
   with pytest.raises(Exception):
      wtsimt.cmdline
