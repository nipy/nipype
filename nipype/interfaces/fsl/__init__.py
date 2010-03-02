"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

Top-level namespace for fsl.  Perhaps should just make fsl a package!
"""

from nipype.interfaces.fsl.base import FSLCommand, FSLInfo
from nipype.interfaces.fsl.preprocess import (Bet, Fast, Flirt, ApplyXfm,
                                              McFlirt, Fnirt, ApplyWarp)
from nipype.interfaces.fsl.model import (Level1Design, Feat, FeatModel,
                                         FilmGLS, FixedEffectsModel,
                                         FeatRegister, Flameo, ContrastMgr,
                                         L2Model)
from nipype.interfaces.fsl.utils import (Smooth, Merge, ExtractRoi, Split,
                                         ImageMaths)
from nipype.interfaces.fsl.dti import (EddyCorrect, Bedpostx, Dtifit, Tbss2reg,
                                       Tbss1preproc, Tbss3postreg,
                                       Tbss4prestats, Randomise,
                                       Randomise_parallel, Probtrackx,
                                       Vecreg, ProjThresh, FindTheBiggest)
