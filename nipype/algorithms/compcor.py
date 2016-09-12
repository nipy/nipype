# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Miscellaneous algorithms

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname(os.path.realpath(__file__))
    >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
    >>> os.chdir(datadir)

'''
from ..interfaces.base import (BaseInterfaceInputSpec, TraitedSpec,
                               BaseInterface, traits, File)
from ..pipeline import engine as pe
from ..interfaces.utility import IdentityInterface
from .misc import regress_poly

import nibabel as nb
import numpy as np
from scipy import linalg, stats
import os

class CompCorInputSpec(BaseInterfaceInputSpec):
    realigned_file = File(exists=True, mandatory=True,
                          desc='already realigned brain image (4D)')
    mask_file = File(exists=True, mandatory=False,
                     desc='mask file that determines ROI (3D)')
    components_file = File('components_file.txt', exists=False,
                           mandatory=False, usedefault=True,
                           desc='filename to store physiological components')
    num_components = traits.Int(6, usedefault=True) # 6 for BOLD, 4 for ASL
    use_regress_poly = traits.Bool(True, usedefault=True,
                                   desc='use polynomial regression'
                                   'pre-component extraction')
    regress_poly_degree = traits.Range(low=1, default=1, usedefault=True,
                                       desc='the degree polynomial to use')
    extra_regressors = File(exists=True, mandatory=False,
                            desc='additional regressors to add')

class CompCorOutputSpec(TraitedSpec):
    components_file = File(exists=True,
                           desc='text file containing the noise components')

class CompCor(BaseInterface):
    '''
    Interface with core CompCor computation, used in aCompCor and tCompCor

    Example
    -------

    >>> ccinterface = CompCor()
    >>> ccinterface.inputs.realigned_file = 'functional.nii'
    >>> ccinterface.inputs.mask_file = 'mask.nii'
    >>> ccinterface.inputs.num_components = 1
    >>> ccinterface.inputs.use_regress_poly = True
    >>> ccinterface.inputs.regress_poly_degree = 2
    '''
    input_spec = CompCorInputSpec
    output_spec = CompCorOutputSpec

    def _run_interface(self, runtime):
        imgseries = nb.load(self.inputs.realigned_file).get_data()
        mask = nb.load(self.inputs.mask_file).get_data()
        voxel_timecourses = imgseries[mask > 0]
        # Zero-out any bad values
        voxel_timecourses[np.isnan(np.sum(voxel_timecourses, axis=1)), :] = 0

        # from paper:
        # "The constant and linear trends of the columns in the matrix M were
        # removed [prior to ...]"
        if self.inputs.use_regress_poly:
            voxel_timecourses = regress_poly(self.inputs.regress_poly_degree,
                                             voxel_timecourses)
        voxel_timecourses = voxel_timecourses - np.mean(voxel_timecourses,
                                                        axis=1)[:, np.newaxis]

        # "Voxel time series from the noise ROI (either anatomical or tSTD) were
        # placed in a matrix M of size Nxm, with time along the row dimension
        # and voxels along the column dimension."
        M = voxel_timecourses.T
        numvols = M.shape[0]
        numvoxels = M.shape[1]

        # "[... were removed] prior to column-wise variance normalization."
        M = M / self._compute_tSTD(M, 1.)

        # "The covariance matrix C = MMT was constructed and decomposed into its
        # principal components using a singular value decomposition."
        u, _, _ = linalg.svd(M, full_matrices=False)
        components = u[:, :self.inputs.num_components]
        if self.inputs.extra_regressors:
            components = self._add_extras(components,
                                          self.inputs.extra_regressors)

        components_file = os.path.join(os.getcwd(), self.inputs.components_file)
        np.savetxt(components_file, components, fmt="%.10f")
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['components_file'] = os.path.abspath(self.inputs.components_file)
        return outputs

    def _compute_tSTD(self, M, x):
        stdM = np.std(M, axis=0)
        # set bad values to x
        stdM[stdM == 0] = x
        stdM[np.isnan(stdM)] = x
        stdM[np.isinf(stdM)] = x
        return stdM

    def _add_extras(self, components, extra_regressors):
            regressors = np.genfromtxt(self.inputs.extra_regressors)
            return np.hstack((components, regressors))

class TCompCorInputSpec(CompCorInputSpec):
    # and all the fields in CompCorInputSpec
    percentile_threshold = traits.Range(low=0., high=1., value=.02,
                                        exclude_low=True, exclude_high=True,
                                        usedefault=True, desc='the percentile '
                                        'used to select highest-variance '
                                        'voxels. By default the 2% of voxels '
                                        'with the highest variance are used.')

class TCompCor(CompCor):
    '''
    Interface for tCompCor. Computes a ROI mask based on variance of voxels.

    Example
    -------

    >>> ccinterface = TCompCor()
    >>> ccinterface.inputs.realigned_file = 'functional.nii'
    >>> ccinterface.inputs.mask_file = 'mask.nii'
    >>> ccinterface.inputs.num_components = 1
    >>> ccinterface.inputs.use_regress_poly = True
    >>> ccinterface.inputs.regress_poly_degree = 2
    >>> ccinterface.inputs.percentile_threshold = .03
    '''

    input_spec = TCompCorInputSpec
    output_spec = CompCorOutputSpec

    def _run_interface(self, runtime):
        imgseries = nb.load(self.inputs.realigned_file).get_data()

        # From the paper:
        # "For each voxel time series, the temporal standard deviation is
        # defined as the standard deviation of the time series after the removal
        # of low-frequency nuisance terms (e.g., linear and quadratic drift)."
        imgseries = regress_poly(2, imgseries)
        imgseries = imgseries - np.mean(imgseries, axis=1)[:, np.newaxis]

        time_voxels = imgseries.T
        num_voxels = np.prod(time_voxels.shape[1:])

        # "To construct the tSTD noise ROI, we sorted the voxels by their
        # temporal standard deviation ..."
        tSTD = self._compute_tSTD(time_voxels, 0)
        sortSTD = np.sort(tSTD, axis=None) # flattened sorted matrix

        # use percentile_threshold to pick voxels
        threshold_index = int(num_voxels * (1. - self.inputs.percentile_threshold))
        threshold_std = sortSTD[threshold_index]
        mask = tSTD >= threshold_std
        mask = mask.astype(int)

        # save mask
        mask_file = 'mask.nii'
        nb.nifti1.save(nb.Nifti1Image(mask, np.eye(4)), mask_file)
        self.inputs.mask_file = mask_file

        super(TCompCor, self)._run_interface(runtime)
        return runtime

ACompCor = CompCor
