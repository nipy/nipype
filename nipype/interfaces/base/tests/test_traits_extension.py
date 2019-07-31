# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Check the resolving/rebasing feature of ``BasePath``s."""
from __future__ import print_function, unicode_literals

from ... import base as nib
from ..traits_extension import rebase_path_traits, resolve_path_traits, Path


class _test_spec(nib.TraitedSpec):
    a = nib.File()
    b = nib.traits.Tuple(nib.File(), nib.File())
    c = nib.traits.List(nib.File())
    d = nib.traits.Either(nib.File(), nib.traits.Float())
    e = nib.OutputMultiObject(nib.File())
    ee = nib.OutputMultiObject(nib.Str)
    f = nib.traits.Dict(nib.Str, nib.File())
    g = nib.traits.Either(nib.File, nib.Str)
    h = nib.Str
    i = nib.traits.Either(nib.File, nib.traits.Tuple(nib.File, nib.traits.Int))
    j = nib.traits.Either(nib.File, nib.traits.Tuple(nib.File, nib.traits.Int),
                          nib.traits.Dict(nib.Str, nib.File()))


def test_rebase_resolve_path_traits():
    """Check rebase_path_traits and resolve_path_traits and idempotence."""
    spec = _test_spec()

    v = '/some/path/f1.txt'
    a = rebase_path_traits(spec.trait('a'), v, '/some/path')
    assert a == Path('f1.txt')

    a = resolve_path_traits(spec.trait('a'), a, '/some/path')
    assert a == Path(v)

    a = rebase_path_traits(spec.trait('a'), v, '/some/other/path')
    assert a == Path(v)

    a = resolve_path_traits(spec.trait('a'), a, '/some/path')
    assert a == Path(v)

    v = ('/some/path/f1.txt', '/some/path/f2.txt')
    b = rebase_path_traits(spec.trait('b'), v, '/some/path')
    assert b == (Path('f1.txt'), Path('f2.txt'))

    b = resolve_path_traits(spec.trait('b'), b, '/some/path')
    assert b == (Path(v[0]), Path(v[1]))

    v = ['/some/path/f1.txt', '/some/path/f2.txt', '/some/path/f3.txt']
    c = rebase_path_traits(spec.trait('c'), v, '/some/path')
    assert c == [Path('f1.txt'), Path('f2.txt'), Path('f3.txt')]

    c = resolve_path_traits(spec.trait('c'), c, '/some/path')
    assert c == [Path(vp) for vp in v]

    v = 2.0
    d = rebase_path_traits(spec.trait('d'), v, '/some/path')
    assert d == v

    d = resolve_path_traits(spec.trait('d'), d, '/some/path')
    assert d == v

    v = '/some/path/either.txt'
    d = rebase_path_traits(spec.trait('d'), v, '/some/path')
    assert d == Path('either.txt')

    d = resolve_path_traits(spec.trait('d'), d, '/some/path')
    assert d == Path(v)

    v = ['/some/path/f1.txt', '/some/path/f2.txt', '/some/path/f3.txt']
    e = rebase_path_traits(spec.trait('e'), v, '/some/path')
    assert e == [Path('f1.txt'), Path('f2.txt'), Path('f3.txt')]

    e = resolve_path_traits(spec.trait('e'), e, '/some/path')
    assert e == [Path(vp) for vp in v]

    v = [['/some/path/f1.txt', '/some/path/f2.txt'], [['/some/path/f3.txt']]]
    e = rebase_path_traits(spec.trait('e'), v, '/some/path')
    assert e == [[Path('f1.txt'), Path('f2.txt')], [[Path('f3.txt')]]]

    e = resolve_path_traits(spec.trait('e'), e, '/some/path')
    assert e == [[[Path(vpp) for vpp in vp] if isinstance(vp, list) else Path(vp) for vp in inner]
                 for inner in v]

    # These are Str - no rebasing/resolving should happen
    v = [['/some/path/f1.txt', '/some/path/f2.txt'], [['/some/path/f3.txt']]]
    ee = rebase_path_traits(spec.trait('ee'), v, '/some/path')
    assert ee == v

    ee = resolve_path_traits(spec.trait('ee'), [['f1.txt', 'f2.txt'], [['f3.txt']]], '/some/path')
    assert ee == [['f1.txt', 'f2.txt'], [['f3.txt']]]

    v = {'1': '/some/path/f1.txt'}
    f = rebase_path_traits(spec.trait('f'), v, '/some')
    assert f == {'1': Path('path/f1.txt')}

    f = resolve_path_traits(spec.trait('f'), f, '/some')
    assert f == {k: Path(val) for k, val in v.items()}

    # Either(Str, File): passing in path-like apply manipulation
    v = '/some/path/either.txt'
    g = rebase_path_traits(spec.trait('g'), v, '/some/path')
    assert g == Path('either.txt')

    g = resolve_path_traits(spec.trait('g'), g, '/some/path')
    assert g == Path(v)

    g = rebase_path_traits(spec.trait('g'), v, '/some')
    assert g == Path('path/either.txt')

    g = resolve_path_traits(spec.trait('g'), g, '/some')
    assert g == Path(v)

    # Either(Str, File): passing str discards File
    v = 'either.txt'
    g = rebase_path_traits(spec.trait('g'), v, '/some/path')
    assert g == v

    # This is a problematic case, it is impossible to know whether this
    # was meant to be a string or a file.
    # In this implementation, strings take precedence
    g = resolve_path_traits(spec.trait('g'), g, '/some/path')
    assert g == v

    v = 'string'
    g = rebase_path_traits(spec.trait('g'), v, '/some')
    assert g == v

    # This is a problematic case, it is impossible to know whether this
    # was meant to be a string or a file.
    g = resolve_path_traits(spec.trait('g'), v, '/some')
    assert g == v

    v = v
    g = rebase_path_traits(spec.trait('g'), v, '/some/path')
    assert g == v  # You dont want this one to be a Path

    # This is a problematic case, it is impossible to know whether this
    # was meant to be a string or a file.
    g = resolve_path_traits(spec.trait('g'), g, '/some/path')
    assert g == v  # You dont want this one to be a Path

    h = rebase_path_traits(spec.trait('h'), v, '/some/path')
    assert h == v

    h = resolve_path_traits(spec.trait('h'), h, '/some/path')
    assert h == v

    v = '/some/path/either/file.txt'
    i = rebase_path_traits(spec.trait('i'), v, '/some/path')
    assert i == Path('either/file.txt')

    i = resolve_path_traits(spec.trait('i'), i, '/some/path')
    assert i == Path(v)

    v = ('/some/path/either/tuple/file.txt', 2)
    i = rebase_path_traits(spec.trait('i'), v, '/some/path')
    assert i == (Path('either/tuple/file.txt'), 2)

    i = resolve_path_traits(spec.trait('i'), i, '/some/path')
    assert i == (Path(v[0]), v[1])

    v = '/some/path/either/file.txt'
    j = rebase_path_traits(spec.trait('j'), v, '/some/path')
    assert j == Path('either/file.txt')

    j = resolve_path_traits(spec.trait('j'), j, '/some/path')
    assert j == Path(v)

    v = ('/some/path/either/tuple/file.txt', 2)
    j = rebase_path_traits(spec.trait('j'), ('/some/path/either/tuple/file.txt', 2), '/some/path')
    assert j == (Path('either/tuple/file.txt'), 2)

    j = resolve_path_traits(spec.trait('j'), j, '/some/path')
    assert j == (Path(v[0]), v[1])

    v = {'a': '/some/path/either/dict/file.txt'}
    j = rebase_path_traits(spec.trait('j'), v, '/some/path')
    assert j == {'a': Path('either/dict/file.txt')}

    j = resolve_path_traits(spec.trait('j'), j, '/some/path')
    assert j == {k: Path(val) for k, val in v.items()}
