"""
Package contains interfaces for using existing functionality in other packages

Exaples  FSL, matlab/SPM , afni

Requires Packages to be installed
"""
__docformat__ = 'restructuredtext'

import subprocess
from copy import deepcopy
from string import Template


class OneTimeProperty(object):
   """A descriptor to make special properties that become normal attributes.
   """
   def __init__(self,func):
       """Create a OneTimeProperty instance.

        Parameters
        ----------
          func : method
          
            The method that will be called the first time to compute a value.
            Afterwards, the method's name will be a standard attribute holding
            the value of this computation.
            """
       self.getter = func
       self.name = func.func_name

   def __get__(self,obj,type=None):
       """This will be called on attribute access on the class or instance. """

       if obj is None:
           # Being called on the class, return the original function. This way,
           # introspection works on the class.
           return func

       val = self.getter(obj)
       print "** setattr_on_read - loading '%s'" % self.name  # dbg
       setattr(obj, self.name, val)
       return val


def setattr_on_read(func):
    """Decorator to create OneTimeProperty attributes.

    Parameters
    ----------
      func : method
        The method that will be called the first time to compute a value.
        Afterwards, the method's name will be a standard attribute holding the
        value of this computation.
    """
    return OneTimeProperty(func)


def load_template(name):
    '''Load a template from the script_templates directory

    Parameters
    ----------
      name : str
        The name of the file to load

    Returns
    -------
      template : string.Template
    '''
    full_fname = '/'.join([os.path.dirname(__file__), 'script_templates', name])
    template_file = open(full_fname)
    template = Template(template_file.read())
    template_file.close()

    return template
    

class Bunch(object):
    """ Provide Elegant attribute access

    (Also provide inelegant dict-style access to make Satra's life easier)

    Notes
    -----
    The Bunch pattern came from the Python Cookbook:
    .. [1] A. Martelli, D. Hudgeon, "Collecting a Bunch of Named
    Items", Python Cookbook, 2nd Ed, Chapter 4.18, 2005.

    """
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)
       
    def update(self, **kwargs):
        self.__dict__.update(**kwargs)
    
    def iteritems(self):
        return self.__dict__.iteritems()

    def get(self, *args):
        '''Need to consider how much of the dict interface we will support'''
        return self.__dict__.get(*args)

    def __setitem__(self, key, value):
        '''deprecated, except for Satra'''
        self.__dict__[key] = value

    def __getitem__(self, key):
        '''deprecated, except for Satra'''
        return(self.__dict__[key])

    def dictcopy(self):
        return deepcopy(self.__dict__)

    def dict2str(self,anydict):
        """ Converts a dict to an ordered representation """
        outstr = '{'
        for f in sorted(anydict):
            if type(anydict[f]) is not type({}):
                outstr = ''.join((outstr,str(f),':',str(anydict[f]),',\n'))
            else:
                outstr = ''.join((outstr,str(f),':',self.dict2str(anydict[f]),',\n'))
        outstr = ''.join((outstr,'}'))
        return outstr

    def __str__(self):
       return self.dict2str(self.__dict__)

class Interface(object):
    '''Some notes: This is the template for Interface objects
    It provide no functionality at this point, but is a reference
    for how interfaces should interact

    Everything in inputs should also be a possible (explicit?) argument to
    .__init__()''' 
    def __init__(self, *args, **inputs):
        self._populate_inputs()
        self.inputs.update(**inputs)
        if args:
            self.inputs.args = args
        self.cmdline = ''

    def run(self):
        raise NotImplementedError

    def copy(self):
        """Return a copy of CommandLine
        
        This is comparable to a copy.deepcopy - such that any "reasonable"
        modifications won't have long distance consequences.

        Returns
        -------
        results : self.__class__
            A new `CommandLine` instance otherwise identical with self 

        """
        return CommandLine(**self.inputs.dictcopy())

    def _populate_inputs(self):
        raise NotImplementedError

class InterfaceResult(object):
    '''Describe the results of .run()-ing a particular Interface'''
    def __init__(self, interface, runtime, outputs):
        self.interface = interface
        self.runtime = runtime
        self.outputs = outputs

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
        
        
    Attributes
    ----------
    args : tuple
        The command, it's arguments and options store in a tuple of strings.

    Returns
    -------
    cmd : CommandLine
        A `CommandLine` object that can be run and/or updated.

    Examples
    --------

    >>> lscmd = CommandLine('ls') # Create a command object
    >>> output = lscmd.run() # Execute the command
    >>> output.out # Get output from the command
    >>> output.err # Get error from command, if any

    # You could also pass in args like this
    >>> lscmd = CommandLine('ls', '-l', '-t')
    # Or
    >>> lscmd = CommandLine('ls -l -t')
    # Or
    >>> lscmd = CommandLine(args=['ls','-l'])

    # One way to view your stdout is to print
    >>> print output.stdout
    >>> output.returncode
    >>> print output.stderr

    Notes
    -----
    When subclassing CommandLine, you will generally override at least:
        _compile_command
        
    Also quite possibly __init__ but generally not run or _runner

    """

    def run(self):
        """Execute the command.

        Parameters
        ----------
        N/A

        Returns
        -------
        results : Bunch
            A `Bunch` object with a copy of self in `interface`

        """

        # This is expected to populate `command` for _runner to work
        self._compile_command()
        returncode, out, err = self._runner(cwd=self.inputs.get('cwd', None))
        runtime = Bunch(returncode=returncode,
                        messages=out,
                        errmessages=err)
                
        return InterfaceResult(self.copy(), runtime, outputs=None) 
        
    def _populate_inputs(self):
        self.inputs = Bunch(args=None)

    def _compile_command(self):
        # This handles args like ['bet', '-f 0.2'] without crashing
        self.cmdline = ' '.join(self.inputs.args)

    def _runner(self, shell=True, cwd=None):
        """Run the command using subprocess.Popen."""
        proc  = subprocess.Popen(self.cmdline, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE, 
                                 shell=shell,
                                 cwd=cwd)
        out, err = proc.communicate()
        returncode = proc.returncode
        return returncode, out, err
    
