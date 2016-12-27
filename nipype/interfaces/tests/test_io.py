# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import print_function, unicode_literals
from builtins import str, zip, range, open
from future import standard_library
import os
import simplejson
import glob
import shutil
import os.path as op
from subprocess import Popen
import hashlib

import pytest
import nipype
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
standard_library.install_aliases()
from subprocess import check_call, CalledProcessError
try:
    ret_code = check_call(['which', 'fakes3'], stdout=open(os.devnull, 'wb'))
    fakes3 = (ret_code == 0)
except CalledProcessError:
    fakes3 = False

from tempfile import mkstemp, mkdtemp

def test_datagrabber():
    dg = nio.DataGrabber()
    assert dg.inputs.template == Undefined
    assert dg.inputs.base_directory == Undefined
    assert dg.inputs.template_args == {'outfiles': []}


@pytest.mark.skipif(noboto, reason="boto library is not available")
def test_s3datagrabber():
    dg = nio.S3DataGrabber()
    assert dg.inputs.template == Undefined
    assert dg.inputs.local_directory == Undefined
    assert dg.inputs.template_args == {'outfiles': []}


templates1 = {"model": "interfaces/{package}/model.py",
             "preprocess": "interfaces/{package}/pre*.py"}
templates2 = {"converter": "interfaces/dcm{to!s}nii.py"}

@pytest.mark.parametrize("SF_args, inputs_att, expected", [
        ({"templates":templates1}, {"package":"fsl"},
         {"infields":["package"], "outfields":["model", "preprocess"], "run_output":{"model":op.join(op.dirname(nipype.__file__),"interfaces/fsl/model.py"), "preprocess":op.join(op.dirname(nipype.__file__),"interfaces/fsl/preprocess.py")}, "node_output":["model", "preprocess"]}),

        ({"templates":templates1, "force_lists":True}, {"package":"spm"},
         {"infields":["package"], "outfields":["model", "preprocess"], "run_output":{"model":[op.join(op.dirname(nipype.__file__),"interfaces/spm/model.py")], "preprocess":[op.join(op.dirname(nipype.__file__),"interfaces/spm/preprocess.py")]}, "node_output":["model", "preprocess"]}),

        ({"templates":templates1}, {"package":"fsl", "force_lists":["model"]},
         {"infields":["package"], "outfields":["model", "preprocess"], "run_output":{"model":[op.join(op.dirname(nipype.__file__),"interfaces/fsl/model.py")], "preprocess":op.join(op.dirname(nipype.__file__),"interfaces/fsl/preprocess.py")}, "node_output":["model", "preprocess"]}),

        ({"templates":templates2}, {"to":2},
         {"infields":["to"], "outfields":["converter"], "run_output":{"converter":op.join(op.dirname(nipype.__file__), "interfaces/dcm2nii.py")}, "node_output":["converter"]}),
        ])
def test_selectfiles(SF_args, inputs_att, expected):
    base_dir = op.dirname(nipype.__file__)
    dg = nio.SelectFiles(base_directory=base_dir, **SF_args)
    for key, val in inputs_att.items():
        setattr(dg.inputs, key, val)

    assert dg._infields == expected["infields"]
    assert sorted(dg._outfields) == expected["outfields"]
    assert sorted(dg._outputs().get()) == expected["node_output"]

    res = dg.run()
    for key, val in expected["run_output"].items():
        assert getattr(res.outputs, key) == val


def test_selectfiles_valueerror():
    """Test ValueError when force_lists has field that isn't in template."""
    base_dir = op.dirname(nipype.__file__)
    templates = {"model": "interfaces/{package}/model.py",
                 "preprocess": "interfaces/{package}/pre*.py"}
    force_lists = ["model", "preprocess", "registration"]
    sf = nio.SelectFiles(templates, base_directory=base_dir,
                         force_lists=force_lists)
    with pytest.raises(ValueError):
        sf.run()


@pytest.mark.skipif(noboto, reason="boto library is not available")
def test_s3datagrabber_communication(tmpdir):
    dg = nio.S3DataGrabber(
        infields=['subj_id', 'run_num'], outfields=['func', 'struct'])
    dg.inputs.anon = True
    dg.inputs.bucket = 'openfmri'
    dg.inputs.bucket_path = 'ds001/'
    dg.inputs.local_directory = str(tmpdir)
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
    assert os.path.join(dg.inputs.local_directory, '/sub001/BOLD/task001_run001/bold.nii.gz') in func_outfiles[0]
    assert os.path.exists(func_outfiles[0])
    assert os.path.join(dg.inputs.local_directory, '/sub001/anatomy/highres001_brain.nii.gz') in struct_outfiles[0]
    assert os.path.exists(struct_outfiles[0])
    assert os.path.join(dg.inputs.local_directory, '/sub002/BOLD/task001_run003/bold.nii.gz') in func_outfiles[1]
    assert os.path.exists(func_outfiles[1])
    assert os.path.join(dg.inputs.local_directory, '/sub002/anatomy/highres001_brain.nii.gz') in struct_outfiles[1]
    assert os.path.exists(struct_outfiles[1])


def test_datagrabber_order(tmpdir):
    for file_name in ['sub002_L1_R1.q', 'sub002_L1_R2.q', 'sub002_L2_R1.q',
                      'sub002_L2_R2.qd', 'sub002_L3_R10.q', 'sub002_L3_R2.q']:
        tmpdir.join(file_name).open('a').close()

    dg = nio.DataGrabber(infields=['sid'])
    dg.inputs.base_directory = str(tmpdir)
    dg.inputs.template = '%s_L%d_R*.q*'
    dg.inputs.template_args = {'outfiles': [['sid', 1], ['sid', 2],
                                            ['sid', 3]]}
    dg.inputs.sid = 'sub002'
    dg.inputs.sort_filelist = True
    res = dg.run()
    outfiles = res.outputs.outfiles

    assert 'sub002_L1_R1'  in outfiles[0][0]
    assert 'sub002_L1_R2'  in outfiles[0][1]
    assert 'sub002_L2_R1'  in outfiles[1][0]
    assert 'sub002_L2_R2'  in outfiles[1][1]
    assert 'sub002_L3_R2'  in outfiles[2][0]
    assert 'sub002_L3_R10' in outfiles[2][1]


def test_datasink():
    ds = nio.DataSink()
    assert ds.inputs.parameterization
    assert ds.inputs.base_directory == Undefined
    assert ds.inputs.strip_dir == Undefined
    assert ds.inputs._outputs == {}

    ds = nio.DataSink(base_directory='foo')
    assert ds.inputs.base_directory == 'foo'

    ds = nio.DataSink(infields=['test'])
    assert 'test' in ds.inputs.copyable_trait_names()


# Make dummy input file
@pytest.fixture(scope="module")
def dummy_input(request, tmpdir_factory):
    '''
    Function to create a dummy file
    '''
    # Init variables
    input_path = tmpdir_factory.mktemp('input_data').join('datasink_test_s3.txt')

    # Create input file
    input_path.write_binary(b'ABCD1234')

    # Return path
    return str(input_path)


# Test datasink writes to s3 properly
@pytest.mark.skipif(noboto3 or not fakes3, reason="boto3 or fakes3 library is not available")
def test_datasink_to_s3(dummy_input, tmpdir):
    '''
    This function tests to see if the S3 functionality of a DataSink
    works properly
    '''
    # Init variables
    ds = nio.DataSink()
    bucket_name = 'test'
    container = 'outputs'
    attr_folder = 'text_file'
    output_dir = 's3://' + bucket_name
    # Local temporary filepaths for testing
    fakes3_dir = str(tmpdir)
    input_path = dummy_input

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

    # Make sure md5sums match
    assert src_md5 == dst_md5


# Test AWS creds read from env vars
@pytest.mark.skipif(noboto3 or not fakes3, reason="boto3 or fakes3 library is not available")
def test_aws_keys_from_env():
    '''
    Function to ensure the DataSink can successfully read in AWS
    credentials from the environment variables
    '''

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
    assert aws_access_key_id == access_key_test
    assert aws_secret_access_key == secret_key_test


# Test the local copy attribute
def test_datasink_localcopy(dummy_input, tmpdir):
    '''
    Function to validate DataSink will make local copy via local_copy
    attribute
    '''

    # Init variables
    local_dir = str(tmpdir)
    container = 'outputs'
    attr_folder = 'text_file'

    # Make dummy input file and datasink
    input_path = dummy_input

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

    # Perform test
    assert src_md5 == dst_md5


def test_datasink_substitutions(tmpdir):
    indir = tmpdir.mkdir('-Tmp-nipype_ds_subs_in')
    outdir = tmpdir.mkdir('-Tmp-nipype_ds_subs_out')
    files = []
    for n in ['ababab.n', 'xabababyz.n']:
        f = str(indir.join(n))
        files.append(f)
        open(f, 'w')
    ds = nio.DataSink(
        parametrization=False,
        base_directory=str(outdir),
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
    assert sorted([os.path.basename(x) for
              x in glob.glob(os.path.join(str(outdir), '*'))]) \
              == ['!-yz-b.n', 'ABABAB.n']  # so we got re used 2nd and both patterns


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
    assert file_exists()
    shutil.rmtree(pth)

    orig_img, orig_hdr = _temp_analyze_files()
    pth, fname = os.path.split(orig_img)
    ds.inputs.remove_dest_dir = True
    setattr(ds.inputs, 'outdir', pth)
    ds.run()
    assert not file_exists()
    shutil.rmtree(outdir)
    shutil.rmtree(pth)


def test_datafinder_depth(tmpdir):
    outdir = str(tmpdir)
    os.makedirs(os.path.join(outdir, '0', '1', '2', '3'))

    df = nio.DataFinder()
    df.inputs.root_paths = os.path.join(outdir, '0')
    for min_depth in range(4):
        for max_depth in range(min_depth, 4):
            df.inputs.min_depth = min_depth
            df.inputs.max_depth = max_depth
            result = df.run()
            expected = ['{}'.format(x) for x in range(min_depth, max_depth + 1)]
            for path, exp_fname in zip(result.outputs.out_paths, expected):
                _, fname = os.path.split(path)
                assert fname == exp_fname


def test_datafinder_unpack(tmpdir):
    outdir = str(tmpdir)
    single_res = os.path.join(outdir, "findme.txt")
    open(single_res, 'a').close()
    open(os.path.join(outdir, "dontfindme"), 'a').close()

    df = nio.DataFinder()
    df.inputs.root_paths = outdir
    df.inputs.match_regex = '.+/(?P<basename>.+)\.txt'
    df.inputs.unpack_single = True
    result = df.run()
    print(result.outputs.out_paths)
    assert result.outputs.out_paths == single_res


def test_freesurfersource():
    fss = nio.FreeSurferSource()
    assert fss.inputs.hemi == 'both'
    assert fss.inputs.subject_id == Undefined
    assert fss.inputs.subjects_dir == Undefined


def test_jsonsink_input(tmpdir):

    ds = nio.JSONFileSink()
    assert ds.inputs._outputs == {}

    ds = nio.JSONFileSink(in_dict={'foo': 'var'})
    assert ds.inputs.in_dict == {'foo': 'var'}

    ds = nio.JSONFileSink(infields=['test'])
    assert 'test' in ds.inputs.copyable_trait_names()


@pytest.mark.parametrize("inputs_attributes", [
        {'new_entry' : 'someValue'},
        {'new_entry' : 'someValue', 'test' : 'testInfields'}
])
def test_jsonsink(tmpdir, inputs_attributes):
    os.chdir(str(tmpdir))
    js = nio.JSONFileSink(infields=['test'], in_dict={'foo': 'var'})
    setattr(js.inputs, 'contrasts.alt', 'someNestedValue')
    expected_data = {"contrasts": {"alt": "someNestedValue"}, "foo": "var"}
    for key, val in inputs_attributes.items():
        setattr(js.inputs, key, val)
        expected_data[key] = val

    res = js.run()
    with open(res.outputs.out_file, 'r') as f:
        data = simplejson.load(f)

    assert data == expected_data



