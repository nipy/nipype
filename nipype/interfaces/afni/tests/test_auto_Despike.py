# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..preprocess import Despike


def test_Despike_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    in_file=dict(argstr='%s',
    copyfile=False,
    mandatory=True,
    position=-1,
    ),
    out_file=dict(keep_extension=False,
    ),
    outputtype=dict(usedefault=True,
    ),
    prefix=dict(argstr='-prefix %s',
    keep_extension=False,
    ),
    )
    inputs = Despike._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_Despike_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = Despike._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
