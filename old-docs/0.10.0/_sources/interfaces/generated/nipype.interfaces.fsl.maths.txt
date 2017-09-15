.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.fsl.maths
====================


.. _nipype.interfaces.fsl.maths.ApplyMask:


.. index:: ApplyMask

ApplyMask
---------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/fsl/maths.py#L171>`__

Wraps command **fslmaths**

Use fslmaths to apply a binary mask to another image.

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                image to operate on
                flag: %s, position: 2
        mask_file: (an existing file name)
                binary image defining mask space
                flag: -mas %s, position: 4
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal
                immediately, `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

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
        internal_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for calculations (default is float)
                flag: -dt %s, position: 1
        nan2zeros: (a boolean)
                change NaNs to zeros before doing anything
                flag: -nan, position: 3
        out_file: (a file name)
                image to write
                flag: %s, position: -2
        output_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for output (default uses input type)
                flag: -odt %s, position: -1
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type

Outputs::

        out_file: (an existing file name)
                image written after calculations

.. _nipype.interfaces.fsl.maths.BinaryMaths:


.. index:: BinaryMaths

BinaryMaths
-----------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/fsl/maths.py#L274>`__

Wraps command **fslmaths**

Use fslmaths to perform mathematical operations using a second image or a numeric value.

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                image to operate on
                flag: %s, position: 2
        operand_file: (an existing file name)
                second image to perform operation with
                flag: %s, position: 5
                mutually_exclusive: operand_value
        operand_value: (a float)
                value to perform operation with
                flag: %.8f, position: 5
                mutually_exclusive: operand_file
        operation: ('add' or 'sub' or 'mul' or 'div' or 'rem' or 'max' or
                 'min')
                operation to perform
                flag: -%s, position: 4
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal
                immediately, `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

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
        internal_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for calculations (default is float)
                flag: -dt %s, position: 1
        nan2zeros: (a boolean)
                change NaNs to zeros before doing anything
                flag: -nan, position: 3
        out_file: (a file name)
                image to write
                flag: %s, position: -2
        output_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for output (default uses input type)
                flag: -odt %s, position: -1
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type

Outputs::

        out_file: (an existing file name)
                image written after calculations

.. _nipype.interfaces.fsl.maths.ChangeDataType:


.. index:: ChangeDataType

ChangeDataType
--------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/fsl/maths.py#L64>`__

Wraps command **fslmaths**

Use fslmaths to change the datatype of an image.

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                image to operate on
                flag: %s, position: 2
        output_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                output data type
                flag: -odt %s, position: -1
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal
                immediately, `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

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
        internal_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for calculations (default is float)
                flag: -dt %s, position: 1
        nan2zeros: (a boolean)
                change NaNs to zeros before doing anything
                flag: -nan, position: 3
        out_file: (a file name)
                image to write
                flag: %s, position: -2
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type

Outputs::

        out_file: (an existing file name)
                image written after calculations

.. _nipype.interfaces.fsl.maths.DilateImage:


.. index:: DilateImage

DilateImage
-----------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/fsl/maths.py#L195>`__

Wraps command **fslmaths**

Use fslmaths to perform a spatial dilation of an image.

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                image to operate on
                flag: %s, position: 2
        operation: ('mean' or 'modal' or 'max')
                filtering operation to perfoem in dilation
                flag: -dil%s, position: 6
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal
                immediately, `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

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
        internal_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for calculations (default is float)
                flag: -dt %s, position: 1
        kernel_file: (an existing file name)
                use external file for kernel
                flag: %s, position: 5
                mutually_exclusive: kernel_size
        kernel_shape: ('3D' or '2D' or 'box' or 'boxv' or 'gauss' or 'sphere'
                 or 'file')
                kernel shape to use
                flag: -kernel %s, position: 4
        kernel_size: (a float)
                kernel size - voxels for box/boxv, mm for sphere, mm sigma for gauss
                flag: %.4f, position: 5
                mutually_exclusive: kernel_file
        nan2zeros: (a boolean)
                change NaNs to zeros before doing anything
                flag: -nan, position: 3
        out_file: (a file name)
                image to write
                flag: %s, position: -2
        output_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for output (default uses input type)
                flag: -odt %s, position: -1
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type

Outputs::

        out_file: (an existing file name)
                image written after calculations

.. _nipype.interfaces.fsl.maths.ErodeImage:


.. index:: ErodeImage

ErodeImage
----------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/fsl/maths.py#L214>`__

