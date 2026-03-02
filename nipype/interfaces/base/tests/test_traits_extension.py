# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Check the resolving/rebasing feature of ``BasePath``s."""
from ... import base as nib
from ..traits_extension import rebase_path_traits, resolve_path_traits, Path


class _test_spec(nib.TraitedSpec):
    a = nib.File()
    b = nib.Tuple(nib.File(), nib.File())
    c = nib.traits.List(nib.File())
    d = nib.traits.Either(nib.File(), nib.traits.Float())
    e = nib.OutputMultiObject(nib.File())
    ee = nib.OutputMultiObject(nib.Str)
    f = nib.traits.Dict(nib.Str, nib.File())
    g = nib.traits.Either(nib.File, nib.Str)
    h = nib.Str
    i = nib.traits.Either(nib.File, nib.Tuple(nib.File, nib.traits.Int))
    j = nib.traits.Either(
        nib.File,
        nib.Tuple(nib.File, nib.traits.Int),
        nib.traits.Dict(nib.Str, nib.File()),
    )
    k = nib.DictStrStr


def test_rebase_resolve_path_traits():
    """Check rebase_path_traits and resolve_path_traits and idempotence."""
    spec = _test_spec()

    v = "/some/path/f1.txt"
    a = rebase_path_traits(spec.trait("a"), v, "/some/path")
    assert a == Path("f1.txt")

    # Idempotence
    assert rebase_path_traits(spec.trait("a"), a, "/some/path") == a

    a = resolve_path_traits(spec.trait("a"), a, "/some/path")
    assert a == Path(v)

    # Idempotence
    assert resolve_path_traits(spec.trait("a"), a, "/some/path") == a

    a = rebase_path_traits(spec.trait("a"), v, "/some/other/path")
    assert a == Path(v)

    # Idempotence
    assert rebase_path_traits(spec.trait("a"), a, "/some/other/path") == a

    a = resolve_path_traits(spec.trait("a"), a, "/some/path")
    assert a == Path(v)

    # Idempotence
    assert resolve_path_traits(spec.trait("a"), a, "/some/path") == a

    v = ("/some/path/f1.txt", "/some/path/f2.txt")
    b = rebase_path_traits(spec.trait("b"), v, "/some/path")
    assert b == (Path("f1.txt"), Path("f2.txt"))

    # Idempotence
    assert rebase_path_traits(spec.trait("b"), b, "/some/path") == b

    b = resolve_path_traits(spec.trait("b"), b, "/some/path")
    assert b == (Path(v[0]), Path(v[1]))

    # Idempotence
    assert resolve_path_traits(spec.trait("b"), b, "/some/path") == b

    v = ["/some/path/f1.txt", "/some/path/f2.txt", "/some/path/f3.txt"]
    c = rebase_path_traits(spec.trait("c"), v, "/some/path")
    assert c == [Path("f1.txt"), Path("f2.txt"), Path("f3.txt")]

    # Idempotence
    assert rebase_path_traits(spec.trait("c"), c, "/some/path") == c

    c = resolve_path_traits(spec.trait("c"), c, "/some/path")
    assert c == [Path(vp) for vp in v]

    # Idempotence
    assert resolve_path_traits(spec.trait("c"), c, "/some/path") == c

    v = 2.0
    d = rebase_path_traits(spec.trait("d"), v, "/some/path")
    assert d == v

    d = resolve_path_traits(spec.trait("d"), d, "/some/path")
    assert d == v

    v = "/some/path/either.txt"
    d = rebase_path_traits(spec.trait("d"), v, "/some/path")
    assert d == Path("either.txt")

    # Idempotence
    assert rebase_path_traits(spec.trait("d"), d, "/some/path") == d

    d = resolve_path_traits(spec.trait("d"), d, "/some/path")
    assert d == Path(v)

    # Idempotence
    assert resolve_path_traits(spec.trait("d"), d, "/some/path") == d

    v = ["/some/path/f1.txt", "/some/path/f2.txt", "/some/path/f3.txt"]
    e = rebase_path_traits(spec.trait("e"), v, "/some/path")
    assert e == [Path("f1.txt"), Path("f2.txt"), Path("f3.txt")]

    # Idempotence
    assert rebase_path_traits(spec.trait("e"), e, "/some/path") == e

    e = resolve_path_traits(spec.trait("e"), e, "/some/path")
    assert e == [Path(vp) for vp in v]

    # Idempotence
    assert resolve_path_traits(spec.trait("e"), e, "/some/path") == e

    v = [["/some/path/f1.txt", "/some/path/f2.txt"], [["/some/path/f3.txt"]]]
    e = rebase_path_traits(spec.trait("e"), v, "/some/path")
    assert e == [[Path("f1.txt"), Path("f2.txt")], [[Path("f3.txt")]]]

    # Idempotence
    assert rebase_path_traits(spec.trait("e"), e, "/some/path") == e

    e = resolve_path_traits(spec.trait("e"), e, "/some/path")
    assert e == [
        [
            [Path(vpp) for vpp in vp] if isinstance(vp, list) else Path(vp)
            for vp in inner
        ]
        for inner in v
    ]

    # Idempotence
    assert resolve_path_traits(spec.trait("e"), e, "/some/path") == e

    # These are Str - no rebasing/resolving should happen
    v = [["/some/path/f1.txt", "/some/path/f2.txt"], [["/some/path/f3.txt"]]]
    ee = rebase_path_traits(spec.trait("ee"), v, "/some/path")
    assert ee == v

    # Idempotence
    assert rebase_path_traits(spec.trait("ee"), ee, "/some/path") == ee

    ee = resolve_path_traits(
        spec.trait("ee"), [["f1.txt", "f2.txt"], [["f3.txt"]]], "/some/path"
    )
    assert ee == [["f1.txt", "f2.txt"], [["f3.txt"]]]

    # Idempotence
    assert resolve_path_traits(spec.trait("ee"), ee, "/some/path") == ee

    v = {"1": "/some/path/f1.txt"}
    f = rebase_path_traits(spec.trait("f"), v, "/some")
    assert f == {"1": Path("path/f1.txt")}

    # Idempotence
    assert rebase_path_traits(spec.trait("f"), f, "/some") == f

    f = resolve_path_traits(spec.trait("f"), f, "/some")
    assert f == {k: Path(val) for k, val in v.items()}

    # Idempotence
    assert resolve_path_traits(spec.trait("f"), f, "/some") == f

    # Either(Str, File): passing in path-like apply manipulation
    v = "/some/path/either.txt"
    g = rebase_path_traits(spec.trait("g"), v, "/some/path")
    assert g == Path("either.txt")

    # Idempotence
    assert rebase_path_traits(spec.trait("g"), g, "/some/path") == g

    g = resolve_path_traits(spec.trait("g"), g, "/some/path")
    assert g == Path(v)

    # Idempotence
    assert resolve_path_traits(spec.trait("g"), g, "/some/path") == g

    g = rebase_path_traits(spec.trait("g"), v, "/some")
    assert g == Path("path/either.txt")

    # Idempotence
    assert rebase_path_traits(spec.trait("g"), g, "/some/path") == g

    g = resolve_path_traits(spec.trait("g"), g, "/some")
    assert g == Path(v)

    # Idempotence
    assert resolve_path_traits(spec.trait("g"), g, "/some/path") == g

    # Either(Str, File): passing str discards File
    v = "either.txt"
    g = rebase_path_traits(spec.trait("g"), v, "/some/path")
    assert g == v

    # Idempotence
    assert rebase_path_traits(spec.trait("g"), g, "/some/path") == g

    # This is a problematic case, it is impossible to know whether this
    # was meant to be a string or a file.
    # In this implementation, strings take precedence
    g = resolve_path_traits(spec.trait("g"), g, "/some/path")
    assert g == v

    # Idempotence
    assert resolve_path_traits(spec.trait("g"), g, "/some/path") == g

    v = "string"
    g = rebase_path_traits(spec.trait("g"), v, "/some")
    assert g == v

    # Idempotence
    assert rebase_path_traits(spec.trait("g"), g, "/some") == g

    # This is a problematic case, it is impossible to know whether this
    # was meant to be a string or a file.
    g = resolve_path_traits(spec.trait("g"), v, "/some")
    assert g == v

    # Idempotence
    assert resolve_path_traits(spec.trait("g"), g, "/some") == g

    g = rebase_path_traits(spec.trait("g"), v, "/some/path")
    assert g == v  # You dont want this one to be a Path

    # Idempotence
    assert rebase_path_traits(spec.trait("g"), g, "/some/path") == g

    # This is a problematic case, it is impossible to know whether this
    # was meant to be a string or a file.
    g = resolve_path_traits(spec.trait("g"), g, "/some/path")
    assert g == v  # You dont want this one to be a Path

    # Idempotence
    assert resolve_path_traits(spec.trait("g"), g, "/some/path") == g

    h = rebase_path_traits(spec.trait("h"), v, "/some/path")
    assert h == v

    # Idempotence
    assert rebase_path_traits(spec.trait("h"), h, "/some/path") == h

    h = resolve_path_traits(spec.trait("h"), h, "/some/path")
    assert h == v

    # Idempotence
    assert resolve_path_traits(spec.trait("h"), h, "/some/path") == h

    v = "/some/path/either/file.txt"
    i = rebase_path_traits(spec.trait("i"), v, "/some/path")
    assert i == Path("either/file.txt")

    # Idempotence
    assert rebase_path_traits(spec.trait("i"), i, "/some/path") == i

    i = resolve_path_traits(spec.trait("i"), i, "/some/path")
    assert i == Path(v)

    # Idempotence
    assert resolve_path_traits(spec.trait("i"), i, "/some/path") == i

    v = ("/some/path/either/tuple/file.txt", 2)
    i = rebase_path_traits(spec.trait("i"), v, "/some/path")
    assert i == (Path("either/tuple/file.txt"), 2)

    # Idempotence
    assert rebase_path_traits(spec.trait("i"), i, "/some/path") == i

    i = resolve_path_traits(spec.trait("i"), i, "/some/path")
    assert i == (Path(v[0]), v[1])

    # Idempotence
    assert resolve_path_traits(spec.trait("i"), i, "/some/path") == i

    v = "/some/path/either/file.txt"
    j = rebase_path_traits(spec.trait("j"), v, "/some/path")
    assert j == Path("either/file.txt")

    # Idempotence
    assert rebase_path_traits(spec.trait("j"), j, "/some/path") == j

    j = resolve_path_traits(spec.trait("j"), j, "/some/path")
    assert j == Path(v)

    # Idempotence
    assert resolve_path_traits(spec.trait("j"), j, "/some/path") == j

    v = ("/some/path/either/tuple/file.txt", 2)
    j = rebase_path_traits(
        spec.trait("j"), ("/some/path/either/tuple/file.txt", 2), "/some/path"
    )
    assert j == (Path("either/tuple/file.txt"), 2)

    # Idempotence
    assert rebase_path_traits(spec.trait("j"), j, "/some/path") == j

    j = resolve_path_traits(spec.trait("j"), j, "/some/path")
    assert j == (Path(v[0]), v[1])

    # Idempotence
    assert resolve_path_traits(spec.trait("j"), j, "/some/path") == j

    v = {"a": "/some/path/either/dict/file.txt"}
    j = rebase_path_traits(spec.trait("j"), v, "/some/path")
    assert j == {"a": Path("either/dict/file.txt")}

    # Idempotence
    assert rebase_path_traits(spec.trait("j"), j, "/some/path") == j

    j = resolve_path_traits(spec.trait("j"), j, "/some/path")
    assert j == {k: Path(val) for k, val in v.items()}

    # Idempotence
    assert resolve_path_traits(spec.trait("j"), j, "/some/path") == j

    v = {"path": "/some/path/f1.txt"}
    k = rebase_path_traits(spec.trait("k"), v, "/some/path")
    assert k == v

    # Idempotence
    assert rebase_path_traits(spec.trait("k"), k, "/some/path") == k

    k = resolve_path_traits(spec.trait("k"), k, "/some/path")
    assert k == v
