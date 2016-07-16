.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.mrtrix3.tracking
===========================


.. _nipype.interfaces.mrtrix3.tracking.Tractography:


.. index:: Tractography

Tractography
------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mrtrix3/tracking.py#L192>`__

Wraps command **tckgen**

Performs streamlines tractography after selecting the appropriate
algorithm.

.. [FACT] Mori, S.; Crain, B. J.; Chacko, V. P. & van Zijl,
  P. C. M. Three-dimensional tracking of axonal projections in the
  brain by magnetic resonance imaging. Annals of Neurology, 1999,
  45, 265-269

.. [iFOD1] Tournier, J.-D.; Calamante, F. & Connelly, A. MRtrix:
  Diffusion tractography in crossing fiber regions. Int. J. Imaging
  Syst. Technol., 2012, 22, 53-66

.. [iFOD2] Tournier, J.-D.; Calamante, F. & Connelly, A. Improved
  probabilistic streamlines tractography by 2nd order integration
  over fibre orientation distributions. Proceedings of the
  International Society for Magnetic Resonance in Medicine, 2010, 1670

.. [Nulldist] Morris, D. M.; Embleton, K. V. & Parker, G. J.
  Probabilistic fibre tracking: Differentiation of connections from
  chance events. NeuroImage, 2008, 42, 1329-1339

.. [Tensor_Det] Basser, P. J.; Pajevic, S.; Pierpaoli, C.; Duda, J.
  and Aldroubi, A. In vivo fiber tractography using DT-MRI data.
  Magnetic Resonance in Medicine, 2000, 44, 625-632

.. [Tensor_Prob] Jones, D. Tractography Gone Wild: Probabilistic Fibre
  Tracking Using the Wild Bootstrap With Diffusion Tensor MRI. IEEE
  Transactions on Medical Imaging, 2008, 27, 1268-1274


Example
~~~~~~~

