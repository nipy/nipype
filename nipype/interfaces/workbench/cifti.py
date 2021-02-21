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





class CiftiCorrelationInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr="%s ",
        position=0,
        desc="The input ptseries or dense series",
    )
    out_file = File(
        name_source=["in_file"],
        name_template="correlation_matrix_%s.nii",
        keep_extension=True,
        argstr=" %s",
        position=1,
        desc="The output CIFTI",
    )
    
    roi_override = traits.Bool(
        exists=True,
        argstr="-roi-override %s ",
        position=2,
        desc=" perform correlation from a subset of rows to all rows",
    )
    
    left_roi = File(
        exists=True,
        position=3,
        argstr="-left-roi %s",
        desc="Specify the left roi metric  to use",
    )

    right_roi = File(
        exists=True,
        position=5,
        argstr="-right-roi %s",
        desc="Specify the right  roi metric  to use",
    )
    cerebellum_roi = File(
        exists=True,
        position=6,
        argstr="-cerebellum-roi %s",
        desc="specify the cerebellum meytric to use",
    )
    
    vol_roi = File(
        exists=True,
        position=7,
        argstr="-vol-roi %s",
        desc="volume roi to use",
    )

    cifti_roi = File(
        exists=True,
        position=8,
        argstr="-cifti-roi %s",
        desc="cifti roi to use",
    )
    weights_file= File(
        exists=True,
        position=9,
        argstr="-weights %s",
        desc="specify the cerebellum surface  metricto use",
    )

    fisher_ztrans = traits.Bool(
        position=10,
        argstr="-fisher-z",
        desc=" fisherz transfrom",
    )
    no_demean = traits.Bool(
        position=11,
        argstr="-fisher-z",
        desc=" fisherz transfrom",
    )
    compute_covariance = traits.Bool(
        position=12,
        argstr="-covariance ",
        desc=" compute covariance instead of correlation",
    )

class CiftiCorrelationOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output CIFTI file")

class CiftiCorrelation(WBCommand):
    r"""
    Compute correlation from CIFTI file
    The input cifti file must have a brain models mapping on the chosen
    dimension, columns for .ptseries or .dtseries,  
    >>> cifticorr = CiftiCorrelation()
    >>> cifticorr.inputs.in_file = 'sub-01XX_task-rest.ptseries.nii'
    >>> cifticorr.inputs.out_file = 'sub_01XX_task-rest.pconn.nii'
    >>> cifticorr.cmdline
    wb_command  -cifti-correlation sub-01XX_task-rest.ptseries.nii \
        'sub_01XX_task-rest.pconn.nii'
    """

    input_spec = CiftiCorrelationInputSpec
    output_spec = CiftiCorrelationOutputSpec
    _cmd = "wb_command  -cifti-correlation" 


class CiftiParcellateInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr="%s ",
        position=0,
        desc="The input CIFTI file",
    )
    atlas_label = traits.File(
        mandatory=True,
        argstr="%s ",
        position=1,
        desc="atlas label, in mm",
    )
    direction = traits.Enum(
        "ROW",
        "COLUMN",
        mandatory=True,
        argstr="%s ",
        position=2,
        desc="which dimension to smooth along, ROW or COLUMN",
    )
    out_file = File(
        name_source=["in_file"],
        name_template="parcelated_%s.nii",
        keep_extension=True,
        argstr=" %s",
        position=3,
        desc="The output CIFTI",
    )
    
    spatial_weights = traits.Str(
        argstr="-spatial-weights ",
        position=4,
        desc=" spatial weight file",
    )
    
    left_area_surf = File(
        exists=True,
        position=5,
        argstr="-left-area-surface %s",
        desc="Specify the left surface to use",
    )

    right_area_surf = File(
        exists=True,
        position=6,
        argstr="-right-area-surface %s",
        desc="Specify the right surface to use",
    )
    cerebellum_area_surf = File(
        exists=True,
        position=7,
        argstr="-cerebellum-area-surf %s",
        desc="specify the cerebellum surface to use",
    )
    
    left_area_metric = File(
        exists=True,
        position=8,
        argstr="-left-area-metric %s",
        desc="Specify the left surface metric to use",
    )

    right_area_metric = File(
        exists=True,
        position=9,
        argstr="-right-area-metric %s",
        desc="Specify the right surface  metric to use",
    )
    cerebellum_area_metric = File(
        exists=True,
        position=10,
        argstr="-cerebellum-area-metric %s",
        desc="specify the cerebellum surface  metricto use",
    )
    
    cifti_weights = File(
        exists=True,
        position=11,
        argstr="-cifti-weights %s",
        desc="cifti file containing weights",
    )
    cor_method = traits.Str(
        position=12,
        default='MEAN ',
        argstr="-method %s",
        desc=" correlation method, option inlcude MODE",
    )

class CiftiParcellateOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output CIFTI file")


class CiftiParcellate(WBCommand):
    r"""
    Extract timeseries from CIFTI file
    The input cifti file must have a brain models mapping on the chosen
    dimension, columns for .dtseries,  
    >>> ciftiparcel = CiftiParcellate()
    >>> ciftiparcel.inputs.in_file = 'sub-01XX_task-rest.dtseries.nii'
    >>> ciftiparcel.inputs.out_file = 'sub_01XX_task-rest.ptseries.nii'
    >>>  ciftiparcel.inputs.atlas_label = 'schaefer_space-fsLR_den-32k_desc-400_atlas.dlabel.nii' 
    >>> ciftiparcel.inputs.direction = 'COLUMN'
    >>> ciftiparcel.cmdline
    wb_command -cifti-parcellate sub-01XX_task-rest.dtseries.nii \
    schaefer_space-fsLR_den-32k_desc-400_atlas.dlabel.nii   COLUMN \  
    sub_01XX_task-rest.ptseries.nii
    """
    input_spec = CiftiParcellateInputSpec
    output_spec = CiftiParcellateOutputSpec
    _cmd = "wb_command -cifti-parcellate"

class CiftiSeparateMetricInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr="%s ",
        position=0,
        desc="The input dense series",
    )
    direction = traits.Enum(
        "ROW",
        "COLUMN",
        mandatory=True,
        argstr="%s ",
        position=1,
        desc="which dimension to smooth along, ROW or COLUMN",
    )
    metric = traits.Str(
        mandatory=True,
        argstr=" -metric %s ",
        position=2,
        desc="which of the structure eg CORTEX_LEFT CORTEX_RIGHT" \
            "check https://www.humanconnectome.org/software/workbench-command/-cifti-separate ",
    )
    out_file = File(
        name_source=["in_file"],
        name_template="correlation_matrix_%s.func.gii",
        keep_extension=True,
        argstr=" %s",
        position=3,
        desc="The gifti output, iether left and right",
    )
    
class CiftiSeparateMetricOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output CIFTI file")

class CiftiSeparateMetric(WBCommand):
    r"""
    Extract left or right hemisphere surface from CIFTI file (.dtseries)
    other structure can also be extracted
    The input cifti file must have a brain models mapping on the chosen
    dimension, columns for .dtseries,  
    >>> ciftiseparate = CiftiSeparateMetric()
    >>> ciftiseparate.inputs.in_file = 'sub-01XX_task-rest.dtseries.nii'
    >>> ciftiseparate.inputs.metric = "CORTEX_LEFT" # extract left hemisphere
    >>> ciftiseparate.inputs.out_file = 'sub_01XX_task-rest_hemi-L.func.gii'
    >>> ciftiseparate.inputs.direction = 'COLUMN'
    >>> ciftiseparate.cmdline
    wb_command  -cifti-separate 'sub-01XX_task-rest.dtseries.nii'  COLUMN \
      -metric CORTEX_LEFT 'sub_01XX_task-rest_hemi-L.func.gii'
    """
    input_spec = CiftiSeparateMetricInputSpec
    output_spec = CiftiSeparateMetricOutputSpec
    _cmd = "wb_command  -cifti-separate "