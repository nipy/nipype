# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""This commandline module provides classes for interfacing with the
`ICA-AROMA.py <https://github.com/maartenmennes/ICA-AROMA>`__ command line tool.
"""

from ..base import (
    TraitedSpec,
    CommandLineInputSpec,
    CommandLine,
    File,
    Directory,
    traits,
    isdefined,
)
import os


class ICA_AROMAInputSpec(CommandLineInputSpec):
    feat_dir = Directory(
        exists=True,
        mandatory=True,
        argstr="-feat %s",
        xor=["in_file", "mat_file", "fnirt_warp_file", "motion_parameters"],
        desc="If a feat directory exists and temporal filtering "
        "has not been run yet, ICA_AROMA can use the files in "
        "this directory.",
    )
    in_file = File(
        exists=True,
        mandatory=True,
        argstr="-i %s",
        xor=["feat_dir"],
        desc="volume to be denoised",
    )
    out_dir = Directory(
        "out", usedefault=True, mandatory=True, argstr="-o %s", desc="output directory"
    )
    mask = File(
        exists=True, argstr="-m %s", xor=["feat_dir"], desc="path/name volume mask"
    )
    dim = traits.Int(
        argstr="-dim %d",
        desc="Dimensionality reduction when running "
        "MELODIC (default is automatic estimation)",
    )
    TR = traits.Float(
        argstr="-tr %.3f",
        desc="TR in seconds. If this is not specified "
        "the TR will be extracted from the "
        "header of the fMRI nifti file.",
    )
    melodic_dir = Directory(
        exists=True,
        argstr="-meldir %s",
        desc="path to MELODIC directory if MELODIC has already been run",
    )
    mat_file = File(
        exists=True,
        argstr="-affmat %s",
        xor=["feat_dir"],
        desc="path/name of the mat-file describing the "
        "affine registration (e.g. FSL FLIRT) of the "
        "functional data to structural space (.mat file)",
    )
    fnirt_warp_file = File(
        exists=True,
        argstr="-warp %s",
        xor=["feat_dir"],
        desc="File name of the warp-file describing "
        "the non-linear registration (e.g. FSL FNIRT) "
        "of the structural data to MNI152 space (.nii.gz)",
    )
    motion_parameters = File(
        exists=True,
        mandatory=True,
        argstr="-mc %s",
        xor=["feat_dir"],
        desc="motion parameters file",
    )
    denoise_type = traits.Enum(
        "nonaggr",
        "aggr",
        "both",
        "no",
        usedefault=True,
        mandatory=True,
        argstr="-den %s",
        desc="Type of denoising strategy:\n"
        "-no: only classification, no denoising\n"
        "-nonaggr (default): non-aggresssive denoising, i.e. partial component regression\n"
        "-aggr: aggressive denoising, i.e. full component regression\n"
        "-both: both aggressive and non-aggressive denoising (two outputs)",
    )


class ICA_AROMAOutputSpec(TraitedSpec):
    aggr_denoised_file = File(
        exists=True, desc="if generated: aggressively denoised volume"
    )
    nonaggr_denoised_file = File(
        exists=True, desc="if generated: non aggressively denoised volume"
    )
    out_dir = Directory(
        exists=True,
        desc="directory contains (in addition to the denoised files): "
        "melodic.ica + classified_motion_components + "
        "classification_overview + feature_scores + melodic_ic_mni)",
    )


class ICA_AROMA(CommandLine):
    """
    Interface for the ICA_AROMA.py script.

    ICA-AROMA (i.e. 'ICA-based Automatic Removal Of Motion Artifacts') concerns
    a data-driven method to identify and remove motion-related independent
    components from fMRI data. To that end it exploits a small, but robust
    set of theoretically motivated features, preventing the need for classifier
    re-training and therefore providing direct and easy applicability.

    See link for further documentation: https://github.com/rhr-pruim/ICA-AROMA

    Example
    -------

    >>> from nipype.interfaces.fsl import ICA_AROMA
    >>> from nipype.testing import example_data
    >>> AROMA_obj = ICA_AROMA()
    >>> AROMA_obj.inputs.in_file = 'functional.nii'
    >>> AROMA_obj.inputs.mat_file = 'func_to_struct.mat'
    >>> AROMA_obj.inputs.fnirt_warp_file = 'warpfield.nii'
    >>> AROMA_obj.inputs.motion_parameters = 'fsl_mcflirt_movpar.txt'
    >>> AROMA_obj.inputs.mask = 'mask.nii.gz'
    >>> AROMA_obj.inputs.denoise_type = 'both'
    >>> AROMA_obj.inputs.out_dir = 'ICA_testout'
    >>> AROMA_obj.cmdline  # doctest: +ELLIPSIS
    'ICA_AROMA.py -den both -warp warpfield.nii -i functional.nii -m mask.nii.gz -affmat func_to_struct.mat -mc fsl_mcflirt_movpar.txt -o .../ICA_testout'
    """

    _cmd = "ICA_AROMA.py"
    input_spec = ICA_AROMAInputSpec
    output_spec = ICA_AROMAOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if name == "out_dir":
            return trait_spec.argstr % os.path.abspath(value)
        return super(ICA_AROMA, self)._format_arg(name, trait_spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_dir"] = os.path.abspath(self.inputs.out_dir)
        out_dir = outputs["out_dir"]

        if self.inputs.denoise_type in ("aggr", "both"):
            outputs["aggr_denoised_file"] = os.path.join(
                out_dir, "denoised_func_data_aggr.nii.gz"
            )
        if self.inputs.denoise_type in ("nonaggr", "both"):
            outputs["nonaggr_denoised_file"] = os.path.join(
                out_dir, "denoised_func_data_nonaggr.nii.gz"
            )
        return outputs
