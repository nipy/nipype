# coding: utf-8

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.fsl as fsl
import os


def transpose(samples_over_fibres):
    import numpy as np
    a = np.array(samples_over_fibres)
    if len(a.shape) == 1:
        a = a.reshape(-1, 1)
    return a.T.tolist()


def create_dmri_preprocessing(name="dMRI_preprocessing", fieldmap_registration=False):
    """Creates a workflow that chains the necessary pipelines to
    correct for motion, eddy currents, and susceptibility
    artifacts in EPI dMRI sequences.

    .. warning::

    IMPORTANT NOTICE: this workflow rotates the b-vectors, so please be adviced
    that not all the dicom converters ensure the consistency between the resulting
    nifti orientation and the b matrix table (e.g. dcm2nii checks it).


    Example
    -------

    >>> nipype_dmri_preprocess = create_dmri_preprocessing("nipype_dmri_prep")
    >>> nipype_dmri_preprocess.inputs.inputnode.in_file = 'diffusion.nii'
    >>> nipype_dmri_preprocess.inputs.inputnode.in_bvec = 'diffusion.bvec'
    >>> nipype_dmri_preprocess.inputs.inputnode.ref_num = 0
    >>> nipype_dmri_preprocess.inputs.inputnode.fieldmap_mag = 'magnitude.nii'
    >>> nipype_dmri_preprocess.inputs.inputnode.fieldmap_pha = 'phase.nii'
    >>> nipype_dmri_preprocess.inputs.inputnode.te_diff = 2.46
    >>> nipype_dmri_preprocess.inputs.inputnode.epi_echospacing = 0.77
    >>> nipype_dmri_preprocess.inputs.inputnode.epi_rev_encoding = False
    >>> nipype_dmri_preprocess.inputs.inputnode.pi_accel_factor = True
    >>> nipype_dmri_preprocess.run() # doctest: +SKIP


    Inputs::

        inputnode.in_file - The diffusion data
        inputnode.in_bvec - The b-matrix file, in FSL format and consistent with the in_file orientation
        inputnode.ref_num - The reference volume (a b=0 volume in dMRI)
        inputnode.fieldmap_mag - The magnitude of the fieldmap
        inputnode.fieldmap_pha - The phase difference of the fieldmap
        inputnode.te_diff - TE increment used (in msec.) on the fieldmap acquisition (generally 2.46ms for 3T scanners)
        inputnode.epi_echospacing - The EPI EchoSpacing parameter (in msec.)
        inputnode.epi_rev_encoding - True if reverse encoding was used (generally False)
        inputnode.pi_accel_factor - Parallel imaging factor (aka GRAPPA acceleration factor)
        inputnode.vsm_sigma - Sigma (in mm.) of the gaussian kernel used for in-slice smoothing of the deformation field (voxel shift map, vsm)


    Outputs::

        outputnode.dmri_corrected
        outputnode.bvec_rotated


    Optional arguments::

        fieldmap_registration - True if registration to fieldmap should be performed (default False)


    """

    pipeline = pe.Workflow(name=name)

    inputnode = pe.Node(interface=util.IdentityInterface(
        fields=['in_file', 'in_bvec', 'ref_num', 'fieldmap_mag',
                'fieldmap_pha', 'te_diff', 'epi_echospacing',
                'epi_rev_encoding', 'pi_accel_factor', 'vsm_sigma']),
        name='inputnode')

    outputnode = pe.Node(interface=util.IdentityInterface(
        fields=['dmri_corrected', 'bvec_rotated']),
        name='outputnode')

    motion = create_motion_correct_pipeline()
    eddy = create_eddy_correct_pipeline()
    susceptibility = create_susceptibility_correct_pipeline(
        fieldmap_registration=fieldmap_registration)

    pipeline.connect([
                     (inputnode,          motion, [('in_file', 'inputnode.in_file'), (
                         'in_bvec', 'inputnode.in_bvec'), ('ref_num', 'inputnode.ref_num')]), (inputnode,            eddy, [('ref_num', 'inputnode.ref_num')]), (motion,               eddy, [('outputnode.motion_corrected', 'inputnode.in_file')]), (eddy,       susceptibility, [('outputnode.eddy_corrected', 'inputnode.in_file')]), (inputnode,  susceptibility, [('ref_num', 'inputnode.ref_num'), ('fieldmap_mag', 'inputnode.fieldmap_mag'), ('fieldmap_pha', 'inputnode.fieldmap_pha'), ('te_diff', 'inputnode.te_diff'), ('epi_echospacing', 'inputnode.epi_echospacing'), ('epi_rev_encoding', 'inputnode.epi_rev_encoding'), ('pi_accel_factor', 'inputnode.pi_accel_factor'), ('vsm_sigma', 'inputnode.vsm_sigma')]), (motion,         outputnode, [('outputnode.out_bvec', 'bvec_rotated')]), (susceptibility, outputnode, [('outputnode.epi_corrected', 'dmri_corrected')])
                     ])

    return pipeline


