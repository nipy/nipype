# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provides interfaces to various commands for running PET analyses provided by FreeSurfer"""

import os

from ... import logging
from ..base import (
    TraitedSpec,
    File,
    traits,
    Tuple,
    Directory,
    InputMultiPath,
    isdefined,
)
from .base import FSCommand, FSTraitedSpec

from .model import GLMFitInputSpec, GLMFit

__docformat__ = "restructuredtext"
iflogger = logging.getLogger("nipype.interface")


class GTMSegInputSpec(FSTraitedSpec):
    subject_id = traits.String(argstr="--s %s", desc="subject id", mandatory=True)

    xcerseg = traits.Bool(
        argstr="--xcerseg",
        desc="run xcerebralseg on this subject to create apas+head.mgz",
    )

    out_file = File(
        "gtmseg.mgz",
        argstr="--o %s",
        desc="output volume relative to subject/mri",
        usedefault=True,
    )

    upsampling_factor = traits.Int(
        argstr="--usf %i", desc="upsampling factor (default is 2)"
    )

    subsegwm = traits.Bool(
        argstr="--subsegwm", default=True, desc="subsegment WM into lobes (default)"
    )

    keep_hypo = traits.Bool(
        argstr="--keep-hypo",
        desc="do not relabel hypointensities as WM when subsegmenting WM",
    )

    keep_cc = traits.Bool(
        argstr="--keep-cc", desc="do not relabel corpus callosum as WM"
    )

    dmax = traits.Float(
        argstr="--dmax %f",
        desc="distance threshold to use when subsegmenting WM (default is 5)",
    )

    ctx_annot = Tuple(
        traits.String,
        traits.Int,
        traits.Int,
        argstr="--ctx-annot %s %i %i",
        desc="annot lhbase rhbase : annotation to use for cortical segmentation (default is aparc 1000 2000)",
    )

    wm_annot = Tuple(
        traits.String,
        traits.Int,
        traits.Int,
        argstr="--wm-annot %s %i %i",
        desc="annot lhbase rhbase : annotation to use for WM segmentation (with --subsegwm, default is lobes 3200 4200)",
    )

    output_upsampling_factor = traits.Int(
        argstr="--output-usf %i",
        desc="set output USF different than USF, mostly for debugging",
    )

    head = traits.String(
        argstr="--head %s", desc="use headseg instead of apas+head.mgz"
    )

    subseg_cblum_wm = traits.Bool(
        argstr="--subseg-cblum-wm", desc="subsegment cerebellum WM into core and gyri"
    )

    no_pons = traits.Bool(
        argstr="--no-pons", desc="do not add pons segmentation when doing ---xcerseg"
    )

    no_vermis = traits.Bool(
        argstr="--no-vermis",
        desc="do not add vermis segmentation when doing ---xcerseg",
    )

    colortable = File(exists=True, argstr="--ctab %s", desc="colortable")
    no_seg_stats = traits.Bool(
        argstr="--no-seg-stats", desc="do not compute segmentation stats"
    )


class GTMSegOutputSpec(TraitedSpec):
    out_file = File(desc="GTM segmentation")


class GTMSeg(FSCommand):
    """create an anatomical segmentation for the geometric transfer matrix (GTM).

    Examples
    --------
    >>> gtmseg = GTMSeg()
    >>> gtmseg.inputs.subject_id = 'subject_id'
    >>> gtmseg.cmdline
    'gtmseg --o gtmseg.mgz --s subject_id'
    """

    _cmd = "gtmseg"
    input_spec = GTMSegInputSpec
    output_spec = GTMSegOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.join(
            self.inputs.subjects_dir,
            self.inputs.subject_id,
            'mri',
            self.inputs.out_file,
        )
        return outputs


