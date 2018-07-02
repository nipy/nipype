# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import range

import os
import os.path as op
import shutil

import numpy as np
import nibabel as nb
import networkx as nx

from ... import logging
from ..base import (BaseInterface, LibraryBaseInterface,
                    BaseInterfaceInputSpec, traits, File,
                    TraitedSpec, Directory, isdefined)
from .base import have_cmp
iflogger = logging.getLogger('nipype.interface')


def create_annot_label(subject_id, subjects_dir, fs_dir, parcellation_name):
    import cmp
    from cmp.util import runCmd
    iflogger.info("Create the cortical labels necessary for our ROIs")
    iflogger.info("=================================================")
    fs_label_dir = op.join(op.join(subjects_dir, subject_id), 'label')
    output_dir = op.abspath(op.curdir)
    paths = []
    cmp_config = cmp.configuration.PipelineConfiguration()
    cmp_config.parcellation_scheme = "Lausanne2008"
    for hemi in ['lh', 'rh']:
        spath = cmp_config._get_lausanne_parcellation('Lausanne2008')[
            parcellation_name]['fs_label_subdir_name'] % hemi
        paths.append(spath)
    for p in paths:
        try:
            os.makedirs(op.join('.', p))
        except:
            pass
    if '33' in parcellation_name:
        comp = [
            ('rh', 'myatlas_36_rh.gcs', 'rh.myaparc_36.annot',
             'regenerated_rh_36', 'myaparc_36'),
            ('rh', 'myatlas_60_rh.gcs', 'rh.myaparc_60.annot',
             'regenerated_rh_60', 'myaparc_60'),
            ('lh', 'myatlas_36_lh.gcs', 'lh.myaparc_36.annot',
             'regenerated_lh_36', 'myaparc_36'),
            ('lh', 'myatlas_60_lh.gcs', 'lh.myaparc_60.annot',
             'regenerated_lh_60', 'myaparc_60'),
        ]
    elif '60' in parcellation_name:
        comp = [
            ('rh', 'myatlas_60_rh.gcs', 'rh.myaparc_60.annot',
             'regenerated_rh_60', 'myaparc_60'),
            ('lh', 'myatlas_60_lh.gcs', 'lh.myaparc_60.annot',
             'regenerated_lh_60', 'myaparc_60'),
        ]
    elif '125' in parcellation_name:
        comp = [
            ('rh', 'myatlas_125_rh.gcs', 'rh.myaparc_125.annot',
             'regenerated_rh_125', 'myaparc_125'),
            ('rh', 'myatlas_60_rh.gcs', 'rh.myaparc_60.annot',
             'regenerated_rh_60', 'myaparc_60'),
            ('lh', 'myatlas_125_lh.gcs', 'lh.myaparc_125.annot',
             'regenerated_lh_125', 'myaparc_125'),
            ('lh', 'myatlas_60_lh.gcs', 'lh.myaparc_60.annot',
             'regenerated_lh_60', 'myaparc_60'),
        ]
    elif '250' in parcellation_name:
        comp = [
            ('rh', 'myatlas_250_rh.gcs', 'rh.myaparc_250.annot',
             'regenerated_rh_250', 'myaparc_250'),
            ('rh', 'myatlas_60_rh.gcs', 'rh.myaparc_60.annot',
             'regenerated_rh_60', 'myaparc_60'),
            ('lh', 'myatlas_250_lh.gcs', 'lh.myaparc_250.annot',
             'regenerated_lh_250', 'myaparc_250'),
            ('lh', 'myatlas_60_lh.gcs', 'lh.myaparc_60.annot',
             'regenerated_lh_60', 'myaparc_60'),
        ]
    else:
        comp = [
            ('rh', 'myatlas_36_rh.gcs', 'rh.myaparc_36.annot',
             'regenerated_rh_36', 'myaparc_36'),
            ('rh', 'myatlasP1_16_rh.gcs', 'rh.myaparcP1_16.annot',
             'regenerated_rh_500', 'myaparcP1_16'),
            ('rh', 'myatlasP17_28_rh.gcs', 'rh.myaparcP17_28.annot',
             'regenerated_rh_500', 'myaparcP17_28'),
            ('rh', 'myatlasP29_36_rh.gcs', 'rh.myaparcP29_36.annot',
             'regenerated_rh_500', 'myaparcP29_36'),
            ('rh', 'myatlas_60_rh.gcs', 'rh.myaparc_60.annot',
             'regenerated_rh_60', 'myaparc_60'),
            ('rh', 'myatlas_125_rh.gcs', 'rh.myaparc_125.annot',
             'regenerated_rh_125', 'myaparc_125'),
            ('rh', 'myatlas_250_rh.gcs', 'rh.myaparc_250.annot',
             'regenerated_rh_250', 'myaparc_250'),
            ('lh', 'myatlas_36_lh.gcs', 'lh.myaparc_36.annot',
             'regenerated_lh_36', 'myaparc_36'),
            ('lh', 'myatlasP1_16_lh.gcs', 'lh.myaparcP1_16.annot',
             'regenerated_lh_500', 'myaparcP1_16'),
            ('lh', 'myatlasP17_28_lh.gcs', 'lh.myaparcP17_28.annot',
             'regenerated_lh_500', 'myaparcP17_28'),
            ('lh', 'myatlasP29_36_lh.gcs', 'lh.myaparcP29_36.annot',
             'regenerated_lh_500', 'myaparcP29_36'),
            ('lh', 'myatlas_60_lh.gcs', 'lh.myaparc_60.annot',
             'regenerated_lh_60', 'myaparc_60'),
            ('lh', 'myatlas_125_lh.gcs', 'lh.myaparc_125.annot',
             'regenerated_lh_125', 'myaparc_125'),
            ('lh', 'myatlas_250_lh.gcs', 'lh.myaparc_250.annot',
             'regenerated_lh_250', 'myaparc_250'),
        ]

    log = cmp_config.get_logger()

    for out in comp:
        mris_cmd = 'mris_ca_label %s %s "%s/surf/%s.sphere.reg" "%s" "%s" ' % (
            subject_id, out[0], op.join(subjects_dir, subject_id), out[0],
            cmp_config.get_lausanne_atlas(out[1]),
            op.join(fs_label_dir, out[2]))
        runCmd(mris_cmd, log)
        iflogger.info('-----------')

        annot = '--annotation "%s"' % out[4]

        mri_an_cmd = 'mri_annotation2label --subject %s --hemi %s --outdir "%s" %s' % (
            subject_id, out[0], op.join(output_dir, out[3]), annot)
        iflogger.info(mri_an_cmd)
        runCmd(mri_an_cmd, log)
        iflogger.info('-----------')
        iflogger.info(os.environ['SUBJECTS_DIR'])
        # extract cc and unknown to add to tractography mask, we do not want this as a region of interest
        # in FS 5.0, unknown and corpuscallosum are not available for the 35 scale (why?),
        # but for the other scales only, take the ones from _60
        rhun = op.join(output_dir, 'rh.unknown.label')
        lhun = op.join(output_dir, 'lh.unknown.label')
        rhco = op.join(output_dir, 'rh.corpuscallosum.label')
        lhco = op.join(output_dir, 'lh.corpuscallosum.label')
    shutil.copy(
        op.join(output_dir, 'regenerated_rh_60', 'rh.unknown.label'), rhun)
    shutil.copy(
        op.join(output_dir, 'regenerated_lh_60', 'lh.unknown.label'), lhun)
    shutil.copy(
        op.join(output_dir, 'regenerated_rh_60', 'rh.corpuscallosum.label'),
        rhco)
    shutil.copy(
        op.join(output_dir, 'regenerated_lh_60', 'lh.corpuscallosum.label'),
        lhco)

    mri_cmd = """mri_label2vol --label "%s" --label "%s" --label "%s" --label "%s" --temp "%s" --o  "%s" --identity """ % (
        rhun, lhun, rhco, lhco,
        op.join(op.join(subjects_dir, subject_id), 'mri', 'orig.mgz'),
        op.join(fs_label_dir, 'cc_unknown.nii.gz'))
    runCmd(mri_cmd, log)
    runCmd('mris_volmask %s' % subject_id, log)
    mri_cmd = 'mri_convert -i "%s/mri/ribbon.mgz" -o "%s/mri/ribbon.nii.gz"' % (
        op.join(subjects_dir, subject_id), op.join(subjects_dir, subject_id))
    runCmd(mri_cmd, log)
    mri_cmd = 'mri_convert -i "%s/mri/aseg.mgz" -o "%s/mri/aseg.nii.gz"' % (
        op.join(subjects_dir, subject_id), op.join(subjects_dir, subject_id))
    runCmd(mri_cmd, log)

    iflogger.info("[ DONE ]")


