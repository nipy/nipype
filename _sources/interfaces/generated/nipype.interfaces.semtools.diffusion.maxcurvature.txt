.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.diffusion.maxcurvature
==========================================


.. _nipype.interfaces.semtools.diffusion.maxcurvature.maxcurvature:


.. index:: maxcurvature

maxcurvature
------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/maxcurvature.py#L20>`__

Wraps command ** maxcurvature **

title: MaxCurvature-Hessian (DTIProcess)

category: Diffusion

description: This program computes the Hessian of the FA image (--image). We use this scalar image as a registration input when doing DTI atlas building. For most adult FA we use a sigma of 2 whereas for neonate or primate images and sigma of 1 or 1.5 is more appropriate. For really noisy images, 2.5 - 4 can be considered. The final image (--output) shows the main feature of the input image.

version: 1.1.0

documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/DTIProcess

license: Copyright (c)  Casey Goodlett. All rights reserved.
  See http://www.ia.unc.edu/dev/Copyright.htm for details.
     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notices for more information.

contributor: Casey Goodlett

acknowledgements: Hans Johnson(1,3,4); Kent Williams(1); (1=University of Iowa Department of Psychiatry, 3=University of Iowa Department of Biomedical Engineering, 4=University of Iowa Department of Electrical and Computer Engineering) provided conversions to make DTIProcess compatible with Slicer execution, and simplified the stand-alone build requirements by removing the dependancies on boost and a fortran compiler.

Inputs::

        [Mandatory]

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
        image: (an existing file name)
                FA Image
                flag: --image %s
        output: (a boolean or a file name)
                Output File
                flag: --output %s
        sigma: (a float)
                Scale of Gradients
                flag: --sigma %f
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        verbose: (a boolean)
                produce verbose output
                flag: --verbose

Outputs::

        output: (an existing file name)
                Output File
