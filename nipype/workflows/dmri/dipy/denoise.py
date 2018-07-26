# -*- coding: utf-8 -*-
# coding: utf-8
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from builtins import range
from ....pipeline import engine as pe
from ....interfaces import utility as niu
from ....interfaces import dipy


def nlmeans_pipeline(name='Denoise',
                     params={
                         'patch_radius': 1,
                         'block_radius': 5
                     }):
    """
    Workflow that performs nlmeans denoising

    Example
    -------

    >>> from nipype.workflows.dmri.dipy.denoise import nlmeans_pipeline
    >>> denoise = nlmeans_pipeline()
    >>> denoise.inputs.inputnode.in_file = 'diffusion.nii'
    >>> denoise.inputs.inputnode.in_mask = 'mask.nii'
    >>> denoise.run() # doctest: +SKIP


    """
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['in_file', 'in_mask']), name='inputnode')
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['out_file']), name='outputnode')

    nmask = pe.Node(
        niu.Function(
            input_names=['in_file', 'in_mask'],
            output_names=['out_file'],
            function=bg_mask),
        name='NoiseMsk')
    nlmeans = pe.Node(dipy.Denoise(**params), name='NLMeans')

    wf = pe.Workflow(name=name)
    wf.connect([(inputnode, nmask, [
        ('in_file', 'in_file'), ('in_mask', 'in_mask')
    ]), (inputnode, nlmeans, [('in_file', 'in_file'), ('in_mask', 'in_mask')]),
                (nmask, nlmeans, [('out_file', 'noise_mask')]),
                (nlmeans, outputnode, [('out_file', 'out_file')])])
    return wf


def csf_mask(in_file, in_mask, out_file=None):
    """
    Artesanal mask of csf in T2w-like images
    """
    import nibabel as nb
    import numpy as np
    from scipy.ndimage import binary_erosion, binary_opening, label
    import scipy.ndimage as nd
    import os.path as op
    from nipype.utils import NUMPY_MMAP

    if out_file is None:
        fname, ext = op.splitext(op.basename(in_file))
        if ext == ".gz":
            fname, ext2 = op.splitext(fname)
            ext = ext2 + ext
        out_file = op.abspath("%s_csfmask%s" % (fname, ext))

    im = nb.load(in_file, mmap=NUMPY_MMAP)
    hdr = im.header.copy()
    hdr.set_data_dtype(np.uint8)
    hdr.set_xyzt_units('mm')
    imdata = im.get_data()
    msk = nb.load(in_mask, mmap=NUMPY_MMAP).get_data()
    msk = binary_erosion(msk, structure=np.ones((15, 15, 10))).astype(np.uint8)
    thres = np.percentile(imdata[msk > 0].reshape(-1), 90.0)
    imdata[imdata < thres] = 0
    imdata = imdata * msk
    imdata[imdata > 0] = 1
    imdata = binary_opening(
        imdata, structure=np.ones((2, 2, 2))).astype(np.uint8)

    label_im, nb_labels = label(imdata)
    sizes = nd.sum(imdata, label_im, list(range(nb_labels + 1)))
    mask_size = sizes != sizes.max()
    remove_pixel = mask_size[label_im]
    label_im[remove_pixel] = 0
    label_im[label_im > 0] = 1
    nb.Nifti1Image(label_im.astype(np.uint8), im.affine,
                   hdr).to_filename(out_file)
    return out_file


def bg_mask(in_file, in_mask, out_file=None):
    """
    Rough mask of background from brain masks
    """
    import nibabel as nb
    import numpy as np
    from scipy.ndimage import binary_dilation
    import scipy.ndimage as nd
    import os.path as op
    from nipype.utils import NUMPY_MMAP

    if out_file is None:
        fname, ext = op.splitext(op.basename(in_file))
        if ext == ".gz":
            fname, ext2 = op.splitext(fname)
            ext = ext2 + ext
        out_file = op.abspath("%s_bgmask%s" % (fname, ext))

    im = nb.load(in_file, mmap=NUMPY_MMAP)
    hdr = im.header.copy()
    hdr.set_data_dtype(np.uint8)
    hdr.set_xyzt_units('mm')
    msk = nb.load(in_mask, mmap=NUMPY_MMAP).get_data()
    msk = 1 - binary_dilation(msk, structure=np.ones((20, 20, 20)))
    nb.Nifti1Image(msk.astype(np.uint8), im.affine, hdr).to_filename(out_file)
    return out_file
