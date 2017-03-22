# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyseg import (no_niftyseg, get_custom_path,
                                        LabelFusion)
from nipype.testing import skipif, example_data
import os
import pytest


@skipif(no_niftyseg(cmd='seg_LabFusion'))
def test_steps():

    # Create a node object
    steps = LabelFusion()

    # Check if the command is properly defined
    assert steps.cmd == get_custom_path('seg_LabFusion')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        steps.run()

    # Assign some input data
    in_file = example_data('im1.nii')
    file_to_seg = example_data('im2.nii')
    template_file = example_data('im3.nii')
    steps.inputs.in_file = in_file
    steps.inputs.kernel_size = 2.0
    steps.inputs.file_to_seg = file_to_seg
    steps.inputs.template_file = template_file
    steps.inputs.template_num = 2
    steps.inputs.classifier_type = 'STEPS'

    cmd_tmp = '{cmd} -in {in_file} -STEPS 2.000000 2 {file_to_seg} \
{template_file} -out {out_file}'
    expected_cmd = cmd_tmp.format(
                        cmd=get_custom_path('seg_LabFusion'),
                        in_file=in_file,
                        file_to_seg=file_to_seg,
                        template_file=template_file,
                        out_file=os.path.join(os.getcwd(), 'im1_steps.nii'))

    assert steps.cmdline == expected_cmd


@skipif(no_niftyseg(cmd='seg_LabFusion'))
def test_staple():

    # Create a node object
    staple = LabelFusion()

    # Check if the command is properly defined
    assert staple.cmd == get_custom_path('seg_LabFusion')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        staple.run()

    # Assign some input data
    in_file = example_data('im1.nii')
    file_to_seg = example_data('im2.nii')
    template_file = example_data('im3.nii')
    staple.inputs.in_file = in_file
    staple.inputs.kernel_size = 2.0
    staple.inputs.file_to_seg = file_to_seg
    staple.inputs.template_file = template_file
    staple.inputs.template_num = 2
    staple.inputs.classifier_type = 'STAPLE'

    cmd_tmp = '{cmd} -in {in_file} -STAPLE -ALL -out {out_file}'
    expected_cmd = cmd_tmp.format(
                        cmd=get_custom_path('seg_LabFusion'),
                        in_file=in_file,
                        file_to_seg=file_to_seg,
                        template_file=template_file,
                        out_file=os.path.join(os.getcwd(), 'im1_staple.nii'))

    assert staple.cmdline == expected_cmd


@skipif(no_niftyseg(cmd='seg_LabFusion'))
def test_mv():

    # Create a node object
    mv = LabelFusion()

    # Check if the command is properly defined
    assert mv.cmd == get_custom_path('seg_LabFusion')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        mv.run()

    # Assign some input data
    in_file = example_data('im1.nii')
    file_to_seg = example_data('im2.nii')
    template_file = example_data('im3.nii')
    mv.inputs.in_file = in_file
    mv.inputs.file_to_seg = file_to_seg
    mv.inputs.template_file = template_file
    mv.inputs.template_num = 2
    mv.inputs.classifier_type = 'MV'
    mv.inputs.sm_ranking = 'ROINCC'
    mv.inputs.dilation_roi = 2

    cmd_tmp = '{cmd} -in {in_file} -MV -ROINCC 2 2 {file_to_seg} \
{template_file} -out {out_file}'
    expected_cmd = cmd_tmp.format(
                        cmd=get_custom_path('seg_LabFusion'),
                        in_file=in_file,
                        file_to_seg=file_to_seg,
                        template_file=template_file,
                        out_file=os.path.join(os.getcwd(), 'im1_mv.nii'))

    assert mv.cmdline == expected_cmd
