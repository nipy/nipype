# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The stats module provides higher-level interfaces to some of the operations
that can be performed with the niftysegstats (seg_stats) command-line program.
"""
import numpy as np

from ..base import TraitedSpec, File, traits, CommandLineInputSpec
from .base import NiftySegCommand, get_custom_path


class StatsInput(CommandLineInputSpec):
    """Input Spec for seg_stats interfaces."""
    in_file = File(position=2,
                   argstr='%s',
                   exists=True,
                   mandatory=True,
                   desc='image to operate on')

    # Constrains
    mask_file = File(exists=True,
                     mandatory=False,
                     position=-2,
                     argstr='-m %s',
                     desc='statistics within the masked area')

    desc = 'Only estimate statistics if voxel is larger than <float>'
    larger_voxel = traits.Float(argstr='-t %f',
                                mandatory=False,
                                position=-3,
                                desc=desc)


class StatsOutput(TraitedSpec):
    """Output Spec for seg_stats interfaces."""
    output = traits.Array(desc='Output array from seg_stats')


class StatsCommand(NiftySegCommand):
    """
    Base Command Interface for seg_stats interfaces.
    """
    _cmd = get_custom_path('seg_stats')
    input_spec = StatsInput
    output_spec = StatsOutput

    def _parse_stdout(self, stdout):
        out = []
        for string_line in stdout.split("\n"):
            print('parsing line ' + string_line)
            if string_line.startswith('#'):
                continue
            if len(string_line) <= 1:
                continue
            line = [float(s) for s in string_line.split()]
            out.append(line)
        return np.array(out).squeeze()

    def _run_interface(self, runtime):
        print('parsing output in run_interface')
        new_runtime = super(UnaryStats, self)._run_interface(runtime)
        self.output = self._parse_stdout(new_runtime.stdout)
        return new_runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['output'] = self.output
        return outputs


class UnaryStatsInput(StatsInput):
    """Input Spec for seg_stats unary operations."""
    operation = traits.Enum('r', 'R', 'a', 's', 'v', 'vl', 'vp', 'n', 'np',
                            'e', 'ne', 'x', 'X', 'c', 'B', 'xvox', 'xdim',
                            argstr='-%s',
                            position=4,
                            mandatory=True,
                            desc='operation to perform')


class UnaryStats(StatsCommand):
    """
    Interface for executable seg_stats from NiftySeg platform.

    Interface to use any unary statistical operations that can be performed
    with the seg_stats command-line program. See below for those operations:
        -r          | The range <min max> of all voxels.
        -R          | The robust range (assuming 2% outliers on both sides)
                    | of all voxels
        -a          | Average of all voxels
        -s          | Standard deviation of all voxels
        -v          | Volume of all voxels above 0 (<# voxels> *
                    | <volume per voxel>)
        -vl         | Volume of each integer label (<# voxels per label> *
                    | <volume per voxel>)
        -vp         | Volume of all probabilsitic voxels (sum(<in>) *
                    | <volume per voxel>)
        -n          | Count of all voxels above 0 (<# voxels>)
        -np         | Sum of all fuzzy voxels (sum(<in>))
        -e          | Entropy of all voxels
        -ne         | Normalized entropy of all voxels
        -x          | Location (i j k x y z) of the smallest value in the image
        -X          | Location (i j k x y z) of the largest value in the image
        -c          | Location (i j k x y z) of the centre of mass of the
                    | object
        -B          | Bounding box of all nonzero voxels
                    | [ xmin xsize ymin ysize zmin zsize ]
        -xvox       | Output the number of voxels in the x direction.
                    | Replace x with y/z for other directions.
        -xdim       | Output the voxel dimention in the x direction.
                    | Replace x with y/z for other directions.

    Note: All NaN or Inf are ignored for all stats.
          The -m and -t options can be used in conjusction.

    For source code, see http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg
    For Documentation, see:
        http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation

    Examples
    --------
    >>> from nipype.interfaces.niftyseg import UnaryStats
    >>> node = UnaryStats()
    >>> node.inputs.in_file = 'im1.nii'  # doctest: +SKIP
    >>> node.inputs.operation = 'v'
    >>> node.cmdline  # doctest: +SKIP
    'seg_stats im1.nii -v'

    """
    input_spec = UnaryStatsInput


class BinaryStatsInput(StatsInput):
    """Input Spec for seg_stats Binary operations."""
    operation = traits.Enum('p', 'sa', 'ss', 'svp', 'al', 'd', 'ncc', 'nmi',
                            'Vl', 'Nl',
                            mandatory=True,
                            argstr='-%s',
                            position=4,
                            desc='operation to perform')

    operand_file = File(exists=True,
                        argstr="%s",
                        mandatory=True,
                        position=5,
                        xor=["operand_value"],
                        desc="second image to perform operation with")

    operand_value = traits.Float(argstr='%.8f',
                                 mandatory=True,
                                 position=5,
                                 xor=["operand_file"],
                                 desc='value to perform operation with')


class BinaryStats(StatsCommand):
    """
    Interface for executable seg_stats from NiftySeg platform.

    Interface to use any binary statistical operations that can be performed
    with the seg_stats command-line program. See below for those operations:
        -p <float>      | The <float>th percentile of all voxels intensity
                        | (float=[0,100])
        -sa  <ax>       | Average of all voxels
        -ss  <ax>       | Standard deviation of all voxels
        -svp <ax>       | Volume of all probabilsitic voxels (sum(<in>) *
                        | <volume per voxel>)
        -al <in2>       | Average value in <in> for each label in <in2>
        -d <in2>        | Calculate the Dice score between all classes in <in>
                        | and <in2>
        -ncc <in2>      | Normalized cross correlation between <in> and <in2>
        -nmi <in2>      | Normalized Mutual Information between <in> and <in2>
        -Vl <csv>       | Volume of each integer label <in>. Save to <csv>file.
        -Nl <csv>       | Count of each label <in>. Save to <csv> file.

    Note: All NaN or Inf are ignored for all stats.
        The -m and -t options can be used in conjusction.

    For source code, see http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg
    For Documentation, see:
        http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation

    Examples
    --------
    >>> from nipype.interfaces.niftyseg import BinaryStats
    >>> node = BinaryStats()
    >>> node.inputs.in_file = 'im1.nii'  # doctest: +SKIP
    >>> node.inputs.operation = 'sa'
    >>> node.inputs.operand_value = 2.0
    >>> node.cmdline  # doctest: +SKIP
    'seg_stats im1.nii -sa 2'

    """
    input_spec = BinaryStatsInput
