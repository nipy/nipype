import nipype
import nipype.pipeline.engine as pe  # pypeline engine
from nipype.interfaces.io import DataGrabber
from nipype.interfaces.freesurfer import MRIConvert, MRIsConvert
import SimpleITK as sitk
import os
import sys
import errno


def awkfile(awk_file, log_file):
    """
    This method uses 'awk' which must be installed prior to running the workflow and is not a
    part of nipype or freesurfer.
    Future work may be done to create a method that achieves the same results using a python
    script.
    """
    import subprocess
    import os
    command = ['awk', '-f', awk_file, log_file]
    print(''.join(command))
    subprocess.call(command)
    log_file = os.path.abspath(log_file)
    return log_file

def copy_files(in_files, out_files):
    """
    Create a function to copy a file that can be modified by a following node 
    without changing the original file
    """
    import shutil
    if len(in_files) != len(out_files):
        print "ERROR: Length of input files must be identical to the length of \
        outrput files to be copied"
        sys.exit(-1)
    for i, in_file in enumerate(in_files):
        out_file = out_files[i]
        print "copying %s to %s" % (in_file, out_file)
        shutil.copy(in_file, out_file)
    return out_files

def copy_file(in_file, out_file=None):
    """
    Create a function to copy a file that can be modified by a following node 
    without changing the original file.
    """
    import os
    import shutil
    if out_file == None:
        out_file = os.path.join(os.getcwd(), os.path.basename(in_file))
    if type(in_file) is list and len(in_file) == 1:
        in_file = in_file[0]
    out_file = os.path.abspath(out_file)
    in_file = os.path.abspath(in_file)
    print "copying %s to %s" % (in_file, out_file)
    shutil.copy(in_file, out_file)
    return out_file

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
        
def getdefaultconfig():
    config = { 'custom_atlas' : None,
               'cw256' : False,
               'cache_dir' : os.getcwd(),
               'field_strength' : '1.5T',
               'fs_home' : checkenv(),
               'in_T1s' : list(),
               'in_T2' : None,
               'in_FLAIR' : None,
               'longitudinal' : False,
               'long_base' : None,
               'openmp' : None,
               'plugin' : 'Linear',
               'plugin_args' : None,
               'qcache' : False,
               'queue' : None,
               'recoding_file' : None,
               'src_subject_id' : 'fsaverage',
               'subject_id' : None,
               'subjects_dir' : None,
               'timepoints' : list() }
    config['source_subject'] = os.path.join(config['fs_home'], 'subjects',
                                            config['src_subject_id'])
    config['awk_file'] = os.path.join(config['fs_home'], 'bin',
                                      'extract_talairach_avi_QA.awk')
    config['registration_template'] = os.path.join(config['fs_home'], 'average',
                                                   'RB_all_withskull_2014-08-21.gca')
    for hemi in ('lh', 'rh'):
        config['{0}_atlas'.format(hemi)] = os.path.join(
            config['fs_home'], 'average',
            '{0}.average.curvature.filled.buckner40.tif'.format(hemi))
        config['{0}_classifier'.format(hemi)] = os.path.join(
            config['fs_home'], 'average',
            'rh.curvature.buckner40.filled.desikan_killiany.2010-03-25.gcs'.format(hemi))
        config['{0}_classifier2'.format(hemi)] = os.path.join(
            config['fs_home'], 'average',
            '{0}.destrieux.simple.2009-07-29.gcs'.format(hemi))
        config['{0}_classifier3'.format(hemi)] = os.path.join(
            config['fs_home'], 'average',
            '{0}.DKTatlas40.gcs'.format(hemi))
    config['LookUpTable'] = os.path.join(config['fs_home'], 'ASegStatsLUT.txt')
    config['WMLookUpTable'] = os.path.join(config['fs_home'], 'WMParcStatsLUT.txt')
    return config


