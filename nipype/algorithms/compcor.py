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

class CompCorOutputSpec(TraitedSpec):
    components_file = File(exists=True,
                           desc='text file containing the noise components')

class CompCor(BaseInterface):
    '''
    Interface with core CompCor computation, used in aCompCor and tCompCor

    Example
    -------

    >>> ccinterface = CompCor()
    >>> ccinterface.inputs.realigned_file = 'nipype/testing/data/functional.nii'
    >>> ccinterface.inputs.mask_file = 'nipype/testing/data/mask.nii'
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

class TCompCor(CompCor):

    def _run_interface(self, runtime):
        imgseries = nb.load(self.inputs.realigned_file).get_data()
        time_voxels = imgseries.T
        num_voxels = np.prod(time_voxels.shape[1:])

        # From the paper:
        # "For each voxel time series, the temporal standard deviation is
        # defined as the standard deviation of the time series after the removal
        # of low-frequency nuisance terms (e.g., linear and quadratic drift)."

        # "To construct the tSTD noise ROI, we sorted the voxels by their
        # temporal standard deviation ..."
        tSTD = self._compute_tSTD(time_voxels, 0)
        sortSTD = np.sort(tSTD, axis=None) # flattened sorted matrix

        # "... and retained a pre-specified upper fraction of the sorted voxels
        # within each slice ... we chose a 2% threshold"
        threshold = sortSTD[int(num_voxels * .98)]
        mask = tSTD >= threshold
        mask = mask.astype(int)

        # save mask
        mask_file = 'mask.nii'
        nb.nifti1.save(nb.Nifti1Image(mask, np.eye(4)), mask_file)
        self.inputs.mask_file = 'mask.nii'

        super(TCompCor, self)._run_interface(runtime)
        return runtime

ACompCor = CompCor
