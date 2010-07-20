# emacs: -*- coding: utf-8; mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set fileencoding=utf-8 ft=python sts=4 ts=4 sw=4 et:
"""
Neuroimaging tools for Python (NIPY).

The aim of NIPY is to produce a platform-independent Python environment for
the analysis of brain imaging data using an open development model.

The main website for NIPY is here:
http://nipy.org/

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

        a. tools to construct hierarchically complex workflows for
        analysis of neuroimaging data

        b. execute workflows in parallel using IPython's parallel
        computing interface
        
        c. tools for interfacing databases, repositories

        d. tools for provenance tracking

Package Organization
====================
The nipy package contains the following subpackages and modules:

.. packagetree::
   :style: UML
"""

from version import version as __version__

__status__   = 'alpha'
__url__     = 'http://nipy.org/'



# We require numpy 1.2 for our test suite.  If Tester fails to import,
# check the version of numpy the user has and inform them they need to
# upgrade.

from nipype.utils.misc import package_check
package_check('numpy', version='1.1')
import numpy as np
from distutils.version import LooseVersion
if LooseVersion(np.__version__) >= '1.2':
    from numpy.testing import Tester
else:
    from testing.numpytesting import Tester

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
    #test.__doc__ = Tester.test.__doc__

test = NipypeTester().test
bench = NipypeTester().bench


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
