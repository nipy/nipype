.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.dipy.simulate
========================


.. _nipype.interfaces.dipy.simulate.SimulateMultiTensor:


.. index:: SimulateMultiTensor

SimulateMultiTensor
-------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/dipy/simulate.py#L82>`__

Interface to MultiTensor model simulator in dipy
http://nipy.org/dipy/examples_built/simulate_multi_tensor.html

Example
~~~~~~~

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

Inputs::

        [Mandatory]
        baseline: (an existing file name)
                baseline T2 signal
        in_dirs: (a list of items which are an existing file name)
                list of fibers (principal directions)
        in_frac: (a list of items which are an existing file name)
                volume fraction of each fiber
        in_vfms: (a list of items which are an existing file name)
                volume fractions of isotropic compartiments

        [Optional]
        bvalues: (a list of items which are an integer (int or long), nipype
                 default value: [1000, 3000])
                list of b-values (when table is automatically generated)
        diff_iso: (a list of items which are a float, nipype default value:
                 [0.003, 0.00096, 0.00068])
                Diffusivity of isotropic compartments
        diff_sf: (a tuple of the form: (a float, a float, a float), nipype
                 default value: (0.0017, 0.0002, 0.0002))
                Single fiber tensor
        gradients: (an existing file name)
                gradients file
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        in_bval: (an existing file name)
                input bvals file
        in_bvec: (an existing file name)
                input bvecs file
        in_mask: (an existing file name)
                mask to simulate data
        n_proc: (an integer (int or long), nipype default value: 0)
                number of processes
        num_dirs: (an integer (int or long), nipype default value: 32)
                number of gradient directions (when table is automatically
                generated)
        out_bval: (a file name, nipype default value: bval.sim)
                simulated b values
        out_bvec: (a file name, nipype default value: bvec.sim)
                simulated b vectors
        out_file: (a file name, nipype default value: sim_dwi.nii.gz)
                output file with fractions to be simluated
        out_mask: (a file name, nipype default value: sim_msk.nii.gz)
                file with the mask simulated
        snr: (an integer (int or long), nipype default value: 0)
                signal-to-noise ratio (dB)

Outputs::

        out_bval: (an existing file name)
                simulated b values
        out_bvec: (an existing file name)
                simulated b vectors
        out_file: (an existing file name)
                simulated DWIs
        out_mask: (an existing file name)
                mask file
