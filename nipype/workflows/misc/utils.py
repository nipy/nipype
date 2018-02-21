# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from builtins import map, range


def get_vox_dims(volume):
    import nibabel as nb
    from nipype.utils import NUMPY_MMAP
    if isinstance(volume, list):
        volume = volume[0]
    nii = nb.load(volume, mmap=NUMPY_MMAP)
    hdr = nii.header
    voxdims = hdr.get_zooms()
    return [float(voxdims[0]), float(voxdims[1]), float(voxdims[2])]


def get_data_dims(volume):
    import nibabel as nb
    from nipype.utils import NUMPY_MMAP
    if isinstance(volume, list):
        volume = volume[0]
    nii = nb.load(volume, mmap=NUMPY_MMAP)
    hdr = nii.header
    datadims = hdr.get_data_shape()
    return [int(datadims[0]), int(datadims[1]), int(datadims[2])]


def get_affine(volume):
    import nibabel as nb
    from nipype.utils import NUMPY_MMAP
    nii = nb.load(volume, mmap=NUMPY_MMAP)
    return nii.affine


def select_aparc(list_of_files):
    for in_file in list_of_files:
        if 'aparc+aseg.mgz' in in_file:
            idx = list_of_files.index(in_file)
    return list_of_files[idx]


def select_aparc_annot(list_of_files):
    for in_file in list_of_files:
        if '.aparc.annot' in in_file:
            idx = list_of_files.index(in_file)
    return list_of_files[idx]


def region_list_from_volume(in_file):
    import nibabel as nb
    import numpy as np
    from nipype.utils import NUMPY_MMAP
    segmentation = nb.load(in_file, mmap=NUMPY_MMAP)
    segmentationdata = segmentation.get_data()
    rois = np.unique(segmentationdata)
    region_list = list(rois)
    region_list.sort()
    region_list.remove(0)
    region_list = list(map(int, region_list))
    return region_list


def id_list_from_lookup_table(lookup_file, region_list):
    import numpy as np
    LUTlabelsRGBA = np.loadtxt(
        lookup_file,
        skiprows=4,
        usecols=[0, 1, 2, 3, 4, 5],
        comments='#',
        dtype={
            'names': ('index', 'label', 'R', 'G', 'B', 'A'),
            'formats': ('int', '|S30', 'int', 'int', 'int', 'int')
        })
    numLUTLabels = np.size(LUTlabelsRGBA)
    LUTlabelDict = {}
    for labels in range(0, numLUTLabels):
        LUTlabelDict[LUTlabelsRGBA[labels][0]] = [
            LUTlabelsRGBA[labels][1], LUTlabelsRGBA[labels][2],
            LUTlabelsRGBA[labels][3], LUTlabelsRGBA[labels][4],
            LUTlabelsRGBA[labels][5]
        ]
    id_list = []
    for region in region_list:
        label = LUTlabelDict[region][0]
        id_list.append(label)
    id_list = list(map(str, id_list))
    return id_list
