.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.converters
==============================


.. _nipype.interfaces.semtools.converters.DWICompare:


.. index:: DWICompare

DWICompare
----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/converters.py#L55>`__

Wraps command ** DWICompare **

title: Nrrd DWI comparison

category: Converters

description: Compares two nrrd format DWI images and verifies that gradient magnitudes, gradient directions, measurement frame, and max B0 value are identicle.  Used for testing DWIConvert.

version: 0.1.0.$Revision: 916 $(alpha)

documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/DWIConvert

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Mark Scully (UIowa)

acknowledgements: This work is part of the National Alliance for Medical Image Computing (NAMIC), funded by the National Institutes of Health through the NIH Roadmap for Medical Research, Grant U54 EB005149.  Additional support for DTI data produced on Philips scanners was contributed by Vincent Magnotta and Hans Johnson at the University of Iowa.

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
        inputVolume1: (an existing file name)
                First input volume (.nhdr or .nrrd)
                flag: --inputVolume1 %s
        inputVolume2: (an existing file name)
                Second input volume (.nhdr or .nrrd)
                flag: --inputVolume2 %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        None

.. _nipype.interfaces.semtools.converters.DWISimpleCompare:


.. index:: DWISimpleCompare

DWISimpleCompare
----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/converters.py#L19>`__

Wraps command ** DWISimpleCompare **

title: Nrrd DWI comparison

category: Converters

description: Compares two nrrd format DWI images and verifies that gradient magnitudes, gradient directions, measurement frame, and max B0 value are identicle.  Used for testing DWIConvert.

version: 0.1.0.$Revision: 916 $(alpha)

documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/DWIConvert

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Mark Scully (UIowa)

acknowledgements: This work is part of the National Alliance for Medical Image Computing (NAMIC), funded by the National Institutes of Health through the NIH Roadmap for Medical Research, Grant U54 EB005149.  Additional support for DTI data produced on Philips scanners was contributed by Vincent Magnotta and Hans Johnson at the University of Iowa.

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        checkDWIData: (a boolean)
                check for existence of DWI data, and if present, compare it
                flag: --checkDWIData
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVolume1: (an existing file name)
                First input volume (.nhdr or .nrrd)
                flag: --inputVolume1 %s
        inputVolume2: (an existing file name)
                Second input volume (.nhdr or .nrrd)
                flag: --inputVolume2 %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        None