def checkenv():
    """Check for the necessary FS environment variables"""
    fs_home = os.environ.get('FREESURFER_HOME')
    path = os.environ.get('PATH')
    print("FREESURFER_HOME: {0}".format(fs_home))
    if fs_home == None:
        print("ERROR: please set FREESURFER_HOME before running the workflow")
    elif not os.path.isdir(fs_home):
        print("ERROR: FREESURFER_HOME must be set to a valid directory before " + 
        "running this workflow")
    elif os.path.join(fs_home, 'bin') not in path.replace('//','/'):
        print(path)
        print("ERROR: Could not find necessary executable in path")
        setupscript = os.path.join(fs_home, 'SetUpFreeSurfer.sh')
        if os.path.isfile(setupscript):
            print("Please source the setup script before running the workflow:" +
            "\nsource {0}".format(setupscript))
        else:
            print("Please ensure that FREESURFER_HOME is set to a valid fs " +
            "directory and source the necessary SetUpFreeSurfer.sh script before running " +
            "this workflow")
    else:        
        return fs_home
    sys.exit(2)


def modify_qsub_args(queue, memoryGB, minThreads, maxThreads, stdout='/dev/null', stderr='/dev/null'):
    """
    Code from BRAINSTools:
    https://github.com/BRAINSia/BRAINSTools.git
    BRAINSTools/AutoWorkup/utilities/distributed.py

    Outputs qsub_args string for Nipype nodes
    queue is the string to specify the queue "-q all.q | -q HJ,ICTS,UI"
    memoryGB is a numeric in gigabytes to be given (ie 2.1 will result in "-l mem_free=2.1G")
          if memoryGB = 0, then it is automatically computed.
    minThreads The fewest number of threads to use (if an algorithm has benifits from more than 1 thread)
    maxThreads The max number of threads to use (if an algorithm is not multi-threaded, then just use 1)
    stdout Where to put stdout logs
    stderr Where to put stderr logs

    >>> modify_qsub_args('test', 2, 5, None)
    -S /bin/bash -cwd -pe smp 5 -l mem_free=2G -o /dev/null -e /dev/null test FAIL
    >>> modify_qsub_args('test', 2, 5, -1 )
    -S /bin/bash -cwd -pe smp 5- -l mem_free=2G -o /dev/null -e /dev/null test FAIL
    >>> modify_qsub_args('test', 8, 5, 7)
    -S /bin/bash -cwd -pe smp 5-7 -l mem_free=8G -o /dev/null -e /dev/null test FAIL
    >>> modify_qsub_args('test', 8, 5, 7, -1)
    -S /bin/bash -cwd -pe smp 5-7 -l mem_free=8G -o /dev/null -e /dev/null test FAIL
    >>> modify_qsub_args('test', 1, 5, 7, stdout='/my/path', stderr='/my/error')
    -S /bin/bash -cwd -pe smp 5-7 -l mem_free=1G -o /my/path -e /my/error test FAIL
    """
    import math
    assert memoryGB <= 48 , "Memory must be supplied in GB, so anything more than 24 seems not-useful now."

    ## NOTE: At least 1 thread needs to be requested per 2GB needed
    memoryThreads = int(math.ceil(memoryGB/float(2))) #Ensure that threads are integers
    minThreads = max(minThreads, memoryThreads)
    maxThreads = max(maxThreads, memoryThreads)
    maxThreads=int(maxThreads) # Ensure that threads are integers
    minThreads=int(minThreads) # Ensure that threads are integers

    if maxThreads is None or minThreads == maxThreads:
       threadsRangeString =  '{0}'.format(minThreads)
       maxThreads = minThreads
    elif maxThreads == -1:
       threadsRangeString= '{0}-'.format(minThreads)
       maxThreads = 12345 #HUGE NUMBER!
    else:
       threadsRangeString= "{0}-{1}".format(minThreads,maxThreads)

    if maxThreads < minThreads:
       assert  maxThreads > minThreads, "Must specify maxThreads({0}) > minThreads({1})".format(minThreads,maxThreads)
    format_str = '-q {queue} -S /bin/bash -cwd -pe smp {totalThreads} -o {stdout} -e {stderr}'.format(
                 mint=minThreads, maxt=threadsRangeString,
                 totalThreads=threadsRangeString,
                 mem=memoryGB,
                 stdout=stdout, stderr=stderr, queue=queue)
    return format_str

