from .. import auxiliary as aux

import numpy as np
import pytest

@pytest.mark.parametrize("mapper, rpn",
                        [
                            ("a",                      ["a"]),
                            (("a", "b"),               ["a", "b", "."]),
                            (["a", "b"],               ["a", "b", "*"]),
                            (["a", ("b", "c")],        ["a", "b", "c", ".", "*"]),
                            ([("a", "b"), "c"],        ["a", "b", ".", "c", "*"]),
                            (["a", ("b", ["c", "d"])], ["a", "b", "c", "d", "*", ".", "*"])
                        ])
def test_mapper2rpn(mapper, rpn):
    assert aux.mapper2rpn(mapper) == rpn


@pytest.mark.parametrize("mapper, other_mappers, rpn",
                         [
                            (["a", "_NA"],        {"NA": ("b", "c")}, ["a", "NA.b", "NA.c", ".", "*"]),
                            (["_NA", "c"],        {"NA": ("a", "b")}, ["NA.a", "NA.b", ".", "c", "*"]),
                            (["a", ("b", "_NA")], {"NA": ["c", "d"]}, ["a", "b", "NA.c", "NA.d", "*", ".", "*"])
                        ])

def test_mapper2rpn_wf_mapper(mapper, other_mappers, rpn):
    assert aux.mapper2rpn(mapper, other_mappers=other_mappers) == rpn


@pytest.mark.parametrize("mapper, mapper_changed",
                        [
                            ("a",               "Node.a"),
                            (["a", ("b", "c")], ["Node.a", ("Node.b", "Node.c")]),
                            (("a", ["b", "c"]), ("Node.a", ["Node.b", "Node.c"]))
                        ])
def test_change_mapper(mapper, mapper_changed):
    assert aux.change_mapper(mapper, "Node") == mapper_changed


@pytest.mark.parametrize("inputs, rpn, expected",
                         [
                             ({"a": np.array([1, 2])}, ["a"], {"a": [0]}),
                             ({"a": np.array([1, 2]), "b": np.array([3, 4])}, ["a", "b", "."], {"a": [0], "b": [0]}),
                             ({"a": np.array([1, 2]), "b": np.array([3, 4, 1])}, ["a", "b", "*"], {"a": [0], "b": [1]}),
                             ({"a": np.array([1, 2]), "b": np.array([3, 4]), "c": np.array([1, 2, 3])}, ["a", "b", ".", "c", "*"],
                                                        {"a": [0], "b": [0], "c": [1]}),
                             ({"a": np.array([1, 2]), "b": np.array([3, 4]), "c": np.array([1, 2, 3])},
                              ["c", "a", "b", ".", "*"], {"a": [1], "b": [1], "c": [0]}),
                             ({"a": np.array([[1, 2], [1, 2]]), "b": np.array([[3, 4], [3, 3]]), "c": np.array([1, 2, 3])},
                                                        ["a", "b", ".", "c", "*"], {"a": [0, 1], "b": [0, 1], "c": [2]}),
                             ({"a": np.array([[1, 2], [1, 2]]), "b": np.array([[3, 4], [3, 3]]),
                               "c": np.array([1, 2, 3])}, ["c", "a", "b", ".", "*"], {"a": [1, 2], "b": [1, 2], "c": [0]})
                         ])
def test_mapping_axis(inputs, rpn, expected):
    res = aux.mapping_axis(inputs, rpn)[0]
    print(res)
    for key in inputs.keys():
        assert res[key] == expected[key]


def test_mapping_axis_error():
    with pytest.raises(Exception):
        aux.mapping_axis({"a": np.array([1, 2]), "b": np.array([3, 4, 5])}, ["a", "b", "."])


@pytest.mark.parametrize("inputs, axis_inputs, ndim, expected",
                         [
                             ({"a": np.array([1, 2])}, {"a": [0]}, 1, [["a"]]),
                             ({"a": np.array([1, 2]), "b": np.array([3, 4])}, {"a": [0], "b": [0]}, 1,
                              [["a", "b"]]),
                             ({"a": np.array([1, 2]), "b": np.array([3, 4, 1])}, {"a": [0], "b": [1]}, 2,
                              [["a"], ["b"]]),
                             ({"a": np.array([1, 2]), "b": np.array([3, 4]), "c": np.array([1, 2, 3])},
                                                        {"a": [0], "b": [0], "c": [1]}, 2, [["a", "b"]]),
                             ({"a": np.array([1, 2]), "b": np.array([3, 4]), "c": np.array([1, 2, 3])},
                              {"a": [1], "b": [1], "c": [0]}, 2, [["c"], ["a", "b"]]),
                             ({"a": np.array([[1, 2], [1, 2]]), "b": np.array([[3, 4], [3, 3]]), "c": np.array([1, 2, 3])},
                                                {"a": [0, 1], "b": [0, 1], "c": [2]}, 3, [["a", "b"], ["a", "b"], ["c"]]),
                             ({"a": np.array([[1, 2], [1, 2]]), "b": np.array([[3, 4], [3, 3]]),
                               "c": np.array([1, 2, 3])}, {"a": [1, 2], "b": [1, 2], "c": [0]}, 3,
                              [["c"], ["a", "b"], ["a", "b"]])
                         ])
def test_converting_axis2input(inputs, axis_inputs, ndim, expected):
    aux.converting_axis2input(inputs, axis_inputs, ndim)[0] == expected
