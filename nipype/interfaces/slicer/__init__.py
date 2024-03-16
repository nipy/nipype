"""
3D Slicer is a platform for medical image informatics processing and visualization.

For an EXPERIMENTAL implementation of an interface for the ``3dSlicer`` full framework,
please check `"dynamic" Slicer <nipype.interfaces.dynamic_slicer.html>`__.
"""

from .diffusion import *
from .segmentation import *
from .filtering import *
from .utilities import EMSegmentTransformToNewFormat
from .surface import (
    MergeModels,
    ModelToLabelMap,
    GrayscaleModelMaker,
    ProbeVolumeWithModel,
    LabelMapSmoothing,
    ModelMaker,
)
from .quantification import *
from .legacy import *
from .registration import *
from .converters import DicomToNrrdConverter, OrientScalarVolume
