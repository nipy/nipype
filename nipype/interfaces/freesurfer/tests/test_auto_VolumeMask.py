# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..utils import VolumeMask


def test_VolumeMask_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    aseg=dict(xor=['in_aseg'],
    ),
    copy_inputs=dict(),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    in_aseg=dict(argstr='--aseg_name %s',
    xor=['aseg'],
    ),
    left_ribbonlabel=dict(argstr='--label_left_ribbon %d',
    mandatory=True,
    ),
    left_whitelabel=dict(argstr='--label_left_white %d',
    mandatory=True,
    ),
    lh_pial=dict(mandatory=True,
    ),
    lh_white=dict(mandatory=True,
    ),
    resource_monitor=dict(nohash=True,
    usedefault=True,
    ),
    rh_pial=dict(mandatory=True,
    ),
    rh_white=dict(mandatory=True,
    ),
    right_ribbonlabel=dict(argstr='--label_right_ribbon %d',
    mandatory=True,
    ),
    right_whitelabel=dict(argstr='--label_right_white %d',
    mandatory=True,
    ),
    save_ribbon=dict(argstr='--save_ribbon',
    ),
    subject_id=dict(argstr='%s',
    mandatory=True,
    position=-1,
    usedefault=True,
    ),
    subjects_dir=dict(),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = VolumeMask.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_VolumeMask_outputs():
    output_map = dict(lh_ribbon=dict(),
    out_ribbon=dict(),
    rh_ribbon=dict(),
    )
    outputs = VolumeMask.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
