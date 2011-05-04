# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Testing code for test tbss.py

To test the following results:
'fa_list1','mask_list1',
'field_list2',
'groupmask3','skeleton_file3','meanfa_file3','mergefa_file3',
'projectedfa_file4','skeleton_mask4','distance_map4'

"""
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


'''
Parallel computation exec config
'''
pluginName = 'IPython'

@skipif(no_fsl)
#@skipif(no_fsl_course_data)
@with_setup(setup_test_dir, remove_test_dir)

def test_tbss_all_pipeline():
    data_dir = '/nfs/j3/userhome/kongxiangzhen/mywork/test_tbss/mydata'
   # fsl_course_dir = os.getenv('FSL_COURSE_DATA')
   # data_dir = os.path.join(fsl_course_dir,'fsl_course_data/tbss')
   # subject_list = ['1260','1549','1636','1651','2078','2378']
    subject_list = ['S0001','S0005','S0036','S0038','S0085','S0099','S0004','S0032','S0037','S0057','S0098']
    subject_list.sort()
    fsl_tbss_dir = '/nfs/j3/userhome/kongxiangzhen/mywork/test_tbss/tbss_fsl/tbss_mydata/'
    workingdir = '/nfs/j3/userhome/kongxiangzhen/mywork/test_tbss'
    
    
    """
    For Nipype TBSS Workflow
    
    Get a list of all FA.nii.gz for nipype TBSS workflow
    """
    def getFAList(subject_list):
        fa_list = []
        for subject_id in subject_list:
            fa_list.append(os.path.join(data_dir,subject_id+'_FA.nii.gz'))
        return fa_list
    """
    A nipype workflow for TBSS
    """
    tbss_all = tbss.create_tbss_all(name='tbss_all')
    tbss_all.inputs.inputnode.target = fsl.Info.standard_image("FMRIB58_FA_1mm.nii.gz")
    tbss_all.inputs.inputnode.skeleton_thresh = 0.2
    tbss_all.inputs.inputnode.fa_list = getFAList(subject_list)

    
    """
    For FSL_TBSS
    
    Get other FSL_TBSS results
    """
    def getFA_prep_list(subjct_list):
        fa_prep_list = []
        for subject_id in subject_list:
            fa_prep_list.append(os.path.join(fsl_tbss_dir,'FA',subject_id+'_FA_FA.nii.gz'))
        return fa_prep_list
    def getmask_prep_list(subjct_list):
        mask_prep_list = []
        for subject_id in subject_list:
            mask_prep_list.append(os.path.join(fsl_tbss_dir,'FA',subject_id+'_FA_FA_mask.nii.gz'))
        return mask_prep_list
    def getfield_list(subjct_list):
        field_list = []
        for subject_id in subject_list:
            field_list.append(os.path.join(fsl_tbss_dir,'FA',subject_id+'_FA_FA_to_target.mat'))
        return field_list
    t3_all_FA = os.path.join(fsl_tbss_dir,'stats/all_FA.nii.gz')
    t3_mean_FA = os.path.join(fsl_tbss_dir,'stats/mean_FA.nii.gz')
    t3_groupmask = os.path.join(fsl_tbss_dir,'stats/mean_FA_mask.nii.gz')
    t3_skeleton_file = os.path.join(fsl_tbss_dir,'stats/mean_FA_skeleton.nii.gz')
    t4_all_FA_skeletonised = os.path.join(fsl_tbss_dir,'stats/all_FA_skeletonised.nii.gz')
    t4_mean_FA_skeleton_mask = os.path.join(fsl_tbss_dir,'stats/mean_FA_skeleton_mask.nii.gz')
    t4_mean_FA_skeleton_mask_dst = os.path.join(fsl_tbss_dir,'stats/mean_FA_skeleton_mask_dst.nii.gz')
    
    """
    """
    merge_fa_list = pe.Node(fsl.Merge(dimension="t", merged_file="all_fa.nii.gz"), name="merge_fa_list")
    merge_mask_list = pe.Node(fsl.Merge(dimension="t", merged_file="all_mask.nii.gz"), name="merge_mask_list")
    
    """
    The Test Nodes
    
    Check outputs of tbss1
    """
    FA_prep = pe.Node(util.AssertEqual(ignore_exception = False), name = "FA_prep")
    merge_FA_prep = pe.Node(fsl.Merge(dimension="t", merged_file="all_FA_prep.nii.gz"), name="merge_FA_prep")
    merge_FA_prep.inputs.in_files = getFA_prep_list(subject_list)
    #FA_prep = pe.MapNode(util.AssertEqual(ignore_exception = True), name = "FA_prep", iterfield=['volume1','volume2'])
    #FA_prep.inputs.volume2 = getFA_prep_list(subject_list)
    mask_prep = pe.Node(util.AssertEqual(), name = "mask_prep")
    merge_mask_prep = pe.Node(fsl.Merge(dimension="t", merged_file="all_mask_prep.nii.gz"), name="merge_mask_prep")
    merge_mask_prep.inputs.in_files = getmask_prep_list(subject_list)
    #mask_prep = pe.MapNode(util.AssertEqual(), name = "mask_prep", iterfield=['volume1','volume2'])
    #mask_prep.inputs.volume2 = getmask_prep_list(subject_list)
    
    """
    Check outputs of tbss2
    """
    #field = pe.MapNode(util.AssertEqual(), name = "field", iterfield=['volume1','volume2'])
    #field.inputs.volume2 = getfield_list(subject_list)
    
    """
    Check outputs of tbss3
    """
    all_FA = pe.Node(util.AssertEqual(ignore_exception = False), name = "all_FA")
    all_FA.inputs.volume2 = t3_all_FA
    mean_FA = pe.Node(util.AssertEqual(ignore_exception = False), name = "mean_FA") # right
    mean_FA.inputs.volume2 = t3_mean_FA
    groupmask = pe.Node(util.AssertEqual(ignore_exception = False), name = "groupmask")
    groupmask.inputs.volume2 = t3_groupmask
    skeleton_file = pe.Node(util.AssertEqual(ignore_exception = False), name = "skeleton_file")
    skeleton_file.inputs.volume2 = t3_skeleton_file
    
    """
    Check outputs of tbss4
    """    
    all_FA_skeletonised = pe.Node(util.AssertEqual(ignore_exception = False), name = "all_FA_skeletonised")
    all_FA_skeletonised.inputs.volume2 = t4_all_FA_skeletonised
    mean_FA_skeleton_mask = pe.Node(util.AssertEqual(ignore_exception = False), name = "mean_FA_skeleton_mask")
    mean_FA_skeleton_mask.inputs.volume2 = t4_mean_FA_skeleton_mask
    mean_FA_skeleton_mask_dst = pe.Node(util.AssertEqual(ignore_exception = False), name = "mean_FA_skeleton_mask_dst")
    mean_FA_skeleton_mask_dst.inputs.volume2 = t4_mean_FA_skeleton_mask_dst
    
    cmp_nipy2fsl = pe.Workflow(name="cmp_nipy2fsl")
    cmp_nipy2fsl.base_dir = workingdir
    cmp_nipy2fsl.connect([
                        (tbss_all,merge_fa_list,[('outputall_node.fa_list1','in_files')]),#OK
                        (merge_fa_list,FA_prep,[('merged_file','volume1')]),
                        (merge_FA_prep,FA_prep,[('merged_file','volume2')]),
                    #    (tbss_all,FA_prep,[('outputall_node.fa_list1','volume1')]),
                        (tbss_all,merge_mask_list,[('outputall_node.mask_list1','in_files')]),#OK
                        (merge_mask_list,mask_prep,[('merged_file','volume1')]),
                        (merge_mask_prep,mask_prep,[('merged_file','volume2')]),
                    #    (tbss_all,mask_prep,[('outputall_node.mask_list1','volume1')]),
                       
                    #    (tbss_all,field,[('outputall_node.field_list2','volume1')]),
                        
                        (tbss_all, all_FA,[('outputall_node.mergefa_file3','volume1')]),#OK
                        (tbss_all, mean_FA,[('outputall_node.meanfa_file3','volume1')]),#OK
                        (tbss_all, groupmask,[('outputall_node.groupmask3','volume1')]),#OK
                        (tbss_all, skeleton_file,[('outputall_node.skeleton_file3','volume1')]),#OK
                        
                        (tbss_all, all_FA_skeletonised,[('outputall_node.projectedfa_file4','volume1')]),#OK
                        (tbss_all, mean_FA_skeleton_mask,[('outputall_node.skeleton_mask4','volume1')]),#OK
                        (tbss_all, mean_FA_skeleton_mask_dst,[('outputall_node.distance_map4','volume1')]),#OK
                        ])

    cmp_nipy2fsl.run(plugin=pluginName)
