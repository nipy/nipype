# -*- coding: utf-8 -*-
"""
Neuroimaging tools for Python (NIPY).

The aim of NIPY is to produce a platform-independent Python environment for
the analysis of brain imaging data using an open development model.

The main website for NIPY is here:
http://nipy.sourceforge.net/

Nipype is the Neuroimaging in Python Pipelines and Interfaces package.
It's aim is to create Python Interfaces to other neuroimaging packages
and create an API for specifying a full analysis pipeline in Python.

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
    from numpy.testing import Tester
    
    class NipypeTester(Tester):
        def test(self, label='fast', verbose=1, extra_argv=None, 
                 doctests=False, coverage=False):
            # setuptools does a chmod +x on ALL python modules when it
            # installs.  By default, as a security measure, nose refuses to
            # import executable files.  To forse nose to execute our tests, we
            # must supply the '--exe' flag.  List thread on this:
            # http://www.mail-archive.com/distutils-sig@python.org/msg05009.html
            if not extra_argv:
                extra_argv = ['--exe']
            else:
                extra_argv.append('--exe')
            super(NipypeTester, self).test(label, verbose, extra_argv, 
                                           doctests, coverage)
        # Grab the docstring from numpy
        test.__doc__ = Tester.test.__doc__

    test = NipypeTester().test
    bench = NipypeTester().bench
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
