"""
Copy out of the top of sympy.core.compatibility as of
b8aa2de87d537eddde044c13f2eaaab99a5dcfe7

This can be deleted when we depend on sympy 0.7.0 or later
"""
"""
Reimplementations of constructs introduced in later versions of Python than we
support.
"""

# These are in here because telling if something is an iterable just by calling
# hasattr(obj, "__iter__") behaves differently in Python 2 and Python 3.  In
# particular, hasattr(str, "__iter__") is False in Python 2 and True in Python 3.
# I think putting them here also makes it easier to use them in the core.

def iterable(i, exclude=(basestring, dict)):
    """
    Return a boolean indicating whether i is an iterable in the sympy sense.

    When sympy is working with iterables, it is almost always assuming
    that the iterable is not a string or a mapping, so those are excluded
    by default. If you want a pure python definition, make exclude=None. To
    exclude multiple items, pass them as a tuple.

    See also: is_sequence

    Examples:

    >>> things = [[1], (1,), set([1]), (j for j in [1, 2]), {1:2}, '1', 1]
    >>> for i in things:
    ...     print iterable(i), type(i)
    True <type 'list'>
    True <type 'tuple'>
    True <type 'set'>
    True <type 'generator'>
    False <type 'dict'>
    False <type 'str'>
    False <type 'int'>

    >>> iterable({}, exclude=None)
    True
    >>> iterable({}, exclude=str)
    True
    >>> iterable("no", exclude=str)
    False

    """
    try:
        iter(i)
    except TypeError:
        return False
    if exclude:
        return not isinstance(i, exclude)
    return True

def is_sequence(i, include=None):
    """
    Return a boolean indicating whether i is a sequence in the sympy
    sense. If anything that fails the test below should be included as
    being a sequence for your application, set 'include' to that object's
    type; multiple types should be passed as a tuple of types.

    Note: although generators can generate a sequence, they often need special
    handling to make sure their elements are captured before the generator is
    exhausted, so these are not included by default in the definition of a
    sequence.

    See also: iterable

    Examples:

    >>> from nipy.fixes.sympy.utilities.compatibility import is_sequence
    >>> from types import GeneratorType
    >>> is_sequence([])
    True
    >>> is_sequence(set())
    False
    >>> is_sequence('abc')
    False
    >>> is_sequence('abc', include=str)
    True
    >>> generator = (c for c in 'abc')
    >>> is_sequence(generator)
    False
    >>> is_sequence(generator, include=(str, GeneratorType))
    True

    """
    return (hasattr(i, '__getitem__') and
            iterable(i) or
            bool(include) and
            isinstance(i, include))
