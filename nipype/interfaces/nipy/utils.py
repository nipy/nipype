"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)

"""
import warnings

import nibabel as nb

from ...utils.misc import package_check

have_nipy = True
try:
    package_check('nipy')
except Exception, e:
    have_nipy = False
else:
    from nipy.algorithms.registration.histogram_registration import HistogramRegistration
    from nipy.algorithms.registration.affine import Affine

from ..base import (TraitedSpec, BaseInterface, traits,
                    BaseInterfaceInputSpec, File, isdefined)


class SimilarityInputSpec(BaseInterfaceInputSpec):

    volume1 = File(exists=True, desc="3D/4D volume", mandatory=True)
    volume2 = File(exists=True, desc="3D/4D volume", mandatory=True)
    mask1 = File(exists=True, desc="3D volume")
    mask2 = File(exists=True, desc="3D volume")
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
    similarity = traits.List( traits.Float(desc="Similarity between volume 1 and 2, frame by frame"))


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
    >>> similarity.inputs.mask1 = 'mask.nii'
    >>> similarity.inputs.mask2 = 'mask.nii'
    >>> similarity.inputs.metric = 'cr'
    >>> res = similarity.run() # doctest: +SKIP
    """

    input_spec = SimilarityInputSpec
    output_spec = SimilarityOutputSpec

    def _run_interface(self, runtime):

        vol1_nii = nb.load(self.inputs.volume1)
        vol2_nii = nb.load(self.inputs.volume2)

        dims = vol1_nii.get_data().ndim

        if dims==3 or dims==2:
            vols1 = [ vol1_nii ]
            vols2 = [ vol2_nii ]
        if dims==4:
            vols1 = nb.four_to_three( vol1_nii )
            vols2 = nb.four_to_three( vol2_nii )

        if dims<2 or dims>4:
            raise RuntimeError( 'Image dimensions not supported (detected %dD file)' % dims )

        if isdefined(self.inputs.mask1):
            mask1 = nb.load(self.inputs.mask1).get_data() == 1
        else:
            mask1 = None

        if isdefined(self.inputs.mask2):
            mask2 = nb.load(self.inputs.mask2).get_data() == 1
        else:
            mask2 = None

        self._similarity = []

        for ts1,ts2 in zip( vols1, vols2 ):
            histreg = HistogramRegistration(from_img = ts1,
                                            to_img = ts2,
                                            similarity=self.inputs.metric,
                                            from_mask = mask1,
                                            to_mask = mask2)
            self._similarity.append( histreg.eval(Affine()) )

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['similarity'] = self._similarity
        return outputs
