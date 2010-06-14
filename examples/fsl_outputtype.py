# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Created on Mar 23, 2010

@author:
'''
import os
from nipype.interfaces import fsl

if __name__ == '__main__':

    out_dir = "fsl_outputtype"
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    skullstrip_nifti_gz = fsl.BET(infile="data/s1/struct.nii",
                                  outfile=out_dir +"/struct_brain.nii.gz",
                                  outputtype = "NIFTI_GZ")
    skullstrip_nifti_gz.run()

    skullstrip_nifti = fsl.BET(infile="data/s1/struct.nii",
                               outfile=out_dir +"/struct_brain.nii",
                               outputtype = "NIFTI")
    skullstrip_nifti.run()

    fsl.NEW_FSLCommand.set_default_outputtype('NIFTI_PAIR')
    skullstrip_default = fsl.BET(infile="data/s1/struct.nii",
                                 outfile=out_dir +"/struct_brain.img")
    skullstrip_default.run()