def center_volume(in_file):
    import SimpleITK as sitk
    import os
    img = sitk.ReadImage(in_file)
    size = img.GetSize()
    origin = img.GetOrigin()
    new_origin = [0,0,0]
    for i, xx in enumerate(origin):
        new_origin[i] = float(size[i])/2
        if xx < 0:
            new_origin[i] = -new_origin[i]
    img.SetOrigin(new_origin)
    out_file = os.path.abspath(os.path.basename(in_file))
    sitk.WriteImage(img, out_file)
    return out_file


def recodeLabelMap(in_file, out_file, recode_file):
    """This function has been adapted from BRAINSTools and serves
    as a means to recode a label map based upon an input csv
    file."""
    import SimpleITK as sitk
    import os
    import csv
    import sys

    # Convert csv to RECODE_TABLE
    CSVFile = open(recode_file, 'rb')
    reader = csv.reader(CSVFile)
    header = reader.next()
    n_cols = len(header)
    if n_cols == 4:
        # ignore label names
        label_keys = (0, 2)
    elif n_cols == 2:
        # no label names present
        label_keys = (0, 1)
    else:
        # csv does not match format requirements
        print("ERROR: input csv file for label recoding does meet requirements")
        sys.exit()

    # read csv file
    RECODE_TABLE = list()
    for line in reader:
        RECODE_TABLE.append((int(line[label_keys[0]]), int(line[label_keys[1]])))
        
    def minimizeSizeOfImage(outlabels):
        """This function will find the largest integer value in the labelmap, and
        cast the image to the smallest possible integer size so that no loss of data
        results."""
        measureFilt  = sitk.StatisticsImageFilter()
        measureFilt.Execute(outlabels)
        imgMin=measureFilt.GetMinimum()
        imgMax=measureFilt.GetMaximum()
        if imgMax < (2**8)-1:
            outlabels = sitk.Cast( outlabels, sitk.sitkUInt8 )
        elif imgMax < (2**16)-1:
            outlabels = sitk.Cast( outlabels, sitk.sitkUInt16 )
        elif imgMax < (2**32)-1:
            outlabels = sitk.Cast( outlabels, sitk.sitkUInt32 )
        elif imgMax < (2**64)-1:
            outlabels = sitk.Cast( outlabels, sitk.sitkUInt64 )
        return outlabels
    
    LabelImage=sitk.Cast(sitk.ReadImage(in_file), sitk.sitkUInt32)
    for (old, new) in RECODE_TABLE:
        LabelImage = sitk.Cast((LabelImage == old), sitk.sitkUInt32)*(new - old)+LabelImage
    LabelImage = minimizeSizeOfImage(LabelImage)
    out_file = os.path.abspath(out_file)
    sitk.WriteImage(LabelImage, out_file)
    return out_file


def create_recoding_wf(in_file, out_file=None):
    wf = nipype.Workflow(name="RecodeLabels")

    inputspec = nipype.pipeline.Node(nipype.IdentityInterface(['labelmap',
                                                               'recode_file']), 
                                     name="inputspec")
    inputspec.inputs.recode_file = in_file

    convert_labelmap = nipype.pipeline.Node(MRIConvert(), name="ConvertLabelMap")
    convert_labelmap.inputs.in_type = 'mgz'
    convert_labelmap.inputs.out_type = 'nii'
    convert_labelmap.inputs.out_orientation = 'RAS'
    convert_labelmap.inputs.out_file = 'labelmap.nii'
    wf.connect([(inputspec, convert_labelmap, [('labelmap', 'in_file')])])

    recode = nipype.Node(nipype.Function(['in_file',
                                          'out_file',
                                          'recode_file'],
                                         ['out_file'],
                                         recodeLabelMap), 
                         name = "RecodeLabelMap")
    if out_file == None:
        recode.inputs.out_file = 'recodedlabelmap.nii'
    else:
        recode.inputs.out_file = out_file

    wf.connect([(convert_labelmap, recode, [('out_file', 'in_file')]),
                (inputspec, recode, [('recode_file', 'recode_file')])])

    center_labelmap = nipype.Node(nipype.Function(['in_file'], ['out_file'],
                                                  center_volume),
                                  name="CenterLabelMap")

    wf.connect([(recode, center_labelmap, [('out_file', 'in_file')])])

    outputspec = nipype.Node(nipype.IdentityInterface(['recodedlabelmap']), name="outputspec")

    wf.connect([(center_labelmap, outputspec, [('out_file', 'recodedlabelmap')])])    
    return wf

