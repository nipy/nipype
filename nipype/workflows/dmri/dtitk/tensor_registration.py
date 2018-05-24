# -*- coding: utf-8 -*-
# coding: utf-8
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from ....pipeline import engine as pe
from ....interfaces import utility as niu
from ....interfaces import dtitk


def affine_tensor_pipeline(name='AffTen'):

    """
    Workflow that performs a linear registration
    (Rigid followed by Affine)

    Example
    -------

    >>> from nipype.workflows.dmri.dtitk.tensor_registration import affine_tensor_pipeline
    >>> affine = affine_tensor_pipeline()
    >>> affine.inputs.inputnode.fixed_file = 'im1.nii'
    >>> affine.inputs.inputnode.moving_file = 'im2.nii'
    >>> affine.run() # doctest: +SKIP


    """
    inputnode = pe.Node(niu.IdentityInterface(
                        fields=['fixed_file', 'moving_file']),
                        name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(
                         fields=['out_file', 'out_file_xfm']),
                         name='outputnode')

    rigid_node = pe.Node(dtitk.Rigid(), name='rigid_node')
    affine_node = pe.Node(dtitk.Affine(), name='affine_node')

    wf = pe.Workflow(name=name)

    wf.connect(inputnode, 'fixed_file', rigid_node, 'fixed_file')
    wf.connect(inputnode, 'moving_file', rigid_node, 'moving_file')
    wf.connect(rigid_node, 'out_file_xfm', affine_node, 'initialize_xfm')
    wf.connect(inputnode, 'fixed_file', affine_node, 'fixed_file')
    wf.connect(inputnode, 'moving_file', affine_node, 'moving_file')
    wf.connect(affine_node, 'out_file', outputnode, 'out_file')
    wf.connect(affine_node, 'out_file_xfm', outputnode, 'out_file_xfm')

    return wf


def diffeomorphic_tensor_pipeline(name='DiffeoTen',
                                  params={'array_size': (128, 128, 64)}):
    """
    Workflow that performs a diffeomorphic registration
    (Rigid and Affine followed by Diffeomorphic)
    Note: the requirements for a diffeomorphic registration specify that
    the dimension 0 is a power of 2 so images are resliced prior to
    registration. Remember to move origin and reslice prior to applying xfm to
    another file!

    Example
    -------

    >>> from nipype.workflows.dmri.dtitk.tensor_registration import diffeomorphic_tensor_pipeline
    >>> diffeo = diffeomorphic_tensor_pipeline()
    >>> diffeo.inputs.inputnode.fixed_file = 'im1.nii'
    >>> diffeo.inputs.inputnode.moving_file = 'im2.nii'
    >>> diffeo.run() # doctest: +SKIP


    """
    inputnode = pe.Node(niu.IdentityInterface(
                        fields=['fixed_file', 'moving_file']),
                        name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(
                         fields=['out_file', 'out_file_xfm',
                                 'fixed_resliced', 'moving_resliced']),
                         name='outputnode')
    origin_node_fixed = pe.Node(dtitk.TVAdjustVoxSp(origin=(0, 0, 0)),
                                name='origin_node_fixed')
    origin_node_moving = origin_node_fixed.clone(name='origin_node_moving')
    reslice_node_pow2 = pe.Node(dtitk.TVResample(
                                origin=(0, 0, 0),
                                array_size=params['array_size']),
                                name='reslice_node_pow2')
    reslice_node_moving = pe.Node(dtitk.TVResample(),
                                  name='reslice_node_moving')
    mask_node = pe.Node(dtitk.BinThresh(lower_bound=0.01, upper_bound=100,
                                        inside_value=1, outside_value=0),
                        name='mask_node')
    rigid_node = pe.Node(dtitk.Rigid(), name='rigid_node')
    affine_node = pe.Node(dtitk.Affine(), name='affine_node')
    diffeo_node = pe.Node(dtitk.Diffeo(n_iters=6, ftol=0.002),
                          name='diffeo_node')
    compose_xfm_node = pe.Node(dtitk.ComposeXfm(), name='compose_xfm_node')
    apply_xfm_node = pe.Node(dtitk.DiffeoSymTensor3DVol(),
                             name='apply_xfm_node')
    adjust_vs_node_to_input = pe.Node(dtitk.TVAdjustVoxSp(),
                                      name='adjust_vs_node_to_input')
    reslice_node_to_input = pe.Node(dtitk.TVResample(),
                                    name='reslice_node_to_input')
    input_fa = pe.Node(dtitk.TVtool(in_flag='fa'), name='input_fa')

    wf = pe.Workflow(name=name)

    # calculate input FA image for origin reference
    wf.connect(inputnode, 'fixed_file', input_fa, 'in_file')
    # Reslice input images
    wf.connect(inputnode, 'fixed_file', origin_node_fixed, 'in_file')
    wf.connect(origin_node_fixed, 'out_file', reslice_node_pow2, 'in_file')
    wf.connect(reslice_node_pow2, 'out_file',
               reslice_node_moving, 'target_file')
    wf.connect(inputnode, 'moving_file', origin_node_moving, 'in_file')
    wf.connect(origin_node_moving, 'out_file', reslice_node_moving, 'in_file')
    # Rigid registration
    wf.connect(reslice_node_pow2, 'out_file', rigid_node, 'fixed_file')
    wf.connect(reslice_node_moving, 'out_file', rigid_node, 'moving_file')
    # Affine registration
    wf.connect(rigid_node, 'out_file_xfm', affine_node, 'initialize_xfm')
    wf.connect(reslice_node_pow2, 'out_file', affine_node, 'fixed_file')
    wf.connect(reslice_node_moving, 'out_file', affine_node, 'moving_file')
    # Diffeo registration
    wf.connect(reslice_node_pow2, 'out_file', mask_node, 'in_file')
    wf.connect(reslice_node_pow2, 'out_file', diffeo_node, 'fixed_file')
    wf.connect(affine_node, 'out_file', diffeo_node, 'moving_file')
    wf.connect(mask_node, 'out_file', diffeo_node, 'mask_file')
    # Compose transform
    wf.connect(diffeo_node, 'out_file_xfm', compose_xfm_node, 'in_df')
    wf.connect(affine_node, 'out_file_xfm', compose_xfm_node, 'in_aff')
    # Apply transform
    wf.connect(reslice_node_moving, 'out_file', apply_xfm_node, 'in_file')
    wf.connect(compose_xfm_node, 'out_file', apply_xfm_node, 'transform')
    # Move origin and reslice to match original fixed input image
    wf.connect(apply_xfm_node, 'out_file', adjust_vs_node_to_input, 'in_file')
    wf.connect(input_fa, 'out_file', adjust_vs_node_to_input, 'target_file')
    wf.connect(adjust_vs_node_to_input, 'out_file', reslice_node_to_input, 'in_file')
    wf.connect(input_fa, 'out_file', reslice_node_to_input, 'target_file')
    # Send to output
    wf.connect(reslice_node_to_input, 'out_file', outputnode, 'out_file')
    wf.connect(compose_xfm_node, 'out_file', outputnode, 'out_file_xfm')
    wf.connect(reslice_node_pow2, 'out_file', outputnode, 'fixed_resliced')
    wf.connect(reslice_node_moving, 'out_file', outputnode, 'moving_resliced')

    return wf
