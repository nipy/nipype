.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.elastix.registration
===============================


.. _nipype.interfaces.elastix.registration.AnalyzeWarp:


.. index:: AnalyzeWarp

AnalyzeWarp
-----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/elastix/registration.py#L175>`__

Wraps command **transformix -def all -jac all -jacmat all**

Use transformix to get details from the input transform (generate
the corresponding deformation field, generate the determinant of the
Jacobian map or the Jacobian map itself)

Example
~~~~~~~

>>> from nipype.interfaces.elastix import AnalyzeWarp
>>> reg = AnalyzeWarp()
>>> reg.inputs.transform_file = 'TransformParameters.0.txt'
>>> reg.cmdline
'transformix -def all -jac all -jacmat all -out ./ -tp TransformParameters.0.txt'

Inputs::

        [Mandatory]
        output_path: (an existing directory name, nipype default value: ./)
                output directory
                flag: -out %s
        transform_file: (an existing file name)
                transform-parameter file, only 1
                flag: -tp %s

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
        num_threads: (an integer (int or long))
                set the maximum number of threads of elastix
                flag: -threads %01d
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        disp_field: (a file name)
                displacements field
        jacdet_map: (a file name)
                det(Jacobian) map
        jacmat_map: (a file name)
                Jacobian matrix map

.. _nipype.interfaces.elastix.registration.ApplyWarp:


.. index:: ApplyWarp

ApplyWarp
---------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/elastix/registration.py#L136>`__

Wraps command **transformix**

Use ``transformix`` to apply a transform on an input image.
The transform is specified in the transform-parameter file.

Example
~~~~~~~

>>> from nipype.interfaces.elastix import ApplyWarp
>>> reg = ApplyWarp()
>>> reg.inputs.moving_image = 'moving1.nii'
>>> reg.inputs.transform_file = 'TransformParameters.0.txt'
>>> reg.cmdline
'transformix -in moving1.nii -out ./ -tp TransformParameters.0.txt'

Inputs::

        [Mandatory]
        moving_image: (an existing file name)
                input image to deform
                flag: -in %s
        output_path: (an existing directory name, nipype default value: ./)
                output directory
                flag: -out %s
        transform_file: (an existing file name)
                transform-parameter file, only 1
                flag: -tp %s

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
        num_threads: (an integer (int or long))
                set the maximum number of threads of elastix
                flag: -threads %01d
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        warped_file: (a file name)
                input moving image warped to fixed image

.. _nipype.interfaces.elastix.registration.PointsWarp:


.. index:: PointsWarp

PointsWarp
----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/elastix/registration.py#L217>`__

Wraps command **transformix**

Use ``transformix`` to apply a transform on an input point set.
The transform is specified in the transform-parameter file.

Example
~~~~~~~

>>> from nipype.interfaces.elastix import PointsWarp
>>> reg = PointsWarp()
>>> reg.inputs.points_file = 'surf1.vtk'
>>> reg.inputs.transform_file = 'TransformParameters.0.txt'
>>> reg.cmdline
'transformix -out ./ -def surf1.vtk -tp TransformParameters.0.txt'

Inputs::

        [Mandatory]
        output_path: (an existing directory name, nipype default value: ./)
                output directory
                flag: -out %s
        points_file: (an existing file name)
                input points (accepts .vtk triangular meshes).
                flag: -def %s
        transform_file: (an existing file name)
                transform-parameter file, only 1
                flag: -tp %s

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
        num_threads: (an integer (int or long))
                set the maximum number of threads of elastix
                flag: -threads %01d
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        warped_file: (a file name)
                input points displaced in fixed image domain

.. _nipype.interfaces.elastix.registration.Registration:


.. index:: Registration

Registration
------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/elastix/registration.py#L44>`__

Wraps command **elastix**

Elastix nonlinear registration interface

Example
~~~~~~~

>>> from nipype.interfaces.elastix import Registration
>>> reg = Registration()
>>> reg.inputs.fixed_image = 'fixed1.nii'
>>> reg.inputs.moving_image = 'moving1.nii'
>>> reg.inputs.parameters = ['elastix.txt']
>>> reg.cmdline
'elastix -f fixed1.nii -m moving1.nii -out ./ -p elastix.txt'

Inputs::

        [Mandatory]
        fixed_image: (an existing file name)
                fixed image
                flag: -f %s
        moving_image: (an existing file name)
                moving image
                flag: -m %s
        output_path: (an existing directory name, nipype default value: ./)
                output directory
                flag: -out %s
        parameters: (a list of items which are an existing file name)
                parameter file, elastix handles 1 or more -p
                flag: -p %s...

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        fixed_mask: (an existing file name)
                mask for fixed image
                flag: -fMask %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        initial_transform: (an existing file name)
                parameter file for initial transform
                flag: -t0 %s
        moving_mask: (an existing file name)
                mask for moving image
                flag: -mMask %s
        num_threads: (an integer (int or long))
                set the maximum number of threads of elastix
                flag: -threads %01d
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        transform: (a list of items which are an existing file name)
                output transform
        warped_file: (a file name)
                input moving image warped to fixed image
        warped_files: (a list of items which are a file name)
                input moving image warped to fixed image at each level
        warped_files_flags: (a list of items which are a boolean)
                flag indicating if warped image was generated
