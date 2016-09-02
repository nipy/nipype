from __future__ import division
from builtins import range
from numpy import ones, kron, mean, eye, hstack, dot, tile
from scipy.linalg import pinv
from ..interfaces.base import BaseInterfaceInputSpec, TraitedSpec, \
    BaseInterface, traits, File
import nibabel as nb
import numpy as np
import os

from nipype.pipeline.engine import Workflow

class CompCoreInputSpec(BaseInterfaceInputSpec):
    realigned_file = File(exists=True, mandatory=True, desc='already realigned brain image')
    mask_file = File(exists=True, mandatory=True, desc='mask file that determines ROI')
    num_components = traits.Int(default=6, usedefault=True) # 6 for BOLD, 4 for ASL
    # additional_regressors??

class CompCoreOutputSpec(TraitedSpec):
    components_file = File(desc='text file containing the noise components')

class CompCore(BaseInterface):
    '''
    Node with core CompCor computation, used in aCompCor and tCompCor

    Example
    -------

    >>> ccinterface = CompCore()
    >>> ccinterface.inputs.realigned_file = '../../testing/data/functional.nii'
    >>> ccinterface.inputs.mask_file = '../../testing/data/mask.nii'
    >>> ccinterface.inputs.num_components = 1

    '''
    input_spec = CompCoreInputSpec
    output_spec = CompCoreOutputSpec

    def _run_interface(self, runtime):
        imgseries = nb.load(self.inputs.realigned_file)
        components = None
        mask = nb.load(self.inputs.realigned_file, self.inputs.mask_file).get_data()
        
        voxel_timecourses = imgseries.get_data()[mask > 0]
        voxel_timecourses[np.isnan(np.sum(voxel_timecourses, axis=1)), :] = 0
        # remove mean and normalize by variance
        # voxel_timecourses.shape == [nvoxels, time]
        X = voxel_timecourses.T
        stdX = np.std(X, axis=0)
        stdX[stdX == 0] = 1.
        stdX[np.isnan(stdX)] = 1.
        stdX[np.isinf(stdX)] = 1.
        X = (X - np.mean(X, axis=0)) / stdX
        u, _, _ = sp.linalg.svd(X, full_matrices=False)
        if components is None:
            components = u[:, :self.inputs.num_components]
        else:
            components = np.hstack((components, u[:, :self.inputs.num_components]))

        components_file = os.path.join(os.getcwd(), 'noise_components.txt')
        np.savetxt(components_file, components, fmt="%.10f")
        return runtime

class aCompCor(Workflow):
    pass

class tCompCor(Workflow):
    pass
