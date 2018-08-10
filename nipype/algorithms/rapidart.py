# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The rapidart module provides routines for artifact detection and region of
interest analysis.

These functions include:

  * ArtifactDetect: performs artifact detection on functional images

  * StimulusCorrelation: determines correlation between stimuli
    schedule and movement/intensity parameters
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import open, range, str, bytes

import os
from copy import deepcopy

from nibabel import load, funcs, Nifti1Image
import numpy as np
from scipy import signal
import scipy.io as sio

from ..utils import NUMPY_MMAP
from ..interfaces.base import (BaseInterface, traits, InputMultiPath,
                               OutputMultiPath, TraitedSpec, File,
                               BaseInterfaceInputSpec, isdefined)
from ..utils.filemanip import ensure_list, save_json, split_filename
from ..utils.misc import find_indices, normalize_mc_params
from .. import logging, config
iflogger = logging.getLogger('nipype.interface')


def _get_affine_matrix(params, source):
    """Return affine matrix given a set of translation and rotation parameters

    params : np.array (upto 12 long) in native package format
    source : the package that generated the parameters
             supports SPM, AFNI, FSFAST, FSL, NIPY
    """
    if source == 'NIPY':
        # nipy does not store typical euler angles, use nipy to convert
        from nipy.algorithms.registration import to_matrix44
        return to_matrix44(params)

    params = normalize_mc_params(params, source)
    # process for FSL, SPM, AFNI and FSFAST
    rotfunc = lambda x: np.array([[np.cos(x), np.sin(x)],
                                  [-np.sin(x), np.cos(x)]])
    q = np.array([0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0])
    if len(params) < 12:
        params = np.hstack((params, q[len(params):]))
    params.shape = (len(params), )
    # Translation
    T = np.eye(4)
    T[0:3, -1] = params[0:3]
    # Rotation
    Rx = np.eye(4)
    Rx[1:3, 1:3] = rotfunc(params[3])
    Ry = np.eye(4)
    Ry[(0, 0, 2, 2), (0, 2, 0, 2)] = rotfunc(params[4]).ravel()
    Rz = np.eye(4)
    Rz[0:2, 0:2] = rotfunc(params[5])
    # Scaling
    S = np.eye(4)
    S[0:3, 0:3] = np.diag(params[6:9])
    # Shear
    Sh = np.eye(4)
    Sh[(0, 0, 1), (1, 2, 2)] = params[9:12]
    if source in ('AFNI', 'FSFAST'):
        return np.dot(T, np.dot(Ry, np.dot(Rx, np.dot(Rz, np.dot(S, Sh)))))
    return np.dot(T, np.dot(Rx, np.dot(Ry, np.dot(Rz, np.dot(S, Sh)))))


def _calc_norm(mc, use_differences, source, brain_pts=None):
    """Calculates the maximum overall displacement of the midpoints
    of the faces of a cube due to translation and rotation.

    Parameters
    ----------
    mc : motion parameter estimates
        [3 translation, 3 rotation (radians)]
    use_differences : boolean
    brain_pts : [4 x n_points] of coordinates

    Returns
    -------

    norm : at each time point
    displacement : euclidean distance (mm) of displacement at each coordinate

    """

    affines = [
        _get_affine_matrix(mc[i, :], source) for i in range(mc.shape[0])
    ]
    return _calc_norm_affine(affines, use_differences, brain_pts)


