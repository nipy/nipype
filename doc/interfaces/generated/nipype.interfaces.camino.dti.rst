.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.camino.dti
=====================


.. _nipype.interfaces.camino.dti.ComputeEigensystem:


.. index:: ComputeEigensystem

ComputeEigensystem
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L995>`__

Wraps command **dteig**

Computes the eigensystem from tensor fitted data.

Reads diffusion tensor (single, two-tensor, three-tensor or multitensor) data from the
standard input, computes the eigenvalues and eigenvectors of each tensor and outputs the
results to the standard output. For multiple-tensor data the program outputs the
eigensystem of each tensor. For each tensor the program outputs: {l_1, e_11, e_12, e_13,
l_2, e_21, e_22, e_33, l_3, e_31, e_32, e_33}, where l_1 >= l_2 >= l_3 and e_i = (e_i1,
e_i2, e_i3) is the eigenvector with eigenvalue l_i. For three-tensor data, for example,
the output contains thirty-six values per voxel.

Example
~~~~~~~

>>> import nipype.interfaces.camino as cmon
>>> dteig = cmon.ComputeEigensystem()
>>> dteig.inputs.in_file = 'tensor_fitted_data.Bdouble'
>>> dteig.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                Tensor-fitted data filename
                flag: < %s, position: 1

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputdatatype: ('double' or 'float' or 'long' or 'int' or 'short' or
                 'char', nipype default value: double)
                Specifies the data type of the input data. The data type can be any
                of the following strings: "char", "short", "int", "long", "float" or
                "double".Default is double data type
                flag: -inputdatatype %s
        inputmodel: ('dt' or 'multitensor')
                Specifies the model that the input data contains parameters for.
                Possible model types are: "dt" (diffusion-tensor data) and
                "multitensor"
                flag: -inputmodel %s
        maxcomponents: (an integer (int or long))
                The maximum number of tensor components in a voxel of the input
                data.
                flag: -maxcomponents %d
        out_file: (a file name)
                flag: > %s, position: -1
        outputdatatype: ('double' or 'float' or 'long' or 'int' or 'short' or
                 'char', nipype default value: double)
                Specifies the data type of the output data. The data type can be any
                of the following strings: "char", "short", "int", "long", "float" or
                "double".Default is double data type
                flag: -outputdatatype %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        eigen: (an existing file name)
                Trace of the diffusion tensor

.. _nipype.interfaces.camino.dti.ComputeFractionalAnisotropy:


.. index:: ComputeFractionalAnisotropy

ComputeFractionalAnisotropy
---------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L877>`__

Wraps command **fa**

Computes the fractional anisotropy of tensors.

Reads diffusion tensor (single, two-tensor or three-tensor) data from the standard input,
computes the fractional anisotropy (FA) of each tensor and outputs the results to the
standard output. For multiple-tensor data the program outputs the FA of each tensor,
so for three-tensor data, for example, the output contains three fractional anisotropy
values per voxel.

Example
~~~~~~~

>>> import nipype.interfaces.camino as cmon
>>> fa = cmon.ComputeFractionalAnisotropy()
>>> fa.inputs.in_file = 'tensor_fitted_data.Bdouble'
>>> fa.inputs.scheme_file = 'A.scheme'
>>> fa.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                Tensor-fitted data filename
                flag: < %s, position: 1

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputdatatype: ('char' or 'short' or 'int' or 'long' or 'float' or
                 'double')
                Specifies the data type of the input file. The data type can be any
                of thefollowing strings: "char", "short", "int", "long", "float" or
                "double".
                flag: -inputdatatype %s
        inputmodel: ('dt' or 'twotensor' or 'threetensor' or 'multitensor')
                Specifies the model that the input tensor data contains parameters
                for.Possible model types are: "dt" (diffusion-tensor data),
                "twotensor" (two-tensor data), "threetensor" (three-tensor data). By
                default, the program assumes that the input data contains a single
                diffusion tensor in each voxel.
                flag: -inputmodel %s
        out_file: (a file name)
                flag: > %s, position: -1
        outputdatatype: ('char' or 'short' or 'int' or 'long' or 'float' or
                 'double')
                Specifies the data type of the output data. The data type can be any
                of thefollowing strings: "char", "short", "int", "long", "float" or
                "double".
                flag: -outputdatatype %s
        scheme_file: (an existing file name)
                Camino scheme file (b values / vectors, see camino.fsl2scheme)
                flag: %s, position: 2
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        fa: (an existing file name)
                Fractional Anisotropy Map

.. _nipype.interfaces.camino.dti.ComputeMeanDiffusivity:


.. index:: ComputeMeanDiffusivity

ComputeMeanDiffusivity
----------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L824>`__

Wraps command **md**

Computes the mean diffusivity (trace/3) from diffusion tensors.

Example
~~~~~~~

>>> import nipype.interfaces.camino as cmon
>>> md = cmon.ComputeMeanDiffusivity()
>>> md.inputs.in_file = 'tensor_fitted_data.Bdouble'
>>> md.inputs.scheme_file = 'A.scheme'
>>> md.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                Tensor-fitted data filename
                flag: < %s, position: 1

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputdatatype: ('char' or 'short' or 'int' or 'long' or 'float' or
                 'double')
                Specifies the data type of the input file. The data type can be any
                of thefollowing strings: "char", "short", "int", "long", "float" or
                "double".
                flag: -inputdatatype %s
        inputmodel: ('dt' or 'twotensor' or 'threetensor')
                Specifies the model that the input tensor data contains parameters
                for.Possible model types are: "dt" (diffusion-tensor data),
                "twotensor" (two-tensor data), "threetensor" (three-tensor data). By
                default, the program assumes that the input data contains a single
                diffusion tensor in each voxel.
                flag: -inputmodel %s
        out_file: (a file name)
                flag: > %s, position: -1
        outputdatatype: ('char' or 'short' or 'int' or 'long' or 'float' or
                 'double')
                Specifies the data type of the output data. The data type can be any
                of thefollowing strings: "char", "short", "int", "long", "float" or
                "double".
                flag: -outputdatatype %s
        scheme_file: (an existing file name)
                Camino scheme file (b values / vectors, see camino.fsl2scheme)
                flag: %s, position: 2
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        md: (an existing file name)
                Mean Diffusivity Map

.. _nipype.interfaces.camino.dti.ComputeTensorTrace:


.. index:: ComputeTensorTrace

ComputeTensorTrace
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L936>`__

Wraps command **trd**

Computes the trace of tensors.

Reads diffusion tensor (single, two-tensor or three-tensor) data from the standard input,
computes the trace of each tensor, i.e., three times the mean diffusivity, and outputs
the results to the standard output. For multiple-tensor data the program outputs the
trace of each tensor, so for three-tensor data, for example, the output contains three
values per voxel.

Divide the output by three to get the mean diffusivity.

Example
~~~~~~~

>>> import nipype.interfaces.camino as cmon
>>> trace = cmon.ComputeTensorTrace()
>>> trace.inputs.in_file = 'tensor_fitted_data.Bdouble'
>>> trace.inputs.scheme_file = 'A.scheme'
>>> trace.run()                 # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                Tensor-fitted data filename
                flag: < %s, position: 1

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputdatatype: ('char' or 'short' or 'int' or 'long' or 'float' or
                 'double')
                Specifies the data type of the input file. The data type can be any
                of thefollowing strings: "char", "short", "int", "long", "float" or
                "double".
                flag: -inputdatatype %s
        inputmodel: ('dt' or 'twotensor' or 'threetensor' or 'multitensor')
                Specifies the model that the input tensor data contains parameters
                for.Possible model types are: "dt" (diffusion-tensor data),
                "twotensor" (two-tensor data), "threetensor" (three-tensor data). By
                default, the program assumes that the input data contains a single
                diffusion tensor in each voxel.
                flag: -inputmodel %s
        out_file: (a file name)
                flag: > %s, position: -1
        outputdatatype: ('char' or 'short' or 'int' or 'long' or 'float' or
                 'double')
                Specifies the data type of the output data. The data type can be any
                of thefollowing strings: "char", "short", "int", "long", "float" or
                "double".
                flag: -outputdatatype %s
        scheme_file: (an existing file name)
                Camino scheme file (b values / vectors, see camino.fsl2scheme)
                flag: %s, position: 2
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        trace: (an existing file name)
                Trace of the diffusion tensor

.. _nipype.interfaces.camino.dti.DTIFit:


.. index:: DTIFit

DTIFit
------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L34>`__

Wraps command **dtfit**

Reads diffusion MRI data, acquired using the acquisition scheme detailed in the scheme file, from the data file.

Use non-linear fitting instead of the default linear regression to the log measurements.
The data file stores the diffusion MRI data in voxel order with the measurements stored in big-endian format and ordered as in the scheme file.
The default input data type is four-byte float. The default output data type is eight-byte double.
See modelfit and camino for the format of the data file and scheme file.
The program fits the diffusion tensor to each voxel and outputs the results,
in voxel order and as big-endian eight-byte doubles, to the standard output.
The program outputs eight values in each voxel: [exit code, ln(S(0)), D_xx, D_xy, D_xz, D_yy, D_yz, D_zz].
An exit code of zero indicates no problems. For a list of other exit codes, see modelfit(1). The entry S(0) is an estimate of the signal at q=0.

Example
~~~~~~~

>>> import nipype.interfaces.camino as cmon
>>> fit = cmon.DTIFit()
>>> fit.inputs.scheme_file = 'A.scheme'
>>> fit.inputs.in_file = 'tensor_fitted_data.Bdouble'
>>> fit.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                voxel-order data filename
                flag: %s, position: 1
        scheme_file: (an existing file name)
                Camino scheme file (b values / vectors, see camino.fsl2scheme)
                flag: %s, position: 2

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        bgmask: (an existing file name)
                Provides the name of a file containing a background mask computed
                using, for example, FSL bet2 program. The mask file contains zero in
                background voxels and non-zero in foreground.
                flag: -bgmask %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        non_linear: (a boolean)
                Use non-linear fitting instead of the default linear regression to
                the log measurements.
                flag: -nonlinear, position: 3
        out_file: (a file name)
                flag: > %s, position: -1
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        tensor_fitted: (an existing file name)
                path/name of 4D volume in voxel order

.. _nipype.interfaces.camino.dti.DTLUTGen:


.. index:: DTLUTGen

DTLUTGen
--------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L297>`__

