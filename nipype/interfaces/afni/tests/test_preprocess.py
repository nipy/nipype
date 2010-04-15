from nipype.testing import *

from nipype.interfaces import afni
from nipype.interfaces.base import InterfaceResult

def test_To3d():
    cmd = afni.To3d()
    yield assert_equal, cmd.cmdline, 'to3d'
    # datatype
    cmd = afni.To3d(datatype='anat')
    yield assert_equal, cmd.cmdline, 'to3d -anat'
    cmd = afni.To3d(datatype='epan')
    yield assert_equal, cmd.cmdline, 'to3d -epan'
    # datum
    cmd = afni.To3d()
    cmd.inputs.datum = 'float'
    yield assert_equal, cmd.cmdline, 'to3d -datum float'
    # session
    cmd = afni.To3d()
    cmd.inputs.session = '/home/bobama'
    yield assert_equal, cmd.cmdline, 'to3d -session /home/bobama'
    # prefix
    cmd = afni.To3d(prefix='foo.nii.gz')
    yield assert_equal, cmd.cmdline, 'to3d -prefix foo.nii.gz'
    # infiles
    cmd = afni.To3d(infiles='/data/*.dcm')
    yield assert_equal, cmd.cmdline, 'to3d /data/*.dcm'
    # infiles list
    cmd = afni.To3d()
    infiles = ['data/foo.dcm', 'data/bar.dcm']
    cmd.inputs.infiles = infiles
    yield assert_equal, cmd.cmdline, 'to3d data/foo.dcm data/bar.dcm'
    cmd = afni.To3d()
    res = cmd.run(infiles=infiles)
    yield assert_equal, res.interface.cmdline, 'to3d data/foo.dcm data/bar.dcm'
    # skip_outliers
    cmd = afni.To3d(skip_outliers=True)
    yield assert_equal, cmd.cmdline, 'to3d -skip_outliers'
    # assume_dicom_mosaic
    cmd = afni.To3d(assume_dicom_mosaic=True)
    yield assert_equal, cmd.cmdline, 'to3d -assume_dicom_mosaic'
    # Test slice time params
    cmd = afni.To3d()
    td = dict(slice_order='zt', nz=12, nt=170, TR=2000, tpattern='alt+z')
    cmd.inputs.time_dependencies = td
    yield assert_equal, cmd.cmdline, 'to3d -time:zt 12 170 2000 alt+z'
    cmd = afni.To3d()
    td = dict(slice_order='tz', nt=150, nz=12, TR=2000, tpattern='alt+z')
    cmd.inputs.time_dependencies = td
    yield assert_equal, cmd.cmdline, 'to3d -time:tz 150 12 2000 alt+z'
    
    # time_dependencies provided as a tuple
    # slice_order, nz, nt, TR, tpattern
    td = ('zt', 12, 130, 2000, 'alt+z')
    cmd = afni.To3d()
    cmd.inputs.time_dependencies = td
    yield assert_equal, cmd.cmdline, 'to3d -time:zt 12 130 2000.00 alt+z'

    # These tests fill fail because they do not specify all required
    # args for the time_dependencies
    # dict(slice_order='zt', nz=12, nt=150, TR=2000, tpattern='alt+z')
    # only slice_order
    cmd.inputs.time_dependencies = dict(slice_order='zt')
    yield assert_raises, KeyError, getattr, cmd, 'cmdline'
    # only slice_order
    cmd.inputs.time_dependencies = dict(slice_order='tz')
    yield assert_raises, KeyError, getattr, cmd, 'cmdline'
    # slice_order and nz
    cmd.inputs.time_dependencies = dict(slice_order='zt', nz=12)
    yield assert_raises, KeyError, getattr, cmd, 'cmdline'
    # slice_order, nz, nt
    cmd.inputs.time_dependencies = dict(slice_order='zt', nz=12, nt=150)
    yield assert_raises, KeyError, getattr, cmd, 'cmdline'
    # slice_order, nz, nt, TR
    cmd.inputs.time_dependencies = dict(slice_order='zt', nz=12, nt=150,
                                        TR=2000)
    yield assert_raises, KeyError, getattr, cmd, 'cmdline'
    # slice_order, nz, nt, tpattern
    cmd.inputs.time_dependencies = dict(slice_order='zt', nz=12, nt=150,
                                        tpattern='alt+z')
    yield assert_raises, KeyError, getattr, cmd, 'cmdline'
    # provide unknown parameters
    cmd = afni.To3d(datatype='anat', foo='bar')    
    yield assert_raises, AttributeError, getattr, cmd, 'cmdline'
    # order of params
    cmd = afni.To3d(datatype='anat')
    cmd.inputs.skip_outliers = True
    cmd.inputs.infiles = 'foo.nii'
    cmd.inputs.prefix = 'bar.nii'
    cmd.inputs.datum = 'float'
    realcmd = 'to3d -anat -datum float -prefix bar.nii -skip_outliers foo.nii'
    yield assert_equal, cmd.cmdline, realcmd
    # result should be InterfaceResult object
    cmd = afni.To3d()
    res = cmd.run('foo.nii')
    yield assert_true, isinstance(res, InterfaceResult)
    # don't specify infile and call run should raise error
    cmd = afni.To3d()
    yield assert_raises, AttributeError, cmd.run


