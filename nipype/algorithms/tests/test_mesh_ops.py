# -*- coding: utf-8 -*-
# coding: utf-8
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os

import pytest
import nipype.testing as npt
from nipype.testing import example_data
import numpy as np
from nipype.algorithms import mesh as m
from ...interfaces import vtkbase as VTKInfo


@pytest.mark.skipif(VTKInfo.no_tvtk(), reason="tvtk is not installed")
def test_ident_distances(tmpdir):
    tmpdir.chdir()

    in_surf = example_data('surf01.vtk')
    dist_ident = m.ComputeMeshWarp()
    dist_ident.inputs.surface1 = in_surf
    dist_ident.inputs.surface2 = in_surf
    dist_ident.inputs.out_file = tmpdir.join('distance.npy').strpath
    res = dist_ident.run()
    assert res.outputs.distance == 0.0

    dist_ident.inputs.weighting = 'area'
    res = dist_ident.run()
    assert res.outputs.distance == 0.0


@pytest.mark.skipif(VTKInfo.no_tvtk(), reason="tvtk is not installed")
def test_trans_distances(tmpdir):
    from ...interfaces.vtkbase import tvtk

    in_surf = example_data('surf01.vtk')
    warped_surf = tmpdir.join('warped.vtk').strpath

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
    dist.inputs.out_file = tmpdir.join('distance.npy').strpath
    res = dist.run()
    assert np.allclose(res.outputs.distance, np.linalg.norm(inc), 4)
    dist.inputs.weighting = 'area'
    res = dist.run()
    assert np.allclose(res.outputs.distance, np.linalg.norm(inc), 4)


@pytest.mark.skipif(VTKInfo.no_tvtk(), reason="tvtk is not installed")
def test_warppoints(tmpdir):
    tmpdir.chdir()

    # TODO: include regression tests for when tvtk is installed


@pytest.mark.skipif(VTKInfo.no_tvtk(), reason="tvtk is not installed")
def test_meshwarpmaths(tmpdir):
    tmpdir.chdir()

    # TODO: include regression tests for when tvtk is installed


@pytest.mark.skipif(not VTKInfo.no_tvtk(), reason="tvtk is installed")
def test_importerror():
    with pytest.raises(ImportError):
        m.ComputeMeshWarp()

    with pytest.raises(ImportError):
        m.WarpPoints()

    with pytest.raises(ImportError):
        m.MeshWarpMaths()
