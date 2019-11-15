# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import pytest
from ..base import EngineBase
from ....interfaces import base as nib
from ....interfaces import utility as niu
from ... import engine as pe


class InputSpec(nib.TraitedSpec):
    input1 = nib.traits.Int(desc="a random int")
    input2 = nib.traits.Int(desc="a random int")
    input_file = nib.File(desc="Random File")


class OutputSpec(nib.TraitedSpec):
    output1 = nib.traits.List(nib.traits.Int, desc="outputs")


class EngineTestInterface(nib.SimpleInterface):
    input_spec = InputSpec
    output_spec = OutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        self._results["output1"] = [1, self.inputs.input1]
        return runtime


@pytest.mark.parametrize("name", ["valid1", "valid_node", "valid-node", "ValidNode0"])
def test_create(name):
    base = EngineBase(name=name)
    assert base.name == name


@pytest.mark.parametrize(
    "name", ["invalid*1", "invalid.1", "invalid@", "in/valid", None]
)
def test_create_invalid(name):
    with pytest.raises(ValueError):
        EngineBase(name=name)


def test_hierarchy():
    base = EngineBase(name="nodename")
    base._hierarchy = "some.history.behind"

    assert base.name == "nodename"
    assert base.fullname == "some.history.behind.nodename"


def test_clone():
    base = EngineBase(name="nodename")
    base2 = base.clone("newnodename")

    assert (
        base.base_dir == base2.base_dir
        and base.config == base2.config
        and base2.name == "newnodename"
    )

    with pytest.raises(ValueError):
        base.clone("nodename")


def test_clone_node_iterables(tmpdir):
    tmpdir.chdir()

    def addstr(string):
        return "%s + 2" % string

    subject_list = ["sub-001", "sub-002"]
    inputnode = pe.Node(niu.IdentityInterface(fields=["subject"]), name="inputnode")
    inputnode.iterables = [("subject", subject_list)]

    node_1 = pe.Node(
        niu.Function(input_names="string", output_names="string", function=addstr),
        name="node_1",
    )
    node_2 = node_1.clone("node_2")

    workflow = pe.Workflow(name="iter_clone_wf")
    workflow.connect(
        [
            (inputnode, node_1, [("subject", "string")]),
            (node_1, node_2, [("string", "string")]),
        ]
    )
    workflow.run()
