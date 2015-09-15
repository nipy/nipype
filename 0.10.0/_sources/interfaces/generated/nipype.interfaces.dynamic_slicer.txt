.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.dynamic_slicer
=========================


.. _nipype.interfaces.dynamic_slicer.SlicerCommandLine:


.. index:: SlicerCommandLine

SlicerCommandLine
-----------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/interfaces/dynamic_slicer.py#L14>`__

Wraps command **Slicer3**

Experimental Slicer wrapper. Work in progress.

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
        module: (a string)
                name of the Slicer command line module you want to use

Outputs::

        None
