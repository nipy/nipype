import os
from tempfile import mkstemp

from nipype.testing import assert_equal, assert_true
from nipype.utils.filemanip import (save_json, load_json, loadflat,
                                    fname_presuffix, fnames_presuffix)

import numpy as np

def test_fname_presuffix():
    fname = 'foo.nii'
    pth = fname_presuffix(fname, 'pre_', '_post', '/tmp')
    yield assert_equal, pth, '/tmp/pre_foo_post.nii'
    fname += '.gz'
    pth = fname_presuffix(fname, 'pre_', '_post', '/tmp')
    yield assert_equal, pth, '/tmp/pre_foo_post.nii.gz'
    pth = fname_presuffix(fname, 'pre_', '_post', '/tmp', use_ext=False)
    yield assert_equal, pth, '/tmp/pre_foo_post'

def test_fnames_presuffix():
    fnames = ['foo.nii', 'bar.nii']
    pths = fnames_presuffix(fnames, 'pre_', '_post', '/tmp')
    yield assert_equal, pths, ['/tmp/pre_foo_post.nii', '/tmp/pre_bar_post.nii']

def test_json():
    # Simple roundtrip test of json files, just a sanity check.
    adict = dict(a='one', c='three', b='two')
    fd, name = mkstemp(suffix='.json')
    save_json(name, adict) # save_json closes the file
    new_dict = load_json(name)
    os.unlink(name)
    yield assert_equal, sorted(adict.items()), sorted(new_dict.items())

def test_loadflat():
    alist = [dict(a='one', c='three', b='two'),
             dict(a='one', c='three', b='two')]
    fd, name = mkstemp(suffix='.npz')
    np.savez(name,a=alist)
    aloaded = loadflat(name)['a']
    os.unlink(name)
    yield assert_equal, len(aloaded), 2
    yield assert_equal, sorted(aloaded[0].items()), sorted(alist[0].items())
    adict = dict(a='one', c='three', b='two')
    fd, name = mkstemp(suffix='.npz')
    np.savez(name,a=adict)
    aloaded = loadflat(name)['a']
    os.unlink(name)
    yield assert_true, isinstance(aloaded, dict)
    yield assert_equal, sorted(aloaded.items()), sorted(adict.items())
    
