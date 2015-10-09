# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
from tempfile import mkdtemp
from shutil import rmtree

from nipype.testing import (assert_equal, assert_true, assert_false,
                            assert_raises, skipif)
import nipype.interfaces.matlab as mlab

matlab_cmd = mlab.get_matlab_command()
no_matlab = matlab_cmd is None
if not no_matlab:
    mlab.MatlabCommand.set_default_matlab_cmd(matlab_cmd)


@skipif(no_matlab)
def test_cmdline():
    basedir = mkdtemp()
    mi = mlab.MatlabCommand(script='whos',
                            script_file='testscript', mfile=False)

    yield assert_equal, mi.cmdline, \
        matlab_cmd + (' -nodesktop -nosplash -singleCompThread -r "fprintf(1,'
                      '\'Executing code at %s:\\n\',datestr(now));ver,try,'
                      'whos,catch ME,fprintf(2,\'MATLAB code threw an '
                      'exception:\\n\');fprintf(2,\'%s\\n\',ME.message);if '
                      'length(ME.stack) ~= 0, fprintf(2,\'File:%s\\nName:%s\\n'
                      'Line:%d\\n\',ME.stack.file,ME.stack.name,'
                      'ME.stack.line);, end;end;;exit"')

    yield assert_equal, mi.inputs.script, 'whos'
    yield assert_equal, mi.inputs.script_file, 'testscript'
    path_exists = os.path.exists(os.path.join(basedir, 'testscript.m'))
    yield assert_false, path_exists
    rmtree(basedir)


@skipif(no_matlab)
def test_mlab_inputspec():
    spec = mlab.MatlabInputSpec()
    for k in ['paths', 'script', 'nosplash', 'mfile', 'logfile', 'script_file',
              'nodesktop']:
        yield assert_true, k in spec.copyable_trait_names()
    yield assert_true, spec.nodesktop
    yield assert_true, spec.nosplash
    yield assert_true, spec.mfile
    yield assert_equal, spec.script_file, 'pyscript.m'


@skipif(no_matlab)
def test_mlab_init():
    yield assert_equal, mlab.MatlabCommand._cmd, 'matlab'
    yield assert_equal, mlab.MatlabCommand.input_spec, mlab.MatlabInputSpec

    yield assert_equal, mlab.MatlabCommand().cmd, matlab_cmd
    mc = mlab.MatlabCommand(matlab_cmd='foo_m')
    yield assert_equal, mc.cmd, 'foo_m'


@skipif(no_matlab)
def test_run_interface():
    mc = mlab.MatlabCommand(matlab_cmd='foo_m')
    yield assert_raises, ValueError, mc.run  # script is mandatory
    mc.inputs.script = 'a=1;'
    yield assert_raises, IOError, mc.run  # foo_m is not an executable
    cwd = os.getcwd()
    basedir = mkdtemp()
    os.chdir(basedir)
    # bypasses ubuntu dash issue
    mc = mlab.MatlabCommand(script='foo;', paths=[basedir], mfile=True)
    yield assert_raises, RuntimeError, mc.run
    # bypasses ubuntu dash issue
    res = mlab.MatlabCommand(script='a=1;', paths=[basedir], mfile=True).run()
    yield assert_equal, res.runtime.returncode, 0
    os.chdir(cwd)
    rmtree(basedir)


@skipif(no_matlab)
def test_set_matlabcmd():
    mi = mlab.MatlabCommand()
    mi.set_default_matlab_cmd('foo')
    yield assert_equal, mi._default_matlab_cmd, 'foo'
    mi.set_default_matlab_cmd(matlab_cmd)
