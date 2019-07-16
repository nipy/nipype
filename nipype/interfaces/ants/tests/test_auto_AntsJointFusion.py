# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..segmentation import AntsJointFusion


def test_AntsJointFusion_inputs():
    input_map = dict(
        alpha=dict(
            argstr='-a %s',
            usedefault=True,
        ),
        args=dict(argstr='%s', ),
        atlas_image=dict(
            argstr='-g %s...',
            mandatory=True,
        ),
        atlas_segmentation_image=dict(
            argstr='-l %s...',
            mandatory=True,
        ),
        beta=dict(
            argstr='-b %s',
            usedefault=True,
        ),
        constrain_nonnegative=dict(
            argstr='-c',
            usedefault=True,
        ),
        dimension=dict(argstr='-d %d', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        exclusion_image=dict(),
        exclusion_image_label=dict(
            argstr='-e %s',
            requires=['exclusion_image'],
        ),
        mask_image=dict(
            argstr='-x %s',
            usedefault=True,
        ),
        num_threads=dict(
            nohash=True,
            usedefault=True,
        ),
        out_atlas_voting_weight_name_format=dict(
            requires=[
                'out_label_fusion', 'out_intensity_fusion_name_format',
                'out_label_post_prob_name_format'
            ], ),
        out_intensity_fusion_name_format=dict(argstr='', ),
        out_label_fusion=dict(
            argstr='%s',
            hash_files=False,
            usedefault=True,
        ),
        out_label_post_prob_name_format=dict(
            requires=['out_label_fusion', 'out_intensity_fusion_name_format'],
        ),
        patch_metric=dict(argstr='-m %s', ),
        patch_radius=dict(
            argstr='-p %s',
            maxlen=3,
            minlen=3,
        ),
        retain_atlas_voting_images=dict(
            argstr='-f',
            usedefault=True,
        ),
        retain_label_posterior_images=dict(
            argstr='-r',
            requires=['atlas_segmentation_image'],
            usedefault=True,
        ),
        search_radius=dict(
            argstr='-s %s',
            usedefault=True,
        ),
        target_image=dict(
            argstr='-t %s',
            mandatory=True,
        ),
        verbose=dict(argstr='-v', ),
    )
    inputs = AntsJointFusion.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_AntsJointFusion_outputs():
    output_map = dict(
        out_atlas_voting_weight_name_format=dict(),
        out_intensity_fusion_name_format=dict(),
        out_label_fusion=dict(usedefault=True, ),
        out_label_post_prob_name_format=dict(),
    )
    outputs = AntsJointFusion.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
