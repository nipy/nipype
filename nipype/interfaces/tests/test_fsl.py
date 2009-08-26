import nipype.interfaces.fsl as fsl
from nose.tools import assert_true, assert_false, assert_raises, assert_equal, assert_not_equal


# test Bet
def test_bet():
    better = fsl.Bet()
    better.inputs.frac = 0.5
    better.inputs.infile = 'infile'
    yield assert_equal, better.cmd, 'bet'

    yield assert_equal, better.cmdline, 'bet infile infile_bet -f 0.50'
    betted = better.run(infile='infile2', outfile='outfile')
    yield assert_not_equal, betted.runtime.returncode, 0
    yield assert_equal, betted.interface.inputs.infile, 'infile2'
    yield assert_equal, betted.interface.inputs.outfile, 'outfile'
    yield assert_equal, betted.runtime.cmdline, 'bet infile2 outfile -f 0.50'
    
        
# test fast
def test_fast():
    faster = fsl.Fast()
    faster.inputs.verbose = True
    fasted = faster.run(infiles='infile')
    fasted2 = faster.run(infiles=['infile', 'otherfile'])
    
    yield assert_equal, faster.cmd, 'fast'
    yield assert_equal, faster.inputs.verbose, True
    yield assert_equal, faster.inputs.manualseg , None
    yield assert_not_equal, faster, fasted
    yield assert_equal, fasted.runtime.cmdline, 'fast --verbose infile'
    yield assert_equal, fasted2.runtime.cmdline, 'fast --verbose infile otherfile'
    

#test flirt
def test_flirt():
    flirter = fsl.Flirt()
    flirter.inputs.bins = 256
    flirter.inputs.cost = 'mutualinfo'
    flirted = flirter.run('infile','reffile','outfile','outmat.mat')
    flirt_est = flirter.run('infile','reffile',outfile=None,outmatrix='outmat.mat')
    flirt_apply = flirter.applyxfm('infile','reffile','inmatrix.mat','outimgfile')
    
    yield assert_not_equal, flirter, flirted
    yield assert_not_equal, flirted, flirt_est
    yield assert_not_equal, flirted, flirt_apply

    yield assert_equal, flirter.cmd, 'flirt'
    yield assert_equal, flirter.inputs.bins, flirted.inputs.bins
    yield assert_equal, flirter.inputs.cost, flirt_est.inputs.cost
    yield assert_equal, flirter.inputs.cost, flirt_apply.inputs.cost
    yield assert_not_equal, flirter.cmdline, flirt_apply.cmdline
    yield assert_equal, flirt_apply.cmdline,'flirt -cost mutualinfo -bins 256 -in infile -ref reffile -applyxfm -init inmatrix.mat -out outimgfile'
    
   
    
