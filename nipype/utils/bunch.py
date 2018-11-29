# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Nipype Bunch container"""
from __future__ import (print_function, unicode_literals, division,
                        absolute_import)
from copy import deepcopy
from builtins import object


class Bunch(object):
    """Dictionary-like class that provides attribute-style access to it's items.

    A `Bunch` is a simple container that stores it's items as class
    attributes.  Internally all items are stored in a dictionary and
    the class exposes several of the dictionary methods.

    Examples
    --------
    >>> from nipype.utils.bunch import Bunch
    >>> inputs = Bunch(infile='subj.nii', fwhm=6.0, register_to_mean=True)
    >>> inputs
    Bunch(fwhm=6.0, infile='subj.nii', register_to_mean=True)
    >>> inputs.register_to_mean = False
    >>> inputs
    Bunch(fwhm=6.0, infile='subj.nii', register_to_mean=False)

    Notes
    -----
    The Bunch pattern came from the Python Cookbook:

    .. [1] A. Martelli, D. Hudgeon, "Collecting a Bunch of Named
           Items", Python Cookbook, 2nd Ed, Chapter 4.18, 2005.

    """

    def __init__(self, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)

    def update(self, *args, **kwargs):
        """update existing attribute, or create new attribute

        Note: update is very much like HasTraits.set"""
        self.__dict__.update(*args, **kwargs)

    def items(self):
        """iterates over bunch attributes as key, value pairs"""
        return list(self.__dict__.items())

    def get(self, *args):
        """Support dictionary get() functionality
        """
        return self.__dict__.get(*args)

    def set(self, **kwargs):
        """Support dictionary get() functionality
        """
        return self.__dict__.update(**kwargs)

    def dictcopy(self):
        """returns a deep copy of existing Bunch as a dictionary"""
        return deepcopy(self.__dict__)

    def __repr__(self):
        """representation of the sorted Bunch as a string

        Currently, this string representation of the `inputs` Bunch of
        interfaces is hashed to determine if the process' dirty-bit
        needs setting or not. Till that mechanism changes, only alter
        this after careful consideration.
        """
        return bunch_repr(self)

    def _repr_pretty_(self, p, cycle):
        """Support for the pretty module from ipython.externals"""
        if cycle:
            p.text('Bunch(...)')
        else:
            p.begin_group(6, 'Bunch(')
            first = True
            for k, v in sorted(self.items()):
                if not first:
                    p.text(',')
                    p.breakable()
                p.text(k + '=')
                p.pretty(v)
                first = False
            p.end_group(6, ')')


def bunch_repr(instance, classname=None):
    """Represent dict-like objects as a Bunch

    >>> bunch_repr({'b': 2, 'c': 3, 'a': {'n': 1, 'm': 2}})
    "Bunch(a={'m': 2, 'n': 1}, b=2, c=3)"
    """
    classname = classname or 'Bunch'
    outstr = ['%s(' % classname]
    first = True
    for k, v in sorted(instance.items()):
        if not first:
            outstr.append(', ')
        if isinstance(v, dict):
            pairs = []
            for key, value in sorted(v.items()):
                pairs.append("'%s': %s" % (key, value))
            v = '{' + ', '.join(pairs) + '}'
            outstr.append('%s=%s' % (k, v))
        else:
            outstr.append('%s=%r' % (k, v))
        first = False
    outstr.append(')')
    return ''.join(outstr)
