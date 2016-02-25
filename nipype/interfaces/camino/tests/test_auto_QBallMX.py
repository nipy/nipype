# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..odf import QBallMX


def test_QBallMX_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    basistype=dict(argstr='-basistype %s',
    usedefault=True,
    ),
    order=dict(argstr='-order %d',
    units='NA',
    ),
    out_file=dict(argstr='> %s',
    position=-1,
    usedefault=True,
    ),
    rbfpointset=dict(argstr='-rbfpointset %d',
    units='NA',
    ),
    rbfsigma=dict(argstr='-rbfsigma %f',
    units='NA',
    ),
    scheme_file=dict(argstr='-schemefile %s',
    mandatory=True,
    ),
    smoothingsigma=dict(argstr='-smoothingsigma %f',
    units='NA',
    ),
    )
    inputs = QBallMX._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_QBallMX_outputs():
    output_map = dict(qmat=dict(),
    )
    outputs = QBallMX._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
