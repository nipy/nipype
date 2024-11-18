# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import pytest

import acres

from ....utils.filemanip import md5
from ... import base as nib


@pytest.mark.parametrize("args", [{}, {"a": 1, "b": [2, 3]}])
def test_bunch(args):
    b = nib.Bunch(**args)
    assert b.__dict__ == args


def test_bunch_attribute():
    b = nib.Bunch(a=1, b=[2, 3], c=None)
    assert b.a == 1
    assert b.b == [2, 3]
    assert b.c is None


def test_bunch_repr():
    b = nib.Bunch(b=2, c=3, a=dict(n=1, m=2))
    assert repr(b) == "Bunch(a={'m': 2, 'n': 1}, b=2, c=3)"


def test_bunch_methods():
    b = nib.Bunch(a=2)
    b.update(a=3)
    newb = b.dictcopy()
    assert b.a == 3
    assert b.get("a") == 3
    assert b.get("badkey", "otherthing") == "otherthing"
    assert b != newb
    assert type(newb) is dict
    assert newb["a"] == 3


def test_bunch_hash():
    # NOTE: Since the path to the json file is included in the Bunch,
    # the hash will be unique to each machine.
    json_pth = acres.Loader('nipype.testing').cached('data', 'realign_json.json')

    b = nib.Bunch(infile=str(json_pth), otherthing="blue", yat=True)
    newbdict, bhash = b._get_bunch_hash()
    assert bhash == "d1f46750044c3de102efc847720fc35f"
    # Make sure the hash stored in the json file for `infile` is correct.
    jshash = md5()
    jshash.update(json_pth.read_bytes())
    assert newbdict["infile"][0][1] == jshash.hexdigest()
    assert newbdict["yat"] is True
