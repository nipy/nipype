# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import unicode_literals
from builtins import str, bytes
from future import standard_library
standard_library.install_aliases()

import os

from nipype.utils.provenance import ProvStore, safe_encode


def test_provenance(tmpdir):
    from nipype.interfaces.base import CommandLine
    tmpdir.chdir()
    ps = ProvStore()
    results = CommandLine('echo hello').run()
    ps.add_results(results)
    provn = ps.g.get_provn()
    assert 'echo hello' in provn


def test_provenance_exists(tmpdir):
    tmpdir.chdir()
    from nipype import config
    from nipype.interfaces.base import CommandLine
    provenance_state = config.get('execution', 'write_provenance')
    hash_state = config.get('execution', 'hash_method')
    config.enable_provenance()
    CommandLine('echo hello').run()
    config.set('execution', 'write_provenance', provenance_state)
    config.set('execution', 'hash_method', hash_state)
    assert tmpdir.join('provenance.provn').check()


def test_safe_encode():
    a = '\xc3\xa9lg'
    out = safe_encode(a)
    assert out.value == a