def test_Threedrefit():
    cmd = afni.Threedrefit()
    yield assert_equal, cmd.cmdline, '3drefit'
    # deoblique
    cmd = afni.Threedrefit()
    cmd.inputs.deoblique = True
    yield assert_equal, cmd.cmdline, '3drefit -deoblique'
    # xorigin
    cmd = afni.Threedrefit()
    cmd.inputs.xorigin = 12.34
    yield assert_equal, cmd.cmdline, '3drefit -xorigin 12.34'
    # yorigin
    cmd = afni.Threedrefit(yorigin=12.34)
    yield assert_equal, cmd.cmdline, '3drefit -yorigin 12.34'
    # zorigin
    cmd = afni.Threedrefit(zorigin=12.34)
    yield assert_equal, cmd.cmdline, '3drefit -zorigin 12.34'
    # infile
    cmd = afni.Threedrefit(infile='foo.nii')
    yield assert_equal, cmd.cmdline, '3drefit foo.nii'
    # order of params
    cmd = afni.Threedrefit(deoblique=True)
    cmd.inputs.zorigin = 34.5
    cmd.inputs.infile = 'foo.nii'
    realcmd = '3drefit -deoblique -zorigin 34.5 foo.nii'
    yield assert_equal, cmd.cmdline, realcmd
    # provide unknown params
    cmd = afni.Threedrefit(foo='bar')
    yield assert_raises, AttributeError, getattr, cmd, 'cmdline'
    # don't specify infile and call run should raise error
    cmd = afni.Threedrefit()
    yield assert_raises, AttributeError, cmd.run
    # result should be InterfaceResult object
    cmd = afni.Threedrefit()
    res = cmd.run('foo.nii')
    yield assert_true, isinstance(res, InterfaceResult)


