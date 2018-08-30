# -*- coding: utf-8 -*-
import os
from shutil import rmtree
from tempfile import mkdtemp

import nipype.interfaces.base as nib
import pytest
import nipype.pipeline.engine as pe


class InputSpec(nib.TraitedSpec):
    input1 = nib.traits.Int(desc='a random int')
    input2 = nib.traits.Int(desc='a random int')


class OutputSpec(nib.TraitedSpec):
    output1 = nib.traits.List(nib.traits.Int, desc='outputs')


class OarTestInterface(nib.BaseInterface):
    input_spec = InputSpec
    output_spec = OutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output1'] = [1, self.inputs.input1]
        return outputs


@pytest.mark.xfail(reason="not known")
def test_run_oar():
    cur_dir = os.getcwd()
    temp_dir = mkdtemp(prefix='test_engine_', dir=os.getcwd())
    os.chdir(temp_dir)

    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=OarTestInterface(), name='mod1')
    mod2 = pe.MapNode(
        interface=OarTestInterface(), iterfield=['input1'], name='mod2')
    pipe.connect([(mod1, mod2, [('output1', 'input1')])])
    pipe.base_dir = os.getcwd()
    mod1.inputs.input1 = 1
    execgraph = pipe.run(plugin="OAR")
    names = [
        '.'.join((node._hierarchy, node.name)) for node in execgraph.nodes()
    ]
    node = list(execgraph.nodes())[names.index('pipe.mod1')]
    result = node.get_output('output1')
    assert result == [1, 1]
    os.chdir(cur_dir)
    rmtree(temp_dir)
