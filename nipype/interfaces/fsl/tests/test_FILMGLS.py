# -*- coding: utf-8 -*-
from nipype.interfaces.fsl.model import FILMGLS, FILMGLSInputSpec


def test_filmgls():
    input_map = dict(
        args=dict(argstr='%s', ),
        autocorr_estimate_only=dict(
            xor=[
                'autocorr_estimate_only', 'fit_armodel', 'tukey_window',
                'multitaper_product', 'use_pava', 'autocorr_noestimate'
            ],
            argstr='-ac',
        ),
        autocorr_noestimate=dict(
            xor=[
                'autocorr_estimate_only', 'fit_armodel', 'tukey_window',
                'multitaper_product', 'use_pava', 'autocorr_noestimate'
            ],
            argstr='-noest',
        ),
        brightness_threshold=dict(argstr='-epith %d', ),
        design_file=dict(argstr='%s', ),
        environ=dict(usedefault=True, ),
        fit_armodel=dict(
            xor=[
                'autocorr_estimate_only', 'fit_armodel', 'tukey_window',
                'multitaper_product', 'use_pava', 'autocorr_noestimate'
            ],
            argstr='-ar',
        ),
        full_data=dict(argstr='-v', ),
        in_file=dict(
            mandatory=True,
            argstr='%s',
        ),
        mask_size=dict(argstr='-ms %d', ),
        multitaper_product=dict(
            xor=[
                'autocorr_estimate_only', 'fit_armodel', 'tukey_window',
                'multitaper_product', 'use_pava', 'autocorr_noestimate'
            ],
            argstr='-mt %d',
        ),
        output_pwdata=dict(argstr='-output_pwdata', ),
        output_type=dict(),
        results_dir=dict(
            usedefault=True,
            argstr='-rn %s',
        ),
        smooth_autocorr=dict(argstr='-sa', ),
        threshold=dict(argstr='%f', ),
        tukey_window=dict(
            xor=[
                'autocorr_estimate_only', 'fit_armodel', 'tukey_window',
                'multitaper_product', 'use_pava', 'autocorr_noestimate'
            ],
            argstr='-tukey %d',
        ),
        use_pava=dict(argstr='-pava', ),
    )
    input_map2 = dict(
        args=dict(argstr='%s', ),
        autocorr_estimate_only=dict(
            xor=[
                'autocorr_estimate_only', 'fit_armodel', 'tukey_window',
                'multitaper_product', 'use_pava', 'autocorr_noestimate'
            ],
            argstr='--ac',
        ),
        autocorr_noestimate=dict(
            xor=[
                'autocorr_estimate_only', 'fit_armodel', 'tukey_window',
                'multitaper_product', 'use_pava', 'autocorr_noestimate'
            ],
            argstr='--noest',
        ),
        brightness_threshold=dict(argstr='--epith=%d', ),
        design_file=dict(argstr='--pd=%s', ),
        environ=dict(usedefault=True, ),
        fit_armodel=dict(
            xor=[
                'autocorr_estimate_only', 'fit_armodel', 'tukey_window',
                'multitaper_product', 'use_pava', 'autocorr_noestimate'
            ],
            argstr='--ar',
        ),
        full_data=dict(argstr='-v', ),
        in_file=dict(
            mandatory=True,
            argstr='--in=%s',
        ),
        mask_size=dict(argstr='--ms=%d', ),
        multitaper_product=dict(
            xor=[
                'autocorr_estimate_only', 'fit_armodel', 'tukey_window',
                'multitaper_product', 'use_pava', 'autocorr_noestimate'
            ],
            argstr='--mt=%d',
        ),
        output_pwdata=dict(argstr='--outputPWdata', ),
        output_type=dict(),
        results_dir=dict(
            argstr='--rn=%s',
            usedefault=True,
        ),
        smooth_autocorr=dict(argstr='--sa', ),
        threshold=dict(
            usedefault=True,
            argstr='--thr=%f',
        ),
        tukey_window=dict(
            xor=[
                'autocorr_estimate_only', 'fit_armodel', 'tukey_window',
                'multitaper_product', 'use_pava', 'autocorr_noestimate'
            ],
            argstr='--tukey=%d',
        ),
        use_pava=dict(argstr='--pava', ),
    )
    instance = FILMGLS()
    if isinstance(instance.inputs, FILMGLSInputSpec):
        for key, metadata in list(input_map.items()):
            for metakey, value in list(metadata.items()):
                assert getattr(instance.inputs.traits()[key], metakey) == value
    else:
        for key, metadata in list(input_map2.items()):
            for metakey, value in list(metadata.items()):
                assert getattr(instance.inputs.traits()[key], metakey) == value
