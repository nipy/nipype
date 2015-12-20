#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.testing import (assert_raises, assert_equal,
                            assert_true, assert_false)
from nipype.interfaces import base as nib
from nipype.interfaces import utility as niu
from nipype.interfaces import io as nio
from nipype.pipeline import engine as pe
from copy import deepcopy
import os.path as op
from tempfile import mkdtemp
from shutil import rmtree
import json


ifresult = None


class SetInputSpec(nib.TraitedSpec):
    val = nib.traits.Int(2, mandatory=True, desc='input')


class SetOutputSpec(nib.TraitedSpec):
    out = nib.traits.Int(desc='ouput')


class SetInterface(nib.BaseInterface):
    input_spec = SetInputSpec
    output_spec = SetOutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        global ifresult
        outputs = self._outputs().get()
        ifresult = outputs['out'] = self.inputs.val
        return outputs


def _base_workflow():

    def _myfunc(val):
        return val + 1

    wf = pe.Workflow('InnerWorkflow')
    inputnode = pe.Node(niu.IdentityInterface(
                        fields=['in_value']), 'inputnode')
    outputnode = pe.Node(niu.IdentityInterface(
                         fields=['out_value']), 'outputnode')
    func = pe.Node(niu.Function(
        input_names=['val'], output_names=['out'],
        function=_myfunc), 'Function')
    ifset = pe.Node(SetInterface(), 'SetIface')

    wf.connect([
        (inputnode, func, [('in_value', 'val')]),
        (func, ifset, [('out', 'val')]),
        (ifset, outputnode, [('out', 'out_value')])
    ])
    return wf


def _base_cachedworkflow():

    def _myfunc(a, b):
        return a + b

    wf = pe.CachedWorkflow('InnerWorkflow',
                           cache_map=('c', 'out'))

    inputnode = pe.Node(niu.IdentityInterface(
                        fields=['a', 'b']), 'inputnode')
    func = pe.Node(niu.Function(
        input_names=['a', 'b'], output_names=['out'],
        function=_myfunc), 'Function')
    ifset = pe.Node(SetInterface(), 'SetIface')

    wf.connect([
        (inputnode, func, [('a', 'a'), ('b', 'b')]),
        (func, ifset, [('out', 'val')]),
        (ifset, 'output', [('out', 'out')])
    ])
    return wf


def test_workflow_disable():
    global ifresult
    wf = _base_workflow()

    ifresult = None
    wf.inputs.inputnode.in_value = 0
    wf.run()
    yield assert_equal, ifresult, 1

    # Check if direct signal setting works
    ifresult = None
    wf.signals.disable = True
    wf.run()
    yield assert_equal, ifresult, None

    ifresult = None
    wf.signals.disable = False
    wf.run()
    yield assert_equal, ifresult, 1

    # Check if signalnode way works
    ifresult = None
    wf.inputs.signalnode.disable = True
    wf.run()
    yield assert_equal, ifresult, None

    ifresult = None
    wf.inputs.signalnode.disable = False
    wf.run()
    yield assert_equal, ifresult, 1

    # Check if one can set signal then node
    ifresult = None
    wf.signals.disable = True
    wf.run()
    yield assert_equal, ifresult, None

    ifresult = None
    wf.inputs.signalnode.disable = False
    wf.run()
    yield assert_equal, ifresult, 1

    # Check if one can set node then signal
    ifresult = None
    wf.inputs.signalnode.disable = True
    wf.run()
    yield assert_equal, ifresult, None

    ifresult = None
    wf.signals.disable = False
    wf.run()
    yield assert_equal, ifresult, 1


def test_workflow_disable_nested_A():
    global ifresult

    inner = _base_workflow()
    dn = pe.Node(niu.IdentityInterface(
        fields=['donotrun', 'value']), 'decisionnode')

    outer = pe.Workflow('OuterWorkflow')

    outer.connect([
        (dn, inner, [('donotrun', 'signalnode.disable')])
    ], conn_type='signal')

    outer.connect([
        (dn, inner, [('value', 'inputnode.in_value')])
    ])

    ifresult = None
    outer.inputs.decisionnode.value = 0
    outer.run()
    yield assert_equal, ifresult, 1

    ifresult = None
    outer.inputs.decisionnode.donotrun = True
    outer.run()
    yield assert_equal, ifresult, None

    ifresult = None
    outer.inputs.decisionnode.donotrun = False
    outer.run()
    yield assert_equal, ifresult, 1


def test_workflow_disable_nested_B():
    global ifresult

    inner = _base_workflow()
    dn = pe.Node(niu.IdentityInterface(fields=['value']),
                 'inputnode')

    outer = pe.Workflow('OuterWorkflow')

    outer.connect([
        (dn, inner, [('value', 'inputnode.in_value')])
    ])

    ifresult = None
    outer.inputs.inputnode.value = 0
    outer.run()
    yield assert_equal, ifresult, 1

    ifresult = None
    outer.signals.disable = True
    outer.run()
    yield assert_equal, ifresult, None

    ifresult = None
    outer.signals.disable = False
    outer.run()
    yield assert_equal, ifresult, 1


