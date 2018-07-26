from __future__ import division
from builtins import range
import nipype.pipeline.engine as pe
from nipype.interfaces import spm
from nipype.interfaces import fsl
from nipype.interfaces import utility as niu
from nipype.interfaces import io as nio
from nipype.algorithms.misc import Gunzip


def _get_first(inlist):
    if isinstance(inlist, (list, tuple)):
        return inlist[0]
    return inlist


def test_spm(name='test_spm_3d'):
    """
    A simple workflow to test SPM's installation. By default will split the 4D volume in
    time-steps.
    """
    workflow = pe.Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(fields=['in_data']), name='inputnode')
    dgr = pe.Node(
        nio.DataGrabber(
            template="feeds/data/fmri.nii.gz",
            outfields=['out_file'],
            sort_filelist=False),
        name='datasource')

    stc = pe.Node(
        spm.SliceTiming(
            num_slices=21,
            time_repetition=1.0,
            time_acquisition=2. - 2. / 32,
            slice_order=list(range(21, 0, -1)),
            ref_slice=10),
        name='stc')
    realign_estimate = pe.Node(
        spm.Realign(jobtype='estimate'), name='realign_estimate')
    realign_write = pe.Node(spm.Realign(jobtype='write'), name='realign_write')
    realign_estwrite = pe.Node(
        spm.Realign(jobtype='estwrite'), name='realign_estwrite')
    smooth = pe.Node(spm.Smooth(fwhm=[6, 6, 6]), name='smooth')

    if name == 'test_spm_3d':
        split = pe.Node(
            fsl.Split(dimension="t", output_type="NIFTI"), name="split")
        workflow.connect([(dgr, split, [(('out_file', _get_first),
                                         'in_file')]),
                          (split, stc, [("out_files", "in_files")])])
    elif name == 'test_spm_4d':
        gunzip = pe.Node(Gunzip(), name="gunzip")
        workflow.connect([(dgr, gunzip, [(('out_file', _get_first),
                                          'in_file')]),
                          (gunzip, stc, [("out_file", "in_files")])])
    else:
        raise NotImplementedError(
            'No implementation of the test workflow \'{}\' was found'.format(
                name))

    workflow.connect([(inputnode, dgr, [('in_data', 'base_directory')]),
                      (stc, realign_estimate,
                       [('timecorrected_files',
                         'in_files')]), (realign_estimate, realign_write,
                                         [('modified_in_files', 'in_files')]),
                      (stc, realign_estwrite,
                       [('timecorrected_files',
                         'in_files')]), (realign_write, smooth,
                                         [('realigned_files', 'in_files')])])
    return workflow


workflow3d = test_spm()
workflow4d = test_spm(name='test_spm_4d')
