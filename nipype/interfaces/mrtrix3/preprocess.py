# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# -*- coding: utf-8 -*-

import os.path as op

from ..base import (
    CommandLine,
    CommandLineInputSpec,
    Directory,
    File,
    InputMultiObject,
    TraitedSpec,
    Undefined,
    isdefined,
    traits,
)
from .base import MRTrix3Base, MRTrix3BaseInputSpec


class DWIDenoiseInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        position=-2,
        mandatory=True,
        desc="input DWI image",
    )
    mask = File(exists=True, argstr="-mask %s", position=1, desc="mask image")
    extent = traits.Tuple(
        (traits.Int, traits.Int, traits.Int),
        argstr="-extent %d,%d,%d",
        desc="set the window size of the denoising filter. (default = 5,5,5)",
    )
    noise = File(
        argstr="-noise %s",
        name_template="%s_noise",
        name_source="in_file",
        keep_extension=True,
        desc="the output noise map",
    )
    out_file = File(
        argstr="%s",
        position=-1,
        name_template="%s_denoised",
        name_source="in_file",
        keep_extension=True,
        desc="the output denoised DWI image",
    )


class DWIDenoiseOutputSpec(TraitedSpec):
    noise = File(desc="the output noise map", exists=True)
    out_file = File(desc="the output denoised DWI image", exists=True)


class DWIDenoise(MRTrix3Base):
    """
    Denoise DWI data and estimate the noise level based on the optimal
    threshold for PCA.

    DWI data denoising and noise map estimation by exploiting data redundancy
    in the PCA domain using the prior knowledge that the eigenspectrum of
    random covariance matrices is described by the universal Marchenko Pastur
    distribution.

    Important note: image denoising must be performed as the first step of the
    image processing pipeline. The routine will fail if interpolation or
    smoothing has been applied to the data prior to denoising.

    Note that this function does not correct for non-Gaussian noise biases.

    For more information, see
    <https://mrtrix.readthedocs.io/en/latest/reference/commands/dwidenoise.html>

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> denoise = mrt.DWIDenoise()
    >>> denoise.inputs.in_file = 'dwi.mif'
    >>> denoise.inputs.mask = 'mask.mif'
    >>> denoise.inputs.noise = 'noise.mif'
    >>> denoise.cmdline                               # doctest: +ELLIPSIS
    'dwidenoise -mask mask.mif -noise noise.mif dwi.mif dwi_denoised.mif'
    >>> denoise.run()                                 # doctest: +SKIP
    """

    _cmd = "dwidenoise"
    input_spec = DWIDenoiseInputSpec
    output_spec = DWIDenoiseOutputSpec


class MRDeGibbsInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        position=-2,
        mandatory=True,
        desc="input DWI image",
    )
    axes = traits.ListInt(
        default_value=[0, 1],
        usedefault=True,
        sep=",",
        minlen=2,
        maxlen=2,
        argstr="-axes %s",
        desc="indicate the plane in which the data was acquired (axial = 0,1; "
        "coronal = 0,2; sagittal = 1,2",
    )
    nshifts = traits.Int(
        default_value=20,
        usedefault=True,
        argstr="-nshifts %d",
        desc="discretization of subpixel spacing (default = 20)",
    )
    minW = traits.Int(
        default_value=1,
        usedefault=True,
        argstr="-minW %d",
        desc="left border of window used for total variation (TV) computation "
        "(default = 1)",
    )
    maxW = traits.Int(
        default_value=3,
        usedefault=True,
        argstr="-maxW %d",
        desc="right border of window used for total variation (TV) computation "
        "(default = 3)",
    )
    out_file = File(
        name_template="%s_unr",
        name_source="in_file",
        keep_extension=True,
        argstr="%s",
        position=-1,
        desc="the output unringed DWI image",
    )


class MRDeGibbsOutputSpec(TraitedSpec):
    out_file = File(desc="the output unringed DWI image", exists=True)


