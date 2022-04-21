# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..petsurfer import GTMSeg


def test_GTMSeg_inputs():
    input_map = dict(
        args=dict(
            argstr="%s",
        ),
        colortable=dict(
            argstr="--ctab %s",
            extensions=None,
        ),
        ctx_annot=dict(
            argstr="--ctx-annot %s %i %i",
        ),
        dmax=dict(
            argstr="--dmax %f",
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        head=dict(
            argstr="--head %s",
        ),
        keep_cc=dict(
            argstr="--keep-cc",
        ),
        keep_hypo=dict(
            argstr="--keep-hypo",
        ),
        no_pons=dict(
            argstr="--no-pons",
        ),
        no_seg_stats=dict(
            argstr="--no-seg-stats",
        ),
        no_vermis=dict(
            argstr="--no-vermis",
        ),
        out_file=dict(
            argstr="--o %s",
            extensions=None,
            usedefault=True,
        ),
        output_upsampling_factor=dict(
            argstr="--output-usf %i",
        ),
        subject_id=dict(
            argstr="--s %s",
            mandatory=True,
        ),
        subjects_dir=dict(),
        subseg_cblum_wm=dict(
            argstr="--subseg-cblum-wm",
        ),
        subsegwm=dict(
            argstr="--subsegwm",
        ),
        upsampling_factor=dict(
            argstr="--usf %i",
        ),
        wm_annot=dict(
            argstr="--wm-annot %s %i %i",
        ),
        xcerseg=dict(
            argstr="--xcerseg",
        ),
    )
    inputs = GTMSeg.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_GTMSeg_outputs():
    output_map = dict(
        out_file=dict(
            extensions=None,
        ),
    )
    outputs = GTMSeg.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