class GTMPVCInputSpec(FSTraitedSpec):
    in_file = File(
        exists=True,
        argstr="--i %s",
        mandatory=True,
        copyfile=False,
        desc="input volume - source data to pvc",
    )

    frame = traits.Int(
        argstr="--frame %i", desc="only process 0-based frame F from inputvol"
    )

    psf = traits.Float(argstr="--psf %f", desc="scanner PSF FWHM in mm")

    segmentation = File(
        argstr="--seg %s",
        exists=True,
        mandatory=True,
        desc="segfile : anatomical segmentation to define regions for GTM",
    )

    _reg_xor = ["reg_file", "regheader", "reg_identity"]
    reg_file = File(
        exists=True,
        argstr="--reg %s",
        mandatory=True,
        desc="LTA registration file that maps PET to anatomical",
        xor=_reg_xor,
    )

    regheader = traits.Bool(
        argstr="--regheader",
        mandatory=True,
        desc="assume input and seg share scanner space",
        xor=_reg_xor,
    )

    reg_identity = traits.Bool(
        argstr="--reg-identity",
        mandatory=True,
        desc="assume that input is in anatomical space",
        xor=_reg_xor,
    )

    pvc_dir = traits.Str(argstr="--o %s", desc="save outputs to dir", genfile=True)

    mask_file = File(
        exists=True,
        argstr="--mask %s",
        desc="ignore areas outside of the mask (in input vol space)",
    )

    auto_mask = Tuple(
        traits.Float,
        traits.Float,
        argstr="--auto-mask %f %f",
        desc="FWHM thresh : automatically compute mask",
    )

    no_reduce_fov = traits.Bool(
        argstr="--no-reduce-fov", desc="do not reduce FoV to encompass mask"
    )

    reduce_fox_eqodd = traits.Bool(
        argstr="--reduce-fox-eqodd",
        desc="reduce FoV to encompass mask but force nc=nr and ns to be odd",
    )

    contrast = InputMultiPath(
        File(exists=True), argstr="--C %s...", desc="contrast file"
    )

    default_seg_merge = traits.Bool(
        argstr="--default-seg-merge", desc="default schema for merging ROIs"
    )

    merge_hypos = traits.Bool(
        argstr="--merge-hypos", desc="merge left and right hypointensites into to ROI"
    )

    merge_cblum_wm_gyri = traits.Bool(
        argstr="--merge-cblum-wm-gyri",
        desc="cerebellum WM gyri back into cerebellum WM",
    )

    tt_reduce = traits.Bool(
        argstr="--tt-reduce", desc="reduce segmentation to that of a tissue type"
    )

    replace = Tuple(
        traits.Int,
        traits.Int,
        argstr="--replace %i %i",
        desc="Id1 Id2 : replace seg Id1 with seg Id2",
    )

    rescale = traits.List(
        argstr="--rescale %s...",
        desc="Id1 <Id2...>  : specify reference region(s) used to rescale (default is pons)",
    )

    no_rescale = traits.Bool(
        argstr="--no-rescale",
        desc="do not global rescale such that mean of reference region is scaleref",
    )

    scale_refval = traits.Float(
        argstr="--scale-refval %f",
        desc="refval : scale such that mean in reference region is refval",
    )

    _ctab_inputs = ("color_table_file", "default_color_table")
    color_table_file = File(
        exists=True,
        argstr="--ctab %s",
        xor=_ctab_inputs,
        desc="color table file with seg id names",
    )

    default_color_table = traits.Bool(
        argstr="--ctab-default",
        xor=_ctab_inputs,
        desc="use $FREESURFER_HOME/FreeSurferColorLUT.txt",
    )

    tt_update = traits.Bool(
        argstr="--tt-update",
        desc="changes tissue type of VentralDC, BrainStem, and Pons to be SubcortGM",
    )

    lat = traits.Bool(argstr="--lat", desc="lateralize tissue types")

    no_tfe = traits.Bool(
        argstr="--no-tfe",
        desc="do not correct for tissue fraction effect (with --psf 0 turns off PVC entirely)",
    )

    no_pvc = traits.Bool(
        argstr="--no-pvc",
        desc="turns off PVC entirely (both PSF and TFE)",
    )

    tissue_fraction_resolution = traits.Float(
        argstr="--segpvfres %f",
        desc="set the tissue fraction resolution parameter (def is 0.5)",
    )

    rbv = traits.Bool(
        argstr="--rbv",
        requires=["subjects_dir"],
        desc="perform Region-based Voxelwise (RBV) PVC",
    )

    rbv_res = traits.Float(
        argstr="--rbv-res %f",
        desc="voxsize : set RBV voxel resolution (good for when standard res takes too much memory)",
    )

    mg = Tuple(
        traits.Float,
        traits.List(traits.String),
        argstr="--mg %g %s",
        desc="gmthresh RefId1 RefId2 ...: perform Mueller-Gaertner PVC, gmthresh is min gm pvf bet 0 and 1",
    )

    mg_ref_cerebral_wm = traits.Bool(
        argstr="--mg-ref-cerebral-wm", desc=" set MG RefIds to 2 and 41"
    )

    mg_ref_lobes_wm = traits.Bool(
        argstr="--mg-ref-lobes-wm",
        desc="set MG RefIds to those for lobes when using wm subseg",
    )

    mgx = traits.Float(
        argstr="--mgx %f",
        desc="gmxthresh : GLM-based Mueller-Gaertner PVC, gmxthresh is min gm pvf bet 0 and 1",
    )

    km_ref = traits.List(
        argstr="--km-ref %s...",
        desc="RefId1 RefId2 ... : compute reference TAC for KM as mean of given RefIds",
    )

    km_hb = traits.List(
        argstr="--km-hb %s...",
        desc="RefId1 RefId2 ... : compute HiBinding TAC for KM as mean of given RefIds",
    )

    steady_state_params = Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr="--ss %f %f %f",
        desc="bpc scale dcf : steady-state analysis spec blood plasma concentration, unit scale and decay correction factor. You must also spec --km-ref. Turns off rescaling",
    )

    X = traits.Bool(
        argstr="--X", desc="save X matrix in matlab4 format as X.mat (it will be big)"
    )

    y = traits.Bool(argstr="--y", desc="save y matrix in matlab4 format as y.mat")

    beta = traits.Bool(
        argstr="--beta", desc="save beta matrix in matlab4 format as beta.mat"
    )

    X0 = traits.Bool(
        argstr="--X0",
        desc="save X0 matrix in matlab4 format as X0.mat (it will be big)",
    )

    save_input = traits.Bool(
        argstr="--save-input", desc="saves rescaled input as input.rescaled.nii.gz"
    )

    save_eres = traits.Bool(argstr="--save-eres", desc="saves residual error")

    save_yhat = traits.Bool(
        argstr="--save-yhat",
        xor=["save_yhat_with_noise"],
        desc="save signal estimate (yhat) smoothed with the PSF",
    )

    save_yhat_with_noise = Tuple(
        traits.Int,
        traits.Int,
        argstr="--save-yhat-with-noise %i %i",
        xor=["save_yhat"],
        desc="seed nreps : save signal estimate (yhat) with noise",
    )

    save_yhat_full_fov = traits.Bool(
        argstr="--save-yhat-full-fov", desc="save signal estimate (yhat)"
    )

    save_yhat0 = traits.Bool(argstr="--save-yhat0", desc="save signal estimate (yhat)")

    optimization_schema = traits.Enum(
        "3D",
        "2D",
        "1D",
        "3D_MB",
        "2D_MB",
        "1D_MB",
        "MBZ",
        "MB3",
        argstr="--opt %s",
        desc="opt : optimization schema for applying adaptive GTM",
    )

    opt_tol = Tuple(
        traits.Int,
        traits.Float,
        traits.Float,
        argstr="--opt-tol %i %f %f",
        desc="n_iters_max ftol lin_min_tol : optimization parameters for adaptive gtm using fminsearch",
    )

    opt_brain = traits.Bool(argstr="--opt-brain", desc="apply adaptive GTM")

    opt_seg_merge = traits.Bool(
        argstr="--opt-seg-merge",
        desc="optimal schema for merging ROIs when applying adaptive GTM",
    )

    num_threads = traits.Int(
        argstr="--threads %i", desc="threads : number of threads to use"
    )

    psf_col = traits.Float(
        argstr="--psf-col %f", desc="xFWHM : full-width-half-maximum in the x-direction"
    )

    psf_row = traits.Float(
        argstr="--psf-row %f", desc="yFWHM : full-width-half-maximum in the y-direction"
    )

    psf_slice = traits.Float(
        argstr="--psf-slice %f",
        desc="zFWHM : full-width-half-maximum in the z-direction",
    )


