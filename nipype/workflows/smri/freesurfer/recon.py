from ....pipeline import engine as pe
from ....interfaces import freesurfer as fs
from ....interfaces import utility as niu
from .autorecon1 import create_AutoRecon1
from .autorecon2 import create_AutoRecon2
from .autorecon3 import create_AutoRecon3
from ....interfaces.freesurfer import AddXFormToHeader
from ....interfaces.io import DataSink
from .utils import getdefaultconfig

def create_skullstripped_recon_flow(name="skullstripped_recon_all"):
    """Performs recon-all on voulmes that are already skull stripped.
    FreeSurfer failes to perform skullstrippig on some volumes (especially
    MP2RAGE). This can be avoided by doing skullstripping before runnig recon-all
    (using for example SPECTRE algorithm)

    Example
    -------
    >>> from nipype.workflows.smri.freesurfer import create_skullstripped_recon_flow
    >>> recon_flow = create_skullstripped_recon_flow()
    >>> recon_flow.inputs.inputspec.subject_id = 'subj1'
    >>> recon_flow.inputs.inputspec.T1_files = 'T1.nii.gz'
    >>> recon_flow.run()  # doctest: +SKIP


    Inputs::
           inputspec.T1_files : skullstripped T1_files (mandatory)
           inputspec.subject_id : freesurfer subject id (optional)
           inputspec.subjects_dir : freesurfer subjects directory (optional)

    Outputs::

           outputspec.subject_id : freesurfer subject id
           outputspec.subjects_dir : freesurfer subjects directory
    """
    wf = pe.Workflow(name=name)

    inputnode = pe.Node(niu.IdentityInterface(fields=['subject_id',
                                                      'subjects_dir',
                                                      'T1_files']),
                        name='inputspec')

    autorecon1 = pe.Node(fs.ReconAll(), name="autorecon1")
    autorecon1.plugin_args = {'submit_specs': 'request_memory = 2500'}
    autorecon1.inputs.directive = "autorecon1"
    autorecon1.inputs.args = "-noskullstrip"
    autorecon1._interface._can_resume = False

    wf.connect(inputnode, "T1_files", autorecon1, "T1_files")
    wf.connect(inputnode, "subjects_dir", autorecon1, "subjects_dir")
    wf.connect(inputnode, "subject_id", autorecon1, "subject_id")

    def link_masks(subjects_dir, subject_id):
        import os
        os.symlink(os.path.join(subjects_dir, subject_id, "mri", "T1.mgz"),
                   os.path.join(subjects_dir, subject_id, "mri", "brainmask.auto.mgz"))
        os.symlink(os.path.join(subjects_dir, subject_id, "mri", "brainmask.auto.mgz"),
                   os.path.join(subjects_dir, subject_id, "mri", "brainmask.mgz"))
        return subjects_dir, subject_id

    masks = pe.Node(niu.Function(input_names=['subjects_dir', 'subject_id'],
                                 output_names=['subjects_dir', 'subject_id'],
                                 function=link_masks), name="link_masks")

    wf.connect(autorecon1, "subjects_dir", masks, "subjects_dir")
    wf.connect(autorecon1, "subject_id", masks, "subject_id")

    autorecon_resume = pe.Node(fs.ReconAll(), name="autorecon_resume")
    autorecon_resume.plugin_args = {'submit_specs': 'request_memory = 2500'}
    autorecon_resume.inputs.args = "-no-isrunning"
    wf.connect(masks, "subjects_dir", autorecon_resume, "subjects_dir")
    wf.connect(masks, "subject_id", autorecon_resume, "subject_id")

    outputnode = pe.Node(niu.IdentityInterface(fields=['subject_id',
                                                       'subjects_dir']),
                         name='outputspec')

    wf.connect(autorecon_resume, "subjects_dir", outputnode, "subjects_dir")
    wf.connect(autorecon_resume, "subject_id", outputnode, "subject_id")
    return wf

