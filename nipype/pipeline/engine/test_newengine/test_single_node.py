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
        ({"a": [3, 4, 5]}, [(["a=3"], 9), (["a=4"], 16), (["a=5"], 25)]), 
        # do we want to allow 2D inputs a, when mapper="a"?
        #({"a": [[3, 4, 5], [6, 7, 8]]}, [([3, 4, 5], [9, 16, 25]), ([6, 7, 8], [36, 49, 64])]),
        ({"a": np.array([3, 4, 5])}, [(["a=3"], 9), (["a=4"], 16), (["a=5"], 25)]),
        ])
def test_singlenode_1(inputs_dict, expected_output):
    N  = Node(inputs=inuts_dict, mapper="a", interface=fun1)
    N.run()
    
    for (i, out) in enumerate(N.output["out"]):
        assert out[0] == expected_output[i][0] # checking state values
        assert (out[1] == expected_output[i][1]).all() # assuming that output value is an array (all() is used)

    

@pytest.mark.parametrize("inputs_dict, expected_output", [
        ({"a": [3, 4, 5]}, [(["a=3"], 9), (["a=4"], 16), (["a=5"], 25)]),
        ({"a": np.array([3, 4, 5])}, [(["a=3"], 9), (["a=4"], 16), (["a=5"], 25)]),
        ])
def test_singlenode_1a(inputs_dict, expected_output):
    N  = Node(mapper="a", interface=fun1)
    # testing if you can set inputs outside __init__
    N.inputs = inputs_dict
    N.run()

    for (i, out) in enumerate(N.output["out"]):
        assert out[0] == expected_output[i][0] 
        assert (out[1] == expected_output[i][1]).all()



@pytest.mark.xfail
def test_single_node_1b():
    # how to name or rename (from a default name, e.g. "out") outputs 
    sn = Node(interface=my_function_1, mapper='a', output_name=["out_1"])
    sn.inputs = {"a" : [3, 1, 8]}
    sn.run()
    assert (sn.outputs["out_1"] == [(["a=3"], 9), (["a=1"], 1), (["a=8"], 64)]).all()


@pytest.mark.parametrize("inputs_dict, expected_output", [
        ({"a": [3, 4, 5]}, [(["a=3"], [1, 3, 9, 27]), (["a=4"], [1, 4, 16, 64]), (["a=5"], [1, 5, 25, 125])]),
        ])
def test_singlenode_2(inputs_dict, expected_output):
    N  = Node(inputs=inputs_dict, mapper="a", interface=fun2)
    N.run()

    for (i, out) in enumerate(N.output["out"]):
        assert out[0] == expected_output[i][0]
        assert (out[1] == expected_output[i][1]).all()



@pytest.mark.parametrize("inputs_dict, expected_output", [
        ({"a":[3, 1, 8], "b":[0, 1, 2]}, [(["a=3","b=0"], 0), (["a=1","b=1"], 1), (["a=8","b=2"], 16)]),
        ({"a":[3, 1, 8], "b":[2]}, [(["a=3","b=2"], 6), (["a=1","b=2"], 2), (["a=8","b=2"], 16)]),
        ])
def test_single_node_3(inputs_dict, expected_output):
    N = Node(interface=fun3, mapper=('a','b'))
    N.inputs = inputs_dict
    N.run()

    for (i, out) in enumerate(N.output["out"]):
        assert out[0] == expected_output[i][0]
        assert (out[1] == expected_output[i][1]).all()



@pytest.mark.parametrize("inputs_dict, expected_output", [
        ({"a":[3, 1], "b":[1, 2, 4]}, [[(["a=3","b=1"], 3), (["a=3","b=2"], 6), (["a=3","b=4"], 12)], 
                                       [(["a=1","b=1"], 1), (["a=1","b=2"], 2), (["a=1","b=4"], 4)]]),
        ({"a":[[3, 1], [30, 10]], "b":[1, 2, 4]},
         [[[(["a=3","b=1"], 3), (["a=3","b=2"], 6), (["a=3","b=4"], 12)], 
           [(["a=1","b=1"], 1), (["a=1","b=2"], 2), (["a=1","b=4"], 4)]],
          [[(["a=30","b=1"], 30), (["a=30","b=2"], 60), (["a=30","b=4"], 120)],
           [(["a=10","b=1"], 10), (["a=10","b=2"], 20), (["a=10","b=4"], 40)]]]),
        ({"a":[3, 1], "b":[2]}, np.array([[(["a=3","b=2"], 6)], [(["a=1","b=2"], 2)]])),
        ])
def test_single_node_4(inputs_dict, expected_output):
    sn = Node(interface=fun3, mapper=['a','b'])
    sn.inputs = inputs_dict
    sn.run()

    for (i, out) in enumerate(sn.output["out"]):
        assert out[0] == expected_output[i][0]
        assert (out[1] == expected_output[i][1]).all()



@pytest.mark.parametrize("inputs_dict", [
        {"a":[[3, 1], [0,0]], "b":[1, 2, 0]},
        {"a":[[3, 1], [0,0], [1, 1]], "b":[1, 2, 0]}, # think if this should work
        {"a":[[3, 1, 1], [0,0, 0]], "b":[1, 2, 0]},  # think if this should work
        ])
def test_single_node_wrong_input(inputs_dict):
    with pytest.raises(Exception):
        sn = Node(interface=fun3, mapper=('a','b'))
        sn.inputs = inputs_dict
        sn.run()

def test_single_node_wrong_key():
    with pytest.raises(Exception):
        sn = Node(interface=fun3, mapper=('a','b'))
        sn.inputs = {"a":[3], "c":[0]}
