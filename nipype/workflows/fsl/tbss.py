# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import nibabel as nib
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.fsl as fsl
import nipype.interfaces.io as nio

def tbss1_op_string(in_files):
    import nibabel as nib
    op_strings = []
    for infile in in_files:
        img = nib.load(infile)
        dimtup = tuple([d-2 for d in img.get_shape()])
        op_str = '-min 1 -ero -roi 1 %d 1 %d 1 %d 0 1'%dimtup
        op_strings.append(op_str)
    return op_strings

def create_tbss_1_preproc(name='tbss_1_preproc'):
    """Preprocess FA data for TBSS: erodes a little and zero end slicers and 
    creates masks(for use in FLIRT & FNIRT from FSL).
    A pipeline that does the same as tbss_1_preproc script in FSL
    
    Example
    --------
    
    >>>tbss1 = tbss.create_tbss_1_preproc(name='tbss1')
    >>>tbss1.run()
    
    Inputs::
    
        inputnode.fa_list
    
    Outputs::
    
        outputnode.fa_list
        outputnode.mask_list

    """
    
    # Define the inputnode
    inputnode = pe.Node(interface = util.IdentityInterface(fields=["fa_list"]),
                        name="inputnode")

    # Prep the FA images
    prepfa = pe.MapNode(fsl.ImageMaths(suffix="_prep"), 
                                    name="prepfa",
                                    iterfield=['in_file','op_string'])
    
    # Slicer
    slicer = pe.MapNode(fsl.Slicer(all_axial = True, image_width=1280),
                        name='slicer', 
                        iterfield=['in_file'])
    
    # Create a mask
    getmask = pe.MapNode(fsl.ImageMaths(op_string="-bin", suffix="_mask"),
                        name="getmask",
                        iterfield=['in_file'])
    
    # Define the tbss1 workflow
    tbss1 = pe.Workflow(name="tbss1")
    tbss1.connect([
        (inputnode, prepfa, [("fa_list", "in_file")]),
        (inputnode, prepfa, [(("fa_list", tbss1_op_string), "op_string")]),
        (prepfa, getmask, [("out_file", "in_file")]),
        (prepfa, slicer,[('out_file', 'in_file')]),
        ])
    
    # Define the outputnode
    outputnode = pe.Node(interface = util.IdentityInterface(fields=["fa_list",
                                                                "mask_list"]), 
                        name="outputnode")
    tbss1.connect([
                (prepfa, outputnode, [("out_file", "fa_list")]),
                (getmask, outputnode, [("out_file","mask_list")]),
                ])
    return tbss1

def create_tbss_2_reg(name="tbss_2_reg"):
    """TBSS nonlinear registration: 
    A pipeline that does the same as tbss_2_reg script in FSL.
        
    Example
    ------
    
    >>> tbss2 = create_tbss_2_reg(name="tbss2")
    >>> tbss2.inputs.inputnode.target = fsl.Info.standard_image("FMRIB58_FA_1mm.nii.gz")
    >>> ...
    
    Inputs::

        inputnode.fa_list
        inputnode.mask_list
        inputnode.target

    Outputs::
    
        outputnode.field_list

    """
   
    # Define the inputnode
    inputnode = pe.Node(interface = util.IdentityInterface(fields=["fa_list",
                                                                   "mask_list",
                                                                   "target"]),
                        name="inputnode")
    
    # Flirt the FA image to the target
    flirt = pe.MapNode(interface=fsl.FLIRT(dof=12),
                    iterfield=['in_file','in_weight'],
                    name="flirt")
    
    # Fnirt the FA image to the target
    config_file = os.path.join(os.environ["FSLDIR"],
                                "etc/flirtsch/FA_2_FMRIB58_1mm.cnf")
    fnirt = pe.MapNode(interface=fsl.FNIRT(config_file=config_file,
                                        fieldcoeff_file=True),
                    iterfield=['in_file', 'inmask_file', 'affine_file'],
                    name="fnirt")
    
    # Define the registration workflow
    tbss2 = pe.Workflow(name=name)
    
    # Connect up the registration workflow
    tbss2.connect([
        (inputnode,flirt,[("fa_list", "in_file"),
                         ("target","reference"),
                         ("mask_list","in_weight")]),
        (inputnode,fnirt,[("fa_list", "in_file"),
                         ("mask_list","inmask_file"),
                         ("target","ref_file")]),
        (flirt,fnirt,[("out_matrix_file", "affine_file")]),
        ])

    # Define the outputnode
    outputnode = pe.Node(interface = util.IdentityInterface(fields=['field_list']),
                         name="outputnode")
    
    tbss2.connect([
        (fnirt,outputnode, [('fieldcoeff_file','field_list')])
        ])
    return tbss2

