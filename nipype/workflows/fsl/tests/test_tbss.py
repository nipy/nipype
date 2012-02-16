# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from nipype.interfaces.fsl.base import no_fsl, no_fsl_course_data
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
from nipype.testing import skipif
import tempfile
import shutil
from subprocess import call
from nipype.workflows.fsl.tbss import create_tbss_1_preproc
import nipype.interfaces.io as nio           # Data i/o


@skipif(no_fsl)
@skipif(no_fsl_course_data)
def test_tbss1():
    fsl_course_dir = os.environ["FSL_COURSE_DATA"]
    test_dir = tempfile.mkdtemp(prefix="nipype_test_tbss1")
    os.mkdir(os.path.join(test_dir, "tbss1_original"))
    old_dir = os.getcwd()
    os.chdir(os.path.join(test_dir, "tbss1_original"))
    subjects = ['1260', '1549', '1636', '1651', '2078', '2378']
    FA_list = [os.path.join(fsl_course_dir, 'fsl_course_data/tbss/', subject_id + '.nii.gz') for subject_id in subjects]

    for file in FA_list:
        shutil.copy(file, os.getcwd())

    call(['tbss_1_preproc'] + [subject_id + '.nii.gz' for subject_id in subjects], env=os.environ.update({'FSLOUTPUTTYPE':'NIFTI'}))

    pipeline = pe.Workflow(name="test_tbss1")
    pipeline.base_dir = os.path.join(test_dir, "tbss1_nipype")

    tbss1 = create_tbss_1_preproc()
    tbss1.inputs.inputnode.fa_list = FA_list

    tbss_original_datasource = pe.Node(nio.DataGrabber(outfields=['fa_list', 'mask_list']), name='tbss_original_datasource')
    tbss_original_datasource.inputs.base_directory = os.path.join(test_dir, "tbss1_original")
    tbss_original_datasource.inputs.template = 'FA/%s_FA%s.nii'
    tbss_original_datasource.inputs.template_args = dict(fa_list=[[subjects, '']],
                                                         mask_list=[[subjects, '_mask']])
    test_fa = pe.MapNode(util.AssertEqual(), name="tbss1_fa_test", iterfield=['volume1', 'volume2'])
    test_mask = pe.MapNode(util.AssertEqual(), name="tbss1_mask_test", iterfield=['volume1', 'volume2'])

    pipeline.connect(tbss1, 'outputnode.fa_list', test_fa, 'volume1')
    pipeline.connect(tbss1, 'outputnode.mask_list', test_mask, 'volume1')
    pipeline.connect(tbss_original_datasource, 'fa_list', test_fa, 'volume2')
    pipeline.connect(tbss_original_datasource, 'mask_list', test_mask, 'volume2')

    pipeline.run(plugin='Linear')

    os.chdir(old_dir)
    shutil.rmtree(test_dir)
