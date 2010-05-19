
"""
   A pipeline example that uses several interfaces to
   perform analysis on diffusion weighted images using
   FSL fdt and tbss tools.

   The data for this analysis is available at
   http://www.mit.edu/~satra/nipype-nightly/users/pipeline_tutorial.html
"""


"""
1. Tell python where to find the appropriate functions.
"""

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

"""

"""
Specify the subject directories
"""
subject_list = ['dwis1']


"""
Map field names to individual subject runs
"""
info = dict(dwi=[['subject_id', 'data.nii.gz']],
            bvecs=[['subject_id','bvecs']],
            bvals=[['subject_id','bvals']],
            seedfile = [['subject_id','MASK_average_thal_right.nii.gz']],
            targetmasks = [['subject_id',['MASK_average_M1_right.nii.gz',
                                          'MASK_average_S1_right.nii.gz',
                                          'MASK_average_occipital_right.nii.gz',
                                          'MASK_average_pfc_right.nii.gz',
                                          'MASK_average_pmc_right.nii.gz',
                                          'MASK_average_ppc_right.nii.gz',
                                          'MASK_average_temporal_right.nii.gz']]],
            xfm=[['subject_id','standard2diff.mat']])

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']), name="infosource")

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
datasource.inputs.base_directory = os.path.abspath('data')
datasource.inputs.template = '%s/%s'
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
fslroi = pe.Node(interface=fsl.ExtractRoi(),name='fslroi')
fslroi.inputs.tmin=0
fslroi.inputs.tsize=1

"""
create a brain mask from the nodif_brain
"""
bet = pe.Node(interface=fsl.Bet(),name='bet')
bet.inputs.mask=True
bet.inputs.frac=0.34

"""
correct the diffusion weighted images for eddy_currents
"""
eddycorrect = pe.Node(interface=fsl.EddyCorrect(),name='eddycorrect')
eddycorrect.inputs.refnum=0

"""
compute the diffusion tensor in each voxel
"""
dtifit = pe.Node(interface=fsl.DtiFit(),name='dtifit')

"""
connect all the nodes for this workflow
"""
computeTensor.connect([
                        (fslroi,bet,[('outfile','infile')]),  
                        (eddycorrect,dtifit,[('outfile','dwi')]),                                   
                        (infosource, dtifit,[['subject_id','basename']]),
                        (bet,dtifit,[('maskfile','mask')])                       
                      ])



"""
Setup for Tracktography
-----------------------
Here we will create a workflow to enable probabilistic tracktography
and hard segmentation of the seed region
"""

tractography = pe.Workflow(name='tractography')

"""
estimate the diffusion parameters: phi, theta, and so on 
"""
bedpostx = pe.Node(interface=fsl.Bedpostx(),name='bedpostx')


"""
perform probabilistic tracktography
"""
probtrackx = pe.Node(interface=fsl.Probtrackx(),name='probtrackx')
probtrackx.inputs.nsamples=3
probtrackx.inputs.nsteps=10
probtrackx.inputs.forcedir=True
probtrackx.inputs.opd=True
probtrackx.inputs.os2t=True
probtrackx.inputs.mode='seedmask'


"""
threshold the output of probtrackx 
"""
projthresh = pe.Node(interface=fsl.Projthresh(),name='projthresh')
projthresh.inputs.threshold = 1


"""
perform hard segmentation on the output of probtrackx
"""
findthebiggest = pe.Node(interface=fsl.FindTheBiggest(),name='findthebiggest')


"""
connect all the nodes for this workflow
"""
tractography.connect([
                        (bedpostx,probtrackx,[('bpxoutdirectory','bpxdirectory')]),
                        (bedpostx,probtrackx,[('bpxoutdirectory','outdir')]),
                        (probtrackx,projthresh,[('targets','infiles')]),
                        (projthresh,findthebiggest,[('outfiles','infiles')])                    
                    ])


"""
Setup data storage area
"""
datasink = pe.Node(interface=nio.DataSink(),name='datasink')
datasink.inputs.base_directory = os.path.abspath('data/dtiresults')

def getstripdir(subject_id):
    return os.path.join(os.path.abspath('data/workingdir'),'_subject_id_%s' % subject_id)


"""
Setup the pipeline that combines the two workflows: tractography and computeTensor
------------------
"""
dwiproc = pe.Workflow(name="dwiproc")
dwiproc.base_dir = os.path.abspath('data/workingdir')
dwiproc.connect([
                    (infosource,datasource,[('subject_id', 'subject_id')]),                   
                    (datasource,computeTensor,[('dwi','fslroi.infile'),
                                               ('bvals','dtifit.bvals'),
                                               ('bvecs','dtifit.bvecs'),
                                               ('dwi','eddycorrect.infile')]),
                    (datasource,tractography,[('bvals','bedpostx.bvals'),
                                              ('bvecs','bedpostx.bvecs'),
                                              ('seedfile','probtrackx.seedfile'),
                                              ('targetmasks','probtrackx.targetmasks')]),
                    (computeTensor,tractography,[('eddycorrect.outfile','bedpostx.dwi'),
                                                 ('bet.maskfile','bedpostx.mask'),
                                                 ('bet.maskfile','probtrackx.mask')]),
                    (infosource, datasink,[('subject_id','container'),
                                           (('subject_id', getstripdir),'strip_dir')]),
                    (tractography,datasink,[('projthresh.outfiles','projthresh.@seeds_to_targets')]),
                    (tractography,datasink,[('findthebiggest.outfile','fbiggest.@biggestsegmentation')])
                ])

dwiproc.run()
dwiproc.write_graph()
          

"""
Setup for Tract-Based Spatial Statistics (TBSS) Computation
-----------------------------------------------------------
Here we will create a generic workflow for TBSS computation
"""
tbss_workflow = pe.Workflow(name='tbss_workflow')
tbss_workflow.base_dir=os.path.abspath('data/tbss')

"""
collect all the FA images for each subject using the DataGrabber class
"""
tbss_source = pe.Node(nio.DataGrabber(),name="tbss_source")
tbss_source.inputs.template = os.path.abspath('data/workingdir/_subject_id_*/dtifit/*_FA.nii.gz')

"""
prepare your FA data in your TBSS working directory in the right format
"""
tbss1 = pe.Node(fsl.Tbss1preproc(),name='tbss1')


"""
apply nonlinear registration of all FA images into standard space
"""
tbss2 = pe.Node(fsl.Tbss2reg(),name='tbss2')
tbss2.inputs.FMRIB58FA=True

"""
create the mean FA image and skeletonise it
"""
tbss3 = pe.Node(fsl.Tbss3postreg(),name='tbss3')
tbss3.inputs.FMRIB58FA=True

"""
project all subjects' FA data onto the mean FA skeleton
"""
tbss4 = pe.Node(fsl.Tbss4prestats(),name='tbss4')
tbss4.inputs.threshold=0.3

"""
feed the 4D projected FA data into GLM modelling and thresholding
in order to find voxels which correlate with your model
"""
randomise = pe.Node(fsl.Randomise(),name='randomise')
randomise.inputs.designmat=os.path.abspath('data/tbss/design.mat')
randomise.inputs.tcon=os.path.abspath('data/tbss/design.con')
randomise.inputs.numperm=10
                    

"""
Setup the pipeline that runs tbss
------------------
"""
tbss_workflow.connect([ (tbss_source,tbss1,[('outfiles','imglist')]),
                        (tbss1,tbss2,[('tbssdir','tbssdir')]),
                        (tbss2,tbss3,[('tbssdir','tbssdir')]),
                        (tbss3,tbss4,[('tbssdir','tbssdir')]),                        
                        (tbss4,randomise,[('all_FA_skeletonised','infile')]),
                        (tbss4,randomise,[('mean_FA_skeleton_mask','mask')])            
                    ])

tbss_workflow.run()
tbss_workflow.write_graph()

























