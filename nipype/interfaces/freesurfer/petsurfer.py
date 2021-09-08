# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provides interfaces to various commands for running PET analyses provided by FreeSurfer
"""

import os
import os.path as op
from glob import glob
import shutil
import sys

import numpy as np
from nibabel import load

from ... import logging, LooseVersion
from ...utils.filemanip import fname_presuffix, check_depends
from ..io import FreeSurferSource
from ..base import (
    TraitedSpec,
    File,
    traits,
    Directory,
    InputMultiPath,
    OutputMultiPath,
    CommandLine,
    CommandLineInputSpec,
    isdefined,
)
from .base import FSCommand, FSTraitedSpec, FSTraitedSpecOpenMP, FSCommandOpenMP, Info
from .utils import copy2subjdir

__docformat__ = "restructuredtext"
iflogger = logging.getLogger("nipype.interface")

# Keeping this to avoid breaking external programs that depend on it, but
# this should not be used internally
FSVersion = Info.looseversion().vstring

class GTMSegInputSpec(FSTraitedSpec):
    
    subject_id = traits.String(
        argstr="--s %s",
        desc="subject id",
        mandatory=True
    )

    xcerseg = traits.Bool(
        argstr="--xcerseg",
        desc="run xcerebralseg on this subject to create apas+head.mgz"
    )

    out_file = File(
        argstr="--o %s",
        desc="output volume relative to subject/mri (default is gtmseg.mgz)"
    )

    usf = traits.Int(
        argstr="--usf %i",
        desc="upsampling factor (default is 2)"
    )

    subsegwm = traits.Bool(
        argstr="--subsegwm",
        desc="subsegment WM into lobes (default)"
    )
    
    keep_hypo = traits.Bool(
        argstr="--keep-hypo",
        desc="do not relabel hypointensities as WM when subsegmenting WM"
    )
    
    keep_cc = traits.Bool(
        argstr="--keep-cc",
        desc="do not relabel corpus callosum as WM"
    )

    dmax = traits.Float(
            argstr="--dmax %f",
            desc="distance threshold to use when subsegmenting WM (default is 5)"
        )

    ctx_annot = traits.Tuple(
        traits.String,
        traits.Int,
        traits.Int,
        argstr="--ctx-annot %s %i %i",
        desc="annot lhbase rhbase : annotation to use for cortical segmentation (default is aparc 1000 2000)"
    )

    wm_annot = traits.Tuple(
        traits.String,
        traits.Int,
        traits.Int,
        argstr="--wm-annot %s %i %i",
        desc="annot lhbase rhbase : annotation to use for WM segmentation (with --subsegwm, default is lobes 3200 4200)"
    )

    output_usf = traits.Int(
        argstr="--output-usf %i",
        desc="set output USF different than USF, mostly for debugging"
    )

    head = traits.String(
        argstr="--head %s",
        desc="use headseg instead of apas+head.mgz"
    )

    subseg_cblum_wm = traits.Bool(
        argstr="--subseg-cblum-wm",
        desc="subsegment cerebellum WM into core and gyri"
    )     

    no_pons = traits.Bool(
        argstr="--no-pons",
        desc="do not add pons segmentation when doing ---xcerseg"
    )
    
    no_vermis = traits.Bool(
        argstr="--no-vermis",
        desc="do not add vermis segmentation when doing ---xcerseg"
    )

    ctab = File(
        exists=True,
        argstr="--ctab %s",
        desc="colortable"
    )
    no_seg_stats = traits.Bool(
        argstr="--no-seg-stats",
        desc="do not compute segmentation stats"
    )    


class GTMSegOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="GTM segmentation")


class GTMSeg(FSCommand):
    """create an anatomical segmentation for the geometric transfer matrix (GTM).

    Examples
    --------
    >>> gtmseg = GTMSeg()
    >>> gtmseg.inputs.out_file = 'gtmseg.nii'
    >>> gtmseg.inputs.subject_id = 'subjec_id'
    >>> gtmseg.cmdline == 'gtmseg --o gtmseg.nii --s subject_id'

    """

    _cmd = "gtmseg"
    input_spec = GTMSegInputSpec
    output_spec = GTMSegOutputSpec

    def _format_arg(self, name, spec, value):       
        return super(GTMSeg, self)._format_arg(name, spec, value)

class GTMPVCInputSpec(FSTraitedSpec):

    in_file = File(
            exists=True,
            argstr="--i %s",
            mandatory=True,
            copyfile=False,
            desc="input volume - source data to pvc",
        )
    
    frame = 

    psf = 

    seg = 

    reg = 

    regheader = 

    reg_identity = 

    output_dir = traits.Str(argstr="--o %s", desc="save outputs to dir", genfile=True)

    mask = 

    auto_mask = 

    no_reduce_fov = 

    reduce_fox_eqodd = 

    contrast = InputMultiPath(
        File(exists=True), argstr="--C %s...", desc="contrast file"
    )

    default_seg_merge = 

    merge_hypos = 

    merge_cblum_wm_gyri = 

    tt_reduce = 

    replace = 

    replace_file = 

    rescale = 

    no_rescale = 

    scale_refval = 

    ctab = 

    ctab_default = 

    tt_update = 

    lat = 

    no_tfe = 

    segpvfres = 

    rbv = 

    rbv_res = 

    mg = 

    mg_ref_cerebral_wm = 

    mg_ref_lobes_wm = 

    mgx = 

    km_ref = 

    km_hb = 

    ss = 

    X = 

    y = 

    beta = 
    
    X0 = 

    save_input = 

    save_eres = 

    save_yhat = 

    save_yhat_with_noise = 

    save_yhat_full_fov = 

    save_yhat0 = 

    synth = 

    synth_only = 

    synth_save = 

    save_text = 

    

class GTMPVCOutputSpec(TraitedSpec):

class GTMPVC(FSCommand):

class MRTMInputSpec(FSTraitedSpec):

class MRTMOutputSpec(TraitedSpec):

class MRTM(FSCommand):

class MRTM2InputSpec(FSTraitedSpec):

class MRTM2OutputSpec(TraitedSpec):

class MRTM2(FSCommand):