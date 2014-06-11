# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from nipype.testing import assert_equal
from nipype.algorithms.metrics import ErrorMap

def test_ErrorMap_inputs():
    input_map = dict(ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    in_ref=dict(mandatory=True,
    ),
    in_tst=dict(mandatory=True,
    ),
    mask=dict(),
    method=dict(usedefault=True,
    ),
    out_map=dict(),
    )
    inputs = ErrorMap.input_spec()

    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(inputs.traits()[key], metakey), value

def test_ErrorMap_outputs():
    output_map = dict(out_map=dict(),
    )
    outputs = ErrorMap.output_spec()

    for key, metadata in output_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(outputs.traits()[key], metakey), value

