from .. import NewNode, NewWorkflow
from ..auxiliary import Function_Interface

import sys, time, os
import numpy as np
import pytest, pdb

python35_only = pytest.mark.skipif(sys.version_info < (3, 5),
                                   reason="requires Python>3.4")

Plugins = ["serial", "mp", "cf", "dask"]

def fun_addtwo(a):
    time.sleep(1)
    if a == 3:
        time.sleep(2)
    return a + 2


def fun_addvar(a, b):
    return a + b



def test_node_1():
    """Node with mandatory arguments only"""
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
    # adding NA to the name of the variable
    assert nn.inputs == {"NA.a": 3}
    assert nn.state._mapper is None


def test_node_3():
    """Node with interface, inputs and mapper"""
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    nn = NewNode(name="NA", interface=interf_addtwo, inputs={"a": [3, 5]}, mapper="a")
    assert nn.mapper == "NA.a"
    assert (nn.inputs["NA.a"] == np.array([3, 5])).all()
    
    assert nn.state._mapper == "NA.a"

    nn.prepare_state_input()
    assert nn.state.state_values([0]) == {"NA.a": 3}
    assert nn.state.state_values([1]) == {"NA.a": 5}


def test_node_4():
    """Node with interface and inputs. mapper set using map method"""
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    nn = NewNode(name="NA", interface=interf_addtwo, inputs={"a": [3, 5]})
    nn.map(mapper="a")
    assert nn.mapper == "NA.a"
    assert (nn.inputs["NA.a"] == np.array([3, 5])).all()

    nn.prepare_state_input()
    assert nn.state._mapper == "NA.a"
    assert nn.state.state_values([0]) == {"NA.a": 3}
    assert nn.state.state_values([1]) == {"NA.a": 5}


def test_node_5():
    """Node with interface, mapper and inputs set with the map method"""
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    nn = NewNode(name="NA", interface=interf_addtwo)
    nn.map(mapper="a", inputs={"a": [3, 5]})
    assert nn.mapper == "NA.a"
    assert (nn.inputs["NA.a"] == np.array([3, 5])).all()

    assert nn.state._mapper == "NA.a"
    nn.prepare_state_input()
    assert nn.state.state_values([0]) == {"NA.a": 3}
    assert nn.state.state_values([1]) == {"NA.a": 5}


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_node_6(plugin):
    """Node with interface, inputs and the simplest mapper, running interface"""
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    nn = NewNode(name="NA", interface=interf_addtwo, base_dir="test_nd6_{}".format(plugin))
    nn.map(mapper="a", inputs={"a": [3, 5]})

    assert nn.mapper == "NA.a"
    assert (nn.inputs["NA.a"] == np.array([3, 5])).all()

    # testing if the node runs properly
    nn.run(plugin=plugin)

    # checking the results
    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
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
    """Node with interface, inputs and scalar mapper, running interface"""
    interf_addvar = Function_Interface(fun_addvar, ["out"])
    nn = NewNode(name="NA", interface=interf_addvar, base_dir="test_nd7_{}".format(plugin))
    # scalar mapper
    nn.map(mapper=("a", "b"), inputs={"a": [3, 5], "b": [2, 1]})

    assert nn.mapper == ("NA.a", "NA.b")
    assert (nn.inputs["NA.a"] == np.array([3, 5])).all()
    assert (nn.inputs["NA.b"] == np.array([2, 1])).all()

    # testing if the node runs properly
    nn.run(plugin=plugin)

    # checking the results
    expected = [({"NA.a": 3, "NA.b": 2}, 5), ({"NA.a": 5, "NA.b": 1}, 6)]
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
    """Node with interface, inputs and vector mapper, running interface"""
    interf_addvar = Function_Interface(fun_addvar, ["out"])
    nn = NewNode(name="NA", interface=interf_addvar, base_dir="test_nd8_{}".format(plugin))
    # [] for outer product
    nn.map(mapper=["a", "b"], inputs={"a": [3, 5], "b": [2, 1]})

    assert nn.mapper == ["NA.a", "NA.b"]
    assert (nn.inputs["NA.a"] == np.array([3, 5])).all()
    assert (nn.inputs["NA.b"] == np.array([2, 1])).all()

    # testing if the node runs properly
    nn.run(plugin=plugin)

    # checking teh results
    expected = [({"NA.a": 3, "NA.b": 1}, 4), ({"NA.a": 3, "NA.b": 2}, 5),
                ({"NA.a": 5, "NA.b": 1}, 6), ({"NA.a": 5, "NA.b": 2}, 7)]
    # to be sure that there is the same order (not sure if node itself should keep the order)
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    nn.result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert nn.result["out"][i][0] == res[0]
        assert nn.result["out"][i][1] == res[1]


