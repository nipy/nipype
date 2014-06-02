#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
# @Author: oesteban - code@oscaresteban.es
# @Date:   2014-06-02 12:06:50
# @Last Modified by:   oesteban
# @Last Modified time: 2014-06-02 14:09:50
"""The :py:mod:`nipype.interfaces.elastix` provides the interface to
the elastix registration software.

.. note:: http://elastix.isi.uu.nl/


"""

import os.path as op
import re

from ..base import (CommandLine, CommandLineInputSpec, isdefined,
                    TraitedSpec, File, traits, InputMultiPath)


from ... import logging
logger = logging.getLogger('interface')


class RegistrationInputSpec(CommandLineInputSpec):
    fixed_image = File(exists=True, mandatory=True, argstr='-f %s',
           desc='fixed image')
    moving_image = File(exists=True, mandatory=True, argstr='-m %s',
           desc='moving image')

    output_path = traits.Directory('./', exists=True, mandatory=True, usedefault=True,
                              argstr='-out %s', desc='output directory')

    parameters = InputMultiPath(File(exists=True), mandatory=True, argstr='-p %s...',
                                desc='parameter file, elastix handles 1 or more -p')

    fixed_mask = File(exists=True, argstr='-fMask %s', desc='mask for fixed image')
    moving_mask = File(exists=True, argstr='-mMask %s', desc='mask for moving image')
    initial_transform = File(exists=True, argstr='-t0 %s',
                             desc='parameter file for initial transform')
    num_threads = traits.Int(1, argstr='-threads %01d',
                             desc='set the maximum number of threads of elastix')


class RegistrationOutputSpec(TraitedSpec):
    transform = InputMultiPath(File(exists=True), desc='output transform')
    warped_file = File(desc='input moving image warped to fixed image')
    warped_files = InputMultiPath(File(), desc=('input moving image warped to'
                                  ' fixed image at each level'))
    warped_files_flags = traits.List(traits.Bool(False),
                                    desc='flag indicating if warped image was generated')


class Registration(CommandLine):
    """Elastix nonlinear registration interface

    Example
    -------

    >>> from nipype.interfaces.elastix import Registration
    >>> reg = Registration()
    >>> reg.inputs.fixed_image = 'fixed1.nii'
    >>> reg.inputs.moving_image = 'moving1.nii'
    >>> reg.inputs.parameters = ['elastix.txt']
    >>> reg.cmdline
    'elastix -f fixed1.nii -m moving1.nii -p elastix.txt -out ./'
    """

    _cmd = 'elastix'
    input_spec = RegistrationInputSpec
    output_spec = RegistrationOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()

        out_dir = op.abspath(self.inputs.output_path)

        opts = [ 'WriteResultImage', 'ResultImageFormat' ]
        regex = re.compile(r'^\((\w+)\s(.+)\)$')

        outputs['transform'] = []
        outputs['warped_files'] = []
        outputs['warped_files_flags'] = []

        for i,params in enumerate(self.inputs.parameters):
            config = {}

            with open(params, 'r') as f:
                for line in f.readlines():
                    line = line.strip()
                    if not line.startswith('//') and line:
                        m = regex.search(line)
                        if m:
                            value = self._cast(m.group(2).strip())
                            config[m.group(1).strip()] = value

            outputs['transform'].append(op.join(out_dir,
                                        'TransformParameters.%01d.txt' % i ))

            warped_file = None
            if config['WriteResultImage']:
                warped_file = op.join(out_dir,
                                      'result.%01d.%s' %(i,config['ResultImageFormat']))

            outputs['warped_files'].append(warped_file)
            outputs['warped_files_flags'].append(config['WriteResultImage'])

        if outputs['warped_files_flags'][-1]:
            outputs['warped_file'] = outputs['warped_files'][-1]

        return outputs


    def _cast(self,val):
        if val.startswith('"') and val.endswith('"'):
            if val == '"true"':
                return True
            elif val == '"false"':
                return False
            else:
                return val[1:-1]

        try:
            return int(val)
        except ValueError:
            try:
                return float(val)
            except ValueError:
                return val
