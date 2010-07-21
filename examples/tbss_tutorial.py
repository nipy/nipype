"""
   XXX Currently not WORKING in release 0.3,
   Check for updates 

   A pipeline example that uses several interfaces to
   perform analysis on diffusion weighted images using
   FSL fdt and tbss tools.

   The data for this analysis is available at
   http://www.mit.edu/~satra/nipype-nightly/users/pipeline_tutorial.html
"""


"""
1. Tell python where to find the appropriate functions.
"""
raise RuntimeWarning, 'tbss_tutorial currently not functional'
import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import os                                    # system functions

"""
1b. Confirm package dependencies are installed.  (This is only for the
tutorial, rarely would you put this in your own code.)
"""
from nipype.utils.misc import package_check

package_check('numpy', '1.3', 'tutorial1')
package_check('scipy', '0.7', 'tutorial1')
package_check('networkx', '1.0', 'tutorial1')
package_check('IPython', '0.10', 'tutorial1')

fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

"""
Setup for Tract-Based Spatial Statistics (TBSS) Computation
-----------------------------------------------------------
Here we will create a generic workflow for TBSS computation
"""
tbss_workflow = pe.Workflow(name='tbss')
tbss_workflow.base_dir=os.path.abspath('tbss_tutorial')

"""
collect all the FA images for each subject using the DataGrabber class
"""

subject_ids = [1260, 1549, 1636, 1651, 2078, 2378]

tbss_source = pe.Node(nio.DataGrabber(outfields=["fa_files"]),name="tbss_source")
tbss_source.inputs.base_directory = os.path.abspath('/media/sdb2/fsl_course/fsl_course_data/tbss/')
tbss_source.inputs.template = '%d.nii.gz'
tbss_source.inputs.template_args = dict(fa_files=[[subject_ids]])
"""
prepare your FA data in your TBSS working directory in the right format
"""
tbss1 = pe.Node(fsl.TBSS1Preproc(),name='tbss1')


"""
apply nonlinear registration of all FA images into standard space
"""
tbss2 = pe.Node(fsl.TBSS2Reg(),name='tbss2')
tbss2.inputs.FMRIB58FA=True

"""
create the mean FA image and skeletonise it
"""
tbss3 = pe.Node(fsl.TBSS3Postreg(),name='tbss3')
tbss3.inputs.FMRIB58FA=True

"""
project all subjects' FA data onto the mean FA skeleton
"""
tbss4 = pe.Node(fsl.TBSS4Prestats(),name='tbss4')
tbss4.inputs.threshold=0.3

"""
feed the 4D projected FA data into GLM modelling and thresholding
in order to find voxels which correlate with your model
"""
randomise = pe.Node(fsl.Randomise(),name='randomise')
#randomise.inputs.design_mat=os.path.abspath('data/design.mat')
#randomise.inputs.tcon=os.path.abspath('data/design.con')
randomise.inputs.num_perm=10


"""
Setup the pipeline that runs tbss
------------------
"""
tbss_workflow.connect([ (tbss_source,tbss1,[('fa_files','img_list')]),
                        (tbss1,tbss2,[('tbss_dir','tbss_dir')]),
                        (tbss2,tbss3,[('tbss_dir','tbss_dir')]),
                        (tbss3,tbss4,[('tbss_dir','tbss_dir')]),
                        (tbss4,randomise,[('all_FA_skeletonised','in_file')]),
                        (tbss4,randomise,[('mean_FA_skeleton_mask','mask')])
                    ])

tbss_workflow.run()
tbss_workflow.write_graph()

