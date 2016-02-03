# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import print_function
from builtins import zip
from builtins import range
from builtins import open

import os
import glob
import shutil
import os.path as op
from tempfile import mkstemp, mkdtemp
from subprocess import Popen

from nose.tools import assert_raises
import nipype
from nipype.testing import assert_equal, assert_true, assert_false, skipif
import nipype.interfaces.io as nio
from nipype.interfaces.base import Undefined

noboto = False
try:
    import boto
    from boto.s3.connection import S3Connection, OrdinaryCallingFormat
except:
    noboto = True


def test_datagrabber():
    dg = nio.DataGrabber()
    yield assert_equal, dg.inputs.template, Undefined
    yield assert_equal, dg.inputs.base_directory, Undefined
    yield assert_equal, dg.inputs.template_args, {'outfiles': []}


@skipif(noboto)
def test_s3datagrabber():
    dg = nio.S3DataGrabber()
    yield assert_equal, dg.inputs.template, Undefined
    yield assert_equal, dg.inputs.local_directory, Undefined
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


@skipif(noboto)
def test_s3datagrabber_communication():
    dg = nio.S3DataGrabber(
        infields=['subj_id', 'run_num'], outfields=['func', 'struct'])
    dg.inputs.anon = True
    dg.inputs.bucket = 'openfmri'
    dg.inputs.bucket_path = 'ds001/'
    tempdir = mkdtemp()
    dg.inputs.local_directory = tempdir
    dg.inputs.sort_filelist = True
    dg.inputs.template = '*'
    dg.inputs.field_template = dict(func='%s/BOLD/task001_%s/bold.nii.gz',
                                    struct='%s/anatomy/highres001_brain.nii.gz')
    dg.inputs.subj_id = ['sub001', 'sub002']
    dg.inputs.run_num = ['run001', 'run003']
    dg.inputs.template_args = dict(
        func=[['subj_id', 'run_num']], struct=[['subj_id']])
    res = dg.run()
    func_outfiles = res.outputs.func
    struct_outfiles = res.outputs.struct

    # check for all files
    yield assert_true, os.path.join(dg.inputs.local_directory, '/sub001/BOLD/task001_run001/bold.nii.gz') in func_outfiles[0]
    yield assert_true, os.path.exists(func_outfiles[0])
    yield assert_true, os.path.join(dg.inputs.local_directory, '/sub001/anatomy/highres001_brain.nii.gz') in struct_outfiles[0]
    yield assert_true, os.path.exists(struct_outfiles[0])
    yield assert_true, os.path.join(dg.inputs.local_directory, '/sub002/BOLD/task001_run003/bold.nii.gz') in func_outfiles[1]
    yield assert_true, os.path.exists(func_outfiles[1])
    yield assert_true, os.path.join(dg.inputs.local_directory, '/sub002/anatomy/highres001_brain.nii.gz') in struct_outfiles[1]
    yield assert_true, os.path.exists(struct_outfiles[1])

    shutil.rmtree(tempdir)


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


@skipif(noboto)
def test_s3datasink():
    ds = nio.S3DataSink()
    yield assert_true, ds.inputs.parameterization
    yield assert_equal, ds.inputs.base_directory, Undefined
    yield assert_equal, ds.inputs.strip_dir, Undefined
    yield assert_equal, ds.inputs._outputs, {}
    ds = nio.S3DataSink(base_directory='foo')
    yield assert_equal, ds.inputs.base_directory, 'foo'
    ds = nio.S3DataSink(infields=['test'])
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


