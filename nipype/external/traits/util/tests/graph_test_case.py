import sys, unittest

from traits.testing.api import doctest_for_module

import traits.util.graph as G


class GraphDocTestCase(doctest_for_module(G)):
    pass


class MapTestCase(unittest.TestCase):
    def test_map(self):
        self.assertEqual(G.map(str, {}), {})
        self.assertEqual(G.map(str, {1:[2,3]}), {'1':['2','3']})
        self.assertEqual(G.map(lambda x: x, {1:[2,3]}), {1:[2,3]})


class ReachableGraphTestCase(unittest.TestCase):

    def _base(self, graph, nodes, result, error=None):
        if error:
            self.assertRaises(error, lambda: self._base(graph, nodes, result))
        else:
            self.assertEqual(G.reachable_graph(graph, nodes), result)

    def test_reachable_graph(self):
        'reachable_graph'
        self._base({}, [], {})
        self._base({}, [1], {}, error=KeyError)
        self._base({1:[2,3], 0:[3]}, [1], {1:[2,3]})
        self._base({1:[2,3], 1:[3]}, [1], {1:[2,3], 1:[3]})
        self._base({1:[2,3], 2:[3]}, [1], {1:[2,3], 2:[3]})
        self._base({1:[2,3], 2:[3]}, [2], {2:[3]})
        self._base({1:[2,3], 2:[3]}, [3], {})
        self._base({1:[2], 3:[4]}, [1,3], {1:[2], 3:[4]})


class ReverseGraphTestCase(unittest.TestCase):
    def _base(self, graph, result, error=None):
        if error:
            self.assertRaises(error, lambda: self._base(graph, result))
        else:
            self.assertEqual(G.reverse(graph), result)

    def test_reverse(self):
        'reverse'
        self._base({}, {})
        self._base({1:[]}, {1:[]})
        self._base({1:[2]}, {2:[1], 1:[]})
        self._base({1:[2,3]}, {2:[1], 3:[1], 1:[]})


if __name__ == '__main__':
    unittest.main(argv=sys.argv)
