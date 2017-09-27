# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..dti import MakeDyadicVectors


def test_MakeDyadicVectors_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    mask=dict(argstr='%s',
    position=2,
    ),
    output=dict(argstr='%s',
    hash_files=False,
    position=3,
    usedefault=True,
    ),
    output_type=dict(),
    perc=dict(argstr='%f',
    position=4,
    ),
    phi_vol=dict(argstr='%s',
    mandatory=True,
    position=1,
    ),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    terminal_output=dict(nohash=True,
    ),
    theta_vol=dict(argstr='%s',
    mandatory=True,
    position=0,
    ),
    )
    inputs = MakeDyadicVectors.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_MakeDyadicVectors_outputs():
    output_map = dict(dispersion=dict(),
    dyads=dict(),
    )
    outputs = MakeDyadicVectors.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
