# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import unicode_literals
from builtins import open

import os
import time
import warnings

import pytest
from ...testing import TempFATFS
from ...utils.filemanip import (save_json, load_json,
                                fname_presuffix, fnames_presuffix,
                                hash_rename, check_forhash,
                                _cifs_table, on_cifs,
                                copyfile, copyfiles,
                                filename_to_list, list_to_filename,
                                check_depends,
                                split_filename, get_related_files)

import numpy as np


def _ignore_atime(stat):
    return stat[:7] + stat[8:]

@pytest.mark.parametrize("filename, split",[
        ('foo.nii',                ('', 'foo', '.nii')),
        ('foo.nii.gz',             ('', 'foo', '.nii.gz')),
        ('/usr/local/foo.nii.gz',  ('/usr/local', 'foo', '.nii.gz')),
        ('../usr/local/foo.nii',   ('../usr/local', 'foo', '.nii')),
        ('/usr/local/foo.a.b.c.d', ('/usr/local', 'foo.a.b.c', '.d')),
        ('/usr/local/',            ('/usr/local', '', ''))
        ])
def test_split_filename(filename, split):
    res = split_filename(filename)
    assert res == split


def test_fname_presuffix():
    fname = 'foo.nii'
    pth = fname_presuffix(fname, 'pre_', '_post', '/tmp')
    assert pth == '/tmp/pre_foo_post.nii'
    fname += '.gz'
    pth = fname_presuffix(fname, 'pre_', '_post', '/tmp')
    assert pth == '/tmp/pre_foo_post.nii.gz'
    pth = fname_presuffix(fname, 'pre_', '_post', '/tmp', use_ext=False)
    assert pth == '/tmp/pre_foo_post'


def test_fnames_presuffix():
    fnames = ['foo.nii', 'bar.nii']
    pths = fnames_presuffix(fnames, 'pre_', '_post', '/tmp')
    assert pths == ['/tmp/pre_foo_post.nii', '/tmp/pre_bar_post.nii']

@pytest.mark.parametrize("filename, newname",[
        ('foobar.nii',    'foobar_0xabc123.nii'),
        ('foobar.nii.gz', 'foobar_0xabc123.nii.gz')
        ])
def test_hash_rename(filename, newname):
    new_name = hash_rename(filename, 'abc123')
    assert new_name == newname


def test_check_forhash():
    fname = 'foobar'
    orig_hash = '_0x4323dbcefdc51906decd8edcb3327943'
    hashed_name = ''.join((fname, orig_hash, '.nii'))
    result, hash = check_forhash(hashed_name)
    assert result
    assert hash == [orig_hash]
    result, hash = check_forhash('foobar.nii')
    assert not result
    assert hash == None

@pytest.fixture()
def _temp_analyze_files(tmpdir):
    """Generate temporary analyze file pair."""
    orig_img = tmpdir.join("orig.img")
    orig_hdr = tmpdir.join("orig.hdr")
    orig_img.open('w+').close()
    orig_hdr.open('w+').close()
    return str(orig_img), str(orig_hdr)


@pytest.fixture()
def _temp_analyze_files_prime(tmpdir):
    """Generate temporary analyze file pair."""
    orig_img = tmpdir.join("orig_prime.img")
    orig_hdr = tmpdir.join("orig_prime.hdr")
    orig_img.open('w+').close()
    orig_hdr.open('w+').close()
    return orig_img.strpath, orig_hdr.strpath


def test_copyfile(_temp_analyze_files):
    orig_img, orig_hdr = _temp_analyze_files
    pth, fname = os.path.split(orig_img)
    new_img = os.path.join(pth, 'newfile.img')
    new_hdr = os.path.join(pth, 'newfile.hdr')
    copyfile(orig_img, new_img)
    assert os.path.exists(new_img)
    assert os.path.exists(new_hdr)


def test_copyfile_true(_temp_analyze_files):
    orig_img, orig_hdr = _temp_analyze_files
    pth, fname = os.path.split(orig_img)
    new_img = os.path.join(pth, 'newfile.img')
    new_hdr = os.path.join(pth, 'newfile.hdr')
    # Test with copy=True
    copyfile(orig_img, new_img, copy=True)
    assert os.path.exists(new_img)
    assert os.path.exists(new_hdr)


