# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import glob
import shutil
import os.path as op
from tempfile import mkstemp, mkdtemp

from nose.tools import assert_raises
import nipype
from nipype.testing import assert_equal, assert_true, assert_false
import nipype.interfaces.io as nio
from nipype.interfaces.base import Undefined


def test_datagrabber():
    dg = nio.DataGrabber()
    yield assert_equal, dg.inputs.template, Undefined
    yield assert_equal, dg.inputs.base_directory, Undefined
    yield assert_equal, dg.inputs.template_args, {'outfiles': []}


def test_selectfiles():
    base_dir = op.dirname(nipype.__file__)
    templates = {"model": "interfaces/{package}/model.py",
                 "preprocess": "interfaces/{package}/pre*.py"}
    dg = nio.SelectFiles(templates, base_directory=base_dir)
    yield assert_equal, dg._infields, ["package"]
    yield assert_equal, sorted(dg._outfields), ["model", "preprocess"]
    dg.inputs.package = "fsl"
    res = dg.run()
    wanted = op.join(op.dirname(nipype.__file__), "interfaces/fsl/model.py")
    yield assert_equal, res.outputs.model, wanted

    dg = nio.SelectFiles(templates,
                         base_directory=base_dir,
                         force_lists=True)
    outfields = sorted(dg._outputs().get())
    yield assert_equal, outfields, ["model", "preprocess"]

    dg.inputs.package = "spm"
    res = dg.run()
    wanted = op.join(op.dirname(nipype.__file__),
                     "interfaces/spm/preprocess.py")
    yield assert_equal, res.outputs.preprocess, [wanted]

    dg.inputs.package = "fsl"
    dg.inputs.force_lists = ["model"]
    res = dg.run()
    preproc = op.join(op.dirname(nipype.__file__),
                      "interfaces/fsl/preprocess.py")
    model = [op.join(op.dirname(nipype.__file__),
                     "interfaces/fsl/model.py")]
    yield assert_equal, res.outputs.preprocess, preproc
    yield assert_equal, res.outputs.model, model

    templates = {"converter": "interfaces/dcm{to!s}nii.py"}
    dg = nio.SelectFiles(templates, base_directory=base_dir)
    dg.inputs.to = 2
    res = dg.run()
    wanted = op.join(base_dir, "interfaces/dcm2nii.py")
    yield assert_equal, res.outputs.converter, wanted


def test_selectfiles_valueerror():
    """Test ValueError when force_lists has field that isn't in template."""
    base_dir = op.dirname(nipype.__file__)
    templates = {"model": "interfaces/{package}/model.py",
                 "preprocess": "interfaces/{package}/pre*.py"}
    force_lists = ["model", "preprocess", "registration"]
    sf = nio.SelectFiles(templates, base_directory=base_dir,
                         force_lists=force_lists)
    yield assert_raises, ValueError, sf.run


def test_datagrabber_order():
    tempdir = mkdtemp()
    file1 = mkstemp(prefix='sub002_L1_R1.q', dir=tempdir)
    file2 = mkstemp(prefix='sub002_L1_R2.q', dir=tempdir)
    file3 = mkstemp(prefix='sub002_L2_R1.q', dir=tempdir)
    file4 = mkstemp(prefix='sub002_L2_R2.q', dir=tempdir)
    file5 = mkstemp(prefix='sub002_L3_R10.q', dir=tempdir)
    file6 = mkstemp(prefix='sub002_L3_R2.q', dir=tempdir)
    dg = nio.DataGrabber(infields=['sid'])
    dg.inputs.base_directory = tempdir
    dg.inputs.template = '%s_L%d_R*.q*'
    dg.inputs.template_args = {'outfiles': [['sid', 1], ['sid', 2],
                                            ['sid', 3]]}
    dg.inputs.sid = 'sub002'
    dg.inputs.sort_filelist = True
    res = dg.run()
    outfiles = res.outputs.outfiles
    yield assert_true, 'sub002_L1_R1' in outfiles[0][0]
    yield assert_true, 'sub002_L1_R2' in outfiles[0][1]
    yield assert_true, 'sub002_L2_R1' in outfiles[1][0]
    yield assert_true, 'sub002_L2_R2' in outfiles[1][1]
    yield assert_true, 'sub002_L3_R2' in outfiles[2][0]
    yield assert_true, 'sub002_L3_R10' in outfiles[2][1]
    shutil.rmtree(tempdir)

def test_datasink():
    ds = nio.DataSink()
    yield assert_true, ds.inputs.parameterization
    yield assert_equal, ds.inputs.base_directory, Undefined
    yield assert_equal, ds.inputs.strip_dir, Undefined
    yield assert_equal, ds.inputs._outputs, {}
    ds = nio.DataSink(base_directory='foo')
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
        base_directory=outdir,
        substitutions=[('ababab', 'ABABAB')],
        # end archoring ($) is used to assure operation on the filename
        # instead of possible temporary directories names matches
        # Patterns should be more comprehendable in the real-world usage
        # cases since paths would be quite more sensible
        regexp_substitutions=[(r'xABABAB(\w*)\.n$', r'a-\1-b.n'),
                              ('(.*%s)[-a]([^%s]*)$' % ((os.path.sep,) * 2),
                               r'\1!\2')])
    setattr(ds.inputs, '@outdir', files)
    ds.run()
    yield assert_equal, \
          sorted([os.path.basename(x) for
                  x in glob.glob(os.path.join(outdir, '*'))]), \
          ['!-yz-b.n', 'ABABAB.n']  # so we got re used 2nd and both patterns
    shutil.rmtree(indir)
    shutil.rmtree(outdir)


def _temp_analyze_files():
    """Generate temporary analyze file pair."""
    fd, orig_img = mkstemp(suffix='.img', dir=mkdtemp())
    orig_hdr = orig_img[:-4] + '.hdr'
    fp = file(orig_hdr, 'w+')
    fp.close()
    return orig_img, orig_hdr


def test_datasink_copydir():
    orig_img, orig_hdr = _temp_analyze_files()
    outdir = mkdtemp()
    pth, fname = os.path.split(orig_img)
    ds = nio.DataSink(base_directory=outdir, parameterization=False)
    setattr(ds.inputs, '@outdir', pth)
    ds.run()
    sep = os.path.sep
    file_exists = lambda: os.path.exists(os.path.join(outdir,
                                                      pth.split(sep)[-1],
                                                      fname))
    yield assert_true, file_exists()
    shutil.rmtree(pth)

    orig_img, orig_hdr = _temp_analyze_files()
    pth, fname = os.path.split(orig_img)
    ds.inputs.remove_dest_dir = True
    setattr(ds.inputs, 'outdir', pth)
    ds.run()
    yield assert_false, file_exists()
    shutil.rmtree(outdir)
    shutil.rmtree(pth)


def test_freesurfersource():
    fss = nio.FreeSurferSource()
    yield assert_equal, fss.inputs.hemi, 'both'
    yield assert_equal, fss.inputs.subject_id, Undefined
    yield assert_equal, fss.inputs.subjects_dir, Undefined
