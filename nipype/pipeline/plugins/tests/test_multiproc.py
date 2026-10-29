# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Test the resource management of MultiProc
"""

import sys
import os
import signal
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
    use_gpu = nib.traits.Bool(False, mandatory=False, desc="boolean for GPU nodes")


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


class ErrorInterface(SingleNodeTestInterface):
    def _run_interface(self, runtime):
        raise RuntimeError("This is an error")


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


def test_no_more_gpu_threads_than_specified(tmpdir):
    tmpdir.chdir()

    pipe = pe.Workflow(name="pipe")
    n1 = pe.Node(SingleNodeTestInterface(), name="n1", n_procs=2)
    n1.inputs.use_gpu = True
    n1.inputs.input1 = 4
    pipe.add_nodes([n1])

    max_threads = 2
    max_gpu = 1
    with pytest.raises(RuntimeError):
        pipe.run(
            plugin="MultiProc",
            plugin_args={"n_procs": max_threads, 'n_gpu_procs': max_gpu},
        )


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


@pytest.mark.parametrize("plugin", ["MultiProc", "LegacyMultiProc"])
def test_error_run_without_submitting(tmp_path, plugin):
    wf = pe.Workflow(name='rws', base_dir=str(tmp_path))
    n1 = pe.Node(SingleNodeTestInterface(), name='n1')
    n1.inputs.input1 = 1
    n2 = pe.Node(ErrorInterface(), name='n2', run_without_submitting=True)
    n3 = pe.Node(SingleNodeTestInterface(), name='n3')

    wf.connect(
        [
            (n1, n2, [('output1', 'input1')]),
            (n2, n3, [('output1', 'input1')]),
        ]
    ),

    with pytest.raises(RuntimeError):
        wf.run(plugin=plugin)


class KilledWorkerInterface(SingleNodeTestInterface):
    def _run_interface(self, runtime):
        os.kill(os.getpid(), signal.SIGKILL)


class UnpicklableInputSpec(InputSpecSingleNode):
    unpicklable = nib.traits.Any(desc="a value that cannot be pickled")


class UnpicklableInputInterface(SingleNodeTestInterface):
    input_spec = UnpicklableInputSpec


@pytest.fixture
def fail_on_hang():
    """Turn a hanging workflow run into a test failure."""

    def _hang(signum, frame):
        raise TimeoutError("MultiProc did not finish: it is waiting forever")

    previous = signal.signal(signal.SIGALRM, _hang)
    signal.alarm(60)
    yield
    signal.alarm(0)
    signal.signal(signal.SIGALRM, previous)


@pytest.mark.skipif(sys.platform == "win32", reason="needs SIGKILL and SIGALRM")
def test_killed_worker_fails_its_node(tmp_path, fail_on_hang):
    wf = pe.Workflow(name="killed", base_dir=str(tmp_path))
    # The "mem_thread" scheduler sorts ready jobs by mem_gb: with one
    # processor n1 runs and kills its worker, breaking the pool, before n2 is
    # submitted.
    n1 = pe.Node(KilledWorkerInterface(), name="n1", mem_gb=0.1)
    n2 = pe.Node(SingleNodeTestInterface(), name="n2", mem_gb=0.2)
    n3 = pe.Node(SingleNodeTestInterface(), name="n3")
    n1.inputs.input1 = 1
    n2.inputs.input1 = 2
    wf.connect(n1, "output1", n3, "input1")
    wf.add_nodes([n2])
    wf.config["execution"]["crashdump_dir"] = str(tmp_path)

    with pytest.raises(RuntimeError, match="BrokenProcessPool"):
        wf.run(
            plugin="MultiProc",
            plugin_args={"n_procs": 1, "memory_gb": 1, "scheduler": "mem_thread"},
        )

    # The independent node still ran, in a restarted pool; n1's dependent did not
    assert (tmp_path / "killed" / "n2" / "result_n2.pklz").exists()
    assert not (tmp_path / "killed" / "n3").exists()


@pytest.mark.skipif(sys.platform == "win32", reason="needs SIGALRM")
def test_unpicklable_node_fails(tmp_path, fail_on_hang):
    wf = pe.Workflow(name="unpicklable", base_dir=str(tmp_path))
    n1 = pe.Node(UnpicklableInputInterface(), name="n1")
    n1.inputs.input1 = 1
    n1.inputs.unpicklable = lambda: None
    wf.add_nodes([n1])
    # A pklz crash file would need to pickle the node too
    wf.config["execution"]["crashfile_format"] = "txt"
    wf.config["execution"]["crashdump_dir"] = str(tmp_path)

    with pytest.raises(RuntimeError):
        wf.run(plugin="MultiProc", plugin_args={"n_procs": 1})
