# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..confounds import TCompCor


def test_TCompCor_inputs():
    input_map = dict(components_file=dict(usedefault=True,
    ),
    header=dict(),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    mask_file=dict(),
    num_components=dict(usedefault=True,
    ),
    percentile_threshold=dict(usedefault=True,
    ),
    realigned_file=dict(mandatory=True,
    ),
    regress_poly_degree=dict(usedefault=True,
    ),
    use_regress_poly=dict(usedefault=True,
    ),
    )
    inputs = TCompCor.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_TCompCor_outputs():
    output_map = dict(components_file=dict(),
    )
    outputs = TCompCor.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