Wraps command **dtlutgen**

Calibrates the PDFs for PICo probabilistic tractography.

This program needs to be run once for every acquisition scheme.
It outputs a lookup table that is used by the dtpicoparams program to find PICo PDF parameters for an image.
The default single tensor LUT contains parameters of the Bingham distribution and is generated by supplying
a scheme file and an estimated signal to noise in white matter regions of the (q=0) image.
The default inversion is linear (inversion index 1).

Advanced users can control several options, including the extent and resolution of the LUT,
the inversion index, and the type of PDF. See dtlutgen(1) for details.

Example
~~~~~~~

>>> import nipype.interfaces.camino as cmon
>>> dtl = cmon.DTLUTGen()
>>> dtl.inputs.snr = 16
>>> dtl.inputs.scheme_file = 'A.scheme'
>>> dtl.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]
        scheme_file: (a file name)
                The scheme file of the images to be processed using this LUT.
                flag: -schemefile %s, position: 2

        [Optional]
        acg: (a boolean)
                Compute a LUT for the ACG PDF.
                flag: -acg
        args: (a string)
                Additional parameters to the command
                flag: %s
        bingham: (a boolean)
                Compute a LUT for the Bingham PDF. This is the default.
                flag: -bingham
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        frange: (a list of from 2 to 2 items which are a float)
                Index to two-tensor LUTs. This is the fractional anisotropy of the
                two tensors. The default is 0.3 to 0.94
                flag: -frange %s, position: 1
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inversion: (an integer (int or long))
                Index of the inversion to use. The default is 1 (linear single
                tensor inversion).
                flag: -inversion %d
        lrange: (a list of from 2 to 2 items which are a float)
                Index to one-tensor LUTs. This is the ratio L1/L3 and L2 / L3.The
                LUT is square, with half the values calculated (because L2 / L3
                cannot be less than L1 / L3 by definition).The minimum must be >= 1.
                For comparison, a ratio L1 / L3 = 10 with L2 / L3 = 1 corresponds to
                an FA of 0.891, and L1 / L3 = 15 with L2 / L3 = 1 corresponds to an
                FA of 0.929. The default range is 1 to 10.
                flag: -lrange %s, position: 1
        out_file: (a file name)
                flag: > %s, position: -1
        samples: (an integer (int or long))
                The number of synthetic measurements to generate at each point in
                the LUT. The default is 2000.
                flag: -samples %d
        snr: (a float)
                The signal to noise ratio of the unweighted (q = 0)
                measurements.This should match the SNR (in white matter) of the
                images that the LUTs are used with.
                flag: -snr %f
        step: (a float)
                Distance between points in the LUT.For example, if lrange is 1 to 10
                and the step is 0.1, LUT entries will be computed at L1 / L3 = 1,
                1.1, 1.2 ... 10.0 and at L2 / L3 = 1.0, 1.1 ... L1 / L3.For single
                tensor LUTs, the default step is 0.2, for two-tensor LUTs it is
                0.02.
                flag: -step %f
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        trace: (a float)
                Trace of the diffusion tensor(s) used in the test function in the
                LUT generation. The default is 2100E-12 m^2 s^-1.
                flag: -trace %G
        watson: (a boolean)
                Compute a LUT for the Watson PDF.
                flag: -watson

Outputs::

        dtLUT: (an existing file name)
                Lookup Table

.. _nipype.interfaces.camino.dti.DTMetric:


.. index:: DTMetric

DTMetric
--------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L104>`__

Wraps command **dtshape**

Computes tensor metric statistics based on the eigenvalues l1 >= l2 >= l3
typically obtained from ComputeEigensystem.

The full list of statistics is:

 - <cl> = (l1 - l2) / l1 , a measure of linearity
 - <cp> = (l2 - l3) / l1 , a measure of planarity
 - <cs> = l3 / l1 , a measure of isotropy
   with: cl + cp + cs = 1
 - <l1> = first eigenvalue
 - <l2> = second eigenvalue
 - <l3> = third eigenvalue
 - <tr> = l1 + l2 + l3
 - <md> = tr / 3
 - <rd> = (l2 + l3) / 2
 - <fa> = fractional anisotropy. (Basser et al, J Magn Reson B 1996)
 - <ra> = relative anisotropy (Basser et al, J Magn Reson B 1996)
 - <2dfa> = 2D FA of the two minor eigenvalues l2 and l3
   i.e. sqrt( 2 * [(l2 - <l>)^2 + (l3 - <l>)^2] / (l2^2 + l3^2) )
   with: <l> = (l2 + l3) / 2


Example
~~~~~~~
Compute the CP planar metric as float data type.

>>> import nipype.interfaces.camino as cam
>>> dtmetric = cam.DTMetric()
>>> dtmetric.inputs.eigen_data = 'dteig.Bdouble'
>>> dtmetric.inputs.metric = 'cp'
>>> dtmetric.inputs.outputdatatype = 'float'
>>> dtmetric.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]
        eigen_data: (an existing file name)
                voxel-order data filename
                flag: -inputfile %s
        metric: ('fa' or 'md' or 'rd' or 'l1' or 'l2' or 'l3' or 'tr' or 'ra'
                 or '2dfa' or 'cl' or 'cp' or 'cs')
                Specifies the metric to compute. Possible choices are: "fa", "md",
                "rd", "l1", "l2", "l3", "tr", "ra", "2dfa", "cl", "cp" or "cs".
                flag: -stat %s

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        data_header: (an existing file name)
                A Nifti .nii or .nii.gz file containing the header information.
                Usually this will be the header of the raw data file from which the
                diffusion tensors were reconstructed.
                flag: -header %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputdatatype: ('double' or 'float' or 'long' or 'int' or 'short' or
                 'char', nipype default value: double)
                Specifies the data type of the input data. The data type can be any
                of the following strings: "char", "short", "int", "long", "float" or
                "double".Default is double data type
                flag: -inputdatatype %s
        outputdatatype: ('double' or 'float' or 'long' or 'int' or 'short' or
                 'char', nipype default value: double)
                Specifies the data type of the output data. The data type can be any
                of the following strings: "char", "short", "int", "long", "float" or
                "double".Default is double data type
                flag: -outputdatatype %s
        outputfile: (a file name)
                Output name. Output will be a .nii.gz file if data_header is
                provided andin voxel order with outputdatatype datatype (default:
                double) otherwise.
                flag: -outputfile %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        metric_stats: (an existing file name)
                Diffusion Tensor statistics of the chosen metric

.. _nipype.interfaces.camino.dti.ModelFit:


.. index:: ModelFit

ModelFit
--------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L220>`__

Wraps command **modelfit**

Fits models of the spin-displacement density to diffusion MRI measurements.

This is an interface to various model fitting routines for diffusion MRI data that
fit models of the spin-displacement density function. In particular, it will fit the
diffusion tensor to a set of measurements as well as various other models including
two or three-tensor models. The program can read input data from a file or can
generate synthetic data using various test functions for testing and simulations.

Example
~~~~~~~

