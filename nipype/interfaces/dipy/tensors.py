# -*- coding: utf-8 -*-
"""Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)
"""

from nipype.interfaces.base import (
    TraitedSpec, BaseInterface, File, traits)
from nipype.utils.filemanip import split_filename
import os.path as op
import nibabel as nb
import numpy as np
from nipype.utils.misc import package_check

from ... import logging
iflogger = logging.getLogger('interface')

have_dipy = True
try:
    package_check('dipy', version='0.6.0')
except Exception, e:
    have_dipy = False
else:
    import dipy.reconst.dti as dti
    from dipy.core.gradients import GradientTable
    from dipy.reconst.vec_val_sum import vec_val_vect


_ut_indices = np.array([[0, 1, 2],
                        [1, 3, 4],
                        [2, 4, 5]])


def from_upper_triangular(D):
    """ Returns a tensor given the six unique tensor elements

    Given the six unique tensor elments (in the order: Dxx, Dxy, Dxz, Dyy, Dyz,
    Dzz) returns a 3 by 3 tensor. All elements after the sixth are ignored.

    Parameters
    -----------
    D : array_like, (..., >6)
        Unique elements of the tensors

    Returns
    --------
    tensor : ndarray (..., 3, 3)
        3 by 3 tensors

    """
    return D[..., _ut_indices]


_ut_rows = np.array([0, 0, 0, 1, 1, 2])
_ut_cols = np.array([0, 1, 2, 1, 2, 2])


def upper_triangular(tensor, b0=None):
    """
    Returns the six upper triangular values of the tensor and a dummy variable
    if b0 is not None

    Parameters
    ----------
    tensor : array_like (..., 3, 3)
        a collection of 3, 3 diffusion tensors
    b0 : float
        if b0 is not none log(b0) is returned as the dummy variable

    Returns
    -------
    D : ndarray
        If b0 is none, then the shape will be (..., 6) otherwise (..., 7)

    """
    if tensor.shape[-2:] != (3, 3):
        raise ValueError("Diffusion tensors should be (..., 3, 3)")
    if b0 is None:
        return tensor[..., _ut_rows, _ut_cols]
    else:
        D = np.empty(tensor.shape[:-2] + (7,), dtype=tensor.dtype)
        D[..., 6] = -np.log(b0)
        D[..., :6] = tensor[..., _ut_rows, _ut_cols]
        return D


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
        # Load the 4D image files
        img = nb.load(self.inputs.in_file)
        data = img.get_data()
        affine = img.get_affine()

        # Load the gradient strengths and directions
        bvals = np.loadtxt(self.inputs.bvals)
        gradients = np.loadtxt(self.inputs.bvecs).T

        # Place in Dipy's preferred format
        gtab = GradientTable(gradients)
        gtab.bvals = bvals

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


class EstimateConductivityInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True,
                   desc='The input 4D diffusion-tensor image file')
    lower_triangular_input = traits.Bool(False, usedefault=True,
        desc='if True, the input tensor is considered to be stored in lower triangular form.')
    lower_triangular_output = traits.Bool(True, usedefault=True,
        desc='if True, the output tensor is stored in lower triangular form.')
    use_outlier_correction = traits.Bool(False, usedefault=True,
        desc='if True, conductivity eigenvalues are bounded to a \
        maximum of 0.4 [S/m]')
    volume_normalized_mapping = traits.Bool(False, usedefault=True,
        desc='if True, uses volume-normalized mapping from [2]_.')
    sigma_white_matter = traits.Float(0.126, usedefault=True, units = 'NA',
                desc="Conductivity for white matter (default: 0.126 [S/m])")
    eigenvalue_scaling_factor = traits.Float(237.5972, usedefault=True, units = 'NA',
                desc="scaling factor used by the direct mapping between \
                    DTI and conductivity tensors")
    out_filename = File(
        genfile=True, desc='The output filename for the conductivity tensor image')


class EstimateConductivityOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class EstimateConductivity(BaseInterface):

    """
    Estimates electrical conductivity from a set of diffusion-weighted
    images, as well as their associated b-values and b-vectors. Calculates
    conductivity with Dipy. Saves the conductivity tensors in lower
    triangular 4D image form.

    Tensors are assumed to be in the white matter of a human brain and
    a default conductivity value and eigenvalue scaling factor is included.
    Options are provided for correcting implausibly high conductivity values
    to a maximum value (0.4 [S/m]). Direct mapping of the tensor [1]_.,
    as well as volume-normalized mapping [2]_., are supported. Adapted
    from the SimNibs package [3]_.

    References
    ----------

    .. [1] Tuch, D. S., Wedeen, V. J., Dale, A. M., George, J. S., and
        Belliveau, J. W., "Conductivity tensor mapping of the human
        brain using diffusion tensor MRI" in Proceedings of the National
        Academy of Sciences 98, 11697–11701, 2001

    .. [2] Güllmar, D., Haueisen, J., and Reichenbach, J. R., "Influence of
        anisotropic electrical conductivity in white matter tissue on
        the EEG/MEG forward and inverse solution. A high-resolution
        whole head simulation study", NeuroImage 51, 145–163, 2010.

    .. [3] Windhoff, M., Opitz, A., and Thielscher A., "Electric field
        calculations in brain stimulation based on finite elements:
        An optimized processing pipeline for the generation and usage of
        accurate individual head models", Human Brain Mapping, 2011.


    Example
    -------

    >>> import nipype.interfaces.dipy as dipy
    >>> conduct = dipy.EstimateConductivity()
    >>> conduct.inputs.in_file = 'diffusion.nii'
    >>> conduct.run()                                   # doctest: +SKIP
    """
    input_spec = EstimateConductivityInputSpec
    output_spec = EstimateConductivityOutputSpec

    def _run_interface(self, runtime):
        # Load the 4D image files
        img = nb.load(self.inputs.in_file)
        data = img.get_data()
        affine = img.get_affine()

        if self.inputs.lower_triangular_input:
            try:
                dti_params = dti.eig_from_lo_tri(data)
            except:
                dti_params = dti.tensor_eig_from_lo_tri(data)

        else:
            data = np.asarray(data)
            data_flat = data.reshape((-1, data.shape[-1]))
            dti_params = np.empty((len(data_flat), 4, 3))

            for ii in range(len(data_flat)):
                tensor = from_upper_triangular(data_flat[ii])
                evals, evecs = dti.decompose_tensor(tensor)
                dti_params[ii, 0] = evals
                dti_params[ii, 1:] = evecs

            dti_params.shape = data.shape[:-1] + (12,)

        evals = dti_params[..., :3]
        evecs = dti_params[..., 3:]

        evecs = evecs.reshape(np.shape(evecs)[:3] + (3,3))


        ### Estimate electrical conductivity

        evals = abs(self.inputs.eigenvalue_scaling_factor * evals)

        if self.inputs.volume_normalized_mapping:
            # Calculate the cube root of the product of the three eigenvalues (for
            # normalization)
            denominator = np.power(
                (evals[..., 0] * evals[..., 1] * evals[..., 2]), (1 / 3))
            # Calculate conductivity and normalize the eigenvalues
            evals = self.inputs.sigma_white_matter * evals / denominator
            evals[denominator < 0.0001] = self.inputs.sigma_white_matter

        # Threshold outliers that show unusually high conductivity
        if self.inputs.use_outlier_correction:
            evals[evals > 0.4] = 0.4

        conductivity_quadratic = np.array(vec_val_vect(evecs, evals))

        if self.inputs.lower_triangular_output:
            conductivity_data = dti.lower_triangular(conductivity_quadratic)
        else:
            conductivity_data = upper_triangular(conductivity_quadratic)

        # Write as a 4D Nifti tensor image with the original affine
        img = nb.Nifti1Image(conductivity_data, affine=affine)
        out_file = op.abspath(self._gen_outfilename())
        nb.save(img, out_file)
        iflogger.info('Conductivity tensor image saved as {i}'.format(i=out_file))
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
        return name + '_conductivity.nii.gz'
