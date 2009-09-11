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
      