>>> import nipype.interfaces.camino as cmon
>>> fit = cmon.ModelFit()
>>> fit.model = 'dt'
>>> fit.inputs.scheme_file = 'A.scheme'
>>> fit.inputs.in_file = 'tensor_fitted_data.Bdouble'
>>> fit.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                voxel-order data filename
                flag: -inputfile %s
        model: ('dt' or 'restore' or 'algdt' or 'nldt_pos' or 'nldt' or
                 'ldt_wtd' or 'adc' or 'ball_stick' or 'cylcyl dt' or 'cylcyl
                 restore' or 'cylcyl algdt' or 'cylcyl nldt_pos' or 'cylcyl nldt' or
                 'cylcyl ldt_wtd' or 'cylcyl adc' or 'cylcyl ball_stick' or
                 'cylcyl_eq dt' or 'cylcyl_eq restore' or 'cylcyl_eq algdt' or
                 'cylcyl_eq nldt_pos' or 'cylcyl_eq nldt' or 'cylcyl_eq ldt_wtd' or
                 'cylcyl_eq adc' or 'cylcyl_eq ball_stick' or 'pospos dt' or 'pospos
                 restore' or 'pospos algdt' or 'pospos nldt_pos' or 'pospos nldt' or
                 'pospos ldt_wtd' or 'pospos adc' or 'pospos ball_stick' or
                 'pospos_eq dt' or 'pospos_eq restore' or 'pospos_eq algdt' or
                 'pospos_eq nldt_pos' or 'pospos_eq nldt' or 'pospos_eq ldt_wtd' or
                 'pospos_eq adc' or 'pospos_eq ball_stick' or 'poscyl dt' or 'poscyl
                 restore' or 'poscyl algdt' or 'poscyl nldt_pos' or 'poscyl nldt' or
                 'poscyl ldt_wtd' or 'poscyl adc' or 'poscyl ball_stick' or
                 'poscyl_eq dt' or 'poscyl_eq restore' or 'poscyl_eq algdt' or
                 'poscyl_eq nldt_pos' or 'poscyl_eq nldt' or 'poscyl_eq ldt_wtd' or
                 'poscyl_eq adc' or 'poscyl_eq ball_stick' or 'cylcylcyl dt' or
                 'cylcylcyl restore' or 'cylcylcyl algdt' or 'cylcylcyl nldt_pos' or
                 'cylcylcyl nldt' or 'cylcylcyl ldt_wtd' or 'cylcylcyl adc' or
                 'cylcylcyl ball_stick' or 'cylcylcyl_eq dt' or 'cylcylcyl_eq
                 restore' or 'cylcylcyl_eq algdt' or 'cylcylcyl_eq nldt_pos' or
                 'cylcylcyl_eq nldt' or 'cylcylcyl_eq ldt_wtd' or 'cylcylcyl_eq adc'
                 or 'cylcylcyl_eq ball_stick' or 'pospospos dt' or 'pospospos
                 restore' or 'pospospos algdt' or 'pospospos nldt_pos' or 'pospospos
                 nldt' or 'pospospos ldt_wtd' or 'pospospos adc' or 'pospospos
                 ball_stick' or 'pospospos_eq dt' or 'pospospos_eq restore' or
                 'pospospos_eq algdt' or 'pospospos_eq nldt_pos' or 'pospospos_eq
                 nldt' or 'pospospos_eq ldt_wtd' or 'pospospos_eq adc' or
                 'pospospos_eq ball_stick' or 'posposcyl dt' or 'posposcyl restore'
                 or 'posposcyl algdt' or 'posposcyl nldt_pos' or 'posposcyl nldt' or
                 'posposcyl ldt_wtd' or 'posposcyl adc' or 'posposcyl ball_stick' or
                 'posposcyl_eq dt' or 'posposcyl_eq restore' or 'posposcyl_eq algdt'
                 or 'posposcyl_eq nldt_pos' or 'posposcyl_eq nldt' or 'posposcyl_eq
                 ldt_wtd' or 'posposcyl_eq adc' or 'posposcyl_eq ball_stick' or
                 'poscylcyl dt' or 'poscylcyl restore' or 'poscylcyl algdt' or
                 'poscylcyl nldt_pos' or 'poscylcyl nldt' or 'poscylcyl ldt_wtd' or
                 'poscylcyl adc' or 'poscylcyl ball_stick' or 'poscylcyl_eq dt' or
                 'poscylcyl_eq restore' or 'poscylcyl_eq algdt' or 'poscylcyl_eq
                 nldt_pos' or 'poscylcyl_eq nldt' or 'poscylcyl_eq ldt_wtd' or
                 'poscylcyl_eq adc' or 'poscylcyl_eq ball_stick')
                Specifies the model to be fit to the data.
                flag: -model %s
        scheme_file: (an existing file name)
                Camino scheme file (b values / vectors, see camino.fsl2scheme)
                flag: -schemefile %s

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        bgmask: (an existing file name)
                Provides the name of a file containing a background mask computed
                using, for example, FSL's bet2 program. The mask file contains zero
                in background voxels and non-zero in foreground.
                flag: -bgmask %s
        bgthresh: (a float)
                Sets a threshold on the average q=0 measurement to separate
                foreground and background. The program does not process background
                voxels, but outputs the same number of values in background voxels
                and foreground voxels. Each value is zero in background voxels apart
                from the exit code which is -1.
                flag: -bgthresh %G
        cfthresh: (a float)
                Sets a threshold on the average q=0 measurement to determine which
                voxels are CSF. This program does not treat CSF voxels any different
                to other voxels.
                flag: -csfthresh %G
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        fixedbvalue: (a list of from 3 to 3 items which are a float)
                As above, but specifies <M> <N> <b>. The resulting scheme is the
                same whether you specify b directly or indirectly using -fixedmodq.
                flag: -fixedbvalue %s
        fixedmodq: (a list of from 4 to 4 items which are a float)
                Specifies <M> <N> <Q> <tau> a spherical acquisition scheme with M
                measurements with q=0 and N measurements with |q|=Q and diffusion
                time tau. The N measurements with |q|=Q have unique directions. The
                program reads in the directions from the files in directory
                PointSets.
                flag: -fixedmod %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputdatatype: ('float' or 'char' or 'short' or 'int' or 'long' or
                 'double')
                Specifies the data type of the input file: "char", "short", "int",
                "long", "float" or "double". The input file must have BIG-ENDIAN
                ordering. By default, the input type is "float".
                flag: -inputdatatype %s
        noisemap: (an existing file name)
                Specifies the name of the file to contain the estimated noise
                variance on the diffusion-weighted signal, generated by a weighted
                tensor fit. The data type of this file is big-endian double.
                flag: -noisemap %s
        out_file: (a file name)
                flag: > %s, position: -1
        outlier: (an existing file name)
                Specifies the name of the file to contain the outlier map generated
                by the RESTORE algorithm.
                flag: -outliermap %s
        outputfile: (a file name)
                Filename of the output file.
                flag: -outputfile %s
        residualmap: (an existing file name)
                Specifies the name of the file to contain the weighted residual
                errors after computing a weighted linear tensor fit. One value is
                produced per measurement, in voxel order.The data type of this file
                is big-endian double. Images of the residuals for each measurement
                can be extracted with shredder.
                flag: -residualmap %s
        sigma: (a float)
                Specifies the standard deviation of the noise in the data. Required
                by the RESTORE algorithm.
                flag: -sigma %G
        tau: (a float)
                Sets the diffusion time separately. This overrides the diffusion
                time specified in a scheme file or by a scheme index for both the
                acquisition scheme and in the data synthesis.
                flag: -tau %G
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        fitted_data: (an existing file name)
                output file of 4D volume in voxel order

.. _nipype.interfaces.camino.dti.PicoPDFs:


.. index:: PicoPDFs

PicoPDFs
--------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L366>`__

Wraps command **picopdfs**

Constructs a spherical PDF in each voxel for probabilistic tractography.

Example
~~~~~~~

>>> import nipype.interfaces.camino as cmon
>>> pdf = cmon.PicoPDFs()
>>> pdf.inputs.inputmodel = 'dt'
>>> pdf.inputs.luts = ['lut_file']
>>> pdf.inputs.in_file = 'voxel-order_data.Bfloat'
>>> pdf.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                voxel-order data filename
                flag: < %s, position: 1
        luts: (a list of items which are an existing file name)
                Files containing the lookup tables.For tensor data, one lut must be
                specified for each type of inversion used in the image (one-tensor,
                two-tensor, three-tensor).For pds, the number of LUTs must match
                -numpds (it is acceptable to use the same LUT several times - see
                example, above).These LUTs may be generated with dtlutgen.
                flag: -luts %s

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        directmap: (a boolean)
                Only applicable when using pds as the inputmodel. Use direct mapping
                between the eigenvalues and the distribution parameters instead of
                the log of the eigenvalues.
                flag: -directmap
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputmodel: ('dt' or 'multitensor' or 'pds', nipype default value:
                 dt)
                input model type
                flag: -inputmodel %s, position: 2
        maxcomponents: (an integer (int or long))
                The maximum number of tensor components in a voxel (default 2) for
                multitensor data.Currently, only the default is supported, but
                future releases may allow the input of three-tensor data using this
                option.
                flag: -maxcomponents %d
        numpds: (an integer (int or long))
                The maximum number of PDs in a voxel (default 3) for PD data.This
                option determines the size of the input and output voxels.This means
                that the data file may be large enough to accomodate three or more
                PDs,but does not mean that any of the voxels are classified as
                containing three or more PDs.
                flag: -numpds %d
        out_file: (a file name)
                flag: > %s, position: -1
        pdf: ('bingham' or 'watson' or 'acg', nipype default value: bingham)
                 Specifies the PDF to use. There are three choices:watson - The
                Watson distribution. This distribution is rotationally
                symmetric.bingham - The Bingham distributionn, which allows
                elliptical probability density contours.acg - The Angular Central
                Gaussian distribution, which also allows elliptical probability
                density contours
                flag: -pdf %s, position: 4
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        pdfs: (an existing file name)
                path/name of 4D volume in voxel order

.. _nipype.interfaces.camino.dti.Track:


.. index:: Track

Track
-----

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L527>`__

Wraps command **track**

Performs tractography using one of the following models:
dt', 'multitensor', 'pds', 'pico', 'bootstrap', 'ballstick', 'bayesdirac'

Example
~~~~~~~

