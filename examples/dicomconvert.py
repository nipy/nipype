# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Convert dicom TimTrio dirs to nii files
"""
import nipype.interfaces.freesurfer as fs
import nipype.pipeline.engine as pe
import nipype.pipeline.node_wrapper as nw
from glob import glob
import os

dicom_dir_template = '/data/s*/TrioTim*'
outputdir = '/data/nifti'
conversionpipeline = pe.Pipeline()
conversionpipeline.config['workdir'] = '/data/workdir/conversion'
conversionpipeline.config['use_parameterized_dirs'] = True
for i, dcmdir in enumerate(sorted(glob(dicom_dir_template))):
    # the second last directory in the path contains subject id
    subjid = dcmdir.split('/')[-2]
    print "Setting up conversion for: %s" % subjid
    # Use freesurfer's mri_convert to do the conversion
    # give the conversion process a unique name so that the workdir
    # stores the hash that this particular subject has been
    # converted.
    converter = nw.NodeWrapper(interface=fs.Dicom2Nifti(),
                               diskbased=True, name=subjid)
    converter.inputs.update(dicomdir=dcmdir,
                            subject_id=subjid,
                            base_output_dir=outputdir,
                            out_type='nii.gz')
    conversionpipeline.add_modules([converter])

if __name__ == '__main__':
    # this will run the conversion in parallel if ipython clients are
    # set up
    conversionpipeline.run()
