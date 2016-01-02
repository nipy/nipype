
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from copy import deepcopy
import os.path as op
from tempfile import mkdtemp
from shutil import rmtree

from ....testing import (assert_raises, assert_equal,
                         assert_true, assert_false)
from ... import engine as pe
from ....interfaces import base as nib
from ....interfaces import utility as niu


ifresult = None


class SetInputSpec(nib.TraitedSpec):
    val = nib.traits.Int(2, mandatory=True, desc='input')


class SetOutputSpec(nib.TraitedSpec):
    out = nib.traits.Int(desc='ouput')


class SetInterface(nib.BaseInterface):
    input_spec = SetInputSpec
    output_spec = SetOutputSpec
    _always_run = True

    def _run_interface(self, runtime):
        global ifresult
        runtime.returncode = 0
        ifresult = self.inputs.val
        return runtime

    def _list_outputs(self):
        global ifresult
        outputs = self._outputs().get()
        outputs['out'] = self.inputs.val
        return outputs


def test_interfaced_workflow():
    global ifresult

    x = lambda: pe.InterfacedWorkflow(name='ShouldRaise')
    yield assert_raises, ValueError, x
    x = lambda: pe.InterfacedWorkflow(name='ShouldRaise',
                                      input_names=['input0'])
    yield assert_raises, ValueError, x
    x = lambda: pe.InterfacedWorkflow(name='ShouldRaise',
                                      output_names=['output0'])
    yield assert_raises, ValueError, x

    wf = pe.InterfacedWorkflow(
        name='InterfacedWorkflow', input_names=['input0'],
        output_names=['output0'])

    outputs = wf.outputs.get()
    yield assert_equal, outputs, {'output0': None}

    inputs = wf.inputs.get()
    yield assert_equal, inputs, {'input0': None}

    # test connections
    mynode = pe.Node(SetInterface(), name='internalnode')
    wf.connect('in', 'input0', mynode, 'val')
    wf.connect(mynode, 'out', 'out', 'output0')

    wf.inputs.input0 = 5
    wf.run()

    yield assert_equal, ifresult, 5


def _base_workflow(name='InterfacedWorkflow', b=0):
    def _sum(a):
        return a + b + 1

    wf = pe.InterfacedWorkflow(
        name=name, input_names=['input0'],
        output_names=['output0'])
    sum0 = pe.Node(niu.Function(
        input_names=['a'], output_names=['out'], function=_sum),
        name='testnode')
    # test connections
    wf.connect('in', 'input0', sum0, 'a')
    wf.connect(sum0, 'out', 'out', 'output0')
    return wf


def test_graft_workflow():
    global ifresult
    wf1 = _base_workflow('Inner0')
    wf = pe.GraftWorkflow(
        name='GraftWorkflow', fields_from=wf1)
    wf.insert(wf1)
    wf.insert(_base_workflow('Inner1', 2))

    outer = pe.Workflow('OuterWorkflow')
    mynode = pe.Node(SetInterface(), name='internalnode')

    outer.connect([
        (wf, mynode, [('outputnode.out', 'val')])
    ])

    wf.inputs.input0 = 3

    ifresult = None
    wf.run()
    yield assert_equal, ifresult, [4, 6]