def create_tbss_3_postreg(name='tbss_3_postreg'):
    """Post-registration processing: derive mean_FA and mean_FA_skeleton from 
    mean of all subjects in study.
    A pipeline that does the same as tbss_3_postreg script from FSL
    
    Example
    --------
    
    >>>tbss3 = create_tbss_3_postreg(name='tbss3')
    >>>...
    
    Inputs::
    
        inputnode.wraped_fa_list
    
    Outputs::
    
        outputnode.groupmask
        outputnode.skeleton_file
        outputnode.meanfa_file
        outputnode.mergefa_file

    """
    
    # Create the inputnode
    inputnode = pe.Node(interface = util.IdentityInterface(fields=['field_list',
                                                                'fa_list',
                                                                'target']),
                        name='inputnode')
    
    # Apply the warpfield to the masked FA image
    applywarp = pe.MapNode(interface=fsl.ApplyWarp(),
                           iterfield=['in_file','field_file'],
                        name="applywarp")
    
    # Merge the FA files into a 4D file
    mergefa = pe.Node(fsl.Merge(dimension="t", merged_file="all_FA.nii.gz"),
                    name="mergefa")
    
    # Get a group mask
    groupmask = pe.Node(fsl.ImageMaths(op_string="-max 0 -Tmin -bin",
                                       out_data_type="char",
                                       suffix="_mask"),
                        name="groupmask")
    
    maskgroup = pe.Node(fsl.ImageMaths(op_string="-mas",
                                       suffix="_masked"),
                        name="maskgroup")
    
    # Take the mean over the fourth dimension
    meanfa = pe.Node(fsl.ImageMaths(op_string="-Tmean",
                                     suffix="_mean"),
                      name="meanfa")
    
    # Use the mean FA volume to generate a tract skeleton
    makeskeleton = pe.Node(fsl.TractSkeleton(skeleton_file=True),
                           name="makeskeleton")
    tbss3 = pe.Workflow(name=name)
    tbss3.connect([
        (inputnode,applywarp,[("fa_list", "in_file"),
                              ("target","ref_file"),
                              ("field_list", "field_file")]),
        (applywarp, mergefa, [("out_file", "in_files")]),
        (mergefa, groupmask, [("merged_file", "in_file")]),
        (mergefa, maskgroup, [("merged_file", "in_file")]),
        (groupmask, maskgroup, [("out_file", "in_file2")]),
        (maskgroup, meanfa, [("out_file", "in_file")]),
        (meanfa, makeskeleton, [("out_file", "in_file")])
        ])
    
    # Create outputnode
    outputnode = pe.Node(interface = util.IdentityInterface(fields=['groupmask',
                                                                'skeleton_file',
                                                                'meanfa_file',
                                                                'mergefa_file']),
                         name='outputnode')
    tbss3.connect([
            (groupmask, outputnode,[('out_file', 'groupmask')]),
            (makeskeleton, outputnode,[('skeleton_file', 'skeleton_file')]),
            (meanfa, outputnode,[('out_file', 'meanfa_file')]),
            (maskgroup, outputnode,[('out_file', 'mergefa_file')])
            ])
    return tbss3

def tbss4_op_string(skeleton_thresh):
    op_string = "-thr %.1f -bin"%skeleton_thresh
    return op_string
    
