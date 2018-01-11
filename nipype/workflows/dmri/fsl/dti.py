# -*- coding: utf-8 -*-
# coding: utf-8

from __future__ import absolute_import

from ....pipeline import engine as pe
from ....interfaces import utility as niu
from ....interfaces import fsl
from ....algorithms import misc

# backwards compatibility
from .epi import create_eddy_correct_pipeline


def transpose(samples_over_fibres):
    import numpy as np
    a = np.array(samples_over_fibres)
    return np.squeeze(a.T).tolist()


def create_bedpostx_pipeline(
        name='bedpostx',
        params={
            'n_fibres': 2,
            'fudge': 1,
            'burn_in': 1000,
            'n_jumps': 1250,
            'sample_every': 25,
            'model': 2,
            'cnlinear': True
        }):
    """
    Creates a pipeline that does the same as bedpostx script from FSL -
    calculates diffusion model parameters (distributions not MLE) voxelwise for
    the whole volume (by splitting it slicewise).

    Example
    -------

    >>> from nipype.workflows.dmri.fsl.dti import create_bedpostx_pipeline
    >>> params = dict(n_fibres = 2, fudge = 1, burn_in = 1000,
    ...               n_jumps = 1250, sample_every = 25)
    >>> bpwf = create_bedpostx_pipeline('nipype_bedpostx', params)
    >>> bpwf.inputs.inputnode.dwi = 'diffusion.nii'
    >>> bpwf.inputs.inputnode.mask = 'mask.nii'
    >>> bpwf.inputs.inputnode.bvecs = 'bvecs'
    >>> bpwf.inputs.inputnode.bvals = 'bvals'
    >>> bpwf.run() # doctest: +SKIP

    Inputs::

        inputnode.dwi
        inputnode.mask
        inputnode.bvecs
        inputnode.bvals

    Outputs::

        outputnode wraps all XFibres outputs

    """

    inputnode = pe.Node(
        niu.IdentityInterface(fields=['dwi', 'mask', 'bvecs', 'bvals']),
        name='inputnode')

    slice_dwi = pe.Node(fsl.Split(dimension='z'), name='slice_dwi')
    slice_msk = pe.Node(fsl.Split(dimension='z'), name='slice_msk')
    mask_dwi = pe.MapNode(
        fsl.ImageMaths(op_string='-mas'),
        iterfield=['in_file', 'in_file2'],
        name='mask_dwi')

    xfib_if = fsl.XFibres(**params)
    xfibres = pe.MapNode(xfib_if, name='xfibres', iterfield=['dwi', 'mask'])

    make_dyads = pe.MapNode(
        fsl.MakeDyadicVectors(),
        name="make_dyads",
        iterfield=['theta_vol', 'phi_vol'])
    out_fields = [
        'dyads', 'dyads_disp', 'thsamples', 'phsamples', 'fsamples',
        'mean_thsamples', 'mean_phsamples', 'mean_fsamples'
    ]

    outputnode = pe.Node(
        niu.IdentityInterface(fields=out_fields), name='outputnode')

    wf = pe.Workflow(name=name)
    wf.connect(
        [(inputnode, slice_dwi, [('dwi', 'in_file')]), (inputnode, slice_msk,
                                                        [('mask', 'in_file')]),
         (slice_dwi, mask_dwi,
          [('out_files', 'in_file')]), (slice_msk, mask_dwi, [('out_files',
                                                               'in_file2')]),
         (slice_dwi, xfibres,
          [('out_files', 'dwi')]), (mask_dwi, xfibres, [('out_file', 'mask')]),
         (inputnode, xfibres, [('bvecs', 'bvecs'),
                               ('bvals', 'bvals')]), (inputnode, make_dyads,
                                                      [('mask', 'mask')])])

    mms = {}
    for k in ['thsamples', 'phsamples', 'fsamples']:
        mms[k] = merge_and_mean(k)
        wf.connect([(xfibres, mms[k], [(k, 'inputnode.in_files')]),
                    (mms[k], outputnode, [('outputnode.merged', k),
                                          ('outputnode.mean',
                                           'mean_%s' % k)])])

    # m_mdsamples = pe.Node(fsl.Merge(dimension="z"),
    #                       name="merge_mean_dsamples")
    wf.connect([
        (mms['thsamples'], make_dyads, [('outputnode.merged', 'theta_vol')]),
        (mms['phsamples'], make_dyads, [('outputnode.merged', 'phi_vol')]),
        # (xfibres, m_mdsamples,  [('mean_dsamples', 'in_files')]),
        (make_dyads, outputnode, [('dyads', 'dyads'), ('dispersion',
                                                       'dyads_disp')])
    ])
    return wf


def merge_and_mean(name='mm'):
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['in_files']), name='inputnode')
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['merged', 'mean']), name='outputnode')
    merge = pe.MapNode(
        fsl.Merge(dimension='z'), name='Merge', iterfield=['in_files'])
    mean = pe.MapNode(
        fsl.ImageMaths(op_string='-Tmean'), name='Mean', iterfield=['in_file'])

    wf = pe.Workflow(name=name)
    wf.connect([(inputnode, merge, [(('in_files', transpose), 'in_files')]),
                (merge, mean, [('merged_file', 'in_file')]),
                (merge, outputnode,
                 [('merged_file', 'merged')]), (mean, outputnode, [('out_file',
                                                                    'mean')])])
    return wf


