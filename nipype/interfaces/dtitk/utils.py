# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""DTITK utility interfaces

DTI-TK developed by Gary Hui Zhang, gary.zhang@ucl.ac.uk
For additional help, visit http://dti-tk.sf.net

The high-dimensional tensor-based DTI registration algorithm

Zhang, H., Avants, B.B, Yushkevich, P.A., Woo, J.H., Wang, S., McCluskey, L.H.,
Elman, L.B., Melhem, E.R., Gee, J.C., High-dimensional spatial normalization of
diffusion tensor images improves the detection of white matter differences in
amyotrophic lateral sclerosis, IEEE Transactions on Medical Imaging,
26(11):1585-1597, November 2007. PMID: 18041273.

The original piecewise-affine tensor-based DTI registration algorithm at the
core of DTI-TK

Zhang, H., Yushkevich, P.A., Alexander, D.C., Gee, J.C., Deformable
registration of diffusion tensor MR images with explicit orientation
optimization, Medical Image Analysis, 10(5):764-785, October 2006. PMID:
16899392.

"""

from ..base import TraitedSpec, CommandLineInputSpec, File, traits, Tuple, isdefined
from ...utils.filemanip import fname_presuffix
from .base import CommandLineDtitk, DTITKRenameMixin
import os

__docformat__ = "restructuredtext"


class TVAdjustVoxSpInputSpec(CommandLineInputSpec):
    in_file = File(
        desc="tensor volume to modify", exists=True, mandatory=True, argstr="-in %s"
    )
    out_file = File(
        desc="output path",
        argstr="-out %s",
        name_source="in_file",
        name_template="%s_avs",
        keep_extension=True,
    )
    target_file = File(
        desc="target volume to match", argstr="-target %s", xor=["voxel_size", "origin"]
    )
    voxel_size = Tuple(
        (traits.Float(), traits.Float(), traits.Float()),
        desc="xyz voxel size (superseded by target)",
        argstr="-vsize %g %g %g",
        xor=["target_file"],
    )
    origin = Tuple(
        (traits.Float(), traits.Float(), traits.Float()),
        desc="xyz origin (superseded by target)",
        argstr="-origin %g %g %g",
        xor=["target_file"],
    )


class TVAdjustVoxSpOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class TVAdjustVoxSp(CommandLineDtitk):
    """
     Adjusts the voxel space of a tensor volume.

    Example
    -------
    >>> from nipype.interfaces import dtitk
    >>> node = dtitk.TVAdjustVoxSp()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.target_file = 'im2.nii'
    >>> node.cmdline
    'TVAdjustVoxelspace -in im1.nii -out im1_avs.nii -target im2.nii'
    >>> node.run() # doctest: +SKIP

    """

    input_spec = TVAdjustVoxSpInputSpec
    output_spec = TVAdjustVoxSpOutputSpec
    _cmd = "TVAdjustVoxelspace"


class SVAdjustVoxSpInputSpec(CommandLineInputSpec):
    in_file = File(
        desc="scalar volume to modify", exists=True, mandatory=True, argstr="-in %s"
    )
    out_file = File(
        desc="output path",
        argstr="-out %s",
        name_source="in_file",
        name_template="%s_avs",
        keep_extension=True,
    )
    target_file = File(
        desc="target volume to match", argstr="-target %s", xor=["voxel_size", "origin"]
    )
    voxel_size = Tuple(
        (traits.Float(), traits.Float(), traits.Float()),
        desc="xyz voxel size (superseded by target)",
        argstr="-vsize %g %g %g",
        xor=["target_file"],
    )
    origin = Tuple(
        (traits.Float(), traits.Float(), traits.Float()),
        desc="xyz origin (superseded by target)",
        argstr="-origin %g %g %g",
        xor=["target_file"],
    )


class SVAdjustVoxSpOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class SVAdjustVoxSp(CommandLineDtitk):
    """
    Adjusts the voxel space of a scalar volume.

    Example
    -------
    >>> from nipype.interfaces import dtitk
    >>> node = dtitk.SVAdjustVoxSp()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.target_file = 'im2.nii'
    >>> node.cmdline
    'SVAdjustVoxelspace -in im1.nii -out im1_avs.nii -target im2.nii'
    >>> node.run() # doctest: +SKIP

    """

    input_spec = SVAdjustVoxSpInputSpec
    output_spec = SVAdjustVoxSpOutputSpec
    _cmd = "SVAdjustVoxelspace"


class TVResampleInputSpec(CommandLineInputSpec):
    in_file = File(
        desc="tensor volume to resample", exists=True, mandatory=True, argstr="-in %s"
    )
    out_file = File(
        desc="output path",
        name_source="in_file",
        name_template="%s_resampled",
        keep_extension=True,
        argstr="-out %s",
    )
    target_file = File(
        desc="specs read from the target volume",
        argstr="-target %s",
        xor=["array_size", "voxel_size", "origin"],
    )
    align = traits.Enum(
        "center",
        "origin",
        argstr="-align %s",
        desc="how to align output volume to input volume",
    )
    interpolation = traits.Enum(
        "LEI", "EI", argstr="-interp %s", desc="Log Euclidean Interpolation"
    )
    array_size = Tuple(
        (traits.Int(), traits.Int(), traits.Int()),
        desc="resampled array size",
        xor=["target_file"],
        argstr="-size %d %d %d",
    )
    voxel_size = Tuple(
        (traits.Float(), traits.Float(), traits.Float()),
        desc="resampled voxel size",
        xor=["target_file"],
        argstr="-vsize %g %g %g",
    )
    origin = Tuple(
        (traits.Float(), traits.Float(), traits.Float()),
        desc="xyz origin",
        xor=["target_file"],
        argstr="-origin %g %g %g",
    )


class TVResampleOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class TVResample(CommandLineDtitk):
    """
    Resamples a tensor volume.

    Example
    -------
    >>> from nipype.interfaces import dtitk
    >>> node = dtitk.TVResample()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.target_file = 'im2.nii'
    >>> node.cmdline
    'TVResample -in im1.nii -out im1_resampled.nii -target im2.nii'
    >>> node.run() # doctest: +SKIP

    """

    input_spec = TVResampleInputSpec
    output_spec = TVResampleOutputSpec
    _cmd = "TVResample"


class SVResampleInputSpec(CommandLineInputSpec):
    in_file = File(
        desc="image to resample", exists=True, mandatory=True, argstr="-in %s"
    )
    out_file = File(
        desc="output path",
        name_source="in_file",
        name_template="%s_resampled",
        keep_extension=True,
        argstr="-out %s",
    )
    target_file = File(
        desc="specs read from the target volume",
        argstr="-target %s",
        xor=["array_size", "voxel_size", "origin"],
    )
    align = traits.Enum(
        "center",
        "origin",
        argstr="-align %s",
        desc="how to align output volume to input volume",
    )
    array_size = Tuple(
        (traits.Int(), traits.Int(), traits.Int()),
        desc="resampled array size",
        xor=["target_file"],
        argstr="-size %d %d %d",
    )
    voxel_size = Tuple(
        (traits.Float(), traits.Float(), traits.Float()),
        desc="resampled voxel size",
        xor=["target_file"],
        argstr="-vsize %g %g %g",
    )
    origin = Tuple(
        (traits.Float(), traits.Float(), traits.Float()),
        desc="xyz origin",
        xor=["target_file"],
        argstr="-origin %g %g %g",
    )


class SVResampleOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class SVResample(CommandLineDtitk):
    """
    Resamples a scalar volume.

    Example
    -------
    >>> from nipype.interfaces import dtitk
    >>> node = dtitk.SVResample()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.target_file = 'im2.nii'
    >>> node.cmdline
    'SVResample -in im1.nii -out im1_resampled.nii -target im2.nii'
    >>> node.run() # doctest: +SKIP

    """

    input_spec = SVResampleInputSpec
    output_spec = SVResampleOutputSpec
    _cmd = "SVResample"


class TVtoolInputSpec(CommandLineInputSpec):
    in_file = File(
        desc="scalar volume to resample", exists=True, argstr="-in %s", mandatory=True
    )
    """NOTE: there are a lot more options here; not implementing all of them"""
    in_flag = traits.Enum("fa", "tr", "ad", "rd", "pd", "rgb", argstr="-%s", desc="")
    out_file = File(argstr="-out %s", genfile=True)


class TVtoolOutputSpec(TraitedSpec):
    out_file = File()


class TVtool(CommandLineDtitk):
    """
    Calculates a tensor metric volume from a tensor volume.

    Example
    -------
    >>> from nipype.interfaces import dtitk
    >>> node = dtitk.TVtool()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.in_flag = 'fa'
    >>> node.cmdline
    'TVtool -in im1.nii -fa -out im1_fa.nii'
    >>> node.run() # doctest: +SKIP

    """

    input_spec = TVtoolInputSpec
    output_spec = TVtoolOutputSpec
    _cmd = "TVtool"

    def _list_outputs(self):
        outputs = self._outputs().get()
        out_file = self.inputs.out_file
        if not isdefined(out_file):
            out_file = self._gen_filename("out_file")
        outputs["out_file"] = os.path.abspath(out_file)
        return outputs

    def _gen_filename(self, name):
        if name != "out_file":
            return
        return fname_presuffix(
            os.path.basename(self.inputs.in_file), suffix="_" + self.inputs.in_flag
        )


"""Note: SVTool not implemented at this time"""


class BinThreshInputSpec(CommandLineInputSpec):
    in_file = File(
        desc="Image to threshold/binarize",
        exists=True,
        position=0,
        argstr="%s",
        mandatory=True,
    )
    out_file = File(
        desc="output path",
        position=1,
        argstr="%s",
        keep_extension=True,
        name_source="in_file",
        name_template="%s_thrbin",
    )
    lower_bound = traits.Float(
        0.01,
        usedefault=True,
        position=2,
        argstr="%g",
        mandatory=True,
        desc="lower bound of binarization range",
    )
    upper_bound = traits.Float(
        100,
        usedefault=True,
        position=3,
        argstr="%g",
        mandatory=True,
        desc="upper bound of binarization range",
    )
    inside_value = traits.Float(
        1,
        position=4,
        argstr="%g",
        usedefault=True,
        mandatory=True,
        desc="value for voxels in binarization range",
    )
    outside_value = traits.Float(
        0,
        position=5,
        argstr="%g",
        usedefault=True,
        mandatory=True,
        desc="value for voxels outside of binarization range",
    )


class BinThreshOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class BinThresh(CommandLineDtitk):
    """
    Binarizes an image.

    Example
    -------
    >>> from nipype.interfaces import dtitk
    >>> node = dtitk.BinThresh()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.lower_bound = 0
    >>> node.inputs.upper_bound = 100
    >>> node.inputs.inside_value = 1
    >>> node.inputs.outside_value = 0
    >>> node.cmdline
    'BinaryThresholdImageFilter im1.nii im1_thrbin.nii 0 100 1 0'
    >>> node.run() # doctest: +SKIP

    """

    input_spec = BinThreshInputSpec
    output_spec = BinThreshOutputSpec
    _cmd = "BinaryThresholdImageFilter"


class BinThreshTask(DTITKRenameMixin, BinThresh):
    pass


class SVAdjustVoxSpTask(DTITKRenameMixin, SVAdjustVoxSp):
    pass


class SVResampleTask(DTITKRenameMixin, SVResample):
    pass


class TVAdjustOriginTask(DTITKRenameMixin, TVAdjustVoxSp):
    pass


class TVAdjustVoxSpTask(DTITKRenameMixin, TVAdjustVoxSp):
    pass


class TVResampleTask(DTITKRenameMixin, TVResample):
    pass


class TVtoolTask(DTITKRenameMixin, TVtool):
    pass
