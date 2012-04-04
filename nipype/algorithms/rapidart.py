# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The rapidart module provides routines for artifact detection and region of
interest analysis.

These functions include:

  * ArtifactDetect: performs artifact detection on functional images

  * StimulusCorrelation: determines correlation between stimuli
    schedule and movement/intensity parameters

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
   >>> os.chdir(datadir)
"""

import os
from copy import deepcopy

from nibabel import load, funcs
import numpy as np
from scipy import signal
import scipy.io as sio

from .. import config
import matplotlib
matplotlib.use(config.get("execution", "matplotlib_backend"))
import matplotlib.pyplot as plt

from nipype.interfaces.base import (BaseInterface, traits, InputMultiPath,
                                    OutputMultiPath, TraitedSpec, File,
                                    BaseInterfaceInputSpec, isdefined)
from nipype.utils.filemanip import filename_to_list, save_json
from nipype.utils.misc import find_indices

class ArtifactDetectInputSpec(BaseInterfaceInputSpec):
    realigned_files = InputMultiPath(File(exists=True),
                                     desc="Names of realigned functional data files",
                                     mandatory=True)
    realignment_parameters = InputMultiPath(File(exists=True), mandatory=True,
                                            desc=("Names of realignment parameters"
                                                  "corresponding to the functional data files"))
    parameter_source = traits.Enum("SPM", "FSL", "Siemens", desc="Are the movement parameters from SPM or FSL or from" \
            "Siemens PACE data. Options: SPM, FSL or Siemens", mandatory=True)
    use_differences = traits.ListBool([True, False], minlen=2, maxlen=2, usedefault=True,
            desc="Use differences between successive motion (first element)" \
            "and intensity paramter (second element) estimates in order" \
            "to determine outliers.  (default is [True, False])")
    use_norm = traits.Bool(True, desc="Uses a composite of the motion parameters in order to determine" \
            "outliers.  Requires ``norm_threshold`` to be set.  (default is" \
            "True) ", usedefault=True)
    norm_threshold = traits.Float(desc="Threshold to use to detect motion-related outliers when" \
            "composite motion is being used (see ``use_norm``)", mandatory=True,
                                  xor=['rotation_threshold', 'translation_threshold'])
    rotation_threshold = traits.Float(desc="Threshold (in radians) to use to detect rotation-related outliers",
                                      mandatory=True, xor=['norm_threshold'])
    translation_threshold = traits.Float(desc="Threshold (in mm) to use to detect translation-related outliers",
                                      mandatory=True, xor=['norm_threshold'])
    zintensity_threshold = traits.Float(desc="Intensity Z-threshold use to detection images that deviate from the" \
            "mean", mandatory=True)
    mask_type = traits.Enum('spm_global', 'file', 'thresh', desc="Type of mask that should be used to mask the functional data." \
            "*spm_global* uses an spm_global like calculation to determine the" \
            "brain mask.  *file* specifies a brain mask file (should be an image" \
            "file consisting of 0s and 1s). *thresh* specifies a threshold to" \
            "use.  By default all voxels are used, unless one of these mask" \
            "types are defined.")
    mask_file = File(exists=True, desc="Mask file to be used if mask_type is 'file'.")
    mask_threshold = traits.Float(desc="Mask threshold to be used if mask_type is 'thresh'.")
    intersect_mask = traits.Bool(True, desc="Intersect the masks when computed from spm_global. (default is" \
            "True)")
    save_plot = traits.Bool(True, desc="save plots containing outliers",
                            usedefault=True)
    plot_type = traits.Enum('png', 'svg', 'eps', 'pdf', desc="file type of the outlier plot",
                            usedefault=True)


class ArtifactDetectOutputSpec(TraitedSpec):
    outlier_files = OutputMultiPath(File(exists=True), desc="One file for each functional run containing a list of 0-based" \
            "indices corresponding to outlier volumes")
    intensity_files = OutputMultiPath(File(exists=True), desc="One file for each functional run containing the global intensity" \
            "values determined from the brainmask")
    norm_files = OutputMultiPath(File, desc="One file for each functional run containing the composite norm")
    statistic_files = OutputMultiPath(File(exists=True), desc="One file for each functional run containing information about the" \
            "different types of artifacts and if design info is provided then" \
            "details of stimulus correlated motion and a listing or artifacts by" \
            "event type.")
    plot_files = OutputMultiPath(File, desc="One image file for each functional run containing the detected outliers")
    #mask_file = File(exists=True,
    #                 desc='generated or provided mask file')


class ArtifactDetect(BaseInterface):
    """Detects outliers in a functional imaging series

    Uses intensity and motion parameters to infer outliers. If `use_norm` is
    True, it computes the movement of the center of each face a cuboid centered
    around the head and returns the maximal movement across the centers.


    Examples
    --------

    >>> ad = ArtifactDetect()
    >>> ad.inputs.realigned_files = 'functional.nii'
    >>> ad.inputs.realignment_parameters = 'functional.par'
    >>> ad.inputs.parameter_source = 'FSL'
    >>> ad.inputs.norm_threshold = 1
    >>> ad.inputs.use_differences = [True, False]
    >>> ad.inputs.zintensity_threshold = 3
    >>> ad.run() # doctest: +SKIP
    """

    input_spec = ArtifactDetectInputSpec
    output_spec = ArtifactDetectOutputSpec

    def _get_output_filenames(self, motionfile, output_dir):
        """Generate output files based on motion filenames

        Parameters
        ----------

        motionfile: file/string
            Filename for motion parameter file
        output_dir: string
            output directory in which the files will be generated
        """
        if isinstance(motionfile, str):
            infile = motionfile
        elif isinstance(motionfile, list):
            infile = motionfile[0]
        else:
            raise Exception("Unknown type of file")
        (filepath, filename) = os.path.split(infile)
        (filename, ext) = os.path.splitext(filename)
        artifactfile = os.path.join(output_dir, ''.join(('art.', filename, '_outliers.txt')))
        intensityfile = os.path.join(output_dir, ''.join(('global_intensity.', filename, '.txt')))
        statsfile = os.path.join(output_dir, ''.join(('stats.', filename, '.txt')))
        normfile = os.path.join(output_dir, ''.join(('norm.', filename, '.txt')))
        plotfile = os.path.join(output_dir, ''.join(('plot.', filename, '.', self.inputs.plot_type)))
        return artifactfile, intensityfile, statsfile, normfile, plotfile

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['outlier_files'] = []
        outputs['intensity_files'] = []
        outputs['statistic_files'] = []
        if isdefined(self.inputs.use_norm) and self.inputs.use_norm:
            outputs['norm_files'] = []
        if isdefined(self.inputs.save_plot) and self.inputs.save_plot:
            outputs['plot_files'] = []
        for i, f in enumerate(filename_to_list(self.inputs.realigned_files)):
            outlierfile, intensityfile, statsfile, normfile, plotfile = self._get_output_filenames(f, os.getcwd())
            outputs['outlier_files'].insert(i, outlierfile)
            outputs['intensity_files'].insert(i, intensityfile)
            outputs['statistic_files'].insert(i, statsfile)
            if isdefined(self.inputs.use_norm) and self.inputs.use_norm:
                outputs['norm_files'].insert(i, normfile)
            if isdefined(self.inputs.save_plot) and self.inputs.save_plot:
                outputs['plot_files'].insert(i, plotfile)
        '''
        outputs['outlier_files'] = list_to_filename(outputs['outlier_files'])
        outputs['intensity_files'] = list_to_filename(outputs['intensity_files'])
        outputs['statistic_files'] = list_to_filename(outputs['statistic_files'])
        if isdefined(self.inputs.use_norm) and self.inputs.use_norm:
            outputs['norm_files'] = list_to_filename(outputs['norm_files'])
        if isdefined(self.inputs.save_plot) and self.inputs.save_plot:
            outputs['plot_files'] = list_to_filename(outputs['plot_files'])
        '''
        return outputs

    def _get_affine_matrix(self, params):
        """Returns an affine matrix given a set of parameters

        params : np.array (upto 12 long)
        [translation (3), rotation (3, xyz, radians), scaling (3),
        shear/affine (3)]

        """
        rotfunc = lambda x: np.array([[np.cos(x), np.sin(x)], [-np.sin(x), np.cos(x)]])
        q = np.array([0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0])
        if len(params) < 12:
            params = np.hstack((params, q[len(params):]))
        params.shape = (len(params),)
        # Translation
        T = np.eye(4)
        T[0:3, -1] = params[0:3]  # np.vstack((np.hstack((np.eye(3), params[0:3,])), np.array([0, 0, 0, 1])))
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

        return np.dot(T, np.dot(Rx, np.dot(Ry, np.dot(Rz, np.dot(S, Sh)))))

    def _calc_norm(self, mc, use_differences):
        """Calculates the maximum overall displacement of the midpoints
        of the faces of a cube due to translation and rotation.

        Parameters
        ----------
        mc : motion parameter estimates
            [3 translation, 3 rotation (radians)]
        use_differences : boolean

        Returns
        -------

        norm : at each time point

        """
        respos = np.diag([70, 70, 75])
        resneg = np.diag([-70, -110, -45])
        # respos=np.diag([50, 50, 50]);resneg=np.diag([-50,-50,-50]);
        # XXX - SG why not the above box
        cube_pts = np.vstack((np.hstack((respos, resneg)), np.ones((1, 6))))
        newpos = np.zeros((mc.shape[0], 18))
        for i in range(mc.shape[0]):
            newpos[i, :] = np.dot(self._get_affine_matrix(mc[i, :]), cube_pts)[0:3, :].ravel()
        normdata = np.zeros(mc.shape[0])
        if use_differences:
            newpos = np.concatenate((np.zeros((1, 18)), np.diff(newpos, n=1, axis=0)), axis=0)
            for i in range(newpos.shape[0]):
                normdata[i] = np.max(np.sqrt(np.sum(np.reshape(np.power(np.abs(newpos[i, :]), 2), (3, 6)), axis=0)))
        else:
            #if not registered to mean we may want to use this
            #mc_sum = np.sum(np.abs(mc), axis=1)
            #ref_idx = find_indices(mc_sum == np.min(mc_sum))
            #ref_idx = ref_idx[0]
            #newpos = np.abs(newpos-np.kron(np.ones((newpos.shape[0], 1)), newpos[ref_idx,:]))
            newpos = np.abs(signal.detrend(newpos, axis=0, type='constant'))
            normdata = np.sqrt(np.mean(np.power(newpos, 2), axis=1))
        return normdata

    def _nanmean(self, a, axis=None):
        if axis:
            return np.nansum(a, axis) / np.sum(1 - np.isnan(a), axis)
        else:
            return np.nansum(a) / np.sum(1 - np.isnan(a))

    def _plot_outliers_with_wave(self, wave, outliers, name):
        plt.plot(wave)
        plt.ylim([wave.min(), wave.max()])
        plt.xlim([0, len(wave) - 1])
        if len(outliers):
            plt.plot(np.tile(outliers[:, None], (1, 2)).T,
                     np.tile([wave.min(), wave.max()], (len(outliers), 1)).T,
                     'r')
        plt.xlabel('Scans - 0-based')
        plt.ylabel(name)

    def _detect_outliers_core(self, imgfile, motionfile, runidx, cwd=None):
        """
        Core routine for detecting outliers
        """
        if not cwd:
            cwd = os.getcwd()
        # read in motion parameters
        mc_in = np.loadtxt(motionfile)
        mc = deepcopy(mc_in)
        if self.inputs.parameter_source == 'SPM':
            pass
        elif self.inputs.parameter_source == 'FSL':
            mc = mc[:, [3, 4, 5, 0, 1, 2]]
        elif self.inputs.parameter_source == 'Siemens':
            Exception("Siemens PACE format not implemented yet")
        else:
            Exception("Unknown source for movement parameters")

        if self.inputs.use_norm:
            # calculate the norm of the motion parameters
            normval = self._calc_norm(mc, self.inputs.use_differences[0])
            tidx = find_indices(normval > self.inputs.norm_threshold)
            ridx = find_indices(normval < 0)
        else:
            if self.inputs.use_differences[0]:
                mc = np.concatenate((np.zeros((1, 6)), np.diff(mc_in, n=1, axis=0)), axis=0)
            traval = mc[:, 0:3]  # translation parameters (mm)
            rotval = mc[:, 3:6]  # rotation parameters (rad)
            tidx = find_indices(np.sum(abs(traval) > self.inputs.translation_threshold, 1) > 0)
            ridx = find_indices(np.sum(abs(rotval) > self.inputs.rotation_threshold, 1) > 0)

        # read in functional image
        if isinstance(imgfile, str):
            nim = load(imgfile)
        elif isinstance(imgfile, list):
            if len(imgfile) == 1:
                nim = load(imgfile[0])
            else:
                images = [load(f) for f in imgfile]
                nim = funcs.concat_images(images)

        # compute global intensity signal
        (x, y, z, timepoints) = nim.get_shape()

        data = nim.get_data()
        g = np.zeros((timepoints, 1))
        masktype = self.inputs.mask_type
        if  masktype == 'spm_global':  # spm_global like calculation
            intersect_mask = self.inputs.intersect_mask
            if intersect_mask:
                mask = np.ones((x, y, z), dtype=bool)
                for t0 in range(timepoints):
                    vol = data[:, :, :, t0]
                    mask = mask * (vol > (self._nanmean(vol) / 8))
                for t0 in range(timepoints):
                    vol = data[:, :, :, t0]
                    g[t0] = self._nanmean(vol[mask])
                if len(find_indices(mask)) < (np.prod((x, y, z)) / 10):
                    intersect_mask = False
                    g = np.zeros((timepoints, 1))
            if not intersect_mask:
                for t0 in range(timepoints):
                    vol = data[:, :, :, t0]
                    mask = vol > (self._nanmean(vol) / 8)
                    g[t0] = self._nanmean(vol[mask])
        elif masktype == 'file':  # uses a mask image to determine intensity
            mask = load(self.inputs.mask_file).get_data()
            mask = mask > 0.5
            for t0 in range(timepoints):
                vol = data[:, :, :, t0]
                g[t0] = self._nanmean(vol[mask])
        elif masktype == 'thresh':  # uses a fixed signal threshold
            for t0 in range(timepoints):
                vol = data[:, :, :, t0]
                mask = vol > self.inputs.mask_threshold
                g[t0] = self._nanmean(vol[mask])
        else:
            mask = np.ones((x, y, z))
            g = self._nanmean(data[mask > 0, :], 1)

        # compute normalized intensity values
        gz = signal.detrend(g, axis=0)       # detrend the signal
        if self.inputs.use_differences[1]:
            gz = np.concatenate((np.zeros((1, 1)), np.diff(gz, n=1, axis=0)), axis=0)
        gz = (gz - np.mean(gz)) / np.std(gz)    # normalize the detrended signal
        iidx = find_indices(abs(gz) > self.inputs.zintensity_threshold)

        outliers = np.unique(np.union1d(iidx, np.union1d(tidx, ridx)))
        artifactfile, intensityfile, statsfile, normfile, plotfile = self._get_output_filenames(imgfile, cwd)

        # write output to outputfile
        np.savetxt(artifactfile, outliers, fmt='%d', delimiter=' ')
        np.savetxt(intensityfile, g, fmt='%.2f', delimiter=' ')
        if self.inputs.use_norm:
            np.savetxt(normfile, normval, fmt='%.4f', delimiter=' ')

        if isdefined(self.inputs.save_plot) and self.inputs.save_plot:
            fig = plt.figure()
            if isdefined(self.inputs.use_norm) and self.inputs.use_norm:
                plt.subplot(211)
            else:
                plt.subplot(311)
            self._plot_outliers_with_wave(gz, iidx, 'Intensity')
            if isdefined(self.inputs.use_norm) and self.inputs.use_norm:
                plt.subplot(212)
                self._plot_outliers_with_wave(normval, np.union1d(tidx, ridx), 'Norm (mm)')
            else:
                diff = ''
                if self.inputs.use_differences[0]:
                    diff = 'diff'
                plt.subplot(312)
                self._plot_outliers_with_wave(traval, tidx, 'Translation (mm)' + diff)
                plt.subplot(313)
                self._plot_outliers_with_wave(rotval, ridx, 'Rotation (rad)' + diff)
            plt.savefig(plotfile)
            plt.close(fig)

        motion_outliers = np.union1d(tidx, ridx)
        stats = [{'motion_file': motionfile,
                  'functional_file': imgfile},
                 {'common_outliers': len(np.intersect1d(iidx, motion_outliers)),
                  'intensity_outliers': len(np.setdiff1d(iidx, motion_outliers)),
                  'motion_outliers': len(np.setdiff1d(motion_outliers, iidx)),
                  },
                 {'motion': [{'using differences': self.inputs.use_differences[0]},
                              {'mean': np.mean(mc_in, axis=0).tolist(),
                               'min': np.min(mc_in, axis=0).tolist(),
                               'max': np.max(mc_in, axis=0).tolist(),
                               'std': np.std(mc_in, axis=0).tolist()},
                              ]},
                 {'intensity': [{'using differences': self.inputs.use_differences[1]},
                                 {'mean': np.mean(gz, axis=0).tolist(),
                                  'min': np.min(gz, axis=0).tolist(),
                                  'max': np.max(gz, axis=0).tolist(),
                                  'std': np.std(gz, axis=0).tolist()},
                                 ]},
                 ]
        if self.inputs.use_norm:
            stats.insert(3, {'motion_norm': {'mean': np.mean(normval, axis=0).tolist(),
                                             'min': np.min(normval, axis=0).tolist(),
                                             'max': np.max(normval, axis=0).tolist(),
                                             'std': np.std(normval, axis=0).tolist(),
                                    }})
        save_json(statsfile, stats)

    def _run_interface(self, runtime):
        """Execute this module.
        """
        funcfilelist = filename_to_list(self.inputs.realigned_files)
        motparamlist = filename_to_list(self.inputs.realignment_parameters)
        for i, imgf in enumerate(funcfilelist):
            self._detect_outliers_core(imgf, motparamlist[i], i, os.getcwd())
        return runtime


class StimCorrInputSpec(BaseInterfaceInputSpec):
    realignment_parameters = InputMultiPath(File(exists=True), mandatory=True,
        desc='Names of realignment parameters corresponding to the functional data files')
    intensity_values = InputMultiPath(File(exists=True), mandatory=True,
              desc='Name of file containing intensity values')
    spm_mat_file = File(exists=True, mandatory=True,
                        desc='SPM mat file (use pre-estimate SPM.mat file)')
    concatenated_design = traits.Bool(mandatory=True,
              desc='state if the design matrix contains concatenated sessions')


class StimCorrOutputSpec(TraitedSpec):
    stimcorr_files = OutputMultiPath(File(exists=True),
                     desc='List of files containing correlation values')


class StimulusCorrelation(BaseInterface):
    """Determines if stimuli are correlated with motion or intensity
    parameters.

    Currently this class supports an SPM generated design matrix and requires
    intensity parameters. This implies that one must run
    :ref:`nipype.algorithms.rapidart.ArtifactDetect`
    and :ref:`nipype.interfaces.spm.model.Level1Design` prior to running this or
    provide an SPM.mat file and intensity parameters through some other means.

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
        (filepath, filename) = os.path.split(motionfile)
        (filename, ext) = os.path.splitext(filename)
        corrfile = os.path.join(output_dir, ''.join(('qa.', filename, '_stimcorr.txt')))
        return corrfile

    def _stimcorr_core(self, motionfile, intensityfile, designmatrix, cwd=None):
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
        cols = spmmat['SPM'][0][0].Sess[0][sessidx].col[0][range(len(U))] - 1
        outmatrix = designmatrix.take(rows.tolist(), axis=0).take(cols.tolist(), axis=1)
        return outmatrix

    def _run_interface(self, runtime):
        """Execute this module.
        """
        motparamlist = self.inputs.realignment_parameters
        intensityfiles = self.inputs.intensity_values
        spmmat = sio.loadmat(self.inputs.spm_mat_file, struct_as_record=False)
        nrows = []
        for i, imgf in enumerate(motparamlist):
            sessidx = i
            rows = None
            if self.inputs.concatenated_design:
                sessidx = 0
                mc_in = np.loadtxt(motparamlist[i])
                rows = np.sum(nrows) + np.arange(mc_in.shape[0])
                nrows.append(mc_in.shape[0])
            matrix = self._get_spm_submatrix(spmmat, sessidx, rows)
            self._stimcorr_core(motparamlist[i], intensityfiles[i],
                                matrix, os.getcwd())
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        files = []
        for i, f in enumerate(self.inputs.realignment_parameters):
            files.insert(i, self._get_output_filenames(f, os.getcwd()))
        if files:
            outputs['stimcorr_files'] = files
        return outputs
