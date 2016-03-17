# coding: utf-8
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from shutil import rmtree
from tempfile import mkdtemp

from nipype.testing import (assert_equal, assert_raises, skipif,
                            assert_almost_equal, example_data)
import numpy as np
from nipype.algorithms import mesh as m
from ...interfaces import vtkbase as VTKInfo


def test_ident_distances():
    tempdir = mkdtemp()
    curdir = os.getcwd()
    os.chdir(tempdir)

    if VTKInfo.no_tvtk():
        yield assert_raises, ImportError, m.ComputeMeshWarp
    else:
        in_surf = example_data('surf01.vtk')
        dist_ident = m.ComputeMeshWarp()
        dist_ident.inputs.surface1 = in_surf
        dist_ident.inputs.surface2 = in_surf
        dist_ident.inputs.out_file = os.path.join(tempdir, 'distance.npy')
        res = dist_ident.run()
        yield assert_equal, res.outputs.distance, 0.0

        dist_ident.inputs.weighting = 'area'
        res = dist_ident.run()
        yield assert_equal, res.outputs.distance, 0.0

    os.chdir(curdir)
    rmtree(tempdir)


def test_trans_distances():
    tempdir = mkdtemp()
    curdir = os.getcwd()
    os.chdir(tempdir)

    if VTKInfo.no_tvtk():
        yield assert_raises, ImportError, m.ComputeMeshWarp
    else:
        from ...interfaces.vtkbase import tvtk

        in_surf = example_data('surf01.vtk')
        warped_surf = os.path.join(tempdir, 'warped.vtk')

        inc = np.array([0.7, 0.3, -0.2])

        r1 = tvtk.PolyDataReader(file_name=in_surf)
        vtk1 = VTKInfo.vtk_output(r1)
        r1.update()
        vtk1.points = np.array(vtk1.points) + inc

        writer = tvtk.PolyDataWriter(file_name=warped_surf)
        VTKInfo.configure_input_data(writer, vtk1)
        writer.write()

        dist = m.ComputeMeshWarp()
        dist.inputs.surface1 = in_surf
        dist.inputs.surface2 = warped_surf
        dist.inputs.out_file = os.path.join(tempdir, 'distance.npy')
        res = dist.run()
        yield assert_almost_equal, res.outputs.distance, np.linalg.norm(inc), 4
        dist.inputs.weighting = 'area'
        res = dist.run()
        yield assert_almost_equal, res.outputs.distance, np.linalg.norm(inc), 4

    os.chdir(curdir)
    rmtree(tempdir)


def test_warppoints():
    tempdir = mkdtemp()
    curdir = os.getcwd()
    os.chdir(tempdir)

    if VTKInfo.no_tvtk():
        yield assert_raises, ImportError, m.WarpPoints

    # TODO: include regression tests for when tvtk is installed

    os.chdir(curdir)
    rmtree(tempdir)


def test_meshwarpmaths():
    tempdir = mkdtemp()
    curdir = os.getcwd()
    os.chdir(tempdir)

    if VTKInfo.no_tvtk():
        yield assert_raises, ImportError, m.MeshWarpMaths

    # TODO: include regression tests for when tvtk is installed

    os.chdir(curdir)
    rmtree(tempdir)
