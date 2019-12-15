# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..maths import MaxnImage


def test_MaxnImage_inputs():
    input_map = dict(
        args=dict(argstr="%s",),
        dimension=dict(argstr="-%smaxn", position=4, usedefault=True,),
        environ=dict(nohash=True, usedefault=True,),
        in_file=dict(argstr="%s", extensions=None, mandatory=True, position=2,),
        internal_datatype=dict(argstr="-dt %s", position=1,),
        nan2zeros=dict(argstr="-nan", position=3,),
        out_file=dict(
            argstr="%s", extensions=None, genfile=True, hash_files=False, position=-2,
        ),
        output_datatype=dict(argstr="-odt %s", position=-1,),
        output_type=dict(),
    )
    inputs = MaxnImage.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_MaxnImage_outputs():
    output_map = dict(out_file=dict(extensions=None,),)
    outputs = MaxnImage.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
