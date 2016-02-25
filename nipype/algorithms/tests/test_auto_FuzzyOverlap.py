# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ...testing import assert_equal
from ..misc import FuzzyOverlap


def test_FuzzyOverlap_inputs():
    input_map = dict(in_ref=dict(mandatory=True,
    ),
    in_tst=dict(mandatory=True,
    ),
    out_file=dict(usedefault=True,
    ),
    weighting=dict(usedefault=True,
    ),
    )
    inputs = FuzzyOverlap._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_FuzzyOverlap_outputs():
    output_map = dict(class_fdi=dict(),
    class_fji=dict(),
    dice=dict(),
    diff_file=dict(),
    jaccard=dict(),
    )
    outputs = FuzzyOverlap._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
