from nipype.testing import (assert_equal, assert_false, assert_true, 
                            assert_raises, skipif)
import nipype.interfaces.spm as spm
import nipype.interfaces.matlab as mlab
from nipype.interfaces.base import Bunch
from tempfile import mkdtemp
import os
from shutil import rmtree
import numpy as np

try:
    matlab_cmd = os.environ['MATLABCMD']
except:
    matlab_cmd = 'matlab -nodesktop -nosplash'

mlab.MatlabCommandLine.matlab_cmd = matlab_cmd

def cannot_find_spm():
    # See if we can find spm or not.
    try:
        spm.spm_info.spm_path
        return False
    except IOError:
        return True

def test_scan_for_fnames():
    a = ['a.nii','b.nii']
    names = spm.scans_for_fnames(a,keep4d=True)
    yield assert_equal, names[0][0], 'a.nii'
    yield assert_equal, names[0][1], 'b.nii'

save_time = True
if not save_time:
    def test_spm_path():
        spm_path = spm.spm_info.spm_path
        if spm_path is not None:
            yield assert_equal, type(spm_path), type('')
            yield assert_true, 'spm' in spm_path

def test_use_mfile():
    mlab = spm.SpmMatlabCommandLine()
    yield assert_true, mlab.mfile
    mlab._use_mfile(False)
    yield assert_false, mlab.mfile

@skipif(cannot_find_spm, "SPM not found")
def test_run():
    mlab = spm.SpmMatlabCommandLine()
    yield assert_raises, NotImplementedError, mlab.run

    class mlabsub(spm.SpmMatlabCommandLine):
        def _compile_command(self):
            return self._gen_matlab_command('',mfile=self.mfile) 
    mlab = mlabsub()
    mlab._use_mfile(False)
    yield assert_raises, NotImplementedError, mlab.run
    class mlabsub2(mlabsub):
        def aggregate_outputs(self):
            pass
    mlab = mlabsub2()
    mlab._use_mfile(False)
    results = mlab.run()
    yield assert_equal, results.runtime.returncode, 0
    
def test_reformat_dict_for_savemat():
    mlab = spm.SpmMatlabCommandLine()
    out = mlab._reformat_dict_for_savemat({'a':{'b':{'c':[]}}})
    yield assert_equal, out, [{'a': [{'b': [{'c': []}]}]}]
    
def test_generate_job():
    mlab = spm.SpmMatlabCommandLine()
    out = mlab._generate_job()
    yield assert_equal, out, ''
    # struct array
    contents = {'contents':[1,2,3,4]}
    out = mlab._generate_job(contents=contents)
    yield assert_equal, out, '.contents(1) = 1;\n.contents(2) = 2;\n.contents(3) = 3;\n.contents(4) = 4;\n'
    # cell array of strings
    a = ['a.nii','b.nii']
    names = spm.scans_for_fnames(a,keep4d=True)
    contents = {'files':names}
    out = mlab._generate_job(prefix='test',contents=contents)
    yield assert_equal, out, "test.files = {...\n'a.nii';...\n'b.nii';...\n};\n"
    # string assignment
    contents = 'foo'
    out = mlab._generate_job(prefix='test',contents=contents)
    yield assert_equal, out, "test = 'foo';\n"
    # cell array of vectors
    contents = {'onsets':np.array([[[np.array([1,2,3,4])]]])}
    out = mlab._generate_job(prefix='test',contents=contents)
    yield assert_equal, out, 'test.onsets = {...\n[1;2;3;4;];...\n};\n'
    
def test_make_matlab_command():
    mlab = spm.SpmMatlabCommandLine()
    outdir = mkdtemp()
    mlab.inputs.cwd = outdir
    contents = {'contents':[1,2,3,4]}
    cmdline,script = mlab._make_matlab_command([contents])
    yield assert_equal, cmdline, \
        ' '.join((matlab_cmd, '-r "pyscript_jobname;exit" '))
    yield assert_true, 'jobs{1}.jobtype{1}.jobname{1}.contents(3) = 3;' in script
    yield assert_true, os.path.exists(os.path.join(mlab.inputs.cwd,'pyscript_jobname.m'))
    if os.path.exists(outdir):
        rmtree(outdir)

def test_spm_realign_inputs():
    realign = spm.Realign()
    definputs = Bunch(infile=None,
                      write=True,
                      quality=None,
                      fwhm=None,
                      separation=None,
                      register_to_mean=None,
                      weight_img=None,
                      interp=None,
                      wrap=None,
                      write_which=None,
                      write_interp=None,
                      write_wrap=None,
                      write_mask=None,
                      flags=None)
    yield assert_equal, str(realign.inputs), str(definputs)

def test_spm_get_input_info():
    realign = spm.Realign()
    yield assert_equal, str(realign.get_input_info()[0]), str(Bunch(key='infile',copy=True))
    
def test_spm_parse_inputs():
    realign = spm.Realign(write=False)
    updatedopts = realign._parseinputs()
    yield assert_equal, updatedopts, [{'estimate': {'roptions': {}, 'eoptions': {}, 'data': []}}]
    yield assert_false, realign.inputs.write

