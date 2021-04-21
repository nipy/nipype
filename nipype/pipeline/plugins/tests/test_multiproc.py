# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Test the resource management of MultiProc
"""
import sys
import os
import pytest
from nipype.pipeline import engine as pe
from nipype.interfaces import base as nib


class InputSpec(nib.TraitedSpec):
    input1 = nib.traits.Int(desc="a random int")
    input2 = nib.traits.Int(desc="a random int")


class OutputSpec(nib.TraitedSpec):
    output1 = nib.traits.List(nib.traits.Int, desc="outputs")


class MultiprocTestInterface(nib.BaseInterface):
    input_spec = InputSpec
    output_spec = OutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["output1"] = [1, self.inputs.input1]
        return outputs


@pytest.mark.skipif(
    sys.version_info >= (3, 8), reason="multiprocessing issues in Python 3.8"
)
def test_run_multiproc(tmpdir):
    tmpdir.chdir()

    pipe = pe.Workflow(name="pipe")
    mod1 = pe.Node(MultiprocTestInterface(), name="mod1")
    mod2 = pe.MapNode(MultiprocTestInterface(), iterfield=["input1"], name="mod2")
    pipe.connect([(mod1, mod2, [("output1", "input1")])])
    pipe.base_dir = os.getcwd()
    mod1.inputs.input1 = 1
    pipe.config["execution"]["poll_sleep_duration"] = 2
    execgraph = pipe.run(plugin="MultiProc")
    names = [node.fullname for node in execgraph.nodes()]
    node = list(execgraph.nodes())[names.index("pipe.mod1")]
    result = node.get_output("output1")
    assert result == [1, 1]


class InputSpecSingleNode(nib.TraitedSpec):
    input1 = nib.traits.Int(desc="a random int")
    input2 = nib.traits.Int(desc="a random int")


class OutputSpecSingleNode(nib.TraitedSpec):
    output1 = nib.traits.Int(desc="a random int")


class SingleNodeTestInterface(nib.BaseInterface):
    input_spec = InputSpecSingleNode
    output_spec = OutputSpecSingleNode

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["output1"] = self.inputs.input1
        return outputs


def test_no_more_memory_than_specified(tmpdir):
    tmpdir.chdir()
    pipe = pe.Workflow(name="pipe")
    n1 = pe.Node(SingleNodeTestInterface(), name="n1", mem_gb=1)
    n2 = pe.Node(SingleNodeTestInterface(), name="n2", mem_gb=1)
    n3 = pe.Node(SingleNodeTestInterface(), name="n3", mem_gb=1)
    n4 = pe.Node(SingleNodeTestInterface(), name="n4", mem_gb=1)

    pipe.connect(n1, "output1", n2, "input1")
    pipe.connect(n1, "output1", n3, "input1")
    pipe.connect(n2, "output1", n4, "input1")
    pipe.connect(n3, "output1", n4, "input2")
    n1.inputs.input1 = 1

    max_memory = 0.5
    with pytest.raises(RuntimeError):
        pipe.run(
            plugin="MultiProc", plugin_args={"memory_gb": max_memory, "n_procs": 2}
        )


def test_no_more_threads_than_specified(tmpdir):
    tmpdir.chdir()

    pipe = pe.Workflow(name="pipe")
    n1 = pe.Node(SingleNodeTestInterface(), name="n1", n_procs=2)
    n2 = pe.Node(SingleNodeTestInterface(), name="n2", n_procs=2)
    n3 = pe.Node(SingleNodeTestInterface(), name="n3", n_procs=4)
    n4 = pe.Node(SingleNodeTestInterface(), name="n4", n_procs=2)

    pipe.connect(n1, "output1", n2, "input1")
    pipe.connect(n1, "output1", n3, "input1")
    pipe.connect(n2, "output1", n4, "input1")
    pipe.connect(n3, "output1", n4, "input2")
    n1.inputs.input1 = 4

    max_threads = 2
    with pytest.raises(RuntimeError):
        pipe.run(plugin="MultiProc", plugin_args={"n_procs": max_threads})


@pytest.mark.skipif(
    sys.version_info >= (3, 8), reason="multiprocessing issues in Python 3.8"
)
def test_hold_job_until_procs_available(tmpdir):
    tmpdir.chdir()

    pipe = pe.Workflow(name="pipe")
    n1 = pe.Node(SingleNodeTestInterface(), name="n1", n_procs=2)
    n2 = pe.Node(SingleNodeTestInterface(), name="n2", n_procs=2)
    n3 = pe.Node(SingleNodeTestInterface(), name="n3", n_procs=2)
    n4 = pe.Node(SingleNodeTestInterface(), name="n4", n_procs=2)

    pipe.connect(n1, "output1", n2, "input1")
    pipe.connect(n1, "output1", n3, "input1")
    pipe.connect(n2, "output1", n4, "input1")
    pipe.connect(n3, "output1", n4, "input2")
    n1.inputs.input1 = 4

    max_threads = 2
    pipe.run(plugin="MultiProc", plugin_args={"n_procs": max_threads})
