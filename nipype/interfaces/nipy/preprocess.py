import os

import nibabel as nb
import numpy as np

from nipype.utils.misc import package_check
package_check('nipy')
from nipy.labs.mask import compute_mask

from nipype.interfaces.base import (TraitedSpec, BaseInterface, traits,
                                    BaseInterfaceInputSpec, isdefined, File)

class ComputeMaskInputSpec(BaseInterfaceInputSpec):
    mean_volume = File(exists=True, mandatory=True, desc="mean EPI image, used to compute the threshold for the mask")
    reference_volume = File(exists=True, desc="reference volume used to compute the mask. If none is give, the \
        mean volume is used.")
    m = traits.Float(desc="lower fraction of the histogram to be discarded")
    M = traits.Float(desc="upper fraction of the histogram to be discarded")
    cc = traits.Bool(desc="if True, only the largest connect component is kept") 
    
class ComputeMaskOutputSpec(TraitedSpec):
    brain_mask = File(exists=True)
    
class ComputeMask(BaseInterface):
    input_spec = ComputeMaskInputSpec
    output_spec = ComputeMaskOutputSpec
    
    def _run_interface(self, runtime):
        
        args = {}
        for key in [k for k,_ in self.inputs.items() if k not in BaseInterfaceInputSpec().trait_names()]:
            value = getattr(self.inputs, key)
            if isdefined(value):
                if key in ['mean_volume', 'reference_volume']:
                    nii = nb.load(value)
                    value = nii.get_data()
                args[key] = value
        
        brain_mask = compute_mask(**args)
        
        self._brain_mask_path = os.path.abspath("brain_mask.nii")
        nb.save(nb.Nifti1Image(brain_mask.astype(np.uint8), nii.get_affine()), self._brain_mask_path)
        
        return runtime
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["brain_mask"] = self._brain_mask_path
        return outputs


