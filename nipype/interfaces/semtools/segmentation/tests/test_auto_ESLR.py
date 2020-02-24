# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..specialized import ESLR


def test_ESLR_inputs():
    input_map = dict(
        args=dict(argstr="%s",),
        closingSize=dict(argstr="--closingSize %d",),
        environ=dict(nohash=True, usedefault=True,),
        high=dict(argstr="--high %d",),
        inputVolume=dict(argstr="--inputVolume %s", extensions=None,),
        low=dict(argstr="--low %d",),
        numberOfThreads=dict(argstr="--numberOfThreads %d",),
        openingSize=dict(argstr="--openingSize %d",),
        outputVolume=dict(argstr="--outputVolume %s", hash_files=False,),
        preserveOutside=dict(argstr="--preserveOutside ",),
        safetySize=dict(argstr="--safetySize %d",),
    )
    inputs = ESLR.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_ESLR_outputs():
    output_map = dict(outputVolume=dict(extensions=None,),)
    outputs = ESLR.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
