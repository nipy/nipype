# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import warnings
from nipype.utils.misc import package_check

try:
    package_check('nitime')
    from nipype.interfaces.nitime.analysis import (CoherenceAnalyzerInputSpec,
                                                   CoherenceAnalyzerOutputSpec,
                                                   CoherenceAnalyzer)
except Exception, e:
    warnings.warn('nitime not installed')

