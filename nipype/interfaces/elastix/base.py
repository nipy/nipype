# -*- coding: utf-8 -*-
# coding: utf-8
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The :py:mod:`nipype.interfaces.elastix` provides the interface to
the elastix registration software.

.. note:: http://elastix.isi.uu.nl/


"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from ... import logging
from ..base import CommandLineInputSpec, Directory, traits
iflogger = logging.getLogger('nipype.interface')


class ElastixBaseInputSpec(CommandLineInputSpec):
    output_path = Directory(
        './',
        exists=True,
        mandatory=True,
        usedefault=True,
        argstr='-out %s',
        desc='output directory')
    num_threads = traits.Int(
        1, usedefault=True,
        argstr='-threads %01d',
        nohash=True,
        desc='set the maximum number of threads of elastix')
