# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""AFNI preprocessing interfaces."""

import os
import os.path as op

from ...utils.filemanip import load_json, save_json, split_filename, fname_presuffix
from ..base import (
    CommandLineInputSpec,
    CommandLine,
    TraitedSpec,
    traits,
    isdefined,
    File,
    InputMultiPath,
    Undefined,
    Str,
    InputMultiObject,
)

from .base import (
    AFNICommandBase,
    AFNICommand,
    AFNICommandInputSpec,
    AFNICommandOutputSpec,
    AFNIPythonCommandInputSpec,
    AFNIPythonCommand,
    Info,
    no_afni,
)

from ... import logging

iflogger = logging.getLogger("nipype.interface")


class CentralityInputSpec(AFNICommandInputSpec):
    """Common input spec class for all centrality-related commands
    """

    mask = File(desc="mask file to mask input data", argstr="-mask %s", exists=True)
    thresh = traits.Float(
        desc="threshold to exclude connections where corr <= thresh",
        argstr="-thresh %f",
    )
    polort = traits.Int(desc="", argstr="-polort %d")
    autoclip = traits.Bool(
        desc="Clip off low-intensity regions in the dataset", argstr="-autoclip"
    )
    automask = traits.Bool(
        desc="Mask the dataset to target brain-only voxels", argstr="-automask"
    )


