# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from ...base import BoutiqueInterface
from ....testing import example_data


EXAMPLE_SPECS = [
    dict(
        spec=example_data('boutiques_fslbet.json'),
        inputs=[
            'additional_surfaces_flag', 'additional_surfaces_t2',
            'approx_skull_flag', 'binary_mask_flag', 'center_of_gravity',
            'debug_flag', 'fractional_intensity', 'head_radius', 'in_file',
            'no_seg_output_flag', 'out_file', 'overlay_flag',
            'reduce_bias_flag', 'residual_optic_cleanup_flag',
            'robust_iters_flag', 'slice_padding_flag', 'thresholding_flag',
            'verbose_flag', 'vg_fractional_intensity', 'vtk_mesh',
            'whole_set_mask_flag'
        ],
        outputs=[
            'approx_skull_img_file', 'binary_skull_file', 'inskull_mask_file',
            'inskull_mesh_file', 'inskull_off_file', 'output_file',
            'outskin_mask_file', 'outskin_mesh_file', 'outskin_off_file',
            'outskull_mask_file', 'outskull_mesh_file', 'outskull_off_file',
            'overlay_file', 'skull_mask_file', 'vtk_mesh_file'
        ]
    )
]


def test_BoutiqueInterface():
    for example in EXAMPLE_SPECS:
        interface = BoutiqueInterface(example['spec'])

        # check interface input/output spec generation
        inputs = list(interface.input_spec().get())
        outputs = list(interface.output_spec().get())
        assert all([f in inputs for f in example['inputs']])
        assert all([f in outputs for f in example['outputs']])

        # confirm help works
        assert isinstance(interface.help(True), str)
