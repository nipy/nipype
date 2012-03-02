# -*- coding: utf-8 -*-
from nipype.interfaces.base import (TraitedSpec, BaseInterface, BaseInterfaceInputSpec,
                                    File, isdefined, traits)
from nipype.utils.filemanip import split_filename
import os, os.path as op
import nibabel as nb, nibabel.trackvis as trk
import numpy as np
import logging
from nipype.utils.misc import package_check
import warnings

logging.basicConfig()
iflogger = logging.getLogger('interface')

try:
    package_check('dipy')
    from dipy.tracking.utils import density_map
except Exception, e:
    warnings.warn('dipy not installed')


class TrackDensityMapInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True,
    desc='The input TrackVis track file')
    voxel_dims = traits.List(traits.Float, minlen=3, maxlen=3,
    desc='The size of each voxel in mm.')
    data_dims = traits.List(traits.Int, minlen=3, maxlen=3,
    desc='The size of the image in voxels.')
    out_filename = File('tdi.nii', usedefault=True, desc='The output filename for the tracks in TrackVis (.trk) format')

class TrackDensityMapOutputSpec(TraitedSpec):
    out_file = File(exists=True)

class TrackDensityMap(BaseInterface):
	"""
	Creates a tract density image from a TrackVis track file using functions from dipy

	Example
	-------

	>>> import nipype.interfaces.dipy as dipy
	>>> trk2tdi = dipy.TrackDensityMap()
	>>> trk2tdi.inputs.in_file = 'converted.trk'
	>>> trk2tdi.run()                                   # doctest: +SKIP
	"""
	input_spec = TrackDensityMapInputSpec
	output_spec = TrackDensityMapOutputSpec

	def _run_interface(self, runtime):
		tracks, header = trk.read(self.inputs.in_file)
		if not isdefined(self.inputs.data_dims):
			data_dims = header['dim']
		else:
			data_dims = self.inputs.data_dims

		if not isdefined(self.inputs.voxel_dims):
			voxel_size = header['voxel_size']
		else:
			voxel_size = self.inputs.voxel_dims

		affine = header['vox_to_ras']

		streams = ((ii[0]) for ii in tracks)
		data = density_map(streams, data_dims, voxel_size)
		if data.max() < 2**15:
		   data = data.astype('int16')

		img = nb.Nifti1Image(data,affine)
		out_file = op.abspath(self.inputs.out_filename)
		nb.save(img, out_file)
		iflogger.info('Track density map saved as {i}'.format(i=out_file))
		iflogger.info('Data Dimensions {d}'.format(d=data_dims))
		iflogger.info('Voxel Dimensions {v}'.format(v=voxel_size))
		return runtime

	def _list_outputs(self):
		outputs = self._outputs().get()
		outputs['out_file'] = op.abspath(self.inputs.out_filename)
		return outputs