class AlignEpiAnatPyInputSpec(AFNIPythonCommandInputSpec):
    in_file = File(
        desc="EPI dataset to align",
        argstr="-epi %s",
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    anat = File(
        desc="name of structural dataset",
        argstr="-anat %s",
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    epi_base = traits.Either(
        traits.Range(low=0),
        traits.Enum("mean", "median", "max"),
        desc="the epi base used in alignment"
        "should be one of (0/mean/median/max/subbrick#)",
        mandatory=True,
        argstr="-epi_base %s",
    )
    anat2epi = traits.Bool(
        desc="align anatomical to EPI dataset (default)", argstr="-anat2epi"
    )
    epi2anat = traits.Bool(desc="align EPI to anatomical dataset", argstr="-epi2anat")
    save_skullstrip = traits.Bool(
        desc="save skull-stripped (not aligned)", argstr="-save_skullstrip"
    )
    suffix = traits.Str(
        "_al",
        desc="append suffix to the original anat/epi dataset to use"
        'in the resulting dataset names (default is "_al")',
        usedefault=True,
        argstr="-suffix %s",
    )
    epi_strip = traits.Enum(
        ("3dSkullStrip", "3dAutomask", "None"),
        desc="method to mask brain in EPI data"
        "should be one of[3dSkullStrip]/3dAutomask/None)",
        argstr="-epi_strip %s",
    )
    volreg = traits.Enum(
        "on",
        "off",
        usedefault=True,
        desc="do volume registration on EPI dataset before alignment"
        "should be 'on' or 'off', defaults to 'on'",
        argstr="-volreg %s",
    )
    tshift = traits.Enum(
        "on",
        "off",
        usedefault=True,
        desc="do time shifting of EPI dataset before alignment"
        "should be 'on' or 'off', defaults to 'on'",
        argstr="-tshift %s",
    )


class AlignEpiAnatPyOutputSpec(TraitedSpec):
    anat_al_orig = File(desc="A version of the anatomy that is aligned to the EPI")
    epi_al_orig = File(desc="A version of the EPI dataset aligned to the anatomy")
    epi_tlrc_al = File(
        desc="A version of the EPI dataset aligned to a standard template"
    )
    anat_al_mat = File(desc="matrix to align anatomy to the EPI")
    epi_al_mat = File(desc="matrix to align EPI to anatomy")
    epi_vr_al_mat = File(desc="matrix to volume register EPI")
    epi_reg_al_mat = File(desc="matrix to volume register and align epi to anatomy")
    epi_al_tlrc_mat = File(
        desc="matrix to volume register and align epi"
        "to anatomy and put into standard space"
    )
    epi_vr_motion = File(
        desc="motion parameters from EPI time-series"
        "registration (tsh included in name if slice"
        "timing correction is also included)."
    )
    skullstrip = File(desc="skull-stripped (not aligned) volume")


class AlignEpiAnatPy(AFNIPythonCommand):
    """Align EPI to anatomical datasets or vice versa.

    This Python script computes the alignment between two datasets, typically
    an EPI and an anatomical structural dataset, and applies the resulting
    transformation to one or the other to bring them into alignment.

    This script computes the transforms needed to align EPI and
    anatomical datasets using a cost function designed for this purpose. The
    script combines multiple transformations, thereby minimizing the amount of
    interpolation applied to the data.

    Basic Usage::

        align_epi_anat.py -anat anat+orig -epi epi+orig -epi_base 5

    The user must provide :abbr:`EPI (echo-planar imaging)` and anatomical datasets
    and specify the EPI sub-brick to use as a base in the alignment.

    Internally, the script always aligns the anatomical to the EPI dataset,
    and the resulting transformation is saved to a 1D file.
    As a user option, the inverse of this transformation may be applied to the
    EPI dataset in order to align it to the anatomical data instead.

    This program generates several kinds of output in the form of datasets
    and transformation matrices which can be applied to other datasets if
    needed. Time-series volume registration, oblique data transformations and
    Talairach (standard template) transformations will be combined as needed
    and requested (with options to turn on and off each of the steps) in
    order to create the aligned datasets.

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> al_ea = afni.AlignEpiAnatPy()
    >>> al_ea.inputs.anat = "structural.nii"
    >>> al_ea.inputs.in_file = "functional.nii"
    >>> al_ea.inputs.epi_base = 0
    >>> al_ea.inputs.epi_strip = '3dAutomask'
    >>> al_ea.inputs.volreg = 'off'
    >>> al_ea.inputs.tshift = 'off'
    >>> al_ea.inputs.save_skullstrip = True
    >>> al_ea.cmdline # doctest: +ELLIPSIS
    'python2 ...align_epi_anat.py -anat structural.nii -epi_base 0 -epi_strip 3dAutomask -epi \
functional.nii -save_skullstrip -suffix _al -tshift off -volreg off'
    >>> res = allineate.run()  # doctest: +SKIP

    See Also
    --------
    For complete details, see the `align_epi_anat.py documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/align_epi_anat.py.html>`__.

    """

    _cmd = "align_epi_anat.py"
    input_spec = AlignEpiAnatPyInputSpec
    output_spec = AlignEpiAnatPyOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        anat_prefix = self._gen_fname(self.inputs.anat)
        epi_prefix = self._gen_fname(self.inputs.in_file)
        if "+" in anat_prefix:
            anat_prefix = "".join(anat_prefix.split("+")[:-1])
        if "+" in epi_prefix:
            epi_prefix = "".join(epi_prefix.split("+")[:-1])
        outputtype = self.inputs.outputtype
        if outputtype == "AFNI":
            ext = ".HEAD"
        else:
            ext = Info.output_type_to_ext(outputtype)
        matext = ".1D"
        suffix = self.inputs.suffix
        if self.inputs.anat2epi:
            outputs["anat_al_orig"] = self._gen_fname(
                anat_prefix, suffix=suffix + "+orig", ext=ext
            )
            outputs["anat_al_mat"] = self._gen_fname(
                anat_prefix, suffix=suffix + "_mat.aff12", ext=matext
            )
        if self.inputs.epi2anat:
            outputs["epi_al_orig"] = self._gen_fname(
                epi_prefix, suffix=suffix + "+orig", ext=ext
            )
            outputs["epi_al_mat"] = self._gen_fname(
                epi_prefix, suffix=suffix + "_mat.aff12", ext=matext
            )
        if self.inputs.volreg == "on":
            outputs["epi_vr_al_mat"] = self._gen_fname(
                epi_prefix, suffix="_vr" + suffix + "_mat.aff12", ext=matext
            )
            if self.inputs.tshift == "on":
                outputs["epi_vr_motion"] = self._gen_fname(
                    epi_prefix, suffix="tsh_vr_motion", ext=matext
                )
            elif self.inputs.tshift == "off":
                outputs["epi_vr_motion"] = self._gen_fname(
                    epi_prefix, suffix="vr_motion", ext=matext
                )
        if self.inputs.volreg == "on" and self.inputs.epi2anat:
            outputs["epi_reg_al_mat"] = self._gen_fname(
                epi_prefix, suffix="_reg" + suffix + "_mat.aff12", ext=matext
            )
        if self.inputs.save_skullstrip:
            outputs.skullstrip = self._gen_fname(
                anat_prefix, suffix="_ns" + "+orig", ext=ext
            )
        return outputs


class AllineateInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dAllineate",
        argstr="-source %s",
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    reference = File(
        exists=True,
        argstr="-base %s",
        desc="file to be used as reference, the first volume will be used if "
        "not given the reference will be the first volume of in_file.",
    )
    out_file = File(
        desc="output file from 3dAllineate",
        argstr="-prefix %s",
        name_template="%s_allineate",
        name_source="in_file",
        hash_files=False,
        xor=["allcostx"],
    )
    out_param_file = File(
        argstr="-1Dparam_save %s",
        desc="Save the warp parameters in ASCII (.1D) format.",
        xor=["in_param_file", "allcostx"],
    )
    in_param_file = File(
        exists=True,
        argstr="-1Dparam_apply %s",
        desc="Read warp parameters from file and apply them to "
        "the source dataset, and produce a new dataset",
        xor=["out_param_file"],
    )
    out_matrix = File(
        argstr="-1Dmatrix_save %s",
        desc="Save the transformation matrix for each volume.",
        xor=["in_matrix", "allcostx"],
    )
    in_matrix = File(
        desc="matrix to align input file",
        argstr="-1Dmatrix_apply %s",
        position=-3,
        xor=["out_matrix"],
    )
    overwrite = traits.Bool(
        desc="overwrite output file if it already exists", argstr="-overwrite"
    )

    allcostx = File(
        desc="Compute and print ALL available cost functionals for the un-warped inputs"
        "AND THEN QUIT. If you use this option none of the other expected outputs will be produced",
        argstr="-allcostx |& tee %s",
        position=-1,
        xor=["out_file", "out_matrix", "out_param_file", "out_weight_file"],
    )
    _cost_funcs = [
        "leastsq",
        "ls",
        "mutualinfo",
        "mi",
        "corratio_mul",
        "crM",
        "norm_mutualinfo",
        "nmi",
        "hellinger",
        "hel",
        "corratio_add",
        "crA",
        "corratio_uns",
        "crU",
    ]

    cost = traits.Enum(
        *_cost_funcs,
        argstr="-cost %s",
        desc="Defines the 'cost' function that defines the matching between "
        "the source and the base"
    )
    _interp_funcs = ["nearestneighbour", "linear", "cubic", "quintic", "wsinc5"]
    interpolation = traits.Enum(
        *_interp_funcs[:-1],
        argstr="-interp %s",
        desc="Defines interpolation method to use during matching"
    )
    final_interpolation = traits.Enum(
        *_interp_funcs,
        argstr="-final %s",
        desc="Defines interpolation method used to create the output dataset"
    )

    #   TECHNICAL OPTIONS (used for fine control of the program):
    nmatch = traits.Int(
        argstr="-nmatch %d",
        desc="Use at most n scattered points to match the datasets.",
    )
    no_pad = traits.Bool(
        argstr="-nopad", desc="Do not use zero-padding on the base image."
    )
    zclip = traits.Bool(
        argstr="-zclip",
        desc="Replace negative values in the input datasets (source & base) "
        "with zero.",
    )
    convergence = traits.Float(
        argstr="-conv %f", desc="Convergence test in millimeters (default 0.05mm)."
    )
    usetemp = traits.Bool(argstr="-usetemp", desc="temporary file use")
    check = traits.List(
        traits.Enum(*_cost_funcs),
        argstr="-check %s",
        desc="After cost functional optimization is done, start at the final "
        "parameters and RE-optimize using this new cost functions. If "
        "the results are too different, a warning message will be "
        "printed. However, the final parameters from the original "
        "optimization will be used to create the output dataset.",
    )

    #      ** PARAMETERS THAT AFFECT THE COST OPTIMIZATION STRATEGY **
    one_pass = traits.Bool(
        argstr="-onepass",
        desc="Use only the refining pass -- do not try a coarse resolution "
        "pass first.  Useful if you know that only small amounts of "
        "image alignment are needed.",
    )
    two_pass = traits.Bool(
        argstr="-twopass",
        desc="Use a two pass alignment strategy for all volumes, searching "
        "for a large rotation+shift and then refining the alignment.",
    )
    two_blur = traits.Float(
        argstr="-twoblur %f", desc="Set the blurring radius for the first pass in mm."
    )
    two_first = traits.Bool(
        argstr="-twofirst",
        desc="Use -twopass on the first image to be registered, and "
        "then on all subsequent images from the source dataset, "
        "use results from the first image's coarse pass to start "
        "the fine pass.",
    )
    two_best = traits.Int(
        argstr="-twobest %d",
        desc="In the coarse pass, use the best 'bb' set of initial"
        "points to search for the starting point for the fine"
        "pass.  If bb==0, then no search is made for the best"
        "starting point, and the identity transformation is"
        "used as the starting point.  [Default=5; min=0 max=11]",
    )
    fine_blur = traits.Float(
        argstr="-fineblur %f",
        desc="Set the blurring radius to use in the fine resolution "
        "pass to 'x' mm.  A small amount (1-2 mm?) of blurring at "
        "the fine step may help with convergence, if there is "
        "some problem, especially if the base volume is very noisy. "
        "[Default == 0 mm = no blurring at the final alignment pass]",
    )
    center_of_mass = Str(
        argstr="-cmass%s",
        desc="Use the center-of-mass calculation to bracket the shifts.",
    )
    autoweight = Str(
        argstr="-autoweight%s",
        desc="Compute a weight function using the 3dAutomask "
        "algorithm plus some blurring of the base image.",
    )
    automask = traits.Int(
        argstr="-automask+%d",
        desc="Compute a mask function, set a value for dilation or 0.",
    )
    autobox = traits.Bool(
        argstr="-autobox",
        desc="Expand the -automask function to enclose a rectangular "
        "box that holds the irregular mask.",
    )
    nomask = traits.Bool(
        argstr="-nomask",
        desc="Don't compute the autoweight/mask; if -weight is not "
        "also used, then every voxel will be counted equally.",
    )
    weight_file = File(
        argstr="-weight %s",
        exists=True,
        deprecated="1.0.0",
        new_name="weight",
        desc="Set the weighting for each voxel in the base dataset; "
        "larger weights mean that voxel count more in the cost function. "
        "Must be defined on the same grid as the base dataset",
    )
    weight = traits.Either(
        File(exists=True),
        traits.Float(),
        argstr="-weight %s",
        desc="Set the weighting for each voxel in the base dataset; "
        "larger weights mean that voxel count more in the cost function. "
        "If an image file is given, the volume must be defined on the "
        "same grid as the base dataset",
    )
    out_weight_file = File(
        argstr="-wtprefix %s",
        desc="Write the weight volume to disk as a dataset",
        xor=["allcostx"],
    )
    source_mask = File(
        exists=True, argstr="-source_mask %s", desc="mask the input dataset"
    )
    source_automask = traits.Int(
        argstr="-source_automask+%d",
        desc="Automatically mask the source dataset with dilation or 0.",
    )
    warp_type = traits.Enum(
        "shift_only",
        "shift_rotate",
        "shift_rotate_scale",
        "affine_general",
        argstr="-warp %s",
        desc="Set the warp type.",
    )
    warpfreeze = traits.Bool(
        argstr="-warpfreeze",
        desc="Freeze the non-rigid body parameters after first volume.",
    )
    replacebase = traits.Bool(
        argstr="-replacebase",
        desc="If the source has more than one volume, then after the first "
        "volume is aligned to the base.",
    )
    replacemeth = traits.Enum(
        *_cost_funcs,
        argstr="-replacemeth %s",
        desc="After first volume is aligned, switch method for later volumes. "
        "For use with '-replacebase'."
    )
    epi = traits.Bool(
        argstr="-EPI",
        desc="Treat the source dataset as being composed of warped "
        "EPI slices, and the base as comprising anatomically "
        "'true' images.  Only phase-encoding direction image "
        "shearing and scaling will be allowed with this option.",
    )
    maxrot = traits.Float(
        argstr="-maxrot %f", desc="Maximum allowed rotation in degrees."
    )
    maxshf = traits.Float(argstr="-maxshf %f", desc="Maximum allowed shift in mm.")
    maxscl = traits.Float(argstr="-maxscl %f", desc="Maximum allowed scaling factor.")
    maxshr = traits.Float(argstr="-maxshr %f", desc="Maximum allowed shearing factor.")
    master = File(
        exists=True,
        argstr="-master %s",
        desc="Write the output dataset on the same grid as this file.",
    )
    newgrid = traits.Float(
        argstr="-newgrid %f",
        desc="Write the output dataset using isotropic grid spacing in mm.",
    )

    # Non-linear experimental
    _nwarp_types = [
        "bilinear",
        "cubic",
        "quintic",
        "heptic",
        "nonic",
        "poly3",
        "poly5",
        "poly7",
        "poly9",
    ]  # same non-hellenistic
    nwarp = traits.Enum(
        *_nwarp_types,
        argstr="-nwarp %s",
        desc="Experimental nonlinear warping: bilinear or legendre poly."
    )
    _dirs = ["X", "Y", "Z", "I", "J", "K"]
    nwarp_fixmot = traits.List(
        traits.Enum(*_dirs),
        argstr="-nwarp_fixmot%s...",
        desc="To fix motion along directions.",
    )
    nwarp_fixdep = traits.List(
        traits.Enum(*_dirs),
        argstr="-nwarp_fixdep%s...",
        desc="To fix non-linear warp dependency along directions.",
    )
    verbose = traits.Bool(argstr="-verb", desc="Print out verbose progress reports.")
    quiet = traits.Bool(
        argstr="-quiet", desc="Don't print out verbose progress reports."
    )


class AllineateOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output image file name")
    out_matrix = File(exists=True, desc="matrix to align input file")
    out_param_file = File(exists=True, desc="warp parameters")
    out_weight_file = File(exists=True, desc="weight volume")
    allcostx = File(
        desc="Compute and print ALL available cost functionals for the un-warped inputs"
    )


class Allineate(AFNICommand):
    """Program to align one dataset (the 'source') to a base dataset

    For complete details, see the `3dAllineate Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAllineate.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> allineate = afni.Allineate()
    >>> allineate.inputs.in_file = 'functional.nii'
    >>> allineate.inputs.out_file = 'functional_allineate.nii'
    >>> allineate.inputs.in_matrix = 'cmatrix.mat'
    >>> allineate.cmdline
    '3dAllineate -source functional.nii -prefix functional_allineate.nii -1Dmatrix_apply cmatrix.mat'
    >>> res = allineate.run()  # doctest: +SKIP

    >>> allineate = afni.Allineate()
    >>> allineate.inputs.in_file = 'functional.nii'
    >>> allineate.inputs.reference = 'structural.nii'
    >>> allineate.inputs.allcostx = 'out.allcostX.txt'
    >>> allineate.cmdline
    '3dAllineate -source functional.nii -base structural.nii -allcostx |& tee out.allcostX.txt'
    >>> res = allineate.run()  # doctest: +SKIP

    >>> allineate = afni.Allineate()
    >>> allineate.inputs.in_file = 'functional.nii'
    >>> allineate.inputs.reference = 'structural.nii'
    >>> allineate.inputs.nwarp_fixmot = ['X', 'Y']
    >>> allineate.cmdline
    '3dAllineate -source functional.nii -nwarp_fixmotX -nwarp_fixmotY -prefix functional_allineate -base structural.nii'
    >>> res = allineate.run()  # doctest: +SKIP
    """

    _cmd = "3dAllineate"
    input_spec = AllineateInputSpec
    output_spec = AllineateOutputSpec

    def _list_outputs(self):
        outputs = super(Allineate, self)._list_outputs()

        if self.inputs.out_weight_file:
            outputs["out_weight_file"] = op.abspath(self.inputs.out_weight_file)

        if self.inputs.out_matrix:
            ext = split_filename(self.inputs.out_matrix)[-1]
            if ext.lower() not in [".1d", ".1D"]:
                outputs["out_matrix"] = self._gen_fname(
                    self.inputs.out_matrix, suffix=".aff12.1D"
                )
            else:
                outputs["out_matrix"] = op.abspath(self.inputs.out_matrix)

        if self.inputs.out_param_file:
            ext = split_filename(self.inputs.out_param_file)[-1]
            if ext.lower() not in [".1d", ".1D"]:
                outputs["out_param_file"] = self._gen_fname(
                    self.inputs.out_param_file, suffix=".param.1D"
                )
            else:
                outputs["out_param_file"] = op.abspath(self.inputs.out_param_file)

        if self.inputs.allcostx:
            outputs["allcostX"] = os.path.abspath(self.inputs.allcostx)
        return outputs


class AutoTcorrelateInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="timeseries x space (volume or surface) file",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    polort = traits.Int(
        desc="Remove polynomical trend of order m or -1 for no detrending",
        argstr="-polort %d",
    )
    eta2 = traits.Bool(desc="eta^2 similarity", argstr="-eta2")
    mask = File(exists=True, desc="mask of voxels", argstr="-mask %s")
    mask_only_targets = traits.Bool(
        desc="use mask only on targets voxels",
        argstr="-mask_only_targets",
        xor=["mask_source"],
    )
    mask_source = File(
        exists=True,
        desc="mask for source voxels",
        argstr="-mask_source %s",
        xor=["mask_only_targets"],
    )
    out_file = File(
        name_template="%s_similarity_matrix.1D",
        desc="output image file name",
        argstr="-prefix %s",
        name_source="in_file",
    )


class AutoTcorrelate(AFNICommand):
    """Computes the correlation coefficient between the time series of each
    pair of voxels in the input dataset, and stores the output into a
    new anatomical bucket dataset [scaled to shorts to save memory space].

    For complete details, see the `3dAutoTcorrelate Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAutoTcorrelate.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> corr = afni.AutoTcorrelate()
    >>> corr.inputs.in_file = 'functional.nii'
    >>> corr.inputs.polort = -1
    >>> corr.inputs.eta2 = True
    >>> corr.inputs.mask = 'mask.nii'
    >>> corr.inputs.mask_only_targets = True
    >>> corr.cmdline  # doctest: +ELLIPSIS
    '3dAutoTcorrelate -eta2 -mask mask.nii -mask_only_targets -prefix functional_similarity_matrix.1D -polort -1 functional.nii'
    >>> res = corr.run()  # doctest: +SKIP
    """

    input_spec = AutoTcorrelateInputSpec
    output_spec = AFNICommandOutputSpec
    _cmd = "3dAutoTcorrelate"

    def _overload_extension(self, value, name=None):
        path, base, ext = split_filename(value)
        if ext.lower() not in [".1d", ".1D", ".nii.gz", ".nii"]:
            ext = ext + ".1D"
        return os.path.join(path, base + ext)


class AutomaskInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dAutomask",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_mask",
        desc="output image file name",
        argstr="-prefix %s",
        name_source="in_file",
    )
    brain_file = File(
        name_template="%s_masked",
        desc="output file from 3dAutomask",
        argstr="-apply_prefix %s",
        name_source="in_file",
    )
    clfrac = traits.Float(
        desc="sets the clip level fraction (must be 0.1-0.9). A small value "
        "will tend to make the mask larger [default = 0.5].",
        argstr="-clfrac %s",
    )
    dilate = traits.Int(desc="dilate the mask outwards", argstr="-dilate %s")
    erode = traits.Int(desc="erode the mask inwards", argstr="-erode %s")


class AutomaskOutputSpec(TraitedSpec):
    out_file = File(desc="mask file", exists=True)
    brain_file = File(desc="brain file (skull stripped)", exists=True)


class Automask(AFNICommand):
    """Create a brain-only mask of the image using AFNI 3dAutomask command

    For complete details, see the `3dAutomask Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAutomask.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> automask = afni.Automask()
    >>> automask.inputs.in_file = 'functional.nii'
    >>> automask.inputs.dilate = 1
    >>> automask.inputs.outputtype = 'NIFTI'
    >>> automask.cmdline  # doctest: +ELLIPSIS
    '3dAutomask -apply_prefix functional_masked.nii -dilate 1 -prefix functional_mask.nii functional.nii'
    >>> res = automask.run()  # doctest: +SKIP

    """

    _cmd = "3dAutomask"
    input_spec = AutomaskInputSpec
    output_spec = AutomaskOutputSpec


class AutoTLRCInputSpec(CommandLineInputSpec):
    outputtype = traits.Enum(
        "AFNI", list(Info.ftypes.keys()), desc="AFNI output filetype"
    )
    in_file = File(
        desc="Original anatomical volume (+orig)."
        "The skull is removed by this script"
        "unless instructed otherwise (-no_ss).",
        argstr="-input %s",
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    base = traits.Str(
        desc="""\
Reference anatomical volume.
Usually this volume is in some standard space like
TLRC or MNI space and with afni dataset view of
(+tlrc).
Preferably, this reference volume should have had
the skull removed but that is not mandatory.
AFNI's distribution contains several templates.
For a longer list, use "whereami -show_templates"
TT_N27+tlrc --> Single subject, skull stripped volume.
This volume is also known as
N27_SurfVol_NoSkull+tlrc elsewhere in
AFNI and SUMA land.
(www.loni.ucla.edu, www.bic.mni.mcgill.ca)
This template has a full set of FreeSurfer
(surfer.nmr.mgh.harvard.edu)
surface models that can be used in SUMA.
For details, see Talairach-related link:
https://afni.nimh.nih.gov/afni/suma
TT_icbm452+tlrc --> Average volume of 452 normal brains.
Skull Stripped. (www.loni.ucla.edu)
TT_avg152T1+tlrc --> Average volume of 152 normal brains.
Skull Stripped.(www.bic.mni.mcgill.ca)
TT_EPI+tlrc --> EPI template from spm2, masked as TT_avg152T1
TT_avg152 and TT_EPI volume sources are from
SPM's distribution. (www.fil.ion.ucl.ac.uk/spm/)
If you do not specify a path for the template, the script
will attempt to locate the template AFNI's binaries directory.
NOTE: These datasets have been slightly modified from
their original size to match the standard TLRC
dimensions (Jean Talairach and Pierre Tournoux
Co-Planar Stereotaxic Atlas of the Human Brain
Thieme Medical Publishers, New York, 1988).
That was done for internal consistency in AFNI.
You may use the original form of these
volumes if you choose but your TLRC coordinates
will not be consistent with AFNI's TLRC database
(San Antonio Talairach Daemon database), for example.""",
        mandatory=True,
        argstr="-base %s",
    )
    no_ss = traits.Bool(
        desc="""\
Do not strip skull of input data set
(because skull has already been removed
or because template still has the skull)
NOTE: The ``-no_ss`` option is not all that optional.
Here is a table of when you should and should not use ``-no_ss``

  +------------------+------------+---------------+
  | Dataset          | Template                   |
  +==================+============+===============+
  |                  | w/ skull   | wo/ skull     |
  +------------------+------------+---------------+
  | WITH skull       | ``-no_ss`` | xxx           |
  +------------------+------------+---------------+
  | WITHOUT skull    | No Cigar   | ``-no_ss``    |
  +------------------+------------+---------------+

Template means: Your template of choice
Dset. means: Your anatomical dataset
``-no_ss`` means: Skull stripping should not be attempted on Dset
xxx means: Don't put anything, the script will strip Dset
No Cigar means: Don't try that combination, it makes no sense.""",
        argstr="-no_ss",
    )


class AutoTLRC(AFNICommand):
    """A minmal wrapper for the AutoTLRC script
    The only option currently supported is no_ss.
    For complete details, see the `3dQwarp Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/@auto_tlrc.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> autoTLRC = afni.AutoTLRC()
    >>> autoTLRC.inputs.in_file = 'structural.nii'
    >>> autoTLRC.inputs.no_ss = True
    >>> autoTLRC.inputs.base = "TT_N27+tlrc"
    >>> autoTLRC.cmdline
    '@auto_tlrc -base TT_N27+tlrc -input structural.nii -no_ss'
    >>> res = autoTLRC.run()  # doctest: +SKIP

    """

    _cmd = "@auto_tlrc"
    input_spec = AutoTLRCInputSpec
    output_spec = AFNICommandOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        ext = ".HEAD"
        outputs["out_file"] = os.path.abspath(
            self._gen_fname(self.inputs.in_file, suffix="+tlrc") + ext
        )
        return outputs


class BandpassInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dBandpass",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_bp",
        desc="output file from 3dBandpass",
        argstr="-prefix %s",
        position=1,
        name_source="in_file",
    )
    lowpass = traits.Float(desc="lowpass", argstr="%f", position=-2, mandatory=True)
    highpass = traits.Float(desc="highpass", argstr="%f", position=-3, mandatory=True)
    mask = File(desc="mask file", position=2, argstr="-mask %s", exists=True)
    despike = traits.Bool(
        argstr="-despike",
        desc="Despike each time series before other processing. Hopefully, "
        "you don't actually need to do this, which is why it is "
        "optional.",
    )
    orthogonalize_file = InputMultiPath(
        File(exists=True),
        argstr="-ort %s",
        desc="Also orthogonalize input to columns in f.1D. Multiple '-ort' "
        "options are allowed.",
    )
    orthogonalize_dset = File(
        exists=True,
        argstr="-dsort %s",
        desc="Orthogonalize each voxel to the corresponding voxel time series "
        "in dataset 'fset', which must have the same spatial and "
        "temporal grid structure as the main input dataset. At present, "
        "only one '-dsort' option is allowed.",
    )
    no_detrend = traits.Bool(
        argstr="-nodetrend",
        desc="Skip the quadratic detrending of the input that occurs before "
        "the FFT-based bandpassing. You would only want to do this if "
        "the dataset had been detrended already in some other program.",
    )
    tr = traits.Float(
        argstr="-dt %f", desc="Set time step (TR) in sec [default=from dataset header]."
    )
    nfft = traits.Int(
        argstr="-nfft %d", desc="Set the FFT length [must be a legal value]."
    )
    normalize = traits.Bool(
        argstr="-norm",
        desc="Make all output time series have L2 norm = 1 (i.e., sum of "
        "squares = 1).",
    )
    automask = traits.Bool(
        argstr="-automask", desc="Create a mask from the input dataset."
    )
    blur = traits.Float(
        argstr="-blur %f",
        desc="Blur (inside the mask only) with a filter width (FWHM) of "
        "'fff' millimeters.",
    )
    localPV = traits.Float(
        argstr="-localPV %f",
        desc="Replace each vector by the local Principal Vector (AKA first "
        "singular vector) from a neighborhood of radius 'rrr' "
        "millimeters. Note that the PV time series is L2 normalized. "
        "This option is mostly for Bob Cox to have fun with.",
    )
    notrans = traits.Bool(
        argstr="-notrans",
        desc="Don't check for initial positive transients in the data. "
        "The test is a little slow, so skipping it is OK, if you KNOW "
        "the data time series are transient-free.",
    )


class Bandpass(AFNICommand):
    """Program to lowpass and/or highpass each voxel time series in a
    dataset, offering more/different options than Fourier

    For complete details, see the `3dBandpass Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dBandpass.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> from nipype.testing import  example_data
    >>> bandpass = afni.Bandpass()
    >>> bandpass.inputs.in_file = 'functional.nii'
    >>> bandpass.inputs.highpass = 0.005
    >>> bandpass.inputs.lowpass = 0.1
    >>> bandpass.cmdline
    '3dBandpass -prefix functional_bp 0.005000 0.100000 functional.nii'
    >>> res = bandpass.run()  # doctest: +SKIP

    """

    _cmd = "3dBandpass"
    input_spec = BandpassInputSpec
    output_spec = AFNICommandOutputSpec


class BlurInMaskInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dSkullStrip",
        argstr="-input %s",
        position=1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_blur",
        desc="output to the file",
        argstr="-prefix %s",
        name_source="in_file",
        position=-1,
    )
    mask = File(
        desc="Mask dataset, if desired.  Blurring will occur only within the "
        "mask. Voxels NOT in the mask will be set to zero in the output.",
        argstr="-mask %s",
    )
    multimask = File(
        desc="Multi-mask dataset -- each distinct nonzero value in dataset "
        "will be treated as a separate mask for blurring purposes.",
        argstr="-Mmask %s",
    )
    automask = traits.Bool(
        desc="Create an automask from the input dataset.", argstr="-automask"
    )
    fwhm = traits.Float(desc="fwhm kernel size", argstr="-FWHM %f", mandatory=True)
    preserve = traits.Bool(
        desc="Normally, voxels not in the mask will be set to zero in the "
        "output. If you want the original values in the dataset to be "
        "preserved in the output, use this option.",
        argstr="-preserve",
    )
    float_out = traits.Bool(
        desc="Save dataset as floats, no matter what the input data type is.",
        argstr="-float",
    )
    options = Str(desc="options", argstr="%s", position=2)


class BlurInMask(AFNICommand):
    """Blurs a dataset spatially inside a mask.  That's all.  Experimental.

    For complete details, see the `3dBlurInMask Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dBlurInMask.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> bim = afni.BlurInMask()
    >>> bim.inputs.in_file = 'functional.nii'
    >>> bim.inputs.mask = 'mask.nii'
    >>> bim.inputs.fwhm = 5.0
    >>> bim.cmdline  # doctest: +ELLIPSIS
    '3dBlurInMask -input functional.nii -FWHM 5.000000 -mask mask.nii -prefix functional_blur'
    >>> res = bim.run()  # doctest: +SKIP

    """

    _cmd = "3dBlurInMask"
    input_spec = BlurInMaskInputSpec
    output_spec = AFNICommandOutputSpec


class BlurToFWHMInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="The dataset that will be smoothed",
        argstr="-input %s",
        mandatory=True,
        exists=True,
    )
    automask = traits.Bool(
        desc="Create an automask from the input dataset.", argstr="-automask"
    )
    fwhm = traits.Float(
        desc="Blur until the 3D FWHM reaches this value (in mm)", argstr="-FWHM %f"
    )
    fwhmxy = traits.Float(
        desc="Blur until the 2D (x,y)-plane FWHM reaches this value (in mm)",
        argstr="-FWHMxy %f",
    )
    blurmaster = File(
        desc="The dataset whose smoothness controls the process.",
        argstr="-blurmaster %s",
        exists=True,
    )
    mask = File(
        desc="Mask dataset, if desired. Voxels NOT in mask will be set to zero "
        "in output.",
        argstr="-mask %s",
        exists=True,
    )


class BlurToFWHM(AFNICommand):
    """Blurs a 'master' dataset until it reaches a specified FWHM smoothness
    (approximately).

    For complete details, see the `3dBlurToFWHM Documentation
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dBlurToFWHM.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> blur = afni.preprocess.BlurToFWHM()
    >>> blur.inputs.in_file = 'epi.nii'
    >>> blur.inputs.fwhm = 2.5
    >>> blur.cmdline  # doctest: +ELLIPSIS
    '3dBlurToFWHM -FWHM 2.500000 -input epi.nii -prefix epi_afni'
    >>> res = blur.run()  # doctest: +SKIP

    """

    _cmd = "3dBlurToFWHM"
    input_spec = BlurToFWHMInputSpec
    output_spec = AFNICommandOutputSpec


class ClipLevelInputSpec(CommandLineInputSpec):
    in_file = File(
        desc="input file to 3dClipLevel",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
    )
    mfrac = traits.Float(
        desc="Use the number ff instead of 0.50 in the algorithm",
        argstr="-mfrac %s",
        position=2,
    )
    doall = traits.Bool(
        desc="Apply the algorithm to each sub-brick separately.",
        argstr="-doall",
        position=3,
        xor=("grad"),
    )
    grad = File(
        desc="Also compute a 'gradual' clip level as a function of voxel "
        "position, and output that to a dataset.",
        argstr="-grad %s",
        position=3,
        xor=("doall"),
    )


class ClipLevelOutputSpec(TraitedSpec):
    clip_val = traits.Float(desc="output")


class ClipLevel(AFNICommandBase):
    """Estimates the value at which to clip the anatomical dataset so
       that background regions are set to zero.

    For complete details, see the `3dClipLevel Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dClipLevel.html>`_

    Examples
    --------
    >>> from nipype.interfaces.afni import preprocess
    >>> cliplevel = preprocess.ClipLevel()
    >>> cliplevel.inputs.in_file = 'anatomical.nii'
    >>> cliplevel.cmdline
    '3dClipLevel anatomical.nii'
    >>> res = cliplevel.run()  # doctest: +SKIP

    """

    _cmd = "3dClipLevel"
    input_spec = ClipLevelInputSpec
    output_spec = ClipLevelOutputSpec

    def aggregate_outputs(self, runtime=None, needed_outputs=None):

        outputs = self._outputs()

        outfile = os.path.join(os.getcwd(), "stat_result.json")

        if runtime is None:
            try:
                clip_val = load_json(outfile)["stat"]
            except IOError:
                return self.run().outputs
        else:
            clip_val = []
            for line in runtime.stdout.split("\n"):
                if line:
                    values = line.split()
                    if len(values) > 1:
                        clip_val.append([float(val) for val in values])
                    else:
                        clip_val.extend([float(val) for val in values])

            if len(clip_val) == 1:
                clip_val = clip_val[0]
            save_json(outfile, dict(stat=clip_val))
        outputs.clip_val = clip_val

        return outputs


class DegreeCentralityInputSpec(CentralityInputSpec):
    """DegreeCentrality inputspec
    """

    in_file = File(
        desc="input file to 3dDegreeCentrality",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    sparsity = traits.Float(
        desc="only take the top percent of connections", argstr="-sparsity %f"
    )
    oned_file = Str(
        desc="output filepath to text dump of correlation matrix", argstr="-out1D %s"
    )


class DegreeCentralityOutputSpec(AFNICommandOutputSpec):
    """DegreeCentrality outputspec
    """

    oned_file = File(
        desc="The text output of the similarity matrix computed after "
        "thresholding with one-dimensional and ijk voxel indices, "
        "correlations, image extents, and affine matrix."
    )


class DegreeCentrality(AFNICommand):
    """Performs degree centrality on a dataset using a given maskfile
    via 3dDegreeCentrality

    For complete details, see the `3dDegreeCentrality Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDegreeCentrality.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> degree = afni.DegreeCentrality()
    >>> degree.inputs.in_file = 'functional.nii'
    >>> degree.inputs.mask = 'mask.nii'
    >>> degree.inputs.sparsity = 1 # keep the top one percent of connections
    >>> degree.inputs.out_file = 'out.nii'
    >>> degree.cmdline
    '3dDegreeCentrality -mask mask.nii -prefix out.nii -sparsity 1.000000 functional.nii'
    >>> res = degree.run()  # doctest: +SKIP

    """

    _cmd = "3dDegreeCentrality"
    input_spec = DegreeCentralityInputSpec
    output_spec = DegreeCentralityOutputSpec

    # Re-define generated inputs
    def _list_outputs(self):
        # Update outputs dictionary if oned file is defined
        outputs = super(DegreeCentrality, self)._list_outputs()
        if self.inputs.oned_file:
            outputs["oned_file"] = os.path.abspath(self.inputs.oned_file)

        return outputs


class DespikeInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dDespike",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_despike",
        desc="output image file name",
        argstr="-prefix %s",
        name_source="in_file",
    )


class Despike(AFNICommand):
    """Removes 'spikes' from the 3D+time input dataset

    For complete details, see the `3dDespike Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDespike.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> despike = afni.Despike()
    >>> despike.inputs.in_file = 'functional.nii'
    >>> despike.cmdline
    '3dDespike -prefix functional_despike functional.nii'
    >>> res = despike.run()  # doctest: +SKIP

    """

    _cmd = "3dDespike"
    input_spec = DespikeInputSpec
    output_spec = AFNICommandOutputSpec


class DetrendInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dDetrend",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_detrend",
        desc="output image file name",
        argstr="-prefix %s",
        name_source="in_file",
    )


class Detrend(AFNICommand):
    """This program removes components from voxel time series using
    linear least squares

    For complete details, see the `3dDetrend Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDetrend.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> detrend = afni.Detrend()
    >>> detrend.inputs.in_file = 'functional.nii'
    >>> detrend.inputs.args = '-polort 2'
    >>> detrend.inputs.outputtype = 'AFNI'
    >>> detrend.cmdline
    '3dDetrend -polort 2 -prefix functional_detrend functional.nii'
    >>> res = detrend.run()  # doctest: +SKIP

    """

    _cmd = "3dDetrend"
    input_spec = DetrendInputSpec
    output_spec = AFNICommandOutputSpec


class ECMInputSpec(CentralityInputSpec):
    """ECM inputspec
    """

    in_file = File(
        desc="input file to 3dECM",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    sparsity = traits.Float(
        desc="only take the top percent of connections", argstr="-sparsity %f"
    )
    full = traits.Bool(
        desc="Full power method; enables thresholding; automatically selected "
        "if -thresh or -sparsity are set",
        argstr="-full",
    )
    fecm = traits.Bool(
        desc="Fast centrality method; substantial speed increase but cannot "
        "accomodate thresholding; automatically selected if -thresh or "
        "-sparsity are not set",
        argstr="-fecm",
    )
    shift = traits.Float(
        desc="shift correlation coefficients in similarity matrix to enforce "
        "non-negativity, s >= 0.0; default = 0.0 for -full, 1.0 for -fecm",
        argstr="-shift %f",
    )
    scale = traits.Float(
        desc="scale correlation coefficients in similarity matrix to after "
        "shifting, x >= 0.0; default = 1.0 for -full, 0.5 for -fecm",
        argstr="-scale %f",
    )
    eps = traits.Float(
        desc="sets the stopping criterion for the power iteration; "
        ":math:`l2\\|v_\\text{old} - v_\\text{new}\\| < eps\\|v_\\text{old}\\|`; "
        "default = 0.001",
        argstr="-eps %f",
    )
    max_iter = traits.Int(
        desc="sets the maximum number of iterations to use in the power "
        "iteration; default = 1000",
        argstr="-max_iter %d",
    )
    memory = traits.Float(
        desc="Limit memory consumption on system by setting the amount of GB "
        "to limit the algorithm to; default = 2GB",
        argstr="-memory %f",
    )


class ECM(AFNICommand):
    """Performs degree centrality on a dataset using a given maskfile
    via the 3dECM command

    For complete details, see the `3dECM Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dECM.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> ecm = afni.ECM()
    >>> ecm.inputs.in_file = 'functional.nii'
    >>> ecm.inputs.mask = 'mask.nii'
    >>> ecm.inputs.sparsity = 0.1 # keep top 0.1% of connections
    >>> ecm.inputs.out_file = 'out.nii'
    >>> ecm.cmdline
    '3dECM -mask mask.nii -prefix out.nii -sparsity 0.100000 functional.nii'
    >>> res = ecm.run()  # doctest: +SKIP

    """

    _cmd = "3dECM"
    input_spec = ECMInputSpec
    output_spec = AFNICommandOutputSpec


class FimInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dfim+",
        argstr="-input %s",
        position=1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_fim",
        desc="output image file name",
        argstr="-bucket %s",
        name_source="in_file",
    )
    ideal_file = File(
        desc="ideal time series file name",
        argstr="-ideal_file %s",
        position=2,
        mandatory=True,
        exists=True,
    )
    fim_thr = traits.Float(
        desc="fim internal mask threshold value", argstr="-fim_thr %f", position=3
    )
    out = Str(
        desc="Flag to output the specified parameter", argstr="-out %s", position=4
    )


class Fim(AFNICommand):
    """Program to calculate the cross-correlation of an ideal reference
    waveform with the measured FMRI time series for each voxel.

    For complete details, see the `3dfim+ Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dfim+.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> fim = afni.Fim()
    >>> fim.inputs.in_file = 'functional.nii'
    >>> fim.inputs.ideal_file= 'seed.1D'
    >>> fim.inputs.out_file = 'functional_corr.nii'
    >>> fim.inputs.out = 'Correlation'
    >>> fim.inputs.fim_thr = 0.0009
    >>> fim.cmdline
    '3dfim+ -input functional.nii -ideal_file seed.1D -fim_thr 0.000900 -out Correlation -bucket functional_corr.nii'
    >>> res = fim.run()  # doctest: +SKIP

    """

    _cmd = "3dfim+"
    input_spec = FimInputSpec
    output_spec = AFNICommandOutputSpec


class FourierInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dFourier",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_fourier",
        desc="output image file name",
        argstr="-prefix %s",
        name_source="in_file",
    )
    lowpass = traits.Float(desc="lowpass", argstr="-lowpass %f", mandatory=True)
    highpass = traits.Float(desc="highpass", argstr="-highpass %f", mandatory=True)
    retrend = traits.Bool(
        desc="Any mean and linear trend are removed before filtering. This "
        "will restore the trend after filtering.",
        argstr="-retrend",
    )


class Fourier(AFNICommand):
    """Program to lowpass and/or highpass each voxel time series in a
    dataset, via the FFT

    For complete details, see the `3dFourier Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dFourier.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> fourier = afni.Fourier()
    >>> fourier.inputs.in_file = 'functional.nii'
    >>> fourier.inputs.retrend = True
    >>> fourier.inputs.highpass = 0.005
    >>> fourier.inputs.lowpass = 0.1
    >>> fourier.cmdline
    '3dFourier -highpass 0.005000 -lowpass 0.100000 -prefix functional_fourier -retrend functional.nii'
    >>> res = fourier.run()  # doctest: +SKIP

    """

    _cmd = "3dFourier"
    input_spec = FourierInputSpec
    output_spec = AFNICommandOutputSpec


class HistInputSpec(CommandLineInputSpec):
    in_file = File(
        desc="input file to 3dHist",
        argstr="-input %s",
        position=1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        desc="Write histogram to niml file with this prefix",
        name_template="%s_hist",
        keep_extension=False,
        argstr="-prefix %s",
        name_source=["in_file"],
    )
    showhist = traits.Bool(
        False, usedefault=True, desc="write a text visual histogram", argstr="-showhist"
    )
    out_show = File(
        name_template="%s_hist.out",
        desc="output image file name",
        keep_extension=False,
        argstr="> %s",
        name_source="in_file",
        position=-1,
    )
    mask = File(desc="matrix to align input file", argstr="-mask %s", exists=True)
    nbin = traits.Int(desc="number of bins", argstr="-nbin %d")
    max_value = traits.Float(argstr="-max %f", desc="maximum intensity value")
    min_value = traits.Float(argstr="-min %f", desc="minimum intensity value")
    bin_width = traits.Float(argstr="-binwidth %f", desc="bin width")


class HistOutputSpec(TraitedSpec):
    out_file = File(desc="output file", exists=True)
    out_show = File(desc="output visual histogram")


class Hist(AFNICommandBase):
    """Computes average of all voxels in the input dataset
    which satisfy the criterion in the options list

    For complete details, see the `3dHist Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dHist.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> hist = afni.Hist()
    >>> hist.inputs.in_file = 'functional.nii'
    >>> hist.cmdline
    '3dHist -input functional.nii -prefix functional_hist'
    >>> res = hist.run()  # doctest: +SKIP

    """

    _cmd = "3dHist"
    input_spec = HistInputSpec
    output_spec = HistOutputSpec
    _redirect_x = True

    def __init__(self, **inputs):
        super(Hist, self).__init__(**inputs)
        if not no_afni():
            version = Info.version()

            # As of AFNI 16.0.00, redirect_x is not needed
            if version[0] > 2015:
                self._redirect_x = False

    def _parse_inputs(self, skip=None):
        if not self.inputs.showhist:
            if skip is None:
                skip = []
            skip += ["out_show"]
        return super(Hist, self)._parse_inputs(skip=skip)

    def _list_outputs(self):
        outputs = super(Hist, self)._list_outputs()
        outputs["out_file"] += ".niml.hist"
        if not self.inputs.showhist:
            outputs["out_show"] = Undefined
        return outputs


class LFCDInputSpec(CentralityInputSpec):
    """LFCD inputspec
    """

    in_file = File(
        desc="input file to 3dLFCD",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )


class LFCD(AFNICommand):
    """Performs degree centrality on a dataset using a given maskfile
    via the 3dLFCD command

    For complete details, see the `3dLFCD Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dLFCD.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> lfcd = afni.LFCD()
    >>> lfcd.inputs.in_file = 'functional.nii'
    >>> lfcd.inputs.mask = 'mask.nii'
    >>> lfcd.inputs.thresh = 0.8 # keep all connections with corr >= 0.8
    >>> lfcd.inputs.out_file = 'out.nii'
    >>> lfcd.cmdline
    '3dLFCD -mask mask.nii -prefix out.nii -thresh 0.800000 functional.nii'
    >>> res = lfcd.run()  # doctest: +SKIP
    """

    _cmd = "3dLFCD"
    input_spec = LFCDInputSpec
    output_spec = AFNICommandOutputSpec


class MaskaveInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dmaskave",
        argstr="%s",
        position=-2,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_maskave.1D",
        desc="output image file name",
        keep_extension=True,
        argstr="> %s",
        name_source="in_file",
        position=-1,
    )
    mask = File(
        desc="matrix to align input file", argstr="-mask %s", position=1, exists=True
    )
    quiet = traits.Bool(desc="matrix to align input file", argstr="-quiet", position=2)


class Maskave(AFNICommand):
    """Computes average of all voxels in the input dataset
    which satisfy the criterion in the options list

    For complete details, see the `3dmaskave Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dmaskave.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> maskave = afni.Maskave()
    >>> maskave.inputs.in_file = 'functional.nii'
    >>> maskave.inputs.mask= 'seed_mask.nii'
    >>> maskave.inputs.quiet= True
    >>> maskave.cmdline  # doctest: +ELLIPSIS
    '3dmaskave -mask seed_mask.nii -quiet functional.nii > functional_maskave.1D'
    >>> res = maskave.run()  # doctest: +SKIP

    """

    _cmd = "3dmaskave"
    input_spec = MaskaveInputSpec
    output_spec = AFNICommandOutputSpec


class MeansInputSpec(AFNICommandInputSpec):
    in_file_a = File(
        desc="input file to 3dMean",
        argstr="%s",
        position=-2,
        mandatory=True,
        exists=True,
    )
    in_file_b = File(
        desc="another input file to 3dMean", argstr="%s", position=-1, exists=True
    )
    datum = traits.Str(
        desc="Sets the data type of the output dataset", argstr="-datum %s"
    )
    out_file = File(
        name_template="%s_mean",
        desc="output image file name",
        argstr="-prefix %s",
        name_source="in_file_a",
    )
    scale = Str(desc="scaling of output", argstr="-%sscale")
    non_zero = traits.Bool(desc="use only non-zero values", argstr="-non_zero")
    std_dev = traits.Bool(desc="calculate std dev", argstr="-stdev")
    sqr = traits.Bool(desc="mean square instead of value", argstr="-sqr")
    summ = traits.Bool(desc="take sum, (not average)", argstr="-sum")
    count = traits.Bool(desc="compute count of non-zero voxels", argstr="-count")
    mask_inter = traits.Bool(desc="create intersection mask", argstr="-mask_inter")
    mask_union = traits.Bool(desc="create union mask", argstr="-mask_union")


