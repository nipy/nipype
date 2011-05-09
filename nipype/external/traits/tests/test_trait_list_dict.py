""" Test the persistence behavior of TraitListObjects, TraitDictObjects and TraitSetObjects.
"""

from __future__ import absolute_import

import copy
from cPickle import dumps, loads

from ..has_traits import HasTraits, on_trait_change
from ..trait_types import Dict, List, Set, Str, Int, Instance


class A(HasTraits):
    list = List(Int, range(5))
    dict = Dict(Str, Int, dict(a=1, b=2))
    set = Set(Int, range(5))

    events = List()

    @on_trait_change('list_items,dict_items,set_items')
    def _receive_events(self, object, name, old, new):
        self.events.append((name, new))

class B(HasTraits):
    dict = Dict(Str, Instance(A))


def test_trait_list_object_persists():
    a = A()
    list = loads(dumps(a.list))
    assert list.object() is None
    list.append(10)
    assert len(a.events) == 0
    a.list.append(20)
    assert len(a.events) == 1
    list2 = loads(dumps(list))
    assert list2.object() is None

def test_trait_dict_object_persists():
    a = A()
    dict = loads(dumps(a.dict))
    assert dict.object() is None
    dict['key'] = 10
    assert len(a.events) == 0
    a.dict['key'] = 10
    assert len(a.events) == 1
    dict2 = loads(dumps(dict))
    assert dict2.object() is None

def test_trait_set_object_persists():
    a = A()
    set = loads(dumps(a.set))
    assert set.object() is None
    set.add(10)
    assert len(a.events) == 0
    a.set.add(20)
    assert len(a.events) == 1
    set2 = loads(dumps(set))
    assert set2.object() is None

def test_trait_list_object_copies():
    a = A()
    list = copy.deepcopy(a.list)
    assert list.object() is None
    list.append(10)
    assert len(a.events) == 0
    a.list.append(20)
    assert len(a.events) == 1
    list2 = copy.deepcopy(list)
    list2.append(30)
    assert list2.object() is None

def test_trait_dict_object_copies():
    a = A()
    dict = copy.deepcopy(a.dict)
    assert dict.object() is None
    dict['key'] = 10
    assert len(a.events) == 0
    a.dict['key'] = 10
    assert len(a.events) == 1
    dict2 = copy.deepcopy(dict)
    dict2['key2'] = 20
    assert dict2.object() is None

def test_trait_set_object_copies():
    a = A()
    set = copy.deepcopy(a.set)
    assert set.object() is None
    set.add(10)
    assert len(a.events) == 0
    a.set.add(20)
    assert len(a.events) == 1
    set2 = copy.deepcopy(set)
    set2.add(30)
    assert set2.object() is None

def test_pickle_whole():
    a = A()
    loads(dumps(a))
    b = B(dict=dict(a=a))
    loads(dumps(b))
