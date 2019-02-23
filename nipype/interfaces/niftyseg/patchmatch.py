# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The fusion module provides higher-level interfaces to some of the operations
that can be performed with the seg_DetectLesions command-line program.
"""

import warnings

from ..base import TraitedSpec, File, traits, CommandLineInputSpec
from .base import NiftySegCommand
from ..niftyreg.base import get_custom_path

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class PatchMatchInputSpec(CommandLineInputSpec):
    """Input Spec for PatchMatch."""
    # Mandatory input arguments
    in_file = File(
        argstr='-i %s',
        exists=True,
        mandatory=True,
        desc='Input image to segment',
        position=1)

    mask_file = File(
        argstr='-m %s',
        exists=True,
        mandatory=True,
        desc='Input mask for the area where applies PatchMatch',
        position=2)

    database_file = File(
        argstr='-db %s',
        exists=True,
        mandatory=True,
        desc='Database with the segmentations',
        position=3)

    # Output file name
    out_file = File(
        name_source=['in_file'],
        name_template='%s_pm.nii.gz',
        desc='The output filename of the patchmatch results',
        argstr='-o %s',
        position=4)

    # Optional arguments
    patch_size = traits.Int(desc="Patch size, #voxels", argstr='-size %i')

    desc = "Constrained search area size, number of times bigger than the \
patchsize"

    cs_size = traits.Int(desc=desc, argstr='-cs %i')

    match_num = traits.Int(
        desc="Number of better matching", argstr='-match %i')

    pm_num = traits.Int(
        desc="Number of patchmatch executions", argstr='-pm %i')

    desc = "Number of iterations for the patchmatch algorithm"
    it_num = traits.Int(desc=desc, argstr='-it %i')


class PatchMatchOutputSpec(TraitedSpec):
    """OutputSpec for PatchMatch."""
    out_file = File(desc="Output segmentation")


class PatchMatch(NiftySegCommand):
    """Interface for executable seg_PatchMatch from NiftySeg platform.

    The database file is a text file and in each line we have a template
    file, a mask with the search region to consider and a file with the
    label to propagate.

    Input image, input mask, template images from database and masks from
    database must have the same 4D resolution (same number of XxYxZ voxels,
    modalities and/or time-points).
    Label files from database must have the same 3D resolution
    (XxYxZ voxels) than input image but can have different number of
    volumes than the input image allowing to propagate multiple labels
    in the same execution.

    `Source code <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg>`_ |
    `Documentation <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation>`_

    Examples
    --------
    >>> from nipype.interfaces import niftyseg
    >>> node = niftyseg.PatchMatch()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.mask_file = 'im2.nii'
    >>> node.inputs.database_file = 'db.xml'
    >>> node.cmdline
    'seg_PatchMatch -i im1.nii -m im2.nii -db db.xml -o im1_pm.nii.gz'

    """
    _cmd = get_custom_path('seg_PatchMatch', env_dir='NIFTYSEGDIR')
    input_spec = PatchMatchInputSpec
    output_spec = PatchMatchOutputSpec
    _suffix = '_pm'