def test_cw_cond_unset():
    global ifresult

    cwf = _base_cachedworkflow()
    cwf.inputs.inputnode.a = 2
    cwf.inputs.inputnode.b = 3

    # check results
    ifresult = None
    res = cwf.run()
    yield assert_equal, ifresult, 5

    ifresult = None
    cwf.inputs.cachenode.c = 7
    res = cwf.run()
    yield assert_equal, ifresult, 7


#def test_cw_removal_cond_set():
#    def _sum(a, b):
#        return a + b
#
#    cwf = pe.CachedWorkflow(
#        'TestCachedWorkflow', cache_map=[('c', 'out')])
#
#    inputnode = pe.Node(niu.IdentityInterface(fields=['a', 'b']),
#                        name='inputnode')
#
#    sumnode = pe.Node(niu.Function(
#        input_names=['a', 'b'], output_names=['sum'],
#        function=_sum), name='SumNode')
#    cwf.connect([
#        (inputnode, sumnode, [('a', 'a'), ('b', 'b')]),
#        (sumnode, 'output', [('sum', 'out')])
#    ])
#
#    cwf.inputs.inputnode.a = 2
#    cwf.inputs.inputnode.b = 3
#    cwf.inputs.cachenode.c = 0
#
#    # check result
#    tmpfile = op.join(mkdtemp(), 'result.json')
#    jsonsink = pe.Node(nio.JSONFileSink(out_file=tmpfile), name='sink')
#    cwf.connect([('output', jsonsink, [('out', 'sum')])])
#    res = cwf.run()
#
#    with open(tmpfile, 'r') as f:
#        result = json.dumps(json.load(f))
#
#    rmtree(op.dirname(tmpfile))
#    yield assert_equal, result, '{"sum": 0}'
#
#
#def test_cw_removal_cond_connected_not_set():
#    def _sum(a, b):
#        return a + b
#
#    cwf = pe.CachedWorkflow(
#        'TestCachedWorkflow', cache_map=[('c', 'out')])
#
#    inputnode = pe.Node(niu.IdentityInterface(fields=['a', 'b']),
#                        name='inputnode')
#
#    sumnode = pe.Node(niu.Function(
#        input_names=['a', 'b'], output_names=['sum'],
#        function=_sum), name='SumNode')
#    cwf.connect([
#        (inputnode, sumnode, [('a', 'a'), ('b', 'b')]),
#        (sumnode, 'output', [('sum', 'out')])
#    ])
#
#    cwf.inputs.inputnode.a = 2
#    cwf.inputs.inputnode.b = 3
#
#    outernode = pe.Node(niu.IdentityInterface(fields=['c']), name='outer')
#    wf = pe.Workflow('OuterWorkflow')
#    wf.connect(outernode, 'c', cwf, 'cachenode.c')
#
#    # check result
#    tmpfile = op.join(mkdtemp(), 'result.json')
#    jsonsink = pe.Node(nio.JSONFileSink(out_file=tmpfile), name='sink')
#    wf.connect([(cwf, jsonsink, [('outputnode.out', 'sum')])])
#    res = wf.run()
#
#    with open(tmpfile, 'r') as f:
#        result = json.dumps(json.load(f))
#
#    rmtree(op.dirname(tmpfile))
#    yield assert_equal, result, '{"sum": 5}'
#
#
#def test_cw_removal_cond_connected_and_set():
#    def _sum(a, b):
#        return a + b
#
#    cwf = pe.CachedWorkflow(
#        'TestCachedWorkflow', cache_map=[('c', 'out')])
#
#    inputnode = pe.Node(niu.IdentityInterface(fields=['a', 'b']),
#                        name='inputnode')
#    sumnode = pe.Node(niu.Function(
#        input_names=['a', 'b'], output_names=['sum'],
#        function=_sum), name='SumNode')
#    cwf.connect([
#        (inputnode, sumnode, [('a', 'a'), ('b', 'b')]),
#        (sumnode, 'output', [('sum', 'out')])
#    ])
#
#    wf = pe.Workflow('OuterWorkflow')
#    wf.connect([
#        (outernode, cwf, [('a', 'inputnode.a'), ('b', 'inputnode.b'),
#                          ('c', 'cachenode.c')])
#    ])
#    outernode.inputs.a = 2
#    outernode.inputs.b = 3
#    outernode.inputs.c = 7
#
#    # check result
#    tmpfile = op.join(mkdtemp(), 'result.json')
#    jsonsink = pe.Node(nio.JSONFileSink(out_file=tmpfile), name='sink')
#    wf.connect([(cwf, jsonsink, [('outputnode.out', 'sum')])])
#    res = wf.run()
#
#    with open(tmpfile, 'r') as f:
#        result = json.dumps(json.load(f))
#
#    rmtree(op.dirname(tmpfile))
#    yield assert_equal, result, '{"sum": 7}'
