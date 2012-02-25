"""
==============================
HARDI - Diffusion Toolkit, FSL
==============================

A pipeline example that uses several interfaces to perform analysis on
diffusion weighted images using Diffusion Toolkit tools.

This tutorial is based on the 2010 FSL course and uses data freely available at
the FSL website at: http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz

More details can be found at
http://www.fmrib.ox.ac.uk/fslcourse/lectures/practicals/fdt/index.htm

In order to run this tutorial you need to have Diffusion Toolkit and FSL tools installed and
accessible from matlab/command line. Check by calling fslinfo and dtk from the command
line.

Tell python where to find the appropriate functions.
"""

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.workflows.fmri.fsl as fsl_wf          # fsl
import nipype.interfaces.diffusion_toolkit as dtk
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import os                                    # system functions

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

The nipype tutorial contains data for two subjects.  Subject data
is in two subdirectories, ``dwis1`` and ``dwis2``.  Each subject directory
contains each of the following files: bvec, bval, diffusion weighted data, a set of target masks,
a seed file, and a transformation matrix.

Below we set some variables to inform the ``datasource`` about the
layout of our data.  We specify the location of the data, the subject
sub-directories and a dictionary that maps each run to a mnemonic (or
field) for the run type (``dwi`` or ``bvals``).  These fields become
the output fields of the ``datasource`` node in the pipeline.

Specify the subject directories
"""

subject_list = ['siemens_hardi_test']


"""
Map field names to individual subject runs
"""

info = dict(dwi=[['subject_id', 'siemens_hardi_test_data']],
            bvecs=[['subject_id','siemens_hardi_test_data.bvec']],
            bvals=[['subject_id','siemens_hardi_test_data.bval']])

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                     name="infosource")

"""Here we set up iteration over all the subjects. The following line
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
datasource.inputs.base_directory = os.path.abspath('data')

datasource.inputs.field_template = dict(dwi='%s/%s.nii')
datasource.inputs.template_args = info


"""
Setup for ODF Computation
--------------------------------------
Here we will create a generic workflow for ODF computation
"""

compute_ODF = pe.Workflow(name='compute_ODF')

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

eddycorrect = fsl_wf.create_eddy_correct_pipeline('eddycorrect')
eddycorrect.inputs.inputnode.ref_num=0


hardi_mat = pe.Node(interface=dtk.HARDIMat(),name='hardi_mat')

odf_recon = pe.Node(interface=dtk.ODFRecon(),name='odf_recon')

"""
connect all the nodes for this workflow
"""

compute_ODF.connect([
                        (fslroi,bet,[('roi_file','in_file')]),
                        (eddycorrect, odf_recon,[('outputnode.eddy_corrected','DWI')]),
                        (eddycorrect, hardi_mat,[('outputnode.eddy_corrected','reference_file')]),
                        (hardi_mat, odf_recon, [('out_file', 'matrix')])
                      ])



"""
Setup for Tracktography
-----------------------
Here we will create a workflow to enable deterministic tracktography
"""

tractography = pe.Workflow(name='tractography')

odf_tracker = pe.Node(interface=dtk.ODFTracker(), name="odf_tracker")

smooth_trk = pe.Node(interface=dtk.SplineFilter(), name="smooth_trk")
smooth_trk.inputs.step_length = 1
"""
connect all the nodes for this workflow
"""

tractography.connect([
                      (odf_tracker, smooth_trk, [('track_file', 'track_file')])
                      ])


"""
Setup the pipeline that combines the two workflows: tractography and compute_ODF
----------------------------------------------------------------------------------
"""

dwiproc = pe.Workflow(name="dwiproc")
dwiproc.base_dir = os.path.abspath('dtk_odf_tutorial')
dwiproc.connect([
                    (infosource,datasource,[('subject_id', 'subject_id')]),
                    (datasource,compute_ODF,[('dwi','fslroi.in_file'),
                                               ('bvals','hardi_mat.bvals'),
                                               ('bvecs','hardi_mat.bvecs'),
                                               ('dwi','eddycorrect.inputnode.in_file')]),
                    (compute_ODF,tractography,[('bet.mask_file','odf_tracker.mask1_file'),
                                                 ('odf_recon.ODF','odf_tracker.ODF'),
                                                 ('odf_recon.max','odf_tracker.max')
                                                 ])
                ])

dwiproc.inputs.compute_ODF.hardi_mat.oblique_correction = True
dwiproc.inputs.compute_ODF.odf_recon.n_directions = 31
dwiproc.inputs.compute_ODF.odf_recon.n_b0 = 5
dwiproc.inputs.compute_ODF.odf_recon.n_output_directions = 181

if __name__ == '__main__':
    dwiproc.run()
    dwiproc.write_graph()