# tests for workflows

@python35_only
def test_workflow_0(plugin="serial"):
    """workflow (without run) with one node with a mapper"""
    wf = NewWorkflow(name="wf0", workingdir="test_wf0_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    # defining a node with mapper and inputs first
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")
    na.map(mapper="a", inputs={"a": [3, 5]})
    # one of the way of adding nodes to the workflow
    wf.add_nodes([na])
    assert wf.nodes[0].mapper == "NA.a"
    assert (wf.nodes[0].inputs['NA.a'] == np.array([3, 5])).all()
    assert len(wf.graph.nodes) == 1

@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_1(plugin):
    """workflow with one node with a mapper"""
    wf = NewWorkflow(name="wf1", workingdir="test_wf1_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")
    na.map(mapper="a", inputs={"a": [3, 5]})
    wf.add_nodes([na])

    wf.run(plugin=plugin)

    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_2(plugin):
    """workflow with two nodes, second node without mapper"""
    wf = NewWorkflow(name="wf2", workingdir="test_wf2_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")
    na.map(mapper="a", inputs={"a": [3, 5]})

    # the second node does not have explicit mapper (but keeps the mapper from the NA node)
    interf_addvar = Function_Interface(fun_addvar, ["out"])
    nb = NewNode(name="NB", interface=interf_addvar, inputs={"b": 10}, base_dir="nb")

    # adding 2 nodes and create a connection (as it is now)
    wf.add_nodes([na, nb])
    wf.connect("NA", "out", "NB", "a")

    assert wf.nodes[0].mapper == "NA.a"
    wf.run(plugin=plugin)

    expected_A = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected_A[0][0].keys())
    expected_A.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_A):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]

    # results from NB keeps the "state input" from the first node
    # two elements as in NA
    expected_B = [({"NA.a": 3, "NB.b": 10}, 15), ({"NA.a": 5, "NB.b": 10}, 17)]
    key_sort = list(expected_B[0][0].keys())
    expected_B.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[1].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_B):
        assert wf.nodes[1].result["out"][i][0] == res[0]
        assert wf.nodes[1].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_2a(plugin):
    """workflow with two nodes, second node with a scalar mapper"""
    wf = NewWorkflow(name="wf2", workingdir="test_wf2a_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")
    na.map(mapper="a", inputs={"a": [3, 5]})

    interf_addvar = Function_Interface(fun_addvar, ["out"])
    nb = NewNode(name="NB", interface=interf_addvar, base_dir="nb")
    # explicit scalar mapper between "a" from NA and b
    nb.map(mapper=("NA.a", "b"), inputs={"b": [2, 1]})

    wf.add_nodes([na, nb])
    wf.connect("NA", "out", "NB", "a")

    assert wf.nodes[0].mapper == "NA.a"
    assert wf.nodes[1].mapper == ("NA.a", "NB.b")
    wf.run(plugin=plugin)

    expected_A = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected_A[0][0].keys())
    expected_A.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_A):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]

    # two elements (scalar mapper)
    expected_B = [({"NA.a": 3, "NB.b": 2}, 7), ({"NA.a": 5, "NB.b": 1}, 8)]
    key_sort = list(expected_B[0][0].keys())
    expected_B.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[1].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_B):
        assert wf.nodes[1].result["out"][i][0] == res[0]
        assert wf.nodes[1].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_2b(plugin):
    """workflow with two nodes, second node with a vector mapper"""
    wf = NewWorkflow(name="wf2", workingdir="test_wf2b_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")
    na.map(mapper="a", inputs={"a": [3, 5]})

    interf_addvar = Function_Interface(fun_addvar, ["out"])
    nb = NewNode(name="NB", interface=interf_addvar, base_dir="nb")
    # outer mapper
    nb.map(mapper=["NA.a", "b"], inputs={"b": [2, 1]})

    wf.add_nodes([na, nb])
    wf.connect("NA", "out", "NB", "a")

    assert wf.nodes[0].mapper == "NA.a"
    assert wf.nodes[1].mapper == ["NA.a", "NB.b"]
    wf.run(plugin=plugin)

    expected_A = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected_A[0][0].keys())
    expected_A.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_A):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]

    # four elements (outer product)
    expected_B = [({"NA.a": 3, "NB.b": 1}, 6), ({"NA.a": 3, "NB.b": 2}, 7),
                  ({"NA.a": 5, "NB.b": 1}, 8), ({"NA.a": 5, "NB.b": 2}, 9)]
    key_sort = list(expected_B[0][0].keys())
    expected_B.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[1].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_B):
        assert wf.nodes[1].result["out"][i][0] == res[0]
        assert wf.nodes[1].result["out"][i][1] == res[1]