def create_roi(subject_id, subjects_dir, fs_dir, parcellation_name, dilation):
    """ Creates the ROI_%s.nii.gz files using the given parcellation information
    from networks. Iteratively create volume. """
    import cmp
    from cmp.util import runCmd
    iflogger.info("Create the ROIs:")
    output_dir = op.abspath(op.curdir)
    fs_dir = op.join(subjects_dir, subject_id)
    cmp_config = cmp.configuration.PipelineConfiguration()
    cmp_config.parcellation_scheme = "Lausanne2008"
    log = cmp_config.get_logger()
    parval = cmp_config._get_lausanne_parcellation('Lausanne2008')[
        parcellation_name]
    pgpath = parval['node_information_graphml']
    aseg = nb.load(op.join(fs_dir, 'mri', 'aseg.nii.gz'))
    asegd = aseg.get_data()

    # identify cortical voxels, right (3) and left (42) hemispheres
    idxr = np.where(asegd == 3)
    idxl = np.where(asegd == 42)
    xx = np.concatenate((idxr[0], idxl[0]))
    yy = np.concatenate((idxr[1], idxl[1]))
    zz = np.concatenate((idxr[2], idxl[2]))

    # initialize variables necessary for cortical ROIs dilation
    # dimensions of the neighbourhood for rois labels assignment (choose odd dimensions!)
    shape = (25, 25, 25)
    center = np.array(shape) // 2
    # dist: distances from the center of the neighbourhood
    dist = np.zeros(shape, dtype='float32')
    for x in range(shape[0]):
        for y in range(shape[1]):
            for z in range(shape[2]):
                distxyz = center - [x, y, z]
                dist[x, y, z] = np.sqrt(np.sum(np.multiply(distxyz, distxyz)))

    iflogger.info("Working on parcellation: ")
    iflogger.info(
        cmp_config._get_lausanne_parcellation('Lausanne2008')[
            parcellation_name])
    iflogger.info("========================")
    pg = nx.read_graphml(pgpath)
    # each node represents a brain region
    # create a big 256^3 volume for storage of all ROIs
    rois = np.zeros((256, 256, 256), dtype=np.int16)

    count = 0
    for brk, brv in pg.nodes(data=True):
        count = count + 1
        iflogger.info(brv)
        iflogger.info(brk)
        if brv['dn_hemisphere'] == 'left':
            hemi = 'lh'
        elif brv['dn_hemisphere'] == 'right':
            hemi = 'rh'
        if brv['dn_region'] == 'subcortical':
            iflogger.info(brv)
            iflogger.info('---------------------')
            iflogger.info('Work on brain region: %s', brv['dn_region'])
            iflogger.info('Freesurfer Name: %s', brv['dn_fsname'])
            iflogger.info('Region %s of %s', count, pg.number_of_nodes())
            iflogger.info('---------------------')
            # if it is subcortical, retrieve roi from aseg
            idx = np.where(asegd == int(brv['dn_fs_aseg_val']))
            rois[idx] = int(brv['dn_correspondence_id'])

        elif brv['dn_region'] == 'cortical':
            iflogger.info(brv)
            iflogger.info('---------------------')
            iflogger.info('Work on brain region: %s', brv['dn_region'])
            iflogger.info('Freesurfer Name: %s', brv['dn_fsname'])
            iflogger.info('Region %s of %s', count, pg.number_of_nodes())
            iflogger.info('---------------------')

            labelpath = op.join(output_dir,
                                parval['fs_label_subdir_name'] % hemi)
            # construct .label file name

            fname = '%s.%s.label' % (hemi, brv['dn_fsname'])

            # execute fs mri_label2vol to generate volume roi from the label file
            # store it in temporary file to be overwritten for each region

            mri_cmd = 'mri_label2vol --label "%s" --temp "%s" --o "%s" --identity' % (
                op.join(labelpath, fname), op.join(fs_dir, 'mri', 'orig.mgz'),
                op.join(output_dir, 'tmp.nii.gz'))
            runCmd(mri_cmd, log)

            tmp = nb.load(op.join(output_dir, 'tmp.nii.gz'))
            tmpd = tmp.get_data()

            # find voxel and set them to intensityvalue in rois
            idx = np.where(tmpd == 1)
            rois[idx] = int(brv['dn_correspondence_id'])

        # store volume eg in ROI_scale33.nii.gz
        out_roi = op.abspath('ROI_%s.nii.gz' % parcellation_name)

        # update the header
        hdr = aseg.header
        hdr2 = hdr.copy()
        hdr2.set_data_dtype(np.uint16)

        log.info("Save output image to %s" % out_roi)
        img = nb.Nifti1Image(rois, aseg.affine, hdr2)
        nb.save(img, out_roi)

    iflogger.info("[ DONE ]")
    # dilate cortical regions
    if dilation is True:
        iflogger.info("Dilating cortical regions...")
        # loop throughout all the voxels belonging to the aseg GM volume
        for j in range(xx.size):
            if rois[xx[j], yy[j], zz[j]] == 0:
                local = extract(
                    rois, shape, position=(xx[j], yy[j], zz[j]), fill=0)
                mask = local.copy()
                mask[np.nonzero(local > 0)] = 1
                thisdist = np.multiply(dist, mask)
                thisdist[np.nonzero(thisdist == 0)] = np.amax(thisdist)
                value = np.int_(
                    local[np.nonzero(thisdist == np.amin(thisdist))])
                if value.size > 1:
                    counts = np.bincount(value)
                    value = np.argmax(counts)
                rois[xx[j], yy[j], zz[j]] = value

        # store volume eg in ROIv_scale33.nii.gz
        out_roi = op.abspath('ROIv_%s.nii.gz' % parcellation_name)
        iflogger.info('Save output image to %s', out_roi)
        img = nb.Nifti1Image(rois, aseg.affine, hdr2)
        nb.save(img, out_roi)

        iflogger.info("[ DONE ]")


