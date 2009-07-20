"""
This script demonstrates how to setup a pipeline for batch conversion from Dicom to Niftii using `nipype.interfaces.freesurfer.Dicom2Nii`. It uses mri_convert to actually do the conversion and freesurfer commands must be available in your path.

This script converts TrioTim directories to subj directories. It uses Siemens patient number (not ID) as subjid

Please change the paths and the variables below. These are project specific scripts and should not be used to test your setup. To go through a tutorial see the documentation.

DOES NOT CONFORM TO CURRENT TRUNK
NEEDS MODIFICATION - SG - XX

"""
import nipy.interfaces.freesurfer as freesurfer
import nipy.pipeline.engine as pe

reload(pe)
reload(freesurfer)

mapping = [('niftifiles','*.nii'),('dicominfo','dicominfo.txt'),('dtiinfo','*mghdti.bv*')]
dicom_dir_template = '/some_path/to/dicomdirs/TrioTim*'
outputdir = '/some_path/to/some_directory'

converter = pe.generate_pipeline_node(freesurfer.Dicom2Nii())
converter.inputs.update(subjtemplate='S.%d',outputdir=outputdir,mapping=mapping)

# get the list of dicomdirs
dcmdirs = sorted(glob.glob(dicom_dir_template))

# iterate over the list and convert each one
converter.iterables = dict(dicomdir=lambda:dcmdirs)

conversionpipeline = pe.Pipeline()
conversionpipeline.addmodules([converter])

# In order to run the above pipeline inside ipython::
#
# run dicomconvert1.py
# conversionpipeline.run()
