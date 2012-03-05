#!/usr/bin/env python
"""
===============
dMRI [DTI, FSL]
===============

A pipeline example that uses several interfaces to perform analysis on
diffusion weighted images using FSL FDT tools.

This tutorial is based on the 2010 FSL course and uses data freely available at
the FSL website at: http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz

More details can be found at
http://www.fmrib.ox.ac.uk/fslcourse/lectures/practicals/fdt/index.htm

In order to run this tutorial you need to have fsl tools installed and
accessible from matlab/command line. Check by calling fslinfo from the command
line.

Tell python where to find the appropriate functions.
"""

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import os                                    # system functions
from nipype.workflows.dmri.fsl.dti import create_eddy_correct_pipeline,\
    create_bedpostx_pipeline

"""
Confirm package dependencies are installed.  (This is only for the
tutorial, rarely would you put this in your own code.)
"""

from nipype.utils.misc import package_check

package_check('numpy', '1.3', 'tutorial1')
package_check('scipy', '0.7', 'tutorial1')
package_check('networkx', '1.0', 'tutorial1')
package_check('IPython', '0.10', 'tutorial1')


"""
Setting up workflows
--------------------

This is a generic workflow for DTI data analysis using the FSL

Data specific components
------------------------

The nipype tutorial contains data for two subjects.  Subject data is in two
subdirectories, ``dwis1`` and ``dwis2``.  Each subject directory contains each
of the following files: bvec, bval, diffusion weighted data, a set of target
masks, a seed file, and a transformation matrix.

Below we set some variables to inform the ``datasource`` about the
layout of our data.  We specify the location of the data, the subject
sub-directories and a dictionary that maps each run to a mnemonic (or
field) for the run type (``dwi`` or ``bvals``).  These fields become
the output fields of the ``datasource`` node in the pipeline.

Specify the subject directories
"""

subject_list = ['subj1']


"""
Map field names to individual subject runs
"""

info = dict(dwi=[['subject_id', 'data']],
            bvecs=[['subject_id','bvecs']],
            bvals=[['subject_id','bvals']],
            seed_file = [['subject_id','MASK_average_thal_right']],
            target_masks = [['subject_id',['MASK_average_M1_right',
                                           'MASK_average_S1_right',
                                           'MASK_average_occipital_right',
                                           'MASK_average_pfc_right',
                                           'MASK_average_pmc_right',
                                           'MASK_average_ppc_right',
                                           'MASK_average_temporal_right']]])

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                     name="infosource")

"""
Here we set up iteration over all the subjects. The following line
is a particular example of the flexibility of the system.  The
``datasource`` attribute ``iterables`` tells the pipeline engine that
it should repeat the analysis on each of the items in the
``subject_list``. In the current example, the entire first level
preprocessing and estimation will be repeated for each subject
contained in subject_list.
"""

infosource.iterables = ('subject_id', subject_list)

"""
Now we create a :class:`nipype.interfaces.io.DataGrabber` object and
fill in the information from above about the layout of our data.  The
:class:`nipype.pipeline.engine.Node` module wraps the interface object
and provides additional housekeeping and pipeline specific
functionality.
"""

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=info.keys()),
                     name = 'datasource')

datasource.inputs.template = "%s/%s"

# This needs to point to the fdt folder you can find after extracting
# http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz
datasource.inputs.base_directory = os.path.abspath('fsl_course_data/fdt/')

datasource.inputs.field_template = dict(dwi='%s/%s.nii.gz',
                                        seed_file="%s.bedpostX/%s.nii.gz",
                                        target_masks="%s.bedpostX/%s.nii.gz")
datasource.inputs.template_args = info


"""
Setup for Diffusion Tensor Computation
--------------------------------------

Here we will create a generic workflow for DTI computation
"""

computeTensor = pe.Workflow(name='computeTensor')

"""
extract the volume with b=0 (nodif_brain)
"""

fslroi = pe.Node(interface=fsl.ExtractROI(),name='fslroi')
fslroi.inputs.t_min=0
fslroi.inputs.t_size=1

"""
create a brain mask from the nodif_brain
"""

bet = pe.Node(interface=fsl.BET(),name='bet')
bet.inputs.mask=True
bet.inputs.frac=0.34

"""
correct the diffusion weighted images for eddy_currents
"""

