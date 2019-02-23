# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from ..base import CommandLineInputSpec, CommandLine, TraitedSpec, File


class Vnifti2ImageInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr='-in %s',
        mandatory=True,
        position=1,
        desc='in file')
    attributes = File(
        exists=True, argstr='-attr %s', position=2, desc='attribute file')
    out_file = File(
        name_template="%s.v",
        keep_extension=False,
        argstr='-out %s',
        hash_files=False,
        position=-1,
        desc='output data file',
        name_source=["in_file"])


class Vnifti2ImageOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='Output vista file')


class Vnifti2Image(CommandLine):
    """
    Convert a nifti file into a vista file.

    Example
    -------

    >>> vimage = Vnifti2Image()
    >>> vimage.inputs.in_file = 'image.nii'
    >>> vimage.cmdline
    'vnifti2image -in image.nii -out image.v'
    >>> vimage.run()                                       # doctest: +SKIP
    """

    _cmd = 'vnifti2image'
    input_spec = Vnifti2ImageInputSpec
    output_spec = Vnifti2ImageOutputSpec


class VtoMatInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr='-in %s',
        mandatory=True,
        position=1,
        desc='in file')
    out_file = File(
        name_template="%s.mat",
        keep_extension=False,
        argstr='-out %s',
        hash_files=False,
        position=-1,
        desc='output mat file',
        name_source=["in_file"])


class VtoMatOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='Output mat file')


class VtoMat(CommandLine):
    """
    Convert a nifti file into a vista file.

    Example
    -------

    >>> vimage = VtoMat()
    >>> vimage.inputs.in_file = 'image.v'
    >>> vimage.cmdline
    'vtomat -in image.v -out image.mat'
    >>> vimage.run()                                       # doctest: +SKIP
    """

    _cmd = 'vtomat'
    input_spec = VtoMatInputSpec
    output_spec = VtoMatOutputSpec
