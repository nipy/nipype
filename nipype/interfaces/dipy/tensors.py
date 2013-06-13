# -*- coding: utf-8 -*-
"""Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)
"""

from nipype.interfaces.base import (
    TraitedSpec, BaseInterface, File)
from nipype.utils.filemanip import split_filename
import os.path as op
import nibabel as nb
import numpy as np
from nipype.utils.misc import package_check
import warnings

from ... import logging
iflogger = logging.getLogger('interface')

try:
    package_check('dipy', version='0.7.0')
    import dipy.reconst.dti as dti
    from dipy.core.gradients import GradientTable
except Exception, e:
    warnings.warn('dipy not installed')


class TensorModeInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True,
                   desc='The input 4D diffusion-weighted image file')
    bvecs = File(exists=True, mandatory=True,
                 desc='The input b-vector text file')
    bvals = File(exists=True, mandatory=True,
                 desc='The input b-value text file')
    out_filename = File(
        genfile=True, desc='The output filename for the Tensor mode image')


class TensorModeOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class TensorMode(BaseInterface):
    """
    Creates a map of the mode of the diffusion tensors given a set of
    diffusion-weighted images, as well as their associated b-values and
    b-vectors. Fits the diffusion tensors and calculates tensor mode
    with Dipy.

    .. [1] Daniel B. Ennis and G. Kindlmann, "Orthogonal Tensor
        Invariants and the Analysis of Diffusion Tensor Magnetic Resonance
        Images", Magnetic Resonance in Medicine, vol. 55, no. 1, pp. 136-146,
        2006.

    Example
    -------

    >>> import nipype.interfaces.dipy as dipy
    >>> mode = dipy.TensorMode()
    >>> mode.inputs.in_file = 'diffusion.nii'
    >>> mode.inputs.bvecs = 'bvecs'
    >>> mode.inputs.bvals = 'bvals'
    >>> mode.run()                                   # doctest: +SKIP
    """
    input_spec = TensorModeInputSpec
    output_spec = TensorModeOutputSpec

    def _run_interface(self, runtime):
        ## Load the 4D image files
        img = nb.load(self.inputs.in_file)
        data = img.get_data()
        affine = img.get_affine()

        ## Load the gradient strengths and directions
        bvals = np.loadtxt(self.inputs.bvals)
        gradients = np.loadtxt(self.inputs.bvecs).T

        ## Place in Dipy's preferred format
        gtab = GradientTable(gradients)
        gtab.bvals = bvals

        ## Mask the data so that tensors are not fit for
        ## unnecessary voxels
        mask = data[..., 0] > 50

        ## Fit the tensors to the data
        tenmodel = dti.TensorModel(gtab)
        tenfit = tenmodel.fit(data, mask)

        ## Calculate the mode of each voxel's tensor
        mode_data = tenfit.mode

        ## Write as a 3D Nifti image with the original affine
        img = nb.Nifti1Image(mode_data, affine)
        out_file = op.abspath(self._gen_outfilename())
        nb.save(img, out_file)
        iflogger.info('Tensor mode image saved as {i}'.format(i=out_file))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = op.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + '_mode.nii'