class MRDeGibbs(MRTrix3Base):
    """
    Remove Gibbs ringing artifacts.

    This application attempts to remove Gibbs ringing artefacts from MRI images
    using the method of local subvoxel-shifts proposed by Kellner et al.

    This command is designed to run on data directly after it has been
    reconstructed by the scanner, before any interpolation of any kind has
    taken place. You should not run this command after any form of motion
    correction (e.g. not after dwipreproc). Similarly, if you intend running
    dwidenoise, you should run this command afterwards, since it has the
    potential to alter the noise structure, which would impact on dwidenoise's
    performance.

    Note that this method is designed to work on images acquired with full
    k-space coverage. Running this method on partial Fourier ('half-scan') data
    may lead to suboptimal and/or biased results, as noted in the original
    reference below. There is currently no means of dealing with this; users
    should exercise caution when using this method on partial Fourier data, and
    inspect its output for any obvious artefacts.

    For more information, see
    <https://mrtrix.readthedocs.io/en/latest/reference/commands/mrdegibbs.html>

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> unring = mrt.MRDeGibbs()
    >>> unring.inputs.in_file = 'dwi.mif'
    >>> unring.cmdline
    'mrdegibbs -axes 0,1 -maxW 3 -minW 1 -nshifts 20 dwi.mif dwi_unr.mif'
    >>> unring.run()                                 # doctest: +SKIP
    """

    _cmd = "mrdegibbs"
    input_spec = MRDeGibbsInputSpec
    output_spec = MRDeGibbsOutputSpec


class DWIBiasCorrectInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        position=-2,
        mandatory=True,
        desc="input DWI image",
    )
    in_mask = File(argstr="-mask %s", desc="input mask image for bias field estimation")
    use_ants = traits.Bool(
        argstr="ants",
        mandatory=True,
        desc="use ANTS N4 to estimate the inhomogeneity field",
        position=0,
        xor=["use_fsl"],
    )
    use_fsl = traits.Bool(
        argstr="fsl",
        mandatory=True,
        desc="use FSL FAST to estimate the inhomogeneity field",
        position=0,
        xor=["use_ants"],
    )
    bias = File(argstr="-bias %s", desc="bias field")
    out_file = File(
        name_template="%s_biascorr",
        name_source="in_file",
        keep_extension=True,
        argstr="%s",
        position=-1,
        desc="the output bias corrected DWI image",
        genfile=True,
    )


class DWIBiasCorrectOutputSpec(TraitedSpec):
    bias = File(desc="the output bias field", exists=True)
    out_file = File(desc="the output bias corrected DWI image", exists=True)


class DWIBiasCorrect(MRTrix3Base):
    """
    Perform B1 field inhomogeneity correction for a DWI volume series.

    For more information, see
    <https://mrtrix.readthedocs.io/en/latest/reference/scripts/dwibiascorrect.html>

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> bias_correct = mrt.DWIBiasCorrect()
    >>> bias_correct.inputs.in_file = 'dwi.mif'
    >>> bias_correct.inputs.use_ants = True
    >>> bias_correct.cmdline
    'dwibiascorrect ants dwi.mif dwi_biascorr.mif'
    >>> bias_correct.run()                             # doctest: +SKIP
    """

    _cmd = "dwibiascorrect"
    input_spec = DWIBiasCorrectInputSpec
    output_spec = DWIBiasCorrectOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if name in ("use_ants", "use_fsl"):
            ver = self.version
            # Changed in version 3.0, after release candidates
            if ver is not None and (ver[0] < "3" or ver.startswith("3.0_RC")):
                return f"-{trait_spec.argstr}"
        return super()._format_arg(name, trait_spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if self.inputs.out_file:
            outputs["out_file"] = op.abspath(self.inputs.out_file)
        if self.inputs.bias:
            outputs["bias"] = op.abspath(self.inputs.bias)
        return outputs


class DWIPreprocInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        position=0,
        mandatory=True,
        desc="input DWI image",
    )
    out_file = File(
        "preproc.mif",
        argstr="%s",
        mandatory=True,
        position=1,
        usedefault=True,
        desc="output file after preprocessing",
    )
    rpe_options = traits.Enum(
        "none",
        "pair",
        "all",
        "header",
        argstr="-rpe_%s",
        position=2,
        mandatory=True,
        desc='Specify acquisition phase-encoding design. "none" for no reversed phase-encoding image, "all" for all DWIs have opposing phase-encoding acquisition, "pair" for using a pair of b0 volumes for inhomogeneity field estimation only, and "header" for phase-encoding information can be found in the image header(s)',
    )
    pe_dir = traits.Str(
        argstr="-pe_dir %s",
        desc="Specify the phase encoding direction of the input series, can be a signed axis number (e.g. -0, 1, +2), an axis designator (e.g. RL, PA, IS), or NIfTI axis codes (e.g. i-, j, k)",
    )
    ro_time = traits.Float(
        argstr="-readout_time %f",
        desc="Total readout time of input series (in seconds)",
    )
    in_epi = File(
        exists=True,
        argstr="-se_epi %s",
        desc="Provide an additional image series consisting of spin-echo EPI images, which is to be used exclusively by topup for estimating the inhomogeneity field (i.e. it will not form part of the output image series)",
    )
    align_seepi = traits.Bool(
        argstr="-align_seepi",
        desc="Achieve alignment between the SE-EPI images used for inhomogeneity field estimation, and the DWIs",
    )
    json_import = File(
        exists=True,
        argstr="-json_import %s",
        desc="Import image header information from an associated JSON file (may be necessary to determine phase encoding information)",
    )
    topup_options = traits.Str(
        argstr='-topup_options "%s"',
        desc="Manually provide additional command-line options to the topup command",
    )
    eddy_options = traits.Str(
        argstr='-eddy_options "%s"',
        desc="Manually provide additional command-line options to the eddy command",
    )
    eddy_mask = File(
        exists=True,
        argstr="-eddy_mask %s",
        desc="Provide a processing mask to use for eddy, instead of having dwifslpreproc generate one internally using dwi2mask",
    )
    eddy_slspec = File(
        exists=True,
        argstr="-eddy_slspec %s",
        desc="Provide a file containing slice groupings for eddy's slice-to-volume registration",
    )
    eddyqc_text = Directory(
        exists=False,
        argstr="-eddyqc_text %s",
        desc="Copy the various text-based statistical outputs generated by eddy, and the output of eddy_qc (if installed), into an output directory",
    )
    eddyqc_all = Directory(
        exists=False,
        argstr="-eddyqc_all %s",
        desc="Copy ALL outputs generated by eddy (including images), and the output of eddy_qc (if installed), into an output directory",
    )
    out_grad_mrtrix = File(
        "grad.b",
        argstr="-export_grad_mrtrix %s",
        desc="export new gradient files in mrtrix format",
    )
    out_grad_fsl = traits.Tuple(
        File("grad.bvecs", desc="bvecs"),
        File("grad.bvals", desc="bvals"),
        argstr="-export_grad_fsl %s, %s",
        desc="export gradient files in FSL format",
    )


