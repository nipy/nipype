# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import glob
import shutil
from tempfile import mkstemp, mkdtemp

from nipype.testing import assert_equal, assert_true, assert_false
import nipype.interfaces.io as nio
from nipype.interfaces.base import Undefined

def test_datagrabber():
    dg = nio.DataGrabber()
    yield assert_equal, dg.inputs.template, Undefined
    yield assert_equal, dg.inputs.base_directory, Undefined
    yield assert_equal, dg.inputs.template_args,{'outfiles': []}

def test_datasink():
    ds = nio.DataSink()
    yield assert_true, ds.inputs.parameterization
    yield assert_equal, ds.inputs.base_directory, Undefined
    yield assert_equal, ds.inputs.strip_dir, Undefined
    yield assert_equal, ds.inputs._outputs, {}
    ds = nio.DataSink(base_directory = 'foo')
    yield assert_equal, ds.inputs.base_directory, 'foo'
    ds = nio.DataSink(infields=['test'])
    yield assert_true, 'test' in ds.inputs.copyable_trait_names()

def test_datasink_substitutions():
    indir = mkdtemp(prefix='-Tmp-nipype_ds_subs_in')
    outdir = mkdtemp(prefix='-Tmp-nipype_ds_subs_out')
    files = []
    for n in ['ababab.n', 'xabababyz.n']:
        f = os.path.join(indir, n)
        files.append(f)
        open(f, 'w')
    ds = nio.DataSink(
        parametrization=False,
        base_directory = outdir,
        substitutions = [('ababab', 'ABABAB')],
        # end archoring ($) is used to assure operation on the filename
        # instead of possible temporary directories names matches
        # Patterns should be more comprehendable in the real-world usage
        # cases since paths would be quite more sensible
        regexp_substitutions = [(r'xABABAB(\w*)\.n$', r'a-\1-b.n'),
                                ('(.*%s)[-a]([^%s]*)$' % ((os.path.sep,)*2),
                                 r'\1!\2')] )
    setattr(ds.inputs, '@outdir', files)
    ds.run()
    yield assert_equal, \
          sorted([os.path.basename(x) for
                  x in glob.glob(os.path.join(outdir, '*'))]), \
          ['!-yz-b.n', 'ABABAB.n'] # so we got re used 2nd and both patterns
    shutil.rmtree(indir)
    shutil.rmtree(outdir)

def _temp_analyze_files():
    """Generate temporary analyze file pair."""
    fd, orig_img = mkstemp(suffix = '.img', dir=mkdtemp())
    orig_hdr = orig_img[:-4] + '.hdr'
    fp = file(orig_hdr, 'w+')
    fp.close()
    return orig_img, orig_hdr

def test_datasink_copydir():
    orig_img, orig_hdr = _temp_analyze_files()
    outdir = mkdtemp()
    pth, fname = os.path.split(orig_img)
    ds = nio.DataSink(base_directory = outdir, parameterization=False)
    setattr(ds.inputs,'@outdir',pth)
    ds.run()
    file_exists = lambda: os.path.exists(os.path.join(outdir, pth.split(os.path.sep)[-1], fname))
    yield assert_true, file_exists()
    shutil.rmtree(pth)

    orig_img, orig_hdr = _temp_analyze_files()
    pth, fname = os.path.split(orig_img)
    ds.inputs.remove_dest_dir = True
    setattr(ds.inputs,'outdir',pth)
    ds.run()
    yield assert_false, file_exists()
    shutil.rmtree(outdir)
    shutil.rmtree(pth)

def test_freesurfersource():
    fss = nio.FreeSurferSource()
    yield assert_equal, fss.inputs.hemi, 'both'
    yield assert_equal, fss.inputs.subject_id, Undefined
    yield assert_equal, fss.inputs.subjects_dir, Undefined
