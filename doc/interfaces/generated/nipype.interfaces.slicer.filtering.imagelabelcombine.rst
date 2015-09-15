.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.slicer.filtering.imagelabelcombine
=============================================


.. _nipype.interfaces.slicer.filtering.imagelabelcombine.ImageLabelCombine:


.. index:: ImageLabelCombine

ImageLabelCombine
-----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/slicer/filtering/imagelabelcombine.py#L20>`__

Wraps command **ImageLabelCombine **

title: Image Label Combine

category: Filtering

description: Combine two label maps into one

version: 0.1.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/ImageLabelCombine

contributor: Alex Yarmarkovich (SPL, BWH)

Inputs::

        [Mandatory]

        [Optional]
        InputLabelMap_A: (an existing file name)
                Label map image
                flag: %s, position: -3
        InputLabelMap_B: (an existing file name)
                Label map image
                flag: %s, position: -2
        OutputLabelMap: (a boolean or a file name)
                Resulting Label map image
                flag: %s, position: -1
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        first_overwrites: (a boolean)
                Use first or second label when both are present
                flag: --first_overwrites
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        OutputLabelMap: (an existing file name)
                Resulting Label map image
