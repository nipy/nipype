# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..dti import PicoPDFs


def test_PicoPDFs_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    directmap=dict(argstr='-directmap',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    in_file=dict(argstr='< %s',
    mandatory=True,
    position=1,
    ),
    inputmodel=dict(argstr='-inputmodel %s',
    position=2,
    usedefault=True,
    ),
    luts=dict(argstr='-luts %s',
    mandatory=True,
    ),
    maxcomponents=dict(argstr='-maxcomponents %d',
    units='NA',
    ),
    numpds=dict(argstr='-numpds %d',
    units='NA',
    ),
    out_file=dict(argstr='> %s',
    genfile=True,
    position=-1,
    ),
    pdf=dict(argstr='-pdf %s',
    position=4,
    usedefault=True,
    ),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = PicoPDFs.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_PicoPDFs_outputs():
    output_map = dict(pdfs=dict(),
    )
    outputs = PicoPDFs.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
