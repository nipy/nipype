.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.brains.utilities
====================================


.. _nipype.interfaces.semtools.brains.utilities.HistogramMatchingFilter:


.. index:: HistogramMatchingFilter

HistogramMatchingFilter
-----------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/brains/utilities.py#L26>`__

Wraps command ** HistogramMatchingFilter **

title: Write Out Image Intensities

category: BRAINS.Utilities

description: For Analysis

version: 0.1

contributor: University of Iowa Department of Psychiatry, http:://www.psychiatry.uiowa.edu

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
        histogramAlgorithm: ('OtsuHistogramMatching')
                 histogram algrithm selection
                flag: --histogramAlgorithm %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputBinaryVolume: (an existing file name)
                inputBinaryVolume
                flag: --inputBinaryVolume %s
        inputVolume: (an existing file name)
                The Input image to be computed for statistics
                flag: --inputVolume %s
        numberOfHistogramBins: (an integer (int or long))
                 number of histogram bin
                flag: --numberOfHistogramBins %d
        numberOfMatchPoints: (an integer (int or long))
                 number of histogram matching points
                flag: --numberOfMatchPoints %d
        outputVolume: (a boolean or a file name)
                Output Image File Name
                flag: --outputVolume %s
        referenceBinaryVolume: (an existing file name)
                referenceBinaryVolume
                flag: --referenceBinaryVolume %s
        referenceVolume: (an existing file name)
                The Input image to be computed for statistics
                flag: --referenceVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        verbose: (a boolean)
                 verbose mode running for debbuging
                flag: --verbose
        writeHistogram: (a string)
                 decide if histogram data would be written with prefixe of the file
                name
                flag: --writeHistogram %s

Outputs::

        outputVolume: (an existing file name)
                Output Image File Name
