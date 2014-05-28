#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
# @Author: oesteban - code@oscaresteban.es
# @Date:   2014-05-28 17:57:20
# @Last Modified by:   oesteban
# @Last Modified time: 2014-05-28 18:55:27

import os
from shutil import rmtree
from tempfile import mkdtemp


import numpy as np
import nibabel as nb
import nipype.testing as nit

from nipype.algorithms.misc import normalize_tpms

def test_normalize_tpms():
    tempdir = mkdtemp()

    in_mask = os.path.join(nit.basedir, 'data' , 'tpms_msk.nii.gz' )
    mskdata = nb.load( in_mask ).get_data()
    mskdata[mskdata>0.0] = 1.0

    mapdata = []
    in_files = []
    out_files = []

    for i in range(3):
        mapname = os.path.join(nit.basedir, 'data' , 'tpm_%02d.nii.gz' % i)
        filename =  os.path.join(tempdir, 'modtpm_%02d.nii.gz' % i )
        out_files.append(os.path.join(tempdir, 'normtpm_%02d.nii.gz' % i ))

        im = nb.load(mapname)
        data = im.get_data()
        mapdata.append( data.copy() )

        nb.Nifti1Image(2.0 * (data * mskdata), im.get_affine(),
                    im.get_header() ).to_filename(filename)
        in_files.append( filename )

    normalize_tpms( in_files, in_mask, out_files=out_files )

    sumdata = np.zeros_like(mskdata)

    for i,tstfname in enumerate( out_files ):
        normdata = nb.load( tstfname ).get_data()
        sumdata+=normdata
        yield assert_equal, np.all( normdata[mskdata==0]==0 ), True
        yield assert_equal, np.allclose( normdata, mapdata[i] ), True

    yield assert_equal, np.allclose( sumdata, mskdata ), True

    rmtree(tempdir)
