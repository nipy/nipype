# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The stats module provides higher-level interfaces to some of the operations
that can be performed with the niftyseg stats (seg_stats) command-line program.
"""
import numpy as np

from ..base import TraitedSpec, File, traits, CommandLineInputSpec
from .base import NiftySegCommand
from ..niftyreg.base import get_custom_path


class StatsInput(CommandLineInputSpec):
    """Input Spec for seg_stats interfaces."""

    in_file = File(
        position=2, argstr="%s", exists=True, mandatory=True, desc="image to operate on"
    )

    # Constrains
    mask_file = File(
        exists=True,
        position=-2,
        argstr="-m %s",
        desc="statistics within the masked area",
    )

    desc = "Only estimate statistics if voxel is larger than <float>"
    larger_voxel = traits.Float(argstr="-t %f", position=-3, desc=desc)


class StatsOutput(TraitedSpec):
    """Output Spec for seg_stats interfaces."""

    output = traits.Array(desc="Output array from seg_stats")


class StatsCommand(NiftySegCommand):
    """
    Base Command Interface for seg_stats interfaces.

    The executable seg_stats enables the estimation of image statistics on
    continuous voxel intensities (average, standard deviation, min/max, robust
    range, percentiles, sum, probabilistic volume, entropy, etc) either over
    the full image or on a per slice basis (slice axis can be specified),
    statistics over voxel coordinates (location of max, min and centre of
    mass, bounding box, etc) and statistics over categorical images (e.g. per
    region volume, count, average, Dice scores, etc). These statistics are
    robust to the presence of NaNs, and can be constrained by a mask and/or
    thresholded at a certain level.
    """

    _cmd = get_custom_path("seg_stats", env_dir="NIFTYSEGDIR")
    input_spec = StatsInput
    output_spec = StatsOutput

    def _parse_stdout(self, stdout):
        out = []
        for string_line in stdout.split("\n"):
            if string_line.startswith("#"):
                continue
            if len(string_line) <= 1:
                continue
            line = [float(s) for s in string_line.split()]
            out.append(line)
        return np.array(out).squeeze()

    def _run_interface(self, runtime):
        new_runtime = super()._run_interface(runtime)
        self.output = self._parse_stdout(new_runtime.stdout)
        return new_runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["output"] = self.output
        return outputs


class UnaryStatsInput(StatsInput):
    """Input Spec for seg_stats unary operations."""

    operation = traits.Enum(
        "r",
        "R",
        "a",
        "s",
        "v",
        "vl",
        "vp",
        "n",
        "np",
        "e",
        "ne",
        "x",
        "X",
        "c",
        "B",
        "xvox",
        "xdim",
        argstr="-%s",
        position=4,
        mandatory=True,
        desc="""\
