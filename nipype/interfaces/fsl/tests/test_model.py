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
    foo.inputs.regressors = dict(reg1=[1,1,1],reg2=[0.2,0.4,0.5],reg3=[1,-1,2])
    con1 = ['con1','T',['reg1','reg2'],[0.5,0.5]]
    con2 = ['con2','T',['reg3'],[1]]
    foo.inputs.contrasts = [con1,con2,['con3','F',[con1,con2]]]
    res = foo.run()
    yield assert_equal, res.outputs.design_mat, os.path.join(os.getcwd(),'design.mat')
    yield assert_equal, res.outputs.design_con, os.path.join(os.getcwd(),'design.con')
    yield assert_equal, res.outputs.design_fts, os.path.join(os.getcwd(),'design.fts')
    yield assert_equal, res.outputs.design_grp, os.path.join(os.getcwd(),'design.grp')
