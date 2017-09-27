# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..segmentation import LaplacianThickness


def test_LaplacianThickness_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    dT=dict(argstr='dT=%d',
    position=6,
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    input_gm=dict(argstr='%s',
    copyfile=True,
    mandatory=True,
    position=2,
    ),
    input_wm=dict(argstr='%s',
    copyfile=True,
    mandatory=True,
    position=1,
    ),
    num_threads=dict(nohash=True,
    usedefault=True,
    ),
    opt_tolerance=dict(argstr='optional-laplacian-tolerance=%d',
    position=8,
    ),
    output_image=dict(argstr='%s',
    genfile=True,
    hash_files=False,
    position=3,
    ),
    prior_thickness=dict(argstr='priorthickval=%d',
    position=5,
    ),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    smooth_param=dict(argstr='smoothparam=%d',
    position=4,
    ),
    sulcus_prior=dict(argstr='use-sulcus-prior',
    position=7,
    ),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = LaplacianThickness.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_LaplacianThickness_outputs():
    output_map = dict(output_image=dict(),
    )
    outputs = LaplacianThickness.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
