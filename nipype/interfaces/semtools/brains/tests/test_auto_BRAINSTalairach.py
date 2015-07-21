# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from nipype.testing import assert_equal
from nipype.interfaces.semtools.brains.segmentation import BRAINSTalairach

def test_BRAINSTalairach_inputs():
    input_map = dict(AC=dict(argstr='--AC %s',
    sep=',',
    ),
    ACisIndex=dict(argstr='--ACisIndex ',
    ),
    IRP=dict(argstr='--IRP %s',
    sep=',',
    ),
    IRPisIndex=dict(argstr='--IRPisIndex ',
    ),
    PC=dict(argstr='--PC %s',
    sep=',',
    ),
    PCisIndex=dict(argstr='--PCisIndex ',
    ),
    SLA=dict(argstr='--SLA %s',
    sep=',',
    ),
    SLAisIndex=dict(argstr='--SLAisIndex ',
    ),
    args=dict(argstr='%s',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    inputVolume=dict(argstr='--inputVolume %s',
    ),
    outputBox=dict(argstr='--outputBox %s',
    hash_files=False,
    ),
    outputGrid=dict(argstr='--outputGrid %s',
    hash_files=False,
    ),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = BRAINSTalairach.input_spec()

    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(inputs.traits()[key], metakey), value

def test_BRAINSTalairach_outputs():
    output_map = dict(outputBox=dict(),
    outputGrid=dict(),
    )
    outputs = BRAINSTalairach.output_spec()

    for key, metadata in output_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(outputs.traits()[key], metakey), value

