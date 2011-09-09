import warnings

from nipype.interfaces.cmtk.cmtk import ROIGen, CreateMatrix
from nipype.utils.misc import package_check

try:
    package_check('cfflib')
    from nipype.interfaces.cmtk.convert import CFFConverter, MergeCNetworks
except Exception, e:
    warnings.warn('cfflib not installed')

