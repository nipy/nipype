# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..base import DipyBaseInterface


def test_DipyBaseInterface_inputs():
    input_map = dict()
    inputs = DipyBaseInterface._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_DipyBaseInterface_outputs():
    output_map = dict()
    outputs = DipyBaseInterface._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
