# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Miscellaneous algorithms

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
    >>> os.chdir(datadir)

'''
import os

import nibabel as nb
import numpy as np
from math import floor, ceil
from scipy.ndimage.morphology import grey_dilation
from scipy.ndimage.morphology import binary_erosion
from scipy.spatial.distance import cdist, euclidean, dice, jaccard
from scipy.ndimage.measurements import center_of_mass, label
from scipy.special import legendre

from nipype.utils.config import config
import matplotlib
matplotlib.use(config.get("execution", "matplotlib_backend"))
import matplotlib.pyplot as plt

from nipype.interfaces.base import (BaseInterface, traits, TraitedSpec, File,
                                    InputMultiPath, OutputMultiPath,
                                    BaseInterfaceInputSpec, isdefined)
from nipype.utils.filemanip import fname_presuffix, split_filename


class PickAtlasInputSpec(BaseInterfaceInputSpec):
    atlas = File(exists=True, desc="Location of the atlas that will be used.", mandatory=True)
    labels = traits.Either(traits.Int, traits.List(traits.Int),
                           desc="Labels of regions that will be included in the mask. Must be \
compatible with the atlas used.", compulsory=True)
    hemi = traits.Enum('both','left','right', desc="Restrict the mask to only one hemisphere: left or right", usedefault=True)
    dilation_size = traits.Int(desc="Defines how much the mask will be dilated (expanded in 3D).", usedefault = True)
    output_file = File(desc="Where to store the output mask.")

class PickAtlasOutputSpec(TraitedSpec):
    mask_file = File(exists=True, desc="output mask file")

class PickAtlas(BaseInterface):
    '''
    Returns ROI masks given an atlas and a list of labels. Supports dilation
    and left right masking (assuming the atlas is properly aligned).
    '''
    input_spec = PickAtlasInputSpec
    output_spec = PickAtlasOutputSpec

    def _run_interface(self, runtime):
        nim = self._get_brodmann_area()
        nb.save(nim, self._gen_output_filename())

        return runtime

    def _gen_output_filename(self):
        if not isdefined(self.inputs.output_file):
            output = fname_presuffix(fname=self.inputs.atlas, suffix = "_mask",
                                     newpath= os.getcwd(), use_ext = True)
        else:
            output = os.path.realpath(self.inputs.output_file)
        return output

    def _get_brodmann_area(self):
        nii = nb.load(self.inputs.atlas)
        origdata = nii.get_data()
        newdata = np.zeros(origdata.shape)

        if not isinstance(self.inputs.labels, list):
            labels = [self.inputs.labels]
        else:
            labels = self.inputs.labels
        for lab in labels:
            newdata[origdata == lab] = 1
        if self.inputs.hemi == 'right':
            newdata[floor(float(origdata.shape[0]) / 2):, :, :] = 0
        elif self.inputs.hemi == 'left':
            newdata[:ceil(float(origdata.shape[0]) / 2), :, : ] = 0

        if self.inputs.dilation_size != 0:
            newdata = grey_dilation(newdata , (2 * self.inputs.dilation_size + 1,
                                               2 * self.inputs.dilation_size + 1,
                                               2 * self.inputs.dilation_size + 1))

        return nb.Nifti1Image(newdata, nii.get_affine(), nii.get_header())

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['mask_file'] = self._gen_output_filename()
        return outputs

class SimpleThresholdInputSpec(BaseInterfaceInputSpec):
    volumes = InputMultiPath(File(exists=True), desc='volumes to be thresholded', mandatory=True)
    threshold = traits.Float(desc='volumes to be thresholdedeverything below this value will be set to zero', mandatory=True)


class SimpleThresholdOutputSpec(TraitedSpec):
    thresholded_volumes = OutputMultiPath(File(exists=True), desc="thresholded volumes")


class SimpleThreshold(BaseInterface):
    input_spec = SimpleThresholdInputSpec
    output_spec = SimpleThresholdOutputSpec

    def _run_interface(self, runtime):
        for fname in self.inputs.volumes:
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
        outputs["thresholded_volumes"] = []
        for fname in self.inputs.volumes:
            _, base, _ = split_filename(fname)
            outputs["thresholded_volumes"].append(os.path.abspath(base + '_thresholded.nii'))
        return outputs

class ModifyAffineInputSpec(BaseInterfaceInputSpec):
    volumes = InputMultiPath(File(exists=True), desc='volumes which affine matrices will be modified', mandatory=True)
    transformation_matrix = traits.Array(value=np.eye(4), shape=(4,4), desc="transformation matrix that will be left multiplied by the affine matrix", usedefault=True)

class ModifyAffineOutputSpec(TraitedSpec):
    transformed_volumes = OutputMultiPath(File(exist=True))

class ModifyAffine(BaseInterface):
    '''
    Left multiplies the affine matrix with a specified values. Saves the volume as a nifti file.
    '''
    input_spec = ModifyAffineInputSpec
    output_spec = ModifyAffineOutputSpec

    def _gen_output_filename(self, name):
        _, base, _ = split_filename(name)
        return os.path.abspath(base + "_transformed.nii")

    def _run_interface(self, runtime):
        for fname in self.inputs.volumes:
            img = nb.load(fname)

            affine = img.get_affine()
            affine = np.dot(self.inputs.transformation_matrix,affine)

            nb.save(nb.Nifti1Image(img.get_data(), affine, img.get_header()), self._gen_output_filename(fname))

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['transformed_volumes'] = []
        for fname in self.inputs.volumes:
            outputs['transformed_volumes'].append(self._gen_output_filename(fname))
        return outputs

class DistanceInputSpec(BaseInterfaceInputSpec):
    volume1 = File(exists=True, mandatory=True, desc="Has to have the same dimensions as volume2.")
    volume2 = File(exists=True, mandatory=True, desc="Has to have the same dimensions as volume1.")
    method = traits.Enum("eucl_min", "eucl_cog", "eucl_mean", "eucl_wmean", desc='""eucl_min": Euclidean distance between two closest points\
    "eucl_cog": mean Euclidian distance between the Center of Gravity of volume1 and CoGs of volume2\
    "eucl_mean": mean Euclidian minimum distance of all volume2 voxels to volume1\
    "eucl_wmean": mean Euclidian minimum distance of all volume2 voxels to volume1 weighted by their values', usedefault = True)

class DistanceOutputSpec(TraitedSpec):
    distance = traits.Float()
    point1 = traits.Array(shape=(3,))
    point2 = traits.Array(shape=(3,))
    histogram = File()

class Distance(BaseInterface):
    '''
    Calculates distance between two volumes.
    '''
    input_spec = DistanceInputSpec
    output_spec = DistanceOutputSpec

    _hist_filename = "hist.pdf"

    def _find_border(self,data):
        eroded = binary_erosion(data)
        border = np.logical_and(data, np.logical_not(eroded))
        return border

    def _get_coordinates(self, data, affine):
        if len(data.shape) == 4:
            data = data[:,:,:,0]
        indices = np.vstack(np.nonzero(data))
        indices = np.vstack((indices, np.ones(indices.shape[1])))
        coordinates = np.dot(affine,indices)
        return coordinates[:3,:]

    def _eucl_min(self, nii1, nii2):
        origdata1 = nii1.get_data().astype(np.bool)
        border1 = self._find_border(origdata1)

        origdata2 = nii2.get_data().astype(np.bool)
        border2 = self._find_border(origdata2)

        set1_coordinates = self._get_coordinates(border1, nii1.get_affine())

        set2_coordinates = self._get_coordinates(border2, nii2.get_affine())

        dist_matrix = cdist(set1_coordinates.T, set2_coordinates.T)
        (point1, point2) = np.unravel_index(np.argmin(dist_matrix), dist_matrix.shape)
        return (euclidean(set1_coordinates.T[point1,:], set2_coordinates.T[point2,:]), set1_coordinates.T[point1,:], set2_coordinates.T[point2,:])

    def _eucl_cog(self, nii1, nii2):
        origdata1 = nii1.get_data().astype(np.bool)
        cog_t = np.array(center_of_mass(origdata1)).reshape(-1,1)
        cog_t = np.vstack((cog_t, np.array([1])))
        cog_t_coor = np.dot(nii1.get_affine(),cog_t)[:3,:]

        origdata2 = nii2.get_data().astype(np.bool)
        (labeled_data, n_labels) = label(origdata2)

        cogs = np.ones((4,n_labels))

        for i in range(n_labels):
            cogs[:3,i] = np.array(center_of_mass(origdata2, labeled_data, i+1))

        cogs_coor = np.dot(nii2.get_affine(),cogs)[:3,:]

        dist_matrix = cdist(cog_t_coor.T, cogs_coor.T)

        return np.mean(dist_matrix)

    def _eucl_mean(self, nii1, nii2, weighted=False):
        origdata1 = nii1.get_data().astype(np.bool)
        border1 = self._find_border(origdata1)

        origdata2 = nii2.get_data().astype(np.bool)

        set1_coordinates = self._get_coordinates(border1, nii1.get_affine())
        set2_coordinates = self._get_coordinates(origdata2, nii2.get_affine())

        dist_matrix = cdist(set1_coordinates.T, set2_coordinates.T)
        min_dist_matrix = np.amin(dist_matrix, axis = 0)
        plt.figure()
        plt.hist(min_dist_matrix, 50, normed=1, facecolor='green')
        plt.savefig(self._hist_filename)
        plt.clf()
        plt.close()

        if weighted:
            return np.average(min_dist_matrix, weights=nii2.get_data()[origdata2].flat)
        else:
            return np.mean(min_dist_matrix)



    def _run_interface(self, runtime):
        nii1 = nb.load(self.inputs.volume1)
        nii2 = nb.load(self.inputs.volume2)

        if self.inputs.method == "eucl_min":
            self._distance, self._point1, self._point2 = self._eucl_min(nii1, nii2)

        elif self.inputs.method == "eucl_cog":
            self._distance = self._eucl_cog(nii1, nii2)

        elif self.inputs.method == "eucl_mean":
            self._distance = self._eucl_mean(nii1, nii2)

        elif self.inputs.method == "eucl_wmean":
            self._distance = self._eucl_mean(nii1, nii2, weighted=True)

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
    volume1 = File(exists=True, mandatory=True, desc="Has to have the same dimensions as volume2.")
    volume2 = File(exists=True, mandatory=True, desc="Has to have the same dimensions as volume1.")
    out_file = File("diff.nii", usedefault=True)

class OverlapOutputSpec(TraitedSpec):
    jaccard = traits.Float()
    dice = traits.Float()
    volume_difference = traits.Int()
    diff_file = File(exists=True)

class Overlap(BaseInterface):
    """
    Calculates various overlap measures between two maps.

    Example
    -------

    >>> overlap = Overlap()
    >>> overlap.inputs.volume1 = 'cont1.nii'
    >>> overlap.inputs.volume1 = 'cont2.nii'
    >>> res = overlap.run() # doctest: +SKIP
    """

    input_spec = OverlapInputSpec
    output_spec = OverlapOutputSpec

    def _bool_vec_dissimilarity(self, booldata1, booldata2, method):
        methods = {"dice": dice, "jaccard": jaccard}
        if not (np.any(booldata1) or np.any(booldata2)):
            return 0
        return 1 - methods[method](booldata1.flat, booldata2.flat)

    def _run_interface(self, runtime):
        nii1 = nb.load(self.inputs.volume1)
        nii2 = nb.load(self.inputs.volume2)

        origdata1 = np.logical_not(np.logical_or(nii1.get_data() == 0, np.isnan(nii1.get_data())))
        origdata2 = np.logical_not(np.logical_or(nii2.get_data() == 0, np.isnan(nii2.get_data())))
        for method in ("dice", "jaccard"):

            setattr(self, '_' + method, self._bool_vec_dissimilarity(origdata1, origdata2, method = method))

        self._volume = int(origdata1.sum() - origdata2.sum())

        both_data = np.zeros(origdata1.shape)
        both_data[origdata1] = 1
        both_data[origdata2] += 2

        nb.save(nb.Nifti1Image(both_data, nii1.get_affine(), nii1.get_header()), self.inputs.out_file)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        for method in ("dice", "jaccard"):
            outputs[method] = getattr(self, '_'+method)
        outputs['volume_difference'] = self._volume
        outputs['diff_file'] = os.path.abspath(self.inputs.out_file)
        return outputs

class CreateNiftiInputSpec(BaseInterfaceInputSpec):
    data_file = File(exists=True, mandatory=True, desc="ANALYZE img file")
    header_file = File(exists=True, mandatory=True, desc="corresponding ANALYZE hdr file")
    affine = traits.Array(exists=True, desc="affine transformation array")

class CreateNiftiOutputSpec(TraitedSpec):
    nifti_file = File(exists=True)

class CreateNifti(BaseInterface):
    input_spec = CreateNiftiInputSpec
    output_spec = CreateNiftiOutputSpec

    def _gen_output_file_name(self):
        _, base, _ = split_filename(self.inputs.data_file)
        return os.path.abspath(base + ".nii")

    def _run_interface(self, runtime):
        hdr = nb.AnalyzeHeader.from_fileobj(open(self.inputs.header_file, 'rb'))

        if isdefined(self.inputs.affine):
            affine = self.inputs.affine
        else:
            affine = None

        data = hdr.data_from_fileobj(open(self.inputs.data_file, 'rb'))
        img = nb.Nifti1Image(data, affine, hdr)
        nb.save(img,  self._gen_output_file_name())

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['nifti_file'] = self._gen_output_file_name()
        return outputs


class TSNRInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True,
                   desc='realigned 4D file')
    regress_poly = traits.Int(min=1, desc='Remove polynomials')

class TSNROutputSpec(TraitedSpec):
    tsnr_file = File(exists=True, desc='tsnr image file')
    mean_file = File(exists=True, desc='mean image file')
    stddev_file = File(exists=True, desc='std dev image file')
    detrended_file = File(desc='detrended input file')

class TSNR(BaseInterface):
    """Computes the time-course SNR for a time series

    Typically you want to run this on a realigned time-series.

    Example
    -------

    >>> tsnr = TSNR()
    >>> tsnr.inputs.in_file = 'functional.nii'
    >>> res = tsnr.run() # doctest: +SKIP

    """
    input_spec = TSNRInputSpec
    output_spec = TSNROutputSpec

    def _gen_output_file_name(self, out_ext=None):
        _, base, _ = split_filename(self.inputs.in_file)
        if out_ext in ['mean', 'stddev']:
            return os.path.abspath(base + "_tsnr_" + out_ext + ".nii.gz")
        elif out_ext in ['detrended']:
            return os.path.abspath(base + "_" + out_ext + ".nii.gz")
        else:
            return os.path.abspath(base + "_tsnr.nii.gz")

    def _run_interface(self, runtime):
        img = nb.load(self.inputs.in_file)
        data = img.get_data()
        if isdefined(self.inputs.regress_poly):
            timepoints = img.get_shape()[-1]
            X = np.ones((timepoints,1))
            for i in range(self.inputs.regress_poly):
                X = np.hstack((X,legendre(i+1)(np.linspace(-1, 1, timepoints))[:, None]))
            betas = np.dot(np.linalg.pinv(X), np.rollaxis(data, 3, 2))
            datahat = np.rollaxis(np.dot(X[:,1:],
                                         np.rollaxis(betas[1:, :, :, :], 0, 3)),
                                  0, 4)
            data = data - datahat
            img = nb.Nifti1Image(data, img.get_affine(), img.get_header())
            nb.save(img,  self._gen_output_file_name('detrended'))
        meanimg = np.mean(data, axis=3)
        stddevimg = np.std(data, axis=3)
        tsnr = meanimg/stddevimg
        img = nb.Nifti1Image(tsnr, img.get_affine(), img.get_header())
        nb.save(img,  self._gen_output_file_name())
        img = nb.Nifti1Image(meanimg, img.get_affine(), img.get_header())
        nb.save(img,  self._gen_output_file_name('mean'))
        img = nb.Nifti1Image(stddevimg, img.get_affine(), img.get_header())
        nb.save(img,  self._gen_output_file_name('stddev'))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['tsnr_file'] = self._gen_output_file_name()
        outputs['mean_file'] = self._gen_output_file_name('mean')
        outputs['stddev_file'] = self._gen_output_file_name('stddev')
        if isdefined(self.inputs.regress_poly):
            outputs['detrended_file'] = self._gen_output_file_name('detrended')
        return outputs