def bedpostx_parallel(
        name='bedpostx_parallel',
        compute_all_outputs=True,
        params={
            'n_fibres': 2,
            'fudge': 1,
            'burn_in': 1000,
            'n_jumps': 1250,
            'sample_every': 25,
            'model': 1,
            'cnlinear': True
        }):
    """
    Does the same as :func:`.create_bedpostx_pipeline` by splitting
    the input dMRI in small ROIs that are better suited for parallel
    processing).

    Example
    -------

    >>> from nipype.workflows.dmri.fsl.dti import bedpostx_parallel
    >>> params = dict(n_fibres = 2, fudge = 1, burn_in = 1000,
    ...               n_jumps = 1250, sample_every = 25)
    >>> bpwf = bedpostx_parallel('nipype_bedpostx_parallel', params=params)
    >>> bpwf.inputs.inputnode.dwi = 'diffusion.nii'
    >>> bpwf.inputs.inputnode.mask = 'mask.nii'
    >>> bpwf.inputs.inputnode.bvecs = 'bvecs'
    >>> bpwf.inputs.inputnode.bvals = 'bvals'
    >>> bpwf.run(plugin='CondorDAGMan') # doctest: +SKIP

    Inputs::

        inputnode.dwi
        inputnode.mask
        inputnode.bvecs
        inputnode.bvals

    Outputs::

        outputnode wraps all XFibres outputs

    """

    inputnode = pe.Node(
        niu.IdentityInterface(fields=['dwi', 'mask', 'bvecs', 'bvals']),
        name='inputnode')
    slice_dwi = pe.Node(misc.SplitROIs(roi_size=(5, 5, 1)), name='slice_dwi')
    if params is not None:
        xfib_if = fsl.XFibres5(**params)
    else:
        xfib_if = fsl.XFibres5()
    xfibres = pe.MapNode(xfib_if, name='xfibres', iterfield=['dwi', 'mask'])

    mrg_dyads = pe.MapNode(
        misc.MergeROIs(), name='Merge_dyads', iterfield=['in_files'])
    mrg_fsamp = pe.MapNode(
        misc.MergeROIs(), name='Merge_mean_fsamples', iterfield=['in_files'])
    out_fields = ['dyads', 'fsamples']

    if compute_all_outputs:
        out_fields += [
            'dyads_disp', 'thsamples', 'phsamples', 'mean_fsamples',
            'mean_thsamples', 'mean_phsamples', 'merged_fsamples',
            'merged_thsamples', 'merged_phsamples'
        ]

    outputnode = pe.Node(
        niu.IdentityInterface(fields=out_fields), name='outputnode')

    wf = pe.Workflow(name=name)
    wf.connect(
        [(inputnode, slice_dwi, [('dwi', 'in_file'), ('mask', 'in_mask')]),
         (slice_dwi, xfibres, [('out_files', 'dwi'), ('out_masks', 'mask')]),
         (inputnode, xfibres,
          [('bvecs', 'bvecs'), ('bvals', 'bvals')]), (inputnode, mrg_dyads, [
              ('mask', 'in_reference')
          ]), (xfibres, mrg_dyads,
               [(('dyads', transpose), 'in_files')]), (slice_dwi, mrg_dyads, [
                   ('out_index', 'in_index')
               ]), (inputnode, mrg_fsamp,
                    [('mask', 'in_reference')]), (xfibres, mrg_fsamp, [
                        (('mean_fsamples', transpose), 'in_files')
                    ]), (slice_dwi, mrg_fsamp, [('out_index', 'in_index')]),
         (mrg_dyads, outputnode,
          [('merged_file', 'dyads')]), (mrg_fsamp, outputnode,
                                        [('merged_file', 'fsamples')])])

    if compute_all_outputs:
        make_dyads = pe.MapNode(
            fsl.MakeDyadicVectors(),
            name="Make_dyads",
            iterfield=['theta_vol', 'phi_vol'])

        wf.connect([(inputnode, make_dyads, [('mask', 'mask')])])
        mms = {}
        for k in ['thsamples', 'phsamples', 'fsamples']:
            mms[k] = merge_and_mean_parallel(k)
            wf.connect(
                [(slice_dwi, mms[k], [('out_index', 'inputnode.in_index')]),
                 (inputnode, mms[k], [('mask', 'inputnode.in_reference')]),
                 (xfibres, mms[k], [(k, 'inputnode.in_files')]),
                 (mms[k], outputnode, [('outputnode.merged', 'merged_%s' % k),
                                       ('outputnode.mean', 'mean_%s' % k)])])

        # m_mdsamples = pe.Node(fsl.Merge(dimension="z"),
        #                       name="merge_mean_dsamples")
        wf.connect([
            (mms['thsamples'], make_dyads, [('outputnode.merged',
                                             'theta_vol')]),
            (mms['phsamples'], make_dyads, [('outputnode.merged', 'phi_vol')]),
            # (xfibres, m_mdsamples,  [('mean_dsamples', 'in_files')]),
            (make_dyads, outputnode, [('dispersion', 'dyads_disp')])
        ])

    return wf


def merge_and_mean_parallel(name='mm'):
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['in_files', 'in_reference', 'in_index']),
        name='inputnode')
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['merged', 'mean']), name='outputnode')
    merge = pe.MapNode(misc.MergeROIs(), name='Merge', iterfield=['in_files'])
    mean = pe.MapNode(
        fsl.ImageMaths(op_string='-Tmean'), name='Mean', iterfield=['in_file'])

    wf = pe.Workflow(name=name)
    wf.connect([(inputnode, merge,
                 [(('in_files', transpose), 'in_files'),
                  ('in_reference', 'in_reference'), ('in_index', 'in_index')]),
                (merge, mean, [('merged_file', 'in_file')]),
                (merge, outputnode,
                 [('merged_file', 'merged')]), (mean, outputnode, [('out_file',
                                                                    'mean')])])
    return wf
