"""Miscellaneous file manipulation functions

"""
import numpy as np

def find_indices(condition):
   "Return the indices where ravel(condition) is true"
   res, = np.nonzero(np.ravel(condition))
   return res
