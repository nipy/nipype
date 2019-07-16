# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..model import FitGLM


def test_FitGLM_inputs():
    input_map = dict(
        TR=dict(mandatory=True, ),
        drift_model=dict(usedefault=True, ),
        hrf_model=dict(usedefault=True, ),
        mask=dict(),
        method=dict(usedefault=True, ),
        model=dict(usedefault=True, ),
        normalize_design_matrix=dict(usedefault=True, ),
        plot_design_matrix=dict(usedefault=True, ),
        save_residuals=dict(usedefault=True, ),
        session_info=dict(mandatory=True, ),
    )
    inputs = FitGLM.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_FitGLM_outputs():
    output_map = dict(
        a=dict(usedefault=True, ),
        axis=dict(),
        beta=dict(usedefault=True, ),
        constants=dict(),
        dof=dict(),
        nvbeta=dict(),
        reg_names=dict(),
        residuals=dict(),
        s2=dict(usedefault=True, ),
    )
    outputs = FitGLM.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
