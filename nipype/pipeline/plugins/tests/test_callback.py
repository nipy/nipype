# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for workflow callbacks
"""
from time import sleep
import pytest
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
        self.statuses.append((node.name, status))


@pytest.mark.parametrize("plugin", ["Linear", "MultiProc", "LegacyMultiProc"])
def test_callback_normal(tmpdir, plugin):
    tmpdir.chdir()

    so = Status()
    wf = pe.Workflow(name="test", base_dir=tmpdir.strpath)
    f_node = pe.Node(
        niu.Function(function=func, input_names=[], output_names=[]), name="f_node"
    )
    wf.add_nodes([f_node])
    wf.config["execution"] = {"crashdump_dir": wf.base_dir, "poll_sleep_duration": 2}
    wf.run(plugin=plugin, plugin_args={"status_callback": so.callback})
    assert so.statuses == [("f_node", "start"), ("f_node", "end")]


@pytest.mark.parametrize("plugin", ["Linear", "MultiProc", "LegacyMultiProc"])
@pytest.mark.parametrize("stop_on_first_crash", [False, True])
def test_callback_exception(tmpdir, plugin, stop_on_first_crash):
    tmpdir.chdir()

    so = Status()
    wf = pe.Workflow(name="test", base_dir=tmpdir.strpath)
    f_node = pe.Node(
        niu.Function(function=bad_func, input_names=[], output_names=[]), name="f_node"
    )
    wf.add_nodes([f_node])
    wf.config["execution"] = {
        "crashdump_dir": wf.base_dir,
        "stop_on_first_crash": stop_on_first_crash,
        "poll_sleep_duration": 2,
    }
    with pytest.raises(Exception):
        wf.run(plugin=plugin, plugin_args={"status_callback": so.callback})

    sleep(0.5)  # Wait for callback to be called (python 2.7)
    assert so.statuses == [("f_node", "start"), ("f_node", "exception")]
