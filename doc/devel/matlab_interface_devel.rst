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

.. testcode::

    import os
    from nipype.interfaces.base import File, traits
    from nipype.interfaces.matlab import MatlabCommand, MatlabInputSpec

    class HelloWorldInputSpec( MatlabInputSpec):
        name = traits.Str(mandatory = True,
                          desc = 'Name of person to say hello to')

    class HelloWorldOutputSpec(MatlabInputSpec):
        matlab_output = traits.Str()

    class HelloWorld(MatlabCommand):
        """ Basic Hello World that displays Hello <name> in MATLAB

        Returns
        -------

        matlab_output : capture of matlab output which may be
                        parsed by user to get computation results

        Examples
        --------

        >>> hello = HelloWorld()
        >>> hello.inputs.name = 'hello_world'
        >>> out = hello.run()
        >>> print(out.outputs.matlab_output)
        """
        input_spec = HelloWorldInputSpec
        output_spec = HelloWorldOutputSpec

        def _my_script(self):
            """This is where you implement your script"""
            script = """
            disp('Hello %s Python')
            two = 1 + 1
            """%(self.inputs.name)
            return script

        def run(self, **inputs):
            ## inject your script
            self.inputs.script =  self._my_script()
            results = super(MatlabCommand, self).run( **inputs)
            stdout = results.runtime.stdout
            # attach stdout to outputs to access matlab results
            results.outputs.matlab_output = stdout
            return results

        def _list_outputs(self):
            outputs = self._outputs().get()
            return outputs


.. literalinclude:: matlab_example2.py

.. admonition:: Example source code

  You can download :download:`the source code of this example <matlab_example2.py>`.

.. include:: ../links_names.txt
