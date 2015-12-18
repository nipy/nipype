#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.testing import (assert_raises, assert_equal,
                            assert_true, assert_false)
from nipype.interfaces import utility as niu
from nipype.interfaces import io as nio
from nipype.pipeline import engine as pe
from copy import deepcopy
import os.path as op
from tempfile import mkdtemp
from shutil import rmtree
import json


def test_cw_removal_cond_unset():
    def _sum(a, b):
        return a + b

    cwf = pe.CachedWorkflow(
        'TestCachedWorkflow', cache_map=[('c', 'out')])

    inputnode = pe.Node(niu.IdentityInterface(fields=['a', 'b']),
                        name='inputnode')

    sumnode = pe.Node(niu.Function(
        input_names=['a', 'b'], output_names=['sum'],
        function=_sum), name='SumNode')
    cwf.connect([
        (inputnode, sumnode, [('a', 'a'), ('b', 'b')]),
        (sumnode, 'output', [('sum', 'out')])
    ])

    cwf.inputs.inputnode.a = 2
    cwf.inputs.inputnode.b = 3

    # check result
    tmpfile = op.join(mkdtemp(), 'result.json')
    jsonsink = pe.Node(nio.JSONFileSink(out_file=tmpfile), name='sink')
    # cwf.connect([('output', jsonsink, [('out', 'sum')])])
    res = cwf.run()

    with open(tmpfile, 'r') as f:
        result = json.dumps(json.load(f))

    rmtree(op.dirname(tmpfile))
    yield assert_equal, result, '{"sum": 5}'


def test_cw_removal_cond_set():
    def _sum(a, b):
        return a + b

    cwf = pe.CachedWorkflow(
        'TestCachedWorkflow', cache_map=[('c', 'out')])

    inputnode = pe.Node(niu.IdentityInterface(fields=['a', 'b']),
                        name='inputnode')

    sumnode = pe.Node(niu.Function(
        input_names=['a', 'b'], output_names=['sum'],
        function=_sum), name='SumNode')
    cwf.connect([
        (inputnode, sumnode, [('a', 'a'), ('b', 'b')]),
        (sumnode, 'output', [('sum', 'out')])
    ])

    cwf.inputs.inputnode.a = 2
    cwf.inputs.inputnode.b = 3
    cwf.inputs.cachenode.c = 0

    # check result
    tmpfile = op.join(mkdtemp(), 'result.json')
    jsonsink = pe.Node(nio.JSONFileSink(out_file=tmpfile), name='sink')
    cwf.connect([('output', jsonsink, [('out', 'sum')])])
    res = cwf.run()

    with open(tmpfile, 'r') as f:
        result = json.dumps(json.load(f))

    rmtree(op.dirname(tmpfile))
    yield assert_equal, result, '{"sum": 0}'


def test_cw_removal_cond_connected_not_set():
    def _sum(a, b):
        return a + b

    cwf = pe.CachedWorkflow(
        'TestCachedWorkflow', cache_map=[('c', 'out')])

    inputnode = pe.Node(niu.IdentityInterface(fields=['a', 'b']),
                        name='inputnode')

    sumnode = pe.Node(niu.Function(
        input_names=['a', 'b'], output_names=['sum'],
        function=_sum), name='SumNode')
    cwf.connect([
        (inputnode, sumnode, [('a', 'a'), ('b', 'b')]),
        (sumnode, 'output', [('sum', 'out')])
    ])

    cwf.inputs.inputnode.a = 2
    cwf.inputs.inputnode.b = 3

    outernode = pe.Node(niu.IdentityInterface(fields=['c']), name='outer')
    wf = pe.Workflow('OuterWorkflow')
    wf.connect(outernode, 'c', cwf, 'cachenode.c')

    # check result
    tmpfile = op.join(mkdtemp(), 'result.json')
    jsonsink = pe.Node(nio.JSONFileSink(out_file=tmpfile), name='sink')
    wf.connect([(cwf, jsonsink, [('outputnode.out', 'sum')])])
    res = wf.run()

    with open(tmpfile, 'r') as f:
        result = json.dumps(json.load(f))

    rmtree(op.dirname(tmpfile))
    yield assert_equal, result, '{"sum": 5}'


def test_cw_removal_cond_connected_and_set():
    def _sum(a, b):
        return a + b

    cwf = pe.CachedWorkflow(
        'TestCachedWorkflow', cache_map=[('c', 'out')])

    inputnode = pe.Node(niu.IdentityInterface(fields=['a', 'b']),
                        name='inputnode')
    sumnode = pe.Node(niu.Function(
        input_names=['a', 'b'], output_names=['sum'],
        function=_sum), name='SumNode')
    cwf.connect([
        (inputnode, sumnode, [('a', 'a'), ('b', 'b')]),
        (sumnode, 'output', [('sum', 'out')])
    ])

    wf = pe.Workflow('OuterWorkflow')
    wf.connect([
        (outernode, cwf, [('a', 'inputnode.a'), ('b', 'inputnode.b'),
                          ('c', 'cachenode.c')])
    ])
    outernode.inputs.a = 2
    outernode.inputs.b = 3
    outernode.inputs.c = 7

    # check result
    tmpfile = op.join(mkdtemp(), 'result.json')
    jsonsink = pe.Node(nio.JSONFileSink(out_file=tmpfile), name='sink')
    wf.connect([(cwf, jsonsink, [('outputnode.out', 'sum')])])
    res = wf.run()

    with open(tmpfile, 'r') as f:
        result = json.dumps(json.load(f))

    rmtree(op.dirname(tmpfile))
    yield assert_equal, result, '{"sum": 7}'
