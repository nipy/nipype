"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

Top-level namespace for fsl.  Perhaps should just make fsl a package!
"""

from nipype.interfaces.fsl.base import FSLCommand, Info
from nipype.interfaces.fsl.preprocess import (FAST, FLIRT, ApplyXfm,
                                              BET, MCFLIRT, FNIRT, ApplyWarp,
                                              SliceTimer)
from nipype.interfaces.fsl.model import (Level1Design, FEAT, FEATModel,
                                         FILMGLS, FEATRegister, FLAMEO, ContrastMgr,
                                         L2Model, SMM)
from nipype.interfaces.fsl.utils import (Smooth, Merge, ExtractROI, Split,
                                         ImageMaths, ImageMeants)
from nipype.interfaces.fsl.dti import (EddyCorrect, BEDPOSTX, DTIFit, TBSS2Reg,
                                       TBSS1Preproc, TBSS3Postreg,
                                       TBSS4Prestats, Randomise,
                                       ProbTrackX, VecReg, ProjThresh, FindTheBiggest)
