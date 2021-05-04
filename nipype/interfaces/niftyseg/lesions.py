# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Nipype interface for seg_FillLesions.

The fusion module provides higher-level interfaces to some of the operations
that can be performed with the seg_FillLesions command-line program.

Examples
--------
See the docstrings of the individual classes for examples.
"""

import warnings

from ..base import TraitedSpec, File, traits, CommandLineInputSpec
from .base import NiftySegCommand
from ..niftyreg.base import get_custom_path

warn = warnings.warn
warnings.filterwarnings("always", category=UserWarning)


class FillLesionsInputSpec(CommandLineInputSpec):
    """Input Spec for FillLesions."""

    # Mandatory input arguments
    in_file = File(
        argstr="-i %s",
        exists=True,
        mandatory=True,
        desc="Input image to fill lesions",
        position=1,
    )

    lesion_mask = File(
        argstr="-l %s", exists=True, mandatory=True, desc="Lesion mask", position=2
    )

    # Output file name
    out_file = File(
        name_source=["in_file"],
        name_template="%s_lesions_filled.nii.gz",
        desc="The output filename of the fill lesions results",
        argstr="-o %s",
        position=3,
    )

    # Optional arguments
    desc = "Dilate the mask <int> times (in voxels, by default 0)"
    in_dilation = traits.Int(desc=desc, argstr="-dil %d")

    desc = "Percentage of minimum number of voxels between patches <float> \
(by default 0.5)."

    match = traits.Float(desc=desc, argstr="-match %f")

    desc = "Minimum percentage of valid voxels in target patch <float> \
(by default 0)."

    search = traits.Float(desc=desc, argstr="-search %f")

    desc = "Smoothing by <float> (in minimal 6-neighbourhood voxels \
(by default 0.1))."

    smooth = traits.Float(desc=desc, argstr="-smo %f")

    desc = "Search regions size respect biggest patch size (by default 4)."
    size = traits.Int(desc=desc, argstr="-size %d")

    desc = "Patch cardinality weighting factor (by default 2)."
    cwf = traits.Float(desc=desc, argstr="-cwf %f")

    desc = "Give a binary mask with the valid search areas."
    bin_mask = File(desc=desc, argstr="-mask %s")

    desc = "Guizard et al. (FIN 2015) method, it doesn't include the \
multiresolution/hierarchical inpainting part, this part needs to be done \
with some external software such as reg_tools and reg_resample from NiftyReg. \
By default it uses the method presented in Prados et al. (Neuroimage 2016)."

    other = traits.Bool(desc=desc, argstr="-other")

    use_2d = traits.Bool(
        desc="Uses 2D patches in the Z axis, by default 3D.", argstr="-2D"
    )

    debug = traits.Bool(
        desc="Save all intermidium files (by default OFF).", argstr="-debug"
    )

    desc = "Set output <datatype> (char, short, int, uchar, ushort, uint, \
float, double)."

    out_datatype = traits.String(desc=desc, argstr="-odt %s")

    verbose = traits.Bool(desc="Verbose (by default OFF).", argstr="-v")


class FillLesionsOutputSpec(TraitedSpec):
    """Output Spec for FillLesions."""

    out_file = File(desc="Output segmentation")


class FillLesions(NiftySegCommand):
    """Interface for executable seg_FillLesions from NiftySeg platform.

    Fill all the masked lesions with WM intensity average.

    `Source code <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg>`_ |
    `Documentation <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation>`_

    Examples
    --------
    >>> from nipype.interfaces import niftyseg
    >>> node = niftyseg.FillLesions()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.lesion_mask = 'im2.nii'
    >>> node.cmdline
    'seg_FillLesions -i im1.nii -l im2.nii -o im1_lesions_filled.nii.gz'

    """

    _cmd = get_custom_path("seg_FillLesions", env_dir="NIFTYSEGDIR")
    input_spec = FillLesionsInputSpec
    output_spec = FillLesionsOutputSpec
