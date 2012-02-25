# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
================================
rc-fMRI - FSL, Nipype, tCompCorr
================================

Performs preprocessing for resting state data based on the tCompCorr method
described in Behzadi et al. (2007).

Tell python where to find the appropriate functions.
"""

import os                                    # system functions

import nipype.interfaces.io as nio           # Data i/o
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.utility as util

#####################################################################
# Preliminaries

from nipype.workflows.fmri.fsl import create_resting_preproc

"""
Set up parameters for the resting state preprocessing workflow.
"""

TR = 3.0
restingflow = create_resting_preproc()
restingflow.inputs.inputspec.num_noise_components = 6
restingflow.inputs.inputspec.highpass_sigma = 100/(2*TR)
restingflow.inputs.inputspec.lowpass_sigma = 12.5/(2*TR)

# Specify the location of the data.
data_dir = os.path.abspath('data')
# Specify the subject directories
subject_list = ['s1']

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                     name="infosource")

"""Here we set up iteration over all the subjects.
"""

infosource.iterables = ('subject_id', subject_list)

"""
Preprocessing pipeline nodes
----------------------------

Now we create a :class:`nipype.interfaces.io.DataSource` object and
fill in the information from above about the layout of our data.
"""

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=['func', 'struct']),
                     name = 'datasource')
datasource.inputs.base_directory = data_dir
datasource.inputs.template = '%s/%s.nii'

# Map field names to individual subject runs.
info = dict(func=[['subject_id', ['f3',]]])

datasource.inputs.template_args = info

"""
Store significant result-files in a special directory
"""

datasink = pe.Node(interface=nio.DataSink(parameterization=False),
                   name='datasink')
datasink.inputs.base_directory = os.path.abspath('./fslresting/compcorred')

"""
Set up complete workflow
------------------------
"""

def get_substitutions(subject_id):
    '''Replace output names of files with more meaningful ones
    '''
    return [('vol0000_warp_merged_detrended_regfilt_filt',
             '%s_filtered'%subject_id),
            ('vol0000_warp_merged_tsnr_stddev_thresh',
             '%s_noisyvoxels'%subject_id)]

l1pipeline = pe.Workflow(name= "resting")
l1pipeline.base_dir = os.path.abspath('./fslresting/workingdir')
l1pipeline.connect([(infosource, datasource, [('subject_id', 'subject_id')]),
                    (datasource, restingflow, [('func', 'inputspec.func')]),
                    (infosource, datasink, [('subject_id', 'container'),
                                            (('subject_id', get_substitutions),
                                              'substitutions')]),
                    (restingflow, datasink, [('outputspec.noise_mask_file',
                                              '@noisefile'),
                                              ('outputspec.filtered_file',
                                               '@filteredfile')])
                    ])

if __name__ == '__main__':
    l1pipeline.run()
    l1pipeline.write_graph()
