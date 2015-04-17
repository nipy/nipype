# -*- coding: utf-8 -*-
"""Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)
"""

from nipype.interfaces.base import (
    traits, TraitedSpec, BaseInterface, BaseInterfaceInputSpec, File,
    InputMultiPath, isdefined)
from nipype.utils.filemanip import split_filename
import os.path as op
import nibabel as nb
import numpy as np
from nipype.utils.misc import package_check
import warnings

from multiprocessing import (Process, Pool, cpu_count, pool,
                             Manager, TimeoutError)

from ... import logging
iflogger = logging.getLogger('interface')

have_dipy = True
try:
    package_check('dipy', version='0.8.0')
except Exception, e:
    have_dipy = False
else:
    import numpy as np
    from dipy.sims.voxel import (multi_tensor, add_noise,
                                 all_tensor_evecs)
    from dipy.core.gradients import gradient_table


class SimulateMultiTensorInputSpec(BaseInterfaceInputSpec):
    in_dirs = InputMultiPath(File(exists=True), mandatory=True,
                             desc='list of fibers (principal directions)')
    in_frac = InputMultiPath(File(exists=True), mandatory=True,
                             desc=('volume fraction of each fiber'))
    in_vfms = InputMultiPath(File(exists=True), mandatory=True,
                             desc='volume fraction map')
    in_mask = File(exists=True, desc='mask to simulate data')

    n_proc = traits.Int(0, usedefault=True, desc='number of processes')
    baseline = File(exists=True, mandatory=True, desc='baseline T2 signal')
    gradients = File(exists=True, desc='gradients file')
    bvec = File(exists=True, desc='bvecs file')
    bval = File(exists=True, desc='bvals file')
    num_dirs = traits.Int(32, usedefault=True,
                          desc=('number of gradient directions (when table '
                                'is automatically generated)'))
    bvalues = traits.List(traits.Int, value=[1000, 3000], usedefault=True,
                          desc=('list of b-values (when table '
                                'is automatically generated)'))
    out_file = File('sim_dwi.nii.gz', usedefault=True,
                    desc='output file with fractions to be simluated')
    out_mask = File('sim_msk.nii.gz', usedefault=True,
                    desc='file with the mask simulated')
    out_bvec = File('bvec.sim', usedefault=True, desc='simulated b vectors')
    out_bval = File('bval.sim', usedefault=True, desc='simulated b values')
    snr = traits.Int(30, usedefault=True, desc='signal-to-noise ratio (dB)')


class SimulateMultiTensorOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='simulated DWIs')
    out_mask = File(exists=True, desc='mask file')
    out_bvec = File(exists=True, desc='simulated b vectors')
    out_bval = File(exists=True, desc='simulated b values')


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

        ffsim = nb.concat_images([nb.load(f) for f in self.inputs.in_frac])
        ffs = np.squeeze(ffsim.get_data())  # fiber fractions

        vfsim = nb.concat_images([nb.load(f) for f in self.inputs.in_vfms])
        vfs = np.squeeze(vfsim.get_data())  # volume fractions

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

        args = np.hstack((vfs[msk > 0], ffs[msk > 0]))

        for f in self.inputs.in_dirs:
            fd = nb.load(f).get_data()
            args = np.hstack((args, fd[msk > 0]))

        b0 = np.array([b0_im.get_data()[msk > 0]]).T
        args = np.hstack((args, b0))

        if isdefined(self.inputs.bval) and isdefined(self.inputs.bvec):
            # Load the gradient strengths and directions
            bvals = np.loadtxt(self.inputs.bval)
            bvecs = np.loadtxt(self.inputs.bvec).T

            # Place in Dipy's preferred format
            gtab = gradient_table(bvals, bvecs)
        else:
            gtab = _generate_gradients(self.inputs.num_dirs,
                                       self.inputs.bvalues)

        np.savetxt(op.abspath(self.inputs.out_bvec), gtab.bvecs.T)
        np.savetxt(op.abspath(self.inputs.out_bval), gtab.bvals.T)

        snr = self.inputs.snr
        args = [tuple(np.hstack((r, gtab, snr))) for r in args]

        n_proc = self.inputs.n_proc
        if n_proc == 0:
            n_proc = cpu_count()

        try:
            pool = Pool(processes=n_proc, maxtasksperchild=50)
        except TypeError:
            pool = Pool(processes=n_proc)

        iflogger.info(('Starting simulation of %d voxels, %d diffusion'
                       ' directions.') % (len(args), len(gtab.bvals)))
        result = pool.map(_compute_voxel, args)
        ndirs = np.shape(result)[1]

        simulated = np.zeros((shape[0], shape[1], shape[2], ndirs))
        simulated[msk > 0] = result

        simhdr = hdr.copy()
        simhdr.set_data_dtype(np.float32)
        simhdr.set_xyzt_units('mm', 'sec')
        nb.Nifti1Image(simulated.astype(np.float32), aff,
                       simhdr).to_filename(op.abspath(self.inputs.out_file))

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        outputs['out_mask'] = op.abspath(self.inputs.out_mask)
        outputs['out_bvec'] = op.abspath(self.inputs.out_bvec)
        outputs['out_bval'] = op.abspath(self.inputs.out_bval)

        return outputs