@skipif(noboto)
def test_s3datasink_substitutions():
    indir = mkdtemp(prefix='-Tmp-nipype_ds_subs_in')
    outdir = mkdtemp(prefix='-Tmp-nipype_ds_subs_out')
    files = []
    for n in ['ababab.n', 'xabababyz.n']:
        f = os.path.join(indir, n)
        files.append(f)
        open(f, 'w')

    # run fakes3 server and set up bucket
    fakes3dir = op.expanduser('~/fakes3')
    try:
        proc = Popen(
            ['fakes3', '-r', fakes3dir, '-p', '4567'], stdout=open(os.devnull, 'wb'))
    except OSError as ose:
        if 'No such file or directory' in str(ose):
            return  # fakes3 not installed. OK!
        raise ose

    conn = S3Connection(anon=True, is_secure=False, port=4567,
                        host='localhost',
                        calling_format=OrdinaryCallingFormat())
    conn.create_bucket('test')

    ds = nio.S3DataSink(
        testing=True,
        anon=True,
        bucket='test',
        bucket_path='output/',
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

    bkt = conn.get_bucket(ds.inputs.bucket)
    bkt_files = list(k for k in bkt.list())

    found = [False, False]
    failed_deletes = 0
    for k in bkt_files:
        if '!-yz-b.n' in k.key:
            found[0] = True
            try:
                bkt.delete_key(k)
            except:
                failed_deletes += 1
        elif 'ABABAB.n' in k.key:
            found[1] = True
            try:
                bkt.delete_key(k)
            except:
                failed_deletes += 1

    # ensure delete requests were successful
    yield assert_equal, failed_deletes, 0

    # ensure both keys are found in bucket
    yield assert_equal, found.count(True), 2

    proc.kill()
    shutil.rmtree(fakes3dir)
    shutil.rmtree(indir)
    shutil.rmtree(outdir)


def _temp_analyze_files():
    """Generate temporary analyze file pair."""
    fd, orig_img = mkstemp(suffix='.img', dir=mkdtemp())
    orig_hdr = orig_img[:-4] + '.hdr'
    fp = open(orig_hdr, 'w+')
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


def test_datafinder_copydir():
    outdir = mkdtemp()
    open(os.path.join(outdir, "findme.txt"), 'a').close()
    open(os.path.join(outdir, "dontfindme"), 'a').close()
    open(os.path.join(outdir, "dontfindmealsotxt"), 'a').close()
    open(os.path.join(outdir, "findmetoo.txt"), 'a').close()
    open(os.path.join(outdir, "ignoreme.txt"), 'a').close()
    open(os.path.join(outdir, "alsoignore.txt"), 'a').close()

    from nipype.interfaces.io import DataFinder
    df = DataFinder()
    df.inputs.root_paths = outdir
    df.inputs.match_regex = '.+/(?P<basename>.+)\.txt'
    df.inputs.ignore_regexes = ['ignore']
    result = df.run()
    expected = ["findme.txt", "findmetoo.txt"]
    for path, expected_fname in zip(result.outputs.out_paths, expected):
        _, fname = os.path.split(path)
        yield assert_equal, fname, expected_fname

    yield assert_equal, result.outputs.basename, ["findme", "findmetoo"]

    shutil.rmtree(outdir)


def test_datafinder_depth():
    outdir = mkdtemp()
    os.makedirs(os.path.join(outdir, '0', '1', '2', '3'))

    from nipype.interfaces.io import DataFinder
    df = DataFinder()
    df.inputs.root_paths = os.path.join(outdir, '0')
    for min_depth in range(4):
        for max_depth in range(min_depth, 4):
            df.inputs.min_depth = min_depth
            df.inputs.max_depth = max_depth
            result = df.run()
            expected = [str(x) for x in range(min_depth, max_depth + 1)]
            for path, exp_fname in zip(result.outputs.out_paths, expected):
                _, fname = os.path.split(path)
                yield assert_equal, fname, exp_fname

    shutil.rmtree(outdir)


def test_datafinder_unpack():
    outdir = mkdtemp()
    single_res = os.path.join(outdir, "findme.txt")
    open(single_res, 'a').close()
    open(os.path.join(outdir, "dontfindme"), 'a').close()

    from nipype.interfaces.io import DataFinder
    df = DataFinder()
    df.inputs.root_paths = outdir
    df.inputs.match_regex = '.+/(?P<basename>.+)\.txt'
    df.inputs.unpack_single = True
    result = df.run()
    print(result.outputs.out_paths)
    yield assert_equal, result.outputs.out_paths, single_res


def test_freesurfersource():
    fss = nio.FreeSurferSource()
    yield assert_equal, fss.inputs.hemi, 'both'
    yield assert_equal, fss.inputs.subject_id, Undefined
    yield assert_equal, fss.inputs.subjects_dir, Undefined


def test_jsonsink():
    import simplejson
    import os

    ds = nio.JSONFileSink()
    yield assert_equal, ds.inputs._outputs, {}
    ds = nio.JSONFileSink(in_dict={'foo': 'var'})
    yield assert_equal, ds.inputs.in_dict, {'foo': 'var'}
    ds = nio.JSONFileSink(infields=['test'])
    yield assert_true, 'test' in ds.inputs.copyable_trait_names()

    curdir = os.getcwd()
    outdir = mkdtemp()
    os.chdir(outdir)
    js = nio.JSONFileSink(infields=['test'], in_dict={'foo': 'var'})
    js.inputs.new_entry = 'someValue'
    setattr(js.inputs, 'contrasts.alt', 'someNestedValue')
    res = js.run()

    with open(res.outputs.out_file, 'r') as f:
        data = simplejson.load(f)
    yield assert_true, data == {"contrasts": {"alt": "someNestedValue"}, "foo": "var", "new_entry": "someValue"}

    js = nio.JSONFileSink(infields=['test'], in_dict={'foo': 'var'})
    js.inputs.new_entry = 'someValue'
    js.inputs.test = 'testInfields'
    setattr(js.inputs, 'contrasts.alt', 'someNestedValue')
    res = js.run()

    with open(res.outputs.out_file, 'r') as f:
        data = simplejson.load(f)
    yield assert_true, data == {"test": "testInfields", "contrasts": {"alt": "someNestedValue"}, "foo": "var", "new_entry": "someValue"}

    os.chdir(curdir)
    shutil.rmtree(outdir)
