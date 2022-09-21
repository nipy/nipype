# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provide a base interface to AFNI commands."""
import os
from sys import platform
import shutil

from ... import logging, LooseVersion
from ...utils.filemanip import split_filename, fname_presuffix
from ..base import (
    CommandLine,
    traits,
    CommandLineInputSpec,
    isdefined,
    File,
    TraitedSpec,
    PackageInfo,
)
from ...external.due import BibTeX

# Use nipype's logging system
IFLOGGER = logging.getLogger("nipype.interface")


class Info(PackageInfo):
    """Handle afni output type and version information."""

    __outputtype = "AFNI"
    ftypes = {"NIFTI": ".nii", "AFNI": "", "NIFTI_GZ": ".nii.gz"}
    version_cmd = "afni --version"

    @staticmethod
    def parse_version(raw_info):
        """Check and parse AFNI's version."""
        version_stamp = raw_info.split("\n")[0].split("Version ")[1]
        if version_stamp.startswith("AFNI"):
            version_stamp = version_stamp.split("AFNI_")[1]
        elif version_stamp.startswith("Debian"):
            version_stamp = version_stamp.split("Debian-")[1].split("~")[0]
        else:
            return None

        version = LooseVersion(version_stamp.replace("_", ".")).version[:3]
        if version[0] < 1000:
            version[0] = version[0] + 2000
        return tuple(version)

    @classmethod
    def output_type_to_ext(cls, outputtype):
        """
        Get the file extension for the given output type.

        Parameters
        ----------
        outputtype : {'NIFTI', 'NIFTI_GZ', 'AFNI'}
            String specifying the output type.

        Returns
        -------
        extension : str
            The file extension for the output type.

        """
        try:
            return cls.ftypes[outputtype]
        except KeyError as e:
            msg = "Invalid AFNIOUTPUTTYPE: ", outputtype
            raise KeyError(msg) from e

    @classmethod
    def outputtype(cls):
        """
        Set default output filetype.

        AFNI has no environment variables, Output filetypes get set in command line calls
        Nipype uses ``AFNI`` as default


        Returns
        -------
        None

        """
        return "AFNI"

    @staticmethod
    def standard_image(img_name):
        """
        Grab an image from the standard location.

        Could be made more fancy to allow for more relocatability

        """
        clout = CommandLine(
            "which afni",
            ignore_exception=True,
            resource_monitor=False,
            terminal_output="allatonce",
        ).run()
        if clout.runtime.returncode != 0:
            return None

        out = clout.runtime.stdout
        basedir = os.path.split(out)[0]
        return os.path.join(basedir, img_name)


class AFNICommandBase(CommandLine):
    """
    A base class to fix a linking problem in OSX and AFNI.

    See Also
    --------
    `This thread
    <http://afni.nimh.nih.gov/afni/community/board/read.php?1,145346,145347#msg-145347>`__
    about the particular environment variable that fixes this problem.

    """

    def _run_interface(self, runtime, correct_return_codes=(0,)):
        if platform == "darwin":
            runtime.environ["DYLD_FALLBACK_LIBRARY_PATH"] = "/usr/local/afni/"
        return super(AFNICommandBase, self)._run_interface(
            runtime, correct_return_codes
        )


class AFNICommandInputSpec(CommandLineInputSpec):
    num_threads = traits.Int(
        1, usedefault=True, nohash=True, desc="set number of threads"
    )
    outputtype = traits.Enum(
        "AFNI", list(Info.ftypes.keys()), desc="AFNI output filetype"
    )
    out_file = File(
        name_template="%s_afni",
        desc="output image file name",
        argstr="-prefix %s",
        name_source=["in_file"],
    )


class AFNICommandOutputSpec(TraitedSpec):
    out_file = File(desc="output file", exists=True)


