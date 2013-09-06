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

_sums = []

_sum_operands = []

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
        global _sum_operands
        outputs = self._outputs().get()
        outputs['operands'] = self.inputs.input1
        _sum_operands.append(outputs['operands'])
        outputs['output1'] = sum(self.inputs.input1)
        _sums.append(outputs['output1'])
        return outputs


_set_len = None
"""The Set interface execution result."""

class SetInputSpec(nib.TraitedSpec):
    input1 = nib.traits.Set(nib.traits.Int, mandatory=True, desc='input')

class SetOutputSpec(nib.TraitedSpec):
    output1 = nib.traits.Int(desc='ouput')

class SetInterface(nib.BaseInterface):
    input_spec = SetInputSpec
    output_spec = SetOutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        global _set_len
        outputs = self._outputs().get()
        _set_len = outputs['output1'] = len(self.inputs.input1)
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
    assert_equal(len(_sums), 1,
                 "The number of join outputs is incorrect")
    assert_equal(_sums[0], 7, "The join Sum output value is incorrect: %s." % _sums[0])
    # the join input preserves the iterables input order
    assert_equal(_sum_operands[0], [3, 4],
        "The join Sum input is incorrect: %s." % _sum_operands[0])
    # there are two iterations of the post-join node in the iterable path
    assert_equal(len(_products), 2,
                 "The number of iterated post-join outputs is incorrect")

    os.chdir(cwd)
    rmtree(wd)

def test_node_joinsource():
    """Test setting the joinsource to a Node."""
    cwd = os.getcwd()
    wd = mkdtemp()
    os.chdir(wd)

    # Make the workflow.
    wf = pe.Workflow(name='test')
    # the iterated input node
    inputspec = pe.Node(IdentityInterface(fields=['n']), name='inputspec')
    inputspec.iterables = [('n', [1, 2])]
    # the join node
    join = pe.JoinNode(SetInterface(), joinsource=inputspec,
        joinfield='input1', name='join')

    # the joinsource is the inputspec name
    assert_equal(join.joinsource, inputspec.name,
        "The joinsource is not set to the node name.")

    os.chdir(cwd)
    rmtree(wd)

def test_set_join_node():
    """Test collecting join inputs to a set."""
    cwd = os.getcwd()
    wd = mkdtemp()
    os.chdir(wd)

    # Make the workflow.
    wf = pe.Workflow(name='test')
    # the iterated input node
    inputspec = pe.Node(IdentityInterface(fields=['n']), name='inputspec')
    inputspec.iterables = [('n', [1, 2, 1, 3, 2])]
    # a pre-join node in the iterated path
    pre_join1 = pe.Node(IncrementInterface(), name='pre_join1')
    wf.connect(inputspec, 'n', pre_join1, 'input1')
    # the set join node
    join = pe.JoinNode(SetInterface(), joinsource='inputspec',
        joinfield='input1', name='join')
    wf.connect(pre_join1, 'output1', join, 'input1')

    wf.run()

    # the join length is the number of unique inputs
    assert_equal(_set_len, 3,
        "The join Set output value is incorrect: %s." % _set_len)

    os.chdir(cwd)
    rmtree(wd)

def test_unique_join_node():
    """Test join with the ``unique`` flag set to True."""
    global _sum_operands
    _sum_operands = []
    cwd = os.getcwd()
    wd = mkdtemp()
    os.chdir(wd)

    # Make the workflow.
    wf = pe.Workflow(name='test')
    # the iterated input node
    inputspec = pe.Node(IdentityInterface(fields=['n']), name='inputspec')
    inputspec.iterables = [('n', [3, 1, 2, 1, 3])]
    # a pre-join node in the iterated path
    pre_join1 = pe.Node(IncrementInterface(), name='pre_join1')
    wf.connect(inputspec, 'n', pre_join1, 'input1')
    # the set join node
    join = pe.JoinNode(SumInterface(), joinsource='inputspec',
        joinfield='input1', unique=True, name='join')
    wf.connect(pre_join1, 'output1', join, 'input1')

    wf.run()

    assert_equal(_sum_operands[0], [4, 2, 3],
        "The unique join output value is incorrect: %s." % _sum_operands[0])

    os.chdir(cwd)
    rmtree(wd)

