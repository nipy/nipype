# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for workflow callbacks
"""

from builtins import object

import pytest
import sys
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe


def func():
    return


def bad_func():
    raise Exception


class Status(object):
    def __init__(self):
        self.statuses = []

    def callback(self, node, status, result=None):
        self.statuses.append((node, status))


def test_callback_normal(tmpdir):
    tmpdir.chdir()

    so = Status()
    wf = pe.Workflow(name='test', base_dir=tmpdir.strpath)
    f_node = pe.Node(
        niu.Function(function=func, input_names=[], output_names=[]),
        name='f_node')
    wf.add_nodes([f_node])
    wf.config['execution'] = {'crashdump_dir': wf.base_dir}
    wf.run(plugin="Linear", plugin_args={'status_callback': so.callback})
    assert len(so.statuses) == 2
    for (n, s) in so.statuses:
        assert n.name == 'f_node'
    assert so.statuses[0][1] == 'start'
    assert so.statuses[1][1] == 'end'


def test_callback_exception(tmpdir):
    tmpdir.chdir()

    so = Status()
    wf = pe.Workflow(name='test', base_dir=tmpdir.strpath)
    f_node = pe.Node(
        niu.Function(function=bad_func, input_names=[], output_names=[]),
        name='f_node')
    wf.add_nodes([f_node])
    wf.config['execution'] = {'crashdump_dir': wf.base_dir}
    try:
        wf.run(plugin="Linear", plugin_args={'status_callback': so.callback})
    except:
        pass
    assert len(so.statuses) == 2
    for (n, s) in so.statuses:
        assert n.name == 'f_node'
    assert so.statuses[0][1] == 'start'
    assert so.statuses[1][1] == 'exception'


def test_callback_multiproc_normal(tmpdir):
    tmpdir.chdir()

    so = Status()
    wf = pe.Workflow(name='test', base_dir=tmpdir.strpath)
    f_node = pe.Node(
        niu.Function(function=func, input_names=[], output_names=[]),
        name='f_node')
    wf.add_nodes([f_node])
    wf.config['execution']['crashdump_dir'] = wf.base_dir
    wf.config['execution']['poll_sleep_duration'] = 2
    wf.run(plugin='MultiProc', plugin_args={'status_callback': so.callback})
    assert len(so.statuses) == 2
    for (n, s) in so.statuses:
        assert n.name == 'f_node'
    assert so.statuses[0][1] == 'start'
    assert so.statuses[1][1] == 'end'


def test_callback_multiproc_exception(tmpdir):
    tmpdir.chdir()

    so = Status()
    wf = pe.Workflow(name='test', base_dir=tmpdir.strpath)
    f_node = pe.Node(
        niu.Function(function=bad_func, input_names=[], output_names=[]),
        name='f_node')
    wf.add_nodes([f_node])
    wf.config['execution'] = {'crashdump_dir': wf.base_dir}

    try:
        wf.run(
            plugin='MultiProc', plugin_args={
                'status_callback': so.callback
            })
    except:
        pass
    assert len(so.statuses) == 2
    for (n, s) in so.statuses:
        assert n.name == 'f_node'
    assert so.statuses[0][1] == 'start'
    assert so.statuses[1][1] == 'exception'
