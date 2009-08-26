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

    >>> matlab.MatlabCommandLine.matlab_cmd = "matlab.2009a -nodesktop -nosplash"
    >>> mcmd = matlab.MatlabCommandLine()
    >>> mcmd.inputs.script_lines = "which('who')"
    >>> out = mcmd.run()
    """
    _cmdline = None
    _cmdline_inputs = None
    @property
    def cmdline(self):
        # This is currently a very inefficient hash! We can become more
        # efficient once we decide on our logic
        if self._cmdline is None or self._cmdline_inputs != self.inputs:
            self._compile_command()
            self_cmdline_inputs = self.inputs

        return self._cmdline

    matlab_cmd = 'matlab -nodesktop -nosplash'
    def __init__(self, matlab_cmd=None,**inputs):
        """initializes interface to matlab
        (default 'matlab -nodesktop -nosplash'
        """
        super(MatlabCommandLine,self).__init__(**inputs)
        self.cmdline2 = None
        if matlab_cmd is not None:
            self.matlab_cmd = matlab_cmd

    def set_matlabcmd(self, cmd):
        """reset the base matlab command
        """
        self.matlab_cmd = cmd
        
    def inputs_help(self):
        doc = """
            Optional Parameters
            -------------------
            (all default to None and are unset)

            script_lines : string
                matlab_script or function name or matlab code to run
            cwd : string
                working directory for command
            """
        print doc
        
    def _populate_inputs(self):
        self.inputs = Bunch(script_lines='',
                            script_name='pyscript',
                            cwd='.')

    def run(self):
        results = self._runner()
        if  'MatlabScriptException' in results.runtime.stderr:
            results.runtime.returncode = 1
        return results

    def _compile_command(self, mfile=True):
        '''Generate necessary Matlab files and cmdline

        Note that this could be called before accessing .cmdline, and we won't
        regenerate anything (unless the inputs have changed)
        '''
        self._cmdline = self.gen_matlab_command(
                script_lines=self.inputs.script_lines,
                script_name=self.inputs.script_name,
                mfile=mfile)
        return self._cmdline

    def gen_matlab_command(self,script_lines='',script_name='pyscript',
            cwd=None,mfile=True):
        """ Put multiline matlab script into script file and run
        Arguments
        ---------

        self :
        script_lines :
        script_name :
        cwd :
            Note that unlike calls to Popen, cwd=None will still check
            self.inputs.cwd!  Use an alternative like '.' if you need it
        """
        if cwd is None:
            cwd = self.inputs.get('cwd', None)
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
        return '%s -r \"%s;exit\" ' % (self.matlab_cmd, script_name)

# Useful Functions for working with matlab

def fltcols(vals):
    ''' Trivial little function to make 1xN float vector '''
    return np.atleast_2d(np.array(vals, dtype=float))


def mlab_tempfile(dir=None):
    """Returns a temporary file-like object with valid matlab name.

    The file name is accessible as the .name attribute of the returned object.
    The caller is responsible for closing the returned object, at which time
    the underlying file gets deleted from the filesystem.

    Parameters
    ----------
    
      dir : str
        A path to use as the starting directory.  Note that this directory must
        already exist, it is NOT created if it doesn't (in that case, OSError
        is raised instead).

    Returns
    -------
      f : A file-like object.

    Examples
    --------

    >>> f = mlab_tempfile()
    >>> '-' not in f.name
    True
    >>> f.close()
    """
    valid_name = re.compile(r'^\w+$')

    # Make temp files until we get one whose name is a valid matlab identifier,
    # since matlab imposes that constraint.  Since the temp file routines may
    # return names that aren't valid matlab names, but we can't control that
    # directly, we just keep trying until we get a valid name.  To avoid an
    # infinite loop for some strange reason, we only try 100 times.
    for n in range(100):
        f = tempfile.NamedTemporaryFile(suffix='.m',prefix='tmp_matlab_',
                                        dir=dir)
        # Check the file name for matlab compilance
        fname =  os.path.splitext(os.path.basename(f.name))[0]
        if valid_name.match(fname):
            break
        # Close the temp file we just made if its name is not valid; the
        # tempfile module then takes care of deleting the actual file on disk.
        f.close()
    else:
        raise ValueError("Could not make temp file after 100 tries")
        
    return f
