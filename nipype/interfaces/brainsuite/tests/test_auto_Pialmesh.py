# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..brainsuite import Pialmesh


def test_Pialmesh_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        exportPrefix=dict(argstr='--prefix %s', ),
        inputMaskFile=dict(
            argstr='-m %s',
            extensions=None,
            mandatory=True,
        ),
        inputSurfaceFile=dict(
            argstr='-i %s',
            extensions=None,
            mandatory=True,
        ),
        inputTissueFractionFile=dict(
            argstr='-f %s',
            extensions=None,
            mandatory=True,
        ),
        laplacianSmoothing=dict(
            argstr='--smooth %f',
            usedefault=True,
        ),
        maxThickness=dict(
            argstr='--max %f',
            usedefault=True,
        ),
        normalSmoother=dict(
            argstr='--nc %f',
            usedefault=True,
        ),
        numIterations=dict(
            argstr='-n %d',
            usedefault=True,
        ),
        outputInterval=dict(
            argstr='--interval %d',
            usedefault=True,
        ),
        outputSurfaceFile=dict(
            argstr='-o %s',
            extensions=None,
            genfile=True,
        ),
        recomputeNormals=dict(argstr='--norm', ),
        searchRadius=dict(
            argstr='-r %f',
            usedefault=True,
        ),
        stepSize=dict(
            argstr='-s %f',
            usedefault=True,
        ),
        tangentSmoother=dict(argstr='--tc %f', ),
        timer=dict(argstr='--timer', ),
        tissueThreshold=dict(
            argstr='-t %f',
            usedefault=True,
        ),
        verbosity=dict(argstr='-v %d', ),
    )
    inputs = Pialmesh.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_Pialmesh_outputs():
    output_map = dict(outputSurfaceFile=dict(extensions=None, ), )
    outputs = Pialmesh.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
