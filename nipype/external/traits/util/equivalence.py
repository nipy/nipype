from copy import copy

from traits.api import HasTraits, Instance, List, Property
from traits.util.sequence import union

# Our representation of equivalence classes can be optimized. It looks like all
# of our methods are linear in the number of classes; liberal use of hashes
# should be able to make some of them sub-linear -- at least 'get_class'.

# TODO Fire more events? e.g. 'classes_items_changed'

class Equivalence(HasTraits):
    ''' An equivalence relation.

        An equivalence relation is a binary relation ~ on a set A with the
        following properties:

        * Reflexivity:  a ~ a
        * Symmetry:     a ~ b iff b ~ a
        * Transitivity: a ~ b and b ~ c implies a ~ c

        For our purposes, the set A is the set of all hashable python objects.

        Examples::

            >>> e = Equivalence(list('foo'), list('bar'), list('baz'))
            >>> e.equivalent('f', 'o')
            True
            >>> e.equivalent('f', 'b')
            False
            >>> e.equivalent('b', 'a', 'r', 'z')
            True
            >>> assert e.get_class('f') == set('fo')
            >>> assert e.get_class('b') == set('barz')

            >>> e.remove('f')
            >>> assert e.get_class('f') == set('f')
            >>> assert e.get_class('o') == set('o')
            >>> assert e.get_class('b') == set('barz')

            >>> e.remove('r', 'z')
            >>> assert e.classes == [set('ba')]
            >>> assert set(e.classes) == set(e) == set([frozenset('ba')])

            >>> e = Equivalence()
            >>> e.equate(1, 3)
            >>> e.equate(2, 4)
            >>> e.equate(5, 6, 7, 8, 9)
            >>> e.equate(10)
            >>> assert len(e.classes) == 3
            >>> assert e.get_class(1) == set([1, 3])
            >>> assert e.get_class(4) == set([2, 4])
            >>> e.equate(2, 3)
            >>> assert e.get_class(1) == e.get_class(4) == set([1, 2, 3, 4])
            >>> e.remove(2, 3)
            >>> assert e.get_class(1) == e.get_class(4) == set([1, 4])
            >>> e.remove(4)
            >>> assert not e.equivalent(1, 4)

            >>> e = Equivalence()
            >>> assert set(e) == set()
            >>> e.equate(1,2)
            >>> e.remove(1,2)
            >>> assert set(e) == set()
    '''

    # Our equivalence classes
    classes = Property(List(Instance(set)))
    _classes = List(Instance(set))

    ### Properties ############################################################

    def _get_classes(self):
        return map(frozenset, self._classes)

    ### object interface ######################################################

    def __init__(self, *classes):
        super(Equivalence, self).__init__()
        for c in classes:
            self.equate(*c)

    def __iter__(self):
        return iter(self.classes)

    def __repr__(self):
        return repr(self._classes)

    ### Equivalence interface #################################################

    def equivalent(self, *args):
        'Whether all given elements are equivalent'
        # If the given elements are all the same element, then they are
        # equivalent whether we've seen them before or not. Otherwise, if we
        # haven't seen all of them, then they aren't equivalent.
        if args:
            return (len(set(args)) == 1 or
                    set(args[1:]).issubset(self.get_class(args[0])))
        else:
            return True # Vacuously

    def get_class(self, a):
        "'a's equivalence class (the set of elements equivalent to 'a')."
        for c in self._classes:
            if a in c:
                return c
        return set([a])

    def equate(self, *args):
        'Declare that the given elements are equivalent to each other.'
        args = set(args)

        # Singleton classes are implicit
        if len(args) == 1:
            return

        unaffected, to_merge = [], []
        for c in self._classes:
            if args & c:
                to_merge.append(c)
            else:
                unaffected.append(c)

        self._classes = unaffected + [args | union(to_merge)]

    def remove(self, *args):
        ''' Declare that each given element is only equivalent to itself.

            Unknown elements are assumed to be equivalent only to themselves,
            so using 'remove' is only necessary to undo effects of previous
            calls to 'equate'.
        '''
        args = set(args)
        for c in copy(self._classes):

            # Remove 'args' from each class
            c -= args

            # Singleton classes are implicit; remove them.
            # Empty classes are cruft; remove them too.
            if len(c) <= 1:
                self._classes.remove(c)