class GTMPVCOutputSpec(TraitedSpec):
    pvc_dir = Directory(desc="output directory")
    ref_file = File(desc="Reference TAC in .dat")
    hb_nifti = File(desc="High-binding TAC in nifti")
    hb_dat = File(desc="High-binding TAC in .dat")
    nopvc_file = File(desc="TACs for all regions with no PVC")
    gtm_file = File(desc="TACs for all regions with GTM PVC")
    gtm_stats = File(desc="Statistics for the GTM PVC")
    input_file = File(desc="4D PET file in native volume space")
    reg_pet2anat = File(desc="Registration file to go from PET to anat")
    reg_anat2pet = File(desc="Registration file to go from anat to PET")
    reg_rbvpet2anat = File(
        desc="Registration file to go from RBV corrected PET to anat"
    )
    reg_anat2rbvpet = File(
        desc="Registration file to go from anat to RBV corrected PET"
    )
    mgx_ctxgm = File(
        desc="Cortical GM voxel-wise values corrected using the extended Muller-Gartner method",
    )
    mgx_subctxgm = File(
        desc="Subcortical GM voxel-wise values corrected using the extended Muller-Gartner method",
    )
    mgx_gm = File(
        desc="All GM voxel-wise values corrected using the extended Muller-Gartner method",
    )
    rbv = File(desc="All GM voxel-wise values corrected using the RBV method")
    opt_params = File(
        desc="Optimal parameter estimates for the FWHM using adaptive GTM"
    )
    yhat0 = File(desc="4D PET file of signal estimate (yhat) after PVC (unsmoothed)")
    yhat = File(
        desc="4D PET file of signal estimate (yhat) after PVC (smoothed with PSF)",
    )
    yhat_full_fov = File(
        desc="4D PET file with full FOV of signal estimate (yhat) after PVC (smoothed with PSF)",
    )
    yhat_with_noise = File(
        desc="4D PET file with full FOV of signal estimate (yhat) with noise after PVC (smoothed with PSF)",
    )
    eres = File(
        desc="4D PET file of residual error after PVC (smoothed with PSF)",
    )
    tissue_fraction = File(
        desc="4D PET file of tissue fraction before PVC",
    )
    tissue_fraction_psf = File(
        desc="4D PET file of tissue fraction after PVC (smoothed with PSF)",
    )
    seg = File(
        desc="Segmentation file of regions used for PVC",
    )
    seg_ctab = File(
        desc="Color table file for segmentation file",
    )