def create_tbss_4_prestats(name='tbss_4_prestats'):
    """Post-registration processing:Creating skeleton mask using a threshold
     projecting all FA data onto skeleton.
    A pipeline that does the same as tbss_4_prestats script from FSL
    
    Example
    --------
    
    >>>tbss4 = create_tbss_4_prestats(name='tbss4')
    >>>tbss.inputs.inputnode.skeleton_thresh = 0.2
    >>>...
    
    Inputs::
    
        inputnode.skeleton_thresh
        inputnode.groupmask
        inputnode.skeleton_file
        inputnode.meanfa_file
        inputnode.mergefa_file
    
    Outputs::
    
        outputnode.all_FA_skeletonised
        outputnode.mean_FA_skeleton_mask
    
    """
    # Create inputnode
    inputnode = pe.Node(interface=util.IdentityInterface(fields=['groupmask',
                                                            'skeleton_file',
                                                            'meanfa_file',
                                                            'mergefa_file',
                                                            'skeleton_thresh']),
                        name='inputnode')
    
    # Mask the skeleton at the threshold
    skeletonmask = pe.Node(fsl.ImageMaths(#op_string="-thr %.1f -bin"%skeleton_thresh,
                                          suffix="_mask"),
                           name="skeletonmask")
    
    # Invert the brainmask then add in the tract skeleton
    invertmask = pe.Node(fsl.ImageMaths(suffix="_inv",
                                        op_string="-mul -1 -add 1 -add"),
                         name="invertmask")
    
    # Generate a distance map with the tract skeleton
    distancemap = pe.Node(fsl.DistanceMap(),
                          name="distancemap")
    
    # Project the FA values onto the skeleton
    projectfa = pe.Node(fsl.TractSkeleton(project_data=True,
                                        skeleton_file = True,
                                        use_cingulum_mask=True),
                        name="projectfa")
    
    # Create tbss4 workflow
    tbss4 = pe.Workflow(name=name)
    tbss4.connect([
        (inputnode, invertmask, [("groupmask", "in_file")]),
        (inputnode, skeletonmask, [("skeleton_file", "in_file"),
                                (('skeleton_thresh', tbss4_op_string),
                                                        'op_string')]),
        (inputnode, projectfa,[('skeleton_thresh','threshold'),
                                ("meanfa_file", "in_file"),
                                ("mergefa_file", "data_file")]),
        (skeletonmask, invertmask, [("out_file", "in_file2")]),
        (invertmask, distancemap, [("out_file", "in_file")]),        
        (distancemap, projectfa, [("distance_map", "distance_map")]),
        ])
    
    # Create the outputnode
    outputnode = pe.Node(interface=util.IdentityInterface(fields=['projectedfa_file',
                                                                'skeleton_mask',
                                                                'distance_map',
                                                                'skeleton_file']),
                         name='outputnode')
    
    tbss4.connect([
            (projectfa, outputnode,[('projected_data', 'projectedfa_file'),
                                    ('skeleton_file', 'skeleton_file')
                                    ]),
            (distancemap, outputnode,[('distance_map', 'distance_map')]),
            (skeletonmask, outputnode, [('out_file', 'skeleton_mask')])
            ])
    
    return tbss4

