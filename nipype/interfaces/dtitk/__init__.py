"""The dtitk module provides classes for interfacing with the `Diffusion
Tensor Imaging Toolkit (DTI-TK)
<http://dti-tk.sourceforge.net/pmwiki/pmwiki.php>`_ command line tools.

Top-level namespace for dti-tk.
"""

# from .base import ()
from .registration import (RigidTask, AffineTask, DiffeoTask,
                           ComposeXfmTask, diffeoSymTensor3DVolTask,
                           affSymTensor3DVolTask, affScalarVolTask,
                           diffeoScalarVolTask)
from .utils import (TVAdjustOriginTask, TVAdjustVoxSpTask,
                    SVAdjustVoxSpTask, TVResampleTask, SVResampleTask,
                    TVtoolTask, BinThreshTask)
