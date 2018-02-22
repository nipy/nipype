.. matlab_interface_devel:

===========================
How to wrap a MATLAB script
===========================


Example 1
+++++++++

This is a minimal script for wrapping MATLAB code. You should replace the MATLAB
code template, and define approriate inputs and outputs.

.. literalinclude:: matlab_example1.py

.. admonition:: Example source code

  You can download :download:`the source code of this example <matlab_example1.py>`.

Example 2
+++++++++

By subclassing :class:`nipype.interfaces.matlab.MatlabCommand` for your main
class, and :class:`nipype.interfaces.matlab.MatlabInputSpec` for your input and
output spec, you gain access to some useful MATLAB hooks

.. literalinclude:: matlab_example2.py

.. admonition:: Example source code

  You can download :download:`the source code of this example <matlab_example2.py>`.

.. include:: ../links_names.txt
