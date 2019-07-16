# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..diffusion import DWIConvert


def test_DWIConvert_inputs():
    input_map = dict(
        allowLossyConversion=dict(argstr='--allowLossyConversion ', ),
        args=dict(argstr='%s', ),
        conversionMode=dict(argstr='--conversionMode %s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        fMRI=dict(argstr='--fMRI ', ),
        fslNIFTIFile=dict(
            argstr='--fslNIFTIFile %s',
            usedefault=True,
        ),
        gradientVectorFile=dict(
            argstr='--gradientVectorFile %s',
            hash_files=False,
        ),
        inputBValues=dict(
            argstr='--inputBValues %s',
            usedefault=True,
        ),
        inputBVectors=dict(
            argstr='--inputBVectors %s',
            usedefault=True,
        ),
        inputDicomDirectory=dict(
            argstr='--inputDicomDirectory %s',
            usedefault=True,
        ),
        inputVolume=dict(
            argstr='--inputVolume %s',
            usedefault=True,
        ),
        outputBValues=dict(
            argstr='--outputBValues %s',
            hash_files=False,
        ),
        outputBVectors=dict(
            argstr='--outputBVectors %s',
            hash_files=False,
        ),
        outputDirectory=dict(
            argstr='--outputDirectory %s',
            hash_files=False,
        ),
        outputVolume=dict(
            argstr='--outputVolume %s',
            hash_files=False,
        ),
        smallGradientThreshold=dict(argstr='--smallGradientThreshold %f', ),
        transposeInputBVectors=dict(argstr='--transposeInputBVectors ', ),
        useBMatrixGradientDirections=dict(
            argstr='--useBMatrixGradientDirections ', ),
        useIdentityMeaseurementFrame=dict(
            argstr='--useIdentityMeaseurementFrame ', ),
        writeProtocolGradientsFile=dict(
            argstr='--writeProtocolGradientsFile ', ),
    )
    inputs = DWIConvert.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_DWIConvert_outputs():
    output_map = dict(
        gradientVectorFile=dict(usedefault=True, ),
        outputBValues=dict(usedefault=True, ),
        outputBVectors=dict(usedefault=True, ),
        outputDirectory=dict(usedefault=True, ),
        outputVolume=dict(usedefault=True, ),
    )
    outputs = DWIConvert.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
