# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
Pytest fixtures used in tests.
"""

import os
import pytest
import numpy as np
from tempfile import mkdtemp
from shutil import rmtree

import nibabel as nb
from nipype.interfaces.fsl import Info
from nipype.interfaces.fsl.base import FSLCommand


@pytest.fixture()
def create_files_in_directory(request):
    outdir = os.path.realpath(mkdtemp())
    cwd = os.getcwd()
    os.chdir(outdir)
    filelist = ['a.nii', 'b.nii']
    for f in filelist:
        hdr = nb.Nifti1Header()
        shape = (3, 3, 3, 4)
        hdr.set_data_shape(shape)
        img = np.random.random(shape)
        nb.save(nb.Nifti1Image(img, np.eye(4), hdr),
                 os.path.join(outdir, f))

    def clean_directory():
        if os.path.exists(outdir):
            rmtree(outdir)
        os.chdir(cwd)

    request.addfinalizer(clean_directory)
    return (filelist, outdir)


@pytest.fixture()
def create_files_in_directory_plus_dummy_file(request):
    outdir = os.path.realpath(mkdtemp())
    cwd = os.getcwd()
    os.chdir(outdir)
    filelist = ['a.nii', 'b.nii']
    for f in filelist:
        hdr = nb.Nifti1Header()
        shape = (3, 3, 3, 4)
        hdr.set_data_shape(shape)
        img = np.random.random(shape)
        nb.save(nb.Nifti1Image(img, np.eye(4), hdr),
                 os.path.join(outdir, f))

    with open(os.path.join(outdir, 'reg.dat'), 'wt') as fp:
        fp.write('dummy file')
    filelist.append('reg.dat')

    def clean_directory():
        if os.path.exists(outdir):
            rmtree(outdir)
        os.chdir(cwd)

    request.addfinalizer(clean_directory)
    return (filelist, outdir)


@pytest.fixture()
def create_surf_file_in_directory(request):
    outdir = os.path.realpath(mkdtemp())
    cwd = os.getcwd()
    os.chdir(outdir)
    surf = 'lh.a.nii'
    hdr = nif.Nifti1Header()
    shape = (1, 100, 1)
    hdr.set_data_shape(shape)
    img = np.random.random(shape)
    nif.save(nif.Nifti1Image(img, np.eye(4), hdr),
             os.path.join(outdir, surf))

    def clean_directory():
        if os.path.exists(outdir):
            rmtree(outdir)
        os.chdir(cwd)

    request.addfinalizer(clean_directory)
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
def create_files_in_directory_plus_output_type(request):
    func_prev_type = set_output_type(request.param)

    testdir = os.path.realpath(mkdtemp())
    origdir = os.getcwd()
    os.chdir(testdir)

    filelist = ['a.nii', 'b.nii']
    for f in filelist:
        hdr = nb.Nifti1Header()
        shape = (3, 3, 3, 4)
        hdr.set_data_shape(shape)
        img = np.random.random(shape)
        nb.save(nb.Nifti1Image(img, np.eye(4), hdr),
                os.path.join(testdir, f))

    out_ext = Info.output_type_to_ext(Info.output_type())

    def fin():
        if os.path.exists(testdir):
            rmtree(testdir)
        set_output_type(func_prev_type)
        os.chdir(origdir)

    request.addfinalizer(fin)
    return (filelist, testdir, out_ext)
