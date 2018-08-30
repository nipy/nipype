# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from nipype.interfaces.fsl.base import no_fsl, no_fsl_course_data
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import pytest
import tempfile
import shutil
from subprocess import call
from nipype.workflows.dmri.fsl.tbss import create_tbss_all
import nipype.interfaces.io as nio
from nipype.interfaces import fsl


def _tbss_test_helper(estimate_skeleton):
    fsl_course_dir = os.path.abspath(os.environ['FSL_COURSE_DATA'])
    fsl.FSLCommand.set_default_output_type('NIFTI_GZ')
    test_dir = tempfile.mkdtemp(prefix="nipype_test_tbss_")
    tbss_orig_dir = os.path.join(test_dir, "tbss_all_original")
    os.mkdir(tbss_orig_dir)
    old_dir = os.getcwd()
    os.chdir(tbss_orig_dir)

    subjects = ['1260', '1549']
    FA_list = [
        os.path.join(fsl_course_dir, 'tbss', subject_id + '.nii.gz')
        for subject_id in subjects
    ]
    for f in FA_list:
        shutil.copy(f, os.getcwd())

    call(
        ['tbss_1_preproc'] +
        [subject_id + '.nii.gz' for subject_id in subjects],
        env=os.environ.update({
            'FSLOUTPUTTYPE': 'NIFTI_GZ'
        }))
    tbss1_orig_dir = os.path.join(test_dir, "tbss1_original")
    shutil.copytree(tbss_orig_dir, tbss1_orig_dir)

    call(
        ['tbss_2_reg', '-T'],
        env=os.environ.update({
            'FSLOUTPUTTYPE': 'NIFTI_GZ'
        }))
    tbss2_orig_dir = os.path.join(test_dir, "tbss2_original")
    shutil.copytree(tbss_orig_dir, tbss2_orig_dir)

    if estimate_skeleton:
        call(
            ['tbss_3_postreg', '-S'],
            env=os.environ.update({
                'FSLOUTPUTTYPE': 'NIFTI_GZ'
            }))
    else:
        call(
            ['tbss_3_postreg', '-T'],
            env=os.environ.update({
                'FSLOUTPUTTYPE': 'NIFTI_GZ'
            }))
    tbss3_orig_dir = os.path.join(test_dir, "tbss3_original")
    shutil.copytree(tbss_orig_dir, tbss3_orig_dir)

    call(
        ['tbss_4_prestats', '0.2'],
        env=os.environ.update({
            'FSLOUTPUTTYPE': 'NIFTI_GZ'
        }))
    tbss4_orig_dir = os.path.join(test_dir, "tbss4_original")
    shutil.copytree(tbss_orig_dir, tbss4_orig_dir)

    pipeline = pe.Workflow(name="test_tbss")
    pipeline.base_dir = os.path.join(test_dir, "tbss_nipype")

    tbss = create_tbss_all(estimate_skeleton=estimate_skeleton)
    tbss.inputs.inputnode.fa_list = FA_list
    tbss.inputs.inputnode.skeleton_thresh = 0.2

    tbss1_original_datasource = pe.Node(
        nio.DataGrabber(
            outfields=['fa_list', 'mask_list'], sort_filelist=False),
        name='tbss1_original_datasource')
    tbss1_original_datasource.inputs.base_directory = tbss1_orig_dir
    tbss1_original_datasource.inputs.template = 'FA/%s_FA%s.nii.gz'
    tbss1_original_datasource.inputs.template_args = dict(
        fa_list=[[subjects, '']], mask_list=[[subjects, '_mask']])

    tbss1_test_fa = pe.MapNode(
        util.AssertEqual(),
        name="tbss1_fa_test",
        iterfield=['volume1', 'volume2'])
    tbss1_test_mask = pe.MapNode(
        util.AssertEqual(),
        name="tbss1_mask_test",
        iterfield=['volume1', 'volume2'])

    pipeline.connect(tbss, 'tbss1.outputnode.fa_list', tbss1_test_fa,
                     'volume1')
    pipeline.connect(tbss, 'tbss1.outputnode.mask_list', tbss1_test_mask,
                     'volume1')
    pipeline.connect(tbss1_original_datasource, 'fa_list', tbss1_test_fa,
                     'volume2')
    pipeline.connect(tbss1_original_datasource, 'mask_list', tbss1_test_mask,
                     'volume2')
    tbss2_original_datasource = pe.Node(
        nio.DataGrabber(outfields=['field_list'], sort_filelist=False),
        name='tbss2_original_datasource')

    tbss2_original_datasource.inputs.base_directory = tbss2_orig_dir
    tbss2_original_datasource.inputs.template = 'FA/%s_FA%s.nii.gz'
    tbss2_original_datasource.inputs.template_args = dict(
        field_list=[[subjects, '_to_target_warp']])
    tbss2_test_field = pe.MapNode(
        util.AssertEqual(),
        name="tbss2_test_field",
        iterfield=['volume1', 'volume2'])

    pipeline.connect(tbss, 'tbss2.outputnode.field_list', tbss2_test_field,
                     'volume1')
    pipeline.connect(tbss2_original_datasource, 'field_list', tbss2_test_field,
                     'volume2')

    tbss3_original_datasource = pe.Node(
        nio.DataGrabber(
            outfields=[
                'groupmask', 'skeleton_file', 'meanfa_file', 'mergefa_file'
            ],
            sort_filelist=False),
        name='tbss3_original_datasource')
    tbss3_original_datasource.inputs.base_directory = tbss3_orig_dir
    tbss3_original_datasource.inputs.template = 'stats/%s.nii.gz'
    tbss3_original_datasource.inputs.template_args = dict(
        groupmask=[['mean_FA_mask']],
        skeleton_file=[['mean_FA_skeleton']],
        meanfa_file=[['mean_FA']],
        mergefa_file=[['all_FA']])

    tbss3_test_groupmask = pe.Node(
        util.AssertEqual(), name="tbss3_test_groupmask")
    tbss3_test_skeleton_file = pe.Node(
        util.AssertEqual(), name="tbss3_test_skeleton_file")
    tbss3_test_meanfa_file = pe.Node(
        util.AssertEqual(), name="tbss3_test_meanfa_file")
    tbss3_test_mergefa_file = pe.Node(
        util.AssertEqual(), name="tbss3_test_mergefa_file")

    pipeline.connect(tbss, 'tbss3.outputnode.groupmask', tbss3_test_groupmask,
                     'volume1')
    pipeline.connect(tbss3_original_datasource, 'groupmask',
                     tbss3_test_groupmask, 'volume2')
    pipeline.connect(tbss, 'tbss3.outputnode.skeleton_file',
                     tbss3_test_skeleton_file, 'volume1')
    pipeline.connect(tbss3_original_datasource, 'skeleton_file',
                     tbss3_test_skeleton_file, 'volume2')
    pipeline.connect(tbss, 'tbss3.outputnode.meanfa_file',
                     tbss3_test_meanfa_file, 'volume1')
    pipeline.connect(tbss3_original_datasource, 'meanfa_file',
                     tbss3_test_meanfa_file, 'volume2')
    pipeline.connect(tbss, 'tbss3.outputnode.mergefa_file',
                     tbss3_test_mergefa_file, 'volume1')
    pipeline.connect(tbss3_original_datasource, 'mergefa_file',
                     tbss3_test_mergefa_file, 'volume2')

    tbss4_original_datasource = pe.Node(
        nio.DataGrabber(
            outfields=['all_FA_skeletonised', 'mean_FA_skeleton_mask'],
            sort_filelist=False),
        name='tbss4_original_datasource')
    tbss4_original_datasource.inputs.base_directory = tbss4_orig_dir
    tbss4_original_datasource.inputs.template = 'stats/%s.nii.gz'
    tbss4_original_datasource.inputs.template_args = dict(
        all_FA_skeletonised=[['all_FA_skeletonised']],
        mean_FA_skeleton_mask=[['mean_FA_skeleton_mask']])
    tbss4_test_all_FA_skeletonised = pe.Node(
        util.AssertEqual(), name="tbss4_test_all_FA_skeletonised")
    tbss4_test_mean_FA_skeleton_mask = pe.Node(
        util.AssertEqual(), name="tbss4_test_mean_FA_skeleton_mask")

    pipeline.connect(tbss, 'tbss4.outputnode.projectedfa_file',
                     tbss4_test_all_FA_skeletonised, 'volume1')
    pipeline.connect(tbss4_original_datasource, 'all_FA_skeletonised',
                     tbss4_test_all_FA_skeletonised, 'volume2')
    pipeline.connect(tbss, 'tbss4.outputnode.skeleton_mask',
                     tbss4_test_mean_FA_skeleton_mask, 'volume1')
    pipeline.connect(tbss4_original_datasource, 'mean_FA_skeleton_mask',
                     tbss4_test_mean_FA_skeleton_mask, 'volume2')

    pipeline.run(plugin='Linear')
    os.chdir(old_dir)
    shutil.rmtree(test_dir)


# this test is disabled until we figure out what is wrong with TBSS in 5.0.9


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
@pytest.mark.skipif(no_fsl_course_data(), reason="fsl data not available")
def test_disabled_tbss_est_skeleton():
    _tbss_test_helper(True)


# this test is disabled until we figure out what is wrong with TBSS in 5.0.9


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
@pytest.mark.skipif(no_fsl_course_data(), reason="fsl data not available")
def test_disabled_tbss_est_skeleton_use_precomputed_skeleton():
    _tbss_test_helper(False)