>>> import nipype.interfaces.camino as cmon
>>> track = cmon.Track()
>>> track.inputs.inputmodel = 'dt'
>>> track.inputs.in_file = 'data.Bfloat'
>>> track.inputs.seed_file = 'seed_mask.nii'
>>> track.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]

        [Optional]
        anisfile: (an existing file name)
                File containing the anisotropy map. This is required to apply an
                anisotropy threshold with non tensor data. If the map issupplied it
                is always used, even in tensor data.
                flag: -anisfile %s
        anisthresh: (a float)
                Terminate fibres that enter a voxel with lower anisotropy than the
                threshold.
                flag: -anisthresh %f
        args: (a string)
                Additional parameters to the command
                flag: %s
        curveinterval: (a float)
                Interval over which the curvature threshold should be evaluated, in
                mm. The default is 5mm. When using the default curvature threshold
                of 90 degrees, this means that streamlines will terminate if they
                curve by more than 90 degrees over a path length of 5mm.
                flag: -curveinterval %f
                requires: curvethresh
        curvethresh: (a float)
                Curvature threshold for tracking, expressed as the maximum angle (in
                degrees) between between two streamline orientations calculated over
                the length of a voxel. If the angle is greater than this, then the
                streamline terminates.
                flag: -curvethresh %f
        data_dims: (a list of from 3 to 3 items which are an integer (int or
                 long))
                data dimensions in voxels
                flag: -datadims %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        gzip: (a boolean)
                save the output image in gzip format
                flag: -gzip
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        in_file: (an existing file name)
                input data file
                flag: -inputfile %s, position: 1
        inputdatatype: ('float' or 'double')
                input file type
                flag: -inputdatatype %s
        inputmodel: ('dt' or 'multitensor' or 'sfpeak' or 'pico' or
                 'repbs_dt' or 'repbs_multitensor' or 'ballstick' or 'wildbs_dt' or
                 'bayesdirac' or 'bayesdirac_dt' or 'bedpostx_dyad' or 'bedpostx',
                 nipype default value: dt)
                input model type
                flag: -inputmodel %s
        interpolator: ('nn' or 'prob_nn' or 'linear')
                The interpolation algorithm determines how the fiber orientation(s)
                are defined at a given continuous point within the input image.
                Interpolators are only used when the tracking algorithm is not FACT.
                The choices are: - NN: Nearest-neighbour interpolation, just uses
                the local voxel data directly.- PROB_NN: Probabilistic nearest-
                neighbor interpolation, similar to the method pro- posed by Behrens
                et al [Magnetic Resonance in Medicine, 50:1077-1088, 2003]. The data
                is not interpolated, but at each point we randomly choose one of the
                8 voxels sur- rounding a point. The probability of choosing a
                particular voxel is based on how close the point is to the centre of
                that voxel.- LINEAR: Linear interpolation of the vector field
                containing the principal directions at each point.
                flag: -interpolator %s
        ipthresh: (a float)
                Curvature threshold for tracking, expressed as the minimum dot
                product between two streamline orientations calculated over the
                length of a voxel. If the dot product between the previous and
                current directions is less than this threshold, then the streamline
                terminates. The default setting will terminate fibres that curve by
                more than 80 degrees. Set this to -1.0 to disable curvature checking
                completely.
                flag: -ipthresh %f
        maxcomponents: (an integer (int or long))
                The maximum number of tensor components in a voxel. This determines
                the size of the input file and does not say anything about the voxel
                classification. The default is 2 if the input model is multitensor
                and 1 if the input model is dt.
                flag: -maxcomponents %d
        numpds: (an integer (int or long))
                The maximum number of PDs in a voxel for input models sfpeak and
                pico. The default is 3 for input model sfpeak and 1 for input model
                pico. This option determines the size of the voxels in the input
                file and does not affect tracking. For tensor data, use the
                -maxcomponents option.
                flag: -numpds %d
        out_file: (a file name)
                output data file
                flag: -outputfile %s, position: -1
        output_root: (a file name)
                root directory for output
                flag: -outputroot %s, position: -1
        outputtracts: ('float' or 'double' or 'oogl')
                output tract file type
                flag: -outputtracts %s
        seed_file: (an existing file name)
                seed file
                flag: -seedfile %s, position: 2
        stepsize: (a float)
                Step size for EULER and RK4 tracking. The default is 1mm.
                flag: -stepsize %f
                requires: tracker
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        tracker: ('fact' or 'euler' or 'rk4', nipype default value: fact)
                The tracking algorithm controls streamlines are generated from the
                data. The choices are: - FACT, which follows the local fibre
                orientation in each voxel. No interpolation is used.- EULER, which
                uses a fixed step size along the local fibre orientation. With
                nearest-neighbour interpolation, this method may be very similar to
                FACT, except that the step size is fixed, whereas FACT steps extend
                to the boundary of the next voxel (distance variable depending on
                the entry and exit points to the voxel).- RK4: Fourth-order Runge-
                Kutta method. The step size is fixed, however the eventual direction
                of the step is determined by taking and averaging a series of
                partial steps.
                flag: -tracker %s
        voxel_dims: (a list of from 3 to 3 items which are a float)
                voxel dimensions in mm
                flag: -voxeldims %s

Outputs::

        tracked: (an existing file name)
                output file containing reconstructed tracts

.. _nipype.interfaces.camino.dti.TrackBallStick:


.. index:: TrackBallStick

TrackBallStick
--------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L745>`__

Wraps command **track**

Performs streamline tractography using ball-stick fitted data

Example
~~~~~~~

>>> import nipype.interfaces.camino as cmon
>>> track = cmon.TrackBallStick()
>>> track.inputs.in_file = 'ballstickfit_data.Bfloat'
>>> track.inputs.seed_file = 'seed_mask.nii'
>>> track.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]

        [Optional]
        anisfile: (an existing file name)
                File containing the anisotropy map. This is required to apply an
                anisotropy threshold with non tensor data. If the map issupplied it
                is always used, even in tensor data.
                flag: -anisfile %s
        anisthresh: (a float)
                Terminate fibres that enter a voxel with lower anisotropy than the
                threshold.
                flag: -anisthresh %f
        args: (a string)
                Additional parameters to the command
                flag: %s
        curveinterval: (a float)
                Interval over which the curvature threshold should be evaluated, in
                mm. The default is 5mm. When using the default curvature threshold
                of 90 degrees, this means that streamlines will terminate if they
                curve by more than 90 degrees over a path length of 5mm.
                flag: -curveinterval %f
                requires: curvethresh
        curvethresh: (a float)
                Curvature threshold for tracking, expressed as the maximum angle (in
                degrees) between between two streamline orientations calculated over
                the length of a voxel. If the angle is greater than this, then the
                streamline terminates.
                flag: -curvethresh %f
        data_dims: (a list of from 3 to 3 items which are an integer (int or
                 long))
                data dimensions in voxels
                flag: -datadims %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        gzip: (a boolean)
                save the output image in gzip format
                flag: -gzip
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        in_file: (an existing file name)
                input data file
                flag: -inputfile %s, position: 1
        inputdatatype: ('float' or 'double')
                input file type
                flag: -inputdatatype %s
        inputmodel: ('dt' or 'multitensor' or 'sfpeak' or 'pico' or
                 'repbs_dt' or 'repbs_multitensor' or 'ballstick' or 'wildbs_dt' or
                 'bayesdirac' or 'bayesdirac_dt' or 'bedpostx_dyad' or 'bedpostx',
                 nipype default value: dt)
                input model type
                flag: -inputmodel %s
        interpolator: ('nn' or 'prob_nn' or 'linear')
                The interpolation algorithm determines how the fiber orientation(s)
                are defined at a given continuous point within the input image.
                Interpolators are only used when the tracking algorithm is not FACT.
                The choices are: - NN: Nearest-neighbour interpolation, just uses
                the local voxel data directly.- PROB_NN: Probabilistic nearest-
                neighbor interpolation, similar to the method pro- posed by Behrens
                et al [Magnetic Resonance in Medicine, 50:1077-1088, 2003]. The data
                is not interpolated, but at each point we randomly choose one of the
                8 voxels sur- rounding a point. The probability of choosing a
                particular voxel is based on how close the point is to the centre of
                that voxel.- LINEAR: Linear interpolation of the vector field
                containing the principal directions at each point.
                flag: -interpolator %s
        ipthresh: (a float)
                Curvature threshold for tracking, expressed as the minimum dot
                product between two streamline orientations calculated over the
                length of a voxel. If the dot product between the previous and
                current directions is less than this threshold, then the streamline
                terminates. The default setting will terminate fibres that curve by
                more than 80 degrees. Set this to -1.0 to disable curvature checking
                completely.
                flag: -ipthresh %f
        maxcomponents: (an integer (int or long))
                The maximum number of tensor components in a voxel. This determines
                the size of the input file and does not say anything about the voxel
                classification. The default is 2 if the input model is multitensor
                and 1 if the input model is dt.
                flag: -maxcomponents %d
        numpds: (an integer (int or long))
                The maximum number of PDs in a voxel for input models sfpeak and
                pico. The default is 3 for input model sfpeak and 1 for input model
                pico. This option determines the size of the voxels in the input
                file and does not affect tracking. For tensor data, use the
                -maxcomponents option.
                flag: -numpds %d
        out_file: (a file name)
                output data file
                flag: -outputfile %s, position: -1
        output_root: (a file name)
                root directory for output
                flag: -outputroot %s, position: -1
        outputtracts: ('float' or 'double' or 'oogl')
                output tract file type
                flag: -outputtracts %s
        seed_file: (an existing file name)
                seed file
                flag: -seedfile %s, position: 2
        stepsize: (a float)
                Step size for EULER and RK4 tracking. The default is 1mm.
                flag: -stepsize %f
                requires: tracker
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        tracker: ('fact' or 'euler' or 'rk4', nipype default value: fact)
                The tracking algorithm controls streamlines are generated from the
                data. The choices are: - FACT, which follows the local fibre
                orientation in each voxel. No interpolation is used.- EULER, which
                uses a fixed step size along the local fibre orientation. With
                nearest-neighbour interpolation, this method may be very similar to
                FACT, except that the step size is fixed, whereas FACT steps extend
                to the boundary of the next voxel (distance variable depending on
                the entry and exit points to the voxel).- RK4: Fourth-order Runge-
                Kutta method. The step size is fixed, however the eventual direction
                of the step is determined by taking and averaging a series of
                partial steps.
                flag: -tracker %s
        voxel_dims: (a list of from 3 to 3 items which are a float)
                voxel dimensions in mm
                flag: -voxeldims %s

Outputs::

        tracked: (an existing file name)
                output file containing reconstructed tracts

.. _nipype.interfaces.camino.dti.TrackBayesDirac:


.. index:: TrackBayesDirac

TrackBayesDirac
---------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L724>`__

