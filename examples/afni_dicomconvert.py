# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Convert dicom TimTrio dirs to nii files
"""
import nipype.interfaces.afni as afni
import nipype.pipeline.engine as pe
from glob import glob
import os


basedir = '/home/derickson/Projects/nipy/nipype-tutorial/afnidata'
dicomdirs = glob('%s/*-EPI'%(basedir))
for ddir in dicomdirs:
    pth, subid = os.path.split(ddir)
    convert = pe.Node(interface = afni.To3d(),
                             diskbased = True,
                             name = 'TestTo3d')
    # add interface specific inputs for this subject
    convert.inputs.infolder = ddir
    convert.inputs.outfile = '%s/%s.nii.gz' % (pth, subid)
    convert.inputs.filetype = 'epan'
    convert.inputs.skipoutliers = True
    convert.inputs.assumemosaic = True
    convert.inputs.datatype = 'float'
    convert.inputs.funcparams = '24 425 1.37'

    refit = pe.Node(interface = afni.Threedrefit(),
                           diskbased = True,
                           name = 'Test3drefit')

    refit.inputs.deoblique = True
    refit.inputs.xorigin = 'cen'
    refit.inputs.yorigin = 'cen'
    refit.inputs.zorigin = 'cen'

    resample = pe.Node(interface = afni.Threedresample(),
                              diskbased = True,
                              name = 'Test3dresample')

    resample.inputs.outfile = '%s/%s-Reorient.nii.gz' % (pth,subid)
    resample.inputs.orientation = 'RPI'

    pipeline = pe.Workflow(name='TestDicomConvertPipe')
    pipeline.base_dir = pth
    pipeline.connect([
                     (convert, refit,
                        [('out_file', 'infile')]),
                     (refit,resample,
                        [('out_file', 'infile')]),
                    ])
    pipeline.run()
