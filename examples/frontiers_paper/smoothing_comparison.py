# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
=============================
Smoothing comparison workflow
=============================
"""


import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.spm as spm          # spm
import nipype.interfaces.freesurfer as fs    # freesurfer
import nipype.interfaces.nipy as nipy
import nipype.interfaces.utility as util
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.algorithms.modelgen as model   # model specification
import nipype.workflows.fmri.fsl as fsl_wf
from nipype.interfaces.base import Bunch
import os                                    # system functions

preprocessing = pe.Workflow(name="preprocessing")

iter_fwhm = pe.Node(interface=util.IdentityInterface(fields=["fwhm"]),
                    name="iter_fwhm")
iter_fwhm.iterables = [('fwhm', [4, 8])]

iter_smoothing_method = pe.Node(interface=util.IdentityInterface(fields=["smoothing_method"]),
                    name="iter_smoothing_method")
iter_smoothing_method.iterables = [('smoothing_method',['isotropic_voxel',
                                           'anisotropic_voxel',
                                           'isotropic_surface'])]

realign = pe.Node(interface=spm.Realign(), name="realign")
realign.inputs.register_to_mean = True

isotropic_voxel_smooth = pe.Node(interface=spm.Smooth(),
                                 name="isotropic_voxel_smooth")
preprocessing.connect(realign, "realigned_files", isotropic_voxel_smooth,
                      "in_files")
preprocessing.connect(iter_fwhm, "fwhm", isotropic_voxel_smooth, "fwhm")

compute_mask = pe.Node(interface=nipy.ComputeMask(), name="compute_mask")
preprocessing.connect(realign, "mean_image", compute_mask, "mean_volume")

anisotropic_voxel_smooth = fsl_wf.create_susan_smooth(name="anisotropic_voxel_smooth",
                                                      separate_masks=False)
anisotropic_voxel_smooth.inputs.smooth.output_type = 'NIFTI'
preprocessing.connect(realign, "realigned_files", anisotropic_voxel_smooth,
                      "inputnode.in_files")
preprocessing.connect(iter_fwhm, "fwhm", anisotropic_voxel_smooth,
                      "inputnode.fwhm")
preprocessing.connect(compute_mask, "brain_mask", anisotropic_voxel_smooth,
                      'inputnode.mask_file')



recon_all = pe.Node(interface=fs.ReconAll(), name = "recon_all")

surfregister = pe.Node(interface=fs.BBRegister(),name='surfregister')
surfregister.inputs.init = 'fsl'
surfregister.inputs.contrast_type = 't2'
preprocessing.connect(realign, 'mean_image', surfregister, 'source_file')
preprocessing.connect(recon_all, 'subject_id', surfregister, 'subject_id')
preprocessing.connect(recon_all, 'subjects_dir', surfregister, 'subjects_dir')

isotropic_surface_smooth = pe.MapNode(interface=fs.Smooth(proj_frac_avg=(0,1,0.1)),
                                      iterfield=['in_file'],
                                      name="isotropic_surface_smooth")
preprocessing.connect(surfregister, 'out_reg_file', isotropic_surface_smooth,
                      'reg_file')
preprocessing.connect(realign, "realigned_files", isotropic_surface_smooth,
                      "in_file")
preprocessing.connect(iter_fwhm, "fwhm", isotropic_surface_smooth,
                      "surface_fwhm")
preprocessing.connect(iter_fwhm, "fwhm", isotropic_surface_smooth, "vol_fwhm")
preprocessing.connect(recon_all, 'subjects_dir', isotropic_surface_smooth,
                      'subjects_dir')

merge_smoothed_files = pe.Node(interface=util.Merge(3),
                               name='merge_smoothed_files')
preprocessing.connect(isotropic_voxel_smooth, 'smoothed_files',
                      merge_smoothed_files, 'in1')
preprocessing.connect(anisotropic_voxel_smooth, 'outputnode.smoothed_files',
                      merge_smoothed_files, 'in2')
preprocessing.connect(isotropic_surface_smooth, 'smoothed_file',
                      merge_smoothed_files, 'in3')

select_smoothed_files = pe.Node(interface=util.Select(),
                                name="select_smoothed_files")
preprocessing.connect(merge_smoothed_files, 'out', select_smoothed_files,
                      'inlist')

def chooseindex(roi):
    return {'isotropic_voxel':range(0,4), 'anisotropic_voxel':range(4,8),
            'isotropic_surface':range(8,12)}[roi]

preprocessing.connect(iter_smoothing_method, ("smoothing_method", chooseindex),
                      select_smoothed_files, 'index')

rename = pe.MapNode(util.Rename(format_string="%(orig)s"), name="rename",
                    iterfield=['in_file'])
rename.inputs.parse_string = "(?P<orig>.*)"

preprocessing.connect(select_smoothed_files, 'out', rename, 'in_file')

specify_model = pe.Node(interface=model.SpecifyModel(), name="specify_model")
specify_model.inputs.input_units             = 'secs'
specify_model.inputs.time_repetition         = 3.
specify_model.inputs.high_pass_filter_cutoff = 120
specify_model.inputs.subject_info = [Bunch(conditions=['Task-Odd','Task-Even'],
                                           onsets=[range(15,240,60),
                                                   range(45,240,60)],
                                           durations=[[15], [15]])]*4

level1design = pe.Node(interface=spm.Level1Design(), name= "level1design")
level1design.inputs.bases = {'hrf':{'derivs': [0,0]}}
level1design.inputs.timing_units = 'secs'
level1design.inputs.interscan_interval = specify_model.inputs.time_repetition

level1estimate = pe.Node(interface=spm.EstimateModel(), name="level1estimate")
level1estimate.inputs.estimation_method = {'Classical' : 1}

contrastestimate = pe.Node(interface = spm.EstimateContrast(),
                           name="contrastestimate")
contrastestimate.inputs.contrasts = [('Task>Baseline','T',
                                      ['Task-Odd','Task-Even'],[0.5,0.5])]

modelling = pe.Workflow(name="modelling")
modelling.connect(specify_model, 'session_info', level1design, 'session_info')
modelling.connect(level1design, 'spm_mat_file', level1estimate, 'spm_mat_file')
modelling.connect(level1estimate,'spm_mat_file', contrastestimate,
                  'spm_mat_file')
modelling.connect(level1estimate,'beta_images', contrastestimate,'beta_images')
modelling.connect(level1estimate,'residual_image', contrastestimate,
                  'residual_image')

main_workflow = pe.Workflow(name="main_workflow")
main_workflow.base_dir = "smoothing_comparison_workflow"
main_workflow.connect(preprocessing, "realign.realignment_parameters",
                      modelling, "specify_model.realignment_parameters")
main_workflow.connect(preprocessing, "select_smoothed_files.out",
                      modelling, "specify_model.functional_runs")
main_workflow.connect(preprocessing, "compute_mask.brain_mask",
                      modelling, "level1design.mask_image")

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=['func', 'struct']),
                     name = 'datasource')
datasource.inputs.base_directory = os.path.abspath('data')
datasource.inputs.template = '%s/%s.nii'
datasource.inputs.template_args = info = dict(func=[['subject_id',
                                                     ['f3','f5','f7','f10']]],
                                              struct=[['subject_id','struct']])
datasource.inputs.subject_id = 's1'

main_workflow.connect(datasource, 'func', preprocessing, 'realign.in_files')
main_workflow.connect(datasource, 'struct', preprocessing,
                      'recon_all.T1_files')

datasink = pe.Node(interface=nio.DataSink(), name="datasink")
datasink.inputs.base_directory = os.path.abspath('smoothing_comparison_workflow/output')
datasink.inputs.regexp_substitutions = [("_rename[0-9]", "")]

main_workflow.connect(modelling, 'contrastestimate.spmT_images', datasink,
                      'contrasts')
main_workflow.connect(preprocessing, 'rename.out_file', datasink,
                      'smoothed_epi')

main_workflow.run()
main_workflow.write_graph()
