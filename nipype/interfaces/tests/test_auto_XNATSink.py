# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ...testing import assert_equal
from ..io import XNATSink


def test_XNATSink_inputs():
    input_map = dict(_outputs=dict(usedefault=True,
    ),
    assessor_id=dict(xor=['reconstruction_id'],
    ),
    cache_dir=dict(),
    config=dict(mandatory=True,
    xor=['server'],
    ),
    experiment_id=dict(mandatory=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    project_id=dict(mandatory=True,
    ),
    pwd=dict(),
    reconstruction_id=dict(xor=['assessor_id'],
    ),
    server=dict(mandatory=True,
    requires=['user', 'pwd'],
    xor=['config'],
    ),
    share=dict(usedefault=True,
    ),
    subject_id=dict(mandatory=True,
    ),
    user=dict(),
    )
    inputs = XNATSink.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_XNATSink_outputs():
    output_map = dict()
    outputs = XNATSink.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
