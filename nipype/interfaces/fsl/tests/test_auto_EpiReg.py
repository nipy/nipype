# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..epi import EpiReg


def test_EpiReg_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        echospacing=dict(argstr='--echospacing=%f', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        epi=dict(
            argstr='--epi=%s',
            mandatory=True,
            position=-4,
            usedefault=True,
        ),
        fmap=dict(
            argstr='--fmap=%s',
            usedefault=True,
        ),
        fmapmag=dict(
            argstr='--fmapmag=%s',
            usedefault=True,
        ),
        fmapmagbrain=dict(
            argstr='--fmapmagbrain=%s',
            usedefault=True,
        ),
        no_clean=dict(
            argstr='--noclean',
            usedefault=True,
        ),
        no_fmapreg=dict(argstr='--nofmapreg', ),
        out_base=dict(
            argstr='--out=%s',
            position=-1,
            usedefault=True,
        ),
        output_type=dict(),
        pedir=dict(argstr='--pedir=%s', ),
        t1_brain=dict(
            argstr='--t1brain=%s',
            mandatory=True,
            position=-2,
            usedefault=True,
        ),
        t1_head=dict(
            argstr='--t1=%s',
            mandatory=True,
            position=-3,
            usedefault=True,
        ),
        weight_image=dict(
            argstr='--weight=%s',
            usedefault=True,
        ),
        wmseg=dict(
            argstr='--wmseg=%s',
            usedefault=True,
        ),
    )
    inputs = EpiReg.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_EpiReg_outputs():
    output_map = dict(
        epi2str_inv=dict(usedefault=True, ),
        epi2str_mat=dict(usedefault=True, ),
        fmap2epi_mat=dict(usedefault=True, ),
        fmap2str_mat=dict(usedefault=True, ),
        fmap_epi=dict(usedefault=True, ),
        fmap_str=dict(usedefault=True, ),
        fmapmag_str=dict(usedefault=True, ),
        fullwarp=dict(usedefault=True, ),
        out_1vol=dict(usedefault=True, ),
        out_file=dict(usedefault=True, ),
        seg=dict(usedefault=True, ),
        shiftmap=dict(usedefault=True, ),
        wmedge=dict(usedefault=True, ),
        wmseg=dict(usedefault=True, ),
    )
    outputs = EpiReg.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
