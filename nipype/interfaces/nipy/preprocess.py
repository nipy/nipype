from nipype.interfaces.base import TraitedSpec, BaseInterface, traits
from nipype.interfaces.traits import File
import nibabel as nb
import numpy as np
from nipy.neurospin.mask import compute_mask
from nipype.utils.misc import isdefined
import os

class ComputeMaskInputSpec(TraitedSpec):
    mean_volume = File(exists=True, mandatory=True)
    reference_volume = File(exists=True)
    m = traits.Float()
    M = traits.Float()
    cc = traits.Float() 
    
class ComputeMaskOutputSpec(TraitedSpec):
    brain_mask = File(exists=True)
    
class ComputeMask(BaseInterface):
    input_spec = ComputeMaskInputSpec
    output_spec = ComputeMaskOutputSpec
    
    def _run_interface(self, runtime):
        mean_volume_nii = nb.load(self.inputs.mean_volume)
        
        args = {}
        affine = None
        for key,_ in self.inputs.items():
            value = getattr(self.inputs, key)
            if isdefined(value):
                if key in ['mean_volume', 'reference_volume']:
                    nii = nb.load(value)
                    affine = nii.get_affine()
                    value = nii.get_data()
                args[key] = value
        
        brain_mask = compute_mask(**args)
        
        self._brain_mask_path = os.path.abspath("brain_mask.nii")
        nb.save(nb.Nifti1Image(brain_mask.astype(np.uint8), nii.get_affine()), self._brain_mask_path)
        
        runtime.returncode = 0
        return runtime
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["brain_mask"] = self._brain_mask_path
        return outputs