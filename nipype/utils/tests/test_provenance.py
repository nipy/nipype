# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from future import standard_library
standard_library.install_aliases()
from builtins import str

import sys

from ...testing import assert_equal, assert_true, assert_false

from ..provenance import ProvStore, safe_encode, text_type


def test_provenance():
    ps = ProvStore()
    from ...interfaces.base import CommandLine
    results = CommandLine('echo hello').run()
    ps.add_results(results)
    provn = ps.g.get_provn()
    prov_json = ps.g.serialize(format='json')
    yield assert_true, 'echo hello' in provn

def test_safe_encode():
    a = '\xc3\xa9lg'
    out = safe_encode(a)
    if not isinstance(a, str):
        a = text_type(a, 'utf-8')
    yield assert_equal, out.value, a