class Means(AFNICommand):
    """Takes the voxel-by-voxel mean of all input datasets using 3dMean

    For complete details, see the `3dMean Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dMean.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> means = afni.Means()
    >>> means.inputs.in_file_a = 'im1.nii'
    >>> means.inputs.in_file_b = 'im2.nii'
    >>> means.inputs.out_file =  'output.nii'
    >>> means.cmdline
    '3dMean -prefix output.nii im1.nii im2.nii'
    >>> res = means.run()  # doctest: +SKIP

    >>> from nipype.interfaces import afni
    >>> means = afni.Means()
    >>> means.inputs.in_file_a = 'im1.nii'
    >>> means.inputs.out_file =  'output.nii'
    >>> means.inputs.datum = 'short'
    >>> means.cmdline
    '3dMean -datum short -prefix output.nii im1.nii'
    >>> res = means.run()  # doctest: +SKIP

    """

    _cmd = "3dMean"
    input_spec = MeansInputSpec
    output_spec = AFNICommandOutputSpec


class OutlierCountInputSpec(CommandLineInputSpec):
    in_file = File(
        argstr="%s", mandatory=True, exists=True, position=-2, desc="input dataset"
    )
    mask = File(
        exists=True,
        argstr="-mask %s",
        xor=["autoclip", "automask"],
        desc="only count voxels within the given mask",
    )
    qthr = traits.Range(
        value=1e-3,
        low=0.0,
        high=1.0,
        usedefault=True,
        argstr="-qthr %.5f",
        desc="indicate a value for q to compute alpha",
    )
    autoclip = traits.Bool(
        False,
        usedefault=True,
        argstr="-autoclip",
        xor=["mask"],
        desc="clip off small voxels",
    )
    automask = traits.Bool(
        False,
        usedefault=True,
        argstr="-automask",
        xor=["mask"],
        desc="clip off small voxels",
    )
    fraction = traits.Bool(
        False,
        usedefault=True,
        argstr="-fraction",
        desc="write out the fraction of masked voxels which are outliers at "
        "each timepoint",
    )
    interval = traits.Bool(
        False,
        usedefault=True,
        argstr="-range",
        desc="write out the median + 3.5 MAD of outlier count with each timepoint",
    )
    save_outliers = traits.Bool(False, usedefault=True, desc="enables out_file option")
    outliers_file = File(
        name_template="%s_outliers",
        argstr="-save %s",
        name_source=["in_file"],
        output_name="out_outliers",
        keep_extension=True,
        desc="output image file name",
    )
    polort = traits.Int(
        argstr="-polort %d", desc="detrend each voxel timeseries with polynomials"
    )
    legendre = traits.Bool(
        False, usedefault=True, argstr="-legendre", desc="use Legendre polynomials"
    )
    out_file = File(
        name_template="%s_outliers",
        name_source=["in_file"],
        keep_extension=False,
        desc="capture standard output",
    )


class OutlierCountOutputSpec(TraitedSpec):
    out_outliers = File(exists=True, desc="output image file name")
    out_file = File(desc="capture standard output")


class OutlierCount(CommandLine):
    """Calculates number of 'outliers' at each time point of a
    a 3D+time dataset.

    For complete details, see the `3dToutcount Documentation
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dToutcount.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> toutcount = afni.OutlierCount()
    >>> toutcount.inputs.in_file = 'functional.nii'
    >>> toutcount.cmdline  # doctest: +ELLIPSIS
    '3dToutcount -qthr 0.00100 functional.nii'
    >>> res = toutcount.run()  # doctest: +SKIP

    """

    _cmd = "3dToutcount"
    input_spec = OutlierCountInputSpec
    output_spec = OutlierCountOutputSpec
    _terminal_output = "file_split"

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []

        # This is not strictly an input, but needs be
        # set before run() is called.
        if self.terminal_output == "none":
            self.terminal_output = "file_split"

        if not self.inputs.save_outliers:
            skip += ["outliers_file"]
        return super(OutlierCount, self)._parse_inputs(skip)

    def _run_interface(self, runtime, correct_return_codes=(0,)):
        runtime = super(OutlierCount, self)._run_interface(
            runtime, correct_return_codes
        )

        # Read from runtime.stdout or runtime.merged
        with open(op.abspath(self.inputs.out_file), "w") as outfh:
            outfh.write(runtime.stdout or runtime.merged)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        if self.inputs.save_outliers:
            outputs["out_outliers"] = op.abspath(self.inputs.outliers_file)
        return outputs


class QualityIndexInputSpec(CommandLineInputSpec):
    in_file = File(
        argstr="%s", mandatory=True, exists=True, position=-2, desc="input dataset"
    )
    mask = File(
        exists=True,
        argstr="-mask %s",
        xor=["autoclip", "automask"],
        desc="compute correlation only across masked voxels",
    )
    spearman = traits.Bool(
        False,
        usedefault=True,
        argstr="-spearman",
        desc="Quality index is 1 minus the Spearman (rank) correlation "
        "coefficient of each sub-brick with the median sub-brick. "
        "(default).",
    )
    quadrant = traits.Bool(
        False,
        usedefault=True,
        argstr="-quadrant",
        desc="Similar to -spearman, but using 1 minus the quadrant correlation "
        "coefficient as the quality index.",
    )
    autoclip = traits.Bool(
        False,
        usedefault=True,
        argstr="-autoclip",
        xor=["mask"],
        desc="clip off small voxels",
    )
    automask = traits.Bool(
        False,
        usedefault=True,
        argstr="-automask",
        xor=["mask"],
        desc="clip off small voxels",
    )
    clip = traits.Float(argstr="-clip %f", desc="clip off values below")
    interval = traits.Bool(
        False,
        usedefault=True,
        argstr="-range",
        desc="write out the median + 3.5 MAD of outlier count with each timepoint",
    )
    out_file = File(
        name_template="%s_tqual",
        name_source=["in_file"],
        argstr="> %s",
        keep_extension=False,
        position=-1,
        desc="capture standard output",
    )


class QualityIndexOutputSpec(TraitedSpec):
    out_file = File(desc="file containing the captured standard output")


class QualityIndex(CommandLine):
    """Computes a quality index for each sub-brick in a 3D+time dataset.
    The output is a 1D time series with the index for each sub-brick.
    The results are written to stdout.

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> tqual = afni.QualityIndex()
    >>> tqual.inputs.in_file = 'functional.nii'
    >>> tqual.cmdline  # doctest: +ELLIPSIS
    '3dTqual functional.nii > functional_tqual'
    >>> res = tqual.run()  # doctest: +SKIP

    See Also
    --------
    For complete details, see the `3dTqual Documentation
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTqual.html>`_

    """

    _cmd = "3dTqual"
    input_spec = QualityIndexInputSpec
    output_spec = QualityIndexOutputSpec


class ROIStatsInputSpec(CommandLineInputSpec):
    in_file = File(
        desc="input dataset", argstr="%s", position=-2, mandatory=True, exists=True
    )
    mask = File(
        desc="input mask",
        argstr="-mask %s",
        position=3,
        exists=True,
        deprecated="1.1.4",
        new_name="mask_file",
    )
    mask_file = File(desc="input mask", argstr="-mask %s", exists=True)
    mask_f2short = traits.Bool(
        desc="Tells the program to convert a float mask to short integers, "
        "by simple rounding.",
        argstr="-mask_f2short",
    )
    num_roi = traits.Int(
        desc="Forces the assumption that the mask dataset's ROIs are "
        "denoted by 1 to n inclusive.  Normally, the program "
        "figures out the ROIs on its own.  This option is "
        "useful if a) you are certain that the mask dataset "
        "has no values outside the range [0 n], b) there may "
        "be some ROIs missing between [1 n] in the mask data-"
        "set and c) you want those columns in the output any-"
        "way so the output lines up with the output from other "
        "invocations of 3dROIstats.",
        argstr="-numroi %s",
    )
    zerofill = traits.Str(
        requires=["num_roi"],
        desc="For ROI labels not found, use the provided string instead of "
        "a '0' in the output file. Only active if `num_roi` is "
        "enabled.",
        argstr="-zerofill %s",
    )
    roisel = File(
        exists=True,
        desc="Only considers ROIs denoted by values found in the specified "
        "file. Note that the order of the ROIs as specified in the file "
        "is not preserved. So an SEL.1D of '2 8 20' produces the same "
        "output as '8 20 2'",
        argstr="-roisel %s",
    )
    debug = traits.Bool(desc="print debug information", argstr="-debug")
    quiet = traits.Bool(desc="execute quietly", argstr="-quiet")
    nomeanout = traits.Bool(
        desc="Do not include the (zero-inclusive) mean among computed stats",
        argstr="-nomeanout",
    )
    nobriklab = traits.Bool(
        desc="Do not print the sub-brick label next to its index", argstr="-nobriklab"
    )
    format1D = traits.Bool(
        xor=["format1DR"],
        desc="Output results in a 1D format that includes commented labels",
        argstr="-1Dformat",
    )
    format1DR = traits.Bool(
        xor=["format1D"],
        desc="Output results in a 1D format that includes uncommented "
        "labels. May not work optimally with typical 1D functions, "
        "but is useful for R functions.",
        argstr="-1DRformat",
    )
    _stat_names = [
        "mean",
        "sum",
        "voxels",
        "minmax",
        "sigma",
        "median",
        "mode",
        "summary",
        "zerominmax",
        "zerosigma",
        "zeromedian",
        "zeromode",
    ]
    stat = InputMultiObject(
        traits.Enum(_stat_names),
        desc="""\
Statistics to compute. Options include:

 * mean       =   Compute the mean using only non_zero voxels.
                  Implies the opposite for the mean computed
                  by default.
 * median     =   Compute the median of nonzero voxels
 * mode       =   Compute the mode of nonzero voxels.
                  (integral valued sets only)
 * minmax     =   Compute the min/max of nonzero voxels
 * sum        =   Compute the sum using only nonzero voxels.
 * voxels     =   Compute the number of nonzero voxels
 * sigma      =   Compute the standard deviation of nonzero
                  voxels

Statistics that include zero-valued voxels:

 * zerominmax =   Compute the min/max of all voxels.
 * zerosigma  =   Compute the standard deviation of all
                  voxels.
 * zeromedian =   Compute the median of all voxels.
 * zeromode   =   Compute the mode of all voxels.
 * summary    =   Only output a summary line with the grand
                  mean across all briks in the input dataset.
                  This option cannot be used with nomeanout.

More that one option can be specified.""",
        argstr="%s...",
    )
    out_file = File(
        name_template="%s_roistat.1D",
        desc="output file",
        keep_extension=False,
        argstr="> %s",
        name_source="in_file",
        position=-1,
    )


class ROIStatsOutputSpec(TraitedSpec):
    out_file = File(desc="output tab-separated values file", exists=True)


class ROIStats(AFNICommandBase):
    """Display statistics over masked regions

    For complete details, see the `3dROIstats Documentation
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dROIstats.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> roistats = afni.ROIStats()
    >>> roistats.inputs.in_file = 'functional.nii'
    >>> roistats.inputs.mask_file = 'skeleton_mask.nii.gz'
    >>> roistats.inputs.stat = ['mean', 'median', 'voxels']
    >>> roistats.inputs.nomeanout = True
    >>> roistats.cmdline
    '3dROIstats -mask skeleton_mask.nii.gz -nomeanout -nzmean -nzmedian -nzvoxels functional.nii > functional_roistat.1D'
    >>> res = roistats.run()  # doctest: +SKIP

    """

    _cmd = "3dROIstats"
    _terminal_output = "allatonce"
    input_spec = ROIStatsInputSpec
    output_spec = ROIStatsOutputSpec

    def _format_arg(self, name, trait_spec, value):
        _stat_dict = {
            "mean": "-nzmean",
            "median": "-nzmedian",
            "mode": "-nzmode",
            "minmax": "-nzminmax",
            "sigma": "-nzsigma",
            "voxels": "-nzvoxels",
            "sum": "-nzsum",
            "summary": "-summary",
            "zerominmax": "-minmax",
            "zeromedian": "-median",
            "zerosigma": "-sigma",
            "zeromode": "-mode",
        }
        if name == "stat":
            value = [_stat_dict[v] for v in value]
        return super(ROIStats, self)._format_arg(name, trait_spec, value)


class RetroicorInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dretroicor",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_retroicor",
        name_source=["in_file"],
        desc="output image file name",
        argstr="-prefix %s",
        position=1,
    )
    card = File(
        desc="1D cardiac data file for cardiac correction",
        argstr="-card %s",
        position=-2,
        exists=True,
    )
    resp = File(
        desc="1D respiratory waveform data for correction",
        argstr="-resp %s",
        position=-3,
        exists=True,
    )
    threshold = traits.Int(
        desc="Threshold for detection of R-wave peaks in input (Make sure it "
        "is above the background noise level, Try 3/4 or 4/5 times range "
        "plus minimum)",
        argstr="-threshold %d",
        position=-4,
    )
    order = traits.Int(
        desc="The order of the correction (2 is typical)",
        argstr="-order %s",
        position=-5,
    )
    cardphase = File(
        desc="Filename for 1D cardiac phase output",
        argstr="-cardphase %s",
        position=-6,
        hash_files=False,
    )
    respphase = File(
        desc="Filename for 1D resp phase output",
        argstr="-respphase %s",
        position=-7,
        hash_files=False,
    )


class Retroicor(AFNICommand):
    """Performs Retrospective Image Correction for physiological
    motion effects, using a slightly modified version of the
    RETROICOR algorithm

    The durations of the physiological inputs are assumed to equal
    the duration of the dataset. Any constant sampling rate may be
    used, but 40 Hz seems to be acceptable. This program's cardiac
    peak detection algorithm is rather simplistic, so you might try
    using the scanner's cardiac gating output (transform it to a
    spike wave if necessary).

    This program uses slice timing information embedded in the
    dataset to estimate the proper cardiac/respiratory phase for
    each slice. It makes sense to run this program before any
    program that may destroy the slice timings (e.g. 3dvolreg for
    motion correction).

    For complete details, see the `3dretroicor Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dretroicor.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> ret = afni.Retroicor()
    >>> ret.inputs.in_file = 'functional.nii'
    >>> ret.inputs.card = 'mask.1D'
    >>> ret.inputs.resp = 'resp.1D'
    >>> ret.inputs.outputtype = 'NIFTI'
    >>> ret.cmdline
    '3dretroicor -prefix functional_retroicor.nii -resp resp.1D -card mask.1D functional.nii'
    >>> res = ret.run()  # doctest: +SKIP

    """

    _cmd = "3dretroicor"
    input_spec = RetroicorInputSpec
    output_spec = AFNICommandOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if name == "in_file":
            if not isdefined(self.inputs.card) and not isdefined(self.inputs.resp):
                return None
        return super(Retroicor, self)._format_arg(name, trait_spec, value)


class SegInputSpec(CommandLineInputSpec):
    in_file = File(
        desc="ANAT is the volume to segment",
        argstr="-anat %s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=True,
    )
    mask = traits.Either(
        traits.Enum("AUTO"),
        File(exists=True),
        desc="only non-zero voxels in mask are analyzed. mask can either be a "
        'dataset or the string "AUTO" which would use AFNI\'s automask '
        "function to create the mask.",
        argstr="-mask %s",
        position=-2,
        mandatory=True,
    )
    blur_meth = traits.Enum(
        "BFT",
        "BIM",
        argstr="-blur_meth %s",
        desc="set the blurring method for bias field estimation",
    )
    bias_fwhm = traits.Float(
        desc="The amount of blurring used when estimating the field bias with "
        "the Wells method",
        argstr="-bias_fwhm %f",
    )
    classes = Str(
        desc="CLASS_STRING is a semicolon delimited string of class labels",
        argstr="-classes %s",
    )
    bmrf = traits.Float(
        desc="Weighting factor controlling spatial homogeneity of the "
        "classifications",
        argstr="-bmrf %f",
    )
    bias_classes = Str(
        desc="A semicolon delimited string of classes that contribute to the "
        "estimation of the bias field",
        argstr="-bias_classes %s",
    )
    prefix = Str(
        desc="the prefix for the output folder containing all output volumes",
        argstr="-prefix %s",
    )
    mixfrac = Str(
        desc="MIXFRAC sets up the volume-wide (within mask) tissue fractions "
        "while initializing the segmentation (see IGNORE for exception)",
        argstr="-mixfrac %s",
    )
    mixfloor = traits.Float(
        desc="Set the minimum value for any class's mixing fraction",
        argstr="-mixfloor %f",
    )
    main_N = traits.Int(desc="Number of iterations to perform.", argstr="-main_N %d")