Wraps command **track**

Performs streamline tractography using a Bayesian tracking with Dirac priors

Example
~~~~~~~

>>> import nipype.interfaces.camino as cmon
>>> track = cmon.TrackBayesDirac()
>>> track.inputs.in_file = 'tensor_fitted_data.Bdouble'
>>> track.inputs.seed_file = 'seed_mask.nii'
>>> track.inputs.scheme_file = 'bvecs.scheme'
>>> track.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]
        scheme_file: (an existing file name)
                The scheme file corresponding to the data being processed.
                flag: -schemefile %s

        [Optional]
        anisfile: (an existing file name)
                File containing the anisotropy map. This is required to apply an
                anisotropy threshold with non tensor data. If the map issupplied it
                is always used, even in tensor data.
                flag: -anisfile %s
        anisthresh: (a float)
                Terminate fibres that enter a voxel with lower anisotropy than the
                threshold.
                flag: -anisthresh %f
        args: (a string)
                Additional parameters to the command
                flag: %s
        curveinterval: (a float)
                Interval over which the curvature threshold should be evaluated, in
                mm. The default is 5mm. When using the default curvature threshold
                of 90 degrees, this means that streamlines will terminate if they
                curve by more than 90 degrees over a path length of 5mm.
                flag: -curveinterval %f
                requires: curvethresh
        curvepriorg: (a float)
                Concentration parameter for the prior distribution on fibre
                orientations given the fibre orientation at the previous step.
                Larger values of g make curvature less likely.
                flag: -curvepriorg %G
        curvepriork: (a float)
                Concentration parameter for the prior distribution on fibre
                orientations given the fibre orientation at the previous step.
                Larger values of k make curvature less likely.
                flag: -curvepriork %G
        curvethresh: (a float)
                Curvature threshold for tracking, expressed as the maximum angle (in
                degrees) between between two streamline orientations calculated over
                the length of a voxel. If the angle is greater than this, then the
                streamline terminates.
                flag: -curvethresh %f
        data_dims: (a list of from 3 to 3 items which are an integer (int or
                 long))
                data dimensions in voxels
                flag: -datadims %s
        datamodel: ('cylsymmdt' or 'ballstick')
                Model of the data for Bayesian tracking. The default model is
                "cylsymmdt", a diffusion tensor with cylindrical symmetry about e_1,
                ie L1 >= L_2 = L_3. The other model is "ballstick", the partial
                volume model (see ballstickfit).
                flag: -datamodel %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        extpriordatatype: ('float' or 'double')
                Datatype of the prior image. The default is "double".
                flag: -extpriordatatype %s
        extpriorfile: (an existing file name)
                Path to a PICo image produced by picopdfs. The PDF in each voxel is
                used as a prior for the fibre orientation in Bayesian tracking. The
                prior image must be in the same space as the diffusion data.
                flag: -extpriorfile %s
        gzip: (a boolean)
                save the output image in gzip format
                flag: -gzip
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        in_file: (an existing file name)
                input data file
                flag: -inputfile %s, position: 1
        inputdatatype: ('float' or 'double')
                input file type
                flag: -inputdatatype %s
        inputmodel: ('dt' or 'multitensor' or 'sfpeak' or 'pico' or
                 'repbs_dt' or 'repbs_multitensor' or 'ballstick' or 'wildbs_dt' or
                 'bayesdirac' or 'bayesdirac_dt' or 'bedpostx_dyad' or 'bedpostx',
                 nipype default value: dt)
                input model type
                flag: -inputmodel %s
        interpolator: ('nn' or 'prob_nn' or 'linear')
                The interpolation algorithm determines how the fiber orientation(s)
                are defined at a given continuous point within the input image.
                Interpolators are only used when the tracking algorithm is not FACT.
                The choices are: - NN: Nearest-neighbour interpolation, just uses
                the local voxel data directly.- PROB_NN: Probabilistic nearest-
                neighbor interpolation, similar to the method pro- posed by Behrens
                et al [Magnetic Resonance in Medicine, 50:1077-1088, 2003]. The data
                is not interpolated, but at each point we randomly choose one of the
                8 voxels sur- rounding a point. The probability of choosing a
                particular voxel is based on how close the point is to the centre of
                that voxel.- LINEAR: Linear interpolation of the vector field
                containing the principal directions at each point.
                flag: -interpolator %s
        ipthresh: (a float)
                Curvature threshold for tracking, expressed as the minimum dot
                product between two streamline orientations calculated over the
                length of a voxel. If the dot product between the previous and
                current directions is less than this threshold, then the streamline
                terminates. The default setting will terminate fibres that curve by
                more than 80 degrees. Set this to -1.0 to disable curvature checking
                completely.
                flag: -ipthresh %f
        iterations: (an integer (int or long))
                Number of streamlines to generate at each seed point. The default is
                5000.
                flag: -iterations %d
        maxcomponents: (an integer (int or long))
                The maximum number of tensor components in a voxel. This determines
                the size of the input file and does not say anything about the voxel
                classification. The default is 2 if the input model is multitensor
                and 1 if the input model is dt.
                flag: -maxcomponents %d
        numpds: (an integer (int or long))
                The maximum number of PDs in a voxel for input models sfpeak and
                pico. The default is 3 for input model sfpeak and 1 for input model
                pico. This option determines the size of the voxels in the input
                file and does not affect tracking. For tensor data, use the
                -maxcomponents option.
                flag: -numpds %d
        out_file: (a file name)
                output data file
                flag: -outputfile %s, position: -1
        output_root: (a file name)
                root directory for output
                flag: -outputroot %s, position: -1
        outputtracts: ('float' or 'double' or 'oogl')
                output tract file type
                flag: -outputtracts %s
        pdf: ('bingham' or 'watson' or 'acg')
                Specifies the model for PICo priors (not the curvature priors). The
                default is "bingham".
                flag: -pdf %s
        pointset: (an integer (int or long))
                Index to the point set to use for Bayesian likelihood calculation.
                The index specifies a set of evenly distributed points on the unit
                sphere, where each point x defines two possible step directions (x
                or -x) for the streamline path. A larger number indexes a larger
                point set, which gives higher angular resolution at the expense of
                computation time. The default is index 1, which gives 1922 points,
                index 0 gives 1082 points, index 2 gives 3002 points.
                flag: -pointset %s
        seed_file: (an existing file name)
                seed file
                flag: -seedfile %s, position: 2
        stepsize: (a float)
                Step size for EULER and RK4 tracking. The default is 1mm.
                flag: -stepsize %f
                requires: tracker
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        tracker: ('fact' or 'euler' or 'rk4', nipype default value: fact)
                The tracking algorithm controls streamlines are generated from the
                data. The choices are: - FACT, which follows the local fibre
                orientation in each voxel. No interpolation is used.- EULER, which
                uses a fixed step size along the local fibre orientation. With
                nearest-neighbour interpolation, this method may be very similar to
                FACT, except that the step size is fixed, whereas FACT steps extend
                to the boundary of the next voxel (distance variable depending on
                the entry and exit points to the voxel).- RK4: Fourth-order Runge-
                Kutta method. The step size is fixed, however the eventual direction
                of the step is determined by taking and averaging a series of
                partial steps.
                flag: -tracker %s
        voxel_dims: (a list of from 3 to 3 items which are a float)
                voxel dimensions in mm
                flag: -voxeldims %s

Outputs::

        tracked: (an existing file name)
                output file containing reconstructed tracts

.. _nipype.interfaces.camino.dti.TrackBedpostxDeter:


.. index:: TrackBedpostxDeter

