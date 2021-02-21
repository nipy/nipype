# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..gtract import gtractCostFastMarching


def test_gtractCostFastMarching_inputs():
    input_map = dict(
        anisotropyWeight=dict(
            argstr="--anisotropyWeight %f",
        ),
        args=dict(
            argstr="%s",
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        inputAnisotropyVolume=dict(
            argstr="--inputAnisotropyVolume %s",
            extensions=None,
        ),
        inputStartingSeedsLabelMapVolume=dict(
            argstr="--inputStartingSeedsLabelMapVolume %s",
            extensions=None,
        ),
        inputTensorVolume=dict(
            argstr="--inputTensorVolume %s",
            extensions=None,
        ),
        numberOfThreads=dict(
            argstr="--numberOfThreads %d",
        ),
        outputCostVolume=dict(
            argstr="--outputCostVolume %s",
            hash_files=False,
        ),
        outputSpeedVolume=dict(
            argstr="--outputSpeedVolume %s",
            hash_files=False,
        ),
        seedThreshold=dict(
            argstr="--seedThreshold %f",
        ),
        startingSeedsLabel=dict(
            argstr="--startingSeedsLabel %d",
        ),
        stoppingValue=dict(
            argstr="--stoppingValue %f",
        ),
    )
    inputs = gtractCostFastMarching.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_gtractCostFastMarching_outputs():
    output_map = dict(
        outputCostVolume=dict(
            extensions=None,
        ),
        outputSpeedVolume=dict(
            extensions=None,
        ),
    )
    outputs = gtractCostFastMarching.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
