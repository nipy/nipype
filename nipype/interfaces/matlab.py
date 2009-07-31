""" General matlab interface code """

# Stdlib imports
import os
import re
import tempfile
import numpy as np
from nipype.interfaces.base import CommandLine, InterfaceResult, Bunch


class MatlabCommandLine(CommandLine):
    """Object that sets up Matlab specific tools and interfaces

    """
    matlab_cmd = 'matlab -nodesktop -nosplash'
    def __init__(self, matlab_cmd=None):
        """initializes interface to matlab
        (default 'matlab -nodesktop -nosplash'
        """
        super(MatlabCommandLine,self).__init__()
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
        #subprocess.call('%s -r \"%s;exit\" ' % (matlab_cmd, cmd),
        #                shell=True)
        self._compile_command()
        returncode, out, err = self._runner(cwd=self.inputs.get('cwd','.'))
        if  'MatlabScriptException' in err:
            returncode = 1
        return InterfaceResult(runtime=Bunch(cmdline=self.cmdline,
                                             returncode=returncode,
                                             stdout=out,stderr=err),
                               outputs=None,
                               interface=self.copy())

    def _compile_command(self):
        self.cmdline = self.gen_matlab_command(script_lines=self.inputs.script_lines,
                                               script_name=self.inputs.script_name,
                                               cwd=self.inputs.cwd)
        return self.cmdline

    def gen_matlab_command(self,script_lines='',script_name='pyscript',cwd='.'):
        """ Put multiline matlab script into script file and run
        Arguments:
        - `self`:
        - `script_lines`:
        - `script_name`:
        - `cwd`:
        """
        mfile = file(os.path.join(cwd,script_name + '.m'), 'wt')
        prescript  = "diary(sprintf('%s.log',mfilename))\n"
        prescript += "fprintf('Executing %s at %s:\\n',mfilename,datestr(now));\n" 
        prescript += "ver\n"
        prescript  += "try,\n"
        postscript = "\ncatch ME,\n"
        postscript += "diary off\n"
        postscript += "diary(sprintf('%s_error.log',mfilename))\n"
        postscript += "ME\n"
        postscript += "ME.stack\n"
        postscript += "fprintf('%s\\n',ME.message); %stdout\n"
        postscript += "fprintf(2,'<MatlabScriptException>') %stderr;\n"
        postscript += "fprintf(2,'%s\\n',ME.message) %stderr;\n"
        postscript += "fprintf(2,'File:%s\\nName:%s\\nLine:%d\\n',ME.stack.file,ME.stack.name,ME.stack.line);\n"
        postscript += "fprintf(2,'</MatlabScriptException>') %stderr;\n"
        postscript += "diary off\n"
        postscript += "end;\n"
        script_lines = prescript+script_lines+postscript
        mfile.write(script_lines)
        mfile.close()
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
