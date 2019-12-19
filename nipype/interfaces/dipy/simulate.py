# -*- coding: utf-8 -*-
from multiprocessing import Pool, cpu_count
import os.path as op

import numpy as np
import nibabel as nb

from ... import logging
from ..base import (
    traits,
    TraitedSpec,
    BaseInterfaceInputSpec,
    File,
    InputMultiPath,
    isdefined,
)
from .base import DipyBaseInterface

IFLOGGER = logging.getLogger("nipype.interface")


class SimulateMultiTensorInputSpec(BaseInterfaceInputSpec):
    in_dirs = InputMultiPath(
        File(exists=True), mandatory=True, desc="list of fibers (principal directions)"
    )
    in_frac = InputMultiPath(
        File(exists=True), mandatory=True, desc=("volume fraction of each fiber")
    )
    in_vfms = InputMultiPath(
        File(exists=True),
        mandatory=True,
        desc=("volume fractions of isotropic " "compartiments"),
    )
    in_mask = File(exists=True, desc="mask to simulate data")

    diff_iso = traits.List(
        [3000e-6, 960e-6, 680e-6],
        traits.Float,
        usedefault=True,
        desc="Diffusivity of isotropic compartments",
    )
    diff_sf = traits.Tuple(
        (1700e-6, 200e-6, 200e-6),
        traits.Float,
        traits.Float,
        traits.Float,
        usedefault=True,
        desc="Single fiber tensor",
    )

    n_proc = traits.Int(0, usedefault=True, desc="number of processes")
    baseline = File(exists=True, mandatory=True, desc="baseline T2 signal")
    gradients = File(exists=True, desc="gradients file")
    in_bvec = File(exists=True, desc="input bvecs file")
    in_bval = File(exists=True, desc="input bvals file")
    num_dirs = traits.Int(
        32,
        usedefault=True,
        desc=(
            "number of gradient directions (when table " "is automatically generated)"
        ),
    )
    bvalues = traits.List(
        traits.Int,
        value=[1000, 3000],
        usedefault=True,
        desc=("list of b-values (when table " "is automatically generated)"),
    )
    out_file = File(
        "sim_dwi.nii.gz",
        usedefault=True,
        desc="output file with fractions to be simluated",
    )
    out_mask = File(
        "sim_msk.nii.gz", usedefault=True, desc="file with the mask simulated"
    )
    out_bvec = File("bvec.sim", usedefault=True, desc="simulated b vectors")
    out_bval = File("bval.sim", usedefault=True, desc="simulated b values")
    snr = traits.Int(0, usedefault=True, desc="signal-to-noise ratio (dB)")


class SimulateMultiTensorOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="simulated DWIs")
    out_mask = File(exists=True, desc="mask file")
    out_bvec = File(exists=True, desc="simulated b vectors")
    out_bval = File(exists=True, desc="simulated b values")


