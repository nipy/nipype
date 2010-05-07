"""The afni module provides classes for interfacing with the `AFNI
<http://www.fmrib.ox.ac.uk/afni/index.html>`_ command line tools.  This
was written to work with AFNI version 4.1.4.

Top-level namespace for afni.  Perhaps should just make afni a package!
"""

from nipype.interfaces.afni.base import Info, AFNICommand, AFNITraitedSpec
#from nipype.interfaces.afni.preprocess import (Fast, Flirt, ApplyXfm,
                                              #Bet, McFlirt, Fnirt, ApplyWarp)
#from nipype.interfaces.afni.model import (Level1Design, Feat, FeatModel,
                                         #FilmGLS, FixedEffectsModel,
                                         #FeatRegister, Flameo, ContrastMgr,
                                         #L2Model)
#from nipype.interfaces.afni.utils import (Smooth, Merge, ExtractRoi, Split,
                                         #ImageMaths)
#from nipype.interfaces.afni.dti import (Eddycorrect, Bedpostx, Dtifit, Tbss2reg,
                                       #Tbss1preproc, Tbss3postreg,
                                       #Tbss4prestats, Randomise,
                                       #Probtrackx,Vecreg, ProjThresh, FindTheBiggest)
