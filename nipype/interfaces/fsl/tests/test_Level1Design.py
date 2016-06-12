import os
from ...base import Undefined
from ..model import Level1Design

def test_level1design():
	l = Level1Design()
	runinfo = dict(cond=[{'name': 'test_condition', 'onset': [0, 10], 'duration':[10, 10]}],regress=[])
	runidx = 0
	contrasts = Undefined
	usetd = False
	do_tempfilter = False
	return Level1Design._create_ev_files(l,os.getcwd(),runinfo,runidx,usetd,contrasts,do_tempfilter,"hrf")
