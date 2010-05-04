
"""
   A pipeline example that uses several interfaces to
   perform analysis on diffusion weighted images using
   FSL fdt and tbss tools.

   The data for this analysis was taken from the following FSL
   website: http://www.fmrib.ox.ac.uk/fslcourse/
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
Data specification for all three tasks: FA computation, Tracktography, and TBSS
---------------------------------------------------------------------------------------
"""

# Specify the subject directories
subject_list = ['dwis1']

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']), name="infosource")
infosource.iterables = ('subject_id', subject_list)

info = dict(dwi=[['subject_id', 'data.nii.gz']],
            bvecs=[['subject_id','bvecs']],
            bvals=[['subject_id','bvals']],
            seedfile = [['subject_id','MASK_average_thal_right.nii.gz']],
            targetmasks = [['subject_id','targets.txt']],
            xfm=[['subject_id','standard2diff.mat']])

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=['dwi','bvecs','bvals',
                                                          'seedfile','targetmasks','xfm']),
                     name = 'datasource')
datasource.inputs.base_directory = os.path.abspath('data')
datasource.inputs.template = '%s/%s'
datasource.inputs.template_args = info

computeFA = pe.Workflow(name='computeFA')
computeFA.base_dir=os.path.abspath('fsl/workingdir')

fslroi = pe.Node(interface=fsl.ExtractRoi(),name='fslroi')
fslroi.inputs.tmin=0
fslroi.inputs.tsize=1

bet = pe.Node(interface=fsl.Bet(),name='bet')
bet.inputs.mask=True
bet.inputs.frac=0.34

eddycorrect = pe.Node(interface=fsl.Eddycorrect(),name='eddycorrect')
eddycorrect.inputs.refnum=0

dtifit = pe.Node(interface=fsl.Dtifit(),name='dtifit')

bedpostx = pe.Node(interface=fsl.Bedpostx(),name='bedpostx')

probtrackx = pe.Node(interface=fsl.Probtrackx(),name='probtrackx')
probtrackx.inputs.nsamples=3
probtrackx.inputs.nsteps=10
probtrackx.inputs.forcedir=True
probtrackx.inputs.opd=True
probtrackx.inputs.os2t=True
probtrackx.inputs.mode='seedmask'

projthresh = pe.Node(interface=fsl.Projthresh(),name='projthresh')
projthresh.inputs.threshold = 1

findthebiggest = pe.Node(interface=fsl.Findthebiggest(),name='findthebiggest')

datasink = pe.Node(interface=nio.DataSink(),name='datasink')
datasink.inputs.base_directory = os.path.abspath('data/dtiresults')

def getstripdir(subject_id):
    return os.path.join(os.path.abspath('fsl/workingdir'),'_subject_id_%s' % subject_id)

computeFA.connect([ (infosource,datasource,[('subject_id', 'subject_id')]),                   
                    (datasource,fslroi,[('dwi','infile')]),
                    (datasource,eddycorrect,[('dwi','infile')]),
                    (fslroi,bet,[('outfile','infile')]),                    
                    
                    (eddycorrect,dtifit,[('outfile','dwi')]),                                   
                    (infosource, dtifit,[['subject_id','basename']]),
                    (bet,dtifit,[('maskfile','mask')]),
                    (datasource,dtifit,[('bvals','bvals')]),
                    (datasource,dtifit,[('bvecs','bvecs')]),

                    (infosource, bedpostx,[['subject_id','bpxdirectory']]),
                    (eddycorrect,bedpostx,[('outfile','dwi')]), 
                    (bet,bedpostx,[('maskfile','mask')]),
                    (datasource,bedpostx,[('bvals','bvals')]),
                    (datasource,bedpostx,[('bvecs','bvecs')]),

                    (bet,probtrackx,[('maskfile','mask')]),
                    (datasource,probtrackx,[('seedfile','seedfile')]),
                    (datasource,probtrackx,[('targetmasks','targetmasks')]),
                    (bedpostx,probtrackx,[('bpxoutdirectory','bpxdirectory')]),
                    (bedpostx,probtrackx,[('bpxoutdirectory','outdir')]),

                    (probtrackx,projthresh,[('targets','infiles')]),
                    (projthresh,findthebiggest,[('outfiles','infiles')]),
                    
                    (infosource, datasink,[('subject_id','container'),
                                           (('subject_id', getstripdir),'strip_dir')]),
                    (projthresh,datasink,[('outfiles','projthresh.@seeds_to_targets')]),
                    (findthebiggest,datasink,[('outfile','fbiggest.@biggestsegmentation')])
                                        
                 ])

computeFA.write_graph()
computeFA.run()

"""
TBSS analysis
"""

# collect all the FA images for each subject
tbss_source = pe.Node(nio.DataGrabber(),name="tbss_source")
tbss_source.inputs.template = os.path.abspath('fsl/workingdir/_subject_id_*/dtifit/*_FA.nii.gz')

tbss1 = pe.Node(fsl.Tbss1preproc(),name='tbss1')

tbss2 = pe.Node(fsl.Tbss2reg(),name='tbss2')
tbss2.inputs.FMRIB58FA=True

tbss3 = pe.Node(fsl.Tbss3postreg(),name='tbss3')
tbss3.inputs.FMRIB58FA=True

tbss4 = pe.Node(fsl.Tbss4prestats(),name='tbss4')
tbss4.inputs.threshold=0.3

randomise = pe.Node(fsl.Randomise(),name='randomise')
randomise.inputs.designmat=os.path.abspath('data/tbss/design.mat')
randomise.inputs.tcon=os.path.abspath('data/tbss/design.con')
randomise.inputs.numperm=10
                    
tbss_workflow = pe.Workflow(name='tbss_workflow')
tbss_workflow.base_dir=os.path.abspath('data/tbss')
tbss_workflow.connect([ (tbss_source,tbss1,[('outfiles','imglist')]),
                        (tbss1,tbss2,[('tbssdir','tbssdir')]),
                        (tbss2,tbss3,[('tbssdir','tbssdir')]),
                        (tbss3,tbss4,[('tbssdir','tbssdir')]),                        
                        (tbss4,randomise,[('all_FA_skeletonised','infile')]),
                        (tbss4,randomise,[('mean_FA_skeleton_mask','mask')])            
                    ])
tbss_workflow.write_graph()
tbss_workflow.run()

























