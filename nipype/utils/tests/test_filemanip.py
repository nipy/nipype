import os
from tempfile import mkstemp

from nipype.testing import assert_equal, assert_true, assert_false
from nipype.utils.filemanip import (save_json, load_json, loadflat,
                                    fname_presuffix, fnames_presuffix,
                                    hash_rename, check_forhash,
                                    copyfile)

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

def test_hash_rename():
    new_name = hash_rename('foobar.nii', 'abc123')
    assert_equal(new_name, 'foobar_0xabc123.nii')

def test_check_forhash():
    fname = 'foobar'
    orig_hash = '_0x4323dbcefdc51906decd8edcb3327943'
    hashed_name = ''.join((fname, orig_hash, '.nii'))
    result, hash = check_forhash(hashed_name)
    yield assert_true, result
    yield assert_equal, hash, [orig_hash]
    result, hash = check_forhash('foobar.nii')
    yield assert_false, result
    yield assert_equal, hash, None

def test_copyfile():
    fd, orig_img = mkstemp(suffix = '.img')
    orig_hdr = orig_img[:-4] + '.hdr'
    fp = file(orig_hdr, 'w+')
    fp.close()
    pth, fname = os.path.split(orig_img)
    new_img = os.path.join(pth, 'newfile.img')
    new_hdr = os.path.join(pth, 'newfile.hdr')
    copyfile(orig_img, new_img)
    yield assert_true, os.path.exists(new_img)
    yield assert_true, os.path.exists(new_hdr)
    os.unlink(new_img)
    os.unlink(new_hdr)
    # Test with copy=True
    copyfile(orig_img, new_img, copy=True)
    yield assert_true, os.path.exists(new_img)
    yield assert_true, os.path.exists(new_hdr)
    os.unlink(new_img)
    os.unlink(new_hdr)
    # final cleanup
    os.unlink(orig_img)
    os.unlink(orig_hdr)

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
    
