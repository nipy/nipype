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
import os.path

from nipype.utils.filemanip import split_filename, copyfile

from nipype.interfaces.freesurfer.base import Info, FSCommand, FSTraitedSpec, FSScriptCommand, FSScriptOutputSpec
from nipype.interfaces.base import (isdefined, TraitedSpec, File, traits, Directory)

from ... import logging
iflogger = logging.getLogger('interface')


class MPRtoMNI305InputSpec(FSTraitedSpec):
    # environment variables, required
    # usedefault=True is hack for on_trait_change in __init__
    reference_dir = Directory("", exists=True, mandatory=True, usedefault=True, desc="TODO")
    target = traits.String("", mandatory=True, usedefault=True, desc="input atlas file")
    # required
    in_file = File(argstr='%s', usedefault=True, desc="the input file prefix for MPRtoMNI305")


class MPRtoMNI305OutputSpec(FSScriptOutputSpec):
    out_file = File(exists=False, desc="The output file '<in_file>_to_<target>_t4_vox2vox.txt'")


class MPRtoMNI305(FSScriptCommand):
    """
    For complete details, see FreeSurfer documentation

    Examples
    ========

    >>> from nipype.interfaces.freesurfer import MPRtoMNI305, Info
    >>> mprtomni305 = MPRtoMNI305()

    >>> mprtomni305.inputs.target = 'structural.nii'
    >>> mprtomni305.inputs.reference_dir = os.path.join(Info.home(), 'average')
    >>> mprtomni305.cmdline()
    'mpr2mni305 output'
    >>> mprtomni305.inputs.out_file = 'struct_out'
    >>> mprtomni305.cmdline()
    'mpr2mni305 struct_out'
    >>> mprtomni305.inputs.environ['REFDIR'] == os.path.join(Info.home(), 'average')
    True
    >>> mprtomni305.inputs.environ['MPR2MNI305_TARGET']
    'structural'

    >>> mprtomni305.run() # doctest: +SKIP

    """
    _cmd = "mpr2mni305"
    input_spec = MPRtoMNI305InputSpec
    output_spec = MPRtoMNI305OutputSpec

    def __init__(self, **inputs):
        super(MPRtoMNI305, self).__init__(**inputs)
        self.inputs.on_trait_change(self._environ_update, 'target')
        self.inputs.on_trait_change(self._environ_update, 'reference_dir')

    def _format_arg(self, opt, spec, val):
        if opt in ['target', 'reference_dir']:
            return ""
        elif opt == 'in_file':
            _, retval, ext = split_filename(val)
            # Need to copy file to working cache directory!
            copyfile(val, os.path.abspath(retval + ext), copy=True, hashmethod='content')
            return retval
        return super(MPRtoMNI305, self)._format_arg(opt, spec, val)

    def _environ_update(self):
        refdir = self.inputs.reference_dir  # refdir = os.path.join(Info.home(), val)
        target = self.inputs.target
        self.inputs.environ['MPR2MNI305_TARGET'] = target
        self.inputs.environ["REFDIR"] = refdir

    def _get_fname(self, fname):
        return split_filename(fname)[1]

    def _list_outputs(self):
        outputs = super(MPRtoMNI305, self)._list_outputs()
        fullname = "_".join([self._get_fname(self.inputs.in_file), "to",
                             self.inputs.target, "t4", "vox2vox.txt"])
        outputs['out_file'] = os.path.abspath(fullname)
        return outputs


class RegisterAVItoTalairachInputSpec(FSTraitedSpec):
    in_file = File(argstr='%s', exists=True, mandatory=True, position=0, desc="The input file")
    target = File(argstr='%s', exists=True, mandatory=True, position=1, desc="The target file")
    vox2vox = File(argstr='%s', exists=True, mandatory=True, position=2, desc="The vox2vox file")
    out_file = File(argstr='%s', mandatory=False, genfile=True, position=3, desc="The transform output")


