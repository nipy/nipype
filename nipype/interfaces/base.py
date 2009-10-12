"""
Package contains interfaces for using existing functionality in other packages

Exaples  FSL, matlab/SPM , afni

Requires Packages to be installed
"""

import os
import subprocess
from copy import deepcopy
from string import Template
from warnings import warn

__docformat__ = 'restructuredtext'


def load_template(name):
    """Load a template from the script_templates directory

    Parameters
    ----------
    name : str
        The name of the file to load

    Returns
    -------
    template : string.Template

    """

    full_fname = os.path.join(os.path.dirname(__file__),
                              'script_templates', name)
    template_file = open(full_fname)
    template = Template(template_file.read())
    template_file.close()
    return template

class Bunch(object):
    """Provide elegant attribute access.

    Notes
    -----
    The Bunch pattern came from the Python Cookbook:
    .. [1] A. Martelli, D. Hudgeon, "Collecting a Bunch of Named
           Items", Python Cookbook, 2nd Ed, Chapter 4.18, 2005.

    """
    def __init__(self, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)

    def update(self, *args, **kwargs):
        """update existing attribute, or create new attribute"""
        self.__dict__.update(*args, **kwargs)

    def iteritems(self):
        """iterates over bunch attributes as key,value pairs"""
        return self.__dict__.iteritems()

    def get(self, *args):
        '''Support dictionary get() functionality 
        '''
        return self.__dict__.get(*args)

    def __setitem__(self, key, value):
        '''deprecated, dict-like setting of attributes'''
        # get rid of for 0.2?
        warn(DeprecationWarning('please use direct attribute'))
        self.__dict__[key] = value

    def __getitem__(self, key):
        '''deprecated, dict-like getting of attributes'''
        # get rid of for 0.2?
        warn(DeprecationWarning('please use direct attribute'))
        return(self.__dict__[key])

    def dictcopy(self):
        """returns a deep copy of existing Bunch as a dictionary"""
        return deepcopy(self.__dict__)

    def __repr__(self):
        """representation of the sorted Bunch as a string

        Currently, this string representation of the `inputs` Bunch of
        interfaces is hashed to determine if the process' dirty-bit
        needs setting or not. Till that mechanism changes, only alter
        this after careful consideration.
        """
        outstr = ['Bunch(']
        first = True
        for k, v in sorted(self.iteritems()):
            if not first:
                outstr.append(', ')
            outstr.append('%s=%r' % (k, v))
            first = False
        outstr.append(')')
        return ''.join(outstr)

    def __pretty__(self, p, cycle):
        '''Support for the pretty module
        
        pretty is included in ipython.externals for ipython > 0.10'''
        if cycle:
            p.text('Bunch(...)')
        else:
            p.begin_group(6, 'Bunch(')
            first = True
            for k, v in sorted(self.iteritems()):
                if not first:
                    p.text(',')
                    p.breakable()
                p.text(k + '=')
                p.pretty(v)
                first = False
            p.end_group(6, ')')
    

class InterfaceResult(object):
    '''Describe the results of .run()-ing a particular Interface'''
    def __init__(self, interface, runtime, outputs=None):
        self.interface = interface
        self.runtime = runtime
        self.outputs = outputs


class Interface(object):
    """This is the template for Interface objects.

    It provides no functionality.  It defines the necessary attributes
    and methods all Interface objects should have.

    Everything in inputs should also be a possible (explicit?) argument to
    .__init__()
    """

    def __init__(self, *args, **inputs):
        """Initialize command with given args and inputs."""
        raise NotImplementedError

    def run(self):
        """Execute the command."""
        raise NotImplementedError

    def _runner(self):
        """Performs the call to execute the command."""
        raise NotImplementedError

    def _populate_inputs(self):
        """Initialize the inputs Bunch attributes."""
        raise NotImplementedError

    def aggregate_outputs(self):
        """Called to populate outputs
        
        Currently, search for discussion of this on private e-mails between Dav
        and Satra (ugh!).  This needs to get in here!"""
        raise NotImplementedError


