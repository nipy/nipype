# -*- coding: utf-8 -*-
"""Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)
"""
import os.path as op
import warnings

import nibabel as nb
import numpy as np

from ..base import (TraitedSpec, BaseInterface, File)
from ...utils.filemanip import split_filename
from ...utils.misc import package_check
from ... import logging
iflogger = logging.getLogger('interface')

have_dipy = True
try:
    package_check('dipy', version='0.6.0')
except Exception as e:
    have_dipy = False
else:
    import dipy.reconst.dti as dti
    from dipy.core.gradients import gradient_table
    from dipy.io.utils import nifti1_symmat


def tensor_fitting(data, bvals, bvecs, mask_file=None):
    """
    Use dipy to fit DTI

    Parameters
    ----------
    in_file : str
        Full path to a DWI data file.
    bvals : str
        Full path to a file containing gradient magnitude information (b-values).
    bvecs : str
        Full path to a file containing gradient direction information (b-vectors).
    mask_file : str, optional
        Full path to a file containing a binary mask. Defaults to use the entire volume.

    Returns
    -------
    TensorFit object, affine
    """
    img = nb.load(in_file)
    data = img.get_data()
    affine = img.affine
    if mask_file is not None:
        mask = nb.load(self.inputs.mask_file).get_data()
    else:
        mask = None

    # Load information about the gradients:
    gtab = grad.gradient_table(self.inputs.bvals, self.inputs.bvecs)

    # Fit it
    tenmodel = dti.TensorModel(gtab)
    return tenmodel.fit(data, mask), affine


class DTIInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True,
                   desc='The input 4D diffusion-weighted image file')
    bvecs = File(exists=True, mandatory=True,
                 desc='The input b-vector text file')
    bvals = File(exists=True, mandatory=True,
                 desc='The input b-value text file')
    mask_file = File(exists=True,
                     desc='An optional white matter mask')
    out_filename = File(
        genfile=True, desc='The output filename for the DTI parameters image')


class DTIOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class DTI(BaseInterface):
    """
    Calculates the diffusion tensor model parameters

    Example
    -------

    >>> import nipype.interfaces.dipy as dipy
    >>> dti = dipy.DTI()
    >>> dti.inputs.in_file = 'diffusion.nii'
    >>> dti.inputs.bvecs = 'bvecs'
    >>> dti.inputs.bvals = 'bvals'
    >>> dti.run()                                   # doctest: +SKIP
    """
    input_spec = DTIInputSpec
    output_spec = DTIOutputSpec

    def _run_interface(self, runtime):
        ten_fit, affine = tensor_fitting(self.inputs.in_file,
                                         self.inputs.bvals,
                                         self.inputs.bvecs,
                                         self.inputs.mask_file)
        lower_triangular = tenfit.lower_triangular()
        img = nifti1_symmat(lower_triangular, affine)
        out_file = op.abspath(self._gen_outfilename())
        nb.save(img, out_file)
        iflogger.info('DTI parameters image saved as {i}'.format(i=out_file))
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
        return name + '_dti.nii'


class TensorModeInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True,
                   desc='The input 4D diffusion-weighted image file')
    bvecs = File(exists=True, mandatory=True,
                 desc='The input b-vector text file')
    bvals = File(exists=True, mandatory=True,
                 desc='The input b-value text file')
    mask_file = File(exists=True,
                     desc='An optional white matter mask')
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
        ten_fit = tensor_fitting(self.inputs.in_file, self.inputs.bvals, self.inputs.bvecs,
                                 self.inputs.mask_file)

        # Write as a 3D Nifti image with the original affine
        img = nb.Nifti1Image(tenfit.mode, affine)
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
