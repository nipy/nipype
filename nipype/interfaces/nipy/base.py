# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Base interface for nipy"""

from ..base import LibraryBaseInterface
from ...utils.misc import package_check

# Originally set in model, preprocess and utils
# Set here to be imported, in case anybody depends on its presence
# Remove in 2.0
have_nipy = True
try:
    package_check("nipy")
except:
    have_nipy = False


class NipyBaseInterface(LibraryBaseInterface):
    _pkg = "nipy"
