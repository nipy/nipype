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

import os.path as op
import numpy as np

from .. import logging
from ..external.due import due, BibTeX
from ..interfaces.base import (traits, TraitedSpec, BaseInterface,
                               BaseInterfaceInputSpec, File, isdefined)
IFLOG = logging.getLogger('interface')


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
