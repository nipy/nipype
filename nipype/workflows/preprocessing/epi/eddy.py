# coding: utf-8
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

import nipype.pipeline.engine as pe
from nipype.interfaces.io import JSONFileGrabber
from nipype.interfaces import utility as niu
from nipype.interfaces import freesurfer as fs
from nipype.interfaces import ants
from nipype.interfaces import fsl
from .utils import *

def ecc_fsl(name='eddy_correct'):
    """
    ECC stands for Eddy currents correction.

    Creates a pipeline that corrects for artifacts induced by Eddy currents in
    dMRI sequences.
    It takes a series of diffusion weighted images and linearly co-registers
    them to one reference image (the average of all b0s in the dataset).

    DWIs are also modulated by the determinant of the Jacobian as indicated by
    [Jones10]_ and [Rohde04]_.

    A list of rigid transformation matrices can be provided, sourcing from a
    :func:`.hmc_pipeline` workflow, to initialize registrations in a *motion
    free* framework.

    A list of affine transformation matrices is available as output, so that
    transforms can be chained (discussion
    `here <https://github.com/nipy/nipype/pull/530#issuecomment-14505042>`_).

    .. admonition:: References

      .. [Jones10] Jones DK, `The signal intensity must be modulated by the
        determinant of the Jacobian when correcting for eddy currents in
        diffusion MRI
        <http://cds.ismrm.org/protected/10MProceedings/files/1644_129.pdf>`_,
        Proc. ISMRM 18th Annual Meeting, (2010).

      .. [Rohde04] Rohde et al., `Comprehensive Approach for Correction of
        Motion and Distortion in Diffusion-Weighted MRI
        <http://stbb.nichd.nih.gov/pdf/com_app_cor_mri04.pdf>`_, MRM
        51:103-114 (2004).

    Example
    -------

    >>> from nipype.workflows.dmri.fsl.artifacts import ecc_pipeline
    >>> ecc = ecc_pipeline()
    >>> ecc.inputs.inputnode.in_file = 'diffusion.nii'
    >>> ecc.inputs.inputnode.in_bval = 'diffusion.bval'
    >>> ecc.inputs.inputnode.in_mask = 'mask.nii'
    >>> ecc.run() # doctest: +SKIP

    Inputs::

        inputnode.in_file - input dwi file
        inputnode.in_mask - weights mask of reference image (a file with data \
range sin [0.0, 1.0], indicating the weight of each voxel when computing the \
metric.
        inputnode.in_bval - b-values table
        inputnode.in_xfms - list of matrices to initialize registration (from \
head-motion correction)

    Outputs::

        outputnode.out_file - corrected dwi file
        outputnode.out_xfms - list of transformation matrices
    """

    from nipype.workflows.data import get_flirt_schedule
    params = dict(dof=12, no_search=True, interp='spline', bgvalue=0,
                  schedule=get_flirt_schedule('ecc'))
    # cost='normmi', cost_func='normmi', bins=64,

    inputnode = pe.Node(niu.IdentityInterface(
        fields=['in_file', 'in_bval', 'in_mask', 'in_xfms']), name='inputnode')
    avg_b0 = pe.Node(niu.Function(
        input_names=['in_dwi', 'in_bval'], output_names=['out_file'],
        function=b0_average), name='b0_avg')
    pick_dws = pe.Node(niu.Function(
        input_names=['in_dwi', 'in_bval', 'b'], output_names=['out_file'],
        function=extract_bval), name='ExtractDWI')
    pick_dws.inputs.b = 'diff'

    flirt = dwi_flirt(flirt_param=params, excl_nodiff=True)

    mult = pe.MapNode(fsl.BinaryMaths(operation='mul'), name='ModulateDWIs',
                      iterfield=['in_file', 'operand_value'])
    thres = pe.MapNode(fsl.Threshold(thresh=0.0), iterfield=['in_file'],
                       name='RemoveNegative')

    split = pe.Node(fsl.Split(dimension='t'), name='SplitDWIs')
    get_mat = pe.Node(niu.Function(
        input_names=['in_bval', 'in_xfms'], output_names=['out_files'],
        function=recompose_xfm), name='GatherMatrices')
    merge = pe.Node(niu.Function(
        input_names=['in_dwi', 'in_bval', 'in_corrected'],
        output_names=['out_file'], function=recompose_dwi), name='MergeDWIs')

    outputnode = pe.Node(niu.IdentityInterface(
        fields=['out_file', 'out_xfms']), name='outputnode')

    wf = pe.Workflow(name=name)
    wf.connect([
        (inputnode,  avg_b0,     [('in_file', 'in_dwi'),
                                  ('in_bval', 'in_bval')]),
        (inputnode,  pick_dws,   [('in_file', 'in_dwi'),
                                  ('in_bval', 'in_bval')]),
        (inputnode,  merge,      [('in_file', 'in_dwi'),
                                  ('in_bval', 'in_bval')]),
        (inputnode,  flirt,      [('in_mask', 'inputnode.ref_mask'),
                                  ('in_xfms', 'inputnode.in_xfms'),
                                  ('in_bval', 'inputnode.in_bval')]),
        (inputnode,  get_mat,    [('in_bval', 'in_bval')]),
        (avg_b0,     flirt,      [('out_file', 'inputnode.reference')]),
        (pick_dws,   flirt,      [('out_file', 'inputnode.in_file')]),
        (flirt,      get_mat,    [('outputnode.out_xfms', 'in_xfms')]),
        (flirt,      mult,       [(('outputnode.out_xfms', _xfm_jacobian),
                                   'operand_value')]),
        (flirt,      split,      [('outputnode.out_file', 'in_file')]),
        (split,      mult,       [('out_files', 'in_file')]),
        (mult,       thres,      [('out_file', 'in_file')]),
        (thres,      merge,      [('out_file', 'in_corrected')]),
        (get_mat,    outputnode, [('out_files', 'out_xfms')]),
        (merge,      outputnode, [('out_file', 'out_file')])
    ])
    return wf
