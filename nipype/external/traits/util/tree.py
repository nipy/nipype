'Functions on trees, that is, nested sequences.'

from traits.util.functional import partial
from traits.util.sequence import all, any, concat, is_sequence

def is_fork(x, leaves=()):
    'Test whether a tree is a fork (instead of a leaf).'
    return is_sequence(x) and not isinstance(x, leaves)

def flatten(tree, leaves=()):
    ''' Flatten a tree, that is, recursively concatenate nested sequences.

        >>> flatten([1, [[2, 3], 4, 5], [[[[6]]]]])
        [1, 2, 3, 4, 5, 6]
        >>> mixed = [1, [[2], 3], (4, 5), [(6,)], 'abc']
        >>> flatten(mixed)
        [1, 2, 3, 4, 5, 6, 'a', 'b', 'c']
        >>> flatten(mixed, leaves=(str,))
        [1, 2, 3, 4, 5, 6, 'abc']
        >>> flatten(mixed, leaves=(str, tuple))
        [1, 2, 3, (4, 5), (6,), 'abc']
        >>> flatten([])
        []
        >>> flatten(1)
        [1]
    '''
    # Pass leaf types around, avoiding infinite regress on strings
    _is_fork = partial(is_fork, leaves=leaves)
    if isinstance(tree, basestring):
        leaves += (basestring,)
    _flatten = partial(flatten, leaves=leaves)

    if not _is_fork(tree):
        return [tree]
    else:
        return concat(_flatten(n) for n in tree)

def tree_map(f, tree, leaves=()):
    ''' Map a function over the leaves of a tree.

        >>> tree_map(str, [1,[2,3]])
        ['1', ['2', '3']]
        >>> tree_map(len, ['foo', ['x', 'asdf']])
        [[1, 1, 1], [[1], [1, 1, 1, 1]]]
        >>> tree_map(len, ['foo', ['x', 'asdf']], leaves=(str,))
        [3, [1, 4]]
    '''
    # Pass leaf types around, avoiding infinite regress on strings
    _is_fork = partial(is_fork, leaves=leaves)
    if isinstance(tree, basestring):
        leaves += (basestring,)
    _tree_map = partial(tree_map, leaves=leaves)

    if not _is_fork(tree):
        return f(tree)
    else:
        seq = isinstance(tree, tuple) and tuple or list
        return seq([ _tree_map(f,n) for n in tree ])

def tree_zip(*trees, **kw):
    ''' Zip recursively.

        Returns nested lists with tuples at the bottom.

        >>> tree_zip([1,[2,3]], [5,[6,7]])
        [(1, 5), [(2, 6), (3, 7)]]
        >>> tree_zip([1,[2,3]], [5,[6,7]], ['a',['b','c']])
        [(1, 5, 'a'), [(2, 6, 'b'), (3, 7, 'c')]]

        >>> tree_zip('foo', 'bar')
        [('f', 'b'), ('o', 'a'), ('o', 'r')]
        >>> tree_zip(['foo'], ['bar'])
        [[('f', 'b'), ('o', 'a'), ('o', 'r')]]
        >>> tree_zip(['foo'], ['bar'], leaves=(str,))
        [('foo', 'bar')]
        >>> tree_zip('foo', ['bar'])
        [('f', 'bar')]
        >>> tree_zip('foo', ['bar'], leaves=(str,))
        ('foo', ['bar'])
        >>> tree_zip(1, 2)
        (1, 2)

        >>> tree_zip([1,[2,3]], [5,6,7,8], [['a','b'],['c','d']])
        [(1, 5, ['a', 'b']), ([2, 3], 6, ['c', 'd'])]
    '''
    # (Default arguments)
    leaves = kw.get('leaves', ())

    # Pass leaf types around, avoiding infinite regress on strings
    _is_fork = partial(is_fork, leaves=leaves)
    if any(isinstance(t, basestring) for t in trees):
        leaves += (basestring,)
    _tree_zip = partial(tree_zip, leaves=leaves)

    if not all(_is_fork(t) for t in trees):
        return trees
    else:
        return [ _tree_zip(*neighbors) for neighbors in zip(*trees) ]

def tree_embeds(t, u, leaves=()):
    ''' ...

        >>> tree_embeds([1], [2])
        True
        >>> tree_embeds([1], [1,2])
        False
        >>> tree_embeds([1], [[1,2]])
        True
        >>> tree_embeds([1,[2,3]], [[True, False], 'ab'])
        True
        >>> tree_embeds([1,[2,3]], [[True, False], 'ab'], leaves=(str,))
        False
        >>> tree_embeds([], [1,2,3])
        False
        >>> tree_embeds(1, [1,2,3])
        True
    '''
    # Pass leaf types around, avoiding infinite regress on strings
    _is_fork = partial(is_fork, leaves=leaves)
    if isinstance(t, basestring) or isinstance(u, basestring):
        leaves += (basestring,)
    _tree_embeds = partial(tree_embeds, leaves=leaves)

    if not _is_fork(t):
        return True
    else:
        return (_is_fork(u) and len(list(t)) == len(list(u)) and
                all(_tree_embeds(n,m) for n,m in zip(t,u)))

def tree_shape(tree, leaves=()):
    ''' The shape of a tree expressed as nested tuples of nothing.

        >>> tree_shape([1,[2,3]]) == tree_shape([True, 'ab'])
        True
        >>> tree_shape([1,[2,3]])
        ((), ((), ()))
        >>> tree_shape(['ab', ['c', 'd']])
        (((), ()), (((),), ((),)))
        >>> tree_shape(['ab', ['c', 'd']], leaves=(str,))
        ((), ((), ()))
        >>> tree_shape(1)
        ()
    '''
    # Pass leaf types around, avoiding infinite regress on strings
    _is_fork = partial(is_fork, leaves=leaves)
    if isinstance(tree, basestring):
        leaves += (basestring,)
    _tree_shape = partial(tree_shape, leaves=leaves)

    if not _is_fork(tree):
        return ()
    else:
        return tuple(_tree_shape(n) for n in tree)
