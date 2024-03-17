"""
DTI-TK is a spatial normalization and atlas construction toolkit for DTI.

Interfaces for the `Diffusion Tensor Imaging Toolkit (DTI-TK)
<http://dti-tk.sourceforge.net/pmwiki/pmwiki.php>`_ command line tools.

"""

from .registration import (
    Rigid,
    Affine,
    Diffeo,
    ComposeXfm,
    DiffeoSymTensor3DVol,
    AffSymTensor3DVol,
    AffScalarVol,
    DiffeoScalarVol,
)
from .utils import (
    TVAdjustVoxSp,
    SVAdjustVoxSp,
    TVResample,
    SVResample,
    TVtool,
    BinThresh,
)
