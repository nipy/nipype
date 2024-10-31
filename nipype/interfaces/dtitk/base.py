# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The dtitk module provides classes for interfacing with the `DTITK
<http://dti-tk.sourceforge.net/pmwiki/pmwiki.php>`_ command line tools.

These are the base tools for working with DTITK.
Preprocessing tools are found in dtitk/preprocess.py
Registration tools are found in dtitk/registration.py

Currently these tools are supported:

* Rigid Tensor Registration
* Affine Tensor Registration
* Diffeomorphic Tensor Registration
* Combine affiine and diffeomorphic transforms
* Application of transform to tensor and scalar volumes
* Threshold and Binarize
* Adjusting the voxel space of tensor and scalar volumes
* Resampling tensor and scalar volumes
* Calculation of tensor metrics from tensor volume

Examples
--------
See the docstrings of the individual classes for examples.

"""
import os

from ... import logging
from ...utils.filemanip import fname_presuffix
from ..base import CommandLine
from nipype.interfaces.fsl.base import Info
import warnings

LOGGER = logging.getLogger("nipype.interface")


class DTITKRenameMixin:
    def __init__(self, *args, **kwargs):
        classes = [cls.__name__ for cls in self.__class__.mro()]
        dep_name = classes[0]
        rename_idx = classes.index("DTITKRenameMixin")
        new_name = classes[rename_idx + 1]
        warnings.warn(
            "The {} interface has been renamed to {}\n"
            "Please see the documentation for DTI-TK "
            "interfaces, as some inputs have been "
            "added or renamed for clarity."
            "".format(dep_name, new_name),
            DeprecationWarning,
        )
        super().__init__(*args, **kwargs)


class CommandLineDtitk(CommandLine):
    def _gen_fname(self, basename, cwd=None, suffix=None, change_ext=True, ext=None):
        """Generate a filename based on the given parameters.

        The filename will take the form: cwd/basename<suffix><ext>.
        If change_ext is True, it will use the extensions specified in
        <instance>inputs.output_type.

        Parameters
        ----------
        basename : str
            Filename to base the new filename on.
        cwd : str
            Path to prefix to the new filename. (default is os.getcwd())
        suffix : str
            Suffix to add to the `basename`.  (defaults is '' )
        change_ext : bool
            Flag to change the filename extension to the FSL output type.
            (default True)

        Returns
        -------
        fname : str
            New filename based on given parameters.

        """

        if basename == "":
            msg = "Unable to generate filename for command %s. " % self.cmd
            msg += "basename is not set!"
            raise ValueError(msg)
        if cwd is None:
            cwd = os.getcwd()
        if ext is None:
            ext = Info.output_type_to_ext(self.inputs.output_type)
        if change_ext:
            if suffix:
                suffix = f"{suffix}{ext}"
            else:
                suffix = ext
        if suffix is None:
            suffix = ""
        fname = fname_presuffix(basename, suffix=suffix, use_ext=False, newpath=cwd)
        return fname