def test_Threedresample():
    cmd = afni.Threedresample()
    yield assert_equal, cmd.cmdline, '3dresample'
    # rsmode
    cmd = afni.Threedresample(rsmode='Li')
    yield assert_equal, cmd.cmdline, '3dresample -rmode Li'
    # orient
    cmd = afni.Threedresample()
    cmd.inputs.orient = 'lpi'
    yield assert_equal, cmd.cmdline, '3dresample -orient lpi'
    # gridfile
    cmd = afni.Threedresample(gridfile='dset+orig')
    yield assert_equal, cmd.cmdline, '3dresample -master dset+orig'
    # infile
    cmd = afni.Threedresample()
    cmd.inputs.infile = 'foo.nii'
    yield assert_equal, cmd.cmdline, '3dresample -inset foo.nii'
    # outfile
    cmd = afni.Threedresample(outfile='bar.nii')
    yield assert_equal, cmd.cmdline, '3dresample -prefix bar.nii'
    # order of params
    cmd = afni.Threedresample(rsmode='Li')
    cmd.inputs.orient = 'lpi'
    cmd.inputs.infile = 'foo.nii'
    cmd.inputs.outfile = 'bar.nii'
    realcmd = '3dresample -rmode Li -orient lpi -prefix bar.nii -inset foo.nii'
    yield assert_equal, cmd.cmdline, realcmd
    # unknown params
    cmd = afni.Threedresample(foo='bar')
    yield assert_raises, AttributeError, getattr, cmd, 'cmdline'
    # infile not specified
    cmd = afni.Threedresample(outfile='bar.nii')
    yield assert_raises, AttributeError, cmd.run
    # outfile not specified
    cmd = afni.Threedresample(infile='foo.nii')
    yield assert_raises, AttributeError, cmd.run
    # result should be InterfaceResult object
    cmd = afni.Threedresample()
    res = cmd.run(infile='foo.nii', outfile='bar.nii')
    yield assert_true, isinstance(res, InterfaceResult)


def test_ThreedTstat():
    cmd = afni.ThreedTstat()
    yield assert_equal, cmd.cmdline, '3dTstat'
    # outfile
    cmd = afni.ThreedTstat(outfile='bar.nii')
    yield assert_equal, cmd.cmdline, '3dTstat -prefix bar.nii'
    # infile
    cmd = afni.ThreedTstat()
    cmd.inputs.infile = 'foo.nii'
    yield assert_equal, cmd.cmdline, '3dTstat foo.nii'
    # order of params
    cmd = afni.ThreedTstat()
    cmd.inputs.infile = 'foo.nii'
    cmd.inputs.outfile = 'bar.nii'
    yield assert_equal, cmd.cmdline, '3dTstat -prefix bar.nii foo.nii'
    # unknown params
    cmd = afni.ThreedTstat(foo='bar')
    yield assert_raises, AttributeError, getattr, cmd, 'cmdline'
    # infile not specified
    cmd = afni.ThreedTstat()
    yield assert_raises, AttributeError, cmd.run
    # result should be InterfaceResult object
    cmd = afni.ThreedTstat()
    res = cmd.run(infile='foo.nii')
    yield assert_true, isinstance(res, InterfaceResult)


def test_ThreedAutomask():
    cmd = afni.ThreedAutomask()
    yield assert_equal, cmd.cmdline, '3dAutomask'
    # outfile
    cmd = afni.ThreedAutomask(outfile='bar.nii')
    yield assert_equal, cmd.cmdline, '3dAutomask -prefix bar.nii'
    # infile
    cmd = afni.ThreedAutomask(infile='foo.nii')
    yield assert_equal, cmd.cmdline, '3dAutomask foo.nii'
    # order of params
    cmd = afni.ThreedAutomask(infile='foo.nii')
    cmd.inputs.outfile = 'bar.nii'
    yield assert_equal, cmd.cmdline, '3dAutomask -prefix bar.nii foo.nii'
    # unknown params
    cmd = afni.ThreedAutomask(foo='bar')
    yield assert_raises, AttributeError, getattr, cmd, 'cmdline'
    # infile not specified
    cmd = afni.ThreedAutomask()
    yield assert_raises, AttributeError, cmd.run
    # result should be InterfaceResult object
    cmd = afni.ThreedAutomask()
    res = cmd.run(infile='foo.nii')
    yield assert_true, isinstance(res, InterfaceResult)


