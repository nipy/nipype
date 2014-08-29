# coding: utf-8

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu
import nipype.interfaces.fsl as fsl
import os

def motion_correct(name='motion_correct'):
    """Creates a pipeline that corrects for head motion artifacts in dMRI sequences.
    It takes a series of diffusion weighted images and rigidly co-registers
    them to one reference image. Finally, the `b`-matrix is rotated accordingly [1]_
    making use of the rotation matrix obtained by FLIRT.

    Search angles have been limited to 3.5 degrees, based on results in [2]_.

    A list of rigid transformation matrices is provided, so that transforms can be
    chained. This is useful to correct for artifacts with only one interpolation process (as
    previously discussed `here <https://github.com/nipy/nipype/pull/530#issuecomment-14505042>`_),
    and also to compute nuisance regressors as proposed by [2]_.

    .. warning:: This workflow rotates the `b`-vectors, so please be advised
      that not all the dicom converters ensure the consistency between the resulting
      nifti orientation and the gradients table (e.g. dcm2nii checks it).

    .. admonition:: References

      .. [1] Leemans A, and Jones DK, Magn Reson Med. 2009 Jun;61(6):1336-49.
        doi: 10.1002/mrm.21890.

      .. [2] Yendiki A et al., Spurious group differences due to head motion in a
        diffusion MRI study. Neuroimage. 2013 Nov 21;88C:79-90.
        doi: 10.1016/j.neuroimage.2013.11.027

    Example
    -------

    >>> from nipype.workflows.dmri.fsl.epi import motion_correct
    >>> hmc = motion_correct()
    >>> hmc.inputs.inputnode.in_file = 'diffusion.nii'
    >>> hmc.inputs.inputnode.in_bvec = 'diffusion.bvec'
    >>> hmc.inputs.inputnode.in_mask = 'mask.nii'
    >>> hmc.run() # doctest: +SKIP

    Inputs::

        inputnode.in_file - input dwi file
        inputnode.in_mask - weights mask of reference image (a file with data range \
in [0.0, 1.0], indicating the weight of each voxel when computing the metric.
        inputnode.in_bvec - gradients file (b-vectors)
        inputnode.ref_num (optional, default=0) index of the b0 volume that should be \
taken as reference

    Outputs::

        outputnode.out_file - corrected dwi file
        outputnode.out_bvec - rotated gradient vectors table
        outputnode.out_xfms - list of transformation matrices

    """
    inputnode = pe.Node(niu.IdentityInterface(fields=['in_file', 'ref_num', 'in_bvec',
                        'in_mask']), name='inputnode')
    split = pe.Node(fsl.Split(dimension='t'), name='SplitDWIs')
    pick_ref = pe.Node(niu.Select(), name='Pick_b0')
    flirt = pe.MapNode(fsl.FLIRT(interp='spline', cost='normmi',
                       cost_func = 'normmi', dof=6, bins=64, save_log=True,
                       searchr_x=[-4,4], searchr_y=[-4,4], searchr_z=[-4,4],
                       fine_search=1, coarse_search=10, padding_size=1),
                       name='CoRegistration', iterfield=['in_file'])
    rot_bvec = pe.Node(niu.Function(input_names=['in_bvec', 'in_matrix'],
                           output_names=['out_file'], function=rotate_bvecs),
                           name='Rotate_Bvec')
    merge = pe.Node(fsl.Merge(dimension='t'), name='MergeDWIs')
    outputnode = pe.Node(niu.IdentityInterface(fields=['out_file',
                         'out_bvec', 'out_xfms']),
                         name='outputnode')

    wf = pe.Workflow(name=name)
    wf.connect([
         (inputnode,  split,      [('in_file', 'in_file')])
        ,(split,      pick_ref,   [('out_files', 'inlist')])
        ,(inputnode,  pick_ref,   [(('ref_num', _checkrnum), 'index')])
        ,(inputnode,  flirt,      [('in_mask', 'ref_weight')])
        ,(split,      flirt,      [('out_files', 'in_file')])
        ,(inputnode,  rot_bvec,   [('in_bvec', 'in_bvec')])
        ,(flirt,      rot_bvec,   [('out_matrix_file', 'in_matrix')])
        ,(pick_ref,   flirt,      [('out', 'reference')])
        ,(flirt,      merge,      [('out_file', 'in_files')])
        ,(merge,      outputnode, [('merged_file', 'out_file')])
        ,(rot_bvec,   outputnode, [('out_file', 'out_bvec')])
        ,(flirt,      outputnode, [('out_matrix_file', 'out_xfms')])
    ])
    return wf

