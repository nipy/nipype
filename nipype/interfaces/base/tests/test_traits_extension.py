# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import print_function, unicode_literals

from ... import base as nib
from ..traits_extension import rebase_path_traits, Path


class _test_spec(nib.TraitedSpec):
    a = nib.traits.File()
    b = nib.traits.Tuple(nib.File(),
                         nib.File())
    c = nib.traits.List(nib.File())
    d = nib.traits.Either(nib.File(), nib.traits.Float())
    e = nib.OutputMultiObject(nib.File())
    f = nib.traits.Dict(nib.Str, nib.File())
    g = nib.traits.Either(nib.File, nib.Str)
    h = nib.Str


def test_rebase_path_traits():
    """Check rebase_path_traits."""
    spec = _test_spec()

    a = rebase_path_traits(
        spec.trait('a'), '/some/path/f1.txt', '/some/path')
    assert '%s' % a == 'f1.txt'

    b = rebase_path_traits(
        spec.trait('b'), ('/some/path/f1.txt', '/some/path/f2.txt'), '/some/path')
    assert b == (Path('f1.txt'), Path('f2.txt'))

    c = rebase_path_traits(
        spec.trait('c'), ['/some/path/f1.txt', '/some/path/f2.txt', '/some/path/f3.txt'],
        '/some/path')
    assert c == [Path('f1.txt'), Path('f2.txt'), Path('f3.txt')]

    e = rebase_path_traits(
        spec.trait('e'), ['/some/path/f1.txt', '/some/path/f2.txt', '/some/path/f3.txt'],
        '/some/path')
    assert e == [Path('f1.txt'), Path('f2.txt'), Path('f3.txt')]

    f = rebase_path_traits(
        spec.trait('f'), {'1': '/some/path/f1.txt'}, '/some/path')
    assert f == {'1': Path('f1.txt')}

    d = rebase_path_traits(
        spec.trait('d'), 2.0, '/some/path')
    assert d == 2.0

    d = rebase_path_traits(
        spec.trait('d'), '/some/path/either.txt', '/some/path')
    assert '%s' % d == 'either.txt'

    g = rebase_path_traits(
        spec.trait('g'), 'some/path/either.txt', '/some/path')
    assert '%s' % g == 'some/path/either.txt'

    g = rebase_path_traits(
        spec.trait('g'), '/some/path/either.txt', '/some')
    assert '%s' % g == 'path/either.txt'

    g = rebase_path_traits(spec.trait('g'), 'string', '/some')
    assert '%s' % g == 'string'

    g = rebase_path_traits(spec.trait('g'), '2', '/some/path')
    assert g == '2'  # You dont want this one to be a Path

    h = rebase_path_traits(spec.trait('h'), '2', '/some/path')
    assert h == '2'
