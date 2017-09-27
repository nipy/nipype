# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..diffusion import DWIRicianLMMSEFilter


def test_DWIRicianLMMSEFilter_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    compressOutput=dict(argstr='--compressOutput ',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    hrf=dict(argstr='--hrf %f',
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    inputVolume=dict(argstr='%s',
    position=-2,
    ),
    iter=dict(argstr='--iter %d',
    ),
    maxnstd=dict(argstr='--maxnstd %d',
    ),
    minnstd=dict(argstr='--minnstd %d',
    ),
    mnve=dict(argstr='--mnve %d',
    ),
    mnvf=dict(argstr='--mnvf %d',
    ),
    outputVolume=dict(argstr='%s',
    hash_files=False,
    position=-1,
    ),
    re=dict(argstr='--re %s',
    sep=',',
    ),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    rf=dict(argstr='--rf %s',
    sep=',',
    ),
    terminal_output=dict(nohash=True,
    ),
    uav=dict(argstr='--uav ',
    ),
    )
    inputs = DWIRicianLMMSEFilter.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_DWIRicianLMMSEFilter_outputs():
    output_map = dict(outputVolume=dict(position=-1,
    ),
    )
    outputs = DWIRicianLMMSEFilter.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