def eddy_correct(name='eddy_correct'):
    """Creates a pipeline that corrects for artifacts induced by Eddy currents in dMRI
    sequences.
    It takes a series of diffusion weighted images and linearly co-registers
    them to one reference image (the average of all b0s in the dataset).

    DWIs are also modulated by the determinant of the Jacobian as indicated by [3]_ and
    [4]_.

    A list of rigid transformation matrices can be provided, sourcing from a
    :func:`.motion_correct` workflow, to initialize registrations in a *motion free*
    framework.

    A list of affine transformation matrices is available as output, so that transforms
    can be chained (discussion
    `here <https://github.com/nipy/nipype/pull/530#issuecomment-14505042>`_).

    .. admonition:: References

      .. [3] Jones DK, `The signal intensity must be modulated by the determinant of \
        the Jacobian when correcting for eddy currents in diffusion MRI \
        <http://cds.ismrm.org/protected/10MProceedings/files/1644_129.pdf>`_,
        Proc. ISMRM 18th Annual Meeting, (2010).

      .. [4] Rohde et al., `Comprehensive Approach for Correction of Motion and Distortion \
        in Diffusion-Weighted MRI \
        <http://stbb.nichd.nih.gov/pdf/com_app_cor_mri04.pdf>`_, MRM 51:103-114 (2004).

    Example
    -------

    >>> from nipype.workflows.dmri.fsl.epi import eddy_correct
    >>> ecc = eddy_correct()
    >>> ecc.inputs.inputnode.in_file = 'diffusion.nii'
    >>> ecc.inputs.inputnode.in_bval = 'diffusion.bval'
    >>> ecc.inputs.inputnode.in_mask = 'mask.nii'
    >>> ecc.run() # doctest: +SKIP

    Inputs::

        inputnode.in_file - input dwi file
        inputnode.in_mask - weights mask of reference image (a file with data range \
sin [0.0, 1.0], indicating the weight of each voxel when computing the metric.
        inputnode.in_bval - b-values table
        inputnode.in_xfms - list of matrices to initialize registration (from head-motion correction)

    Outputs::

        outputnode.out_file - corrected dwi file
        outputnode.out_xfms - list of transformation matrices
    """
    inputnode = pe.Node(niu.IdentityInterface(fields=['in_file', 'in_bval',
                        'in_mask', 'in_xfms']), name='inputnode')
    split = pe.Node(fsl.Split(dimension='t'), name='SplitDWIs')
    avg_b0 = pe.Node(niu.Function(input_names=['in_dwi', 'in_bval'],
                     output_names=['out_file'], function=b0_average), name='b0_avg')
    pick_dwi = pe.Node(niu.Select(), name='Pick_DWIs')
    flirt = pe.MapNode(fsl.FLIRT(no_search=True, interp='spline', cost='normmi',
                       cost_func = 'normmi', dof=12, bins=64, save_log=True,
                       padding_size=1), name='CoRegistration',
                       iterfield=['in_file', 'in_matrix_file'])
    initmat = pe.Node(niu.Function(input_names=['in_bval', 'in_xfms'],
                      output_names=['init_xfms'], function=_checkinitxfm),
                      name='InitXforms')

    mult = pe.MapNode(fsl.BinaryMaths(operation='mul'), name='ModulateDWIs',
                      iterfield=['in_file', 'operand_value'])
    thres = pe.MapNode(fsl.Threshold(thresh=0.0), iterfield=['in_file'],
                       name='RemoveNegative')

    get_mat = pe.Node(niu.Function(input_names=['in_bval', 'in_xfms'],
                      output_names=['out_files'], function=recompose_xfm),
                      name='GatherMatrices')
    merge = pe.Node(niu.Function(input_names=['in_dwi', 'in_bval', 'in_corrected'],
                    output_names=['out_file'], function=recompose_dwi), name='MergeDWIs')

    outputnode = pe.Node(niu.IdentityInterface(fields=['out_file', 'out_xfms']),
                         name='outputnode')

    wf = pe.Workflow(name=name)
    wf.connect([
         (inputnode,  split,      [('in_file', 'in_file')])
        ,(inputnode,  avg_b0,     [('in_file', 'in_dwi'),
                                   ('in_bval', 'in_bval')])
        ,(inputnode,  merge,      [('in_file', 'in_dwi'),
                                   ('in_bval', 'in_bval')])
        ,(inputnode,  initmat,    [('in_xfms', 'in_xfms'),
                                   ('in_bval', 'in_bval')])
        ,(inputnode,  get_mat,    [('in_bval', 'in_bval')])
        ,(split,      pick_dwi,   [('out_files', 'inlist')])
        ,(inputnode,  pick_dwi,   [(('in_bval', _nonb0), 'index')])
        ,(inputnode,  flirt,      [('in_mask', 'ref_weight')])
        ,(avg_b0,     flirt,      [('out_file', 'reference')])
        ,(pick_dwi,   flirt,      [('out', 'in_file')])
        ,(initmat,    flirt,      [('init_xfms', 'in_matrix_file')])
        ,(flirt,      get_mat,    [('out_matrix_file', 'in_xfms')])
        ,(flirt,      mult,       [(('out_matrix_file',_xfm_jacobian), 'operand_value')])
        ,(flirt,      mult,       [('out_file', 'in_file')])
        ,(mult,       thres,      [('out_file', 'in_file')])
        ,(thres,      merge,      [('out_file', 'in_corrected')])
        ,(get_mat,    outputnode, [('out_files', 'out_xfms')])
        ,(merge,      outputnode, [('out_file', 'out_file')])
    ])
    return wf