class GTMPVC(FSCommand):
    """Perform Partial Volume Correction (PVC) to PET Data.

    Examples
    --------
    >>> gtmpvc = GTMPVC()
    >>> gtmpvc.inputs.in_file = 'sub-01_ses-baseline_pet.nii.gz'
    >>> gtmpvc.inputs.segmentation = 'gtmseg.mgz'
    >>> gtmpvc.inputs.reg_file = 'sub-01_ses-baseline_pet_mean_reg.lta'
    >>> gtmpvc.inputs.pvc_dir = 'pvc'
    >>> gtmpvc.inputs.psf = 4
    >>> gtmpvc.inputs.default_seg_merge = True
    >>> gtmpvc.inputs.auto_mask = (1, 0.1)
    >>> gtmpvc.inputs.km_ref = ['8 47']
    >>> gtmpvc.inputs.km_hb = ['11 12 50 51']
    >>> gtmpvc.inputs.no_rescale = True
    >>> gtmpvc.inputs.save_input = True
    >>> gtmpvc.cmdline  # doctest: +NORMALIZE_WHITESPACE
    'mri_gtmpvc --auto-mask 1.000000 0.100000 --default-seg-merge \
    --i sub-01_ses-baseline_pet.nii.gz --km-hb 11 12 50 51 --km-ref 8 47 --no-rescale \
    --psf 4.000000 --o pvc --reg sub-01_ses-baseline_pet_mean_reg.lta --save-input \
    --seg gtmseg.mgz'

    >>> gtmpvc = GTMPVC()
    >>> gtmpvc.inputs.in_file = 'sub-01_ses-baseline_pet.nii.gz'
    >>> gtmpvc.inputs.segmentation = 'gtmseg.mgz'
    >>> gtmpvc.inputs.regheader = True
    >>> gtmpvc.inputs.pvc_dir = 'pvc'
    >>> gtmpvc.inputs.mg = (0.5, ["ROI1", "ROI2"])
    >>> gtmpvc.cmdline  # doctest: +NORMALIZE_WHITESPACE
    'mri_gtmpvc --i sub-01_ses-baseline_pet.nii.gz --mg 0.5 ROI1 ROI2 --o pvc --regheader --seg gtmseg.mgz'
    """

    _cmd = "mri_gtmpvc"
    input_spec = GTMPVCInputSpec
    output_spec = GTMPVCOutputSpec

    def _format_arg(self, name, spec, val):
        # Values taken from
        # https://github.com/freesurfer/freesurfer/blob/fs-7.2/mri_gtmpvc/mri_gtmpvc.cpp#L115-L122
        if name == 'optimization_schema':
            return (
                spec.argstr
                % {
                    "3D": 1,
                    "2D": 2,
                    "1D": 3,
                    "3D_MB": 4,
                    "2D_MB": 5,
                    "1D_MB": 6,
                    "MBZ": 7,
                    "MB3": 8,
                }[val]
            )
        if name == 'mg':
            return spec.argstr % (val[0], ' '.join(val[1]))
        return super()._format_arg(name, spec, val)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        # Get the top-level output directory
        if not isdefined(self.inputs.pvc_dir):
            pvcdir = os.getcwd()
        else:
            pvcdir = os.path.abspath(self.inputs.pvc_dir)
        outputs["pvc_dir"] = pvcdir

        # Assign the output files that always get created
        outputs["ref_file"] = os.path.join(pvcdir, "km.ref.tac.dat")
        outputs["hb_nifti"] = os.path.join(pvcdir, "km.hb.tac.nii.gz")
        outputs["hb_dat"] = os.path.join(pvcdir, "km.hb.tac.dat")
        outputs["nopvc_file"] = os.path.join(pvcdir, "nopvc.nii.gz")
        outputs["gtm_file"] = os.path.join(pvcdir, "gtm.nii.gz")
        outputs["gtm_stats"] = os.path.join(pvcdir, "gtm.stats.dat")
        outputs["reg_pet2anat"] = os.path.join(pvcdir, "aux", "bbpet2anat.lta")
        outputs["reg_anat2pet"] = os.path.join(pvcdir, "aux", "anat2bbpet.lta")
        outputs["eres"] = os.path.join(pvcdir, "eres.nii.gz")
        outputs["tissue_fraction"] = os.path.join(
            pvcdir, "aux", "tissue.fraction.nii.gz"
        )
        outputs["tissue_fraction_psf"] = os.path.join(
            pvcdir, "aux", "tissue.fraction.psf.nii.gz"
        )
        outputs["seg"] = os.path.join(pvcdir, "aux", "seg.nii.gz")
        outputs["seg_ctab"] = os.path.join(pvcdir, "aux", "seg.ctab")

        # Assign the conditional outputs
        if self.inputs.save_input:
            outputs["input_file"] = os.path.join(pvcdir, "input.nii.gz")
        if self.inputs.save_yhat0:
            outputs["yhat0"] = os.path.join(pvcdir, "yhat0.nii.gz")
        if self.inputs.save_yhat:
            outputs["yhat"] = os.path.join(pvcdir, "yhat.nii.gz")
        if self.inputs.save_yhat_full_fov:
            outputs["yhat_full_fov"] = os.path.join(pvcdir, "yhat.fullfov.nii.gz")
        if self.inputs.save_yhat_with_noise:
            outputs["yhat_with_noise"] = os.path.join(pvcdir, "yhat.nii.gz")
        if self.inputs.mgx:
            outputs["mgx_ctxgm"] = os.path.join(pvcdir, "mgx.ctxgm.nii.gz")
            outputs["mgx_subctxgm"] = os.path.join(pvcdir, "mgx.subctxgm.nii.gz")
            outputs["mgx_gm"] = os.path.join(pvcdir, "mgx.gm.nii.gz")
        if self.inputs.rbv:
            outputs["rbv"] = os.path.join(pvcdir, "rbv.nii.gz")
            outputs["reg_rbvpet2anat"] = os.path.join(pvcdir, "aux", "rbv2anat.lta")
            outputs["reg_anat2rbvpet"] = os.path.join(pvcdir, "aux", "anat2rbv.lta")
        if self.inputs.optimization_schema:
            outputs["opt_params"] = os.path.join(pvcdir, "aux", "opt.params.dat")

        return outputs


