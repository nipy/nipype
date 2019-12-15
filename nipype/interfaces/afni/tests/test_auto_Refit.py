# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..utils import Refit


def test_Refit_inputs():
    input_map = dict(
        args=dict(argstr="%s",),
        atrcopy=dict(argstr="-atrcopy %s %s",),
        atrfloat=dict(argstr="-atrfloat %s %s",),
        atrint=dict(argstr="-atrint %s %s",),
        atrstring=dict(argstr="-atrstring %s %s",),
        deoblique=dict(argstr="-deoblique",),
        duporigin_file=dict(argstr="-duporigin %s", extensions=None,),
        environ=dict(nohash=True, usedefault=True,),
        in_file=dict(
            argstr="%s", copyfile=True, extensions=None, mandatory=True, position=-1,
        ),
        nosaveatr=dict(argstr="-nosaveatr",),
        saveatr=dict(argstr="-saveatr",),
        space=dict(argstr="-space %s",),
        xdel=dict(argstr="-xdel %f",),
        xorigin=dict(argstr="-xorigin %s",),
        xyzscale=dict(argstr="-xyzscale %f",),
        ydel=dict(argstr="-ydel %f",),
        yorigin=dict(argstr="-yorigin %s",),
        zdel=dict(argstr="-zdel %f",),
        zorigin=dict(argstr="-zorigin %s",),
    )
    inputs = Refit.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_Refit_outputs():
    output_map = dict(out_file=dict(extensions=None,),)
    outputs = Refit.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
