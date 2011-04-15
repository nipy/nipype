# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

from nose import with_setup
from nipype.testing import (skipif)
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
from nipype.interfaces.fsl import no_fsl, no_fsl_course_data

import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio 
from nipype.testing.utils import setup_test_dir, remove_test_dir
import warnings
import tbss

global test_dir

'''
Parallel computation exec config
'''
pluginName = 'IPython'

@skipif(no_fsl)
@skipif(no_fsl_course_data)
@with_setup(setup_test_dir, remove_test_dir)

def test_tbss_all_pipeline():
    fsl_course_dir = '/path/nipypetutorial_dti_study'
    data_dir = os.path.join(fsl_course_dir,'/fsl_course_data/tbss')
    subject_list = ['1260','1549','1636','1651','2078','2378']
    
    original_all_FA_skeletonised = '/path/tbss_fsl/tbss/stats/all_FA_skeletonised.nii.gz'
    original_mean_FA_skeleton = '/path/tbss_fsl/tbss/stats/mean_FA_skeleton.nii.gz'
    
    def getFAList(subject_list):
        fa_list = []
        for subject_id in subject_list:
            fa_list.append(os.path.join(data_dir,subject_id,'.nii.gz'))
        return fa_list
    tbss_all = tbss.create_tbss_all(name='tbss_all')
    tbss_all.inputs.inputnode.target = fsl.Info.standard_image("FMRIB58_FA_1mm.nii.gz")
    tbss_all.inputs.inputnode.skeleton_thresh = 0.2
    tbss_all.inputs.inputnode.fa.list = getFAList(subject_list)
    
    original_tbss_result = pe.Node(interface = util.IdentityInterface(fields=['all_FA_skeletonised','mean_FA_skeleton']),
                                   name='original_tbss_result')
    original_tbss_result.inputs.all_FA_skeletonised = original_all_FA_skeletonised
    original_tbss_result.inputs.mean_FA_skeleton = original_mean_FA_skeleton
    
    test_all = pe.Node(util.AssertEqual(), name = "tbss_all_test_all")
    test_mean = pe.Node(util.AssertEqual(), name = "tbss_all_test_mean")
      
    pipeline = pe.Workflow(name="test_tbss_all")
    pipeline.base_dir = test_dir
    pipeline.connect([
                        (tbss_all, test_all,[('outputnode.projectedfa_file','inputnode.volume1')]),
                        (original_tbss_result, test_all,[('all_FA_skeletonised','inputnode.volume2')]),
                        (tbss_all, test_mean,[('outputnode.skeleton_file','inputnode.volume1')]),
                        (original_tbss_result, test_mean,[('mean_FA_skeleton','inputnode.volume2')]),
                        ])
    pipeline.run(plugin=pluginName)
