# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provides interfaces to various commands provided by Camino
"""
import os
from nipype.interfaces.camino2trackvis.base import Camino2TrackvisCommand, Camino2TrackvisCommandInputSpec

import re
from glob import glob
from nibabel import load
from nipype.utils.filemanip import fname_presuffix, split_filename, copyfile
from nipype.utils.misc import isdefined
__docformat__ = 'restructuredtext'

from nipype.interfaces.base import (TraitedSpec, File, traits, CommandLine,
    CommandLineInputSpec)
	
class camino_to_trackvisInputSpec(Camino2TrackvisCommandInputSpec):
	"""
	camino_to_trackvis
	Convert files from camino .Bfloat format to trackvis .trk format.

	The input .Bfloat (camino) file.  If this option is not provided, data is read from stdin.
	-input

	Output: The filename to which to write the .trk (trackvis) file.
	-output

	The minimum length of tracts to output
	-min-length

	Three comma-separated integers giving the number of voxels along each dimension of the source scans.
	-data-dims

	Three comma-separated numbers giving the size of each voxel in mm.
	-voxel-dims

	Set the order in which various directions were stored.
	-voxel-order

	Specify with three letters consisting of one each from the pairs LR, AP, and SI.
	These stand for Left-Right, Anterior-Posterior, and Superior-Inferior.
	Whichever is specified in each position will be the direction of increasing order.
	Read coordinate system from a NIfTI file.
	"""

	in_file = File(exists=True, argstr='-i %s',
	mandatory=True, position=1,
	desc='big endian float tract file')
	
	out_file = File(exists=True, argstr='-o %s',
	mandatory=True, position=2, desc='Trackvis trk file name')
	
	diffusion_dims = File(exists=True, argstr='-d %s',
					mandatory=True, position=3,
					desc='Diffusion image dimensions in voxels, separated by commas')

	voxel_dims = File(exists=True, argstr='-d %s',
					mandatory=True, position=4,
					desc='Diffusion image dimensions in voxels, separated by commas')
					
class camino_to_trackvisOutputSpec(TraitedSpec):
	out_file = File(exists=True, desc='path/name of 4D volume in Trackvis format') 

class camino_to_trackvis(Camino2TrackvisCommand):
	_cmd = 'camino_to_trackvis'
	input_spec=camino_to_trackvisInputSpec
	output_spec=camino_to_trackvisOutputSpec
		
	def _list_outputs(self):
		out_prefix = self.inputs.out_prefix
		output_type = self.inputs.output_type
	
		outputs = self.output_spec().get()
		return outputs
	def _run_interface(self, runtime):
		if not isdefined(self.inputs.out_file):
		    self.inputs.out_file = self._gen_fname(self.inputs.in_file,suffix = '_trk')
		runtime = super(camino_to_trackvis, self)._run_interface(runtime)
		if runtime.stderr:
		    runtime.returncode = 1
		return runtime
	
	def _gen_filename(self, name):
		if name is 'out_file':
		    return self._list_outputs()['trackvis']
		else:
		    return None