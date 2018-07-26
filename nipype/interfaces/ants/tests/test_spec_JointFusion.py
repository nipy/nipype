# -*- coding: utf-8 -*-
from __future__ import division
from builtins import range
from nipype.testing import example_data
from nipype.interfaces.base import InputMultiPath
from traits.trait_errors import TraitError
from nipype.interfaces.ants import JointFusion
import pytest


def test_JointFusion_dimension():
    at = JointFusion()
    set_dimension = lambda d: setattr(at.inputs, 'dimension', int(d))
    for d in range(2, 5):
        set_dimension(d)
        assert at.inputs.dimension == int(d)
    for d in [0, 1, 6, 7]:
        with pytest.raises(TraitError):
            set_dimension(d)


@pytest.mark.parametrize("m", range(1, 5))
def test_JointFusion_modalities(m):
    at = JointFusion()
    setattr(at.inputs, 'modalities', int(m))
    assert at.inputs.modalities == int(m)


@pytest.mark.parametrize("a, b",
                         [(a, b) for a in range(10) for b in range(10)])
def test_JointFusion_method(a, b):
    at = JointFusion()
    set_method = lambda a, b: setattr(at.inputs, 'method', 'Joint[%.1f,%d]'.format(a, b))
    _a = a / 10.0
    set_method(_a, b)
    # set directly
    assert at.inputs.method == 'Joint[%.1f,%d]'.format(_a, b)
    aprime = _a + 0.1
    bprime = b + 1
    at.inputs.alpha = aprime
    at.inputs.beta = bprime
    # set with alpha/beta
    assert at.inputs.method == 'Joint[%.1f,%d]'.format(aprime, bprime)


@pytest.mark.parametrize("attr, x",
                         [(attr, x)
                          for attr in ['patch_radius', 'search_radius']
                          for x in range(5)])
def test_JointFusion_radius(attr, x):
    at = JointFusion()
    setattr(at.inputs, attr, [x, x + 1, x**x])
    assert at._format_arg(attr, None, getattr(
        at.inputs, attr))[4:] == '{0}x{1}x{2}'.format(x, x + 1, x**x)


def test_JointFusion_cmd():
    at = JointFusion()
    at.inputs.dimension = 3
    at.inputs.modalities = 1
    at.inputs.method = 'Joint[0.1,2]'
    at.inputs.output_label_image = 'fusion_labelimage_output.nii'
    warped_intensity_images = [
        example_data('im1.nii'),
        example_data('im2.nii')
    ]
    at.inputs.warped_intensity_images = warped_intensity_images
    segmentation_images = [
        example_data('segmentation0.nii.gz'),
        example_data('segmentation1.nii.gz')
    ]
    at.inputs.warped_label_images = segmentation_images
    T1_image = example_data('T1.nii')
    at.inputs.target_image = T1_image
    at.inputs.patch_radius = [3, 2, 1]
    at.inputs.search_radius = [1, 2, 3]
    expected_command = ('jointfusion 3 1 -m Joint[0.1,2] -rp 3x2x1 -rs 1x2x3'
                        ' -tg %s -g %s -g %s -l %s -l %s'
                        ' fusion_labelimage_output.nii') % (
                            T1_image, warped_intensity_images[0],
                            warped_intensity_images[1], segmentation_images[0],
                            segmentation_images[1])
    assert at.cmdline == expected_command
    # setting intensity or labels with unequal lengths raises error
    with pytest.raises(AssertionError):
        at._format_arg('warped_intensity_images', InputMultiPath,
                       warped_intensity_images + [example_data('im3.nii')])