class SimulateMultiTensor(DipyBaseInterface):
    """
    Interface to MultiTensor model simulator in dipy
    http://nipy.org/dipy/examples_built/simulate_multi_tensor.html

    Example
    -------

    >>> import nipype.interfaces.dipy as dipy
    >>> sim = dipy.SimulateMultiTensor()
    >>> sim.inputs.in_dirs = ['fdir00.nii', 'fdir01.nii']
    >>> sim.inputs.in_frac = ['ffra00.nii', 'ffra01.nii']
    >>> sim.inputs.in_vfms = ['tpm_00.nii.gz', 'tpm_01.nii.gz',
    ...                       'tpm_02.nii.gz']
    >>> sim.inputs.baseline = 'b0.nii'
    >>> sim.inputs.in_bvec = 'bvecs'
    >>> sim.inputs.in_bval = 'bvals'
    >>> sim.run()                                   # doctest: +SKIP
    """

    input_spec = SimulateMultiTensorInputSpec
    output_spec = SimulateMultiTensorOutputSpec

    def _run_interface(self, runtime):
        from dipy.core.gradients import gradient_table

        # Gradient table
        if isdefined(self.inputs.in_bval) and isdefined(self.inputs.in_bvec):
            # Load the gradient strengths and directions
            bvals = np.loadtxt(self.inputs.in_bval)
            bvecs = np.loadtxt(self.inputs.in_bvec).T
            gtab = gradient_table(bvals, bvecs)
        else:
            gtab = _generate_gradients(self.inputs.num_dirs, self.inputs.bvalues)
        ndirs = len(gtab.bvals)
        np.savetxt(op.abspath(self.inputs.out_bvec), gtab.bvecs.T)
        np.savetxt(op.abspath(self.inputs.out_bval), gtab.bvals)

        # Load the baseline b0 signal
        b0_im = nb.load(self.inputs.baseline)
        hdr = b0_im.header
        shape = b0_im.shape
        aff = b0_im.affine

        # Check and load sticks and their volume fractions
        nsticks = len(self.inputs.in_dirs)
        if len(self.inputs.in_frac) != nsticks:
            raise RuntimeError(
                ("Number of sticks and their volume fractions" " must match.")
            )

        # Volume fractions of isotropic compartments
        nballs = len(self.inputs.in_vfms)
        vfs = np.squeeze(nb.concat_images(self.inputs.in_vfms).dataobj)
        if nballs == 1:
            vfs = vfs[..., np.newaxis]
        total_vf = np.sum(vfs, axis=3)

        # Generate a mask
        if isdefined(self.inputs.in_mask):
            msk = np.asanyarray(nb.load(self.inputs.in_mask).dataobj)
            msk[msk > 0.0] = 1.0
            msk[msk < 1.0] = 0.0
        else:
            msk = np.zeros(shape)
            msk[total_vf > 0.0] = 1.0

        msk = np.clip(msk, 0.0, 1.0)
        nvox = len(msk[msk > 0])

        # Fiber fractions
        ffsim = nb.concat_images(self.inputs.in_frac)
        ffs = np.nan_to_num(np.squeeze(ffsim.dataobj))  # fiber fractions
        ffs = np.clip(ffs, 0.0, 1.0)
        if nsticks == 1:
            ffs = ffs[..., np.newaxis]

        for i in range(nsticks):
            ffs[..., i] *= msk

        total_ff = np.sum(ffs, axis=3)

        # Fix incongruencies in fiber fractions
        for i in range(1, nsticks):
            if np.any(total_ff > 1.0):
                errors = np.zeros_like(total_ff)
                errors[total_ff > 1.0] = total_ff[total_ff > 1.0] - 1.0
                ffs[..., i] -= errors
                ffs[ffs < 0.0] = 0.0
            total_ff = np.sum(ffs, axis=3)

        for i in range(vfs.shape[-1]):
            vfs[..., i] -= total_ff
        vfs = np.clip(vfs, 0.0, 1.0)

        fractions = np.concatenate((ffs, vfs), axis=3)

        nb.Nifti1Image(fractions, aff, None).to_filename("fractions.nii.gz")
        nb.Nifti1Image(np.sum(fractions, axis=3), aff, None).to_filename(
            "total_vf.nii.gz"
        )

        mhdr = hdr.copy()
        mhdr.set_data_dtype(np.uint8)
        mhdr.set_xyzt_units("mm", "sec")
        nb.Nifti1Image(msk, aff, mhdr).to_filename(op.abspath(self.inputs.out_mask))

        # Initialize stack of args
        fracs = fractions[msk > 0]

        # Stack directions
        dirs = None
        for i in range(nsticks):
            f = self.inputs.in_dirs[i]
            fd = np.nan_to_num(nb.load(f).dataobj)
            w = np.linalg.norm(fd, axis=3)[..., np.newaxis]
            w[w < np.finfo(float).eps] = 1.0
            fd /= w
            if dirs is None:
                dirs = fd[msk > 0].copy()
            else:
                dirs = np.hstack((dirs, fd[msk > 0]))

        # Add random directions for isotropic components
        for d in range(nballs):
            fd = np.random.randn(nvox, 3)
            w = np.linalg.norm(fd, axis=1)
            fd[w < np.finfo(float).eps, ...] = np.array([1.0, 0.0, 0.0])
            w[w < np.finfo(float).eps] = 1.0
            fd /= w[..., np.newaxis]
            dirs = np.hstack((dirs, fd))

        sf_evals = list(self.inputs.diff_sf)
        ba_evals = list(self.inputs.diff_iso)

        mevals = [sf_evals] * nsticks + [[ba_evals[d]] * 3 for d in range(nballs)]

        b0 = b0_im.get_fdata()[msk > 0]
        args = []
        for i in range(nvox):
            args.append(
                {
                    "fractions": fracs[i, ...].tolist(),
                    "sticks": [
                        tuple(dirs[i, j : j + 3]) for j in range(nsticks + nballs)
                    ],
                    "gradients": gtab,
                    "mevals": mevals,
                    "S0": b0[i],
                    "snr": self.inputs.snr,
                }
            )

        n_proc = self.inputs.n_proc
        if n_proc == 0:
            n_proc = cpu_count()

        try:
            pool = Pool(processes=n_proc, maxtasksperchild=50)
        except TypeError:
            pool = Pool(processes=n_proc)

        # Simulate sticks using dipy
        IFLOGGER.info(
            "Starting simulation of %d voxels, %d diffusion directions.",
            len(args),
            ndirs,
        )
        result = np.array(pool.map(_compute_voxel, args))
        if np.shape(result)[1] != ndirs:
            raise RuntimeError(
                ("Computed directions do not match number" "of b-values.")
            )

        signal = np.zeros((shape[0], shape[1], shape[2], ndirs))
        signal[msk > 0] = result

        simhdr = hdr.copy()
        simhdr.set_data_dtype(np.float32)
        simhdr.set_xyzt_units("mm", "sec")
        nb.Nifti1Image(signal.astype(np.float32), aff, simhdr).to_filename(
            op.abspath(self.inputs.out_file)
        )

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        outputs["out_mask"] = op.abspath(self.inputs.out_mask)
        outputs["out_bvec"] = op.abspath(self.inputs.out_bvec)
        outputs["out_bval"] = op.abspath(self.inputs.out_bval)

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
      <https://doi.org/10.1002/mrm.10209>`_.
    .. [Pierpaoli1996] Pierpaoli et al., Diffusion tensor MR imaging
      of the human brain, Radiology 201:637-648. 1996.
    """
    from dipy.sims.voxel import multi_tensor

    ffs = args["fractions"]
    gtab = args["gradients"]
    signal = np.zeros_like(gtab.bvals, dtype=np.float32)

    # Simulate dwi signal
    sf_vf = np.sum(ffs)
    if sf_vf > 0.0:
        ffs = (np.array(ffs) / sf_vf) * 100
        snr = args["snr"] if args["snr"] > 0 else None

        try:
            signal, _ = multi_tensor(
                gtab,
                args["mevals"],
                S0=args["S0"],
                angles=args["sticks"],
                fractions=ffs,
                snr=snr,
            )
        except Exception:
            pass

    return signal.tolist()


def _generate_gradients(ndirs=64, values=[1000, 3000], nb0s=1):
    """
    Automatically generate a `gradient table
    <http://nipy.org/dipy/examples_built/gradients_spheres.html#example-gradients-spheres>`_

    """
    import numpy as np
    from dipy.core.sphere import disperse_charges, Sphere, HemiSphere
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

    for i in range(0, nb0s):
        bvals = bvals.tolist()
        bvals.insert(0, 0)

        bvecs = bvecs.tolist()
        bvecs.insert(0, np.zeros(3))

    return gradient_table(bvals, bvecs)
