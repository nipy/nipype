# -*- coding: utf-8 -*-
"""The bru2nii module provides basic functions for dicom conversion
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import os
from .base import (CommandLine, CommandLineInputSpec, traits, TraitedSpec,
                   isdefined, File, Directory)


class Bru2InputSpec(CommandLineInputSpec):
    input_dir = Directory(
        desc="Input Directory",
        exists=True,
        mandatory=True,
        position=-1,
        argstr="%s")
    actual_size = traits.Bool(
        argstr='-a',
        desc="Keep actual size - otherwise x10 scale so animals match human.")
    force_conversion = traits.Bool(
        argstr='-f',
        desc="Force conversion of localizers images (multiple slice "
        "orientations).")
    append_protocol_name = traits.Bool(
        argstr='-p', desc="Append protocol name to output filename.")
    output_filename = traits.Str(
        argstr="-o %s",
        desc="Output filename ('.nii' will be appended)",
        genfile=True)


class Bru2OutputSpec(TraitedSpec):
    nii_file = File(exists=True)


class Bru2(CommandLine):
    """Uses bru2nii's Bru2 to convert Bruker files

    Examples
    ========

    >>> from nipype.interfaces.bru2nii import Bru2
    >>> converter = Bru2()
    >>> converter.inputs.input_dir = "brukerdir"
    >>> converter.cmdline  # doctest: +ELLIPSIS
    'Bru2 -o .../nipype/testing/data/brukerdir brukerdir'
    """
    input_spec = Bru2InputSpec
    output_spec = Bru2OutputSpec
    _cmd = "Bru2"

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_filename):
            output_filename1 = os.path.abspath(self.inputs.output_filename)
        else:
            output_filename1 = self._gen_filename('output_filename')
        outputs["nii_file"] = output_filename1 + ".nii"
        return outputs

    def _gen_filename(self, name):
        if name == 'output_filename':
            outfile = os.path.join(
                os.getcwd(),
                os.path.basename(os.path.normpath(self.inputs.input_dir)))
            return outfile
