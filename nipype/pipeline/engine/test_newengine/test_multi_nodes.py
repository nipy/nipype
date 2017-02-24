from supernode import Node, Workflow # or whatever                                        

import numpy as np

import pytest, pdb
from test_single_node import fun1, fun2, fun3  # functions should be probably in one place TODO

def fun4(A, b, **dict):
    return A + b


@pytest.mark.parametrize("inputs_dict1, inputs_dict2, expected_output", [
        ({"a": [3, 4, 5]}, {"b": [10, 20, 30]}, [[19, 29, 39], [26, 36, 46], [35, 45, 55]]),
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
   
    assert (wf.outputs["out"] == expected_output).all()


@pytest.mark.parametrize("inputs_dict1, inputs_dict2, expected_output", [
        ({"a": [3, 4, 5]}, {"b": [10, 20, 30]}, [19, 36, 55]),
          ])
def test_2nodes_2(inputs_dict1, inputs_dict2, expected_output):
    wf = Workflow()
    N1  = Node(inputs=inputs_dict1, mapper="a", interface=fun1)
    wf.add_nodes(N1)

    N2 =  Node(inputs=inputs_dict2, mapper="(N1.a,b)", interface=fun4)
    wf.connect(N1, "a", N2, "A")

    wf.run()

    assert (wf.outputs["out"] == expected_output).all()


@pytest.mark.parametrize("inputs_dict1, inputs_dict2, expected_output", [
        ({"a": [3, 4, 5]}, {"b": [10, 20, 30, 40]}, 
         [[11, 23, 39, 67], [11, 24, 46, 104], [11, 25, 55, 165]]),
          ])
def test_2nodes_3(inputs_dict1, inputs_dict2, expected_output):
    wf = Workflow()
    N1  = Node(inputs=inputs_dict2, mapper="a", interface=fun2)
    wf.add_nodes(N1)

    # IMPORTANT: I understand that if b is used in a mapper with A,
    # I do not anymore assume a x b, i.e. no "state input mapping"
    N2 =  Node(inputs=inputs_dict2, mapper="(A,b)", interface=fun4)
    wf.connect(N1, "a", N2, "A")

    wf.run()

    assert (wf.outputs["out"] == expected_output).all()

@pytest.mark.parametrize("inputs_dict1, inputs_dict2, expected_output", [
        ({"a": [3, 4, 5]}, {"b": [10, 20, 30, 40]},
         [[[11, 21, 31, 41], [13, 23, 33, 43], [19, 29, 39, 49], [37, 47, 57, 67]], 
          [[11, 21, 31, 41], [14, 24, 34, 44], [26, 36, 46, 56], [74, 84, 94, 104]], 
          [[11, 21, 31, 41], [15, 25, 35, 45], [35, 45, 55, 65], [135, 145, 155, 165]]]),
          ])
def test_2nodes_3(inputs_dict1, inputs_dict2, expected_output):
    wf = Workflow()
    N1  = Node(inputs=inputs_dict2, mapper="a", interface=fun2)
    wf.add_nodes(N1)

    # IMPORTANT: I understand that if b is used in a mapper with A, 
    # I do not anymore assume a x b, i.e. no "state input mapping"       
    N2 =  Node(inputs=inputs_dict2, mapper="[A,b]", interface=fun4)
    wf.connect(N1, "a", N2, "A")

    wf.run()

    assert (wf.outputs["out"] == expected_output).all()



