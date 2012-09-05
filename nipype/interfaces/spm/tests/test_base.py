# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
from tempfile import mkdtemp
from shutil import rmtree

import nibabel as nb
import numpy as np

from nipype.testing import (assert_equal, assert_false, assert_true, skipif)
import nipype.interfaces.spm.base as spm
from nipype.interfaces.spm import no_spm
import nipype.interfaces.matlab as mlab
from nipype.interfaces.spm.base import SPMCommandInputSpec
from nipype.interfaces.base import traits

try:
    matlab_cmd = os.environ['MATLABCMD']
except:
    matlab_cmd = 'matlab'

mlab.MatlabCommand.set_default_matlab_cmd(matlab_cmd)


def create_files_in_directory():
    outdir = mkdtemp()
    cwd = os.getcwd()
    os.chdir(outdir)
    filelist = ['a.nii', 'b.nii']
    for f in filelist:
        hdr = nb.Nifti1Header()
        shape = (3, 3, 3, 4)
        hdr.set_data_shape(shape)
        img = np.random.random(shape)
        nb.save(nb.Nifti1Image(img, np.eye(4), hdr),
                 os.path.join(outdir, f))
    return filelist, outdir, cwd


def clean_directory(outdir, old_wd):
    if os.path.exists(outdir):
        rmtree(outdir)
    os.chdir(old_wd)


def test_scan_for_fnames():
    filelist, outdir, cwd = create_files_in_directory()
    names = spm.scans_for_fnames(filelist, keep4d=True)
    yield assert_equal, names[0], filelist[0]
    yield assert_equal, names[1], filelist[1]
    clean_directory(outdir, cwd)


save_time = False
if not save_time:
    @skipif(no_spm)
    def test_spm_path():
        spm_path = spm.Info.version()['path']
        if spm_path is not None:
            yield assert_equal, type(spm_path), type('')
            yield assert_true, 'spm' in spm_path


def test_use_mfile():
    class TestClass(spm.SPMCommand):
        input_spec = spm.SPMCommandInputSpec
    dc = TestClass()  # dc = derived_class
    yield assert_true, dc.inputs.mfile


@skipif(no_spm, "SPM not found")
def test_cmd_update():
    class TestClass(spm.SPMCommand):
        input_spec = spm.SPMCommandInputSpec
    dc = TestClass()  # dc = derived_class
    dc.inputs.matlab_cmd = 'foo'
    yield assert_equal, dc.mlab._cmd, 'foo'


def test_cmd_update2():
    class TestClass(spm.SPMCommand):
        _jobtype = 'jobtype'
        _jobname = 'jobname'
        input_spec = spm.SPMCommandInputSpec
    dc = TestClass()  # dc = derived_class
    yield assert_equal, dc.jobtype, 'jobtype'
    yield assert_equal, dc.jobname, 'jobname'


def test_reformat_dict_for_savemat():
    class TestClass(spm.SPMCommand):
        input_spec = spm.SPMCommandInputSpec
    dc = TestClass()  # dc = derived_class
    out = dc._reformat_dict_for_savemat({'a': {'b': {'c': []}}})
    yield assert_equal, out, [{'a': [{'b': [{'c': []}]}]}]


def test_generate_job():
    class TestClass(spm.SPMCommand):
        input_spec = spm.SPMCommandInputSpec
    dc = TestClass()  # dc = derived_class
    out = dc._generate_job()
    yield assert_equal, out, ''
    # struct array
    contents = {'contents': [1, 2, 3, 4]}
    out = dc._generate_job(contents=contents)
    yield assert_equal, out, ('.contents(1) = 1;\n.contents(2) = 2;'
                              '\n.contents(3) = 3;\n.contents(4) = 4;\n')
    # cell array of strings
    filelist, outdir, cwd = create_files_in_directory()
    names = spm.scans_for_fnames(filelist, keep4d=True)
    contents = {'files': names}
    out = dc._generate_job(prefix='test', contents=contents)
    yield assert_equal, out, "test.files = {...\n'a.nii';...\n'b.nii';...\n};\n"
    clean_directory(outdir, cwd)
    # string assignment
    contents = 'foo'
    out = dc._generate_job(prefix='test', contents=contents)
    yield assert_equal, out, "test = 'foo';\n"
    # cell array of vectors
    contents = {'onsets': np.array((1,), dtype=object)}
    contents['onsets'][0] = [1, 2, 3, 4]
    out = dc._generate_job(prefix='test', contents=contents)
    yield assert_equal, out, 'test.onsets = {...\n[1, 2, 3, 4];...\n};\n'

def test_bool():
    class TestClassInputSpec(SPMCommandInputSpec):
        test_in = include_intercept = traits.Bool(field='testfield')
        
    class TestClass(spm.SPMCommand):
        input_spec = TestClassInputSpec
        _jobtype = 'jobtype'
        _jobname = 'jobname'
    dc = TestClass()  # dc = derived_class
    dc.inputs.test_in = True
    out = dc._make_matlab_command(dc._parse_inputs())
    yield assert_equal, out.find('jobs{1}.jobtype{1}.jobname{1}.testfield = 1;') > 0, 1
    
def test_make_matlab_command():
    class TestClass(spm.SPMCommand):
        _jobtype = 'jobtype'
        _jobname = 'jobname'
        input_spec = spm.SPMCommandInputSpec
    dc = TestClass()  # dc = derived_class
    filelist, outdir, cwd = create_files_in_directory()
    contents = {'contents': [1, 2, 3, 4]}
    script = dc._make_matlab_command([contents])
    yield assert_true, 'jobs{1}.jobtype{1}.jobname{1}.contents(3) = 3;' in script
    clean_directory(outdir, cwd)