Wraps command **fslmaths**

Use fslmaths to perform a spatial erosion of an image.

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                image to operate on
                flag: %s, position: 2
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal
                immediately, `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

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
        internal_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for calculations (default is float)
                flag: -dt %s, position: 1
        kernel_file: (an existing file name)
                use external file for kernel
                flag: %s, position: 5
                mutually_exclusive: kernel_size
        kernel_shape: ('3D' or '2D' or 'box' or 'boxv' or 'gauss' or 'sphere'
                 or 'file')
                kernel shape to use
                flag: -kernel %s, position: 4
        kernel_size: (a float)
                kernel size - voxels for box/boxv, mm for sphere, mm sigma for gauss
                flag: %.4f, position: 5
                mutually_exclusive: kernel_file
        minimum_filter: (a boolean, nipype default value: False)
                if true, minimum filter rather than erosion by zeroing-out
                flag: %s, position: 6
        nan2zeros: (a boolean)
                change NaNs to zeros before doing anything
                flag: -nan, position: 3
        out_file: (a file name)
                image to write
                flag: %s, position: -2
        output_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for output (default uses input type)
                flag: -odt %s, position: -1
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type

Outputs::

        out_file: (an existing file name)
                image written after calculations

.. _nipype.interfaces.fsl.maths.IsotropicSmooth:


.. index:: IsotropicSmooth

IsotropicSmooth
---------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/fsl/maths.py#L151>`__

Wraps command **fslmaths**

Use fslmaths to spatially smooth an image with a gaussian kernel.

Inputs::

        [Mandatory]
        fwhm: (a float)
                fwhm of smoothing kernel [mm]
                flag: -s %.5f, position: 4
                mutually_exclusive: sigma
        in_file: (an existing file name)
                image to operate on
                flag: %s, position: 2
        sigma: (a float)
                sigma of smoothing kernel [mm]
                flag: -s %.5f, position: 4
                mutually_exclusive: fwhm
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal
                immediately, `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

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
        internal_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for calculations (default is float)
                flag: -dt %s, position: 1
        nan2zeros: (a boolean)
                change NaNs to zeros before doing anything
                flag: -nan, position: 3
        out_file: (a file name)
                image to write
                flag: %s, position: -2
        output_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for output (default uses input type)
                flag: -odt %s, position: -1
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type

Outputs::

        out_file: (an existing file name)
                image written after calculations

.. _nipype.interfaces.fsl.maths.MathsCommand:


.. index:: MathsCommand

MathsCommand
------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/fsl/maths.py#L35>`__

Wraps command **fslmaths**


Inputs::

        [Mandatory]
        in_file: (an existing file name)
                image to operate on
                flag: %s, position: 2
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal
                immediately, `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

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
        internal_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for calculations (default is float)
                flag: -dt %s, position: 1
        nan2zeros: (a boolean)
                change NaNs to zeros before doing anything
                flag: -nan, position: 3
        out_file: (a file name)
                image to write
                flag: %s, position: -2
        output_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for output (default uses input type)
                flag: -odt %s, position: -1
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type

Outputs::

        out_file: (an existing file name)
                image written after calculations

.. _nipype.interfaces.fsl.maths.MaxImage:


.. index:: MaxImage

MaxImage
--------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/fsl/maths.py#L126>`__

Wraps command **fslmaths**

Use fslmaths to generate a max image across a given dimension.

