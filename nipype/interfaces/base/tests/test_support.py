# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import print_function, unicode_literals
import os
import pytest
from builtins import open
from future import standard_library
from pkg_resources import resource_filename as pkgrf

from ....utils.filemanip import md5
from ... import base as nib

standard_library.install_aliases()


@pytest.mark.parametrize("args", [{}, {'a': 1, 'b': [2, 3]}])
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
    assert b.get('a') == 3
    assert b.get('badkey', 'otherthing') == 'otherthing'
    assert b != newb
    assert type(dict()) == type(newb)
    assert newb['a'] == 3


def test_bunch_hash():
    # NOTE: Since the path to the json file is included in the Bunch,
    # the hash will be unique to each machine.
    json_pth = pkgrf('nipype',
                     os.path.join('testing', 'data', 'realign_json.json'))

    b = nib.Bunch(infile=json_pth, otherthing='blue', yat=True)
    newbdict, bhash = b._get_bunch_hash()
    assert bhash == 'd1f46750044c3de102efc847720fc35f'
    # Make sure the hash stored in the json file for `infile` is correct.
    jshash = md5()
    with open(json_pth, 'r') as fp:
        jshash.update(fp.read().encode('utf-8'))
    assert newbdict['infile'][0][1] == jshash.hexdigest()
    assert newbdict['yat'] is True
