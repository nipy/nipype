from supernode import Node # or whatever

import numpy as np

import pytest, pdb
from test_single_node import fun1, fun2, fun3
from test_multi_nodes import fun4

def fun2a(a, **dict):
    pow = np.arange(3)
    return a**pow


@pytest.mark.parametrize("inputs_dict, expected_output", [ 
        ({"a": [3, 4, 5]}, [(["a=3"], ([], 9)), (["a=4"], ([], 16)), (["a=5"], ([], 25))]), # lists are empty since there are no more inputs related to the values 
        # do we want to allow 2D inputs a, when mapper="a"?
        #({"a": [[3, 4, 5], [6, 7, 8]]}, [([3, 4, 5], [9, 16, 25]), ([6, 7, 8], [36, 49, 64])]),
        ({"a": np.array([3, 4, 5])}, 
         [(["a=3"], ([], 9)), (["a=4"], ([], 16)), (["a=5"], ([], 25))]),
        ])
def test_singlenode_groupbyind_1(inputs_dict, expected_output):
    # for now i'm doing only groupByIndex, should I keep the original reducer name?
    N  = Node(inputs=inuts_dict, mapper="a", groupByInd="a", interface=fun1)
    N.run()
    
    # should we have both N.output and N.output_grouped/reduced ??
    for (i, out) in enumerate(N.output["out"]):
        assert out[0] == expected_output[i][0] 
        assert (out[1][1] == expected_output[i][1][1]).all() #still assuming that values will be returned as arrays 

    
@pytest.mark.parametrize("inputs_dict, expected_output", [
        ({"a":[3, 1, 8], "b":[0, 1, 2]}, 
         [(["a=3"], (["b=0"], 0)), (["a=1"], (["b=1"], 1)), (["a=8"], (["b=2"], 16))]), # since there is a dot product, after grouping over "a" we have still only single values (but they are connected to values of "b") 
        ])
def test_single_groupbyind_2(inputs_dict, expected_output):
    N = Node(interface=fun3, mapper=('a','b'), groupByInd="a")
    N.inputs = inputs_dict
    N.run()

    for (i, out) in enumerate(N.output["out"]):
        assert out[0] == expected_output[i][0]
        assert (out[1][1] == expected_output[i][1][1]).all()



@pytest.mark.parametrize("inputs_dict, expected_output", [
        ({"a":[3, 1], "b":[1, 2, 4]}, 
         [(["a=3"], [(["b=1"], 3), (["b=2"], 6), (["b=4"], 12)]), # there is a cross product, so after grouping over "a" we have still have one dim left (i.e. there is a list for every element of "a")
          (["a=1"], [(["b=1"], 1), (["b=2"], 2), (["b=4"], 4)])]),
        ])
def test_single_groupbyind_4(inputs_dict, expected_output):
    sn = Node(interface=fun3, mapper=['a','b'], groupByInd="a")
    sn.inputs = inputs_dict
    sn.run()

    for (i, out) in enumerate(sn.output["out"]):
        assert out[0] == expected_output[i][0]
        assert (out[1][1] == expected_output[i][1][1]).all()


@pytest.mark.parametrize("inputs_dict1, inputs_dict2, expected_output", [
        ({"a": [3, 4, 5]}, {"b": [10, 20, 30]},
         [(["N1.a=3"], [(["b=10"], 19), (["b=20"], 29), (["b=30"], 39)]),
          (["N1.a=4"], [(["b=10"], 26), (["b=20"], 36), (["b=30"], 46)]),
          (["N1.a=5"], [(["b=10"], 35), (["b=20"], 45), (["b=30"], 55)])]),
          ])
def test_2nodes_groupbyind_1(inputs_dict1, inputs_dict2, expected_output):
    wf = Workflow()
    N1  = Node(inputs=inputs_dict1, mapper="a", interface=fun1)
    wf.add_nodes(N1)

    N2 =  Node(inputs=inputs_dict2, interface=fun4, reducer="N1.a")
    wf.connect(N1, "a", N2, "A")

    wf.run()

    for (i, out) in enumerate(wf.output["out"]):
        assert out[0] == expected_output[i][0]
        for (j, redu) in enumerate(out[1]): 
            assert redu[0] == expected_output[i][j][0]
            assert (redu[1] == expected_output[i][j][1]).all()