# using add method to add nodes

@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_3(plugin):
    """using add(node) method"""
    wf = NewWorkflow(name="wf3", workingdir="test_wf3_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")
    na.map(mapper="a", inputs={"a": [3, 5]})
    # using add method (as in the Satra's example) with a node
    wf.add(na)

    assert wf.nodes[0].mapper == "NA.a"
    wf.run(plugin=plugin)

    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_3a(plugin):
    """using add(interface) method"""
    wf = NewWorkflow(name="wf3a", workingdir="test_wf3a_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])

    # using the add method with an interface
    wf.add(interf_addtwo, base_dir="na", mapper="a", inputs={"a": [3, 5]}, name="NA")

    assert wf.nodes[0].mapper == "NA.a"
    wf.run(plugin=plugin)

    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_3b(plugin):
    """using add (function) method"""
    wf = NewWorkflow(name="wf3b", workingdir="test_wf3b_{}".format(plugin))
    # using the add method with a function
    wf.add(fun_addtwo, base_dir="na", mapper="a", inputs={"a": [3, 5]}, name="NA")

    assert wf.nodes[0].mapper == "NA.a"
    wf.run(plugin=plugin)

    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]



@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_4(plugin):
    """ using add(node) method
        using wf.connect to connect two nodes
    """
    wf = NewWorkflow(name="wf4", workingdir="test_wf4_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")
    na.map(mapper="a", inputs={"a": [3, 5]})
    wf.add(na)

    interf_addvar = Function_Interface(fun_addvar, ["out"])
    nb = NewNode(name="NB", interface=interf_addvar, base_dir="nb")
    # explicit mapper with a variable from the previous node
    # providing inputs with b
    nb.map(mapper=("NA.a", "b"), inputs={"b": [2, 1]})
    wf.add(nb)
    # connect method as it is in the current version
    wf.connect("NA", "out", "NB", "a")

    wf.run(plugin=plugin)

    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]

    expected_B = [({"NA.a": 3, "NB.b": 2}, 7), ({"NA.a": 5, "NB.b": 1}, 8)]
    key_sort = list(expected_B[0][0].keys())
    expected_B.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[1].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_B):
        assert wf.nodes[1].result["out"][i][0] == res[0]
        assert wf.nodes[1].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_4a(plugin):
    """ using add(node) method with kwarg arg to connect nodes (instead of wf.connect) """
    wf = NewWorkflow(name="wf4a", workingdir="test_wf4a_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")
    na.map(mapper="a", inputs={"a": [3, 5]})
    wf.add(na)

    interf_addvar = Function_Interface(fun_addvar, ["out"])
    nb = NewNode(name="NB", interface=interf_addvar, base_dir="nb")
    # explicit mapper with a variable from the previous node
    nb.map(mapper=("NA.a", "b"), inputs={"b": [2, 1]})
    # instead of "connect", using kwrg argument in the add method as in the example
    wf.add(nb, a="NA.out")

    wf.run(plugin=plugin)

    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]

    expected_B = [({"NA.a": 3, "NB.b": 2}, 7), ({"NA.a": 5, "NB.b": 1}, 8)]
    key_sort = list(expected_B[0][0].keys())
    expected_B.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[1].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_B):
        assert wf.nodes[1].result["out"][i][0] == res[0]
        assert wf.nodes[1].result["out"][i][1] == res[1]



# using map after add method

