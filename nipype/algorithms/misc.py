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

import os, os.path as op

import nibabel as nb
import numpy as np
from math import floor, ceil
from scipy.ndimage.morphology import grey_dilation
from scipy.ndimage.morphology import binary_erosion
from scipy.spatial.distance import cdist, euclidean, dice, jaccard
from scipy.ndimage.measurements import center_of_mass, label
from scipy.special import legendre
import scipy.io as sio
import itertools

from nipype.utils.config import config
import matplotlib
matplotlib.use(config.get("execution", "matplotlib_backend"))
import matplotlib.pyplot as plt

from nipype.interfaces.base import (BaseInterface, traits, TraitedSpec, File,
                                    InputMultiPath, OutputMultiPath,
                                    BaseInterfaceInputSpec, isdefined)
from nipype.utils.filemanip import fname_presuffix, split_filename
import logging

logging.basicConfig()
iflogger = logging.getLogger('interface')


class PickAtlasInputSpec(BaseInterfaceInputSpec):
    atlas = File(exists=True, desc="Location of the atlas that will be used.", mandatory=True)
    labels = traits.Either(traits.Int, traits.List(traits.Int),
                           desc="Labels of regions that will be included in the mask. Must be \
compatible with the atlas used.", compulsory=True)
    hemi = traits.Enum('both', 'left', 'right', desc="Restrict the mask to only one hemisphere: left or right", usedefault=True)
    dilation_size = traits.Int(desc="Defines how much the mask will be dilated (expanded in 3D).", usedefault=True)
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
            output = fname_presuffix(fname=self.inputs.atlas, suffix="_mask",
                                     newpath=os.getcwd(), use_ext=True)
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
    transformation_matrix = traits.Array(value=np.eye(4), shape=(4, 4), desc="transformation matrix that will be left multiplied by the affine matrix", usedefault=True)


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
            affine = np.dot(self.inputs.transformation_matrix, affine)

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
    method = traits.Enum("eucl_min", "eucl_cog", "eucl_mean", "eucl_wmean", "eucl_max", desc='""eucl_min": Euclidean distance between two closest points\
    "eucl_cog": mean Euclidian distance between the Center of Gravity of volume1 and CoGs of volume2\
    "eucl_mean": mean Euclidian minimum distance of all volume2 voxels to volume1\
    "eucl_wmean": mean Euclidian minimum distance of all volume2 voxels to volume1 weighted by their values\
    "eucl_max": maximum over minimum Euclidian distances of all volume2 voxels to volume1 (also known as the Hausdorff distance)',
    usedefault=True)
    mask_volume = File(exists=True, desc="calculate overlap only within this mask.")


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

        set1_coordinates = self._get_coordinates(border1, nii1.get_affine())

        set2_coordinates = self._get_coordinates(border2, nii2.get_affine())

        dist_matrix = cdist(set1_coordinates.T, set2_coordinates.T)
        (point1, point2) = np.unravel_index(np.argmin(dist_matrix), dist_matrix.shape)
        return (euclidean(set1_coordinates.T[point1, :], set2_coordinates.T[point2, :]), set1_coordinates.T[point1, :], set2_coordinates.T[point2, :])

    def _eucl_cog(self, nii1, nii2):
        origdata1 = nii1.get_data().astype(np.bool)
        cog_t = np.array(center_of_mass(origdata1)).reshape(-1, 1)
        cog_t = np.vstack((cog_t, np.array([1])))
        cog_t_coor = np.dot(nii1.get_affine(), cog_t)[:3, :]

        origdata2 = nii2.get_data().astype(np.bool)
        (labeled_data, n_labels) = label(origdata2)

        cogs = np.ones((4, n_labels))

        for i in range(n_labels):
            cogs[:3, i] = np.array(center_of_mass(origdata2, labeled_data, i + 1))

        cogs_coor = np.dot(nii2.get_affine(), cogs)[:3, :]

        dist_matrix = cdist(cog_t_coor.T, cogs_coor.T)

        return np.mean(dist_matrix)

    def _eucl_mean(self, nii1, nii2, weighted=False):
        origdata1 = nii1.get_data().astype(np.bool)
        border1 = self._find_border(origdata1)

        origdata2 = nii2.get_data().astype(np.bool)

        set1_coordinates = self._get_coordinates(border1, nii1.get_affine())
        set2_coordinates = self._get_coordinates(origdata2, nii2.get_affine())

        dist_matrix = cdist(set1_coordinates.T, set2_coordinates.T)
        min_dist_matrix = np.amin(dist_matrix, axis=0)
        plt.figure()
        plt.hist(min_dist_matrix, 50, normed=1, facecolor='green')
        plt.savefig(self._hist_filename)
        plt.clf()
        plt.close()

        if weighted:
            return np.average(min_dist_matrix, weights=nii2.get_data()[origdata2].flat)
        else:
            return np.mean(min_dist_matrix)

    def _eucl_max(self, nii1, nii2):
        origdata1 = nii1.get_data()
        origdata1 = np.logical_not(np.logical_or(origdata1 == 0, np.isnan(origdata1)))
        origdata2 = nii2.get_data()
        origdata2 = np.logical_not(np.logical_or(origdata2 == 0, np.isnan(origdata2)))

        if isdefined(self.inputs.mask_volume):
            maskdata = nb.load(self.inputs.mask_volume).get_data()
            maskdata = np.logical_not(np.logical_or(maskdata == 0, np.isnan(maskdata)))
            origdata1 = np.logical_and(maskdata, origdata1)
            origdata2 = np.logical_and(maskdata, origdata2)

        if origdata1.max() == 0 or origdata2.max() == 0:
            return np.NaN

        border1 = self._find_border(origdata1)
        border2 = self._find_border(origdata2)

        set1_coordinates = self._get_coordinates(border1, nii1.get_affine())
        set2_coordinates = self._get_coordinates(border2, nii2.get_affine())
        distances = cdist(set1_coordinates.T, set2_coordinates.T)
        mins = np.concatenate((np.amin(distances, axis=0), np.amin(distances, axis=1)))

        return np.max(mins)

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
    volume1 = File(exists=True, mandatory=True, desc="Has to have the same dimensions as volume2.")
    volume2 = File(exists=True, mandatory=True, desc="Has to have the same dimensions as volume1.")
    mask_volume = File(exists=True, desc="calculate overlap only within this mask.")
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

        if isdefined(self.inputs.mask_volume):
            maskdata = nb.load(self.inputs.mask_volume).get_data()
            maskdata = np.logical_not(np.logical_or(maskdata == 0, np.isnan(maskdata)))
            origdata1 = np.logical_and(maskdata, origdata1)
            origdata2 = np.logical_and(maskdata, origdata2)

        for method in ("dice", "jaccard"):
            setattr(self, '_' + method, self._bool_vec_dissimilarity(origdata1, origdata2, method=method))

        self._volume = int(origdata1.sum() - origdata2.sum())

        both_data = np.zeros(origdata1.shape)
        both_data[origdata1] = 1
        both_data[origdata2] += 2

        nb.save(nb.Nifti1Image(both_data, nii1.get_affine(), nii1.get_header()), self.inputs.out_file)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        for method in ("dice", "jaccard"):
            outputs[method] = getattr(self, '_' + method)
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
        nb.save(img, self._gen_output_file_name())

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

class GunzipInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True)

class GunzipOutputSpec(TraitedSpec):
    out_file = File(exists=True)

class Gunzip(BaseInterface):
    """

    """
    input_spec = GunzipInputSpec
    output_spec = GunzipOutputSpec

    def _gen_output_file_name(self):
        _, base, ext = split_filename(self.inputs.in_file)
        if ext[-2:].lower() == ".gz":
            ext = ext[:-3]
        return os.path.abspath(base + ext[:-3])

    def _run_interface(self, runtime):
        import gzip
        in_file = gzip.open(self.inputs.in_file, 'rb')
        out_file = open(self._gen_output_file_name(), 'wb')
        out_file.write(in_file.read())
        out_file.close()
        in_file.close()
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self._gen_output_file_name()
        return outputs

def replaceext(in_list, ext):
    out_list = list()
    for filename in in_list:
        path, name, _ = split_filename(op.abspath(filename))
        out_name = op.join(path,name) + ext
        out_list.append(out_name)
    return out_list

def matlab2csv(in_array, name, reshape):
    output_array = np.asarray(in_array)
    if reshape == True:
		if len(np.shape(output_array)) > 1:
			output_array = np.reshape(output_array,(np.shape(output_array)[0]*np.shape(output_array)[1],1))
			iflogger.info(np.shape(output_array))
    output_name = op.abspath(name + '.csv')
    np.savetxt(output_name, output_array, delimiter=',')
    return output_name