class MRTM1InputSpec(GLMFitInputSpec):
    mrtm1 = Tuple(
        File(exists=True),
        File(exists=True),
        mandatory=True,
        argstr="--mrtm1 %s %s",
        desc="RefTac TimeSec : perform MRTM1 kinetic modeling",
    )


class MRTM1(GLMFit):
    """Perform MRTM1 kinetic modeling.

    Examples
    --------
    >>> mrtm = MRTM1()
    >>> mrtm.inputs.in_file = 'tac.nii'
    >>> mrtm.inputs.mrtm1 = ('ref_tac.dat', 'timing.dat')
    >>> mrtm.inputs.glm_dir = 'mrtm'
    >>> mrtm.cmdline
    'mri_glmfit --glmdir mrtm --y tac.nii --mrtm1 ref_tac.dat timing.dat'
    """

    input_spec = MRTM1InputSpec


class MRTM2InputSpec(GLMFitInputSpec):
    mrtm2 = Tuple(
        File(exists=True),
        File(exists=True),
        traits.Float,
        mandatory=True,
        argstr="--mrtm2 %s %s %f",
        desc="RefTac TimeSec k2prime : perform MRTM2 kinetic modeling",
    )


class MRTM2(GLMFit):
    """Perform MRTM2 kinetic modeling.
    Examples
    --------
    >>> mrtm2 = MRTM2()
    >>> mrtm2.inputs.in_file = 'tac.nii'
    >>> mrtm2.inputs.mrtm2 = ('ref_tac.dat', 'timing.dat', 0.07872)
    >>> mrtm2.inputs.glm_dir = 'mrtm2'
    >>> mrtm2.cmdline
    'mri_glmfit --glmdir mrtm2 --y tac.nii --mrtm2 ref_tac.dat timing.dat 0.078720'
    """

    input_spec = MRTM2InputSpec


class LoganInputSpec(GLMFitInputSpec):
    logan = Tuple(
        File(exists=True),
        File(exists=True),
        traits.Float,
        mandatory=True,
        argstr="--logan %s %s %g",
        desc="RefTac TimeSec tstar   : perform Logan kinetic modeling",
    )


class Logan(GLMFit):
    """Perform Logan kinetic modeling.
    Examples
    --------
    >>> logan = Logan()
    >>> logan.inputs.in_file = 'tac.nii'
    >>> logan.inputs.logan = ('ref_tac.dat', 'timing.dat', 2600)
    >>> logan.inputs.glm_dir = 'logan'
    >>> logan.cmdline
    'mri_glmfit --glmdir logan --y tac.nii --logan ref_tac.dat timing.dat 2600'
    """

    input_spec = LoganInputSpec
