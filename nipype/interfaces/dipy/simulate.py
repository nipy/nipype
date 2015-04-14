# -*- coding: utf-8 -*-
"""Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)
"""

from nipype.interfaces.base import (
    TraitedSpec, BaseInterface, BaseInterfaceInputSpec, File,
    InputMultiPath, isdefined)
from nipype.utils.filemanip import split_filename
import os.path as op
import nibabel as nb
import numpy as np
from nipype.utils.misc import package_check
import warnings

from ... import logging
iflogger = logging.getLogger('interface')

have_dipy = True
try:
    package_check('dipy', version='0.8.0')
except Exception, e:
    have_dipy = False
else:
    import numpy as np
    from dipy.sims.voxel import (multi_tensor,
                                 all_tensor_evecs)
    from dipy.core.gradients import GradientTable


class SimulateMultiTensorInputSpec(BaseInterfaceInputSpec):
    in_dirs = InputMultiPath(File(exists=True), mandatory=True,
                             desc='list of fibers (principal directions)')
    in_frac = InputMultiPath(File(exists=True), mandatory=True,
                             desc=('volume fraction of each fiber'))
    in_vfms = InputMultiPath(File(exists=True), mandatory=True,
                             desc='volume fraction map')
    in_mask = File(exists=True, desc='mask to simulate data')

    baseline = File(exists=True, mandatory=True, desc='baseline T2 signal')
    gradients = File(exists=True, desc='gradients file')
    bvec = File(exists=True, mandatory=True, desc='bvecs file')
    bval = File(exists=True, mandatory=True, desc='bvals file')
    out_file = File('sim_dwi.nii.gz', usedefault=True,
                    desc='output file with fractions to be simluated')
    out_mask = File('sim_msk.nii.gz', usedefault=True,
                    desc='file with the mask simulated')


class SimulateMultiTensorOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='simulated DWIs')
    out_mask = File(exists=True, desc='mask file')


class SimulateMultiTensor(BaseInterface):

    """
    Interface to MultiTensor model simulator in dipy
    http://nipy.org/dipy/examples_built/simulate_multi_tensor.html

    Example
    -------

    >>> import nipype.interfaces.dipy as dipy
    >>> sim = dipy.SimulateMultiTensor()
    >>> sim.inputs.in_dirs = 'fibers.nii'
    >>> sim.inputs.in_frac = 'fractions.nii'
    >>> sim.inputs.baseline = 'S0.nii'
    >>> sim.inputs.bvecs = 'bvecs'
    >>> sim.inputs.bvals = 'bvals'
    >>> sim.run()                                   # doctest: +SKIP
    """
    input_spec = SimulateMultiTensorInputSpec
    output_spec = SimulateMultiTensorOutputSpec

    def _run_interface(self, runtime):
        # Load the baseline b0 signal
        b0_im = nb.load(self.inputs.baseline)
        hdr = b0_im.get_header()
        shape = b0_im.get_shape()
        aff = b0_im.get_affine()
        b0 = b0_im.get_data().reshape(-1)

        ffsim = nb.concat_images([nb.load(f) for f in self.inputs.in_frac])
        ffs = np.squeeze(ffsim.get_data())  # fiber fractions

        vfsim = nb.concat_images([nb.load(f) for f in self.inputs.in_vfms])
        vfs = np.squeeze(vfsim.get_data())  # volume fractions

        # Load structural files
        thetas = []
        phis = []

        total_ff = np.sum(ffs, axis=3)
        total_vf = np.sum(vfs, axis=3)

        msk = np.zeros(shape, dtype=np.uint8)
        msk[(total_vf > 0.0) & (total_ff > 0.0)] = 1

        if isdefined(self.inputs.in_mask):
            msk = nb.load(self.inputs.in_mask).get_data()
            msk[msk > 0.0] = 1.0
            msk[msk < 1.0] = 0.0

        mhdr = hdr.copy()
        mhdr.set_data_dtype(np.uint8)
        mhdr.set_xyzt_units('mm', 'sec')
        nb.Nifti1Image(msk, aff, mhdr).to_filename(
            op.abspath(self.inputs.out_mask))

        for f in self.inputs.in_dirs:
            fd = nb.load(f).get_data()
            x = fd[msk > 0][..., 0]
            y = fd[msk > 0][..., 1]
            z = fd[msk > 0][..., 2]
            th = np.arccos(z / np.sqrt(x ** 2 + y ** 2 + z ** 2))
            ph = np.arctan2(y, x)
            thetas.append(th)
            phis.append(ph)

        # Load the gradient strengths and directions
        bvals = np.loadtxt(self.inputs.bval)
        gradients = np.loadtxt(self.inputs.bvec).T

        # Place in Dipy's preferred format
        gtab = GradientTable(gradients)
        gtab.bvals = bvals

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        outputs['out_mask'] = op.abspath(self.inputs.out_mask)
        return outputs


def _compute_voxel(vfs, ffs, ths, phs, S0, gtab, snr=None,
                   csf_evals=[0.0015, 0.0015, 0.0015],
                   gm_evals=[0.0007, 0.0007, 0.0007],
                   wm_evals=[0.0015, 0.0003, 0.0003]):

    nf = len(ffs)
    total_ff = np.sum(ffs)

    gm_vf = vfs[1] * (1 - total_ff) / (vfs[0] + vfs[1])
    ffs.insert(0, gm_vf)
    csf_vf = vfs[0] * (1 - total_ff) / (vfs[0] + vfs[1])
    ffs.insert(0, csf_vf)
    angles = [(0, 0), (0, 0)]  # angles of gm and csf
    angles += [(th, ph) for ph, th in zip(ths, phs)]

    mevals = np.array([csf_evals, gm_evals] + [wm_evals] * nf)
    ffs = np.array(ffs) * 100
    signal, sticks = multi_tensor(gtab, mevals, S0=S0, angles=angles,
                                  fractions=ffs, snr=snr)
    return signal, sticks
