from .. import NewNode
from ..auxiliary import Function_Interface

import numpy as np
import pytest, pdb

def fun_addtwo(a):
    return a + 2


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
    assert nn.state.state_values([0]) == {"NA-a": 3}
    assert nn.state.state_values([1]) == {"NA-a": 5}


def test_node_4():
    """Node with interface and inputs"""
    interf_addtwo = Function_Interface(fun_addtwo, ["out"])
    nn = NewNode(name="NA", interface=interf_addtwo, inputs={"a": [3, 5]})
    nn.map(mapper="a")
    assert nn.mapper == "NA-a"
    assert (nn.inputs["NA-a"] == np.array([3, 5])).all()

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
    assert nn.state.state_values([0]) == {"NA-a": 3}
    assert nn.state.state_values([1]) == {"NA-a": 5}


Plugins = ["mp", "serial", "cf", "dask"] 

@pytest.mark.parametrize("plugin", Plugins)
def test_node_6(plugin):
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
    for i, res in enumerate(expected):
        assert nn.result["out"][i][0] == res[0]
        assert nn.result["out"][i][1] == res[1]
