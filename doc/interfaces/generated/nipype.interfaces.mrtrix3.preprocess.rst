.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.mrtrix3.preprocess
=============================


.. _nipype.interfaces.mrtrix3.preprocess.ResponseSD:


.. index:: ResponseSD

ResponseSD
----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mrtrix3/preprocess.py#L80>`__

Wraps command **dwi2response**

Generate an appropriate response function from the image data for
spherical deconvolution.

.. [1] Tax, C. M.; Jeurissen, B.; Vos, S. B.; Viergever, M. A. and
  Leemans, A., Recursive calibration of the fiber response function
  for spherical deconvolution of diffusion MRI data. NeuroImage,
  2014, 86, 67-80


Example
~~~~~~~

>>> import nipype.interfaces.mrtrix3 as mrt
>>> resp = mrt.ResponseSD()
>>> resp.inputs.in_file = 'dwi.mif'
>>> resp.inputs.in_mask = 'mask.nii.gz'
>>> resp.inputs.grad_fsl = ('bvecs', 'bvals')
>>> resp.cmdline                               # doctest: +ELLIPSIS
'dwi2response -fslgrad bvecs bvals -mask mask.nii.gz dwi.mif response.txt'
>>> resp.run()                                 # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                input diffusion weighted images
                flag: %s, position: -2
        out_file: (a file name, nipype default value: response.txt)
                output file containing SH coefficients
                flag: %s, position: -1

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        bval_scale: ('yes' or 'no')
                specifies whether the b - values should be scaled by the square of
                the corresponding DW gradient norm, as often required for multishell
                or DSI DW acquisition schemes. The default action can also be set in
                the MRtrix config file, under the BValueScaling entry. Valid choices
                are yes / no, true / false, 0 / 1 (default: true).
                flag: -bvalue_scaling %s
        disp_mult: (a float)
                dispersion of FOD lobe must not exceed some threshold as determined
                by this multiplier and the FOD dispersion in other single-fibre
                voxels. The threshold is: (mean + (multiplier * (mean - min)));
                default = 1.0. Criterion is only applied in second pass of RF
                estimation.
                flag: -dispersion_multiplier %f
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
        in_mask: (an existing file name)
                provide initial mask image
                flag: -mask %s
        int_mult: (a float)
                integral of FOD lobe must not be outside some range as determined by
                this multiplier and FOD lobe integral in other single-fibre voxels.
                The range is: (mean +- (multiplier * stdev)); default = 2.0.
                Criterion is only applied in second pass of RF estimation.
                flag: -integral_multiplier %f
        iterations: (an integer (int or long))
                maximum number of iterations per pass
                flag: -max_iters %d
        max_change: (a float)
                maximum percentile change in any response function coefficient; if
                no individual coefficient changes by more than this fraction, the
                algorithm is terminated.
                flag: -max_change %f
        max_sh: (an integer (int or long))
                maximum harmonic degree of response function
                flag: -lmax %d
        nthreads: (an integer (int or long))
                number of threads. if zero, the number of available cpus will be
                used
                flag: -nthreads %d
        out_sf: (a file name)
                write a mask containing single-fibre voxels
                flag: -sf %s
        shell: (a list of items which are a float)
                specify one or more dw gradient shells
                flag: -shell %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        test_all: (a boolean)
                re-test all voxels at every iteration
                flag: -test_all
        vol_ratio: (a float)
                maximal volume ratio between the sum of all other positive lobes in
                the voxel and the largest FOD lobe
                flag: -volume_ratio %f

Outputs::

        out_file: (an existing file name)
                the output response file
        out_sf: (a file name)
                mask containing single-fibre voxels
