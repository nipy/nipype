# -*- coding: utf-8 -*-
"""Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)
"""
import nibabel as nb

from ..base import TraitedSpec, File, isdefined
from .base import DipyDiffusionInterface, DipyBaseInputSpec

from ... import logging
IFLOGGER = logging.getLogger('interface')


class DTIInputSpec(DipyBaseInputSpec):
    mask_file = File(exists=True,
                     desc='An optional white matter mask')


class DTIOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class DTI(DipyDiffusionInterface):
    """
    Calculates the diffusion tensor model parameters

    Example
    -------

    >>> import nipype.interfaces.dipy as dipy
    >>> dti = dipy.DTI()
    >>> dti.inputs.in_file = 'diffusion.nii'
    >>> dti.inputs.in_bvec = 'bvecs'
    >>> dti.inputs.in_bval = 'bvals'
    >>> dti.run()                                   # doctest: +SKIP
    """
    _input_spec = DTIInputSpec
    _output_spec = DTIOutputSpec

    def _run_interface(self, runtime):
        from dipy.reconst import dti
        from dipy.io.utils import nifti1_symmat
        gtab = self._get_gradient_table()

        img = nb.load(self.inputs.in_file)
        data = img.get_data()
        affine = img.affine
        mask = None
        if isdefined(self.inputs.mask_file):
            mask = nb.load(self.inputs.mask_file).get_data()

        # Fit it
        tenmodel = dti.TensorModel(gtab)
        ten_fit = tenmodel.fit(data, mask)
        lower_triangular = tenfit.lower_triangular()
        img = nifti1_symmat(lower_triangular, affine)
        out_file = self._gen_filename('dti')
        nb.save(img, out_file)
        IFLOGGER.info('DTI parameters image saved as {i}'.format(i=out_file))
        return runtime

    def _post_run(self):
        self.outputs.out_file = self._gen_filename('dti')
        

class TensorModeInputSpec(DipyBaseInputSpec):
    mask_file = File(exists=True,
                     desc='An optional white matter mask')


class TensorModeOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class TensorMode(DipyDiffusionInterface):

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
    >>> mode.inputs.in_bvec = 'bvecs'
    >>> mode.inputs.in_bval = 'bvals'
    >>> mode.run()                                   # doctest: +SKIP
    """
    _input_spec = TensorModeInputSpec
    _output_spec = TensorModeOutputSpec

    def _run_interface(self, runtime):
        from dipy.reconst import dti

        # Load the 4D image files
        img = nb.load(self.inputs.in_file)
        data = img.get_data()
        affine = img.get_affine()

        # Load the gradient strengths and directions
        gtab = self._get_gradient_table()

        # Mask the data so that tensors are not fit for
        # unnecessary voxels
        mask = data[..., 0] > 50

        # Fit the tensors to the data
        tenmodel = dti.TensorModel(gtab)
        tenfit = tenmodel.fit(data, mask)

        # Calculate the mode of each voxel's tensor
        mode_data = tenfit.mode

        # Write as a 3D Nifti image with the original affine
        img = nb.Nifti1Image(mode_data, affine)
        out_file = self._gen_filename('mode')
        nb.save(img, out_file)
        IFLOGGER.info('Tensor mode image saved as {i}'.format(i=out_file))
        return runtime

    def _post_run(self):
        self.outputs.out_file = self._gen_filename('mode')
        