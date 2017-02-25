from supernode import Node, Workflow # or whatever                                        

import numpy as np

import pytest, pdb
from test_single_node import fun1, fun2, fun3  # functions should be probably in one place TODO

def fun4(A, b, **dict):
    return A + b


@pytest.mark.parametrize("inputs_dict1, inputs_dict2, expected_output", [
        ({"a": [3, 4, 5]}, {"b": [10, 20, 30]}, 
         [[(["a=3","b=10"], 19), (["a=3","b=20"], 29), (["a=3","b=30"], 39)], 
          [(["a=4","b=10"], 26), (["a=4","b=20"], 36), (["a=4","b=30"], 46)], 
          [(["a=5","b=10"], 35), (["a=5","b=20"], 45), (["a=5","b=30"], 55)]]),
          ])
def test_2nodes_1(inputs_dict1, inputs_dict2, expected_output):
    # not sure how do you want to initiate (with Node or empty), assuming empty and adding node
    wf = Workflow()
    N1  = Node(inputs=inputs_dict1, mapper="a", interface=fun1)
    wf.add_nodes(N1)
    
    # no mapper, so assuming "N1.axb", i.e. [N1.a,b]
    N2 =  Node(inputs=inputs_dict2, interface=fun4)
    # not sure what should be the order of defining N2 and connect 
    # you either can check in the connect if N2 exists
    # or you can check in the N2.__init__ if mapper possible, i.e. N1.a exists etc.
    # assuming that i dont have to add N2 if I use connect
    wf.connect(N1, "a", N2, "A")

    wf.run()
   
    for (i, out) in enumerate(wf.output["out"]):
        assert out[0] == expected_output[i][0]
        assert (out[1] == expected_output[i][1]).all()



@pytest.mark.parametrize("inputs_dict1, inputs_dict2, expected_output", [
        ({"a": [3, 4, 5]}, {"b": [10, 20, 30]}, 
         [(["a=3","b=10"], 19), (["a=4","b=20"], 36), (["a=5","b=30"], 55)]),
          ])
def test_2nodes_2(inputs_dict1, inputs_dict2, expected_output):
    wf = Workflow()
    N1  = Node(inputs=inputs_dict1, mapper="a", interface=fun1)
    wf.add_nodes(N1)

    N2 =  Node(inputs=inputs_dict2, mapper=("N1.a","b"), interface=fun4)
    wf.connect(N1, "a", N2, "A")

    wf.run()

    for (i, out) in enumerate(wf.output["out"]):
        assert out[0] == expected_output[i][0]
        assert (out[1] == expected_output[i][1]).all()



@pytest.mark.parametrize("inputs_dict1, inputs_dict2, expected_output", [
        ({"a": [3, 4, 5]}, {"b": [10, 20, 30, 40]}, 
         # should I also include N1.a in the state?
         [[(["N1.a=3","A=1","b=10"], 11), (["N1.a=3","A=3","b=20"], 23), (["N1.a=3","A=9","b=30"], 39), (["N1.a=3","A=27","b=40"], 67)], 
          [(["N1.a=4","A=1","b=10"], 11), (["N1.a=4","A=4","b=20"], 24), (["N1.a=4","A=16","b=30"], 46), (["N1.a=4","A=64","b=40"], 104)], 
          [(["N1.a=5","A=1","b=10"], 11), (["N1.a=5","A=5","b=20"], 25), (["N1.a=5","A=25","b=30"], 55), (["N1.a=5","A=125","b=40"], 165)]]),
          ])
def test_2nodes_3(inputs_dict1, inputs_dict2, expected_output):
    wf = Workflow()
    N1  = Node(inputs=inputs_dict2, mapper="a", interface=fun2)
    wf.add_nodes(N1)

    # IMPORTANT: I understand that if b is used in a mapper with A,
    # I do not anymore assume a x b, i.e. no "state input mapping"
    N2 =  Node(inputs=inputs_dict2, mapper=("A","b"), interface=fun4)
    wf.connect(N1, "a", N2, "A")

    wf.run()

    for (i, out) in enumerate(wf.output["out"]):
        assert out[0] == expected_output[i][0]
        assert (out[1] == expected_output[i][1]).all()


