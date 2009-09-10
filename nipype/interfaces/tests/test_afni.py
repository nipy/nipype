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
    # skip_outliers
    cmd = afni.To3d(skip_outliers=True)
    yield assert_equal, cmd.cmdline, 'to3d -skip_outliers'
    # assume_dicom_mosaic
    cmd = afni.To3d(assume_dicom_mosaic=True)
    yield assert_equal, cmd.cmdline, 'to3d -assume_dicom_mosaic'

    # Test slice time params
    cmd = afni.To3d()
    td = dict(slice_order='zt', nz=12, nt=150, TR=2000, tpattern='alt+z')
    cmd.inputs.time_dependencies = td
    yield assert_equal, cmd.cmdline, 'to3d -time:zt 12 150 2000 alt+z'

    cmd = afni.To3d()
    td = dict(slice_order='tz', nt=150, nz=12, TR=2000, tpattern='alt+z')
    cmd.inputs.time_dependencies = td
    yield assert_equal, cmd.cmdline, 'to3d -time:tz 150 12 2000 alt+z'

    # These tests fill fail because they do not specify all required
    # args for the time_dependencies
    # dict(slice_order='zt', nz=12, nt=150, TR=2000, tpattern='alt+z')
    cmd = afni.To3d()
    cmd.inputs.time_dependencies = dict()
    yield assert_raises, KeyError, getattr, cmd, 'cmdline'
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
    # provide too many parameters for time_dependencies
    cmd.inputs.time_dependencies = dict(slice_order='zt', nz=12, nt=150,
                                        tpattern='alt+z', TR=2000, 
                                        username='foo')
    yield assert_raises, AttributeError, getattr, cmd, 'cmdline'
    # provide unknown parameters
    cmd = afni.To3d(datatype='anat', foo='bar')    
    yield assert_raises, AttributeError, getattr, cmd, 'cmdline'
    

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
