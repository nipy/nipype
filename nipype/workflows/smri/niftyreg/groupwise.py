# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe
import nipype.interfaces.niftyreg as niftyreg

'''
This file provides some common registration routines useful for a variety of pipelines.
Including linear and non-linear image co-registration
'''


def create_linear_gw_step(name="linear_gw_niftyreg",
                          demean=True,
                          linear_options_hash=None,
                          use_mask=False,
                          verbose=False):
    """Creates a workflow that perform linear co-registration of a set of images using RegAladin, 
    producing an average image and a set of affine transformation matrices linking each
    of the floating images to the average.

    Example
    -------

    >>> linear_coreg = create_linear_gw_step('my_linear_coreg') # doctest: +SKIP
    >>> linear_coreg.inputs.input_node.in_files = ['file1.nii.gz', 'file2.nii.gz'] # doctest: +SKIP
    >>> linear_coreg.inputs.input_node.ref_file = ['initial_ref'] # doctest: +SKIP
    >>> linear_coreg.inputs.input_node # doctest: +SKIP
    >>> linear_coreg.run()  # doctest: +SKIP

    Inputs::

        input_node.in_files - The input files to be registered
        input_node.ref_file - The initial reference image that the input files are registered to
        input_node.rmask_file - Mask of the reference image
        input_node.in_aff_files - Initial affine transformation files
        

    Outputs::

        output_node.average_image - The average image
        output_node.aff_files - The affine transformation files


    Optional arguments::
        linear_options_hash - An options dictionary containing a list of parameters for RegAladin that take
        the same form as given in the interface (default None)
        demean - Selects whether to demean the transformation matrices when performing the averaging (default True)
        initial_affines - Selects whether to iterate over initial affine images,
        which we generally won't have (default False)


    """
    # We need to create an input node for the workflow    
    input_node = pe.Node(niu.IdentityInterface(
        fields=['in_files',
                'ref_file',
                'rmask_file']),
        name='input_node')

    if linear_options_hash is None:
        linear_options_hash = dict()

    # Rigidly register each of the images to the average
    lin_reg = pe.MapNode(interface=niftyreg.RegAladin(**linear_options_hash),
                         name="lin_reg",
                         iterfield=['flo_file'])
    if verbose is False:
        lin_reg.inputs.verbosity_off_flag = True

    # Average the images
    ave_ims = pe.Node(interface=niftyreg.RegAverage(), name="ave_ims")

    # We have a new average image and the affine
    # transformations, which are returned as an output node. 
    output_node = pe.Node(niu.IdentityInterface(
        fields=['average_image',
                'trans_files']),
        name='output_node')

    # Create the sub workflow
    pipeline = pe.Workflow(name=name)
    pipeline.base_output_dir = name

    # Connect the inputs to the lin_reg node
    pipeline.connect([(input_node, lin_reg, [('ref_file', 'ref_file')]),
                      (input_node, lin_reg, [('in_files', 'flo_file')])])
    if use_mask:
        pipeline.connect(input_node, 'rmask_file', lin_reg, 'rmask_file')

    if demean:
        pipeline.connect(input_node, 'ref_file', ave_ims, 'demean1_ref_file')
        pipeline.connect(lin_reg, 'avg_output', ave_ims, 'warp_files')
    else:
        pipeline.connect(lin_reg, 'res_file', ave_ims, 'avg_files')

    # Connect up the output node
    pipeline.connect(lin_reg, 'aff_file', output_node, 'trans_files')
    pipeline.connect(ave_ims, 'out_file', output_node, 'average_image')
    return pipeline


