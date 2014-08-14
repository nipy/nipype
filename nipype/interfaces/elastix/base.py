#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
# @Author: oesteban - code@oscaresteban.es
# @Date:   2014-06-03 13:42:46
# @Last Modified by:   oesteban
# @Last Modified time: 2014-08-14 19:25:37
"""The :py:mod:`nipype.interfaces.elastix` provides the interface to
the elastix registration software.

.. note:: http://elastix.isi.uu.nl/

"""

from nipype.interfaces.base import CommandLineInputSpec, traits
from nipype import logging
logger = logging.getLogger('interface')


class ElastixBaseInputSpec(CommandLineInputSpec):
    num_threads = traits.Int(1, argstr='-threads %01d',
                             desc='set the maximum number of threads of elastix')
    output_path = traits.Str('./', mandatory=True, usedefault=True,
                             argstr='-out %s', desc='output directory')
