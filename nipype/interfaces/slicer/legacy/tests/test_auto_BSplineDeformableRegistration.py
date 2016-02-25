# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from .....testing import assert_equal
from ..registration import BSplineDeformableRegistration


def test_BSplineDeformableRegistration_inputs():
    input_map = dict(FixedImageFileName=dict(argstr='%s',
    position=-2,
    ),
    MovingImageFileName=dict(argstr='%s',
    position=-1,
    ),
    args=dict(argstr='%s',
    ),
    constrain=dict(argstr='--constrain ',
    ),
    default=dict(argstr='--default %d',
    ),
    gridSize=dict(argstr='--gridSize %d',
    ),
    histogrambins=dict(argstr='--histogrambins %d',
    ),
    initialtransform=dict(argstr='--initialtransform %s',
    ),
    iterations=dict(argstr='--iterations %d',
    ),
    maximumDeformation=dict(argstr='--maximumDeformation %f',
    ),
    outputtransform=dict(argstr='--outputtransform %s',
    hash_files=False,
    ),
    outputwarp=dict(argstr='--outputwarp %s',
    hash_files=False,
    ),
    resampledmovingfilename=dict(argstr='--resampledmovingfilename %s',
    hash_files=False,
    ),
    spatialsamples=dict(argstr='--spatialsamples %d',
    ),
    )
    inputs = BSplineDeformableRegistration._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_BSplineDeformableRegistration_outputs():
    output_map = dict(outputtransform=dict(),
    outputwarp=dict(),
    resampledmovingfilename=dict(),
    )
    outputs = BSplineDeformableRegistration._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
