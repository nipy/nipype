""" General matlab interface code """

# Stdlib imports
from copy import deepcopy
import os
import re
import tempfile

import numpy as np

from nipype.interfaces.base import CommandLine, InterfaceResult, Bunch
from nipype.interfaces.base import (NEW_CommandLine, InterfaceResult, traits,
                                    TraitedSpec, Undefined)

class MatlabCommandLine(CommandLine):
    """Object that sets up Matlab specific tools and interfaces

    >>> import nipype.interfaces.matlab as matlab
    >>> matlab.MatlabCommandLine().matlab_cmd = "matlab.2009a -nodesktop -nosplash"
    >>> mcmd = matlab.MatlabCommandLine()
    >>> mcmd.inputs.script_lines = "which('who')"
    >>> out = mcmd.run() # doctest: +SKIP
    """
    matlab_cmd = 'matlab -nodesktop -nosplash'
    def __init__(self, matlab_cmd=None,**inputs):
        """initializes interface to matlab
        (default 'matlab -nodesktop -nosplash'
        """
        super(MatlabCommandLine,self).__init__(**inputs)
        self._cmdline = None
        self._cmdline_inputs = None
        if matlab_cmd is not None:
            self.matlab_cmd = matlab_cmd

    @property
    def cmdline(self):
        # This is currently a very inefficient hash! We can become more
        # efficient once we decide on our logic
        if self._cmdline is None or self._cmdline_inputs != self.inputs:
            self._compile_command()
            self._cmdline_inputs = deepcopy(self.inputs)

        return self._cmdline


    def set_matlabcmd(self, cmd):
        """reset the base matlab command
        """
        self.matlab_cmd = cmd
        
    def inputs_help(self):
        """
            Parameters
            ----------
            (all default to None and are unset)

            script_lines : string
                matlab_script or function name or matlab code to run
            script_name : string
                named of matlab script to generate if mfile is True
                default [pyscript]
            mfile : boolean
                True if an m-file containing the script is generated.
                default [True]
            cwd : string
                working directory for command.  default [os.getcwd()]
        """
        print self.inputs_help.__doc__
        
    def _populate_inputs(self):
        self.inputs = Bunch(script_lines='',
                            script_name='pyscript',
                            mfile=True,
                            cwd=None)

    def run(self,**kwargs):
        
        results = self._runner()
        if 'command not found' in results.runtime.stderr:
            msg = 'Cannot find matlab!\n' + \
                '\tTried command:  ' + results.runtime.cmdline + \
                '\n\tShell reported: ' + results.runtime.stderr
            raise IOError(msg)
        if  'MatlabScriptException' in results.runtime.stderr:
            results.runtime.returncode = 1
        return results

    def _compile_command(self):
        '''Generate necessary Matlab files and cmdline

        Note that this could be called before accessing .cmdline, and we wont
        regenerate anything (unless the inputs have changed)
        '''
        return self._gen_matlab_command(script_lines=self.inputs.script_lines,
                                             script_name=self.inputs.script_name,
                                             mfile = self.inputs.mfile,
                                             cwd = self.inputs.cwd)
    
    def _gen_matlab_command(self,script_lines='',script_name='pyscript',
                                 mfile = True,cwd = None):
        if cwd is None:
            cwd = os.getcwd()
        # generate the script
        prescript  = ''
        if mfile:
            prescript += "diary(sprintf('%s.log',mfilename));\n"
            prescript += "fprintf(1,'Executing %s at %s:\\n',mfilename,datestr(now));\n"
        else:
            prescript += "fprintf(1,'Executing code at %s:\\n',datestr(now));\n" 
        prescript += "ver,\n"
        prescript += "try,\n"
        postscript  = ''
        postscript += "\n,catch ME,\n"
        if mfile:
            postscript += "diary off;\n"
            postscript += "diary(sprintf('%s_error.log',mfilename));\n"
        postscript += "ME,\n"
        postscript += "ME.stack,\n"
        postscript += "fprintf('%s\\n',ME.message);\n"
        postscript += "fprintf(2,'<MatlabScriptException>');\n"
        postscript += "fprintf(2,'%s\\n',ME.message);\n"
        postscript += "fprintf(2,'File:%s\\nName:%s\\nLine:%d\\n',ME.stack.file,ME.stack.name,ME.stack.line);\n"
        postscript += "fprintf(2,'</MatlabScriptException>');\n"
        if mfile:
            postscript += "diary off,\n"
        postscript += "end;\n"
        script_lines = prescript+script_lines+postscript
        if mfile:
            mfile = file(os.path.join(cwd,script_name + '.m'), 'wt')
            mfile.write(script_lines)
            mfile.close()
        else:
            script_name = ''.join(script_lines.split('\n'))
        self._cmdline = '%s -r \"%s;exit\" ' % (self.matlab_cmd, script_name)
        return self._cmdline
    

class MatlabInputSpec(TraitedSpec):
    script  = traits.Str(argstr='-r \"%s;exit\"', desc='m-code to run',
                         mandatory=True, position=-1)
    nodesktop = traits.Bool(True, argstr='-nodesktop', usedefault=True,
                            desc='Switch off desktop mode on unix platforms')
    nosplash = traits.Bool(True, argstr='-nosplash', usedefault=True,
                           descr='Switch of splash screen')
    logfile = traits.File(argstr='-logfile %s',
                          desc='Save matlab output to log')
    # non-commandline options
    mfile   = traits.Bool(False, desc='Run m-code using m-file',
                          usedefault=True)
    script_file = traits.File('pyscript.m', usedefault=True,
                              desc='Name of file to write m-code to')
    paths   = traits.List(traits.Directory, desc='Paths to add to matlabpath')

class NEW_MatlabCommand(NEW_CommandLine):
    """Interface that runs matlab code

    >>> import nipype.interfaces.matlab as matlab
    >>> mlab = matlab.NEW_MatlabCommand()
    >>> mlab.inputs.script = "which('who')"
    >>> out = mlab.run() # doctest: +SKIP
    """

    _cmd = 'matlab'
    input_spec = MatlabInputSpec
    
    def __init__(self, matlab_cmd = None, **inputs):
        """initializes interface to matlab
        (default 'matlab -nodesktop -nosplash'
        """
        super(NEW_MatlabCommand,self).__init__(**inputs)
        if matlab_cmd is not None:
            self._cmd = matlab_cmd

    def _run_interface(self,runtime):
        runtime = super(NEW_MatlabCommand, self)._run_interface(runtime)
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
        return super(NEW_MatlabCommand, self)._format_arg(name, trait_spec, value)

    def _gen_matlab_command(self, argstr, script_lines):
        cwd = os.getcwd()
        mfile = self.inputs.mfile
        paths = []
        if self.inputs.paths is not Undefined:
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
