# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

from info import (LONG_DESCRIPTION as __doc__,
                  URL as __url__,
                  STATUS as __status__,
                  __version__)
from utils.config import NipypeConfig
config = NipypeConfig()
from utils.logger import Logging
logging = Logging(config)

from distutils.version import LooseVersion

from .fixes.numpy.testing import nosetester

class _NoseTester(nosetester.NoseTester):
    """ Subclass numpy's NoseTester to add doctests by default
    """

    def _get_custom_doctester(self):
        return None

    def test(self, label='fast', verbose=1, extra_argv=['--exe'],
             doctests=True, coverage=False):
        """Run the full test suite

        Examples
        --------
        This will run the test suite and stop at the first failing
        example
        >>> from nipype import test
        >>> test(extra_argv=['--exe', '-sx']) #doctest: +SKIP
        """
        return super(_NoseTester, self).test(label=label,
                                             verbose=verbose,
                                             extra_argv=extra_argv,
                                             doctests=doctests,
                                             coverage=coverage)

try:
    test = _NoseTester(raise_warnings="release").test
except TypeError:
    # Older versions of numpy do not have a raise_warnings argument
    test = _NoseTester().test
del nosetester


def _test_local_install():
    """ Warn the user that running with nipy being
        imported locally is a bad idea.
    """
    if os.getcwd() == os.sep.join(
                            os.path.abspath(__file__).split(os.sep)[:-2]):
        import warnings
        warnings.warn('Running the tests from the install directory may '
                     'trigger some failures')

_test_local_install()

# Set up package information function
from pkg_info import get_pkg_info as _get_pkg_info
get_info = lambda: _get_pkg_info(os.path.dirname(__file__))

# Cleanup namespace
del _test_local_install

# If this file is exec after being imported, the following lines will
# fail
try:
    del Tester
except:
    pass


from pipeline import Node, MapNode, JoinNode, Workflow
from interfaces import (fsl, spm, freesurfer, afni, ants, slicer, dipy, nipy,
                        mrtrix, camino, DataGrabber, DataSink, SelectFiles,
                        IdentityInterface, Rename, Function, Select, Merge)
