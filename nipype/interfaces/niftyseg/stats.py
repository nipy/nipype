# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    The stats module provides higher-level interfaces to some of the operations
    that can be performed with the niftysegstats (seg_stats) command-line program.
"""
import os
import numpy as np

from nipype.interfaces.niftyseg.base import NIFTYSEGCommand, NIFTYSEGCommandInputSpec
from nipype.interfaces.base import (TraitedSpec, File, traits, InputMultiPath,
                                    isdefined)

class StatsInput(NIFTYSEGCommandInputSpec):
    
    in_file = File(position=2, argstr="%s", exists=True, mandatory=True,
                desc="image to operate on")
    mask_file = File(exists=True, mandatory=False, position=-2, argstr="-m %s", desc="statistics within the masked area")
    
class StatsCommand(NIFTYSEGCommand):

    _cmd = "seg_stats"
    input_spec = StatsInput
    
class UnaryStatsInput(StatsInput):

    operation = traits.Enum("r", "R", "a", "s", "v", "vl", "V", 
                            "n", "N", "x", "X", "c", "B",
                            argstr="-%s", position=4, mandatory=True,
                            desc="operation to perform")


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
	  -r 		| The range <min max> of all voxels.
	  -R 		| The robust range (assuming 2% outliers on both sides) of all voxels

	Classical operations (datatype: all)
	  -a 		| Average of all voxels 
	  -s 		| Standard deviation of all voxels 
	  -v 		| Volume of all binarized voxels (<# voxels> * <volume per voxel>)
	  -vl 		| Volume of each integer label (<# voxels per label> * <volume per voxel>)
	  -V 		| Volume of all probabilsitic voxels (sum(<in>) * <volume per voxel>)
	  -n 		| Sum of all binarized voxels (<# voxels>)
	  -N 		| Sum of all probabilsitic voxels (sum(<in>))

	Coordinates operations (datatype: all)
	  -x 		| Location (in vox) of the smallest value in the image
	  -X 		| Location (in vox) of the largest value in the image
	  -c 		| Location (in vox) of the centre of mass of the object
	  -B 		| Bounding box of all nonzero voxels [ xmin xsize ymin ysize zmin zsize ]

    """
    input_spec = UnaryStatsInput

    def _list_outputs(self):
        self._suffix = "_" + self.inputs.operation
        return super(UnaryStats, self)._list_outputs()


class BinaryStatsInput(StatsInput):

    operation = traits.Enum("p", "d",
                            mandatory=True, argstr="-%s", position=4,
                            desc="operation to perform")
    operand_value = traits.Float(argstr="%.8f", mandatory=True, position=5,
                                 desc="value to perform operation with")


class BinaryStats(StatsCommand):

    """

    Use niftysegstats (seg_stats) to perorm a variety of mathematical binary operations on an image.
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
	  -p <float> 	| The <float>th percentile of all voxels intensity (float=[0,100])

	Label attribute operations (datatype: char or uchar)
	  -d <in2>	| Calculate the Dice score between all classes in <in> and <in2>

    """

    input_spec = BinaryStatsInput

