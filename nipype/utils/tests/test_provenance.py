# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from future import standard_library
standard_library.install_aliases()
from builtins import str

import os
from tempfile import mkdtemp

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

def test_provenance_exists():
    tempdir = mkdtemp()
    cwd = os.getcwd()
    os.chdir(tempdir)
    from ...interfaces.base import CommandLine
    from ... import config
    provenance_state = config.get('execution', 'write_provenance')
    hash_state = config.get('execution', 'hash_method')
    config.enable_provenance()
    CommandLine('echo hello').run()
    config.set('execution', 'write_provenance', provenance_state)
    config.set('execution', 'hash_method', hash_state)
    provenance_exists = os.path.exists(os.path.join(tempdir, 'provenance.provn'))
    os.chdir(cwd)
    yield assert_true, provenance_exists

def test_safe_encode():
    a = '\xc3\xa9lg'
    out = safe_encode(a)
    if not isinstance(a, str):
        a = text_type(a, 'utf-8')
    yield assert_equal, out.value, a