TrackBedpostxDeter
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L623>`__

Wraps command **track**

Data from FSL's bedpostx can be imported into Camino for deterministic tracking.
(Use TrackBedpostxProba for bedpostx probabilistic tractography.)

The tracking is based on the vector images dyads1.nii.gz, ... , dyadsN.nii.gz,
where there are a maximum of N compartments (corresponding to each fiber
population) in each voxel.

It also uses the N images mean_f1samples.nii.gz, ..., mean_fNsamples.nii.gz,
normalized such that the sum of all compartments is 1. Compartments where the
mean_f is less than a threshold are discarded and not used for tracking.
The default value is 0.01. This can be changed with the min_vol_frac option.

Example
~~~~~~~

>>> import nipype.interfaces.camino as cam
>>> track = cam.TrackBedpostxDeter()
>>> track.inputs.bedpostxdir = 'bedpostxout'
>>> track.inputs.seed_file = 'seed_mask.nii'
>>> track.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]
        bedpostxdir: (an existing directory name)
                Directory containing bedpostx output
                flag: -bedpostxdir %s

        [Optional]
        anisfile: (an existing file name)
                File containing the anisotropy map. This is required to apply an
                anisotropy threshold with non tensor data. If the map issupplied it
                is always used, even in tensor data.
                flag: -anisfile %s
        anisthresh: (a float)
                Terminate fibres that enter a voxel with lower anisotropy than the
                threshold.
                flag: -anisthresh %f
        args: (a string)
                Additional parameters to the command
                flag: %s
        curveinterval: (a float)
                Interval over which the curvature threshold should be evaluated, in
                mm. The default is 5mm. When using the default curvature threshold
                of 90 degrees, this means that streamlines will terminate if they
                curve by more than 90 degrees over a path length of 5mm.
                flag: -curveinterval %f
                requires: curvethresh
        curvethresh: (a float)
                Curvature threshold for tracking, expressed as the maximum angle (in
                degrees) between between two streamline orientations calculated over
                the length of a voxel. If the angle is greater than this, then the
                streamline terminates.
                flag: -curvethresh %f
        data_dims: (a list of from 3 to 3 items which are an integer (int or
                 long))
                data dimensions in voxels
                flag: -datadims %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        gzip: (a boolean)
                save the output image in gzip format
                flag: -gzip
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        in_file: (an existing file name)
                input data file
                flag: -inputfile %s, position: 1
        inputdatatype: ('float' or 'double')
                input file type
                flag: -inputdatatype %s
        inputmodel: ('dt' or 'multitensor' or 'sfpeak' or 'pico' or
                 'repbs_dt' or 'repbs_multitensor' or 'ballstick' or 'wildbs_dt' or
                 'bayesdirac' or 'bayesdirac_dt' or 'bedpostx_dyad' or 'bedpostx',
                 nipype default value: dt)
                input model type
                flag: -inputmodel %s
        interpolator: ('nn' or 'prob_nn' or 'linear')
                The interpolation algorithm determines how the fiber orientation(s)
                are defined at a given continuous point within the input image.
                Interpolators are only used when the tracking algorithm is not FACT.
                The choices are: - NN: Nearest-neighbour interpolation, just uses
                the local voxel data directly.- PROB_NN: Probabilistic nearest-
                neighbor interpolation, similar to the method pro- posed by Behrens
                et al [Magnetic Resonance in Medicine, 50:1077-1088, 2003]. The data
                is not interpolated, but at each point we randomly choose one of the
                8 voxels sur- rounding a point. The probability of choosing a
                particular voxel is based on how close the point is to the centre of
                that voxel.- LINEAR: Linear interpolation of the vector field
                containing the principal directions at each point.
                flag: -interpolator %s
        ipthresh: (a float)
                Curvature threshold for tracking, expressed as the minimum dot
                product between two streamline orientations calculated over the
                length of a voxel. If the dot product between the previous and
                current directions is less than this threshold, then the streamline
                terminates. The default setting will terminate fibres that curve by
                more than 80 degrees. Set this to -1.0 to disable curvature checking
                completely.
                flag: -ipthresh %f
        maxcomponents: (an integer (int or long))
                The maximum number of tensor components in a voxel. This determines
                the size of the input file and does not say anything about the voxel
                classification. The default is 2 if the input model is multitensor
                and 1 if the input model is dt.
                flag: -maxcomponents %d
        min_vol_frac: (a float)
                Zeros out compartments in bedpostx data with a mean volume fraction
                f of less than min_vol_frac. The default is 0.01.
                flag: -bedpostxminf %d
        numpds: (an integer (int or long))
                The maximum number of PDs in a voxel for input models sfpeak and
                pico. The default is 3 for input model sfpeak and 1 for input model
                pico. This option determines the size of the voxels in the input
                file and does not affect tracking. For tensor data, use the
                -maxcomponents option.
                flag: -numpds %d
        out_file: (a file name)
                output data file
                flag: -outputfile %s, position: -1
        output_root: (a file name)
                root directory for output
                flag: -outputroot %s, position: -1
        outputtracts: ('float' or 'double' or 'oogl')
                output tract file type
                flag: -outputtracts %s
        seed_file: (an existing file name)
                seed file
                flag: -seedfile %s, position: 2
        stepsize: (a float)
                Step size for EULER and RK4 tracking. The default is 1mm.
                flag: -stepsize %f
                requires: tracker
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        tracker: ('fact' or 'euler' or 'rk4', nipype default value: fact)
                The tracking algorithm controls streamlines are generated from the
                data. The choices are: - FACT, which follows the local fibre
                orientation in each voxel. No interpolation is used.- EULER, which
                uses a fixed step size along the local fibre orientation. With
                nearest-neighbour interpolation, this method may be very similar to
                FACT, except that the step size is fixed, whereas FACT steps extend
                to the boundary of the next voxel (distance variable depending on
                the entry and exit points to the voxel).- RK4: Fourth-order Runge-
                Kutta method. The step size is fixed, however the eventual direction
                of the step is determined by taking and averaging a series of
                partial steps.
                flag: -tracker %s
        voxel_dims: (a list of from 3 to 3 items which are a float)
                voxel dimensions in mm
                flag: -voxeldims %s

Outputs::

        tracked: (an existing file name)
                output file containing reconstructed tracts

.. _nipype.interfaces.camino.dti.TrackBedpostxProba:


.. index:: TrackBedpostxProba

TrackBedpostxProba
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L666>`__

Wraps command **track**

Data from FSL's bedpostx can be imported into Camino for probabilistic tracking.
(Use TrackBedpostxDeter for bedpostx deterministic tractography.)

The tracking uses the files merged_th1samples.nii.gz, merged_ph1samples.nii.gz,
... , merged_thNsamples.nii.gz, merged_phNsamples.nii.gz where there are a
maximum of N compartments (corresponding to each fiber population) in each
voxel. These images contain M samples of theta and phi, the polar coordinates
describing the "stick" for each compartment. At each iteration, a random number
X between 1 and M is drawn and the Xth samples of theta and phi become the
principal directions in the voxel.

It also uses the N images mean_f1samples.nii.gz, ..., mean_fNsamples.nii.gz,
normalized such that the sum of all compartments is 1. Compartments where the
mean_f is less than a threshold are discarded and not used for tracking.
The default value is 0.01. This can be changed with the min_vol_frac option.

Example
~~~~~~~

>>> import nipype.interfaces.camino as cam
>>> track = cam.TrackBedpostxProba()
>>> track.inputs.bedpostxdir = 'bedpostxout'
>>> track.inputs.seed_file = 'seed_mask.nii'
>>> track.inputs.iterations = 100
>>> track.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]
        bedpostxdir: (an existing directory name)
                Directory containing bedpostx output
                flag: -bedpostxdir %s

        [Optional]
        anisfile: (an existing file name)
                File containing the anisotropy map. This is required to apply an
                anisotropy threshold with non tensor data. If the map issupplied it
                is always used, even in tensor data.
                flag: -anisfile %s
        anisthresh: (a float)
                Terminate fibres that enter a voxel with lower anisotropy than the
                threshold.
                flag: -anisthresh %f
        args: (a string)
                Additional parameters to the command
                flag: %s
        curveinterval: (a float)
                Interval over which the curvature threshold should be evaluated, in
                mm. The default is 5mm. When using the default curvature threshold
                of 90 degrees, this means that streamlines will terminate if they
                curve by more than 90 degrees over a path length of 5mm.
                flag: -curveinterval %f
                requires: curvethresh
        curvethresh: (a float)
                Curvature threshold for tracking, expressed as the maximum angle (in
                degrees) between between two streamline orientations calculated over
                the length of a voxel. If the angle is greater than this, then the
                streamline terminates.
                flag: -curvethresh %f
        data_dims: (a list of from 3 to 3 items which are an integer (int or
                 long))
                data dimensions in voxels
                flag: -datadims %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        gzip: (a boolean)
                save the output image in gzip format
                flag: -gzip
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        in_file: (an existing file name)
                input data file
                flag: -inputfile %s, position: 1
        inputdatatype: ('float' or 'double')
                input file type
                flag: -inputdatatype %s
        inputmodel: ('dt' or 'multitensor' or 'sfpeak' or 'pico' or
                 'repbs_dt' or 'repbs_multitensor' or 'ballstick' or 'wildbs_dt' or
                 'bayesdirac' or 'bayesdirac_dt' or 'bedpostx_dyad' or 'bedpostx',
                 nipype default value: dt)
                input model type
                flag: -inputmodel %s
        interpolator: ('nn' or 'prob_nn' or 'linear')
                The interpolation algorithm determines how the fiber orientation(s)
                are defined at a given continuous point within the input image.
                Interpolators are only used when the tracking algorithm is not FACT.
                The choices are: - NN: Nearest-neighbour interpolation, just uses
                the local voxel data directly.- PROB_NN: Probabilistic nearest-
                neighbor interpolation, similar to the method pro- posed by Behrens
                et al [Magnetic Resonance in Medicine, 50:1077-1088, 2003]. The data
                is not interpolated, but at each point we randomly choose one of the
                8 voxels sur- rounding a point. The probability of choosing a
                particular voxel is based on how close the point is to the centre of
                that voxel.- LINEAR: Linear interpolation of the vector field
                containing the principal directions at each point.
                flag: -interpolator %s
        ipthresh: (a float)
                Curvature threshold for tracking, expressed as the minimum dot
                product between two streamline orientations calculated over the
                length of a voxel. If the dot product between the previous and
                current directions is less than this threshold, then the streamline
                terminates. The default setting will terminate fibres that curve by
                more than 80 degrees. Set this to -1.0 to disable curvature checking
                completely.
                flag: -ipthresh %f
        iterations: (an integer (int or long))
                Number of streamlines to generate at each seed point. The default is
                1.
                flag: -iterations %d
        maxcomponents: (an integer (int or long))
                The maximum number of tensor components in a voxel. This determines
                the size of the input file and does not say anything about the voxel
                classification. The default is 2 if the input model is multitensor
                and 1 if the input model is dt.
                flag: -maxcomponents %d
        min_vol_frac: (a float)
                Zeros out compartments in bedpostx data with a mean volume fraction
                f of less than min_vol_frac. The default is 0.01.
                flag: -bedpostxminf %d
        numpds: (an integer (int or long))
                The maximum number of PDs in a voxel for input models sfpeak and
                pico. The default is 3 for input model sfpeak and 1 for input model
                pico. This option determines the size of the voxels in the input
                file and does not affect tracking. For tensor data, use the
                -maxcomponents option.
                flag: -numpds %d
        out_file: (a file name)
                output data file
                flag: -outputfile %s, position: -1
        output_root: (a file name)
                root directory for output
                flag: -outputroot %s, position: -1
        outputtracts: ('float' or 'double' or 'oogl')
                output tract file type
                flag: -outputtracts %s
        seed_file: (an existing file name)
                seed file
                flag: -seedfile %s, position: 2
        stepsize: (a float)
                Step size for EULER and RK4 tracking. The default is 1mm.
                flag: -stepsize %f
                requires: tracker
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        tracker: ('fact' or 'euler' or 'rk4', nipype default value: fact)
                The tracking algorithm controls streamlines are generated from the
                data. The choices are: - FACT, which follows the local fibre
                orientation in each voxel. No interpolation is used.- EULER, which
                uses a fixed step size along the local fibre orientation. With
                nearest-neighbour interpolation, this method may be very similar to
                FACT, except that the step size is fixed, whereas FACT steps extend
                to the boundary of the next voxel (distance variable depending on
                the entry and exit points to the voxel).- RK4: Fourth-order Runge-
                Kutta method. The step size is fixed, however the eventual direction
                of the step is determined by taking and averaging a series of
                partial steps.
                flag: -tracker %s
        voxel_dims: (a list of from 3 to 3 items which are a float)
                voxel dimensions in mm
                flag: -voxeldims %s

