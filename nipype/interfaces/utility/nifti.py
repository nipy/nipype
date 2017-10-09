# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Various utilities for manipulating nifti files

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname(os.path.realpath(__file__))
    >>> datadir = os.path.realpath(os.path.join(filepath,
    ...                            '../../testing/data'))
    >>> os.chdir(datadir)

List of nifti datatypes
~~~~~~~~~~~~~~~~~~~~~~~

.. note: original Analyze 7.5 types

  DT_NONE                    0
  DT_UNKNOWN                 0     / what it says, dude           /
  DT_BINARY                  1     / binary (1 bit/voxel)         /
  DT_UNSIGNED_CHAR           2     / unsigned char (8 bits/voxel) /
  DT_SIGNED_SHORT            4     / signed short (16 bits/voxel) /
  DT_SIGNED_INT              8     / signed int (32 bits/voxel)   /
  DT_FLOAT                  16     / float (32 bits/voxel)        /
  DT_COMPLEX                32     / complex (64 bits/voxel)      /
  DT_DOUBLE                 64     / double (64 bits/voxel)       /
  DT_RGB                   128     / RGB triple (24 bits/voxel)   /
  DT_ALL                   255     / not very useful (?)          /

.. note: added names for the same data types

  DT_UINT8                   2
  DT_INT16                   4
  DT_INT32                   8
  DT_FLOAT32                16
  DT_COMPLEX64              32
  DT_FLOAT64                64
  DT_RGB24                 128


.. note: new codes for NIFTI

  DT_INT8                  256     / signed char (8 bits)         /
  DT_UINT16                512     / unsigned short (16 bits)     /
  DT_UINT32                768     / unsigned int (32 bits)       /
  DT_INT64                1024     / long long (64 bits)          /
  DT_UINT64               1280     / unsigned long long (64 bits) /
  DT_FLOAT128             1536     / long double (128 bits)       /
  DT_COMPLEX128           1792     / double pair (128 bits)       /
  DT_COMPLEX256           2048     / long double pair (256 bits)  /
  NIFTI_TYPE_UINT8           2 /! unsigned char. /
  NIFTI_TYPE_INT16           4 /! signed short. /
  NIFTI_TYPE_INT32           8 /! signed int. /
  NIFTI_TYPE_FLOAT32        16 /! 32 bit float. /
  NIFTI_TYPE_COMPLEX64      32 /! 64 bit complex = 2 32 bit floats. /
  NIFTI_TYPE_FLOAT64        64 /! 64 bit float = double. /
  NIFTI_TYPE_RGB24         128 /! 3 8 bit bytes. /
  NIFTI_TYPE_INT8          256 /! signed char. /
  NIFTI_TYPE_UINT16        512 /! unsigned short. /
  NIFTI_TYPE_UINT32        768 /! unsigned int. /
  NIFTI_TYPE_INT64        1024 /! signed long long. /
  NIFTI_TYPE_UINT64       1280 /! unsigned long long. /
  NIFTI_TYPE_FLOAT128     1536 /! 128 bit float = long double. /
  NIFTI_TYPE_COMPLEX128   1792 /! 128 bit complex = 2 64 bit floats. /
  NIFTI_TYPE_COMPLEX256   2048 /! 256 bit complex = 2 128 bit floats /

"""

from __future__ import print_function, division, absolute_import, unicode_literals
from os import path as op
import numpy as np
import nibabel as nb

from io import open

from nipype import logging
from nipype.utils import NUMPY_MMAP
from nipype.interfaces.base import traits, TraitedSpec, BaseInterface, BaseInterfaceInputSpec, File


IFLOGGER = logging.getLogger('interface')

DTYPE_MAP = {
    1: np.uint8, 2: np.uint8, 256: np.uint8,
    4: np.uint16,
    8: np.uint32, 1024: np.uint32, 1280: np.uint32,
    64: np.float32, 1536: np.float32
}

class ConformImageInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='input image')
    check_ras = traits.Bool(True, usedefault=True,
                            desc='check that orientation is RAS')
    check_dtype = traits.Bool(False, usedefault=True,
                              desc='check data type, and limit to 8-32 bits')
    base_affine = traits.Bool(False, usedefault=True,
                              desc='ignore sform and qform matrices')
    save_hdr = traits.Bool(False, usedefault=True, desc='backup old header')


class ConformImageOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='output conformed file')
    out_hdr = File(desc='Python pickle containing backed-up header')


class ConformImage(BaseInterface):

    """
    Conforms the orientation, affine matrix and data type of the input image

    """
    input_spec = ConformImageInputSpec
    output_spec = ConformImageOutputSpec

    def __init__(self, **inputs):
        self._results = {}
        super(ConformImage, self).__init__(**inputs)

    def _list_outputs(self):
        return self._results

    def _run_interface(self, runtime):
        # load image
        if not np.any((self.inputs.check_ras,
                       self.inputs.check_dtype,
                       self.inputs.base_affine)):
            self._results['out_file'] = self.inputs.in_file
            IFLOGGER.warning('No conform operation requested on the input image "%s".',
                             self.inputs.in_file)
            return runtime

        # Generate name
        out_file, ext = op.splitext(op.basename(self.inputs.in_file))
        if ext == '.gz':
            out_file, ext2 = op.splitext(out_file)
            ext = ext2 + ext

        nii = nb.load(self.inputs.in_file, mmap=NUMPY_MMAP)
        data = nii.get_data()
        hdr = nii.header.copy()

        if self.inputs.save_hdr:
            self._results['out_hdr'] = op.abspath('{}_hdr.pklz'.format(out_file))
            with open(self._results['out_hdr'], 'wb') as fheader:
                hdr.write_to(fheader)


        aff = nii.affine

        if self.inputs.check_ras:
            data = nb.as_closest_canonical(nii).get_data()

        if self.inputs.base_affine:
            data = nb.as_closest_canonical(nii).get_data()
            aff = nb.as_closest_canonical(nii).header.get_base_affine()
            hdr['qform_code'] = 0
            hdr['sform_code'] = 0

            if not self.inputs.check_ras:
                # Data was intentionally oriented in RAS+
                # flip axis to maintain data in LAS+
                data = data[::-1, ...]
            else:
                # Base affine is LAS+, make RAS+
                aff[0, :] *= -1.0

        if self.inputs.check_dtype:
            datatype = int(hdr['datatype'])
            dtype = DTYPE_MAP.get(datatype, None)

            if dtype is None:
                dtype = hdr.get_data_dtype()
                IFLOGGER.info('Data type "%s" of input image %s will remain unchanged',
                              dtype, self.inputs.in_file)
            else:
                IFLOGGER.info('Image %s was casted to data type "%s"',
                              self.inputs.in_file, dtype)

            hdr.set_data_dtype(dtype)


        self._results['out_file'] = op.abspath('{}_conformed{}'.format(out_file, ext))
        nii = nb.Nifti1Image(data.astype(dtype), aff, hdr).to_filename(
            self._results['out_file'])
        return runtime
