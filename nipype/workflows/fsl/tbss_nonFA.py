# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import nibabel as nib
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.fsl as fsl
import nipype.interfaces.io as nio

def create_tbss_non_FA(name='tbss_non_FA'):
    """
    A pipeline that implemet tbss_non_FA in FSL
    
    Example
    --------
    
    >>>tbss_nonFA = tbss.create_tbss_all('tbss')
    >>>tbss_nonFA.base_dir = os.path.abspath(workingdir)
    >>>tbss_nonFA.inputnode.file_list = []
    >>>tbss_nonFA.inputnode.target = fsl.Info.standard_image("FMRIB58_FA_1mm.nii.gz")
    >>>tbss_nonFA.inputnode.field_list = []
    >>>tbss_nonFA.inputnode.skeleton_thresh = 0.2
    >>>tbss_nonFA.inputnode.mean_FA_mask = './xxx'
    >>>tbss_nonFA.inputnode.meanfa_file = './xxx'
    >>>tbss_nonFA.inputnode.distance_map = []
    
    Inputs::
    
        inputnode.file_list
        inputnode.target
        inputnode.field_list
        inputnode.skeleton_thresh
        inputnode.merged_file
        inputnode.mean_FA_mask
        inputnode.meanfa_file
        inputnode.distance_map
    
    Outputs::
        outputnode.projected_nonFA_file
        
    """

    # Define the inputnode
    inputnode = pe.Node(interface=util.IdentityInterface(fields=['file_list',
                                                                'target',
                                                                'field_list',
                                                                'skeleton_thresh',
                                                                'merged_file',
                                                                'mean_FA_mask',
                                                                'meanfa_file',
                                                                'distance_map']),
                        name='inputnode')
    
    # Apply the warpfield to the non FA image
    applywarp = pe.MapNode(interface=fsl.ApplyWarp(),
                            iterfield=['in_file','field_file'],
                            name="applywarp")
    # Merge the non FA files into a 4D file
    merge = pe.Node(fsl.Merge(dimension="t"), name="merge")
    #merged_file="all_FA.nii.gz"
    maskgroup = pe.Node(fsl.ImageMaths(op_string="-mas",
                                       suffix="_masked"),
                        name="maskgroup")
    projectfa = pe.Node(fsl.TractSkeleton(project_data=True,
                                        #projected_data = 'test.nii.gz',
                                        use_cingulum_mask=True
                                      ),
                        name="projectfa")
    
    tbss_nonFA = pe.Workflow(name="tbss_nonFA")
    tbss_nonFA.connect([
                    (inputnode, applywarp,[('file_list','in_file'),
                                            ('target','ref_file'),
                                            ('field_list','field_file'),
                                            ]),
                    (inputnode, merge, [('merged_file','merged_file'),]),
                    (applywarp, merge,[("out_file", "in_files")]),
                        
                    (merge, maskgroup, [("merged_file", "in_file")]),
                        
                    (inputnode, maskgroup, [('mean_FA_mask', 'in_file2')]),
                        
                    (maskgroup, projectfa,[('out_file','data_file')]),
                    (inputnode, projectfa,[('skeleton_thresh','threshold'),
                                            ("meanfa_file", "in_file"),
                                            ("distance_map", "distance_map"),
                                            ]),
                ])
    
    # Define the outputnode
    outputnode = pe.Node(interface=util.IdentityInterface(
                                            fields=['projected_nonFA_file']),
                         name='outputnode')
    tbss_nonFA.connect([
            (projectfa, outputnode,[('projected_data','projected_nonFA_file'),
                                    ]),
            ])
    return tbss_nonFA