def _calc_norm_affine(affines, use_differences, brain_pts=None):
    """Calculates the maximum overall displacement of the midpoints
    of the faces of a cube due to translation and rotation.

    Parameters
    ----------
    affines : list of [4 x 4] affine matrices
    use_differences : boolean
    brain_pts : [4 x n_points] of coordinates

    Returns
    -------

    norm : at each time point
    displacement : euclidean distance (mm) of displacement at each coordinate

    """

    if brain_pts is None:
        respos = np.diag([70, 70, 75])
        resneg = np.diag([-70, -110, -45])
        all_pts = np.vstack((np.hstack((respos, resneg)), np.ones((1, 6))))
        displacement = None
    else:
        all_pts = brain_pts
    n_pts = all_pts.size - all_pts.shape[1]
    newpos = np.zeros((len(affines), n_pts))
    if brain_pts is not None:
        displacement = np.zeros((len(affines), int(n_pts / 3)))
    for i, affine in enumerate(affines):
        newpos[i, :] = np.dot(affine, all_pts)[0:3, :].ravel()
        if brain_pts is not None:
            displacement[i, :] = np.sqrt(
                np.sum(
                    np.power(
                        np.reshape(newpos[i, :],
                                   (3, all_pts.shape[1])) - all_pts[0:3, :],
                        2),
                    axis=0))
    # np.savez('displacement.npz', newpos=newpos, pts=all_pts)
    normdata = np.zeros(len(affines))
    if use_differences:
        newpos = np.concatenate(
            (np.zeros((1, n_pts)), np.diff(newpos, n=1, axis=0)), axis=0)
        for i in range(newpos.shape[0]):
            normdata[i] = \
                np.max(np.sqrt(np.sum(
                    np.reshape(np.power(np.abs(newpos[i, :]), 2),
                               (3, all_pts.shape[1])),
                    axis=0)))
    else:
        newpos = np.abs(signal.detrend(newpos, axis=0, type='constant'))
        normdata = np.sqrt(np.mean(np.power(newpos, 2), axis=1))
    return normdata, displacement


class ArtifactDetectInputSpec(BaseInterfaceInputSpec):
    realigned_files = InputMultiPath(
        File(exists=True),
        desc=("Names of realigned functional data "
              "files"),
        mandatory=True)
    realignment_parameters = InputMultiPath(
        File(exists=True),
        mandatory=True,
        desc=("Names of realignment "
              "parameters corresponding to "
              "the functional data files"))
    parameter_source = traits.Enum(
        "SPM",
        "FSL",
        "AFNI",
        "NiPy",
        "FSFAST",
        desc="Source of movement parameters",
        mandatory=True)
    use_differences = traits.ListBool(
        [True, False],
        minlen=2,
        maxlen=2,
        usedefault=True,
        desc=("Use differences between successive"
              " motion (first element) and "
              "intensity parameter (second "
              "element) estimates in order to "
              "determine outliers.  "
              "(default is [True, False])"))
    use_norm = traits.Bool(
        True,
        usedefault=True,
        requires=['norm_threshold'],
        desc=("Uses a composite of the motion parameters in "
              "order to determine outliers."))
    norm_threshold = traits.Float(
        xor=['rotation_threshold', 'translation_threshold'],
        mandatory=True,
        desc=("Threshold to use to detect motion-rela"
              "ted outliers when composite motion is "
              "being used"))
    rotation_threshold = traits.Float(
        mandatory=True,
        xor=['norm_threshold'],
        desc=("Threshold (in radians) to use to "
              "detect rotation-related outliers"))
    translation_threshold = traits.Float(
        mandatory=True,
        xor=['norm_threshold'],
        desc=("Threshold (in mm) to use to "
              "detect translation-related "
              "outliers"))
    zintensity_threshold = traits.Float(
        mandatory=True,
        desc=("Intensity Z-threshold use to "
              "detection images that deviate "
              "from the mean"))
    mask_type = traits.Enum(
        'spm_global',
        'file',
        'thresh',
        mandatory=True,
        desc=("Type of mask that should be used to mask the"
              " functional data. *spm_global* uses an "
              "spm_global like calculation to determine the"
              " brain mask. *file* specifies a brain mask "
              "file (should be an image file consisting of "
              "0s and 1s). *thresh* specifies a threshold "
              "to use. By default all voxels are used,"
              "unless one of these mask types are defined"))
    mask_file = File(
        exists=True, desc="Mask file to be used if mask_type is 'file'.")
    mask_threshold = traits.Float(
        desc=("Mask threshold to be used if mask_type"
              " is 'thresh'."))
    intersect_mask = traits.Bool(
        True, usedefault=True,
        desc=("Intersect the masks when computed from "
              "spm_global."))
    save_plot = traits.Bool(
        True, desc="save plots containing outliers", usedefault=True)
    plot_type = traits.Enum(
        'png',
        'svg',
        'eps',
        'pdf',
        desc="file type of the outlier plot",
        usedefault=True)
    bound_by_brainmask = traits.Bool(
        False,
        desc=("use the brain mask to "
              "determine bounding box"
              "for composite norm (works"
              "for SPM and Nipy - currently"
              "inaccurate for FSL, AFNI"),
        usedefault=True)
    global_threshold = traits.Float(
        8.0,
        desc=("use this threshold when mask "
              "type equal's spm_global"),
        usedefault=True)


