"""
Package contains interfaces for using existing functionality in other packages

Exaples  FSL, matlab/SPM , afni

Requires Packages to be installed
"""
__docformat__ = 'restructuredtext'

import subprocess


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




class Bunch(object):
    """ Provide Elegant attribute access
    """
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)
       
    def update(self, **kwargs):
        self.__dict__.update(**kwargs)
    
    def iteritems(self):
        return self.__dict__.iteritems()



class CommandLine(object):
    """Encapsulate a command-line function along with the arguments and options.

    Parameters
    ----------
    args: arguments (includes command)

    Returns
    -------
    CommandLine : object

    Examples
    --------

    >>> lscmd = CommandLine('ls') # Create a command object
    >>> output = lscmd.run() # Execute the command
    >>> output.output['out'] # Get output from the command
    >>> output.output['err'] # Get error from command, if any

    # You could also pass in args like this
    >>> lscmd = CommandLine('ls', '-l', '-t')
    # Or
    >>> lscmd = CommandLine('ls -l -t')

    # One way to parse your output is to split on the newline '\n' character:
    >>>  output.output['out'].splitlines()

    Notes
    -----
    When subclassing CommandLine, you will generally override at least:
        update
        _compile_command
        
    Also quite possibly __init__ but generally not run or _runner

    """

    def __init__(self, *args):
        self.args = args


    def run(self, *args, **kwargs):
        """updates arguments, compiles command, sends to runner, 
        stores output and returns new object
        """
        obj_to_run = self.update(*args, **kwargs)
        cmd = obj_to_run._compile_command()
        returncode, out, err = obj_to_run._runner(cmd, 
                                                  cwd=kwargs.get('cwd', None))
        obj_to_run.output = {'returncode':returncode,
                             'out': out,
                             'err':err}
        return obj_to_run
        

    def _runner(self, cmd, shell=True,cwd=None):
        """Use subprocess.Popen to run command
        """
        print cwd
        proc  = subprocess.Popen(cmd, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE, 
                                 shell=shell,
                                 cwd=cwd)
        out, err = proc.communicate()
        returncode = proc.returncode
        return returncode, out, err
    
    def _compile_command(self):
        return ' '.join(self.args)

    def update(self, *args,**kwargs):
        """create derivative command with additional arguments
        returns new CommandLine object
        """
        
        return CommandLine(*(self.args+args))
