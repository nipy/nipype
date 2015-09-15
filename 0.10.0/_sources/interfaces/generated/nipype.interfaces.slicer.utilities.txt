.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.slicer.utilities
===========================


.. _nipype.interfaces.slicer.utilities.EMSegmentTransformToNewFormat:


.. index:: EMSegmentTransformToNewFormat

EMSegmentTransformToNewFormat
-----------------------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/slicer/utilities.py#L19>`__

Wraps command **EMSegmentTransformToNewFormat **

title:
  Transform MRML Files to New EMSegmenter Standard


category:
  Utilities


description:
  Transform MRML Files to New EMSegmenter Standard

Inputs::

        [Mandatory]
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
        inputMRMLFileName: (an existing file name)
                Active MRML scene that contains EMSegment algorithm parameters in
                the format before 3.6.3 - please include absolute file name in path.
                flag: --inputMRMLFileName %s
        outputMRMLFileName: (a boolean or a file name)
                Write out the MRML scene after transformation to format 3.6.3 has
                been made. - has to be in the same directory as the input MRML file
                due to Slicer Core bug - please include absolute file name in path
                flag: --outputMRMLFileName %s
        templateFlag: (a boolean)
                Set to true if the transformed mrml file should be used as template
                file
                flag: --templateFlag

Outputs::

        outputMRMLFileName: (an existing file name)
                Write out the MRML scene after transformation to format 3.6.3 has
                been made. - has to be in the same directory as the input MRML file
                due to Slicer Core bug - please include absolute file name in path
