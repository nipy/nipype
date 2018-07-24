from .. import NewNode, NewWorkflow
from ..auxiliary import Function_Interface

import sys, time
import numpy as np
import pytest, pdb

python35_only = pytest.mark.skipif(sys.version_info < (3, 5),
                                   reason="requires Python>3.4")


def fun_addtwo(a):
    time.sleep(3)
    return a + 2


def fun_addvar(a, b):
    return a + b



def test_node_1():
    """Node with only mandatory arguments"""
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    nn = NewNode(name="NA", interface=interf_addtwo)
    assert nn.mapper is None
    assert nn.inputs == {}
    assert nn.state._mapper is None


def test_node_2():
    """Node with interface and inputs"""
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    nn = NewNode(name="NA", interface=interf_addtwo, inputs={"a": 3})
    assert nn.mapper is None
    assert nn.inputs == {"NA-a": 3}
    assert nn.state._mapper is None


def test_node_3():
    """Node with interface and inputs"""
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    nn = NewNode(name="NA", interface=interf_addtwo, inputs={"a": [3, 5]}, mapper="a")
    assert nn.mapper == "NA-a"
    assert (nn.inputs["NA-a"] == np.array([3, 5])).all()
    
    assert nn.state._mapper == "NA-a"

    nn.prepare_state_input()
    assert nn.state.state_values([0]) == {"NA-a": 3}
    assert nn.state.state_values([1]) == {"NA-a": 5}


def test_node_4():
    """Node with interface and inputs"""
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    nn = NewNode(name="NA", interface=interf_addtwo, inputs={"a": [3, 5]})
    nn.map(mapper="a")
    assert nn.mapper == "NA-a"
    assert (nn.inputs["NA-a"] == np.array([3, 5])).all()

    nn.prepare_state_input()
    assert nn.state._mapper == "NA-a"
    assert nn.state.state_values([0]) == {"NA-a": 3}
    assert nn.state.state_values([1]) == {"NA-a": 5}


def test_node_5():
    """Node with interface and inputs"""
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    nn = NewNode(name="NA", interface=interf_addtwo)
    nn.map(mapper="a", inputs={"a": [3, 5]})
    assert nn.mapper == "NA-a"
    assert (nn.inputs["NA-a"] == np.array([3, 5])).all()

    assert nn.state._mapper == "NA-a"
    nn.prepare_state_input()
    assert nn.state.state_values([0]) == {"NA-a": 3}
    assert nn.state.state_values([1]) == {"NA-a": 5}


Plugins = ["mp", "serial", "cf", "dask"] 

#@pytest.mark.parametrize("plugin", Plugins)
#@python35_only
def test_node_6(plugin="serial"):
    """Node with interface and inputs, running interface"""
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    nn = NewNode(name="NA", interface=interf_addtwo, base_dir="test6_{}".format(plugin))
    nn.map(mapper="a", inputs={"a": [3, 5]})

    assert nn.mapper == "NA-a"
    assert (nn.inputs["NA-a"] == np.array([3, 5])).all()

    # testing if the node runs properly
    nn.run(plugin=plugin)

    # checking teh results
    expected = [({"NA-a": 3}, 5), ({"NA-a": 5}, 7)]
    # to be sure that there is the same order (not sure if node itself should keep the order)
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    nn.result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert nn.result["out"][i][0] == res[0]
        assert nn.result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_node_7(plugin):
    """Node with interface and inputs, running interface"""
    interf_addvar = Function_Interface(fun_addvar, ["out"])
    nn = NewNode(name="NA", interface=interf_addvar, base_dir="test7_{}".format(plugin))
    nn.map(mapper=("a", "b"), inputs={"a": [3, 5], "b": [2, 1]})

    assert nn.mapper == ("NA-a", "NA-b")
    assert (nn.inputs["NA-a"] == np.array([3, 5])).all()
    assert (nn.inputs["NA-b"] == np.array([2, 1])).all()

    # testing if the node runs properly
    nn.run(plugin=plugin)

    # checking teh results
    expected = [({"NA-a": 3, "NA-b": 2}, 5), ({"NA-a": 5, "NA-b": 1}, 6)]
    # to be sure that there is the same order (not sure if node itself should keep the order)
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    nn.result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert nn.result["out"][i][0] == res[0]
        assert nn.result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_node_8(plugin):
    """Node with interface and inputs, running interface"""
    interf_addvar = Function_Interface(fun_addvar, ["out"])
    nn = NewNode(name="NA", interface=interf_addvar, base_dir="test8_{}".format(plugin))
    nn.map(mapper=["a", "b"], inputs={"a": [3, 5], "b": [2, 1]})

    assert nn.mapper == ["NA-a", "NA-b"]
    assert (nn.inputs["NA-a"] == np.array([3, 5])).all()
    assert (nn.inputs["NA-b"] == np.array([2, 1])).all()

    # testing if the node runs properly
    nn.run(plugin=plugin)

    # checking teh results
    expected = [({"NA-a": 3, "NA-b": 1}, 4), ({"NA-a": 3, "NA-b": 2}, 5),
                ({"NA-a": 5, "NA-b": 1}, 6), ({"NA-a": 5, "NA-b": 2}, 7)]
    # to be sure that there is the same order (not sure if node itself should keep the order)
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    nn.result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert nn.result["out"][i][0] == res[0]
        assert nn.result["out"][i][1] == res[1]


