# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ...testing import assert_equal
from ..io import DataSink


def test_DataSink_inputs():
    input_map = dict(_outputs=dict(usedefault=True,
    ),
    base_directory=dict(),
    bucket=dict(mandatory=False,
    trait_value=True,
    ),
    container=dict(),
    creds_path=dict(),
    encrypt_bucket_keys=dict(),
    local_copy=dict(),
    parameterization=dict(usedefault=True,
    ),
    regexp_substitutions=dict(),
    remove_dest_dir=dict(usedefault=True,
    ),
    strip_dir=dict(),
    substitutions=dict(),
    )
    inputs = DataSink._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_DataSink_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = DataSink._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
