.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.featurecreator
==================================


.. _nipype.interfaces.semtools.featurecreator.GenerateCsfClippedFromClassifiedImage:


.. index:: GenerateCsfClippedFromClassifiedImage

GenerateCsfClippedFromClassifiedImage
-------------------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/featurecreator.py#L18>`__

Wraps command ** GenerateCsfClippedFromClassifiedImage **

title: GenerateCsfClippedFromClassifiedImage

category: FeatureCreator

description: Get the distance from a voxel to the nearest voxel of a given tissue type.

version: 0.1.0.$Revision: 1 $(alpha)

documentation-url: http:://www.na-mic.org/

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was written by Hans J. Johnson.

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
        inputCassifiedVolume: (an existing file name)
                Required: input tissue label image
                flag: --inputCassifiedVolume %s
        outputVolume: (a boolean or a file name)
                Required: output image
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: output image
