# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Image assessment algorithms. Typical overlap and error computation
measures to evaluate results from other processing units.

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
    >>> os.chdir(datadir)

'''
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import zip, range

import os
import os.path as op

import nibabel as nb
import numpy as np
from scipy.ndimage.morphology import binary_erosion
from scipy.spatial.distance import cdist, euclidean, dice, jaccard
from scipy.ndimage.measurements import center_of_mass, label

from .. import config, logging
from ..utils.misc import package_check

from ..interfaces.base import (BaseInterface, traits, TraitedSpec, File,
                               InputMultiPath, BaseInterfaceInputSpec,
                               isdefined)
from ..utils import NUMPY_MMAP

iflogger = logging.getLogger('interface')


class DistanceInputSpec(BaseInterfaceInputSpec):
    volume1 = File(
        exists=True,
        mandatory=True,
        desc="Has to have the same dimensions as volume2.")
    volume2 = File(
        exists=True,
        mandatory=True,
        desc="Has to have the same dimensions as volume1.")
    method = traits.Enum(
        "eucl_min",
        "eucl_cog",
        "eucl_mean",
        "eucl_wmean",
        "eucl_max",
        desc='""eucl_min": Euclidean distance between two closest points\
        "eucl_cog": mean Euclidian distance between the Center of Gravity\
        of volume1 and CoGs of volume2\
        "eucl_mean": mean Euclidian minimum distance of all volume2 voxels\
        to volume1\
        "eucl_wmean": mean Euclidian minimum distance of all volume2 voxels\
        to volume1 weighted by their values\
        "eucl_max": maximum over minimum Euclidian distances of all volume2\
        voxels to volume1 (also known as the Hausdorff distance)',
        usedefault=True)
    mask_volume = File(
        exists=True, desc="calculate overlap only within this mask.")


class DistanceOutputSpec(TraitedSpec):
    distance = traits.Float()
    point1 = traits.Array(shape=(3, ))
    point2 = traits.Array(shape=(3, ))
    histogram = File()


class Distance(BaseInterface):
    """Calculates distance between two volumes.
    """
    input_spec = DistanceInputSpec
    output_spec = DistanceOutputSpec

    _hist_filename = "hist.pdf"

    def _find_border(self, data):
        eroded = binary_erosion(data)
        border = np.logical_and(data, np.logical_not(eroded))
        return border

    def _get_coordinates(self, data, affine):
        if len(data.shape) == 4:
            data = data[:, :, :, 0]
        indices = np.vstack(np.nonzero(data))
        indices = np.vstack((indices, np.ones(indices.shape[1])))
        coordinates = np.dot(affine, indices)
        return coordinates[:3, :]

    def _eucl_min(self, nii1, nii2):
        origdata1 = nii1.get_data().astype(np.bool)
        border1 = self._find_border(origdata1)

        origdata2 = nii2.get_data().astype(np.bool)
        border2 = self._find_border(origdata2)

        set1_coordinates = self._get_coordinates(border1, nii1.affine)

        set2_coordinates = self._get_coordinates(border2, nii2.affine)

        dist_matrix = cdist(set1_coordinates.T, set2_coordinates.T)
        (point1, point2) = np.unravel_index(
            np.argmin(dist_matrix), dist_matrix.shape)
        return (euclidean(set1_coordinates.T[point1, :],
                          set2_coordinates.T[point2, :]),
                set1_coordinates.T[point1, :], set2_coordinates.T[point2, :])

    def _eucl_cog(self, nii1, nii2):
        origdata1 = np.logical_and(nii1.get_data() != 0,
                                   np.logical_not(np.isnan(nii1.get_data())))
        cog_t = np.array(center_of_mass(origdata1.copy())).reshape(-1, 1)
        cog_t = np.vstack((cog_t, np.array([1])))
        cog_t_coor = np.dot(nii1.affine, cog_t)[:3, :]

        origdata2 = np.logical_and(nii2.get_data() != 0,
                                   np.logical_not(np.isnan(nii2.get_data())))
        (labeled_data, n_labels) = label(origdata2)

        cogs = np.ones((4, n_labels))

        for i in range(n_labels):
            cogs[:3, i] = np.array(
                center_of_mass(origdata2, labeled_data, i + 1))

        cogs_coor = np.dot(nii2.affine, cogs)[:3, :]

        dist_matrix = cdist(cog_t_coor.T, cogs_coor.T)

        return np.mean(dist_matrix)

    def _eucl_mean(self, nii1, nii2, weighted=False):
        origdata1 = nii1.get_data().astype(np.bool)
        border1 = self._find_border(origdata1)

        origdata2 = nii2.get_data().astype(np.bool)

        set1_coordinates = self._get_coordinates(border1, nii1.affine)
        set2_coordinates = self._get_coordinates(origdata2, nii2.affine)

        dist_matrix = cdist(set1_coordinates.T, set2_coordinates.T)
        min_dist_matrix = np.amin(dist_matrix, axis=0)
        import matplotlib
        matplotlib.use(config.get('execution', 'matplotlib_backend'))
        import matplotlib.pyplot as plt
        plt.figure()
        plt.hist(min_dist_matrix, 50, normed=1, facecolor='green')
        plt.savefig(self._hist_filename)
        plt.clf()
        plt.close()

        if weighted:
            return np.average(
                min_dist_matrix, weights=nii2.get_data()[origdata2].flat)
        else:
            return np.mean(min_dist_matrix)

    def _eucl_max(self, nii1, nii2):
        origdata1 = nii1.get_data()
        origdata1 = np.logical_not(
            np.logical_or(origdata1 == 0, np.isnan(origdata1)))
        origdata2 = nii2.get_data()
        origdata2 = np.logical_not(
            np.logical_or(origdata2 == 0, np.isnan(origdata2)))

        if isdefined(self.inputs.mask_volume):
            maskdata = nb.load(self.inputs.mask_volume).get_data()
            maskdata = np.logical_not(
                np.logical_or(maskdata == 0, np.isnan(maskdata)))
            origdata1 = np.logical_and(maskdata, origdata1)
            origdata2 = np.logical_and(maskdata, origdata2)

        if origdata1.max() == 0 or origdata2.max() == 0:
            return np.NaN

        border1 = self._find_border(origdata1)
        border2 = self._find_border(origdata2)

        set1_coordinates = self._get_coordinates(border1, nii1.affine)
        set2_coordinates = self._get_coordinates(border2, nii2.affine)
        distances = cdist(set1_coordinates.T, set2_coordinates.T)
        mins = np.concatenate((np.amin(distances, axis=0),
                               np.amin(distances, axis=1)))

        return np.max(mins)

    def _run_interface(self, runtime):
        # there is a bug in some scipy ndimage methods that gets tripped by memory mapped objects
        nii1 = nb.load(self.inputs.volume1, mmap=False)
        nii2 = nb.load(self.inputs.volume2, mmap=False)

        if self.inputs.method == "eucl_min":
            self._distance, self._point1, self._point2 = self._eucl_min(
                nii1, nii2)

        elif self.inputs.method == "eucl_cog":
            self._distance = self._eucl_cog(nii1, nii2)

        elif self.inputs.method == "eucl_mean":
            self._distance = self._eucl_mean(nii1, nii2)

        elif self.inputs.method == "eucl_wmean":
            self._distance = self._eucl_mean(nii1, nii2, weighted=True)
        elif self.inputs.method == "eucl_max":
            self._distance = self._eucl_max(nii1, nii2)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['distance'] = self._distance
        if self.inputs.method == "eucl_min":
            outputs['point1'] = self._point1
            outputs['point2'] = self._point2
        elif self.inputs.method in ["eucl_mean", "eucl_wmean"]:
            outputs['histogram'] = os.path.abspath(self._hist_filename)
        return outputs


class OverlapInputSpec(BaseInterfaceInputSpec):
    volume1 = File(
        exists=True,
        mandatory=True,
        desc='Has to have the same dimensions as volume2.')
    volume2 = File(
        exists=True,
        mandatory=True,
        desc='Has to have the same dimensions as volume1.')
    mask_volume = File(
        exists=True, desc='calculate overlap only within this mask.')
    bg_overlap = traits.Bool(
        False,
        usedefault=True,
        mandatory=True,
        desc='consider zeros as a label')
    out_file = File('diff.nii', usedefault=True)
    weighting = traits.Enum(
        'none',
        'volume',
        'squared_vol',
        usedefault=True,
        desc=('\'none\': no class-overlap weighting is '
              'performed. \'volume\': computed class-'
              'overlaps are weighted by class volume '
              '\'squared_vol\': computed class-overlaps '
              'are weighted by the squared volume of '
              'the class'))
    vol_units = traits.Enum(
        'voxel',
        'mm',
        mandatory=True,
        usedefault=True,
        desc='units for volumes')


class OverlapOutputSpec(TraitedSpec):
    jaccard = traits.Float(desc='averaged jaccard index')
    dice = traits.Float(desc='averaged dice index')
    roi_ji = traits.List(
        traits.Float(), desc=('the Jaccard index (JI) per ROI'))
    roi_di = traits.List(traits.Float(), desc=('the Dice index (DI) per ROI'))
    volume_difference = traits.Float(desc=('averaged volume difference'))
    roi_voldiff = traits.List(
        traits.Float(), desc=('volume differences of ROIs'))
    labels = traits.List(traits.Int(), desc=('detected labels'))
    diff_file = File(exists=True, desc='error map of differences')


class Overlap(BaseInterface):
    """
    Calculates Dice and Jaccard's overlap measures between two ROI maps.
    The interface is backwards compatible with the former version in
    which only binary files were accepted.

    The averaged values of overlap indices can be weighted. Volumes
    now can be reported in :math:`mm^3`, although they are given in voxels
    to keep backwards compatibility.

    Example
    -------

    >>> overlap = Overlap()
    >>> overlap.inputs.volume1 = 'cont1.nii'
    >>> overlap.inputs.volume2 = 'cont2.nii'
    >>> res = overlap.run() # doctest: +SKIP

    """
    input_spec = OverlapInputSpec
    output_spec = OverlapOutputSpec

    def _bool_vec_dissimilarity(self, booldata1, booldata2, method):
        methods = {'dice': dice, 'jaccard': jaccard}
        if not (np.any(booldata1) or np.any(booldata2)):
            return 0
        return 1 - methods[method](booldata1.flat, booldata2.flat)

    def _run_interface(self, runtime):
        nii1 = nb.load(self.inputs.volume1)
        nii2 = nb.load(self.inputs.volume2)

        scale = 1.0

        if self.inputs.vol_units == 'mm':
            voxvol = nii1.header.get_zooms()
            for i in range(nii1.get_data().ndim - 1):
                scale = scale * voxvol[i]

        data1 = nii1.get_data()
        data1[np.logical_or(data1 < 0, np.isnan(data1))] = 0
        max1 = int(data1.max())
        data1 = data1.astype(np.min_scalar_type(max1))
        data2 = nii2.get_data().astype(np.min_scalar_type(max1))
        data2[np.logical_or(data1 < 0, np.isnan(data1))] = 0

        if isdefined(self.inputs.mask_volume):
            maskdata = nb.load(self.inputs.mask_volume).get_data()
            maskdata = ~np.logical_or(maskdata == 0, np.isnan(maskdata))
            data1[~maskdata] = 0
            data2[~maskdata] = 0

        res = []
        volumes1 = []
        volumes2 = []

        labels = np.unique(data1[data1 > 0].reshape(-1)).tolist()
        if self.inputs.bg_overlap:
            labels.insert(0, 0)

        for l in labels:
            res.append(
                self._bool_vec_dissimilarity(
                    data1 == l, data2 == l, method='jaccard'))
            volumes1.append(scale * len(data1[data1 == l]))
            volumes2.append(scale * len(data2[data2 == l]))

        results = dict(jaccard=[], dice=[])
        results['jaccard'] = np.array(res)
        results['dice'] = 2.0 * results['jaccard'] / (results['jaccard'] + 1.0)

        weights = np.ones((len(volumes1), ), dtype=np.float32)
        if self.inputs.weighting != 'none':
            weights = weights / np.array(volumes1)
            if self.inputs.weighting == 'squared_vol':
                weights = weights**2
        weights = weights / np.sum(weights)

        both_data = np.zeros(data1.shape)
        both_data[(data1 - data2) != 0] = 1

        nb.save(
            nb.Nifti1Image(both_data, nii1.affine, nii1.header),
            self.inputs.out_file)

        self._labels = labels
        self._ove_rois = results
        self._vol_rois = (
            np.array(volumes1) - np.array(volumes2)) / np.array(volumes1)

        self._dice = round(np.sum(weights * results['dice']), 5)
        self._jaccard = round(np.sum(weights * results['jaccard']), 5)
        self._volume = np.sum(weights * self._vol_rois)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['labels'] = self._labels
        outputs['jaccard'] = self._jaccard
        outputs['dice'] = self._dice
        outputs['volume_difference'] = self._volume

        outputs['roi_ji'] = self._ove_rois['jaccard'].tolist()
        outputs['roi_di'] = self._ove_rois['dice'].tolist()
        outputs['roi_voldiff'] = self._vol_rois.tolist()
        outputs['diff_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class FuzzyOverlapInputSpec(BaseInterfaceInputSpec):
    in_ref = InputMultiPath(
        File(exists=True),
        mandatory=True,
        desc='Reference image. Requires the same dimensions as in_tst.')
    in_tst = InputMultiPath(
        File(exists=True),
        mandatory=True,
        desc='Test image. Requires the same dimensions as in_ref.')
    weighting = traits.Enum(
        'none',
        'volume',
        'squared_vol',
        usedefault=True,
        desc=('\'none\': no class-overlap weighting is '
              'performed. \'volume\': computed class-'
              'overlaps are weighted by class volume '
              '\'squared_vol\': computed class-overlaps '
              'are weighted by the squared volume of '
              'the class'))
    out_file = File(
        'diff.nii',
        desc='alternative name for resulting difference-map',
        usedefault=True)


class FuzzyOverlapOutputSpec(TraitedSpec):
    jaccard = traits.Float(desc='Fuzzy Jaccard Index (fJI), all the classes')
    dice = traits.Float(desc='Fuzzy Dice Index (fDI), all the classes')
    diff_file = File(
        exists=True,
        desc=
        'resulting difference-map of all classes, using the chosen weighting')
    class_fji = traits.List(
        traits.Float(),
        desc='Array containing the fJIs of each computed class')
    class_fdi = traits.List(
        traits.Float(),
        desc='Array containing the fDIs of each computed class')


class FuzzyOverlap(BaseInterface):
    """Calculates various overlap measures between two maps, using the fuzzy
    definition proposed in: Crum et al., Generalized Overlap Measures for
    Evaluation and Validation in Medical Image Analysis, IEEE Trans. Med.
    Ima. 25(11),pp 1451-1461, Nov. 2006.

    in_ref and in_tst are lists of 2/3D images, each element on the list
    containing one volume fraction map of a class in a fuzzy partition
    of the domain.

    Example
    -------

    >>> overlap = FuzzyOverlap()
    >>> overlap.inputs.in_ref = [ 'ref_class0.nii', 'ref_class1.nii' ]
    >>> overlap.inputs.in_tst = [ 'tst_class0.nii', 'tst_class1.nii' ]
    >>> overlap.inputs.weighting = 'volume'
    >>> res = overlap.run() # doctest: +SKIP
    """

    input_spec = FuzzyOverlapInputSpec
    output_spec = FuzzyOverlapOutputSpec

    def _run_interface(self, runtime):
        ncomp = len(self.inputs.in_ref)
        assert (ncomp == len(self.inputs.in_tst))
        weights = np.ones(shape=ncomp)

        img_ref = np.array([
            nb.load(fname, mmap=NUMPY_MMAP).get_data()
            for fname in self.inputs.in_ref
        ])
        img_tst = np.array([
            nb.load(fname, mmap=NUMPY_MMAP).get_data()
            for fname in self.inputs.in_tst
        ])

        msk = np.sum(img_ref, axis=0)
        msk[msk > 0] = 1.0
        tst_msk = np.sum(img_tst, axis=0)
        tst_msk[tst_msk > 0] = 1.0

        # check that volumes are normalized
        # img_ref[:][msk>0] = img_ref[:][msk>0] / (np.sum( img_ref, axis=0 ))[msk>0]
        # img_tst[tst_msk>0] = img_tst[tst_msk>0] / np.sum( img_tst, axis=0 )[tst_msk>0]

        self._jaccards = []
        volumes = []

        diff_im = np.zeros(img_ref.shape)

        for ref_comp, tst_comp, diff_comp in zip(img_ref, img_tst, diff_im):
            num = np.minimum(ref_comp, tst_comp)
            ddr = np.maximum(ref_comp, tst_comp)
            diff_comp[ddr > 0] += 1.0 - (num[ddr > 0] / ddr[ddr > 0])
            self._jaccards.append(np.sum(num) / np.sum(ddr))
            volumes.append(np.sum(ref_comp))

        self._dices = 2.0 * (np.array(self._jaccards) /
                             (np.array(self._jaccards) + 1.0))

        if self.inputs.weighting != "none":
            weights = 1.0 / np.array(volumes)
            if self.inputs.weighting == "squared_vol":
                weights = weights**2

        weights = weights / np.sum(weights)

        setattr(self, '_jaccard', np.sum(weights * self._jaccards))
        setattr(self, '_dice', np.sum(weights * self._dices))

        diff = np.zeros(diff_im[0].shape)

        for w, ch in zip(weights, diff_im):
            ch[msk == 0] = 0
            diff += w * ch

        nb.save(
            nb.Nifti1Image(diff,
                           nb.load(self.inputs.in_ref[0]).affine,
                           nb.load(self.inputs.in_ref[0]).header),
            self.inputs.out_file)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        for method in ("dice", "jaccard"):
            outputs[method] = getattr(self, '_' + method)
        # outputs['volume_difference'] = self._volume
        outputs['diff_file'] = os.path.abspath(self.inputs.out_file)
        outputs['class_fji'] = np.array(self._jaccards).astype(float).tolist()
        outputs['class_fdi'] = self._dices.astype(float).tolist()
        return outputs


class ErrorMapInputSpec(BaseInterfaceInputSpec):
    in_ref = File(
        exists=True,
        mandatory=True,
        desc="Reference image. Requires the same dimensions as in_tst.")
    in_tst = File(
        exists=True,
        mandatory=True,
        desc="Test image. Requires the same dimensions as in_ref.")
    mask = File(exists=True, desc="calculate overlap only within this mask.")
    metric = traits.Enum(
        "sqeuclidean",
        "euclidean",
        desc='error map metric (as implemented in scipy cdist)',
        usedefault=True,
        mandatory=True)
    out_map = File(desc="Name for the output file")


class ErrorMapOutputSpec(TraitedSpec):
    out_map = File(exists=True, desc="resulting error map")
    distance = traits.Float(desc="Average distance between volume 1 and 2")


class ErrorMap(BaseInterface):
    """ Calculates the error (distance) map between two input volumes.

    Example
    -------

    >>> errormap = ErrorMap()
    >>> errormap.inputs.in_ref = 'cont1.nii'
    >>> errormap.inputs.in_tst = 'cont2.nii'
    >>> res = errormap.run() # doctest: +SKIP
    """
    input_spec = ErrorMapInputSpec
    output_spec = ErrorMapOutputSpec
    _out_file = ''

    def _run_interface(self, runtime):
        # Get two numpy data matrices
        nii_ref = nb.load(self.inputs.in_ref)
        ref_data = np.squeeze(nii_ref.get_data())
        tst_data = np.squeeze(nb.load(self.inputs.in_tst).get_data())
        assert (ref_data.ndim == tst_data.ndim)

        # Load mask
        comps = 1
        mapshape = ref_data.shape

        if (ref_data.ndim == 4):
            comps = ref_data.shape[-1]
            mapshape = ref_data.shape[:-1]

        if isdefined(self.inputs.mask):
            msk = nb.load(self.inputs.mask).get_data()
            if (mapshape != msk.shape):
                raise RuntimeError("Mask should match volume shape, \
                                   mask is %s and volumes are %s" %
                                   (list(msk.shape), list(mapshape)))
        else:
            msk = np.ones(shape=mapshape)

        # Flatten both volumes and make the pixel differennce
        mskvector = msk.reshape(-1)
        msk_idxs = np.where(mskvector == 1)
        refvector = ref_data.reshape(-1, comps)[msk_idxs].astype(np.float32)
        tstvector = tst_data.reshape(-1, comps)[msk_idxs].astype(np.float32)
        diffvector = (refvector - tstvector)

        # Scale the difference
        if self.inputs.metric == 'sqeuclidean':
            errvector = diffvector**2
            if (comps > 1):
                errvector = np.sum(errvector, axis=1)
            else:
                errvector = np.squeeze(errvector)
        elif self.inputs.metric == 'euclidean':
            errvector = np.linalg.norm(diffvector, axis=1)

        errvectorexp = np.zeros_like(
            mskvector, dtype=np.float32)  # The default type is uint8
        errvectorexp[msk_idxs] = errvector

        # Get averaged error
        self._distance = np.average(
            errvector)  # Only average the masked voxels

        errmap = errvectorexp.reshape(mapshape)

        hdr = nii_ref.header.copy()
        hdr.set_data_dtype(np.float32)
        hdr['data_type'] = 16
        hdr.set_data_shape(mapshape)

        if not isdefined(self.inputs.out_map):
            fname, ext = op.splitext(op.basename(self.inputs.in_tst))
            if ext == '.gz':
                fname, ext2 = op.splitext(fname)
                ext = ext2 + ext
            self._out_file = op.abspath(fname + "_errmap" + ext)
        else:
            self._out_file = self.inputs.out_map

        nb.Nifti1Image(errmap.astype(np.float32), nii_ref.affine,
                       hdr).to_filename(self._out_file)

        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_map'] = self._out_file
        outputs['distance'] = self._distance
        return outputs


class SimilarityInputSpec(BaseInterfaceInputSpec):
    volume1 = File(exists=True, desc="3D/4D volume", mandatory=True)
    volume2 = File(exists=True, desc="3D/4D volume", mandatory=True)
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
    similarity = traits.List(
        traits.Float(desc="Similarity between volume 1 and 2, frame by frame"))


class Similarity(BaseInterface):
    """Calculates similarity between two 3D or 4D volumes. Both volumes have to be in
    the same coordinate system, same space within that coordinate system and
    with the same voxel dimensions.

    .. note:: This interface is an extension of
              :py:class:`nipype.interfaces.nipy.utils.Similarity` to support 4D files.
              Requires :py:mod:`nipy`

    Example
    -------
    >>> from nipype.algorithms.metrics import Similarity
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
    _have_nipy = True

    def __init__(self, **inputs):
        try:
            package_check('nipy')
        except Exception:
            self._have_nipy = False
        super(Similarity, self).__init__(**inputs)

    def _run_interface(self, runtime):
        if not self._have_nipy:
            raise RuntimeError('nipy is not installed')

        from nipy.algorithms.registration.histogram_registration import HistogramRegistration
        from nipy.algorithms.registration.affine import Affine

        vol1_nii = nb.load(self.inputs.volume1)
        vol2_nii = nb.load(self.inputs.volume2)

        dims = vol1_nii.get_data().ndim

        if dims == 3 or dims == 2:
            vols1 = [vol1_nii]
            vols2 = [vol2_nii]
        if dims == 4:
            vols1 = nb.four_to_three(vol1_nii)
            vols2 = nb.four_to_three(vol2_nii)

        if dims < 2 or dims > 4:
            raise RuntimeError(
                'Image dimensions not supported (detected %dD file)' % dims)

        if isdefined(self.inputs.mask1):
            mask1 = nb.load(self.inputs.mask1).get_data() == 1
        else:
            mask1 = None

        if isdefined(self.inputs.mask2):
            mask2 = nb.load(self.inputs.mask2).get_data() == 1
        else:
            mask2 = None

        self._similarity = []

        for ts1, ts2 in zip(vols1, vols2):
            histreg = HistogramRegistration(
                from_img=ts1,
                to_img=ts2,
                similarity=self.inputs.metric,
                from_mask=mask1,
                to_mask=mask2)
            self._similarity.append(histreg.eval(Affine()))

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['similarity'] = self._similarity
        return outputs
