#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
======================================================
sMRI: Using new ANTS for creating a T1 template (ITK4)
======================================================

In this tutorial we will use ANTS (new ITK4 version aka "antsRegistration") based workflow  to
create a template out of multiple T1 volumes. We will also showcase how to fine tune SGE jobs requirements.

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


"""
ListOfImagesDictionaries - a list of dictionaries where each dictionary is
for one scan session, and the mappings in the dictionary are for all the
co-aligned images for that one scan session
"""

ListOfImagesDictionaries=[
{'T1':os.path.join(mydatadir,'01_T1_half.nii.gz'),'INV_T1':os.path.join(mydatadir,'01_T1_inv_half.nii.gz'),'LABEL_MAP':os.path.join(mydatadir,'01_T1_inv_half.nii.gz')},
{'T1':os.path.join(mydatadir,'02_T1_half.nii.gz'),'INV_T1':os.path.join(mydatadir,'02_T1_inv_half.nii.gz'),'LABEL_MAP':os.path.join(mydatadir,'02_T1_inv_half.nii.gz')},
{'T1':os.path.join(mydatadir,'03_T1_half.nii.gz'),'INV_T1':os.path.join(mydatadir,'03_T1_inv_half.nii.gz'),'LABEL_MAP':os.path.join(mydatadir,'03_T1_inv_half.nii.gz')}
]
input_passive_images=[
{'INV_T1':os.path.join(mydatadir,'01_T1_inv_half.nii.gz')},
{'INV_T1':os.path.join(mydatadir,'02_T1_inv_half.nii.gz')},
{'INV_T1':os.path.join(mydatadir,'03_T1_inv_half.nii.gz')}
]

"""
registrationImageTypes - A list of the image types to be used actively during
the estimation process of registration, any image type not in this list
will be passively resampled with the estimated transforms.
['T1','T2']
"""

registrationImageTypes=['T1']

"""
interpolationMap - A map of image types to interpolation modes.  If an
image type is not listed, it will be linearly interpolated.
{ 'labelmap':'NearestNeighbor', 'FLAIR':'WindowedSinc' }
"""

interpolationMapping={'INV_T1':'LanczosWindowedSinc','LABEL_MAP':'NearestNeighbor','T1':'Linear'}

"""
3. Define the workflow and its working directory
"""

tbuilder=pe.Workflow(name="antsRegistrationTemplateBuilder")
tbuilder.base_dir=requestedPath

"""
4. Define data sources. In real life these would be replace by DataGrabbers
"""

InitialTemplateInputs=[ mdict['T1'] for mdict in ListOfImagesDictionaries ]

datasource = pe.Node(interface=util.IdentityInterface(fields=
                    ['InitialTemplateInputs', 'ListOfImagesDictionaries',
                     'registrationImageTypes','interpolationMapping']),
                    run_without_submitting=True,
                    name='InputImages' )
datasource.inputs.InitialTemplateInputs=InitialTemplateInputs
datasource.inputs.ListOfImagesDictionaries=ListOfImagesDictionaries
datasource.inputs.registrationImageTypes=registrationImageTypes
datasource.inputs.interpolationMapping=interpolationMapping

"""
5. Template is initialized by a simple average in this simple example,
   any reference image could be used (i.e. a previously created template)
"""

initAvg = pe.Node(interface=ants.AverageImages(), name ='initAvg')
initAvg.inputs.dimension = 3
initAvg.inputs.normalize = True

tbuilder.connect(datasource, "InitialTemplateInputs", initAvg, "images")

"""
6. Define the first iteration of template building
"""

buildTemplateIteration1=antsRegistrationTemplateBuildSingleIterationWF('iteration01')

"""
Here we are fine tuning parameters of the SGE job (memory limit, numebr of cores etc.)
"""

BeginANTS = buildTemplateIteration1.get_node("BeginANTS")
BeginANTS.plugin_args={'qsub_args': '-S /bin/bash -pe smp1 8-12 -l mem_free=6000M -o /dev/null -e /dev/null queue_name', 'overwrite': True}

tbuilder.connect(initAvg, 'output_average_image', buildTemplateIteration1, 'inputspec.fixed_image')
tbuilder.connect(datasource, 'ListOfImagesDictionaries', buildTemplateIteration1, 'inputspec.ListOfImagesDictionaries')
tbuilder.connect(datasource, 'registrationImageTypes', buildTemplateIteration1, 'inputspec.registrationImageTypes')
tbuilder.connect(datasource, 'interpolationMapping', buildTemplateIteration1, 'inputspec.interpolationMapping')

"""
7. Define the second iteration of template building
"""

buildTemplateIteration2 = antsRegistrationTemplateBuildSingleIterationWF('iteration02')
BeginANTS = buildTemplateIteration2.get_node("BeginANTS")
BeginANTS.plugin_args={'qsub_args': '-S /bin/bash -pe smp1 8-12 -l mem_free=6000M -o /dev/null -e /dev/null queue_name', 'overwrite': True}
tbuilder.connect(buildTemplateIteration1, 'outputspec.template', buildTemplateIteration2, 'inputspec.fixed_image')
tbuilder.connect(datasource, 'ListOfImagesDictionaries', buildTemplateIteration2, 'inputspec.ListOfImagesDictionaries')
tbuilder.connect(datasource, 'registrationImageTypes', buildTemplateIteration2, 'inputspec.registrationImageTypes')
tbuilder.connect(datasource, 'interpolationMapping', buildTemplateIteration2, 'inputspec.interpolationMapping')

"""
8. Move selected files to a designated results folder
"""

datasink = pe.Node(io.DataSink(), name="datasink")
datasink.inputs.base_directory = os.path.join(requestedPath, "results")

tbuilder.connect(buildTemplateIteration2, 'outputspec.template',datasink,'PrimaryTemplate')
tbuilder.connect(buildTemplateIteration2, 'outputspec.passive_deformed_templates',datasink,'PassiveTemplate')
tbuilder.connect(initAvg, 'output_average_image', datasink,'PreRegisterAverage')

"""
9. Run the workflow
"""

tbuilder.run(plugin="SGE")