def create_wm_mask(subject_id, subjects_dir, fs_dir, parcellation_name):
    import cmp
    import scipy.ndimage.morphology as nd
    iflogger.info("Create white matter mask")
    fs_dir = op.join(subjects_dir, subject_id)
    cmp_config = cmp.configuration.PipelineConfiguration()
    cmp_config.parcellation_scheme = "Lausanne2008"
    pgpath = cmp_config._get_lausanne_parcellation('Lausanne2008')[
        parcellation_name]['node_information_graphml']
    # load ribbon as basis for white matter mask
    fsmask = nb.load(op.join(fs_dir, 'mri', 'ribbon.nii.gz'))
    fsmaskd = fsmask.get_data()

    wmmask = np.zeros(fsmaskd.shape)
    # extract right and left white matter
    idx_lh = np.where(fsmaskd == 120)
    idx_rh = np.where(fsmaskd == 20)

    wmmask[idx_lh] = 1
    wmmask[idx_rh] = 1

    # remove subcortical nuclei from white matter mask
    aseg = nb.load(op.join(fs_dir, 'mri', 'aseg.nii.gz'))
    asegd = aseg.get_data()

    # need binary erosion function
    imerode = nd.binary_erosion

    # ventricle erosion
    csfA = np.zeros(asegd.shape)
    csfB = np.zeros(asegd.shape)

    # structuring elements for erosion
    se1 = np.zeros((3, 3, 5))
    se1[1, :, 2] = 1
    se1[:, 1, 2] = 1
    se1[1, 1, :] = 1
    se = np.zeros((3, 3, 3))
    se[1, :, 1] = 1
    se[:, 1, 1] = 1
    se[1, 1, :] = 1

    # lateral ventricles, thalamus proper and caudate
    # the latter two removed for better erosion, but put back afterwards
    idx = np.where((asegd == 4) | (asegd == 43) | (asegd == 11) | (asegd == 50)
                   | (asegd == 31) | (asegd == 63) | (asegd == 10)
                   | (asegd == 49))
    csfA[idx] = 1
    csfA = imerode(imerode(csfA, se1), se)

    # thalmus proper and cuadate are put back because they are not lateral ventricles
    idx = np.where((asegd == 11) | (asegd == 50) | (asegd == 10)
                   | (asegd == 49))
    csfA[idx] = 0

    # REST CSF, IE 3RD AND 4TH VENTRICULE AND EXTRACEREBRAL CSF
    idx = np.where((asegd == 5) | (asegd == 14) | (asegd == 15) | (asegd == 24)
                   | (asegd == 44) | (asegd == 72) | (asegd == 75)
                   | (asegd == 76) | (asegd == 213) | (asegd == 221))
    # 43 ??, 4??  213?, 221?
    # more to discuss.
    for i in [5, 14, 15, 24, 44, 72, 75, 76, 213, 221]:
        idx = np.where(asegd == i)
        csfB[idx] = 1

    # do not remove the subthalamic nucleus for now from the wm mask
    # 23, 60
    # would stop the fiber going to the segmented "brainstem"

    # grey nuclei, either with or without erosion
    gr_ncl = np.zeros(asegd.shape)

    # with erosion
    for i in [10, 11, 12, 49, 50, 51]:
        idx = np.where(asegd == i)
        # temporary volume
        tmp = np.zeros(asegd.shape)
        tmp[idx] = 1
        tmp = imerode(tmp, se)
        idx = np.where(tmp == 1)
        gr_ncl[idx] = 1

    # without erosion
    for i in [13, 17, 18, 26, 52, 53, 54, 58]:
        idx = np.where(asegd == i)
        gr_ncl[idx] = 1

    # remove remaining structure, e.g. brainstem
    remaining = np.zeros(asegd.shape)
    idx = np.where(asegd == 16)
    remaining[idx] = 1

    # now remove all the structures from the white matter
    idx = np.where((csfA != 0) | (csfB != 0) | (gr_ncl != 0)
                   | (remaining != 0))
    wmmask[idx] = 0
    iflogger.info(
        "Removing lateral ventricles and eroded grey nuclei and brainstem from white matter mask"
    )

    # ADD voxels from 'cc_unknown.nii.gz' dataset
    ccun = nb.load(op.join(fs_dir, 'label', 'cc_unknown.nii.gz'))
    ccund = ccun.get_data()
    idx = np.where(ccund != 0)
    iflogger.info("Add corpus callosum and unknown to wm mask")
    wmmask[idx] = 1

    # check if we should subtract the cortical rois from this parcellation
    iflogger.info('Loading ROI_%s.nii.gz to subtract cortical ROIs from white '
                  'matter mask', parcellation_name)
    roi = nb.load(op.join(op.curdir, 'ROI_%s.nii.gz' % parcellation_name))
    roid = roi.get_data()
    assert roid.shape[0] == wmmask.shape[0]
    pg = nx.read_graphml(pgpath)
    for brk, brv in pg.nodes(data=True):
        if brv['dn_region'] == 'cortical':
            iflogger.info('Subtracting region %s with intensity value %s',
                          brv['dn_region'], brv['dn_correspondence_id'])
            idx = np.where(roid == int(brv['dn_correspondence_id']))
            wmmask[idx] = 0

    # output white matter mask. crop and move it afterwards
    wm_out = op.join(fs_dir, 'mri', 'fsmask_1mm.nii.gz')
    img = nb.Nifti1Image(wmmask, fsmask.affine, fsmask.header)
    iflogger.info('Save white matter mask: %s', wm_out)
    nb.save(img, wm_out)