def test_copyfiles(_temp_analyze_files, _temp_analyze_files_prime):
    orig_img1, orig_hdr1 = _temp_analyze_files
    orig_img2, orig_hdr2 = _temp_analyze_files_prime
    pth, fname = os.path.split(orig_img1)
    new_img1 = os.path.join(pth, 'newfile.img')
    new_hdr1 = os.path.join(pth, 'newfile.hdr')
    pth, fname = os.path.split(orig_img2)
    new_img2 = os.path.join(pth, 'secondfile.img')
    new_hdr2 = os.path.join(pth, 'secondfile.hdr')
    newfiles = copyfiles([orig_img1, orig_img2], [new_img1, new_img2])
    assert os.path.exists(new_img1)
    assert os.path.exists(new_hdr1)
    assert os.path.exists(new_img2)
    assert os.path.exists(new_hdr2)


def test_linkchain(_temp_analyze_files):
    if os.name is not 'posix':
        return
    orig_img, orig_hdr = _temp_analyze_files
    pth, fname = os.path.split(orig_img)
    new_img1 = os.path.join(pth, 'newfile1.img')
    new_hdr1 = os.path.join(pth, 'newfile1.hdr')
    new_img2 = os.path.join(pth, 'newfile2.img')
    new_hdr2 = os.path.join(pth, 'newfile2.hdr')
    new_img3 = os.path.join(pth, 'newfile3.img')
    new_hdr3 = os.path.join(pth, 'newfile3.hdr')
    copyfile(orig_img, new_img1)
    assert os.path.islink(new_img1)
    assert os.path.islink(new_hdr1)
    copyfile(new_img1, new_img2, copy=True)
    assert not os.path.islink(new_img2)
    assert not os.path.islink(new_hdr2)
    assert not os.path.samefile(orig_img, new_img2)
    assert not os.path.samefile(orig_hdr, new_hdr2)
    copyfile(new_img1, new_img3, copy=True, use_hardlink=True)
    assert not os.path.islink(new_img3)
    assert not os.path.islink(new_hdr3)
    assert os.path.samefile(orig_img, new_img3)
    assert os.path.samefile(orig_hdr, new_hdr3)


def test_recopy(_temp_analyze_files):
    # Re-copying with the same parameters on an unchanged file should be
    # idempotent
    #
    # Test for copying from regular files and symlinks
    orig_img, orig_hdr = _temp_analyze_files
    pth, fname = os.path.split(orig_img)
    img_link = os.path.join(pth, 'imglink.img')
    hdr_link = os.path.join(pth, 'imglink.hdr')
    new_img = os.path.join(pth, 'newfile.img')
    new_hdr = os.path.join(pth, 'newfile.hdr')
    copyfile(orig_img, img_link)
    for copy in (True, False):
        for use_hardlink in (True, False):
            for hashmethod in ('timestamp', 'content'):
                kwargs = {'copy': copy, 'use_hardlink': use_hardlink,
                          'hashmethod': hashmethod}
                # Copying does not preserve the original file's timestamp, so
                # we may delete and re-copy, if the test is slower than a clock
                # tick
                if copy and not use_hardlink and hashmethod == 'timestamp':
                    continue

                copyfile(orig_img, new_img, **kwargs)
                img_stat = _ignore_atime(os.stat(new_img))
                hdr_stat = _ignore_atime(os.stat(new_hdr))
                copyfile(orig_img, new_img, **kwargs)
                err_msg = "Regular - OS: {}; Copy: {}; Hardlink: {}".format(
                    os.name, copy, use_hardlink)
                assert img_stat == _ignore_atime(os.stat(new_img)), err_msg
                assert hdr_stat == _ignore_atime(os.stat(new_hdr)), err_msg
                os.unlink(new_img)
                os.unlink(new_hdr)

                copyfile(img_link, new_img, **kwargs)
                img_stat = _ignore_atime(os.stat(new_img))
                hdr_stat = _ignore_atime(os.stat(new_hdr))
                copyfile(img_link, new_img, **kwargs)
                err_msg = "Symlink - OS: {}; Copy: {}; Hardlink: {}".format(
                    os.name, copy, use_hardlink)
                assert img_stat == _ignore_atime(os.stat(new_img)), err_msg
                assert hdr_stat == _ignore_atime(os.stat(new_hdr)), err_msg
                os.unlink(new_img)
                os.unlink(new_hdr)


def test_copyfallback(_temp_analyze_files):
    if os.name is not 'posix':
        return
    orig_img, orig_hdr = _temp_analyze_files
    pth, imgname = os.path.split(orig_img)
    pth, hdrname = os.path.split(orig_hdr)
    try:
        fatfs = TempFATFS()
    except (IOError, OSError):
        warnings.warn('Fuse mount failed. copyfile fallback tests skipped.')
    else:
        with fatfs as fatdir:
            tgt_img = os.path.join(fatdir, imgname)
            tgt_hdr = os.path.join(fatdir, hdrname)
            for copy in (True, False):
                for use_hardlink in (True, False):
                    copyfile(orig_img, tgt_img, copy=copy,
                             use_hardlink=use_hardlink)
                    assert os.path.exists(tgt_img)
                    assert os.path.exists(tgt_hdr)
                    assert not os.path.islink(tgt_img)
                    assert not os.path.islink(tgt_hdr)
                    assert not os.path.samefile(orig_img, tgt_img)
                    assert not os.path.samefile(orig_hdr, tgt_hdr)
                    os.unlink(tgt_img)
                    os.unlink(tgt_hdr)


