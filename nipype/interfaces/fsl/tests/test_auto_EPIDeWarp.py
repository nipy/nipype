# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..epi import EPIDeWarp


def test_EPIDeWarp_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    cleanup=dict(argstr='--cleanup',
    ),
    dph_file=dict(argstr='--dph %s',
    mandatory=True,
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    epi_file=dict(argstr='--epi %s',
    ),
    epidw=dict(argstr='--epidw %s',
    genfile=False,
    ),
    esp=dict(argstr='--esp %s',
    usedefault=True,
    ),
    exf_file=dict(argstr='--exf %s',
    ),
    exfdw=dict(argstr='--exfdw %s',
    genfile=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    mag_file=dict(argstr='--mag %s',
    mandatory=True,
    position=0,
    ),
    nocleanup=dict(argstr='--nocleanup',
    usedefault=True,
    ),
    output_type=dict(),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    sigma=dict(argstr='--sigma %s',
    usedefault=True,
    ),
    tediff=dict(argstr='--tediff %s',
    usedefault=True,
    ),
    terminal_output=dict(nohash=True,
    ),
    tmpdir=dict(argstr='--tmpdir %s',
    genfile=True,
    ),
    vsm=dict(argstr='--vsm %s',
    genfile=True,
    ),
    )
    inputs = EPIDeWarp.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_EPIDeWarp_outputs():
    output_map = dict(exf_mask=dict(),
    exfdw=dict(),
    unwarped_file=dict(),
    vsm_file=dict(),
    )
    outputs = EPIDeWarp.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