class DWIPreprocOutputSpec(TraitedSpec):
    out_file = File(argstr="%s", desc="output preprocessed image series")
    out_grad_mrtrix = File(
        "grad.b",
        argstr="%s",
        usedefault=True,
        desc="preprocessed gradient file in mrtrix3 format",
    )
    out_fsl_bvec = File(
        "grad.bvecs",
        argstr="%s",
        usedefault=True,
        desc="exported fsl gradient bvec file",
    )
    out_fsl_bval = File(
        "grad.bvals",
        argstr="%s",
        usedefault=True,
        desc="exported fsl gradient bval file",
    )


class DWIPreproc(MRTrix3Base):
    """
    Perform diffusion image pre-processing using FSL's eddy tool; including inhomogeneity distortion correction using FSL's topup tool if possible

    For more information, see
    <https://mrtrix.readthedocs.io/en/latest/reference/commands/dwifslpreproc.html>

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> preproc = mrt.DWIPreproc()
    >>> preproc.inputs.in_file = 'dwi.mif'
    >>> preproc.inputs.rpe_options = 'none'
    >>> preproc.inputs.out_file = "preproc.mif"
    >>> preproc.inputs.eddy_options = '--slm=linear --repol'     # linear second level model and replace outliers
    >>> preproc.inputs.out_grad_mrtrix = "grad.b"    # export final gradient table in MRtrix format
    >>> preproc.inputs.ro_time = 0.165240   # 'TotalReadoutTime' in BIDS JSON metadata files
    >>> preproc.inputs.pe_dir = 'j'     # 'PhaseEncodingDirection' in BIDS JSON metadata files
    >>> preproc.cmdline
    'dwifslpreproc dwi.mif preproc.mif -rpe_none -eddy_options "--slm=linear --repol" -export_grad_mrtrix grad.b -pe_dir j -readout_time 0.165240'
    >>> preproc.run()                             # doctest: +SKIP
    """

    _cmd = "dwifslpreproc"
    input_spec = DWIPreprocInputSpec
    output_spec = DWIPreprocOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        if self.inputs.export_grad_mrtrix:
            outputs["out_grad_mrtrix"] = op.abspath(self.inputs.out_grad_mrtrix)
        if self.inputs.export_grad_fsl:
            outputs["out_fsl_bvec"] = op.abspath(self.inputs.out_grad_fsl[0])
            outputs["out_fsl_bval"] = op.abspath(self.inputs.out_grad_fsl[1])

        return outputs


