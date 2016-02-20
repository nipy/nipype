# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ...testing import assert_equal
from ..misc import ModifyAffine


def test_ModifyAffine_inputs():
    input_map = dict(ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    transformation_matrix=dict(usedefault=True,
    ),
    transformed_volumes=dict(),
    volumes=dict(mandatory=True,
    ),
    )
    inputs = ModifyAffine.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_ModifyAffine_outputs():
    output_map = dict(transformed_volumes=dict(),
    )
    outputs = ModifyAffine.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