class ArtifactDetectOutputSpec(TraitedSpec):
    outlier_files = OutputMultiPath(
        File(exists=True),
        desc=("One file for each functional run "
              "containing a list of 0-based indices"
              " corresponding to outlier volumes"))
    intensity_files = OutputMultiPath(
        File(exists=True),
        desc=("One file for each functional run "
              "containing the global intensity "
              "values determined from the "
              "brainmask"))
    norm_files = OutputMultiPath(
        File,
        desc=("One file for each functional run "
              "containing the composite norm"))
    statistic_files = OutputMultiPath(
        File(exists=True),
        desc=("One file for each functional run "
              "containing information about the "
              "different types of artifacts and "
              "if design info is provided then "
              "details of stimulus correlated "
              "motion and a listing or artifacts "
              "by event type."))
    plot_files = OutputMultiPath(
        File,
        desc=("One image file for each functional run "
              "containing the detected outliers"))
    mask_files = OutputMultiPath(
        File,
        desc=("One image file for each functional run "
              "containing the mask used for global "
              "signal calculation"))
    displacement_files = OutputMultiPath(
        File,
        desc=("One image file for each "
              "functional run containing the "
              "voxel displacement timeseries"))


class ArtifactDetect(BaseInterface):
    """Detects outliers in a functional imaging series

    Uses intensity and motion parameters to infer outliers. If `use_norm` is
    True, it computes the movement of the center of each face a cuboid centered
    around the head and returns the maximal movement across the centers. If you
    wish to use individual thresholds instead, import `Undefined` from
    `nipype.interfaces.base` and set `....inputs.use_norm = Undefined`


    Examples
    --------

    >>> ad = ArtifactDetect()
    >>> ad.inputs.realigned_files = 'functional.nii'
    >>> ad.inputs.realignment_parameters = 'functional.par'
    >>> ad.inputs.parameter_source = 'FSL'
    >>> ad.inputs.norm_threshold = 1
    >>> ad.inputs.use_differences = [True, False]
    >>> ad.inputs.zintensity_threshold = 3
    >>> ad.run()  # doctest: +SKIP
    """

    input_spec = ArtifactDetectInputSpec
    output_spec = ArtifactDetectOutputSpec

    def __init__(self, **inputs):
        super(ArtifactDetect, self).__init__(**inputs)

    def _get_output_filenames(self, motionfile, output_dir):
        """Generate output files based on motion filenames

        Parameters
        ----------

        motionfile: file/string
            Filename for motion parameter file
        output_dir: string
            output directory in which the files will be generated
        """
        if isinstance(motionfile, (str, bytes)):
            infile = motionfile
        elif isinstance(motionfile, list):
            infile = motionfile[0]
        else:
            raise Exception("Unknown type of file")
        _, filename, ext = split_filename(infile)
        artifactfile = os.path.join(output_dir, ''.join(('art.', filename,
                                                         '_outliers.txt')))
        intensityfile = os.path.join(output_dir, ''.join(('global_intensity.',
                                                          filename, '.txt')))
        statsfile = os.path.join(output_dir, ''.join(('stats.', filename,
                                                      '.txt')))
        normfile = os.path.join(output_dir, ''.join(('norm.', filename,
                                                     '.txt')))
        plotfile = os.path.join(output_dir, ''.join(('plot.', filename, '.',
                                                     self.inputs.plot_type)))
        displacementfile = os.path.join(output_dir, ''.join(('disp.', filename,
                                                             ext)))
        maskfile = os.path.join(output_dir, ''.join(('mask.', filename, ext)))
        return (artifactfile, intensityfile, statsfile, normfile, plotfile,
                displacementfile, maskfile)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['outlier_files'] = []
        outputs['intensity_files'] = []
        outputs['statistic_files'] = []
        outputs['mask_files'] = []
        if isdefined(self.inputs.use_norm) and self.inputs.use_norm:
            outputs['norm_files'] = []
            if self.inputs.bound_by_brainmask:
                outputs['displacement_files'] = []
        if isdefined(self.inputs.save_plot) and self.inputs.save_plot:
            outputs['plot_files'] = []
        for i, f in enumerate(ensure_list(self.inputs.realigned_files)):
            (outlierfile, intensityfile, statsfile, normfile, plotfile,
             displacementfile, maskfile) = \
                self._get_output_filenames(f, os.getcwd())
            outputs['outlier_files'].insert(i, outlierfile)
            outputs['intensity_files'].insert(i, intensityfile)
            outputs['statistic_files'].insert(i, statsfile)
            outputs['mask_files'].insert(i, maskfile)
            if isdefined(self.inputs.use_norm) and self.inputs.use_norm:
                outputs['norm_files'].insert(i, normfile)
                if self.inputs.bound_by_brainmask:
                    outputs['displacement_files'].insert(i, displacementfile)
            if isdefined(self.inputs.save_plot) and self.inputs.save_plot:
                outputs['plot_files'].insert(i, plotfile)
        return outputs

    def _plot_outliers_with_wave(self, wave, outliers, name):
        import matplotlib
        matplotlib.use(config.get("execution", "matplotlib_backend"))
        import matplotlib.pyplot as plt
        plt.plot(wave)
        plt.ylim([wave.min(), wave.max()])
        plt.xlim([0, len(wave) - 1])
        if len(outliers):
            plt.plot(
                np.tile(outliers[:, None], (1, 2)).T,
                np.tile([wave.min(), wave.max()], (len(outliers), 1)).T, 'r')
        plt.xlabel('Scans - 0-based')
        plt.ylabel(name)

    def _detect_outliers_core(self, imgfile, motionfile, runidx, cwd=None):
        """
        Core routine for detecting outliers
        """
        if not cwd:
            cwd = os.getcwd()

        # read in functional image
        if isinstance(imgfile, (str, bytes)):
            nim = load(imgfile, mmap=NUMPY_MMAP)
        elif isinstance(imgfile, list):
            if len(imgfile) == 1:
                nim = load(imgfile[0], mmap=NUMPY_MMAP)
            else:
                images = [load(f, mmap=NUMPY_MMAP) for f in imgfile]
                nim = funcs.concat_images(images)

        # compute global intensity signal
        (x, y, z, timepoints) = nim.shape

        data = nim.get_data()
        affine = nim.affine
        g = np.zeros((timepoints, 1))
        masktype = self.inputs.mask_type
        if masktype == 'spm_global':  # spm_global like calculation
            iflogger.debug('art: using spm global')
            intersect_mask = self.inputs.intersect_mask
            if intersect_mask:
                mask = np.ones((x, y, z), dtype=bool)
                for t0 in range(timepoints):
                    vol = data[:, :, :, t0]
                    # Use an SPM like approach
                    mask_tmp = vol > \
                        (np.nanmean(vol) / self.inputs.global_threshold)
                    mask = mask * mask_tmp
                for t0 in range(timepoints):
                    vol = data[:, :, :, t0]
                    g[t0] = np.nanmean(vol[mask])
                if len(find_indices(mask)) < (np.prod((x, y, z)) / 10):
                    intersect_mask = False
                    g = np.zeros((timepoints, 1))
            if not intersect_mask:
                iflogger.info('not intersect_mask is True')
                mask = np.zeros((x, y, z, timepoints))
                for t0 in range(timepoints):
                    vol = data[:, :, :, t0]
                    mask_tmp = vol > \
                        (np.nanmean(vol) / self.inputs.global_threshold)
                    mask[:, :, :, t0] = mask_tmp
                    g[t0] = np.nansum(vol * mask_tmp) / np.nansum(mask_tmp)
        elif masktype == 'file':  # uses a mask image to determine intensity
            maskimg = load(self.inputs.mask_file, mmap=NUMPY_MMAP)
            mask = maskimg.get_data()
            affine = maskimg.affine
            mask = mask > 0.5
            for t0 in range(timepoints):
                vol = data[:, :, :, t0]
                g[t0] = np.nanmean(vol[mask])
        elif masktype == 'thresh':  # uses a fixed signal threshold
            for t0 in range(timepoints):
                vol = data[:, :, :, t0]
                mask = vol > self.inputs.mask_threshold
                g[t0] = np.nanmean(vol[mask])
        else:
            mask = np.ones((x, y, z))
            g = np.nanmean(data[mask > 0, :], 1)

        # compute normalized intensity values
        gz = signal.detrend(g, axis=0)  # detrend the signal
        if self.inputs.use_differences[1]:
            gz = np.concatenate(
                (np.zeros((1, 1)), np.diff(gz, n=1, axis=0)), axis=0)
        gz = (gz - np.mean(gz)) / np.std(gz)  # normalize the detrended signal
        iidx = find_indices(abs(gz) > self.inputs.zintensity_threshold)

        # read in motion parameters
        mc_in = np.loadtxt(motionfile)
        mc = deepcopy(mc_in)

        (artifactfile, intensityfile, statsfile, normfile, plotfile,
         displacementfile, maskfile) = self._get_output_filenames(
             imgfile, cwd)
        mask_img = Nifti1Image(mask.astype(np.uint8), affine)
        mask_img.to_filename(maskfile)

        if self.inputs.use_norm:
            brain_pts = None
            if self.inputs.bound_by_brainmask:
                voxel_coords = np.nonzero(mask)
                coords = np.vstack((voxel_coords[0],
                                    np.vstack((voxel_coords[1],
                                               voxel_coords[2])))).T
                brain_pts = np.dot(affine,
                                   np.hstack((coords,
                                              np.ones((coords.shape[0],
                                                       1)))).T)
            # calculate the norm of the motion parameters
            normval, displacement = _calc_norm(
                mc,
                self.inputs.use_differences[0],
                self.inputs.parameter_source,
                brain_pts=brain_pts)
            tidx = find_indices(normval > self.inputs.norm_threshold)
            ridx = find_indices(normval < 0)
            if displacement is not None:
                dmap = np.zeros((x, y, z, timepoints), dtype=np.float)
                for i in range(timepoints):
                    dmap[voxel_coords[0], voxel_coords[1], voxel_coords[2],
                         i] = displacement[i, :]
                dimg = Nifti1Image(dmap, affine)
                dimg.to_filename(displacementfile)
        else:
            if self.inputs.use_differences[0]:
                mc = np.concatenate(
                    (np.zeros((1, 6)), np.diff(mc_in, n=1, axis=0)), axis=0)
            traval = mc[:, 0:3]  # translation parameters (mm)
            rotval = mc[:, 3:6]  # rotation parameters (rad)
            tidx = find_indices(
                np.sum(abs(traval) > self.inputs.translation_threshold, 1) > 0)
            ridx = find_indices(
                np.sum(abs(rotval) > self.inputs.rotation_threshold, 1) > 0)

        outliers = np.unique(np.union1d(iidx, np.union1d(tidx, ridx)))

        # write output to outputfile
        np.savetxt(artifactfile, outliers, fmt=b'%d', delimiter=' ')
        np.savetxt(intensityfile, g, fmt=b'%.2f', delimiter=' ')
        if self.inputs.use_norm:
            np.savetxt(normfile, normval, fmt=b'%.4f', delimiter=' ')

        if isdefined(self.inputs.save_plot) and self.inputs.save_plot:
            import matplotlib
            matplotlib.use(config.get("execution", "matplotlib_backend"))
            import matplotlib.pyplot as plt
            fig = plt.figure()
            if isdefined(self.inputs.use_norm) and self.inputs.use_norm:
                plt.subplot(211)
            else:
                plt.subplot(311)
            self._plot_outliers_with_wave(gz, iidx, 'Intensity')
            if isdefined(self.inputs.use_norm) and self.inputs.use_norm:
                plt.subplot(212)
                self._plot_outliers_with_wave(normval, np.union1d(tidx, ridx),
                                              'Norm (mm)')
            else:
                diff = ''
                if self.inputs.use_differences[0]:
                    diff = 'diff'
                plt.subplot(312)
                self._plot_outliers_with_wave(traval, tidx,
                                              'Translation (mm)' + diff)
                plt.subplot(313)
                self._plot_outliers_with_wave(rotval, ridx,
                                              'Rotation (rad)' + diff)
            plt.savefig(plotfile)
            plt.close(fig)

        motion_outliers = np.union1d(tidx, ridx)
        stats = [
            {
                'motion_file': motionfile,
                'functional_file': imgfile
            },
            {
                'common_outliers': len(np.intersect1d(iidx, motion_outliers)),
                'intensity_outliers': len(np.setdiff1d(iidx, motion_outliers)),
                'motion_outliers': len(np.setdiff1d(motion_outliers, iidx)),
            },
            {
                'motion': [
                    {
                        'using differences': self.inputs.use_differences[0]
                    },
                    {
                        'mean': np.mean(mc_in, axis=0).tolist(),
                        'min': np.min(mc_in, axis=0).tolist(),
                        'max': np.max(mc_in, axis=0).tolist(),
                        'std': np.std(mc_in, axis=0).tolist()
                    },
                ]
            },
            {
                'intensity': [
                    {
                        'using differences': self.inputs.use_differences[1]
                    },
                    {
                        'mean': np.mean(gz, axis=0).tolist(),
                        'min': np.min(gz, axis=0).tolist(),
                        'max': np.max(gz, axis=0).tolist(),
                        'std': np.std(gz, axis=0).tolist()
                    },
                ]
            },
        ]
        if self.inputs.use_norm:
            stats.insert(
                3, {
                    'motion_norm': {
                        'mean': np.mean(normval, axis=0).tolist(),
                        'min': np.min(normval, axis=0).tolist(),
                        'max': np.max(normval, axis=0).tolist(),
                        'std': np.std(normval, axis=0).tolist(),
                    }
                })
        save_json(statsfile, stats)

    def _run_interface(self, runtime):
        """Execute this module.
        """
        funcfilelist = ensure_list(self.inputs.realigned_files)
        motparamlist = ensure_list(self.inputs.realignment_parameters)
        for i, imgf in enumerate(funcfilelist):
            self._detect_outliers_core(
                imgf, motparamlist[i], i, cwd=os.getcwd())
        return runtime


