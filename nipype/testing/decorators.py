# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Extend numpy's decorators to use nipype's gui and data labels.
"""
from numpy.testing import dec

from nibabel.data import DataError


def make_label_dec(label, ds=None):
    """Factory function to create a decorator that applies one or more labels.

    Parameters
    ----------
    label : str or sequence
        One or more labels that will be applied by the decorator to the
        functions it decorates. Labels are attributes of the decorated function
        with their value set to True.
    ds : str
        An optional docstring for the resulting decorator. If not given, a
        default docstring is auto-generated.

    Returns
    -------
    ldec : function
        A decorator.

    Examples
    --------
    >>> slow = make_label_dec('slow')
    >>> slow.__doc__
    "Labels a test as 'slow'"

    >>> rare = make_label_dec(['slow','hard'],
    ... "Mix labels 'slow' and 'hard' for rare tests")
    >>> @rare
    ... def f(): pass
    ...
    >>>
    >>> f.slow
    True
    >>> f.hard
    True
    """
    if isinstance(label, str):
        labels = [label]
    else:
        labels = label
    # Validate that the given label(s) are OK for use in setattr() by doing a
    # dry run on a dummy function.
    tmp = lambda: None
    for label in labels:
        setattr(tmp, label, True)
    # This is the actual decorator we'll return

    def decor(f):
        for label in labels:
            setattr(f, label, True)
        return f

    # Apply the user's docstring
    if ds is None:
        ds = "Labels a test as %r" % label
        decor.__doc__ = ds
    return decor


# For tests that need further review


def needs_review(msg):
    """ Skip a test that needs further review.

    Parameters
    ----------
    msg : string
        msg regarding the review that needs to be done
    """

    def skip_func(func):
        return dec.skipif(True, msg)(func)

    return skip_func


# Easier version of the numpy knownfailure
def knownfailure(f):
    return dec.knownfailureif(True)(f)


def if_datasource(ds, msg):
    try:
        ds.get_filename()
    except DataError:
        return dec.skipif(True, msg)
    return lambda f: f
