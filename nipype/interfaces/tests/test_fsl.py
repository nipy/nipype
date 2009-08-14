import nipype.interfaces.fsl as fsl
from nose.tools import assert_true, assert_false, assert_raises, assert_equal, assert_not_equal


# test Bet
def test_bet():
    better = fsl.Bet()
    better.inputs.frac = 0.5
    # better2 = better.update()
    # better3 = better.update(frac=0.1)
    # 
    # yield assert_not_equal, better, better2
    # yield assert_not_equal, better, better3
    # yield assert_equal, better.inputs.frac, 0.5
    # yield assert_equal, better3.inputs.frac, 0.1
    
    yield assert_equal, better.cmd, 'bet'

    yield assert_equal, better.cmdline, 'bet -f 0.50'
    betted = better.run(infile='infile', outfile='outfile')
    yield assert_not_equal, betted.retcode, 0
    yield assert_equal, betted.inputs.infile, 'infile'
    yield assert_equal, betted.inputs.outfile, 'outfile'
    yield assert_equal, betted.runtime.cmdline, 'bet infile outfile -f 0.50'
    
        
# test fast
def test_fast():
    faster = fsl.Fast()
    faster.inputs.verbose = True
    faster2 = faster.update(iters_afterbias=6)
    fasted = faster.run('infile')
    fasted2 = faster.run(['infile', 'otherfile'])
    
    yield assert_equal, faster.cmd, 'fast'
    yield assert_equal, faster.inputs.verbose, True
    yield assert_equal, faster.inputs.manualseg , None
    yield assert_equal, faster2.inputs.verbose, True
    yield assert_equal, faster2.inputs.iters_afterbias, 6
    yield assert_not_equal, faster, faster2
    yield assert_not_equal, faster, fasted
    yield assert_equal, fasted.cmdline, 'fast infile --verbose'
    yield assert_equal, faster.cmdline, ''
    yield assert_not_equal, fasted.err, ''
    

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
    
   
    