class ResponseSDInputSpec(MRTrix3BaseInputSpec):
    algorithm = traits.Enum(
        "msmt_5tt",
        "dhollander",
        "tournier",
        "tax",
        argstr="%s",
        position=1,
        mandatory=True,
        desc="response estimation algorithm (multi-tissue)",
    )
    in_file = File(
        exists=True,
        argstr="%s",
        position=-5,
        mandatory=True,
        desc="input DWI image",
    )
    mtt_file = File(argstr="%s", position=-4, desc="input 5tt image")
    wm_file = File(
        "wm.txt",
        argstr="%s",
        position=-3,
        usedefault=True,
        desc="output WM response text file",
    )
    gm_file = File(argstr="%s", position=-2, desc="output GM response text file")
    csf_file = File(argstr="%s", position=-1, desc="output CSF response text file")
    in_mask = File(exists=True, argstr="-mask %s", desc="provide initial mask image")
    max_sh = InputMultiObject(
        traits.Int,
        argstr="-lmax %s",
        sep=",",
        desc=(
            "maximum harmonic degree of response function - single value for "
            "single-shell response, list for multi-shell response"
        ),
    )


class ResponseSDOutputSpec(TraitedSpec):
    wm_file = File(argstr="%s", desc="output WM response text file")
    gm_file = File(argstr="%s", desc="output GM response text file")
    csf_file = File(argstr="%s", desc="output CSF response text file")


class ResponseSD(MRTrix3Base):
    """
    Estimate response function(s) for spherical deconvolution using the specified algorithm.

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> resp = mrt.ResponseSD()
    >>> resp.inputs.in_file = 'dwi.mif'
    >>> resp.inputs.algorithm = 'tournier'
    >>> resp.inputs.grad_fsl = ('bvecs', 'bvals')
    >>> resp.cmdline                               # doctest: +ELLIPSIS
    'dwi2response tournier -fslgrad bvecs bvals dwi.mif wm.txt'
    >>> resp.run()                                 # doctest: +SKIP

    # We can also pass in multiple harmonic degrees in the case of multi-shell
    >>> resp.inputs.max_sh = [6,8,10]
    >>> resp.cmdline
    'dwi2response tournier -fslgrad bvecs bvals -lmax 6,8,10 dwi.mif wm.txt'
    """

    _cmd = "dwi2response"
    input_spec = ResponseSDInputSpec
    output_spec = ResponseSDOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["wm_file"] = op.abspath(self.inputs.wm_file)
        if self.inputs.gm_file != Undefined:
            outputs["gm_file"] = op.abspath(self.inputs.gm_file)
        if self.inputs.csf_file != Undefined:
            outputs["csf_file"] = op.abspath(self.inputs.csf_file)
        return outputs


class ACTPrepareFSLInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="input anatomical image",
    )

    out_file = File(
        "act_5tt.mif",
        argstr="%s",
        mandatory=True,
        position=-1,
        usedefault=True,
        desc="output file after processing",
    )


class ACTPrepareFSLOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output response file")


class ACTPrepareFSL(CommandLine):
    """
    Generate anatomical information necessary for Anatomically
    Constrained Tractography (ACT).

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> prep = mrt.ACTPrepareFSL()
    >>> prep.inputs.in_file = 'T1.nii.gz'
    >>> prep.cmdline                               # doctest: +ELLIPSIS
    'act_anat_prepare_fsl T1.nii.gz act_5tt.mif'
    >>> prep.run()                                 # doctest: +SKIP
    """

    _cmd = "act_anat_prepare_fsl"
    input_spec = ACTPrepareFSLInputSpec
    output_spec = ACTPrepareFSLOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs


class ReplaceFSwithFIRSTInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-4,
        desc="input anatomical image",
    )
    in_t1w = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-3,
        desc="input T1 image",
    )
    in_config = File(
        exists=True,
        argstr="%s",
        position=-2,
        desc="connectome configuration file",
    )

    out_file = File(
        "aparc+first.mif",
        argstr="%s",
        mandatory=True,
        position=-1,
        usedefault=True,
        desc="output file after processing",
    )


class ReplaceFSwithFIRSTOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output response file")


class ReplaceFSwithFIRST(CommandLine):
    """
    Replace deep gray matter structures segmented with FSL FIRST in a
    FreeSurfer parcellation.

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> prep = mrt.ReplaceFSwithFIRST()
    >>> prep.inputs.in_file = 'aparc+aseg.nii'
    >>> prep.inputs.in_t1w = 'T1.nii.gz'
    >>> prep.inputs.in_config = 'mrtrix3_labelconfig.txt'
    >>> prep.cmdline                               # doctest: +ELLIPSIS
    'fs_parc_replace_sgm_first aparc+aseg.nii T1.nii.gz \
mrtrix3_labelconfig.txt aparc+first.mif'
    >>> prep.run()                                 # doctest: +SKIP
    """

    _cmd = "fs_parc_replace_sgm_first"
    input_spec = ReplaceFSwithFIRSTInputSpec
    output_spec = ReplaceFSwithFIRSTOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs
