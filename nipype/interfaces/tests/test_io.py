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

# Check for boto
noboto = False
try:
    import boto
    from boto.s3.connection import S3Connection, OrdinaryCallingFormat
except ImportError:
    noboto = True

# Check for boto3
noboto3 = False
try:
    import boto3
    from botocore.utils import fix_s3_host
except ImportError:
    noboto3 = True

# Check for fakes3
import subprocess
try:
    ret_code = subprocess.check_call(['which', 'fakes3'], stdout=open(os.devnull, 'wb'))
    if ret_code == 0:
        fakes3 = True
    else:
        fakes3 = False
except subprocess.CalledProcessError:
    fakes3 = False

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


# Make dummy input file
def _make_dummy_input():
    '''
    Function to create a dummy file
    '''

    # Import packages
    import tempfile


    # Init variables
    input_dir = tempfile.mkdtemp()
    input_path = os.path.join(input_dir, 'datasink_test_s3.txt')

    # Create input file
    with open(input_path, 'wb') as f:
        f.write(b'ABCD1234')

    # Return path
    return input_path


# Test datasink writes to s3 properly
@skipif(noboto3 or not fakes3)
def test_datasink_to_s3():
    '''
    This function tests to see if the S3 functionality of a DataSink
    works properly
    '''

    # Import packages
    import hashlib
    import tempfile

    # Init variables
    ds = nio.DataSink()
    bucket_name = 'test'
    container = 'outputs'
    attr_folder = 'text_file'
    output_dir = 's3://' + bucket_name
    # Local temporary filepaths for testing
    fakes3_dir = tempfile.mkdtemp()
    input_path = _make_dummy_input()

    # Start up fake-S3 server
    proc = Popen(['fakes3', '-r', fakes3_dir, '-p', '4567'], stdout=open(os.devnull, 'wb'))

    # Init boto3 s3 resource to talk with fakes3
    resource = boto3.resource(aws_access_key_id='mykey',
                              aws_secret_access_key='mysecret',
                              service_name='s3',
                              endpoint_url='http://localhost:4567',
                              use_ssl=False)
    resource.meta.client.meta.events.unregister('before-sign.s3', fix_s3_host)

    # Create bucket
    bucket = resource.create_bucket(Bucket=bucket_name)

    # Prep datasink
    ds.inputs.base_directory = output_dir
    ds.inputs.container = container
    ds.inputs.bucket = bucket
    setattr(ds.inputs, attr_folder, input_path)

    # Run datasink
    ds.run()

    # Get MD5sums and compare
    key = '/'.join([container, attr_folder, os.path.basename(input_path)])
    obj = bucket.Object(key=key)
    dst_md5 = obj.e_tag.replace('"', '')
    src_md5 = hashlib.md5(open(input_path, 'rb').read()).hexdigest()

    # Kill fakes3
    proc.kill()

    # Delete fakes3 folder and input file
    shutil.rmtree(fakes3_dir)
    shutil.rmtree(os.path.dirname(input_path))

    # Make sure md5sums match
    yield assert_equal, src_md5, dst_md5


# Test AWS creds read from env vars
@skipif(noboto3 or not fakes3)
def test_aws_keys_from_env():
    '''
    Function to ensure the DataSink can successfully read in AWS
    credentials from the environment variables
    '''

    # Import packages
    import os
    import nipype.interfaces.io as nio

    # Init variables
    ds = nio.DataSink()
    aws_access_key_id = 'ABCDACCESS'
    aws_secret_access_key = 'DEFGSECRET'

    # Set env vars
    os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key_id
    os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_access_key

    # Call function to return creds
    access_key_test, secret_key_test = ds._return_aws_keys()

    # Assert match
    yield assert_equal, aws_access_key_id, access_key_test
    yield assert_equal, aws_secret_access_key, secret_key_test


# Test the local copy attribute
def test_datasink_localcopy():
    '''
    Function to validate DataSink will make local copy via local_copy
    attribute
    '''

    # Import packages
    import hashlib
    import tempfile

    # Init variables
    local_dir = tempfile.mkdtemp()
    container = 'outputs'
    attr_folder = 'text_file'

    # Make dummy input file and datasink
    input_path = _make_dummy_input()
    ds = nio.DataSink()

    # Set up datasink
    ds.inputs.container = container
    ds.inputs.local_copy = local_dir
    setattr(ds.inputs, attr_folder, input_path)

    # Expected local copy path
    local_copy = os.path.join(local_dir, container, attr_folder,
                              os.path.basename(input_path))

    # Run the datasink
    ds.run()

    # Check md5sums of both
    src_md5 = hashlib.md5(open(input_path, 'rb').read()).hexdigest()
    dst_md5 = hashlib.md5(open(local_copy, 'rb').read()).hexdigest()

    # Delete temp diretories
    shutil.rmtree(os.path.dirname(input_path))
    shutil.rmtree(local_dir)

    # Perform test
    yield assert_equal, src_md5, dst_md5


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