def test_get_related_files(_temp_analyze_files):
    orig_img, orig_hdr = _temp_analyze_files

    related_files = get_related_files(orig_img)
    assert orig_img in related_files
    assert orig_hdr in related_files

    related_files = get_related_files(orig_hdr)
    assert orig_img in related_files
    assert orig_hdr in related_files


def test_get_related_files_noninclusive(_temp_analyze_files):
    orig_img, orig_hdr = _temp_analyze_files

    related_files = get_related_files(orig_img, include_this_file=False)
    assert orig_img not in related_files
    assert orig_hdr in related_files

    related_files = get_related_files(orig_hdr, include_this_file=False)
    assert orig_img in related_files
    assert orig_hdr not in related_files

@pytest.mark.parametrize("filename, expected", [
        ('foo.nii',      ['foo.nii']),
        (['foo.nii'],    ['foo.nii']),
        (('foo', 'bar'), ['foo', 'bar']),
        (12.34,          None)
        ])
def test_filename_to_list(filename, expected):
    x = filename_to_list(filename)
    assert x == expected

@pytest.mark.parametrize("list, expected", [
        (['foo.nii'],    'foo.nii'),
        (['foo', 'bar'], ['foo', 'bar']),
        ])
def test_list_to_filename(list, expected):
    x = list_to_filename(list)
    assert x == expected


def test_check_depends(tmpdir):
    def touch(fname):
        with open(fname, 'a'):
            os.utime(fname, None)


    dependencies = [tmpdir.join(str(i)).strpath for i in range(3)]
    targets = [tmpdir.join(str(i)).strpath for i in range(3, 6)]

    # Targets newer than dependencies
    for dep in dependencies:
        touch(dep)
    time.sleep(1)
    for tgt in targets:
        touch(tgt)
    assert check_depends(targets, dependencies)

    # Targets older than newest dependency
    time.sleep(1)
    touch(dependencies[0])
    assert not check_depends(targets, dependencies)

    # Missing dependency
    os.unlink(dependencies[0])
    try:
        check_depends(targets, dependencies)
    except OSError as e:
        pass
    else:
        assert False, "Should raise OSError on missing dependency"


def test_json(tmpdir):
    # Simple roundtrip test of json files, just a sanity check.
    adict = dict(a='one', c='three', b='two')
    name = tmpdir.join('test.json').strpath
    save_json(name, adict)  # save_json closes the file
    new_dict = load_json(name)
    os.unlink(name)
    assert sorted(adict.items()) == sorted(new_dict.items())


@pytest.mark.parametrize("file, length, expected_files", [
        ('/path/test.img',  3, ['/path/test.hdr', '/path/test.img', '/path/test.mat']),
        ('/path/test.hdr',  3, ['/path/test.hdr', '/path/test.img', '/path/test.mat']),
        ('/path/test.BRIK', 2, ['/path/test.BRIK', '/path/test.HEAD']),
        ('/path/test.HEAD', 2, ['/path/test.BRIK', '/path/test.HEAD']),
        ('/path/foo.nii',   2, ['/path/foo.nii', '/path/foo.mat'])
        ])
def test_related_files(file, length, expected_files):
    related_files = get_related_files(file)

    assert len(related_files) == length

    for ef in expected_files:
        assert ef in related_files


def test_cifs_check():
    assert isinstance(_cifs_table, list)
    assert isinstance(on_cifs('/'), bool)
    fake_table = [('/scratch/tmp', 'ext4'), ('/scratch', 'cifs')]
    cifs_targets = [('/scratch/tmp/x/y', False),
                    ('/scratch/tmp/x', False),
                    ('/scratch/x/y', True),
                    ('/scratch/x', True),
                    ('/x/y', False),
                    ('/x', False),
                    ('/', False)]

    orig_table = _cifs_table[:]
    _cifs_table[:] = []

    for target, _ in cifs_targets:
        assert on_cifs(target) is False

    _cifs_table.extend(fake_table)
    for target, expected in cifs_targets:
        assert on_cifs(target) is expected

    _cifs_table[:] = []
    _cifs_table.extend(orig_table)
