# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import os
import functools
from distutils.version import LooseVersion

from .info import (LONG_DESCRIPTION as __doc__, URL as __url__, STATUS as
                   __status__, __version__)
from .utils.config import NipypeConfig
from .utils.logger import Logging
from .refs import due
from .pkg_info import get_pkg_info as _get_pkg_info

try:
    import faulthandler
    faulthandler.enable()
except (ImportError, IOError) as e:
    pass

config = NipypeConfig()
logging = Logging(config)


class NipypeTester(object):
    def __call__(self, doctests=True, parallel=False):
        try:
            import pytest
        except ImportError:
            raise RuntimeError(
                'py.test not installed, run: pip install pytest')
        args = []
        if not doctests:
            args.extend(['-p', 'no:doctest'])
        if parallel:
            try:
                import xdist
            except ImportError:
                raise RuntimeError(
                    "pytest-xdist required for parallel run")
            args.append('-n auto')
        args.append(os.path.dirname(__file__))
        pytest.main(args=args)


test = NipypeTester()


def get_info():
    """Returns package information"""
    return _get_pkg_info(os.path.dirname(__file__))


from .pipeline import Node, MapNode, JoinNode, Workflow
from .interfaces import (DataGrabber, DataSink, SelectFiles, IdentityInterface,
                         Rename, Function, Select, Merge)


@functools.lru_cache()
def check_version(raise_exception=False):
    """Check for the latest version of the library

    parameters:
    raise_exception: boolean
        Raise a RuntimeError if a bad version is being used
    """

    import etelemetry
    logger = logging.getLogger('nipype.utils')

    INIT_MSG = "Running {packname} version {version} (latest: {latest})".format

    latest = {"version": 'Unknown', "bad_versions": []}
    result = None
    try:
        result = etelemetry.get_project("nipy/nipype")
    except Exception as e:
        logger.warning("Could not check for version updates: \n%s", e)
    finally:
        if result:
            latest.update(**result)
            if LooseVersion(__version__) != LooseVersion(latest["version"]):
                logger.info(INIT_MSG(packname='nipype',
                                     version=__version__,
                                     latest=latest["version"]))
            if latest["bad_versions"] and \
                    any([LooseVersion(__version__) == LooseVersion(ver)
                         for ver in latest["bad_versions"]]):
                message = ('You are using a version of Nipype with a critical '
                           'bug. Please use a different version.')
                if raise_exception:
                    raise RuntimeError(message)
                else:
                    logger.critical(message)


# Run telemetry on import for interactive sessions, such as IPython, Jupyter notebooks, Python REPL
if config.getboolean('execution', 'check_version'):
    import __main__
    if not hasattr(__main__, '__file__'):
        check_version()
