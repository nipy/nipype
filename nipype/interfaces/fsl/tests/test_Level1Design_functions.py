# -*- coding: utf-8 -*-
import os
from ...base import Undefined
from ..model import Level1Design


def test_level1design(tmpdir):
    old = tmpdir.chdir()
    l = Level1Design()
    runinfo = dict(
        cond=[{
            'name': 'test_condition',
            'onset': [0, 10],
            'duration': [10, 10]
        }],
        regress=[])
    runidx = 0
    contrasts = Undefined
    do_tempfilter = False
    orthogonalization = {}
    basic_ev_parameters = {'temporalderiv': False}
    convolution_variants = [('custom', 7, {
        'temporalderiv': False,
        'bfcustompath': '/some/path'
    }), ('hrf', 3, basic_ev_parameters), ('dgamma', 3, basic_ev_parameters),
                            ('gamma', 2, basic_ev_parameters),
                            ('none', 0, basic_ev_parameters)]
    for key, val, ev_parameters in convolution_variants:
        output_num, output_txt = Level1Design._create_ev_files(
            l, os.getcwd(), runinfo, runidx, ev_parameters, orthogonalization,
            contrasts, do_tempfilter, key)
        assert "set fmri(convolve1) {0}".format(val) in output_txt
