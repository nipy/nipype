.. _interface_devel:

===============================
How to wrap a command line tool
===============================

The aim of this section is to describe how external programs and scripts can be
wrapped for use in Nipype either as interactive interfaces or within the
workflow/pipeline environment. Currently, there is support for command line
executables/scripts and matlab scripts. One can also create pure Python
interfaces. The key to defining interfaces is to provide a formal specification
of inputs and outputs and determining what outputs are generated given a set of
inputs.

Defining inputs and outputs
===========================

In Nipype we use Enthought Traits to define inputs and outputs of the
interfaces. This allows to introduce easy type checking. Inputs and outputs are
grouped into separate classes (usually suffixed with InputSpec and OutputSpec).
For example:

.. testcode::
	
	class ExampleInputSpec(TraitedSpec):
		input_volume = File(desc = "Input volume", exists = True,
		                    mandatory = True)
		parameter = traits.Int(desc = "some parameter")
		
	class ExampleOutputSpec(TraitedSpec):
		output_volume = File(desc = "Output volume", exists = True)
		
For the Traits (and Nipype) to work correctly output and input spec has to be
inherited from TraitedSpec (however, this does not have to be direct
inheritance).

Traits (File, Int etc.) have different parameters (called metadata). In the
above example we have used the ``desc`` metadata which holds human readable
description of the input. The ``mandatory`` flag forces Nipype to throw an
exception if the input was not set. ``exists`` is a special flag that works only
for ``File traits`` and checks if the provided file exists. More details can be
found at `interface_specs`_.

The input and output specifications have to be connected to the our example
interface class:

.. testcode::

	class Example(Interface):
		input_spec = ExampleInputSpec
		output_spec = ExampleOutputSpec
		
Where the names of the classes grouping inputs and outputs were arbitrary the
names of the fields within the interface they are assigned are not (it always
has to be input_spec and output_spec). Of course this interface does not do much
because we have not specified how to process the inputs and create the outputs.
This can be done in many ways.
 
Command line executable
=======================

As with all interfaces command line wrappers need to have inputs defined.
Command line input spec has to inherit from CommandLineInputSpec which adds two
extra inputs: environ (a dictionary of environmental variables), and args (a
string defining extra flags). In addition input spec can define the relation
between the inputs and the generated command line. To achieve this we have
added two metadata: ``argstr`` (string defining how the argument should be
formated) and ``position`` (number defining the order of the arguments).
For example
 
.. testcode::

	class ExampleInputSpec(CommandLineSpec):
		input_volume = File(desc = "Input volume", exists = True,
		                    mandatory = True, position = 0, argstr="%s")
		parameter = traits.Int(desc = "some parameter", argstr = "--param %d")
		
As you probably noticed the ``argstr`` is a printf type string with formatting
symbols. For an input defined in InputSpec to be included into the executed
commandline ``argstr`` has to be included. Additionally inside the main
interface class you need to specify the name of the executable by assigning it
to the ``_cmd`` field. Also the main interface class needs to inherit from
`CommandLine`_:

.. testcode::

	class Example(CommandLine):
		_cmd = 'my_command'
		input_spec = ExampleInputSpec
		output_spec = ExampleOutputSpec
		
There is one more thing we need to take care of. When the executable finishes
processing it will presumably create some output files. We need to know which
files to look for, check if they exist and expose them to whatever node would
like to use them. This is done by implementing `_list_outputs`_ method in the
main interface class. Basically what it does is assigning the expected output
files to the fields of our output spec:

.. testcode::

	def _list_outputs(self):
		outputs = self.output_spec().get()
		outputs['output_volume'] = os.path.abspath('name_of_the_file_this_cmd_made.nii')
		return outputs
		
Sometimes the inputs need extra parsing before turning into command line
parameters. For example imagine a parameter selecting between three methods:
"old", "standard" and "new". Imagine also that the command line accept this as
a parameter "--method=" accepting 0, 1 or 2. Since we are aiming to make nipype
scripts as informative as possible it's better to define the inputs as
following:

.. testcode::

	class ExampleInputSpec(CommandLineSpec):
		method = traits.Enum("old", "standard", "new", desc = "method",
		                     argstr="--method=%d")

Here we've used the Enum trait which restricts input a few fixed options. If we
would leave it as it is it would not work since the argstr is expecting
numbers. We need to do additional parsing by overloading the following method
in the main interface class:

.. testcode::
	
	def _format_arg(self, name, spec, value):
		if name == 'method':
		    return spec.argstr%{"old":0, "standard":1, "new":2}[value]
		return super(Example, self)._format_arg(name, spec, value)
		
Here is a minimalistic interface for the gzip command:

.. testcode::
	
	from nipype.interfaces.base import (
	    TraitedSpec, 
	    CommandLineInputSpec,
	    CommandLine, 
	    File
	)
	import os
	
	class GZipInputSpec(CommandLineInputSpec):
	    input_file = File(desc="File", exists=True, mandatory=True, argstr="%s")
	        
	class GZipOutputSpec(TraitedSpec):
	    output_file = File(desc = "Zip file", exists = True)
	        
	class GZipTask(CommandLine):
	    input_spec = GZipInputSpec
	    output_spec = GZipOutputSpec
	    cmd = 'gzip'
	    
	    def _list_outputs(self):
	            outputs = self.output_spec().get()
	            outputs['output_file'] = os.path.abspath(self.inputs.input_file + ".gz")
	            return outputs
	            
	if __name__ == '__main__':
	    
	    zipper = GZipTask(input_file='an_existing_file')
	    print zipper.cmdline
	    zipper.run()

Creating outputs on the fly
===========================

In many cases, command line executables will require specifying output file
names as arguments on the command line. We have simplified this procedure with
three additional metadata terms: ``name_source``, ``name_template``,
``keep_extension``.

For example in the :ref:`InvWarp <nipype.interfaces.fsl.InvWarp>` class, the
``inverse_warp`` parameter is the name of the output file that is created by
the routine.

.. testcode::

    class InvWarpInputSpec(FSLCommandInputSpec):
        ...
        inverse_warp = File(argstr='--out=%s', name_source=['warp'],
                            hash_files=False, name_template='%s_inverse',
        ...

we add several metadata to inputspec.

name_source
    indicates which field to draw from, this field must be the name of a File.

hash_files
    indicates that the input for this field if provided should not be used in
    computing the input hash for this interface.

name_template (optional)
     overrides the default ``_generated`` suffix
     
output_name (optional)
     name of the output (if this is not set same name as the input will be 
     assumed)

keep_extension (optional - not used)
     if you want the extension from the input to be kept

In addition one can add functionality to your class or base class, to allow
changing extensions specific to package or interface

.. testcode::

    def self._overload_extension(self, value):
        return value #do whatever you want here with the name

Finally, in the outputspec make sure the name matches that of the inputspec.

.. testcode::

    class InvWarpOutputSpec(TraitedSpec):
        inverse_warp = File(exists=True,
                            desc=('Name of output file, containing warps that '
                            'are the "reverse" of those in --warp.'))