class Matlab2CSVInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True, desc='Input MATLAB .mat file')
    reshape_matrix = traits.Bool(True, usedefault=True, desc='The output of this interface is meant for R, so matrices will be reshaped to vectors by default.')

class Matlab2CSVOutputSpec(TraitedSpec):
    csv_files = OutputMultiPath(File(desc='Output CSV files for each variable saved in the input .mat file'))

class Matlab2CSV(BaseInterface):
    """
    Simple interface to save the components of a MATLAB .mat file as a text file with comma-separated values (CSVs).

    CSV files are easily loaded in R, for use in statistical processing.
    For further information, see cran.r-project.org/doc/manuals/R-data.pdf

    Example
    -------

    >>> import nipype.algorithms.misc as misc
    >>> mat2csv = misc.Matlab2CSV()
    >>> mat2csv.inputs.in_file = 'cmatrix.mat'
    >>> mat2csv.run() # doctest: +SKIP
    """
    input_spec = Matlab2CSVInputSpec
    output_spec = Matlab2CSVOutputSpec

    def _run_interface(self, runtime):
        in_dict = sio.loadmat(op.abspath(self.inputs.in_file))

        # Check if the file has multiple variables in it. If it does, loop through them and save them as individual CSV files.
        # If not, save the variable as a single CSV file using the input file name and a .csv extension.

        saved_variables = list()
        for key in in_dict.keys():
            if not key.startswith('__'):
				if isinstance(in_dict[key][0],np.ndarray):
					saved_variables.append(key)
				else:
					iflogger.info('One of the keys in the input file, {k}, is not a Numpy array'.format(k=key))

        if len(saved_variables) > 1:
            iflogger.info('{N} variables found:'.format(N=len(saved_variables)))
            iflogger.info(saved_variables)
            for variable in saved_variables:
                iflogger.info('...Converting {var} - type {ty} - to CSV'.format(var=variable, ty=type(in_dict[variable])))
                matlab2csv(in_dict[variable], variable, self.inputs.reshape_matrix)
        elif len(saved_variables) == 1:
            _, name, _ = split_filename(self.inputs.in_file)
            variable = saved_variables[0]
            iflogger.info('Single variable found {var}, type {ty}:'.format(var=variable, ty=type(in_dict[variable])))
            iflogger.info('...Converting {var} to CSV from {f}'.format(var=variable, f=self.inputs.in_file))
            matlab2csv(in_dict[variable], name, self.inputs.reshape_matrix)
        else:
            iflogger.error('No values in the MATLAB file?!')
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        in_dict = sio.loadmat(op.abspath(self.inputs.in_file))
        saved_variables = list()
        for key in in_dict.keys():
            if not key.startswith('__'):
				if isinstance(in_dict[key][0],np.ndarray):
					saved_variables.append(key)
				else:
					iflogger.error('One of the keys in the input file, {k}, is not a Numpy array'.format(k=key))

        if len(saved_variables) > 1:
            outputs['csv_files'] = replaceext(saved_variables, '.csv')
        elif len(saved_variables) == 1:
            _, name, ext = split_filename(self.inputs.in_file)
            outputs['csv_files'] = op.abspath(name + '.csv')
        else:
            iflogger.error('No values in the MATLAB file?!')
        return outputs

def merge_csvs(in_list):
	for idx, in_file in enumerate(in_list):
		try:
			in_array = np.loadtxt(in_file, delimiter=',')
		except ValueError, ex:
			try:
				in_array = np.loadtxt(in_file, delimiter=',', skiprows=1)
			except ValueError, ex:
				first = open(in_file, 'r')
				header_line = first.readline()
				header_list = header_line.split(',')
				n_cols = len(header_list)
				try:
					in_array = np.loadtxt(in_file, delimiter=',', skiprows=1, usecols=range(1,n_cols))
				except ValueError, ex:
					in_array = np.loadtxt(in_file, delimiter=',', skiprows=1, usecols=range(1,n_cols-1))
		if idx == 0:
			out_array = in_array
		else:
			out_array = np.dstack((out_array, in_array))
	out_array = np.squeeze(out_array)
	iflogger.info('Final output array shape:')
	iflogger.info(np.shape(out_array))
	return out_array