class CommandLine(Interface):
    """Encapsulate a command-line function along with the arguments and options.

    Provides a convenient mechanism to build a command line with it's
    arguments and options incrementally.  A `CommandLine` object can
    be reused, and it's arguments and options updated.  The
    `CommandLine` class is the base class for all nipype.interfaces
    classes.

    Parameters
    ----------
    args : string
        A string representing the command and it's arguments.
    inputs : mapping
        key value pairs that populate a Bunch()


    Attributes
    ----------
    args : list
        The command, it's arguments and options store in a list of strings.
        ['ls', '-al']
        These are added to command line string first
    inputs : Bunch of key,value inputs
        The only valid key for CommandLine is args
        Other keys are not recognized in CommandLine, and
        require parsing in subclasses
        if there are args=['ls','-al'] 
        These are added to command line string before simple positional args
    Returns
    -------
    
    cmd : CommandLine
        A `CommandLine` object that can be run and/or updated.

    Examples
    --------
    >>> from nipype.interfaces.base import CommandLine
    >>> cmd = CommandLine('echo')
    >>> cmd.cmdline
    'echo'
    >>> res = cmd.run('foo')
    >>> print res.runtime.stdout
    foo
    <BLANKLINE>

    You could pass arguments in the following ways and all result in
    the same command.
    >>> lscmd = CommandLine('ls', '-l', '-t')
    >>> lscmd.cmdline
    'ls -l -t'
    >>> lscmd = CommandLine('ls -l -t') 
    >>> lscmd.cmdline
    'ls -l -t'
    >>> lscmd = CommandLine(args=['ls', '-l', '-t'])
    >>> lscmd.cmdline
    'ls -l -t'

    Notes
    -----
    
    When subclassing CommandLine, you will generally override at least:
        _compile_command, and run

    Also quite possibly __init__ but generally not  _runner

    """

    def __init__(self, *args, **inputs):
        self._populate_inputs()
        self._update(*args, **inputs)

    def _update(self, *args, **inputs):
        '''Helper function to support DRY'''
        # XXX should rethink how CommandLine is to be used and work
        # through the processing of args and inputs['args'].
        try:
            # if inputs['args'] exists and is splittable (thus, not a list)
            # Handles case like this: CommandLine(args='echo foo')
            if hasattr(inputs['args'], 'split'):
                inputs['args']  = inputs['args'].split()
        except KeyError:
            pass

        self.inputs.update(inputs)

        if args:
            # In general, only CommandLine objects have an 'args' attr
            # in self.inputs.  Most of the subclasses of CommandLine
            # (Bet, Fast, etc...) do not, so we need to confirm it
            # exists before checking if it's None.
            if hasattr(self.inputs, 'args') and self.inputs.args:
                self.inputs.args.extend(list(args))
            else:
                self.inputs.args = list(args)

    def run(self, *args, **inputs):
        """Execute the command.
        
        Parameters
        ----------
        args : list
            additional arguments that will be appended to inputs.args
        inputs : mapping
            additional key,value pairs will update inputs
            it will overwrite existing key, value pairs
           
        Returns
        -------
        results : InterfaceResult Object
            A `Bunch` object with a copy of self in `interface`
        
        """
        self._update(*args, **inputs) 
            
        return self._runner()

    def _populate_inputs(self):
        self.inputs = Bunch(args=None)

    @property
    def cmdline(self):
        # This handles args like ['bet', '-f 0.2'] without crashing
        return ' '.join(self.inputs.args)

    def _runner(self, shell=True, cwd=None):
        """Run the command using subprocess.Popen.
        
        Arguments
        ---------
        
        shell : bool
            shell command passed to Popen, do we parse the cmdline?
        cwd : str
            Note that unlike calls to Popen, cwd=None will still check
            self.inputs.cwd!  Use an alternative like '.' if you need it
        """
        if cwd is None:
            cwd = self.inputs.get('cwd', '.')
        runtime = Bunch(cmdline=self.cmdline)

        proc  = subprocess.Popen(runtime.cmdline,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=shell,
                                 cwd=cwd)

        runtime.stdout, runtime.stderr = proc.communicate()
        runtime.returncode = proc.returncode

        return InterfaceResult(deepcopy(self), runtime)

    def get_input_info(self):
        """ Provides information about file inputs to copy or link to cwd.
        
        Notes
        -----
        see `spm.Realign.get_input_info`
            
        """
        return []

