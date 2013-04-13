# -*- coding: utf-8 -*-
from nipype.interfaces.base import (TraitedSpec, BaseInterface, BaseInterfaceInputSpec,
                                    File, isdefined, traits)
from nipype.utils.filemanip import split_filename
import os.path as op
import nibabel as nb
import numpy as np
from nipype.utils.misc import package_check
import warnings

from ... import logging
iflogger = logging.getLogger('interface')

try:
    package_check('dipy')
    import dipy.reconst.dti as dti
    from dipy.core.gradients import GradientTable
except Exception, e:
    warnings.warn('dipy not installed')


class TensorModeInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True,
    desc='The input diffusion-weighted image file')
    bvecs = File(exists=True, mandatory=True,
    desc='The input b-vector file')
    bvals = File(exists=True, mandatory=True,
    desc='The input b-value track file')
    out_filename = File('mode.nii', usedefault=True, desc='The output filename for the tracks in TrackVis (.trk) format')

class TensorModeOutputSpec(TraitedSpec):
    out_file = File(exists=True)

class TensorMode(BaseInterface):
	"""
	Creates a tract density image from a TrackVis track file using functions from dipy

	Example
	-------

	>>> import nipype.interfaces.dipy as dipy
	>>> mode = dipy.TensorMode()
	>>> mode.inputs.in_file = 'dwi.nii'
	>>> mode.run()                                   # doctest: +SKIP
	"""
	input_spec = TensorModeInputSpec
	output_spec = TensorModeOutputSpec

	def _run_interface(self, runtime):
		img=nb.load(self.inputs.in_file)
		data=img.get_data()
		affine=img.get_affine()

		bvals=np.loadtxt(self.inputs.bvals)
		gradients=np.loadtxt(self.inputs.bvecs).T

		gtab = GradientTable(gradients)
		gtab.bvals = bvals

		mask = data[..., 0] > 50
		tenmodel = dti.TensorModel(gtab)
		tenfit = tenmodel.fit(data, mask)

		mode_data = tenfit.mode
		img = nb.Nifti1Image(mode_data,affine)
		out_file = op.abspath(self.inputs.out_filename)
		nb.save(img, out_file)
		iflogger.info('Tensor mode image saved as {i}'.format(i=out_file))
		return runtime

	def _list_outputs(self):
		outputs = self._outputs().get()
		outputs['out_file'] = op.abspath(self.inputs.out_filename)
		return outputs