class StimCorrInputSpec(BaseInterfaceInputSpec):
    realignment_parameters = InputMultiPath(
        File(exists=True),
        mandatory=True,
        desc=("Names of realignment "
              "parameters corresponding to "
              "the functional data files"))
    intensity_values = InputMultiPath(
        File(exists=True),
        mandatory=True,
        desc=("Name of file containing intensity "
              "values"))
    spm_mat_file = File(
        exists=True,
        mandatory=True,
        desc="SPM mat file (use pre-estimate SPM.mat file)")
    concatenated_design = traits.Bool(
        mandatory=True,
        desc=("state if the design matrix "
              "contains concatenated sessions"))


class StimCorrOutputSpec(TraitedSpec):
    stimcorr_files = OutputMultiPath(
        File(exists=True),
        desc=("List of files containing "
              "correlation values"))


class StimulusCorrelation(BaseInterface):
    """Determines if stimuli are correlated with motion or intensity
    parameters.

    Currently this class supports an SPM generated design matrix and requires
    intensity parameters. This implies that one must run
    :ref:`ArtifactDetect <nipype.algorithms.rapidart.ArtifactDetect>`
    and :ref:`Level1Design <nipype.interfaces.spm.model.Level1Design>` prior to
    running this or provide an SPM.mat file and intensity parameters through
    some other means.

    Examples
    --------

    >>> sc = StimulusCorrelation()
    >>> sc.inputs.realignment_parameters = 'functional.par'
    >>> sc.inputs.intensity_values = 'functional.rms'
    >>> sc.inputs.spm_mat_file = 'SPM.mat'
    >>> sc.inputs.concatenated_design = False
    >>> sc.run() # doctest: +SKIP

    """

    input_spec = StimCorrInputSpec
    output_spec = StimCorrOutputSpec

    def _get_output_filenames(self, motionfile, output_dir):
        """Generate output files based on motion filenames

        Parameters
        ----------
        motionfile: file/string
            Filename for motion parameter file
        output_dir: string
            output directory in which the files will be generated
        """
        (_, filename) = os.path.split(motionfile)
        (filename, _) = os.path.splitext(filename)
        corrfile = os.path.join(output_dir, ''.join(('qa.', filename,
                                                     '_stimcorr.txt')))
        return corrfile

    def _stimcorr_core(self, motionfile, intensityfile, designmatrix,
                       cwd=None):
        """
        Core routine for determining stimulus correlation

        """
        if not cwd:
            cwd = os.getcwd()
        # read in motion parameters
        mc_in = np.loadtxt(motionfile)
        g_in = np.loadtxt(intensityfile)
        g_in.shape = g_in.shape[0], 1
        dcol = designmatrix.shape[1]
        mccol = mc_in.shape[1]
        concat_matrix = np.hstack((np.hstack((designmatrix, mc_in)), g_in))
        cm = np.corrcoef(concat_matrix, rowvar=0)
        corrfile = self._get_output_filenames(motionfile, cwd)
        # write output to outputfile
        file = open(corrfile, 'w')
        file.write("Stats for:\n")
        file.write("Stimulus correlated motion:\n%s\n" % motionfile)
        for i in range(dcol):
            file.write("SCM.%d:" % i)
            for v in cm[i, dcol + np.arange(mccol)]:
                file.write(" %.2f" % v)
            file.write('\n')
        file.write("Stimulus correlated intensity:\n%s\n" % intensityfile)
        for i in range(dcol):
            file.write("SCI.%d: %.2f\n" % (i, cm[i, -1]))
        file.close()

    def _get_spm_submatrix(self, spmmat, sessidx, rows=None):
        """
        Parameters
        ----------
        spmmat: scipy matlab object
            full SPM.mat file loaded into a scipy object
        sessidx: int
            index to session that needs to be extracted.
        """
        designmatrix = spmmat['SPM'][0][0].xX[0][0].X
        U = spmmat['SPM'][0][0].Sess[0][sessidx].U[0]
        if rows is None:
            rows = spmmat['SPM'][0][0].Sess[0][sessidx].row[0] - 1
        cols = (spmmat['SPM'][0][0].Sess[0][sessidx].col[0][list(
            range(len(U)))] - 1)
        outmatrix = designmatrix.take(
            rows.tolist(), axis=0).take(
                cols.tolist(), axis=1)
        return outmatrix

    def _run_interface(self, runtime):
        """Execute this module.
        """
        motparamlist = self.inputs.realignment_parameters
        intensityfiles = self.inputs.intensity_values
        spmmat = sio.loadmat(self.inputs.spm_mat_file, struct_as_record=False)
        nrows = []
        for i in range(len(motparamlist)):
            sessidx = i
            rows = None
            if self.inputs.concatenated_design:
                sessidx = 0
                mc_in = np.loadtxt(motparamlist[i])
                rows = np.sum(nrows) + np.arange(mc_in.shape[0])
                nrows.append(mc_in.shape[0])
            matrix = self._get_spm_submatrix(spmmat, sessidx, rows)
            self._stimcorr_core(motparamlist[i], intensityfiles[i], matrix,
                                os.getcwd())
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        files = []
        for i, f in enumerate(self.inputs.realignment_parameters):
            files.insert(i, self._get_output_filenames(f, os.getcwd()))
        if files:
            outputs['stimcorr_files'] = files
        return outputs
