"""
This script demonstrates how to setup a pipeline for batch conversion from Dicom to Niftii using `nipype.interfaces.freesurfer.Dicom2Nii`. It uses mri_convert to actually do the conversion and freesurfer commands must be available in your path.

Please change the paths and the variables below. These are project specific scripts and should not be used to test your setup. To go through a tutorial see the documentation.

"""
import nipy.interfaces.freesurfer as freesurfer
import nipy.pipeline.engine as pe

reload(pe)
reload(freesurfer)


mapping = [('niftifiles','*.nii'),('dicominfo','dicominfo.txt'),('dtiinfo','*mghdti.bv*')]
base_dicom_dir = '/data/memory/sourcemem/'
subjlist = ['s163','s108','s126']
outputdir = '/groups/memory/sourcemem/data/'


conversionpipeline = pe.Pipeline()
for s in subjlist:
    converter = pe.generate_pipeline_node(freesurfer.Dicom2Nii())
    converter.inputs.update(dicomdir=os.path.join(base_dicom,s),subjtemplate='%s',subjid=s,outputdir=outputdir,mapping=mapping)
    # Alternate form
    # converter.inputs['dicomdir'] = os.path.join(base_dicom,s)
    # converter.inputs['subjtemplate'] = '%s'
    # converter.inputs['subjid'] = s
    # converter.inputs['outputdir'] = outputdir
    # converter.inputs['mapping'] = mapping
    conversionpipeline.addmodules([converter])


# In order to run the above pipeline inside ipython::
#
# run dicomconvert1.py
# conversionpipeline.run()


