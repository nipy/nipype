# -*- coding: utf-8 -*-
"""
Neuroimaging tools for Python (NIPY).

The aim of NIPY is to produce a platform-independent Python environment for
the analysis of brain imaging data using an open development model.

The main repository for NIPY is here:
https://launchpad.net/nipy

This repository is mainly focussed on implementing interfaces and pipelines.
Not considered separate from NIPY, it does haveits own release schdule, and 
currently has no reliance on core modules in NIPY (...this will change)

Interfaces

    1. provide interface for using other packages through Python

        a. fsl (fsl 4.0 and above) http://www.fmrib.ox.ac.uk/fsl/

        b. spm (spm5, spm 8) http://www.fil.ion.ucl.ac.uk/spm/

        c. freesurfer

        d. afni
        
    2. pipeline functionality for batch processing data

        a. wrappers to provide common basic interface independent functionality
        (SkullStrip, Coregister, Realign, Warp,...)

        b. engine(s) to use other packages for controlling pipeline
        (networkx, ruffus, etc..)

        c. tools for interfacing databases, repositories

        d. tools for providence tracking, subject specific flags

Package Organization 
==================== 
The nipy package contains the following subpackages and modules: 

.. packagetree:: 
   :style: UML  
"""

from version import version as __version__

__status__   = 'alpha'
__url__     = 'http://nipy.sourceforge.net/'

# We require numpy 1.2 for our test suite.  If Tester fails to import,
# check the version of numpy the user has and inform them they need to
# upgrade.
try:
    #from nipy.testing import Tester
    from numpy.testing import Tester
    test = Tester().test
    bench = Tester().bench
except ImportError:
    # If the user has an older version of numpy which does not have
    # the nose test framework, fail gracefully and prompt them to
    # upgrade.
    import numpy as np
    npver = np.__version__.split('.')
    npver = '.'.join((npver[0], npver[1]))
    npver = float(npver)
    if npver < 1.2:
        raise ImportError('Nipy/nipype requires numpy version 1.2 or greater. '
                          '\n    You have numpy version %s installed.'
                          '\n    Please upgrade numpy:  '
                          'http://www.scipy.org/NumPy' 
                          % np.__version__)


def _test_local_install():
    """ Warn the user that running with nipy being
        imported locally is a bad idea.
    """
    import os
    if os.getcwd() == os.sep.join(
                            os.path.abspath(__file__).split(os.sep)[:-2]):
        import warnings
        warnings.warn('Running the tests from the install directory may '
                     'trigger some failures')

_test_local_install()


# Cleanup namespace
del _test_local_install

# If this file is exec after being imported, the following lines will
# fail
try:
    del version
    del Tester
except:
    pass
