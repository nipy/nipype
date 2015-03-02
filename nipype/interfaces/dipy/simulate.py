# -*- coding: utf-8 -*-
"""Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)
"""

from nipype.interfaces.base import (
    TraitedSpec, BaseInterface, File)
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


class SimulateDWIInputSpec(BaseInterfaceInputSpec):
    fibers = InputMultiPath(File(exists=True), mandatory=True,
                            desc='list of fibers principal directions')
    vfractions = File(exists=True, mandatory=True,
                      desc='volume fractions')
    S0 = File(exists=True, mandatory=True, desc='baseline T2 signal')
    out_file = File('sim_dwi.nii.gz', usedefault=True,
                    desc='output file with fractions to be simluated')
    gradients = File(exists=True, desc='gradients file')
    bvec = File(exists=True, desc='bvecs file')
    bval = File(exists=True, desc='bvals file')
