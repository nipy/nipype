'Non-standard functions for various sequence objects'

###############################################################################
# sequence objects
###############################################################################

def is_sequence(x):
    try:
        iter(x)
        return True
    except TypeError:
        return False

all = lambda l: False not in map(bool, l)
any = lambda l: True in map(bool, l)

###############################################################################
# list
###############################################################################

def concat(lists):
    ''' Concatenate a list of lists.

        >>> concat(range(i) for i in range(5))
        [0, 0, 1, 0, 1, 2, 0, 1, 2, 3]
        >>> concat([[1,2], [3]])
        [1, 2, 3]
        >>> concat([[1,2,[3,4]], [5,6]])
        [1, 2, [3, 4], 5, 6]
        >>> concat([])
        []
    '''
    l = []
    map(l.extend, lists)
    return l

###############################################################################
# set
###############################################################################

from copy import copy

def union(sets):
    ''' Union a collection of sets.

        >>> union([set('ab'), set('bc'), set('ac')]) == set('abc')
        True
        >>> union([])
        set([])
    '''
    s = set()
    map(s.update, sets)
    return s

def intersect(sets):
    ''' Intersect a non-empty collection of sets.

        >>> intersect([set('ab'), set('bc'), set('bb')])
        set(['b'])
        >>> intersect([set('ab'), set('bc'), set('ac')])
        set([])
        >>> try: intersect([])
        ... except: print 'bad'
        ...
        bad
    '''
    sets = iter(sets)
    s = copy(sets.next())
    map(s.intersection_update, sets)
    return s

def disjoint(*sets):
    ''' Test whether a collection of sets is pair-wise disjoint.

        >>> disjoint(set([1,2]), set([3]))
        True
        >>> disjoint(set('abc'), set('xy'), set('z'), set('cde'))
        False
        >>> disjoint()
        True
    '''
    return len(union(sets)) == len(concat(sets))
