# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import warnings
warnings.simplefilter('ignore')
from nipype.testing import *

from nipype.interfaces import afni

def afni_not_installed():
    ''' XXX: This test assumes that AFNI.Info.version will not crash on a system without AFNI installed'''
    if afni.Info.version is None:
        return True
    else:
        return False

def test_allineate():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='-source %s',mandatory=True,),
                     matrix = dict(argstr='-1dmatrix_apply %s',),
                     out_file = dict(argstr='-prefix %s'),
                     outputtype = dict(),
                     )
    instance = afni.Allineate()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_brickstat():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='%s',mandatory=True,),
                     mask = dict(argstr='-mask %s',),
                     min = dict(argstr='-min',),
                     outputtype = dict(),
                     )
    instance = afni.BrickStat()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_skullstrip():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='-input %s',mandatory=True,),
                     out_file = dict(argstr='-prefix %s'),
                     outputtype = dict(),
                     )
    instance = afni.SkullStrip()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_volreg():
    input_map = dict(args = dict(argstr='%s',),
                     basefile = dict(argstr='-base %s',),
                     copyorigin = dict(argstr='-twodup',),
                     environ = dict(usedefault=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='%s',mandatory=True,),
                     md1dfile = dict(argstr='-maxdisp1D %s',),
                     oned_file = dict(argstr='-1Dfile %s',),
                     out_file = dict(argstr='-prefix %s',),
                     outputtype = dict(),
                     timeshift = dict(argstr='-tshift 0',),
                     verbose = dict(argstr='-verbose',),
                     zpad = dict(argstr='-zpad %d',),
                     )
    instance = afni.Volreg()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_calc():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     expr = dict(argstr='-expr "%s"',mandatory=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_file_a = dict(argstr='-a %s',mandatory=True,),
                     in_file_b = dict(argstr=' -b %s',),
                     out_file = dict(argstr='-prefix %s',),
                     single_idx = dict(),
                     start_idx = dict(requires=['stop_idx'],),
                     stop_idx = dict(requires=['start_idx'],),
                     )
    instance = afni.Calc()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_to3d():
    input_map = dict(args = dict(argstr='%s',),
                     assumemosaic = dict(argstr='-assume_dicom_mosaic',),
                     datatype = dict(argstr='-datum %s',),
                     environ = dict(usedefault=True,),
                     filetype = dict(argstr='-%s',),
                     funcparams = dict(argstr='-time:zt %s alt+z2',),
                     ignore_exception = dict(usedefault=True,),
                     infolder = dict(argstr='%s/*.dcm',mandatory=True,),
                     out_file = dict(argstr='-prefix %s'),
                     outputtype = dict(),
                     skipoutliers = dict(argstr='-skip_outliers',),
                     )
    instance = afni.To3D()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_fim():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     fim_thr = dict(argstr='-fim_thr %f',),
                     ideal_file = dict(argstr='-ideal_file %s',mandatory=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr=' -input %s',mandatory=True,),
                     out = dict(argstr='-out %s',),
                     out_file = dict(argstr='-bucket %s'),
                     outputtype = dict(),
                     )
    instance = afni.Fim()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_tcat():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_files = dict(argstr=' %s',mandatory=True,),
                     out_file = dict(argstr='-prefix %s',),
                     outputtype = dict(),
                     rlt = dict(argstr='-rlt%s',),
                     )
    instance = afni.TCat()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_resample():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='-inset %s',mandatory=True,),
                     orientation = dict(argstr='-orient %s',),
                     out_file = dict(argstr='-prefix %s',),
                     outputtype = dict(),
                     suffix = dict(),
                     )
    instance = afni.Resample()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_despike():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='%s',mandatory=True,),
                     out_file = dict(argstr='-prefix %s',),
                     outputtype = dict(),
                     )
    instance = afni.Despike()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_refit():
    input_map = dict(args = dict(argstr='%s',),
                     deoblique = dict(argstr='-deoblique',),
                     environ = dict(usedefault=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(copyfile=True,mandatory=True,argstr='%s',),
                     outputtype = dict(),
                     xorigin = dict(argstr='-xorigin %s',),
                     yorigin = dict(argstr='-yorigin %s',),
                     zorigin = dict(argstr='-zorigin %s',),
                     )
    instance = afni.Refit()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_warp():
    input_map = dict(args = dict(argstr='%s',),
                     deoblique = dict(argstr='-deoblique',),
                     environ = dict(usedefault=True,),
                     gridset = dict(argstr='-gridset %s',),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='%s',mandatory=True,),
                     interp = dict(argstr='-%s',),
                     matparent = dict(argstr='-matparent %s',),
                     mni2tta = dict(argstr='-mni2tta',),
                     out_file = dict(argstr='-prefix %s',),
                     outputtype = dict(),
                     suffix = dict(),
                     tta2mni = dict(argstr='-tta2mni',),
                     zpad = dict(argstr='-zpad %d',),
                     )
    instance = afni.Warp()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_detrend():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='%s',mandatory=True,),
                     out_file = dict(argstr='-prefix %s',),
                     outputtype = dict(),
                     )
    instance = afni.Detrend()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_copy():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='%s',mandatory=True,),
                     out_file = dict(argstr='-prefix %s',),
                     outputtype = dict(),
                     )
    instance = afni.Copy()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_roistats():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='%s',mandatory=True,),
                     mask = dict(argstr='-mask %s',),
                     mask_f2short = dict(argstr='-mask_f2short',),
                     outputtype = dict(),
                     quiet = dict(argstr='-quiet',),
                     )
    instance = afni.ROIStats()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_tcorrelate():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     ignore_exception = dict(usedefault=True,),
                     out_file = dict(argstr='-prefix %s',),
                     outputtype = dict(),
                     pearson = dict(argstr='-pearson',),
                     polort = dict(argstr='-polort %d',),
                     xset = dict(argstr=' %s',mandatory=True,),
                     yset = dict(argstr=' %s',mandatory=True,),
                     )
    instance = afni.TCorrelate()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_zcutup():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='%s',mandatory=True,),
                     keep = dict(argstr='-keep %s',),
                     out_file = dict(argstr='-prefix %s'),
                     outputtype = dict(),
                     )
    instance = afni.ZCutUp()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_merge():
    input_map = dict(args = dict(argstr='%s',),
                     blurfwhm = dict(argstr='-1blur_fwhm %d',),
                     doall = dict(argstr='-doall',),
                     environ = dict(usedefault=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_files = dict(argstr='%s',mandatory=True,),
                     out_file = dict(argstr='-prefix %s'),
                     outputtype = dict(),
                     )
    instance = afni.Merge()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_fourier():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     highpass = dict(argstr='-highpass %f',mandatory=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='%s',mandatory=True,),
                     lowpass = dict(argstr='-lowpass %f',mandatory=True,),
                     out_file = dict(argstr='-prefix %s',),
                     outputtype = dict(),
                     )
    instance = afni.Fourier()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_tshift():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     ignore = dict(argstr='-ignore %s',),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='%s',mandatory=True,),
                     interp = dict(argstr='-%s',),
                     out_file = dict(argstr='-prefix %s',),
                     outputtype = dict(),
                     rlt = dict(argstr='-rlt',),
                     rltplus = dict(argstr='-rlt+',),
                     suffix = dict(),
                     tpattern = dict(argstr='-tpattern %s',),
                     tr = dict(argstr='-TR %s',),
                     tslice = dict(argstr='-slice %s',xor=['tzero'],),
                     tzero = dict(argstr='-tzero %s',xor=['tslice'],),
                     )
    instance = afni.TShift()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_tstat():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='%s',mandatory=True,),
                     out_file = dict(argstr='-prefix %s',),
                     outputtype = dict(),
                     )
    instance = afni.TStat()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_maskave():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(usedefault=True,),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='%s',mandatory=True,),
                     mask = dict(argstr='-mask %s',),
                     out_file = dict(argstr='> %s',),
                     outputtype = dict(),
                     quiet = dict(argstr='-quiet',),
                     )
    instance = afni.Maskave()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_automask():
    input_map = dict(apply_mask = dict(argstr='-apply_prefix %s'),
                     apply_suffix = dict(),
                     args = dict(argstr='%s',),
                     clfrac = dict(argstr='-dilate %s',),
                     dilate = dict(argstr='-dilate %s',),
                     environ = dict(usedefault=True,),
                     erode = dict(argstr='-erode %s',),
                     ignore_exception = dict(usedefault=True,),
                     in_file = dict(argstr='%s',mandatory=True,),
                     mask_suffix = dict(),
                     out_file = dict(argstr='-prefix %s'),
                     outputtype = dict(),
                     )
    instance = afni.Automask()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value
