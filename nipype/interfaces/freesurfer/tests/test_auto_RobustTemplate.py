# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..longitudinal import RobustTemplate


def test_RobustTemplate_inputs():
    input_map = dict(
        args=dict(
            argstr="%s",
        ),
        auto_detect_sensitivity=dict(
            argstr="--satit",
            mandatory=True,
            xor=["outlier_sensitivity"],
        ),
        average_metric=dict(
            argstr="--average %d",
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        fixed_timepoint=dict(
            argstr="--fixtp",
        ),
        in_files=dict(
            argstr="--mov %s",
            mandatory=True,
        ),
        in_intensity_scales=dict(
            argstr="--iscalein %s",
        ),
        initial_timepoint=dict(
            argstr="--inittp %d",
        ),
        initial_transforms=dict(
            argstr="--ixforms %s",
        ),
        intensity_scaling=dict(
            argstr="--iscale",
        ),
        no_iteration=dict(
            argstr="--noit",
        ),
        num_threads=dict(),
        out_file=dict(
            argstr="--template %s",
            extensions=None,
            mandatory=True,
            usedefault=True,
        ),
        outlier_sensitivity=dict(
            argstr="--sat %.4f",
            mandatory=True,
            xor=["auto_detect_sensitivity"],
        ),
        scaled_intensity_outputs=dict(
            argstr="--iscaleout %s",
        ),
        subjects_dir=dict(),
        subsample_threshold=dict(
            argstr="--subsample %d",
        ),
        transform_outputs=dict(
            argstr="--lta %s",
        ),
    )
    inputs = RobustTemplate.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_RobustTemplate_outputs():
    output_map = dict(
        out_file=dict(
            extensions=None,
        ),
        scaled_intensity_outputs=dict(),
        transform_outputs=dict(),
    )
    outputs = RobustTemplate.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
