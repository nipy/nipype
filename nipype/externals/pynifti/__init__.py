#emacs: -*- mode: python-mode; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the PyNIfTI package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""This module provides Python bindings to the NIfTI data format.

The PyNIfTI module is a Python interface to the NIfTI I/O libraries. Using
PyNIfTI, one can easily read and write NIfTI and ANALYZE images from within
Python. The :class:`~nifti.image.NiftiImage` class provides pythonic
access to the full header information and for a maximum of interoperability the
image data is made available via NumPy arrays.

==============
 Volumeimages
==============

Quickstart::

   import nipype.externals.pynifti

   img1 = nifti.load('my_file.nii')
   img2 = nifti.load('other_file.nii.gz')
   img3 = nifti.load('spm_file.img')

   data = img1.get_data()
   affine = img1.get_affine()

   print img1

   nifti.save(img1, 'my_file_copy.nii.gz')

   new_image = nifti.Nifti1Image(data, affine)
   nifti.save(new_image, 'new_image.nii.gz')
"""

__docformat__ = 'restructuredtext'

# expose the two main classes
#from nifti.image import NiftiImage, MemMappedNiftiImage

# canonical version string
__version__ = '0.20090303.1'


# module imports
from nipype.externals.pynifti import analyze as ana
from nipype.externals.pynifti import spm99analyze as spm99
from nipype.externals.pynifti import spm2analyze as spm2
from nipype.externals.pynifti import nifti1 as ni1
from nipype.externals.pynifti import minc
# object imports
from nipype.externals.pynifti.loadsave import load, save
from nipype.externals.pynifti.analyze import AnalyzeHeader, AnalyzeImage
from nipype.externals.pynifti.spm99analyze import Spm99AnalyzeHeader, Spm99AnalyzeImage
from nipype.externals.pynifti.spm2analyze import Spm2AnalyzeHeader, Spm2AnalyzeImage
from nipype.externals.pynifti.nifti1 import Nifti1Header, Nifti1Image
from nipype.externals.pynifti.minc import MincHeader, MincImage
from nipype.externals.pynifti.funcs import squeeze_image, concat_images
