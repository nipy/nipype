# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from nipype.testing import assert_equal
from nipype.interfaces.semtools.diffusion.gtract import gtractCopyImageOrientation

def test_gtractCopyImageOrientation_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    inputReferenceVolume=dict(argstr='--inputReferenceVolume %s',
    ),
    inputVolume=dict(argstr='--inputVolume %s',
    ),
    numberOfThreads=dict(argstr='--numberOfThreads %d',
    ),
    outputVolume=dict(argstr='--outputVolume %s',
    hash_files=False,
    ),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = gtractCopyImageOrientation.input_spec()

    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(inputs.traits()[key], metakey), value

def test_gtractCopyImageOrientation_outputs():
    output_map = dict(outputVolume=dict(),
    )
    outputs = gtractCopyImageOrientation.output_spec()

    for key, metadata in output_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(outputs.traits()[key], metakey), value

