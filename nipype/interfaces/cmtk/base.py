# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
""" Base interface for cmtk """

from ..base import LibraryBaseInterface
from ...utils.misc import package_check


class CFFBaseInterface(LibraryBaseInterface):
    _pkg = "cfflib"


# Originally set in convert, nbs, nx, parcellation
# Set here to be imported, in case anybody depends on its presence
# Remove in 2.0
have_cmp = True
try:
    package_check("cmp")
except ImportError:
    have_cmp = False

have_cfflib = True
try:
    package_check("cfflib")
except ImportError:
    have_cfflib = False

have_cv = True
try:
    package_check("cviewer")
except ImportError:
    have_cv = False
