# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from future import standard_library
standard_library.install_aliases()

from nipype.testing import assert_equal, assert_true, assert_false

from ..provenance import ProvStore


def test_provenance():
    ps = ProvStore()
    from ...interfaces.base import CommandLine
    results = CommandLine('echo hello').run()
    ps.add_results(results)
    provn = ps.g.get_provn()
    prov_json = ps.g.serialize(format='json')
    yield assert_true, 'echo hello' in provn
