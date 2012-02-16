# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""A pipeline that uses several interfaces to perform tbss_non_FA.

"""

import os                                    # system functions
import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
from nipype.workflows.fsl import tbss_nonFA

"""Specify the related directories

"""

sessDir = '/nfs/s2/dticenter/data4test/tbss/mydata'
subject_list = ['S0001', 'S0005', 'S0036', 'S0038', 'S0085', 'S0099', 'S0004', 'S0032', 'S0037', 'S0057', 'S0098']
tbssDir = '/nfs/s2/dticenter/data4test/tbss/tbss_test_workingdir'
skeleton_thr = 0.2
nonFA = 'AD'#'AD'/'RD'/'MD'/'MO'/...('L1'/'L2'/'L3')
if nonFA == 'AD':
    updir = 'forAD'
elif nonFA == 'RD':
    updir = 'forRD'
elif nonFA == 'MD' or nonFA == 'MO':
    updir = 'dtifit'
else:
    print 'nonFA must be AD or RD or MD or MO(not zero)!'

#pluginName = 'IPython'

"""Here we get the FA list including all the subjects.

"""
def get_nonFAList(subject_list):
    file_list = []
    for subject_id in subject_list:
        file_list.append(os.path.join(sessDir, subject_id + '_' + nonFA)
                        )
    return file_list
def getfieldList(subject_list):
    field_list = []
    index = 0
    for subject_id in subject_list:
        field_list.append(os.path.join(tbssDir, 
                                    'tbssproc/tbss_all/tbss2/fnirt/mapflow',
                                    '_fnirt' + str(index),
                                    subject_id + '_FA_prep_fieldwarp')
                        )
        index = index+1
    return field_list

tbss_source = pe.Node(interface=nio.DataGrabber(outfiles=['file_list', 
                                                        'field_list']), 
                    name='tbss_source')
tbss_source.inputs.base_directory = os.path.abspath('/')
tbss_source.inputs.template = '%s.nii.gz'
tbss_source.inputs.template_args = dict(
                                    file_list=[[get_nonFAList(subject_list)]],
                                    field_list = [[getfieldList(subject_list)]]
                                    )

'''TBSS analysis

'''
tbss_nonFA = tbss_nonFA.create_tbss_non_FA(name='tbss_'+nonFA)
tbss_nonFA.inputs.inputnode.target = fsl.Info.standard_image("FMRIB58_FA_1mm.nii.gz")
tbss_nonFA.inputs.inputnode.skeleton_thresh = skeleton_thr
tbss_nonFA.inputs.inputnode.merged_file = 'all_'+nonFA+'.nii.gz'
tbss_nonFA.inputs.inputnode.mean_FA_mask = os.path.join(tbssDir,
                       'tbssproc/tbss_all/tbss3/groupmask/all_FA_mask.nii.gz')
tbss_nonFA.inputs.inputnode.meanfa_file = os.path.join(tbssDir,
                   'tbssproc/tbss_all/tbss3/meanfa/all_FA_masked_mean.nii.gz')
tbss_nonFA.inputs.inputnode.distance_map = os.path.join(tbssDir,
          'tbssproc/tbss_all/tbss4/distancemap/all_FA_mask_inv_dstmap.nii.gz')

tbss_nonFA_proc = pe.Workflow(name="tbss_"+nonFA+"_proc")
tbss_nonFA_proc.base_dir = os.path.abspath(tbssDir)
tbss_nonFA_proc.connect([
            (tbss_source, tbss_nonFA,[('file_list', 'inputnode.file_list'),
                                        ('field_list', 'inputnode.field_list')
                                        ]),
            ])


if __name__=='__main__':
    tbss_nonFA_proc.run()
    #tbss_nonFA_proc.write_graph()
