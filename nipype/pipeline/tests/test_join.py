# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for join expansion
"""
from copy import deepcopy
import os
from shutil import rmtree
from tempfile import mkdtemp

import networkx as nx

from nipype.testing import (assert_equal, assert_true)
import nipype.interfaces.base as nib
import nipype.pipeline.engine as pe
from nipype.interfaces.utility import IdentityInterface, Join


class IncrementInputSpec(nib.TraitedSpec):
    input1 = nib.traits.Int(mandatory=True, desc='input')

class IncrementOutputSpec(nib.TraitedSpec):
    output1 = nib.traits.Int(desc='ouput')

class IncrementInterface(nib.BaseInterface):
    input_spec = IncrementInputSpec
    output_spec = IncrementOutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output1'] = self.inputs.input1 + 1
        return outputs


_sum = 0
"""The Sum interface execution result."""

class SumInputSpec(nib.TraitedSpec):
    input1 = nib.traits.List(nib.traits.Int, mandatory=True, desc='input')

class SumOutputSpec(nib.TraitedSpec):
    output1 = nib.traits.Int(desc='ouput')

class SumInterface(nib.BaseInterface):
    input_spec = SumInputSpec
    output_spec = SumOutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        global _sum
        outputs = self._outputs().get()
        _sum = outputs['output1'] = sum(self.inputs.input1)
        return outputs


_products = []
"""The Scale interface execution result."""

class ScaleInputSpec(nib.TraitedSpec):
    scalar = nib.traits.Int(mandatory=True, desc='scalar')
    vector = nib.traits.List(nib.traits.Int, mandatory=True, desc='vector')

class ScaleOutputSpec(nib.TraitedSpec):
    output1 = nib.traits.List(nib.traits.Int, mandatory=True, desc='output')

class ScaleInterface(nib.BaseInterface):
    input_spec = ScaleInputSpec
    output_spec = ScaleOutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        global _products
        outputs = self._outputs().get()
        outputs['output1'] = [2 * n for n in self.inputs.vector]
        _products.append(outputs['output1'])
        return outputs


def test_join_expansion():
    cwd = os.getcwd()
    wd = mkdtemp()
    os.chdir(wd)

    # Make the workflow.
    wf = pe.Workflow(name='test')
    inputspec = pe.Node(IdentityInterface(fields=['n']), name='inputspec')
    inputspec.iterables = [('n', [1, 2])]
    pre_join1 = pe.Node(IncrementInterface(), name='pre_join1')
    wf.connect(inputspec, 'n', pre_join1, 'input1')
    pre_join2 = pe.Node(IncrementInterface(), name='pre_join2')
    wf.connect(pre_join1, 'output1', pre_join2, 'input1')
    join = pe.Node(Join(), joinsource='inputspec', name='join')
    wf.connect(pre_join2, 'output1', join, 'in')
    post_join1 = pe.Node(SumInterface(), name='post_join1')
    wf.connect(join, 'out', post_join1, 'input1')
    post_join2 = pe.Node(ScaleInterface(), name='post_join2')
    wf.connect(join, 'out', post_join2, 'vector')
    wf.connect(pre_join1, 'output1', post_join2, 'scalar')
    
    result = wf.run()
    
    # the two expanded pre-join predecessor nodes feed into one join node
    joins = [node for node in result.nodes() if node.name == 'join']
    assert_equal(len(joins), 1, "The number of join result nodes is incorrect.")
    # the expanded graph contains 2 * 2 = 4 iteration pre-join nodes, 1 join
    # node, 1 non-iterated post-join node and 2 * 1 iteration post-join nodes.
    # Nipype factors away the IdentityInterface.
    assert_equal(len(result.nodes()), 8, "The number of expanded nodes is incorrect.")
    # the post-join Sum result is (1 + 1 + 1) + (2 + 1 + 1)
    assert_equal(_sum, 7, "The post-join Sum output value is incorrect.")
    # the post-join Scale result is two iterated copies of (1 + 1) * [3, 4].
    # the iterables input order is preserved in the join output.
    assert_equal(_products, [[6, 8], [6, 8]], "The post-join Scale output value is incorrect.")

    os.chdir(cwd)
    rmtree(wd)


if __name__ == "__main__":
    import nose

    nose.main(defaultTest=__name__)