>>> import nipype.interfaces.mrtrix3 as mrt
>>> tk = mrt.Tractography()
>>> tk.inputs.in_file = 'fods.mif'
>>> tk.inputs.roi_mask = 'mask.nii.gz'
>>> tk.inputs.seed_sphere = (80, 100, 70, 10)
>>> tk.cmdline                               # doctest: +ELLIPSIS
'tckgen -algorithm iFOD2 -mask mask.nii.gz -seed_sphere 80.000000,100.000000,70.000000,10.000000 fods.mif tracked.tck'
>>> tk.run()                                 # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                input file to be processed
                flag: %s, position: -2
        out_file: (a file name, nipype default value: tracked.tck)
                output file containing tracks
                flag: %s, position: -1

        [Optional]
        act_file: (an existing file name)
                use the Anatomically-Constrained Tractography framework during
                tracking; provided image must be in the 5TT (five - tissue - type)
                format
                flag: -act %s
        algorithm: ('iFOD2' or 'FACT' or 'iFOD1' or 'Nulldist' or 'SD_Stream'
                 or 'Tensor_Det' or 'Tensor_Prob', nipype default value: iFOD2)
                tractography algorithm to be used
                flag: -algorithm %s
        angle: (a float)
                set the maximum angle between successive steps (default is 90deg x
                stepsize / voxelsize)
                flag: -angle %f
        args: (a string)
                Additional parameters to the command
                flag: %s
        backtrack: (a boolean)
                allow tracks to be truncated
                flag: -backtrack
        bval_scale: ('yes' or 'no')
                specifies whether the b - values should be scaled by the square of
                the corresponding DW gradient norm, as often required for multishell
                or DSI DW acquisition schemes. The default action can also be set in
                the MRtrix config file, under the BValueScaling entry. Valid choices
                are yes / no, true / false, 0 / 1 (default: true).
                flag: -bvalue_scaling %s
        crop_at_gmwmi: (a boolean)
                crop streamline endpoints more precisely as they cross the GM-WM
                interface
                flag: -crop_at_gmwmi
        cutoff: (a float)
                set the FA or FOD amplitude cutoff for terminating tracks (default
                is 0.1)
                flag: -cutoff %f
        cutoff_init: (a float)
                set the minimum FA or FOD amplitude for initiating tracks (default
                is the same as the normal cutoff)
                flag: -initcutoff %f
        downsample: (a float)
                downsample the generated streamlines to reduce output file size
                flag: -downsample %f
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        grad_file: (an existing file name)
                dw gradient scheme (MRTrix format
                flag: -grad %s
        grad_fsl: (a tuple of the form: (an existing file name, an existing
                 file name))
                (bvecs, bvals) dw gradient scheme (FSL format
                flag: -fslgrad %s %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        in_bval: (an existing file name)
                bvals file in FSL format
        in_bvec: (an existing file name)
                bvecs file in FSL format
                flag: -fslgrad %s %s
        init_dir: (a tuple of the form: (a float, a float, a float))
                specify an initial direction for the tracking (this should be
                supplied as a vector of 3 comma-separated values
                flag: -initdirection %f,%f,%f
        max_length: (a float)
                set the maximum length of any track in mm (default is 100 x
                voxelsize)
                flag: -maxlength %f
        max_seed_attempts: (an integer (int or long))
                set the maximum number of times that the tracking algorithm should
                attempt to find an appropriate tracking direction from a given seed
                point
                flag: -max_seed_attempts %d
        max_tracks: (an integer (int or long))
                set the maximum number of tracks to generate. The program will not
                generate more tracks than this number, even if the desired number of
                tracks hasn't yet been reached (default is 100 x number)
                flag: -maxnum %d
        min_length: (a float)
                set the minimum length of any track in mm (default is 5 x voxelsize)
                flag: -minlength %f
        n_samples: (an integer (int or long))
                set the number of FOD samples to take per step for the 2nd order
                (iFOD2) method
                flag: -samples %d
        n_tracks: (an integer (int or long))
                set the desired number of tracks. The program will continue to
                generate tracks until this number of tracks have been selected and
                written to the output file
                flag: -number %d
        n_trials: (an integer (int or long))
                set the maximum number of sampling trials at each point (only used
                for probabilistic tracking)
                flag: -trials %d
        noprecompt: (a boolean)
                do NOT pre-compute legendre polynomial values. Warning: this will
                slow down the algorithm by a factor of approximately 4
                flag: -noprecomputed
        nthreads: (an integer (int or long))
                number of threads. if zero, the number of available cpus will be
                used
                flag: -nthreads %d
        out_seeds: (a file name)
                output the seed location of all successful streamlines to a file
                flag: -output_seeds %s
        power: (an integer (int or long))
                raise the FOD to the power specified (default is 1/nsamples)
                flag: -power %d
        roi_excl: (an existing file name or a tuple of the form: (a float, a
                 float, a float, a float))
                specify an exclusion region of interest, streamlines that enter ANY
                exclude region will be discarded
                flag: -exclude %s
        roi_incl: (an existing file name or a tuple of the form: (a float, a
                 float, a float, a float))
                specify an inclusion region of interest, streamlines must traverse
                ALL inclusion regions to be accepted
                flag: -include %s
        roi_mask: (an existing file name or a tuple of the form: (a float, a
                 float, a float, a float))
                specify a masking region of interest. If defined,streamlines exiting
                the mask will be truncated
                flag: -mask %s
        seed_dynamic: (an existing file name)
                determine seed points dynamically using the SIFT model (must not
                provide any other seeding mechanism). Note that while this seeding
                mechanism improves the distribution of reconstructed streamlines
                density, it should NOT be used as a substitute for the SIFT method
                itself.
                flag: -seed_dynamic %s
        seed_gmwmi: (an existing file name)
                seed from the grey matter - white matter interface (only valid if
                using ACT framework)
                flag: -seed_gmwmi %s
                requires: act_file
        seed_grid_voxel: (a tuple of the form: (an existing file name, an
                 integer (int or long)))
                seed a fixed number of streamlines per voxel in a mask image; place
                seeds on a 3D mesh grid (grid_size argument is per axis; so a
                grid_size of 3 results in 27 seeds per voxel)
                flag: -seed_grid_per_voxel %s %d
                mutually_exclusive: seed_image, seed_rnd_voxel
        seed_image: (an existing file name)
                seed streamlines entirely at random within mask
                flag: -seed_image %s
        seed_rejection: (an existing file name)
                seed from an image using rejection sampling (higher values = more
                probable to seed from
                flag: -seed_rejection %s
        seed_rnd_voxel: (a tuple of the form: (an existing file name, an
                 integer (int or long)))
                seed a fixed number of streamlines per voxel in a mask image; random
                placement of seeds in each voxel
                flag: -seed_random_per_voxel %s %d
                mutually_exclusive: seed_image, seed_grid_voxel
        seed_sphere: (a tuple of the form: (a float, a float, a float, a
                 float))
                spherical seed
                flag: -seed_sphere %f,%f,%f,%f
        sph_trait: (a tuple of the form: (a float, a float, a float, a
                 float))
                flag: %f,%f,%f,%f
        step_size: (a float)
                set the step size of the algorithm in mm (default is 0.1 x
                voxelsize; for iFOD2: 0.5 x voxelsize)
                flag: -step %f
        stop: (a boolean)
                stop propagating a streamline once it has traversed all include
                regions
                flag: -stop
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        unidirectional: (a boolean)
                track from the seed point in one direction only (default is to track
                in both directions)
                flag: -unidirectional
        use_rk4: (a boolean)
                use 4th-order Runge-Kutta integration (slower, but eliminates
                curvature overshoot in 1st-order deterministic methods)
                flag: -rk4

Outputs::

        out_file: (an existing file name)
                the output filtered tracks
        out_seeds: (a file name)
                output the seed location of all successful streamlines to a file