class AFNICommand(AFNICommandBase):
    """Shared options for several AFNI commands."""

    input_spec = AFNICommandInputSpec
    _outputtype = None

    _references = [
        {
            "entry": BibTeX(
                "@article{Cox1996,"
                "author={R.W. Cox},"
                "title={AFNI: software for analysis and "
                "visualization of functional magnetic "
                "resonance neuroimages},"
                "journal={Computers and Biomedical research},"
                "volume={29},"
                "number={3},"
                "pages={162-173},"
                "year={1996},"
                "}"
            ),
            "tags": ["implementation"],
        },
        {
            "entry": BibTeX(
                "@article{CoxHyde1997,"
                "author={R.W. Cox and J.S. Hyde},"
                "title={Software tools for analysis and "
                "visualization of fMRI data},"
                "journal={NMR in Biomedicine},"
                "volume={10},"
                "number={45},"
                "pages={171-178},"
                "year={1997},"
                "}"
            ),
            "tags": ["implementation"],
        },
    ]

    @property
    def num_threads(self):
        """Get number of threads."""
        return self.inputs.num_threads

    @num_threads.setter
    def num_threads(self, value):
        self.inputs.num_threads = value

    @classmethod
    def set_default_output_type(cls, outputtype):
        """
        Set the default output type for AFNI classes.

        This method is used to set the default output type for all afni
        subclasses.  However, setting this will not update the output
        type for any existing instances.  For these, assign the
        <instance>.inputs.outputtype.
        """
        if outputtype in Info.ftypes:
            cls._outputtype = outputtype
        else:
            raise AttributeError("Invalid AFNI outputtype: %s" % outputtype)

    def __init__(self, **inputs):
        """Instantiate an AFNI command tool wrapper."""
        super(AFNICommand, self).__init__(**inputs)
        self.inputs.on_trait_change(self._output_update, "outputtype")

        if hasattr(self.inputs, "num_threads"):
            self.inputs.on_trait_change(self._nthreads_update, "num_threads")

        if self._outputtype is None:
            self._outputtype = Info.outputtype()

        if not isdefined(self.inputs.outputtype):
            self.inputs.outputtype = self._outputtype
        else:
            self._output_update()

    def _nthreads_update(self):
        """Update environment with new number of threads."""
        self.inputs.environ["OMP_NUM_THREADS"] = "%d" % self.inputs.num_threads

    def _output_update(self):
        """
        Update the internal property with the provided input.

        i think? updates class private attribute based on instance input
        in fsl also updates ENVIRON variable....not valid in afni
        as it uses no environment variables
        """
        self._outputtype = self.inputs.outputtype

    def _overload_extension(self, value, name=None):
        path, base, _ = split_filename(value)
        return os.path.join(
            path, base + Info.output_type_to_ext(self.inputs.outputtype)
        )

    def _list_outputs(self):
        outputs = super(AFNICommand, self)._list_outputs()
        metadata = dict(name_source=lambda t: t is not None)
        out_names = list(self.inputs.traits(**metadata).keys())
        if out_names:
            for name in out_names:
                if outputs[name]:
                    _, _, ext = split_filename(outputs[name])
                    if ext == "":
                        outputs[name] = outputs[name] + "+orig.BRIK"
        return outputs

    def _gen_fname(self, basename, cwd=None, suffix=None, change_ext=True, ext=None):
        """
        Generate a filename based on the given parameters.

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
        if not basename:
            msg = "Unable to generate filename for command %s. " % self.cmd
            msg += "basename is not set!"
            raise ValueError(msg)

        if cwd is None:
            cwd = os.getcwd()
        if ext is None:
            ext = Info.output_type_to_ext(self.inputs.outputtype)
        if change_ext:
            suffix = "".join((suffix, ext)) if suffix else ext

        if suffix is None:
            suffix = ""
        fname = fname_presuffix(basename, suffix=suffix, use_ext=False, newpath=cwd)
        return fname


class AFNIPythonCommandInputSpec(CommandLineInputSpec):
    outputtype = traits.Enum(
        "AFNI", list(Info.ftypes.keys()), desc="AFNI output filetype"
    )
    py27_path = traits.Either(
        "python2", File(exists=True), usedefault=True, default="python2"
    )


class AFNIPythonCommand(AFNICommand):
    """A subtype of AFNI command line for Python scripts."""

    @property
    def cmd(self):
        """Revise the command path."""
        orig_cmd = super(AFNIPythonCommand, self).cmd
        found = shutil.which(orig_cmd)
        return found if found is not None else orig_cmd

    @property
    def _cmd_prefix(self):
        return "{} ".format(self.inputs.py27_path)


def no_afni():
    """Check whether AFNI is not available."""
    if Info.version() is None:
        return True
    return False
