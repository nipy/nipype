# -*- coding: utf-8 -*-
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import warnings
import nibabel as nb

from .base import NipyBaseInterface, have_nipy
from ..base import (TraitedSpec, traits, BaseInterfaceInputSpec,
                    File, isdefined)


class SimilarityInputSpec(BaseInterfaceInputSpec):
    volume1 = File(exists=True, desc="3D volume", mandatory=True)
    volume2 = File(exists=True, desc="3D volume", mandatory=True)
    mask1 = File(exists=True, desc="3D volume")
    mask2 = File(exists=True, desc="3D volume")
    metric = traits.Either(
        traits.Enum('cc', 'cr', 'crl1', 'mi', 'nmi', 'slr'),
        traits.Callable(),
        desc="""str or callable
Cost-function for assessing image similarity. If a string,
one of 'cc': correlation coefficient, 'cr': correlation
ratio, 'crl1': L1-norm based correlation ratio, 'mi': mutual
information, 'nmi': normalized mutual information, 'slr':
supervised log-likelihood ratio. If a callable, it should
take a two-dimensional array representing the image joint
histogram as an input and return a float.""",
        usedefault=True)


class SimilarityOutputSpec(TraitedSpec):
    similarity = traits.Float(desc="Similarity between volume 1 and 2")


class Similarity(NipyBaseInterface):
    """Calculates similarity between two 3D volumes. Both volumes have to be in
    the same coordinate system, same space within that coordinate system and
    with the same voxel dimensions.

    .. deprecated:: 0.10.0
       Use :py:class:`nipype.algorithms.metrics.Similarity` instead.

    Example
    -------
    >>> from nipype.interfaces.nipy.utils import Similarity
    >>> similarity = Similarity()
    >>> similarity.inputs.volume1 = 'rc1s1.nii'
    >>> similarity.inputs.volume2 = 'rc1s2.nii'
    >>> similarity.inputs.mask1 = 'mask.nii'
    >>> similarity.inputs.mask2 = 'mask.nii'
    >>> similarity.inputs.metric = 'cr'
    >>> res = similarity.run() # doctest: +SKIP
    """

    input_spec = SimilarityInputSpec
    output_spec = SimilarityOutputSpec

    def __init__(self, **inputs):
        warnings.warn(("This interface is deprecated since 0.10.0."
                       " Please use nipype.algorithms.metrics.Similarity"),
                      DeprecationWarning)
        super(Similarity, self).__init__(**inputs)

    def _run_interface(self, runtime):
        from nipy.algorithms.registration.histogram_registration import HistogramRegistration
        from nipy.algorithms.registration.affine import Affine

        vol1_nii = nb.load(self.inputs.volume1)
        vol2_nii = nb.load(self.inputs.volume2)

        if isdefined(self.inputs.mask1):
            mask1 = nb.load(self.inputs.mask1).get_data() == 1
        else:
            mask1 = None

        if isdefined(self.inputs.mask2):
            mask2 = nb.load(self.inputs.mask2).get_data() == 1
        else:
            mask2 = None

        histreg = HistogramRegistration(
            from_img=vol1_nii,
            to_img=vol2_nii,
            similarity=self.inputs.metric,
            from_mask=mask1,
            to_mask=mask2)
        self._similarity = histreg.eval(Affine())

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['similarity'] = self._similarity
        return outputs
