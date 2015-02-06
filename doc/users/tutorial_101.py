# -*- coding: utf-8 -*-
import os
import nipype.interfaces.spm as spm         # the spm interfaces
import nipype.pipeline.engine as pe         # the workflow and node wrappers

import nipype.interfaces.matlab as mlab      # how to run matlab
# Path to matlab
mlab.MatlabCommand.set_default_matlab_cmd("/full/path/to/matlab_exe")
# Add SPM to MATLAB path if not present
mlab.MatlabCommand.set_default_paths("/full/path/to/spm")

#
# Define nodes
#

realigner = pe.Node(interface=spm.Realign(), name='realign')
realigner.inputs.in_files = os.abspath('somefuncrun.nii')
realigner.inputs.register_to_mean = True

smoother = pe.Node(interface=spm.Smooth(fwhm=6), name='smooth')

#
# Creating and configuring a workflow
#
workflow = pe.Workflow(name='preproc')
workflow.base_dir = '.'

#
# Connecting nodes to each other
#
workflow.connect(realigner, 'realigned_files', smoother, 'in_files')


#
# Visualizing the workflow
#
workflow.write_graph()

#
# Extend it
#
import nipype.algorithms.rapidart as ra
artdetect = pe.Node(interface=ra.ArtifactDetect(), name='artdetect')
artdetect.inputs.use_differences = [True, False]
artdetect.inputs.use_norm = True
artdetect.inputs.norm_threshold = 0.5
artdetect.inputs.zintensity_threshold = 3
artdetect.inputs.parameter_source = 'SPM'
artdetect.inputs.mask_type = 'spm_global'
workflow.connect([(realigner, artdetect,
                   [('realigned_files', 'realigned_files'),
                    ('realignment_parameters', 'realignment_parameters')]
                  )])
workflow.write_graph()

#
# Execute the workflow
#
workflow.run()