@pytest.mark.parametrize("inputs_dict1, inputs_dict2, expected_output", [
        ({"a": [3, 4, 5]}, {"b": [10, 20, 30, 40]},
         [[[(["N1.a=3","A=1","b=10"], 11), (["N1.a=3","A=1","b=20"], 21), (["N1.a=3","A=1","b=30"], 31), (["N1.a=3","A=1","b=40"], 41)], 
           [(["N1.a=3","A=3","b=10"], 13), (["N1.a=3","A=3","b=20"], 23), (["N1.a=3","A=3","b=30"], 33), (["N1.a=3","A=3","b=40"], 43)], 
           [(["N1.a=3","A=9","b=10"], 19), (["N1.a=3","A=9","b=20"], 29), (["N1.a=3","A=9","b=30"], 39), (["N1.a=3","A=9","b=40"], 49)], 
           [(["N1.a=3","A=27","b=10"], 37), (["N1.a=3","A=27","b=20"], 47), (["N1.a=3","A=27","b=30"], 57), (["N1.a=3","A=1","b=10"], 67)]], 
          [[(["N1.a=4","A=1","b=10"], 11), (["N1.a=4","A=1","b=20"], 21), (["N1.a=4","A=1","b=30"], 31), (["N1.a=4","A=1","b=40"], 41)], 
           [(["N1.a=4","A=4","b=10"], 14), (["N1.a=4","A=4","b=20"], 24),(["N1.a=4","A=4","b=30"], 34), (["N1.a=4","A=4","b=40"], 44)], 
           [(["N1.a=4","A=16","b=10"], 26), (["N1.a=4","A=16","b=20"], 36), (["N1.a=4","A=16","b=30"], 46), (["N1.a=4","A=16","b=40"], 56)], 
           [(["N1.a=4","A=64","b=10"], 74), (["N1.a=4","A=64","b=20"], 84), (["N1.a=4","A=64","b=30"], 94), (["N1.a=4","A=64","b=40"], 104)]], 
          [[(["N1.a=5","A=1","b=10"], 11), (["N1.a=5","A=1","b=20"], 21), (["N1.a=5","A=1","b=30"], 31), (["N1.a=5","A=1","b=40"], 41)], 
           [(["N1.a=5","A=5","b=10"], 15), (["N1.a=5","A=5","b=20"], 25), (["N1.a=5","A=5","b=30"], 35), (["N1.a=5","A=5","b=40"], 45)], 
           [(["N1.a=5","A=25","b=10"], 35), (["N1.a=5","A=25","b=20"], 45), (["N1.a=5","A=25","b=30"], 55), (["N1.a=5","A=25","b=40"], 65)], 
           [(["N1.a=5","A=125","b=10"], 135), (["N1.a=5","A=125","b=20"], 145), (["N1.a=5","A=125","b=30"], 155), (["N1.a=5","A=125","b=40"], 165)]]]),
          ])
def test_2nodes_3(inputs_dict1, inputs_dict2, expected_output):
    wf = Workflow()
    N1  = Node(inputs=inputs_dict2, mapper="a", interface=fun2)
    wf.add_nodes(N1)

    # IMPORTANT: I understand that if b is used in a mapper with A, 
    # I do not anymore assume a x b, i.e. no "state input mapping"       
    N2 =  Node(inputs=inputs_dict2, mapper=["A","b"], interface=fun4)
    wf.connect(N1, "a", N2, "A")

    wf.run()

    for (i, out) in enumerate(wf.output["out"]):
        assert out[0] == expected_output[i][0]
        assert (out[1] == expected_output[i][1]).all()




