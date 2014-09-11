# coding: utf-8

import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces import fsl
import os

#backwards compatibility
from epi import create_eddy_correct_pipeline


def transpose(samples_over_fibres):
    import numpy as np
    a = np.array(samples_over_fibres)
    return np.squeeze(a.T).tolist()


def create_bedpostx_pipeline(name='bedpostx', params={}):
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

    inputnode = pe.Node(niu.IdentityInterface(fields=['dwi', 'mask',
                        'bvecs', 'bvals']), name='inputnode')

    slice_dwi = pe.Node(fsl.Split(dimension='z'), name='slice_dwi')
    slice_msk = pe.Node(fsl.Split(dimension='z'), name='slice_msk')
    mask_dwi = pe.MapNode(fsl.ImageMaths(op_string='-mas'),
                          iterfield=['in_file', 'in_file2'], name='mask_dwi')

    xfib_if = fsl.XFibres(**params)
    xfibres = pe.MapNode(xfib_if, name='xfibres',
                         iterfield=['dwi', 'mask'])

    make_dyads = pe.MapNode(fsl.MakeDyadicVectors(), name="make_dyads",
                            iterfield=['theta_vol', 'phi_vol'])
    out_fields = ['dyads', 'dyads_disp',
                  'thsamples', 'phsamples', 'fsamples',
                  'mean_thsamples', 'mean_phsamples', 'mean_fsamples']

    outputnode = pe.Node(niu.IdentityInterface(fields=out_fields),
                         name='outputnode')

    wf = pe.Workflow(name=name)
    wf.connect([
        (inputnode, slice_dwi,  [('dwi', 'in_file')]),
        (inputnode, slice_msk,  [('mask', 'in_file')]),
        (slice_dwi, mask_dwi,   [('out_files', 'in_file')]),
        (slice_msk, mask_dwi,   [('out_files', 'in_file2')]),
        (slice_dwi, xfibres,    [('out_files', 'dwi')]),
        (mask_dwi, xfibres,     [('out_file', 'mask')]),
        (inputnode, xfibres,    [('bvecs', 'bvecs'),
                                 ('bvals', 'bvals')]),
        (inputnode, make_dyads, [('mask', 'mask')])
    ])

    mms = {}
    for k in ['thsamples', 'phsamples', 'fsamples']:
        mms[k] = merge_and_mean(k)
        wf.connect([
            (xfibres, mms[k], [(k, 'inputnode.in_files')]),
            (mms[k], outputnode, [('outputnode.merged', k),
                                  ('outputnode.mean', 'mean_%s' % k)])

        ])

    # m_mdsamples = pe.Node(fsl.Merge(dimension="z"),
    #                       name="merge_mean_dsamples")
    wf.connect([
        (mms['thsamples'], make_dyads, [('outputnode.merged', 'theta_vol')]),
        (mms['phsamples'], make_dyads, [('outputnode.merged', 'phi_vol')]),
        #(xfibres, m_mdsamples,  [('mean_dsamples', 'in_files')]),
        (make_dyads, outputnode, [('dyads', 'dyads'),
                                  ('dispersion', 'dyads_disp')])
    ])
    return wf


def merge_and_mean(name='mm'):
    inputnode = pe.Node(niu.IdentityInterface(fields=['in_files']),
                        name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(fields=['merged', 'mean']),
                         name='outputnode')
    merge = pe.MapNode(fsl.Merge(dimension='z'), name='Merge',
                       iterfield=['in_files'])
    mean = pe.MapNode(fsl.ImageMaths(op_string='-Tmean'), name='Mean',
                      iterfield=['in_file'])

    wf = pe.Workflow(name=name)
    wf.connect([
        (inputnode, merge,  [(('in_files', transpose), 'in_files')]),
        (merge, mean,       [('merged_file', 'in_file')]),
        (merge, outputnode, [('merged_file', 'merged')]),
        (mean, outputnode,  [('out_file', 'mean')])
    ])
    return wf


def gen_chunks(dwi, mask, nchunks=6):
    import nibabel as nb
    import numpy as np

    mask = nb.load(mask).get_data()
    mask[mask > 0] = 1
    mask[mask < 1] = 0
    nzels = np.nonzero(mask)
    np.savetxt('nonzeroidx.txt', nzels)

    dshape = mask.shape
    mask = mask.reshape(-1).astype(np.uint8)
    els = np.sum(mask)
    chunkels = round(els / nchunks)

    data = mask.copy()

    out_files = []
    out_masks = []

    for i in xrange(chunkels):
        first = i * chunkels
        last = (i+1) * chunkels + 1

        chunk = data[first:last, ...]

        fname = 'chunk%05d.nii.gz' % i
        nb.Nifti1Image(chunk, None, None).to_filename(fname)
        out_files.append(fname)

        mname = 'mask%05d.nii.gz' % i
        nb.Nifti1Image(mask[first:last],
                       None, None).to_filename(mname)
        out_masks.append(mname)

    return out_files, out_masks

