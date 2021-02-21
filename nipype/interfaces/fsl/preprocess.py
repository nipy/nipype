# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.
"""
import os
import os.path as op
from warnings import warn

import numpy as np
from nibabel import load

from ... import LooseVersion
from ...utils.filemanip import split_filename
from ..base import (
    TraitedSpec,
    File,
    InputMultiPath,
    OutputMultiPath,
    Undefined,
    traits,
    isdefined,
)
from .base import FSLCommand, FSLCommandInputSpec, Info


class BETInputSpec(FSLCommandInputSpec):
    # We use position args here as list indices - so a negative number
    # will put something on the end
    in_file = File(
        exists=True,
        desc="input file to skull strip",
        argstr="%s",
        position=0,
        mandatory=True,
    )
    out_file = File(
        desc="name of output skull stripped image",
        argstr="%s",
        position=1,
        genfile=True,
        hash_files=False,
    )
    outline = traits.Bool(desc="create surface outline image", argstr="-o")
    mask = traits.Bool(desc="create binary mask image", argstr="-m")
    skull = traits.Bool(desc="create skull image", argstr="-s")
    no_output = traits.Bool(argstr="-n", desc="Don't generate segmented output")
    frac = traits.Float(desc="fractional intensity threshold", argstr="-f %.2f")
    vertical_gradient = traits.Float(
        argstr="-g %.2f",
        desc="vertical gradient in fractional intensity threshold (-1, 1)",
    )
    radius = traits.Int(argstr="-r %d", units="mm", desc="head radius")
    center = traits.List(
        traits.Int,
        desc="center of gravity in voxels",
        argstr="-c %s",
        minlen=0,
        maxlen=3,
        units="voxels",
    )
    threshold = traits.Bool(
        argstr="-t", desc="apply thresholding to segmented brain image and mask"
    )
    mesh = traits.Bool(argstr="-e", desc="generate a vtk mesh brain surface")
    # the remaining 'options' are more like modes (mutually exclusive) that
    # FSL actually implements in a shell script wrapper around the bet binary.
    # for some combinations of them in specific order a call would not fail,
    # but in general using more than one of the following is clearly not
    # supported
    _xor_inputs = (
        "functional",
        "reduce_bias",
        "robust",
        "padding",
        "remove_eyes",
        "surfaces",
        "t2_guided",
    )
    robust = traits.Bool(
        desc="robust brain centre estimation (iterates BET several times)",
        argstr="-R",
        xor=_xor_inputs,
    )
    padding = traits.Bool(
        desc=(
            "improve BET if FOV is very small in Z (by temporarily padding "
            "end slices)"
        ),
        argstr="-Z",
        xor=_xor_inputs,
    )
    remove_eyes = traits.Bool(
        desc="eye & optic nerve cleanup (can be useful in SIENA)",
        argstr="-S",
        xor=_xor_inputs,
    )
    surfaces = traits.Bool(
        desc=(
            "run bet2 and then betsurf to get additional skull and scalp "
            "surfaces (includes registrations)"
        ),
        argstr="-A",
        xor=_xor_inputs,
    )
    t2_guided = File(
        desc="as with creating surfaces, when also feeding in "
        "non-brain-extracted T2 (includes registrations)",
        argstr="-A2 %s",
        xor=_xor_inputs,
    )
    functional = traits.Bool(argstr="-F", xor=_xor_inputs, desc="apply to 4D fMRI data")
    reduce_bias = traits.Bool(
        argstr="-B", xor=_xor_inputs, desc="bias field and neck cleanup"
    )


class BETOutputSpec(TraitedSpec):
    out_file = File(desc="path/name of skullstripped file (if generated)")
    mask_file = File(desc="path/name of binary brain mask (if generated)")
    outline_file = File(desc="path/name of outline file (if generated)")
    meshfile = File(desc="path/name of vtk mesh file (if generated)")
    inskull_mask_file = File(desc="path/name of inskull mask (if generated)")
    inskull_mesh_file = File(desc="path/name of inskull mesh outline (if generated)")
    outskull_mask_file = File(desc="path/name of outskull mask (if generated)")
    outskull_mesh_file = File(desc="path/name of outskull mesh outline (if generated)")
    outskin_mask_file = File(desc="path/name of outskin mask (if generated)")
    outskin_mesh_file = File(desc="path/name of outskin mesh outline (if generated)")
    skull_mask_file = File(desc="path/name of skull mask (if generated)")
    skull_file = File(desc="path/name of skull file (if generated)")


class BET(FSLCommand):
    """FSL BET wrapper for skull stripping

    For complete details, see the `BET Documentation.
    <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/BET/UserGuide>`_

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> btr = fsl.BET()
    >>> btr.inputs.in_file = 'structural.nii'
    >>> btr.inputs.frac = 0.7
    >>> btr.inputs.out_file = 'brain_anat.nii'
    >>> btr.cmdline
    'bet structural.nii brain_anat.nii -f 0.70'
    >>> res = btr.run() # doctest: +SKIP

    """

    _cmd = "bet"
    input_spec = BETInputSpec
    output_spec = BETOutputSpec

    def _run_interface(self, runtime):
        # The returncode is meaningless in BET.  So check the output
        # in stderr and if it's set, then update the returncode
        # accordingly.
        runtime = super(BET, self)._run_interface(runtime)
        if runtime.stderr:
            self.raise_exception(runtime)
        return runtime

    def _gen_outfilename(self):
        out_file = self.inputs.out_file
        if not isdefined(out_file) and isdefined(self.inputs.in_file):
            out_file = self._gen_fname(self.inputs.in_file, suffix="_brain")
        return os.path.abspath(out_file)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = self._gen_outfilename()

        basename = os.path.basename(outputs["out_file"])
        cwd = os.path.dirname(outputs["out_file"])
        kwargs = {"basename": basename, "cwd": cwd}

        if (isdefined(self.inputs.mesh) and self.inputs.mesh) or (
            isdefined(self.inputs.surfaces) and self.inputs.surfaces
        ):
            outputs["meshfile"] = self._gen_fname(
                suffix="_mesh.vtk", change_ext=False, **kwargs
            )
        if (isdefined(self.inputs.mask) and self.inputs.mask) or (
            isdefined(self.inputs.reduce_bias) and self.inputs.reduce_bias
        ):
            outputs["mask_file"] = self._gen_fname(suffix="_mask", **kwargs)
        if isdefined(self.inputs.outline) and self.inputs.outline:
            outputs["outline_file"] = self._gen_fname(suffix="_overlay", **kwargs)
        if isdefined(self.inputs.surfaces) and self.inputs.surfaces:
            outputs["inskull_mask_file"] = self._gen_fname(
                suffix="_inskull_mask", **kwargs
            )
            outputs["inskull_mesh_file"] = self._gen_fname(
                suffix="_inskull_mesh", **kwargs
            )
            outputs["outskull_mask_file"] = self._gen_fname(
                suffix="_outskull_mask", **kwargs
            )
            outputs["outskull_mesh_file"] = self._gen_fname(
                suffix="_outskull_mesh", **kwargs
            )
            outputs["outskin_mask_file"] = self._gen_fname(
                suffix="_outskin_mask", **kwargs
            )
            outputs["outskin_mesh_file"] = self._gen_fname(
                suffix="_outskin_mesh", **kwargs
            )
            outputs["skull_mask_file"] = self._gen_fname(suffix="_skull_mask", **kwargs)
        if isdefined(self.inputs.skull) and self.inputs.skull:
            outputs["skull_file"] = self._gen_fname(suffix="_skull", **kwargs)
        if isdefined(self.inputs.no_output) and self.inputs.no_output:
            outputs["out_file"] = Undefined
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._gen_outfilename()
        return None


class FASTInputSpec(FSLCommandInputSpec):
    """ Defines inputs (trait classes) for FAST """

    in_files = InputMultiPath(
        File(exists=True),
        copyfile=False,
        desc="image, or multi-channel set of images, " "to be segmented",
        argstr="%s",
        position=-1,
        mandatory=True,
    )
    out_basename = File(desc="base name of output files", argstr="-o %s")
    # ^^ uses in_file name as basename if none given
    number_classes = traits.Range(
        low=1, high=10, argstr="-n %d", desc="number of tissue-type classes"
    )
    output_biasfield = traits.Bool(desc="output estimated bias field", argstr="-b")
    output_biascorrected = traits.Bool(
        desc="output restored image (bias-corrected image)", argstr="-B"
    )
    img_type = traits.Enum(
        (1, 2, 3),
        desc="int specifying type of image: (1 = T1, 2 = T2, 3 = PD)",
        argstr="-t %d",
    )
    bias_iters = traits.Range(
        low=1,
        high=10,
        argstr="-I %d",
        desc="number of main-loop iterations during " "bias-field removal",
    )
    bias_lowpass = traits.Range(
        low=4,
        high=40,
        desc="bias field smoothing extent (FWHM) " "in mm",
        argstr="-l %d",
        units="mm",
    )
    init_seg_smooth = traits.Range(
        low=0.0001,
        high=0.1,
        desc="initial segmentation spatial "
        "smoothness (during bias field "
        "estimation)",
        argstr="-f %.3f",
    )
    segments = traits.Bool(
        desc="outputs a separate binary image for each " "tissue type", argstr="-g"
    )
    init_transform = File(
        exists=True,
        desc="<standard2input.mat> initialise" " using priors",
        argstr="-a %s",
    )
    other_priors = InputMultiPath(
        File(exist=True),
        desc="alternative prior images",
        argstr="-A %s",
        minlen=3,
        maxlen=3,
    )
    no_pve = traits.Bool(
        desc="turn off PVE (partial volume estimation)", argstr="--nopve"
    )
    no_bias = traits.Bool(desc="do not remove bias field", argstr="-N")
    use_priors = traits.Bool(desc="use priors throughout", argstr="-P")
    # ^^ Must also set -a!, mutually inclusive?? No, conditional mandatory... need to figure out how to handle with traits.
    segment_iters = traits.Range(
        low=1,
        high=50,
        desc="number of segmentation-initialisation" " iterations",
        argstr="-W %d",
    )
    mixel_smooth = traits.Range(
        low=0.0, high=1.0, desc="spatial smoothness for mixeltype", argstr="-R %.2f"
    )
    iters_afterbias = traits.Range(
        low=1,
        high=20,
        desc="number of main-loop iterations " "after bias-field removal",
        argstr="-O %d",
    )
    hyper = traits.Range(
        low=0.0, high=1.0, desc="segmentation spatial smoothness", argstr="-H %.2f"
    )
    verbose = traits.Bool(desc="switch on diagnostic messages", argstr="-v")
    manual_seg = File(
        exists=True, desc="Filename containing intensities", argstr="-s %s"
    )
    probability_maps = traits.Bool(
        desc="outputs individual probability maps", argstr="-p"
    )


class FASTOutputSpec(TraitedSpec):
    """Specify possible outputs from FAST"""

    tissue_class_map = File(
        exists=True,
        desc="path/name of binary segmented volume file"
        " one val for each class  _seg",
    )
    tissue_class_files = OutputMultiPath(
        File(
            desc=(
                "path/name of binary segmented volumes one file for each class  "
                "_seg_x"
            )
        )
    )
    restored_image = OutputMultiPath(
        File(
            desc=(
                "restored images (one for each input image) named according to "
                "the input images _restore"
            )
        )
    )

    mixeltype = File(desc="path/name of mixeltype volume file _mixeltype")

    partial_volume_map = File(desc="path/name of partial volume file _pveseg")
    partial_volume_files = OutputMultiPath(
        File(desc="path/name of partial volumes files one for each class, _pve_x")
    )

    bias_field = OutputMultiPath(File(desc="Estimated bias field _bias"))
    probability_maps = OutputMultiPath(
        File(desc="filenames, one for each class, for each input, prob_x")
    )


class FAST(FSLCommand):
    """FSL FAST wrapper for segmentation and bias correction

    For complete details, see the `FAST Documentation.
    <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FAST>`_

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> fastr = fsl.FAST()
    >>> fastr.inputs.in_files = 'structural.nii'
    >>> fastr.inputs.out_basename = 'fast_'
    >>> fastr.cmdline
    'fast -o fast_ -S 1 structural.nii'
    >>> out = fastr.run()  # doctest: +SKIP

    """

    _cmd = "fast"
    input_spec = FASTInputSpec
    output_spec = FASTOutputSpec

    def _format_arg(self, name, spec, value):
        # first do what should be done in general
        formatted = super(FAST, self)._format_arg(name, spec, value)
        if name == "in_files":
            # FAST needs the -S parameter value to correspond to the number
            # of input images, otherwise it will ignore all but the first
            formatted = "-S %d %s" % (len(value), formatted)
        return formatted

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.number_classes):
            nclasses = 3
        else:
            nclasses = self.inputs.number_classes
        # when using multichannel, results basename is based on last
        # input filename
        _gen_fname_opts = {}
        if isdefined(self.inputs.out_basename):
            _gen_fname_opts["basename"] = self.inputs.out_basename
            _gen_fname_opts["cwd"] = os.getcwd()
        else:
            _gen_fname_opts["basename"] = self.inputs.in_files[-1]
            _gen_fname_opts["cwd"], _, _ = split_filename(_gen_fname_opts["basename"])

        outputs["tissue_class_map"] = self._gen_fname(suffix="_seg", **_gen_fname_opts)
        if self.inputs.segments:
            outputs["tissue_class_files"] = []
            for i in range(nclasses):
                outputs["tissue_class_files"].append(
                    self._gen_fname(suffix="_seg_%d" % i, **_gen_fname_opts)
                )
        if isdefined(self.inputs.output_biascorrected):
            outputs["restored_image"] = []
            if len(self.inputs.in_files) > 1:
                # for multi-image segmentation there is one corrected image
                # per input
                for val, f in enumerate(self.inputs.in_files):
                    # image numbering is 1-based
                    outputs["restored_image"].append(
                        self._gen_fname(
                            suffix="_restore_%d" % (val + 1), **_gen_fname_opts
                        )
                    )
            else:
                # single image segmentation has unnumbered output image
                outputs["restored_image"].append(
                    self._gen_fname(suffix="_restore", **_gen_fname_opts)
                )

        outputs["mixeltype"] = self._gen_fname(suffix="_mixeltype", **_gen_fname_opts)
        if not self.inputs.no_pve:
            outputs["partial_volume_map"] = self._gen_fname(
                suffix="_pveseg", **_gen_fname_opts
            )
            outputs["partial_volume_files"] = []
            for i in range(nclasses):
                outputs["partial_volume_files"].append(
                    self._gen_fname(suffix="_pve_%d" % i, **_gen_fname_opts)
                )
        if self.inputs.output_biasfield:
            outputs["bias_field"] = []
            if len(self.inputs.in_files) > 1:
                # for multi-image segmentation there is one bias field image
                # per input
                for val, f in enumerate(self.inputs.in_files):
                    # image numbering is 1-based
                    outputs["bias_field"].append(
                        self._gen_fname(
                            suffix="_bias_%d" % (val + 1), **_gen_fname_opts
                        )
                    )
            else:
                # single image segmentation has unnumbered output image
                outputs["bias_field"].append(
                    self._gen_fname(suffix="_bias", **_gen_fname_opts)
                )

        if self.inputs.probability_maps:
            outputs["probability_maps"] = []
            for i in range(nclasses):
                outputs["probability_maps"].append(
                    self._gen_fname(suffix="_prob_%d" % i, **_gen_fname_opts)
                )
        return outputs


class FLIRTInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True, argstr="-in %s", mandatory=True, position=0, desc="input file"
    )
    reference = File(
        exists=True, argstr="-ref %s", mandatory=True, position=1, desc="reference file"
    )
    out_file = File(
        argstr="-out %s",
        desc="registered output file",
        name_source=["in_file"],
        name_template="%s_flirt",
        position=2,
        hash_files=False,
    )
    out_matrix_file = File(
        argstr="-omat %s",
        name_source=["in_file"],
        keep_extension=True,
        name_template="%s_flirt.mat",
        desc="output affine matrix in 4x4 asciii format",
        position=3,
        hash_files=False,
    )
    out_log = File(
        name_source=["in_file"],
        keep_extension=True,
        requires=["save_log"],
        name_template="%s_flirt.log",
        desc="output log",
    )
    in_matrix_file = File(argstr="-init %s", desc="input 4x4 affine matrix")
    apply_xfm = traits.Bool(
        argstr="-applyxfm",
        desc=(
            "apply transformation supplied by in_matrix_file or uses_qform to"
            " use the affine matrix stored in the reference header"
        ),
    )
    apply_isoxfm = traits.Float(
        argstr="-applyisoxfm %f",
        xor=["apply_xfm"],
        desc="as applyxfm but forces isotropic resampling",
    )
    datatype = traits.Enum(
        "char",
        "short",
        "int",
        "float",
        "double",
        argstr="-datatype %s",
        desc="force output data type",
    )
    cost = traits.Enum(
        "mutualinfo",
        "corratio",
        "normcorr",
        "normmi",
        "leastsq",
        "labeldiff",
        "bbr",
        argstr="-cost %s",
        desc="cost function",
    )
    # XXX What is the difference between 'cost' and 'searchcost'?  Are
    # these both necessary or do they map to the same variable.
    cost_func = traits.Enum(
        "mutualinfo",
        "corratio",
        "normcorr",
        "normmi",
        "leastsq",
        "labeldiff",
        "bbr",
        argstr="-searchcost %s",
        desc="cost function",
    )
    uses_qform = traits.Bool(
        argstr="-usesqform", desc="initialize using sform or qform"
    )
    display_init = traits.Bool(argstr="-displayinit", desc="display initial matrix")
    angle_rep = traits.Enum(
        "quaternion",
        "euler",
        argstr="-anglerep %s",
        desc="representation of rotation angles",
    )
    interp = traits.Enum(
        "trilinear",
        "nearestneighbour",
        "sinc",
        "spline",
        argstr="-interp %s",
        desc="final interpolation method used in reslicing",
    )
    sinc_width = traits.Int(
        argstr="-sincwidth %d", units="voxels", desc="full-width in voxels"
    )
    sinc_window = traits.Enum(
        "rectangular",
        "hanning",
        "blackman",
        argstr="-sincwindow %s",
        desc="sinc window",
    )  # XXX better doc
    bins = traits.Int(argstr="-bins %d", desc="number of histogram bins")
    dof = traits.Int(argstr="-dof %d", desc="number of transform degrees of freedom")
    no_resample = traits.Bool(argstr="-noresample", desc="do not change input sampling")
    force_scaling = traits.Bool(
        argstr="-forcescaling", desc="force rescaling even for low-res images"
    )
    min_sampling = traits.Float(
        argstr="-minsampling %f",
        units="mm",
        desc="set minimum voxel dimension for sampling",
    )
    padding_size = traits.Int(
        argstr="-paddingsize %d",
        units="voxels",
        desc="for applyxfm: interpolates outside image " "by size",
    )
    searchr_x = traits.List(
        traits.Int,
        minlen=2,
        maxlen=2,
        units="degrees",
        argstr="-searchrx %s",
        desc="search angles along x-axis, in degrees",
    )
    searchr_y = traits.List(
        traits.Int,
        minlen=2,
        maxlen=2,
        units="degrees",
        argstr="-searchry %s",
        desc="search angles along y-axis, in degrees",
    )
    searchr_z = traits.List(
        traits.Int,
        minlen=2,
        maxlen=2,
        units="degrees",
        argstr="-searchrz %s",
        desc="search angles along z-axis, in degrees",
    )
    no_search = traits.Bool(
        argstr="-nosearch", desc="set all angular searches to ranges 0 to 0"
    )
    coarse_search = traits.Int(
        argstr="-coarsesearch %d", units="degrees", desc="coarse search delta angle"
    )
    fine_search = traits.Int(
        argstr="-finesearch %d", units="degrees", desc="fine search delta angle"
    )
    schedule = File(
        exists=True, argstr="-schedule %s", desc="replaces default schedule"
    )
    ref_weight = File(
        exists=True, argstr="-refweight %s", desc="File for reference weighting volume"
    )
    in_weight = File(
        exists=True, argstr="-inweight %s", desc="File for input weighting volume"
    )
    no_clamp = traits.Bool(argstr="-noclamp", desc="do not use intensity clamping")
    no_resample_blur = traits.Bool(
        argstr="-noresampblur", desc="do not use blurring on downsampling"
    )
    rigid2D = traits.Bool(argstr="-2D", desc="use 2D rigid body mode - ignores dof")
    save_log = traits.Bool(desc="save to log file")
    verbose = traits.Int(argstr="-verbose %d", desc="verbose mode, 0 is least")
    bgvalue = traits.Float(
        0,
        argstr="-setbackground %f",
        desc=("use specified background value for points " "outside FOV"),
    )

    # BBR options
    wm_seg = File(
        argstr="-wmseg %s",
        min_ver="5.0.0",
        desc="white matter segmentation volume needed by BBR cost function",
    )
    wmcoords = File(
        argstr="-wmcoords %s",
        min_ver="5.0.0",
        desc="white matter boundary coordinates for BBR cost function",
    )
    wmnorms = File(
        argstr="-wmnorms %s",
        min_ver="5.0.0",
        desc="white matter boundary normals for BBR cost function",
    )
    fieldmap = File(
        argstr="-fieldmap %s",
        min_ver="5.0.0",
        desc=(
            "fieldmap image in rads/s - must be already registered to the "
            "reference image"
        ),
    )
    fieldmapmask = File(
        argstr="-fieldmapmask %s", min_ver="5.0.0", desc="mask for fieldmap image"
    )
    pedir = traits.Int(
        argstr="-pedir %d",
        min_ver="5.0.0",
        desc="phase encode direction of EPI - 1/2/3=x/y/z & -1/-2/-3=-x/-y/-z",
    )
    echospacing = traits.Float(
        argstr="-echospacing %f",
        min_ver="5.0.0",
        desc="value of EPI echo spacing - units of seconds",
    )
    bbrtype = traits.Enum(
        "signed",
        "global_abs",
        "local_abs",
        argstr="-bbrtype %s",
        min_ver="5.0.0",
        desc=("type of bbr cost function: signed [default], global_abs, " "local_abs"),
    )
    bbrslope = traits.Float(
        argstr="-bbrslope %f", min_ver="5.0.0", desc="value of bbr slope"
    )


class FLIRTOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="path/name of registered file (if generated)")
    out_matrix_file = File(
        exists=True, desc="path/name of calculated affine transform " "(if generated)"
    )
    out_log = File(desc="path/name of output log (if generated)")


class FLIRT(FSLCommand):
    """FSL FLIRT wrapper for coregistration

    For complete details, see the `FLIRT Documentation.
    <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT>`_

    To print out the command line help, use:
        fsl.FLIRT().inputs_help()

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import example_data
    >>> flt = fsl.FLIRT(bins=640, cost_func='mutualinfo')
    >>> flt.inputs.in_file = 'structural.nii'
    >>> flt.inputs.reference = 'mni.nii'
    >>> flt.inputs.output_type = "NIFTI_GZ"
    >>> flt.cmdline # doctest: +ELLIPSIS
    'flirt -in structural.nii -ref mni.nii -out structural_flirt.nii.gz -omat structural_flirt.mat -bins 640 -searchcost mutualinfo'
    >>> res = flt.run() #doctest: +SKIP

    """

    _cmd = "flirt"
    input_spec = FLIRTInputSpec
    output_spec = FLIRTOutputSpec
    _log_written = False

    def aggregate_outputs(self, runtime=None, needed_outputs=None):
        outputs = super(FLIRT, self).aggregate_outputs(
            runtime=runtime, needed_outputs=needed_outputs
        )
        if self.inputs.save_log and not self._log_written:
            with open(outputs.out_log, "a") as text_file:
                text_file.write(runtime.stdout + "\n")
            self._log_written = True
        return outputs

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []
        if self.inputs.save_log and not self.inputs.verbose:
            self.inputs.verbose = 1
        if self.inputs.apply_xfm and not (
            self.inputs.in_matrix_file or self.inputs.uses_qform
        ):
            raise RuntimeError(
                "Argument apply_xfm requires in_matrix_file or "
                "uses_qform arguments to run"
            )
        skip.append("save_log")
        return super(FLIRT, self)._parse_inputs(skip=skip)


class ApplyXFMInputSpec(FLIRTInputSpec):
    apply_xfm = traits.Bool(
        True,
        argstr="-applyxfm",
        desc=(
            "apply transformation supplied by in_matrix_file or uses_qform to"
            " use the affine matrix stored in the reference header"
        ),
        usedefault=True,
    )


class ApplyXFM(FLIRT):
    """Currently just a light wrapper around FLIRT,
    with no modifications

    ApplyXFM is used to apply an existing tranform to an image


    Examples
    --------

    >>> import nipype.interfaces.fsl as fsl
    >>> from nipype.testing import example_data
    >>> applyxfm = fsl.preprocess.ApplyXFM()
    >>> applyxfm.inputs.in_file = example_data('structural.nii')
    >>> applyxfm.inputs.in_matrix_file = example_data('trans.mat')
    >>> applyxfm.inputs.out_file = 'newfile.nii'
    >>> applyxfm.inputs.reference = example_data('mni.nii')
    >>> applyxfm.inputs.apply_xfm = True
    >>> result = applyxfm.run() # doctest: +SKIP

    """

    input_spec = ApplyXFMInputSpec


class MCFLIRTInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        position=0,
        argstr="-in %s",
        mandatory=True,
        desc="timeseries to motion-correct",
    )
    out_file = File(
        argstr="-out %s", genfile=True, desc="file to write", hash_files=False
    )
    cost = traits.Enum(
        "mutualinfo",
        "woods",
        "corratio",
        "normcorr",
        "normmi",
        "leastsquares",
        argstr="-cost %s",
        desc="cost function to optimize",
    )
    bins = traits.Int(argstr="-bins %d", desc="number of histogram bins")
    dof = traits.Int(argstr="-dof %d", desc="degrees of freedom for the transformation")
    ref_vol = traits.Int(argstr="-refvol %d", desc="volume to align frames to")
    scaling = traits.Float(argstr="-scaling %.2f", desc="scaling factor to use")
    smooth = traits.Float(
        argstr="-smooth %.2f", desc="smoothing factor for the cost function"
    )
    rotation = traits.Int(
        argstr="-rotation %d", desc="scaling factor for rotation tolerances"
    )
    stages = traits.Int(
        argstr="-stages %d",
        desc="stages (if 4, perform final search with sinc interpolation",
    )
    init = File(exists=True, argstr="-init %s", desc="inital transformation matrix")
    interpolation = traits.Enum(
        "spline",
        "nn",
        "sinc",
        argstr="-%s_final",
        desc="interpolation method for transformation",
    )
    use_gradient = traits.Bool(argstr="-gdt", desc="run search on gradient images")
    use_contour = traits.Bool(argstr="-edge", desc="run search on contour images")
    mean_vol = traits.Bool(argstr="-meanvol", desc="register to mean volume")
    stats_imgs = traits.Bool(
        argstr="-stats", desc="produce variance and std. dev. images"
    )
    save_mats = traits.Bool(argstr="-mats", desc="save transformation matrices")
    save_plots = traits.Bool(argstr="-plots", desc="save transformation parameters")
    save_rms = traits.Bool(
        argstr="-rmsabs -rmsrel", desc="save rms displacement parameters"
    )
    ref_file = File(
        exists=True, argstr="-reffile %s", desc="target image for motion correction"
    )


class MCFLIRTOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="motion-corrected timeseries")
    variance_img = File(exists=True, desc="variance image")
    std_img = File(exists=True, desc="standard deviation image")
    mean_img = File(exists=True, desc="mean timeseries image (if mean_vol=True)")
    par_file = File(exists=True, desc="text-file with motion parameters")
    mat_file = OutputMultiPath(File(exists=True), desc="transformation matrices")
    rms_files = OutputMultiPath(
        File(exists=True), desc="absolute and relative displacement parameters"
    )


class MCFLIRT(FSLCommand):
    """FSL MCFLIRT wrapper for within-modality motion correction

    For complete details, see the `MCFLIRT Documentation.
    <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/MCFLIRT>`_

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> mcflt = fsl.MCFLIRT()
    >>> mcflt.inputs.in_file = 'functional.nii'
    >>> mcflt.inputs.cost = 'mutualinfo'
    >>> mcflt.inputs.out_file = 'moco.nii'
    >>> mcflt.cmdline
    'mcflirt -in functional.nii -cost mutualinfo -out moco.nii'
    >>> res = mcflt.run()  # doctest: +SKIP

    """

    _cmd = "mcflirt"
    input_spec = MCFLIRTInputSpec
    output_spec = MCFLIRTOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "interpolation":
            if value == "trilinear":
                return ""
            else:
                return spec.argstr % value
        return super(MCFLIRT, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()

        outputs["out_file"] = self._gen_outfilename()
        output_dir = os.path.dirname(outputs["out_file"])

        if isdefined(self.inputs.stats_imgs) and self.inputs.stats_imgs:
            if LooseVersion(Info.version()) < LooseVersion("6.0.0"):
                # FSL <6.0 outputs have .nii.gz_variance.nii.gz as extension
                outputs["variance_img"] = self._gen_fname(
                    outputs["out_file"] + "_variance.ext", cwd=output_dir
                )
                outputs["std_img"] = self._gen_fname(
                    outputs["out_file"] + "_sigma.ext", cwd=output_dir
                )
            else:
                outputs["variance_img"] = self._gen_fname(
                    outputs["out_file"], suffix="_variance", cwd=output_dir
                )
                outputs["std_img"] = self._gen_fname(
                    outputs["out_file"], suffix="_sigma", cwd=output_dir
                )

        # The mean image created if -stats option is specified ('meanvol')
        # is missing the top and bottom slices. Therefore we only expose the
        # mean image created by -meanvol option ('mean_reg') which isn't
        # corrupted.
        # Note that the same problem holds for the std and variance image.

        if isdefined(self.inputs.mean_vol) and self.inputs.mean_vol:
            if LooseVersion(Info.version()) < LooseVersion("6.0.0"):
                # FSL <6.0 outputs have .nii.gz_mean_img.nii.gz as extension
                outputs["mean_img"] = self._gen_fname(
                    outputs["out_file"] + "_mean_reg.ext", cwd=output_dir
                )
            else:
                outputs["mean_img"] = self._gen_fname(
                    outputs["out_file"], suffix="_mean_reg", cwd=output_dir
                )

        if isdefined(self.inputs.save_mats) and self.inputs.save_mats:
            _, filename = os.path.split(outputs["out_file"])
            matpathname = os.path.join(output_dir, filename + ".mat")
            _, _, _, timepoints = load(self.inputs.in_file).shape
            outputs["mat_file"] = []
            for t in range(timepoints):
                outputs["mat_file"].append(os.path.join(matpathname, "MAT_%04d" % t))
        if isdefined(self.inputs.save_plots) and self.inputs.save_plots:
            # Note - if e.g. out_file has .nii.gz, you get .nii.gz.par,
            # which is what mcflirt does!
            outputs["par_file"] = outputs["out_file"] + ".par"
        if isdefined(self.inputs.save_rms) and self.inputs.save_rms:
            outfile = outputs["out_file"]
            outputs["rms_files"] = [outfile + "_abs.rms", outfile + "_rel.rms"]
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._gen_outfilename()
        return None

    def _gen_outfilename(self):
        out_file = self.inputs.out_file
        if isdefined(out_file):
            out_file = os.path.realpath(out_file)
        if not isdefined(out_file) and isdefined(self.inputs.in_file):
            out_file = self._gen_fname(self.inputs.in_file, suffix="_mcf")
        return os.path.abspath(out_file)


class FNIRTInputSpec(FSLCommandInputSpec):
    ref_file = File(
        exists=True, argstr="--ref=%s", mandatory=True, desc="name of reference image"
    )
    in_file = File(
        exists=True, argstr="--in=%s", mandatory=True, desc="name of input image"
    )
    affine_file = File(
        exists=True, argstr="--aff=%s", desc="name of file containing affine transform"
    )
    inwarp_file = File(
        exists=True,
        argstr="--inwarp=%s",
        desc="name of file containing initial non-linear warps",
    )
    in_intensitymap_file = traits.List(
        File(exists=True),
        argstr="--intin=%s",
        copyfile=False,
        minlen=1,
        maxlen=2,
        desc=(
            "name of file/files containing "
            "initial intensity mapping "
            "usually generated by previous "
            "fnirt run"
        ),
    )
    fieldcoeff_file = traits.Either(
        traits.Bool,
        File,
        argstr="--cout=%s",
        desc="name of output file with field coefficients or true",
    )
    warped_file = File(
        argstr="--iout=%s", desc="name of output image", genfile=True, hash_files=False
    )
    field_file = traits.Either(
        traits.Bool,
        File,
        argstr="--fout=%s",
        desc="name of output file with field or true",
        hash_files=False,
    )
    jacobian_file = traits.Either(
        traits.Bool,
        File,
        argstr="--jout=%s",
        desc=(
            "name of file for writing out the "
            "Jacobian of the field (for "
            "diagnostic or VBM purposes)"
        ),
        hash_files=False,
    )
    modulatedref_file = traits.Either(
        traits.Bool,
        File,
        argstr="--refout=%s",
        desc=(
            "name of file for writing out "
            "intensity modulated --ref (for "
            "diagnostic purposes)"
        ),
        hash_files=False,
    )
    out_intensitymap_file = traits.Either(
        traits.Bool,
        File,
        argstr="--intout=%s",
        desc=(
            "name of files for writing "
            "information pertaining to "
            "intensity mapping"
        ),
        hash_files=False,
    )
    log_file = File(
        argstr="--logout=%s", desc="Name of log-file", genfile=True, hash_files=False
    )
    config_file = traits.Either(
        traits.Enum("T1_2_MNI152_2mm", "FA_2_FMRIB58_1mm"),
        File(exists=True),
        argstr="--config=%s",
        desc="Name of config file specifying command line arguments",
    )
    refmask_file = File(
        exists=True,
        argstr="--refmask=%s",
        desc="name of file with mask in reference space",
    )
    inmask_file = File(
        exists=True,
        argstr="--inmask=%s",
        desc="name of file with mask in input image space",
    )
    skip_refmask = traits.Bool(
        argstr="--applyrefmask=0",
        xor=["apply_refmask"],
        desc="Skip specified refmask if set, default false",
    )
    skip_inmask = traits.Bool(
        argstr="--applyinmask=0",
        xor=["apply_inmask"],
        desc="skip specified inmask if set, default false",
    )
    apply_refmask = traits.List(
        traits.Enum(0, 1),
        argstr="--applyrefmask=%s",
        xor=["skip_refmask"],
        desc=("list of iterations to use reference mask on (1 to use, 0 to " "skip)"),
        sep=",",
    )
    apply_inmask = traits.List(
        traits.Enum(0, 1),
        argstr="--applyinmask=%s",
        xor=["skip_inmask"],
        desc="list of iterations to use input mask on (1 to use, 0 to skip)",
        sep=",",
    )
    skip_implicit_ref_masking = traits.Bool(
        argstr="--imprefm=0",
        desc=("skip implicit masking  based on value in --ref image. " "Default = 0"),
    )
    skip_implicit_in_masking = traits.Bool(
        argstr="--impinm=0",
        desc=("skip implicit masking  based on value in --in image. " "Default = 0"),
    )
    refmask_val = traits.Float(
        argstr="--imprefval=%f", desc="Value to mask out in --ref image. Default =0.0"
    )
    inmask_val = traits.Float(
        argstr="--impinval=%f", desc="Value to mask out in --in image. Default =0.0"
    )
    max_nonlin_iter = traits.List(
        traits.Int,
        argstr="--miter=%s",
        desc="Max # of non-linear iterations list, default [5, 5, 5, 5]",
        sep=",",
    )
    subsampling_scheme = traits.List(
        traits.Int,
        argstr="--subsamp=%s",
        desc="sub-sampling scheme, list, default [4, 2, 1, 1]",
        sep=",",
    )
    warp_resolution = traits.Tuple(
        traits.Int,
        traits.Int,
        traits.Int,
        argstr="--warpres=%d,%d,%d",
        desc=(
            "(approximate) resolution (in mm) of warp basis in x-, y- and "
            "z-direction, default 10, 10, 10"
        ),
    )
    spline_order = traits.Int(
        argstr="--splineorder=%d",
        desc="Order of spline, 2->Qadratic spline, 3->Cubic spline. Default=3",
    )
    in_fwhm = traits.List(
        traits.Int,
        argstr="--infwhm=%s",
        desc=(
            "FWHM (in mm) of gaussian smoothing kernel for input volume, "
            "default [6, 4, 2, 2]"
        ),
        sep=",",
    )
    ref_fwhm = traits.List(
        traits.Int,
        argstr="--reffwhm=%s",
        desc=(
            "FWHM (in mm) of gaussian smoothing kernel for ref volume, "
            "default [4, 2, 0, 0]"
        ),
        sep=",",
    )
    regularization_model = traits.Enum(
        "membrane_energy",
        "bending_energy",
        argstr="--regmod=%s",
        desc=(
            "Model for regularisation of warp-field [membrane_energy "
            "bending_energy], default bending_energy"
        ),
    )
    regularization_lambda = traits.List(
        traits.Float,
        argstr="--lambda=%s",
        desc=(
            "Weight of regularisation, default depending on --ssqlambda and "
            "--regmod switches. See user documetation."
        ),
        sep=",",
    )
    skip_lambda_ssq = traits.Bool(
        argstr="--ssqlambda=0",
        desc="If true, lambda is not weighted by current ssq, default false",
    )
    jacobian_range = traits.Tuple(
        traits.Float,
        traits.Float,
        argstr="--jacrange=%f,%f",
        desc="Allowed range of Jacobian determinants, default 0.01, 100.0",
    )
    derive_from_ref = traits.Bool(
        argstr="--refderiv",
        desc=("If true, ref image is used to calculate derivatives. " "Default false"),
    )
    intensity_mapping_model = traits.Enum(
        "none",
        "global_linear",
        "global_non_linear",
        "local_linear",
        "global_non_linear_with_bias",
        "local_non_linear",
        argstr="--intmod=%s",
        desc="Model for intensity-mapping",
    )
    intensity_mapping_order = traits.Int(
        argstr="--intorder=%d",
        desc="Order of poynomial for mapping intensities, default 5",
    )
    biasfield_resolution = traits.Tuple(
        traits.Int,
        traits.Int,
        traits.Int,
        argstr="--biasres=%d,%d,%d",
        desc=(
            "Resolution (in mm) of bias-field modelling local intensities, "
            "default 50, 50, 50"
        ),
    )
    bias_regularization_lambda = traits.Float(
        argstr="--biaslambda=%f",
        desc="Weight of regularisation for bias-field, default 10000",
    )
    skip_intensity_mapping = traits.Bool(
        argstr="--estint=0",
        xor=["apply_intensity_mapping"],
        desc="Skip estimate intensity-mapping default false",
    )
    apply_intensity_mapping = traits.List(
        traits.Enum(0, 1),
        argstr="--estint=%s",
        xor=["skip_intensity_mapping"],
        desc=(
            "List of subsampling levels to apply intensity mapping for "
            "(0 to skip, 1 to apply)"
        ),
        sep=",",
    )
    hessian_precision = traits.Enum(
        "double",
        "float",
        argstr="--numprec=%s",
        desc=("Precision for representing Hessian, double or float. " "Default double"),
    )


class FNIRTOutputSpec(TraitedSpec):
    fieldcoeff_file = File(exists=True, desc="file with field coefficients")
    warped_file = File(exists=True, desc="warped image")
    field_file = File(desc="file with warp field")
    jacobian_file = File(desc="file containing Jacobian of the field")
    modulatedref_file = File(desc="file containing intensity modulated --ref")
    out_intensitymap_file = traits.List(
        File,
        minlen=2,
        maxlen=2,
        desc="files containing info pertaining to intensity mapping",
    )
    log_file = File(desc="Name of log-file")


class FNIRT(FSLCommand):
    """FSL FNIRT wrapper for non-linear registration

    For complete details, see the `FNIRT Documentation.
    <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FNIRT>`_

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import example_data
    >>> fnt = fsl.FNIRT(affine_file=example_data('trans.mat'))
    >>> res = fnt.run(ref_file=example_data('mni.nii', in_file=example_data('structural.nii')) #doctest: +SKIP

    T1 -> Mni153

    >>> from nipype.interfaces import fsl
    >>> fnirt_mprage = fsl.FNIRT()
    >>> fnirt_mprage.inputs.in_fwhm = [8, 4, 2, 2]
    >>> fnirt_mprage.inputs.subsampling_scheme = [4, 2, 1, 1]

    Specify the resolution of the warps

    >>> fnirt_mprage.inputs.warp_resolution = (6, 6, 6)
    >>> res = fnirt_mprage.run(in_file='structural.nii', ref_file='mni.nii', warped_file='warped.nii', fieldcoeff_file='fieldcoeff.nii')#doctest: +SKIP

    We can check the command line and confirm that it's what we expect.

    >>> fnirt_mprage.cmdline  #doctest: +SKIP
    'fnirt --cout=fieldcoeff.nii --in=structural.nii --infwhm=8,4,2,2 --ref=mni.nii --subsamp=4,2,1,1 --warpres=6,6,6 --iout=warped.nii'

    """

    _cmd = "fnirt"
    input_spec = FNIRTInputSpec
    output_spec = FNIRTOutputSpec

    filemap = {
        "warped_file": "warped",
        "field_file": "field",
        "jacobian_file": "field_jacobian",
        "modulatedref_file": "modulated",
        "out_intensitymap_file": "intmap",
        "log_file": "log.txt",
        "fieldcoeff_file": "fieldwarp",
    }

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for key, suffix in list(self.filemap.items()):
            inval = getattr(self.inputs, key)
            change_ext = True
            if key in ["warped_file", "log_file"]:
                if suffix.endswith(".txt"):
                    change_ext = False
                if isdefined(inval):
                    outputs[key] = os.path.abspath(inval)
                else:
                    outputs[key] = self._gen_fname(
                        self.inputs.in_file, suffix="_" + suffix, change_ext=change_ext
                    )
            elif isdefined(inval):
                if isinstance(inval, bool):
                    if inval:
                        outputs[key] = self._gen_fname(
                            self.inputs.in_file,
                            suffix="_" + suffix,
                            change_ext=change_ext,
                        )
                else:
                    outputs[key] = os.path.abspath(inval)

            if key == "out_intensitymap_file" and isdefined(outputs[key]):
                basename = FNIRT.intensitymap_file_basename(outputs[key])
                outputs[key] = [
                    outputs[key],
                    "%s.txt" % basename,
                ]
        return outputs

    def _format_arg(self, name, spec, value):
        if name in ("in_intensitymap_file", "out_intensitymap_file"):
            if name == "out_intensitymap_file":
                value = self._list_outputs()[name]
            value = [FNIRT.intensitymap_file_basename(v) for v in value]
            assert len(set(value)) == 1, "Found different basenames for {}: {}".format(
                name, value
            )
            return spec.argstr % value[0]
        if name in list(self.filemap.keys()):
            return spec.argstr % self._list_outputs()[name]
        return super(FNIRT, self)._format_arg(name, spec, value)

    def _gen_filename(self, name):
        if name in ["warped_file", "log_file"]:
            return self._list_outputs()[name]
        return None

    def write_config(self, configfile):
        """Writes out currently set options to specified config file

        XX TODO : need to figure out how the config file is written

        Parameters
        ----------
        configfile : /path/to/configfile
        """
        try:
            fid = open(configfile, "w+")
        except IOError:
            print("unable to create config_file %s" % (configfile))

        for item in list(self.inputs.get().items()):
            fid.write("%s\n" % (item))
        fid.close()

    @classmethod
    def intensitymap_file_basename(cls, f):
        """Removes valid intensitymap extensions from `f`, returning a basename
        that can refer to both intensitymap files.
        """
        for ext in list(Info.ftypes.values()) + [".txt"]:
            if f.endswith(ext):
                return f[: -len(ext)]
        # TODO consider warning for this case
        return f


class ApplyWarpInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        argstr="--in=%s",
        mandatory=True,
        position=0,
        desc="image to be warped",
    )
    out_file = File(
        argstr="--out=%s",
        genfile=True,
        position=2,
        desc="output filename",
        hash_files=False,
    )
    ref_file = File(
        exists=True,
        argstr="--ref=%s",
        mandatory=True,
        position=1,
        desc="reference image",
    )
    field_file = File(
        exists=True, argstr="--warp=%s", desc="file containing warp field"
    )
    abswarp = traits.Bool(
        argstr="--abs", xor=["relwarp"], desc="treat warp field as absolute: x' = w(x)"
    )
    relwarp = traits.Bool(
        argstr="--rel",
        xor=["abswarp"],
        position=-1,
        desc="treat warp field as relative: x' = x + w(x)",
    )
    datatype = traits.Enum(
        "char",
        "short",
        "int",
        "float",
        "double",
        argstr="--datatype=%s",
        desc="Force output data type [char short int float double].",
    )
    supersample = traits.Bool(
        argstr="--super", desc="intermediary supersampling of output, default is off"
    )
    superlevel = traits.Either(
        traits.Enum("a"),
        traits.Int,
        argstr="--superlevel=%s",
        desc=(
            "level of intermediary supersampling, a for 'automatic' or "
            "integer level. Default = 2"
        ),
    )
    premat = File(
        exists=True,
        argstr="--premat=%s",
        desc="filename for pre-transform (affine matrix)",
    )
    postmat = File(
        exists=True,
        argstr="--postmat=%s",
        desc="filename for post-transform (affine matrix)",
    )
    mask_file = File(
        exists=True,
        argstr="--mask=%s",
        desc="filename for mask image (in reference space)",
    )
    interp = traits.Enum(
        "nn",
        "trilinear",
        "sinc",
        "spline",
        argstr="--interp=%s",
        position=-2,
        desc="interpolation method",
    )


class ApplyWarpOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="Warped output file")


class ApplyWarp(FSLCommand):
    """FSL's applywarp wrapper to apply the results of a FNIRT registration

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import example_data
    >>> aw = fsl.ApplyWarp()
    >>> aw.inputs.in_file = example_data('structural.nii')
    >>> aw.inputs.ref_file = example_data('mni.nii')
    >>> aw.inputs.field_file = 'my_coefficients_filed.nii' #doctest: +SKIP
    >>> res = aw.run() #doctest: +SKIP


    """

    _cmd = "applywarp"
    input_spec = ApplyWarpInputSpec
    output_spec = ApplyWarpOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "superlevel":
            return spec.argstr % str(value)
        return super(ApplyWarp, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] = self._gen_fname(self.inputs.in_file, suffix="_warp")
        else:
            outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()[name]
        return None


class SliceTimerInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        argstr="--in=%s",
        mandatory=True,
        position=0,
        desc="filename of input timeseries",
    )
    out_file = File(
        argstr="--out=%s",
        genfile=True,
        desc="filename of output timeseries",
        hash_files=False,
    )
    index_dir = traits.Bool(argstr="--down", desc="slice indexing from top to bottom")
    time_repetition = traits.Float(
        argstr="--repeat=%f", desc="Specify TR of data - default is 3s"
    )
    slice_direction = traits.Enum(
        1,
        2,
        3,
        argstr="--direction=%d",
        desc="direction of slice acquisition (x=1, y=2, z=3) - default is z",
    )
    interleaved = traits.Bool(argstr="--odd", desc="use interleaved acquisition")
    custom_timings = File(
        exists=True,
        argstr="--tcustom=%s",
        desc=(
            "slice timings, in fractions of TR, range 0:1 (default is 0.5 = "
            "no shift)"
        ),
    )
    global_shift = traits.Float(
        argstr="--tglobal",
        desc="shift in fraction of TR, range 0:1 (default is 0.5 = no shift)",
    )
    custom_order = File(
        exists=True,
        argstr="--ocustom=%s",
        desc=(
            "filename of single-column custom interleave order file (first "
            "slice is referred to as 1 not 0)"
        ),
    )


class SliceTimerOutputSpec(TraitedSpec):
    slice_time_corrected_file = File(exists=True, desc="slice time corrected file")


class SliceTimer(FSLCommand):
    """FSL slicetimer wrapper to perform slice timing correction

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import example_data
    >>> st = fsl.SliceTimer()
    >>> st.inputs.in_file = example_data('functional.nii')
    >>> st.inputs.interleaved = True
    >>> result = st.run() #doctest: +SKIP

    """

    _cmd = "slicetimer"
    input_spec = SliceTimerInputSpec
    output_spec = SliceTimerOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        out_file = self.inputs.out_file
        if not isdefined(out_file):
            out_file = self._gen_fname(self.inputs.in_file, suffix="_st")
        outputs["slice_time_corrected_file"] = os.path.abspath(out_file)
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["slice_time_corrected_file"]
        return None


class SUSANInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=1,
        desc="filename of input timeseries",
    )
    brightness_threshold = traits.Float(
        argstr="%.10f",
        position=2,
        mandatory=True,
        desc=(
            "brightness threshold and should be greater than noise level "
            "and less than contrast of edges to be preserved."
        ),
    )
    fwhm = traits.Float(
        argstr="%.10f",
        position=3,
        mandatory=True,
        desc="fwhm of smoothing, in mm, gets converted using sqrt(8*log(2))",
    )
    dimension = traits.Enum(
        3,
        2,
        argstr="%d",
        position=4,
        usedefault=True,
        desc="within-plane (2) or fully 3D (3)",
    )
    use_median = traits.Enum(
        1,
        0,
        argstr="%d",
        position=5,
        usedefault=True,
        desc=(
            "whether to use a local median filter in the cases where "
            "single-point noise is detected"
        ),
    )
    usans = traits.List(
        traits.Tuple(File(exists=True), traits.Float),
        maxlen=2,
        argstr="",
        position=6,
        usedefault=True,
        desc="determines whether the smoothing area (USAN) is to be "
        "found from secondary images (0, 1 or 2). A negative "
        "value for any brightness threshold will auto-set the "
        "threshold at 10% of the robust range",
    )
    out_file = File(
        argstr="%s",
        position=-1,
        genfile=True,
        desc="output file name",
        hash_files=False,
    )


class SUSANOutputSpec(TraitedSpec):
    smoothed_file = File(exists=True, desc="smoothed output file")


class SUSAN(FSLCommand):
    """FSL SUSAN wrapper to perform smoothing

    For complete details, see the `SUSAN Documentation.
    <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/SUSAN>`_

    Examples
    --------

    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import example_data
    >>> anatfile  # doctest: +SKIP
    anatomical.nii  # doctest: +SKIP
    >>> sus = fsl.SUSAN()
    >>> sus.inputs.in_file = example_data('structural.nii')
    >>> sus.inputs.brightness_threshold = 2000.0
    >>> sus.inputs.fwhm = 8.0
    >>> result = sus.run()  # doctest: +SKIP
    """

    _cmd = "susan"
    input_spec = SUSANInputSpec
    output_spec = SUSANOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "fwhm":
            return spec.argstr % (float(value) / np.sqrt(8 * np.log(2)))
        if name == "usans":
            if not value:
                return "0"
            arglist = [str(len(value))]
            for filename, thresh in value:
                arglist.extend([filename, "%.10f" % thresh])
            return " ".join(arglist)
        return super(SUSAN, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()
        out_file = self.inputs.out_file
        if not isdefined(out_file):
            out_file = self._gen_fname(self.inputs.in_file, suffix="_smooth")
        outputs["smoothed_file"] = os.path.abspath(out_file)
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["smoothed_file"]
        return None


class FUGUEInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, argstr="--in=%s", desc="filename of input volume")
    shift_in_file = File(
        exists=True,
        argstr="--loadshift=%s",
        desc="filename for reading pixel shift volume",
    )
    phasemap_in_file = File(
        exists=True, argstr="--phasemap=%s", desc="filename for input phase image"
    )
    fmap_in_file = File(
        exists=True,
        argstr="--loadfmap=%s",
        desc="filename for loading fieldmap (rad/s)",
    )
    unwarped_file = File(
        argstr="--unwarp=%s",
        desc="apply unwarping and save as filename",
        xor=["warped_file"],
        requires=["in_file"],
    )
    warped_file = File(
        argstr="--warp=%s",
        desc="apply forward warping and save as filename",
        xor=["unwarped_file"],
        requires=["in_file"],
    )
    forward_warping = traits.Bool(
        False, usedefault=True, desc="apply forward warping instead of unwarping"
    )
    dwell_to_asym_ratio = traits.Float(
        argstr="--dwelltoasym=%.10f", desc="set the dwell to asym time ratio"
    )
    dwell_time = traits.Float(
        argstr="--dwell=%.10f",
        desc=(
            "set the EPI dwell time per phase-encode line - same as echo "
            "spacing - (sec)"
        ),
    )
    asym_se_time = traits.Float(
        argstr="--asym=%.10f", desc="set the fieldmap asymmetric spin echo time (sec)"
    )
    median_2dfilter = traits.Bool(argstr="--median", desc="apply 2D median filtering")
    despike_2dfilter = traits.Bool(
        argstr="--despike", desc="apply a 2D de-spiking filter"
    )
    no_gap_fill = traits.Bool(
        argstr="--nofill", desc="do not apply gap-filling measure to the fieldmap"
    )
    no_extend = traits.Bool(
        argstr="--noextend",
        desc="do not apply rigid-body extrapolation to the fieldmap",
    )
    smooth2d = traits.Float(
        argstr="--smooth2=%.2f", desc="apply 2D Gaussian smoothing of sigma N (in mm)"
    )
    smooth3d = traits.Float(
        argstr="--smooth3=%.2f", desc="apply 3D Gaussian smoothing of sigma N (in mm)"
    )
    poly_order = traits.Int(
        argstr="--poly=%d", desc="apply polynomial fitting of order N"
    )
    fourier_order = traits.Int(
        argstr="--fourier=%d", desc="apply Fourier (sinusoidal) fitting of order N"
    )
    pava = traits.Bool(argstr="--pava", desc="apply monotonic enforcement via PAVA")
    despike_threshold = traits.Float(
        argstr="--despikethreshold=%s",
        desc="specify the threshold for de-spiking (default=3.0)",
    )
    unwarp_direction = traits.Enum(
        "x",
        "y",
        "z",
        "x-",
        "y-",
        "z-",
        argstr="--unwarpdir=%s",
        desc="specifies direction of warping (default y)",
    )
    phase_conjugate = traits.Bool(
        argstr="--phaseconj", desc="apply phase conjugate method of unwarping"
    )
    icorr = traits.Bool(
        argstr="--icorr",
        requires=["shift_in_file"],
        desc=("apply intensity correction to unwarping (pixel shift method " "only)"),
    )
    icorr_only = traits.Bool(
        argstr="--icorronly",
        requires=["unwarped_file"],
        desc="apply intensity correction only",
    )
    mask_file = File(
        exists=True, argstr="--mask=%s", desc="filename for loading valid mask"
    )
    nokspace = traits.Bool(
        False, argstr="--nokspace", desc="do not use k-space forward warping"
    )

    # Special outputs: shift (voxel shift map, vsm)
    save_shift = traits.Bool(
        False, xor=["save_unmasked_shift"], desc="write pixel shift volume"
    )
    shift_out_file = File(
        argstr="--saveshift=%s", desc="filename for saving pixel shift volume"
    )
    save_unmasked_shift = traits.Bool(
        argstr="--unmaskshift",
        xor=["save_shift"],
        desc="saves the unmasked shiftmap when using --saveshift",
    )

    # Special outputs: fieldmap (fmap)
    save_fmap = traits.Bool(
        False, xor=["save_unmasked_fmap"], desc="write field map volume"
    )
    fmap_out_file = File(
        argstr="--savefmap=%s", desc="filename for saving fieldmap (rad/s)"
    )
    save_unmasked_fmap = traits.Bool(
        False,
        argstr="--unmaskfmap",
        xor=["save_fmap"],
        desc="saves the unmasked fieldmap when using --savefmap",
    )


class FUGUEOutputSpec(TraitedSpec):
    unwarped_file = File(desc="unwarped file")
    warped_file = File(desc="forward warped file")
    shift_out_file = File(desc="voxel shift map file")
    fmap_out_file = File(desc="fieldmap file")


class FUGUE(FSLCommand):
    """FSL FUGUE set of tools for EPI distortion correction

    `FUGUE <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FUGUE>`_ is, most generally,
    a set of tools for EPI distortion correction.

    Distortions may be corrected for
        1. improving registration with non-distorted images (e.g. structurals),
           or
        2. dealing with motion-dependent changes.

    FUGUE is designed to deal only with the first case -
    improving registration.


    Examples
    --------


    Unwarping an input image (shift map is known):

    >>> from nipype.interfaces.fsl.preprocess import FUGUE
    >>> fugue = FUGUE()
    >>> fugue.inputs.in_file = 'epi.nii'
    >>> fugue.inputs.mask_file = 'epi_mask.nii'
    >>> fugue.inputs.shift_in_file = 'vsm.nii'  # Previously computed with fugue as well
    >>> fugue.inputs.unwarp_direction = 'y'
    >>> fugue.inputs.output_type = "NIFTI_GZ"
    >>> fugue.cmdline # doctest: +ELLIPSIS
    'fugue --in=epi.nii --mask=epi_mask.nii --loadshift=vsm.nii --unwarpdir=y --unwarp=epi_unwarped.nii.gz'
    >>> fugue.run() #doctest: +SKIP


    Warping an input image (shift map is known):

    >>> from nipype.interfaces.fsl.preprocess import FUGUE
    >>> fugue = FUGUE()
    >>> fugue.inputs.in_file = 'epi.nii'
    >>> fugue.inputs.forward_warping = True
    >>> fugue.inputs.mask_file = 'epi_mask.nii'
    >>> fugue.inputs.shift_in_file = 'vsm.nii'  # Previously computed with fugue as well
    >>> fugue.inputs.unwarp_direction = 'y'
    >>> fugue.inputs.output_type = "NIFTI_GZ"
    >>> fugue.cmdline # doctest: +ELLIPSIS
    'fugue --in=epi.nii --mask=epi_mask.nii --loadshift=vsm.nii --unwarpdir=y --warp=epi_warped.nii.gz'
    >>> fugue.run() #doctest: +SKIP


    Computing the vsm (unwrapped phase map is known):

    >>> from nipype.interfaces.fsl.preprocess import FUGUE
    >>> fugue = FUGUE()
    >>> fugue.inputs.phasemap_in_file = 'epi_phasediff.nii'
    >>> fugue.inputs.mask_file = 'epi_mask.nii'
    >>> fugue.inputs.dwell_to_asym_ratio = (0.77e-3 * 3) / 2.46e-3
    >>> fugue.inputs.unwarp_direction = 'y'
    >>> fugue.inputs.save_shift = True
    >>> fugue.inputs.output_type = "NIFTI_GZ"
    >>> fugue.cmdline # doctest: +ELLIPSIS
    'fugue --dwelltoasym=0.9390243902 --mask=epi_mask.nii --phasemap=epi_phasediff.nii --saveshift=epi_phasediff_vsm.nii.gz --unwarpdir=y'
    >>> fugue.run() #doctest: +SKIP


    """

    _cmd = "fugue"
    input_spec = FUGUEInputSpec
    output_spec = FUGUEOutputSpec

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []

        input_phase = isdefined(self.inputs.phasemap_in_file)
        input_vsm = isdefined(self.inputs.shift_in_file)
        input_fmap = isdefined(self.inputs.fmap_in_file)

        if not input_phase and not input_vsm and not input_fmap:
            raise RuntimeError(
                (
                    "Either phasemap_in_file, shift_in_file or fmap_in_file must "
                    "be set."
                )
            )

        if not isdefined(self.inputs.in_file):
            skip += ["unwarped_file", "warped_file"]
        else:
            if self.inputs.forward_warping:
                skip += ["unwarped_file"]
                trait_spec = self.inputs.trait("warped_file")
                trait_spec.name_template = "%s_warped"
                trait_spec.name_source = "in_file"
                trait_spec.output_name = "warped_file"
            else:
                skip += ["warped_file"]
                trait_spec = self.inputs.trait("unwarped_file")
                trait_spec.name_template = "%s_unwarped"
                trait_spec.name_source = "in_file"
                trait_spec.output_name = "unwarped_file"

        # Handle shift output
        if not isdefined(self.inputs.shift_out_file):
            vsm_save_masked = (
                isdefined(self.inputs.save_shift) and self.inputs.save_shift
            )
            vsm_save_unmasked = (
                isdefined(self.inputs.save_unmasked_shift)
                and self.inputs.save_unmasked_shift
            )

            if vsm_save_masked or vsm_save_unmasked:
                trait_spec = self.inputs.trait("shift_out_file")
                trait_spec.output_name = "shift_out_file"

                if input_fmap:
                    trait_spec.name_source = "fmap_in_file"
                elif input_phase:
                    trait_spec.name_source = "phasemap_in_file"
                elif input_vsm:
                    trait_spec.name_source = "shift_in_file"
                else:
                    raise RuntimeError(
                        (
                            "Either phasemap_in_file, shift_in_file or "
                            "fmap_in_file must be set."
                        )
                    )

                if vsm_save_unmasked:
                    trait_spec.name_template = "%s_vsm_unmasked"
                else:
                    trait_spec.name_template = "%s_vsm"
            else:
                skip += ["save_shift", "save_unmasked_shift", "shift_out_file"]

        # Handle fieldmap output
        if not isdefined(self.inputs.fmap_out_file):
            fmap_save_masked = (
                isdefined(self.inputs.save_fmap) and self.inputs.save_fmap
            )
            fmap_save_unmasked = (
                isdefined(self.inputs.save_unmasked_fmap)
                and self.inputs.save_unmasked_fmap
            )

            if fmap_save_masked or fmap_save_unmasked:
                trait_spec = self.inputs.trait("fmap_out_file")
                trait_spec.output_name = "fmap_out_file"

                if input_vsm:
                    trait_spec.name_source = "shift_in_file"
                elif input_phase:
                    trait_spec.name_source = "phasemap_in_file"
                elif input_fmap:
                    trait_spec.name_source = "fmap_in_file"
                else:
                    raise RuntimeError(
                        (
                            "Either phasemap_in_file, shift_in_file or "
                            "fmap_in_file must be set."
                        )
                    )

                if fmap_save_unmasked:
                    trait_spec.name_template = "%s_fieldmap_unmasked"
                else:
                    trait_spec.name_template = "%s_fieldmap"
            else:
                skip += ["save_fmap", "save_unmasked_fmap", "fmap_out_file"]

        return super(FUGUE, self)._parse_inputs(skip=skip)


class PRELUDEInputSpec(FSLCommandInputSpec):
    complex_phase_file = File(
        exists=True,
        argstr="--complex=%s",
        mandatory=True,
        xor=["magnitude_file", "phase_file"],
        desc="complex phase input volume",
    )
    magnitude_file = File(
        exists=True,
        argstr="--abs=%s",
        mandatory=True,
        xor=["complex_phase_file"],
        desc="file containing magnitude image",
    )
    phase_file = File(
        exists=True,
        argstr="--phase=%s",
        mandatory=True,
        xor=["complex_phase_file"],
        desc="raw phase file",
    )
    unwrapped_phase_file = File(
        genfile=True,
        argstr="--unwrap=%s",
        desc="file containing unwrapepd phase",
        hash_files=False,
    )
    num_partitions = traits.Int(
        argstr="--numphasesplit=%d", desc="number of phase partitions to use"
    )
    labelprocess2d = traits.Bool(
        argstr="--labelslices", desc="does label processing in 2D (slice at a time)"
    )
    process2d = traits.Bool(
        argstr="--slices",
        xor=["labelprocess2d"],
        desc="does all processing in 2D (slice at a time)",
    )
    process3d = traits.Bool(
        argstr="--force3D",
        xor=["labelprocess2d", "process2d"],
        desc="forces all processing to be full 3D",
    )
    threshold = traits.Float(
        argstr="--thresh=%.10f", desc="intensity threshold for masking"
    )
    mask_file = File(
        exists=True, argstr="--mask=%s", desc="filename of mask input volume"
    )
    start = traits.Int(
        argstr="--start=%d", desc="first image number to process (default 0)"
    )
    end = traits.Int(
        argstr="--end=%d", desc="final image number to process (default Inf)"
    )
    savemask_file = File(
        argstr="--savemask=%s", desc="saving the mask volume", hash_files=False
    )
    rawphase_file = File(
        argstr="--rawphase=%s", desc="saving the raw phase output", hash_files=False
    )
    label_file = File(
        argstr="--labels=%s", desc="saving the area labels output", hash_files=False
    )
    removeramps = traits.Bool(
        argstr="--removeramps", desc="remove phase ramps during unwrapping"
    )


class PRELUDEOutputSpec(TraitedSpec):
    unwrapped_phase_file = File(exists=True, desc="unwrapped phase file")


class PRELUDE(FSLCommand):
    """FSL prelude wrapper for phase unwrapping

    Examples
    --------

    Please insert examples for use of this command

    """

    input_spec = PRELUDEInputSpec
    output_spec = PRELUDEOutputSpec
    _cmd = "prelude"

    def __init__(self, **kwargs):
        super(PRELUDE, self).__init__(**kwargs)
        warn("This has not been fully tested. Please report any failures.")

    def _list_outputs(self):
        outputs = self._outputs().get()
        out_file = self.inputs.unwrapped_phase_file
        if not isdefined(out_file):
            if isdefined(self.inputs.phase_file):
                out_file = self._gen_fname(self.inputs.phase_file, suffix="_unwrapped")
            elif isdefined(self.inputs.complex_phase_file):
                out_file = self._gen_fname(
                    self.inputs.complex_phase_file, suffix="_phase_unwrapped"
                )
        outputs["unwrapped_phase_file"] = os.path.abspath(out_file)
        return outputs

    def _gen_filename(self, name):
        if name == "unwrapped_phase_file":
            return self._list_outputs()["unwrapped_phase_file"]
        return None


class FIRSTInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        position=-2,
        copyfile=False,
        argstr="-i %s",
        desc="input data file",
    )
    out_file = File(
        "segmented",
        usedefault=True,
        mandatory=True,
        position=-1,
        argstr="-o %s",
        desc="output data file",
        hash_files=False,
    )
    verbose = traits.Bool(argstr="-v", position=1, desc="Use verbose logging.")
    brain_extracted = traits.Bool(
        argstr="-b",
        position=2,
        desc="Input structural image is already brain-extracted",
    )
    no_cleanup = traits.Bool(
        argstr="-d",
        position=3,
        desc="Input structural image is already brain-extracted",
    )
    method = traits.Enum(
        "auto",
        "fast",
        "none",
        xor=["method_as_numerical_threshold"],
        argstr="-m %s",
        position=4,
        usedefault=True,
        desc=(
            "Method must be one of auto, fast, none, or it can be entered "
            "using the 'method_as_numerical_threshold' input"
        ),
    )
    method_as_numerical_threshold = traits.Float(
        argstr="-m %.4f",
        position=4,
        desc=(
            "Specify a numerical threshold value or use the 'method' input "
            "to choose auto, fast, or none"
        ),
    )
    list_of_specific_structures = traits.List(
        traits.Str,
        argstr="-s %s",
        sep=",",
        position=5,
        minlen=1,
        desc="Runs only on the specified structures (e.g. L_Hipp, R_Hipp"
        "L_Accu, R_Accu, L_Amyg, R_Amyg"
        "L_Caud, R_Caud, L_Pall, R_Pall"
        "L_Puta, R_Puta, L_Thal, R_Thal, BrStem",
    )
    affine_file = File(
        exists=True,
        position=6,
        argstr="-a %s",
        desc=(
            "Affine matrix to use (e.g. img2std.mat) (does not " "re-run registration)"
        ),
    )


class FIRSTOutputSpec(TraitedSpec):
    vtk_surfaces = OutputMultiPath(
        File(exists=True), desc="VTK format meshes for each subcortical region"
    )
    bvars = OutputMultiPath(File(exists=True), desc="bvars for each subcortical region")
    original_segmentations = File(
        exists=True,
        desc=(
            "3D image file containing the segmented regions "
            "as integer values. Uses CMA labelling"
        ),
    )
    segmentation_file = File(
        exists=True,
        desc=("4D image file containing a single volume per " "segmented region"),
    )


class FIRST(FSLCommand):
    """FSL run_first_all wrapper for segmentation of subcortical volumes

    http://www.fmrib.ox.ac.uk/fsl/first/index.html

    Examples
    --------

    >>> from nipype.interfaces import fsl
    >>> first = fsl.FIRST()
    >>> first.inputs.in_file = 'structural.nii'
    >>> first.inputs.out_file = 'segmented.nii'
    >>> res = first.run() #doctest: +SKIP

    """

    _cmd = "run_first_all"
    input_spec = FIRSTInputSpec
    output_spec = FIRSTOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if isdefined(self.inputs.list_of_specific_structures):
            structures = self.inputs.list_of_specific_structures
        else:
            structures = [
                "L_Hipp",
                "R_Hipp",
                "L_Accu",
                "R_Accu",
                "L_Amyg",
                "R_Amyg",
                "L_Caud",
                "R_Caud",
                "L_Pall",
                "R_Pall",
                "L_Puta",
                "R_Puta",
                "L_Thal",
                "R_Thal",
                "BrStem",
            ]
        outputs["original_segmentations"] = self._gen_fname("original_segmentations")
        outputs["segmentation_file"] = self._gen_fname("segmentation_file")
        outputs["vtk_surfaces"] = self._gen_mesh_names("vtk_surfaces", structures)
        outputs["bvars"] = self._gen_mesh_names("bvars", structures)
        return outputs

    def _gen_fname(self, basename):
        path, outname, ext = split_filename(self.inputs.out_file)

        method = "none"
        if isdefined(self.inputs.method) and self.inputs.method != "none":
            method = "fast"
            if self.inputs.list_of_specific_structures and self.inputs.method == "auto":
                method = "none"

        if isdefined(self.inputs.method_as_numerical_threshold):
            thres = "%.4f" % self.inputs.method_as_numerical_threshold
            method = thres.replace(".", "")

        if basename == "original_segmentations":
            return op.abspath("%s_all_%s_origsegs.nii.gz" % (outname, method))
        if basename == "segmentation_file":
            return op.abspath("%s_all_%s_firstseg.nii.gz" % (outname, method))

        return None

    def _gen_mesh_names(self, name, structures):
        path, prefix, ext = split_filename(self.inputs.out_file)
        if name == "vtk_surfaces":
            vtks = list()
            for struct in structures:
                vtk = prefix + "-" + struct + "_first.vtk"
                vtks.append(op.abspath(vtk))
            return vtks
        if name == "bvars":
            bvars = list()
            for struct in structures:
                bvar = prefix + "-" + struct + "_first.bvars"
                bvars.append(op.abspath(bvar))
            return bvars
        return None