def create_bedpostx_pipeline(name="bedpostx"):
    """Creates a pipeline that does the same as bedpostx script from FSL -
    calculates diffusion model parameters (distributions not MLE) voxelwise for
    the whole volume (by splitting it slicewise).

    Example
    -------

    >>> nipype_bedpostx = create_bedpostx_pipeline("nipype_bedpostx")
    >>> nipype_bedpostx.inputs.inputnode.dwi = 'diffusion.nii'
    >>> nipype_bedpostx.inputs.inputnode.mask = 'mask.nii'
    >>> nipype_bedpostx.inputs.inputnode.bvecs = 'bvecs'
    >>> nipype_bedpostx.inputs.inputnode.bvals = 'bvals'
    >>> nipype_bedpostx.inputs.xfibres.n_fibres = 2
    >>> nipype_bedpostx.inputs.xfibres.fudge = 1
    >>> nipype_bedpostx.inputs.xfibres.burn_in = 1000
    >>> nipype_bedpostx.inputs.xfibres.n_jumps = 1250
    >>> nipype_bedpostx.inputs.xfibres.sample_every = 25
    >>> nipype_bedpostx.run() # doctest: +SKIP

    Inputs::

        inputnode.dwi
        inputnode.mask

    Outputs::

        outputnode.thsamples
        outputnode.phsamples
        outputnode.fsamples
        outputnode.mean_thsamples
        outputnode.mean_phsamples
        outputnode.mean_fsamples
        outputnode.dyads
        outputnode.dyads_dispersion

    """

    inputnode = pe.Node(
        interface=util.IdentityInterface(fields=["dwi", "mask"]),
        name="inputnode")

    mask_dwi = pe.Node(interface=fsl.ImageMaths(op_string="-mas"),
                       name="mask_dwi")
    slice_dwi = pe.Node(interface=fsl.Split(dimension="z"), name="slice_dwi")
    slice_mask = pe.Node(interface=fsl.Split(dimension="z"),
                         name="slice_mask")

    preproc = pe.Workflow(name="preproc")

    preproc.connect([(inputnode, mask_dwi, [('dwi', 'in_file')]),
                     (inputnode, mask_dwi, [('mask', 'in_file2')]),
                     (mask_dwi, slice_dwi, [('out_file', 'in_file')]),
                     (inputnode, slice_mask, [('mask', 'in_file')])
                     ])

    xfibres = pe.MapNode(interface=fsl.XFibres(), name="xfibres",
                         iterfield=['dwi', 'mask'])

    # Normal set of parameters
    xfibres.inputs.n_fibres = 2
    xfibres.inputs.fudge = 1
    xfibres.inputs.burn_in = 1000
    xfibres.inputs.n_jumps = 1250
    xfibres.inputs.sample_every = 25
    xfibres.inputs.model = 1
    xfibres.inputs.non_linear = True
    xfibres.inputs.update_proposal_every = 24

    inputnode = pe.Node(interface=util.IdentityInterface(fields=["thsamples",
                                                                 "phsamples",
                                                                 "fsamples",
                                                                 "dyads",
                                                                 "mean_dsamples",
                                                                 "mask"]),
                        name="inputnode")

    merge_thsamples = pe.MapNode(fsl.Merge(dimension="z"),
                                 name="merge_thsamples", iterfield=['in_files'])
    merge_phsamples = pe.MapNode(fsl.Merge(dimension="z"),
                                 name="merge_phsamples", iterfield=['in_files'])
    merge_fsamples = pe.MapNode(fsl.Merge(dimension="z"),
                                name="merge_fsamples", iterfield=['in_files'])

    merge_mean_dsamples = pe.Node(fsl.Merge(dimension="z"),
                                  name="merge_mean_dsamples")

    mean_thsamples = pe.MapNode(fsl.ImageMaths(op_string="-Tmean"),
                                name="mean_thsamples", iterfield=['in_file'])
    mean_phsamples = pe.MapNode(fsl.ImageMaths(op_string="-Tmean"),
                                name="mean_phsamples", iterfield=['in_file'])
    mean_fsamples = pe.MapNode(fsl.ImageMaths(op_string="-Tmean"),
                               name="mean_fsamples", iterfield=['in_file'])
    make_dyads = pe.MapNode(fsl.MakeDyadicVectors(), name="make_dyads",
                            iterfield=['theta_vol', 'phi_vol'])

    postproc = pe.Workflow(name="postproc")

    postproc.connect(
        [(inputnode, merge_thsamples, [(('thsamples', transpose), 'in_files')]),
         (inputnode, merge_phsamples, [((
                                        'phsamples', transpose), 'in_files')]),
         (inputnode, merge_fsamples, [((
                                       'fsamples', transpose), 'in_files')]),
         (inputnode, merge_mean_dsamples, [
          ('mean_dsamples', 'in_files')]),

         (merge_thsamples, mean_thsamples, [
          ('merged_file', 'in_file')]),
         (merge_phsamples, mean_phsamples, [
          ('merged_file', 'in_file')]),
         (merge_fsamples, mean_fsamples, [
          ('merged_file', 'in_file')]),
         (merge_thsamples, make_dyads, [
          ('merged_file', 'theta_vol')]),
         (merge_phsamples, make_dyads, [
          ('merged_file', 'phi_vol')]),
         (inputnode, make_dyads, [('mask', 'mask')]),
         ])

    inputnode = pe.Node(interface=util.IdentityInterface(fields=["dwi",
                                                                 "mask",
                                                                 "bvecs",
                                                                 "bvals"]),
                        name="inputnode")

    bedpostx = pe.Workflow(name=name)
    bedpostx.connect([(inputnode, preproc, [('mask', 'inputnode.mask')]),
                      (inputnode, preproc, [('dwi', 'inputnode.dwi')]),

                      (preproc, xfibres, [('slice_dwi.out_files', 'dwi'),
                                          ('slice_mask.out_files', 'mask')]),
                      (inputnode, xfibres, [('bvals', 'bvals')]),
                      (inputnode, xfibres, [('bvecs', 'bvecs')]),

                      (inputnode, postproc, [('mask', 'inputnode.mask')]),
                      (xfibres, postproc, [
                          ('thsamples', 'inputnode.thsamples'),
                       ('phsamples',
                        'inputnode.phsamples'),
                    ('fsamples', 'inputnode.fsamples'),
                          ('dyads', 'inputnode.dyads'),
                          ('mean_dsamples', 'inputnode.mean_dsamples')]),
    ])

    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=["thsamples",
                                                 "phsamples",
                                                 "fsamples",
                                                 "mean_thsamples",
                                                 "mean_phsamples",
                                                 "mean_fsamples",
                                                 "dyads",
                                                 "dyads_dispersion"]),
        name="outputnode")
    bedpostx.connect(
        [(postproc, outputnode, [("merge_thsamples.merged_file", "thsamples"),
                    ("merge_phsamples.merged_file",
                     "phsamples"),
          ("merge_fsamples.merged_file",
           "fsamples"),
          ("mean_thsamples.out_file",
           "mean_thsamples"),
          ("mean_phsamples.out_file",
           "mean_phsamples"),
          ("mean_fsamples.out_file",
                                               "mean_fsamples"),
                                              ("make_dyads.dyads", "dyads"),
                                              ("make_dyads.dispersion", "dyads_dispersion")])
                      ])
    return bedpostx


