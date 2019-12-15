# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..maths import TemporalFilter


def test_TemporalFilter_inputs():
    input_map = dict(
        args=dict(argstr="%s",),
        environ=dict(nohash=True, usedefault=True,),
        highpass_sigma=dict(argstr="-bptf %.6f", position=4, usedefault=True,),
        in_file=dict(argstr="%s", extensions=None, mandatory=True, position=2,),
        internal_datatype=dict(argstr="-dt %s", position=1,),
        lowpass_sigma=dict(argstr="%.6f", position=5, usedefault=True,),
        nan2zeros=dict(argstr="-nan", position=3,),
        out_file=dict(
            argstr="%s", extensions=None, genfile=True, hash_files=False, position=-2,
        ),
        output_datatype=dict(argstr="-odt %s", position=-1,),
        output_type=dict(),
    )
    inputs = TemporalFilter.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_TemporalFilter_outputs():
    output_map = dict(out_file=dict(extensions=None,),)
    outputs = TemporalFilter.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
