# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Example of registration workflows using niftyreg, useful for a variety of
pipelines. Including linear and non-linear image co-registration
"""

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import str, range
from ....interfaces import utility as niu
from ....interfaces import niftyreg as niftyreg
from ....pipeline import engine as pe


def create_linear_gw_step(name="linear_gw_niftyreg",
                          demean=True,
                          linear_options_hash=None,
                          use_mask=False,
                          verbose=False):
    """
    Creates a workflow that performs linear co-registration of a set of images
    using RegAladin, producing an average image and a set of affine
    transformation matrices linking each of the floating images to the average.

    Inputs::

        inputspec.in_files - The input files to be registered
        inputspec.ref_file - The initial reference image that the input files
                              are registered to
        inputspec.rmask_file - Mask of the reference image
        inputspec.in_aff_files - Initial affine transformation files

    Outputs::

        outputspec.average_image - The average image
        outputspec.aff_files - The affine transformation files

    Optional arguments::

        linear_options_hash - An options dictionary containing a list of
                              parameters for RegAladin that take
        the same form as given in the interface (default None)
        demean - Selects whether to demean the transformation matrices when
                 performing the averaging (default True)
        initial_affines - Selects whether to iterate over initial affine
                          images, which we generally won't have (default False)

    Example
    -------

    >>> from nipype.workflows.smri.niftyreg import create_linear_gw_step
    >>> lgw = create_linear_gw_step('my_linear_coreg')  # doctest: +SKIP
    >>> lgw.inputs.inputspec.in_files = [
    ...     'file1.nii.gz', 'file2.nii.gz']  # doctest: +SKIP
    >>> lgw.inputs.inputspec.ref_file = ['ref.nii.gz']  # doctest: +SKIP
    >>> lgw.run()  # doctest: +SKIP

    """
    # Create the sub workflow
    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    # We need to create an input node for the workflow
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['in_files', 'ref_file', 'rmask_file']),
        name='inputspec')

    if linear_options_hash is None:
        linear_options_hash = dict()

    # Rigidly register each of the images to the average
    lin_reg = pe.MapNode(
        interface=niftyreg.RegAladin(**linear_options_hash),
        name="lin_reg",
        iterfield=['flo_file'])

    if verbose is False:
        lin_reg.inputs.verbosity_off_flag = True

    # Average the images
    ave_ims = pe.Node(interface=niftyreg.RegAverage(), name="ave_ims")

    # We have a new average image and the affine
    # transformations, which are returned as an output node.
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['average_image', 'trans_files']),
        name='outputspec')

    # Connect the inputs to the lin_reg node
    workflow.connect([(inputnode, lin_reg, [('ref_file', 'ref_file')]),
                      (inputnode, lin_reg, [('in_files', 'flo_file')])])
    if use_mask:
        workflow.connect(inputnode, 'rmask_file', lin_reg, 'rmask_file')

    if demean:
        workflow.connect([(inputnode, ave_ims, [('ref_file',
                                                 'demean1_ref_file')]),
                          (lin_reg, ave_ims, [('avg_output', 'warp_files')])])
    else:
        workflow.connect(lin_reg, 'res_file', ave_ims, 'avg_files')

    # Connect up the output node
    workflow.connect([(lin_reg, outputnode, [('aff_file', 'trans_files')]),
                      (ave_ims, outputnode, [('out_file', 'average_image')])])

    return workflow


def create_nonlinear_gw_step(name="nonlinear_gw_niftyreg",
                             demean=True,
                             nonlinear_options_hash=None,
                             initial_affines=False,
                             use_mask=False,
                             verbose=False):
    """
    Creates a workflow that perform non-linear co-registrations of a set of
    images using RegF3d, producing an non-linear average image and a set of
    cpp transformation linking each of the floating images to the average.

    Inputs::

        inputspec.in_files - The input files to be registered
        inputspec.ref_file - The initial reference image that the input files
                              are registered to
        inputspec.rmask_file - Mask of the reference image
        inputspec.in_trans_files - Initial transformation files (affine or
                                    cpps)

    Outputs::

        outputspec.average_image - The average image
        outputspec.cpp_files - The bspline transformation files

    Optional arguments::

        nonlinear_options_hash - An options dictionary containing a list of
                                 parameters for RegAladin that take the
        same form as given in the interface (default None)
        initial_affines - Selects whether to iterate over initial affine
                          images, which we generally won't have (default False)

    Example
    -------
    >>> from nipype.workflows.smri.niftyreg import create_nonlinear_gw_step
    >>> nlc = create_nonlinear_gw_step('nonlinear_coreg')  # doctest: +SKIP
    >>> nlc.inputs.inputspec.in_files = [
    ...     'file1.nii.gz', 'file2.nii.gz']  # doctest: +SKIP
    >>> nlc.inputs.inputspec.ref_file = ['ref.nii.gz']  # doctest: +SKIP
    >>> nlc.run()  # doctest: +SKIP

    """

    # Create the workflow
    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    # We need to create an input node for the workflow
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['in_files', 'ref_file', 'rmask_file', 'input_aff_files']),
        name='inputspec')

    if nonlinear_options_hash is None:
        nonlinear_options_hash = dict()

    # non-rigidly register each of the images to the average
    # flo_file can take a list of files
    # Need to be able to iterate over input affine files, but what about the
    # cases where we have no input affine files?
    # Passing empty strings are not valid filenames, and undefined fields can
    # not be iterated over.
    # Current simple solution, as this is not generally required, is to use a
    # flag which specifies wherther to iterate
    if initial_affines:
        nonlin_reg = pe.MapNode(
            interface=niftyreg.RegF3D(**nonlinear_options_hash),
            name="nonlin_reg",
            iterfield=['flo_file', 'aff_file'])
    else:
        nonlin_reg = pe.MapNode(
            interface=niftyreg.RegF3D(**nonlinear_options_hash),
            name="nonlin_reg",
            iterfield=['flo_file'])

    if verbose is False:
        nonlin_reg.inputs.verbosity_off_flag = True

    # Average the images
    ave_ims = pe.Node(interface=niftyreg.RegAverage(), name="ave_ims")

    # We have a new centered average image, the resampled original images and
    # the affine transformations, which are returned as an output node.
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['average_image', 'trans_files']),
        name='outputspec')

    # Connect the inputs to the lin_reg node, which is split over in_files
    workflow.connect([(inputnode, nonlin_reg, [('in_files', 'flo_file')]),
                      (inputnode, nonlin_reg, [('ref_file', 'ref_file')])])

    if use_mask:
        workflow.connect(inputnode, 'rmask_file', nonlin_reg, 'rmask_file')

    # If we have initial affine transforms, we need to connect them in
    if initial_affines:
        workflow.connect(inputnode, 'input_aff_files', nonlin_reg, 'aff_file')

    if demean:
        if 'vel_flag' in list(nonlinear_options_hash.keys()) and \
           nonlinear_options_hash['vel_flag'] is True and \
           initial_affines:
            workflow.connect(inputnode, 'ref_file', ave_ims,
                             'demean3_ref_file')
        else:
            workflow.connect(inputnode, 'ref_file', ave_ims,
                             'demean2_ref_file')
        workflow.connect(nonlin_reg, 'avg_output', ave_ims, 'warp_files')
    else:
        workflow.connect(nonlin_reg, 'res_file', ave_ims, 'avg_files')

    # Connect up the output node
    workflow.connect([(nonlin_reg, outputnode, [('cpp_file', 'trans_files')]),
                      (ave_ims, outputnode, [('out_file', 'average_image')])])

    return workflow


# Creates an atlas image by iterative registration. An initial reference image
# can be provided, otherwise one will be made.
def create_groupwise_average(name="atlas_creation",
                             itr_rigid=3,
                             itr_affine=3,
                             itr_non_lin=5,
                             linear_options_hash=None,
                             nonlinear_options_hash=None,
                             use_mask=False,
                             verbose=False):
    """
    Create the overall workflow that embeds all the rigid, affine and
    non-linear components.

    Inputs::

        inputspec.in_files - The input files to be registered
        inputspec.ref_file - The initial reference image that the input files
                              are registered to
        inputspec.rmask_file - Mask of the reference image
        inputspec.in_trans_files - Initial transformation files (affine or
                                    cpps)

    Outputs::

        outputspec.average_image - The average image
        outputspec.cpp_files - The bspline transformation files


    Example
    -------

    >>> from nipype.workflows.smri.niftyreg import create_groupwise_average
    >>> node = create_groupwise_average('groupwise_av')  # doctest: +SKIP
    >>> node.inputs.inputspec.in_files = [
    ...     'file1.nii.gz', 'file2.nii.gz']  # doctest: +SKIP
    >>> node.inputs.inputspec.ref_file = ['ref.nii.gz']  # doctest: +SKIP
    >>> node.inputs.inputspec.rmask_file = ['mask.nii.gz']  # doctest: +SKIP
    >>> node.run()  # doctest: +SKIP

    """
    # Create workflow
    workflow = pe.Workflow(name=name)

    if linear_options_hash is None:
        linear_options_hash = dict()

    if nonlinear_options_hash is None:
        nonlinear_options_hash = dict()

    # Create the input and output node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['in_files', 'ref_file', 'rmask_file']),
        name='inputspec')

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['average_image', 'trans_files']),
        name='outputspec')

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

        # Define if the average image should be demean to ensure we have a
        # barycenter
        if (i < itr_rigid) or (i == (itr_rigid + itr_affine - 1)):
            demean_arg = False
        else:
            demean_arg = True

        # Create the rigid or affine sub-workflow and add it to the relevant
        # list
        wf = create_linear_gw_step(
            name='lin_reg' + str(i),
            linear_options_hash=linear_options_hash,
            demean=demean_arg,
            verbose=verbose)
        lin_workflows.append(wf)

        # Connect up the input data to the workflow
        workflow.connect(inputnode, 'in_files', wf, 'inputspec.in_files')
        if use_mask:
            workflow.connect(inputnode, 'rmask_file', wf,
                             'inputspec.rmask_file')
        # If it exist, connect the previous workflow to the current one
        if i == 0:
            workflow.connect(inputnode, 'ref_file', wf, 'inputspec.ref_file')
        else:
            workflow.connect(lin_workflows[i - 1], 'outputspec.average_image',
                             wf, 'inputspec.ref_file')

    demean_arg = True

    # Create the nonlinear groupwise registration sub-workflows
    for i in range(itr_non_lin):

        if len(lin_workflows) > 0:
            initial_affines_arg = True
        if i == (itr_non_lin - 1):
            demean_arg = False

        wf = create_nonlinear_gw_step(
            name='nonlin' + str(i),
            demean=demean_arg,
            initial_affines=initial_affines_arg,
            nonlinear_options_hash=nonlinear_options_hash,
            verbose=verbose)

        # Connect up the input data to the workflows
        workflow.connect(inputnode, 'in_files', wf, 'inputspec.in_files')
        if use_mask:
            workflow.connect(inputnode, 'rmask_file', wf,
                             'inputspec.rmask_file')

        if initial_affines_arg:
            # Take the final linear registration results and use them to
            # initialise the NR
            workflow.connect(lin_workflows[-1], 'outputspec.trans_files', wf,
                             'inputspec.input_aff_files')

        if i == 0:
            if len(lin_workflows) > 0:
                workflow.connect(lin_workflows[-1], 'outputspec.average_image',
                                 wf, 'inputspec.ref_file')
            else:
                workflow.connect(inputnode, 'ref_file', wf,
                                 'inputspec.ref_file')
        else:
            workflow.connect(nonlin_workflows[i - 1],
                             'outputspec.average_image', wf,
                             'inputspec.ref_file')

        nonlin_workflows.append(wf)

    # Set up the last workflow
    lw = None
    if len(nonlin_workflows) > 0:
        lw = nonlin_workflows[-1]
    elif len(lin_workflows) > 0:
        lw = lin_workflows[-1]

    # Connect the data to return
    workflow.connect(
        [(lw, outputnode, [('outputspec.average_image', 'average_image')]),
         (lw, outputnode, [('outputspec.trans_files', 'trans_files')])])

    return workflow
