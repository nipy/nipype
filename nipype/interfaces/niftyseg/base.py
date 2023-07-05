# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The niftyseg module provides classes for interfacing with `niftyseg
<https://sourceforge.net/projects/niftyseg/>`_ command line tools.
These are the base tools for working with niftyseg.
EM Statistical Segmentation tool is found in niftyseg/em.py
Fill lesions tool is found in niftyseg/lesions.py
Mathematical operation tool is found in niftyseg/maths.py
Patch Match tool is found in niftyseg/patchmatch.py
Statistical operation tool is found in niftyseg/stats.py
Label Fusion and CalcTopNcc tools are in niftyseg/steps.py
Examples
--------
See the docstrings of the individual classes for examples.
"""

from ..niftyfit.base import NiftyFitCommand


class NiftySegCommand(NiftyFitCommand):
    """
    Base support interface for NiftySeg commands.
    """

    _suffix = "_ns"
    _min_version = None

    def __init__(self, **inputs):
        super().__init__(**inputs)

    def get_version(self):
        return super().version_from_command(cmd="seg_EM", flag="--version")
