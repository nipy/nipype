from shutil import which

import nipype.interfaces.base as nib
import pytest
import nipype.pipeline.engine as pe


class InputSpec(nib.TraitedSpec):
    input1 = nib.traits.Int(desc="a random int")
    input2 = nib.traits.Int(desc="a random int")


class OutputSpec(nib.TraitedSpec):
    output1 = nib.traits.List(nib.traits.Int, desc="outputs")


class PbsTestInterface(nib.BaseInterface):
    input_spec = InputSpec
    output_spec = OutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["output1"] = [1, self.inputs.input1]
        return outputs


@pytest.mark.skipif(which("qsub") is None, reason="PBS not installed")
@pytest.mark.timeout(60)
def test_run_pbsgraph(tmp_path):
    pipe = pe.Workflow(name="pipe", base_dir=str(tmp_path))
    mod1 = pe.Node(interface=PbsTestInterface(), name="mod1")
    mod2 = pe.MapNode(interface=PbsTestInterface(), iterfield=["input1"], name="mod2")
    pipe.connect([(mod1, mod2, [("output1", "input1")])])
    mod1.inputs.input1 = 1
    execgraph = pipe.run(plugin="PBSGraph")
    names = [f"{node._hierarchy}.{node.name}" for node in execgraph.nodes()]
    node = list(execgraph.nodes())[names.index("pipe.mod1")]
    result = node.get_output("output1")
    assert result == [1, 1]