def createsrcsubj(source_directory):
    """
    Returns a node that acts as the datasource for a source subject such as 
    'fsaverage'
    """
    outfields = ['lh_BA1_exvivo',
                 'lh_BA2_exvivo',
                 'lh_BA3a_exvivo',
                 'lh_BA3b_exvivo',
                 'lh_BA4a_exvivo',
                 'lh_BA4p_exvivo',
                 'lh_BA6_exvivo',
                 'lh_BA44_exvivo',
                 'lh_BA45_exvivo',
                 'lh_V1_exvivo',
                 'lh_V2_exvivo',
                 'lh_MT_exvivo',
                 'lh_entorhinal_exvivo',
                 'lh_perirhinal_exvivo',
                 'lh_BA1_exvivo_thresh',
                 'lh_BA2_exvivo_thresh',
                 'lh_BA3a_exvivo_thresh',
                 'lh_BA3b_exvivo_thresh',
                 'lh_BA4a_exvivo_thresh',
                 'lh_BA4p_exvivo_thresh',
                 'lh_BA6_exvivo_thresh',
                 'lh_BA44_exvivo_thresh',
                 'lh_BA45_exvivo_thresh',
                 'lh_V1_exvivo_thresh',
                 'lh_V2_exvivo_thresh',
                 'lh_MT_exvivo_thresh',
                 'lh_entorhinal_exvivo_thresh',
                 'lh_perirhinal_exvivo_thresh',
                 'rh_BA1_exvivo',
                 'rh_BA2_exvivo',
                 'rh_BA3a_exvivo',
                 'rh_BA3b_exvivo',
                 'rh_BA4a_exvivo',
                 'rh_BA4p_exvivo',
                 'rh_BA6_exvivo',
                 'rh_BA44_exvivo',
                 'rh_BA45_exvivo',
                 'rh_V1_exvivo',
                 'rh_V2_exvivo',
                 'rh_MT_exvivo',
                 'rh_entorhinal_exvivo',
                 'rh_perirhinal_exvivo',
                 'rh_BA1_exvivo_thresh',
                 'rh_BA2_exvivo_thresh',
                 'rh_BA3a_exvivo_thresh',
                 'rh_BA3b_exvivo_thresh',
                 'rh_BA4a_exvivo_thresh',
                 'rh_BA4p_exvivo_thresh',
                 'rh_BA6_exvivo_thresh',
                 'rh_BA44_exvivo_thresh',
                 'rh_BA45_exvivo_thresh',
                 'rh_V1_exvivo_thresh',
                 'rh_V2_exvivo_thresh',
                 'rh_MT_exvivo_thresh',
                 'rh_entorhinal_exvivo_thresh',
                 'rh_perirhinal_exvivo_thresh']
    datasource = pe.Node(nio.DataGrabber(outfields=outfields), name="Source_Subject")
    datasource.inputs.base_directory = source_directory
    datasource.inputs.template = '*'
    datasource.inputs.field_template = dict(
        lh_BA1_exvivo='label/lh.BA1_exvivo.label',
        lh_BA2_exvivo='label/lh.BA2_exvivo.label',
        lh_BA3a_exvivo='label/lh.BA3a_exvivo.label',
        lh_BA3b_exvivo='label/lh.BA3b_exvivo.label',
        lh_BA4a_exvivo='label/lh.BA4a_exvivo.label',
        lh_BA4p_exvivo='label/lh.BA4p_exvivo.label',
        lh_BA6_exvivo='label/lh.BA6_exvivo.label',
        lh_BA44_exvivo='label/lh.BA44_exvivo.label',
        lh_BA45_exvivo='label/lh.BA45_exvivo.label',
        lh_V1_exvivo='label/lh.V1_exvivo.label',
        lh_V2_exvivo='label/lh.V2_exvivo.label',
        lh_MT_exvivo='label/lh.MT_exvivo.label',
        lh_entorhinal_exvivo='label/lh.entorhinal_exvivo.label',
        lh_perirhinal_exvivo='label/lh.perirhinal_exvivo.label',
        lh_BA1_exvivo_thresh='label/lh.BA1_exvivo.thresh.label',
        lh_BA2_exvivo_thresh='label/lh.BA2_exvivo.thresh.label',
        lh_BA3a_exvivo_thresh='label/lh.BA3a_exvivo.thresh.label',
        lh_BA3b_exvivo_thresh='label/lh.BA3b_exvivo.thresh.label',
        lh_BA4a_exvivo_thresh='label/lh.BA4a_exvivo.thresh.label',
        lh_BA4p_exvivo_thresh='label/lh.BA4p_exvivo.thresh.label',
        lh_BA6_exvivo_thresh='label/lh.BA6_exvivo.thresh.label',
        lh_BA44_exvivo_thresh='label/lh.BA44_exvivo.thresh.label',
        lh_BA45_exvivo_thresh='label/lh.BA45_exvivo.thresh.label',
        lh_V1_exvivo_thresh='label/lh.V1_exvivo.thresh.label',
        lh_V2_exvivo_thresh='label/lh.V2_exvivo.thresh.label',
        lh_MT_exvivo_thresh='label/lh.MT_exvivo.thresh.label',
        lh_entorhinal_exvivo_thresh='label/lh.entorhinal_exvivo.thresh.label',
        lh_perirhinal_exvivo_thresh='label/lh.perirhinal_exvivo.thresh.label',
        rh_BA1_exvivo='label/rh.BA1_exvivo.label',
        rh_BA2_exvivo='label/rh.BA2_exvivo.label',
        rh_BA3a_exvivo='label/rh.BA3a_exvivo.label',
        rh_BA3b_exvivo='label/rh.BA3b_exvivo.label',
        rh_BA4a_exvivo='label/rh.BA4a_exvivo.label',
        rh_BA4p_exvivo='label/rh.BA4p_exvivo.label',
        rh_BA6_exvivo='label/rh.BA6_exvivo.label',
        rh_BA44_exvivo='label/rh.BA44_exvivo.label',
        rh_BA45_exvivo='label/rh.BA45_exvivo.label',
        rh_V1_exvivo='label/rh.V1_exvivo.label',
        rh_V2_exvivo='label/rh.V2_exvivo.label',
        rh_MT_exvivo='label/rh.MT_exvivo.label',
        rh_entorhinal_exvivo='label/rh.entorhinal_exvivo.label',
        rh_perirhinal_exvivo='label/rh.perirhinal_exvivo.label',
        rh_BA1_exvivo_thresh='label/rh.BA1_exvivo.thresh.label',
        rh_BA2_exvivo_thresh='label/rh.BA2_exvivo.thresh.label',
        rh_BA3a_exvivo_thresh='label/rh.BA3a_exvivo.thresh.label',
        rh_BA3b_exvivo_thresh='label/rh.BA3b_exvivo.thresh.label',
        rh_BA4a_exvivo_thresh='label/rh.BA4a_exvivo.thresh.label',
        rh_BA4p_exvivo_thresh='label/rh.BA4p_exvivo.thresh.label',
        rh_BA6_exvivo_thresh='label/rh.BA6_exvivo.thresh.label',
        rh_BA44_exvivo_thresh='label/rh.BA44_exvivo.thresh.label',
        rh_BA45_exvivo_thresh='label/rh.BA45_exvivo.thresh.label',
        rh_V1_exvivo_thresh='label/rh.V1_exvivo.thresh.label',
        rh_V2_exvivo_thresh='label/rh.V2_exvivo.thresh.label',
        rh_MT_exvivo_thresh='label/rh.MT_exvivo.thresh.label',
        rh_entorhinal_exvivo_thresh='label/rh.entorhinal_exvivo.thresh.label',
        rh_perirhinal_exvivo_thresh='label/rh.perirhinal_exvivo.thresh.label')
    return datasource, outfields

