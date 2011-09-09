import warnings
from nipype.utils.misc import package_check

try:
    package_check('nipy')
    from model import FitGLM, EstimateContrast
    from preprocess import ComputeMask
except Exception, e:
    warnings.warn('nipy not installed')