Outputs::

        tracked: (an existing file name)
                output file containing reconstructed tracts

.. _nipype.interfaces.camino.dti.TrackBootstrap:


.. index:: TrackBootstrap

TrackBootstrap
--------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L774>`__

Wraps command **track**

Performs bootstrap streamline tractography using mulitple scans of the same subject

Example
~~~~~~~

>>> import nipype.interfaces.camino as cmon
>>> track = cmon.TrackBootstrap()
>>> track.inputs.inputmodel='repbs_dt'
>>> track.inputs.scheme_file = 'bvecs.scheme'
>>> track.inputs.bsdatafiles = ['fitted_data1.Bfloat', 'fitted_data2.Bfloat']
>>> track.inputs.seed_file = 'seed_mask.nii'
>>> track.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]
        bsdatafiles: (a list of items which are an existing file name)
                Specifies files containing raw data for repetition bootstrapping.
                Use -inputfile for wild bootstrap data.
                flag: -bsdatafile %s
        scheme_file: (an existing file name)
                The scheme file corresponding to the data being processed.
                flag: -schemefile %s

        [Optional]
        anisfile: (an existing file name)
                File containing the anisotropy map. This is required to apply an
                anisotropy threshold with non tensor data. If the map issupplied it
                is always used, even in tensor data.
                flag: -anisfile %s
        anisthresh: (a float)
                Terminate fibres that enter a voxel with lower anisotropy than the
                threshold.
                flag: -anisthresh %f
        args: (a string)
                Additional parameters to the command
                flag: %s
        bgmask: (an existing file name)
                Provides the name of a file containing a background mask computed
                using, for example, FSL's bet2 program. The mask file contains zero
                in background voxels and non-zero in foreground.
                flag: -bgmask %s
        curveinterval: (a float)
                Interval over which the curvature threshold should be evaluated, in
                mm. The default is 5mm. When using the default curvature threshold
                of 90 degrees, this means that streamlines will terminate if they
                curve by more than 90 degrees over a path length of 5mm.
                flag: -curveinterval %f
                requires: curvethresh
        curvethresh: (a float)
                Curvature threshold for tracking, expressed as the maximum angle (in
                degrees) between between two streamline orientations calculated over
                the length of a voxel. If the angle is greater than this, then the
                streamline terminates.
                flag: -curvethresh %f
        data_dims: (a list of from 3 to 3 items which are an integer (int or
                 long))
                data dimensions in voxels
                flag: -datadims %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        gzip: (a boolean)
                save the output image in gzip format
                flag: -gzip
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        in_file: (an existing file name)
                input data file
                flag: -inputfile %s, position: 1
        inputdatatype: ('float' or 'double')
                input file type
                flag: -inputdatatype %s
        inputmodel: ('dt' or 'multitensor' or 'sfpeak' or 'pico' or
                 'repbs_dt' or 'repbs_multitensor' or 'ballstick' or 'wildbs_dt' or
                 'bayesdirac' or 'bayesdirac_dt' or 'bedpostx_dyad' or 'bedpostx',
                 nipype default value: dt)
                input model type
                flag: -inputmodel %s
        interpolator: ('nn' or 'prob_nn' or 'linear')
                The interpolation algorithm determines how the fiber orientation(s)
                are defined at a given continuous point within the input image.
                Interpolators are only used when the tracking algorithm is not FACT.
                The choices are: - NN: Nearest-neighbour interpolation, just uses
                the local voxel data directly.- PROB_NN: Probabilistic nearest-
                neighbor interpolation, similar to the method pro- posed by Behrens
                et al [Magnetic Resonance in Medicine, 50:1077-1088, 2003]. The data
                is not interpolated, but at each point we randomly choose one of the
                8 voxels sur- rounding a point. The probability of choosing a
                particular voxel is based on how close the point is to the centre of
                that voxel.- LINEAR: Linear interpolation of the vector field
                containing the principal directions at each point.
                flag: -interpolator %s
        inversion: (an integer (int or long))
                Tensor reconstruction algorithm for repetition bootstrapping.
                Default is 1 (linear reconstruction, single tensor).
                flag: -inversion %s
        ipthresh: (a float)
                Curvature threshold for tracking, expressed as the minimum dot
                product between two streamline orientations calculated over the
                length of a voxel. If the dot product between the previous and
                current directions is less than this threshold, then the streamline
                terminates. The default setting will terminate fibres that curve by
                more than 80 degrees. Set this to -1.0 to disable curvature checking
                completely.
                flag: -ipthresh %f
        iterations: (an integer (int or long))
                Number of streamlines to generate at each seed point.
                flag: -iterations %d
        maxcomponents: (an integer (int or long))
                The maximum number of tensor components in a voxel. This determines
                the size of the input file and does not say anything about the voxel
                classification. The default is 2 if the input model is multitensor
                and 1 if the input model is dt.
                flag: -maxcomponents %d
        numpds: (an integer (int or long))
                The maximum number of PDs in a voxel for input models sfpeak and
                pico. The default is 3 for input model sfpeak and 1 for input model
                pico. This option determines the size of the voxels in the input
                file and does not affect tracking. For tensor data, use the
                -maxcomponents option.
                flag: -numpds %d
        out_file: (a file name)
                output data file
                flag: -outputfile %s, position: -1
        output_root: (a file name)
                root directory for output
                flag: -outputroot %s, position: -1
        outputtracts: ('float' or 'double' or 'oogl')
                output tract file type
                flag: -outputtracts %s
        seed_file: (an existing file name)
                seed file
                flag: -seedfile %s, position: 2
        stepsize: (a float)
                Step size for EULER and RK4 tracking. The default is 1mm.
                flag: -stepsize %f
                requires: tracker
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        tracker: ('fact' or 'euler' or 'rk4', nipype default value: fact)
                The tracking algorithm controls streamlines are generated from the
                data. The choices are: - FACT, which follows the local fibre
                orientation in each voxel. No interpolation is used.- EULER, which
                uses a fixed step size along the local fibre orientation. With
                nearest-neighbour interpolation, this method may be very similar to
                FACT, except that the step size is fixed, whereas FACT steps extend
                to the boundary of the next voxel (distance variable depending on
                the entry and exit points to the voxel).- RK4: Fourth-order Runge-
                Kutta method. The step size is fixed, however the eventual direction
                of the step is determined by taking and averaging a series of
                partial steps.
                flag: -tracker %s
        voxel_dims: (a list of from 3 to 3 items which are a float)
                voxel dimensions in mm
                flag: -voxeldims %s

Outputs::

        tracked: (an existing file name)
                output file containing reconstructed tracts

.. _nipype.interfaces.camino.dti.TrackDT:


.. index:: TrackDT

TrackDT
-------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L571>`__

Wraps command **track**

Performs streamline tractography using tensor data

Example
~~~~~~~

>>> import nipype.interfaces.camino as cmon
>>> track = cmon.TrackDT()
>>> track.inputs.in_file = 'tensor_fitted_data.Bdouble'
>>> track.inputs.seed_file = 'seed_mask.nii'
>>> track.run()                 # doctest: +SKIP