def source_long_files_workflow(name="Source_Longitudinal_Files"):
    """Creates a workflow to source the longitudinal files from a freesurfer directory.
    This should only be used when the files are not in a prexisting workflow"""

    wf = Workflow(name=name)
    
    inputspec = Node(IdentityInterface(fields=['subject_id',
                                               'subjects_dir',
                                               'timepoints']),
                     name="inputspec")

    # TODO: Create outputspec
    
    # grab files from the initial single session run
    grab_inittp_files = pe.Node(DataGrabber(), name="Grab_Initial_Files",
                                infields=['subject_id'],
                                outfileds=['inputvols', 'iscales', 'ltas'])
    grab_inittp_files.inputs.template = '*'
    grab_inittp_files.inputs.base_directory = config['subjects_dir']
    grab_inittp_files.inputs.field_template = dict(inputvols='%s/mri/orig/0*.mgz',
                                                   iscales='%s/mri/orig/0*-iscale.txt',
                                                   ltas='%s/mri/orig/0*.lta')
        
    grab_inittp_files.inputs.template_args = dict(inputvols=[['subject_id']],
                                                  iscales=[['subject_id']],
                                                  ltas=[['subject_id']])

    wf.connect([(grab_inittp_files, outputspec, [('inputvols', 'inputspec.in_T1s'),
                                                   ('iscales', 'inputspec.iscales'),
                                                   ('ltas', 'inputspec.ltas')])])

    merge_norms = pe.Node(Merge(len(config['timepoints'])), name="Merge_Norms")
    merge_segs = pe.Node(Merge(len(config['timepoints'])), name="Merge_Segmentations")
    merge_segs_noCC = pe.Node(Merge(len(config['timepoints'])), name="Merge_Segmentations_noCC")
    merge_template_ltas = pe.Node(Merge(len(config['timepoints'])), name="Merge_Template_ltas")

    for i, tp in enumerate(config['timepoints']):
        # datasource timepoint files
        tp_data_source = pe.Node(FreeSurferSource(), name="{0}_DataSource".format(tp))
        tp_data_source.inputs.subject_id = tp
        tp_data_source.inputs.subjects_dir = config['subjects_dir']
        
        tp_data_grabber = pe.Node(DataGrabber(), name="{0}_DataGrabber".format(tp),
                                  infields=['tp', 'long_tempate'],
                                  outfileds=['subj_to_template_lta', 'seg_noCC', 'seg_presurf'])
        tp_data_grabber.inputs.template = '*'
        tp_data_grabber.inputs.base_directory = config['subjects_dir']
        tp_data_grabber.inputs.field_template = dict(
            subj_to_template_lta='%s/mri/transforms/%s_to_%s.lta',
            seg_noCC='%s/mri/aseg.auto_noCCseg.mgz',
            seg_presurf='%s/mri/aseg.presurf.mgz',)

        tp_data_grabber.inputs.template_args = dict(
            subj_to_template_lta=[['long_template', 'tp', 'long_template']],
            seg_noCC=[['tp']],
            seg_presurf=[['tp']])
                        
        wf.connect([(tp_data_source, merge_norms, [('norm',
                                                          'in{0}'.format(i))]),
                          (tp_data_grabber, merge_segs, [('seg_presurf',
                                                          'in{0}'.format(i))]),
                          (tp_data_grabber, merge_segs_noCC, [('seg_noCC',
                                                               'in{0}'.format(i))]),
                          (tp_data_grabber, merge_template_ltas, [('subj_to_template_lta',
                                                                   'in{0}'.format(i))])])

        if tp == config['subject_id']:
            wf.connect([(tp_data_source, outputspec, [('wm', 'inputspec.init_wm')]),
                              (tp_data_grabber, outputspec, [('subj_to_template_lta',
                                                          'inputspec.subj_to_template_lta')]),
                              (tp_data_grabber, outputspec, [('subj_to_template_lta',
                                                          'inputspec.subj_to_template_lta')])])

    wf.connect([(merge_norms, outputspec, [('out', 'inputspec.alltps_norms')]),
                      (merge_segs, outputspec, [('out', 'inputspec.alltps_segs')]),
                      (merge_template_ltas, outputspec, [('out', 'inputspec.alltps_to_template_ltas')]),
                      (merge_segs_noCC, outputspec, [('out', 'inputspec.alltps_segs_noCC')])])

                        

    # datasource files from the template run
    ds_template_files = pe.Node(FreeSurferSource(), name="Datasource_Template_Files")
    ds_template_files.inputs.subject_id = config['subject_id']
    ds_template_files.inputs.subjects_dir = config['subjects_dir']

    wf.connect([(ds_template_files, ar1_wf, [('brainmask', 'inputspec.template_brainmask')]),
                      (ds_template_files, outputspec, [('aseg', 'inputspec.template_aseg')])])
    
    # grab files from template run
    grab_template_files = pe.Node(DataGrabber(), name="Grab_Template_Files",
                                  infields=['subject_id', 'long_template'],
                                  outfields=['template_talairach_xfm',
                                             'template_talairach_lta',
                                             'template_talairach_m3z',
                                             'template_label_intensities',
                                             'template_lh_white',
                                             'template_rh_white',
                                             'template_lh_pial',
                                             'template_rh_pial'])
    grab_template_files.inputs.template = '*'
    grab_template_files.inputs.base_directory = config['subjects_dir']
    grab_template_files.inputs.subject_id = config['subject_id']
    grab_template_files.inputs.long_template = config['long_template']
    grab_template_files.inputs.field_template = dict(
        template_talairach_xfm='%s/mri/transfroms/talairach.xfm',
        template_talairach_lta='%s/mri/transfroms/talairach.lta',
        template_talairach_m3z='%s/mri/transfroms/talairach.m3z',
        template_label_intensities='%s/mri/aseg.auto_noCCseg.label_intensities.txt',
        template_lh_white='%s/surf/lh.white',
        template_rh_white='%s/surf/rh.white',
        template_lh_pial='%s/surf/lh.pial',
        template_rh_pial='%s/surf/rh.pial')
    
    grab_template_files.inputs.template_args = dict(
        template_talairach_xfm=[['long_template']],
        template_talairach_lta=[['long_template']],
        template_talairach_m3z=[['long_template']],
        template_lh_white=[['long_template']],
        template_rh_white=[['long_template']],
        template_lh_pial=[['long_template']],
        template_rh_pial=[['long_template']])
    wf.connect([(grab_template_files, outputspec, [('template_talairach_xfm',
                                                    'inputspec.template_talairach_xfm'),
                                                   ('template_talairach_lta',
                                                    'inputspec.template_talairach_lta'),
                                                   ('template_talairach_m3z',
                                                    'inputspec.template_talairach_m3z'),
                                                   ('template_label_intensities',
                                                    'inputspec.template_label_intensities'),
                                                   ('template_lh_white', 'inputspec.template_lh_white'),
                                                   ('template_rh_white', 'inputspec.template_rh_white'),
                                                   ('template_lh_pial', 'inputspec.template_lh_pial'),
                                                   ('template_rh_pial', 'inputspec.template_rh_pial')])
            ])
    return wf