def create_nonlinear_gw_step(name="nonlinear_gw_niftyreg",
                             demean=True,
                             nonlinear_options_hash=None,
                             initial_affines=False,
                             use_mask=False,
                             verbose=False):
    """Creates a workflow that perform non-linear co-registrations of a set of images using RegF3d,
    producing an non-linear average image and a set of cpp transformation linking each
    of the floating images to the average.

    Example
    -------
    >>> nonlinear_coreg = create_nonlinear_gw_step('my_linear_coreg') # doctest: +SKIP
    >>> nonlinear_coreg.inputs.input_node.in_files = ['file1.nii.gz', 'file2.nii.gz'] # doctest: +SKIP
    >>> nonlinear_coreg.inputs.input_node.ref_file = ['initial_ref'] # doctest: +SKIP
    >>> nonlinear_coreg.inputs.input_node # doctest: +SKIP
    >>> nonlinear_coreg.run()  # doctest: +SKIP

    Inputs::

        input_node.in_files - The input files to be registered
        input_node.ref_file - The initial reference image that the input files are registered to
        input_node.rmask_file - Mask of the reference image
        input_node.in_trans_files - Initial transformation files (affine or cpps)
        

    Outputs::

        output_node.average_image - The average image
        output_node.cpp_files - The bspline transformation files


    Optional arguments::
        nonlinear_options_hash - An options dictionary containing a list of parameters for RegAladin that take the
        same form as given in the interface (default None)
        initial_affines - Selects whether to iterate over initial affine images,
        which we generally won't have (default False)


    """
    # We need to create an input node for the workflow    
    input_node = pe.Node(niu.IdentityInterface(
        fields=['in_files',
                'ref_file',
                'rmask_file',
                'input_aff_files']),
        name='input_node')

    if nonlinear_options_hash is None:
        nonlinear_options_hash = dict()

    # non-rigidly register each of the images to the average
    # flo_file can take a list of files
    # Need to be able to iterate over input affine files, but what about the cases where we have no input affine files?
    # Passing empty strings are not valid filenames, and undefined fields can not be iterated over.
    # Current simple solution, as this is not generally required, is to use a flag which specifies wherther to iterate
    if initial_affines:
        nonlin_reg = pe.MapNode(interface=niftyreg.RegF3D(**nonlinear_options_hash),
                                name="nonlin_reg",
                                iterfield=['flo_file', 'aff_file'])
    else:
        nonlin_reg = pe.MapNode(interface=niftyreg.RegF3D(**nonlinear_options_hash),
                                name="nonlin_reg",
                                iterfield=['flo_file'])
    if verbose is False:
        nonlin_reg.inputs.verbosity_off_flag = True

    # Average the images
    ave_ims = pe.Node(interface=niftyreg.RegAverage(), name="ave_ims")

    # We have a new centered average image, the resampled original images and the affine 
    # transformations, which are returned as an output node. 
    output_node = pe.Node(niu.IdentityInterface(
        fields=['average_image',
                'trans_files']),
        name='output_node')

    pipeline = pe.Workflow(name=name)
    pipeline.base_output_dir = name

    # Connect the inputs to the lin_reg node, which is split over in_files
    pipeline.connect([(input_node, nonlin_reg, [('in_files', 'flo_file')]),
                      (input_node, nonlin_reg, [('ref_file', 'ref_file')])])
    #
    if use_mask:
        pipeline.connect(input_node, 'rmask_file', nonlin_reg, 'rmask_file')

    # If we have initial affine transforms, we need to connect them in
    if initial_affines:
        pipeline.connect(input_node, 'input_aff_files', nonlin_reg, 'aff_file')

    if demean:
        if 'vel_flag' in nonlinear_options_hash.keys() and nonlinear_options_hash['vel_flag'] is True and\
                initial_affines:
            pipeline.connect(input_node, 'ref_file', ave_ims, 'demean3_ref_file')
        else:
            pipeline.connect(input_node, 'ref_file', ave_ims, 'demean2_ref_file')
        pipeline.connect(nonlin_reg, 'avg_output', ave_ims, 'warp_files')
    else:
        pipeline.connect(nonlin_reg, 'res_file', ave_ims, 'avg_files')

    # Connect up the output node
    pipeline.connect(nonlin_reg, 'cpp_file', output_node, 'trans_files')
    pipeline.connect(ave_ims, 'out_file', output_node, 'average_image')
    return pipeline


