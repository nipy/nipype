#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
# @Author: oesteban - code@oscaresteban.es
# @Date:   2014-06-03 13:42:46
# @Last Modified by:   oesteban
# @Last Modified time: 2014-06-17 10:17:43
"""The :py:mod:`nipype.interfaces.elastix` provides the interface to
the elastix registration software.

.. note:: http://elastix.isi.uu.nl/


"""

from ..base import (CommandLine, CommandLineInputSpec, isdefined,
                    TraitedSpec, File, traits, InputMultiPath)
from ... import logging
logger = logging.getLogger('interface')


class ElastixBaseInputSpec(CommandLineInputSpec):
    output_path = traits.Directory('./', exists=True, mandatory=True, usedefault=True,
                              argstr='-out %s', desc='output directory')
    num_threads = traits.Int(1, argstr='-threads %01d',
                             desc='set the maximum number of threads of elastix')
