"""Miscellaneous utility functions
"""
import numpy as np
import os
from distutils.version import LooseVersion

def find_indices(condition):
   "Return the indices where ravel(condition) is true"
   res, = np.nonzero(np.ravel(condition))
   return res

def mktree(path):
   dirs = path.split(os.path.sep)
   outdir = dirs[0]
   if outdir == '':
      outdir = os.path.sep
   for d in dirs[1:]:
      outdir = os.path.join(outdir,d)
      if not os.path.exists(outdir):
         os.mkdir(outdir)

def is_container(item):
   """Checks if item is a container (list, tuple, dict, set)
   
   Parameters
   ----------
   item : object 
       object to check for .__iter__
      
   Returns
   -------
   output : Boolean
       True if container
       False if not (eg string)
   """
   if hasattr(item, '__iter__'):
      return True
   else:
      return False
      
def container_to_string(cont):
   """Convert a container to a command line string.
   
   Elements of the container are joined with a space between them,
   suitable for a command line parameter.

   If the container `cont` is only a sequence, like a string and not a
   container, it is returned unmodified.

   Parameters
   ----------
   cont : container
      A container object like a list, tuple, dict, or a set.

   Returns
   -------
   cont_str : string
       Container elements joined into a string.

   """
   if hasattr(cont, '__iter__'):
      return ' '.join(cont)
   else:
      return str(cont)


# Dependency checks.  Copied this from Nipy, with some modificiations
# (added app as a parameter).
def package_check(pkg_name, version=None, app=None, checker=LooseVersion):
    """Check that the minimal version of the required package is installed.

    Parameters
    ----------
    pkg_name : string
        Name of the required package.
    version : string
        Minimal version number for required package.
    app : string
        Application that is performing the check.  For instance, the
        name of the tutorial being executed that depends on specific
        packages.  Default is *Nipype*.
    checker : object
        The class that will perform the version checking.  Default is
        distutils.version.LooseVersion.

    Examples
    --------
    package_check('numpy', '1.3')
    package_check('networkx', '1.0', 'tutorial1')

    """

    if app:
        msg = '%s requires %s' % (app, pkg_name)
    else:
        msg = 'Nipype requires %s' % pkg_name
    try:
        mod = __import__(pkg_name)
    except ImportError:
        raise ImportError(msg)
    if not version:
        return
    msg += ' >= %s' % version
    try:
        have_version = mod.__version__
    except AttributeError:
        raise RuntimeError('Cannot find version for %s' % pkg_name)
    if checker(have_version) < checker(version):
        raise RuntimeError(msg)

