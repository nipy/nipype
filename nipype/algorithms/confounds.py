# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Algorithms to compute confounds in :abbr:`fMRI (functional MRI)`

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname(os.path.realpath(__file__))
    >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
    >>> os.chdir(datadir)

'''
from __future__ import print_function, division, unicode_literals, absolute_import
from builtins import str, zip, range, open

import os
import os.path as op

import nibabel as nb
import numpy as np

from .. import logging
from ..external.due import due, Doi, BibTeX
from ..interfaces.base import (traits, TraitedSpec, BaseInterface,
                               BaseInterfaceInputSpec, File, isdefined)
IFLOG = logging.getLogger('interface')


class ComputeDVARSInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='functional data, after HMC')
    in_mask = File(exists=True, mandatory=True, desc='a brain mask')
    remove_zerovariance = traits.Bool(False, usedefault=True,
                                      desc='remove voxels with zero variance')
    save_std = traits.Bool(True, usedefault=True,
                           desc='save standardized DVARS')
    save_nstd = traits.Bool(False, usedefault=True,
                            desc='save non-standardized DVARS')
    save_vxstd = traits.Bool(False, usedefault=True,
                             desc='save voxel-wise standardized DVARS')
    save_all = traits.Bool(False, usedefault=True, desc='output all DVARS')

    series_tr = traits.Float(desc='repetition time in sec.')
    save_plot = traits.Bool(False, usedefault=True, desc='write DVARS plot')
    figdpi = traits.Int(100, usedefault=True, desc='output dpi for the plot')
    figsize = traits.Tuple(traits.Float(11.7), traits.Float(2.3), usedefault=True,
                           desc='output figure size')
    figformat = traits.Enum('png', 'pdf', 'svg', usedefault=True,
                            desc='output format for figures')



class ComputeDVARSOutputSpec(TraitedSpec):
    out_std = File(exists=True, desc='output text file')
    out_nstd = File(exists=True, desc='output text file')
    out_vxstd = File(exists=True, desc='output text file')
    out_all = File(exists=True, desc='output text file')
    avg_std = traits.Float()
    avg_nstd = traits.Float()
    avg_vxstd = traits.Float()
    fig_std = File(exists=True, desc='output DVARS plot')
    fig_nstd = File(exists=True, desc='output DVARS plot')
    fig_vxstd = File(exists=True, desc='output DVARS plot')


class ComputeDVARS(BaseInterface):
    """
    Computes the DVARS.
    """
    input_spec = ComputeDVARSInputSpec
    output_spec = ComputeDVARSOutputSpec
    references_ = [{
        'entry': BibTeX("""\
@techreport{nichols_notes_2013,
    address = {Coventry, UK},
    title = {Notes on {Creating} a {Standardized} {Version} of {DVARS}},
    url = {http://www2.warwick.ac.uk/fac/sci/statistics/staff/academic-\
research/nichols/scripts/fsl/standardizeddvars.pdf},
    urldate = {2016-08-16},
    institution = {University of Warwick},
    author = {Nichols, Thomas},
    year = {2013}
}"""),
        'tags': ['method']
    }, {
        'entry': BibTeX("""\
@article{power_spurious_2012,
    title = {Spurious but systematic correlations in functional connectivity {MRI} networks \
arise from subject motion},
    volume = {59},
    doi = {10.1016/j.neuroimage.2011.10.018},
    number = {3},
    urldate = {2016-08-16},
    journal = {NeuroImage},
    author = {Power, Jonathan D. and Barnes, Kelly A. and Snyder, Abraham Z. and Schlaggar, \
Bradley L. and Petersen, Steven E.},
    year = {2012},
    pages = {2142--2154},
}
"""),
        'tags': ['method']
    }]

    def __init__(self, **inputs):
        self._results = {}
        super(ComputeDVARS, self).__init__(**inputs)

    def _gen_fname(self, suffix, ext=None):
        fname, in_ext = op.splitext(op.basename(
            self.inputs.in_file))

        if in_ext == '.gz':
            fname, in_ext2 = op.splitext(fname)
            in_ext = in_ext2 + in_ext

        if ext is None:
            ext = in_ext

        if ext.startswith('.'):
            ext = ext[1:]

        return op.abspath('{}_{}.{}'.format(fname, suffix, ext))

    def _run_interface(self, runtime):
        dvars = compute_dvars(self.inputs.in_file, self.inputs.in_mask,
                              remove_zerovariance=self.inputs.remove_zerovariance)

        self._results['avg_std'] = dvars[0].mean()
        self._results['avg_nstd'] = dvars[1].mean()
        self._results['avg_vxstd'] = dvars[2].mean()

        tr = None
        if isdefined(self.inputs.series_tr):
            tr = self.inputs.series_tr

        if self.inputs.save_std:
            out_file = self._gen_fname('dvars_std', ext='tsv')
            np.savetxt(out_file, dvars[0], fmt=b'%0.6f')
            self._results['out_std'] = out_file

            if self.inputs.save_plot:
                self._results['fig_std'] = self._gen_fname(
                    'dvars_std', ext=self.inputs.figformat)
                fig = plot_confound(dvars[0], self.inputs.figsize, 'Standardized DVARS',
                                    series_tr=tr)
                fig.savefig(self._results['fig_std'], dpi=float(self.inputs.figdpi),
                        format=self.inputs.figformat,
                        bbox_inches='tight')
                fig.clf()

        if self.inputs.save_nstd:
            out_file = self._gen_fname('dvars_nstd', ext='tsv')
            np.savetxt(out_file, dvars[1], fmt=b'%0.6f')
            self._results['out_nstd'] = out_file

            if self.inputs.save_plot:
                self._results['fig_nstd'] = self._gen_fname(
                    'dvars_nstd', ext=self.inputs.figformat)
                fig = plot_confound(dvars[1], self.inputs.figsize, 'DVARS', series_tr=tr)
                fig.savefig(self._results['fig_nstd'], dpi=float(self.inputs.figdpi),
                        format=self.inputs.figformat,
                        bbox_inches='tight')
                fig.clf()

        if self.inputs.save_vxstd:
            out_file = self._gen_fname('dvars_vxstd', ext='tsv')
            np.savetxt(out_file, dvars[2], fmt=b'%0.6f')
            self._results['out_vxstd'] = out_file

            if self.inputs.save_plot:
                self._results['fig_vxstd'] = self._gen_fname(
                    'dvars_vxstd', ext=self.inputs.figformat)
                fig = plot_confound(dvars[2], self.inputs.figsize, 'Voxelwise std DVARS',
                                    series_tr=tr)
                fig.savefig(self._results['fig_vxstd'], dpi=float(self.inputs.figdpi),
                        format=self.inputs.figformat,
                        bbox_inches='tight')
                fig.clf()

        if self.inputs.save_all:
            out_file = self._gen_fname('dvars', ext='tsv')
            np.savetxt(out_file, np.vstack(dvars).T, fmt=b'%0.8f', delimiter=b'\t',
                       header='std DVARS\tnon-std DVARS\tvx-wise std DVARS')
            self._results['out_all'] = out_file

        return runtime

    def _list_outputs(self):
        return self._results


class FramewiseDisplacementInputSpec(BaseInterfaceInputSpec):
    in_plots = File(exists=True, desc='motion parameters as written by FSL MCFLIRT')
    radius = traits.Float(50, usedefault=True,
                          desc='radius in mm to calculate angular FDs, 50mm is the '
                               'default since it is used in Power et al. 2012')
    out_file = File('fd_power_2012.txt', usedefault=True, desc='output file name')
    out_figure = File('fd_power_2012.pdf', usedefault=True, desc='output figure name')
    series_tr = traits.Float(desc='repetition time in sec.')
    save_plot = traits.Bool(False, usedefault=True, desc='write FD plot')
    normalize = traits.Bool(False, usedefault=True, desc='calculate FD in mm/s')
    figdpi = traits.Int(100, usedefault=True, desc='output dpi for the FD plot')
    figsize = traits.Tuple(traits.Float(11.7), traits.Float(2.3), usedefault=True,
                           desc='output figure size')

class FramewiseDisplacementOutputSpec(TraitedSpec):
    out_file = File(desc='calculated FD per timestep')
    out_figure = File(desc='output image file')
    fd_average = traits.Float(desc='average FD')

class FramewiseDisplacement(BaseInterface):
    """
    Calculate the :abbr:`FD (framewise displacement)` as in [Power2012]_.
    This implementation reproduces the calculation in fsl_motion_outliers

    .. [Power2012] Power et al., Spurious but systematic correlations in functional
         connectivity MRI networks arise from subject motion, NeuroImage 59(3),
         2012. doi:`10.1016/j.neuroimage.2011.10.018
         <http://dx.doi.org/10.1016/j.neuroimage.2011.10.018>`_.


    """

    input_spec = FramewiseDisplacementInputSpec
    output_spec = FramewiseDisplacementOutputSpec

    references_ = [{
        'entry': BibTeX("""\
@article{power_spurious_2012,
    title = {Spurious but systematic correlations in functional connectivity {MRI} networks \
arise from subject motion},
    volume = {59},
    doi = {10.1016/j.neuroimage.2011.10.018},
    number = {3},
    urldate = {2016-08-16},
    journal = {NeuroImage},
    author = {Power, Jonathan D. and Barnes, Kelly A. and Snyder, Abraham Z. and Schlaggar, \
Bradley L. and Petersen, Steven E.},
    year = {2012},
    pages = {2142--2154},
}
"""),
        'tags': ['method']
    }]

    def _run_interface(self, runtime):
        mpars = np.loadtxt(self.inputs.in_plots)  # mpars is N_t x 6
        diff = mpars[:-1, :] - mpars[1:, :]
        diff[:, :3] *= self.inputs.radius
        fd_res = np.abs(diff).sum(axis=1)

        self._results = {
            'out_file': op.abspath(self.inputs.out_file),
            'fd_average': float(fd_res.mean())
        }
        np.savetxt(self.inputs.out_file, fd_res)

        if self.inputs.save_plot:
            tr = None
            if isdefined(self.inputs.series_tr):
                tr = self.inputs.series_tr

            if self.inputs.normalize and tr is None:
                IFLOG.warn('FD plot cannot be normalized if TR is not set')

            self._results['out_figure'] = op.abspath(self.inputs.out_figure)
            fig = plot_confound(fd_res, self.inputs.figsize, 'FD', units='mm',
                                series_tr=tr, normalize=self.inputs.normalize)
            fig.savefig(self._results['out_figure'], dpi=float(self.inputs.figdpi),
                        format=self.inputs.out_figure[-3:],
                        bbox_inches='tight')
            fig.clf()

        return runtime

    def _list_outputs(self):
        return self._results


def compute_dvars(in_file, in_mask, remove_zerovariance=False):
    """
    Compute the :abbr:`DVARS (D referring to temporal
    derivative of timecourses, VARS referring to RMS variance over voxels)`
    [Power2012]_.

    Particularly, the *standardized* :abbr:`DVARS (D referring to temporal
    derivative of timecourses, VARS referring to RMS variance over voxels)`
    [Nichols2013]_ are computed.

    .. [Nichols2013] Nichols T, `Notes on creating a standardized version of
         DVARS <http://www2.warwick.ac.uk/fac/sci/statistics/staff/academic-\
research/nichols/scripts/fsl/standardizeddvars.pdf>`_, 2013.

    .. note:: Implementation details

      Uses the implementation of the `Yule-Walker equations
      from nitime
      <http://nipy.org/nitime/api/generated/nitime.algorithms.autoregressive.html\
#nitime.algorithms.autoregressive.AR_est_YW>`_
      for the :abbr:`AR (auto-regressive)` filtering of the fMRI signal.

    :param numpy.ndarray func: functional data, after head-motion-correction.
    :param numpy.ndarray mask: a 3D mask of the brain
    :param bool output_all: write out all dvars
    :param str out_file: a path to which the standardized dvars should be saved.
    :return: the standardized DVARS

    """
    import os.path as op
    import numpy as np
    import nibabel as nb
    from nitime.algorithms import AR_est_YW

    func = nb.load(in_file).get_data().astype(np.float32)
    mask = nb.load(in_mask).get_data().astype(np.uint8)

    if len(func.shape) != 4:
        raise RuntimeError(
            "Input fMRI dataset should be 4-dimensional")

    # Robust standard deviation
    func_sd = (np.percentile(func, 75, axis=3) -
               np.percentile(func, 25, axis=3)) / 1.349
    func_sd[mask <= 0] = 0

    # ar1_img = np.zeros_like(func_sd)
    # ar1_img[idx] = diff_SDhat
    nb.Nifti1Image(func_sd, nb.load(in_mask).get_affine()).to_filename('func_sd.nii.gz')


    if remove_zerovariance:
        # Remove zero-variance voxels across time axis
        mask = zero_variance(func, mask)

    idx = np.where(mask > 0)
    mfunc = func[idx[0], idx[1], idx[2], :]

    # Demean
    mfunc -= mfunc.mean(axis=1).astype(np.float32)[..., np.newaxis]

    # Compute (non-robust) estimate of lag-1 autocorrelation
    ar1 = np.apply_along_axis(AR_est_YW, 1, mfunc, 1)[:, 0]

    # Compute (predicted) standard deviation of temporal difference time series
    diff_SDhat = np.squeeze(np.sqrt(((1 - ar1) * 2).tolist())) * func_sd[mask > 0].reshape(-1)
    diff_sd_mean = diff_SDhat.mean()

    # Compute temporal difference time series
    func_diff = np.diff(mfunc, axis=1)

    # DVARS (no standardization)
    dvars_nstd = func_diff.std(axis=0)

    # standardization
    dvars_stdz = dvars_nstd / diff_sd_mean

    # voxelwise standardization
    diff_vx_stdz = func_diff / np.array([diff_SDhat] * func_diff.shape[-1]).T
    dvars_vx_stdz = diff_vx_stdz.std(axis=0, ddof=1)

    return (dvars_stdz, dvars_nstd, dvars_vx_stdz)

def zero_variance(func, mask):
    """
    Mask out voxels with zero variance across t-axis

    :param numpy.ndarray func: input fMRI dataset, after motion correction
    :param numpy.ndarray mask: 3D brain mask
    :return: the 3D mask of voxels with nonzero variance across :math:`t`.
    :rtype: numpy.ndarray

    """
    idx = np.where(mask > 0)
    func = func[idx[0], idx[1], idx[2], :]
    tvariance = func.var(axis=1)
    tv_mask = np.zeros_like(tvariance, dtype=np.uint8)
    tv_mask[tvariance > 0] = 1

    newmask = np.zeros_like(mask, dtype=np.uint8)
    newmask[idx] = tv_mask
    return newmask

def plot_confound(tseries, figsize, name, units=None,
                  series_tr=None, normalize=False):
    """
    A helper function to plot :abbr:`fMRI (functional MRI)` confounds.

    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    from matplotlib.backends.backend_pdf import FigureCanvasPdf as FigureCanvas
    import seaborn as sns

    fig = plt.Figure(figsize=figsize)
    FigureCanvas(fig)
    grid = GridSpec(1, 2, width_ratios=[3, 1], wspace=0.025)
    grid.update(hspace=1.0, right=0.95, left=0.1, bottom=0.2)

    ax = fig.add_subplot(grid[0, :-1])
    if normalize and series_tr is not None:
        tseries /= series_tr

    ax.plot(tseries)
    ax.set_xlim((0, len(tseries)))
    ylabel = name
    if units is not None:
        ylabel += (' speed [{}/s]' if normalize else ' [{}]').format(units)
    ax.set_ylabel(ylabel)

    xlabel = 'Frame #'
    if series_tr is not None:
        xlabel = 'Frame # ({} sec TR)'.format(series_tr)
    ax.set_xlabel(xlabel)
    ylim = ax.get_ylim()

    ax = fig.add_subplot(grid[0, -1])
    sns.distplot(tseries, vertical=True, ax=ax)
    ax.set_xlabel('Frames')
    ax.set_ylim(ylim)
    ax.set_yticklabels([])
    return fig
