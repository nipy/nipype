# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import warnings
warnings.simplefilter('ignore')
from nipype.testing import *

from nipype.interfaces import afni
from nipype.interfaces.base import InterfaceResult

def afni_not_installed():
    ''' XXX: This test assumes that AFNI.Info.version will not crash on a system without AFNI installed'''
    if afni.Info.version is None:
        return True
    else:
        return False

def test_To3dInputSpec():
    inputs_map = dict(infolder = dict(argstr= '%s/*.dcm',
                                  position = -1,
                                  mandatory = True),
                      outfile = dict(desc = 'converted image file',
                                 argstr = '-prefix %s',
                                 position = -2,
                                 mandatory = True),
                      filetype = dict(desc = 'type of datafile being converted',
                                  argstr = '-%s'),
                      skipoutliers = dict(desc = 'skip the outliers check',
                                      argstr = '-skip_outliers'),
                      assumemosaic = dict(desc = 'assume that Siemens image is mosaic',
                                      argstr = '-assume_dicom_mosaic'),
                      datatype = dict(desc = 'set output file datatype',
                                  argstr = '-datum %s'),
                      funcparams = dict(desc = 'parameters for functional data',
                                    argstr = '-time:zt %s alt+z2'))
    instance = afni.To3d()
    for key, metadata in inputs_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

'''XXX: This test is broken.  output_spec does not appear to have the out_file attribute the same way that inputs does
def test_To3dOutputSpec():
    outputs_map = dict(out_file = dict(desc = 'converted file'))
    instance = afni.To3d()
    for key, metadata in outputs_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.output_spec.traits()[key], metakey), value
'''


def test_ThreedrefitInputSpec():
    inputs_map = dict(infile = dict(desc = 'input file to 3drefit',
                                    argstr = '%s',
                                    position = -1,
                                    mandatory = True),
                      deoblique = dict(desc = 'replace current transformation matrix with cardinal matrix',
                                       argstr = '-deoblique'),
                      xorigin = dict(desc = 'x distance for edge voxel offset',
                                     argstr = '-xorigin %s'),
                      yorigin = dict(desc = 'y distance for edge voxel offset',
                                     argstr = '-yorigin %s'),
                      zorigin = dict(desc = 'y distance for edge voxel offset',
                                     argstr = '-yorigin %s'))
    instance = afni.Threedrefit()
    for key, metadata in inputs_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value


def test_ThreedresampleInputSpec():
    inputs_map = dict(infile = dict(desc = 'input file to 3dresample',
                                    argstr = '-inset %s',
                                    position = -1,
                                    mandatory = True),
                      outfile = dict(desc = 'output file from 3dresample',
                                     argstr = '-prefix %s',
                                     position = -2,
                                     mandatory = True),
                      orientation = dict(desc = 'new orientation code',
                                         argstr = '-orient %s'))
    instance = afni.Threedresample()
    for key, metadata in inputs_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value


def test_ThreedTstatInputSpec():
    inputs_map = dict(infile = dict(desc = 'input file to 3dTstat',
                                    argstr = '%s',
                                    position = -1,
                                    mandatory = True),
                      outfile = dict(desc = 'output file from 3dTstat',
                                     argstr = '-prefix %s',
                                     position = -2,
                                     mandatory = True),
                      options = dict(desc = 'selected statistical output',
                                     argstr = '%s'))
    instance = afni.ThreedTstat()
    for key, metadata in inputs_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value


def test_ThreedAutomaskInputSpec():
    inputs_map = dict(infile = dict(desc = 'input file to 3dAutomask',
                                    argstr = '%s',
                                    position = -1,
                                    mandatory = True),
                      outfile = dict(desc = 'output file from 3dAutomask',
                                     argstr = '-prefix %s',
                                     position = -2,
                                     mandatory = True),
                      options = dict(desc = 'automask settings',
                                     argstr = '%s'))
    instance = afni.ThreedAutomask()
    for key, metadata in inputs_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value


def test_ThreedvolregInputSpec():
    inputs_map = dict(infile = dict(desc = 'input file to 3dvolreg',
                                    argstr = '%s',
                                    position = -1,
                                    mandatory = True),
                      outfile = dict(desc = 'output file from 3dvolreg',
                                     argstr = '-prefix %s',
                                     position = -2,
                                     mandatory = True),
                      basefile = dict(desc = 'base file for registration',
                                      argstr = '-base %s',
                                      position = -5),
                      md1dfile = dict(desc = 'max displacement output file',
                                      argstr = '-maxdisp1D %s',
                                      position = -4),
                      onedfile = dict(desc = '1D movement parameters output file',
                                      argstr = '-1Dfile %s',
                                      position = -3),
                      verbose = dict(desc = 'more detailed description of the process',
                                     argstr = '-verbose'),
                      timeshift = dict(desc = 'time shift to mean slice time offset',
                                       argstr = '-tshift 0'),
                      copyorigin = dict(desc = 'copy base file origin coords to output',
                                        argstr = '-twodup'),
                      other = dict(desc = 'other options',
                                   argstr = '%s'))
    instance = afni.Threedvolreg()
    for key, metadata in inputs_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value


def test_ThreedmergeInputSpec():
    inputs_map = dict(infile = dict(desc = 'input file to 3dvolreg',
                                    argstr = '%s',
                                    position = -1,
                                    mandatory = True),
                      outfile = dict(desc = 'output file from 3dvolreg',
                                     argstr = '-prefix %s',
                                     position = -2,
                                     mandatory = True),
                      doall = dict(desc = 'apply options to all sub-bricks in dataset',
                                   argstr = '-doall'),
                      blurfwhm = dict(desc = 'FWHM blur value (mm)',
                                      argstr = '-1blur_fwhm %d',
                                      units = 'mm'),
                      other = dict(desc = 'other options',
                                   argstr = '%s'))
    instance = afni.Threedmerge()
    for key, metadata in inputs_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value


def test_ThreedZcutupInputSpec():
    inputs_map = dict(infile = dict(desc = 'input file to 3dZcutup',
                                    argstr = '%s',
                                    position = -1,
                                    mandatory = True),
                      outfile = dict(desc = 'output file from 3dZcutup',
                                     argstr = '-prefix %s',
                                     position = -2,
                                     mandatory = True),
                      keep = dict(desc = 'slice range to keep in output',
                                  argstr = '-keep %s'),
                      other = dict(desc = 'other options',
                                   argstr = '%s'))
    instance = afni.ThreedZcutup()
    for key, metadata in inputs_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value


def ThreedAllineateInputSpec():
    inputs_map = dict(infile = dict(desc = 'input file to 3dAllineate',
                                    argstr = '-source %s',
                                    position = -1,
                                    mandatory = True),
                      outfile = dict(desc = 'output file from 3dAllineate',
                                     argstr = '-prefix %s',
                                     position = -2,
                                     mandatory = True),
                      matrix = dict(desc = 'matrix to align input file',
                                    argstr = '-1dmatrix_apply %s',
                                    position = -3))
    instance = afni.ThreedAllineate()
    for key, metadata in inputs_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value





#@skipif(afni_not_installed)
@skipif(True)
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


@skipif(True)
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


@skipif(True)
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


@skipif(True)
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


@skipif(True)
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


@skipif(True)
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


@skipif(True)
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


