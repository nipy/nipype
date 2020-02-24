# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""This module provides interfaces for workbench CIFTI commands"""
from ..base import TraitedSpec, File, traits, CommandLineInputSpec
from .base import WBCommand
from ... import logging

iflogger = logging.getLogger("nipype.interface")


class CiftiSmoothInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=0,
        desc="The input CIFTI file",
    )
    sigma_surf = traits.Float(
        mandatory=True,
        argstr="%s",
        position=1,
        desc="the sigma for the gaussian surface smoothing kernel, in mm",
    )
    sigma_vol = traits.Float(
        mandatory=True,
        argstr="%s",
        position=2,
        desc="the sigma for the gaussian volume smoothing kernel, in mm",
    )
    direction = traits.Enum(
        "ROW",
        "COLUMN",
        mandatory=True,
        argstr="%s",
        position=3,
        desc="which dimension to smooth along, ROW or COLUMN",
    )
    out_file = File(
        name_source=["in_file"],
        name_template="smoothed_%s.nii",
        keep_extension=True,
        argstr="%s",
        position=4,
        desc="The output CIFTI",
    )
    left_surf = File(
        exists=True,
        mandatory=True,
        position=5,
        argstr="-left-surface %s",
        desc="Specify the left surface to use",
    )
    left_corrected_areas = File(
        exists=True,
        position=6,
        argstr="-left-corrected-areas %s",
        desc="vertex areas (as a metric) to use instead of computing them from "
        "the left surface.",
    )
    right_surf = File(
        exists=True,
        mandatory=True,
        position=7,
        argstr="-right-surface %s",
        desc="Specify the right surface to use",
    )
    right_corrected_areas = File(
        exists=True,
        position=8,
        argstr="-right-corrected-areas %s",
        desc="vertex areas (as a metric) to use instead of computing them from "
        "the right surface",
    )
    cerebellum_surf = File(
        exists=True,
        position=9,
        argstr="-cerebellum-surface %s",
        desc="specify the cerebellum surface to use",
    )
    cerebellum_corrected_areas = File(
        exists=True,
        position=10,
        requires=["cerebellum_surf"],
        argstr="cerebellum-corrected-areas %s",
        desc="vertex areas (as a metric) to use instead of computing them from "
        "the cerebellum surface",
    )
    cifti_roi = File(
        exists=True,
        position=11,
        argstr="-cifti-roi %s",
        desc="CIFTI file for ROI smoothing",
    )
    fix_zeros_vol = traits.Bool(
        position=12,
        argstr="-fix-zeros-volume",
        desc="treat values of zero in the volume as missing data",
    )
    fix_zeros_surf = traits.Bool(
        position=13,
        argstr="-fix-zeros-surface",
        desc="treat values of zero on the surface as missing data",
    )
    merged_volume = traits.Bool(
        position=14,
        argstr="-merged-volume",
        desc="smooth across subcortical structure boundaries",
    )


class CiftiSmoothOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output CIFTI file")


class CiftiSmooth(WBCommand):
    """
    Smooth a CIFTI file

    The input cifti file must have a brain models mapping on the chosen
    dimension, columns for .dtseries, and either for .dconn.  By default,
    data in different structures is smoothed independently (i.e., "parcel
    constrained" smoothing), so volume structures that touch do not smooth
    across this boundary.  Specify ``merged_volume`` to ignore these
    boundaries. Surface smoothing uses the ``GEO_GAUSS_AREA`` smoothing method.

    The ``*_corrected_areas`` options are intended for when it is unavoidable
    to smooth on group average surfaces, it is only an approximate correction
    for the reduction of structure in a group average surface.  It is better
    to smooth the data on individuals before averaging, when feasible.

    The ``fix_zeros_*`` options will treat values of zero as lack of data, and
    not use that value when generating the smoothed values, but will fill
    zeros with extrapolated values.  The ROI should have a brain models
    mapping along columns, exactly matching the mapping of the chosen
    direction in the input file.  Data outside the ROI is ignored.

    >>> from nipype.interfaces.workbench import CiftiSmooth
    >>> smooth = CiftiSmooth()
    >>> smooth.inputs.in_file = 'sub-01_task-rest.dtseries.nii'
    >>> smooth.inputs.sigma_surf = 4
    >>> smooth.inputs.sigma_vol = 4
    >>> smooth.inputs.direction = 'COLUMN'
    >>> smooth.inputs.right_surf = 'sub-01.R.midthickness.32k_fs_LR.surf.gii'
    >>> smooth.inputs.left_surf = 'sub-01.L.midthickness.32k_fs_LR.surf.gii'
    >>> smooth.cmdline
    'wb_command -cifti-smoothing sub-01_task-rest.dtseries.nii 4.0 4.0 COLUMN \
    smoothed_sub-01_task-rest.dtseries.nii \
    -left-surface sub-01.L.midthickness.32k_fs_LR.surf.gii \
    -right-surface sub-01.R.midthickness.32k_fs_LR.surf.gii'
    """

    input_spec = CiftiSmoothInputSpec
    output_spec = CiftiSmoothOutputSpec
    _cmd = "wb_command -cifti-smoothing"