Examples
~~~~~~~~
from nipype.interfaces.fsl.maths import MaxImage
maxer = MaxImage()
maxer.inputs.in_file = "functional.nii"
maxer.dimension = "T"
maths.cmdline
fslmaths functional.nii -Tmax functional_max.nii

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                image to operate on
                flag: %s, position: 2
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal
                immediately, `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        dimension: ('T' or 'X' or 'Y' or 'Z', nipype default value: T)
                dimension to max across
                flag: -%smax, position: 4
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        internal_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for calculations (default is float)
                flag: -dt %s, position: 1
        nan2zeros: (a boolean)
                change NaNs to zeros before doing anything
                flag: -nan, position: 3
        out_file: (a file name)
                image to write
                flag: %s, position: -2
        output_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for output (default uses input type)
                flag: -odt %s, position: -1
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type

Outputs::

        out_file: (an existing file name)
                image written after calculations

.. _nipype.interfaces.fsl.maths.MeanImage:


.. index:: MeanImage

MeanImage
---------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/fsl/maths.py#L113>`__

Wraps command **fslmaths**

Use fslmaths to generate a mean image across a given dimension.

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                image to operate on
                flag: %s, position: 2
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal
                immediately, `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        dimension: ('T' or 'X' or 'Y' or 'Z', nipype default value: T)
                dimension to mean across
                flag: -%smean, position: 4
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        internal_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for calculations (default is float)
                flag: -dt %s, position: 1
        nan2zeros: (a boolean)
                change NaNs to zeros before doing anything
                flag: -nan, position: 3
        out_file: (a file name)
                image to write
                flag: %s, position: -2
        output_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for output (default uses input type)
                flag: -odt %s, position: -1
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type

Outputs::

        out_file: (an existing file name)
                image written after calculations

.. _nipype.interfaces.fsl.maths.MultiImageMaths:


.. index:: MultiImageMaths

MultiImageMaths
---------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/fsl/maths.py#L289>`__

Wraps command **fslmaths**

Use fslmaths to perform a sequence of mathematical operations.

Examples
~~~~~~~~
from nipype.interfaces.fsl import MultiImageMaths
maths = MultiImageMaths()
maths.inputs.in_file = "functional.nii"
maths.inputs.op_string = "-add %s -mul -1 -div %s"
maths.inputs.operand_files = ["functional2.nii", "functional3.nii"]
maths.inputs.out_file = functional4.nii
maths.cmdline
fslmaths functional1.nii -add functional2.nii -mul -1 -div functional3.nii functional4.nii

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                image to operate on
                flag: %s, position: 2
        op_string: (a string)
                python formatted string of operations to perform
                flag: %s, position: 4
        operand_files: (an existing file name)
                list of file names to plug into op string
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal
                immediately, `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

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
        internal_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for calculations (default is float)
                flag: -dt %s, position: 1
        nan2zeros: (a boolean)
                change NaNs to zeros before doing anything
                flag: -nan, position: 3
        out_file: (a file name)
                image to write
                flag: %s, position: -2
        output_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for output (default uses input type)
                flag: -odt %s, position: -1
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type

Outputs::

        out_file: (an existing file name)
                image written after calculations

.. _nipype.interfaces.fsl.maths.SpatialFilter:


.. index:: SpatialFilter

SpatialFilter
-------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/fsl/maths.py#L235>`__

Wraps command **fslmaths**

