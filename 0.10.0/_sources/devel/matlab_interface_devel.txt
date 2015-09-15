.. matlab_interface_devel:

===========================
How to wrap a MATLAB script
===========================

This is minimal script for wrapping MATLAB code. You should replace the MATLAB
code template, and define approriate inputs and outputs.


Example 1
+++++++++

.. testcode::

	from nipype.interfaces.matlab import MatlabCommand
	from nipype.interfaces.base import TraitedSpec, BaseInterface, BaseInterfaceInputSpec, File
	import os
	from string import Template
	
	class ConmapTxt2MatInputSpec(BaseInterfaceInputSpec):
	    in_file = File(exists=True, mandatory=True)
	    out_file = File('cmatrix.mat', usedefault=True)
	    
	class ConmapTxt2MatOutputSpec(TraitedSpec):
	    out_file = File(exists=True)
	    
	class ConmapTxt2Mat(BaseInterface): 
	    input_spec = ConmapTxt2MatInputSpec 
	    output_spec = ConmapTxt2MatOutputSpec
	    
	    def _run_interface(self, runtime):
	        d = dict(in_file=self.inputs.in_file,
	        out_file=self.inputs.out_file)
	        #this is your MATLAB code template
	        script = Template("""in_file = ‘$in_file'; 
	out_file = ‘$out_file'; 
	ConmapTxt2Mat(in_file, out_file);
	exit;
	""").substitute(d)
	        
	        # mfile = True  will create an .m file with your script and executed. 
		# Alternatively
	        # mfile can be set to False which will cause the matlab code to be 
		# passed
	        # as a commandline argument to the matlab executable 
		# (without creating any files).
	        # This, however, is less reliable and harder to debug 
		# (code will be reduced to
	        # a single line and stripped of any comments).

	        mlab = MatlabCommand(script=script, mfile=True)
		result = mlab.run()
	        return result.runtime
	
	    def _list_outputs(self): 
	        outputs = self._outputs().get() 
	        outputs['out_file'] = os.path.abspath(self.inputs.out_file) 
	        return outputs


Example 2
+++++++++

By subclassing **MatlabCommand** for your main class, and **MatlabInputSpec** for your input and output spec, you gain access to some useful MATLAB hooks

.. testcode::
 
	import os
        from nipype.interfaces.base import File, traits 
        from nipype.interfaces.matlab import MatlabCommand, MatlabInputSpec
        

        class HelloWorldInputSpec( MatlabInputSpec):
            name = traits.Str( mandatory = True, 
                               desc = 'Name of person to say hello to')

    	class HelloWorldOutputSpec( MatlabInputSpec):
            matlab_output = traits.Str( )

        class HelloWorld( MatlabCommand):
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
            >>> print out.outputs.matlab_output 
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








