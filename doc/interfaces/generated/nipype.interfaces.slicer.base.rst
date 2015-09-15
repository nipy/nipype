.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.slicer.base
======================


.. _nipype.interfaces.slicer.base.SlicerCommandLine:


.. index:: SlicerCommandLine

SlicerCommandLine
-----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/slicer/base.py#L3>`__

Wraps command **None**


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
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        None
