# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..dti import MakeDyadicVectors


def test_MakeDyadicVectors_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    mask=dict(argstr='%s',
    position=2,
    ),
    output=dict(argstr='%s',
    hash_files=False,
    position=3,
    usedefault=True,
    ),
    output_type=dict(usedefault=True,
    ),
    perc=dict(argstr='%f',
    position=4,
    ),
    phi_vol=dict(argstr='%s',
    mandatory=True,
    position=1,
    ),
    theta_vol=dict(argstr='%s',
    mandatory=True,
    position=0,
    ),
    )
    inputs = MakeDyadicVectors._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_MakeDyadicVectors_outputs():
    output_map = dict(dispersion=dict(),
    dyads=dict(),
    )
    outputs = MakeDyadicVectors._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
