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
    
    frame = traits.Int(
        argstr="--frame %i",
        desc="only process 0-based frame F from inputvol"
    )

    psf = traits.Float(
        argstr="--psf %f",
        desc="scanner PSF FWHM in mm"
    ) 
    _xor_inputs = ("segmentation_file", "annot", "surf_label")
    segmentation_file = File(
        exists=True,
        argstr="--seg %s",
        xor=_xor_inputs,
        mandatory=True,
        desc="anatomical segmentation to define regions for GTM",
    )
    _reg_xor = (
        "reg_file",
        "lta_file"
    )
    reg_file = File(
        exists=True,
        xor=_reg_xor,
        argstr="--reg %s",
        mandatory=True,
        desc="LTA registration file that maps PET to anatomical",
    )

    regheader = traits.Bool(
        argstr="--regheader", desc="assume input and seg share scanner space"
    ) 

    reg_identity = traits.Bool(
        argstr="--regheader", desc="assume that input is in anatomical space"
    )

    output_dir = traits.Str(argstr="--o %s", desc="save outputs to dir", genfile=True)

    mask_file = File(
        exists=True, argstr="--mask %s", desc="ignore areas outside of the mask (in input vol space)"
    )

    auto_mask = traits.Tuple(
        traits.Float,
        traits.Float,
        argstr="--auto-mask %f %f",
        desc="FWHM thresh : automatically compute mask"
    )

    no_reduce_fov = traits.Bool(
        argstr="--no-reduce-fov", desc="do not reduce FoV to encompass mask"
    ) 

    reduce_fox_eqodd = traits.Bool(
        argstr="--reduce-fox-eqodd", desc="reduce FoV to encompass mask but force nc=nr and ns to be odd"
    )

    contrast = InputMultiPath(
        File(exists=True), argstr="--C %s...", desc="contrast file"
    )

    default_seg_merge = traits.Bool(
        argstr="--default-seg-merge", desc="default schema for merging ROIs"
    ) 

    merge_hypos = traits.Bool(
        argstr="--merge-hypos", desc="merge left and right hypointensites into to ROI"
    )  

    merge_cblum_wm_gyri = traits.Bool(
        argstr="--merge-cblum-wm-gyri", desc="cerebellum WM gyri back into cerebellum WM"
    )   

    tt_reduce = traits.Bool(
        argstr="--tt-reduce", desc="reduce segmentation to that of a tissue type"
    )    

    replace = traits.Tuple(
        traits.Int,
        traits.Int,
        argstr="--replace %i %i",
        desc="Id1 Id2 : replace seg Id1 with seg Id2"
    )

    rescale =  traits.List(
        argstr="--rescale %s...", desc="Id1 <Id2...>  : specify reference region(s) used to rescale (default is pons)"
    )

    no_rescale = traits.Bool(
        argstr="--no-rescale", desc="do not global rescale such that mean of reference region is scaleref"
    )     

    scale_refval = traits.Float(
        argstr="--scale-refval %f",
        desc="refval : scale such that mean in reference region is refval"
    )  

    _ctab_inputs = ("color_table_file", "default_color_table", "gca_color_table")
    color_table_file = File(
        exists=True,
        argstr="--ctab %s",
        xor=_ctab_inputs,
        desc="color table file with seg id names",
    )

    default_color_table = traits.Bool(
        argstr="--ctab-default",
        xor=_ctab_inputs,
        desc="use $FREESURFER_HOME/FreeSurferColorLUT.txt",
    )

    tt_update = traits.Bool(
        argstr="--tt-update", desc="changes tissue type of VentralDC, BrainStem, and Pons to be SubcortGM"
    )      

    lat = traits.Bool(
        argstr="--lat", desc="lateralize tissue types"
    )       

    no_tfe = traits.Bool(
        argstr="--no-tfe", desc="do not correction for tissue fraction effect (with --psf 0 turns off PVC entirely)"
    )        

    segpvfres = traits.Float(
        argstr="--segpvfres %f",
        desc="set the tissue fraction resolution parameter (def is 0.5)"
    )   

    rbv = traits.Bool(
        argstr="--rbv", desc="perform RBV PVC"
    )         

    rbv_res = traits.Float(
        argstr="--rbv-res %f",
        desc="voxsize : set RBV voxel resolution (good for when standard res takes too much memory)"
    ) 

    mg = traits.List(
        argstr="--id %s...", desc="Manually specify segmentation ids"
    )

    mg_ref_cerebral_wm = traits.Bool(
        argstr="--mg-ref-cerebral-wm", desc=" set MG RefIds to 2 and 41"
    )       

    mg_ref_lobes_wm = traits.Bool(
        argstr="--mg-ref-lobes-wm", desc="set MG RefIds to those for lobes when using wm subseg"
    )      

    mgx = traits.Float(
        argstr="--mgx %f",
        desc="gmxthresh : GLM-based Mueller-Gaertner PVC, gmxthresh is min gm pvf bet 0 and 1"
    ) 

    km_ref = traits.List(
        argstr="--km-ref %s...", desc="RefId1 RefId2 ... : compute reference TAC for KM as mean of given RefIds"
    )

    km_hb = traits.List(
        argstr="--km-hb %s...", desc="RefId1 RefId2 ... : compute HiBinding TAC for KM as mean of given RefIds"
    ) 

    ss = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr="--ss %f %f %f",
        desc="bpc scale dcf : steady-state analysis spec blood plasma concentration, unit scale and decay correction factor. You must also spec --km-ref. Turns off rescaling"
    ) 

    X = traits.Bool(
        argstr="--X", desc="save X matrix in matlab4 format as X.mat (it will be big)"
    ) 

    y = traits.Bool(
        argstr="--y", desc="save y matrix in matlab4 format as y.mat"
    )

    beta = traits.Bool(
        argstr="--beta", desc="save beta matrix in matlab4 format as beta.mat"
    )
    
    X0 = traits.Bool(
        argstr="--X0", desc="save X0 matrix in matlab4 format as X0.mat (it will be big)"
    )

    save_input = traits.Bool(
        argstr="--save-input", desc="saves rescaled input as input.rescaled.nii.gz"
    )

    save_eres = traits.Bool(
        argstr="--save-eres", desc="saves residual error"
    )

    save_yhat = traits.Bool(
        argstr="--save-yhat", desc="save signal estimate (yhat)"
    )

    save_yhat_with_noise = traits.Tuple(
        traits.Int,
        traits.Int,
        argstr="--ss %i %i",
        desc="seed nreps : saves yhat with noise, seed < 0 for TOD"
    ) 
    
    traits.Bool(
        argstr="--save-yhat-with-noise", desc="save signal estimate (yhat) with noise"
    ) 

    save_yhat_full_fov = traits.Bool(
        argstr="--save_yhat_full_fov", desc="save signal estimate (yhat)"
    )

    save_yhat0 = traits.Bool(
        argstr="--save_yhat0", desc="save signal estimate (yhat)"
    )

class GTMPVCOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="PVC correction")

class GTMPVC(FSCommand):
    """create an anatomical segmentation for the geometric transfer matrix (GTM).

    Examples
    --------
    >>> gtmpvc = GTMPVC()
    >>> gtmpvc.inputs.out_file = ''
    >>> gtmpvc.cmdline == 'mri_gtmpvc '

    """

    _cmd = "mri_gtmpvc"
    input_spec = GTMPVCInputSpec
    output_spec = GTMPVCOutputSpec

    def _format_arg(self, name, spec, value):       
        return super(GTMPVC, self)._format_arg(name, spec, value)

#class MRTMInputSpec(FSTraitedSpec):

#class MRTMOutputSpec(TraitedSpec):

#class MRTM(FSCommand):

#class MRTM2InputSpec(FSTraitedSpec):

#class MRTM2OutputSpec(TraitedSpec):

#class MRTM2(FSCommand):

#class LoganRefInputSpec(FSTraitedSpec):

#class LoganRefOutputSpec(TraitedSpec):

#class LoganRef(FSCommand):