def create_reconall_workflow(name="ReconAll", plugin_args=None):
    """Creates the ReconAll workflow in nipype.

    Inputs::
           inputspec.T1_files : T1 files (mandatory)
           inputspec.T2_file : T2 file (optional)
           inputspec.FLAIR_file : FLAIR file (optional)
           inputspec.cw256 : Conform inputs to 256 FOV (optional)
           inputspec.num_threads: Number of threads on nodes that utilize OpenMP (default=1)
           plugin_args : Dictionary of plugin args to set to nodes that utilize OpenMP (optional)
    Outpus::
           
    """
    reconall = pe.Workflow(name=name)
    
    inputspec = pe.Node(niu.IdentityInterface(fields=['subject_id',
                                                      'subjects_dir',
                                                      'T1_files',
                                                      'T2_file',
                                                      'FLAIR_file',
                                                      'num_threads',
                                                      'cw256',
                                                      'reg_template',
                                                      'reg_template_withskull',
                                                      'lh_atlas',
                                                      'rh_atlas',
                                                      'lh_classifier1',
                                                      'rh_classifier1',
                                                      'lh_classifier2',
                                                      'rh_classifier2',
                                                      'lh_classifier3',
                                                      'rh_classifier3',
                                                      'lookup_table',
                                                      'wm_lookup_table',
                                                      'src_subject_id',
                                                      'src_subject_dir',
                                                      'color_table']),
                        run_without_submitting=True,
                        name='inputspec')

    # get the default configurations
    defaultconfig = getdefaultconfig()

    # set the default template and classifier files
    inputspec.inputs.reg_template = defaultconfig['registration_template']
    inputspec.inputs.reg_template_withskull = defaultconfig['registration_template_withskull']
    inputspec.inputs.lh_atlas = defaultconfig['lh_atlas']
    inputspec.inputs.rh_atlas = defaultconfig['rh_atlas']
    inputspec.inputs.lh_classifier1 = defaultconfig['lh_classifier']
    inputspec.inputs.rh_classifier1 = defaultconfig['rh_classifier']
    inputspec.inputs.lh_classifier2 = defaultconfig['lh_classifier2']
    inputspec.inputs.rh_classifier2 = defaultconfig['rh_classifier2']
    inputspec.inputs.rh_classifier3 = defaultconfig['rh_classifier3']
    inputspec.inputs.src_subject_id = defaultconfig['src_subject_id']
    inputspec.inputs.src_subject_dir = defaultconfig['src_subject_dir']
    inputspec.inputs.color_table = defaultconfig['AvgColorTable']
    inputspec.inputs.lookup_table = defaultconfig['LookUpTable']
    inputspec.inputs.wm_lookup_table = defaultconfig['WMLookUpTable']
    
    # create AutoRecon1
    ar1_wf, ar1_outputs = create_AutoRecon1(plugin_args=plugin_args,
                                            awk_file=defaultconfig['awk_file'])
    # connect inputs for AutoRecon1
    reconall.connect([(inputspec, ar1_wf, [('T1_files', 'inputspec.T1_files'),
                                           ('T2_file', 'inputspec.T2_file'),
                                           ('FLAIR_file', 'inputspec.FLAIR_file'),
                                           ('num_threads', 'inputspec.num_threads'),
                                           ('cw256', 'inputspec.cw256'),
                                           ('reg_template_withskull', 'inputspec.reg_template_withskull')])])

    # create AutoRecon2
    ar2_wf, ar2_outputs = create_AutoRecon2(plugin_args=plugin_args)
    # connect inputs for AutoRecon2
    reconall.connect([(inputspec, ar2_wf, [('num_threads', 'inputspec.num_threads'),
                                           ('reg_template', 'inputspec.reg_template'),
                                           ('reg_template_withskull', 'inputspec.reg_template_withskull')]),
                      (ar1_wf, ar2_wf, [('outputspec.brainmask', 'inputspec.brainmask'),
                                        ('outputspec.talairach', 'inputspec.transform'),
                                        ('outputspec.orig', 'inputspec.orig')])])
    # create AutoRecon3
    ar3_wf, ar3_outputs = create_AutoRecon3(plugin_args=plugin_args)
    # connect inputs for AutoRecon3
    reconall.connect([(inputspec, ar3_wf, [('lh_atlas', 'inputspec.lh_atlas'),
                                           ('rh_atlas', 'inputspec.rh_atlas'),
                                           ('lh_classifier1', 'inputspec.lh_classifier1'),
                                           ('rh_classifier1', 'inputspec.rh_classifier1'),
                                           ('lh_classifier2', 'inputspec.lh_classifier2'),
                                           ('rh_classifier2', 'inputspec.rh_classifier2'),
                                           ('lh_classifier3', 'inputspec.lh_classifier3'),
                                           ('rh_classifier3', 'inputspec.rh_classifier3'),
                                           ('lookup_table', 'inputspec.lookup_table'),
                                           ('wm_lookup_table', 'inputspec.wm_lookup_table'),
                                           ('src_subject_dir', 'inputspec.src_subject_dir'),
                                           ('src_subject_id', 'inputspec.src_subject_id'),
                                           ('color_table', 'inputspec.color_table')]),
                      (ar1_wf, ar3_wf, [('outputspec.brainmask', 'inputspec.brainmask'),
                                        ('outputspec.talairach', 'inputspec.transform'),
                                        ('outputspec.orig', 'inputspec.orig_mgz'),
                                        ('outputspec.rawavg', 'inputspec.rawavg')]),
                      (ar2_wf, ar3_wf, [('outputspec.aseg_presurf', 'inputspec.aseg_presurf'),
                                        ('outputspec.brain_finalsurfs', 'inputspec.brain_finalsurfs'),
                                        ('outputspec.wm', 'inputspec.wm'),
                                        ('outputspec.filled', 'inputspec.filled'),
                                        ('outputspec.norm', 'inputspec.norm')])])
    for hemi in ('lh', 'rh'):
        reconall.connect([(ar2_wf, ar3_wf, [('outputspec.{0}_inflated'.format(hemi),
                                             'inputspec.{0}_inflated'.format(hemi)),
                                            ('outputspec.{0}_smoothwm'.format(hemi),
                                             'inputspec.{0}_smoothwm'.format(hemi)),
                                            ('outputspec.{0}_white'.format(hemi),
                                             'inputspec.{0}_white'.format(hemi)),
                                            ('outputspec.{0}_cortex'.format(hemi),
                                             'inputspec.{0}_cortex_label'.format(hemi)),
                                            ('outputspec.{0}_area'.format(hemi),
                                             'inputspec.{0}_area'.format(hemi)),
                                            ('outputspec.{0}_curv'.format(hemi),
                                             'inputspec.{0}_curv'.format(hemi)),
                                            ('outputspec.{0}_sulc'.format(hemi),
                                             'inputspec.{0}_sulc'.format(hemi)),
                                            ('outputspec.{0}_orig_nofix'.format(hemi),
                                             'inputspec.{0}_orig_nofix'.format(hemi)),
                                            ('outputspec.{0}_orig'.format(hemi),
                                             'inputspec.{0}_orig'.format(hemi)),
                                            ('outputspec.{0}_white_H'.format(hemi),
                                             'inputspec.{0}_white_H'.format(hemi)),
                                            ('outputspec.{0}_white_K'.format(hemi),
                                             'inputspec.{0}_white_K'.format(hemi))])])


            # Add more outputs to outputspec
    outputs = ar1_outputs + ar2_outputs + ar3_outputs
    outputspec = pe.Node(niu.IdentityInterface(fields=outputs, mandatory_inputs=True),
                         name="outputspec")

    for outfields, wf in [(ar1_outputs, ar1_wf),
                          (ar2_outputs, ar2_wf),
                          (ar3_outputs, ar3_wf)]:
        for field in outfields:
            reconall.connect([(wf, outputspec, [('outputspec.' + field, field)])])

    # PreDataSink: Switch Transforms to datasinked transfrom
    # The transforms in the header files of orig.mgz, orig_nu.mgz, and nu.mgz
    # are all reference a transform in the cache directory. We need to rewrite the
    # headers to reference the datasinked transform

    # get the filepath to where the transform will be datasinked
    def getDSTransformPath(subjects_dir, subject_id):
        import os
        transform = os.path.join(subjects_dir, subject_id, 'mri', 'transforms',
                                  'talairach.xfm')
        return transform
    dstransform = pe.Node(niu.Function(['subjects_dir', 'subject_id'],
                                   ['transform'],
                                   getDSTransformPath),
                          name="PreDataSink_GetTransformPath")
    reconall.connect([(inputspec, dstransform, [('subjects_dir', 'subjects_dir'),
                                                ('subject_id', 'subject_id')])])
    # add the data sink transfrom location to the headers
    predatasink_orig = pe.Node(AddXFormToHeader(), name="PreDataSink_Orig")
    predatasink_orig.inputs.copy_name = True
    predatasink_orig.inputs.out_file = 'orig.mgz'
    reconall.connect([(outputspec, predatasink_orig, [('orig', 'in_file')]),
                      (dstransform, predatasink_orig, [('transform', 'transform')])])
    predatasink_orig_nu = pe.Node(AddXFormToHeader(), name="PreDataSink_Orig_Nu")
    predatasink_orig_nu.inputs.copy_name = True
    predatasink_orig_nu.inputs.out_file = 'orig_nu.mgz'
    reconall.connect([(outputspec, predatasink_orig_nu, [('orig_nu', 'in_file')]),
                      (dstransform, predatasink_orig_nu, [('transform', 'transform')])])
    predatasink_nu = pe.Node(AddXFormToHeader(), name="PreDataSink_Nu")
    predatasink_nu.inputs.copy_name = True
    predatasink_nu.inputs.out_file = 'nu.mgz'
    reconall.connect([(outputspec, predatasink_nu, [('nu', 'in_file')]),
                      (dstransform, predatasink_nu, [('transform', 'transform')])])

    
    # Datasink outputs
    datasink = pe.Node(DataSink(), name="DataSink")
    datasink.inputs.parameterization = False
    
    reconall.connect([(inputspec, datasink, [('subjects_dir', 'base_directory'),
                                             ('subject_id', 'container')])])

    # assign datasink inputs
    reconall.connect([(predatasink_orig, datasink, [('out_file', 'mri.@orig')]),
                      (predatasink_orig_nu, datasink, [('out_file', 'mri.@orig_nu')]),
                      (predatasink_nu, datasink, [('out_file', 'mri.@nu')]),
                      (outputspec, datasink, [('origvols', 'mri.orig'),
                                              ('t2_raw', 'mri.orig.@t2raw'),
                                              ('flair', 'mri.orig.@flair'),
                                              ('rawavg', 'mri.@rawavg'),
                                              ('talairach_auto', 'mri.transforms.@tal_auto'),
                                              ('talairach', 'mri.transforms.@tal'),
                                              ('t1', 'mri.@t1'),
                                              ('brainmask_auto', 'mri.@brainmask_auto'),
                                              ('brainmask', 'mri.@brainmask'),
                                              ('braintemplate', 'mri.@braintemplate'),
                                              ('tal_lta', 'mri.transforms.@tal_lta'),
                                              ('norm', 'mri.@norm'),
                                              ('ctrl_pts', 'mri.@ctrl_pts'),
                                              ('tal_m3z', 'mri.transforms.@tal_m3z'),
                                              ('nu_noneck', 'mri.@nu_noneck'),
                                              ('talskull2', 'mri.transforms.@talskull2'),
                                              ('aseg_noCC', 'mri.@aseg_noCC'),
                                              ('cc_up', 'mri.transforms.@cc_up'),
                                              ('aseg_auto', 'mri.@aseg_auto'),
                                              ('aseg_presurf', 'mri.@aseg_presuf'),
                                              ('brain', 'mri.@brain'),
                                              ('brain_finalsurfs', 'mri.@brain_finalsurfs'),
                                              ('wm_seg', 'mri.@wm_seg'),
                                              ('wm_aseg', 'mri.@wm_aseg'),
                                              ('wm', 'mri.@wm'),
                                              ('filled', 'mri.@filled'),
                                              ('ponscc_log', 'mri.@ponscc_log'),
                                              ('lh_orig_nofix', 'surf.@lh_orig_nofix'),
                                              ('lh_orig', 'surf.@lh_orig'),
                                              ('lh_smoothwm_nofix', 'surf.@lh_smoothwm_nofix'),
                                              ('lh_inflated_nofix', 'surf.@lh_inflated_nofix'),
                                              ('lh_qsphere_nofix', 'surf.@lh_qsphere_nofix'),
                                              ('lh_white', 'surf.@lh_white'),
                                              ('lh_curv', 'surf.@lh_curv'),
                                              ('lh_area', 'surf.@lh_area'),
                                              ('lh_cortex', 'surf.@lh_cortex'),
                                              ('lh_thickness', 'surf.@lh_thickness'),
                                              ('lh_smoothwm', 'surf.@lh_smoothwm'),
                                              ('lh_sulc', 'surf.@lh_sulc'),
                                              ('lh_inflated', 'surf.@lh_inflated'),
                                              ('lh_white_H', 'surf.@lh_white_H'),
                                              ('lh_white_K', 'surf.@lh_white_K'),
                                              ('lh_inflated_H', 'surf.@lh_inflated_H'),
                                              ('lh_inflated_K', 'surf.@lh_inflated_K'),
                                              ('lh_curv_stats', 'surf.@lh_curv_stats'),
                                              ('rh_orig_nofix', 'surf.@rh_orig_nofix'),
                                              ('rh_orig', 'surf.@rh_orig'),
                                              ('rh_smoothwm_nofix', 'surf.@rh_smoothwm_nofix'),
                                              ('rh_inflated_nofix', 'surf.@rh_inflated_nofix'),
                                              ('rh_qsphere_nofix', 'surf.@rh_qsphere_nofix'),
                                              ('rh_white', 'surf.@rh_white'),
                                              ('rh_curv', 'surf.@rh_curv'),
                                              ('rh_area', 'surf.@rh_area'),
                                              ('rh_cortex', 'surf.@rh_cortex'),
                                              ('rh_thickness', 'surf.@rh_thickness'),
                                              ('rh_smoothwm', 'surf.@rh_smoothwm'),
                                              ('rh_sulc', 'surf.@rh_sulc'),
                                              ('rh_inflated', 'surf.@rh_inflated'),
                                              ('rh_white_H', 'surf.@rh_white_H'),
                                              ('rh_white_K', 'surf.@rh_white_K'),
                                              ('rh_inflated_H', 'surf.@rh_inflated_H'),
                                              ('rh_inflated_K', 'surf.@rh_inflated_K'),
                                              ('rh_curv_stats', 'surf.@rh_curv_stats'),
                                              ('lh_aparc_annot_ctab', 'label.@aparc_annot_ctab'),
                                              ('aseg', 'mri.@aseg'),
                                              ('wmparc', 'mri.@wmparc'),
                                              ('wmparc_stats', 'stats.@wmparc_stats'),
                                              ('aseg_stats', 'stats.@aseg_stats'),
                                              ('aparc_a2009s_aseg', 'mri.@aparc_a2009s_aseg'),
                                              ('aparc_aseg', 'mri.@aparc_aseg'),
                                              ('aseg_presurf_hypos', 'mri.@aseg_presurf_hypos'),
                                              ('ribbon', 'mri.@ribbon'),
                                              ('rh_ribbon', 'mri.@rh_ribbon'),
                                              ('lh_ribbon', 'mri.@lh_ribbon'),
                                              ('lh_sphere', 'surf.@lh_sphere'),
                                              ('rh_sphere', 'surf.@rh_sphere'),
                                              ('lh_sphere_reg', 'surf.@lh_sphere_reg'),
                                              ('rh_sphere_reg', 'surf.@rh_sphere_reg'),
                                              ('lh_jacobian_white', 'surf.@lh_jacobian_white'),
                                              ('rh_jacobian_white', 'surf.@rh_jacobian_white'),
                                              ('lh_avg_curv', 'surf.@lh_avg_curv'),
                                              ('rh_avg_curv', 'surf.@rh_avg_curv'),
                                              ('lh_aparc_annot', 'surf.@lh_aparc_annot'),
                                              ('rh_aparc_annot', 'surf.@rh_aparc_annot'),
                                              ('lh_area_pial', 'surf.@lh_area_pial'),
                                              ('rh_area_pial', 'surf.@rh_area_pial'),
                                              ('lh_curv_pial', 'surf.@lh_curv_pial'),
                                              ('rh_curv_pial', 'surf.@rh_curv_pial'),
                                              ('lh_pial', 'surf.@lh_pial'),
                                              ('rh_pial', 'surf.@rh_pial'),
                                              ('lh_thickness_pial', 'surf.@lh_thickness_pial'),
                                              ('rh_thickness_pial', 'surf.@rh_thickness_pial'),
                                              ('lh_area_mid', 'surf.@lh_area_mid'),
                                              ('rh_area_mid', 'surf.@rh_area_mid'),
                                              ('lh_volume', 'surf.@lh_volume'),
                                              ('rh_volume', 'surf.@rh_volume'),
                                              ('lh_aparc_annot_ctab', 'label.@lh_aparc_annot_ctab'),
                                              ('rh_aparc_annot_ctab', 'label.@rh_aparc_annot_ctab'),
                                              ('lh_aparc_stats', 'stats.@lh_aparc_stats'),
                                              ('rh_aparc_stats', 'stats.@rh_aparc_stats'),
                                              ('lh_aparc_pial_stats', 'stats.@lh_aparc_pial_stats'),
                                              ('rh_aparc_pial_stats', 'stats.@rh_aparc_pial_stats'),
                                              ('lh_aparc_a2009s_annot', 'label.@lh_aparc_a2009s_annot'),
                                              ('rh_aparc_a2009s_annot', 'label.@rh_aparc_a2009s_annot'),
                                              ('lh_aparc_a2009s_annot_ctab', 'label.@lh_aparc_a2009s_annot_ctab'),
                                              ('rh_aparc_a2009s_annot_ctab', 'label.@rh_aparc_a2009s_annot_ctab'),
                                              ('lh_aparc_a2009s_annot_stats', 'stats.@lh_aparc_a2009s_annot_stats'),
                                              ('rh_aparc_a2009s_annot_stats', 'stats.@rh_aparc_a2009s_annot_stats'),
                                              ('lh_aparc_DKTatlas40_annot', 'label.@lh_aparc_DKTatlas40_annot'),
                                              ('rh_aparc_DKTatlas40_annot', 'label.@rh_aparc_DKTatlas40_annot'),
                                              ('lh_aparc_DKTatlas40_annot_ctab', 'label.@lh_aparc_DKTatlas40_annot_ctab'),
                                              ('rh_aparc_DKTatlas40_annot_ctab', 'label.@rh_aparc_DKTatlas40_annot_ctab'),
                                              ('lh_aparc_DKTatlas40_annot_stats', 'stats.@lh_aparc_DKTatlas40_annot_stats'),
                                              ('rh_aparc_DKTatlas40_annot_stats', 'stats.@rh_aparc_DKTatlas40_annot_stats'),
                                              ('lh_wg_pct_mgh', 'surf.@lh_wg_pct_mgh'),
                                              ('rh_wg_pct_mgh', 'surf.@rh_wg_pct_mgh'),
                                              ('lh_wg_pct_stats', 'stats.@lh_wg_pct_stats'),
                                              ('rh_wg_pct_stats', 'stats.@rh_wg_pct_stats'),
                                              ('lh_pctsurfcon_log', 'log.@lh_pctsurfcon_log'),
                                              ('rh_pctsurfcon_log', 'log.@rh_pctsurfcon_log'),
                                          ]),
                      ])

    #### Workflow additions go here
    if defaultconfig['recoding_file']:
        from utils import create_recoding_wf
        recode = create_recoding_wf(defaultconfig['recoding_file'])
        reconall.connect([(ar3_wf, recode, [('outputspec.aseg', 'inputspec.labelmap')]),
                          (recode, outputspec, [('outputspec.recodedlabelmap', 'recoded_labelmap')])])
        
        
    return reconall



    