Use fslmaths to spatially filter an image.

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                image to operate on
                flag: %s, position: 2
        operation: ('mean' or 'median' or 'meanu')
                operation to filter with
                flag: -f%s, position: 6
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal
                immediately, `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

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
        internal_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for calculations (default is float)
                flag: -dt %s, position: 1
        kernel_file: (an existing file name)
                use external file for kernel
                flag: %s, position: 5
                mutually_exclusive: kernel_size
        kernel_shape: ('3D' or '2D' or 'box' or 'boxv' or 'gauss' or 'sphere'
                 or 'file')
                kernel shape to use
                flag: -kernel %s, position: 4
        kernel_size: (a float)
                kernel size - voxels for box/boxv, mm for sphere, mm sigma for gauss
                flag: %.4f, position: 5
                mutually_exclusive: kernel_file
        nan2zeros: (a boolean)
                change NaNs to zeros before doing anything
                flag: -nan, position: 3
        out_file: (a file name)
                image to write
                flag: %s, position: -2
        output_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for output (default uses input type)
                flag: -odt %s, position: -1
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type

Outputs::

        out_file: (an existing file name)
                image written after calculations

.. _nipype.interfaces.fsl.maths.TemporalFilter:


.. index:: TemporalFilter

TemporalFilter
--------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/fsl/maths.py#L320>`__

Wraps command **fslmaths**

Use fslmaths to apply a low, high, or bandpass temporal filter to a timeseries.

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                image to operate on
                flag: %s, position: 2
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal
                immediately, `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        highpass_sigma: (a float, nipype default value: -1)
                highpass filter sigma (in volumes)
                flag: -bptf %.6f, position: 4
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        internal_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for calculations (default is float)
                flag: -dt %s, position: 1
        lowpass_sigma: (a float, nipype default value: -1)
                lowpass filter sigma (in volumes)
                flag: %.6f, position: 5
        nan2zeros: (a boolean)
                change NaNs to zeros before doing anything
                flag: -nan, position: 3
        out_file: (a file name)
                image to write
                flag: %s, position: -2
        output_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for output (default uses input type)
                flag: -odt %s, position: -1
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type

Outputs::

        out_file: (an existing file name)
                image written after calculations

.. _nipype.interfaces.fsl.maths.Threshold:


.. index:: Threshold

Threshold
---------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/fsl/maths.py#L83>`__

Wraps command **fslmaths**

Use fslmaths to apply a threshold to an image in a variety of ways.

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                image to operate on
                flag: %s, position: 2
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal
                immediately, `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        thresh: (a float)
                threshold value
                flag: %s, position: 4

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        direction: ('below' or 'above', nipype default value: below)
                zero-out either below or above thresh value
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        internal_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for calculations (default is float)
                flag: -dt %s, position: 1
        nan2zeros: (a boolean)
                change NaNs to zeros before doing anything
                flag: -nan, position: 3
        out_file: (a file name)
                image to write
                flag: %s, position: -2
        output_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for output (default uses input type)
                flag: -odt %s, position: -1
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type
        use_nonzero_voxels: (a boolean)
                use nonzero voxels to caluclate robust range
                requires: use_robust_range
        use_robust_range: (a boolean)
                inteperet thresh as percentage (0-100) of robust range

Outputs::

        out_file: (an existing file name)
                image written after calculations

.. _nipype.interfaces.fsl.maths.UnaryMaths:


.. index:: UnaryMaths

UnaryMaths
----------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/fsl/maths.py#L252>`__

Wraps command **fslmaths**

Use fslmaths to perorm a variety of mathematical operations on an image.

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                image to operate on
                flag: %s, position: 2
        operation: ('exp' or 'log' or 'sin' or 'cos' or 'tan' or 'asin' or
                 'acos' or 'atan' or 'sqr' or 'sqrt' or 'recip' or 'abs' or 'bin' or
                 'binv' or 'fillh' or 'fillh26' or 'index' or 'edge' or 'nan' or
                 'nanm' or 'rand' or 'randn' or 'range')
                operation to perform
                flag: -%s, position: 4
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal
                immediately, `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

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
        internal_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for calculations (default is float)
                flag: -dt %s, position: 1
        nan2zeros: (a boolean)
                change NaNs to zeros before doing anything
                flag: -nan, position: 3
        out_file: (a file name)
                image to write
                flag: %s, position: -2
        output_datatype: ('float' or 'char' or 'int' or 'short' or 'double'
                 or 'input')
                datatype to use for output (default uses input type)
                flag: -odt %s, position: -1
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type

Outputs::

        out_file: (an existing file name)
                image written after calculations