def test_Threedvolreg():
    cmd = afni.Threedvolreg()
    yield assert_equal, cmd.cmdline, '3dvolreg'
    # verbose
    cmd = afni.Threedvolreg(verbose=True)
    yield assert_equal, cmd.cmdline, '3dvolreg -verbose'
    # copy_origin
    cmd = afni.Threedvolreg(copy_origin=True)
    yield assert_equal, cmd.cmdline, '3dvolreg -twodup'
    # time_shift
    cmd = afni.Threedvolreg()
    cmd.inputs.time_shift = 14
    yield assert_equal, cmd.cmdline, '3dvolreg -tshift 14'
    # basefile 
    cmd = afni.Threedvolreg()
    cmd.inputs.basefile = 5
    yield assert_equal, cmd.cmdline, '3dvolreg -base 5'
    # md1dfile
    cmd = afni.Threedvolreg(md1dfile='foo.nii')
    yield assert_equal, cmd.cmdline, '3dvolreg -maxdisp1D foo.nii'
    # onedfile
    cmd = afni.Threedvolreg(onedfile='bar.nii')
    yield assert_equal, cmd.cmdline, '3dvolreg -1Dfile bar.nii'
    # outfile
    cmd = afni.Threedvolreg(outfile='bar.nii')
    yield assert_equal, cmd.cmdline, '3dvolreg -prefix bar.nii'
    # infile
    cmd = afni.Threedvolreg()
    cmd.inputs.infile = 'foo.nii'
    yield assert_equal, cmd.cmdline, '3dvolreg foo.nii'
    # order of params
    cmd = afni.Threedvolreg(infile='foo.nii')
    cmd.inputs.time_shift = 14
    cmd.inputs.copy_origin = True
    cmd.inputs.outfile = 'bar.nii'
    realcmd = '3dvolreg -twodup -tshift 14 -prefix bar.nii foo.nii'
    yield assert_equal, cmd.cmdline, realcmd
    # unknown params
    cmd = afni.Threedvolreg(foo='bar')
    yield assert_raises, AttributeError, getattr, cmd, 'cmdline'
    # infile not specified
    cmd = afni.Threedvolreg()
    yield assert_raises, AttributeError, cmd.run
    # result should be InterfaceResult object
    cmd = afni.Threedvolreg()
    res = cmd.run(infile='foo.nii')
    yield assert_true, isinstance(res, InterfaceResult)


def test_Threedmerge():
    cmd = afni.Threedmerge()
    yield assert_equal, cmd.cmdline, '3dmerge'
    # doall
    cmd = afni.Threedmerge(doall=True)
    yield assert_equal, cmd.cmdline, '3dmerge -doall'
    # gblur_fwhm
    cmd = afni.Threedmerge()
    cmd.inputs.gblur_fwhm = 2.0
    yield assert_equal, cmd.cmdline, '3dmerge -1blur_fwhm 2.0'
    # outfile
    cmd = afni.Threedmerge(outfile='bar.nii')
    yield assert_equal, cmd.cmdline, '3dmerge -prefix bar.nii'
    # infile
    cmd = afni.Threedmerge(infiles='foo.nii')
    yield assert_equal, cmd.cmdline, '3dmerge foo.nii'
    # infile list
    cmd = afni.Threedmerge(infiles=['data/foo.nii', 'data/bar.nii'])
    yield assert_equal, cmd.cmdline, '3dmerge data/foo.nii data/bar.nii'
    # order of params
    cmd = afni.Threedmerge(infiles='foo.nii')
    cmd.inputs.outfile = 'bar.nii'
    cmd.inputs.doall = True
    cmd.inputs.gblur_fwhm = 2.0
    realcmd = '3dmerge -doall -1blur_fwhm 2.0 -prefix bar.nii foo.nii'
    yield assert_equal, cmd.cmdline, realcmd
    # unknown params
    cmd = afni.Threedmerge(foo='bar')
    yield assert_raises, AttributeError, getattr, cmd, 'cmdline'
    # infile not specified
    cmd = afni.Threedmerge()
    yield assert_raises, AttributeError, cmd.run
    # result should be InterfaceResult object
    cmd = afni.Threedmerge()
    res = cmd.run(infiles='foo.nii')
    yield assert_true, isinstance(res, InterfaceResult)


