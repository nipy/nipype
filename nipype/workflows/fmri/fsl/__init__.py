# -*- coding: utf-8 -*-
from .preprocess import (create_susan_smooth, create_fsl_fs_preproc,
                         create_parallelfeat_preproc, create_featreg_preproc,
                         create_reg_workflow)
from .estimate import create_modelfit_workflow, create_fixed_effects_flow

# backwards compatibility
from ...rsfmri.fsl.resting import create_resting_preproc
