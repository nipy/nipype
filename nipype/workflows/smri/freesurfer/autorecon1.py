import sys
import os
import nipype
from nipype.interfaces.utility import Function,IdentityInterface
import nipype.pipeline.engine as pe  # pypeline engine
from nipype.interfaces.freesurfer import *
from utils import copy_file, copy_files, awkfile

def checkT1s(T1_files, cw256=False):
    """Verifying size of inputs and setting workflow parameters"""
    import SimpleITK as sitk
    import os
    import sys
    if len(T1_files) == 0:
        print("ERROR: No T1's Given")
        sys.exit(-1)
    for i, t1 in enumerate(T1_files):
        if t1.endswith(".mgz"):
            # convert input fs files to NIFTI
            convert = MRIConvert()
            convert.inputs.in_file = t1
            convert.inputs.out_file = os.path.abspath(os.path.basename(t1).replace('.mgz', '.nii.gz'))
            convert.run()
            T1_files[i] = convert.inputs.out_file
    size = None
    origvol_names = list()
    for i, t1 in enumerate(T1_files):
        # assign an input number
        file_num = str(i + 1)
        while len(file_num) < 3:
            file_num = '0' + file_num
        origvol_names.append("{0}.mgz".format(file_num))
        # check the size of the image
        img = sitk.ReadImage(t1)
        if not size:
            size = img.GetSize()
        elif size != img.GetSize():
            print("ERROR: T1s not the same size. Cannot process {0} {1} together".format(T1_files[0],
                                                                                         otherFilename))
            sys.exit(-1)
    # check if cw256 is set to crop the images if size is larger than 256
    if not cw256:
        for dim in size:
            if dim > 256:
                print("Setting MRI Convert to crop images to 256 FOV")
                cw256 = True
    if len(T1_files) > 1:
        resample_type = 'cubic'
    else:
        resample_type = 'interpolate'
    return T1_files, cw256, resample_type, origvol_names

