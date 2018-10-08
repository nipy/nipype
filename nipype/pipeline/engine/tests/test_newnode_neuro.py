import os
import pytest

from nipype.pipeline.engine import NewNode, NewWorkflow
from ..submitter import Submitter

#dj niworkflows vs ...??
from nipype.interfaces.utility import Rename
import nipype.interfaces.freesurfer as fs

from fmriprep.interfaces.freesurfer import PatchedConcatenateLTA as ConcatenateLTA

@pytest.fixture()
def change_dir(request):
    orig_dir = os.getcwd()
    test_dir = os.path.join(orig_dir, "/nipype/nipype/pipeline/engine/test_neuro")
    os.makedirs(test_dir, exist_ok=True)
    os.chdir(test_dir)

    def move2orig():
        os.chdir(orig_dir)

    request.addfinalizer(move2orig)

import pdb

Name = "example"
DEFAULT_MEMORY_MIN_GB = None
# TODO, adding fields to Inputs (subject_id)
Inputs = {"subject_id": "sub-01",
          "output_spaces": ["fsaverage", "fsaverage5"],
          "source_file": "/fmriprep_test/workdir1/fmriprep_wf/single_subject_01_wf/func_preproc_ses_test_task_fingerfootlips_wf/bold_t1_trans_wf/merge/vol0000_xform-00000_merged.nii",
          "t1_preproc": "/fmriprep_test/output1/fmriprep/sub-01/anat/sub-01_T1w_preproc.nii.gz",
          "t1_2_fsnative_forward_transform": "/fmriprep_test/workdir1/fmriprep_wf/single_subject_01_wf/anat_preproc_wf/surface_recon_wf/t1_2_fsnative_xfm/out.lta",
          "subjects_dir": "/fmriprep_test/output1/freesurfer/"
}

Plugins = ["serial", "mp", "cf", "dask"]

def select_target(subject_id, space):
    """ Given a source subject ID and a target space, get the target subject ID """
    return subject_id if space == 'fsnative' else space

@pytest.mark.parametrize("plugin", Plugins)
def test_neuro(change_dir, plugin):

    # wf = Workflow(name, mem_gb_node=DEFAULT_MEMORY_MIN_GB,
    #               inputs=['source_file', 't1_preproc', 'subject_id',
    #                       'subjects_dir', 't1_2_fsnative_forward_transform',
    #                       'mem_gb', 'output_spaces', 'medial_surface_nan'],
    #               outputs='surfaces')
    #
    #dj: why do I need outputs?


    wf = NewWorkflow(name=Name, inputs=Inputs, workingdir="test_neuro_{}".format(plugin), print_val=False,
                     wf_output_names=[("sampler", "out_file", "sampler_out"), ("targets", "out", "target_out")])

    # @interface
    # def select_target(subject_id, space):
    #     """ Given a source subject ID and a target space, get the target subject ID """
    #     return subject_id if space == 'fsnative' else space



    # wf.add('targets', select_target(subject_id=wf.inputs.subject_id))
    #   .map('space', space=[space for space in wf.inputs.output_spaces
    #                        if space.startswith('fs')])

    #dj: don't have option in map to connect with wf input

    wf.add(runnable=select_target, name="targets", subject_id="subject_id", output_names=["out"],
           out_read=True, print_val=False)\
        .map_node(mapper="space", inputs={"space": [space for space in Inputs["output_spaces"]
                                               if space.startswith("fs")]})

    # wf.add('rename_src', Rename(format_string='%(subject)s',
    #                             keep_ext=True,
    #                             in_file=wf.inputs.source_file))
    #   .map('subject')

    wf.add(name='rename_src',
           runnable=Rename(format_string='%(subject)s', keep_ext=True),
                                in_file="source_file", subject="subject_id",
                                output_names=["out_file"],
           print_val=False)\
    #    .map_node('subject') #TODO: now it's only one subject


    # wf.add('resampling_xfm',
    #        fs.utils.LTAConvert(in_lta='identity.nofile',
    #                            out_lta=True,
    #                            source_file=wf.inputs.source_file,
    #                            target_file=wf.inputs.t1_preproc)
    #   .add('set_xfm_source', ConcatenateLTA(out_type='RAS2RAS',
    #                                         in_lta2=wf.inputs.t1_2_fsnative_forward_transform,
    #                                         in_lta1=wf.resampling_xfm.out_lta))


    wf.add(name='resampling_xfm',
           runnable=fs.utils.LTAConvert(in_lta='identity.nofile', out_lta=True),
           source_file="source_file", target_file="t1_preproc",
           output_names=["out_lta"],
           print_val=False)\
        .add(name='set_xfm_source', runnable=ConcatenateLTA(out_type='RAS2RAS'),
            in_lta2="t1_2_fsnative_forward_transform", in_lta1="resampling_xfm.out_lta",
            output_names=["out_file"], print_val=False)



    # wf.add('sampler',
    #        fs.SampleToSurface(sampling_method='average', sampling_range=(0, 1, 0.2),
    #                           sampling_units='frac', interp_method='trilinear',
    #                           cortex_mask=True, override_reg_subj=True,
    #                           out_type='gii',
    #                           subjects_dir=wf.inputs.subjects_dir,
    #                           subject_id=wf.inputs.subject_id,
    #                           reg_file=wf.set_xfm_source.out_file,
    #                           target_subject=wf.targets.out,
    #                           source_file=wf.rename_src.out_file),
    #         mem_gb=mem_gb * 3)
    #        .map([('source_file', 'target_subject'), 'hemi'], hemi=['lh', 'rh'])


    wf.add(name='sampler',
           runnable=fs.SampleToSurface(sampling_method='average', sampling_range=(0, 1, 0.2),
                                  sampling_units='frac', interp_method='trilinear',
                                  cortex_mask=True, override_reg_subj=True,
                                  out_type='gii'), print_val=False,
           subjects_dir="subjects_dir", subject_id="subject_id", reg_file="set_xfm_source.out_file",
           target_subject="targets.out", source_file="rename_src.out_file", output_names=["out_file"])\
        .map_node(mapper=['_targets', 'hemi'], inputs={"hemi": ['lh', 'rh']})


    sub = Submitter(plugin=plugin, runnable=wf)
    sub.run()
    sub.close()

    assert "target_out" in wf.output.keys()
    assert len(list(wf.output["target_out"].keys())) == 2

    assert "sampler_out" in wf.output.keys()
    assert len(list(wf.output["sampler_out"].keys())) == 4
    # dj: no conditions
    # dj: no join for now

    # wf.add_cond('cond1',
    #             condition=wf.inputs.medial_surface_nan,
    #             iftrue=wf.add('medial_nans', MedialNaNs(subjects_dir=wf.inputs.subjects_dir,
    #                                              in_file=wf.sampler.out_file,
    #                                              target_subject=wf.targets.out))
    #                      .set_output('out', wf.median_nans.out),
    #             elseclause=wf.set_output('out', wf.sampler.out_file))
    #
    # wf.add('merger', niu.Merge(1, ravel_inputs=True,
    #                            in1=wf.cond1.out),
    #             run_without_submitting=True)
    #       .join('sampler.hemi')
    #
    # wf.add('update_metadata',
    #        GiftiSetAnatomicalStructure(in_file=wf.merger.out))
    # wf.outputs.surfaces = wf.update_metadata.out_file