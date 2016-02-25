# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ....testing import assert_equal
from ..nbs import NetworkBasedStatistic


def test_NetworkBasedStatistic_inputs():
    input_map = dict(edge_key=dict(usedefault=True,
    ),
    in_group1=dict(mandatory=True,
    ),
    in_group2=dict(mandatory=True,
    ),
    node_position_network=dict(),
    number_of_permutations=dict(usedefault=True,
    ),
    out_nbs_network=dict(),
    out_nbs_pval_network=dict(),
    t_tail=dict(usedefault=True,
    ),
    threshold=dict(usedefault=True,
    ),
    )
    inputs = NetworkBasedStatistic._input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value


def test_NetworkBasedStatistic_outputs():
    output_map = dict(nbs_network=dict(),
    nbs_pval_network=dict(),
    network_files=dict(),
    )
    outputs = NetworkBasedStatistic._output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value