@pytest.mark.parametrize("inputs_dict1, inputs_dict2, expected_output", [
        ({"a": [3, 4, 5]}, {"b": [10, 20, 30]},
         [(["b=10"], [(["N1.a=3"], 19), (["N1.a=4"], 26), (["N1.a=5"], 35)]),
          (["b=20"], [(["N1.a=3"], 29), (["N1.a=4"], 36), (["N1.a=5"], 45)]),
          (["b=30"], [(["N1.a=3"], 39), (["N1.a=4"], 46), (["N1.a=5"], 55)])]),
          ])
def test_2nodes_groupbyind_1a(inputs_dict1, inputs_dict2, expected_output):
    wf = Workflow()
    N1  = Node(inputs=inputs_dict1, mapper="a", interface=fun1)
    wf.add_nodes(N1)

    N2 =  Node(inputs=inputs_dict2, interface=fun4, groupByInd="b")
    wf.connect(N1, "a", N2, "A")

    wf.run()

    for (i, out) in enumerate(wf.output["out"]):
        assert out[0] == expected_output[i][0]
        for (j, redu) in enumerate(out[1]):
            assert redu[0] == expected_output[i][j][0]
            assert (redu[1] == expected_output[i][j][1]).all()


@pytest.mark.parametrize("inputs_dict1, inputs_dict2, expected_output", [
        ({"a": [3, 4]}, {"b": [10, 20, 30]},
         [(["N1.a=3"], [(["A=1","b=10"], 11), (["A=3","b=20"], 23), (["A=9","b=30"], 39)]),
          (["N1.a=4"], [(["A=1","b=10"], 11), (["A=4","b=20"], 24), (["A=16","b=30"], 46)])]) # if we group over "a", we still have "b" and "A" (not sure if values of "A" should be included)
        ])
def test_2nodes_3(inputs_dict1, inputs_dict2, expected_output):
    wf = Workflow()
    N1  = Node(inputs=inputs_dict2, mapper="a", interface=fun2a)
    wf.add_nodes(N1)

    N2 =  Node(inputs=inputs_dict2, mapper=("A","b"), interface=fun4, groupByInd="N1.a")
    wf.connect(N1, "a", N2, "A")

    wf.run()

    for (i, out) in enumerate(wf.output["out"]):
        assert out[0] == expected_output[i][0]
        for (j, redu) in enumerate(out[1]):
            assert redu[0] == expected_output[i][j][0]
            assert (redu[1] == expected_output[i][j][1]).all()


@pytest.mark.parametrize("inputs_dict1, inputs_dict2, expected_output", [
        ({"a": [3, 4]}, {"b": [10, 20, 30]},
          [(["b=10"], [(["A=1","N1.a=3"], 11), (["A=1","N1.a=4"], 11)]), 
           (["b=20"], [(["A=3","N1.a=3"], 23), (["A=4","N1.a=4"], 24)]),
           (["b=30"], [(["A=9","N1.a=3"], 39), (["A=16","N1.a=4"], 46)])]),
        ])
def test_2nodes_3a(inputs_dict1, inputs_dict2, expected_output):
    wf = Workflow()
    N1  = Node(inputs=inputs_dict2, mapper="a", interface=fun2a)
    wf.add_nodes(N1)

    N2 =  Node(inputs=inputs_dict2, mapper=("A","b"), interface=fun4, groupByInd="b")
    wf.connect(N1, "a", N2, "A")

    wf.run()

    for (i, out) in enumerate(wf.output["out"]):
        assert out[0] == expected_output[i][0]
        for (j, redu) in enumerate(out[1]):
            assert redu[0] == expected_output[i][j][0]
            assert (redu[1] == expected_output[i][j][1]).all()




# I was thinking about writing test_2nodes_3a with grouByInd="A", but again I have 
# a feeling that this would be weird... 
# Elemnts of A can be related to contrast or something else, but values of A_i are 
# the combinations of contrast and N1.a, so if we group by index we will not get 
# unique values of A in one group.
# And groupingByValue might give completely different grouping 
# (group elements that are related to different values of contrast)
# will write more in PR's comments 