class Seg(AFNICommandBase):
    """3dSeg segments brain volumes into tissue classes. The program allows
    for adding a variety of global and voxelwise priors. However for the
    moment, only mixing fractions and MRF are documented.

    For complete details, see the `3dSeg Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dSeg.html>`_

    Examples
    --------
    >>> from nipype.interfaces.afni import preprocess
    >>> seg = preprocess.Seg()
    >>> seg.inputs.in_file = 'structural.nii'
    >>> seg.inputs.mask = 'AUTO'
    >>> seg.cmdline
    '3dSeg -mask AUTO -anat structural.nii'
    >>> res = seg.run()  # doctest: +SKIP

    """

    _cmd = "3dSeg"
    input_spec = SegInputSpec
    output_spec = AFNICommandOutputSpec

    def aggregate_outputs(self, runtime=None, needed_outputs=None):

        import glob

        outputs = self._outputs()

        if isdefined(self.inputs.prefix):
            outfile = os.path.join(os.getcwd(), self.inputs.prefix, "Classes+*.BRIK")
        else:
            outfile = os.path.join(os.getcwd(), "Segsy", "Classes+*.BRIK")

        outputs.out_file = glob.glob(outfile)[0]

        return outputs


class SkullStripInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dSkullStrip",
        argstr="-input %s",
        position=1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_skullstrip",
        desc="output image file name",
        argstr="-prefix %s",
        name_source="in_file",
    )


class SkullStrip(AFNICommand):
    """A program to extract the brain from surrounding tissue from MRI
    T1-weighted images.
    TODO Add optional arguments.

    For complete details, see the `3dSkullStrip Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dSkullStrip.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> skullstrip = afni.SkullStrip()
    >>> skullstrip.inputs.in_file = 'functional.nii'
    >>> skullstrip.inputs.args = '-o_ply'
    >>> skullstrip.cmdline
    '3dSkullStrip -input functional.nii -o_ply -prefix functional_skullstrip'
    >>> res = skullstrip.run()  # doctest: +SKIP

    """

    _cmd = "3dSkullStrip"
    _redirect_x = True
    input_spec = SkullStripInputSpec
    output_spec = AFNICommandOutputSpec

    def __init__(self, **inputs):
        super(SkullStrip, self).__init__(**inputs)

        if not no_afni():
            v = Info.version()

            # Between AFNI 16.0.00 and 16.2.07, redirect_x is not needed
            if v >= (2016, 0, 0) and v < (2016, 2, 7):
                self._redirect_x = False


class TCorr1DInputSpec(AFNICommandInputSpec):
    xset = File(
        desc="3d+time dataset input",
        argstr=" %s",
        position=-2,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    y_1d = File(
        desc="1D time series file input",
        argstr=" %s",
        position=-1,
        mandatory=True,
        exists=True,
    )
    out_file = File(
        desc="output filename prefix",
        name_template="%s_correlation.nii.gz",
        argstr="-prefix %s",
        name_source="xset",
        keep_extension=True,
    )
    pearson = traits.Bool(
        desc="Correlation is the normal Pearson correlation coefficient",
        argstr=" -pearson",
        xor=["spearman", "quadrant", "ktaub"],
        position=1,
    )
    spearman = traits.Bool(
        desc="Correlation is the Spearman (rank) correlation coefficient",
        argstr=" -spearman",
        xor=["pearson", "quadrant", "ktaub"],
        position=1,
    )
    quadrant = traits.Bool(
        desc="Correlation is the quadrant correlation coefficient",
        argstr=" -quadrant",
        xor=["pearson", "spearman", "ktaub"],
        position=1,
    )
    ktaub = traits.Bool(
        desc="Correlation is the Kendall's tau_b correlation coefficient",
        argstr=" -ktaub",
        xor=["pearson", "spearman", "quadrant"],
        position=1,
    )


class TCorr1DOutputSpec(TraitedSpec):
    out_file = File(desc="output file containing correlations", exists=True)


class TCorr1D(AFNICommand):
    """Computes the correlation coefficient between each voxel time series
    in the input 3D+time dataset.

    For complete details, see the `3dTcorr1D Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTcorr1D.html>`_

    >>> from nipype.interfaces import afni
    >>> tcorr1D = afni.TCorr1D()
    >>> tcorr1D.inputs.xset= 'u_rc1s1_Template.nii'
    >>> tcorr1D.inputs.y_1d = 'seed.1D'
    >>> tcorr1D.cmdline
    '3dTcorr1D -prefix u_rc1s1_Template_correlation.nii.gz  u_rc1s1_Template.nii  seed.1D'
    >>> res = tcorr1D.run()  # doctest: +SKIP

    """

    _cmd = "3dTcorr1D"
    input_spec = TCorr1DInputSpec
    output_spec = TCorr1DOutputSpec


class TCorrMapInputSpec(AFNICommandInputSpec):
    in_file = File(exists=True, argstr="-input %s", mandatory=True, copyfile=False)
    seeds = File(exists=True, argstr="-seed %s", xor=("seeds_width"))
    mask = File(exists=True, argstr="-mask %s")
    automask = traits.Bool(argstr="-automask")
    polort = traits.Int(argstr="-polort %d")
    bandpass = traits.Tuple((traits.Float(), traits.Float()), argstr="-bpass %f %f")
    regress_out_timeseries = File(exists=True, argstr="-ort %s")
    blur_fwhm = traits.Float(argstr="-Gblur %f")
    seeds_width = traits.Float(argstr="-Mseed %f", xor=("seeds"))

    # outputs
    mean_file = File(argstr="-Mean %s", suffix="_mean", name_source="in_file")
    zmean = File(argstr="-Zmean %s", suffix="_zmean", name_source="in_file")
    qmean = File(argstr="-Qmean %s", suffix="_qmean", name_source="in_file")
    pmean = File(argstr="-Pmean %s", suffix="_pmean", name_source="in_file")

    _thresh_opts = (
        "absolute_threshold",
        "var_absolute_threshold",
        "var_absolute_threshold_normalize",
    )
    thresholds = traits.List(traits.Int())
    absolute_threshold = File(
        argstr="-Thresh %f %s",
        suffix="_thresh",
        name_source="in_file",
        xor=_thresh_opts,
    )
    var_absolute_threshold = File(
        argstr="-VarThresh %f %f %f %s",
        suffix="_varthresh",
        name_source="in_file",
        xor=_thresh_opts,
    )
    var_absolute_threshold_normalize = File(
        argstr="-VarThreshN %f %f %f %s",
        suffix="_varthreshn",
        name_source="in_file",
        xor=_thresh_opts,
    )

    correlation_maps = File(argstr="-CorrMap %s", name_source="in_file")
    correlation_maps_masked = File(argstr="-CorrMask %s", name_source="in_file")

    _expr_opts = ("average_expr", "average_expr_nonzero", "sum_expr")
    expr = Str()
    average_expr = File(
        argstr="-Aexpr %s %s", suffix="_aexpr", name_source="in_file", xor=_expr_opts
    )
    average_expr_nonzero = File(
        argstr="-Cexpr %s %s", suffix="_cexpr", name_source="in_file", xor=_expr_opts
    )
    sum_expr = File(
        argstr="-Sexpr %s %s", suffix="_sexpr", name_source="in_file", xor=_expr_opts
    )
    histogram_bin_numbers = traits.Int()
    histogram = File(name_source="in_file", argstr="-Hist %d %s", suffix="_hist")


class TCorrMapOutputSpec(TraitedSpec):
    mean_file = File()
    zmean = File()
    qmean = File()
    pmean = File()
    absolute_threshold = File()
    var_absolute_threshold = File()
    var_absolute_threshold_normalize = File()
    correlation_maps = File()
    correlation_maps_masked = File()
    average_expr = File()
    average_expr_nonzero = File()
    sum_expr = File()
    histogram = File()


class TCorrMap(AFNICommand):
    """For each voxel time series, computes the correlation between it
    and all other voxels, and combines this set of values into the
    output dataset(s) in some way.

    For complete details, see the `3dTcorrMap Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTcorrMap.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> tcm = afni.TCorrMap()
    >>> tcm.inputs.in_file = 'functional.nii'
    >>> tcm.inputs.mask = 'mask.nii'
    >>> tcm.mean_file = 'functional_meancorr.nii'
    >>> tcm.cmdline # doctest: +SKIP
    '3dTcorrMap -input functional.nii -mask mask.nii -Mean functional_meancorr.nii'
    >>> res = tcm.run()  # doctest: +SKIP

    """

    _cmd = "3dTcorrMap"
    input_spec = TCorrMapInputSpec
    output_spec = TCorrMapOutputSpec
    _additional_metadata = ["suffix"]

    def _format_arg(self, name, trait_spec, value):
        if name in self.inputs._thresh_opts:
            return trait_spec.argstr % self.inputs.thresholds + [value]
        elif name in self.inputs._expr_opts:
            return trait_spec.argstr % (self.inputs.expr, value)
        elif name == "histogram":
            return trait_spec.argstr % (self.inputs.histogram_bin_numbers, value)
        else:
            return super(TCorrMap, self)._format_arg(name, trait_spec, value)


class TCorrelateInputSpec(AFNICommandInputSpec):
    xset = File(
        desc="input xset",
        argstr="%s",
        position=-2,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    yset = File(
        desc="input yset",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_tcorr",
        desc="output image file name",
        argstr="-prefix %s",
        name_source="xset",
    )
    pearson = traits.Bool(
        desc="Correlation is the normal Pearson correlation coefficient",
        argstr="-pearson",
    )
    polort = traits.Int(desc="Remove polynomical trend of order m", argstr="-polort %d")


class TCorrelate(AFNICommand):
    """Computes the correlation coefficient between corresponding voxel
    time series in two input 3D+time datasets 'xset' and 'yset'

    For complete details, see the `3dTcorrelate Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTcorrelate.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> tcorrelate = afni.TCorrelate()
    >>> tcorrelate.inputs.xset= 'u_rc1s1_Template.nii'
    >>> tcorrelate.inputs.yset = 'u_rc1s2_Template.nii'
    >>> tcorrelate.inputs.out_file = 'functional_tcorrelate.nii.gz'
    >>> tcorrelate.inputs.polort = -1
    >>> tcorrelate.inputs.pearson = True
    >>> tcorrelate.cmdline
    '3dTcorrelate -prefix functional_tcorrelate.nii.gz -pearson -polort -1 u_rc1s1_Template.nii u_rc1s2_Template.nii'
    >>> res = tcarrelate.run()  # doctest: +SKIP

    """

    _cmd = "3dTcorrelate"
    input_spec = TCorrelateInputSpec
    output_spec = AFNICommandOutputSpec


class TNormInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dTNorm",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_tnorm",
        desc="output image file name",
        argstr="-prefix %s",
        name_source="in_file",
    )
    norm2 = traits.Bool(
        desc="L2 normalize (sum of squares = 1) [DEFAULT]", argstr="-norm2"
    )
    normR = traits.Bool(
        desc="normalize so sum of squares = number of time points \\* e.g., so RMS = 1.",
        argstr="-normR",
    )
    norm1 = traits.Bool(
        desc="L1 normalize (sum of absolute values = 1)", argstr="-norm1"
    )
    normx = traits.Bool(
        desc="Scale so max absolute value = 1 (L_infinity norm)", argstr="-normx"
    )
    polort = traits.Int(
        desc="""\
Detrend with polynomials of order p before normalizing [DEFAULT = don't do this].
Use '-polort 0' to remove the mean, for example""",
        argstr="-polort %s",
    )
    L1fit = traits.Bool(
        desc="""\
Detrend with L1 regression (L2 is the default)
This option is here just for the hell of it""",
        argstr="-L1fit",
    )


class TNorm(AFNICommand):
    """Shifts voxel time series from input so that separate slices are aligned
    to the same temporal origin.

    For complete details, see the `3dTnorm Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTnorm.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> tnorm = afni.TNorm()
    >>> tnorm.inputs.in_file = 'functional.nii'
    >>> tnorm.inputs.norm2 = True
    >>> tnorm.inputs.out_file = 'rm.errts.unit errts+tlrc'
    >>> tnorm.cmdline
    '3dTnorm -norm2 -prefix rm.errts.unit errts+tlrc functional.nii'
    >>> res = tshift.run()  # doctest: +SKIP

    """

    _cmd = "3dTnorm"
    input_spec = TNormInputSpec
    output_spec = AFNICommandOutputSpec


class TProjectInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dTproject",
        argstr="-input %s",
        position=1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_tproject",
        desc="output image file name",
        position=-1,
        argstr="-prefix %s",
        name_source="in_file",
    )
    censor = File(
        desc="""\
Filename of censor .1D time series.
This is a file of 1s and 0s, indicating which
time points are to be included (1) and which are
to be excluded (0).""",
        argstr="-censor %s",
        exists=True,
    )
    censortr = traits.List(
        traits.Str(),
        desc="""\
List of strings that specify time indexes
to be removed from the analysis.  Each string is
of one of the following forms:

* ``37`` => remove global time index #37
* ``2:37`` => remove time index #37 in run #2
* ``37..47`` => remove global time indexes #37-47
* ``37-47`` => same as above
* ``2:37..47`` => remove time indexes #37-47 in run #2
* ``*:0-2`` => remove time indexes #0-2 in all runs

  * Time indexes within each run start at 0.
  * Run indexes start at 1 (just be to confusing).
  * N.B.: 2:37,47 means index #37 in run #2 and
    global time index 47; it does NOT mean
    index #37 in run #2 AND index #47 in run #2.

""",
        argstr="-CENSORTR %s",
    )
    cenmode = traits.Enum(
        "KILL",
        "ZERO",
        "NTRP",
        desc="""\
Specifies how censored time points are treated in
the output dataset:

* mode = ZERO -- put zero values in their place;
  output datset is same length as input
* mode = KILL -- remove those time points;
  output dataset is shorter than input
* mode = NTRP -- censored values are replaced by interpolated
  neighboring (in time) non-censored values,
  BEFORE any projections, and then the
  analysis proceeds without actual removal
  of any time points -- this feature is to
  keep the Spanish Inquisition happy.
* The default mode is KILL !!!

""",
        argstr="-cenmode %s",
    )
    concat = File(
        desc="""\
The catenation file, as in 3dDeconvolve, containing the
TR indexes of the start points for each contiguous run
within the input dataset (the first entry should be 0).

* Also as in 3dDeconvolve, if the input dataset is
  automatically catenated from a collection of datasets,
  then the run start indexes are determined directly,
  and '-concat' is not needed (and will be ignored).
* Each run must have at least 9 time points AFTER
  censoring, or the program will not work!
* The only use made of this input is in setting up
  the bandpass/stopband regressors.
* '-ort' and '-dsort' regressors run through all time
  points, as read in.  If you want separate projections
  in each run, then you must either break these ort files
  into appropriate components, OR you must run 3dTproject
  for each run separately, using the appropriate pieces
  from the ort files via the ``{...}`` selector for the
  1D files and the ``[...]`` selector for the datasets.

""",
        exists=True,
        argstr="-concat %s",
    )
    noblock = traits.Bool(
        desc="""\
Also as in 3dDeconvolve, if you want the program to treat
an auto-catenated dataset as one long run, use this option.
However, '-noblock' will not affect catenation if you use
the '-concat' option.""",
        argstr="-noblock",
    )
    ort = File(
        desc="""\
Remove each column in file.
Each column will have its mean removed.""",
        exists=True,
        argstr="-ort %s",
    )
    polort = traits.Int(
        desc="""\
Remove polynomials up to and including degree pp.

* Default value is 2.
* It makes no sense to use a value of pp greater than
  2, if you are bandpassing out the lower frequencies!
* For catenated datasets, each run gets a separate set
  set of pp+1 Legendre polynomial regressors.
* Use of -polort -1 is not advised (if data mean != 0),
  even if -ort contains constant terms, as all means are
  removed.

""",
        argstr="-polort %d",
    )
    dsort = InputMultiObject(
        File(exists=True, copyfile=False),
        argstr="-dsort %s...",
        desc="""\
Remove the 3D+time time series in dataset fset.

* That is, 'fset' contains a different nuisance time
  series for each voxel (e.g., from AnatICOR).
* Multiple -dsort options are allowed.

""",
    )
    bandpass = traits.Tuple(
        traits.Float,
        traits.Float,
        desc="""Remove all frequencies EXCEPT those in the range""",
        argstr="-bandpass %g %g",
    )
    stopband = traits.Tuple(
        traits.Float,
        traits.Float,
        desc="""Remove all frequencies in the range""",
        argstr="-stopband %g %g",
    )
    TR = traits.Float(
        desc="""\
Use time step dd for the frequency calculations,
rather than the value stored in the dataset header.""",
        argstr="-TR %g",
    )
    mask = File(
        exists=True,
        desc="""\
Only operate on voxels nonzero in the mset dataset.

* Voxels outside the mask will be filled with zeros.
* If no masking option is given, then all voxels
  will be processed.

""",
        argstr="-mask %s",
    )
    automask = traits.Bool(
        desc="""Generate a mask automatically""", xor=["mask"], argstr="-automask"
    )
    blur = traits.Float(
        desc="""\
Blur (inside the mask only) with a filter that has
width (FWHM) of fff millimeters.
Spatial blurring (if done) is after the time
series filtering.""",
        argstr="-blur %g",
    )
    norm = traits.Bool(
        desc="""
Normalize each output time series to have sum of
squares = 1. This is the LAST operation.""",
        argstr="-norm",
    )


