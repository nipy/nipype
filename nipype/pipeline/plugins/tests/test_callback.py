# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for workflow callbacks
"""
from time import sleep
import pytest
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

try:
    import pandas
    has_pandas = True
except ImportError:
     has_pandas = False

def func():
    return


def bad_func():
    raise Exception


class Status:
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


@pytest.mark.parametrize("plugin", ["Linear", "MultiProc", "LegacyMultiProc"])
@pytest.mark.skipif(not has_pandas, "Test requires pandas")
def test_callback_gantt(tmpdir, plugin):
    import logging

    from os import path

    from nipype.utils.profiler import log_nodes_cb
    from nipype.utils.draw_gantt_chart import generate_gantt_chart

    log_filename = path.join(tmpdir, "callback.log")
    logger = logging.getLogger("callback")
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(log_filename)
    logger.addHandler(handler)

    # create workflow
    wf = pe.Workflow(name="test", base_dir=tmpdir.strpath)
    f_node = pe.Node(
        niu.Function(function=func, input_names=[], output_names=[]), name="f_node"
    )
    wf.add_nodes([f_node])
    wf.config["execution"] = {"crashdump_dir": wf.base_dir, "poll_sleep_duration": 2}

    plugin_args = {"status_callback": log_nodes_cb}
    if plugin != "Linear":
        plugin_args["n_procs"] = 8
    wf.run(plugin=plugin, plugin_args=plugin_args)

    generate_gantt_chart(
        path.join(tmpdir, "callback.log"), 1 if plugin == "Linear" else 8
    )
    assert path.exists(path.join(tmpdir, "callback.log.html"))