@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_5(plugin):
    """using a map method for one node"""
    wf = NewWorkflow(name="wf5", workingdir="test_wf5_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")

    wf.add(na)
    # using the map method after add (using mapper for the last added node as default)
    wf.map(mapper="a", inputs={"a": [3, 5]})
    wf.run(plugin=plugin)

    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_5a(plugin):
    """using a map method for one node (using add and map in one chain)"""
    wf = NewWorkflow(name="wf5a", workingdir="test_wf5a_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")

    wf.add(na).map(mapper="a", inputs={"a": [3, 5]})
    wf.run(plugin=plugin)

    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_6(plugin):
    """using a map method for two nodes (using last added node as default)"""
    wf = NewWorkflow(name="wf6", workingdir="test_wf6_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")

    interf_addvar = Function_Interface(fun_addvar, ["out"])
    nb = NewNode(name="NB", interface=interf_addvar, base_dir="nb")
    # using the map methods after add (using mapper for the last added nodes as default)
    wf.add(na)
    wf.map(mapper="a", inputs={"a": [3, 5]})
    wf.add(nb)
    wf.map(mapper=("NA.a", "b"), inputs={"b": [2, 1]})
    wf.connect("NA", "out", "NB", "a")
    wf.run(plugin=plugin)

    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]

    expected_B = [({"NA.a": 3, "NB.b": 2}, 7), ({"NA.a": 5, "NB.b": 1}, 8)]
    key_sort = list(expected_B[0][0].keys())
    expected_B.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[1].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_B):
        assert wf.nodes[1].result["out"][i][0] == res[0]
        assert wf.nodes[1].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_6a(plugin):
    """using a map method for two nodes (specifying the node)"""
    wf = NewWorkflow(name="wf6a", workingdir="test_wf6a_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")

    interf_addvar = Function_Interface(fun_addvar, ["out"])
    nb = NewNode(name="NB", interface=interf_addvar, base_dir="nb")
    # using the map method after add (specifying the node)
    wf.add(na)
    wf.add(nb)
    wf.map(mapper="a", inputs={"a": [3, 5]}, node=na)
    wf.map(mapper=("NA.a", "b"), inputs={"b": [2, 1]}, node=nb)
    wf.connect("NA", "out", "NB", "a")
    wf.run(plugin=plugin)

    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]

    expected_B = [({"NA.a": 3, "NB.b": 2}, 7), ({"NA.a": 5, "NB.b": 1}, 8)]
    key_sort = list(expected_B[0][0].keys())
    expected_B.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[1].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_B):
        assert wf.nodes[1].result["out"][i][0] == res[0]
        assert wf.nodes[1].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_6b(plugin):
    """using a map method for two nodes (specifying the node), using kwarg arg instead of connect"""
    wf = NewWorkflow(name="wf6b", workingdir="test_wf6b_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")

    interf_addvar = Function_Interface(fun_addvar, ["out"])
    nb = NewNode(name="NB", interface=interf_addvar, base_dir="nb")

    wf.add(na)
    wf.add(nb, a="NA.out")
    wf.map(mapper="a", inputs={"a": [3, 5]}, node=na)
    wf.map(mapper=("NA.a", "b"), inputs={"b": [2, 1]}, node=nb)
    wf.run(plugin=plugin)

    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]

    expected_B = [({"NA.a": 3, "NB.b": 2}, 7), ({"NA.a": 5, "NB.b": 1}, 8)]
    key_sort = list(expected_B[0][0].keys())
    expected_B.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[1].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_B):
        assert wf.nodes[1].result["out"][i][0] == res[0]
        assert wf.nodes[1].result["out"][i][1] == res[1]


# tests for a workflow that have its own input

