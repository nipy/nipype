# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..epi import EpiReg


def test_EpiReg_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    echospacing=dict(argstr='--echospacing=%f',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    epi=dict(argstr='--epi=%s',
    mandatory=True,
    position=-4,
    ),
    epi2str_inv=dict(),
    epi2str_mat=dict(),
    fmap=dict(argstr='--fmap=%s',
    ),
    fmap2epi_mat=dict(),
    fmap2str_mat=dict(),
    fmap_epi=dict(),
    fmap_str=dict(),
    fmapmag=dict(argstr='--fmapmag=%s',
    ),
    fmapmagbrain=dict(argstr='--fmapmagbrain=%s',
    ),
    fullwarp=dict(),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    no_clean=dict(argstr='--noclean',
    usedefault=True,
    ),
    no_fmapreg=dict(argstr='--nofmapreg',
    usedefault=True,
    ),
    out_1vol=dict(),
    out_base=dict(argstr='--out=%s',
    position=-1,
    usedefault=True,
    ),
    out_file=dict(),
    output_type=dict(usedefault=True,
    ),
    pedir=dict(argstr='--pedir=%s',
    ),
    shiftmap=dict(),
    t1_brain=dict(argstr='--t1brain=%s',
    mandatory=True,
    position=-2,
    ),
    t1_head=dict(argstr='--t1=%s',
    mandatory=True,
    position=-3,
    ),
    terminal_output=dict(nohash=True,
    ),
    weight_image=dict(argstr='--weight=%s',
    ),
    wmedge=dict(),
    wmseg=dict(),
    )
    inputs = EpiReg.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_EpiReg_outputs():
    output_map = dict(epi2str_inv=dict(),
    epi2str_mat=dict(),
    fmap2epi_mat=dict(),
    fmap2str_mat=dict(),
    fmap_epi=dict(),
    fmap_str=dict(),
    fmapmag_str=dict(),
    fullwarp=dict(),
    out_1vol=dict(),
    out_file=dict(),
    shiftmap=dict(),
    wmedge=dict(),
    wmseg=dict(),
    )
    outputs = EpiReg.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
