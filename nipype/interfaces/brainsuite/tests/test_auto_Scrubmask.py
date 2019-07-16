# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..brainsuite import Scrubmask


def test_Scrubmask_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        backgroundFillThreshold=dict(
            argstr='-b %d',
            usedefault=True,
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        foregroundTrimThreshold=dict(
            argstr='-f %d',
            usedefault=True,
        ),
        inputMaskFile=dict(
            argstr='-i %s',
            mandatory=True,
            usedefault=True,
        ),
        numberIterations=dict(argstr='-n %d', ),
        outputMaskFile=dict(
            argstr='-o %s',
            genfile=True,
            usedefault=True,
        ),
        timer=dict(argstr='--timer', ),
        verbosity=dict(argstr='-v %d', ),
    )
    inputs = Scrubmask.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_Scrubmask_outputs():
    output_map = dict(outputMaskFile=dict(usedefault=True, ), )
    outputs = Scrubmask.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
