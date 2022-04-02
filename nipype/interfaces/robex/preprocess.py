import os
from pathlib import Path

from nipype.interfaces.base import (
    TraitedSpec,
    CommandLineInputSpec,
    CommandLine,
    File,
    traits,
    isdefined,
)
from nipype.utils.filemanip import split_filename


class RobexInputSpec(CommandLineInputSpec):
    in_file = File(
        desc="Input volume", exists=True, mandatory=True, position=0, argstr="%s"
    )
    out_file = File(
        desc="Output volume",
        position=1,
        argstr="%s",
        hash_files=False,
        name_template='%s_brain',
        name_source=["in_file"],
        keep_extension=True,
    )
    out_mask = File(
        desc="Output mask",
        position=2,
        argstr="%s",
        hash_files=False,
        name_template='%s_brainmask',
        name_source=["in_file"],
        keep_extension=True,
    )
    seed = traits.Int(desc="Seed for random number generator", position=3, argstr="%i")


class RobexOutputSpec(TraitedSpec):
    out_file = File(desc="Output volume")
    out_mask = File(desc="Output mask")


class RobexSegment(CommandLine):
    """

    ROBEX is an automatic whole-brain extraction tool for T1-weighted MRI data (commonly known as skull stripping).
    ROBEX aims for robust skull-stripping across datasets with no parameter settings. It fits a triangular mesh,
    constrained by a shape model, to the probabilistic output of a supervised brain boundary classifier.
    Because the shape model cannot perfectly accommodate unseen cases, a small free deformation is subsequently allowed.
    The deformation is optimized using graph cuts.
    The method ROBEX is based on was published in IEEE Transactions on Medical Imaging;
    please visit the website http://www.jeiglesias.com to download the paper.

    Examples
    --------
    >>> from nipype.interfaces.robex.preprocess import RobexSegment
    >>> robex = RobexSegment()
    >>> robex.inputs.in_file = 'structural.nii'
    >>> robex.cmdline
    'runROBEX.sh structural.nii structural_brain.nii structural_brainmask.nii'
    >>> robex.run() # doctest: +SKIP

    """

    input_spec = RobexInputSpec
    output_spec = RobexOutputSpec
    _cmd = 'runROBEX.sh'