class RegisterAVItoTalairachOutputSpec(FSScriptOutputSpec):
    out_file = traits.File(exists=False, desc="The output file for RegisterAVItoTalairach")


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

    >>> register.inputs.in_file = 'structural.mgz'
    >>> register.inputs.target = 'mni305.cor.mgz'
    >>> register.inputs.vox2vox = 'talsrcimg_to_structural_t4_vox2vox.txt'
    >>> register.cmdline
    'avi2talxfm structural.mgz mni305.cor.mgz talsrcimg_to_structural_t4_vox2vox.txt talairach.auto.xfm'

    >>> register.run() # doctest: +SKIP
    """
    _cmd = "avi2talxfm"
    input_spec = RegisterAVItoTalairachInputSpec
    output_spec = RegisterAVItoTalairachOutputSpec

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None

    def _list_outputs(self):
        outputs = super(RegisterAVItoTalairach, self)._list_outputs()
        # outputs = self.output_spec().get()
        if isdefined(self.inputs.out_file):
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        else:
            outputs['out_file'] = 'talairach.auto.xfm'
        return outputs


class EMRegisterInputSpec(FSTraitedSpec):
    # required
    in_file = File(argstr="%s", exists=True, mandatory=True, position=-3, desc="in brain volume")
    template = File(argstr="%s", exists=True, mandatory=True, position=-2, desc="template gca")
    out_file = File(argstr="%s", exists=False, mandatory=True, position=-1, genfile=True, desc="output transform")
    # optional
    skull = traits.Bool(argstr="-skull", desc="align to atlas containing skull (uns=5)")
    mask = File(argstr="-mask %s", exists=True, mandatory=False, desc="use volume as a mask")
    nbrspacing = traits.Int(argstr="-uns %d", mandatory=False,
                                    desc="align to atlas containing skull setting unknown_nbr_spacing = nbrspacing")
    transform = File(argstr="-t %s", exists=True, mandatory=False, desc="Previously computed transform")
    
class EMRegisterOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="output transform")


class EMRegister(FSCommand):
    """ This program creates a tranform in lta format
    """
    _cmd = 'mri_em_register'
    input_spec = EMRegisterInputSpec
    output_spec = EMRegisterOutputSpec

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_file):
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        else:
            outputs['out_file'] = 'talairach_with_skull.lta'
        return outputs

class RegisterInputSpec(FSTraitedSpec):
    # required
    in_surf = File(argstr="%s", exists=True, mandatory=True, position=-3,
                   desc="Surface to register, often {hemi}.sphere")
    target = File(argstr="%s", exists=True, mandatory=True, position=-2,
                  desc="The data to register to. In normal recon-all usage, this is a template file for average surface.")
    in_smoothwm = File(exists=True, mandatory=True,
                   desc="Undocumented mandatory input file ${SUBJECTS_DIR}/surf/{hemisphere}.smoothwm ")
    in_sulc = File(exists=True, mandatory=True,
                   desc="Undocumented mandatory input file ${SUBJECTS_DIR}/surf/{hemisphere}.sulc ")
    # optional
    curv = File(argstr="-curv", mandatory=False, exists=True,
                          desc="Use smoothwm curvature for final alignment")
    out_file = File(argstr="%s", exists=False, position=-1, genfile=True,
                    desc="Output surface file to capture registration")
    
class RegisterOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Output surface file to capture registration")


class Register(FSCommand):
    """ This program registers a surface to an average surface template.
    """
    _cmd = 'mris_register'
    input_spec = RegisterInputSpec
    output_spec = RegisterOutputSpec

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_file):
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.in_surf) + '.reg'
        return outputs


class PaintInputSpec(FSTraitedSpec):
    # required
    in_surf = File(argstr="%s", exists=True, mandatory=True, position=-2,
                   desc="Surface file with grid (vertices) onto which the template data is to be sampled or 'painted'")
    template = File(argstr="%s", exists=True, mandatory=True, position=-3,
                  desc="Template file")
    #optional
    template_param = traits.Int(mandatory=False, desc="Frame number of the input template")
    averages = traits.Int(argstr="-a %d", mandatory=False,
                         desc="Average curvature patterns")
    out_file = File(argstr="%s", exists=False, position=-1, genfile=True,
                    desc="File containing a surface-worth of per-vertex values, saved in 'curvature' format.")
    
class PaintOutputSpec(TraitedSpec):
    out_file = File(exists=False,
                    desc="File containing a surface-worth of per-vertex values, saved in 'curvature' format.")


class Paint(FSCommand):
    """
    This program is useful for extracting one of the arrays ("a variable")
    from a surface-registration template file. The output is a file 
    containing a surface-worth of per-vertex values, saved in "curvature" 
    format. Because the template data is sampled to a particular surface 
    mesh, this conjures the idea of "painting to a surface".
    """
    _cmd = 'mrisp_paint'
    input_spec = PaintInputSpec
    output_spec = PaintOutputSpec

    def _format_arg(self, opt, spec, val):
        if opt == 'template':
            if isdefined(self.inputs.template_param):
                return spec.argstr % (val + '#' + str(self.inputs.template_param))
        return super(Paint, self)._format_arg(opt, spec, val)
    
    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_file):
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        else:
            head, tail = os.path.split(self.inputs.in_surf)
            hemisphere = tail.split('.')[0]
            filename = hemisphere + '.avg_curv'
            outputs['out_file'] = os.path.join(head, filename)
        return outputs