def _checkrnum(ref_num):
    from nipype.interfaces.base import isdefined
    if (ref_num is None) or not isdefined(ref_num):
        return 0
    return ref_num

def _checkinitxfm(in_bval, in_xfms=None):
    from nipype.interfaces.base import isdefined
    import numpy as np
    import os.path as op
    bvals = np.loadtxt(in_bval)
    non_b0 = np.where(bvals!=0)[0].tolist()

    init_xfms = []
    if (in_xfms is None) or (not isdefined(in_xfms)) or (len(in_xfms)!=len(bvals)):
        for i in non_b0:
            xfm_file = op.abspath('init_%04d.mat' % i)
            np.savetxt(xfm_file, np.eye(4))
            init_xfms.append(xfm_file)
    else:
        for i in non_b0:
            init_xfms.append(in_xfms[i])
    return init_xfms

def _nonb0(in_bval):
    import numpy as np
    bvals = np.loadtxt(in_bval)
    return np.where(bvals!=0)[0].tolist()

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


def _xfm_jacobian(in_xfm):
    import numpy as np
    from math import fabs
    return [fabs(np.linalg.det(np.loadtxt(xfm))) for xfm in in_xfm]


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

    imgs = nb.four_to_three(nb.load(in_dwi))
    bval = np.loadtxt(in_bval)

    b0s = []

    for bval, img in zip(bval, imgs):
        if bval==0:
            b0s.append(img.get_data())

    b0 = np.average(np.array(b0s), axis=0)

    hdr = imgs[0].get_header().copy()
    nii = nb.Nifti1Image(b0, imgs[0].get_affine(), hdr)

    nb.save(nii, out_file)
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
        if np.all(bvec==0.0):
            new_bvecs.append(bvec)
        else:
            invrot = np.linalg.inv(np.loadtxt(mat))[:3,:3]
            newbvec = invrot.dot(bvec)
            new_bvecs.append((newbvec/np.linalg.norm(newbvec)))

    np.savetxt(out_file, np.array(new_bvecs).T, fmt='%0.15f')
    return out_file
