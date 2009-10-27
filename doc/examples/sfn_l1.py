import os
from glob import glob

import nipype.interfaces.io as nio
import nipype.interfaces.fsl as fsl
import nipype.pipeline.node_wrapper as nw

data_dir = os.path.abspath('./nifti')
subject_list = ['sfn0%d' % i for i in range(1,8)]

info = {}
for s in subject_list:
    subj_dir = os.path.join(data_dir, 'l1output', s, 'registration')
    struct = glob(subj_dir + 't1_warped.nii.gz')
    func = sorted(glob(subj_dir + 'registered/ep2dneuro96*_smooth.nii.gz'))
    # events will be a list of lists of files
    events = []
    for i, f in enumerate(func):
        events.append(glob(os.path.join('block%d*' % i + 2)))
    info[s] = ((func, 'func'), (struct, 'struct'), (events, 'events'))

l1_datasource = nw.NodeWrapper(interface=nio.DataSource())
l1_datasource.inputs.update(base_directory = data_dir,
                            subject_template = '%s',
                            file_template = '%s',
                            subject_info = info)
l1_datasource.iterables = {'subject_id': lambda:subject_list}

cond_names = ['vibe-all-left',          
              'vibe-all-right',  
              'vibe-seq-left',   
              'vibe-seq-right',  
              'visual-all-left', 
              'visual-all-right',
              'visual-seq-left', 
              'visual-seq-right'] 
l1_feat = nw.NodeWrapper(fsl.L1FSFmaker(), diskbased=True)
l1_feat.inputs.update(num_scans=4,
                      cond_names=cond_names,
                      num_vols=198)
    

