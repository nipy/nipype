import os
import warnings

import nibabel as nb
import numpy as np

from nipype.utils.misc import package_check

try:
    package_check('nipy')
except Exception, e:
    warnings.warn('nipy not installed')
else:
    from nipy.labs.mask import compute_mask
    from nipy.algorithms.registration import FmriRealign4d as FR4d
    from nipy import save_image

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
        for key in [k for k, _ in self.inputs.items() if k not in BaseInterfaceInputSpec().trait_names()]:
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

class FmriRealign4dInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc = "File to realign")
    tr = traits.Float(desc="TR in seconds")
    slice_order = traits.Enum("ascending","descending",desc = "slice order",mandatory=True)
    interleaved = traits.Bool(desc = "True if interleaved",mandatory=True)
    tr_slices = traits.Float(desc = "TR slices")
    start = traits.Float(desc="start")
    time_interp = traits.Bool(desc = "time interpolation")
    ref_scan = File(exists=True, desc = "Reference Scan")

class FmriRealign4dOutputSpec(TraitedSpec):
    out_file = File()
    par_file = File()

class FmriRealign4d(BaseInterface):
    """ realign using nipy's FmriRealign4d
    Examples
    --------
    >>> from nipype.interfaces.nipy.preprocess import FmriRealign4d
    >>> realigner = FmriRealign4d()
    >>> realigner.inputs.in_file = 'functional.nii'
    >>> realigner.inputs.tr = 2
    >>> realigner.inputs.slice_order = 'ascending'
    >>> realigner.inputs.interleaved = True
    >>> res = realigner.run()
    """
    
    input_spec = FmriRealign4dInputSpec
    output_spec = FmriRealign4dOutputSpec
    
    def _run_interface(self, runtime):
        im = nb.load(self.inputs.in_file)
        im.affine = im.get_affine()
        if not isdefined(self.inputs.tr):
            TR = None
        else:
            TR = self.inputs.tr
        if not isdefined(self.inputs.tr_slices):
            TR_slices = None
        else:
            TR_slices = self.inputs.tr_slices
        if not isdefined(self.inputs.start):
            start = 0.0
        else:    
            start = self.inputs.start
        if not isdefined(self.inputs.time_interp):
            time_interp = True
        else:
            time_interp = self.inputs.time_interp
            
        R = FR4d(im, tr=TR, slice_order=self.inputs.slice_order, interleaved=self.inputs.interleaved, tr_slices = TR_slices, time_interp = time_interp, start = start)
        if not isdefined(self.inputs.ref_scan):
            R.estimate()
        else:
            R.estimate()#refscan=self.inputs.ref_scan)??
        corr_run = R.resample()
        self._out_file_path = 'corr_%s'%(os.path.split(self.inputs.in_file)[1])
        save_image(corr_run[0],self._out_file_path)
        self._par_file_path = '%s.par'%(os.path.split(self.inputs.in_file)[1])
        mfile = open(self._par_file_path,'w')
        motion = R._transforms[0]
        #output a .par file that looks like fsl.mcflirt's .par file
        for i, mo in enumerate(motion):
            string = str(mo.rotation[0])+"  "+str(mo.rotation[1])+"  "+str(mo.rotation[2])+"  "+str(mo.translation[0])+"  "+str(mo.translation[1])+"  "+str(mo.translation[2])+"  \n"
            mfile.write(string)
        mfile.close()
        return runtime  
        
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = os.path.abspath(self._out_file_path)
        outputs['par_file'] = os.path.abspath(self._par_file_path)
        return outputs    
