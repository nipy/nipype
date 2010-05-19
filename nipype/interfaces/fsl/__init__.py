"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

Top-level namespace for fsl.  Perhaps should just make fsl a package!
"""

from nipype.interfaces.fsl.base import FSLCommand, Info
from nipype.interfaces.fsl.preprocess import (Fast, Flirt, ApplyXfm,
                                              Bet, McFlirt, Fnirt, ApplyWarp,
                                              SliceTimer)
from nipype.interfaces.fsl.model import (Level1Design, Feat, FeatModel,
                                         FilmGLS, FeatRegister, Flameo, ContrastMgr,
                                         L2Model, SMM)
from nipype.interfaces.fsl.utils import (Smooth, Merge, ExtractRoi, Split,
                                         ImageMaths)
from nipype.interfaces.fsl.dti import (EddyCorrect, Bedpostx, DtiFit, Tbss2Reg,
                                       Tbss1Preproc, Tbss3Postreg,
                                       Tbss4Prestats, Randomise,
                                       Probtrackx, VecReg, ProjThresh, FindTheBiggest)
