import os
import nipype.interfaces.base as nib

import pytest
import nipype.pipeline.engine as pe


class InputSpec(nib.TraitedSpec):
    input1 = nib.traits.Int(desc="a random int")
    input2 = nib.traits.Int(desc="a random int")


class OutputSpec(nib.TraitedSpec):
    output1 = nib.traits.List(nib.traits.Int, desc="outputs")


class DebugTestInterface(nib.BaseInterface):
    input_spec = InputSpec
    output_spec = OutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["output1"] = [1, self.inputs.input1]
        return outputs


def callme(node, graph):
    pass


def test_debug(tmpdir):
    tmpdir.chdir()

    pipe = pe.Workflow(name="pipe")
    mod1 = pe.Node(DebugTestInterface(), name="mod1")
    mod2 = pe.MapNode(DebugTestInterface(), iterfield=["input1"], name="mod2")

    pipe.connect([(mod1, mod2, [("output1", "input1")])])
    pipe.base_dir = os.getcwd()
    mod1.inputs.input1 = 1

    run_wf = lambda: pipe.run(plugin="Debug")
    with pytest.raises(ValueError):
        run_wf()

    exc = None
    try:
        pipe.run(plugin="Debug", plugin_args={"callable": callme})
    except Exception as e:
        exc = e

    assert exc is None, "unexpected exception caught"
