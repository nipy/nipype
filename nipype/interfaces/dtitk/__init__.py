"""The dtitk module provides classes for interfacing with the `Diffusion
Tensor Imaging Toolkit (DTI-TK)
<http://dti-tk.sourceforge.net/pmwiki/pmwiki.php>`_ command line tools.

Top-level namespace for dti-tk.
"""

# from .base import ()
from .registration import (Rigid, Affine, Diffeo,
                           ComposeXfm, DiffeoSymTensor3DVol, AffSymTensor3DVol,
                           AffScalarVol, DiffeoScalarVol)
from .utils import (TVAdjustVoxSp, SVAdjustVoxSp, TVResample, SVResample,
                    TVtool, BinThresh)
