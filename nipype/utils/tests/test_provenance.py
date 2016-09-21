# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import unicode_literals
from builtins import str, bytes
from future import standard_library
standard_library.install_aliases()


import os
from tempfile import mkdtemp

from nipype.testing import assert_equal, assert_true, assert_false
from nipype.utils.provenance import ProvStore, safe_encode

def test_provenance():
    ps = ProvStore()
    from nipype.interfaces.base import CommandLine
    results = CommandLine('echo hello').run()
    ps.add_results(results)
    provn = ps.g.get_provn()
    prov_json = ps.g.serialize(format='json')
    yield assert_true, 'echo hello' in provn

def test_provenance_exists():
    tempdir = mkdtemp()
    cwd = os.getcwd()
    os.chdir(tempdir)
    from nipype import config
    from nipype.interfaces.base import CommandLine
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
    yield assert_equal, out.value, a
