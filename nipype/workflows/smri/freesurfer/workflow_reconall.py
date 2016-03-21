import nipype
import nipype.pipeline.engine as pe  # pypeline engine
from nipype.interfaces.io import DataGrabber, FreeSurferSource, DataSink
from nipype.interfaces.freesurfer import AddXFormToHeader
from nipype.interfaces.utility import Merge, IdentityInterface
from autorecon1 import create_AutoRecon1
from autorecon2 import create_AutoRecon2
from autorecon3 import create_AutoRecon3
import os

def create_reconall(config):
    ar1_wf, ar1_outputs = create_AutoRecon1(config)
    ar2_wf, ar2_outputs = create_AutoRecon2(config)
    ar3_wf, ar3_outputs = create_AutoRecon3(config)

    # Connect workflows 
    reconall = pe.Workflow(name="recon-all")

    # connect autorecon 1 - 3 
    reconall.connect([(ar1_wf, ar3_wf, [('outputspec.brainmask', 'inputspec.brainmask'),
                                        ('outputspec.talairach', 'inputspec.transform'),
                                        ('outputspec.orig', 'inputspec.orig_mgz'),
                                        ('outputspec.rawavg', 'inputspec.rawavg'),
                                        ]),
                      (ar1_wf, ar2_wf, [('outputspec.brainmask', 'inputspec.brainmask'),
                                        ('outputspec.talairach', 'inputspec.transform'),
                                        ('outputspec.orig', 'inputspec.orig'),
                                        ]),
                      (ar2_wf, ar3_wf, [('outputspec.aseg_presurf', 'inputspec.aseg_presurf'),
                                        ('outputspec.brain_finalsurfs', 'inputspec.brain_finalsurfs'),
                                        ('outputspec.wm', 'inputspec.wm'),
                                        ('outputspec.filled', 'inputspec.filled'),
                                        ('outputspec.norm', 'inputspec.norm'),
                                        ]),
                      ])
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
    outputspec = pe.Node(IdentityInterface(fields=outputs, mandatory_inputs=True),
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
    
    # TODO: Make this into a node
    datasinked_transform = os.path.join(config['subjects_dir'], config['current_id'],
                                        'mri', 'transforms' 'talairach.xfm')
    
    predatasink_orig = pe.Node(AddXFormToHeader(), name="PreDataSink_Orig")
    predatasink_orig.inputs.copy_name = True
    predatasink_orig.inputs.out_file = 'orig.mgz'
    predatasink_orig.inputs.transform = datasinked_transform
    reconall.connect([(outputspec, predatasink_orig, [('orig', 'in_file')])])
    predatasink_orig_nu = pe.Node(AddXFormToHeader(), name="PreDataSink_Orig_Nu")
    predatasink_orig_nu.inputs.copy_name = True
    predatasink_orig_nu.inputs.out_file = 'orig_nu.mgz'
    predatasink_orig_nu.inputs.transform = datasinked_transform
    reconall.connect([(outputspec, predatasink_orig_nu, [('orig_nu', 'in_file')])])
    predatasink_nu = pe.Node(AddXFormToHeader(), name="PreDataSink_Nu")
    predatasink_nu.inputs.copy_name = True
    predatasink_nu.inputs.out_file = 'nu.mgz'
    predatasink_nu.inputs.transform = datasinked_transform
    reconall.connect([(outputspec, predatasink_nu, [('nu', 'in_file')])])

    
    # Datasink outputs
    datasink = pe.Node(DataSink(), name="DataSink")
    datasink.inputs.container = config['current_id']
    datasink.inputs.base_directory = config['subjects_dir']
    

    # substitutions
    #TODO: Make this into a node
    subs = list()
    for i in range(len(config['in_T1s'])):
        subs.append(("_T1_prep{0}".format(i), ""))
    datasink.inputs.substitutions = subs
    
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
    if config['recoding_file'] != None:
        from utils import create_recoding_wf
        recode = create_recoding_wf(config['recoding_file'])
        reconall.connect([(ar3_wf, recode, [('outputspec.aseg', 'inputspec.labelmap')]),
                          (recode, outputspec, [('outputspec.recodedlabelmap', 'recoded_labelmap')])])
        
        
    return reconall

