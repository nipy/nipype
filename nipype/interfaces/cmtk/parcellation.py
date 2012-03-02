# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)

"""

from nipype.interfaces.base import (BaseInterface, BaseInterfaceInputSpec, traits,
                                    File, TraitedSpec, Directory, isdefined)
import os, os.path as op
import numpy as np
import nibabel as nb
import networkx as nx
import shutil
from nipype.utils.misc import package_check
import warnings

have_cmp = True
try:
    package_check('cmp')
except Exception, e:
    have_cmp = False
    warnings.warn('cmp not installed')
else:
    import cmp
    from cmp.util import runCmd

def create_annot_label(subject_id, subjects_dir, fs_dir, parcellation_name):
    print "Create the cortical labels necessary for our ROIs"
    print "================================================="
    fs_label_dir = op.join(op.join(subjects_dir,subject_id), 'label')
    output_dir = op.abspath(op.curdir)
    paths = []
    cmp_config = cmp.configuration.PipelineConfiguration()
    cmp_config.parcellation_scheme = "Lausanne2008"
    for hemi in ['lh', 'rh']:
        spath = cmp_config._get_lausanne_parcellation('Lausanne2008')[parcellation_name]['fs_label_subdir_name'] % hemi
        paths.append(spath)
    for p in paths:
        try:
            os.makedirs(op.join('.', p))
        except:
            pass

    comp = [
    ('rh', 'myatlas_36_rh.gcs', 'rh.myaparc_36.annot', 'regenerated_rh_36','myaparc_36'),
    ('rh', 'myatlasP1_16_rh.gcs','rh.myaparcP1_16.annot','regenerated_rh_500','myaparcP1_16'),
    ('rh', 'myatlasP17_28_rh.gcs','rh.myaparcP17_28.annot','regenerated_rh_500','myaparcP17_28'),
    ('rh', 'myatlasP29_36_rh.gcs','rh.myaparcP29_36.annot','regenerated_rh_500','myaparcP29_36'),
    ('rh','myatlas_60_rh.gcs','rh.myaparc_60.annot','regenerated_rh_60','myaparc_60'),
    ('rh','myatlas_125_rh.gcs','rh.myaparc_125.annot','regenerated_rh_125','myaparc_125'),
    ('rh','myatlas_250_rh.gcs','rh.myaparc_250.annot','regenerated_rh_250','myaparc_250'),
    ('lh', 'myatlas_36_lh.gcs', 'lh.myaparc_36.annot', 'regenerated_lh_36','myaparc_36'),
    ('lh', 'myatlasP1_16_lh.gcs','lh.myaparcP1_16.annot','regenerated_lh_500','myaparcP1_16'),
    ('lh', 'myatlasP17_28_lh.gcs','lh.myaparcP17_28.annot','regenerated_lh_500','myaparcP17_28'),
    ('lh', 'myatlasP29_36_lh.gcs','lh.myaparcP29_36.annot','regenerated_lh_500','myaparcP29_36'),
    ('lh','myatlas_60_lh.gcs','lh.myaparc_60.annot','regenerated_lh_60', 'myaparc_60'),
    ('lh','myatlas_125_lh.gcs','lh.myaparc_125.annot','regenerated_lh_125','myaparc_125'),
    ('lh','myatlas_250_lh.gcs','lh.myaparc_250.annot','regenerated_lh_250','myaparc_250'),
    ]
    log = cmp_config.get_logger()

    for out in comp:
        mris_cmd = 'mris_ca_label %s %s "%s/surf/%s.sphere.reg" "%s" "%s" ' % (subject_id, out[0],
		    op.join(subjects_dir,subject_id), out[0], cmp_config.get_lausanne_atlas(out[1]), op.join(fs_label_dir, out[2]))
        runCmd( mris_cmd, log )
        print '-----------'

        annot = '--annotation "%s"' % out[4]

        mri_an_cmd = 'mri_annotation2label --subject %s --hemi %s --outdir "%s" %s' % (subject_id, out[0], op.join(output_dir, out[3]), annot)
        print mri_an_cmd
        runCmd( mri_an_cmd, log )
        print '-----------'
        print os.environ['SUBJECTS_DIR']
    # extract cc and unknown to add to tractography mask, we do not want this as a region of interest
    # in FS 5.0, unknown and corpuscallosum are not available for the 35 scale (why?),
    # but for the other scales only, take the ones from _60
	rhun = op.join(output_dir, 'rh.unknown.label')
	lhun = op.join(output_dir, 'lh.unknown.label')
	rhco = op.join(output_dir, 'rh.corpuscallosum.label')
	lhco = op.join(output_dir, 'lh.corpuscallosum.label')
    shutil.copy(op.join(output_dir, 'regenerated_rh_60', 'rh.unknown.label'), rhun)
    shutil.copy(op.join(output_dir, 'regenerated_lh_60', 'lh.unknown.label'), lhun)
    shutil.copy(op.join(output_dir, 'regenerated_rh_60', 'rh.corpuscallosum.label'), rhco)
    shutil.copy(op.join(output_dir, 'regenerated_lh_60', 'lh.corpuscallosum.label'), lhco)

    mri_cmd = """mri_label2vol --label "%s" --label "%s" --label "%s" --label "%s" --temp "%s" --o  "%s" --identity """ % (rhun, lhun, rhco, lhco, op.join(op.join(subjects_dir,subject_id), 'mri', 'orig.mgz'), op.join(fs_label_dir, 'cc_unknown.nii.gz') )
    runCmd( mri_cmd, log )
    runCmd( 'mris_volmask %s' % subject_id , log)
    mri_cmd = 'mri_convert -i "%s/mri/ribbon.mgz" -o "%s/mri/ribbon.nii.gz"' % (op.join(subjects_dir,subject_id), op.join(subjects_dir,subject_id))
    runCmd( mri_cmd, log )
    mri_cmd = 'mri_convert -i "%s/mri/aseg.mgz" -o "%s/mri/aseg.nii.gz"' % (op.join(subjects_dir,subject_id), op.join(subjects_dir,subject_id))
    runCmd( mri_cmd, log )

    print "[ DONE ]"

def create_roi(subject_id, subjects_dir, fs_dir, parcellation_name):
    """ Creates the ROI_%s.nii.gz files using the given parcellation information
    from networks. Iteratively create volume. """
    print "Create the ROIs:"
    output_dir = op.abspath(op.curdir)
    fs_dir = op.join(subjects_dir, subject_id)
    cmp_config = cmp.configuration.PipelineConfiguration()
    cmp_config.parcellation_scheme = "Lausanne2008"
    log = cmp_config.get_logger()
    parval = cmp_config._get_lausanne_parcellation('Lausanne2008')[parcellation_name]
    pgpath = parval['node_information_graphml']
    aseg = nb.load(op.join(fs_dir, 'mri', 'aseg.nii.gz'))
    asegd = aseg.get_data()

    print "Working on parcellation: "
    print cmp_config._get_lausanne_parcellation('Lausanne2008')[parcellation_name]
    print "========================"
    pg = nx.read_graphml(pgpath)
    # each node represents a brain region
    # create a big 256^3 volume for storage of all ROIs
    rois = np.zeros( (256, 256, 256), dtype=np.int16 )

    count = 0
    for brk, brv in pg.nodes_iter(data=True):
        count = count + 1
        print brv
        print brk
        if brv['dn_hemisphere'] == 'left':
            hemi = 'lh'
        elif brv['dn_hemisphere'] == 'right':
            hemi = 'rh'
        if brv['dn_region'] == 'subcortical':
            print brv
            print "---------------------"
            print "Work on brain region: %s" % (brv['dn_region'])
            print "Freesurfer Name: %s" %  brv['dn_fsname']
            print "Region %s of %s " % (count, pg.number_of_nodes())
            print "---------------------"
            # if it is subcortical, retrieve roi from aseg
            idx = np.where(asegd == int(brv['dn_fs_aseg_val']))
            rois[idx] = int(brv['dn_correspondence_id'])

        elif brv['dn_region'] == 'cortical':
            print brv
            print "---------------------"
            print "Work on brain region: %s" % (brv['dn_region'])
            print "Freesurfer Name: %s" %  brv['dn_fsname']
            print "Region %s of %s " % (count, pg.number_of_nodes())
            print "---------------------"

            labelpath = op.join(output_dir, parval['fs_label_subdir_name'] % hemi)
            # construct .label file name

            fname = '%s.%s.label' % (hemi, brv['dn_fsname'])

            # execute fs mri_label2vol to generate volume roi from the label file
            # store it in temporary file to be overwritten for each region

            mri_cmd = 'mri_label2vol --label "%s" --temp "%s" --o "%s" --identity' % (op.join(labelpath, fname),
                    op.join(fs_dir, 'mri', 'orig.mgz'), op.join(output_dir, 'tmp.nii.gz'))
            runCmd( mri_cmd, log )

            tmp = nb.load(op.join(output_dir, 'tmp.nii.gz'))
            tmpd = tmp.get_data()

            # find voxel and set them to intensityvalue in rois
            idx = np.where(tmpd == 1)
            rois[idx] = int(brv['dn_correspondence_id'])

        # store volume eg in ROI_scale33.nii.gz
        out_roi = op.join(output_dir, 'ROI_%s.nii.gz' % parcellation_name)

        # update the header
        hdr = aseg.get_header()
        hdr2 = hdr.copy()
        hdr2.set_data_dtype(np.uint16)

        log.info("Save output image to %s" % out_roi)
        img = nb.Nifti1Image(rois, aseg.get_affine(), hdr2)
        nb.save(img, out_roi)

    print "[ DONE ]"


def create_wm_mask(subject_id, subjects_dir, fs_dir, parcellation_name):
    print "Create white matter mask"
    fs_dir = op.join(subjects_dir, subject_id)
    cmp_config = cmp.configuration.PipelineConfiguration()
    cmp_config.parcellation_scheme = "Lausanne2008"
    log = cmp_config.get_logger()
    pgpath = cmp_config._get_lausanne_parcellation('Lausanne2008')[parcellation_name]['node_information_graphml']
    # load ribbon as basis for white matter mask
    fsmask = nb.load(op.join(fs_dir, 'mri', 'ribbon.nii.gz'))
    fsmaskd = fsmask.get_data()

    wmmask = np.zeros( fsmaskd.shape )
    # extract right and left white matter
    idx_lh = np.where(fsmaskd == 120)
    idx_rh = np.where(fsmaskd == 20)

    wmmask[idx_lh] = 1
    wmmask[idx_rh] = 1

    # remove subcortical nuclei from white matter mask
    aseg = nb.load(op.join(fs_dir, 'mri', 'aseg.nii.gz'))
    asegd = aseg.get_data()

    try:
        import scipy.ndimage.morphology as nd
    except ImportError:
        raise Exception('Need scipy for binary erosion of white matter mask')

    # need binary erosion function
    imerode = nd.binary_erosion

    # ventricle erosion
    csfA = np.zeros( asegd.shape )
    csfB = np.zeros( asegd.shape )

    # structuring elements for erosion
    se1 = np.zeros( (3,3,5) )
    se1[1,:,2] = 1; se1[:,1,2] = 1; se1[1,1,:] = 1
    se = np.zeros( (3,3,3) );
    se[1,:,1] = 1; se[:,1,1] = 1; se[1,1,:] = 1

    # lateral ventricles, thalamus proper and caudate
    # the latter two removed for better erosion, but put back afterwards
    idx = np.where( (asegd == 4) |
                    (asegd == 43) |
                    (asegd == 11) |
                    (asegd == 50) |
                    (asegd == 31) |
                    (asegd == 63) |
                    (asegd == 10) |
                    (asegd == 49) )
    csfA[idx] = 1
    csfA = imerode(imerode(csfA, se1),se)

    # thalmus proper and cuadate are put back because they are not lateral ventricles
    idx = np.where( (asegd == 11) |
                    (asegd == 50) |
                    (asegd == 10) |
                    (asegd == 49) )
    csfA[idx] = 0

    # REST CSF, IE 3RD AND 4TH VENTRICULE AND EXTRACEREBRAL CSF
    idx = np.where( (asegd == 5) |
                    (asegd == 14) |
                    (asegd == 15) |
                    (asegd == 24) |
                    (asegd == 44) |
                    (asegd == 72) |
                    (asegd == 75) |
                    (asegd == 76) |
                    (asegd == 213) |
                    (asegd == 221))
    # 43 ??, 4??  213?, 221?
    # more to discuss.
    for i in [5,14,15,24,44,72,75,76,213,221]:
        idx = np.where(asegd == i)
        csfB[idx] = 1

    # do not remove the subthalamic nucleus for now from the wm mask
    # 23, 60
    # would stop the fiber going to the segmented "brainstem"

    # grey nuclei, either with or without erosion
    gr_ncl = np.zeros( asegd.shape )

    # with erosion
    for i in [10,11,12,49,50,51]:
        idx = np.where(asegd == i)
        # temporary volume
        tmp = np.zeros( asegd.shape )
        tmp[idx] = 1
        tmp = imerode(tmp,se)
        idx = np.where(tmp == 1)
        gr_ncl[idx] = 1

    # without erosion
    for i in [13,17,18,26,52,53,54,58]:
        idx = np.where(asegd == i)
        gr_ncl[idx] = 1

    # remove remaining structure, e.g. brainstem
    remaining = np.zeros( asegd.shape )
    idx = np.where( asegd == 16 )
    remaining[idx] = 1

    # now remove all the structures from the white matter
    idx = np.where( (csfA != 0) | (csfB != 0) | (gr_ncl != 0) | (remaining != 0) )
    wmmask[idx] = 0
    print "Removing lateral ventricles and eroded grey nuclei and brainstem from white matter mask"

    # ADD voxels from 'cc_unknown.nii.gz' dataset
    ccun = nb.load(op.join(fs_dir, 'label', 'cc_unknown.nii.gz'))
    ccund = ccun.get_data()
    idx = np.where(ccund != 0)
    print "Add corpus callosum and unknown to wm mask"
    wmmask[idx] = 1

    # check if we should subtract the cortical rois from this parcellation
    parval = cmp_config._get_lausanne_parcellation('Lausanne2008')[parcellation_name]
    print "Loading %s to subtract cortical ROIs from white matter mask" % ('ROI_%s.nii.gz' % parcellation_name)
    roi = nb.load(op.join(op.curdir, 'ROI_%s.nii.gz' % parcellation_name))
    roid = roi.get_data()
    assert roid.shape[0] == wmmask.shape[0]
    pg = nx.read_graphml(pgpath)
    for brk, brv in pg.nodes_iter(data=True):
        if brv['dn_region'] == 'cortical':
            print "Subtracting region %s with intensity value %s" % (brv['dn_region'], brv['dn_correspondence_id'])
            idx = np.where(roid == int(brv['dn_correspondence_id']))
            wmmask[idx] = 0

    # output white matter mask. crop and move it afterwards
    wm_out = op.join(fs_dir, 'mri', 'fsmask_1mm.nii.gz')
    img = nb.Nifti1Image(wmmask, fsmask.get_affine(), fsmask.get_header() )
    print "Save white matter mask: %s" % wm_out
    nb.save(img, wm_out)

def crop_and_move_datasets(subject_id, subjects_dir, fs_dir, parcellation_name, out_roi_file):
    fs_dir = op.join(subjects_dir, subject_id)
    cmp_config = cmp.configuration.PipelineConfiguration()
    cmp_config.parcellation_scheme = "Lausanne2008"
    log = cmp_config.get_logger()
    pgpath = cmp_config._get_lausanne_parcellation('Lausanne2008')[parcellation_name]['node_information_graphml']
    reg_path = out_roi_file
    output_dir = op.abspath(op.curdir)

    print "Cropping and moving datasets to %s" % output_dir
    ds = [
          (op.join(fs_dir, 'mri', 'aseg.nii.gz'), op.join(output_dir, 'aseg.nii.gz') ),
          (op.join(fs_dir, 'mri', 'ribbon.nii.gz'), op.join(output_dir, 'ribbon.nii.gz') ),
          (op.join(fs_dir, 'mri', 'fsmask_1mm.nii.gz'), op.join(output_dir, 'fsmask_1mm.nii.gz') ),
          (op.join(fs_dir, 'label', 'cc_unknown.nii.gz'), op.join(output_dir, 'cc_unknown.nii.gz') )
          ]

    ds.append( (op.join(op.curdir, 'ROI_%s.nii.gz' % parcellation_name), op.join(op.curdir, 'ROI_HR_th.nii.gz')) )
    orig = op.join(fs_dir, 'mri', 'orig', '001.mgz')
    for d in ds:
        print "Processing %s:" % d[0]
        if not op.exists(d[0]):
            raise Exception('File %s does not exist.' % d[0])
        # reslice to original volume because the roi creation with freesurfer
        # changed to 256x256x256 resolution
        mri_cmd = 'mri_convert -rl "%s" -rt nearest "%s" -nc "%s"' % (orig, d[0], d[1])
        runCmd( mri_cmd,log )

class ParcellateInputSpec(BaseInterfaceInputSpec):
    subject_id = traits.String(mandatory=True, desc='Subject ID')
    parcellation_name = traits.Enum('scale500', ['scale33', 'scale60', 'scale125', 'scale250','scale500'], usedefault=True)
    freesurfer_dir = Directory(desc='Freesurfer main directory')
    subjects_dir = Directory(desc='Freesurfer main directory')
    out_roi_file = File(genfile = True, desc='Region of Interest file for connectivity mapping')

class ParcellateOutputSpec(TraitedSpec):
    roi_file = File(desc='Region of Interest file for connectivity mapping')

class Parcellate(BaseInterface):
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
    >>> parcellate.inputs.parcellation_name = 'scale500'
    >>> parcellate.run()                 # doctest: +SKIP
    """

    input_spec = ParcellateInputSpec
    output_spec = ParcellateOutputSpec

    def _run_interface(self, runtime):
        if self.inputs.subjects_dir:
           os.environ.update({'SUBJECTS_DIR': self.inputs.subjects_dir})
        print "ROI_HR_th.nii.gz / fsmask_1mm.nii.gz CREATION"
        print "============================================="
        create_annot_label(self.inputs.subject_id, self.inputs.subjects_dir, self.inputs.freesurfer_dir, self.inputs.parcellation_name)
        create_roi(self.inputs.subject_id, self.inputs.subjects_dir, self.inputs.freesurfer_dir, self.inputs.parcellation_name)
        create_wm_mask(self.inputs.subject_id, self.inputs.subjects_dir, self.inputs.freesurfer_dir, self.inputs.parcellation_name)
        crop_and_move_datasets(self.inputs.subject_id, self.inputs.subjects_dir, self.inputs.freesurfer_dir, self.inputs.parcellation_name, self.inputs.out_roi_file)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.out_roi_file):
            outputs['roi_file'] = op.abspath(self.inputs.out_roi_file)
        else:
            outputs['roi_file'] = op.abspath(self._gen_outfilename('nii.gz', 'ROI'))
        return outputs

    def _gen_outfilename(self, ext, prefix='ROI'):
        return prefix + '_' + self.inputs.parcellation_name + '.' + ext
