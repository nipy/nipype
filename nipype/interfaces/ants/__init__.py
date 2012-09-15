# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""Top-level namespace for ants."""

# Registraiton programs
from .ANTS import ANTS
from .antsRegistration import antsRegistration
# deprecated
from .antsIntroduction import antsIntroduction

# Resampling Programs
from .antsApplyTransforms import antsApplyTransforms
from .WarpImageMultiTransform import WarpImageMultiTransform
from .WarpTimeSeriesImageMultiTransform import WarpTimeSeriesImageMultiTransform
# deprecated
from .alternateInterfaceApplyTransforms import ApplyTransforms

# Segmentation Programs
from .Atropos import Atropos
from .N4BiasFieldCorrection import N4BiasFieldCorrection

# Utility Programs
from .AverageAffineTransform import AverageAffineTransform
from .AverageImages import AverageImages
from .MultiplyImages import MultiplyImages

# deprecated
from .buildtemplateparallel import buildtemplateparallel  ## This has many components, but it runs it as a single node
