.. python_interface_devel:

===========================
How to wrap a Python script
===========================

This is a minimal pure python interface. As you can see all you need to do is to
do is to define inputs, outputs, _run_interface() (not run()), and _list_outputs. 

.. testcode::
	
    from nipype.interfaces.base import BaseInterface, \
        BaseInterfaceInputSpec, traits, File, TraitedSpec
    from nipype.utils.filemanip import split_filename
        
    import nibabel as nb
    import numpy as np
    import os
    
    class SimpleThresholdInputSpec(BaseInterfaceInputSpec):
        volume = File(exists=True, desc='volume to be thresholded', mandatory=True)
        threshold = traits.Float(desc='everything below this value will be set to zero',
                                 mandatory=True)
        
        
    class SimpleThresholdOutputSpec(TraitedSpec):
        thresholded_volume = File(exists=True, desc="thresholded volume")
        
    
    class SimpleThreshold(BaseInterface):
        input_spec = SimpleThresholdInputSpec
        output_spec = SimpleThresholdOutputSpec
        
        def _run_interface(self, runtime):
            fname = self.inputs.volume
            img = nb.load(fname)
            data = np.array(img.get_data())
            
            active_map = data > self.inputs.threshold
            
            thresholded_map = np.zeros(data.shape)
            thresholded_map[active_map] = data[active_map]
            
            new_img = nb.Nifti1Image(thresholded_map, img.get_affine(), img.get_header())
            _, base, _ = split_filename(fname)
            nb.save(new_img, base + '_thresholded.nii')
            
            return runtime
        
        def _list_outputs(self):
            outputs = self._outputs().get()
            fname = self.inputs.volume
            _, base, _ = split_filename(fname)
            outputs["thresholded_volume"] = os.path.abspath(base + '_thresholded.nii')
            return outputs