class TProject(AFNICommand):
    """
    This program projects (detrends) out various 'nuisance' time series from
    each voxel in the input dataset.  Note that all the projections are done
    via linear regression, including the frequency-based options such
    as ``-passband``.  In this way, you can bandpass time-censored data, and at
    the same time, remove other time series of no interest
    (e.g., physiological estimates, motion parameters).
    Shifts voxel time series from input so that seperate slices are aligned to
    the same temporal origin.

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> tproject = afni.TProject()
    >>> tproject.inputs.in_file = 'functional.nii'
    >>> tproject.inputs.bandpass = (0.00667, 99999)
    >>> tproject.inputs.polort = 3
    >>> tproject.inputs.automask = True
    >>> tproject.inputs.out_file = 'projected.nii.gz'
    >>> tproject.cmdline
    '3dTproject -input functional.nii -automask -bandpass 0.00667 99999 -polort 3 -prefix projected.nii.gz'
    >>> res = tproject.run()  # doctest: +SKIP

    See Also
    --------
    For complete details, see the `3dTproject Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTproject.html>`__

    """

    _cmd = "3dTproject"
    input_spec = TProjectInputSpec
    output_spec = AFNICommandOutputSpec


class TShiftInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dTshift",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_tshift",
        desc="output image file name",
        argstr="-prefix %s",
        name_source="in_file",
    )
    tr = Str(
        desc='manually set the TR. You can attach suffix "s" for seconds '
        'or "ms" for milliseconds.',
        argstr="-TR %s",
    )
    tzero = traits.Float(
        desc="align each slice to given time offset", argstr="-tzero %s", xor=["tslice"]
    )
    tslice = traits.Int(
        desc="align each slice to time offset of given slice",
        argstr="-slice %s",
        xor=["tzero"],
    )
    ignore = traits.Int(
        desc="ignore the first set of points specified", argstr="-ignore %s"
    )
    interp = traits.Enum(
        ("Fourier", "linear", "cubic", "quintic", "heptic"),
        desc="different interpolation methods (see 3dTshift for details) "
        "default = Fourier",
        argstr="-%s",
    )
    tpattern = traits.Either(
        traits.Enum(
            "alt+z",
            "altplus",  # Synonyms
            "alt+z2",
            "alt-z",
            "altminus",  # Synonyms
            "alt-z2",
            "seq+z",
            "seqplus",  # Synonyms
            "seq-z",
            "seqminus",
        ),  # Synonyms
        Str,  # For backwards compatibility
        desc="use specified slice time pattern rather than one in header",
        argstr="-tpattern %s",
        xor=["slice_timing"],
    )
    slice_timing = traits.Either(
        File(exists=True),
        traits.List(traits.Float),
        desc="time offsets from the volume acquisition onset for each slice",
        argstr="-tpattern @%s",
        xor=["tpattern"],
    )
    slice_encoding_direction = traits.Enum(
        "k",
        "k-",
        usedefault=True,
        desc="Direction in which slice_timing is specified (default: k). If negative,"
        "slice_timing is defined in reverse order, that is, the first entry "
        "corresponds to the slice with the largest index, and the final entry "
        "corresponds to slice index zero. Only in effect when slice_timing is "
        "passed as list, not when it is passed as file.",
    )
    rlt = traits.Bool(
        desc="Before shifting, remove the mean and linear trend", argstr="-rlt"
    )
    rltplus = traits.Bool(
        desc="Before shifting, remove the mean and linear trend and later put "
        "back the mean",
        argstr="-rlt+",
    )


class TShiftOutputSpec(AFNICommandOutputSpec):
    timing_file = File(desc="AFNI formatted timing file, if ``slice_timing`` is a list")


class TShift(AFNICommand):
    """Shifts voxel time series from input so that seperate slices are aligned
    to the same temporal origin.

    For complete details, see the `3dTshift Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTshift.html>`_

    Examples
    --------
    Slice timing details may be specified explicitly via the ``slice_timing``
    input:

    >>> from nipype.interfaces import afni
    >>> TR = 2.5
    >>> tshift = afni.TShift()
    >>> tshift.inputs.in_file = 'functional.nii'
    >>> tshift.inputs.tzero = 0.0
    >>> tshift.inputs.tr = '%.1fs' % TR
    >>> tshift.inputs.slice_timing = list(np.arange(40) / TR)
    >>> tshift.cmdline
    '3dTshift -prefix functional_tshift -tpattern @slice_timing.1D -TR 2.5s -tzero 0.0 functional.nii'

    When the ``slice_timing`` input is used, the ``timing_file`` output is populated,
    in this case with the generated file.

    >>> tshift._list_outputs()['timing_file']  # doctest: +ELLIPSIS
    '.../slice_timing.1D'

    >>> np.loadtxt(tshift._list_outputs()['timing_file']).tolist()[:5]
    [0.0, 0.4, 0.8, 1.2, 1.6]

    If ``slice_encoding_direction`` is set to ``'k-'``, the slice timing is reversed:

    >>> tshift.inputs.slice_encoding_direction = 'k-'
    >>> tshift.cmdline
    '3dTshift -prefix functional_tshift -tpattern @slice_timing.1D -TR 2.5s -tzero 0.0 functional.nii'
    >>> np.loadtxt(tshift._list_outputs()['timing_file']).tolist()[:5]
    [15.6, 15.2, 14.8, 14.4, 14.0]

    This method creates a ``slice_timing.1D`` file to be passed to ``3dTshift``.
    A pre-existing slice-timing file may be used in the same way:

    >>> tshift = afni.TShift()
    >>> tshift.inputs.in_file = 'functional.nii'
    >>> tshift.inputs.tzero = 0.0
    >>> tshift.inputs.tr = '%.1fs' % TR
    >>> tshift.inputs.slice_timing = 'slice_timing.1D'
    >>> tshift.cmdline
    '3dTshift -prefix functional_tshift -tpattern @slice_timing.1D -TR 2.5s -tzero 0.0 functional.nii'

    When a pre-existing file is provided, ``timing_file`` is simply passed through.

    >>> tshift._list_outputs()['timing_file']  # doctest: +ELLIPSIS
    '.../slice_timing.1D'

    Alternatively, pre-specified slice timing patterns may be specified with the
    ``tpattern`` input.
    For example, to specify an alternating, ascending slice timing pattern:

    >>> tshift = afni.TShift()
    >>> tshift.inputs.in_file = 'functional.nii'
    >>> tshift.inputs.tzero = 0.0
    >>> tshift.inputs.tr = '%.1fs' % TR
    >>> tshift.inputs.tpattern = 'alt+z'
    >>> tshift.cmdline
    '3dTshift -prefix functional_tshift -tpattern alt+z -TR 2.5s -tzero 0.0 functional.nii'

    For backwards compatibility, ``tpattern`` may also take filenames prefixed
    with ``@``.
    However, in this case, filenames are not validated, so this usage will be
    deprecated in future versions of Nipype.

    >>> tshift = afni.TShift()
    >>> tshift.inputs.in_file = 'functional.nii'
    >>> tshift.inputs.tzero = 0.0
    >>> tshift.inputs.tr = '%.1fs' % TR
    >>> tshift.inputs.tpattern = '@slice_timing.1D'
    >>> tshift.cmdline
    '3dTshift -prefix functional_tshift -tpattern @slice_timing.1D -TR 2.5s -tzero 0.0 functional.nii'

    In these cases, ``timing_file`` is undefined.

    >>> tshift._list_outputs()['timing_file']  # doctest: +ELLIPSIS
    <undefined>

    In any configuration, the interface may be run as usual:

    >>> res = tshift.run()  # doctest: +SKIP
    """

    _cmd = "3dTshift"
    input_spec = TShiftInputSpec
    output_spec = TShiftOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if name == "tpattern" and value.startswith("@"):
            iflogger.warning(
                'Passing a file prefixed by "@" will be deprecated'
                "; please use the `slice_timing` input"
            )
        elif name == "slice_timing" and isinstance(value, list):
            value = self._write_slice_timing()
        return super(TShift, self)._format_arg(name, trait_spec, value)

    def _write_slice_timing(self):
        slice_timing = list(self.inputs.slice_timing)
        if self.inputs.slice_encoding_direction.endswith("-"):
            slice_timing.reverse()

        fname = "slice_timing.1D"
        with open(fname, "w") as fobj:
            fobj.write("\t".join(map(str, slice_timing)))
        return fname

    def _list_outputs(self):
        outputs = super(TShift, self)._list_outputs()
        if isdefined(self.inputs.slice_timing):
            if isinstance(self.inputs.slice_timing, list):
                outputs["timing_file"] = os.path.abspath("slice_timing.1D")
            else:
                outputs["timing_file"] = os.path.abspath(self.inputs.slice_timing)
        return outputs


class TSmoothInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dTSmooth",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_smooth",
        desc="output file from 3dTSmooth",
        argstr="-prefix %s",
        name_source="in_file",
    )
    datum = traits.Str(
        desc="Sets the data type of the output dataset", argstr="-datum %s"
    )
    lin = traits.Bool(
        desc=r"3 point linear filter: :math:`0.15\,a + 0.70\,b + 0.15\,c`"
        " [This is the default smoother]",
        argstr="-lin",
    )
    med = traits.Bool(desc="3 point median filter: median(a,b,c)", argstr="-med")
    osf = traits.Bool(
        desc="3 point order statistics filter:"
        r":math:`0.15\,min(a,b,c) + 0.70\,median(a,b,c) + 0.15\,max(a,b,c)`",
        argstr="-osf",
    )
    lin3 = traits.Int(
        desc=r"3 point linear filter: :math:`0.5\,(1-m)\,a + m\,b + 0.5\,(1-m)\,c`. "
        "Here, 'm' is a number strictly between 0 and 1.",
        argstr="-3lin %d",
    )
    hamming = traits.Int(
        argstr="-hamming %d",
        desc="Use N point Hamming windows. (N must be odd and bigger than 1.)",
    )
    blackman = traits.Int(
        argstr="-blackman %d",
        desc="Use N point Blackman windows. (N must be odd and bigger than 1.)",
    )
    custom = File(
        argstr="-custom %s",
        desc="odd # of coefficients must be in a single column in ASCII file",
    )
    adaptive = traits.Int(
        argstr="-adaptive %d",
        desc="use adaptive mean filtering of width N "
        "(where N must be odd and bigger than 3).",
    )


class TSmooth(AFNICommand):
    """Smooths each voxel time series in a 3D+time dataset and produces
    as output a new 3D+time dataset (e.g., lowpass filter in time).

    For complete details, see the `3dTsmooth Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTSmooth.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> from nipype.testing import  example_data
    >>> smooth = afni.TSmooth()
    >>> smooth.inputs.in_file = 'functional.nii'
    >>> smooth.inputs.adaptive = 5
    >>> smooth.cmdline
    '3dTsmooth -adaptive 5 -prefix functional_smooth functional.nii'
    >>> res = smooth.run()  # doctest: +SKIP

    """

    _cmd = "3dTsmooth"
    input_spec = TSmoothInputSpec
    output_spec = AFNICommandOutputSpec


class VolregInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dvolreg",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    in_weight_volume = traits.Either(
        traits.Tuple(File(exists=True), traits.Int),
        File(exists=True),
        desc="weights for each voxel specified by a file with an "
        "optional volume number (defaults to 0)",
        argstr="-weight '%s[%d]'",
    )
    out_file = File(
        name_template="%s_volreg",
        desc="output image file name",
        argstr="-prefix %s",
        name_source="in_file",
    )
    basefile = File(
        desc="base file for registration", argstr="-base %s", position=-6, exists=True
    )
    zpad = traits.Int(
        desc="Zeropad around the edges by 'n' voxels during rotations",
        argstr="-zpad %d",
        position=-5,
    )
    md1d_file = File(
        name_template="%s_md.1D",
        desc="max displacement output file",
        argstr="-maxdisp1D %s",
        name_source="in_file",
        keep_extension=True,
        position=-4,
    )
    oned_file = File(
        name_template="%s.1D",
        desc="1D movement parameters output file",
        argstr="-1Dfile %s",
        name_source="in_file",
        keep_extension=True,
    )
    verbose = traits.Bool(
        desc="more detailed description of the process", argstr="-verbose"
    )
    timeshift = traits.Bool(
        desc="time shift to mean slice time offset", argstr="-tshift 0"
    )
    copyorigin = traits.Bool(
        desc="copy base file origin coords to output", argstr="-twodup"
    )
    oned_matrix_save = File(
        name_template="%s.aff12.1D",
        desc="Save the matrix transformation",
        argstr="-1Dmatrix_save %s",
        keep_extension=True,
        name_source="in_file",
    )
    interp = traits.Enum(
        ("Fourier", "cubic", "heptic", "quintic", "linear"),
        desc="spatial interpolation methods [default = heptic]",
        argstr="-%s",
    )


class VolregOutputSpec(TraitedSpec):
    out_file = File(desc="registered file", exists=True)
    md1d_file = File(desc="max displacement info file", exists=True)
    oned_file = File(desc="movement parameters info file", exists=True)
    oned_matrix_save = File(
        desc="matrix transformation from base to input", exists=True
    )


class Volreg(AFNICommand):
    """Register input volumes to a base volume using AFNI 3dvolreg command

    For complete details, see the `3dvolreg Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dvolreg.html>`_

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> volreg = afni.Volreg()
    >>> volreg.inputs.in_file = 'functional.nii'
    >>> volreg.inputs.args = '-Fourier -twopass'
    >>> volreg.inputs.zpad = 4
    >>> volreg.inputs.outputtype = 'NIFTI'
    >>> volreg.cmdline  # doctest: +ELLIPSIS
    '3dvolreg -Fourier -twopass -1Dfile functional.1D -1Dmatrix_save functional.aff12.1D -prefix \
functional_volreg.nii -zpad 4 -maxdisp1D functional_md.1D functional.nii'
    >>> res = volreg.run()  # doctest: +SKIP

    >>> from nipype.interfaces import afni
    >>> volreg = afni.Volreg()
    >>> volreg.inputs.in_file = 'functional.nii'
    >>> volreg.inputs.interp = 'cubic'
    >>> volreg.inputs.verbose = True
    >>> volreg.inputs.zpad = 1
    >>> volreg.inputs.basefile = 'functional.nii'
    >>> volreg.inputs.out_file = 'rm.epi.volreg.r1'
    >>> volreg.inputs.oned_file = 'dfile.r1.1D'
    >>> volreg.inputs.oned_matrix_save = 'mat.r1.tshift+orig.1D'
    >>> volreg.cmdline
    '3dvolreg -cubic -1Dfile dfile.r1.1D -1Dmatrix_save mat.r1.tshift+orig.1D -prefix \
rm.epi.volreg.r1 -verbose -base functional.nii -zpad 1 -maxdisp1D functional_md.1D functional.nii'
    >>> res = volreg.run()  # doctest: +SKIP

    """

    _cmd = "3dvolreg"
    input_spec = VolregInputSpec
    output_spec = VolregOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if name == "in_weight_volume" and not isinstance(value, tuple):
            value = (value, 0)
        return super(Volreg, self)._format_arg(name, trait_spec, value)


class WarpInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="input file to 3dWarp",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_warp",
        desc="output image file name",
        argstr="-prefix %s",
        name_source="in_file",
        keep_extension=True,
    )
    tta2mni = traits.Bool(
        desc="transform dataset from Talairach to MNI152", argstr="-tta2mni"
    )
    mni2tta = traits.Bool(
        desc="transform dataset from MNI152 to Talaraich", argstr="-mni2tta"
    )
    matparent = File(
        desc="apply transformation from 3dWarpDrive",
        argstr="-matparent %s",
        exists=True,
    )
    oblique_parent = File(
        desc="Read in the oblique transformation matrix from an oblique "
        "dataset and make cardinal dataset oblique to match",
        argstr="-oblique_parent %s",
        exists=True,
    )
    deoblique = traits.Bool(
        desc="transform dataset from oblique to cardinal", argstr="-deoblique"
    )
    interp = traits.Enum(
        ("linear", "cubic", "NN", "quintic"),
        desc="spatial interpolation methods [default = linear]",
        argstr="-%s",
    )
    gridset = File(
        desc="copy grid of specified dataset", argstr="-gridset %s", exists=True
    )
    newgrid = traits.Float(desc="specify grid of this size (mm)", argstr="-newgrid %f")
    zpad = traits.Int(
        desc="pad input dataset with N planes of zero on all sides.", argstr="-zpad %d"
    )
    verbose = traits.Bool(
        desc="Print out some information along the way.", argstr="-verb"
    )
    save_warp = traits.Bool(desc="save warp as .mat file", requires=["verbose"])


class WarpOutputSpec(TraitedSpec):
    out_file = File(desc="Warped file.", exists=True)
    warp_file = File(desc="warp transform .mat file")