def create_motion_correct_pipeline(name="motion_correct"):
    """Creates a pipeline that corrects for motion artifact in dMRI sequences.
    It takes a series of diffusion weighted images and rigidly corregisters
    them to one reference image. Finally, the b-matrix is rotated accordingly
    (Leemans et al. 2009 - http://www.ncbi.nlm.nih.gov/pubmed/19319973),
    making use of the rotation matrix obtained by FLIRT.

    .. warning::

    IMPORTANT NOTICE: this workflow rotates the b-vectors, so please be adviced
    that not all the dicom converters ensure the consistency between the resulting
    nifti orientation and the b matrix table (e.g. dcm2nii checks it).


    Example
    -------

    >>> nipype_motioncorrect = create_motion_correct_pipeline("nipype_motioncorrect")
    >>> nipype_motioncorrect.inputs.inputnode.in_file = 'diffusion.nii'
    >>> nipype_motioncorrect.inputs.inputnode.in_bvec = 'diffusion.bvec'
    >>> nipype_motioncorrect.inputs.inputnode.ref_num = 0
    >>> nipype_motioncorrect.run() # doctest: +SKIP

    Inputs::

        inputnode.in_file
        inputnode.ref_num
        inputnode.in_bvec

    Outputs::

        outputnode.motion_corrected
        outputnode.out_bvec

    """

    inputnode = pe.Node(
        interface=util.IdentityInterface(
            fields=["in_file", "ref_num", "in_bvec"]),
                        name="inputnode")

    pipeline = pe.Workflow(name=name)

    split = pe.Node(fsl.Split(dimension='t'), name="split")
    pick_ref = pe.Node(util.Select(), name="pick_ref")
    coregistration = pe.MapNode(fsl.FLIRT(no_search=True, interp='spline',
                                padding_size=1, dof=6), name="coregistration", iterfield=["in_file"])
    rotate_bvecs = pe.Node(util.Function(input_names=["in_bvec", "in_matrix"], output_names=[
                           "out_file"], function=_rotate_bvecs), name="rotate_b_matrix")
    merge = pe.Node(fsl.Merge(dimension="t"), name="merge")
    outputnode = pe.Node(
        interface=util.IdentityInterface(
            fields=["motion_corrected", "out_bvec"]),
                        name="outputnode")

    pipeline.connect([
                         (inputnode, split, [("in_file", "in_file")]), (
                             split, pick_ref, [("out_files", "inlist")]), (inputnode, pick_ref, [("ref_num", "index")]), (split, coregistration, [("out_files", "in_file")]), (inputnode, rotate_bvecs, [("in_bvec", "in_bvec")]), (coregistration, rotate_bvecs, [("out_matrix_file", "in_matrix")]), (pick_ref, coregistration, [("out", "reference")]), (coregistration, merge, [("out_file", "in_files")]), (merge, outputnode, [("merged_file", "motion_corrected")]), (rotate_bvecs, outputnode, [("out_file", "out_bvec")])
                    ])

    return pipeline


