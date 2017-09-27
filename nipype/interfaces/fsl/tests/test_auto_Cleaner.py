# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..fix import Cleaner


def test_Cleaner_inputs():
    input_map = dict(aggressive=dict(argstr='-A',
    position=3,
    ),
    args=dict(argstr='%s',
    ),
    artifacts_list_file=dict(argstr='%s',
    mandatory=True,
    position=1,
    ),
    cleanup_motion=dict(argstr='-m',
    position=2,
    ),
    confound_file=dict(argstr='-x %s',
    position=4,
    ),
    confound_file_1=dict(argstr='-x %s',
    position=5,
    ),
    confound_file_2=dict(argstr='-x %s',
    position=6,
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    highpass=dict(argstr='-m -h %f',
    position=2,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = Cleaner.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_Cleaner_outputs():
    output_map = dict(cleaned_functional_file=dict(),
    )
    outputs = Cleaner.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
