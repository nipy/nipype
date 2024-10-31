# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The niftyfit module provide an interface with the niftyfit software
developed in TIG, UCL.

Software available at:
https://cmiclab.cs.ucl.ac.uk/CMIC/NiftyFit-Release

Version used for this version of the interfaces (git):

commit c6232e4c4223c3d19f7a32906409da5af36299a2
Date:   Fri Jan 6 13:34:02 2017 +0000

Examples
--------
See the docstrings of the individual classes for examples.
"""

import os

from ..base import CommandLine
from ...utils.filemanip import split_filename


class NiftyFitCommand(CommandLine):
    """
    Base support interface for NiftyFit commands.
    """

    _suffix = "_nf"

    def __init__(self, **inputs):
        """Init method calling super. No version to be checked."""
        super().__init__(**inputs)

    def _gen_fname(self, basename, out_dir=None, suffix=None, ext=None):
        if basename == "":
            msg = "Unable to generate filename for command %s. " % self.cmd
            msg += "basename is not set!"
            raise ValueError(msg)
        _, final_bn, final_ext = split_filename(basename)
        if out_dir is None:
            out_dir = os.getcwd()
        if ext is not None:
            final_ext = ext
        if suffix is not None:
            final_bn = f"{final_bn}{suffix}"
        return os.path.abspath(os.path.join(out_dir, final_bn + final_ext))
