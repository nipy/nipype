# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import unicode_literals
from builtins import open

import os
from tempfile import mkstemp, mkdtemp
import warnings

from ...testing import (assert_equal, assert_true, assert_false,
                        assert_in, assert_not_in, TempFATFS)
from ...utils.filemanip import (save_json, load_json,
                                fname_presuffix, fnames_presuffix,
                                hash_rename, check_forhash,
                                copyfile, copyfiles,
                                filename_to_list, list_to_filename,
                                split_filename, get_related_files)

import numpy as np


def _ignore_atime(stat):
    return stat[:7] + stat[8:]


def test_split_filename():
    res = split_filename('foo.nii')
    yield assert_equal, res, ('', 'foo', '.nii')
    res = split_filename('foo.nii.gz')
    yield assert_equal, res, ('', 'foo', '.nii.gz')
    res = split_filename('/usr/local/foo.nii.gz')
    yield assert_equal, res, ('/usr/local', 'foo', '.nii.gz')
    res = split_filename('../usr/local/foo.nii')
    yield assert_equal, res, ('../usr/local', 'foo', '.nii')
    res = split_filename('/usr/local/foo.a.b.c.d')
    yield assert_equal, res, ('/usr/local', 'foo.a.b.c', '.d')
    res = split_filename('/usr/local/')
    yield assert_equal, res, ('/usr/local', '', '')


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
    yield assert_equal, new_name, 'foobar_0xabc123.nii'
    new_name = hash_rename('foobar.nii.gz', 'abc123')
    yield assert_equal, new_name, 'foobar_0xabc123.nii.gz'


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


def _temp_analyze_files():
    """Generate temporary analyze file pair."""
    fd, orig_img = mkstemp(suffix='.img')
    orig_hdr = orig_img[:-4] + '.hdr'
    fp = open(orig_hdr, 'w+')
    fp.close()
    return orig_img, orig_hdr


def test_copyfile():
    orig_img, orig_hdr = _temp_analyze_files()
    pth, fname = os.path.split(orig_img)
    new_img = os.path.join(pth, 'newfile.img')
    new_hdr = os.path.join(pth, 'newfile.hdr')
    copyfile(orig_img, new_img)
    yield assert_true, os.path.exists(new_img)
    yield assert_true, os.path.exists(new_hdr)
    os.unlink(new_img)
    os.unlink(new_hdr)
    # final cleanup
    os.unlink(orig_img)
    os.unlink(orig_hdr)


def test_copyfile_true():
    orig_img, orig_hdr = _temp_analyze_files()
    pth, fname = os.path.split(orig_img)
    new_img = os.path.join(pth, 'newfile.img')
    new_hdr = os.path.join(pth, 'newfile.hdr')
    # Test with copy=True
    copyfile(orig_img, new_img, copy=True)
    yield assert_true, os.path.exists(new_img)
    yield assert_true, os.path.exists(new_hdr)
    os.unlink(new_img)
    os.unlink(new_hdr)
    # final cleanup
    os.unlink(orig_img)
    os.unlink(orig_hdr)


def test_copyfiles():
    orig_img1, orig_hdr1 = _temp_analyze_files()
    orig_img2, orig_hdr2 = _temp_analyze_files()
    pth, fname = os.path.split(orig_img1)
    new_img1 = os.path.join(pth, 'newfile.img')
    new_hdr1 = os.path.join(pth, 'newfile.hdr')
    pth, fname = os.path.split(orig_img2)
    new_img2 = os.path.join(pth, 'secondfile.img')
    new_hdr2 = os.path.join(pth, 'secondfile.hdr')
    newfiles = copyfiles([orig_img1, orig_img2], [new_img1, new_img2])
    yield assert_true, os.path.exists(new_img1)
    yield assert_true, os.path.exists(new_hdr1)
    yield assert_true, os.path.exists(new_img2)
    yield assert_true, os.path.exists(new_hdr2)
    # cleanup
    os.unlink(orig_img1)
    os.unlink(orig_hdr1)
    os.unlink(orig_img2)
    os.unlink(orig_hdr2)
    os.unlink(new_img1)
    os.unlink(new_hdr1)
    os.unlink(new_img2)
    os.unlink(new_hdr2)


def test_linkchain():
    if os.name is not 'posix':
        return
    orig_img, orig_hdr = _temp_analyze_files()
    pth, fname = os.path.split(orig_img)
    new_img1 = os.path.join(pth, 'newfile1.img')
    new_hdr1 = os.path.join(pth, 'newfile1.hdr')
    new_img2 = os.path.join(pth, 'newfile2.img')
    new_hdr2 = os.path.join(pth, 'newfile2.hdr')
    new_img3 = os.path.join(pth, 'newfile3.img')
    new_hdr3 = os.path.join(pth, 'newfile3.hdr')
    copyfile(orig_img, new_img1)
    yield assert_true, os.path.islink(new_img1)
    yield assert_true, os.path.islink(new_hdr1)
    copyfile(new_img1, new_img2, copy=True)
    yield assert_false, os.path.islink(new_img2)
    yield assert_false, os.path.islink(new_hdr2)
    yield assert_false, os.path.samefile(orig_img, new_img2)
    yield assert_false, os.path.samefile(orig_hdr, new_hdr2)
    copyfile(new_img1, new_img3, copy=True, use_hardlink=True)
    yield assert_false, os.path.islink(new_img3)
    yield assert_false, os.path.islink(new_hdr3)
    yield assert_true, os.path.samefile(orig_img, new_img3)
    yield assert_true, os.path.samefile(orig_hdr, new_hdr3)

    os.unlink(new_img1)
    os.unlink(new_hdr1)
    os.unlink(new_img2)
    os.unlink(new_hdr2)
    os.unlink(new_img3)
    os.unlink(new_hdr3)
    # final cleanup
    os.unlink(orig_img)
    os.unlink(orig_hdr)

