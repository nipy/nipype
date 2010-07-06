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
In NiPyPe we have decided to use Enthought Traits to define inputs and outputs of the interfaces. 
This allows to introduce easy type checking. Inputs and outputs are grouped into separete classes 
(usually suffixed with InputSpec and OutputSpec). For example:

.. testcode::
	
	class ExampleInputSpec(TraitedSpec):
		input_volume = File(desc = "Input volume", exists = True, mandatory = True)
		parameter = traits.Int(desc = "some parameter")
		
	class ExampleOutputSpec(TraitedSpec):
		output_volume = File(desc = "Output volume", exists = True)
		
For the Traits (and NiPyPe) to work correctly output and input spec has to be inherited from TraitedSpec 
(however, this does not have to be direct inheritance). 

Traits (File, Int etc.) have different parameters (called metadata). In the above example we have used the desc metadata 
which holds human readable description of the input. mandatory flag forces NiPyPe to throw an exception if the input was not set.
exists is a special flag that works only for File traits and checks if the provided file exists.

The input and output specifications have to be connected to the our example interface class:

.. testcode::

	class Example(Interface):
		input_spec = ExampleInputSpec
		output_spec = ExampleOutputSpec
		
Where the names of the classes grouping inputs and outputs were arbitrary the names of the fields within 
the interface they are assigned are not (it always has to be input_spec and output_spec). Of course this interface does not do much 
because we have not specified how to process the inputs and create the outputs. This can be done in many ways.
 
Command line executable
=======================
As with all interfaces command line wrappers need to have inputs defined. Command line input spec has to inherit from 
CommandLineInputSpec which adds two extra inputs: environ (a dictionary of environmental variables), and args (a string defining extra flags).
 In addition input spec can define the relation between the inputs and the generated command line. To achieve this we have adde two metadata: argstr 
 (string defining how the argument should be formated) and position (number defining the order of the arguments). For example
 
.. testcode::

	class ExampleInputSpec(CommandLineSpec):
		input_volume = File(desc = "Input volume", exists = True, mandatory = True, position = 0)
		parameter = traits.Int(desc = "some parameter", argstr = "--param %d")
		
As you probably noticed the argstr is a printf type string with formatting symbols. Additionally inside the main
interface class you need to specify the name of the executable by assigning it to the _cmd field. Also the main interface 
class needs to inherit from CommandLine:

.. testcode::

	class Example(CommandLine):
		_cmd = 'my_command'
		input_spec = ExampleInputSpec
		output_spec = ExampleOutputSpec
		
There is one more thing we need to take care of. When the executable finishes processing it will presumably create some 
output files. We need to know which files to look for, check if they exist and expose them to whatever node would like to use them.
This is done by implementing _list_outputs() method in the main interface class. Basically what it does is assigning the expected output files to the fields of our
output spec:

.. testcode::

	def _list_outputs(self):
		outputs = self.output_spec().get()
		outputs['output_volume'] = os.path.abspath('name_of_the_file_this_cmd_made.nii')
		return outputs
		
Sometimes the inputs need extra parsing before turning into command line parameters. For example imagine a parameter selecting between three methods: 
"old", "standard" and "new". Imagine also that the command line accept this as a parameter "--method=" accepting 0, 1 or 2. Since we
are aiming to make nipype scripts as informative as possible it's better to define the inputs as following:

.. testcode::

	class ExampleInputSpec(CommandLineSpec):
		method = traits.Enum("old", "standard", "new", desc = "method", argstr="--method=%d")

Here we've used the Enum trait which restricts input a few fixed options. If we would leave it as it is it would not work since the argstr is expecting
numbers. We need to do additional parsing by overloading the following method in the main interface class:

.. testcode::
	
	def _format_arg(self, name, value):
		if name == 'method':
		    return spec.argstr%{"old":0, "standard":1, "new":2}[value]
		return super(Example, self)._format_arg(name, spec, value)