def test_multiple_join_nodes():
    """Test two join nodes, one downstream of the other."""
    global _products
    _products = []
    cwd = os.getcwd()
    wd = mkdtemp()
    os.chdir(wd)

    # Make the workflow.
    wf = pe.Workflow(name='test')
    # the iterated input node
    inputspec = pe.Node(IdentityInterface(fields=['n']), name='inputspec')
    inputspec.iterables = [('n', [1, 2, 3])]
    # a pre-join node in the iterated path
    pre_join1 = pe.Node(IncrementInterface(), name='pre_join1')
    wf.connect(inputspec, 'n', pre_join1, 'input1')
    # the first join node
    join1 = pe.JoinNode(IdentityInterface(fields=['vector']),
                        joinsource='inputspec', joinfield='vector',
                        name='join1')
    wf.connect(pre_join1, 'output1', join1, 'vector')
    # an uniterated post-join node
    post_join1 = pe.Node(SumInterface(), name='post_join1')
    wf.connect(join1, 'vector', post_join1, 'input1')
    # the downstream join node connected to both an upstream join
    # path output and a separate input in the iterated path
    join2 = pe.JoinNode(IdentityInterface(fields=['vector', 'scalar']),
                        joinsource='inputspec', joinfield='vector',
                        name='join2')
    wf.connect(pre_join1, 'output1', join2, 'vector')
    wf.connect(post_join1, 'output1', join2, 'scalar')
    # a second post-join node
    post_join2 = pe.Node(SumInterface(), name='post_join2')
    wf.connect(join2, 'vector', post_join2, 'input1')
    # a third post-join node
    post_join3 = pe.Node(ProductInterface(), name='post_join3')
    wf.connect(post_join2, 'output1', post_join3, 'input1')
    wf.connect(join2, 'scalar', post_join3, 'input2')

    result = wf.run()

    # The expanded graph contains one pre_join1 replicate per inputspec
    # replicate and one of each remaining node = 3 + 5 = 8 nodes.
    # The replicated inputspec nodes are factored out of the expansion.
    assert_equal(len(result.nodes()), 8,
                 "The number of expanded nodes is incorrect.")
    # The outputs are:
    # pre_join1: [2, 3, 4]
    # post_join1: 9
    # join2: [2, 3, 4] and 9
    # post_join2: 9
    # post_join3: 9 * 9 = 81
    assert_equal(_products, [81], "The post-join product is incorrect")

    os.chdir(cwd)
    rmtree(wd)

def test_identity_join_node():
    """Test an IdentityInterface join."""
    global _sum_operands
    _sum_operands = []
    cwd = os.getcwd()
    wd = mkdtemp()
    os.chdir(wd)

    # Make the workflow.
    wf = pe.Workflow(name='test')
    # the iterated input node
    inputspec = pe.Node(IdentityInterface(fields=['n']),
                        name='inputspec')
    inputspec.iterables = [('n', [1, 2, 3])]
    # a pre-join node in the iterated path
    pre_join1 = pe.Node(IncrementInterface(), name='pre_join1')
    wf.connect(inputspec, 'n', pre_join1, 'input1')
    # the IdentityInterface join node
    join = pe.JoinNode(IdentityInterface(fields=['vector']),
                       joinsource='inputspec', joinfield='vector',
                       name='join')
    wf.connect(pre_join1, 'output1', join, 'vector')
    # an uniterated post-join node
    post_join1 = pe.Node(SumInterface(), name='post_join1')
    wf.connect(join, 'vector', post_join1, 'input1')

    result = wf.run()

    # the expanded graph contains 1 * 3 iteration pre-join nodes, 1 join
    # node and 1 post-join node. Nipype factors away the iterable input
    # IdentityInterface but keeps the join IdentityInterface.
    assert_equal(len(result.nodes()), 5,
        "The number of expanded nodes is incorrect.")
    assert_equal(_sum_operands[0], [2, 3, 4],
                 "The join Sum input is incorrect: %s." %_sum_operands[0])

    os.chdir(cwd)
    rmtree(wd)

