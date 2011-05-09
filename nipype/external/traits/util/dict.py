'Non-standard dictionary functions'

from sequence import intersect

def map_keys(f, d):
    ''' Map a function over the keys in a dictionary.

        >>> map_keys(str, {1: 2, 3: 4}) == {'1': 2, '3': 4}
        True
        >>> map_keys(lambda x: 0, {1: 2, 3: 4}) in [{0: 2}, {0: 4}]
        True
    '''
    return dict([ (f(k), v) for k,v in d.items() ])

def map_values(f, d):
    ''' Map a function over the values in a dictionary.

        >>> map_values(str, {1: 2, 3: 4}) == {1: '2', 3: '4'}
        True
        >>> map_values(lambda x: 0, {1: 2, 3: 4}) == {1: 0, 3: 0}
        True
    '''
    return dict([ (k, f(v)) for k,v in d.items() ])

def map_items(f, d):
    ''' Map a binary function over the key-value pairs in a dictionary.

        >>> map_items(lambda a,b: (a*2, b**2), {1: 2, 3: 4}) == {2: 4, 6: 16}
        True
    '''
    return dict([ f(k,v) for k,v in d.items() ])

def filter_keys(p, d):
    ''' Filter a dictionary by a predicate on keys.

        >>> filter_keys(lambda n: n % 2, {0: 1, 1: 2, 2: 3}) == {1: 2}
        True
    '''
    return dict([ (k,v) for k,v in d.items() if p(k) ])

def filter_values(p, d):
    ''' Filter a dictionary by a predicate on values.

        >>> filter_values(lambda n: n % 2, {0: 1, 1: 2, 2: 3}) == {0: 1, 2: 3}
        True
    '''
    return dict([ (k,v) for k,v in d.items() if p(v) ])

def filter_items(p, d):
    ''' Filter a dictionary by a predicate on key-value pairs.

        >>> import operator
        >>> filter_items(operator.le, {0: 0, 1: 2, 3: 2}) == {0: 0, 1: 2}
        True
    '''
    return dict([ (k,v) for k,v in d.items() if p(k,v) ])

def dict_zip(*dicts):
    ''' Zip dictionaries.

        >>> dict_zip(dict(a=True), dict(a='foo'))
        {'a': (True, 'foo')}
        >>> dict_zip(dict(a=0, b=2), dict(a=1, c=3), dict(a=None, c=4))
        {'a': (0, 1, None)}
        >>> dict_zip(dict(a=0), dict(b=1, c=2, d=3))
        {}
    '''
    keys = intersect([ set(d) for d in dicts ])
    return dict([ (k, tuple([ d[k] for d in dicts ])) for k in keys ])

def sub_dict(d, keys):
    ''' Create a dictionary from a subset of another.

        >>> sub_dict({1: 2, 3: 4, 'a': 'b'}, [1, 3]) == {1: 2, 3: 4}
        True

        >>> try:
        ...     sub_dict({1: 2}, [1, 3])
        ...     assert False
        ... except KeyError:
        ...     print 'Key error!'
        Key error!
    '''
    return dict([ (k, d[k]) for k in keys ])
