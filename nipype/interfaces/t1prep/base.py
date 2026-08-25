# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Base classes and shared helpers for the T1Prep interface family.

* :class:`Info`           – T1Prep version detection.
* :class:`T1PrepCommand`  – :class:`CommandLine` base that invokes T1Prep
  sub-modules via ``python -m t1prep.<module>`` using the current Python
  interpreter (resolved lazily, so workflows that switch interpreters keep
  working).
* :func:`import_cat_surf` – import the ``cat_surf`` Python API, preferring
  the ``t1prep.cat_surf`` re-export.
"""

import sys

from ..base import CommandLine, PackageInfo

__docformat__ = "restructuredtext"


class Info(PackageInfo):
    """T1Prep package information.

    Examples
    --------

    >>> from nipype.interfaces.t1prep import Info
    >>> Info.version()  # doctest: +SKIP

    """

    @classmethod
    def version(cls):
        if cls._version is None:
            try:
                import t1prep  # type: ignore
            except ImportError:
                return None
            cls._version = getattr(t1prep, "__version__", None)
        return cls._version

    @staticmethod
    def parse_version(raw_info):
        return raw_info


def import_cat_surf():
    """Import ``cat_surf``, preferring the ``t1prep.cat_surf`` re-export."""
    try:
        from t1prep import cat_surf  # type: ignore
    except ImportError:
        import cat_surf  # type: ignore
    return cat_surf


class T1PrepCommand(CommandLine):
    """Base class for T1Prep command-line interfaces.

    Sub-classes set :attr:`_module` to the dotted name of the T1Prep
    sub-module to invoke (e.g. ``"t1prep.segment"``).  The full command is
    assembled lazily from :data:`sys.executable` so the active interpreter
    is always used, even if it changes after import.
    """

    _module = None
    _cmd = "python"  # placeholder; the real command comes from the cmd property

    @property
    def cmd(self):
        if self._module is None:
            raise NotImplementedError(
                f"{type(self).__name__} must set the _module class attribute."
            )
        return f"{sys.executable} -m {self._module}"

    @property
    def version(self):
        return Info.version()
