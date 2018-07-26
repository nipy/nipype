# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .denoising import UnbiasedNonLocalMeans
from .featuredetection import (
    GenerateSummedGradientImage, CannySegmentationLevelSetImageFilter,
    DilateImage, TextureFromNoiseImageFilter, FlippedDifference, ErodeImage,
    GenerateBrainClippedImage, NeighborhoodMedian, GenerateTestImage,
    NeighborhoodMean, HammerAttributeCreator, TextureMeasureFilter, DilateMask,
    DumpBinaryTrainingVectors, DistanceMaps, STAPLEAnalysis,
    GradientAnisotropicDiffusionImageFilter, CannyEdge)
