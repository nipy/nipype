import os
import nipype.interfaces.base as nib
from tempfile import mkdtemp
from shutil import rmtree

from nipype.testing import assert_raises, assert_false
import nipype.pipeline.engine as pe

class InputSpec(nib.TraitedSpec):
    input1 = nib.traits.Int(desc='a random int')
    input2 = nib.traits.Int(desc='a random int')

class OutputSpec(nib.TraitedSpec):
    output1 = nib.traits.List(nib.traits.Int, desc='outputs')

class TestInterface(nib.BaseInterface):
    input_spec = InputSpec
    output_spec = OutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output1'] = [1, self.inputs.input1]
        return outputs

def callme(node, graph):
    pass

def test_debug():
    cur_dir = os.getcwd()
    temp_dir = mkdtemp(prefix='test_engine_')
    os.chdir(temp_dir)

    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.MapNode(interface=TestInterface(),
                      iterfield=['input1'],
                      name='mod2')
    pipe.connect([(mod1,mod2,[('output1','input1')])])
    pipe.base_dir = os.getcwd()
    mod1.inputs.input1 = 1
    run_wf = lambda: pipe.run(plugin="Debug")
    yield assert_raises, ValueError, run_wf
    try:
        pipe.run(plugin="Debug", plugin_args={'callable': callme})
        exception_raised = False
    except Exception:
        exception_raised = True
    yield assert_false, exception_raised
    os.chdir(cur_dir)
    rmtree(temp_dir)