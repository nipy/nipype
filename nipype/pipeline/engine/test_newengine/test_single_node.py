from supernode import Node # or whatever

import numpy as np

import pytest, pdb

def fun1(a, **dict):
    return a**2

def fun2(a, **dict):
    pow = np.arange(4)
    return a**pow

def fun3(a, b, **dict):
    return a * b



@pytest.mark.parametrize("inputs_dict, expected_output", [ 
        ({"a": [3, 4, 5]}, [9, 16, 25]),
        ({"a": [[3, 4, 5], [6, 7, 8]]}, [[9, 16, 25], [36, 49, 64]]),
        ({"a": np.array([3, 4, 5])}, [9, 16, 25]),
        ])
def test_singlenode_1(inputs_dict, expected_output):
    N  = Node(inputs=inuts_dict, mapper="a", interface=fun1)
    N.run()
    assert (N.outputs["out"] == expected_output).all()
    

@pytest.mark.parametrize("inputs_dict, expected_output", [
        ({"a": [3, 4, 5]}, [9, 16, 25]),
        ({"a": [[3, 4, 5], [6, 7, 8]]}, [[9, 16, 25], [36, 49, 64]]),
        ({"a": np.array([3, 4, 5])}, [9, 16, 25]),
        ])
def test_singlenode_1a(inputs_dict, expected_output):
    N  = Node(inputs=inputs_dict, mapper="a", interface=fun1)
    # testing if you can set inputs outside __init__
    N.inputs = inputs_dic
    N.run()
    assert (N.outputs["out"] == expected_output).all()


def test_single_node_1b():
    # how to name or rename (from a default name, e.g. "out") outputs 
    sn = Node(interface=my_function_1, mapper='a', output_name=["out_1"])
    sn.inputs = {"a" : [3, 1, 8]}
    sn.run()
    assert (sn.outputs["out_1"] == [9, 1, 64]).all()


@pytest.mark.parametrize("inputs_dict, expected_output", [
        ({"a": [3, 4, 5]}, [[1, 3, 9, 27], [1, 4, 16, 64], [1, 5, 25, 125]]),
        ({"a": [[3, 4, 5], [6, 7, 8]]}, 
         [[[1, 3, 9, 27], [1, 4, 16, 64], [1, 5, 25, 125]], 
          [[1, 6, 36, 196], [1, 7, 49, 343], [1, 8, 64, 512]]]),
        ({"a": np.array([3, 4, 5])}, [[1, 3, 9, 27], [1, 4, 16, 64], [1, 5, 25, 125]]),
        ])
def test_singlenode_2(inputs_dict, expected_output):
    N  = Node(inputs=inputs_dict, mapper="a", interface=fun2)
    N.run()
    assert (N.outputs["out"] == expected_output).all()


@pytest.mark.parametrize("inputs_dict, expected_output", [
        ({"a":[3, 1, 8], "b":[0, 1, 2]}, [0, 1, 16]),
        ({"a":[3, 1, 8], "b":[2]}, [6, 2, 16]),
        ])
def test_single_node_3(inputs_dict, expected_output):
    N = Node(interface=fun3, mapper='(a,b)')
    N.inputs = inputs_dict
    N.run()
    assert (N.outputs["out"] == expected_output).all()


@pytest.mark.parametrize("inputs_dict, expected_output", [
        ({"a":[3, 1], "b":[1, 2, 4]}, [[3, 6, 12], [1, 2, 4]]),
        ({"a":[[3, 1]], "b":[1, 2, 4]},[[[3, 6, 12], [1, 2, 4]]]),
        ({"a":[[3, 1], [30, 10]], "b":[1, 2, 4]},
         [[[3, 6, 12], [1, 2, 4]],[[30, 60, 120],[10, 20, 40]]]),
        ({"a":[3, 1], "b":[2]}, np.array([[6], [2]])),
        ])
def test_single_node_4(inputs_dict, expected_output):
    sn = Node(interface=fun3, mapper='[a,b]')
    sn.inputs = inputs_dict
    sn.run()
    assert (sn.outputs["out"] == expected_output).all()


@pytest.mark.parametrize("inputs_dict", [
        {"a":[[3, 1], [0,0]], "b":[1, 2, 0]},
        {"a":[[3, 1], [0,0], [1, 1]], "b":[1, 2, 0]}, # think if this should work
        {"a":[[3, 1, 1], [0,0, 0]], "b":[1, 2, 0]},  # think if this should work
        ])
def test_single_node_wrong_input(inputs_dict):
    with pytest.raises(Exception):
        sn = Node(interface=fun3, mapper='(a,b)')
        sn.inputs = inputs_dict
        sn.run()

def test_single_node_wrong_key():
    with pytest.raises(Exception):
        sn = Node(interface=fun3, mapper='(a,b)')
        sn.inputs = {"a":[3], "c":[0]}
