.. matlab_interface_devel:

===========================
How to wrap a MATLAB script
===========================

This is minimal script for wrapping MATLAB code. You should replace the MATLAB
code template, and define approriate inputs and outputs.

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
	        
	        # mfile = True  will create an .m file with your script and executed. Alternatively
	        # mfile can be set to False which will cause the matlab code to be passed
	        # as a commandline argument to the matlab executable (without creating any files).
	        # This, however, is less reliable and harder to debug (code will be reduced to
	        # a single line and stripped of any comments).
	        mlab = MatlabCommand(script=script, mfile=True)
					result = mlab.run()
	        return result.runtime
	
	    def _list_outputs(self): 
	        outputs = self._outputs().get() 
	        outputs['out_file'] = os.path.abspath(self.inputs.out_file) 
	        return outputs

