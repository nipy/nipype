# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Algorithms to compute confounds in :abbr:`fMRI (functional MRI)`
'''
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import range

import os
import os.path as op

import nibabel as nb
import numpy as np
from numpy.polynomial import Legendre
from scipy import linalg

from .. import config, logging
from ..external.due import BibTeX
from ..interfaces.base import (traits, TraitedSpec, BaseInterface,
                               BaseInterfaceInputSpec, File, isdefined,
                               InputMultiPath, OutputMultiPath)
from ..utils import NUMPY_MMAP
from ..utils.misc import normalize_mc_params

IFLOGGER = logging.getLogger('nipype.interface')


class ComputeDVARSInputSpec(BaseInterfaceInputSpec):
    in_file = File(
        exists=True, mandatory=True, desc='functional data, after HMC')
    in_mask = File(exists=True, mandatory=True, desc='a brain mask')
    remove_zerovariance = traits.Bool(
        True, usedefault=True, desc='remove voxels with zero variance')
    save_std = traits.Bool(
        True, usedefault=True, desc='save standardized DVARS')
    save_nstd = traits.Bool(
        False, usedefault=True, desc='save non-standardized DVARS')
    save_vxstd = traits.Bool(
        False, usedefault=True, desc='save voxel-wise standardized DVARS')
    save_all = traits.Bool(False, usedefault=True, desc='output all DVARS')

    series_tr = traits.Float(desc='repetition time in sec.')
    save_plot = traits.Bool(False, usedefault=True, desc='write DVARS plot')
    figdpi = traits.Int(100, usedefault=True, desc='output dpi for the plot')
    figsize = traits.Tuple(
        traits.Float(11.7),
        traits.Float(2.3),
        usedefault=True,
        desc='output figure size')
    figformat = traits.Enum(
        'png', 'pdf', 'svg', usedefault=True, desc='output format for figures')
    intensity_normalization = traits.Float(
        1000.0,
        usedefault=True,
        desc='Divide value in each voxel at each timepoint '
        'by the median calculated across all voxels'
        'and timepoints within the mask (if specified)'
        'and then multiply by the value specified by'
        'this parameter. By using the default (1000)'
        'output DVARS will be expressed in '
        'x10 % BOLD units compatible with Power et al.'
        '2012. Set this to 0 to disable intensity'
        'normalization altogether.')


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
        'entry':
        BibTeX("""\
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
        'entry':
        BibTeX("""\
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
        fname, in_ext = op.splitext(op.basename(self.inputs.in_file))

        if in_ext == '.gz':
            fname, in_ext2 = op.splitext(fname)
            in_ext = in_ext2 + in_ext

        if ext is None:
            ext = in_ext

        if ext.startswith('.'):
            ext = ext[1:]

        return op.abspath('{}_{}.{}'.format(fname, suffix, ext))

    def _run_interface(self, runtime):
        dvars = compute_dvars(
            self.inputs.in_file,
            self.inputs.in_mask,
            remove_zerovariance=self.inputs.remove_zerovariance,
            intensity_normalization=self.inputs.intensity_normalization)

        (self._results['avg_std'], self._results['avg_nstd'],
         self._results['avg_vxstd']) = np.mean(
             dvars, axis=1).astype(float)

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
                fig = plot_confound(
                    dvars[0],
                    self.inputs.figsize,
                    'Standardized DVARS',
                    series_tr=tr)
                fig.savefig(
                    self._results['fig_std'],
                    dpi=float(self.inputs.figdpi),
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
                fig = plot_confound(
                    dvars[1], self.inputs.figsize, 'DVARS', series_tr=tr)
                fig.savefig(
                    self._results['fig_nstd'],
                    dpi=float(self.inputs.figdpi),
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
                fig = plot_confound(
                    dvars[2],
                    self.inputs.figsize,
                    'Voxelwise std DVARS',
                    series_tr=tr)
                fig.savefig(
                    self._results['fig_vxstd'],
                    dpi=float(self.inputs.figdpi),
                    format=self.inputs.figformat,
                    bbox_inches='tight')
                fig.clf()

        if self.inputs.save_all:
            out_file = self._gen_fname('dvars', ext='tsv')
            np.savetxt(
                out_file,
                np.vstack(dvars).T,
                fmt=b'%0.8f',
                delimiter=b'\t',
                header='std DVARS\tnon-std DVARS\tvx-wise std DVARS',
                comments='')
            self._results['out_all'] = out_file

        return runtime

    def _list_outputs(self):
        return self._results


class FramewiseDisplacementInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='motion parameters')
    parameter_source = traits.Enum(
        "FSL",
        "AFNI",
        "SPM",
        "FSFAST",
        "NIPY",
        desc="Source of movement parameters",
        mandatory=True)
    radius = traits.Float(
        50,
        usedefault=True,
        desc='radius in mm to calculate angular FDs, 50mm is the '
        'default since it is used in Power et al. 2012')
    out_file = File(
        'fd_power_2012.txt', usedefault=True, desc='output file name')
    out_figure = File(
        'fd_power_2012.pdf', usedefault=True, desc='output figure name')
    series_tr = traits.Float(desc='repetition time in sec.')
    save_plot = traits.Bool(False, usedefault=True, desc='write FD plot')
    normalize = traits.Bool(
        False, usedefault=True, desc='calculate FD in mm/s')
    figdpi = traits.Int(
        100, usedefault=True, desc='output dpi for the FD plot')
    figsize = traits.Tuple(
        traits.Float(11.7),
        traits.Float(2.3),
        usedefault=True,
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
        'entry':
        BibTeX("""\
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
        mpars = np.loadtxt(self.inputs.in_file)  # mpars is N_t x 6
        mpars = np.apply_along_axis(
            func1d=normalize_mc_params,
            axis=1,
            arr=mpars,
            source=self.inputs.parameter_source)
        diff = mpars[:-1, :6] - mpars[1:, :6]
        diff[:, 3:6] *= self.inputs.radius
        fd_res = np.abs(diff).sum(axis=1)

        self._results = {
            'out_file': op.abspath(self.inputs.out_file),
            'fd_average': float(fd_res.mean())
        }
        np.savetxt(
            self.inputs.out_file,
            fd_res,
            header='FramewiseDisplacement',
            comments='')

        if self.inputs.save_plot:
            tr = None
            if isdefined(self.inputs.series_tr):
                tr = self.inputs.series_tr

            if self.inputs.normalize and tr is None:
                IFLOGGER.warn('FD plot cannot be normalized if TR is not set')

            self._results['out_figure'] = op.abspath(self.inputs.out_figure)
            fig = plot_confound(
                fd_res,
                self.inputs.figsize,
                'FD',
                units='mm',
                series_tr=tr,
                normalize=self.inputs.normalize)
            fig.savefig(
                self._results['out_figure'],
                dpi=float(self.inputs.figdpi),
                format=self.inputs.out_figure[-3:],
                bbox_inches='tight')
            fig.clf()

        return runtime

    def _list_outputs(self):
        return self._results


class CompCorInputSpec(BaseInterfaceInputSpec):
    realigned_file = File(
        exists=True, mandatory=True, desc='already realigned brain image (4D)')
    mask_files = InputMultiPath(
        File(exists=True),
        desc=('One or more mask files that determines '
              'ROI (3D). When more that one file is '
              'provided `merge_method` or '
              '`merge_index` must be provided'))
    merge_method = traits.Enum(
        'union',
        'intersect',
        'none',
        xor=['mask_index'],
        requires=['mask_files'],
        desc=('Merge method if multiple masks are '
              'present - `union` uses voxels included in'
              ' at least one input mask, `intersect` '
              'uses only voxels present in all input '
              'masks, `none` performs CompCor on '
              'each mask individually'))
    mask_index = traits.Range(
        low=0,
        xor=['merge_method'],
        requires=['mask_files'],
        desc=('Position of mask in `mask_files` to use - '
              'first is the default.'))
    components_file = traits.Str(
        'components_file.txt',
        usedefault=True,
        desc='Filename to store physiological components')
    num_components = traits.Int(6, usedefault=True)  # 6 for BOLD, 4 for ASL
    pre_filter = traits.Enum(
        'polynomial',
        'cosine',
        False,
        usedefault=True,
        desc='Detrend time series prior to component '
        'extraction')
    use_regress_poly = traits.Bool(
        deprecated='0.15.0',
        new_name='pre_filter',
        desc=('use polynomial regression '
              'pre-component extraction'))
    regress_poly_degree = traits.Range(
        low=1, value=1, usedefault=True, desc='the degree polynomial to use')
    header_prefix = traits.Str(
        desc=('the desired header for the output tsv '
              'file (one column). If undefined, will '
              'default to "CompCor"'))
    high_pass_cutoff = traits.Float(
        128,
        usedefault=True,
        desc='Cutoff (in seconds) for "cosine" pre-filter')
    repetition_time = traits.Float(
        desc='Repetition time (TR) of series - derived from image header if '
        'unspecified')
    save_pre_filter = traits.Either(
        traits.Bool, File, desc='Save pre-filter basis as text file')
    ignore_initial_volumes = traits.Range(
        low=0,
        usedefault=True,
        desc='Number of volumes at start of series to ignore')


class CompCorOutputSpec(TraitedSpec):
    components_file = File(
        exists=True, desc='text file containing the noise components')
    pre_filter_file = File(desc='text file containing high-pass filter basis')


class CompCor(BaseInterface):
    """
    Interface with core CompCor computation, used in aCompCor and tCompCor

    CompCor provides three pre-filter options, all of which include per-voxel
    mean removal:
      - polynomial: Legendre polynomial basis
      - cosine: Discrete cosine basis
      - False: mean-removal only

    In the case of ``polynomial`` and ``cosine`` filters, a pre-filter file may
    be saved with a row for each volume/timepoint, and a column for each
    non-constant regressor.
    If no non-constant (mean-removal) columns are used, this file may be empty.

    If ``ignore_initial_volumes`` is set, then the specified number of initial
    volumes are excluded both from pre-filtering and CompCor component
    extraction.
    Each column in the components and pre-filter files are prefixe with zeros
    for each excluded volume so that the number of rows continues to match the
    number of volumes in the input file.
    In addition, for each excluded volume, a column is added to the pre-filter
    file with a 1 in the corresponding row.

    Example
    -------

    >>> ccinterface = CompCor()
    >>> ccinterface.inputs.realigned_file = 'functional.nii'
    >>> ccinterface.inputs.mask_files = 'mask.nii'
    >>> ccinterface.inputs.num_components = 1
    >>> ccinterface.inputs.pre_filter = 'polynomial'
    >>> ccinterface.inputs.regress_poly_degree = 2

    """
    input_spec = CompCorInputSpec
    output_spec = CompCorOutputSpec
    references_ = [{
        'entry':
        BibTeX(
            "@article{compcor_2007,"
            "title = {A component based noise correction method (CompCor) for BOLD and perfusion based},"
            "volume = {37},"
            "number = {1},"
            "doi = {10.1016/j.neuroimage.2007.04.042},"
            "urldate = {2016-08-13},"
            "journal = {NeuroImage},"
            "author = {Behzadi, Yashar and Restom, Khaled and Liau, Joy and Liu, Thomas T.},"
            "year = {2007},"
            "pages = {90-101},}"),
        'tags': ['method', 'implementation']
    }]

    def __init__(self, *args, **kwargs):
        ''' exactly the same as compcor except the header '''
        super(CompCor, self).__init__(*args, **kwargs)
        self._header = 'CompCor'

    def _run_interface(self, runtime):
        mask_images = []
        if isdefined(self.inputs.mask_files):
            mask_images = combine_mask_files(self.inputs.mask_files,
                                             self.inputs.merge_method,
                                             self.inputs.mask_index)

        if self.inputs.use_regress_poly:
            self.inputs.pre_filter = 'polynomial'

        # Degree 0 == remove mean; see compute_noise_components
        degree = (self.inputs.regress_poly_degree
                  if self.inputs.pre_filter == 'polynomial' else 0)

        imgseries = nb.load(self.inputs.realigned_file, mmap=NUMPY_MMAP)

        if len(imgseries.shape) != 4:
            raise ValueError('{} expected a 4-D nifti file. Input {} has '
                             '{} dimensions (shape {})'.format(
                                 self._header, self.inputs.realigned_file,
                                 len(imgseries.shape), imgseries.shape))

        if len(mask_images) == 0:
            img = nb.Nifti1Image(
                np.ones(imgseries.shape[:3], dtype=np.bool),
                affine=imgseries.affine,
                header=imgseries.header)
            mask_images = [img]

        skip_vols = self.inputs.ignore_initial_volumes
        if skip_vols:
            imgseries = imgseries.__class__(
                imgseries.get_data()[..., skip_vols:], imgseries.affine,
                imgseries.header)

        mask_images = self._process_masks(mask_images, imgseries.get_data())

        TR = 0
        if self.inputs.pre_filter == 'cosine':
            if isdefined(self.inputs.repetition_time):
                TR = self.inputs.repetition_time
            else:
                # Derive TR from NIfTI header, if possible
                try:
                    TR = imgseries.header.get_zooms()[3]
                    if imgseries.header.get_xyzt_units()[1] == 'msec':
                        TR /= 1000
                except (AttributeError, IndexError):
                    TR = 0

                if TR == 0:
                    raise ValueError(
                        '{} cannot detect repetition time from image - '
                        'Set the repetition_time input'.format(self._header))

        components, filter_basis = compute_noise_components(
            imgseries.get_data(), mask_images, self.inputs.num_components,
            self.inputs.pre_filter, degree, self.inputs.high_pass_cutoff, TR)

        if skip_vols:
            old_comp = components
            nrows = skip_vols + components.shape[0]
            components = np.zeros(
                (nrows, components.shape[1]), dtype=components.dtype)
            components[skip_vols:] = old_comp

        components_file = os.path.join(os.getcwd(),
                                       self.inputs.components_file)
        np.savetxt(
            components_file,
            components,
            fmt=b"%.10f",
            delimiter='\t',
            header=self._make_headers(components.shape[1]),
            comments='')

        if self.inputs.pre_filter and self.inputs.save_pre_filter:
            pre_filter_file = self._list_outputs()['pre_filter_file']
            ftype = {
                'polynomial': 'Legendre',
                'cosine': 'Cosine'
            }[self.inputs.pre_filter]
            ncols = filter_basis.shape[1] if filter_basis.size > 0 else 0
            header = ['{}{:02d}'.format(ftype, i) for i in range(ncols)]
            if skip_vols:
                old_basis = filter_basis
                # nrows defined above
                filter_basis = np.zeros(
                    (nrows, ncols + skip_vols), dtype=filter_basis.dtype)
                if old_basis.size > 0:
                    filter_basis[skip_vols:, :ncols] = old_basis
                filter_basis[:skip_vols, -skip_vols:] = np.eye(skip_vols)
                header.extend([
                    'NonSteadyStateOutlier{:02d}'.format(i)
                    for i in range(skip_vols)
                ])
            np.savetxt(
                pre_filter_file,
                filter_basis,
                fmt=b'%.10f',
                delimiter='\t',
                header='\t'.join(header),
                comments='')

        return runtime

    def _process_masks(self, mask_images, timeseries=None):
        return mask_images

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['components_file'] = os.path.abspath(
            self.inputs.components_file)

        save_pre_filter = self.inputs.save_pre_filter
        if save_pre_filter:
            if isinstance(save_pre_filter, bool):
                save_pre_filter = os.path.abspath('pre_filter.tsv')
            outputs['pre_filter_file'] = save_pre_filter

        return outputs

    def _make_headers(self, num_col):
        header = self.inputs.header_prefix if \
            isdefined(self.inputs.header_prefix) else self._header
        headers = ['{}{:02d}'.format(header, i) for i in range(num_col)]
        return '\t'.join(headers)


class ACompCor(CompCor):
    """
    Anatomical compcor: for inputs and outputs, see CompCor.
    When the mask provided is an anatomical mask, then CompCor
    is equivalent to ACompCor.
    """

    def __init__(self, *args, **kwargs):
        ''' exactly the same as compcor except the header '''
        super(ACompCor, self).__init__(*args, **kwargs)
        self._header = 'aCompCor'


class TCompCorInputSpec(CompCorInputSpec):
    # and all the fields in CompCorInputSpec
    percentile_threshold = traits.Range(
        low=0.,
        high=1.,
        value=.02,
        exclude_low=True,
        exclude_high=True,
        usedefault=True,
        desc='the percentile '
        'used to select highest-variance '
        'voxels, represented by a number '
        'between 0 and 1, exclusive. By '
        'default, this value is set to .02. '
        'That is, the 2% of voxels '
        'with the highest variance are used.')


class TCompCorOutputSpec(CompCorOutputSpec):
    # and all the fields in CompCorOutputSpec
    high_variance_masks = OutputMultiPath(
        File(exists=True),
        desc=(("voxels exceeding the variance"
               " threshold")))


class TCompCor(CompCor):
    """
    Interface for tCompCor. Computes a ROI mask based on variance of voxels.

    Example
    -------

    >>> ccinterface = TCompCor()
    >>> ccinterface.inputs.realigned_file = 'functional.nii'
    >>> ccinterface.inputs.mask_files = 'mask.nii'
    >>> ccinterface.inputs.num_components = 1
    >>> ccinterface.inputs.pre_filter = 'polynomial'
    >>> ccinterface.inputs.regress_poly_degree = 2
    >>> ccinterface.inputs.percentile_threshold = .03

    """

    input_spec = TCompCorInputSpec
    output_spec = TCompCorOutputSpec

    def __init__(self, *args, **kwargs):
        ''' exactly the same as compcor except the header '''
        super(TCompCor, self).__init__(*args, **kwargs)
        self._header = 'tCompCor'
        self._mask_files = []

    def _process_masks(self, mask_images, timeseries=None):
        out_images = []
        self._mask_files = []
        for i, img in enumerate(mask_images):
            mask = img.get_data().astype(np.bool)
            imgseries = timeseries[mask, :]
            imgseries = regress_poly(2, imgseries)[0]
            tSTD = _compute_tSTD(imgseries, 0, axis=-1)
            threshold_std = np.percentile(
                tSTD,
                np.round(100. *
                         (1. - self.inputs.percentile_threshold)).astype(int))
            mask_data = np.zeros_like(mask)
            mask_data[mask != 0] = tSTD >= threshold_std
            out_image = nb.Nifti1Image(
                mask_data, affine=img.affine, header=img.header)

            # save mask
            mask_file = os.path.abspath('mask_{:03d}.nii.gz'.format(i))
            out_image.to_filename(mask_file)
            IFLOGGER.debug('tCompcor computed and saved mask of shape %s to '
                           'mask_file %s', str(mask.shape), mask_file)
            self._mask_files.append(mask_file)
            out_images.append(out_image)
        return out_images

    def _list_outputs(self):
        outputs = super(TCompCor, self)._list_outputs()
        outputs['high_variance_masks'] = self._mask_files
        return outputs


class TSNRInputSpec(BaseInterfaceInputSpec):
    in_file = InputMultiPath(
        File(exists=True),
        mandatory=True,
        desc='realigned 4D file or a list of 3D files')
    regress_poly = traits.Range(low=1, desc='Remove polynomials')
    tsnr_file = File(
        'tsnr.nii.gz',
        usedefault=True,
        hash_files=False,
        desc='output tSNR file')
    mean_file = File(
        'mean.nii.gz',
        usedefault=True,
        hash_files=False,
        desc='output mean file')
    stddev_file = File(
        'stdev.nii.gz',
        usedefault=True,
        hash_files=False,
        desc='output tSNR file')
    detrended_file = File(
        'detrend.nii.gz',
        usedefault=True,
        hash_files=False,
        desc='input file after detrending')


class TSNROutputSpec(TraitedSpec):
    tsnr_file = File(exists=True, desc='tsnr image file')
    mean_file = File(exists=True, desc='mean image file')
    stddev_file = File(exists=True, desc='std dev image file')
    detrended_file = File(desc='detrended input file')


class TSNR(BaseInterface):
    """
    Computes the time-course SNR for a time series

    Typically you want to run this on a realigned time-series.

    Example
    -------

    >>> tsnr = TSNR()
    >>> tsnr.inputs.in_file = 'functional.nii'
    >>> res = tsnr.run() # doctest: +SKIP

    """
    input_spec = TSNRInputSpec
    output_spec = TSNROutputSpec

    def _run_interface(self, runtime):
        img = nb.load(self.inputs.in_file[0], mmap=NUMPY_MMAP)
        header = img.header.copy()
        vollist = [
            nb.load(filename, mmap=NUMPY_MMAP)
            for filename in self.inputs.in_file
        ]
        data = np.concatenate(
            [
                vol.get_data().reshape(vol.shape[:3] + (-1, ))
                for vol in vollist
            ],
            axis=3)
        data = np.nan_to_num(data)

        if data.dtype.kind == 'i':
            header.set_data_dtype(np.float32)
            data = data.astype(np.float32)

        if isdefined(self.inputs.regress_poly):
            data = regress_poly(
                self.inputs.regress_poly, data, remove_mean=False)[0]
            img = nb.Nifti1Image(data, img.affine, header)
            nb.save(img, op.abspath(self.inputs.detrended_file))

        meanimg = np.mean(data, axis=3)
        stddevimg = np.std(data, axis=3)
        tsnr = np.zeros_like(meanimg)
        tsnr[stddevimg > 1.e-3] = meanimg[stddevimg > 1.e-3] / stddevimg[
            stddevimg > 1.e-3]
        img = nb.Nifti1Image(tsnr, img.affine, header)
        nb.save(img, op.abspath(self.inputs.tsnr_file))
        img = nb.Nifti1Image(meanimg, img.affine, header)
        nb.save(img, op.abspath(self.inputs.mean_file))
        img = nb.Nifti1Image(stddevimg, img.affine, header)
        nb.save(img, op.abspath(self.inputs.stddev_file))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        for k in ['tsnr_file', 'mean_file', 'stddev_file']:
            outputs[k] = op.abspath(getattr(self.inputs, k))

        if isdefined(self.inputs.regress_poly):
            outputs['detrended_file'] = op.abspath(self.inputs.detrended_file)
        return outputs


class NonSteadyStateDetectorInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='4D NIFTI EPI file')


class NonSteadyStateDetectorOutputSpec(TraitedSpec):
    n_volumes_to_discard = traits.Int(desc='Number of non-steady state volumes'
                                      'detected in the beginning of the scan.')


class NonSteadyStateDetector(BaseInterface):
    """
    Returns the number of non-steady state volumes detected at the beginning
    of the scan.
    """

    input_spec = NonSteadyStateDetectorInputSpec
    output_spec = NonSteadyStateDetectorOutputSpec

    def _run_interface(self, runtime):
        in_nii = nb.load(self.inputs.in_file)
        global_signal = in_nii.get_data()[:, :, :, :50].mean(axis=0).mean(
            axis=0).mean(axis=0)

        self._results = {'n_volumes_to_discard': is_outlier(global_signal)}

        return runtime

    def _list_outputs(self):
        return self._results


def compute_dvars(in_file,
                  in_mask,
                  remove_zerovariance=False,
                  intensity_normalization=1000):
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
    import numpy as np
    import nibabel as nb
    from nitime.algorithms import AR_est_YW
    import warnings

    func = nb.load(in_file, mmap=NUMPY_MMAP).get_data().astype(np.float32)
    mask = nb.load(in_mask, mmap=NUMPY_MMAP).get_data().astype(np.uint8)

    if len(func.shape) != 4:
        raise RuntimeError("Input fMRI dataset should be 4-dimensional")

    idx = np.where(mask > 0)
    mfunc = func[idx[0], idx[1], idx[2], :]

    if intensity_normalization != 0:
        mfunc = (mfunc / np.median(mfunc)) * intensity_normalization

    # Robust standard deviation (we are using "lower" interpolation
    # because this is what FSL is doing
    func_sd = (np.percentile(mfunc, 75, axis=1, interpolation="lower") -
               np.percentile(mfunc, 25, axis=1, interpolation="lower")) / 1.349

    if remove_zerovariance:
        mfunc = mfunc[func_sd != 0, :]
        func_sd = func_sd[func_sd != 0]

    # Compute (non-robust) estimate of lag-1 autocorrelation
    ar1 = np.apply_along_axis(AR_est_YW, 1,
                              regress_poly(0, mfunc,
                                           remove_mean=True)[0].astype(
                                               np.float32), 1)[:, 0]

    # Compute (predicted) standard deviation of temporal difference time series
    diff_sdhat = np.squeeze(np.sqrt(((1 - ar1) * 2).tolist())) * func_sd
    diff_sd_mean = diff_sdhat.mean()

    # Compute temporal difference time series
    func_diff = np.diff(mfunc, axis=1)

    # DVARS (no standardization)
    dvars_nstd = np.sqrt(np.square(func_diff).mean(axis=0))

    # standardization
    dvars_stdz = dvars_nstd / diff_sd_mean

    with warnings.catch_warnings():  # catch, e.g., divide by zero errors
        warnings.filterwarnings('error')

        # voxelwise standardization
        diff_vx_stdz = np.square(
            func_diff / np.array([diff_sdhat] * func_diff.shape[-1]).T)
        dvars_vx_stdz = np.sqrt(diff_vx_stdz.mean(axis=0))

    return (dvars_stdz, dvars_nstd, dvars_vx_stdz)


def plot_confound(tseries,
                  figsize,
                  name,
                  units=None,
                  series_tr=None,
                  normalize=False):
    """
    A helper function to plot :abbr:`fMRI (functional MRI)` confounds.

    """
    import matplotlib
    matplotlib.use(config.get('execution', 'matplotlib_backend'))
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


def is_outlier(points, thresh=3.5):
    """
    Returns a boolean array with True if points are outliers and False
    otherwise.

    :param nparray points: an numobservations by numdimensions numpy array of observations
    :param float thresh: the modified z-score to use as a threshold. Observations with
        a modified z-score (based on the median absolute deviation) greater
        than this value will be classified as outliers.

    :return: A bolean mask, of size numobservations-length array.

    .. note:: References

        Boris Iglewicz and David Hoaglin (1993), "Volume 16: How to Detect and
        Handle Outliers", The ASQC Basic References in Quality Control:
        Statistical Techniques, Edward F. Mykytka, Ph.D., Editor.

    """
    if len(points.shape) == 1:
        points = points[:, None]
    median = np.median(points, axis=0)
    diff = np.sum((points - median)**2, axis=-1)
    diff = np.sqrt(diff)
    med_abs_deviation = np.median(diff)

    modified_z_score = 0.6745 * diff / med_abs_deviation

    timepoints_to_discard = 0
    for i in range(len(modified_z_score)):
        if modified_z_score[i] <= thresh:
            break
        else:
            timepoints_to_discard += 1

    return timepoints_to_discard


def cosine_filter(data, timestep, period_cut, remove_mean=True, axis=-1):
    datashape = data.shape
    timepoints = datashape[axis]

    data = data.reshape((-1, timepoints))

    frametimes = timestep * np.arange(timepoints)
    X = _full_rank(_cosine_drift(period_cut, frametimes))[0]
    non_constant_regressors = X[:, :-1] if X.shape[1] > 1 else np.array([])

    betas = np.linalg.lstsq(X, data.T)[0]

    if not remove_mean:
        X = X[:, :-1]
        betas = betas[:-1]

    residuals = data - X.dot(betas).T

    return residuals.reshape(datashape), non_constant_regressors


def regress_poly(degree, data, remove_mean=True, axis=-1):
    """
    Returns data with degree polynomial regressed out.

    :param bool remove_mean: whether or not demean data (i.e. degree 0),
    :param int axis: numpy array axes along which regression is performed

    """
    IFLOGGER.debug('Performing polynomial regression on data of shape %s',
                   str(data.shape))

    datashape = data.shape
    timepoints = datashape[axis]

    # Rearrange all voxel-wise time-series in rows
    data = data.reshape((-1, timepoints))

    # Generate design matrix
    X = np.ones((timepoints, 1))  # quick way to calc degree 0
    for i in range(degree):
        polynomial_func = Legendre.basis(i + 1)
        value_array = np.linspace(-1, 1, timepoints)
        X = np.hstack((X, polynomial_func(value_array)[:, np.newaxis]))

    non_constant_regressors = X[:, :-1] if X.shape[1] > 1 else np.array([])

    # Calculate coefficients
    betas = np.linalg.pinv(X).dot(data.T)

    # Estimation
    if remove_mean:
        datahat = X.dot(betas).T
    else:  # disregard the first layer of X, which is degree 0
        datahat = X[:, 1:].dot(betas[1:, ...]).T
    regressed_data = data - datahat

    # Back to original shape
    return regressed_data.reshape(datashape), non_constant_regressors


def combine_mask_files(mask_files, mask_method=None, mask_index=None):
    """Combines input mask files into a single nibabel image

    A helper function for CompCor

    mask_files: a list
        one or more binary mask files
    mask_method: enum ('union', 'intersect', 'none')
        determines how to combine masks
    mask_index: an integer
        determines which file to return (mutually exclusive with mask_method)

    returns: a list of nibabel images
    """

    if isdefined(mask_index) or not isdefined(mask_method):
        if not isdefined(mask_index):
            if len(mask_files) == 1:
                mask_index = 0
            else:
                raise ValueError(('When more than one mask file is provided, '
                                  'one of merge_method or mask_index must be '
                                  'set'))
        if mask_index < len(mask_files):
            mask = nb.load(mask_files[mask_index], mmap=NUMPY_MMAP)
            return [mask]
        raise ValueError(('mask_index {0} must be less than number of mask '
                          'files {1}').format(mask_index, len(mask_files)))
    masks = []
    if mask_method == 'none':
        for filename in mask_files:
            masks.append(nb.load(filename, mmap=NUMPY_MMAP))
        return masks

    if mask_method == 'union':
        mask = None
        for filename in mask_files:
            img = nb.load(filename, mmap=NUMPY_MMAP)
            if mask is None:
                mask = img.get_data() > 0
            np.logical_or(mask, img.get_data() > 0, mask)
        img = nb.Nifti1Image(mask, img.affine, header=img.header)
        return [img]

    if mask_method == 'intersect':
        mask = None
        for filename in mask_files:
            img = nb.load(filename, mmap=NUMPY_MMAP)
            if mask is None:
                mask = img.get_data() > 0
            np.logical_and(mask, img.get_data() > 0, mask)
        img = nb.Nifti1Image(mask, img.affine, header=img.header)
        return [img]


def compute_noise_components(imgseries, mask_images, num_components,
                             filter_type, degree, period_cut, repetition_time):
    """Compute the noise components from the imgseries for each mask

    imgseries: a nibabel img
    mask_images: a list of nibabel images
    num_components: number of noise components to return
    filter_type: type off filter to apply to time series before computing
                 noise components.
        'polynomial' - Legendre polynomial basis
        'cosine' - Discrete cosine (DCT) basis
        False - None (mean-removal only)

    Filter options:

    degree: order of polynomial used to remove trends from the timeseries
    period_cut: minimum period (in sec) for DCT high-pass filter
    repetition_time: time (in sec) between volume acquisitions

    returns:

    components: a numpy array
    basis: a numpy array containing the (non-constant) filter regressors

    """
    components = None
    basis = np.array([])
    for img in mask_images:
        mask = img.get_data().astype(np.bool)
        if imgseries.shape[:3] != mask.shape:
            raise ValueError(
                'Inputs for CompCor, timeseries and mask, do not have '
                'matching spatial dimensions ({} and {}, respectively)'.format(
                    imgseries.shape[:3], mask.shape))

        voxel_timecourses = imgseries[mask, :]

        # Zero-out any bad values
        voxel_timecourses[np.isnan(np.sum(voxel_timecourses, axis=1)), :] = 0

        # Currently support Legendre-polynomial or cosine or detrending
        # With no filter, the mean is nonetheless removed (poly w/ degree 0)
        if filter_type == 'cosine':
            voxel_timecourses, basis = cosine_filter(
                voxel_timecourses, repetition_time, period_cut)
        elif filter_type in ('polynomial', False):
            # from paper:
            # "The constant and linear trends of the columns in the matrix M were
            # removed [prior to ...]"
            voxel_timecourses, basis = regress_poly(degree, voxel_timecourses)

        # "Voxel time series from the noise ROI (either anatomical or tSTD) were
        # placed in a matrix M of size Nxm, with time along the row dimension
        # and voxels along the column dimension."
        M = voxel_timecourses.T

        # "[... were removed] prior to column-wise variance normalization."
        M = M / _compute_tSTD(M, 1.)

        # "The covariance matrix C = MMT was constructed and decomposed into its
        # principal components using a singular value decomposition."
        u, _, _ = linalg.svd(M, full_matrices=False)
        if components is None:
            components = u[:, :num_components]
        else:
            components = np.hstack((components, u[:, :num_components]))
    if components is None and num_components > 0:
        raise ValueError('No components found')
    return components, basis


def _compute_tSTD(M, x, axis=0):
    stdM = np.std(M, axis=axis)
    # set bad values to x
    stdM[stdM == 0] = x
    stdM[np.isnan(stdM)] = x
    return stdM


# _cosine_drift and _full_rank copied from nipy/modalities/fmri/design_matrix
#
# Nipy release: 0.4.1
# Modified for smooth integration in CompCor classes


def _cosine_drift(period_cut, frametimes):
    """Create a cosine drift matrix with periods greater or equals to period_cut

    Parameters
    ----------
    period_cut: float
         Cut period of the low-pass filter (in sec)
    frametimes: array of shape(nscans)
         The sampling times (in sec)

    Returns
    -------
    cdrift:  array of shape(n_scans, n_drifts)
             cosin drifts plus a constant regressor at cdrift[:,0]

    Ref: http://en.wikipedia.org/wiki/Discrete_cosine_transform DCT-II
    """
    len_tim = len(frametimes)
    n_times = np.arange(len_tim)
    hfcut = 1. / period_cut  # input parameter is the period

    # frametimes.max() should be (len_tim-1)*dt
    dt = frametimes[1] - frametimes[0]
    # hfcut = 1/(2*dt) yields len_time
    # If series is too short, return constant regressor
    order = max(int(np.floor(2 * len_tim * hfcut * dt)), 1)
    cdrift = np.zeros((len_tim, order))
    nfct = np.sqrt(2.0 / len_tim)

    for k in range(1, order):
        cdrift[:, k - 1] = nfct * np.cos(
            (np.pi / len_tim) * (n_times + .5) * k)

    cdrift[:, order - 1] = 1.  # or 1./sqrt(len_tim) to normalize
    return cdrift


def _full_rank(X, cmax=1e15):
    """
    This function possibly adds a scalar matrix to X
    to guarantee that the condition number is smaller than a given threshold.

    Parameters
    ----------
    X: array of shape(nrows, ncols)
    cmax=1.e-15, float tolerance for condition number

    Returns
    -------
    X: array of shape(nrows, ncols) after regularization
    cmax=1.e-15, float tolerance for condition number
    """
    U, s, V = np.linalg.svd(X, 0)
    smax, smin = s.max(), s.min()
    c = smax / smin
    if c < cmax:
        return X, c
    IFLOGGER.warn('Matrix is singular at working precision, regularizing...')
    lda = (smax - cmax * smin) / (cmax - 1)
    s = s + lda
    X = np.dot(U, np.dot(np.diag(s), V))
    return X, cmax
