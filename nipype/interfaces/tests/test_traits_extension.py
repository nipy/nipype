# -*- coding: utf-8 -*-
""" tests for the custom traits defined in ./traits_extension.py """

import unittest

from traits.trait_errors import TraitError

from nipype.interfaces.traits_extension import NiftiFile

class TestNiftiFile(unittest.TestCase):
    """ tests the custom Trait class NiftiFile """

    def test_NiftiFile_no_dimension(self):
        """ Initialize a NiftiFile trait without specifying dimensionality
        or setting dimensionality = None """

    def test_NiftiFile_dimensionality_check(self):
        """ Initialize a NiftiFile trait, specifying dimensionality """

    def test_NiftiFile_exists_false(self):
        """ Fail to initialize a NiftiFile trait if exists=False """
        with self.assertRaisesRegexp(TraitError, 'an existing nifti file'):
            NiftiFile(exists=False)

    def test_NiftiFile_exists_true(self):
        """ Initialize a NiftiFile trait without specifying exists or setting exists=True """
        nifti_files = [NiftiFile(), NiftiFile(exists=True)]

        for nifti_file in nifti_files:
            self.assertTrue(nifti_file.exists)

    def test_integration(self):
        """ test behavior while actually in a workflow """
