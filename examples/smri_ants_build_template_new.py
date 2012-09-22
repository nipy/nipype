#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
======================================================
sMRI: Using new ANTS for creating a T1 template (ITK4)
======================================================

In this tutorial we will use ANTS (new ITK4 version aka "antsRegistration") based workflow  to
create a template out of multiple T1 volumes.

1. Tell python where to find the appropriate functions.
"""

import os
import nipype.interfaces.utility as util
import nipype.interfaces.ants as ants
import nipype.interfaces.io as io
import nipype.pipeline.engine as pe  # pypeline engine

from nipype.workflows.smri.ants import antsRegistrationTemplateBuildSingleIterationWF

"""
2. Download T1 volumes into home directory
"""

import urllib2
homeDir=os.getenv("HOME")
requestedPath=os.path.join(homeDir,'nipypeTestPath')
mydatadir=os.path.realpath(requestedPath)
if not os.path.exists(mydatadir):
    os.makedirs(mydatadir)
print mydatadir

MyFileURLs=[
           ('http://slicer.kitware.com/midas3/download?bitstream=13121','01_T1_half.nii.gz'),
           ('http://slicer.kitware.com/midas3/download?bitstream=13122','02_T1_half.nii.gz'),
           ('http://slicer.kitware.com/midas3/download?bitstream=13124','03_T1_half.nii.gz'),
           ('http://slicer.kitware.com/midas3/download?bitstream=13128','01_T1_inv_half.nii.gz'),
           ('http://slicer.kitware.com/midas3/download?bitstream=13123','02_T1_inv_half.nii.gz'),
           ('http://slicer.kitware.com/midas3/download?bitstream=13125','03_T1_inv_half.nii.gz'),
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
os.path.join(mydatadir,'03_T1_half.nii.gz')
]
input_passive_images=[
{'INV_T1':os.path.join(mydatadir,'01_T1_inv_half.nii.gz')},
{'INV_T1':os.path.join(mydatadir,'02_T1_inv_half.nii.gz')},
{'INV_T1':os.path.join(mydatadir,'03_T1_inv_half.nii.gz')}
]


"""
3. Define the workflow and its working directory
"""
tbuilder=pe.Workflow(name="antsRegistrationTemplateBuilder")
tbuilder.base_dir=requestedPath

"""
4. Define data sources. In real life these would be replace by DataGrabbers
"""
datasource = pe.Node(interface=util.IdentityInterface(fields=
                    ['imageList', 'passiveImagesDictionariesList']),
                    run_without_submitting=True,
                    name='InputImages' )
datasource.inputs.imageList=input_images
datasource.inputs.passiveImagesDictionariesList=input_passive_images

"""
5. Template is initialized by a simple average
"""
initAvg = pe.Node(interface=ants.AverageImages(), name ='initAvg')
initAvg.inputs.dimension = 3
initAvg.inputs.normalize = True

tbuilder.connect(datasource, "imageList", initAvg, "images")

"""
6. Define the first iteration of template building
"""

buildTemplateIteration1=antsRegistrationTemplateBuildSingleIterationWF('iteration01')
tbuilder.connect(initAvg, 'output_average_image', buildTemplateIteration1, 'InputSpec.fixed_image')
tbuilder.connect(datasource, 'imageList', buildTemplateIteration1, 'InputSpec.images')
tbuilder.connect(datasource, 'passiveImagesDictionariesList', buildTemplateIteration1, 'InputSpec.ListOfPassiveImagesDictionaries')

"""
7. Define the second iteration of template building
"""

buildTemplateIteration2 = antsRegistrationTemplateBuildSingleIterationWF('iteration02')
tbuilder.connect(buildTemplateIteration1, 'OutputSpec.template', buildTemplateIteration2, 'InputSpec.fixed_image')
tbuilder.connect(datasource, 'imageList', buildTemplateIteration2, 'InputSpec.images')
tbuilder.connect(datasource, 'passiveImagesDictionariesList', buildTemplateIteration2, 'InputSpec.ListOfPassiveImagesDictionaries')

"""
8. Move selected files to a designated results folder
"""

datasink = pe.Node(io.DataSink(), name="datasink")
datasink.inputs.base_directory = os.path.join(requestedPath, "results")

tbuilder.connect(buildTemplateIteration2, 'OutputSpec.template',datasink,'PrimaryTemplate')
tbuilder.connect(buildTemplateIteration2, 'OutputSpec.passive_deformed_templates',datasink,'PassiveTemplate')
tbuilder.connect(initAvg, 'output_average_image', datasink,'PreRegisterAverage')

"""
8. Run the workflow
"""

tbuilder.run()
