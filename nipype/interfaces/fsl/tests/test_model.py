# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import tempfile
import shutil

from nipype.testing import (assert_equal, assert_true,
                            skipif)
import nipype.interfaces.fsl.model as fsl
from nipype.interfaces.fsl import Info
from nipype.interfaces.fsl import no_fsl

tmp_infile = None
tmp_dir = None
cwd = None

@skipif(no_fsl)
def setup_infile():
    global tmp_infile, tmp_dir, cwd
    cwd = os.getcwd()
    ext = Info.output_type_to_ext(Info.output_type())
    tmp_dir = tempfile.mkdtemp()
    tmp_infile = os.path.join(tmp_dir, 'foo' + ext)
    file(tmp_infile, 'w')
    os.chdir(tmp_dir)
    return tmp_infile, tmp_dir

def teardown_infile(tmp_dir):
    os.chdir(cwd)
    shutil.rmtree(tmp_dir)

@skipif(no_fsl)
def test_MultipleRegressDesign():
    _, tp_dir = setup_infile()
    foo = fsl.MultipleRegressDesign()
    foo.inputs.regressors = dict(voice_stenght=[1,1,1],age=[0.2,0.4,0.5],BMI=[1,-1,2])
    con1 = ['voice_and_age','T',['age','voice_stenght'],[0.5,0.5]]
    con2 = ['just_BMI','T',['BMI'],[1]]
    foo.inputs.contrasts = [con1,con2,['con3','F',[con1,con2]]]
    res = foo.run()
    yield assert_equal, res.outputs.design_mat, os.path.join(os.getcwd(),'design.mat')
    yield assert_equal, res.outputs.design_con, os.path.join(os.getcwd(),'design.con')
    yield assert_equal, res.outputs.design_fts, os.path.join(os.getcwd(),'design.fts')
    yield assert_equal, res.outputs.design_grp, os.path.join(os.getcwd(),'design.grp')

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
    yield assert_equal, open(os.path.join(os.getcwd(),'design.con'), 'r').read(), design_con_expected_content
    yield assert_equal, open(os.path.join(os.getcwd(),'design.mat'), 'r').read(), design_mat_expected_content
    yield assert_equal, open(os.path.join(os.getcwd(),'design.fts'), 'r').read(), design_fts_expected_content
    yield assert_equal, open(os.path.join(os.getcwd(),'design.grp'), 'r').read(), design_grp_expected_content

    teardown_infile(tp_dir)
