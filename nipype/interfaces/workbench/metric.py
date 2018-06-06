# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""This module provides interfaces for workbench surface commands"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
import os

from ..base import (TraitedSpec, File, traits, CommandLineInputSpec)
from .base import WBCommand
from ... import logging

iflogger = logging.getLogger('nipype.interface')


class MetricResampleInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=0,
        desc="The metric file to resample")
    current_sphere = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=1,
        desc="A sphere surface with the mesh that the metric is currently on")
    new_sphere = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=2,
        desc="A sphere surface that is in register with <current-sphere> and"
             " has the desired output mesh")
    method = traits.Enum(
        "ADAP_BARY_AREA",
        "BARYCENTRIC",
        argstr="%s",
        mandatory=True,
        position=3,
        desc="The method name - ADAP_BARY_AREA method is recommended for"
             " ordinary metric data, because it should use all data while"
             " downsampling, unlike BARYCENTRIC. If ADAP_BARY_AREA is used,"
             " exactly one of area_surfs or area_metrics must be specified")
    out_file = File(
        name_source=["new_sphere"],
        name_template="%s.out",
        keep_extension=True,
        argstr="%s",
        position=4,
        desc="The output metric")
    area_surfs = traits.Bool(
        position=5,
        argstr="-area-surfs",
        xor=["area_metrics"],
        desc="Specify surfaces to do vertex area correction based on")
    area_metrics = traits.Bool(
        position=5,
        argstr="-area-metrics",
        xor=["area_surfs"],
        desc="Specify vertex area metrics to do area correction based on")
    current_area = File(
        exists=True,
        position=6,
        argstr="%s",
        desc="A relevant anatomical surface with <current-sphere> mesh OR"
             " a metric file with vertex areas for <current-sphere> mesh")
    new_area = File(
        exists=True,
        position=7,
        argstr="%s",
        desc="A relevant anatomical surface with <current-sphere> mesh OR"
             " a metric file with vertex areas for <current-sphere> mesh")
    roi_metric = File(
        exists=True,
        position=8,
        argstr="-current-roi %s",
        desc="Input roi on the current mesh used to exclude non-data vertices")
    valid_roi_out = traits.Bool(
        position=9,
        argstr="-valid-roi-out",
        desc="Output the ROI of vertices that got data from valid source vertices")
    largest = traits.Bool(
        position=10,
        argstr="-largest",
        desc="Use only the value of the vertex with the largest weight")


class MetricResampleOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output metric")
    roi_file = File(desc="ROI of vertices that got data from valid source vertices")


class MetricResample(WBCommand):
    """
    Resample a metric file to a different mesh

    Resamples a metric file, given two spherical surfaces that are in
    register.  If ``ADAP_BARY_AREA`` is used, exactly one of -area-surfs or
    ``-area-metrics`` must be specified.

    The ``ADAP_BARY_AREA`` method is recommended for ordinary metric data,
    because it should use all data while downsampling, unlike ``BARYCENTRIC``.
    The recommended areas option for most data is individual midthicknesses
    for individual data, and averaged vertex area metrics from individual
    midthicknesses for group average data.

    The ``-current-roi`` option only masks the input, the output may be slightly
    dilated in comparison, consider using ``-metric-mask`` on the output when
    using ``-current-roi``.

    The ``-largest option`` results in nearest vertex behavior when used with
    ``BARYCENTRIC``.  When resampling a binary metric, consider thresholding at
    0.5 after resampling rather than using ``-largest``.

    >>> from nipype.interfaces.workbench import MetricResample
    >>> metres = MetricResample()
    >>> metres.inputs.in_file = 'sub-01_task-rest_bold_space-fsaverage5.L.func.gii'
    >>> metres.inputs.method = 'ADAP_BARY_AREA'
    >>> metres.inputs.current_sphere = 'fsaverage5_std_sphere.L.10k_fsavg_L.surf.gii'
    >>> metres.inputs.new_sphere = 'fs_LR-deformed_to-fsaverage.L.sphere.32k_fs_LR.surf.gii'
    >>> metres.inputs.area_metrics = True
    >>> metres.inputs.current_area = 'fsaverage5.L.midthickness_va_avg.10k_fsavg_L.shape.gii'
    >>> metres.inputs.new_area = 'fs_LR.L.midthickness_va_avg.32k_fs_LR.shape.gii'
    >>> metres.cmdline
    'wb_command -metric-resample sub-01_task-rest_bold_space-fsaverage5.L.func.gii \
    fsaverage5_std_sphere.L.10k_fsavg_L.surf.gii \
    fs_LR-deformed_to-fsaverage.L.sphere.32k_fs_LR.surf.gii \
    ADAP_BARY_AREA fs_LR-deformed_to-fsaverage.L.sphere.32k_fs_LR.surf.out \
    -area-metrics fsaverage5.L.midthickness_va_avg.10k_fsavg_L.shape.gii \
    fs_LR.L.midthickness_va_avg.32k_fs_LR.shape.gii'
    """
    input_spec = MetricResampleInputSpec
    output_spec = MetricResampleOutputSpec
    _cmd = 'wb_command -metric-resample'

    def _format_arg(self, opt, spec, val):
        if opt in ['current_area', 'new_area']:
            if not self.inputs.area_surfs and not self.inputs.area_metrics:
                raise ValueError("{} was set but neither area_surfs or"
                                 " area_metrics were set".format(opt))
        if opt == "method":
            if (val == "ADAP_BARY_AREA" and
                    not self.inputs.area_surfs and
                    not self.inputs.area_metrics):
                raise ValueError("Exactly one of area_surfs or area_metrics"
                                 " must be specified")
        if opt == "valid_roi_out" and val:
            # generate a filename and add it to argstr
            roi_out = self._gen_filename(self.inputs.in_file, suffix='_roi')
            iflogger.info("Setting roi output file as", roi_out)
            spec.argstr += " " + roi_out
        return super(MetricResample, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = super(MetricResample, self)._list_outputs()
        if self.inputs.valid_roi_out:
            roi_file = self._gen_filename(self.inputs.in_file, suffix='_roi')
            outputs['roi_file'] = os.path.abspath(roi_file)
        return outputs