def remove_identical_paths(in_files):
    import os.path as op
    if len(in_files) > 1:
        out_names = list()
        commonprefix = op.commonprefix(in_files)
        lastslash = commonprefix.rfind('/')
        commonpath = commonprefix[0:(lastslash+1)]
        for fileidx, in_file in enumerate(in_files):
            path, name, ext = split_filename(in_file)
            in_file = op.join(path, name)
            name = in_file.replace(commonpath, '')
            name = name.replace('_subject_id_', '')
            out_names.append(name)
    else:
        path, name, ext = split_filename(in_files[0])
        out_names = [name]
    return out_names

def maketypelist(rowheadings, shape, extraheadingBool, extraheading):
    typelist = []
    if rowheadings:
        typelist.append(('heading','a40'))
    if len(shape) > 1:
        for idx in range(1,(min(shape)+1)):
            typelist.append((str(idx), float))
    else:
        typelist.append((str(1), float))
    if extraheadingBool:
        typelist.append((extraheading, 'a40'))
    iflogger.info(typelist)
    return typelist

def makefmtlist(output_array, typelist, rowheadingsBool, shape, extraheadingBool):
    output = np.zeros(max(shape), typelist)
    fmtlist = []
    if rowheadingsBool:
        fmtlist.append('%s')
    if len(shape) > 1:
        for idx in range(1,min(shape)+1):
            output[str(idx)] = output_array[:,idx-1]
            fmtlist.append('%f')
    else:
        output[str(1)] = output_array
        fmtlist.append('%f')
    if extraheadingBool:
        fmtlist.append('%s')
    fmt = ','.join(fmtlist)
    return fmt, output

class MergeCSVFilesInputSpec(TraitedSpec):
    in_files = InputMultiPath(File(exists=True), mandatory=True, desc='Input comma-separated value (CSV) files')
    out_file = File('merged.csv', usedefault=True, desc='Output filename for merged CSV file')
    column_headings = traits.List(traits.Str, desc='List of column headings to save in merged CSV file (must be equal to number of input files). If left undefined, these will be pulled from the input filenames.')
    row_headings = traits.List(traits.Str, desc='List of row headings to save in merged CSV file (must be equal to number of rows in the input files).')
    extra_column_heading = traits.Str(desc='New heading to add for the added field.')
    extra_field = traits.Str(desc='New field to add to each row. This is useful for saving the group or subject ID in the file.')

class MergeCSVFilesOutputSpec(TraitedSpec):
    csv_file = File(desc='Output CSV file containing columns ')