def test_recopy():
    # Re-copying with the same parameters on an unchanged file should be
    # idempotent
    #
    # Test for copying from regular files and symlinks
    orig_img, orig_hdr = _temp_analyze_files()
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
                yield (assert_equal, img_stat, _ignore_atime(os.stat(new_img)),
                       err_msg)
                yield (assert_equal, hdr_stat, _ignore_atime(os.stat(new_hdr)),
                       err_msg)
                os.unlink(new_img)
                os.unlink(new_hdr)

                copyfile(img_link, new_img, **kwargs)
                img_stat = _ignore_atime(os.stat(new_img))
                hdr_stat = _ignore_atime(os.stat(new_hdr))
                copyfile(img_link, new_img, **kwargs)
                err_msg = "Symlink - OS: {}; Copy: {}; Hardlink: {}".format(
                    os.name, copy, use_hardlink)
                yield (assert_equal, img_stat, _ignore_atime(os.stat(new_img)),
                       err_msg)
                yield (assert_equal, hdr_stat, _ignore_atime(os.stat(new_hdr)),
                       err_msg)
                os.unlink(new_img)
                os.unlink(new_hdr)

    os.unlink(img_link)
    os.unlink(hdr_link)
    os.unlink(orig_img)
    os.unlink(orig_hdr)

def test_copyfallback():
    if os.name is not 'posix':
        return
    orig_img, orig_hdr = _temp_analyze_files()
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
                    yield assert_true, os.path.exists(tgt_img)
                    yield assert_true, os.path.exists(tgt_hdr)
                    yield assert_false, os.path.islink(tgt_img)
                    yield assert_false, os.path.islink(tgt_hdr)
                    yield assert_false, os.path.samefile(orig_img, tgt_img)
                    yield assert_false, os.path.samefile(orig_hdr, tgt_hdr)
                    os.unlink(tgt_img)
                    os.unlink(tgt_hdr)
    finally:
        os.unlink(orig_img)
        os.unlink(orig_hdr)


def test_get_related_files():
    orig_img, orig_hdr = _temp_analyze_files()

    related_files = get_related_files(orig_img)
    yield assert_in, orig_img, related_files
    yield assert_in, orig_hdr, related_files

    related_files = get_related_files(orig_hdr)
    yield assert_in, orig_img, related_files
    yield assert_in, orig_hdr, related_files


def test_get_related_files_noninclusive():
    orig_img, orig_hdr = _temp_analyze_files()

    related_files = get_related_files(orig_img, include_this_file=False)
    yield assert_not_in, orig_img, related_files
    yield assert_in, orig_hdr, related_files

    related_files = get_related_files(orig_hdr, include_this_file=False)
    yield assert_in, orig_img, related_files
    yield assert_not_in, orig_hdr, related_files


def test_filename_to_list():
    x = filename_to_list('foo.nii')
    yield assert_equal, x, ['foo.nii']
    x = filename_to_list(['foo.nii'])
    yield assert_equal, x, ['foo.nii']
    x = filename_to_list(('foo', 'bar'))
    yield assert_equal, x, ['foo', 'bar']
    x = filename_to_list(12.34)
    yield assert_equal, x, None


def test_list_to_filename():
    x = list_to_filename(['foo.nii'])
    yield assert_equal, x, 'foo.nii'
    x = list_to_filename(['foo', 'bar'])
    yield assert_equal, x, ['foo', 'bar']


def test_json():
    # Simple roundtrip test of json files, just a sanity check.
    adict = dict(a='one', c='three', b='two')
    fd, name = mkstemp(suffix='.json')
    save_json(name, adict)  # save_json closes the file
    new_dict = load_json(name)
    os.unlink(name)
    yield assert_equal, sorted(adict.items()), sorted(new_dict.items())


def test_related_files():
    file1 = '/path/test.img'
    file2 = '/path/test.hdr'
    file3 = '/path/test.BRIK'
    file4 = '/path/test.HEAD'
    file5 = '/path/foo.nii'

    spm_files1 = get_related_files(file1)
    spm_files2 = get_related_files(file2)
    afni_files1 = get_related_files(file3)
    afni_files2 = get_related_files(file4)
    yield assert_equal, len(spm_files1), 3
    yield assert_equal, len(spm_files2), 3
    yield assert_equal, len(afni_files1), 2
    yield assert_equal, len(afni_files2), 2
    yield assert_equal, len(get_related_files(file5)), 1

    yield assert_true, '/path/test.hdr' in spm_files1
    yield assert_true, '/path/test.img' in spm_files1
    yield assert_true, '/path/test.mat' in spm_files1
    yield assert_true, '/path/test.hdr' in spm_files2
    yield assert_true, '/path/test.img' in spm_files2
    yield assert_true, '/path/test.mat' in spm_files2
    yield assert_true, '/path/test.BRIK' in afni_files1
    yield assert_true, '/path/test.HEAD' in afni_files1
    yield assert_true, '/path/test.BRIK' in afni_files2
    yield assert_true, '/path/test.HEAD' in afni_files2
