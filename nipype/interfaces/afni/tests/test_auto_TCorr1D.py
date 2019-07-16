# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..preprocess import TCorr1D


def test_TCorr1D_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        ktaub=dict(
            argstr=' -ktaub',
            position=1,
            xor=['pearson', 'spearman', 'quadrant'],
        ),
        num_threads=dict(
            nohash=True,
            usedefault=True,
        ),
        out_file=dict(
            argstr='-prefix %s',
            keep_extension=True,
            name_source='xset',
            name_template='%s_correlation.nii.gz',
            usedefault=True,
        ),
        outputtype=dict(),
        pearson=dict(
            argstr=' -pearson',
            position=1,
            xor=['spearman', 'quadrant', 'ktaub'],
        ),
        quadrant=dict(
            argstr=' -quadrant',
            position=1,
            xor=['pearson', 'spearman', 'ktaub'],
        ),
        spearman=dict(
            argstr=' -spearman',
            position=1,
            xor=['pearson', 'quadrant', 'ktaub'],
        ),
        xset=dict(
            argstr=' %s',
            copyfile=False,
            mandatory=True,
            position=-2,
            usedefault=True,
        ),
        y_1d=dict(
            argstr=' %s',
            mandatory=True,
            position=-1,
            usedefault=True,
        ),
    )
    inputs = TCorr1D.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_TCorr1D_outputs():
    output_map = dict(out_file=dict(usedefault=True, ), )
    outputs = TCorr1D.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