def create_eddy_correct_pipeline(name="eddy_correct"):
    """Creates a pipeline that replaces eddy_correct script in FSL. It takes a
    series of diffusion weighted images and linearly co-registers them to one
    reference image. No rotation of the B-matrix is performed, so this pipeline
    should be executed after the motion correction pipeline.

    Example
    -------

    >>> nipype_eddycorrect = create_eddy_correct_pipeline("nipype_eddycorrect")
    >>> nipype_eddycorrect.inputs.inputnode.in_file = 'diffusion.nii'
    >>> nipype_eddycorrect.inputs.inputnode.ref_num = 0
    >>> nipype_eddycorrect.run() # doctest: +SKIP

    Inputs::

        inputnode.in_file
        inputnode.ref_num

    Outputs::

        outputnode.eddy_corrected
    """

    inputnode = pe.Node(
        interface=util.IdentityInterface(fields=["in_file", "ref_num"]),
                        name="inputnode")

    pipeline = pe.Workflow(name=name)

    split = pe.Node(fsl.Split(dimension='t'), name="split")
    pick_ref = pe.Node(util.Select(), name="pick_ref")
    coregistration = pe.MapNode(fsl.FLIRT(no_search=True, padding_size=1,
                                dof=12, interp='spline'), name="coregistration", iterfield=["in_file"])
    merge = pe.Node(fsl.Merge(dimension="t"), name="merge")
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=["eddy_corrected"]),
                        name="outputnode")

    pipeline.connect([
                         (inputnode, split, [("in_file", "in_file")]), (
                             split, pick_ref, [("out_files", "inlist")]), (inputnode, pick_ref, [("ref_num", "index")]), (split, coregistration, [("out_files", "in_file")]), (pick_ref, coregistration, [("out", "reference")]), (coregistration, merge, [("out_file", "in_files")]), (merge, outputnode, [("merged_file", "eddy_corrected")])
                    ])
    return pipeline


