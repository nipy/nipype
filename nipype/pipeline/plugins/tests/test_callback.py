# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""Tests for workflow callbacks
"""
from tempfile import mkdtemp
from shutil import rmtree

from nipype.testing import assert_equal
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe


def func():
    return


def bad_func():
    raise Exception


class Status:

    def __init__(self):
        self.statuses = []

    def callback(self, node, status):
        self.statuses.append((node, status))


def test_callback_normal():
    so = Status()
    wf = pe.Workflow(name='test', base_dir=mkdtemp())
    f_node = pe.Node(niu.Function(function=func, input_names=[],
                                  output_names=[]),
                     name='f_node')
    wf.add_nodes([f_node])
    wf.config['execution'] = {'crashdump_dir': wf.base_dir}
    wf.run(plugin="Linear", plugin_args={'status_callback': so.callback})
    assert_equal(len(so.statuses), 2)
    for (n, s) in so.statuses:
        yield assert_equal, n.name, 'f_node'
    yield assert_equal, so.statuses[0][1], 'start'
    yield assert_equal, so.statuses[1][1], 'end'
    rmtree(wf.base_dir)


def test_callback_exception():
    so = Status()
    wf = pe.Workflow(name='test', base_dir=mkdtemp())
    f_node = pe.Node(niu.Function(function=bad_func, input_names=[],
                                  output_names=[]),
                     name='f_node')
    wf.add_nodes([f_node])
    wf.config['execution'] = {'crashdump_dir': wf.base_dir}
    try:
        wf.run(plugin="Linear", plugin_args={'status_callback': so.callback})
    except:
        pass
    assert_equal(len(so.statuses), 2)
    for (n, s) in so.statuses:
        yield assert_equal, n.name, 'f_node'
    yield assert_equal, so.statuses[0][1], 'start'
    yield assert_equal, so.statuses[1][1], 'exception'
    rmtree(wf.base_dir)


def test_callback_multiproc_normal():
    so = Status()
    wf = pe.Workflow(name='test', base_dir=mkdtemp())
    f_node = pe.Node(niu.Function(function=func, input_names=[],
                                  output_names=[]),
                     name='f_node')
    wf.add_nodes([f_node])
    wf.config['execution'] = {'crashdump_dir': wf.base_dir}
    wf.run(plugin='MultiProc', plugin_args={'status_callback': so.callback})
    assert_equal(len(so.statuses), 2)
    for (n, s) in so.statuses:
        yield assert_equal, n.name, 'f_node'
    yield assert_equal, so.statuses[0][1], 'start'
    yield assert_equal, so.statuses[1][1], 'end'
    rmtree(wf.base_dir)


def test_callback_multiproc_exception():
    so = Status()
    wf = pe.Workflow(name='test', base_dir=mkdtemp())
    f_node = pe.Node(niu.Function(function=bad_func, input_names=[],
                                  output_names=[]),
                     name='f_node')
    wf.add_nodes([f_node])
    wf.config['execution'] = {'crashdump_dir': wf.base_dir}
    try:
        wf.run(plugin='MultiProc',
               plugin_args={'status_callback': so.callback})
    except:
        pass
    assert_equal(len(so.statuses), 2)
    for (n, s) in so.statuses:
        yield assert_equal, n.name, 'f_node'
    yield assert_equal, so.statuses[0][1], 'start'
    yield assert_equal, so.statuses[1][1], 'exception'
    rmtree(wf.base_dir)