class Warp(AFNICommand):
    """Use 3dWarp for spatially transforming a dataset.

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> warp = afni.Warp()
    >>> warp.inputs.in_file = 'structural.nii'
    >>> warp.inputs.deoblique = True
    >>> warp.inputs.out_file = 'trans.nii.gz'
    >>> warp.cmdline
    '3dWarp -deoblique -prefix trans.nii.gz structural.nii'
    >>> res = warp.run()  # doctest: +SKIP

    >>> warp_2 = afni.Warp()
    >>> warp_2.inputs.in_file = 'structural.nii'
    >>> warp_2.inputs.newgrid = 1.0
    >>> warp_2.inputs.out_file = 'trans.nii.gz'
    >>> warp_2.cmdline
    '3dWarp -newgrid 1.000000 -prefix trans.nii.gz structural.nii'
    >>> res = warp_2.run()  # doctest: +SKIP

    See Also
    --------
    For complete details, see the `3dWarp Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dWarp.html>`__.

    """

    _cmd = "3dWarp"
    input_spec = WarpInputSpec
    output_spec = WarpOutputSpec

    def _run_interface(self, runtime, correct_return_codes=(0,)):
        runtime = super(Warp, self)._run_interface(runtime, correct_return_codes)

        if self.inputs.save_warp:
            import numpy as np

            warp_file = self._list_outputs()["warp_file"]
            np.savetxt(warp_file, [runtime.stdout], fmt=str("%s"))
        return runtime

    def _list_outputs(self):
        outputs = super(Warp, self)._list_outputs()
        if self.inputs.save_warp:
            outputs["warp_file"] = fname_presuffix(
                outputs["out_file"], suffix="_transform.mat", use_ext=False
            )

        return outputs


class QwarpInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc="Source image (opposite phase encoding direction than base image).",
        argstr="-source %s",
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    base_file = File(
        desc="Base image (opposite phase encoding direction than source image).",
        argstr="-base %s",
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        argstr="-prefix %s",
        name_template="ppp_%s",
        name_source=["in_file"],
        desc="""\
Sets the prefix/suffix for the output datasets.

* The source dataset is warped to match the base
  and gets prefix 'ppp'. (Except if '-plusminus' is used
* The final interpolation to this output dataset is
  done using the 'wsinc5' method.  See the output of
  3dAllineate -HELP
  (in the "Modifying '-final wsinc5'" section) for
  the lengthy technical details.
* The 3D warp used is saved in a dataset with
  prefix 'ppp_WARP' -- this dataset can be used
  with 3dNwarpApply and 3dNwarpCat, for example.
* To be clear, this is the warp from source dataset
  coordinates to base dataset coordinates, where the
  values at each base grid point are the xyz displacments
  needed to move that grid point's xyz values to the
  corresponding xyz values in the source dataset:
  base( (x,y,z) + WARP(x,y,z) ) matches source(x,y,z)
  Another way to think of this warp is that it 'pulls'
  values back from source space to base space.
* 3dNwarpApply would use 'ppp_WARP' to transform datasets
  aligned with the source dataset to be aligned with the
  base dataset.

**If you do NOT want this warp saved, use the option '-nowarp'**.
(However, this warp is usually the most valuable possible output!)

* If you want to calculate and save the inverse 3D warp,
  use the option '-iwarp'.  This inverse warp will then be
  saved in a dataset with prefix 'ppp_WARPINV'.
* This inverse warp could be used to transform data from base
  space to source space, if you need to do such an operation.
* You can easily compute the inverse later, say by a command like
  3dNwarpCat -prefix Z_WARPINV 'INV(Z_WARP+tlrc)'
  or the inverse can be computed as needed in 3dNwarpApply, like
  3dNwarpApply -nwarp 'INV(Z_WARP+tlrc)' -source Dataset.nii ...

""",
    )
    resample = traits.Bool(
        desc="""\
This option simply resamples the source dataset to match the
base dataset grid.  You can use this if the two datasets
overlap well (as seen in the AFNI GUI), but are not on the
same 3D grid.

* If they don't overlap well, allineate them first
* The reampling here is done with the
  'wsinc5' method, which has very little blurring artifact.
* If the base and source datasets ARE on the same 3D grid,
  then the -resample option will be ignored.
* You CAN use -resample with these 3dQwarp options:
  -plusminus  -inilev  -iniwarp  -duplo

""",
        argstr="-resample",
    )
    allineate = traits.Bool(
        desc="This option will make 3dQwarp run 3dAllineate first, to align "
        "the source dataset to the base with an affine transformation. "
        "It will then use that alignment as a starting point for the "
        "nonlinear warping.",
        argstr="-allineate",
    )
    allineate_opts = traits.Str(
        desc="add extra options to the 3dAllineate command to be run by 3dQwarp.",
        argstr="-allineate_opts %s",
        requires=["allineate"],
    )
    nowarp = traits.Bool(desc="Do not save the _WARP file.", argstr="-nowarp")
    iwarp = traits.Bool(
        desc="Do compute and save the _WARPINV file.",
        argstr="-iwarp",
        xor=["plusminus"],
    )
    pear = traits.Bool(
        desc="Use strict Pearson correlation for matching."
        "Not usually recommended, since the 'clipped Pearson' method"
        "used by default will reduce the impact of outlier values.",
        argstr="-pear",
    )
    noneg = traits.Bool(
        desc="""\
Replace negative values in either input volume with 0.

* If there ARE negative input values, and you do NOT use -noneg,
  then strict Pearson correlation will be used, since the 'clipped'
  method only is implemented for non-negative volumes.
* '-noneg' is not the default, since there might be situations where
  you want to align datasets with positive and negative values mixed.
* But, in many cases, the negative values in a dataset are just the
  result of interpolation artifacts (or other peculiarities), and so
  they should be ignored.  That is what '-noneg' is for.

""",
        argstr="-noneg",
    )
    nopenalty = traits.Bool(
        desc="""\
Replace negative values in either input volume with 0.

* If there ARE negative input values, and you do NOT use -noneg,
  then strict Pearson correlation will be used, since the 'clipped'
  method only is implemented for non-negative volumes.
* '-noneg' is not the default, since there might be situations where
  you want to align datasets with positive and negative values mixed.
* But, in many cases, the negative values in a dataset are just the
  result of interpolation artifacts (or other peculiarities), and so
  they should be ignored. That is what '-noneg' is for.

""",
        argstr="-nopenalty",
    )
    penfac = traits.Float(
        argstr="-penfac %f",
        desc="""\
Use this value to weight the penalty.
The default value is 1. Larger values mean the
penalty counts more, reducing grid distortions,
insha'Allah; '-nopenalty' is the same as '-penfac 0'.
In 23 Sep 2013 Zhark increased the default value of
the penalty by a factor of 5, and also made it get
progressively larger with each level of refinement.
Thus, warping results will vary from earlier instances
of 3dQwarp.

* The progressive increase in the penalty at higher levels
  means that the 'cost function' can actually look like the
  alignment is getting worse when the levels change.
* IF you wish to turn off this progression, for whatever
  reason (e.g., to keep compatibility with older results),
  use the option '-penold'.To be completely compatible with
  the older 3dQwarp, you'll also have to use '-penfac 0.2'.

""",
    )
    noweight = traits.Bool(
        desc="If you want a binary weight (the old default), use this option."
        "That is, each voxel in the base volume automask will be"
        "weighted the same in the computation of the cost functional.",
        argstr="-noweight",
    )
    weight = File(
        desc="Instead of computing the weight from the base dataset,"
        "directly input the weight volume from dataset 'www'."
        "Useful if you know what over parts of the base image you"
        "want to emphasize or de-emphasize the matching functional.",
        argstr="-weight %s",
        exists=True,
    )
    wball = traits.List(
        traits.Int(),
        desc=""""\
``-wball x y z r f``
Enhance automatic weight from '-useweight' by a factor
of 1+f\\*Gaussian(FWHM=r) centered in the base image at
DICOM coordinates (x,y,z) and with radius 'r'. The
goal of this option is to try and make the alignment
better in a specific part of the brain.
Example:  -wball 0 14 6 30 40
to emphasize the thalamic area (in MNI/Talairach space).

* The 'r' parameter must be positive!
* The 'f' parameter must be between 1 and 100 (inclusive).
* '-wball' does nothing if you input your own weight
  with the '-weight' option.
* '-wball' does change the binary weight created by
  the '-noweight' option.
* You can only use '-wball' once in a run of 3dQwarp.

**The effect of '-wball' is not dramatic.** The example
above makes the average brain image across a collection
of subjects a little sharper in the thalamic area, which
might have some small value.  If you care enough about
alignment to use '-wball', then you should examine the
results from 3dQwarp for each subject, to see if the
alignments are good enough for your purposes.""",
        argstr="-wball %s",
        minlen=5,
        maxlen=5,
        xor=["wmask"],
    )
    traits.Tuple((traits.Float(), traits.Float()), argstr="-bpass %f %f")
    wmask = traits.Tuple(
        (File(exists=True), traits.Float()),
        desc="""\
Similar to '-wball', but here, you provide a dataset 'ws'
that indicates where to increase the weight.

* The 'ws' dataset must be on the same 3D grid as the base dataset.
* 'ws' is treated as a mask -- it only matters where it
  is nonzero -- otherwise, the values inside are not used.
* After 'ws' comes the factor 'f' by which to increase the
  automatically computed weight.  Where 'ws' is nonzero,
  the weighting will be multiplied by (1+f).
* As with '-wball', the factor 'f' should be between 1 and 100.

""",
        argstr="-wpass %s %f",
        xor=["wball"],
    )
    out_weight_file = File(
        argstr="-wtprefix %s", desc="Write the weight volume to disk as a dataset"
    )
    blur = traits.List(
        traits.Float(),
        desc="""\
Gaussian blur the input images by 'bb' (FWHM) voxels before
doing the alignment (the output dataset will not be blurred).
The default is 2.345 (for no good reason).

* Optionally, you can provide 2 values for 'bb', and then
  the first one is applied to the base volume, the second
  to the source volume.
  e.g., '-blur 0 3' to skip blurring the base image
  (if the base is a blurry template, for example).
* A negative blur radius means to use 3D median filtering,
  rather than Gaussian blurring.  This type of filtering will
  better preserve edges, which can be important in alignment.
* If the base is a template volume that is already blurry,
  you probably don't want to blur it again, but blurring
  the source volume a little is probably a good idea, to
  help the program avoid trying to match tiny features.
* Note that -duplo will blur the volumes some extra
  amount for the initial small-scale warping, to make
  that phase of the program converge more rapidly.

""",
        argstr="-blur %s",
        minlen=1,
        maxlen=2,
    )
    pblur = traits.List(
        traits.Float(),
        desc="""\
Use progressive blurring; that is, for larger patch sizes,
the amount of blurring is larger.  The general idea is to
avoid trying to match finer details when the patch size
and incremental warps are coarse.  When '-blur' is used
as well, it sets a minimum amount of blurring that will
be used. [06 Aug 2014 -- '-pblur' may become the default someday].

* You can optionally give the fraction of the patch size that
  is used for the progressive blur by providing a value between
  0 and 0.25 after '-pblur'.  If you provide TWO values, the
  the first fraction is used for progressively blurring the
  base image and the second for the source image.  The default
  parameters when just '-pblur' is given is the same as giving
  the options as '-pblur 0.09 0.09'.
* '-pblur' is useful when trying to match 2 volumes with high
  amounts of detail; e.g, warping one subject's brain image to
  match another's, or trying to warp to match a detailed template.
* Note that using negative values with '-blur' means that the
  progressive blurring will be done with median filters, rather
  than Gaussian linear blurring.

Note: The combination of the -allineate and -pblur options will make
the results of using 3dQwarp to align to a template somewhat
less sensitive to initial head position and scaling.""",
        argstr="-pblur %s",
        minlen=1,
        maxlen=2,
    )
    emask = File(
        desc="Here, 'ee' is a dataset to specify a mask of voxels"
        "to EXCLUDE from the analysis -- all voxels in 'ee'"
        "that are NONZERO will not be used in the alignment."
        "The base image always automasked -- the emask is"
        "extra, to indicate voxels you definitely DON'T want"
        "included in the matching process, even if they are"
        "inside the brain.",
        argstr="-emask %s",
        exists=True,
        copyfile=False,
    )
    noXdis = traits.Bool(desc="Warp will not displace in x direction", argstr="-noXdis")
    noYdis = traits.Bool(desc="Warp will not displace in y direction", argstr="-noYdis")
    noZdis = traits.Bool(desc="Warp will not displace in z direction", argstr="-noZdis")
    iniwarp = traits.List(
        File(exists=True, copyfile=False),
        desc="""\
A dataset with an initial nonlinear warp to use.

* If this option is not used, the initial warp is the identity.
* You can specify a catenation of warps (in quotes) here, as in
  program 3dNwarpApply.
* As a special case, if you just input an affine matrix in a .1D
  file, that will work also -- it is treated as giving the initial
  warp via the string "IDENT(base_dataset) matrix_file.aff12.1D".
* You CANNOT use this option with -duplo !!
* -iniwarp is usually used with -inilev to re-start 3dQwarp from
  a previous stopping point.

""",
        argstr="-iniwarp %s",
        xor=["duplo"],
    )
    inilev = traits.Int(
        desc="""\
The initial refinement 'level' at which to start.

* Usually used with -iniwarp; CANNOT be used with -duplo.
* The combination of -inilev and -iniwarp lets you take the
  results of a previous 3dQwarp run and refine them further:
  Note that the source dataset in the second run is the SAME as
  in the first run.  If you don't see why this is necessary,
  then you probably need to seek help from an AFNI guru.

""",
        argstr="-inilev %d",
        xor=["duplo"],
    )
    minpatch = traits.Int(
        desc="""\
The value of mm should be an odd integer.

* The default value of mm is 25.
* For more accurate results than mm=25, try 19 or 13.
* The smallest allowed patch size is 5.
* You may want stop at a larger patch size (say 7 or 9) and use
  the -Qfinal option to run that final level with quintic warps,
  which might run faster and provide the same degree of warp detail.
* Trying to make two different brain volumes match in fine detail
  is usually a waste of time, especially in humans.  There is too
  much variability in anatomy to match gyrus to gyrus accurately.
  For this reason, the default minimum patch size is 25 voxels.
  Using a smaller '-minpatch' might try to force the warp to
  match features that do not match, and the result can be useless
  image distortions -- another reason to LOOK AT THE RESULTS.

""",
        argstr="-minpatch %d",
    )
    maxlev = traits.Int(
        desc="""\
The initial refinement 'level' at which to start.

* Usually used with -iniwarp; CANNOT be used with -duplo.
* The combination of -inilev and -iniwarp lets you take the
  results of a previous 3dQwarp run and refine them further:
  Note that the source dataset in the second run is the SAME as
  in the first run.  If you don't see why this is necessary,
  then you probably need to seek help from an AFNI guru.

""",
        argstr="-maxlev %d",
        xor=["duplo"],
        position=-1,
    )
    gridlist = File(
        desc="""\
This option provides an alternate way to specify the patch
grid sizes used in the warp optimization process. 'gl' is
a 1D file with a list of patches to use -- in most cases,
you will want to use it in the following form:
``-gridlist '1D: 0 151 101 75 51'``

* Here, a 0 patch size means the global domain. Patch sizes
  otherwise should be odd integers >= 5.
* If you use the '0' patch size again after the first position,
  you will actually get an iteration at the size of the
  default patch level 1, where the patch sizes are 75% of
  the volume dimension.  There is no way to force the program
  to literally repeat the sui generis step of lev=0.

""",
        argstr="-gridlist %s",
        exists=True,
        copyfile=False,
        xor=["duplo", "plusminus"],
    )
    allsave = traits.Bool(
        desc="""
This option lets you save the output warps from each level"
of the refinement process.  Mostly used for experimenting."
Will only save all the outputs if the program terminates"
normally -- if it crashes, or freezes, then all these"
warps are lost.""",
        argstr="-allsave",
        xor=["nopadWARP", "duplo", "plusminus"],
    )
    duplo = traits.Bool(
        desc="""\
Start off with 1/2 scale versions of the volumes,"
for getting a speedy coarse first alignment."

* Then scales back up to register the full volumes."
  The goal is greater speed, and it seems to help this"
  positively piggish program to be more expeditious."
* However, accuracy is somewhat lower with '-duplo',"
  for reasons that currenly elude Zhark; for this reason,"
  the Emperor does not usually use '-duplo'.

""",
        argstr="-duplo",
        xor=["gridlist", "maxlev", "inilev", "iniwarp", "plusminus", "allsave"],
    )
    workhard = traits.Bool(
        desc="""\
Iterate more times, which can help when the volumes are
hard to align at all, or when you hope to get a more precise
alignment.

* Slows the program down (possibly a lot), of course.
* When you combine '-workhard'  with '-duplo', only the
  full size volumes get the extra iterations.
* For finer control over which refinement levels work hard,
  you can use this option in the form (for example) ``-workhard:4:7``
  which implies the extra iterations will be done at levels
  4, 5, 6, and 7, but not otherwise.
* You can also use '-superhard' to iterate even more, but
  this extra option will REALLY slow things down.

  * Under most circumstances, you should not need to use either
    ``-workhard`` or ``-superhard``.
  * The fastest way to register to a template image is via the
    ``-duplo`` option, and without the ``-workhard`` or ``-superhard`` options.
  * If you use this option in the form '-Workhard' (first letter
    in upper case), then the second iteration at each level is
    done with quintic polynomial warps.

""",
        argstr="-workhard",
        xor=["boxopt", "ballopt"],
    )
    Qfinal = traits.Bool(
        desc="""\
At the finest patch size (the final level), use Hermite
quintic polynomials for the warp instead of cubic polynomials.

* In a 3D 'patch', there are 2x2x2x3=24 cubic polynomial basis
  function parameters over which to optimize (2 polynomials
  dependent on each of the x,y,z directions, and 3 different
  directions of displacement).
* There are 3x3x3x3=81 quintic polynomial parameters per patch.
* With -Qfinal, the final level will have more detail in
  the allowed warps, at the cost of yet more CPU time.
* However, no patch below 7x7x7 in size will be done with quintic
  polynomials.
* This option is also not usually needed, and is experimental.

""",
        argstr="-Qfinal",
    )
    Qonly = traits.Bool(
        desc="""\
Use Hermite quintic polynomials at all levels.

* Very slow (about 4 times longer).  Also experimental.
* Will produce a (discrete representation of a) C2 warp.

""",
        argstr="-Qonly",
    )
    plusminus = traits.Bool(
        desc="""\
Normally, the warp displacements dis(x) are defined to match
base(x) to source(x+dis(x)).  With this option, the match
is between base(x-dis(x)) and source(x+dis(x)) -- the two
images 'meet in the middle'.

* One goal is to mimic the warping done to MRI EPI data by
  field inhomogeneities, when registering between a 'blip up'
  and a 'blip down' down volume, which will have opposite
  distortions.
* Define Wp(x) = x+dis(x) and Wm(x) = x-dis(x).  Then since
  base(Wm(x)) matches source(Wp(x)), by substituting INV(Wm(x))
  wherever we see x, we have base(x) matches source(Wp(INV(Wm(x))));
  that is, the warp V(x) that one would get from the 'usual' way
  of running 3dQwarp is V(x) = Wp(INV(Wm(x))).
* Conversely, we can calculate Wp(x) in terms of V(x) as follows:
  If V(x) = x + dv(x), define Vh(x) = x + dv(x)/2;
  then Wp(x) = V(INV(Vh(x)))
* With the above formulas, it is possible to compute Wp(x) from
  V(x) and vice-versa, using program 3dNwarpCalc.  The requisite
  commands are left as an exercise for the aspiring AFNI Jedi Master.
* You can use the semi-secret '-pmBASE' option to get the V(x)
  warp and the source dataset warped to base space, in addition to
  the Wp(x) '_PLUS' and Wm(x) '_MINUS' warps.

  * Alas: -plusminus does not work with -duplo or -allineate :-(
  * However, you can use -iniwarp with -plusminus :-)
  * The outputs have _PLUS (from the source dataset) and _MINUS
    (from the base dataset) in their filenames, in addition to
    the prefix.  The -iwarp option, if present, will be ignored.

""",
        argstr="-plusminus",
        xor=["duplo", "allsave", "iwarp"],
    )
    nopad = traits.Bool(
        desc="""\
Do NOT use zero-padding on the 3D base and source images.
[Default == zero-pad, if needed]

* The underlying model for deformations goes to zero at the
  edge of the volume being warped.  However, if there is
  significant data near an edge of the volume, then it won't
  get displaced much, and so the results might not be good.
* Zero padding is designed as a way to work around this potential
  problem.  You should NOT need the '-nopad' option for any
  reason that Zhark can think of, but it is here to be symmetrical
  with 3dAllineate.
* Note that the output (warped from source) dataset will be on the
  base dataset grid whether or not zero-padding is allowed.  However,
  unless you use the following option, allowing zero-padding (i.e.,
  the default operation) will make the output WARP dataset(s) be
  on a larger grid (also see '-expad' below).

""",
        argstr="-nopad",
    )
    nopadWARP = traits.Bool(
        desc="If for some reason you require the warp volume to"
        "match the base volume, then use this option to have the output"
        "WARP dataset(s) truncated.",
        argstr="-nopadWARP",
        xor=["allsave", "expad"],
    )
    expad = traits.Int(
        desc="This option instructs the program to pad the warp by an extra"
        "'EE' voxels (and then 3dQwarp starts optimizing it)."
        "This option is seldom needed, but can be useful if you"
        "might later catenate the nonlinear warp -- via 3dNwarpCat --"
        "with an affine transformation that contains a large shift."
        "Under that circumstance, the nonlinear warp might be shifted"
        "partially outside its original grid, so expanding that grid"
        "can avoid this problem."
        "Note that this option perforce turns off '-nopadWARP'.",
        argstr="-expad %d",
        xor=["nopadWARP"],
    )
    ballopt = traits.Bool(
        desc="Normally, the incremental warp parameters are optimized inside"
        "a rectangular 'box' (24 dimensional for cubic patches, 81 for"
        "quintic patches), whose limits define the amount of distortion"
        "allowed at each step.  Using '-ballopt' switches these limits"
        "to be applied to a 'ball' (interior of a hypersphere), which"
        "can allow for larger incremental displacements.  Use this"
        "option if you think things need to be able to move farther.",
        argstr="-ballopt",
        xor=["workhard", "boxopt"],
    )
    baxopt = traits.Bool(
        desc="Use the 'box' optimization limits instead of the 'ball'"
        "[this is the default at present]."
        "Note that if '-workhard' is used, then ball and box optimization"
        "are alternated in the different iterations at each level, so"
        "these two options have no effect in that case.",
        argstr="-boxopt",
        xor=["workhard", "ballopt"],
    )
    verb = traits.Bool(
        desc="more detailed description of the process", argstr="-verb", xor=["quiet"]
    )
    quiet = traits.Bool(
        desc="Cut out most of the fun fun fun progress messages :-(",
        argstr="-quiet",
        xor=["verb"],
    )
    # Hidden and semi-hidden options
    overwrite = traits.Bool(desc="Overwrite outputs", argstr="-overwrite")
    lpc = traits.Bool(
        desc="Local Pearson minimization (i.e., EPI-T1 registration)"
        "This option has not be extensively tested"
        "If you use '-lpc', then '-maxlev 0' is automatically set."
        "If you want to go to more refined levels, you can set '-maxlev'"
        "This should be set up to have lpc as the second to last argument"
        "and maxlev as the second to last argument, as needed by AFNI"
        "Using maxlev > 1 is not recommended for EPI-T1 alignment.",
        argstr="-lpc",
        xor=["nmi", "mi", "hel", "lpa", "pear"],
        position=-2,
    )
    lpa = traits.Bool(
        desc="Local Pearson maximization. This option has not be extensively tested",
        argstr="-lpa",
        xor=["nmi", "mi", "lpc", "hel", "pear"],
    )
    hel = traits.Bool(
        desc="Hellinger distance: a matching function for the adventurous"
        "This option has NOT be extensively tested for usefullness"
        "and should be considered experimental at this infundibulum.",
        argstr="-hel",
        xor=["nmi", "mi", "lpc", "lpa", "pear"],
    )
    mi = traits.Bool(
        desc="Mutual Information: a matching function for the adventurous"
        "This option has NOT be extensively tested for usefullness"
        "and should be considered experimental at this infundibulum.",
        argstr="-mi",
        xor=["mi", "hel", "lpc", "lpa", "pear"],
    )
    nmi = traits.Bool(
        desc="Normalized Mutual Information: a matching function for the adventurous"
        "This option has NOT been extensively tested for usefullness"
        "and should be considered experimental at this infundibulum.",
        argstr="-nmi",
        xor=["nmi", "hel", "lpc", "lpa", "pear"],
    )


