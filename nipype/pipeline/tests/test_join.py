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
from nipype.interfaces.utility import IdentityInterface


class IncrementInputSpec(nib.TraitedSpec):
    input1 = nib.traits.Int(mandatory=True, desc='input')
    inc = nib.traits.Int(usedefault=True, default_value=1, desc='increment')

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
        outputs['output1'] = self.inputs.input1 + self.inputs.inc
        return outputs

_sum = 0

_join = None

class SumInputSpec(nib.TraitedSpec):
    input1 = nib.traits.List(nib.traits.Int, mandatory=True, desc='input')

class SumOutputSpec(nib.TraitedSpec):
    output1 = nib.traits.Int(desc='ouput')
    operands = nib.traits.List(nib.traits.Int, desc='operands')

class SumInterface(nib.BaseInterface):
    input_spec = SumInputSpec
    output_spec = SumOutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        global _sum
        global _join
        outputs = self._outputs().get()
        _join = outputs['operands'] = self.inputs.input1
        _sum = outputs['output1'] = sum(self.inputs.input1)
        return outputs


_products = []
"""The Products interface execution results."""

class ProductInputSpec(nib.TraitedSpec):
    input1 = nib.traits.Int(mandatory=True, desc='input1')
    input2 = nib.traits.Int(mandatory=True, desc='input2')

class ProductOutputSpec(nib.TraitedSpec):
    output1 = nib.traits.Int(mandatory=True, desc='output')

class ProductInterface(nib.BaseInterface):
    input_spec = ProductInputSpec
    output_spec = ProductOutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        global _products
        outputs = self._outputs().get()
        outputs['output1'] = self.inputs.input1 * self.inputs.input2
        _products.append(outputs['output1'])
        return outputs

def test_join_expansion():
    cwd = os.getcwd()
    wd = mkdtemp()
    os.chdir(wd)

    # Make the workflow.
    wf = pe.Workflow(name='test')
    # the iterated input node
    inputspec = pe.Node(IdentityInterface(fields=['n']), name='inputspec')
    inputspec.iterables = [('n', [1, 2])]
    # a pre-join node in the iterated path
    pre_join1 = pe.Node(IncrementInterface(), name='pre_join1')
    wf.connect(inputspec, 'n', pre_join1, 'input1')
    # another pre-join node in the iterated path
    pre_join2 = pe.Node(IncrementInterface(), name='pre_join2')
    wf.connect(pre_join1, 'output1', pre_join2, 'input1')
    # the join node
    join = pe.JoinNode(SumInterface(), joinsource='inputspec',
        joinfield='input1', name='join')
    wf.connect(pre_join2, 'output1', join, 'input1')
    # an uniterated post-join node
    post_join1 = pe.Node(IncrementInterface(), name='post_join1')
    wf.connect(join, 'output1', post_join1, 'input1')
    # a post-join node in the iterated path
    post_join2 = pe.Node(ProductInterface(), name='post_join2')
    wf.connect(join, 'output1', post_join2, 'input1')
    wf.connect(pre_join1, 'output1', post_join2, 'input2')
    
    result = wf.run()
    
    # the two expanded pre-join predecessor nodes feed into one join node
    joins = [node for node in result.nodes() if node.name == 'join']
    assert_equal(len(joins), 1, "The number of join result nodes is incorrect.")
    # the expanded graph contains 2 * 2 = 4 iteration pre-join nodes, 1 join
    # node, 1 non-iterated post-join node and 2 * 1 iteration post-join nodes.
    # Nipype factors away the IdentityInterface.
    assert_equal(len(result.nodes()), 8, "The number of expanded nodes is incorrect.")
    # the join Sum result is (1 + 1 + 1) + (2 + 1 + 1)
    assert_equal(_sum, 7, "The join Sum output value is incorrect: %s." % _sum)
    # the join input preserves the iterables input order
    assert_equal(_join, [3, 4], "The join Sum input is incorrect: %s." % _join)
    # there are two iterations of the post-join node in the iterable path
    assert_equal(len(_products), 2,
                 "The number of iterated post-join outputs is incorrect")

    os.chdir(cwd)
    rmtree(wd)


if __name__ == "__main__":
    import nose
    
    nose.main(defaultTest=__name__)