def test_multifield_join_node():
    """Test join on several fields."""
    global _products
    _products = []
    cwd = os.getcwd()
    wd = mkdtemp()
    os.chdir(wd)

    # Make the workflow.
    wf = pe.Workflow(name='test')
    # the iterated input node
    inputspec = pe.Node(IdentityInterface(fields=['m', 'n']),
                        name='inputspec')
    inputspec.iterables = [('m', [1, 2]), ('n', [3, 4])]
    # two pre-join nodes in a parallel iterated path
    inc1 = pe.Node(IncrementInterface(), name='inc1')
    wf.connect(inputspec, 'm', inc1, 'input1')
    inc2 = pe.Node(IncrementInterface(), name='inc2')
    wf.connect(inputspec, 'n', inc2, 'input1')
    # the join node
    join = pe.JoinNode(IdentityInterface(fields=['vector1', 'vector2']),
                       joinsource='inputspec', name='join')
    wf.connect(inc1, 'output1', join, 'vector1')
    wf.connect(inc2, 'output1', join, 'vector2')
    # a post-join node
    prod = pe.MapNode(ProductInterface(), name='prod',
                       iterfield=['input1', 'input2'])
    wf.connect(join, 'vector1', prod, 'input1')
    wf.connect(join, 'vector2', prod, 'input2')

    result = wf.run()

    # the iterables are expanded as the cartesian product of the iterables values.
    # thus, the expanded graph contains 2 * (2 * 2) iteration pre-join nodes, 1 join
    # node and 1 post-join node.
    assert_equal(len(result.nodes()), 10,
                 "The number of expanded nodes is incorrect.")
    # the product inputs are [2, 4], [2, 5], [3, 4], [3, 5]
    assert_equal(_products, [8, 10, 12, 15],
                 "The post-join products is incorrect: %s." % _products)

    os.chdir(cwd)
    rmtree(wd)

def test_synchronize_join_node():
    """Test join on an input node which has the ``synchronize`` flag set to True."""
    global _products
    _products = []
    cwd = os.getcwd()
    wd = mkdtemp()
    os.chdir(wd)

    # Make the workflow.
    wf = pe.Workflow(name='test')
    # the iterated input node
    inputspec = pe.Node(IdentityInterface(fields=['m', 'n']), name='inputspec')
    inputspec.iterables = [('m', [1, 2]), ('n', [3, 4])]
    inputspec.synchronize = True
    # two pre-join nodes in a parallel iterated path
    inc1 = pe.Node(IncrementInterface(), name='inc1')
    wf.connect(inputspec, 'm', inc1, 'input1')
    inc2 = pe.Node(IncrementInterface(), name='inc2')
    wf.connect(inputspec, 'n', inc2, 'input1')
    # the join node
    join = pe.JoinNode(IdentityInterface(fields=['vector1', 'vector2']),
        joinsource='inputspec', name='join')
    wf.connect(inc1, 'output1', join, 'vector1')
    wf.connect(inc2, 'output1', join, 'vector2')
    # a post-join node
    prod = pe.MapNode(ProductInterface(), name='prod', iterfield=['input1', 'input2'])
    wf.connect(join, 'vector1', prod, 'input1')
    wf.connect(join, 'vector2', prod, 'input2')

    result = wf.run()

    # there are 3 iterables expansions.
    # thus, the expanded graph contains 2 * 2 iteration pre-join nodes, 1 join
    # node and 1 post-join node.
    assert_equal(len(result.nodes()), 6,
                 "The number of expanded nodes is incorrect.")
    # the product inputs are [2, 3] and [4, 5]
    assert_equal(_products, [8, 15],
                 "The post-join products is incorrect: %s." % _products)

    os.chdir(cwd)
    rmtree(wd)