def create_susceptibility_correct_pipeline(name="susceptibility_correct", fieldmap_registration=False):
    """ Replaces the epidewarp.fsl script (http://www.nmr.mgh.harvard.edu/~greve/fbirn/b0/epidewarp.fsl)
    for susceptibility distortion correction of dMRI & fMRI acquired with EPI sequences and the fieldmap
    information (Jezzard et al., 1995) using FSL's FUGUE. The registration to the (warped) fieldmap
    (strictly following the original script) is available using fieldmap_registration=True.

    Example
    -------

    >>> nipype_epicorrect = create_susceptibility_correct_pipeline("nipype_epicorrect", fieldmap_registration=False)
    >>> nipype_epicorrect.inputs.inputnode.in_file = 'diffusion.nii'
    >>> nipype_epicorrect.inputs.inputnode.fieldmap_mag = 'magnitude.nii'
    >>> nipype_epicorrect.inputs.inputnode.fieldmap_pha = 'phase.nii'
    >>> nipype_epicorrect.inputs.inputnode.te_diff = 2.46
    >>> nipype_epicorrect.inputs.inputnode.epi_echospacing = 0.77
    >>> nipype_epicorrect.inputs.inputnode.epi_rev_encoding = False
    >>> nipype_epicorrect.inputs.inputnode.ref_num = 0
    >>> nipype_epicorrect.inputs.inputnode.pi_accel_factor = 1.0
    >>> nipype_epicorrect.run() # doctest: +SKIP

    Inputs::

        inputnode.in_file - The volume acquired with EPI sequence
        inputnode.fieldmap_mag - The magnitude of the fieldmap
        inputnode.fieldmap_pha - The phase difference of the fieldmap
        inputnode.te_diff - Time difference between TE in ms.
        inputnode.epi_echospacing - The echo spacing (aka dwell time) in the EPI sequence
        inputnode.epi_ph_encoding_dir - The phase encoding direction in EPI acquisition (default y)
        inputnode.epi_rev_encoding - True if it is acquired with reverse encoding
        inputnode.pi_accel_factor - Acceleration factor used for EPI parallel imaging (GRAPPA)
        inputnode.vsm_sigma - Sigma value of the gaussian smoothing filter applied to the vsm (voxel shift map)
        inputnode.ref_num - The reference volume (B=0 in dMRI or a central frame in fMRI)


    Outputs::

        outputnode.epi_corrected


    Optional arguments::

        fieldmap_registration - True if registration to fieldmap should be done (default False)

    """

    inputnode = pe.Node(interface=util.IdentityInterface(fields=["in_file",
                                                                   "fieldmap_mag",
                                                                   "fieldmap_pha",
                                                                   "te_diff",
                                                                   "epi_echospacing",
                                                                   "epi_ph_encoding_dir",
                                                                   "epi_rev_encoding",
                                                                   "pi_accel_factor",
                                                                   "vsm_sigma",
                                                                   "ref_num",
                                                                   "unwarp_direction"
                                                                   ]), name="inputnode")

    pipeline = pe.Workflow(name=name)

    # Keep first frame from magnitude
    select_mag = pe.Node(interface=fsl.utils.ExtractROI(
        t_size=1, t_min=0), name="select_magnitude")

    # mask_brain
    mask_mag = pe.Node(interface=fsl.BET(mask=True), name='mask_magnitude')
    mask_mag_dil = pe.Node(interface=util.Function(input_names=[
                           "in_file"], output_names=["out_file"], function=_dilate_mask), name='mask_dilate')

    # Compute dwell time
    dwell_time = pe.Node(interface=util.Function(input_names=["dwell_time", "pi_factor", "is_reverse_encoding"], output_names=[
                         "dwell_time"], function=_compute_dwelltime), name='dwell_time')

    # Normalize phase diff to be [-pi, pi)
    norm_pha = pe.Node(interface=util.Function(input_names=["in_file"], output_names=[
                       "out_file"], function=_prepare_phasediff), name='normalize_phasediff')
    # Execute FSL PRELUDE: prelude -p %s -a %s -o %s -f -v -m %s
    prelude = pe.Node(interface=fsl.PRELUDE(
        process3d=True), name='phase_unwrap')
    fill_phase = pe.Node(interface=util.Function(input_names=["in_file"], output_names=[
                         "out_file"], function=_fill_phase), name='fill_phasediff')

    # to assure that vsm is same dimension as mag. The input only affects the output dimension.
    # The content of the input has no effect on the vsm. The de-warped mag volume is
    # meaningless and will be thrown away
    # fugue -i %s -u %s -p %s --dwell=%s --asym=%s --mask=%s --saveshift=%s %
    # ( mag_name, magdw_name, ph_name, esp, tediff, mask_name, vsmmag_name)
    vsm = pe.Node(interface=fsl.FUGUE(save_shift=True), name="generate_vsm")
    vsm_mean = pe.Node(interface=util.Function(input_names=["in_file", "mask_file", "in_unwarped"], output_names=[
                       "out_file"], function=_vsm_remove_mean), name="vsm_mean_shift")

    # fugue_epi
    dwi_split = pe.Node(interface=util.Function(input_names=[
                        'in_file'], output_names=['out_files'], function=_split_dwi), name='dwi_split')
    # 'fugue -i %s -u %s --loadshift=%s --mask=%s' % ( vol_name, out_vol_name, vsm_name, mask_name )
    dwi_applyxfm = pe.MapNode(interface=fsl.FUGUE(
        icorr=True, save_shift=False), iterfield=['in_file'], name='dwi_fugue')
    # Merge back all volumes
    dwi_merge = pe.Node(interface=fsl.utils.Merge(
        dimension='t'), name='dwi_merge')

    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=["epi_corrected"]),
                        name="outputnode")

    pipeline.connect([
                     (inputnode,    dwell_time, [('epi_echospacing', 'dwell_time'), (
                         'pi_accel_factor', 'pi_factor'), ('epi_rev_encoding', 'is_reverse_encoding')]), (inputnode,    select_mag, [('fieldmap_mag', 'in_file')]), (inputnode,      norm_pha, [('fieldmap_pha', 'in_file')]), (select_mag,     mask_mag, [('roi_file', 'in_file')]), (mask_mag,   mask_mag_dil, [('mask_file', 'in_file')]), (select_mag,      prelude, [('roi_file', 'magnitude_file')]), (norm_pha,        prelude, [('out_file', 'phase_file')]), (mask_mag_dil,    prelude, [('out_file', 'mask_file')]), (prelude,      fill_phase, [('unwrapped_phase_file', 'in_file')]), (inputnode,           vsm, [('fieldmap_mag', 'in_file')]), (fill_phase,          vsm, [('out_file', 'phasemap_file')]), (inputnode,           vsm, [(('te_diff', _ms2sec), 'asym_se_time'), ('vsm_sigma', 'smooth2d')]), (dwell_time,          vsm, [(('dwell_time', _ms2sec), 'dwell_time')]), (mask_mag_dil,        vsm, [('out_file', 'mask_file')]), (mask_mag_dil,   vsm_mean, [('out_file', 'mask_file')]), (vsm,            vsm_mean, [('unwarped_file', 'in_unwarped'), ('shift_out_file', 'in_file')]), (inputnode,     dwi_split, [('in_file', 'in_file')]), (dwi_split,  dwi_applyxfm, [('out_files', 'in_file')]), (dwi_applyxfm,  dwi_merge, [('unwarped_file', 'in_files')]), (dwi_merge,    outputnode, [('merged_file', 'epi_corrected')])
                    ])

    if fieldmap_registration:
        """ Register magfw to example epi. There are some parameters here that may need to be tweaked. Should probably strip the mag
            Pre-condition: forward warp the mag in order to reg with func. What does mask do here?
        """
        # Select reference volume from EPI (B0 in dMRI and a middle frame in
        # fMRI)
        select_epi = pe.Node(interface=fsl.utils.ExtractROI(
            t_size=1), name="select_epi")

        # fugue -i %s -w %s --loadshift=%s --mask=%s % ( mag_name, magfw_name,
        # vsmmag_name, mask_name ), log ) # Forward Map
        vsm_fwd = pe.Node(interface=fsl.FUGUE(
            save_warped=True), name="vsm_fwd")
        vsm_reg = pe.Node(interface=fsl.FLIRT(bins=256, cost='corratio', dof=6, interp='spline',  searchr_x=[
                          -10, 10], searchr_y=[-10, 10], searchr_z=[-10, 10]), name="vsm_registration")
        # 'flirt -in %s -ref %s -out %s -init %s -applyxfm' % ( vsmmag_name, ref_epi, vsmmag_name, magfw_mat_out )
        vsm_applyxfm = pe.Node(interface=fsl.ApplyXfm(
            interp='spline'), name='vsm_apply_xfm')
        # 'flirt -in %s -ref %s -out %s -init %s -applyxfm' % ( mask_name, ref_epi, mask_name, magfw_mat_out )
        msk_applyxfm = pe.Node(interface=fsl.ApplyXfm(
            interp='nearestneighbour'), name='msk_apply_xfm')

        pipeline.connect([
                     (inputnode,      select_epi, [(
                         'in_file', 'in_file'), ('ref_num', 't_min')]), (select_epi,        vsm_reg, [('roi_file', 'reference')]), (vsm,               vsm_fwd, [('shift_out_file', 'shift_in_file')]), (mask_mag_dil,      vsm_fwd, [('out_file', 'mask_file')]), (inputnode,         vsm_fwd, [('fieldmap_mag', 'in_file')]), (vsm_fwd,           vsm_reg, [('warped_file', 'in_file')]), (vsm_reg,      msk_applyxfm, [('out_matrix_file', 'in_matrix_file')]), (select_epi,   msk_applyxfm, [('roi_file', 'reference')]), (mask_mag_dil, msk_applyxfm, [('out_file', 'in_file')]), (vsm_reg,      vsm_applyxfm, [('out_matrix_file', 'in_matrix_file')]), (select_epi,   vsm_applyxfm, [('roi_file', 'reference')]), (vsm_mean,     vsm_applyxfm, [('out_file', 'in_file')]), (msk_applyxfm, dwi_applyxfm, [('out_file', 'mask_file')]), (vsm_applyxfm, dwi_applyxfm, [('out_file', 'shift_in_file')])
                    ])
    else:
        pipeline.connect([
                     (mask_mag_dil, dwi_applyxfm, [('out_file', 'mask_file')]), (
                         vsm_mean,     dwi_applyxfm, [('out_file', 'shift_in_file')])
                    ])

    return pipeline


