import numpy as np
import nibabel as nb

from ... import logging
from ..base import TraitedSpec, File, isdefined
from .base import DipyDiffusionInterface, DipyBaseInterfaceInputSpec

IFLOGGER = logging.getLogger("nipype.interface")


class APMQballInputSpec(DipyBaseInterfaceInputSpec):
    mask_file = File(exists=True, desc="An optional brain mask")


class APMQballOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class APMQball(DipyDiffusionInterface):
    """
    Calculates the anisotropic power map

    Example
    -------

    >>> import nipype.interfaces.dipy as dipy
    >>> apm = dipy.APMQball()
    >>> apm.inputs.in_file = 'diffusion.nii'
    >>> apm.inputs.in_bvec = 'bvecs'
    >>> apm.inputs.in_bval = 'bvals'
    >>> apm.run()                                   # doctest: +SKIP
    """

    input_spec = APMQballInputSpec
    output_spec = APMQballOutputSpec

    def _run_interface(self, runtime):
        from dipy.reconst import shm
        from dipy.data import get_sphere
        from dipy.reconst.peaks import peaks_from_model

        gtab = self._get_gradient_table()

        img = nb.load(self.inputs.in_file)
        data = np.asanyarray(img.dataobj)
        affine = img.affine
        mask = None
        if isdefined(self.inputs.mask_file):
            mask = np.asanyarray(nb.load(self.inputs.mask_file).dataobj)

        # Fit it
        model = shm.QballModel(gtab, 8)
        sphere = get_sphere("symmetric724")
        peaks = peaks_from_model(
            model=model,
            data=data,
            relative_peak_threshold=0.5,
            min_separation_angle=25,
            sphere=sphere,
            mask=mask,
        )
        apm = shm.anisotropic_power(peaks.shm_coeff)
        out_file = self._gen_filename("apm")
        nb.Nifti1Image(apm.astype("float32"), affine).to_filename(out_file)
        IFLOGGER.info("APM qball image saved as %s", out_file)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = self._gen_filename("apm")

        return outputs