@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_7(plugin):
    """using inputs for workflow and connect_workflow"""
    # adding inputs to the workflow directly
    wf = NewWorkflow(name="wf7", inputs={"wf_a": [3, 5]}, workingdir="test_wf7_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")

    wf.add(na)
    # connecting the node with inputs from the workflow
    wf.connect_workflow("NA", "wf_a","a")
    wf.map(mapper="a")
    wf.run(plugin=plugin)

    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_7a(plugin):
    """using inputs for workflow and connect(None...)"""
    # adding inputs to the workflow directly
    wf = NewWorkflow(name="wf7a", inputs={"wf_a": [3, 5]}, workingdir="test_wf7a_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")

    wf.add(na)
    # if connect has None as the first arg, it is the same as connect_workflow
    wf.connect(None, "wf_a", "NA", "a")
    wf.map(mapper="a")
    wf.run(plugin=plugin)

    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_7b(plugin):
    """using inputs for workflow and kwarg arg in add (instead of connect)"""
    wf = NewWorkflow(name="wf7b", inputs={"wf_a": [3, 5]}, workingdir="test_wf7b_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")
    # using kwrg argument in the add method (instead of connect or connect_workflow
    wf.add(na, a="wf_a")
    wf.map(mapper="a")
    wf.run(plugin=plugin)

    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_8(plugin):
    """using inputs for workflow and connect_workflow for the second node"""
    wf = NewWorkflow(name="wf8", workingdir="test_wf8_{}".format(plugin), inputs={"b": 10})
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")
    na.map(mapper="a", inputs={"a": [3, 5]})

    interf_addvar = Function_Interface(fun_addvar, ["out"])
    nb = NewNode(name="NB", interface=interf_addvar, base_dir="nb")

    wf.add_nodes([na, nb])
    wf.connect("NA", "out", "NB", "a")
    wf.connect_workflow("NB", "b", "b")
    assert wf.nodes[0].mapper == "NA.a"
    wf.run(plugin=plugin)

    expected_A = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected_A[0][0].keys())
    expected_A.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_A):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]


    expected_B = [({"NA.a": 3, "NB.b": 10}, 15), ({"NA.a": 5, "NB.b": 10}, 17)]
    key_sort = list(expected_B[0][0].keys())
    expected_B.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[1].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_B):
        assert wf.nodes[1].result["out"][i][0] == res[0]
        assert wf.nodes[1].result["out"][i][1] == res[1]


# testing if _NA in mapper works, using interfaces in add

@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_9(plugin):
    """using add(interface) method and mapper from previous nodes"""
    wf = NewWorkflow(name="wf9", workingdir="test_wf9_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    wf.add(name="NA", runnable=interf_addtwo, base_dir="na").map(mapper="a", inputs={"a": [3, 5]})
    interf_addvar = Function_Interface(fun_addvar, ["out"])
    # _NA means that I'm using mapper from the NA node, it's the same as ("NA.a", "b")
    wf.add(name="NB", runnable=interf_addvar, base_dir="nb", a="NA.out").map(mapper=("_NA", "b"), inputs={"b": [2, 1]})
    wf.run(plugin=plugin)

    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]

    expected_B = [({"NA.a": 3, "NB.b": 2}, 7), ({"NA.a": 5, "NB.b": 1}, 8)]
    key_sort = list(expected_B[0][0].keys())
    expected_B.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[1].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_B):
        assert wf.nodes[1].result["out"][i][0] == res[0]
        assert wf.nodes[1].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_10(plugin):
    """using add(interface) method and scalar mapper from previous nodes"""
    wf = NewWorkflow(name="wf10", workingdir="test_wf10_{}".format(plugin))
    interf_addvar1 = Function_Interface(fun_addvar, ["out"])
    wf.add(name="NA", runnable=interf_addvar1, base_dir="na").map(mapper=("a", "b"), inputs={"a": [3, 5], "b": [0, 10]})
    interf_addvar2 = Function_Interface(fun_addvar, ["out"])
    # _NA means that I'm using mapper from the NA node, it's the same as (("NA.a", NA.b), "b")
    wf.add(name="NB", runnable=interf_addvar2, base_dir="nb", a="NA.out").map(mapper=("_NA", "b"), inputs={"b": [2, 1]})
    wf.run(plugin=plugin)

    expected = [({"NA.a": 3, "NA.b": 0}, 3), ({"NA.a": 5, "NA.b": 10}, 15)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]

    expected_B = [({"NA.a": 3, "NA.b": 0, "NB.b": 2}, 5), ({"NA.a": 5, "NA.b": 10, "NB.b": 1}, 16)]
    key_sort = list(expected_B[0][0].keys())
    expected_B.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[1].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_B):
        assert wf.nodes[1].result["out"][i][0] == res[0]
        assert wf.nodes[1].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_10a(plugin):
    """using add(interface) method and vector mapper from previous nodes"""
    wf = NewWorkflow(name="wf10a", workingdir="test_wf10a_{}".format(plugin))
    interf_addvar1 = Function_Interface(fun_addvar, ["out"])
    wf.add(name="NA", runnable=interf_addvar1, base_dir="na").map(mapper=["a", "b"], inputs={"a": [3, 5], "b": [0, 10]})
    interf_addvar2 = Function_Interface(fun_addvar, ["out"])
    # _NA means that I'm using mapper from the NA node, it's the same as (["NA.a", NA.b], "b")
    wf.add(name="NB", runnable=interf_addvar2, base_dir="nb", a="NA.out").map(mapper=("_NA", "b"), inputs={"b": [[2, 1], [0, 0]]})
    wf.run(plugin=plugin)

    expected = [({"NA.a": 3, "NA.b": 0}, 3), ({"NA.a": 3, "NA.b": 10}, 13),
                ({"NA.a": 5, "NA.b": 0}, 5), ({"NA.a": 5, "NA.b": 10}, 15)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]

    expected_B = [({"NA.a": 3, "NA.b": 0, "NB.b": 2}, 5), ({"NA.a": 3, "NA.b": 10, "NB.b": 1}, 14),
                  ({"NA.a": 5, "NA.b": 0, "NB.b": 0}, 5), ({"NA.a": 5, "NA.b": 10, "NB.b": 0}, 15)]
    key_sort = list(expected_B[0][0].keys())
    expected_B.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[1].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_B):
        assert wf.nodes[1].result["out"][i][0] == res[0]
        assert wf.nodes[1].result["out"][i][1] == res[1]