def create_tbss_all(name='tbss_all'):
    """Create a pipeline that combines create_tbss_* pipelines
    
    Example
    --------
    
    >>>tbss = tbss.create_tbss_all('tbss')
    >>>tbss.base_dir = os.path.abspath(workingdir)
    >>>tbss.inputs.inputnode.target = fsl.Info.standard_image("FMRIB58_FA_1mm.nii.gz")
    >>>tbss.inputs.inputnode.skeleton_thresh = 0.2
    
    Inputs::
    
        inputnode.fa_list
        inputnode.target
        inputnode.skeleton_thresh
    
    Outputs::
    
        outputnode.meanfa_file
        outputnode.projectedfa_file
        outputnode.skeleton_file
        outputnode.skeleton_mask
        
    """

    # Define the inputnode
    inputnode = pe.Node(interface=util.IdentityInterface(fields=['fa_list',
                                                                'target',
                                                                'skeleton_thresh']),
                        name='inputnode')
    
    tbss1 = create_tbss_1_preproc(name='tbss1')
    tbss2 = create_tbss_2_reg(name='tbss2')
    tbss3 = create_tbss_3_postreg(name='tbss3')    
    tbss4 = create_tbss_4_prestats(name='tbss4')
    
    tbss_all = pe.Workflow(name="tbss_all")
    tbss_all.connect([
                (inputnode, tbss1,[('fa_list', 'inputnode.fa_list')]),
                (inputnode, tbss2,[('target', 'inputnode.target')]),
                (inputnode, tbss3,[('target', 'inputnode.target')]),
                (inputnode, tbss4,[('skeleton_thresh', 'inputnode.skeleton_thresh')]),
                    
                (tbss1, tbss2,[('outputnode.fa_list', 'inputnode.fa_list'),
                                   ('outputnode.mask_list', 'inputnode.mask_list')]),
                (tbss1, tbss3,[('outputnode.fa_list', 'inputnode.fa_list')]),
                (tbss2, tbss3, [('outputnode.field_list', 'inputnode.field_list')]),
                (tbss3,tbss4,[
                            ('outputnode.groupmask', 'inputnode.groupmask'),
                            ('outputnode.skeleton_file', 'inputnode.skeleton_file'),
                            ('outputnode.meanfa_file', 'inputnode.meanfa_file'),
                            ('outputnode.mergefa_file', 'inputnode.mergefa_file')
                        ])
                ])
    
    # Define the outputnode
    outputnode = pe.Node(interface=util.IdentityInterface(fields=['groupmask',
                                                                'skeleton_file3',
                                                                'meanfa_file',
                                                                'mergefa_file',
                                                                'projectedfa_file',
                                                                'skeleton_file4',
                                                                'skeleton_mask',
                                                                'distance_map']),
                         name='outputnode')
    outputall_node = pe.Node(interface=util.IdentityInterface(
                                                        fields=['fa_list1',
                                                                'mask_list1',
                                                                'field_list2',
                                                                'groupmask3',
                                                                'skeleton_file3',
                                                                'meanfa_file3',
                                                                'mergefa_file3',
                                                                'projectedfa_file4',
                                                                'skeleton_mask4',
                                                                'distance_map4']),
                         name='outputall_node')

    tbss_all.connect([
                (tbss3, outputnode,[('outputnode.meanfa_file','meanfa_file'),
                                    ('outputnode.mergefa_file','mergefa_file'),
                                    ('outputnode.groupmask','groupmask'),
                                    ('outputnode.skeleton_file','skeleton_file3'),
                                    ]),
                (tbss4, outputnode,[('outputnode.projectedfa_file','projectedfa_file'),
                                    ('outputnode.skeleton_file','skeleton_file4'),
                                    ('outputnode.skeleton_mask','skeleton_mask'),
                                    ('outputnode.distance_map','distance_map'),
                                    ]),
                    
                (tbss1, outputall_node,[('outputnode.fa_list','fa_list1'),
                                    ('outputnode.mask_list','mask_list1'),
                                    ]),
                (tbss2, outputall_node,[('outputnode.field_list','field_list2'),
                                        ]),
                (tbss3, outputall_node,[
                                    ('outputnode.meanfa_file','meanfa_file3'),
                                    ('outputnode.mergefa_file','mergefa_file3'),
                                    ('outputnode.groupmask','groupmask3'),
                                    ('outputnode.skeleton_file','skeleton_file3'),
                                    ]),
                (tbss4, outputall_node,[
                                    ('outputnode.projectedfa_file','projectedfa_file4'),
                                    ('outputnode.skeleton_mask','skeleton_mask4'),
                                    ('outputnode.distance_map','distance_map4'),
                                    ]),
                    ])
    return tbss_all
