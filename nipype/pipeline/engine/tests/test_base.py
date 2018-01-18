# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import print_function, unicode_literals

import pytest
from ..base import EngineBase
from ....interfaces import base as nib


class InputSpec(nib.TraitedSpec):
    input1 = nib.traits.Int(desc='a random int')
    input2 = nib.traits.Int(desc='a random int')
    input_file = nib.traits.File(desc='Random File')


class OutputSpec(nib.TraitedSpec):
    output1 = nib.traits.List(nib.traits.Int, desc='outputs')


class EngineTestInterface(nib.BaseInterface):
    input_spec = InputSpec
    output_spec = OutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output1'] = [1, self.inputs.input1]
        return outputs


@pytest.mark.parametrize(
    'name', ['valid1', 'valid_node', 'valid-node', 'ValidNode0'])
def test_create(name):
    base = EngineBase(name=name)
    assert base.name == name


@pytest.mark.parametrize(
    'name', ['invalid*1', 'invalid.1', 'invalid@', 'in/valid', None])
def test_create_invalid(name):
    with pytest.raises(ValueError):
        EngineBase(name=name)


def test_hierarchy():
    base = EngineBase(name='nodename')
    base._hierarchy = 'some.history.behind'

    assert base.name == 'nodename'
    assert base.fullname == 'some.history.behind.nodename'


def test_clone():
    base = EngineBase(name='nodename')
    base2 = base.clone('newnodename')

    assert (base.base_dir == base2.base_dir and
            base.config == base2.config and
            base2.name == 'newnodename')

    with pytest.raises(ValueError):
        base.clone('nodename')
