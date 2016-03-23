#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
========================================
sMRI: USing CBS Tools for skullstripping
========================================

This simple workflow uses SPECTRE2010 algorithm to skullstrip an MP2RAGE anatomical scan.
"""


import nipype.pipeline.engine as pe
from nipype.interfaces.mipav.developer import JistIntensityMp2rageMasking, MedicAlgorithmSPECTRE2010

wf = pe.Workflow("skullstripping")

mask = pe.Node(JistIntensityMp2rageMasking(), name="masking")
mask.inputs.inSecond = "/Users/filo/7t_trt/niftis/sub001/session_1/MP2RAGE_INV2.nii.gz"
mask.inputs.inQuantitative = "/Users/filo/7t_trt/niftis/sub001/session_1/MP2RAGE_UNI.nii.gz"
mask.inputs.inT1weighted = "/Users/filo/7t_trt/niftis/sub001/session_1/MP2RAGE_T1.nii.gz"
mask.inputs.outMasked = True
mask.inputs.outMasked2 = True
mask.inputs.outSignal = True
mask.inputs.outSignal2 = True

skullstrip = pe.Node(MedicAlgorithmSPECTRE2010(), name="skullstrip")
skullstrip.inputs.outStripped = True
skullstrip.inputs.xDefaultMem = 6000

wf.connect(mask, 'outMasked', skullstrip, 'inInput')
wf.run()
