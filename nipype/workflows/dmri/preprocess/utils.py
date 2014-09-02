#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# @Author: oesteban
# @Date:   2014-08-30 10:53:13
# @Last Modified by:   Oscar Esteban
# @Last Modified time: 2014-09-02 13:17:12

def cleanup_edge_pipeline(name='Cleanup'):
    """
    Perform some de-spiking filtering to clean up the edge of the fieldmap
    (copied from fsl_prepare_fieldmap)
    """
    import nipype.pipeline.engine as pe
    import nipype.interfaces.utility as niu
    import nipype.interfaces.fsl as fsl

    inputnode = pe.Node(niu.IdentityInterface(fields=['in_file', 'in_mask']),
                        name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(fields=['out_file']),
                         name='outputnode')

    fugue = pe.Node(fsl.FUGUE(save_fmap=True, despike_2dfilter=True, despike_threshold=2.1),
                    name='Despike')
    erode = pe.Node(fsl.maths.MathsCommand(nan2zeros=True,
                    args='-kernel 2D -ero'), name='MskErode')
    newmsk = pe.Node(fsl.MultiImageMaths(op_string='-sub %s -thr 0.5 -bin'),
                     name='NewMask')
    applymsk = pe.Node(fsl.ApplyMask(nan2zeros=True), name='ApplyMask')
    join = pe.Node(niu.Merge(2), name='Merge')
    addedge = pe.Node(fsl.MultiImageMaths(op_string='-mas %s -add %s'),
                      name='AddEdge')

    wf = pe.Workflow(name=name)
    wf.connect([
         (inputnode,     fugue,      [('in_file', 'fmap_in_file'),
                                      ('in_mask', 'mask_file')])
        ,(inputnode,     erode,      [('in_mask', 'in_file')])
        ,(inputnode,     newmsk,     [('in_mask', 'in_file')])
        ,(erode,         newmsk,     [('out_file', 'operand_files')])
        ,(fugue,         applymsk,   [('fmap_out_file', 'in_file')])
        ,(newmsk,        applymsk,   [('out_file', 'mask_file')])
        ,(erode,         join,       [('out_file', 'in1')])
        ,(applymsk,      join,       [('out_file', 'in2')])
        ,(inputnode,     addedge,    [('in_file', 'in_file')])
        ,(join,          addedge,     [('out', 'operand_files')])
        ,(addedge,       outputnode, [('out_file', 'out_file')])
    ])
    return wf


def recompose_dwi(in_dwi, in_bval, in_corrected, out_file=None):
    """
    Recompose back the dMRI data accordingly the b-values table after EC correction
    """
    import numpy as np
    import nibabel as nb
    import os.path as op

    if out_file is None:
        fname,ext = op.splitext(op.basename(in_dwi))
        if ext == ".gz":
            fname,ext2 = op.splitext(fname)
            ext = ext2 + ext
        out_file = op.abspath("%s_eccorrect%s" % (fname, ext))

    im = nb.load(in_dwi)
    dwidata = im.get_data()
    bvals = np.loadtxt(in_bval)
    non_b0 = np.where(bvals!=0)[0].tolist()

    if len(non_b0)!=len(in_corrected):
        raise RuntimeError('Length of DWIs in b-values table and after correction should match')

    for bindex, dwi in zip(non_b0, in_corrected):
        dwidata[...,bindex] = nb.load(dwi).get_data()

    nb.Nifti1Image(dwidata, im.get_affine(), im.get_header()).to_filename(out_file)
    return out_file

def recompose_xfm(in_bval, in_xfms):
    """
    Insert identity transformation matrices in b0 volumes to build up a list
    """
    import numpy as np
    import os.path as op

    bvals = np.loadtxt(in_bval)
    out_matrix = np.array([np.eye(4)] * len(bvals))
    xfms = iter([np.loadtxt(xfm) for xfm in in_xfms])
    out_files = []

    for i, b in enumerate(bvals):
        if b == 0.0:
            mat = np.eye(4)
        else:
            mat = xfms.next()

        out_name = 'eccor_%04d.mat' % i
        out_files.append(out_name)
        np.savetxt(out_name, mat)

    return out_files


