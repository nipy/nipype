# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..base import NitimeBaseInterface


def test_NitimeBaseInterface_inputs():
    input_map = dict()
    inputs = NitimeBaseInterface.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
