""" General matlab interface code """

# Stdlib imports
import os
import re
import tempfile
import numpy as np
from nipype.interfaces.base import CommandLine, InterfaceResult, Bunch
from copy import deepcopy

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
            cwd : string
                working directory for command
        """
        print self.inputs_help.__doc__
        
    def _populate_inputs(self):
        self.inputs = Bunch(script_lines='',
                            script_name='pyscript',
                            mfile=True,
                            cwd='.')

    def run(self):
        
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
            cwd = self.inputs.get('cwd','.')
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
    


