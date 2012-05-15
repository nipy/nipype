import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
import os
from nipype.interfaces.freesurfer.preprocess import ReconAll
from nipype.interfaces.freesurfer.utils import MakeAverageSubject

subject_list = ['s1', 's3']
data_dir = os.path.abspath('data')
subjects_dir = os.path.abspath('amri_freesurfer_tutorial/subjects_dir')

wf = pe.Workflow(name="l1workflow")
wf.base_dir = os.path.abspath('amri_freesurfer_tutorial/workdir')

datasource = pe.MapNode(interface=nio.DataGrabber(infields=['subject_id'],
                                                  outfields=['struct']),
                        name='datasource',
                        iterfield=['subject_id'])
datasource.inputs.base_directory = data_dir
datasource.inputs.template = '%s/%s.nii'
datasource.inputs.template_args = dict(struct=[['subject_id', 'struct']])
datasource.inputs.subject_id = subject_list

recon_all = pe.MapNode(interface=ReconAll(), name='recon_all',
                       iterfield=['subject_id', 'T1_files'])
recon_all.inputs.subject_id = subject_list
if not os.path.exists(subjects_dir):
    os.mkdir(subjects_dir)
recon_all.inputs.subjects_dir = subjects_dir

wf.connect(datasource, 'struct', recon_all, 'T1_files')

average = pe.Node(interface=MakeAverageSubject(), name="average")
average.inputs.subjects_dir = subjects_dir

wf.connect(recon_all, 'subject_id', average, 'subjects_ids')

wf.run("MultiProc", plugin_args={'n_procs': 4})
