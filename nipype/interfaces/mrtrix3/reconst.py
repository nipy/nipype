# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# -*- coding: utf-8 -*-

import os.path as op

from ..base import traits, TraitedSpec, File, InputMultiObject, isdefined
from .base import MRTrix3BaseInputSpec, MRTrix3Base


class FitTensorInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="input diffusion weighted images",
    )
    out_file = File(
        "dti.mif",
        argstr="%s",
        mandatory=True,
        position=-1,
        usedefault=True,
        desc="the output diffusion tensor image",
    )

    # General options
    in_mask = File(
        exists=True,
        argstr="-mask %s",
        desc=("only perform computation within the specified binary brain mask image"),
    )
    method = traits.Enum(
        "nonlinear",
        "loglinear",
        "sech",
        "rician",
        argstr="-method %s",
        desc=("select method used to perform the fitting"),
    )
    reg_term = traits.Float(
        argstr="-regularisation %f",
        max_ver="0.3.13",
        desc=(
            "specify the strength of the regularisation term on the "
            "magnitude of the tensor elements (default = 5000). This "
            "only applies to the non-linear methods"
        ),
    )
    predicted_signal = File(
        argstr="-predicted_signal %s",
        desc=(
            "specify a file to contain the predicted signal from the tensor "
            "fits. This can be used to calculate the residual signal"
        ),
    )


class FitTensorOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output DTI file")
    predicted_signal = File(desc="Predicted signal from fitted tensors")


class FitTensor(MRTrix3Base):
    """
    Convert diffusion-weighted images to tensor images


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> tsr = mrt.FitTensor()
    >>> tsr.inputs.in_file = 'dwi.mif'
    >>> tsr.inputs.in_mask = 'mask.nii.gz'
    >>> tsr.inputs.grad_fsl = ('bvecs', 'bvals')
    >>> tsr.cmdline                               # doctest: +ELLIPSIS
    'dwi2tensor -fslgrad bvecs bvals -mask mask.nii.gz dwi.mif dti.mif'
    >>> tsr.run()                                 # doctest: +SKIP
    """

    _cmd = "dwi2tensor"
    input_spec = FitTensorInputSpec
    output_spec = FitTensorOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        if isdefined(self.inputs.predicted_signal):
            outputs["predicted_signal"] = op.abspath(self.inputs.predicted_signal)
        return outputs


class EstimateFODInputSpec(MRTrix3BaseInputSpec):
    algorithm = traits.Enum(
        "csd",
        "msmt_csd",
        argstr="%s",
        position=-8,
        mandatory=True,
        desc="FOD algorithm",
    )
    in_file = File(
        exists=True, argstr="%s", position=-7, mandatory=True, desc="input DWI image"
    )
    wm_txt = File(
        argstr="%s", position=-6, mandatory=True, desc="WM response text file"
    )
    wm_odf = File(
        "wm.mif",
        argstr="%s",
        position=-5,
        usedefault=True,
        mandatory=True,
        desc="output WM ODF",
    )
    gm_txt = File(argstr="%s", position=-4, desc="GM response text file")
    gm_odf = File(
        "gm.mif", usedefault=True, argstr="%s", position=-3, desc="output GM ODF"
    )
    csf_txt = File(argstr="%s", position=-2, desc="CSF response text file")
    csf_odf = File(
        "csf.mif", usedefault=True, argstr="%s", position=-1, desc="output CSF ODF"
    )
    mask_file = File(exists=True, argstr="-mask %s", desc="mask image")

    # DW Shell selection options
    shell = traits.List(
        traits.Float,
        sep=",",
        argstr="-shell %s",
        desc="specify one or more dw gradient shells",
    )
    max_sh = InputMultiObject(
        traits.Int,
        value=[8],
        usedefault=True,
        argstr="-lmax %s",
        sep=",",
        desc=(
            "maximum harmonic degree of response function - single value for single-shell response, list for multi-shell response"
        ),
    )
    in_dirs = File(
        exists=True,
        argstr="-directions %s",
        desc=(
            "specify the directions over which to apply the non-negativity "
            "constraint (by default, the built-in 300 direction set is "
            "used). These should be supplied as a text file containing the "
            "[ az el ] pairs for the directions."
        ),
    )
    predicted_signal = File(
        argstr="-predicted_signal %s",
        desc=(
            "specify a file to contain the predicted signal from the FOD "
            "estimates. This can be used to calculate the residual signal."
            "Note that this is only valid if algorithm == 'msmt_csd'. "
            "For single shell reconstructions use a combination of SHConv "
            "and SH2Amp instead."
        ),
    )


