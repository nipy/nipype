.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.slicer.legacy.converters
===================================


.. _nipype.interfaces.slicer.legacy.converters.BSplineToDeformationField:


.. index:: BSplineToDeformationField

BSplineToDeformationField
-------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/slicer/legacy/converters.py#L19>`__

Wraps command **BSplineToDeformationField **

title: BSpline to deformation field

category: Legacy.Converters

description: Create a dense deformation field from a bspline+bulk transform.

version: 0.1.0.$Revision: 2104 $(alpha)

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/BSplineToDeformationField

contributor: Andrey Fedorov (SPL, BWH)

acknowledgements: This work is funded by NIH grants R01 CA111288 and U01 CA151261.

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        defImage: (a boolean or a file name)
                flag: --defImage %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        refImage: (an existing file name)
                flag: --refImage %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        tfm: (an existing file name)
                flag: --tfm %s

Outputs::

        defImage: (an existing file name)