class QwarpOutputSpec(TraitedSpec):
    warped_source = File(
        desc="Warped source file. If plusminus is used, this is the undistorted"
        "source file."
    )
    warped_base = File(desc="Undistorted base file.")
    source_warp = File(
        desc="Displacement in mm for the source image."
        "If plusminus is used this is the field suceptibility correction"
        "warp (in 'mm') for source image."
    )
    base_warp = File(
        desc="Displacement in mm for the base image."
        "If plus minus is used, this is the field suceptibility correction"
        "warp (in 'mm') for base image. This is only output if plusminus"
        "or iwarp options are passed"
    )
    weights = File(desc="Auto-computed weight volume.")


class Qwarp(AFNICommand):
    """
    Allineate your images prior to passing them to this workflow.

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> qwarp = afni.Qwarp()
    >>> qwarp.inputs.in_file = 'sub-01_dir-LR_epi.nii.gz'
    >>> qwarp.inputs.nopadWARP = True
    >>> qwarp.inputs.base_file = 'sub-01_dir-RL_epi.nii.gz'
    >>> qwarp.inputs.plusminus = True
    >>> qwarp.cmdline
    '3dQwarp -base sub-01_dir-RL_epi.nii.gz -source sub-01_dir-LR_epi.nii.gz -nopadWARP \
-prefix ppp_sub-01_dir-LR_epi -plusminus'
    >>> res = qwarp.run()  # doctest: +SKIP

    >>> from nipype.interfaces import afni
    >>> qwarp = afni.Qwarp()
    >>> qwarp.inputs.in_file = 'structural.nii'
    >>> qwarp.inputs.base_file = 'mni.nii'
    >>> qwarp.inputs.resample = True
    >>> qwarp.cmdline
    '3dQwarp -base mni.nii -source structural.nii -prefix ppp_structural -resample'
    >>> res = qwarp.run()  # doctest: +SKIP

    >>> from nipype.interfaces import afni
    >>> qwarp = afni.Qwarp()
    >>> qwarp.inputs.in_file = 'structural.nii'
    >>> qwarp.inputs.base_file = 'epi.nii'
    >>> qwarp.inputs.out_file = 'anatSSQ.nii.gz'
    >>> qwarp.inputs.resample = True
    >>> qwarp.inputs.lpc = True
    >>> qwarp.inputs.verb = True
    >>> qwarp.inputs.iwarp = True
    >>> qwarp.inputs.blur = [0,3]
    >>> qwarp.cmdline
    '3dQwarp -base epi.nii -blur 0.0 3.0 -source structural.nii -iwarp -prefix anatSSQ.nii.gz \
-resample -verb -lpc'

    >>> res = qwarp.run()  # doctest: +SKIP

    >>> from nipype.interfaces import afni
    >>> qwarp = afni.Qwarp()
    >>> qwarp.inputs.in_file = 'structural.nii'
    >>> qwarp.inputs.base_file = 'mni.nii'
    >>> qwarp.inputs.duplo = True
    >>> qwarp.inputs.blur = [0,3]
    >>> qwarp.cmdline
    '3dQwarp -base mni.nii -blur 0.0 3.0 -duplo -source structural.nii -prefix ppp_structural'

    >>> res = qwarp.run()  # doctest: +SKIP

    >>> from nipype.interfaces import afni
    >>> qwarp = afni.Qwarp()
    >>> qwarp.inputs.in_file = 'structural.nii'
    >>> qwarp.inputs.base_file = 'mni.nii'
    >>> qwarp.inputs.duplo = True
    >>> qwarp.inputs.minpatch = 25
    >>> qwarp.inputs.blur = [0,3]
    >>> qwarp.inputs.out_file = 'Q25'
    >>> qwarp.cmdline
    '3dQwarp -base mni.nii -blur 0.0 3.0 -duplo -source structural.nii -minpatch 25 -prefix Q25'

    >>> res = qwarp.run()  # doctest: +SKIP
    >>> qwarp2 = afni.Qwarp()
    >>> qwarp2.inputs.in_file = 'structural.nii'
    >>> qwarp2.inputs.base_file = 'mni.nii'
    >>> qwarp2.inputs.blur = [0,2]
    >>> qwarp2.inputs.out_file = 'Q11'
    >>> qwarp2.inputs.inilev = 7
    >>> qwarp2.inputs.iniwarp = ['Q25_warp+tlrc.HEAD']
    >>> qwarp2.cmdline
    '3dQwarp -base mni.nii -blur 0.0 2.0 -source structural.nii -inilev 7 -iniwarp Q25_\
warp+tlrc.HEAD -prefix Q11'

    >>> res2 = qwarp2.run()  # doctest: +SKIP
    >>> res2 = qwarp2.run()  # doctest: +SKIP
    >>> qwarp3 = afni.Qwarp()
    >>> qwarp3.inputs.in_file = 'structural.nii'
    >>> qwarp3.inputs.base_file = 'mni.nii'
    >>> qwarp3.inputs.allineate = True
    >>> qwarp3.inputs.allineate_opts = '-cose lpa -verb'
    >>> qwarp3.cmdline
    "3dQwarp -allineate -allineate_opts '-cose lpa -verb' -base mni.nii -source structural.nii \
-prefix ppp_structural"

    >>> res3 = qwarp3.run()  # doctest: +SKIP

    See Also
    --------
    For complete details, see the `3dQwarp Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dQwarp.html>`__

    """

    _cmd = "3dQwarp"
    input_spec = QwarpInputSpec
    output_spec = QwarpOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if name == "allineate_opts":
            return trait_spec.argstr % ("'" + value + "'")
        return super(Qwarp, self)._format_arg(name, trait_spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if not isdefined(self.inputs.out_file):
            prefix = self._gen_fname(self.inputs.in_file, suffix="_QW")
            outputtype = self.inputs.outputtype
            if outputtype == "AFNI":
                ext = ".HEAD"
                suffix = "+tlrc"
            else:
                ext = Info.output_type_to_ext(outputtype)
                suffix = ""
        else:
            prefix = self.inputs.out_file
            ext_ind = max(
                [prefix.lower().rfind(".nii.gz"), prefix.lower().rfind(".nii")]
            )
            if ext_ind == -1:
                ext = ".HEAD"
                suffix = "+tlrc"
            else:
                ext = prefix[ext_ind:]
                suffix = ""

        # All outputs should be in the same directory as the prefix
        out_dir = os.path.dirname(os.path.abspath(prefix))

        outputs["warped_source"] = (
            fname_presuffix(prefix, suffix=suffix, use_ext=False, newpath=out_dir) + ext
        )
        if not self.inputs.nowarp:
            outputs["source_warp"] = (
                fname_presuffix(
                    prefix, suffix="_WARP" + suffix, use_ext=False, newpath=out_dir
                )
                + ext
            )
        if self.inputs.iwarp:
            outputs["base_warp"] = (
                fname_presuffix(
                    prefix, suffix="_WARPINV" + suffix, use_ext=False, newpath=out_dir
                )
                + ext
            )
        if isdefined(self.inputs.out_weight_file):
            outputs["weights"] = os.path.abspath(self.inputs.out_weight_file)

        if self.inputs.plusminus:
            outputs["warped_source"] = (
                fname_presuffix(
                    prefix, suffix="_PLUS" + suffix, use_ext=False, newpath=out_dir
                )
                + ext
            )
            outputs["warped_base"] = (
                fname_presuffix(
                    prefix, suffix="_MINUS" + suffix, use_ext=False, newpath=out_dir
                )
                + ext
            )
            outputs["source_warp"] = (
                fname_presuffix(
                    prefix, suffix="_PLUS_WARP" + suffix, use_ext=False, newpath=out_dir
                )
                + ext
            )
            outputs["base_warp"] = (
                fname_presuffix(
                    prefix,
                    suffix="_MINUS_WARP" + suffix,
                    use_ext=False,
                    newpath=out_dir,
                )
                + ext
            )
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._gen_fname(self.inputs.in_file, suffix="_QW")


class QwarpPlusMinusInputSpec(QwarpInputSpec):
    source_file = File(
        desc="Source image (opposite phase encoding direction than base image)",
        argstr="-source %s",
        exists=True,
        deprecated="1.1.2",
        new_name="in_file",
        copyfile=False,
    )
    out_file = File(
        "Qwarp.nii.gz",
        argstr="-prefix %s",
        position=0,
        usedefault=True,
        desc="Output file",
    )
    plusminus = traits.Bool(
        True,
        usedefault=True,
        position=1,
        desc="Normally, the warp displacements dis(x) are defined to match"
        "base(x) to source(x+dis(x)).  With this option, the match"
        "is between base(x-dis(x)) and source(x+dis(x)) -- the two"
        "images 'meet in the middle'. For more info, view Qwarp` interface",
        argstr="-plusminus",
        xor=["duplo", "allsave", "iwarp"],
    )


class QwarpPlusMinus(Qwarp):
    """A version of 3dQwarp for performing field susceptibility correction
    using two images with opposing phase encoding directions.

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> qwarp = afni.QwarpPlusMinus()
    >>> qwarp.inputs.in_file = 'sub-01_dir-LR_epi.nii.gz'
    >>> qwarp.inputs.nopadWARP = True
    >>> qwarp.inputs.base_file = 'sub-01_dir-RL_epi.nii.gz'
    >>> qwarp.cmdline
    '3dQwarp -prefix Qwarp.nii.gz -plusminus -base sub-01_dir-RL_epi.nii.gz \
-source sub-01_dir-LR_epi.nii.gz -nopadWARP'
    >>> res = warp.run()  # doctest: +SKIP

    See Also
    --------
    For complete details, see the `3dQwarp Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dQwarp.html>`__

    """

    input_spec = QwarpPlusMinusInputSpec
