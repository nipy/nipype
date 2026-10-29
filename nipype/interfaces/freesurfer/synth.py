# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Interfaces to the learning-based tools of FreeSurfer ("SynthX" family):
``mri_synthstrip``, ``mri_synthseg`` and ``mri_synthmorph``.
"""

import os

from ..base import File, TraitedSpec, isdefined, traits
from ...utils.filemanip import fname_presuffix
from .base import FSCommand, FSTraitedSpec


class SynthStripInputSpec(FSTraitedSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr="-i %s",
        desc="image to skullstrip",
    )
    out_file = File(
        argstr="-o %s",
        name_source=["in_file"],
        name_template="%s_brain",
        keep_extension=True,
        hash_files=False,
        desc="skull-stripped image",
    )
    mask_file = File(argstr="-m %s", hash_files=False, desc="binary brain mask")
    no_csf = traits.Bool(argstr="--no-csf", desc="exclude CSF from the brain border")
    use_gpu = traits.Bool(
        argstr="--gpu", desc="use the GPU (the CPU is used by default)"
    )
    model_file = File(
        exists=True, argstr="--model %s", desc="alternative model weights"
    )
    border = traits.Float(
        argstr="-b %.2f", desc="mask border threshold in mm (tool default: 1)"
    )
    fill = traits.Float(
        argstr="-f %.2f", desc="background fill value (tool default: min(image.min, 0))"
    )
    num_threads = traits.Int(
        argstr="--threads %d",
        nohash=True,
        xor=["use_gpu"],
        desc="number of threads used by the CPU version",
    )


class SynthStripOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="skull-stripped image")
    mask_file = File(desc="binary brain mask (if requested)")


class SynthStrip(FSCommand):
    """Skull-strip an image of any contrast with ``mri_synthstrip``.

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import SynthStrip
    >>> strip = SynthStrip(in_file="structural.nii", mask_file="mask.nii.gz")
    >>> strip.cmdline
    'mri_synthstrip -i structural.nii -m mask.nii.gz -o structural_brain.nii'

    """

    _cmd = "mri_synthstrip"
    input_spec = SynthStripInputSpec
    output_spec = SynthStripOutputSpec

    def _list_outputs(self):
        outputs = super()._list_outputs()
        if isdefined(self.inputs.mask_file):
            outputs["mask_file"] = os.path.abspath(self.inputs.mask_file)
        return outputs


class SynthSegInputSpec(FSTraitedSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr="--i %s",
        desc="image to segment",
    )
    out_file = File(
        argstr="--o %s",
        name_source=["in_file"],
        name_template="%s_segmentation",
        keep_extension=True,
        hash_files=False,
        desc="segmentation image",
    )
    parcellation = traits.Bool(
        argstr="--parc",
        desc="also perform cortical parcellation",
    )
    robust = traits.Bool(argstr="--robust", desc="use the more robust variant")
    fast = traits.Bool(
        argstr="--fast", desc="disable some postprocessing for faster prediction"
    )
    use_gpu = traits.Bool(
        False,
        usedefault=True,
        argstr="%s",
        desc="run on the GPU. By default the CPU is used (``--cpu``): FreeSurfer "
        "is distributed without GPU support, and mri_synthseg would otherwise "
        "try the GPU on its own",
    )
    keep_geometry = traits.Bool(
        argstr="--keepgeom", desc="force the output geometry to match the input"
    )
    version_1 = traits.Bool(argstr="--v1", desc="run SynthSeg 1.0")
    ct = traits.Bool(argstr="--ct", desc="input is a CT scan")
    photo = traits.Enum(
        "left",
        "right",
        "both",
        argstr="--photo %s",
        desc="input is a stack of 3D reconstructed dissection photos",
    )
    volume_file = File(
        argstr="--vol %s", hash_files=False, desc="CSV file of regional volumes"
    )
    qc_file = File(argstr="--qc %s", hash_files=False, desc="CSV file of QC scores")
    post_file = File(
        argstr="--post %s", hash_files=False, desc="3D posterior probabilities"
    )
    resampled_file = File(
        argstr="--resample %s", hash_files=False, desc="input resampled at 1mm"
    )
    crop = traits.List(
        traits.Int,
        argstr="--crop %s",
        sep=" ",
        desc="crop the input to a patch of this size before segmentation "
        "(divisible by 32)",
    )
    autocrop = traits.Bool(argstr="--autocrop", desc="ignore background voxels in FOV")
    num_threads = traits.Int(
        argstr="--threads %d",
        nohash=True,
        desc="number of threads used by the CPU version",
    )


class SynthSegOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="segmentation image")
    volume_file = File(desc="CSV file of regional volumes (if requested)")
    qc_file = File(desc="CSV file of QC scores (if requested)")
    post_file = File(desc="3D posterior probabilities (if requested)")
    resampled_file = File(desc="input resampled at 1mm (if requested)")


class SynthSeg(FSCommand):
    """Contrast-agnostic brain segmentation with ``mri_synthseg``.

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import SynthSeg
    >>> seg = SynthSeg(in_file="structural.nii", parcellation=True, robust=True)
    >>> seg.cmdline
    'mri_synthseg --i structural.nii --o structural_segmentation.nii --parc --robust --cpu'

    FreeSurfer is distributed without GPU support, so the CPU is forced unless
    ``use_gpu=True`` is set.

    """

    _cmd = "mri_synthseg"
    input_spec = SynthSegInputSpec
    output_spec = SynthSegOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "use_gpu":
            # mri_synthseg picks the GPU when it finds one: CPU must be forced
            return None if value else "--cpu"
        return super()._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = super()._list_outputs()
        for name in ("volume_file", "qc_file", "post_file", "resampled_file"):
            value = getattr(self.inputs, name)
            if isdefined(value):
                outputs[name] = os.path.abspath(value)
        return outputs


class SynthMorphRegInputSpec(FSTraitedSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-2,
        desc="moving image",
    )
    reference = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-1,
        desc="fixed (reference) image",
    )
    model = traits.Enum(
        "joint",
        "deform",
        "affine",
        "rigid",
        argstr="-m %s",
        usedefault=True,
        desc="transformation model",
    )
    out_file = File(
        argstr="-o %s",
        name_source=["in_file"],
        name_template="%s_registered",
        keep_extension=True,
        hash_files=False,
        desc="moved image",
    )
    initial_mat = File(
        exists=True,
        argstr="-i %s",
        desc="matrix applied to the moving image before registration",
    )
    warp_file = File(
        argstr="-t %s",
        genfile=True,
        hash_files=False,
        desc="transform from moving to fixed space",
    )
    inv_warp_file = File(
        argstr="-T %s",
        genfile=True,
        hash_files=False,
        desc="transform from fixed to moving space",
    )
    use_gpu = traits.Bool(
        argstr="-g",
        xor=["num_threads"],
        desc="use the GPU (the CPU is used by default)",
    )
    regularization = traits.Float(
        argstr="-r %.3f",
        desc="regularization of the deformable registration, in (0, 1) "
        "(tool default: 0.5)",
    )
    steps = traits.Int(
        argstr="-n %d",
        desc="integration steps of the deformable registration "
        "(tool default: 7, should not be less than 5)",
    )
    num_threads = traits.Int(
        argstr="-j %d",
        nohash=True,
        xor=["use_gpu"],
        desc="number of threads used by the CPU version",
    )


class SynthMorphRegOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="moved image")
    warp_file = File(exists=True, desc="transform from moving to fixed space")
    inv_warp_file = File(exists=True, desc="transform from fixed to moving space")


class SynthMorphReg(FSCommand):
    """Register two images of any contrast with ``mri_synthmorph register``.

    The transform files default to ``<in_file>_warp_file`` and
    ``<in_file>_inv_warp_file`` in the working directory, with a ``.lta``
    extension for the linear models (``affine``, ``rigid``) and ``.nii.gz``
    otherwise.

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import SynthMorphReg
    >>> reg = SynthMorphReg(
    ...     in_file="structural.nii",
    ...     reference="functional.nii",
    ...     warp_file="warp.nii.gz",
    ...     inv_warp_file="inv_warp.nii.gz",
    ... )
    >>> reg.cmdline
    'mri_synthmorph register -T inv_warp.nii.gz -m joint -o structural_registered.nii -t warp.nii.gz structural.nii functional.nii'

    """

    _cmd = "mri_synthmorph register"
    input_spec = SynthMorphRegInputSpec
    output_spec = SynthMorphRegOutputSpec

    def _gen_filename(self, name):
        if name in ("warp_file", "inv_warp_file"):
            ext = ".lta" if self.inputs.model in ("affine", "rigid") else ".nii.gz"
            return fname_presuffix(
                self.inputs.in_file,
                suffix=f"_{name}{ext}",
                use_ext=False,
                newpath=os.getcwd(),
            )
        return None

    def _list_outputs(self):
        outputs = super()._list_outputs()
        for name in ("warp_file", "inv_warp_file"):
            value = getattr(self.inputs, name)
            outputs[name] = os.path.abspath(
                value if isdefined(value) else self._gen_filename(name)
            )
        return outputs


class SynthMorphApplyInputSpec(FSTraitedSpec):
    warp_file = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-3,
        desc="transform to apply",
    )
    in_file = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-2,
        desc="moving image",
    )
    out_file = File(
        argstr="%s",
        position=-1,
        name_source=["in_file"],
        name_template="%s_registered",
        keep_extension=True,
        hash_files=False,
        desc="moved image",
    )
    update_voxel = traits.Bool(
        argstr="-H", desc="update the voxel matrix instead of resampling"
    )
    method = traits.Enum(
        "linear",
        "nearest",
        argstr="-m %s",
        desc="interpolation method: linear for images, nearest for segmentations",
    )
    fill = traits.Float(
        argstr="-f %f", desc="fill value outside the field of view (tool default: 0)"
    )
    out_type = traits.Enum(
        "float32",
        "uint8",
        "uint16",
        "int16",
        "int32",
        argstr="-t %s",
        desc="output data type",
    )


class SynthMorphApplyOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="moved image")


class SynthMorphApply(FSCommand):
    """Apply a ``mri_synthmorph register`` transform with ``mri_synthmorph apply``.

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import SynthMorphApply
    >>> apply = SynthMorphApply(warp_file="warpfield.nii", in_file="structural.nii")
    >>> apply.cmdline
    'mri_synthmorph apply warpfield.nii structural.nii structural_registered.nii'

    """

    _cmd = "mri_synthmorph apply"
    input_spec = SynthMorphApplyInputSpec
    output_spec = SynthMorphApplyOutputSpec
