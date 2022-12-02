# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provides interfaces to various longitudinal commands provided by freesurfer
"""

import os

from ... import logging
from ..base import TraitedSpec, File, traits, InputMultiPath, OutputMultiPath, isdefined, InputMultiObject, Directory
from .base import FSCommand, FSTraitedSpec, FSCommandOpenMP, FSTraitedSpecOpenMP, CommandLine
from .preprocess import ReconAllInputSpec
from ..io import FreeSurferSource

__docformat__ = "restructuredtext"
iflogger = logging.getLogger("nipype.interface")


class RobustTemplateInputSpec(FSTraitedSpecOpenMP):
    # required
    in_files = InputMultiPath(
        File(exists=True),
        mandatory=True,
        argstr="--mov %s",
        desc="input movable volumes to be aligned to common mean/median " "template",
    )
    out_file = File(
        "mri_robust_template_out.mgz",
        mandatory=True,
        usedefault=True,
        argstr="--template %s",
        desc="output template volume (final mean/median image)",
    )
    auto_detect_sensitivity = traits.Bool(
        argstr="--satit",
        xor=["outlier_sensitivity"],
        mandatory=True,
        desc="auto-detect good sensitivity (recommended for head or full "
        "brain scans)",
    )
    outlier_sensitivity = traits.Float(
        argstr="--sat %.4f",
        xor=["auto_detect_sensitivity"],
        mandatory=True,
        desc='set outlier sensitivity manually (e.g. "--sat 4.685" ). Higher '
        "values mean less sensitivity.",
    )
    # optional
    transform_outputs = traits.Either(
        InputMultiPath(File(exists=False)),
        traits.Bool,
        argstr="--lta %s",
        desc="output xforms to template (for each input)",
    )
    intensity_scaling = traits.Bool(
        default_value=False,
        argstr="--iscale",
        desc="allow also intensity scaling (default off)",
    )
    scaled_intensity_outputs = traits.Either(
        InputMultiPath(File(exists=False)),
        traits.Bool,
        argstr="--iscaleout %s",
        desc="final intensity scales (will activate --iscale)",
    )
    subsample_threshold = traits.Int(
        argstr="--subsample %d",
        desc="subsample if dim > # on all axes (default no subs.)",
    )
    average_metric = traits.Enum(
        "median",
        "mean",
        argstr="--average %d",
        desc="construct template from: 0 Mean, 1 Median (default)",
    )
    initial_timepoint = traits.Int(
        argstr="--inittp %d",
        desc="use TP# for spacial init (default random), 0: no init",
    )
    fixed_timepoint = traits.Bool(
        default_value=False,
        argstr="--fixtp",
        desc="map everything to init TP# (init TP is not resampled)",
    )
    no_iteration = traits.Bool(
        default_value=False,
        argstr="--noit",
        desc="do not iterate, just create first template",
    )
    initial_transforms = InputMultiPath(
        File(exists=True),
        argstr="--ixforms %s",
        desc="use initial transforms (lta) on source",
    )
    in_intensity_scales = InputMultiPath(
        File(exists=True), argstr="--iscalein %s", desc="use initial intensity scales"
    )


class RobustTemplateOutputSpec(TraitedSpec):
    out_file = File(
        exists=True, desc="output template volume (final mean/median image)"
    )
    transform_outputs = OutputMultiPath(
        File(exists=True), desc="output xform files from moving to template"
    )
    scaled_intensity_outputs = OutputMultiPath(
        File(exists=True), desc="output final intensity scales"
    )


class RobustTemplate(FSCommandOpenMP):
    """construct an unbiased robust template for longitudinal volumes

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import RobustTemplate
    >>> template = RobustTemplate()
    >>> template.inputs.in_files = ['structural.nii', 'functional.nii']
    >>> template.inputs.auto_detect_sensitivity = True
    >>> template.inputs.average_metric = 'mean'
    >>> template.inputs.initial_timepoint = 1
    >>> template.inputs.fixed_timepoint = True
    >>> template.inputs.no_iteration = True
    >>> template.inputs.subsample_threshold = 200
    >>> template.cmdline  #doctest:
    'mri_robust_template --satit --average 0 --fixtp --mov structural.nii functional.nii --inittp 1 --noit --template mri_robust_template_out.mgz --subsample 200'
    >>> template.inputs.out_file = 'T1.nii'
    >>> template.cmdline  #doctest:
    'mri_robust_template --satit --average 0 --fixtp --mov structural.nii functional.nii --inittp 1 --noit --template T1.nii --subsample 200'

    >>> template.inputs.transform_outputs = ['structural.lta',
    ...                                      'functional.lta']
    >>> template.inputs.scaled_intensity_outputs = ['structural-iscale.txt',
    ...                                             'functional-iscale.txt']
    >>> template.cmdline    #doctest: +ELLIPSIS
    'mri_robust_template --satit --average 0 --fixtp --mov structural.nii functional.nii --inittp 1 --noit --template T1.nii --iscaleout .../structural-iscale.txt .../functional-iscale.txt --subsample 200 --lta .../structural.lta .../functional.lta'

    >>> template.inputs.transform_outputs = True
    >>> template.inputs.scaled_intensity_outputs = True
    >>> template.cmdline    #doctest: +ELLIPSIS
    'mri_robust_template --satit --average 0 --fixtp --mov structural.nii functional.nii --inittp 1 --noit --template T1.nii --iscaleout .../is1.txt .../is2.txt --subsample 200 --lta .../tp1.lta .../tp2.lta'

    >>> template.run()  #doctest: +SKIP

    References
    ----------
    [https://surfer.nmr.mgh.harvard.edu/fswiki/mri_robust_template]

    """

    _cmd = "mri_robust_template"
    input_spec = RobustTemplateInputSpec
    output_spec = RobustTemplateOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "average_metric":
            # return enumeration value
            return spec.argstr % {"mean": 0, "median": 1}[value]
        if name in ("transform_outputs", "scaled_intensity_outputs"):
            value = self._list_outputs()[name]
        return super(RobustTemplate, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        n_files = len(self.inputs.in_files)
        fmt = "{}{:02d}.{}" if n_files > 9 else "{}{:d}.{}"
        if isdefined(self.inputs.transform_outputs):
            fnames = self.inputs.transform_outputs
            if fnames is True:
                fnames = [fmt.format("tp", i + 1, "lta") for i in range(n_files)]
            outputs["transform_outputs"] = [os.path.abspath(x) for x in fnames]
        if isdefined(self.inputs.scaled_intensity_outputs):
            fnames = self.inputs.scaled_intensity_outputs
            if fnames is True:
                fnames = [fmt.format("is", i + 1, "txt") for i in range(n_files)]
            outputs["scaled_intensity_outputs"] = [os.path.abspath(x) for x in fnames]
        return outputs


class FuseSegmentationsInputSpec(FSTraitedSpec):
    # required
    subject_id = traits.String(
        argstr="%s", position=-3, desc="subject_id being processed"
    )
    timepoints = InputMultiPath(
        traits.String(),
        mandatory=True,
        argstr="%s",
        position=-2,
        desc="subject_ids or timepoints to be processed",
    )
    out_file = File(
        exists=False, mandatory=True, position=-1, desc="output fused segmentation file"
    )
    in_segmentations = InputMultiPath(
        File(exists=True),
        argstr="-a %s",
        mandatory=True,
        desc="name of aseg file to use (default: aseg.mgz) \
        must include the aseg files for all the given timepoints",
    )
    in_segmentations_noCC = InputMultiPath(
        File(exists=True),
        argstr="-c %s",
        mandatory=True,
        desc="name of aseg file w/o CC labels (default: aseg.auto_noCCseg.mgz) \
        must include the corresponding file for all the given timepoints",
    )
    in_norms = InputMultiPath(
        File(exists=True),
        argstr="-n %s",
        mandatory=True,
        desc="-n <filename>  - name of norm file to use (default: norm.mgs) \
        must include the corresponding norm file for all given timepoints \
        as well as for the current subject",
    )


class FuseSegmentationsOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="output fused segmentation file")


class FuseSegmentations(FSCommand):
    """fuse segmentations together from multiple timepoints

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import FuseSegmentations
    >>> fuse = FuseSegmentations()
    >>> fuse.inputs.subject_id = 'tp.long.A.template'
    >>> fuse.inputs.timepoints = ['tp1', 'tp2']
    >>> fuse.inputs.out_file = 'aseg.fused.mgz'
    >>> fuse.inputs.in_segmentations = ['aseg.mgz', 'aseg.mgz']
    >>> fuse.inputs.in_segmentations_noCC = ['aseg.mgz', 'aseg.mgz']
    >>> fuse.inputs.in_norms = ['norm.mgz', 'norm.mgz', 'norm.mgz']
    >>> fuse.cmdline
    'mri_fuse_segmentations -n norm.mgz -a aseg.mgz -c aseg.mgz tp.long.A.template tp1 tp2'
    """

    _cmd = "mri_fuse_segmentations"
    input_spec = FuseSegmentationsInputSpec
    output_spec = FuseSegmentationsOutputSpec

    def _format_arg(self, name, spec, value):
        if name in ("in_segmentations", "in_segmentations_noCC", "in_norms"):
            # return enumeration value
            return spec.argstr % os.path.basename(value[0])
        return super(FuseSegmentations, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


class BaseReconAllInputSpec(ReconAllInputSpec):
    subject_id = traits.Str(argstr="-subjid %s", desc="subject name")
    base_id = traits.Str(argstr="-base %s", desc="base template name", xor=["subject_id"])
    timepoints = InputMultiObject(
        traits.Str(), argstr="-tp %s...", desc="processed time point to use in template"
    )

class BaseReconAllOutputSpec(FreeSurferSource.output_spec):
    subjects_dir = Directory(exists=True, desc="FreeSurfer subjects directory")
    subject_id = traits.Str(desc="Subject template name")

class BaseReconAll(CommandLine):
    """Uses the longitudinal pipeline of recon-all to create a template for a given number of subject's sessions.

    Examples
    --------
    >>> from nipype.interfaces.freesurfer.longitudinal import BaseReconAll
    >>> baserecon = BaseReconAll()
    >>> baserecon.inputs.base_id = 'sub-template'
    >>> baserecon.inputs.timepoints = ['ses-1','ses-2']
    >>> baserecon.inputs.directive = 'all'
    >>> baserecon.inputs.subjects_dir = '.'
    >>> baserecon.cmdline
    'recon-all -all -base sub-template -sd . -tp ses-1 -tp ses-2'
    """

    _cmd = "recon-all"
    input_spec = BaseReconAllInputSpec
    output_spec = BaseReconAllOutputSpec
    _can_resume = True
    force_run = False

    def _gen_subjects_dir(self):
        return os.getcwd()


    def _gen_filename(self, name):
        if name == "subjects_dir":
            return self._gen_subjects_dir()
        return None


    def _list_outputs(self):
        if isdefined(self.inputs.subjects_dir):
            subjects_dir = self.inputs.subjects_dir
        else:
            subjects_dir = self._gen_subjects_dir()

        if isdefined(self.inputs.hemi):
            hemi = self.inputs.hemi
        else:
            hemi = "both"

        outputs = self._outputs().get()

        outputs.update(
            FreeSurferSource(subject_id=self.inputs.base_id,
                subjects_dir=subjects_dir, hemi=hemi)._list_outputs()
        )
        outputs["subject_id"] = self.inputs.base_id
        outputs["subjects_dir"] = subjects_dir
        return outputs


    def _is_resuming(self):
        subjects_dir = self.inputs.subjects_dir
        if not isdefined(subjects_dir):
            subjects_dir = self._gen_subjects_dir()
        if os.path.isdir(os.path.join(subjects_dir, self.inputs.base_id, "mri")):
            return True
        return False


    def _format_arg(self, name, trait_spec, value):
        return super(BaseReconAll, self)._format_arg(name, trait_spec, value)


    @property
    def cmdline(self):
        cmd = super(BaseReconAll, self).cmdline

        if not self._is_resuming():
            return cmd

        subjects_dir = self.inputs.subjects_dir
        if not isdefined(subjects_dir):
            subjects_dir = self._gen_subjects_dir()

        directive = self.inputs.directive
        if not isdefined(directive):
            steps = []

        iflogger.info(f"recon-all: {cmd}")
        return cmd


class LongReconAllInputSpec(ReconAllInputSpec):
    subject_id = traits.Str(argstr="-subjid %s", desc="subject name")
    long_id = traits.Str(
        argstr="-long %s",
        desc="longitudinal session/timepoint id",
        xor=["subject_id"],
        requires=["base_id"],
        position=1
    )
    base_id = traits.Str(
        argstr="%s",
        desc="longitudinal base template id",
        requires=["long_id"],
        position=2
    )


class LongReconAllOutputSpec(FreeSurferSource.output_spec):
    subjects_dir = Directory(exists=True, desc="FreeSurfer subjects directory")
    subject_id = traits.Str(desc="Subject template name")


class LongReconAll(CommandLine):
    """Uses FreeSurfer's longitudinal recon-all to process a subject given
    the previously processed base template.

    Examples
    ---------

    >>> from nipype.interfaces.freesurfer.longitudinal import LongReconAll
    >>> longrecon = LongReconAll()
    >>> longrecon.inputs.long_id = "ses-1"
    >>> longrecon.inputs.base_id = "sub-template"
    >>> longrecon.inputs.directive = "all"
    >>> longrecon.inputs.subjects_dir = "."
    >>> longrecon.cmdline
    'recon-all -all -long ses-1 sub-template -sd .'
    """

    _cmd = "recon-all"
    input_spec = LongReconAllInputSpec
    output_spec = LongReconAllOutputSpec
    _can_resume = True
    force_run = False

    def _gen_subjects_dir(self):
        return os.getcwd()

    def _gen_filename(self, name):
        if name == "subjects_dir":
            return self._gen_subjects_dir()
        return None

    def _list_outputs(self):
        subject_id = f"{self.inputs.long_id[0]}.long.{self.inputs.long_id[1]}"

        if isdefined(self.inputs.subjects_dir):
            subjects_dir = self.inputs.subjects_dir
        else:
            subjects_dir = self._gen_subjects_dir()

        if isdefined(self.inputs.hemi):
            hemi = self.inputs.hemi
        else:
            hemi = "both"

        outputs = self._outputs().get()

        outputs.update(
            FreeSurferSource(
                subject_id=subject_id, subjects_dir=subjects_dir, hemi=hemi
            )._list_outputs()
        )
        outputs["subject_id"] = subject_id
        outputs["subjects_dir"] = subjects_dir
        return outputs

    def _is_resuming(self):
        subjects_dir = self.inputs.subjects_dir
        subject_id = f"{self.inputs.long_id[0]}.long{self.inputs.long_id[1]}"
        if not isdefined(subjects_dir):
            subjects_dir = self._gen_subjects_dir()
        if os.path.isdir(os.path.join(subjects_dir, subject_id, "mri")):
            return True
        return False

    def _format_arg(self, name, trait_spec, value):
        return super(LongReconAll, self)._format_arg(name, trait_spec, value)

    @property
    def cmdline(self):
        cmd = super(LongReconAll, self).cmdline

        if not self._is_resuming():
            return cmd

        subjects_dir = self.inputs.subjects_dir
        if not isdefined(subjects_dir):
            subjects_dir = self._gen_subjects_dir()

        directive = self.inputs.directive
        if not isdefined(directive):
            steps = []

        iflogger.info(f"recon-all: {cmd}")
        return cmd
