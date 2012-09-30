#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
==================================
sMRI: Using ANTS for registration
==================================

In this simple tutorial we will use the Registration interface from ANTS to
coregister two T1 volumes.

1. Tell python where to find the appropriate functions.
"""

import os
import urllib2
from nipype.interfaces.ants import Registration

"""
2. Download T1 volumes into home directory
"""

homeDir=os.getenv("HOME")
requestedPath=os.path.join(homeDir,'nipypeTestPath')
mydatadir=os.path.realpath(requestedPath)
if not os.path.exists(mydatadir):
    os.makedirs(mydatadir)
print mydatadir

MyFileURLs=[
           ('http://slicer.kitware.com/midas3/download?bitstream=13121','01_T1_half.nii.gz'),
           ('http://slicer.kitware.com/midas3/download?bitstream=13122','02_T1_half.nii.gz'),
           ]
for tt in MyFileURLs:
    myURL=tt[0]
    localFilename=os.path.join(mydatadir,tt[1])
    if not os.path.exists(localFilename):
        remotefile = urllib2.urlopen(myURL)

        localFile = open(localFilename, 'wb')
        localFile.write(remotefile.read())
        localFile.close()
        print("Downloaded file: {0}".format(localFilename))
    else:
        print("File previously downloaded {0}".format(localFilename))

input_images=[
os.path.join(mydatadir,'01_T1_half.nii.gz'),
os.path.join(mydatadir,'02_T1_half.nii.gz'),
]

"""
3. Define the parameters of the registration
"""

reg = Registration()
reg.inputs.fixed_image =  [input_images[0], input_images[0] ]
reg.inputs.moving_image = [input_images[1], input_images[1] ]
reg.inputs.transforms = ['Affine', 'SyN']
reg.inputs.transform_parameters = [(2.0,), (0.25, 3.0, 0.0)]
reg.inputs.number_of_iterations = [[1500, 200], [100, 50, 30]]
reg.inputs.dimension = 3
reg.inputs.write_composite_transform = True
reg.inputs.metric = ['Mattes']*2
reg.inputs.metric_weight = [1]*2 # Default (value ignored currently by ANTs)
reg.inputs.radius_or_number_of_bins = [32]*2
reg.inputs.sampling_strategy = ['Random', None]
reg.inputs.sampling_percentage = [0.05, None]
reg.inputs.convergence_threshold = [1.e-8, 1.e-9]
reg.inputs.convergence_window_size = [20]*2
reg.inputs.smoothing_sigmas = [[1,0], [2,1,0]]
reg.inputs.shrink_factors = [[2,1], [3,2,1]]
reg.inputs.use_estimate_learning_rate_once = [True, True]
reg.inputs.use_histogram_matching = [True, True] # This is the default
reg.inputs.output_transform_prefix = 'thisTransform'
reg.inputs.output_warped_image = 'INTERNAL_WARPED.nii.gz'
reg.cmdline


"""
3. Run the registration
"""

reg.run()