def crop_and_move_datasets(subject_id, subjects_dir, fs_dir, parcellation_name,
                           out_roi_file, dilation):
    from cmp.util import runCmd
    fs_dir = op.join(subjects_dir, subject_id)
    cmp_config = cmp.configuration.PipelineConfiguration()
    cmp_config.parcellation_scheme = "Lausanne2008"
    log = cmp_config.get_logger()
    output_dir = op.abspath(op.curdir)

    iflogger.info('Cropping and moving datasets to %s', output_dir)
    ds = [(op.join(fs_dir, 'mri', 'aseg.nii.gz'),
           op.abspath('aseg.nii.gz')), (op.join(fs_dir, 'mri',
                                                'ribbon.nii.gz'),
                                        op.abspath('ribbon.nii.gz')),
          (op.join(fs_dir, 'mri', 'fsmask_1mm.nii.gz'),
           op.abspath('fsmask_1mm.nii.gz')), (op.join(fs_dir, 'label',
                                                      'cc_unknown.nii.gz'),
                                              op.abspath('cc_unknown.nii.gz'))]

    ds.append((op.abspath('ROI_%s.nii.gz' % parcellation_name),
               op.abspath('ROI_HR_th.nii.gz')))
    if dilation is True:
        ds.append((op.abspath('ROIv_%s.nii.gz' % parcellation_name),
                   op.abspath('ROIv_HR_th.nii.gz')))
    orig = op.join(fs_dir, 'mri', 'orig', '001.mgz')
    for d in ds:
        iflogger.info('Processing %s:', d[0])
        if not op.exists(d[0]):
            raise Exception('File %s does not exist.' % d[0])
        # reslice to original volume because the roi creation with freesurfer
        # changed to 256x256x256 resolution
        mri_cmd = 'mri_convert -rl "%s" -rt nearest "%s" -nc "%s"' % (orig,
                                                                      d[0],
                                                                      d[1])
        runCmd(mri_cmd, log)


