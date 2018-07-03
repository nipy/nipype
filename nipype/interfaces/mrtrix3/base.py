# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# -*- coding: utf-8 -*-
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from ... import logging
from ..base import (CommandLineInputSpec, CommandLine, traits, File, isdefined)
iflogger = logging.getLogger('nipype.interface')


class MRTrix3BaseInputSpec(CommandLineInputSpec):
    nthreads = traits.Int(
        argstr='-nthreads %d',
        desc='number of threads. if zero, the number'
        ' of available cpus will be used',
        nohash=True)
    # DW gradient table import options
    grad_file = File(
        exists=True,
        argstr='-grad %s',
        desc='dw gradient scheme (MRTrix format')
    grad_fsl = traits.Tuple(
        File(exists=True),
        File(exists=True),
        argstr='-fslgrad %s %s',
        desc='(bvecs, bvals) dw gradient scheme (FSL format')
    bval_scale = traits.Enum(
        'yes',
        'no',
        argstr='-bvalue_scaling %s',
        desc='specifies whether the b - values should be scaled by the square'
        ' of the corresponding DW gradient norm, as often required for '
        'multishell or DSI DW acquisition schemes. The default action '
        'can also be set in the MRtrix config file, under the '
        'BValueScaling entry. Valid choices are yes / no, true / '
        'false, 0 / 1 (default: true).')

    in_bvec = File(
        exists=True, argstr='-fslgrad %s %s', desc='bvecs file in FSL format')
    in_bval = File(exists=True, desc='bvals file in FSL format')


class MRTrix3Base(CommandLine):
    def _format_arg(self, name, trait_spec, value):
        if name == 'nthreads' and value == 0:
            value = 1
            try:
                from multiprocessing import cpu_count
                value = cpu_count()
            except:
                iflogger.warn('Number of threads could not be computed')
                pass
            return trait_spec.argstr % value

        if name == 'in_bvec':
            return trait_spec.argstr % (value, self.inputs.in_bval)

        return super(MRTrix3Base, self)._format_arg(name, trait_spec, value)

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []

        try:
            if (isdefined(self.inputs.grad_file)
                    or isdefined(self.inputs.grad_fsl)):
                skip += ['in_bvec', 'in_bval']

            is_bvec = isdefined(self.inputs.in_bvec)
            is_bval = isdefined(self.inputs.in_bval)
            if is_bvec or is_bval:
                if not is_bvec or not is_bval:
                    raise RuntimeError('If using bvecs and bvals inputs, both'
                                       'should be defined')
                skip += ['in_bval']
        except AttributeError:
            pass

        return super(MRTrix3Base, self)._parse_inputs(skip=skip)
