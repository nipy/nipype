# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..io import DataFinder


def test_DataFinder_inputs():
    input_map = dict(ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    ignore_regexes=dict(),
    match_regex=dict(usedefault=True,
    ),
    max_depth=dict(),
    min_depth=dict(),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    root_paths=dict(mandatory=True,
    ),
    unpack_single=dict(usedefault=True,
    ),
    )
    inputs = DataFinder.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_DataFinder_outputs():
    output_map = dict()
    outputs = DataFinder.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
