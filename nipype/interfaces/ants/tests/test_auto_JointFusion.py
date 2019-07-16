# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..segmentation import JointFusion


def test_JointFusion_inputs():
    input_map = dict(
        alpha=dict(
            requires=['method'],
            usedefault=True,
        ),
        args=dict(argstr='%s', ),
        atlas_group_id=dict(argstr='-gp %d...', ),
        atlas_group_weights=dict(argstr='-gpw %d...', ),
        beta=dict(
            requires=['method'],
            usedefault=True,
        ),
        dimension=dict(
            argstr='%d',
            mandatory=True,
            position=0,
            usedefault=True,
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        exclusion_region=dict(
            argstr='-x %s',
            usedefault=True,
        ),
        method=dict(
            argstr='-m %s',
            usedefault=True,
        ),
        modalities=dict(
            argstr='%d',
            mandatory=True,
            position=1,
        ),
        num_threads=dict(
            nohash=True,
            usedefault=True,
        ),
        output_label_image=dict(
            argstr='%s',
            mandatory=True,
            name_template='%s',
            output_name='output_label_image',
            position=-1,
            usedefault=True,
        ),
        patch_radius=dict(
            argstr='-rp %s',
            maxlen=3,
            minlen=3,
        ),
        search_radius=dict(
            argstr='-rs %s',
            maxlen=3,
            minlen=3,
        ),
        target_image=dict(
            argstr='-tg %s...',
            mandatory=True,
        ),
        warped_intensity_images=dict(
            argstr='-g %s...',
            mandatory=True,
        ),
        warped_label_images=dict(
            argstr='-l %s...',
            mandatory=True,
        ),
    )
    inputs = JointFusion.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_JointFusion_outputs():
    output_map = dict(output_label_image=dict(usedefault=True, ), )
    outputs = JointFusion.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
