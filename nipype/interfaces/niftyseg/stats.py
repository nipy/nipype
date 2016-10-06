# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The stats module provides higher-level interfaces to some of the operations
that can be performed with the niftysegstats (seg_stats) command-line program.
"""
import numpy as np

from nipype.interfaces.niftyseg.base import NIFTYSEGCommand, \
                    NIFTYSEGCommandInputSpec, getNiftySegPath
from nipype.interfaces.base import (TraitedSpec, File, traits)


class StatsInput(NIFTYSEGCommandInputSpec):
    in_file = File(position=2, argstr='%s', exists=True, mandatory=True,
                   desc='image to operate on')
    mask_file = File(exists=True, mandatory=False, position=-2, argstr='-m %s',
                     desc='statistics within the masked area')


class StatsOutput(TraitedSpec):
    output = traits.Array(desc='Output array from seg_stats')


class StatsCommand(NIFTYSEGCommand):
    _cmd = getNiftySegPath('seg_stats')
    input_spec = StatsInput
    output_spec = StatsOutput


class UnaryStatsInput(StatsInput):
    operation = traits.Enum('r', 'R', 'a', 's', 'v', 'vl', 'vp', 'n', 'np',
                            'e', 'ne', 'x', 'X', 'c', 'B', 'xvox', 'xdim',
                            argstr='-%s', position=4, mandatory=True,
                            desc='operation to perform')


class UnaryStats(StatsCommand):
    """
    Use niftysegstats (seg_stats) to calculate statistics on an image.
    mandatory input specs is in_file

    Note: All NaN or Inf are ignored for all stats.
          The -m and -t options can be used in conjusction.

    Examples
    --------
    from nipype.interfaces.niftyseg import UnaryStats
    calculator = UnaryStats()
    calculator.inputs.in_file = "T1.nii.gz"
    calculator.inputs.operation = "v"
    calculator.cmdline
    seg_stats T1.nii.gz -v

    available operations:

    * * Statistics (at least one option is mandatory) * *
        Range operations (datatype: all)
        -r     		| The range <min max> of all voxels.
        -R     		| The robust range (assuming 2% outliers on both sides)
                      of all voxels

    Classical statistics (datatype: all)
        -a     		| Average of all voxels
        -s     		| Standard deviation of all voxels
        -v     		| Volume of all voxels above 0 (<# voxels> *
                      <volume per voxel>)
        -vl    		| Volume of each integer label (<# voxels per label> *
                      <volume per voxel>)
        -vp    		| Volume of all probabilsitic voxels (sum(<in>) *
                      <volume per voxel>)
        -n     		| Count of all voxels above 0 (<# voxels>)
        -np    		| Sum of all fuzzy voxels (sum(<in>))
        -e     		| Entropy of all voxels
        -ne    		| Normalized entropy of all voxels

    Coordinates operations (datatype: all)
        -x     		| Location (i j k x y z) of the smallest value in the image
        -X     		| Location (i j k x y z) of the largest value in the image
        -c     		| Location (i j k x y z) of the centre of mass of the object
        -B     		| Bounding box of all nonzero voxels
                        [ xmin xsize ymin ysize zmin zsize ]

    Header info (datatype: all)
        -xvox  		| Output the number of voxels in the x direction.
                      Replace x with y/z for other directions.
        -xdim  		| Output the voxel dimention in the x direction.
                      Replace x with y/z for other directions.

    """
    input_spec = UnaryStatsInput

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


class BinaryStatsInput(StatsInput):
    operation = traits.Enum('p', 'd', 'al', 'ncc', 'nmi', 'sa', 'ss', 'svp',
                            mandatory=True, argstr='-%s', position=4,
                            desc='operation to perform')
    operand_file = File(exists=True, argstr="%s", mandatory=True, position=5,
                        xor=["operand_value"],
                        desc="second image to perform operation with")
    operand_value = traits.Float(argstr='%.8f', mandatory=True, position=5,
                                 xor=["operand_file"],
                                 desc='value to perform operation with')


class BinaryStats(StatsCommand):
    """
    Use seg_stats to perform a variety of mathematical binary operations.
    mandatory input specs is operation and (operand_file or operand_value)

    Note: All NaN or Inf are ignored for all stats.
        The -m and -t options can be used in conjusction.
    Examples
    --------
    from nipype.interfaces.niftyseg import UnaryStats
    calculator = UnaryStats()
    calculator.inputs.in_file = "T1.nii.gz"
    calculator.inputs.operation = "v"
    calculator.cmdline
    seg_stats T1.nii.gz -v

    available operations:

    Range operations (datatype: all)
        -p <float> 	| The <float>th percentile of all voxels intensity
                      (float=[0,100])

    Classical statistics per slice along axis <ax> (ax=1,2,3)
        -sa  <ax>      	| Average of all voxels
        -ss  <ax>      	| Standard deviation of all voxels
        -svp <ax>      	| Volume of all probabilsitic voxels (sum(<in>) *
                          <volume per voxel>)

    Label attribute operations (datatype: char or uchar)
        -al <in2>      	| Average value in <in> for each label in <in2>
        -d <in2>	    | Calculate the Dice score between all classes in <in>
                          and <in2>

    Image similarities (datatype: all)
        -ncc <in2>     	| Normalized cross correlation between <in> and <in2>
        -nmi <in2>     	| Normalized Mutual Information between <in> and <in2>
    """
    input_spec = BinaryStatsInput
