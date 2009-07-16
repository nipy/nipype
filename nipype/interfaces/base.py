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
    """ Base CommandLine class that handles arguments and generates command line string
        That can be run using subprocess.Popen

        
    """
    def __init__(self, *args):
        """
        base commandline class, handles arguments, uses subprocess.Popen

        Parameters
        ----------
        args: arguments (includes command)


        Returns
        -------
        CommandLine : object
        

        When subclassing CommandLine, you will generally override at least:
        update
        _compile_command
        
        Also quite possibly __init__ but generally not run or _runner

        """ 
        self.args = args


    def run(self, *args, **kwargs):
        """updates arguments, compiles command, sends to runner, 
        stores output and returns new object
        """
        obj_to_run = self.update(*args, **kwargs)
        cmd = obj_to_run._compile_command()
        returncode, out, err = obj_to_run._runner(cmd)
        obj_to_run.output = {'returncode':returncode,
                             'out': out,
                             'err':err}
        return obj_to_run
        

    def _runner(self, cmd, shell=True):
        """Use subprocess.Popen to run command
        """
        proc  = subprocess.Popen(cmd, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE, 
                                 shell=shell)
        out, err = proc.communicate()
        returncode = proc.returncode
        return returncode, out, err
    
    def _compile_command(self):
        return ' '.join(self.args)

    def update(self, *args):
        """create derivative command with additional arguments
        returns new CommandLine object
        """
        
        return CommandLine(*(self.args+args))
