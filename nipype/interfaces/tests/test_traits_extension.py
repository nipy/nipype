# -*- coding: utf-8 -*-
""" tests for the custom traits defined in ./traits_extension.py """

import unittest
import mock

from traits.trait_errors import TraitError

import nibabel as nb
import numpy as np

from nipype.interfaces.traits_extension import NiftiFile

class TestNiftiFile(unittest.TestCase):
    """ tests the custom Trait class NiftiFile """

    filename = 'not a real filename'

    def test_NiftiFile_no_dimension(self):
        """ Initialize a NiftiFile trait without specifying dimensionality
        or setting dimensionality = None """
        nifti_files = [NiftiFile(), NiftiFile(dimensionality=None)]

        for nifti_file in nifti_files:
            self.assertEqual(nifti_file.dimensionality, None)

    def test_NiftiFile_bad_dimensionality(self):
        """ Fail to initialize a NiftiFile trait if dimensionality is not an integer """
        for bad_dim in ['string', 3.14]:
            with self.assertRaisesRegexp(TraitError, 'must be an integer'):
                NiftiFile(dimensionality=bad_dim)

    def test_NiftiFile_dimensionality(self):
        """ Initialize a NiftiFile trait, specifying dimensionality """
        for dim in range(1, 5):
            self.assertEqual(NiftiFile(dimensionality=dim).dimensionality, dim)

    def test_NiftiFile_exists_false(self):
        """ Fail to initialize a NiftiFile trait if exists=False """
        with self.assertRaisesRegexp(TraitError, 'an existing nifti file'):
            NiftiFile(exists=False)

    def test_NiftiFile_exists_true(self):
        """ Initialize a NiftiFile trait without specifying exists or setting exists=True """
        nifti_files = [NiftiFile(), NiftiFile(exists=True)]

        for nifti_file in nifti_files:
            self.assertTrue(nifti_file.exists)

    @mock.patch('os.path.isfile', return_value=True)
    @mock.patch('nibabel.load')
    def test_validate_dimensionality(self, mock_load, mock_isfile):
        """ Test that validation passes when dimensionalities match, fails when they don't """
        mock_load.return_value = nb.Nifti1Image(np.ones((2, 3, 4)), np.eye(4))

        NiftiFile(dimensionality=3).validate(None, 'this will pass', self.filename)

    def test_validate_existence(self):
        """ Pass validation when the file exists, fail when it doesn't """
        with self.assertRaisesRegexp(TraitError, 'this will fail'):
            NiftiFile(dimensionality=4).validate(None, 'this will fail', self.filename)

    def test_validate_nifti(self):
        """ Pass validation when the file is a nifti file, fail when it isn't """

    def test_integration(self):
        """ test behavior while actually in a workflow """
