"""
This script demonstrates how to setup a pipeline for batch conversion from Dicom to Niftii using `nipype.interfaces.freesurfer.Dicom2Nii`. It uses mri_convert to actually do the conversion and freesurfer commands must be available in your path.

Please change the paths and the variables below. These are project specific scripts and should not be used to test your setup. To go through a tutorial see the documentation.

DOES NOT CONFORM TO CURRENT TRUNK
NEEDS MODIFICATION - SG - XX

"""
import nipy.interfaces.freesurfer as freesurfer
import nipy.pipeline.engine as pe

reload(pe)
reload(freesurfer)


mapping = [('niftifiles','*.nii'),('dicominfo','dicominfo.txt'),('dtiinfo','*mghdti.bv*')]
base = '/groups/rhythm/entrainment/subjects/'
template = 'entrpilot_%d'
subjlist = [2,3,4]
outputdir = '/groups/rhythm/entrainment_pipeline_eveline/subjects'

conversionpipeline = pe.Pipeline()
for s in subjlist:
    converter = pe.generate_pipeline_node(freesurfer.Dicom2Nii())
    converter.inputs.update(dicomdir=os.path.join(base,template % s,'dicom'),subjtemplate=template,subjid=s,outputdir=outputdir,mapping=mapping)
    conversionpipeline.addmodules([converter])

# In order to run the above pipeline inside ipython::
#
# run dicomconvert2.py
# conversionpipeline.run()
