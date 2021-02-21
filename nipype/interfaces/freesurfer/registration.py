# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provides interfaces to various longitudinal commands provided by freesurfer
"""

import os
import os.path

from ... import logging
from ...utils.filemanip import split_filename, copyfile

from .base import (
    FSCommand,
    FSTraitedSpec,
    FSScriptCommand,
    FSScriptOutputSpec,
    FSCommandOpenMP,
    FSTraitedSpecOpenMP,
)
from ..base import isdefined, TraitedSpec, File, traits, Directory

__docformat__ = "restructuredtext"
iflogger = logging.getLogger("nipype.interface")


class MPRtoMNI305InputSpec(FSTraitedSpec):
    # environment variables, required
    # usedefault=True is hack for on_trait_change in __init__
    reference_dir = Directory(
        "", exists=True, mandatory=True, usedefault=True, desc="TODO"
    )
    target = traits.String("", mandatory=True, usedefault=True, desc="input atlas file")
    # required
    in_file = File(
        argstr="%s", usedefault=True, desc="the input file prefix for MPRtoMNI305"
    )


class MPRtoMNI305OutputSpec(FSScriptOutputSpec):
    out_file = File(
        exists=False, desc="The output file '<in_file>_to_<target>_t4_vox2vox.txt'"
    )


class MPRtoMNI305(FSScriptCommand):
    """
    For complete details, see FreeSurfer documentation

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import MPRtoMNI305, Info
    >>> mprtomni305 = MPRtoMNI305()
    >>> mprtomni305.inputs.target = 'structural.nii'
    >>> mprtomni305.inputs.reference_dir = '.' # doctest: +SKIP
    >>> mprtomni305.cmdline # doctest: +SKIP
    'mpr2mni305 output'
    >>> mprtomni305.inputs.out_file = 'struct_out' # doctest: +SKIP
    >>> mprtomni305.cmdline # doctest: +SKIP
    'mpr2mni305 struct_out' # doctest: +SKIP
    >>> mprtomni305.inputs.environ['REFDIR'] == os.path.join(Info.home(), 'average') # doctest: +SKIP
    True
    >>> mprtomni305.inputs.environ['MPR2MNI305_TARGET'] # doctest: +SKIP
    'structural'
    >>> mprtomni305.run() # doctest: +SKIP

    """

    _cmd = "mpr2mni305"
    input_spec = MPRtoMNI305InputSpec
    output_spec = MPRtoMNI305OutputSpec

    def __init__(self, **inputs):
        super(MPRtoMNI305, self).__init__(**inputs)
        self.inputs.on_trait_change(self._environ_update, "target")
        self.inputs.on_trait_change(self._environ_update, "reference_dir")

    def _format_arg(self, opt, spec, val):
        if opt in ["target", "reference_dir"]:
            return ""
        elif opt == "in_file":
            _, retval, ext = split_filename(val)
            # Need to copy file to working cache directory!
            copyfile(
                val, os.path.abspath(retval + ext), copy=True, hashmethod="content"
            )
            return retval
        return super(MPRtoMNI305, self)._format_arg(opt, spec, val)

    def _environ_update(self):
        # refdir = os.path.join(Info.home(), val)
        refdir = self.inputs.reference_dir
        target = self.inputs.target
        self.inputs.environ["MPR2MNI305_TARGET"] = target
        self.inputs.environ["REFDIR"] = refdir

    def _get_fname(self, fname):
        return split_filename(fname)[1]

    def _list_outputs(self):
        outputs = super(MPRtoMNI305, self)._list_outputs()
        fullname = "_".join(
            [
                self._get_fname(self.inputs.in_file),
                "to",
                self.inputs.target,
                "t4",
                "vox2vox.txt",
            ]
        )
        outputs["out_file"] = os.path.abspath(fullname)
        return outputs


class RegisterAVItoTalairachInputSpec(FSTraitedSpec):
    in_file = File(
        argstr="%s", exists=True, mandatory=True, position=0, desc="The input file"
    )
    target = File(
        argstr="%s", exists=True, mandatory=True, position=1, desc="The target file"
    )
    vox2vox = File(
        argstr="%s", exists=True, mandatory=True, position=2, desc="The vox2vox file"
    )
    out_file = File(
        "talairach.auto.xfm",
        usedefault=True,
        argstr="%s",
        position=3,
        desc="The transform output",
    )


class RegisterAVItoTalairachOutputSpec(FSScriptOutputSpec):
    out_file = File(exists=False, desc="The output file for RegisterAVItoTalairach")


class RegisterAVItoTalairach(FSScriptCommand):
    """
    converts the vox2vox from talairach_avi to a talairach.xfm file

    This is a script that converts the vox2vox from talairach_avi to a
    talairach.xfm file. It is meant to replace the following cmd line:

    tkregister2_cmdl \
        --mov $InVol \
        --targ $FREESURFER_HOME/average/mni305.cor.mgz \
        --xfmout ${XFM} \
        --vox2vox talsrcimg_to_${target}_t4_vox2vox.txt \
        --noedit \
        --reg talsrcimg.reg.tmp.dat
    set targ = $FREESURFER_HOME/average/mni305.cor.mgz
    set subject = mgh-02407836-v2
    set InVol = $SUBJECTS_DIR/$subject/mri/orig.mgz
    set vox2vox = $SUBJECTS_DIR/$subject/mri/transforms/talsrcimg_to_711-2C_as_mni_average_305_t4_vox2vox.txt

    Examples
    ========

    >>> from nipype.interfaces.freesurfer import RegisterAVItoTalairach
    >>> register = RegisterAVItoTalairach()
    >>> register.inputs.in_file = 'structural.mgz'                         # doctest: +SKIP
    >>> register.inputs.target = 'mni305.cor.mgz'                          # doctest: +SKIP
    >>> register.inputs.vox2vox = 'talsrcimg_to_structural_t4_vox2vox.txt' # doctest: +SKIP
    >>> register.cmdline                                                   # doctest: +SKIP
    'avi2talxfm structural.mgz mni305.cor.mgz talsrcimg_to_structural_t4_vox2vox.txt talairach.auto.xfm'

    >>> register.run() # doctest: +SKIP
    """

    _cmd = "avi2talxfm"
    input_spec = RegisterAVItoTalairachInputSpec
    output_spec = RegisterAVItoTalairachOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


class EMRegisterInputSpec(FSTraitedSpecOpenMP):
    # required
    in_file = File(
        argstr="%s", exists=True, mandatory=True, position=-3, desc="in brain volume"
    )
    template = File(
        argstr="%s", exists=True, mandatory=True, position=-2, desc="template gca"
    )
    out_file = File(
        argstr="%s",
        exists=False,
        name_source=["in_file"],
        name_template="%s_transform.lta",
        hash_files=False,
        keep_extension=False,
        position=-1,
        desc="output transform",
    )
    # optional
    skull = traits.Bool(argstr="-skull", desc="align to atlas containing skull (uns=5)")
    mask = File(argstr="-mask %s", exists=True, desc="use volume as a mask")
    nbrspacing = traits.Int(
        argstr="-uns %d",
        desc="align to atlas containing skull setting unknown_nbr_spacing = nbrspacing",
    )
    transform = File(argstr="-t %s", exists=True, desc="Previously computed transform")


class EMRegisterOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="output transform")


class EMRegister(FSCommandOpenMP):
    """ This program creates a tranform in lta format

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import EMRegister
    >>> register = EMRegister()
    >>> register.inputs.in_file = 'norm.mgz'
    >>> register.inputs.template = 'aseg.mgz'
    >>> register.inputs.out_file = 'norm_transform.lta'
    >>> register.inputs.skull = True
    >>> register.inputs.nbrspacing = 9
    >>> register.cmdline
    'mri_em_register -uns 9 -skull norm.mgz aseg.mgz norm_transform.lta'
    """

    _cmd = "mri_em_register"
    input_spec = EMRegisterInputSpec
    output_spec = EMRegisterOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


class RegisterInputSpec(FSTraitedSpec):
    # required
    in_surf = File(
        argstr="%s",
        exists=True,
        mandatory=True,
        position=-3,
        copyfile=True,
        desc="Surface to register, often {hemi}.sphere",
    )
    target = File(
        argstr="%s",
        exists=True,
        mandatory=True,
        position=-2,
        desc="The data to register to. In normal recon-all usage, "
        + "this is a template file for average surface.",
    )
    in_sulc = File(
        exists=True,
        mandatory=True,
        copyfile=True,
        desc="Undocumented mandatory input file ${SUBJECTS_DIR}/surf/{hemisphere}.sulc ",
    )
    out_file = File(
        argstr="%s",
        exists=False,
        position=-1,
        genfile=True,
        desc="Output surface file to capture registration",
    )
    # optional
    curv = traits.Bool(
        argstr="-curv",
        requires=["in_smoothwm"],
        desc="Use smoothwm curvature for final alignment",
    )
    in_smoothwm = File(
        exists=True,
        copyfile=True,
        desc="Undocumented input file ${SUBJECTS_DIR}/surf/{hemisphere}.smoothwm ",
    )


class RegisterOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Output surface file to capture registration")


class Register(FSCommand):
    """ This program registers a surface to an average surface template.

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import Register
    >>> register = Register()
    >>> register.inputs.in_surf = 'lh.pial'
    >>> register.inputs.in_smoothwm = 'lh.pial'
    >>> register.inputs.in_sulc = 'lh.pial'
    >>> register.inputs.target = 'aseg.mgz'
    >>> register.inputs.out_file = 'lh.pial.reg'
    >>> register.inputs.curv = True
    >>> register.cmdline
    'mris_register -curv lh.pial aseg.mgz lh.pial.reg'
    """

    _cmd = "mris_register"
    input_spec = RegisterInputSpec
    output_spec = RegisterOutputSpec

    def _format_arg(self, opt, spec, val):
        if opt == "curv":
            return spec.argstr
        return super(Register, self)._format_arg(opt, spec, val)

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()[name]
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_file):
            outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        else:
            outputs["out_file"] = os.path.abspath(self.inputs.in_surf) + ".reg"
        return outputs


class PaintInputSpec(FSTraitedSpec):
    # required
    in_surf = File(
        argstr="%s",
        exists=True,
        mandatory=True,
        position=-2,
        desc="Surface file with grid (vertices) onto which the "
        + "template data is to be sampled or 'painted'",
    )
    template = File(
        argstr="%s", exists=True, mandatory=True, position=-3, desc="Template file"
    )
    # optional
    template_param = traits.Int(desc="Frame number of the input template")
    averages = traits.Int(argstr="-a %d", desc="Average curvature patterns")
    out_file = File(
        argstr="%s",
        exists=False,
        position=-1,
        name_template="%s.avg_curv",
        hash_files=False,
        name_source=["in_surf"],
        keep_extension=False,
        desc="File containing a surface-worth of per-vertex values, "
        + "saved in 'curvature' format.",
    )


class PaintOutputSpec(TraitedSpec):
    out_file = File(
        exists=False,
        desc="File containing a surface-worth of per-vertex values, saved in 'curvature' format.",
    )


class Paint(FSCommand):
    """
    This program is useful for extracting one of the arrays ("a variable")
    from a surface-registration template file. The output is a file
    containing a surface-worth of per-vertex values, saved in "curvature"
    format. Because the template data is sampled to a particular surface
    mesh, this conjures the idea of "painting to a surface".

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import Paint
    >>> paint = Paint()
    >>> paint.inputs.in_surf = 'lh.pial'
    >>> paint.inputs.template = 'aseg.mgz'
    >>> paint.inputs.averages = 5
    >>> paint.inputs.out_file = 'lh.avg_curv'
    >>> paint.cmdline
    'mrisp_paint -a 5 aseg.mgz lh.pial lh.avg_curv'
    """

    _cmd = "mrisp_paint"
    input_spec = PaintInputSpec
    output_spec = PaintOutputSpec

    def _format_arg(self, opt, spec, val):
        if opt == "template":
            if isdefined(self.inputs.template_param):
                return spec.argstr % (val + "#" + str(self.inputs.template_param))
        return super(Paint, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


class MRICoregInputSpec(FSTraitedSpec):
    source_file = File(
        argstr="--mov %s",
        desc="source file to be registered",
        mandatory=True,
        copyfile=False,
    )
    reference_file = File(
        argstr="--ref %s",
        desc="reference (target) file",
        mandatory=True,
        copyfile=False,
        xor=["subject_id"],
    )
    out_lta_file = traits.Either(
        True,
        File,
        argstr="--lta %s",
        default=True,
        usedefault=True,
        desc="output registration file (LTA format)",
    )
    out_reg_file = traits.Either(
        True, File, argstr="--regdat %s", desc="output registration file (REG format)"
    )
    out_params_file = traits.Either(
        True, File, argstr="--params %s", desc="output parameters file"
    )

    subjects_dir = Directory(
        exists=True, argstr="--sd %s", desc="FreeSurfer SUBJECTS_DIR"
    )
    subject_id = traits.Str(
        argstr="--s %s",
        position=1,
        mandatory=True,
        xor=["reference_file"],
        requires=["subjects_dir"],
        desc="freesurfer subject ID (implies ``reference_mask == "
        "aparc+aseg.mgz`` unless otherwise specified)",
    )
    dof = traits.Enum(
        6, 9, 12, argstr="--dof %d", desc="number of transform degrees of freedom"
    )
    reference_mask = traits.Either(
        False,
        traits.Str,
        argstr="--ref-mask %s",
        position=2,
        desc="mask reference volume with given mask, or None if ``False``",
    )
    source_mask = traits.Str(
        argstr="--mov-mask", desc="mask source file with given mask"
    )
    num_threads = traits.Int(argstr="--threads %d", desc="number of OpenMP threads")
    no_coord_dithering = traits.Bool(
        argstr="--no-coord-dither", desc="turn off coordinate dithering"
    )
    no_intensity_dithering = traits.Bool(
        argstr="--no-intensity-dither", desc="turn off intensity dithering"
    )
    sep = traits.List(
        argstr="--sep %s...",
        minlen=1,
        maxlen=2,
        desc="set spatial scales, in voxels (default [2, 4])",
    )
    initial_translation = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr="--trans %g %g %g",
        desc="initial translation in mm (implies no_cras0)",
    )
    initial_rotation = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr="--rot %g %g %g",
        desc="initial rotation in degrees",
    )
    initial_scale = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr="--scale %g %g %g",
        desc="initial scale",
    )
    initial_shear = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr="--shear %g %g %g",
        desc="initial shear (Hxy, Hxz, Hyz)",
    )
    no_cras0 = traits.Bool(
        argstr="--no-cras0",
        desc="do not set translation parameters to align "
        "centers of source and reference files",
    )
    max_iters = traits.Range(
        low=1, argstr="--nitersmax %d", desc="maximum iterations (default: 4)"
    )
    ftol = traits.Float(
        argstr="--ftol %e", desc="floating-point tolerance (default=1e-7)"
    )
    linmintol = traits.Float(argstr="--linmintol %e")
    saturation_threshold = traits.Range(
        low=0.0,
        high=100.0,
        argstr="--sat %g",
        desc="saturation threshold (default=9.999)",
    )
    conform_reference = traits.Bool(
        argstr="--conf-ref", desc="conform reference without rescaling"
    )
    no_brute_force = traits.Bool(argstr="--no-bf", desc="do not brute force search")
    brute_force_limit = traits.Float(
        argstr="--bf-lim %g",
        xor=["no_brute_force"],
        desc="constrain brute force search to +/- lim",
    )
    brute_force_samples = traits.Int(
        argstr="--bf-nsamp %d",
        xor=["no_brute_force"],
        desc="number of samples in brute force search",
    )
    no_smooth = traits.Bool(
        argstr="--no-smooth",
        desc="do not apply smoothing to either reference or source file",
    )
    ref_fwhm = traits.Float(
        argstr="--ref-fwhm", desc="apply smoothing to reference file"
    )
    source_oob = traits.Bool(
        argstr="--mov-oob", desc="count source voxels that are out-of-bounds as 0"
    )
    # Skipping mat2par


class MRICoregOutputSpec(TraitedSpec):
    out_reg_file = File(exists=True, desc="output registration file")
    out_lta_file = File(exists=True, desc="output LTA-style registration file")
    out_params_file = File(exists=True, desc="output parameters file")


class MRICoreg(FSCommand):
    """ This program registers one volume to another

    mri_coreg is a C reimplementation of spm_coreg in FreeSurfer

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import MRICoreg
    >>> coreg = MRICoreg()
    >>> coreg.inputs.source_file = 'moving1.nii'
    >>> coreg.inputs.reference_file = 'fixed1.nii'
    >>> coreg.inputs.subjects_dir = '.'
    >>> coreg.cmdline # doctest: +ELLIPSIS
    'mri_coreg --lta .../registration.lta --ref fixed1.nii --mov moving1.nii --sd .'

    If passing a subject ID, the reference mask may be disabled:

    >>> coreg = MRICoreg()
    >>> coreg.inputs.source_file = 'moving1.nii'
    >>> coreg.inputs.subjects_dir = '.'
    >>> coreg.inputs.subject_id = 'fsaverage'
    >>> coreg.inputs.reference_mask = False
    >>> coreg.cmdline # doctest: +ELLIPSIS
    'mri_coreg --s fsaverage --no-ref-mask --lta .../registration.lta --mov moving1.nii --sd .'

    Spatial scales may be specified as a list of one or two separations:

    >>> coreg.inputs.sep = [4]
    >>> coreg.cmdline # doctest: +ELLIPSIS
    'mri_coreg --s fsaverage --no-ref-mask --lta .../registration.lta --sep 4 --mov moving1.nii --sd .'

    >>> coreg.inputs.sep = [4, 5]
    >>> coreg.cmdline # doctest: +ELLIPSIS
    'mri_coreg --s fsaverage --no-ref-mask --lta .../registration.lta --sep 4 --sep 5 --mov moving1.nii --sd .'
    """

    _cmd = "mri_coreg"
    input_spec = MRICoregInputSpec
    output_spec = MRICoregOutputSpec

    def _format_arg(self, opt, spec, val):
        if opt in ("out_reg_file", "out_lta_file", "out_params_file") and val is True:
            val = self._list_outputs()[opt]
        elif opt == "reference_mask" and val is False:
            return "--no-ref-mask"
        return super(MRICoreg, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self.output_spec().get()

        out_lta_file = self.inputs.out_lta_file
        if isdefined(out_lta_file):
            if out_lta_file is True:
                out_lta_file = "registration.lta"
            outputs["out_lta_file"] = os.path.abspath(out_lta_file)

        out_reg_file = self.inputs.out_reg_file
        if isdefined(out_reg_file):
            if out_reg_file is True:
                out_reg_file = "registration.dat"
            outputs["out_reg_file"] = os.path.abspath(out_reg_file)

        out_params_file = self.inputs.out_params_file
        if isdefined(out_params_file):
            if out_params_file is True:
                out_params_file = "registration.par"
            outputs["out_params_file"] = os.path.abspath(out_params_file)

        return outputs
