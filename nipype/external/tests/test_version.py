import warnings

import pytest

from nipype.external.version import LooseVersion as Vendored

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    try:
        from distutils.version import LooseVersion as Original
    except ImportError:
        pytest.skip()


@pytest.mark.parametrize("v1, v2", [("0.0.0", "0.0.0"), ("0.0.0", "1.0.0")])
def test_LooseVersion_compat(v1, v2):
    vend1, vend2 = Vendored(v1), Vendored(v2)
    orig1, orig2 = Original(v1), Original(v2)

    assert vend1 == orig1
    assert orig1 == vend1
    assert vend2 == orig2
    assert orig2 == vend2
    assert (vend1 == orig2) == (v1 == v2)
    assert (vend1 < orig2) == (v1 < v2)
    assert (vend1 > orig2) == (v1 > v2)
    assert (vend1 <= orig2) == (v1 <= v2)
    assert (vend1 >= orig2) == (v1 >= v2)
    assert (orig1 == vend2) == (v1 == v2)
    assert (orig1 < vend2) == (v1 < v2)
    assert (orig1 > vend2) == (v1 > v2)
    assert (orig1 <= vend2) == (v1 <= v2)
    assert (orig1 >= vend2) == (v1 >= v2)
