# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..preprocess import CreateWarped


def test_CreateWarped_inputs():
    input_map = dict(
        flowfield_files=dict(
            copyfile=False,
            field="crt_warped.flowfields",
            mandatory=True,
        ),
        image_files=dict(
            copyfile=False,
            field="crt_warped.images",
            mandatory=True,
        ),
        interp=dict(
            field="crt_warped.interp",
        ),
        iterations=dict(
            field="crt_warped.K",
        ),
        matlab_cmd=dict(),
        mfile=dict(
            usedefault=True,
        ),
        modulate=dict(
            field="crt_warped.jactransf",
        ),
        paths=dict(),
        use_mcr=dict(),
        use_v8struct=dict(
            min_ver="8",
            usedefault=True,
        ),
    )
    inputs = CreateWarped.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_CreateWarped_outputs():
    output_map = dict(
        warped_files=dict(),
    )
    outputs = CreateWarped.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