eddycorrect = create_eddy_correct_pipeline('eddycorrect')
eddycorrect.inputs.inputnode.ref_num=0

"""
compute the diffusion tensor in each voxel
"""

dtifit = pe.Node(interface=fsl.DTIFit(),name='dtifit')

"""
connect all the nodes for this workflow
"""

computeTensor.connect([
                        (fslroi,bet,[('roi_file','in_file')]),
                        (eddycorrect, dtifit,[('outputnode.eddy_corrected','dwi')]),
                        (infosource, dtifit,[['subject_id','base_name']]),
                        (bet,dtifit,[('mask_file','mask')])
                      ])



"""
Setup for Tracktography
-----------------------

Here we will create a workflow to enable probabilistic tracktography
and hard segmentation of the seed region
"""

tractography = pe.Workflow(name='tractography')
tractography.base_dir = os.path.abspath('fsl_dti_tutorial')

"""
estimate the diffusion parameters: phi, theta, and so on
"""

bedpostx = create_bedpostx_pipeline()
bedpostx.get_node("xfibres").iterables = ("n_fibres",[1,2])


flirt = pe.Node(interface=fsl.FLIRT(), name='flirt')
flirt.inputs.in_file = fsl.Info.standard_image('MNI152_T1_2mm_brain.nii.gz')
flirt.inputs.dof = 12

"""
perform probabilistic tracktography
"""

probtrackx = pe.Node(interface=fsl.ProbTrackX(),name='probtrackx')
probtrackx.inputs.mode='seedmask'
probtrackx.inputs.c_thresh = 0.2
probtrackx.inputs.n_steps=2000
probtrackx.inputs.step_length=0.5
probtrackx.inputs.n_samples=5000
probtrackx.inputs.opd=True
probtrackx.inputs.os2t=True
probtrackx.inputs.loop_check=True


"""
perform hard segmentation on the output of probtrackx
"""

findthebiggest = pe.Node(interface=fsl.FindTheBiggest(),name='findthebiggest')


"""
connect all the nodes for this workflow
"""

tractography.add_nodes([bedpostx, flirt])
tractography.connect([(bedpostx,probtrackx,[('outputnode.thsamples','thsamples'),
                                            ('outputnode.phsamples','phsamples'),
                                            ('outputnode.fsamples','fsamples')
                                            ]),
                      (probtrackx,findthebiggest,[('targets','in_files')]),
                      (flirt, probtrackx, [('out_matrix_file','xfm')])
                     ])


"""
Setup data storage area
"""

datasink = pe.Node(interface=nio.DataSink(),name='datasink')
datasink.inputs.base_directory = os.path.abspath('dtiresults')

def getstripdir(subject_id):
    import os
    return os.path.join(os.path.abspath('data/workingdir/dwiproc'),'_subject_id_%s' % subject_id)


"""
Setup the pipeline that combines the two workflows: tractography and computeTensor
----------------------------------------------------------------------------------
"""

dwiproc = pe.Workflow(name="dwiproc")
dwiproc.base_dir = os.path.abspath('fsl_dti_tutorial')
dwiproc.connect([
                    (infosource,datasource,[('subject_id', 'subject_id')]),
                    (datasource,computeTensor,[('dwi','fslroi.in_file'),
                                               ('bvals','dtifit.bvals'),
                                               ('bvecs','dtifit.bvecs'),
                                               ('dwi','eddycorrect.inputnode.in_file')]),
                    (datasource,tractography,[('bvals','bedpostx.inputnode.bvals'),
                                              ('bvecs','bedpostx.inputnode.bvecs'),
                                              ('seed_file','probtrackx.seed'),
                                              ('target_masks','probtrackx.target_masks')
                                              ]),
                    (computeTensor,tractography,[('eddycorrect.outputnode.eddy_corrected','bedpostx.inputnode.dwi'),
                                                 ('bet.mask_file','bedpostx.inputnode.mask'),
                                                 ('bet.mask_file','probtrackx.mask'),
                                                 ('fslroi.roi_file','flirt.reference')]),
                    (infosource, datasink,[('subject_id','container'),
                                           (('subject_id', getstripdir),'strip_dir')]),
                    (tractography,datasink,[('findthebiggest.out_file','fbiggest.@biggestsegmentation')])
                ])

if __name__ == '__main__':
    dwiproc.run()
    dwiproc.write_graph()


