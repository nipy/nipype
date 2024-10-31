# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Interfaces to run R scripts."""
import os
from shutil import which

from .base import (
    CommandLineInputSpec,
    isdefined,
    CommandLine,
    traits,
    File,
)


def get_r_command():
    if "NIPYPE_NO_R" in os.environ:
        return None
    r_cmd = os.getenv("RCMD", default="R")

    return r_cmd if which(r_cmd) else None


no_r = get_r_command() is None


class RInputSpec(CommandLineInputSpec):
    """Basic expected inputs to R interface"""

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
    >>> r = r.RCommand(rfile=False) # doctest: +SKIP
    >>> r.inputs.script = "Sys.getenv('USER')" # doctest: +SKIP
    >>> out = r.run()  # doctest: +SKIP
    """

    _cmd = get_r_command()
    input_spec = RInputSpec

    def __init__(self, r_cmd=None, **inputs):
        """initializes interface to r
        (default 'R')
        """
        super().__init__(**inputs)
        if r_cmd and isdefined(r_cmd):
            self._cmd = r_cmd

        # For r commands force all output to be returned since r
        # does not have a clean way of notifying an error
        self.terminal_output = "allatonce"

    def set_default_r_cmd(self, r_cmd):
        """Set the default R command line for R classes.

        This method is used to set values for all R
        subclasses.
        """
        self._cmd = r_cmd

    def set_default_rfile(self, rfile):
        """Set the default R script file format for R classes.

        This method is used to set values for all R
        subclasses.
        """
        self._rfile = rfile

    def _run_interface(self, runtime):
        self.terminal_output = "allatonce"
        runtime = super()._run_interface(runtime)
        if "R code threw an exception" in runtime.stderr:
            self.raise_exception(runtime)
        return runtime

    def _format_arg(self, name, trait_spec, value):
        if name in ["script"]:
            argstr = trait_spec.argstr
            return self._gen_r_command(argstr, value)
        return super()._format_arg(name, trait_spec, value)

    def _gen_r_command(self, argstr, script_lines):
        """Generates commands and, if rfile specified, writes it to disk."""
        if not self.inputs.rfile:
            # replace newlines with ;, strip comments
            script = "; ".join(
                [
                    line
                    for line in script_lines.split("\n")
                    if not line.strip().startswith("#")
                ]
            )
            # escape " and $
            script = script.replace('"', '\\"')
            script = script.replace("$", "\\$")
        else:
            script_path = os.path.join(os.getcwd(), self.inputs.script_file)
            with open(script_path, "w") as rfile:
                rfile.write(script_lines)
            script = "source('%s')" % script_path

        return argstr % script
