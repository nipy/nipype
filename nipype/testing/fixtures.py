# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
Pytest fixtures used in tests.
"""
from __future__ import print_function, division, unicode_literals, absolute_import


import os
import pytest
import numpy as np
import nibabel as nb

from io import open
from builtins import str

from nipype.utils.filemanip import filename_to_list
from nipype.interfaces.fsl import Info
from nipype.interfaces.fsl.base import FSLCommand


def analyze_pair_image_files(outdir, filelist, shape):
    for f in filename_to_list(filelist):
        hdr = nb.Nifti1Header()
        hdr.set_data_shape(shape)
        img = np.random.random(shape)
        analyze = nb.AnalyzeImage(img, np.eye(4), hdr)
        analyze.to_filename(os.path.join(outdir, f))


def nifti_image_files(outdir, filelist, shape):
    for f in filename_to_list(filelist):
        img = np.random.random(shape)
        nb.Nifti1Image(img, np.eye(4), None).to_filename(
            os.path.join(outdir, f))


@pytest.fixture()
def create_files_in_directory(request, tmpdir):
    outdir = str(tmpdir)
    cwd = os.getcwd()
    os.chdir(outdir)
    filelist = ['a.nii', 'b.nii']
    nifti_image_files(outdir, filelist, shape=(3,3,3,4))

    def change_directory():
        os.chdir(cwd)

    request.addfinalizer(change_directory)
    return (filelist, outdir)


@pytest.fixture()
def create_analyze_pair_file_in_directory(request, tmpdir):
    outdir = str(tmpdir)
    cwd = os.getcwd()
    os.chdir(outdir)
    filelist = ['a.hdr']
    analyze_pair_image_files(outdir, filelist, shape=(3, 3, 3, 4))

    def change_directory():
        os.chdir(cwd)

    request.addfinalizer(change_directory)
    return (filelist, outdir)


@pytest.fixture()
def create_files_in_directory_plus_dummy_file(request, tmpdir):
    outdir = str(tmpdir)
    cwd = os.getcwd()
    os.chdir(outdir)
    filelist = ['a.nii', 'b.nii']
    nifti_image_files(outdir, filelist, shape=(3,3,3,4))

    with open(os.path.join(outdir, 'reg.dat'), 'wt') as fp:
        fp.write('dummy file')
    filelist.append('reg.dat')

    def change_directory():
        os.chdir(cwd)

    request.addfinalizer(change_directory)
    return (filelist, outdir)


@pytest.fixture()
def create_surf_file_in_directory(request, tmpdir):
    outdir = str(tmpdir)
    cwd = os.getcwd()
    os.chdir(outdir)
    surf = 'lh.a.nii'
    nifti_image_files(outdir, filelist=surf, shape=(1, 100, 1))

    def change_directory():
        os.chdir(cwd)

    request.addfinalizer(change_directory)
    return (surf, outdir)


def set_output_type(fsl_output_type):
    prev_output_type = os.environ.get('FSLOUTPUTTYPE', None)

    if fsl_output_type is not None:
        os.environ['FSLOUTPUTTYPE'] = fsl_output_type
    elif 'FSLOUTPUTTYPE' in os.environ:
        del os.environ['FSLOUTPUTTYPE']

    FSLCommand.set_default_output_type(Info.output_type())
    return prev_output_type

@pytest.fixture(params=[None]+list(Info.ftypes))
def create_files_in_directory_plus_output_type(request, tmpdir):
    func_prev_type = set_output_type(request.param)

    testdir = str(tmpdir)
    origdir = os.getcwd()
    os.chdir(testdir)
    filelist = ['a.nii', 'b.nii']
    nifti_image_files(testdir, filelist, shape=(3,3,3,4))

    out_ext = Info.output_type_to_ext(Info.output_type())

    def fin():
        set_output_type(func_prev_type)
        os.chdir(origdir)

    request.addfinalizer(fin)
    return (filelist, testdir, out_ext)