def extract(Z, shape, position, fill):
    """ Extract voxel neighbourhood
Parameters
----------
Z: the original data
shape: tuple containing neighbourhood dimensions
position: tuple containing central point indexes
fill: value for the padding of Z
Returns
-------
R: the neighbourhood of the specified point in Z
"""
    R = np.ones(shape, dtype=Z.dtype) * \
        fill  # initialize output block to the fill value
    P = np.array(list(position)).astype(
        int)  # position coordinates(numpy array)
    Rs = np.array(list(R.shape)).astype(
        int)  # output block dimensions (numpy array)
    Zs = np.array(list(Z.shape)).astype(
        int)  # original volume dimensions (numpy array)

    R_start = np.zeros(len(shape)).astype(int)
    R_stop = np.array(list(shape)).astype(int)
    Z_start = (P - Rs // 2)
    Z_start_cor = (np.maximum(Z_start, 0)).tolist()  # handle borders
    R_start = R_start + (Z_start_cor - Z_start)
    Z_stop = (P + Rs // 2) + Rs % 2
    Z_stop_cor = (np.minimum(Z_stop, Zs)).tolist()  # handle borders
    R_stop = R_stop - (Z_stop - Z_stop_cor)

    R[R_start[0]:R_stop[0], R_start[1]:R_stop[1], R_start[2]:R_stop[
        2]] = Z[Z_start_cor[0]:Z_stop_cor[0], Z_start_cor[1]:Z_stop_cor[1],
                Z_start_cor[2]:Z_stop_cor[2]]

    return R


class ParcellateInputSpec(BaseInterfaceInputSpec):
    subject_id = traits.String(mandatory=True, desc='Subject ID')
    parcellation_name = traits.Enum(
        'scale500', ['scale33', 'scale60', 'scale125', 'scale250', 'scale500'],
        usedefault=True)
    freesurfer_dir = Directory(exists=True, desc='Freesurfer main directory')
    subjects_dir = Directory(exists=True, desc='Freesurfer subjects directory')
    out_roi_file = File(
        genfile=True, desc='Region of Interest file for connectivity mapping')
    dilation = traits.Bool(
        False,
        usedefault=True,
        desc='Dilate cortical parcels? Useful for fMRI connectivity')


class ParcellateOutputSpec(TraitedSpec):
    roi_file = File(
        exists=True, desc='Region of Interest file for connectivity mapping')
    roiv_file = File(
        desc='Region of Interest file for fMRI connectivity mapping')
    white_matter_mask_file = File(exists=True, desc='White matter mask file')
    cc_unknown_file = File(
        desc='Image file with regions labelled as unknown cortical structures',
        exists=True)
    ribbon_file = File(
        desc='Image file detailing the cortical ribbon', exists=True)
    aseg_file = File(
        desc=
        'Automated segmentation file converted from Freesurfer "subjects" directory',
        exists=True)
    roi_file_in_structural_space = File(
        desc=
        'ROI image resliced to the dimensions of the original structural image',
        exists=True)
    dilated_roi_file_in_structural_space = File(
        desc=
        'dilated ROI image resliced to the dimensions of the original structural image'
    )


class Parcellate(LibraryBaseInterface):
    """Subdivides segmented ROI file into smaller subregions

    This interface implements the same procedure as in the ConnectomeMapper's
    parcellation stage (cmp/stages/parcellation/maskcreation.py) for a single
    parcellation scheme (e.g. 'scale500').

    Example
    -------

    >>> import nipype.interfaces.cmtk as cmtk
    >>> parcellate = cmtk.Parcellate()
    >>> parcellate.inputs.freesurfer_dir = '.'
    >>> parcellate.inputs.subjects_dir = '.'
    >>> parcellate.inputs.subject_id = 'subj1'
    >>> parcellate.inputs.dilation = True
    >>> parcellate.inputs.parcellation_name = 'scale500'
    >>> parcellate.run()                 # doctest: +SKIP
    """

    input_spec = ParcellateInputSpec
    output_spec = ParcellateOutputSpec
    _pkg = 'cmp'
    imports = ('scipy', )

    def _run_interface(self, runtime):
        if self.inputs.subjects_dir:
            os.environ.update({'SUBJECTS_DIR': self.inputs.subjects_dir})

        if not os.path.exists(
                op.join(self.inputs.subjects_dir, self.inputs.subject_id)):
            raise Exception
        iflogger.info("ROI_HR_th.nii.gz / fsmask_1mm.nii.gz CREATION")
        iflogger.info("=============================================")
        create_annot_label(self.inputs.subject_id, self.inputs.subjects_dir,
                           self.inputs.freesurfer_dir,
                           self.inputs.parcellation_name)
        create_roi(self.inputs.subject_id, self.inputs.subjects_dir,
                   self.inputs.freesurfer_dir, self.inputs.parcellation_name,
                   self.inputs.dilation)
        create_wm_mask(self.inputs.subject_id, self.inputs.subjects_dir,
                       self.inputs.freesurfer_dir,
                       self.inputs.parcellation_name)
        crop_and_move_datasets(
            self.inputs.subject_id, self.inputs.subjects_dir,
            self.inputs.freesurfer_dir, self.inputs.parcellation_name,
            self.inputs.out_roi_file, self.inputs.dilation)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.out_roi_file):
            outputs['roi_file'] = op.abspath(self.inputs.out_roi_file)
        else:
            outputs['roi_file'] = op.abspath(
                self._gen_outfilename('nii.gz', 'ROI'))
        if self.inputs.dilation is True:
            outputs['roiv_file'] = op.abspath(
                self._gen_outfilename('nii.gz', 'ROIv'))
        outputs['white_matter_mask_file'] = op.abspath('fsmask_1mm.nii.gz')
        outputs['cc_unknown_file'] = op.abspath('cc_unknown.nii.gz')
        outputs['ribbon_file'] = op.abspath('ribbon.nii.gz')
        outputs['aseg_file'] = op.abspath('aseg.nii.gz')
        outputs['roi_file_in_structural_space'] = op.abspath(
            'ROI_HR_th.nii.gz')
        if self.inputs.dilation is True:
            outputs['dilated_roi_file_in_structural_space'] = op.abspath(
                'ROIv_HR_th.nii.gz')
        return outputs

    def _gen_outfilename(self, ext, prefix='ROI'):
        return prefix + '_' + self.inputs.parcellation_name + '.' + ext
