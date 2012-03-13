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

# We require numpy 1.2 for our test suite.  If Tester fails to import,
# check the version of numpy the user has and inform them they need to
# upgrade.
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


def check_for_updates():
    from urllib import urlopen
    import re
    devdata = urlopen(('http://www.mit.edu/~satra/nipype-nightly'
                       '/version.html')).read()
    try:
        dev_ver = re.search('Release:</th><td class="field-body">(.*)</td>\n',
                            devdata).groups()[0]
    except AttributeError:
        dev_ver = 'unknown'

    devdata = urlopen(('http://nipy.org/nipype/version.html')).read()
    try:
        rel_ver = re.search('Release:</th><td class="field-body">(.*)</td>\n',
                            devdata).groups()[0]
    except AttributeError:
        rel_ver = 'unknown'
    print "Installed version: %s" % __version__
    print "Current stable version: %s" % rel_ver
    print "Current dev version: %s" % dev_ver

if int(config.get('check', 'interval')) > 0:
    from time import time
    t = time()
    last_check = config.get_data('last_check')
    if last_check is None or (t - last_check) > int(config.get('check',
                                                               'interval')):
        try:
            check_for_updates()
        except Exception, e:
            print e
        finally:
            config.save_data('last_check', t)