def _rotate_bvecs(in_bvec, in_matrix):
    import os
    import numpy as np

    name, fext = os.path.splitext(os.path.basename(in_bvec))
    if fext == '.gz':
        name, _ = os.path.splitext(name)
    out_file = os.path.abspath('./%s_rotated.bvec' % name)
    bvecs = np.loadtxt(in_bvec)
    new_bvecs = [bvecs[:, 0]]

    for i, vol_matrix in enumerate(in_matrix[1::]):
        bvec = np.matrix(bvecs[:, i])
        rot = np.matrix(np.loadtxt(vol_matrix)[0:3, 0:3])
        new_bvecs.append((np.array(rot * bvec.T).T)[0])
    np.savetxt(out_file, np.array(new_bvecs).T, fmt='%0.15f')
    return out_file


def _cat_logs(in_files):
    import shutil
    import os

    name, fext = os.path.splitext(os.path.basename(in_files[0]))
    if fext == '.gz':
        name, _ = os.path.splitext(name)
    out_file = os.path.abspath('./%s_ecclog.log' % name)
    out_str = ""
    with open(out_file, 'wb') as totallog:
        for i, fname in enumerate(in_files):
            totallog.write("\n\npreprocessing %d\n" % i)
            with open(fname) as inlog:
                for line in inlog:
                    totallog.write(line)
    return out_file


