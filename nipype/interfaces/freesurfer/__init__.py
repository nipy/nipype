# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Top-level namespace for freesurfer."""

from .base import Info, FSCommand, no_freesurfer
from .preprocess import (
    ParseDICOMDir, UnpackSDICOMDir, MRIConvert, Resample, ReconAll, BBRegister,
    ApplyVolTransform, Smooth, DICOMConvert, RobustRegister, FitMSParams,
    SynthesizeFLASH, MNIBiasCorrection, WatershedSkullStrip, Normalize,
    CANormalize, CARegister, CALabel, MRIsCALabel, SegmentCC, SegmentWM,
    EditWMwithAseg, ConcatenateLTA)
from .model import (MRISPreproc, MRISPreprocReconAll, GLMFit, OneSampleTTest,
                    Binarize, Concatenate, SegStats, SegStatsReconAll,
                    Label2Vol, MS_LDA, Label2Label, Label2Annot,
                    SphericalAverage)
from .utils import (
    SampleToSurface, SurfaceSmooth, SurfaceTransform, Surface2VolTransform,
    SurfaceSnapshots, ApplyMask, MRIsConvert, MRITessellate, MRIPretess,
    MRIMarchingCubes, SmoothTessellation, MakeAverageSubject,
    ExtractMainComponent, Tkregister2, AddXFormToHeader,
    CheckTalairachAlignment, TalairachAVI, TalairachQC, RemoveNeck, MRIFill,
    MRIsInflate, Sphere, FixTopology, EulerNumber, RemoveIntersection,
    MakeSurfaces, Curvature, CurvatureStats, Jacobian, MRIsCalc, VolumeMask,
    ParcellationStats, Contrast, RelabelHypointensities, Aparc2Aseg, Apas2Aseg,
    MRIsExpand, MRIsCombine)
from .longitudinal import (RobustTemplate, FuseSegmentations)
from .registration import (MPRtoMNI305, RegisterAVItoTalairach, EMRegister,
                           Register, Paint, MRICoreg)
