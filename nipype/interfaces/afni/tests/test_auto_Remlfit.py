# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..model import Remlfit


def test_Remlfit_inputs():
    input_map = dict(
        STATmask=dict(
            argstr="-STATmask %s",
            extensions=None,
        ),
        addbase=dict(
            argstr="-addbase %s",
            copyfile=False,
            sep=" ",
        ),
        args=dict(
            argstr="%s",
        ),
        automask=dict(
            argstr="-automask",
            usedefault=True,
        ),
        dsort=dict(
            argstr="-dsort %s",
            copyfile=False,
            extensions=None,
        ),
        dsort_nods=dict(
            argstr="-dsort_nods",
            requires=["dsort"],
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        errts_file=dict(
            argstr="-Rerrts %s",
            extensions=None,
        ),
        fitts_file=dict(
            argstr="-Rfitts %s",
            extensions=None,
        ),
        fout=dict(
            argstr="-fout",
        ),
        glt_file=dict(
            argstr="-Rglt %s",
            extensions=None,
        ),
        gltsym=dict(
            argstr='-gltsym "%s" %s...',
        ),
        goforit=dict(
            argstr="-GOFORIT",
        ),
        in_files=dict(
            argstr='-input "%s"',
            copyfile=False,
            mandatory=True,
            sep=" ",
        ),
        mask=dict(
            argstr="-mask %s",
            extensions=None,
        ),
        matim=dict(
            argstr="-matim %s",
            extensions=None,
            xor=["matrix"],
        ),
        matrix=dict(
            argstr="-matrix %s",
            extensions=None,
            mandatory=True,
        ),
        nobout=dict(
            argstr="-nobout",
        ),
        nodmbase=dict(
            argstr="-nodmbase",
            requires=["addbase", "dsort"],
        ),
        nofdr=dict(
            argstr="-noFDR",
        ),
        num_threads=dict(
            nohash=True,
            usedefault=True,
        ),
        obeta=dict(
            argstr="-Obeta %s",
            extensions=None,
        ),
        obuck=dict(
            argstr="-Obuck %s",
            extensions=None,
        ),
        oerrts=dict(
            argstr="-Oerrts %s",
            extensions=None,
        ),
        ofitts=dict(
            argstr="-Ofitts %s",
            extensions=None,
        ),
        oglt=dict(
            argstr="-Oglt %s",
            extensions=None,
        ),
        out_file=dict(
            argstr="-Rbuck %s",
            extensions=None,
        ),
        outputtype=dict(),
        ovar=dict(
            argstr="-Ovar %s",
            extensions=None,
        ),
        polort=dict(
            argstr="-polort %d",
            xor=["matrix"],
        ),
        quiet=dict(
            argstr="-quiet",
        ),
        rbeta_file=dict(
            argstr="-Rbeta %s",
            extensions=None,
        ),
        rout=dict(
            argstr="-rout",
        ),
        slibase=dict(
            argstr="-slibase %s",
        ),
        slibase_sm=dict(
            argstr="-slibase_sm %s",
        ),
        tout=dict(
            argstr="-tout",
        ),
        usetemp=dict(
            argstr="-usetemp",
        ),
        var_file=dict(
            argstr="-Rvar %s",
            extensions=None,
        ),
        verb=dict(
            argstr="-verb",
        ),
        wherr_file=dict(
            argstr="-Rwherr %s",
            extensions=None,
        ),
    )
    inputs = Remlfit.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_Remlfit_outputs():
    output_map = dict(
        errts_file=dict(
            extensions=None,
        ),
        fitts_file=dict(
            extensions=None,
        ),
        glt_file=dict(
            extensions=None,
        ),
        obeta=dict(
            extensions=None,
        ),
        obuck=dict(
            extensions=None,
        ),
        oerrts=dict(
            extensions=None,
        ),
        ofitts=dict(
            extensions=None,
        ),
        oglt=dict(
            extensions=None,
        ),
        out_file=dict(
            extensions=None,
        ),
        ovar=dict(
            extensions=None,
        ),
        rbeta_file=dict(
            extensions=None,
        ),
        var_file=dict(
            extensions=None,
        ),
        wherr_file=dict(
            extensions=None,
        ),
    )
    outputs = Remlfit.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