def _compute_dwelltime(dwell_time=0.68, pi_factor=1.0, is_reverse_encoding=False):
    dwell_time *= (1.0/pi_factor)

    if is_reverse_encoding:
        dwell_time *= -1.0

    return dwell_time


def _prepare_phasediff(in_file):
    import nibabel as nib
    import os
    import numpy as np
    img = nib.load(in_file)
    max_diff = np.max(img.get_data().reshape(-1))
    min_diff = np.min(img.get_data().reshape(-1))
    A = (2.0 * np.pi)/(max_diff-min_diff)
    B = np.pi - (A * max_diff)
    diff_norm = img.get_data() * A + B

    name, fext = os.path.splitext(os.path.basename(in_file))
    if fext == '.gz':
        name, _ = os.path.splitext(name)
    out_file = os.path.abspath('./%s_2pi.nii.gz' % name)
    nib.save(nib.Nifti1Image(
        diff_norm, img.get_affine(), img.get_header()), out_file)
    return out_file


def _dilate_mask(in_file, iterations=4):
    import nibabel as nib
    import scipy.ndimage as ndimage
    import os
    img = nib.load(in_file)
    img._data = ndimage.binary_dilation(img.get_data(), iterations=iterations)

    name, fext = os.path.splitext(os.path.basename(in_file))
    if fext == '.gz':
        name, _ = os.path.splitext(name)
    out_file = os.path.abspath('./%s_dil.nii.gz' % name)
    nib.save(img, out_file)
    return out_file


