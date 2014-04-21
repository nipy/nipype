import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.camino as camino
import nipype.interfaces.fsl as fsl
import nipype.interfaces.camino2trackvis as cam2trk
import nipype.algorithms.misc as misc
import os  
from nipype.interfaces.mipav.developer import JistIntensityMp2rageMasking, MedicAlgorithmSPECTRE2010

wf = pe.Workflow("skullstripping")

mask = pe.Node(JistIntensityMp2rageMasking(), name="masking")
mask.inputs.inSecond = "/scr/adenauer1/7T_TRT/pilot/data/OK2T140312_093516.SEPT/nifti/S4_MP2RAGE_5_3_TR5000_iPAT=2_INV2.nii"
mask.inputs.inQuantitative = "/scr/adenauer1/7T_TRT/pilot/data/OK2T140312_093516.SEPT/nifti/S7_MP2RAGE_5_3_TR5000_iPAT=2_UNI_Images.nii"
mask.inputs.inT1weighted = "/scr/adenauer1/7T_TRT/pilot/data/OK2T140312_093516.SEPT/nifti/S6_MP2RAGE_5_3_TR5000_iPAT=2_T1_Images.nii"
mask.inputs.outMasked = True
mask.inputs.outMasked2 = True
mask.inputs.outSignal = True
mask.inputs.outSignal2 = True

skullstrip = pe.Node(MedicAlgorithmSPECTRE2010(), name="skullstrip")
skullstrip.inputs.outStripped = True
skullstrip.inputs.maxMemoryUsage = 6000

wf.connect(mask, 'outMasked', skullstrip, 'inInput')
wf.run()