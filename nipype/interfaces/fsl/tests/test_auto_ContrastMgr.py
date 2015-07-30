# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from nipype.testing import assert_equal
from nipype.interfaces.fsl.model import ContrastMgr

def test_ContrastMgr_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    contrast_num=dict(argstr='-cope',
    ),
    corrections=dict(copyfile=False,
    mandatory=True,
    ),
    dof_file=dict(argstr='',
    copyfile=False,
    mandatory=True,
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    fcon_file=dict(argstr='-f %s',
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    output_type=dict(),
    param_estimates=dict(argstr='',
    copyfile=False,
    mandatory=True,
    ),
    sigmasquareds=dict(argstr='',
    copyfile=False,
    mandatory=True,
    position=-2,
    ),
    suffix=dict(argstr='-suffix %s',
    ),
    tcon_file=dict(argstr='%s',
    mandatory=True,
    position=-1,
    ),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = ContrastMgr.input_spec()

    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(inputs.traits()[key], metakey), value

def test_ContrastMgr_outputs():
    output_map = dict(copes=dict(),
    fstats=dict(),
    neffs=dict(),
    tstats=dict(),
    varcopes=dict(),
    zfstats=dict(),
    zstats=dict(),
    )
    outputs = ContrastMgr.output_spec()

    for key, metadata in output_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(outputs.traits()[key], metakey), value