# tests for workflows that set mapper to node that are later added to a workflow

@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_1(plugin):
    """one node with a mapper"""
    wf = NewWorkflow(name="wf1", workingdir="test_wf1_".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")
    na.map(mapper="a", inputs={"a": [3, 5]})
    wf.add_nodes([na])
    assert wf.nodes[0].mapper == "NA-a"
    wf.run(plugin=plugin)

    expected = [({"NA-a": 3}, 5), ({"NA-a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_2(plugin):
    """workflow with 2 nodes, second node without mapper"""
    wf = NewWorkflow(name="wf2", workingdir="test_wf2_".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")
    na.map(mapper="a", inputs={"a": [3, 5]})

    interf_addvar = Function_Interface(fun_addvar, ["out"])
    nb = NewNode(name="NB", interface=interf_addvar, inputs={"b": 10}, base_dir="nb")

    wf.add_nodes([na, nb])
    wf.connect(na, "out", nb, "a")

    assert wf.nodes[0].mapper == "NA-a"
    wf.run(plugin=plugin)

    expected_A = [({"NA-a": 3}, 5), ({"NA-a": 5}, 7)]
    key_sort = list(expected_A[0][0].keys())
    expected_A.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_A):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]


    expected_B = [({"NA-a": 3, "NB-b": 10}, 15), ({"NA-a": 5, "NB-b": 10}, 17)]
    key_sort = list(expected_B[0][0].keys())
    expected_B.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[1].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_B):
        assert wf.nodes[1].result["out"][i][0] == res[0]
        assert wf.nodes[1].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_2a(plugin):
    """workflow with 2 nodes, second node with a scalar mapper"""
    wf = NewWorkflow(name="wf2", workingdir="test_wf2a_".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")
    na.map(mapper="a", inputs={"a": [3, 5]})

    interf_addvar = Function_Interface(fun_addvar, ["out"])
    nb = NewNode(name="NB", interface=interf_addvar, base_dir="nb")
    nb.map(mapper=("NA-a", "b"), inputs={"b": [2, 1]})

    wf.add_nodes([na, nb])
    wf.connect(na, "out", nb, "a")

    assert wf.nodes[0].mapper == "NA-a"
    wf.run(plugin=plugin)

    expected_A = [({"NA-a": 3}, 5), ({"NA-a": 5}, 7)]
    key_sort = list(expected_A[0][0].keys())
    expected_A.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_A):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]

    expected_B = [({"NA-a": 3, "NB-b": 2}, 7), ({"NA-a": 5, "NB-b": 1}, 8)]
    key_sort = list(expected_B[0][0].keys())
    expected_B.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[1].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_B):
        assert wf.nodes[1].result["out"][i][0] == res[0]
        assert wf.nodes[1].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_2b(plugin):
    """workflow with 2 nodes, second node with a vector mapper"""
    wf = NewWorkflow(name="wf2", workingdir="test_wf2b_".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")
    na.map(mapper="a", inputs={"a": [3, 5]})

    interf_addvar = Function_Interface(fun_addvar, ["out"])
    nb = NewNode(name="NB", interface=interf_addvar, base_dir="nb")
    nb.map(mapper=["NA-a", "b"], inputs={"b": [2, 1]})


    wf.add_nodes([na, nb])
    wf.connect(na, "out", nb, "a")

    assert wf.nodes[0].mapper == "NA-a"
    wf.run(plugin=plugin)

    expected_A = [({"NA-a": 3}, 5), ({"NA-a": 5}, 7)]
    key_sort = list(expected_A[0][0].keys())
    expected_A.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_A):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]


    expected_B = [({"NA-a": 3, "NB-b": 1}, 6), ({"NA-a": 3, "NB-b": 2}, 7),
                  ({"NA-a": 5, "NB-b": 1}, 8), ({"NA-a": 5, "NB-b": 2}, 9)]
    key_sort = list(expected_B[0][0].keys())
    expected_B.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[1].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_B):
        assert wf.nodes[1].result["out"][i][0] == res[0]
        assert wf.nodes[1].result["out"][i][1] == res[1]