def test_itersource_join_source_node():
    """Test join on an input node which has an ``itersource``."""
    cwd = os.getcwd()
    wd = mkdtemp()
    os.chdir(wd)

    # Make the workflow.
    wf = pe.Workflow(name='test')
    # the iterated input node
    inputspec = pe.Node(IdentityInterface(fields=['n']), name='inputspec')
    inputspec.iterables = [('n', [1, 2])]
    # an intermediate node in the first iteration path
    pre_join1 = pe.Node(IncrementInterface(), name='pre_join1')
    wf.connect(inputspec, 'n', pre_join1, 'input1')
    # an iterable pre-join node with an itersource
    pre_join2 = pe.Node(ProductInterface(), name='pre_join2')
    pre_join2.itersource = ('inputspec', 'n')
    pre_join2.iterables = ('input1', {1: [3, 4], 2: [5, 6]})
    wf.connect(pre_join1, 'output1', pre_join2, 'input2')
    # an intermediate node in the second iteration path
    pre_join3 = pe.Node(IncrementInterface(), name='pre_join3')
    wf.connect(pre_join2, 'output1', pre_join3, 'input1')
    # the join node
    join = pe.JoinNode(IdentityInterface(fields=['vector']),
        joinsource='pre_join2', joinfield='vector', name='join')
    wf.connect(pre_join3, 'output1', join, 'vector')
    # a join successor node
    post_join1 = pe.Node(SumInterface(), name='post_join1')
    wf.connect(join, 'vector', post_join1, 'input1')

    result = wf.run()

    # the expanded graph contains
    # 1 pre_join1 replicate for each inputspec iteration,
    # 2 pre_join2 replicates for each inputspec iteration,
    # 1 pre_join3 for each pre_join2 iteration,
    # 1 join replicate for each inputspec iteration and
    # 1 post_join1 replicate for each join replicate =
    # 2 + (2 * 2) + 4 + 2 + 2 = 14 expansion graph nodes.
    # Nipype factors away the iterable input
    # IdentityInterface but keeps the join IdentityInterface.
    assert_equal(len(result.nodes()), 14,
                 "The number of expanded nodes is incorrect.")
    # The first join inputs are:
    # 1 + (3 * 2) and 1 + (4 * 2)
    # The second join inputs are:
    # 1 + (5 * 3) and 1 + (6 * 3)
    # the post-join nodes execution order is indeterminate;
    # therefore, compare the lists item-wise.
    assert_true([16, 19] in _sum_operands,
                 "The join Sum input is incorrect: %s." % _sum_operands)
    assert_true([7, 9] in _sum_operands,
                 "The join Sum input is incorrect: %s." % _sum_operands)

    os.chdir(cwd)
    rmtree(wd)

def test_itersource_two_join_nodes():
    """Test join with a midstream ``itersource`` and an upstream
    iterable."""
    cwd = os.getcwd()
    wd = mkdtemp()
    os.chdir(wd)

    # Make the workflow.
    wf = pe.Workflow(name='test')
    # the iterated input node
    inputspec = pe.Node(IdentityInterface(fields=['n']), name='inputspec')
    inputspec.iterables = [('n', [1, 2])]
    # an intermediate node in the first iteration path
    pre_join1 = pe.Node(IncrementInterface(), name='pre_join1')
    wf.connect(inputspec, 'n', pre_join1, 'input1')
    # an iterable pre-join node with an itersource
    pre_join2 = pe.Node(ProductInterface(), name='pre_join2')
    pre_join2.itersource = ('inputspec', 'n')
    pre_join2.iterables = ('input1', {1: [3, 4], 2: [5, 6]})
    wf.connect(pre_join1, 'output1', pre_join2, 'input2')
    # an intermediate node in the second iteration path
    pre_join3 = pe.Node(IncrementInterface(), name='pre_join3')
    wf.connect(pre_join2, 'output1', pre_join3, 'input1')
    # the first join node
    join1 = pe.JoinNode(IdentityInterface(fields=['vector']),
        joinsource='pre_join2', joinfield='vector', name='join1')
    wf.connect(pre_join3, 'output1', join1, 'vector')
    # a join successor node
    post_join1 = pe.Node(SumInterface(), name='post_join1')
    wf.connect(join1, 'vector', post_join1, 'input1')
    # a summary join node
    join2 = pe.JoinNode(IdentityInterface(fields=['vector']),
        joinsource='inputspec', joinfield='vector', name='join2')
    wf.connect(post_join1, 'output1', join2, 'vector')

    result = wf.run()

    # the expanded graph contains the 14 test_itersource_join_source_node
    # nodes plus the summary join node.
    assert_equal(len(result.nodes()), 15,
                 "The number of expanded nodes is incorrect.")

    os.chdir(cwd)
    rmtree(wd)


if __name__ == "__main__":
    import nose

    nose.main(defaultTest=__name__)
