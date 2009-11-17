import os
from tempfile import mkdtemp
from shutil import rmtree

from nipype.testing import assert_equal, assert_true
import nipype.interfaces.matlab as mlab
from nipype.interfaces.base import CommandLine, Bunch

try:
    matlab_cmd = os.environ['MATLABCMD']
except:
    matlab_cmd = 'matlab'

res = CommandLine('which %s' % matlab_cmd).run()
matlab_path = res.runtime.stdout.strip()

matlab_command = ''
no_matlab = True
if matlab_path != '':
    matlab_command = '%s -nodesktop -nosplash' % \
        matlab_path.split(os.path.sep)[-1]
    no_matlab = False
    
# If a test requires matlab, prefix it with the skipif decorator like
# below.  Must import skipif from nipype.testing
#
#@skipif(no_matlab)
# def test_func():
#     pass

def test_init():
    mi = mlab.MatlabCommandLine()
    yield assert_equal, mi._cmdline, None
    yield assert_equal, mi._cmdline_inputs, None
    mi = mlab.MatlabCommandLine(matlab_cmd='foo')
    yield assert_equal, mi.matlab_cmd, 'foo'

def test_cmdline():
    basedir = mkdtemp()

    mi = mlab.MatlabCommandLine(script_lines='whos',
                                script_name='testscript',
                                cwd=basedir)
    yield assert_equal, mi.cmdline, \
        'matlab -nodesktop -nosplash -r "testscript;exit" '
    yield assert_equal, mi._cmdline, \
        'matlab -nodesktop -nosplash -r "testscript;exit" '
    inputs = str(Bunch(cwd=basedir, mfile=True, script_lines='whos', 
                       script_name='testscript', ))
    yield assert_equal, inputs, str(mi._cmdline_inputs)
    path_exists = os.path.exists(os.path.join(basedir,'testscript.m'))
    yield assert_true, path_exists
    rmtree(basedir)

def test_set_matlabcmd():
    mi = mlab.MatlabCommandLine()
    mi.set_matlabcmd('foo')
    yield assert_equal, mi.matlab_cmd, 'foo'