def b0_average(in_dwi, in_bval, out_file=None):
    """
    A function that averages the *b0* volumes from a DWI dataset.

    .. warning:: *b0* should be already registered (head motion artifact should
      be corrected).

    """
    import numpy as np
    import nibabel as nb
    import os.path as op

    if out_file is None:
        fname,ext = op.splitext(op.basename(in_dwi))
        if ext == ".gz":
            fname,ext2 = op.splitext(fname)
            ext = ext2 + ext
        out_file = op.abspath("%s_avg_b0%s" % (fname, ext))

    imgs = np.array(nb.four_to_three(nb.load(in_dwi)))
    bval = np.loadtxt(in_bval)
    b0s = [im.get_data().astype(np.float32) for im in imgs[np.where(bval==0)]]
    b0 = np.average(np.array(b0s), axis=0)

    hdr = imgs[0].get_header().copy()
    hdr.set_data_shape(b0.shape)
    hdr.set_xyzt_units('mm')
    hdr.set_data_dtype(np.float32)
    nb.Nifti1Image(b0, imgs[0].get_affine(), hdr).to_filename(out_file)
    return out_file


def rotate_bvecs(in_bvec, in_matrix):
    """
    Rotates the input bvec file accordingly with a list of matrices.

    .. note:: the input affine matrix transforms points in the destination image to their \
    corresponding coordinates in the original image. Therefore, this matrix should be inverted \
    first, as we want to know the target position of :math:`\\vec{r}`.

    """
    import os
    import numpy as np

    name, fext = os.path.splitext(os.path.basename(in_bvec))
    if fext == '.gz':
        name, _ = os.path.splitext(name)
    out_file = os.path.abspath('./%s_rotated.bvec' % name)
    bvecs = np.loadtxt(in_bvec).T
    new_bvecs = []

    if len(bvecs) != len(in_matrix):
        raise RuntimeError('Number of b-vectors and rotation matrices should match.')

    for bvec, mat in zip(bvecs, in_matrix):
        if np.all(bvec == 0.0):
            new_bvecs.append(bvec)
        else:
            invrot = np.linalg.inv(np.loadtxt(mat))[:3,:3]
            newbvec = invrot.dot(bvec)
            new_bvecs.append((newbvec/np.linalg.norm(newbvec)))

    np.savetxt(out_file, np.array(new_bvecs).T, fmt='%0.15f')
    return out_file


def eddy_rotate_bvecs(in_bvec, eddy_params):
    """
    Rotates the input bvec file accordingly with a list of parameters sourced
    from ``eddy``, as explained `here
    <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/EDDY/Faq#Will_eddy_rotate_my_bevcs_for_me.3F>`_.
    """
    import os
    import numpy as np
    from math import sin, cos

    name, fext = os.path.splitext(os.path.basename(in_bvec))
    if fext == '.gz':
        name, _ = os.path.splitext(name)
    out_file = os.path.abspath('%s_rotated.bvec' % name)
    bvecs = np.loadtxt(in_bvec).T
    new_bvecs = []

    params = np.loadtxt(eddy_params)

    if len(bvecs) != len(params):
        raise RuntimeError('Number of b-vectors and rotation matrices should match.')

    for bvec, row in zip(bvecs, params):
        if np.all(bvec == 0.0):
            new_bvecs.append(bvec)
        else:
            ax = row[3]
            ay = row[4]
            az = row[5]

            Rx = np.array([[1.0, 0.0, 0.0], [0.0, cos(ax), -sin(ax)], [0.0, sin(ax), cos(ax)]])
            Ry = np.array([[cos(ay), 0.0, sin(ay)], [0.0, 1.0, 0.0], [-sin(ay), 0.0, cos(ay)]])
            Rz = np.array([[cos(az), -sin(az), 0.0], [sin(az), cos(az), 0.0], [0.0, 0.0, 1.0]])
            R = Rx.dot(Ry).dot(Rz)

            invrot = np.linalg.inv(R)
            newbvec = invrot.dot(bvec)
            new_bvecs.append((newbvec/np.linalg.norm(newbvec)))

    np.savetxt(out_file, np.array(new_bvecs).T, fmt='%0.15f')
    return out_file


