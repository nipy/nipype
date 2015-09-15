.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.mrtrix3.reconst
==========================


.. _nipype.interfaces.mrtrix3.reconst.EstimateFOD:


.. index:: EstimateFOD

EstimateFOD
-----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mrtrix3/reconst.py#L132>`__

Wraps command **dwi2fod**

Convert diffusion-weighted images to tensor images

Note that this program makes use of implied symmetries in the diffusion
profile. First, the fact the signal attenuation profile is real implies
that it has conjugate symmetry, i.e. Y(l,-m) = Y(l,m)* (where * denotes
the complex conjugate). Second, the diffusion profile should be
antipodally symmetric (i.e. S(x) = S(-x)), implying that all odd l
components should be zero. Therefore, this program only computes the even
elements.

Note that the spherical harmonics equations used here differ slightly from
those conventionally used, in that the (-1)^m factor has been omitted.
This should be taken into account in all subsequent calculations.
The spherical harmonic coefficients are stored as follows. First, since
the signal attenuation profile is real, it has conjugate symmetry, i.e.
Y(l,-m) = Y(l,m)* (where * denotes the complex conjugate). Second, the
diffusion profile should be antipodally symmetric (i.e. S(x) = S(-x)),
implying that all odd l components should be zero. Therefore, only the
even elements are computed.

Note that the spherical harmonics equations used here differ slightly from
those conventionally used, in that the (-1)^m factor has been omitted.
This should be taken into account in all subsequent calculations.
Each volume in the output image corresponds to a different spherical
harmonic component. Each volume will correspond to the following:

volume 0: l = 0, m = 0
volume 1: l = 2, m = -2 (imaginary part of m=2 SH)
volume 2: l = 2, m = -1 (imaginary part of m=1 SH)
volume 3: l = 2, m = 0
volume 4: l = 2, m = 1 (real part of m=1 SH)
volume 5: l = 2, m = 2 (real part of m=2 SH)
etc...



Example
~~~~~~~

>>> import nipype.interfaces.mrtrix3 as mrt
>>> fod = mrt.EstimateFOD()
>>> fod.inputs.in_file = 'dwi.mif'
>>> fod.inputs.response = 'response.txt'
>>> fod.inputs.in_mask = 'mask.nii.gz'
>>> fod.inputs.grad_fsl = ('bvecs', 'bvals')
>>> fod.cmdline                               # doctest: +ELLIPSIS
'dwi2fod -fslgrad bvecs bvals -mask mask.nii.gz dwi.mif response.txt fods.mif'
>>> fod.run()                                 # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                input diffusion weighted images
                flag: %s, position: -3
        out_file: (a file name, nipype default value: fods.mif)
                the output spherical harmonics coefficients image
                flag: %s, position: -1
        response: (an existing file name)
                a text file containing the diffusion-weighted signal response
                function coefficients for a single fibre population
                flag: %s, position: -2

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
        in_dirs: (an existing file name)
                specify the directions over which to apply the non-negativity
                constraint (by default, the built-in 300 direction set is used).
                These should be supplied as a text file containing the [ az el ]
                pairs for the directions.
                flag: -directions %s
        in_mask: (an existing file name)
                provide initial mask image
                flag: -mask %s
        max_sh: (an integer (int or long))
                maximum harmonic degree of response function
                flag: -lmax %d
        n_iter: (an integer (int or long))
                the maximum number of iterations to perform for each voxel
                flag: -niter %d
        neg_lambda: (a float)
                the regularisation parameter lambda that controls the strength of
                the non-negativity constraint
                flag: -neg_lambda %f
        nthreads: (an integer (int or long))
                number of threads. if zero, the number of available cpus will be
                used
                flag: -nthreads %d
        sh_filter: (an existing file name)
                the linear frequency filtering parameters used for the initial
                linear spherical deconvolution step (default = [ 1 1 1 0 0 ]). These
                should be supplied as a text file containing the filtering
                coefficients for each even harmonic order.
                flag: -filter %s
        shell: (a list of items which are a float)
                specify one or more dw gradient shells
                flag: -shell %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        thres: (a float)
                the threshold below which the amplitude of the FOD is assumed to be
                zero, expressed as an absolute amplitude
                flag: -threshold %f

Outputs::

        out_file: (an existing file name)
                the output response file

.. _nipype.interfaces.mrtrix3.reconst.FitTensor:


.. index:: FitTensor

FitTensor
---------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mrtrix3/reconst.py#L51>`__

Wraps command **dwi2tensor**

Convert diffusion-weighted images to tensor images


Example
~~~~~~~

>>> import nipype.interfaces.mrtrix3 as mrt
>>> tsr = mrt.FitTensor()
>>> tsr.inputs.in_file = 'dwi.mif'
>>> tsr.inputs.in_mask = 'mask.nii.gz'
>>> tsr.inputs.grad_fsl = ('bvecs', 'bvals')
>>> tsr.cmdline                               # doctest: +ELLIPSIS
'dwi2tensor -fslgrad bvecs bvals -mask mask.nii.gz dwi.mif dti.mif'
>>> tsr.run()                                 # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                input diffusion weighted images
                flag: %s, position: -2
        out_file: (a file name, nipype default value: dti.mif)
                the output diffusion tensor image
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
                only perform computation within the specified binary brain mask
                image
                flag: -mask %s
        method: ('nonlinear' or 'loglinear' or 'sech' or 'rician')
                select method used to perform the fitting
                flag: -method %s
        nthreads: (an integer (int or long))
                number of threads. if zero, the number of available cpus will be
                used
                flag: -nthreads %d
        reg_term: (a float)
                specify the strength of the regularisation term on the magnitude of
                the tensor elements (default = 5000). This only applies to the non-
                linear methods
                flag: -regularisation %f
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        out_file: (an existing file name)
                the output DTI file