# Creates an atlas image by iterative registration. An initial reference image can be provided,
# otherwise one will be made.
def create_groupwise_average(name="atlas_creation",
                             itr_rigid=3,
                             itr_affine=3,
                             itr_non_lin=5,
                             linear_options_hash=None,
                             nonlinear_options_hash=None,
                             use_mask=False,
                             verbose=False):
    # Create the overall workflow that embeds all the rigid, affine and non-linear components
    pipeline = pe.Workflow(name=name)

    if linear_options_hash is None:
        linear_options_hash = dict()

    if nonlinear_options_hash is None:
        nonlinear_options_hash = dict()

    # Create the input and output node
    input_node = pe.Node(niu.IdentityInterface(
        fields=['in_files',
                'ref_file',
                'rmask_file']),
        name='input_node')
    output_node = pe.Node(niu.IdentityInterface(
        fields=['average_image',
                'trans_files']),
        name='output_node')

    # Create lists to store the rigid, affine and non-linear sub-workflow
    lin_workflows = []
    nonlin_workflows = []

    # Create the linear groupwise registration sub-workflows
    for i in range(itr_rigid + itr_affine):

        # Define is the sub-workflow is rigid or affine
        if i >= itr_rigid:
            linear_options_hash['rig_only_flag'] = False
        else:
            linear_options_hash['rig_only_flag'] = True
        # Define if the average image should be demean to ensure we have a barycenter
        if (i < itr_rigid) or (i == (itr_rigid + itr_affine - 1)):
            demean_arg = False
        else:
            demean_arg = True
        # Create the rigid or affine sub-workflow and add it to the relevant list
        w = create_linear_gw_step(name='lin_reg' + str(i),
                                  linear_options_hash=linear_options_hash,
                                  demean=demean_arg,
                                  verbose=verbose)
        lin_workflows.append(w)
        # Connect up the input data to the workflow
        pipeline.connect(input_node, 'in_files', w, 'input_node.in_files')
        if use_mask:
            pipeline.connect(input_node, 'rmask_file', w, 'input_node.rmask_file')
        # If it exist, connect the previous workflow to the current one
        if i == 0:
            pipeline.connect(input_node, 'ref_file', w, 'input_node.ref_file')
        else:
            pipeline.connect(lin_workflows[i - 1], 'output_node.average_image', w, 'input_node.ref_file')

    demean_arg = True

    # Create the nonlinear groupwise registration sub-workflows
    for i in range(itr_non_lin):

        if len(lin_workflows) > 0:
            initial_affines_arg = True
        if i == (itr_non_lin - 1):
            demean_arg = False

        w = create_nonlinear_gw_step(name='nonlin' + str(i),
                                     demean=demean_arg,
                                     initial_affines=initial_affines_arg,
                                     nonlinear_options_hash=nonlinear_options_hash,
                                     verbose=verbose)

        # Connect up the input data to the workflows
        pipeline.connect(input_node, 'in_files', w, 'input_node.in_files')
        if use_mask:
            pipeline.connect(input_node, 'rmask_file', w, 'input_node.rmask_file')

        if initial_affines_arg:
            # Take the final linear registration results and use them to initialise the NR
            pipeline.connect(lin_workflows[-1], 'output_node.trans_files', w, 'input_node.input_aff_files')
        if i == 0:
            if len(lin_workflows) > 0:
                pipeline.connect(lin_workflows[-1], 'output_node.average_image',
                                 w, 'input_node.ref_file')
            else:
                pipeline.connect(input_node, 'ref_file',
                                 w, 'input_node.ref_file')
        else:
            pipeline.connect(nonlin_workflows[i - 1], 'output_node.average_image',
                             w, 'input_node.ref_file')

        nonlin_workflows.append(w)

    # Set up the last workflow
    last_workflow = None
    if len(nonlin_workflows) > 0:
        last_workflow = nonlin_workflows[-1]
    elif len(lin_workflows) > 0:
        last_workflow = lin_workflows[-1]

    # Connect the data to return
    pipeline.connect(last_workflow, 'output_node.average_image', output_node, 'average_image')
    pipeline.connect(last_workflow, 'output_node.trans_files', output_node, 'trans_files')

    return pipeline