def _compute_voxel(args):
    """
    Simulate DW signal for one voxel. Uses the multi-tensor model and
    three isotropic compartments.

    Apparent diffusivity tensors are taken from [Alexander2002]_
    and [Pierpaoli1996]_.

    .. [Alexander2002] Alexander et al., Detection and modeling of non-Gaussian
      apparent diffusion coefficient profiles in human brain data, MRM
      48(2):331-340, 2002, doi: `10.1002/mrm.10209
      <http://dx.doi.org/10.1002/mrm.10209>`_.
    .. [Pierpaoli1996] Pierpaoli et al., Diffusion tensor MR imaging
      of the human brain, Radiology 201:637-648. 1996.
    """
    D_ball = [3000e-6, 960e-6, 680e-6]
    sf_evals = [1700e-6, 200e-6, 200e-6]

    vfs = [args[0], args[1], args[2]]
    ffs = [args[3], args[4], args[5]]  # single fiber fractions
    sticks = [(args[6], args[7], args[8]),
              (args[8], args[10], args[11]),
              (args[12], args[13], args[14])]

    S0 = args[15]
    gtab = args[16]

    nf = len(ffs)
    mevals = [sf_evals] * nf
    sf_vf = np.sum(ffs)
    ffs = ((np.array(ffs) / sf_vf) * 100)

    # Simulate sticks
    signal, _ = multi_tensor(gtab, np.array(mevals), S0=1,
                             angles=sticks, fractions=ffs, snr=None)
    signal *= sf_vf

    # Simulate balls
    r = 1.0 - sf_vf
    if r > 1.0e-3:
        for vf, d in zip(vfs, D_ball):
            f0 = vf * r
            signal += f0 * np.exp(-gtab.bvals * d)

    snr = None
    try:
        snr = args[17]
    except IndexError:
        pass

    if snr is not None and snr >= 0:
        signal[1:] = add_noise(signal[1:], snr, 1)

    return signal * S0


def _generate_gradients(ndirs=64, values=[1000, 3000], nb0s=1):
    """
    Automatically generate a `gradient table
    <http://nipy.org/dipy/examples_built/gradients_spheres.html#example-gradients-spheres>`_

    """
    import numpy as np
    from dipy.core.sphere import (disperse_charges, Sphere, HemiSphere)
    from dipy.core.gradients import gradient_table

    theta = np.pi * np.random.rand(ndirs)
    phi = 2 * np.pi * np.random.rand(ndirs)
    hsph_initial = HemiSphere(theta=theta, phi=phi)
    hsph_updated, potential = disperse_charges(hsph_initial, 5000)

    values = np.atleast_1d(values).tolist()
    vertices = hsph_updated.vertices
    bvecs = vertices.copy()
    bvals = np.ones(vertices.shape[0]) * values[0]

    for v in values[1:]:
        bvecs = np.vstack((bvecs, vertices))
        bvals = np.hstack((bvals, v * np.ones(vertices.shape[0])))

    for i in xrange(0, nb0s):
        bvals = bvals.tolist()
        bvals.insert(0, 0)

        bvecs = bvecs.tolist()
        bvecs.insert(0, np.zeros(3))

    return gradient_table(bvals, bvecs)
