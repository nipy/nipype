# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ...testing import assert_equal
from ..io import SQLiteSink


def test_SQLiteSink_inputs():
    input_map = dict(database_file=dict(mandatory=True,
    ),
    table_name=dict(mandatory=True,
    ),
    )
    inputs = SQLiteSink._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_SQLiteSink_outputs():
    output_map = dict()
    outputs = SQLiteSink._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
