# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..io import S3DataGrabber


def test_S3DataGrabber_inputs():
    input_map = dict(anon=dict(usedefault=True,
    ),
    bucket=dict(mandatory=True,
    ),
    bucket_path=dict(usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    local_directory=dict(),
    raise_on_empty=dict(usedefault=True,
    ),
    region=dict(usedefault=True,
    ),
    sort_filelist=dict(mandatory=True,
    ),
    template=dict(mandatory=True,
    ),
    template_args=dict(),
    )
    inputs = S3DataGrabber.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_S3DataGrabber_outputs():
    output_map = dict()
    outputs = S3DataGrabber.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
