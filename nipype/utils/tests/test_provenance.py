# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
from nibabel.optpkg import optional_package
import pytest

_, have_rdflib5, _ = optional_package("rdflib", min_version="5.0.0")

from nipype.utils.provenance import ProvStore, safe_encode

needs_rdflib5 = pytest.mark.skipif(
    not have_rdflib5, reason="Test requires rdflib 5.0.0 or higher"
)


@needs_rdflib5
@pytest.mark.timeout(60)
def test_provenance(tmpdir):
    from nipype.interfaces.base import CommandLine

    tmpdir.chdir()
    ps = ProvStore()
    results = CommandLine("echo hello").run()
    ps.add_results(results)
    provn = ps.g.get_provn()
    assert "echo hello" in provn


@needs_rdflib5
@pytest.mark.timeout(60)
def test_provenance_exists(tmpdir):
    tmpdir.chdir()
    from nipype import config
    from nipype.interfaces.base import CommandLine

    provenance_state = config.get("execution", "write_provenance")
    hash_state = config.get("execution", "hash_method")
    config.enable_provenance()
    CommandLine("echo hello").run()
    config.set("execution", "write_provenance", provenance_state)
    config.set("execution", "hash_method", hash_state)
    assert tmpdir.join("provenance.provn").check()


def test_safe_encode():
    a = "\xc3\xa9lg"
    out = safe_encode(a)
    assert out.value == a
