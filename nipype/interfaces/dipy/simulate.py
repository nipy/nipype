# -*- coding: utf-8 -*-
"""Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)
"""

from nipype.interfaces.base import (
    TraitedSpec, BaseInterface, BaseInterfaceInputSpec, File)
from nipype.utils.filemanip import split_filename
import os.path as op
import nibabel as nb
import numpy as np
from nipype.utils.misc import package_check
import warnings

from ... import logging
iflogger = logging.getLogger('interface')

have_dipy = True
try:
    package_check('dipy', version='0.8.0')
except Exception, e:
    have_dipy = False
else:
    import numpy as np
    from dipy.sims.voxel import (multi_tensor,
                                 all_tensor_evecs)


class SimulateMultiTensorInputSpec(BaseInterfaceInputSpec):
    fibers = InputMultiPath(File(exists=True), mandatory=True,
                            desc='list of fibers principal directions')
    vfractions = File(exists=True, mandatory=True,
                      desc='volume fractions')
    baseline = File(exists=True, mandatory=True, desc='baseline T2 signal')
    gradients = File(exists=True, desc='gradients file')
    bvec = File(exists=True, desc='bvecs file')
    bval = File(exists=True, desc='bvals file')
    out_file = File('sim_dwi.nii.gz', usedefault=True,
                    desc='output file with fractions to be simluated')


class SimulateMultiTensorOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class SimulateMultiTensor(BaseInterface):

    """
    Interface to MultiTensor model simulator in dipy
    http://nipy.org/dipy/examples_built/simulate_multi_tensor.html

    Example
    -------

    >>> import nipype.interfaces.dipy as dipy
    >>> sim = dipy.SimulateMultiTensor()
    >>> sim.inputs.fibers = 'fibers.nii'
    >>> sim.inputs.vfractions = 'fractions.nii'
    >>> sim.inputs.baseline = 'S0.nii'
    >>> sim.inputs.bvecs = 'bvecs'
    >>> sim.inputs.bvals = 'bvals'
    >>> sim.run()                                   # doctest: +SKIP
    """
    input_spec = SimulateMultiTensorInputSpec
    output_spec = SimulateMultiTensorOutputSpec

    def _run_interface(self, runtime):
        # Load the 4D image files
        img = nb.load(self.inputs.fibers)
        fibers = img.get_data()
        fractions = nb.load(self.inputs.vfractions).get_data()
        affine = img.get_affine()

        # Load the baseline b0 signal
        b0 = nb.load(self.inputs.baseline).get_data()

        # Load the gradient strengths and directions
        bvals = np.loadtxt(self.inputs.bvals)
        gradients = np.loadtxt(self.inputs.bvecs).T

        # Place in Dipy's preferred format
        gtab = GradientTable(gradients)
        gtab.bvals = bvals
