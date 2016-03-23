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
from nipype.interfaces.io import SelectFiles
from nipype.interfaces.mipav.developer import JistIntensityMp2rageMasking, MedicAlgorithmSPECTRE2010

wf = pe.Workflow("7t_trt_skullstripping")
wf.base_dir = "/home/filo/workdir"

templates={"INV2": "/data/7t_trt/niftis/{subject_id}/session_1/MP2RAGE_INV2.nii.gz",
           "UNI": "/data/7t_trt/niftis/{subject_id}/session_1/MP2RAGE_UNI.nii.gz",
           "T1": "/data/7t_trt/niftis/{subject_id}/session_1/MP2RAGE_T1.nii.gz"}
datagrabber = pe.Node(SelectFiles(templates), name="dataGrabber")
datagrabber.iterables = ('subject_id', ["sub%03d"% i for i in range(1, 23)])

mask = pe.Node(JistIntensityMp2rageMasking(), name="masking")
mask.inputs.outMasked = True
mask.inputs.outMasked2 = True
mask.inputs.outSignal = True
mask.inputs.outSignal2 = True
mask.inputs.xMaxProcess = 8

wf.connect(datagrabber, 'INV2', mask, 'inSecond')
wf.connect(datagrabber, 'UNI', mask, 'inQuantitative')
wf.connect(datagrabber, 'T1', mask, 'inT1weighted')

skullstrip = pe.Node(MedicAlgorithmSPECTRE2010(), name="skullstrip")
skullstrip.inputs.outStripped = True
skullstrip.inputs.outMask = True
skullstrip.inputs.xDefaultMem = 6000
skullstrip.inputs.xMaxProcess = 8

wf.connect(mask, 'outMasked', skullstrip, 'inInput')
wf.run()