Inputs::

        [Mandatory]

        [Optional]
        anisfile: (an existing file name)
                File containing the anisotropy map. This is required to apply an
                anisotropy threshold with non tensor data. If the map issupplied it
                is always used, even in tensor data.
                flag: -anisfile %s
        anisthresh: (a float)
                Terminate fibres that enter a voxel with lower anisotropy than the
                threshold.
                flag: -anisthresh %f
        args: (a string)
                Additional parameters to the command
                flag: %s
        curveinterval: (a float)
                Interval over which the curvature threshold should be evaluated, in
                mm. The default is 5mm. When using the default curvature threshold
                of 90 degrees, this means that streamlines will terminate if they
                curve by more than 90 degrees over a path length of 5mm.
                flag: -curveinterval %f
                requires: curvethresh
        curvethresh: (a float)
                Curvature threshold for tracking, expressed as the maximum angle (in
                degrees) between between two streamline orientations calculated over
                the length of a voxel. If the angle is greater than this, then the
                streamline terminates.
                flag: -curvethresh %f
        data_dims: (a list of from 3 to 3 items which are an integer (int or
                 long))
                data dimensions in voxels
                flag: -datadims %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        gzip: (a boolean)
                save the output image in gzip format
                flag: -gzip
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        in_file: (an existing file name)
                input data file
                flag: -inputfile %s, position: 1
        inputdatatype: ('float' or 'double')
                input file type
                flag: -inputdatatype %s
        inputmodel: ('dt' or 'multitensor' or 'sfpeak' or 'pico' or
                 'repbs_dt' or 'repbs_multitensor' or 'ballstick' or 'wildbs_dt' or
                 'bayesdirac' or 'bayesdirac_dt' or 'bedpostx_dyad' or 'bedpostx',
                 nipype default value: dt)
                input model type
                flag: -inputmodel %s
        interpolator: ('nn' or 'prob_nn' or 'linear')
                The interpolation algorithm determines how the fiber orientation(s)
                are defined at a given continuous point within the input image.
                Interpolators are only used when the tracking algorithm is not FACT.
                The choices are: - NN: Nearest-neighbour interpolation, just uses
                the local voxel data directly.- PROB_NN: Probabilistic nearest-
                neighbor interpolation, similar to the method pro- posed by Behrens
                et al [Magnetic Resonance in Medicine, 50:1077-1088, 2003]. The data
                is not interpolated, but at each point we randomly choose one of the
                8 voxels sur- rounding a point. The probability of choosing a
                particular voxel is based on how close the point is to the centre of
                that voxel.- LINEAR: Linear interpolation of the vector field
                containing the principal directions at each point.
                flag: -interpolator %s
        ipthresh: (a float)
                Curvature threshold for tracking, expressed as the minimum dot
                product between two streamline orientations calculated over the
                length of a voxel. If the dot product between the previous and
                current directions is less than this threshold, then the streamline
                terminates. The default setting will terminate fibres that curve by
                more than 80 degrees. Set this to -1.0 to disable curvature checking
                completely.
                flag: -ipthresh %f
        maxcomponents: (an integer (int or long))
                The maximum number of tensor components in a voxel. This determines
                the size of the input file and does not say anything about the voxel
                classification. The default is 2 if the input model is multitensor
                and 1 if the input model is dt.
                flag: -maxcomponents %d
        numpds: (an integer (int or long))
                The maximum number of PDs in a voxel for input models sfpeak and
                pico. The default is 3 for input model sfpeak and 1 for input model
                pico. This option determines the size of the voxels in the input
                file and does not affect tracking. For tensor data, use the
                -maxcomponents option.
                flag: -numpds %d
        out_file: (a file name)
                output data file
                flag: -outputfile %s, position: -1
        output_root: (a file name)
                root directory for output
                flag: -outputroot %s, position: -1
        outputtracts: ('float' or 'double' or 'oogl')
                output tract file type
                flag: -outputtracts %s
        seed_file: (an existing file name)
                seed file
                flag: -seedfile %s, position: 2
        stepsize: (a float)
                Step size for EULER and RK4 tracking. The default is 1mm.
                flag: -stepsize %f
                requires: tracker
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        tracker: ('fact' or 'euler' or 'rk4', nipype default value: fact)
                The tracking algorithm controls streamlines are generated from the
                data. The choices are: - FACT, which follows the local fibre
                orientation in each voxel. No interpolation is used.- EULER, which
                uses a fixed step size along the local fibre orientation. With
                nearest-neighbour interpolation, this method may be very similar to
                FACT, except that the step size is fixed, whereas FACT steps extend
                to the boundary of the next voxel (distance variable depending on
                the entry and exit points to the voxel).- RK4: Fourth-order Runge-
                Kutta method. The step size is fixed, however the eventual direction
                of the step is determined by taking and averaging a series of
                partial steps.
                flag: -tracker %s
        voxel_dims: (a list of from 3 to 3 items which are a float)
                voxel dimensions in mm
                flag: -voxeldims %s

Outputs::

        tracked: (an existing file name)
                output file containing reconstructed tracts

.. _nipype.interfaces.camino.dti.TrackPICo:


.. index:: TrackPICo

TrackPICo
---------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/camino/dti.py#L594>`__

Wraps command **track**

Performs streamline tractography using the Probabilistic Index of Connectivity (PICo) algorithm

Example
~~~~~~~

>>> import nipype.interfaces.camino as cmon
>>> track = cmon.TrackPICo()
>>> track.inputs.in_file = 'pdfs.Bfloat'
>>> track.inputs.seed_file = 'seed_mask.nii'
>>> track.run()                  # doctest: +SKIP

Inputs::

        [Mandatory]

        [Optional]
        anisfile: (an existing file name)
                File containing the anisotropy map. This is required to apply an
                anisotropy threshold with non tensor data. If the map issupplied it
                is always used, even in tensor data.
                flag: -anisfile %s
        anisthresh: (a float)
                Terminate fibres that enter a voxel with lower anisotropy than the
                threshold.
                flag: -anisthresh %f
        args: (a string)
                Additional parameters to the command
                flag: %s
        curveinterval: (a float)
                Interval over which the curvature threshold should be evaluated, in
                mm. The default is 5mm. When using the default curvature threshold
                of 90 degrees, this means that streamlines will terminate if they
                curve by more than 90 degrees over a path length of 5mm.
                flag: -curveinterval %f
                requires: curvethresh
        curvethresh: (a float)
                Curvature threshold for tracking, expressed as the maximum angle (in
                degrees) between between two streamline orientations calculated over
                the length of a voxel. If the angle is greater than this, then the
                streamline terminates.
                flag: -curvethresh %f
        data_dims: (a list of from 3 to 3 items which are an integer (int or
                 long))
                data dimensions in voxels
                flag: -datadims %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        gzip: (a boolean)
                save the output image in gzip format
                flag: -gzip
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        in_file: (an existing file name)
                input data file
                flag: -inputfile %s, position: 1
        inputdatatype: ('float' or 'double')
                input file type
                flag: -inputdatatype %s
        inputmodel: ('dt' or 'multitensor' or 'sfpeak' or 'pico' or
                 'repbs_dt' or 'repbs_multitensor' or 'ballstick' or 'wildbs_dt' or
                 'bayesdirac' or 'bayesdirac_dt' or 'bedpostx_dyad' or 'bedpostx',
                 nipype default value: dt)
                input model type
                flag: -inputmodel %s
        interpolator: ('nn' or 'prob_nn' or 'linear')
                The interpolation algorithm determines how the fiber orientation(s)
                are defined at a given continuous point within the input image.
                Interpolators are only used when the tracking algorithm is not FACT.
                The choices are: - NN: Nearest-neighbour interpolation, just uses
                the local voxel data directly.- PROB_NN: Probabilistic nearest-
                neighbor interpolation, similar to the method pro- posed by Behrens
                et al [Magnetic Resonance in Medicine, 50:1077-1088, 2003]. The data
                is not interpolated, but at each point we randomly choose one of the
                8 voxels sur- rounding a point. The probability of choosing a
                particular voxel is based on how close the point is to the centre of
                that voxel.- LINEAR: Linear interpolation of the vector field
                containing the principal directions at each point.
                flag: -interpolator %s
        ipthresh: (a float)
                Curvature threshold for tracking, expressed as the minimum dot
                product between two streamline orientations calculated over the
                length of a voxel. If the dot product between the previous and
                current directions is less than this threshold, then the streamline
                terminates. The default setting will terminate fibres that curve by
                more than 80 degrees. Set this to -1.0 to disable curvature checking
                completely.
                flag: -ipthresh %f
        iterations: (an integer (int or long))
                Number of streamlines to generate at each seed point. The default is
                5000.
                flag: -iterations %d
        maxcomponents: (an integer (int or long))
                The maximum number of tensor components in a voxel. This determines
                the size of the input file and does not say anything about the voxel
                classification. The default is 2 if the input model is multitensor
                and 1 if the input model is dt.
                flag: -maxcomponents %d
        numpds: (an integer (int or long))
                The maximum number of PDs in a voxel for input models sfpeak and
                pico. The default is 3 for input model sfpeak and 1 for input model
                pico. This option determines the size of the voxels in the input
                file and does not affect tracking. For tensor data, use the
                -maxcomponents option.
                flag: -numpds %d
        out_file: (a file name)
                output data file
                flag: -outputfile %s, position: -1
        output_root: (a file name)
                root directory for output
                flag: -outputroot %s, position: -1
        outputtracts: ('float' or 'double' or 'oogl')
                output tract file type
                flag: -outputtracts %s
        pdf: ('bingham' or 'watson' or 'acg')
                Specifies the model for PICo parameters. The default is "bingham.
                flag: -pdf %s
        seed_file: (an existing file name)
                seed file
                flag: -seedfile %s, position: 2
        stepsize: (a float)
                Step size for EULER and RK4 tracking. The default is 1mm.
                flag: -stepsize %f
                requires: tracker
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        tracker: ('fact' or 'euler' or 'rk4', nipype default value: fact)
                The tracking algorithm controls streamlines are generated from the
                data. The choices are: - FACT, which follows the local fibre
                orientation in each voxel. No interpolation is used.- EULER, which
                uses a fixed step size along the local fibre orientation. With
                nearest-neighbour interpolation, this method may be very similar to
                FACT, except that the step size is fixed, whereas FACT steps extend
                to the boundary of the next voxel (distance variable depending on
                the entry and exit points to the voxel).- RK4: Fourth-order Runge-
                Kutta method. The step size is fixed, however the eventual direction
                of the step is determined by taking and averaging a series of
                partial steps.
                flag: -tracker %s
        voxel_dims: (a list of from 3 to 3 items which are a float)
                voxel dimensions in mm
                flag: -voxeldims %s

Outputs::

        tracked: (an existing file name)
                output file containing reconstructed tracts
