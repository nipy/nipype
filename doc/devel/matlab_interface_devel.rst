.. matlab_interface_devel:

===========================
How to wrap a MATLAB script
===========================


.. testcode::

	from nipype.interfaces.matlab import MatlabInputSpec, MatlabCommand
	from nipype.interfaces.traits import File
	from nipype.interfaces.base import TraitedSpec
	import os
	
	class SampleMatlabScriptInputSpec(MatlabInputSpec):
	    in_file = File(exists=True, mandatory=True)
	    out_file = File('cmatrix.mat', usedefault=True)
	    
	class SampleMatlabScriptOutputSpec(TraitedSpec):
	    out_file = File(exists=True)
	    
	class SampleMatlabScript(MatlabCommand):
	    input_spec = SampleMatlabScriptInputSpec
	    output_spec = SampleMatlabScriptOutputSpec
	    
	    def __init__(self, **inputs):
	        inputs['script'] = """in_file = '%%in_file%%';
	out_file = '%%out_file%%';
	
	% Read data from in_file, do something with it
	cmatrix = [1 1]
	C = 1
	
	%Save stuff to out_file
	save(out_file, 'cmatrix', 'C');
	return;
	"""
	        return super(SampleMatlabScript, self).__init__(**inputs)
	    
	    def _run_interface(self, runtime):
	        #replace the placeholders in the template with inputs
	        self.inputs.script = self.inputs.script.replace("%%in_file%%", self.inputs.in_file) 
	        self.inputs.script = self.inputs.script.replace("%%out_file%%", self.inputs.out_file)
	        
	        # mfile = True  will create an .m file with your script and executed. Alternatively
	        # mfile can be set to False which will cause the matlab code to be passed
	        # as a commandline argument to the matlab executable (without creating any files).
	        # This, however, is less reliable and harder to debug (code will be reduced to
	        # a single line and stripped of any comments).
	        self.inputs.mfile = True
	        
	        return super(SampleMatlabScript, self)._run_interface(runtime)
	    
	    def _list_outputs(self):
	        outputs = self._outputs().get()
	        outputs['out_file'] = os.path.abspath(self.inputs.out_file)
	        return outputs