@pytest.mark.parametrize("plugin", Plugins)
@python35_only
def test_workflow_11(plugin):
    """using add(interface) method and vector mapper from previous two nodes"""
    wf = NewWorkflow(name="wf11", workingdir="test_wf11_{}".format(plugin))
    interf_addvar1 = Function_Interface(fun_addvar, ["out"])
    wf.add(name="NA", runnable=interf_addvar1, base_dir="na").map(mapper=("a", "b"), inputs={"a": [3, 5], "b": [0, 10]})
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    wf.add(name="NB", runnable=interf_addtwo, base_dir="nb").map(mapper="a", inputs={"a": [2, 1]})
    interf_addvar2 = Function_Interface(fun_addvar, ["out"])
    # _NA, _NB means that I'm using mappers from the NA/NB nodes, it's the same as [("NA.a", NA.b), "NB.a"]
    wf.add(name="NC", runnable=interf_addvar2, base_dir="nc", a="NA.out", b="NB.out").map(mapper=["_NA", "_NB"])
    wf.run(plugin=plugin)

    expected = [({"NA.a": 3, "NA.b": 0}, 3), ({"NA.a": 5, "NA.b": 10}, 15)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.nodes[0].result["out"][i][0] == res[0]
        assert wf.nodes[0].result["out"][i][1] == res[1]


    expected_C = [({"NA.a": 3, "NA.b": 0, "NB.a": 1}, 6),   ({"NA.a": 3, "NA.b": 0, "NB.a": 2}, 7),
                  ({"NA.a": 5, "NA.b": 10, "NB.a": 1}, 18), ({"NA.a": 5, "NA.b": 10, "NB.a": 2}, 19)]
    key_sort = list(expected_C[0][0].keys())
    expected_C.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.nodes[2].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected_C):
        assert wf.nodes[2].result["out"][i][0] == res[0]
        assert wf.nodes[2].result["out"][i][1] == res[1]


# tests for a workflow that have its own input and mapper
#WIP

#@pytest.mark.parametrize("plugin", Plugins)
@python35_only
#@pytest.mark.xfail(reason="mapper in workflow still not implemented")
def test_workflow_12(plugin="serial"):
    """using inputs for workflow and connect_workflow"""
    wf = NewWorkflow(name="wf9", inputs={"wf_a": [3, 5]}, mapper="wf_a", workingdir="test_wf12_{}".format(plugin))
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    na = NewNode(name="NA", interface=interf_addtwo, base_dir="na")
    wf.add(na)
    wf.connect_workflow("NA", "wf_a", "a")

    assert len(wf.inner_workflows) == 2
    assert wf.inner_workflows[0].mapper is None
    assert wf.inner_workflows[0].inputs == {'wf9(0,).wf_a': 3}
    assert wf.inner_workflows[1].inputs == {'wf9(1,).wf_a': 5}
    wf.run(plugin=plugin)
    expected = [({"NA.a": 3}, 5), ({"NA.a": 5}, 7)]
    key_sort = list(expected[0][0].keys())
    expected.sort(key=lambda t: [t[0][key] for key in key_sort])
    wf.inner_workflows[0].nodes[0].result["out"].sort(key=lambda t: [t[0][key] for key in key_sort])
    for i, res in enumerate(expected):
        assert wf.inner_workflows[i].nodes[0].result["out"][0][0] == res[0]
        assert wf.inner_workflows[i].nodes[0].result["out"][0][1] == res[1]
