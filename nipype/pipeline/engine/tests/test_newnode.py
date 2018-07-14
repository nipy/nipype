from .. import NewNode
from ..auxiliary import Function_Interface

import numpy as np
import pytest, pdb

def fun_addtwo(a):
    return a + 2

interf_addtwo = Function_Interface(fun_addtwo, ["out"])

def test_node_1():
    """Node with only mandatory arguments"""
    nn = NewNode(name="N_A", interface=interf_addtwo)
    assert nn.mapper is None
    assert nn.inputs == {}
    assert nn.state._mapper is None


def test_node_2():
    """Node with interface and inputs"""
    nn = NewNode(name="N_A", interface=interf_addtwo, inputs={"a": 3})
    assert nn.mapper is None
    assert nn.inputs == {"N_A-a": 3}
    assert nn.state._mapper is None


def test_node_3():
    """Node with interface and inputs"""
    nn = NewNode(name="N_A", interface=interf_addtwo, inputs={"a": [3, 5]}, mapper="a")
    assert nn.mapper == "N_A-a"
    assert (nn.inputs["N_A-a"] == np.array([3, 5])).all()
    
    assert nn.state._mapper == "N_A-a"
    assert nn.state.state_values([0]) == {"N_A-a": 3}
    assert nn.state.state_values([1]) == {"N_A-a": 5}


def test_node_4():
    """Node with interface and inputs"""
    nn = NewNode(name="N_A", interface=interf_addtwo, inputs={"a": [3, 5]})
    nn.map(mapper="a")
    assert nn.mapper == "N_A-a"
    assert (nn.inputs["N_A-a"] == np.array([3, 5])).all()

    assert nn.state._mapper == "N_A-a"
    assert nn.state.state_values([0]) == {"N_A-a": 3}
    assert nn.state.state_values([1]) == {"N_A-a": 5}


def test_node_5():
    """Node with interface and inputs"""
    nn = NewNode(name="N_A", interface=interf_addtwo)
    nn.map(mapper="a", inputs={"a": [3, 5]})
    assert nn.mapper == "N_A-a"
    assert (nn.inputs["N_A-a"] == np.array([3, 5])).all()

    assert nn.state._mapper == "N_A-a"
    assert nn.state.state_values([0]) == {"N_A-a": 3}
    assert nn.state.state_values([1]) == {"N_A-a": 5}
    pdb.set_trace()
