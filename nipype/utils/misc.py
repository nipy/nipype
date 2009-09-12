"""Miscellaneous utility functions
"""
import numpy as np
import os

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
