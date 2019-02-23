# -*- coding: utf-8 -*-
from __future__ import unicode_literals
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from builtins import open

import os

import pytest
import nipype.interfaces.fsl.model as fsl
from nipype.interfaces.fsl import no_fsl


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_MultipleRegressDesign(tmpdir):
    tmpdir.chdir()
    foo = fsl.MultipleRegressDesign()
    foo.inputs.regressors = dict(
        voice_stenght=[1, 1, 1], age=[0.2, 0.4, 0.5], BMI=[1, -1, 2])
    con1 = ['voice_and_age', 'T', ['age', 'voice_stenght'], [0.5, 0.5]]
    con2 = ['just_BMI', 'T', ['BMI'], [1]]
    foo.inputs.contrasts = [con1, con2, ['con3', 'F', [con1, con2]]]
    res = foo.run()

    for ii in ["mat", "con", "fts", "grp"]:
        assert getattr(res.outputs,
                       "design_" + ii) == tmpdir.join('design.' + ii).strpath

    design_mat_expected_content = """/NumWaves       3
/NumPoints      3
/PPheights      3.000000e+00 5.000000e-01 1.000000e+00

/Matrix
1.000000e+00 2.000000e-01 1.000000e+00
-1.000000e+00 4.000000e-01 1.000000e+00
2.000000e+00 5.000000e-01 1.000000e+00
"""

    design_con_expected_content = """/ContrastName1   voice_and_age
/ContrastName2   just_BMI
/NumWaves       3
/NumContrasts   2
/PPheights          1.000000e+00 1.000000e+00
/RequiredEffect     100.000 100.000

/Matrix
0.000000e+00 5.000000e-01 5.000000e-01
1.000000e+00 0.000000e+00 0.000000e+00
"""

    design_fts_expected_content = """/NumWaves       2
/NumContrasts   1

/Matrix
1 1
"""

    design_grp_expected_content = """/NumWaves       1
/NumPoints      3

/Matrix
1
1
1
"""
    for ii in ["mat", "con", "fts", "grp"]:
        assert tmpdir.join('design.' + ii).read() == eval(
            "design_" + ii + "_expected_content")
