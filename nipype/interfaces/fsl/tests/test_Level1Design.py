import os
from nose.tools import assert_true
from ...base import Undefined
from ..model import Level1Design

def test_level1design():
	l = Level1Design()
	runinfo = dict(cond=[{'name': 'test_condition', 'onset': [0, 10], 'duration':[10, 10]}],regress=[])
	runidx = 0
	contrasts = Undefined
	usetd = False
	do_tempfilter = False
	output_num, output_txt = Level1Design._create_ev_files(l,os.getcwd(),runinfo,runidx,usetd,contrasts,do_tempfilter,"hrf")
	yield assert_true, "set fmri(convolve1) 3" in output_txt
	output_num, output_txt = Level1Design._create_ev_files(l,os.getcwd(),runinfo,runidx,usetd,contrasts,do_tempfilter,"dgamma")
	yield assert_true, "set fmri(convolve1) 3" in output_txt
	output_num, output_txt = Level1Design._create_ev_files(l,os.getcwd(),runinfo,runidx,usetd,contrasts,do_tempfilter,"gamma")
	yield assert_true, "set fmri(convolve1) 2" in output_txt
	output_num, output_txt = Level1Design._create_ev_files(l,os.getcwd(),runinfo,runidx,usetd,contrasts,do_tempfilter,"none")
	yield assert_true, "set fmri(convolve1) 0" in output_txt
