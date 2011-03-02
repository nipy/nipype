
"""
A pipeline example that uses several interfaces to
perform analysis on diffusion weighted images using
FSL FDT tools.

This tutorial is based on the 2010 FSL course and uses
data freely available at the FSL website at:
http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz

More details can be found at http://www.fmrib.ox.ac.uk/fslcourse/lectures/practicals/fdt/index.htm
"""


"""
Tell python where to find the appropriate functions.
"""

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.camino as camino
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
"""

"""
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

inputnode = pe.Node(interface=util.IdentityInterface(fields=["dwi", "bvecs", "bvals"]), name="inputnode")

"""
convert nifti DWI to camino raw format
"""

image2voxel = pe.Node(interface=camino.image2voxel(out_prefix="dwi"), name="image2voxel")

"""
convert bvecs and bvals to camino scheme format
"""

fsl2scheme = pe.Node(interface=camino.fsl2scheme(), name="fsl2scheme")


"""
compute the diffusion tensor in each voxel
"""

dtifit = pe.Node(interface=camino.dtfit(),name='dtifit')

"""
connect all the nodes for this workflow
"""

computeTensor.connect([(inputnode, image2voxel, [("dwi", "in_file")]),
                       (inputnode, fsl2scheme, [("bvecs", "bvec_file"),
                                                ("bvals", "bval_file")]),
                       
                       (image2voxel, dtifit,[['out_file','in_file']]),
                       (fsl2scheme, dtifit,[['out_file','scheme_file']])
                      ])


"""
Setup the pipeline that combines the two workflows: tractography and computeTensor
----------------------------------------------------------------------------------
"""

dwiproc = pe.Workflow(name="dwiproc")
dwiproc.base_dir = os.path.abspath('fsl_dti_tutorial')
dwiproc.connect([
                    (infosource,datasource,[('subject_id', 'subject_id')]),
                    (datasource,computeTensor,[('dwi','inputnode.dwi'),
                                               ('bvals','inputnode.bvals'),
                                               ('bvecs','inputnode.bvecs')])
                ])

dwiproc.run()
dwiproc.write_graph()


