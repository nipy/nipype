# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Interfaces to run R scripts."""
import os

from .. import config
from .base import (
    CommandLineInputSpec,
    InputMultiPath,
    isdefined,
    CommandLine,
    traits,
    File,
    Directory,
)


def get_r_command():
    if "NIPYPE_NO_R" in os.environ:
        return None
    try:
        r_cmd = os.environ["RCMD"]
    except:
        r_cmd = "R"
    return r_cmd


no_r = get_r_command() is None


class RInputSpec(CommandLineInputSpec):
    """ Basic expected inputs to R interface """

    script = traits.Str(
        argstr='-e "%s"', desc="R code to run", mandatory=True, position=-1
    )
    # non-commandline options
    rfile = traits.Bool(True, desc="Run R using R script", usedefault=True)
    script_file = File(
        "pyscript.R", usedefault=True, desc="Name of file to write R code to"
    )
    

class RCommand(CommandLine):
    """Interface that runs R code

    >>> import nipype.interfaces.r as r
    >>> r = r.RCommand(rfile=False)  # don't write script file
    >>> r.inputs.script = "Sys.getenv('USER')"
    >>> out = r.run()  # doctest: +SKIP
    """

    _cmd = "R"
    _default_r_cmd = None
    _default_rfile = None
    input_spec = RInputSpec

    def __init__(self, r_cmd=None, **inputs):
        """initializes interface to r
        (default 'R')
        """
        super(RCommand, self).__init__(**inputs)
        if r_cmd and isdefined(r_cmd):
            self._cmd = r_cmd
        elif self._default_r_cmd:
            self._cmd = self._default_r_cmd

        if self._default_rfile and not isdefined(self.inputs.rfile):
            self.inputs.rfile = self._default_rfile

        # For r commands force all output to be returned since r
        # does not have a clean way of notifying an error
        self.terminal_output = "allatonce"

    @classmethod
    def set_default_r_cmd(cls, r_cmd):
        """Set the default R command line for R classes.

        This method is used to set values for all R
        subclasses.  However, setting this will not update the output
        type for any existing instances.  For these, assign the
        <instance>.inputs.r_cmd.
        """
        cls._default_r_cmd = r_cmd

    @classmethod
    def set_default_rfile(cls, rfile):
        """Set the default R script file format for R classes.

        This method is used to set values for all R
        subclasses.  However, setting this will not update the output
        type for any existing instances.  For these, assign the
        <instance>.inputs.rfile.
        """
        cls._default_rfile = rfile

    def _run_interface(self, runtime):
        self.terminal_output = "allatonce"
        runtime = super(RCommand, self)._run_interface(runtime)
        if "R code threw an exception" in runtime.stderr:
            self.raise_exception(runtime)
        return runtime

    def _format_arg(self, name, trait_spec, value):
        if name in ["script"]:
            argstr = trait_spec.argstr
            return self._gen_r_command(argstr, value)
        return super(RCommand, self)._format_arg(name, trait_spec, value)

    def _gen_r_command(self, argstr, script_lines):
        """ Generates commands and, if rfile specified, writes it to disk."""
        if not self.inputs.rfile:
            # replace newlines with ;, strip comments
            script = "; ".join([
                        line
                        for line in script_lines.split("\n")
                        if not line.strip().startswith("#")
                    ])
            # escape " and $
            script = script.replace('"','\\"')
            script = script.replace('$','\\$')
        else:
            script_path = os.path.join(os.getcwd(), self.inputs.script_file)
            with open(script_path, "wt") as rfile:
                rfile.write(script_lines)
            script = "source('%s')" % script_path

        return argstr % script