Operation to perform:

    * r - The range <min max> of all voxels.
    * R - The robust range (assuming 2% outliers on both sides) of all voxels
    * a - Average of all voxels
    * s - Standard deviation of all voxels
    * v - Volume of all voxels above 0 (<# voxels> * <volume per voxel>)
    * vl - Volume of each integer label (<# voxels per label> x <volume per voxel>)
    * vp - Volume of all probabilsitic voxels (sum(<in>) x <volume per voxel>)
    * n - Count of all voxels above 0 (<# voxels>)
    * np - Sum of all fuzzy voxels (sum(<in>))
    * e - Entropy of all voxels
    * ne - Normalized entropy of all voxels
    * x - Location (i j k x y z) of the smallest value in the image
    * X - Location (i j k x y z) of the largest value in the image
    * c - Location (i j k x y z) of the centre of mass of the object
    * B - Bounding box of all nonzero voxels [ xmin xsize ymin ysize zmin zsize ]
    * xvox - Output the number of voxels in the x direction.
      Replace x with y/z for other directions.
    * xdim - Output the voxel dimension in the x direction.
      Replace x with y/z for other directions.

""",
    )


class UnaryStats(StatsCommand):
    """Unary statistical operations.

    See Also
    --------
    `Source code <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg>`__ --
    `Documentation <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation>`__

    Examples
    --------
    >>> import copy
    >>> from nipype.interfaces import niftyseg
    >>> unary = niftyseg.UnaryStats()
    >>> unary.inputs.in_file = 'im1.nii'

    >>> # Test v operation
    >>> unary_v = copy.deepcopy(unary)
    >>> unary_v.inputs.operation = 'v'
    >>> unary_v.cmdline
    'seg_stats im1.nii -v'
    >>> unary_v.run()  # doctest: +SKIP

    >>> # Test vl operation
    >>> unary_vl = copy.deepcopy(unary)
    >>> unary_vl.inputs.operation = 'vl'
    >>> unary_vl.cmdline
    'seg_stats im1.nii -vl'
    >>> unary_vl.run()  # doctest: +SKIP

    >>> # Test x operation
    >>> unary_x = copy.deepcopy(unary)
    >>> unary_x.inputs.operation = 'x'
    >>> unary_x.cmdline
    'seg_stats im1.nii -x'
    >>> unary_x.run()  # doctest: +SKIP

    """

    input_spec = UnaryStatsInput


class BinaryStatsInput(StatsInput):
    """Input Spec for seg_stats Binary operations."""

    operation = traits.Enum(
        "p",
        "sa",
        "ss",
        "svp",
        "al",
        "d",
        "ncc",
        "nmi",
        "Vl",
        "Nl",
        mandatory=True,
        argstr="-%s",
        position=4,
        desc="""\
Operation to perform:

    * p - <float> - The <float>th percentile of all voxels intensity (float=[0,100])
    * sa - <ax> - Average of all voxels
    * ss - <ax> - Standard deviation of all voxels
    * svp - <ax> - Volume of all probabilsitic voxels (sum(<in>) x <volume per voxel>)
    * al - <in2> - Average value in <in> for each label in <in2>
    * d - <in2> - Calculate the Dice score between all classes in <in> and <in2>
    * ncc - <in2> - Normalized cross correlation between <in> and <in2>
    * nmi - <in2> - Normalized Mutual Information between <in> and <in2>
    * Vl - <csv> - Volume of each integer label <in>. Save to <csv>file.
    * Nl - <csv> - Count of each label <in>. Save to <csv> file.

""",
    )

    operand_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=5,
        xor=["operand_value"],
        desc="second image to perform operation with",
    )

    operand_value = traits.Float(
        argstr="%.8f",
        mandatory=True,
        position=5,
        xor=["operand_file"],
        desc="value to perform operation with",
    )


class BinaryStats(StatsCommand):
    """Binary statistical operations.

    See Also
    --------
    `Source code <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg>`__ --
    `Documentation <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation>`__

    Examples
    --------
    >>> import copy
    >>> from nipype.interfaces import niftyseg
    >>> binary = niftyseg.BinaryStats()
    >>> binary.inputs.in_file = 'im1.nii'
    >>> # Test sa operation
    >>> binary_sa = copy.deepcopy(binary)
    >>> binary_sa.inputs.operation = 'sa'
    >>> binary_sa.inputs.operand_value = 2.0
    >>> binary_sa.cmdline
    'seg_stats im1.nii -sa 2.00000000'
    >>> binary_sa.run()  # doctest: +SKIP
    >>> # Test ncc operation
    >>> binary_ncc = copy.deepcopy(binary)
    >>> binary_ncc.inputs.operation = 'ncc'
    >>> binary_ncc.inputs.operand_file = 'im2.nii'
    >>> binary_ncc.cmdline
    'seg_stats im1.nii -ncc im2.nii'
    >>> binary_ncc.run()  # doctest: +SKIP
    >>> # Test Nl operation
    >>> binary_nl = copy.deepcopy(binary)
    >>> binary_nl.inputs.operation = 'Nl'
    >>> binary_nl.inputs.operand_file = 'output.csv'
    >>> binary_nl.cmdline
    'seg_stats im1.nii -Nl output.csv'
    >>> binary_nl.run()  # doctest: +SKIP

    """

    input_spec = BinaryStatsInput
