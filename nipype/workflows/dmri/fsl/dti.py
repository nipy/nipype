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

    out_fields = xfib_if.output_spec().get().keys()

    outputnode = pe.Node(niu.IdentityInterface(fields=out_fields),
                         name='outputnode')

    wf = pe.Workflow(name=name)
    wf.connect([
        (inputnode, slice_dwi, [('dwi', 'in_file')]),
        (inputnode, slice_msk, [('mask', 'in_file')]),
        (slice_dwi, mask_dwi,  [('out_files', 'in_file')]),
        (slice_msk, mask_dwi,  [('out_files', 'in_file2')]),
        (slice_dwi, xfibres,   [('out_files', 'dwi')]),
        (mask_dwi, xfibres,    [('out_file', 'mask')]),
        (inputnode, xfibres,   [('bvecs', 'bvecs'),
                                ('bvals', 'bvals')]),
        (xfibres, outputnode,  [((f, transpose), f) for f in out_fields])
    ])

    return wf
