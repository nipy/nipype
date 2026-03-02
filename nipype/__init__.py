# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Information on specific functions, classes, and methods.

:Release: |version|
:Date: |today|

Top-level module API
--------------------

"""
import os

# No longer used internally but could be used externally.
from looseversion import LooseVersion

from .info import URL as __url__, STATUS as __status__, __version__
from .utils.config import NipypeConfig
from .utils.logger import Logging
from .refs import due
from .pkg_info import get_pkg_info as _get_pkg_info

try:
    import faulthandler

    faulthandler.enable()
except (ImportError, OSError):
    pass

config = NipypeConfig()
logging = Logging(config)


class NipypeTester:
    def __call__(self, doctests=True, parallel=False):
        try:
            import pytest
        except ImportError:
            raise RuntimeError("py.test not installed, run: pip install pytest")
        args = []
        if not doctests:
            args.extend(["-p", "no:doctest"])
        if parallel:
            try:
                import xdist
            except ImportError:
                raise RuntimeError("pytest-xdist required for parallel run")
            args.append("-n auto")
        args.append(os.path.dirname(__file__))
        pytest.main(args=args)


test = NipypeTester()


def get_info():
    """Returns package information"""
    return _get_pkg_info(os.path.dirname(__file__))


from .pipeline import Node, MapNode, JoinNode, Workflow
from .interfaces import (
    DataGrabber,
    DataSink,
    SelectFiles,
    IdentityInterface,
    Rename,
    Function,
    Select,
    Merge,
)


def check_latest_version(raise_exception=False):
    """
    Check for the latest version of the library.

    Parameters
    ----------
    raise_exception: bool
        Raise a RuntimeError if a bad version is being used
    """
    import etelemetry

    logger = logging.getLogger("nipype.utils")
    return etelemetry.check_available_version(
        "nipy/nipype", __version__, logger, raise_exception
    )


# Run telemetry on import for interactive sessions, such as IPython, Jupyter notebooks, Python REPL
if config.getboolean("execution", "check_version"):
    import __main__

    if not hasattr(__main__, "__file__") and "NIPYPE_NO_ET" not in os.environ:
        from .interfaces.base import BaseInterface

        if BaseInterface._etelemetry_version_data is None:
            BaseInterface._etelemetry_version_data = check_latest_version() or "n/a"