def create_AutoRecon1(name="AutoRecon1", longitudinal=False, field_strength='1.5T',
                      custom_atlas=None, awk_file=None, plugin_args=None):
    """Creates the AutoRecon1 workflow in nipype.

    Inputs::
           inputspec.T1_files : T1 files (mandatory)
           inputspec.T2_file : T2 file (optional)
           inputspec.FLAIR_file : FLAIR file (optional)
           inputspec.cw256 : Conform inputs to 256 FOV (optional)
           inputspec.num_threads: Number of threads to use with EM Register (default=1)
    Outpus::
           
    """
    ar1_wf = pe.Workflow(name=name)
    inputspec = pe.Node(interface=IdentityInterface(fields=['T1_files',
                                                            'T2_file',
                                                            'in_flair',
                                                            'cw256',
                                                            'num_threads',
                                                            'skulltemplate']),
                        run_without_submitting=True,
                        name='inputspec')

    if not longitudinal:
        # single session processing
        verify_inputs = pe.Node(Function(infields=["T1_files", "cw256"],
                                         outfields=["T1_files", "cw256", "resample_type", "origvol_names"],
                                         checkT1s)
                                name="Check_T1s"),
        ar1_wf.conncet([(inputspec, verify_inputs, [('T1_files', 'T1_files'),
                                                    ('cw256', 'cw256')])])


        # T1 image preparation
        # For all T1's mri_convert ${InputVol} ${out_file}
        T1_image_preparation = pe.MapNode(MRIConvert(),
                                          iterfield=['in_file', 'out_file'],
                                          name="T1_prep")

        ar1_wf.connect([(verify_inputs, T1_image_preparation, [('T1_files', 'in_file'),
                                                               ('origvol_names', 'out_file')]),
                        ])

        def convert_modalities(in_file, out_file):
            """Returns an undefined output if the in_file is not defined"""
            from nipype.interfaces.base import isdefined
            from nipype.interfaces.freesurfer import MRIConvert
            if isdefined(in_file):
                convert = MRIConvert()
                convert.inputs.in_file = in_file
                convert.inputs.out_file = out_file
                convert.inputs.no_scale = True
                convert.run()
                out_file = os.path.abspath(convert.outputs.out_file)
            return out_file

        T2_convert = pe.Node(Function(['in_file', 'out_file'],
                                      ['out_file'],
                                      convert_modalities),
                             name="T2_Convert")
        T2_convert.inputs.out_file = 'T2raw.mgz'
        ar1_wf.connect([(inputspec, T2_convert, [('T2_file', 'in_file')])]) 

        FLAIR_convert = pe.Node(Function(['in_file', 'out_file'],
                                         ['out_file'],
                                         convert_modalities),
                                name="T2_Convert")
        FLAIR_convert.inputs.out_file = 'FLAIRraw.mgz'
        ar1_wf.connect([(inputspec, FLAIR_convert, [('in_flair', 'in_file')])])        
    else:
        # longitudinal inputs
        inputspec = pe.Node(interface=IdentityInterface(fields=['T1_files',
                                                                'iscales',
                                                                'ltas',
                                                                'subj_to_template_lta',
                                                                'template_talairach_xfm',
                                                                'template_brainmask']),
                            run_without_submitting=True,
                            name='inputspec')

        def output_names(T1_files):
            """Create file names that are dependent on the number of T1 inputs"""
            iscale_names = list()
            lta_names = list()
            for i, t1 in enumerate(T1_files):
                # assign an input number
                file_num = str(i + 1)
                while len(file_num) < 3:
                    file_num = '0' + file_num
                iscale_names.append("{0}-iscale.txt".format(file_num))
                lta_names.append("{0}.lta".format(file_num))
            return iscale_names, lta_names

        filenames = pe.Node(Function(['T1_files'],
                                     ['iscale_names', 'lta_names']
                                     output_names),
                            name="Longitudinal_Filenames")
        ar1_wf.connect([(inputspec, filenames, [('T1_files', 'T1_files')])])
        
        copy_ltas = pe.MapNode(Function(['in_file', 'out_file'],
                                        ['out_file'],
                                        copy_file),
                               iterfield=['in_file', 'out_file'],
                               name='Copy_ltas')
        ar1_wf.connect([(inputspec, copy_ltas, [('ltas', 'in_file')]),
                        (filenames, copy_ltas, [('lta_names', 'out_file')])])

        copy_iscales = pe.MapNode(Function(['in_file', 'out_file'],
                                           ['out_file'],
                                           copy_file),
                                  iterfield=['in_file', 'out_file'],
                                  name='Copy_iscales')
        ar1_wf.connect([(inputspec, copy_iscales, [('iscales', 'in_file')]),
                        (filenames, copy_iscales, [('iscale_names', 'out_file')])])

        concatenate_lta = pe.MapNode(ConcatenateLTA(), iterfield=['in_file'],
                                     name="Concatenate_ltas")
        ar1_wf.connect([(copy_ltas, concatenate_lta, [('out_file', 'in_file')]),
                        (inputspec, concatenate_lta, [('subj_to_template_lta', 'subj_to_base')])])

    
    # Motion Correction
    """
    When there are multiple source volumes, this step will correct for small
    motions between them and then average them together.  The output of the
    motion corrected average is mri/rawavg.mgz which is then conformed to
    255 cubed char images (1mm isotropic voxels) in mri/orig.mgz.
    """

    def createTemplate(in_files, out_file):
        if len(in_files) == 1 and not longitudinal:
            print("WARNING: only one run found. This is OK, but motion correction" +
                  "cannot be performed on one run, so I'll copy the run to rawavg" +
                  "and continue.")
            copy_file(in_files[0], out_file)
            intensity_scales = None
            transforms = None
        else:
            from nipype.interfaces.freesurfer import RobustTemplate
            # if multiple T1 scans are given
            intensity_scales = [os.path.basename(f.replace('.mgz', '-iscale.txt')) for f in in_files]
            transforms = [os.path.basename(f.replace('.mgz', '.lta')) for f in in_files]
            robtemp = RobustTemplate()
            robtemp.inputs.average_metric = 'median'
            robtemp.inputs.out_file = out_file
            robtemp.inputs.no_iteration = True
            robtemp.inputs.fixed_timepoint = True
            robtemp.inputs.auto_detect_sensitivity = True
            robtemp.inputs.initial_timepoint = 1
            robtemp.inputs.scaled_intensity_outputs = intensity_scales
            robtemp.inputs.transform_outputs = transforms
            robtemp.inputs.subsample_threshold = 200
            robtemp.inputs.intensity_scaling = True
            robtemp.run()
            intensity_scales = [os.path.abspath(f) for f in robtemp.outputs.scaled_intensity_outputs]
            transforms = [os.path.abspath(f) for f in robtemp.outputs.transform_outputs]
            out_file = robtemp.outputs.out_file
        out_file = os.path.abspath(out_file)
        return out_file, intensity_scales, transforms
    
    if not longitudinal:
        create_template = pe.Node(Function(['in_files', 'out_file'],
                                           ['out_file', 'intensity_scales', 'transforms'],
                                           createTemplate),
                                  name="Robust_Template")
        create_template.inputs.out_file = 'rawavg.mgz'
        ar1_wf.connect([(T1_image_preparation, create_template, [('out_file', 'in_files')])])
    else:
        create_template = pe.Node(RobustTemplate(), name="Robust_Template")
        create_template.inputs.average_metric = 'median'
        create_template.inputs.out_file = 'rawavg.mgz'
        create_template.inputs.no_iteration = True
        ar1_wf.connect([(concatenate_lta, create_template, [('out_file', 'initial_transforms')]),
                        (inputSpec, create_template, [('in_t1s', 'in_files')]),
                        (copy_iscales, create_template, [('out_file','in_intensity_scales')])])

    # mri_convert
    conform_template = pe.Node(MRIConvert(), name='Conform_Template')
    conform_template.inputs.out_file = 'orig.mgz'
    if not longitudinal:
        conform_template.inputs.conform = True
        ar1_wf.connect([(verify_inputs, conform_template, [('cw256', 'cw256'),
                                                           ('resample_type', 'resample_type')])]) 
    else:
        conform_template.inputs.out_datatype = 'uchar'
            
    ar1_wf.connect([(create_template, conform_template, [('out_file', 'in_file')])])

    # Talairach
    """
    This computes the affine transform from the orig volume to the MNI305 atlas using Avi Snyders 4dfp
    suite of image registration tools, through a FreeSurfer script called talairach_avi.
    Several of the downstream programs use talairach coordinates as seed points.
    """

    bias_correction = pe.Node(MNIBiasCorrection(), name="Bias_correction")
    bias_correction.inputs.iterations = 1
    bias_correction.inputs.protocol_iterations = 1000
    if field_strength == '3T':
        # 3T params from Zheng, Chee, Zagorodnov 2009 NeuroImage paper
        # "Improvement of brain segmentation accuracy by optimizing
        # non-uniformity correction using N3"
        # namely specifying iterations, proto-iters and distance: 
        bias_correction.inputs.distance = 50
    else:
        # 1.5T default
        bias_correction.inputs.distance = 200
    # per c.larsen, decrease convergence threshold (default is 0.001)
    bias_correction.inputs.stop = 0.0001
    # per c.larsen, decrease shrink parameter: finer sampling (default is 4)
    bias_correction.inputs.shrink =  2
    # add the mask, as per c.larsen, bias-field correction is known to work
    # much better when the brain area is properly masked, in this case by
    # brainmask.mgz.
    bias_correction.inputs.no_rescale = True
    bias_correction.inputs.out_file = 'orig_nu.mgz'

    ar1_wf.connect([(conform_template, bias_correction, [('out_file', 'in_file')]),
                ])

    if not longitudinal:
        # single session processing
        talairach_avi = pe.Node(TalairachAVI(), name="Compute_Transform")
        if custom_atlas != None:
            # allows to specify a custom atlas
            talairach_avi.inputs.atlas = custom_atlas
        talairach_avi.inputs.out_file = 'talairach.auto.xfm'
        ar1_wf.connect([(bias_correction, talairach_avi, [('out_file', 'in_file')])])
    else:
        # longitudinal processing
        # Just copy the template xfm
        talairach_avi = pe.Node(Function(['in_file', 'out_file'],
                                             ['out_file'],
                                             copy_file),
                                    name='Copy_Template_Transform')
        talairach_avi.inputs.out_file = 'talairach.auto.xfm'

        ar1_wf.connect([(inputspec, talairach_avi, [('template_talairach_xfm', 'in_file')])])
        
    copy_transform = pe.Node(Function(['in_file', 'out_file'],
                                      ['out_file'],
                                      copy_file),
                             name='Copy_Transform')
    copy_transform.inputs.out_file = 'talairach.xfm'

    ar1_wf.connect([(talairach_avi, copy_transform, [('out_file', 'in_file')])])


    # In recon-all the talairach.xfm is added to orig.mgz, even though
    # it does not exist yet. This is a compromise to keep from
    # having to change the time stamp of the orig volume after talairaching.
    # Here we are going to add xfm to the header after the xfm has been created.
    # This may mess up the timestamp.

    add_xform_to_orig = pe.Node(AddXFormToHeader(), name="Add_Transform_to_Orig")
    add_xform_to_orig.inputs.copy_name = True
    add_xform_to_orig.inputs.out_file = conform_template.inputs.out_file

    ar1_wf.connect([(conform_template, add_xform_to_orig, [('out_file', 'in_file')]),
                    (copy_transform, add_xform_to_orig, [('out_file', 'transform')])])

    # This node adds the transform to the orig_nu.mgz file. This step does not
    # exist in the recon-all workflow, because that workflow adds the talairach
    # to the orig.mgz file header before the talairach actually exists.
    add_xform_to_orig_nu = pe.Node(AddXFormToHeader(), name="Add_Transform_to_Orig_Nu")
    add_xform_to_orig_nu.inputs.copy_name = True
    add_xform_to_orig_nu.inputs.out_file = bias_correction.inputs.out_file

    ar1_wf.connect([(bias_correction, add_xform_to_orig_nu, [('out_file', 'in_file')]),
                    (copy_transform, add_xform_to_orig_nu, [('out_file', 'transform')])])


        
    # check the alignment of the talairach
    # TODO: Figure out how to read output from this node.
    check_alignment = pe.Node(CheckTalairachAlignment(),
                              name="Check_Talairach_Alignment")
    check_alignment.inputs.threshold = 0.005
    ar1_wf.connect([(copy_transform, check_alignment, [('out_file', 'in_file')]),
                    ])

    if not longitudinal and awk_file:
        def awkfile(in_file, log_file):
            """
            This method uses 'awk' which must be installed prior to running the workflow and is not a
            part of nipype or freesurfer.
            """
            import subprocess
            import os
            command = ['awk', '-f', awk_file, log_file]
            print(''.join(command))
            subprocess.call(command)
            log_file = os.path.abspath(log_file)
            return log_file

        awk_logfile = pe.Node(Function(['in_file', 'log_file'],
                                       ['log_file'],
                                       awkfile),
                              name='Awk')
        awk_logfile.inputs.in_file = awk_file
                                       
        ar1_wf.connect([(talairach_avi, awk_logfile, [('out_log', 'log_file')])])

        # TODO datasink the output from TalirachQC...not sure how to do this
        tal_qc = pe.Node(TalairachQC(), name="Detect_Aligment_Failures")
        ar1_wf.connect([(awk_logfile, tal_qc, [('log_file', 'log_file')])])

    # Intensity Normalization
    # Performs intensity normalization of the orig volume and places the result in mri/T1.mgz.
    # Attempts to correct for fluctuations in intensity that would otherwise make intensity-based
    # segmentation much more difficult. Intensities for all voxels are scaled so that the mean
    # intensity of the white matter is 110.

    mri_normalize = pe.Node(Normalize(), name="Normalize_T1")
    mri_normalize.inputs.gradient = 1
    mri_normalize.inputs.out_file = 'T1.mgz'
    ar1_wf.connect([(add_xform_to_orig_nu, mri_normalize, [('out_file', 'in_file')]),
                    (copy_transform, mri_normalize,
                     [('out_file', 'transform')]),
                    ])
    
    # Skull Strip
    """
    Removes the skull from mri/T1.mgz and stores the result in 
    mri/brainmask.auto.mgz and mri/brainmask.mgz. Runs the mri_watershed program.
    """
    if not longitudinal:    
        mri_em_register = pe.Node(EMRegister(), name="EM_Register")
        mri_em_register.inputs.out_file = 'talairach_with_skull.lta'
        mri_em_register.inputs.skull = True
        if plugin_args:
            mri_em_register.plugin_args = plugin_args
            
        ar1_wf.connect([(add_xform_to_orig_nu, mri_em_register, [('out_file', 'in_file')]),
                        (inputspec, mri_em_register, [('num_threads', 'num_threads'),
                                                      ('skulltemplate', 'template')])])

        brainmask = pe.Node(WatershedSkullStrip(),
                            name='Watershed_Skull_Strip')
        brainmask.inputs.t1 = True
        brainmask.inputs.out_file = 'brainmask.auto.mgz'
        ar1_wf.connect([(mri_normalize, brainmask, [('out_file', 'in_file')]),
                        (mri_em_register, brainmask, [('out_file', 'transform')]),
                        (inputspec, brainmask, [('skulltemplate', 'brain_atlas')])])
    else:
        copy_template_brainmask = pe.Node(Function(['in_file', 'out_file'],
                                                   ['out_file'],
                                                   copy_file),
                                          name='Copy_Template_Brainmask')
        #TODO: Change this to inputspec
        copy_template_brainmask.inputs.out_file = 'brainmask_{0}.mgz'.format(config['long_template'])
        
        ar1_wf.connect([(inputspec, copy_template_brainmask, [('template_brainmask', 'in_file')])])

        mask1 = pe.Node(ApplyMask(), name="ApplyMask1")
        mask1.inputs.keep_mask_deletion_edits = True
        mask1.inputs.out_file = 'brainmask.auto.mgz'
        
        ar1_wf.connect([(mri_normalize, mask1, [('out_file', 'in_file')]),
                        (copy_template_brainmask, mask1, [('out_file', 'mask_file')])])

        brainmask = pe.Node(ApplyMask(), name="ApplyMask2")
        brainmask.inputs.keep_mask_deletion_edits = True
        brainmask.inputs.transfer = 255
        brainmask.inputs.out_file = mask1.inputs.out_file

        ar1_wf.connect([(mask1, brainmask, [('out_file', 'in_file')]),
                        (copy_template_brainmask, brainmask, [('out_file', 'mask_file')])])
                        
    copy_brainmask = pe.Node(Function(['in_file', 'out_file'],
                                      ['out_file'],
                                      copy_file),
                             name='Copy_Brainmask')
    copy_brainmask.inputs.out_file = 'brainmask.mgz'

    ar1_wf.connect([(brainmask, copy_brainmask, [('out_file', 'in_file')])])

    outputs = ['origvols',
               't2_raw',
               'flair',
               'rawavg',
               'orig_nu',
               'orig',
               'talairach_auto',
               'talairach',
               't1',
               'talskull',
               'brainmask_auto',
               'brainmask',
               'braintemplate']
    outputspec = pe.Node(IdentityInterface(fields=outputs),
                         name="outputspec")

    ar1_wf.connect([(T1_image_preparation, outputspec, [('out_file', 'origvols')]),
                    (T2_convert, outputspec, [('out_file', 't2_raw')]),
                    (FLAIR_convert, outputspec, [('out_file', 'flair')]),
                    (create_template, outputspec, [('out_file', 'rawavg')]),
                    (add_xform_to_orig, outputspec, [('out_file', 'orig')]),
                    (add_xform_to_orig_nu, outputspec, [('out_file', 'orig_nu')]),
                    (talairach_avi, outputspec, [('out_file', 'talairach_auto')]),
                    (copy_transform, outputspec, [('out_file', 'talairach')]),
                    (mri_normalize, outputspec, [('out_file', 't1')]),
                    (brainmask, outputspec, [('out_file', 'brainmask_auto')]),
                    (copy_brainmask, outputspec, [('out_file', 'brainmask')]),                    
                    ])

    
    if not longitudinal:
        ar1_wf.connect([(mri_em_register, outputspec, [('out_file', 'talskull')]),
                        ])
    else:
        ar1_wf.connect([(copy_template_brainmask, outputspec, [('out_file', 'braintemplate')]),
                        ])

    return ar1_wf, outputs
