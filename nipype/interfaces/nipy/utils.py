import warnings

import nibabel as nb

from ...utils.misc import package_check

try:
    package_check('nipy')
except Exception, e:
    warnings.warn('nipy not installed')
else:
    from nipy.algorithms.registration.histogram_registration import HistogramRegistration
    from nipy.algorithms.registration.affine import Affine

from ..base import (TraitedSpec, BaseInterface, traits,
                    BaseInterfaceInputSpec, File, isdefined)


class SimilarityInputSpec(BaseInterfaceInputSpec):

    volume1 = File(exists=True, desc="3D volume", mandatory=True)
    volume2 = File(exists=True, desc="3D volume", mandatory=True)
    mask1 = File(exists=True, desc="3D volume", mandatory=True)
    mask2 = File(exists=True, desc="3D volume", mandatory=True)
    metric = traits.Either(traits.Enum('cc', 'cr', 'crl1', 'mi', 'nmi', 'slr'),
                          traits.Callable(),
                         desc="""str or callable
Cost-function for assessing image similarity. If a string,
one of 'cc': correlation coefficient, 'cr': correlation
ratio, 'crl1': L1-norm based correlation ratio, 'mi': mutual
information, 'nmi': normalized mutual information, 'slr':
supervised log-likelihood ratio. If a callable, it should
take a two-dimensional array representing the image joint
histogram as an input and return a float.""", usedefault=True)


class SimilarityOutputSpec(TraitedSpec):

    similarity = traits.Float(desc="Similarity between volume 1 and 2")


class Similarity(BaseInterface):
    """Calculates similarity between two 3D volumes. Both volumes have to be in
    the same coordinate system, same space within that coordinate system and
    with the same voxel dimensions.

    Example
    -------
    >>> from nipype.interfaces.nipy.utils import Similarity
    >>> similarity = Similarity()
    >>> similarity.inputs.volume1 = 'rc1s1.nii'
    >>> similarity.inputs.volume2 = 'rc1s2.nii'
    >>> similarity.inputs.metric = 'cr'
    >>> res = similarity.run() # doctest: +SKIP
    """

    input_spec = SimilarityInputSpec
    output_spec = SimilarityOutputSpec

    def _run_interface(self, runtime):

        vol1_nii = nb.load(self.inputs.volume1)
        vol2_nii = nb.load(self.inputs.volume2)
        
        if isdefined(self.inputs.mask1):
            mask1_nii = nb.load(self.inputs.mask1)
            mask1_nii = nb.Nifti1Image(nb.load(self.inputs.mask1).get_data() == 1, mask1_nii.get_affine(),
                                       mask1_nii.get_header())
        else:
            mask1_nii = None
            
        if isdefined(self.inputs.mask2):
            mask2_nii = nb.load(self.inputs.mask2)
            mask2_nii = nb.Nifti1Image(nb.load(self.inputs.mask2).get_data() == 1, mask2_nii.get_affine(),
                                       mask2_nii.get_header())
        else:
            mask2_nii = None

        histreg = HistogramRegistration(from_img = vol1_nii,
                                        to_img = vol2_nii,
                                        similarity=self.inputs.metric,
                                        from_mask = mask1_nii,
                                        to_mask = mask2_nii)
        self._similarity = histreg.eval(Affine())

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['similarity'] = self._similarity
        return outputs