class MergeCSVFiles(BaseInterface):
    """
    This interface is designed to facilitate data loading in the R environment.
    It takes input CSV files and merges them into a single CSV file.
    If provided, it will also incorporate column heading names into the resulting CSV file.

    CSV files are easily loaded in R, for use in statistical processing.
    For further information, see cran.r-project.org/doc/manuals/R-data.pdf

    Example
    -------

    >>> import nipype.algorithms.misc as misc
    >>> mat2csv = misc.MergeCSVFiles()
    >>> mat2csv.inputs.in_files = ['degree.mat','clustering.mat']
    >>> mat2csv.inputs.column_headings = ['degree','clustering']
    >>> mat2csv.run() # doctest: +SKIP
    """
    input_spec = MergeCSVFilesInputSpec
    output_spec = MergeCSVFilesOutputSpec

    def _run_interface(self, runtime):
        extraheadingBool = False
        rowheadingsBool = False
        """
        This block defines the column headings.
        """
        if isdefined(self.inputs.column_headings):
            iflogger.info('Column headings have been provided:')
            headings = self.inputs.column_headings
        else:
            iflogger.info('Column headings not provided! Pulled from input filenames:')
            headings = remove_identical_paths(self.inputs.in_files)

        if isdefined(self.inputs.extra_field):
            if isdefined(self.inputs.extra_column_heading):
                extraheading = self.inputs.extra_column_heading
                iflogger.info('Extra column heading provided: {col}'.format(col=extraheading))
            else:
                extraheading = 'type'
                iflogger.info('Extra column heading was not defined. Using "type"')
            headings.append(extraheading)
            extraheadingBool = True

        if len(self.inputs.in_files) == 1:
            iflogger.warn('Only one file input!')

        if isdefined(self.inputs.row_headings):
            iflogger.info('Row headings have been provided. Adding "labels" column header.')
            csv_headings = '"labels","' + '","'.join(itertools.chain(headings)) + '"\n'
            rowheadingsBool = True
        else:
            iflogger.info('Row headings have not been provided.')
            csv_headings = '"' + '","'.join(itertools.chain(headings)) + '"\n'

        iflogger.info('Final Headings:')
        iflogger.info(csv_headings)

        """
        Next we merge the arrays and define the output text file
        """

        output_array = merge_csvs(self.inputs.in_files)
        _, name, ext = split_filename(self.inputs.out_file)
        if not ext == '.csv':
            ext = '.csv'

        out_file = op.abspath(name + ext)
        file_handle = open(out_file,'w')
        file_handle.write(csv_headings)

        shape = np.shape(output_array)
        typelist = maketypelist(rowheadingsBool, shape, extraheadingBool, extraheading)
        fmt, output = makefmtlist(output_array, typelist, rowheadingsBool, shape, extraheadingBool)

        if rowheadingsBool:
            row_heading_list = self.inputs.row_headings
            row_heading_list_with_quotes = []
            for row_heading in row_heading_list:
                row_heading_with_quotes = '"' + row_heading + '"'
                row_heading_list_with_quotes.append(row_heading_with_quotes)
            row_headings = np.array(row_heading_list_with_quotes)
            output['heading'] = row_headings

        if isdefined(self.inputs.extra_field):
            extrafieldlist = []
            for idx in range(0,max(shape)):
                extrafieldlist.append(self.inputs.extra_field)
            iflogger.info(len(extrafieldlist))
            output[extraheading] = extrafieldlist
        iflogger.info(output)
        iflogger.info(fmt)
        np.savetxt(file_handle, output, fmt, delimiter=',')
        file_handle.close()
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        _, name, ext = split_filename(self.inputs.out_file)
        if not ext == '.csv':
            ext = '.csv'
        out_file = op.abspath(name + ext)
        outputs['csv_file'] = out_file
        return outputs

class AddCSVColumnInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True, desc='Input comma-separated value (CSV) files')
    out_file = File('extra_heading.csv', usedefault=True, desc='Output filename for merged CSV file')
    extra_column_heading = traits.Str(desc='New heading to add for the added field.')
    extra_field = traits.Str(desc='New field to add to each row. This is useful for saving the group or subject ID in the file.')

class AddCSVColumnOutputSpec(TraitedSpec):
    csv_file = File(desc='Output CSV file containing columns ')

class AddCSVColumn(BaseInterface):
    """
    Short interface to add an extra column and field to a text file

    Example
    -------

    >>> import nipype.algorithms.misc as misc
    >>> addcol = misc.AddCSVColumn()
    >>> addcol.inputs.in_file = 'degree.csv'
    >>> addcol.inputs.extra_column_heading = 'group'
    >>> addcol.inputs.extra_field = 'male'
    >>> addcol.run() # doctest: +SKIP
    """
    input_spec = AddCSVColumnInputSpec
    output_spec = AddCSVColumnOutputSpec

    def _run_interface(self, runtime):
		in_file = open(self.inputs.in_file, 'r')
		_, name, ext = split_filename(self.inputs.out_file)
		if not ext == '.csv':
			ext = '.csv'
		out_file = op.abspath(name + ext)

		out_file = open(out_file, 'w')
		firstline = in_file.readline()
		firstline = firstline.replace('\n','')
		new_firstline = firstline + ',"' + self.inputs.extra_column_heading + '"\n'
		out_file.write(new_firstline)
		for line in in_file:
			new_line = line.replace('\n','')
			new_line = new_line + ',' + self.inputs.extra_field + '\n'
			out_file.write(new_line)
		return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        _, name, ext = split_filename(self.inputs.out_file)
        if not ext == '.csv':
            ext = '.csv'
        out_file = op.abspath(name + ext)
        outputs['csv_file'] = out_file
        return outputs
