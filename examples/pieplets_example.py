from nipype.pipeline.pipelet import ComplexPipelet


"""Import necessary modules from nipype."""

import nipype.interfaces.io as nio           # Data i/o 
import nipype.interfaces.spm as spm          # spm
import nipype.interfaces.utility as util     # utility 
import nipype.pipeline.node_wrapper as nw    # nodes for pypelines
import os                                    # system functions

# Specify the location of the data.
data_dir = os.path.abspath('data')
# Specify the subject directories
subject_list = ['s1', 's3']
# Map field names to individual subject runs.
info = dict(func=[['subject_id', ['f3','f5','f7','f10']]],
            struct=[['subject_id','struct']])

infosource = util.IdentityInterface(fields=['subject_id'])
infosource.iterables = ('subject_id', subject_list)

datasource = nio.DataGrabber(infields=['subject_id'],outfields=['func', 'struct'], name="datasource")
datasource.inputs.base_directory = data_dir
datasource.inputs.template = '%s/%s.nii'
datasource.inputs.template_args = info

realign = spm.Realign()
realign.inputs.register_to_mean = True

l1pipeline = ComplexPipelet()
l1pipeline.config['workdir'] = os.path.abspath('spm/workingdir')

l1pipeline.connect([(infosource, datasource, [('subject_id', 'subject_id')]),
                  (datasource,realign,[('func','infile')])
                  ])

if __name__ == '__main__':
    l1pipeline.run()
