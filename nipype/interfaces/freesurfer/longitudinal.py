# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provides interfaces to various longitudinal commands provided by freesurfer

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)

"""
__docformat__ = 'restructuredtext'

import os
#import itertools

from nipype.utils.filemanip import fname_presuffix
from nipype.interfaces.freesurfer.base import FSCommand, FSTraitedSpec
from nipype.interfaces.base import (TraitedSpec, File, traits,
                                    InputMultiPath, OutputMultiPath, isdefined)

from ... import logging
iflogger = logging.getLogger('interface')


class RobustTemplateInputSpec(FSTraitedSpec):
    # required
    infiles = InputMultiPath(File(exists=True), mandatory=True, argstr='--mov %s',
                             desc='input movable volumes to be aligned to common mean/median template')
    template_output = File('mri_robust_template_out.mgz', mandatory=True, usedefault=True, argstr='--template %s',
                           desc='output template volume (final mean/median image)')
    auto_detect_sensitivity = traits.Bool(argstr='--satit', xor=['outlier_sensitivity'], mandatory=True,
                                          desc='auto-detect good sensitivity (recommended for head or full brain scans)')
    outlier_sensitivity = traits.Float(argstr='--sat %.4f', xor=['auto_detect_sensitivity'], mandatory=True,
                                       desc='set outlier sensitivity manually (e.g. "--sat 4.685" ). Higher values mean ' +\
                                       'less sensitivity.')
    # optional
    transform_outputs = InputMultiPath(File(exists=False),
                                       argstr='--lta %s', desc='output xforms to template (for each input)')
    intensity_scaling = traits.Bool(default_value=False, argstr='--iscale', desc='allow also intensity scaling (default off)')
    scaled_intensity_outputs = InputMultiPath(File(exists=False),
                                              argstr='--iscaleout %s',
                                              desc='final intensity scales (will activate --iscale)')
    subsample_threshold = traits.Int(argstr='--subsample %d', desc='subsample if dim > # on all axes (default no subs.)')
    average_metric = traits.Enum('median', 'mean', argstr='--average %d',
                                 desc='construct template from: 0 Mean, 1 Median (default)')
    initial_timepoint = traits.Int(argstr='--inittp %d', desc='use TP# for spacial init (default random), 0: no init')
    fixed_timepoint = traits.Bool(default_value=False, argstr='--fixtp',
                                  desc='map everthing to init TP# (init TP is not resampled)')
    no_iteration = traits.Bool(default_value=False, argstr='--noit', desc='do not iterate, just create first template')


class RobustTemplateOutputSpec(TraitedSpec):
    template_output = File(exists=True, desc='output template volume (final mean/median image)')
    transform_outputs = OutputMultiPath(File(exists=True), desc="output xform files from moving to template")
    scaled_intensity_outputs = OutputMultiPath(File(exists=True), desc="output final intensity scales")


class RobustTemplate(FSCommand):
    """ construct an unbiased robust template for longitudinal volumes

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import RobustTemplate
    >>> template = RobustTemplate()
    >>> template.inputs.infiles = ['structural.nii', 'functional.nii']
    >>> template.inputs.auto_detect_sensitivity = True
    >>> template.inputs.average_metric = 'mean'
    >>> template.inputs.initial_timepoint = 1
    >>> template.inputs.fixed_timepoint = True
    >>> template.inputs.no_iteration = True
    >>> template.inputs.subsample_threshold = 200
    >>> template.cmdline  #doctest: +NORMALIZE_WHITESPACE
    'mri_robust_template --satit --average 0 --fixtp --mov structural.nii functional.nii --inittp 1 --noit --subsample 200 --template mri_robust_template_out.mgz'
    >>> template.inputs.template_output = 'T1.nii'
    >>> template.cmdline  #doctest: +NORMALIZE_WHITESPACE
    'mri_robust_template --satit --average 0 --fixtp --mov structural.nii functional.nii --inittp 1 --noit --subsample 200 --template T1.nii'

    >>> template.inputs.transform_outputs = ['structural.lta', 'functional.lta']
    >>> template.inputs.scaled_intensity_outputs = ['structural-iscale.txt', 'functional-iscale.txt']
    >>> template.cmdline    #doctest: +NORMALIZE_WHITESPACE
    'mri_robust_template --satit --average 0 --fixtp --mov structural.nii functional.nii --inittp 1 --noit --iscaleout structural-iscale.txt functional-iscale.txt --subsample 200 --template T1.nii --lta structural.lta functional.lta'

    >>> template.run()  #doctest: +SKIP

    References
    ----------
    [https://surfer.nmr.mgh.harvard.edu/fswiki/mri_robust_template]

    """

    _cmd = 'mri_robust_template'
    input_spec = RobustTemplateInputSpec
    output_spec = RobustTemplateOutputSpec

    def _format_arg(self, name, spec, value):
        if name == 'average_metric':
            return spec.argstr % {"mean": 0, "median": 1}[value]  # return enumeration value
        return super(RobustTemplate, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['template_output'] = os.path.abspath(self.inputs.template_output)
        if isdefined(self.inputs.transform_outputs):
            outputs['transform_outputs'] = [os.path.abspath(x) for x in self.inputs.transform_outputs]
        if isdefined(self.inputs.scaled_intensity_outputs):
            outputs['scaled_intensity_outputs'] = [os.path.abspath(x) for x in self.inputs.scaled_intensity_outputs]
        return outputs