class EstimateFODOutputSpec(TraitedSpec):
    wm_odf = File(argstr="%s", desc="output WM ODF")
    gm_odf = File(argstr="%s", desc="output GM ODF")
    csf_odf = File(argstr="%s", desc="output CSF ODF")
    predicted_signal = File(desc="output predicted signal")


class EstimateFOD(MRTrix3Base):
    """
    Estimate fibre orientation distributions from diffusion data using spherical deconvolution

    .. warning::

       The CSD algorithm does not work as intended, but fixing it in this interface could break
       existing workflows. This interface has been superseded by
       :py:class:`.ConstrainedSphericalDecomposition`.

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> fod = mrt.EstimateFOD()
    >>> fod.inputs.algorithm = 'msmt_csd'
    >>> fod.inputs.in_file = 'dwi.mif'
    >>> fod.inputs.wm_txt = 'wm.txt'
    >>> fod.inputs.grad_fsl = ('bvecs', 'bvals')
    >>> fod.cmdline
    'dwi2fod -fslgrad bvecs bvals -lmax 8 msmt_csd dwi.mif wm.txt wm.mif gm.mif csf.mif'
    >>> fod.run()  # doctest: +SKIP
    """

    _cmd = "dwi2fod"
    input_spec = EstimateFODInputSpec
    output_spec = EstimateFODOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["wm_odf"] = op.abspath(self.inputs.wm_odf)
        if isdefined(self.inputs.gm_odf):
            outputs["gm_odf"] = op.abspath(self.inputs.gm_odf)
        if isdefined(self.inputs.csf_odf):
            outputs["csf_odf"] = op.abspath(self.inputs.csf_odf)
        if isdefined(self.inputs.predicted_signal):
            if self.inputs.algorithm != "msmt_csd":
                raise Exception(
                    "'predicted_signal' option can only be used with "
                    "the 'msmt_csd' algorithm"
                )
            outputs["predicted_signal"] = op.abspath(self.inputs.predicted_signal)
        return outputs


class ConstrainedSphericalDeconvolutionInputSpec(EstimateFODInputSpec):
    gm_odf = File(argstr="%s", position=-3, desc="output GM ODF")
    csf_odf = File(argstr="%s", position=-1, desc="output CSF ODF")
    max_sh = InputMultiObject(
        traits.Int,
        argstr="-lmax %s",
        sep=",",
        desc=(
            "maximum harmonic degree of response function - single value for single-shell response, list for multi-shell response"
        ),
    )


class ConstrainedSphericalDeconvolution(EstimateFOD):
    """
    Estimate fibre orientation distributions from diffusion data using spherical deconvolution

    This interface supersedes :py:class:`.EstimateFOD`.
    The old interface has contained a bug when using the CSD algorithm as opposed to the MSMT CSD
    algorithm, but fixing it could potentially break existing workflows. The new interface works
    the same, but does not populate the following inputs by default:

    * ``gm_odf``
    * ``csf_odf``
    * ``max_sh``

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> fod = mrt.ConstrainedSphericalDeconvolution()
    >>> fod.inputs.algorithm = 'csd'
    >>> fod.inputs.in_file = 'dwi.mif'
    >>> fod.inputs.wm_txt = 'wm.txt'
    >>> fod.inputs.grad_fsl = ('bvecs', 'bvals')
    >>> fod.cmdline
    'dwi2fod -fslgrad bvecs bvals csd dwi.mif wm.txt wm.mif'
    >>> fod.run()  # doctest: +SKIP
    """

    input_spec = ConstrainedSphericalDeconvolutionInputSpec
