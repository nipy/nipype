.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.legacy.registration
=======================================


.. _nipype.interfaces.semtools.legacy.registration.scalartransform:


.. index:: scalartransform

scalartransform
---------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/legacy/registration.py#L24>`__

Wraps command ** scalartransform **

title: ScalarTransform (DTIProcess)

category: Legacy.Registration

version: 1.0.0

documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/DTIProcess

license: Copyright (c)  Casey Goodlett. All rights reserved.
  See http://www.ia.unc.edu/dev/Copyright.htm for details.
     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notices for more information.

contributor: Casey Goodlett

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        deformation: (an existing file name)
                Deformation field.
                flag: --deformation %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        h_field: (a boolean)
                The deformation is an h-field.
                flag: --h_field
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        input_image: (an existing file name)
                Image to tranform
                flag: --input_image %s
        interpolation: ('nearestneighbor' or 'linear' or 'cubic')
                Interpolation type (nearestneighbor, linear, cubic)
                flag: --interpolation %s
        invert: (a boolean)
                Invert tranform before applying.
                flag: --invert
        output_image: (a boolean or a file name)
                The transformed image
                flag: --output_image %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        transformation: (a boolean or a file name)
                Output file for transformation parameters
                flag: --transformation %s

Outputs::

        output_image: (an existing file name)
                The transformed image
        transformation: (an existing file name)
                Output file for transformation parameters
