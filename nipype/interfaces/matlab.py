# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
""" General matlab interface code """
import os

from nipype.interfaces.base import CommandLineInputSpec, InputMultiPath
from nipype.utils.misc import isdefined
from nipype.interfaces.base import (CommandLine, traits, File, Directory)
from nipype.utils.config import config

class MatlabInputSpec(CommandLineInputSpec):
    """ Basic expected inputs to Matlab interface """
    
    script  = traits.Str(argstr='-r \"%s;exit\"', desc='m-code to run',
                         mandatory=True, position=-1)
    nodesktop = traits.Bool(True, argstr='-nodesktop',
                            usedefault=True,
                            desc='Switch off desktop mode on unix platforms')
    nosplash = traits.Bool(True, argstr='-nosplash', usedefault=True,
                           descr='Switch of splash screen')
    logfile = File(argstr='-logfile %s',
                          desc='Save matlab output to log')
    single_comp_thread = traits.Bool(argstr="-singleCompThread",
                                   desc="force single threaded operation")
    # non-commandline options
    mfile   = traits.Bool(False, desc='Run m-code using m-file',
                          usedefault=True)
    script_file = File('pyscript.m', usedefault=True,
                              desc='Name of file to write m-code to')
    paths   = InputMultiPath(Directory(), desc='Paths to add to matlabpath')

class MatlabCommand(CommandLine):
    """Interface that runs matlab code

    >>> import nipype.interfaces.matlab as matlab
    >>> mlab = matlab.MatlabCommand()
    >>> mlab.inputs.script = "which('who')"
    >>> out = mlab.run() # doctest: +SKIP
    """

    _cmd = 'matlab'
    _default_matlab_cmd = None
    _default_mfile = None
    _default_paths = None
    input_spec = MatlabInputSpec
    
    def __init__(self, matlab_cmd = None, **inputs):
        """initializes interface to matlab
        (default 'matlab -nodesktop -nosplash')
        """
        super(MatlabCommand,self).__init__(**inputs)
        if matlab_cmd and isdefined(matlab_cmd):
            self._cmd = matlab_cmd
        elif self._default_matlab_cmd:
            self._cmd = self._default_matlab_cmd
            
        if self._default_mfile and not isdefined(self.inputs.mfile):
            self.inputs.mfile = self._default_mfile
            
        if self._default_paths and not isdefined(self.inputs.paths):
            self.inputs.paths = self._default_paths
            
        if not isdefined(self.inputs.single_comp_thread):
            if config.getboolean('execution','single_thread_matlab'):
                self.inputs.single_comp_thread = True
            
    @classmethod
    def set_default_matlab_cmd(cls, matlab_cmd):
        """Set the default MATLAB command line for MATLAB classes.

        This method is used to set values for all MATLAB
        subclasses.  However, setting this will not update the output
        type for any existing instances.  For these, assign the
        <instance>.inputs.matlab_cmd.
        """
        cls._default_matlab_cmd = matlab_cmd
        
    @classmethod
    def set_default_mfile(cls, mfile):
        """Set the default MATLAB script file format for MATLAB classes.

        This method is used to set values for all MATLAB
        subclasses.  However, setting this will not update the output
        type for any existing instances.  For these, assign the
        <instance>.inputs.mfile.
        """
        cls._default_mfile = mfile
        
    @classmethod
    def set_default_paths(cls, paths):
        """Set the default MATLAB paths for MATLAB classes.

        This method is used to set values for all MATLAB
        subclasses.  However, setting this will not update the output
        type for any existing instances.  For these, assign the
        <instance>.inputs.paths.
        """
        cls._default_paths = paths

    def _run_interface(self,runtime):
        runtime = super(MatlabCommand, self)._run_interface(runtime)
        if 'command not found' in runtime.stderr:
            msg = 'Cannot find matlab!\n' + \
                '\tTried command:  ' + runtime.cmdline + \
                '\n\tShell reported: ' + runtime.stderr
            raise IOError(msg)
        if  'MatlabScriptException' in runtime.stderr:
            runtime.returncode = 1
        return runtime

    def _format_arg(self, name, trait_spec, value):
        if name in ['script']:
            return self._gen_matlab_command(trait_spec.argstr, value)
        return super(MatlabCommand, self)._format_arg(name, trait_spec, value)

    def _gen_matlab_command(self, argstr, script_lines):
        cwd = os.getcwd()
        mfile = self.inputs.mfile
        paths = []
        if isdefined(self.inputs.paths):
            paths = self.inputs.paths
        # prescript
        prescript  = ''
        if mfile:
            prescript += "fprintf(1,'Executing %s at %s:\\n',mfilename,datestr(now));\n"
        else:
            prescript += "fprintf(1,'Executing code at %s:\\n',datestr(now));\n" 
        prescript += "ver,\n"
        prescript += "try,\n"
        for path in paths:
            prescript += "addpath('%s');\n" % path
        # postscript
        postscript  = ''
        postscript += "\n,catch ME,\n"
        postscript += "ME,\n"
        postscript += "ME.stack,\n"
        postscript += "fprintf('%s\\n',ME.message);\n"
        postscript += "fprintf(2,'<MatlabScriptException>');\n"
        postscript += "fprintf(2,'%s\\n',ME.message);\n"
        postscript += "fprintf(2,'File:%s\\nName:%s\\nLine:%d\\n',ME.stack.file,ME.stack.name,ME.stack.line);\n"
        postscript += "fprintf(2,'</MatlabScriptException>');\n"
        postscript += "end;\n"
        script_lines = prescript+script_lines+postscript
        if mfile:
            mfile = file(os.path.join(cwd,self.inputs.script_file), 'wt')
            mfile.write(script_lines)
            mfile.close()
            script = "addpath('%s');%s" % (cwd, self.inputs.script_file.split('.')[0])
        else:
            script = ''.join(script_lines.split('\n'))
        return argstr % script
