""" Example first level analysis. Realigns functionals to the mean EPI
template and uses a subject specific condition model.

DOES NOT CONFORM TO CURRENT TRUNK
NEEDS MODIFICATION - SG - XX

"""
import nipy.interfaces.spm as spm
import nipy.interfaces.mit as mit
import nipy.pipeline.engine as pe
import nipy.pypemodules.MITio as mitio
import scipy.io as sio
import os
import glob

reload(spm)
reload(mit)
reload(pe)
reload(fbio)
reload(mitio)

"""
The following typemap is just a mapping from a mnemonic to a fieldname. The mnemonic is used in the subject info specifier below, but the output of the module is contained in the fieldnames. This should be customized for your specific set of scans

Example, `me` is the mnemonic for the multiecho scan
"""

typemap = dict(mecho='struct_multiecho',struct='struct_series',func='funct_series',dti='dti_vol',rest='resting_vol')

# Setup subject specific run information
info = {}
info['s163'] = [([6],'mecho'),([7],'struct'),([12,14,16],'func'),([22],'dti'),([9,18],'rest')]
info['s108'] = [([6],'mecho'),([7],'struct'),([17,19,21],'func'),([23],'dti'),([11],'rest')]
info['s126'] = [([6],'mecho'),([7],'struct'),([12,14,17],'func'),([19],'dti'),([9],'rest')]
subject_info = dict(typemap=typemap,info=info)

niftidirbase = '/path/to/dir containing the subject nifti directories'
subjist = sorted(info.keys())

""" The following function generates conditions based on a matlab mat file that contains the subject speific condition info.
"""
class subjectcondinfo(object):
    def __str__(self):
        return 'subjectinfofunc'

    def __call__(self,subjid):
        subjcondfile = '%s_statistics.mat' % subjid
	data = sio.loadmat(os.path.join('/groups/memory/sourcemem',subjcondfile))
	conditions = []
	userregfiles = []
	for r in range(3):
	    runinfo = data['stats'][0][r]
	    cond1 = ['Miss',runinfo.Miss_onsets[0].tolist(),[0],[1]]
	    cond2 = ['Source2',runinfo.Source_2_onsets[0].tolist(),[0],[1]]
	    cond3 = ['SourceFont',runinfo.Source_Font_onsets[0].tolist(),[0],[1]]
	    cond4 = ['SourceQuestion',runinfo.Source_Question_onsets[0].tolist(),[0],[1]]
	    cond5 = ['Source0',runinfo.Source_0_onsets[0].tolist(),[0],[1]]
	    conditions.append([cond1,cond2,cond3,cond4,cond5])
	return (conditions,userregfiles)

# Setup contrast info
cont1 = ['Hit>Miss', 'T', ['Source2','SourceFont','SourceQuestion','Source0','Miss'],[1,1,1,1,-4]]
cont2 = ['Source2>0', 'T', ['Source2','Source0'],[1,-1]]
cont3 = ['Source2>source0miss', 'T', ['Source2','Source0','Miss'],[2,-1,-1]]
cont4 = ['source12>source0miss', 'T', ['Source2','SourceFont','SourceQuestion','Source0','Miss'],[1,0.5,0.5,-1,-1]]
cont5 = ['mem strength', 'T', ['Source2','SourceFont','SourceQuestion','Source0','Miss'],[2,0.5,0.5,-1,-2]]
cont6 = ['source strength', 'T', ['Source2','SourceFont','SourceQuestion'],[1,-0.5,-0.5]]
cont7 = ['source specificity', 'T', ['SourceFont','SourceQuestion'],[1,-1]]
cont8 = ['Task vs Fixation', 'T', ['Miss','Source2','SourceFont','SourceQuestion','Source0'],[0.2,0.2,0.2,0.2,0.2]]
cont9 = ['source12>0', 'T', ['Source2','SourceFont','SourceQuestion','Source0'],[1,1,1,-3]]
contrastlist = [cont1,cont2,cont3,cont4,cont5,cont6,cont7,cont8,cont9]


# SETUP DATASOURCE
datasource = pe.generate_pipeline_node(mitio.MITSource())
datasource.inputs.update(subj_template='%s',subj_info=subject_info,base_dir=niftidirbase)
# Iterate over subjects
datasource.iterables.update(subj_id=lambda:subjlist)

##### SETUP PREPROCESSING COMPONENTS #####

realign    = pe.generate_pipeline_node(spm.Realign(rtm=True))
normalize  = pe.generate_pipeline_node(spm.NonaffineNormalize())
normalize.inputs.update(template=['/software/spm5_1782/templates/EPI.nii'])
smooth     = pe.generate_pipeline_node(spm.Smooth())
smooth.inputs.update(fwhm=6)
artdetect  = pe.generate_pipeline_node(mit.ArtifactDetect())
artdetect.inputs.update(zintensity_threshold=3)

##### SETUP MODEL SPECIFICATION OPTIONS
modelspec = pe.generate_pipeline_node(spm.ModelSpec())
modelspec.inputs.update(RT=2,inunits='scans',outunits='scans',subjectinfo=subjectcondinfo)
modeldesign = pe.generate_pipeline_node(spm.Level1Design())
modeldesign.inputs.update(RT=2,concatruns=False,temporalderiv=True)
l1modelestimate = pe.generate_pipeline_node(spm.L1ModelEstimate())
contrastestimate = pe.generate_pipeline_node(spm.ContrastEstimate())
contrastestimate.inputs.update(contrasts=contrastlist)

# Setup Level 1 Pipeline

# Pipeline 1
# coregister mean functional to structural.
level1pipeline = pe.Pipeline()
level1pipeline.config['workdir'] = os.path.abspath('/path/to/working')
# The following creates directory names based on whatever you are iterating over.
# In this example the iteration is over subjects.
level1pipeline.config['use_parameterized_dirs'] = True
level1pipeline.connect([
    (datasource,realign,[('funct_series','files')]),
    (realign,normalize,[('mean','source'),('files','files')]),
    (normalize,smooth,[('files','files')]),
    (realign,artdetect,[('files','imgfiles'),('parameters','motionfiles')]),
    (realign,modelspec,[('parameters','motionfiles')]),
    (datasource,modelspec,[('subj_id','subjid')]),
    (smooth,modeldesign,[('files','preprocfiles')]),
    (artdetect,modeldesign,[('artifactfiles','outlierfiles')]),
    (modelspec,modeldesign,[('modelspecfile','modelconfig')]),
    (modeldesign,l1modelestimate,[('spmmatfile','spmmatfile')]),
    (l1modelestimate,contrastestimate,[('spmmatfile','spmmatfile'),('betaimgs','betaimgs'),('maskimg','maskimg'),('resmsimg','resmsimg'),('rpvimg','rpvimg')]),
    ])

# In order to run the above pipeline inside ipython::
#
# run firstlevelanalysis1.py
# level1pipeline.run()
