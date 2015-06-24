# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Top-level namespace for freesurfer."""

from .base import Info, FSCommand
from .preprocess import (ParseDICOMDir, UnpackSDICOMDir, MRIConvert, Resample,
                         ReconAll, BBRegister, ApplyVolTransform,Smooth,
                         DICOMConvert, RobustRegister, FitMSParams,
                         SynthesizeFLASH, MNIBiasCorrection, Normalize, EditWMwithAseg,
                         SegmentWM, SegmentCC, CALabel, CARegister, CANormalize,
                         MRIsCALabel)
from .model import (MRISPreproc, GLMFit, OneSampleTTest, Binarize, Concatenate,
                    SegStats, Label2Vol, MS_LDA)
from .utils import (SampleToSurface, SurfaceSmooth, SurfaceTransform, Surface2VolTransform,
                    SurfaceSnapshots, ApplyMask, MRIsConvert, MRITessellate, MRIPretess,
                    MRIMarchingCubes, SmoothTessellation, MakeAverageSubject, TalairachQC,
                    ExtractMainComponent, Tkregister2, AddXFormToHeader, CheckTalairachAlignment,
                    RemoveNeck, CurvatureStats, Curvature, MRIsInflate, MakeSurfaces,
                    RemoveIntersection, EulerNumber, FixTopology, Sphere, ExtractMainComponent,
                    MRIFill, Jacobian, MRIsCalc)

from .longitudinal import RobustTemplate

from .registration import (MPRtoMNI305, RegisterAVItoTalairach, EMRegister, Register, Paint)
