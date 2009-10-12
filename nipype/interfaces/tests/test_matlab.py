from nipype.testing import assert_raises, assert_equal, assert_true, assert_false
import nipype.interfaces.matlab as mlab
from nipype.interfaces.base import CommandLine, Bunch
from tempfile import mkdtemp

import os

try:
    matlab_cmd = os.environ['MATLABCMD']
except:
    matlab_cmd = 'matlab'

res = CommandLine('which %s'%matlab_cmd).run()
matlab_path = res.runtime.stdout.strip()

if matlab_path != '':
    matlab_command = '%s -nodesktop -nosplash'%matlab_path.split(os.path.sep)[-1]
    mlab.matlab_cmd = matlab_command
    basedir = os.environ.get('TMPDIR', mkdtemp())
        
    def test_init():
        mi = mlab.MatlabCommandLine()
        yield assert_equal, mi._cmdline, None
        yield assert_equal, mi._cmdline_inputs, None
        yield assert_equal, mi.matlab_cmd, matlab_command
        mi = mlab.MatlabCommandLine(matlab_cmd='foo')
        yield assert_equal, mi.matlab_cmd, 'foo'
        yield assert_equal, mlab.matlab_cmd, matlab_command

    def test_cmdline():
        mi = mlab.MatlabCommandLine(script_lines='whos',script_name='testscript',cwd=basedir)
        yield assert_equal, mi.cmdline, 'matlab -nodesktop -nosplash -r "testscript;exit" '
        yield assert_equal, mi._cmdline, 'matlab -nodesktop -nosplash -r "testscript;exit" '
        inputs = str(Bunch(cwd=basedir, mfile=True, script_lines='whos', script_name='testscript', ))
        yield assert_equal, inputs, str(mi._cmdline_inputs)
        path_exists = os.path.exists(os.path.join(basedir,'testscript.m'))
        yield assert_true, path_exists

    def test_set_matlabcmd():
        mi = mlab.MatlabCommandLine()
        mi.set_matlabcmd('foo')
        yield assert_equal, mi.matlab_cmd, 'foo'
        yield assert_equal, mlab.matlab_cmd, matlab_command


