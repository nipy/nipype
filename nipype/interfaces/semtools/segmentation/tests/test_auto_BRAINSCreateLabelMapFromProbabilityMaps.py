from __future__ import unicode_literals
# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from nipype.testing import assert_equal
from nipype.interfaces.semtools.segmentation.specialized import BRAINSCreateLabelMapFromProbabilityMaps

def test_BRAINSCreateLabelMapFromProbabilityMaps_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    cleanLabelVolume=dict(argstr='--cleanLabelVolume %s',
    hash_files=False,
    ),
    dirtyLabelVolume=dict(argstr='--dirtyLabelVolume %s',
    hash_files=False,
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    foregroundPriors=dict(argstr='--foregroundPriors %s',
    sep=',',
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    inclusionThreshold=dict(argstr='--inclusionThreshold %f',
    ),
    inputProbabilityVolume=dict(argstr='--inputProbabilityVolume %s...',
    ),
    nonAirRegionMask=dict(argstr='--nonAirRegionMask %s',
    ),
    priorLabelCodes=dict(argstr='--priorLabelCodes %s',
    sep=',',
    ),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = BRAINSCreateLabelMapFromProbabilityMaps.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value

def test_BRAINSCreateLabelMapFromProbabilityMaps_outputs():
    output_map = dict(cleanLabelVolume=dict(),
    dirtyLabelVolume=dict(),
    )
    outputs = BRAINSCreateLabelMapFromProbabilityMaps.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value