def compute_readout(params):
    """
    Computes readout time from epi params (see `eddy documentation
    <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/EDDY/Faq#How_do_I_know_what_to_put_into_my_--acqp_file.3F>`_).

    .. warning:: ``params['echospacing']`` should be in *sec* units.


    """
    epi_factor = 1.0
    acc_factor = 1.0
    try:
        if params['epi_factor'] > 1:
            epi_factor = float(params['epi_factor'] - 1)
    except:
        pass
    try:
        if params['acc_factor'] > 1:
            acc_factor = 1.0 / params['acc_factor']
    except:
        pass
    return acc_factor * epi_factor * params['echospacing']


def siemens2rads(in_file, out_file=None):
    """
    Converts input phase difference map to rads
    """
    import numpy as np
    import nibabel as nb
    import os.path as op
    import math

    if out_file is None:
        fname, fext = op.splitext(op.basename(in_file))
        if fext == '.gz':
            fname, _ = op.splitext(fname)
        out_file = op.abspath('./%s_rads.nii.gz' % fname)

    in_file = np.atleast_1d(in_file).tolist()
    im = nb.load(in_file[0])
    data = im.get_data().astype(np.float32)
    hdr = im.get_header().copy()

    if len(in_file) == 2:
        data = nb.load(in_file[1]).get_data().astype(np.float32) - data
    elif (data.ndim == 4) and (data.shape[-1] == 2):
        data = np.squeeze(data[...,1] - data[...,0])
        hdr.set_data_shape(data.shape[:3])

    imin = data.min()
    imax = data.max()
    data = (2.0 * math.pi * (data - imin)/(imax-imin)) - math.pi
    hdr.set_data_dtype(np.float32)
    hdr.set_xyzt_units('mm')
    hdr['datatype'] = 16
    nb.Nifti1Image(data, im.get_affine(), hdr).to_filename(out_file)
    return out_file

def rads2radsec(in_file, delta_te, out_file=None):
    """
    Converts input phase difference map to rads
    """
    import numpy as np
    import nibabel as nb
    import os.path as op
    import math

    if out_file is None:
        fname, fext = op.splitext(op.basename(in_file))
        if fext == '.gz':
            fname, _ = op.splitext(fname)
        out_file = op.abspath('./%s_radsec.nii.gz' % fname)

    im = nb.load(in_file)
    data = im.get_data().astype(np.float32) * (1.0/delta_te)
    nb.Nifti1Image(data, im.get_affine(),
                   im.get_header()).to_filename(out_file)
    return out_file

def demean_image(in_file, in_mask=None, out_file=None):
    """
    Demean image data inside mask
    """
    import numpy as np
    import nibabel as nb
    import os.path as op
    import math

    if out_file is None:
        fname, fext = op.splitext(op.basename(in_file))
        if fext == '.gz':
            fname, _ = op.splitext(fname)
        out_file = op.abspath('./%s_demean.nii.gz' % fname)

    im = nb.load(in_file)
    data = im.get_data().astype(np.float32)
    msk = np.ones_like(data)

    if not in_mask is None:
        msk = nb.load(in_mask).get_data().astype(np.float32)
        msk[msk>0] = 1.0
        msk[msk<1] = 0.0

    mean = np.median(data[msk==1].reshape(-1))
    data[msk==1] = data[msk==1] - mean
    nb.Nifti1Image(data, im.get_affine(), im.get_header()).to_filename(out_file)
    return out_file


def add_empty_vol(in_file, out_file=None):
    """
    Adds an empty vol to the phase difference image
    """
    import nibabel as nb
    import os.path as op
    import numpy as np
    import math

    if out_file is None:
        fname, fext = op.splitext(op.basename(in_file))
        if fext == '.gz':
            fname, _ = op.splitext(fname)
        out_file = op.abspath('./%s_4D.nii.gz' % fname)

    im = nb.load(in_file)
    zim = nb.Nifti1Image(np.zeros_like(im.get_data()), im.get_affine(),
                         im.get_header())
    nb.funcs.concat_images([im, zim]).to_filename(out_file)
    return out_file