def _fill_phase(in_file):
    import nibabel as nib
    import os
    import numpy as np
    img = nib.load(in_file)
    dumb_img = nib.Nifti1Image(np.zeros(
        img.get_shape()), img.get_affine(), img.get_header())
    out_nii = nib.funcs.concat_images((img, dumb_img))
    name, fext = os.path.splitext(os.path.basename(in_file))
    if fext == '.gz':
        name, _ = os.path.splitext(name)
    out_file = os.path.abspath('./%s_phase_unwrapped.nii.gz' % name)
    nib.save(out_nii, out_file)
    return out_file


def _vsm_remove_mean(in_file, mask_file, in_unwarped):
    import nibabel as nib
    import os
    import numpy as np
    import numpy.ma as ma
    img = nib.load(in_file)
    msk = nib.load(mask_file).get_data()
    img_data = img.get_data()
    img_data[msk == 0] = 0
    vsmmag_masked = ma.masked_values(img_data.reshape(-1), 0.0)
    vsmmag_masked = vsmmag_masked - vsmmag_masked.mean()
    img._data = vsmmag_masked.reshape(img.get_shape())
    name, fext = os.path.splitext(os.path.basename(in_file))
    if fext == '.gz':
        name, _ = os.path.splitext(name)
    out_file = os.path.abspath('./%s_demeaned.nii.gz' % name)
    nib.save(img, out_file)
    return out_file


def _ms2sec(val):
    return val*1e-3;


def _split_dwi(in_file):
    import nibabel as nib
    import os
    out_files = []
    frames = nib.funcs.four_to_three(nib.load(in_file))
    name, fext = os.path.splitext(os.path.basename(in_file))
    if fext == '.gz':
        name, _ = os.path.splitext(name)
    for i, frame in enumerate(frames):
        out_file = os.path.abspath('./%s_%03d.nii.gz' % (name, i))
        nib.save(frame, out_file)
        out_files.append(out_file)
    return out_files
