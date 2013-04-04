# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft = python sts = 4 ts = 4 sw = 4 et:
"""Afni preprocessing interfaces

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""
import warnings

import os
import re
from .base import AFNIBaseCommandInputSpec, AFNIBaseCommand
from ..base import (Directory, CommandLineInputSpec, CommandLine, TraitedSpec,
                    traits, isdefined, File, InputMultiPath, Undefined)
from ...utils.filemanip import (load_json, save_json, split_filename)
from nipype.utils.filemanip import fname_presuffix
from nipype.interfaces.afni.base import AFNICommand, AFNICommandInputSpec,\
    AFNICommandOutputSpec

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class To3DInputSpec(AFNICommandInputSpec):
    out_file = File("%s", desc='output image file name',
                    argstr='-prefix %s', name_source=["in_folder", "infolder"], usedefault=True)
    in_xor = ["infolder", "in_folder"]
    in_folder = Directory(desc='folder with DICOM images to convert',
                          argstr='%s/*.dcm',
                          position=-1,
                          mandatory=True,
                          exists=True,
                          xor=in_xor)

    infolder = Directory(desc='folder with DICOM images to convert',
                         argstr='%s/*.dcm',
                         position=-1,
                         mandatory=True,
                         exists=True,
                         deprecated='0.8',
                         new_name="in_folder",
                         xor=in_xor)

    filetype = traits.Enum('spgr', 'fse', 'epan', 'anat', 'ct', 'spct',
                           'pet', 'mra', 'bmap', 'diff',
                           'omri', 'abuc', 'fim', 'fith', 'fico', 'fitt', 'fift',
                           'fizt', 'fict', 'fibt',
                           'fibn', 'figt', 'fipt',
                           'fbuc', argstr='-%s', desc='type of datafile being converted')

    skipoutliers = traits.Bool(desc='skip the outliers check',
                               argstr='-skip_outliers')

    assumemosaic = traits.Bool(desc='assume that Siemens image is mosaic',
                               argstr='-assume_dicom_mosaic')

    datatype = traits.Enum('short', 'float', 'byte', 'complex',
                           desc='set output file datatype', argstr='-datum %s')

    funcparams = traits.Str(desc='parameters for functional data',
                            argstr='-time:zt %s alt+z2')


class To3D(AFNICommand):
    """Create a 3D dataset from 2D image files using AFNI to3d command

    For complete details, see the `to3d Documentation
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/to3d.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> To3D = afni.To3D()
    >>> To3D.inputs.datatype = 'float'
    >>> To3D.inputs.infolder = 'dicomdir'
    >>> To3D.inputs.filetype = "anat"
    >>> To3D.inputs.outputtype = "NIFTI"
    >>> To3D.cmdline
    'to3d -datum float -anat -prefix dicomdir.nii dicomdir/*.dcm'
    >>> res = To3D.run() #doctest: +SKIP

   """

    _cmd = 'to3d'
    input_spec = To3DInputSpec
    output_spec = AFNICommandOutputSpec


class TShiftInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dTShift',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True)

    out_file = File("%s_tshift", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file", usedefault=True)

    tr = traits.Str(desc='manually set the TR' +
                    'You can attach suffix "s" for seconds or "ms" for milliseconds.',
                    argstr='-TR %s')

    tzero = traits.Float(desc='align each slice to given time offset',
                         argstr='-tzero %s',
                         xor=['tslice'])

    tslice = traits.Int(desc='align each slice to time offset of given slice',
                        argstr='-slice %s',
                        xor=['tzero'])

    ignore = traits.Int(desc='ignore the first set of points specified',
                        argstr='-ignore %s')

    interp = traits.Enum(('Fourier', 'linear', 'cubic', 'quintic', 'heptic'),
                         desc='different interpolation methods (see 3dTShift for details)' +
                         ' default = Fourier', argstr='-%s')

    tpattern = traits.Enum(('alt+z', 'alt+z2', 'alt-z',
                            'alt-z2', 'seq+z', 'seq-z'),
                           desc='use specified slice time pattern rather than one in header',
                           argstr='-tpattern %s')

    rlt = traits.Bool(desc='Before shifting, remove the mean and linear trend',
                      argstr="-rlt")

    rltplus = traits.Bool(desc='Before shifting,' +
                          ' remove the mean and linear trend and ' +
                          'later put back the mean',
                          argstr="-rlt+")


class TShift(AFNICommand):
    """Shifts voxel time series from input
    so that seperate slices are aligned to the same
    temporal origin

    For complete details, see the `3dTshift Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTshift.html>

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> tshift = afni.TShift()
    >>> tshift.inputs.in_file = 'functional.nii'
    >>> tshift.inputs.tpattern = 'alt+z'
    >>> tshift.inputs.tzero = 0.0
    >>> tshift.cmdline
    '3dTshift -prefix functional_tshift+orig.BRIK -tpattern alt+z -tzero 0.0 functional.nii'
    >>> res = tshift.run()   # doctest: +SKIP

    """

    _cmd = '3dTshift'
    input_spec = TShiftInputSpec
    output_spec = AFNICommandOutputSpec


class RefitInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3drefit',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True,
                   copyfile=True)

    out_file = File("%s_refit", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file", usedefault=True)

    deoblique = traits.Bool(desc='replace current transformation' +
                            ' matrix with cardinal matrix',
                            argstr='-deoblique')

    xorigin = traits.Str(desc='x distance for edge voxel offset',
                         argstr='-xorigin %s')

    yorigin = traits.Str(desc='y distance for edge voxel offset',
                         argstr='-yorigin %s')
    zorigin = traits.Str(desc='z distance for edge voxel offset',
                         argstr='-zorigin %s')
    suffix = traits.Str('_refit', desc="out_file suffix", usedefault=True)


class Refit(AFNICommand):
    """Changes some of the information inside a 3D dataset's header

    For complete details, see the `3drefit Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3drefit.html>

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> refit = afni.Refit()
    >>> refit.inputs.in_file = 'structural.nii'
    >>> refit.inputs.deoblique=True
    >>> res = refit.run() # doctest: +SKIP

    """

    _cmd = '3drefit'
    input_spec = RefitInputSpec
    output_spec = AFNICommandOutputSpec


class WarpInputSpec(AFNICommandInputSpec):

    in_file = File(desc='input file to 3dWarp',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True)

    out_file = File("%s_warp", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file", usedefault=True)

    tta2mni = traits.Bool(desc='transform dataset from Talairach to MNI152',
                          argstr='-tta2mni')

    mni2tta = traits.Bool(desc='transform dataset from MNI152 to Talaraich',
                          argstr='-mni2tta')

    matparent = File(desc="apply transformation from 3dWarpDrive",
                     argstr="-matparent %s",
                     exists=True)

    deoblique = traits.Bool(desc='transform dataset from oblique to cardinal',
                            argstr='-deoblique')

    interp = traits.Enum(('linear', 'cubic', 'NN', 'quintic'),
                         desc='spatial interpolation methods [default = linear]',
                         argstr='-%s')

    gridset = File(desc="copy grid of specified dataset",
                   argstr="-gridset %s",
                   exists=True)

    zpad = traits.Int(desc="pad input dataset with N planes" +
                      " of zero on all sides.",
                      argstr="-zpad %d")

    suffix = traits.Str('_warp', desc="out_file suffix", usedefault=True)


class Warp(AFNICommand):
    """Use 3dWarp for spatially transforming a dataset

    For complete details, see the `3dWarp Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dWarp.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> warp = afni.Warp()
    >>> warp.inputs.in_file = 'structural.nii'
    >>> warp.inputs.deoblique = True
    >>> res = warp.run() # doctest: +SKIP

    """

    _cmd = '3dWarp'
    input_spec = WarpInputSpec
    output_spec = AFNICommandOutputSpec


class ResampleInputSpec(AFNICommandInputSpec):

    in_file = File(desc='input file to 3dresample',
                   argstr='-inset %s',
                   position=-1,
                   mandatory=True,
                   exists=True)

    out_file = File("%s_resample", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file", usedefault=True)

    orientation = traits.Str(desc='new orientation code',
                             argstr='-orient %s')


class Resample(AFNICommand):
    """Resample or reorient an image using AFNI 3dresample command

    For complete details, see the `3dresample Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dresample.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> resample = afni.Resample()
    >>> resample.inputs.in_file = 'functional.nii'
    >>> resample.inputs.orientation= 'RPI'
    >>> res = resample.run() # doctest: +SKIP

    """

    _cmd = '3dresample'
    input_spec = ResampleInputSpec
    output_spec = AFNICommandOutputSpec


class AutoTcorrelateInputSpec(AFNICommandInputSpec):
    in_file = File(desc='timeseries x space (volume or surface) file',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True)

    polort = traits.Int(
        desc='Remove polynomical trend of order m or -1 for no detrending',
        argstr="-polort %d")
    eta2 = traits.Bool(desc='eta^2 similarity',
                       argstr="-eta2")
    mask = File(exists=True, desc="mask of voxels",
                argstr="-mask %s")
    mask_only_targets = traits.Bool(desc="use mask only on targets voxels",
                                    argstr="-mask_only_targets",
                                    xor=['mask_source'])
                                    
    mask_source = File(exists=True, 
                        desc="mask for source voxels", 
                        argstr="-mask_source %s",
                        xor=['mask_only_targets'])

    out_file = File("%s_similarity_matrix.1D", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file", usedefault=True)


class AutoTcorrelate(AFNICommand):
    """Computes the correlation coefficient between the time series of each
    pair of voxels in the input dataset, and stores the output into a
    new anatomical bucket dataset [scaled to shorts to save memory space].

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> corr = afni.AutoTcorrelate()
    >>> corr.inputs.in_file = 'functional.nii'
    >>> corr.inputs.out_file = 'my_similarity_matrix.1D'
    >>> corr.inputs.polort = -1
    >>> corr.inputs.eta2 = True
    >>> corr.inputs.mask = 'mask.nii'
    >>> corr.inputs.mask_only_targets = True
    >>> corr.cmdline # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    '3dAutoTcorrelate -eta2 -mask mask.nii -mask_only_targets -prefix ...my_similarity_matrix.1D -polort -1 functional.nii'
    >>> res = corr.run() # doctest: +SKIP
    """
    input_spec = AutoTcorrelateInputSpec
    output_spec = AFNICommandOutputSpec
    _cmd = '3dAutoTcorrelate'

    def _overload_extension(self, value):
        path, base, ext = split_filename(value)
        if ext.lower() not in [".1d", ".nii.gz", ".nii"]:
            ext = ext + ".1D"
        return os.path.join(path, base + ext)

    def _gen_filename(self, name):
        return os.path.abspath(super(AutoTcorrelate, self)._gen_filename(name))


class TStatInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dTstat',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True)

    out_file = File("%s_tstat", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file", usedefault=True)

    mask = File(desc='mask file',
                argstr='-mask %s',
                exists=True)
    options = traits.Str(desc='selected statistical output',
                         argstr='%s')


class TStat(AFNICommand):
    """Compute voxel-wise statistics using AFNI 3dTstat command

    For complete details, see the `3dTstat Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTstat.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> tstat = afni.TStat()
    >>> tstat.inputs.in_file = 'functional.nii'
    >>> tstat.inputs.args= '-mean'
    >>> res = tstat.run() # doctest: +SKIP

    """

    _cmd = '3dTstat'
    input_spec = TStatInputSpec
    output_spec = AFNICommandOutputSpec


class DetrendInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dDetrend',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True)

    out_file = File("%s_detrend", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file", usedefault=True)


class Detrend(AFNICommand):
    """This program removes components from voxel time series using
    linear least squares

    For complete details, see the `3dDetrend Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDetrend.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> detrend = afni.Detrend()
    >>> detrend.inputs.in_file = 'functional.nii'
    >>> detrend.inputs.args = '-polort 2'
    >>> res = detrend.run() # doctest: +SKIP

    """

    _cmd = '3dDetrend'
    input_spec = DetrendInputSpec
    output_spec = AFNICommandOutputSpec


class DespikeInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dDespike',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True)

    out_file = File("%s_despike", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file", usedefault=True)


class Despike(AFNICommand):
    """Removes 'spikes' from the 3D+time input dataset

    For complete details, see the `3dDespike Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDespike.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> despike = afni.Despike()
    >>> despike.inputs.in_file = 'functional.nii'
    >>> res = despike.run() # doctest: +SKIP

    """

    _cmd = '3dDespike'
    input_spec = DespikeInputSpec
    output_spec = AFNICommandOutputSpec


class AutomaskInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dAutomask',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True)

    out_file = File("%s_mask", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file", usedefault=True)

    brain_file = File("%s_masked",
                      desc="output file from 3dAutomask",
                      argstr='-apply_prefix %s',
                      name_source="in_file",
                      usedefault=True)

    clfrac = traits.Float(desc='sets the clip level fraction' +
                          ' (must be 0.1-0.9). ' +
                          'A small value will tend to make the mask larger [default = 0.5].',
                          argstr="-dilate %s")

    dilate = traits.Int(desc='dilate the mask outwards',
                        argstr="-dilate %s")

    erode = traits.Int(desc='erode the mask inwards',
                       argstr="-erode %s")

    mask_suffix = traits.Str(
        desc="out_file suffix", depracated=0.8, new_name="out_file")
    apply_suffix = traits.Str(
        desc="out_file suffix", depracated=0.8, new_name="brain_file")
    apply_mask = File(desc="output file from 3dAutomask",
                      argstr='-apply_prefix %s',
                      name_source="in_file", depracated=0.8, new_name="brain_file")


class AutomaskOutputSpec(TraitedSpec):
    out_file = File(desc='mask file',
                    exists=True)

    brain_file = File(desc='brain file (skull stripped)')


class Automask(AFNICommand):
    """Create a brain-only mask of the image using AFNI 3dAutomask command

    For complete details, see the `3dAutomask Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAutomask.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> automask = afni.Automask()
    >>> automask.inputs.in_file = 'functional.nii'
    >>> automask.inputs.dilate = 1
    >>> automask.inputs.outputtype = "NIFTI"
    >>> automask.cmdline
    '3dAutomask -apply_prefix functional_masked.nii -dilate 1 -prefix functional_mask.nii functional.nii'
    >>> res = automask.run() # doctest: +SKIP

    """

    _cmd = '3dAutomask'
    input_spec = AutomaskInputSpec
    output_spec = AutomaskOutputSpec

    def _gen_filename(self, name):
        trait_spec = self.inputs.trait(name)
        if name == "out_file" and isdefined(self.inputs.mask_suffix):
            suffix = ''
            prefix = ''
            if isdefined(self.inputs.mask_suffix):
                suffix = self.inputs.suffix

            _, base, _ = split_filename(
                getattr(self.inputs, trait_spec.name_source))
            return self._gen_fname(basename=base, prefix=prefix, suffix=suffix, cwd=os.getcwd())
        elif name == "brain_file" and isdefined(self.inputs.apply_suffix):
            suffix = ''
            prefix = ''
            if isdefined(self.inputs.apply_suffix):
                suffix = self.inputs.suffix

            _, base, _ = split_filename(
                getattr(self.inputs, trait_spec.name_source))
            return self._gen_fname(basename=base, prefix=prefix, suffix=suffix, cwd=os.getcwd())
        elif name == "apply_mask" and isdefined(self.inputs.apply_suffix):
            suffix = ''
            prefix = ''
            if isdefined(self.inputs.apply_suffix):
                suffix = self.inputs.suffix

            _, base, _ = split_filename(
                getattr(self.inputs, trait_spec.name_source))
            return self._gen_fname(basename=base, prefix=prefix, suffix=suffix, cwd=os.getcwd())
        elif hasattr(self.inputs, name) and isdefined(getattr(self.inputs, name)):
            return super(Automask, self)._gen_filename(name)
        return Undefined

    def _list_outputs(self):
        outputs = super(Automask, self)._list_outputs()
        if isdefined(self.inputs.apply_mask):
            outputs['brain_file'] = os.path.abspath(
                self._gen_filename('apply_mask'))
        return outputs


class VolregInputSpec(AFNICommandInputSpec):

    in_file = File(desc='input file to 3dvolreg',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True)
    out_file = File("%s_volreg", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file", usedefault=True)

    basefile = File(desc='base file for registration',
                    argstr='-base %s',
                    position=-6,
                    exists=True)
    zpad = traits.Int(desc='Zeropad around the edges' +
                      ' by \'n\' voxels during rotations',
                      argstr='-zpad %d',
                      position=-5)
    md1dfile = File(desc='max displacement output file',
                    argstr='-maxdisp1D %s',
                    position=-4)
    oned_file = File('%s.1D', desc='1D movement parameters output file',
                     argstr='-1Dfile %s',
                     name_source="in_file",
                     keep_extension=True,
                     usedefault=True)
    verbose = traits.Bool(desc='more detailed description of the process',
                          argstr='-verbose')
    timeshift = traits.Bool(desc='time shift to mean slice time offset',
                            argstr='-tshift 0')
    copyorigin = traits.Bool(desc='copy base file origin coords to output',
                             argstr='-twodup')


class VolregOutputSpec(TraitedSpec):
    out_file = File(desc='registered file', exists=True)
    md1d_file = File(desc='max displacement info file', exists=True)
    oned_file = File(desc='movement parameters info file', exists=True)


class Volreg(AFNICommand):
    """Register input volumes to a base volume using AFNI 3dvolreg command

    For complete details, see the `3dvolreg Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dvolreg.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> volreg = afni.Volreg()
    >>> volreg.inputs.in_file = 'functional.nii'
    >>> volreg.inputs.args = '-Fourier -twopass'
    >>> volreg.inputs.zpad = 4
    >>> volreg.inputs.outputtype = "NIFTI"
    >>> volreg.cmdline
    '3dvolreg -Fourier -twopass -1Dfile functional.1D -prefix functional_volreg.nii -zpad 4 functional.nii'
    >>> res = volreg.run() # doctest: +SKIP

    """

    _cmd = '3dvolreg'
    input_spec = VolregInputSpec
    output_spec = VolregOutputSpec


class MergeInputSpec(AFNICommandInputSpec):
    in_files = InputMultiPath(
        File(desc='input file to 3dmerge', exists=True),
        argstr='%s',
        position=-1,
        mandatory=True)
    out_file = File("%s_merge", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file", usedefault=True)
    doall = traits.Bool(desc='apply options to all sub-bricks in dataset',
                        argstr='-doall')
    blurfwhm = traits.Int(desc='FWHM blur value (mm)',
                          argstr='-1blur_fwhm %d',
                          units='mm')


class Merge(AFNICommand):
    """Merge or edit volumes using AFNI 3dmerge command

    For complete details, see the `3dmerge Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dmerge.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> merge = afni.Merge()
    >>> merge.inputs.in_files = ['functional.nii', 'functional2.nii']
    >>> merge.inputs.blurfwhm = 4
    >>> merge.inputs.doall = True
    >>> merge.inputs.out_file = 'e7.nii'
    >>> res = merge.run() # doctest: +SKIP

    """

    _cmd = '3dmerge'
    input_spec = MergeInputSpec
    output_spec = AFNICommandOutputSpec


class CopyInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dcopy',
                   argstr='%s',
                   position=-2,
                   mandatory=True,
                   exists=True)
    out_file = File("%s_copy", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file", usedefault=True)


class Copy(AFNICommand):
    """Copies an image of one type to an image of the same
    or different type using 3dcopy command

    For complete details, see the `3dcopy Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dcopy.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> copy = afni.Copy()
    >>> copy.inputs.in_file = 'functional.nii'
    >>> copy.inputs.out_file = 'new_func.nii'
    >>> res = copy.run() # doctest: +SKIP

    """

    _cmd = '3dcopy'
    input_spec = CopyInputSpec
    output_spec = AFNICommandOutputSpec


class FourierInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dFourier',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True)
    out_file = File("%s_fourier", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file", usedefault=True)
    lowpass = traits.Float(desc='lowpass',
                           argstr='-lowpass %f',
                           position=0,
                           mandatory=True)
    highpass = traits.Float(desc='highpass',
                            argstr='-highpass %f',
                            position=1,
                            mandatory=True)


class Fourier(AFNICommand):
    """Program to lowpass and/or highpass each voxel time series in a
    dataset, via the FFT

    For complete details, see the `3dFourier Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dfourier.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> fourier = afni.Fourier()
    >>> fourier.inputs.in_file = 'functional.nii'
    >>> fourier.inputs.args = '-retrend'
    >>> fourier.inputs.highpass = 0.005
    >>> fourier.inputs.lowpass = 0.1
    >>> res = fourier.run() # doctest: +SKIP

    """

    _cmd = '3dFourier'
    input_spec = FourierInputSpec
    output_spec = AFNICommandOutputSpec


class BandpassInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3dBandpass',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)
    out_file = File(
        '%s_bp',
        desc='output file from 3dBandpass',
        argstr='-prefix %s',
        position=1,
        name_source='in_file',
        genfile=True,
        usedefault=True)
    lowpass = traits.Float(
        desc='lowpass',
        argstr='%f',
        position=-2,
        mandatory=True)
    highpass = traits.Float(
        desc='highpass',
        argstr='%f',
        position=-3,
        mandatory=True)
    mask = File(
        desc='mask file',
        position=2,
        argstr='-mask %s',
        exists=True)
    despike = traits.Bool(
        argstr='-despike',
        desc="""Despike each time series before other processing.
                  ++ Hopefully, you don't actually need to do this,
                     which is why it is optional.""")
    orthogonalize_file = InputMultiPath(
        File(exists=True),
        argstr="-ort %s",
        desc="""Also orthogonalize input to columns in f.1D
                   ++ Multiple '-ort' options are allowed.""")
    orthogonalize_dset = File(
        exists=True,
        argstr="-dsort %s",
        desc="""Orthogonalize each voxel to the corresponding
                   voxel time series in dataset 'fset', which must
                   have the same spatial and temporal grid structure
                   as the main input dataset.
                   ++ At present, only one '-dsort' option is allowed.""")
    no_detrend = traits.Bool(
        argstr='-nodetrend',
        desc="""Skip the quadratic detrending of the input that
                    occurs before the FFT-based bandpassing.
                   ++ You would only want to do this if the dataset
                      had been detrended already in some other program.""")
    tr = traits.Float(
        arsgtr="-dt %f",
        desc="set time step (TR) in sec [default=from dataset header]")
    nfft = traits.Int(
        argstr='-nfft %d',
        desc="set the FFT length [must be a legal value]")
    normalize = traits.Bool(
        argstr='-norm',
        desc="""Make all output time series have L2 norm = 1
                   ++ i.e., sum of squares = 1""")
    automask = traits.Bool(
        argstr='-automask',
        desc="Create a mask from the input dataset")
    blur = traits.Float(
        argstr='-blur %f',
        desc="""Blur (inside the mask only) with a filter
                    width (FWHM) of 'fff' millimeters.""")
    localPV = traits.Float(
        argstr='-localPV %f',
        desc="""Replace each vector by the local Principal Vector
                    (AKA first singular vector) from a neighborhood
                    of radius 'rrr' millimiters.
                   ++ Note that the PV time series is L2 normalized.
                   ++ This option is mostly for Bob Cox to have fun with.""")
    notrans = traits.Bool(
        argstr='-notrans',
        desc="""Don't check for initial positive transients in the data:
                   ++ The test is a little slow, so skipping it is OK,
                   if you KNOW the data time series are transient-free.""")


class Bandpass(AFNICommand):
    """Program to lowpass and/or highpass each voxel time series in a
    dataset, offering more/different options than Fourier

    For complete details, see the `3dBandpass Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dbandpass.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> bandpass = afni.Bandpass()
    >>> bandpass.inputs.in_file = example_data('functional.nii')
    >>> bandpass.inputs.highpass = 0.005
    >>> bandpass.inputs.lowpass = 0.1
    >>> res = bandpass.run() # doctest: +SKIP

    """

    _cmd = '3dBandpass'
    input_spec = BandpassInputSpec
    output_spec = AFNICommandOutputSpec


class ZCutUpInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dZcutup',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True)
    out_file = File("%s_zcupup", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file", usedefault=True)
    keep = traits.Str(desc='slice range to keep in output',
                      argstr='-keep %s')


class ZCutUp(AFNICommand):
    """Cut z-slices from a volume using AFNI 3dZcutup command

    For complete details, see the `3dZcutup Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dZcutup.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> zcutup = afni.ZCutUp()
    >>> zcutup.inputs.in_file = 'functional.nii'
    >>> zcutup.inputs.out_file = 'functional_zcutup.nii'
    >>> zcutup.inputs.keep= '0 10'
    >>> res = zcutup.run() # doctest: +SKIP

    """

    _cmd = '3dZcutup'
    input_spec = ZCutUpInputSpec
    output_spec = AFNICommandOutputSpec


class AllineateInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dAllineate',
                   argstr='-source %s',
                   position=-1,
                   mandatory=True,
                   exists=True)
    reference = File(
        exists=True,
        argstr='-base %s',
        desc="""file to be used as reference, the first volume will be used
if not given the reference will be the first volume of in_file.""")
    out_file = File(
        desc='output file from 3dAllineate',
        argstr='-prefix %s',
        position=-2,
        name_source='%s_allineate',
        genfile=True)
    suffix = traits.Str('_allineate', desc="out_file suffix", usedefault=True)

    out_param_file = File(
        argstr='-1Dparam_save %s',
        desc='Save the warp parameters in ASCII (.1D) format.')
    in_param_file = File(
        exists=True,
        argstr='-1Dparam_apply %s',
        desc="""Read warp parameters from file and apply them to
                  the source dataset, and produce a new dataset""")
    out_matrix = File(
        argstr='-1Dmatrix_save %s',
        desc='Save the transformation matrix for each volume.')
    in_matrix = File(desc='matrix to align input file',
                     argstr='-1Dmatrix_apply %s',
                     position=-3)

    _cost_funcs = [
        'leastsq', 'ls',
        'mutualinfo', 'mi',
        'corratio_mul', 'crM',
        'norm_mutualinfo', 'nmi',
        'hellinger', 'hel',
        'corratio_add', 'crA',
        'corratio_uns', 'crU']

    cost = traits.Enum(
        *_cost_funcs, argstr='-cost %s',
        desc="""Defines the 'cost' function that defines the matching
                between the source and the base""")
    _interp_funcs = [
        'nearestneighbour', 'linear', 'cubic', 'quintic', 'wsinc5']
    interpolation = traits.Enum(
        *_interp_funcs[:-1], argstr='-interp %s',
        desc='Defines interpolation method to use during matching')
    final_interpolation = traits.Enum(
        *_interp_funcs, argstr='-final %s',
        desc='Defines interpolation method used to create the output dataset')

    #   TECHNICAL OPTIONS (used for fine control of the program):
    nmatch = traits.Int(
        argstr='-nmatch %d',
        desc='Use at most n scattered points to match the datasets.')
    no_pad = traits.Bool(
        argstr='-nopad',
        desc='Do not use zero-padding on the base image.')
    zclip = traits.Bool(
        argstr='-zclip',
        desc='Replace negative values in the input datasets (source & base) with zero.')
    convergence = traits.Float(
        argstr='-conv %f',
        desc='Convergence test in millimeters (default 0.05mm).')
    usetemp = traits.Bool(argstr='-usetemp', desc='temporary file use')
    check = traits.List(
        traits.Enum(*_cost_funcs), argstr='-check %s',
        desc="""After cost functional optimization is done, start at the
                final parameters and RE-optimize using this new cost functions.
                If the results are too different, a warning message will be
                printed.  However, the final parameters from the original
                optimization will be used to create the output dataset.""")

    #      ** PARAMETERS THAT AFFECT THE COST OPTIMIZATION STRATEGY **
    one_pass = traits.Bool(
        argstr='-onepass',
        desc="""Use only the refining pass -- do not try a coarse
                resolution pass first.  Useful if you know that only
                small amounts of image alignment are needed.""")
    two_pass = traits.Bool(
        argstr='-twopass',
        desc="""Use a two pass alignment strategy for all volumes, searching
              for a large rotation+shift and then refining the alignment.""")
    two_blur = traits.Float(
        argstr='-twoblur',
        desc='Set the blurring radius for the first pass in mm.')
    two_first = traits.Bool(
        argstr='-twofirst',
        desc="""Use -twopass on the first image to be registered, and
               then on all subsequent images from the source dataset,
               use results from the first image's coarse pass to start
               the fine pass.""")
    two_best = traits.Int(
        argstr='-twobest %d',
        desc="""In the coarse pass, use the best 'bb' set of initial
               points to search for the starting point for the fine
               pass.  If bb==0, then no search is made for the best
               starting point, and the identity transformation is
               used as the starting point.  [Default=5; min=0 max=11]""")
    fine_blur = traits.Float(
        argstr='-fineblur %f',
        desc="""Set the blurring radius to use in the fine resolution
               pass to 'x' mm.  A small amount (1-2 mm?) of blurring at
               the fine step may help with convergence, if there is
               some problem, especially if the base volume is very noisy.
               [Default == 0 mm = no blurring at the final alignment pass]""")

    center_of_mass = traits.Str(
        argstr='-cmass%s',
        desc='Use the center-of-mass calculation to bracket the shifts.')
    autoweight = traits.Str(
        argstr='-autoweight%s',
        desc="""Compute a weight function using the 3dAutomask
               algorithm plus some blurring of the base image.""")
    automask = traits.Int(
        argstr='-automask+%d',
        desc="""Compute a mask function, set a value for dilation or 0.""")
    autobox = traits.Bool(
        argstr='-autobox',
        desc="""Expand the -automask function to enclose a rectangular
                box that holds the irregular mask.""")
    nomask = traits.Bool(
        argstr='-nomask',
        desc="""Don't compute the autoweight/mask; if -weight is not
                also used, then every voxel will be counted equally.""")
    weight_file = File(
        argstr='-weight %s', exists=True,
        desc="""Set the weighting for each voxel in the base dataset;
                larger weights mean that voxel count more in the cost function.
                Must be defined on the same grid as the base dataset""")
    out_weight_file = traits.File(
        argstr='-wtprefix %s',
        desc="""Write the weight volume to disk as a dataset""")

    source_mask = File(
        exists=True, argstr='-source_mask %s',
        desc='mask the input dataset')
    source_automask = traits.Int(
        argstr='-source_automask+%d',
        desc='Automatically mask the source dataset with dilation or 0.')
    warp_type = traits.Enum(
        'shift_only', 'shift_rotate', 'shift_rotate_scale', 'affine_general',
        argstr='-warp %s',
        desc='Set the warp type.')
    warpfreeze = traits.Bool(
        argstr='-warpfreeze',
        desc='Freeze the non-rigid body parameters after first volume.')
    replacebase = traits.Bool(
        argstr='-replacebase',
        desc="""If the source has more than one volume, then after the first
                volume is aligned to the base""")
    replacemeth = traits.Enum(
        *_cost_funcs,
        argstr='-replacemeth %s',
        desc="""After first volume is aligned, switch method for later volumes.
                For use with '-replacebase'.""")
    epi = traits.Bool(
        argstr='-EPI',
        desc="""Treat the source dataset as being composed of warped
                EPI slices, and the base as comprising anatomically
                'true' images.  Only phase-encoding direction image
                shearing and scaling will be allowed with this option.""")
    master = File(
        exists=True, argstr='-master %s',
        desc='Write the output dataset on the same grid as this file')
    newgrid = traits.Float(
        argstr='-newgrid %f',
        desc='Write the output dataset using isotropic grid spacing in mm')

    # Non-linear experimental
    _nwarp_types = ['bilinear',
                    'cubic', 'quintic', 'heptic', 'nonic',
                    'poly3', 'poly5', 'poly7',  'poly9']  # same non-hellenistic
    nwarp = traits.Enum(
        *_nwarp_types, argstr='-nwarp %s',
        desc='Experimental nonlinear warping: bilinear or legendre poly.')
    _dirs = ['X', 'Y', 'Z', 'I', 'J', 'K']
    nwarp_fixmot = traits.List(
        traits.Enum(*_dirs),
        argstr='-nwarp_fixmot%s',
        desc='To fix motion along directions.')
    nwarp_fixdep = traits.List(
        traits.Enum(*_dirs),
        argstr='-nwarp_fixdep%s',
        desc='To fix non-linear warp dependency along directions.')


class AllineateOutputSpec(TraitedSpec):
    out_file = File(desc='output image file name')
    matrix = File(desc='matrix to align input file')


class Allineate(AFNICommand):
    """Program to align one dataset (the 'source') to a base dataset

    For complete details, see the `3dAllineate Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAllineate.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> allineate = afni.Allineate()
    >>> allineate.inputs.in_file = 'functional.nii'
    >>> allineate.inputs.out_file= 'functional_allineate.nii'
    >>> allineate.inputs.matrix= 'cmatrix.mat'
    >>> res = allineate.run() # doctest: +SKIP

    """

    _cmd = '3dAllineate'
    input_spec = AllineateInputSpec
    output_spec = AllineateOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if name == 'nwarp_fixmot' or name == 'nwarp_fixdep':
            arg = ' '.join([trait_spec.argstr % v for v in value])
            return arg
        return super(Allineate, self)._format_arg(name, trait_spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                                                  suffix=self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]


class MaskaveInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dmaskave',
                   argstr='%s',
                   position=-2,
                   mandatory=True,
                   exists=True)
    out_file = File("%s_maskave.1D", desc='output image file name',
                    argstr="> %s", name_source="in_file", usedefault=True, position=-1)
    mask = File(desc='matrix to align input file',
                argstr='-mask %s',
                position=1,
                exists=True)
    quiet = traits.Bool(desc='matrix to align input file',
                        argstr='-quiet',
                        position=2)


class Maskave(AFNICommand):
    """Computes average of all voxels in the input dataset
    which satisfy the criterion in the options list

    For complete details, see the `3dmaskave Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dmaskave.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> maskave = afni.Maskave()
    >>> maskave.inputs.in_file = 'functional.nii'
    >>> maskave.inputs.mask= 'seed_mask.nii'
    >>> maskave.inputs.quiet= True
    >>> maskave.cmdline
    '3dmaskave -mask seed_mask.nii -quiet functional.nii > functional_maskave.1D'
    >>> res = maskave.run() # doctest: +SKIP

    """

    _cmd = '3dmaskave'
    input_spec = MaskaveInputSpec
    output_spec = AFNICommandOutputSpec


class SkullStripInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dSkullStrip',
                   argstr='-input %s',
                   position=1,
                   mandatory=True,
                   exists=True)
    out_file = File("%s_skullstrip", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file", usedefault=True)


class SkullStrip(AFNICommand):
    """A program to extract the brain from surrounding
    tissue from MRI T1-weighted images

    For complete details, see the `3dSkullStrip Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dSkullStrip.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> skullstrip = afni.SkullStrip()
    >>> skullstrip.inputs.in_file = 'functional.nii'
    >>> skullstrip.inputs.args = '-o_ply'
    >>> res = skullstrip.run() # doctest: +SKIP

    """
    _cmd = '3dSkullStrip'
    input_spec = SkullStripInputSpec
    output_spec = AFNICommandOutputSpec


class TCatInputSpec(AFNICommandInputSpec):
    in_files = InputMultiPath(
        File(exists=True),
        desc='input file to 3dTcat',
        argstr=' %s',
        position=-1,
        mandatory=True)
    out_file = File("%s_tcat", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file", usedefault=True)
    rlt = traits.Str(desc='options', argstr='-rlt%s', position=1)


class TCat(AFNICommand):
    """Concatenate sub-bricks from input datasets into
    one big 3D+time dataset

    For complete details, see the `3dTcat Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTcat.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> tcat = afni.TCat()
    >>> tcat.inputs.in_files = ['functional.nii', 'functional2.nii']
    >>> tcat.inputs.out_file= 'functional_tcat.nii'
    >>> tcat.inputs.rlt = '+'
    >>> res = tcat.run() # doctest: +SKIP

    """

    _cmd = '3dTcat'
    input_spec = TCatInputSpec
    output_spec = AFNICommandOutputSpec


class FimInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dfim+',
                   argstr=' -input %s',
                   position=1,
                   mandatory=True,
                   exists=True)
    out_file = File("%s_fim", desc='output image file name',
                    argstr='-bucket %s', name_source="in_file", usedefault=True)
    ideal_file = File(desc='ideal time series file name',
                      argstr='-ideal_file %s',
                      position=2,
                      mandatory=True,
                      exists=True)
    fim_thr = traits.Float(desc='fim internal mask threshold value',
                           argstr='-fim_thr %f', position=3)
    out = traits.Str(desc='Flag to output the specified parameter',
                     argstr='-out %s', position=4)


class Fim(AFNICommand):
    """Program to calculate the cross-correlation of
    an ideal reference waveform with the measured FMRI
    time series for each voxel

    For complete details, see the `3dfim+ Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dfim+.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> fim = afni.Fim()
    >>> fim.inputs.in_file = 'functional.nii'
    >>> fim.inputs.ideal_file= 'seed.1D'
    >>> fim.inputs.out_file = 'functional_corr.nii'
    >>> fim.inputs.out = 'Correlation'
    >>> fim.inputs.fim_thr = 0.0009
    >>> res = fim.run() # doctest: +SKIP

    """

    _cmd = '3dfim+'
    input_spec = FimInputSpec
    output_spec = AFNICommandOutputSpec


class TCorrelateInputSpec(AFNIBaseCommandInputSpec):
    xset = File(desc='input xset',
                argstr=' %s',
                position=-2,
                mandatory=True,
                exists=True)
    yset = File(desc='input yset',
                argstr=' %s',
                position=-1,
                mandatory=True,
                exists=True)
    out_file = File("%s_tcorr", desc='output image file name',
                    argstr='-prefix %s', name_source="xset", usedefault=True)
    pearson = traits.Bool(desc='Correlation is the normal' +
                          ' Pearson correlation coefficient',
                          argstr='-pearson',
                          position=1)
    polort = traits.Int(desc='Remove polynomical trend of order m',
                        argstr='-polort %d', position=2)


class TCorrelate(AFNIBaseCommand):
    """Computes the correlation coefficient between corresponding voxel
    time series in two input 3D+time datasets 'xset' and 'yset'

    For complete details, see the `3dTcorrelate Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTcorrelate.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> tcorrelate = afni.TCorrelate()
    >>> tcorrelate.inputs.xset= 'u_rc1s1_Template.nii'
    >>> tcorrelate.inputs.yset = 'u_rc1s2_Template.nii'
    >>> tcorrelate.inputs.out_file = 'functional_tcorrelate.nii.gz'
    >>> tcorrelate.inputs.polort = -1
    >>> tcorrelate.inputs.pearson = True
    >>> res = tcarrelate.run() # doctest: +SKIP

    """

    _cmd = '3dTcorrelate'
    input_spec = TCorrelateInputSpec
    output_spec = AFNICommandOutputSpec


class BrickStatInputSpec(AFNIBaseCommandInputSpec):
    in_file = File(desc='input file to 3dmaskave',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True)

    mask = File(desc='-mask dset = use dset as mask to include/exclude voxels',
                argstr='-mask %s',
                position=2,
                exists=True)

    min = traits.Bool(desc='print the minimum value in dataset',
                      argstr='-min',
                      position=1)


class BrickStatOutputSpec(TraitedSpec):
    min_val = traits.Float(desc='output')


class BrickStat(AFNIBaseCommand):
    """Compute maximum and/or minimum voxel values of an input dataset

    For complete details, see the `3dBrickStat Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dBrickStat.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> brickstat = afni.BrickStat()
    >>> brickstat.inputs.in_file = 'functional.nii'
    >>> brickstat.inputs.mask = 'skeleton_mask.nii.gz'
    >>> brickstat.inputs.min = True
    >>> res = brickstat.run() # doctest: +SKIP

    """
    _cmd = '3dBrickStat'
    input_spec = BrickStatInputSpec
    output_spec = BrickStatOutputSpec

    def aggregate_outputs(self, runtime=None, needed_outputs=None):

        outputs = self._outputs()

        outfile = os.path.join(os.getcwd(), 'stat_result.json')

        if runtime is None:
            try:
                min_val = load_json(outfile)['stat']
            except IOError:
                return self.run().outputs
        else:
            min_val = []
            for line in runtime.stdout.split('\n'):
                if line:
                    values = line.split()
                    if len(values) > 1:
                        min_val.append([float(val) for val in values])
                    else:
                        min_val.extend([float(val) for val in values])

            if len(min_val) == 1:
                min_val = min_val[0]
            save_json(outfile, dict(stat=min_val))
        outputs.min_val = min_val

        return outputs


class ROIStatsInputSpec(AFNIBaseCommandInputSpec):
    in_file = File(desc='input file to 3dROIstats',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True)

    mask = File(desc='input mask',
                argstr='-mask %s',
                position=3,
                exists=True)

    mask_f2short = traits.Bool(
        desc='Tells the program to convert a float mask ' +
        'to short integers, by simple rounding.',
        argstr='-mask_f2short',
        position=2)

    quiet = traits.Bool(desc='execute quietly',
                        argstr='-quiet',
                        position=1)


class ROIStatsOutputSpec(TraitedSpec):
    stats = File(desc='output', exists=True)


class ROIStats(AFNIBaseCommand):
    """Display statistics over masked regions

    For complete details, see the `3dROIstats Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dROIstats.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> roistats = afni.ROIStats()
    >>> roistats.inputs.in_file = 'functional.nii'
    >>> roistats.inputs.mask = 'skeleton_mask.nii.gz'
    >>> roistats.inputs.quiet=True
    >>> res = roistats.run() # doctest: +SKIP

    """
    _cmd = '3dROIstats'
    input_spec = ROIStatsInputSpec
    output_spec = ROIStatsOutputSpec

    def aggregate_outputs(self, runtime=None, needed_outputs=None):

        outputs = self._outputs()

        outfile = os.path.join(os.getcwd(), 'stat_result.json')

        if runtime is None:
            try:
                stats = load_json(outfile)['stat']
            except IOError:
                return self.run().outputs
        else:
            stats = []
            for line in runtime.stdout.split('\n'):
                if line:
                    values = line.split()
                    if len(values) > 1:
                        stats.append([float(val) for val in values])
                    else:
                        stats.extend([float(val) for val in values])

            if len(stats) == 1:
                stats = stats[0]
            of = os.path.join(os.getcwd(), 'TS.1D')
            f = open(of, 'w')

            for st in stats:
                f.write(str(st) + '\n')
            f.close()
            save_json(outfile, dict(stat=of))
        outputs.stats = of

        return outputs


"""
3dcalc -a ${rest}.nii.gz[${TRstart}..${TRend}] -expr 'a' -prefix $
{rest}_dr.nii.gz

3dcalc -a ${rest}_mc.nii.gz -b ${rest}_mask.nii.gz -expr 'a*b' -prefix
${rest}_ss.nii.gz
"""


class CalcInputSpec(AFNICommandInputSpec):
    in_file_a = File(desc='input file to 3dcalc',
                     argstr='-a %s', position=0, mandatory=True, exists=True)
    in_file_b = File(desc='operand file to 3dcalc',
                     argstr=' -b %s', position=1, exists=True)
    out_file = File("%s_calc", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file_a", usedefault=True)
    expr = traits.Str(desc='expr', argstr='-expr "%s"', position=2,
                      mandatory=True)
    start_idx = traits.Int(desc='start index for in_file_a',
                           requires=['stop_idx'])
    stop_idx = traits.Int(desc='stop index for in_file_a',
                          requires=['start_idx'])
    single_idx = traits.Int(desc='volume index for in_file_a')
    other = File(desc='other options', argstr='')
    suffix = traits.Str('_calc', desc="out_file suffix", usedefault=True)


class Calc(AFNICommand):
    """This program does voxel-by-voxel arithmetic on 3D datasets

    For complete details, see the `3dcalc Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dcalc.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> calc = afni.Calc()
    >>> calc.inputs.in_file_a = 'functional.nii'
    >>> calc.inputs.in_file_b = 'functional2.nii'
    >>> calc.inputs.expr='a*b'
    >>> calc.inputs.out_file =  'functional_calc.nii.gz'
    >>> calc.inputs.outputtype = "NIFTI"
    >>> calc.cmdline
    '3dcalc -a functional.nii  -b functional2.nii -expr "a*b" -prefix functional_calc.nii.gz'

    """

    _cmd = '3dcalc'
    input_spec = CalcInputSpec
    output_spec = AFNICommandOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if name == 'in_file_a':
            arg = trait_spec.argstr % value
            if isdefined(self.inputs.start_idx):
                arg += '[%d..%d]' % (self.inputs.start_idx,
                                     self.inputs.stop_idx)
            if isdefined(self.inputs.single_idx):
                arg += '[%d]' % (self.inputs.single_idx)
            return arg
        return super(Calc, self)._format_arg(name, trait_spec, value)

    def _parse_inputs(self, skip=None):
        """Skip the arguments without argstr metadata
        """
        return super(Calc, self)._parse_inputs(
            skip=('start_idx', 'stop_idx', 'other'))


class BlurInMaskInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3dSkullStrip',
        argstr='-input %s',
        position=1,
        mandatory=True,
        exists=True)
    out_file = File(
        '%s_blur',
        desc='output to the file',
        argstr='-prefix %s',
        name_source='in_file',
        position=-1,
        genfile=True)
    mask = File(
        desc='Mask dataset, if desired.  Blurring will occur only within the mask.  Voxels NOT in the mask will be set to zero in the output.',
        argstr='-mask %s')
    multimask = File(
        desc='Multi-mask dataset -- each distinct nonzero value in dataset will be treated as a separate mask for blurring purposes.',
        argstr='-Mmask %s')
    automask = traits.Bool(
        desc='Create an automask from the input dataset.',
        argstr='-automask')
    fwhm = traits.Float(
        desc='fwhm kernel size',
        argstr='-FWHM %f',
        mandatory=True)
    preserve = traits.Bool(
        desc='Normally, voxels not in the mask will be set to zero in the output.  If you want the original values in the dataset to be preserved in the output, use this option.',
        argstr='-preserve')
    float_out = traits.Bool(
        desc='Save dataset as floats, no matter what the input data type is.',
        argstr='-float')
    options = traits.Str(desc='options', argstr='%s', position=2)
    suffix = traits.Str('_blurmask', desc="out_file suffix", usedefault=True)


class BlurInMask(AFNICommand):
    """ Blurs a dataset spatially inside a mask.  That's all.  Experimental.

    For complete details, see the `3dBlurInMask Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dBlurInMask.html>

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> bim = afni.BlurInMask()
    >>> bim.inputs.in_file = 'functional.nii'
    >>> bim.inputs.mask = 'mask.nii'
    >>> bim.inputs.fwhm = 5.0
    >>> res = bim.run()   # doctest: +SKIP

    """

    _cmd = '3dBlurInMask'
    input_spec = BlurInMaskInputSpec
    output_spec = AFNICommandOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                                                  suffix=self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]


class TCorrMapInputSpec(AFNIBaseCommandInputSpec):
    in_file = File(exists=True, argstr='-input %s', mandatory=True)
    seeds = File(exists=True, argstr='-seed %s', xor=('seeds_width'))
    mask = File(exists=True, argstr='-mask %s')
    automask = traits.Bool(argstr='-automask')
    polort = traits.Int(argstr='-polort %d')
    bandpass = traits.Tuple((traits.Float(), traits.Float()),
                            argstr='-bpass %f %f')
    regress_out_timeseries = traits.File(exists=True, argstr='-ort %s')
    blur_fwhm = traits.Float(argstr='-Gblur %f')
    seeds_width = traits.Float(argstr='-Mseed %f', xor=('seeds'))

    # outputs
    mean_file = File(argstr='-Mean %s', suffix='_mean', name_source="in_file")
    zmean = File(argstr='-Zmean %s', suffix='_zmean', name_source="in_file")
    qmean = File(argstr='-Qmean %s', suffix='_qmean', name_source="in_file")
    pmean = File(argstr='-Pmean %s', suffix='_pmean', name_source="in_file")

    _thresh_opts = ('absolute_threshold',
                    'var_absolute_threshold',
                    'var_absolute_threshold_normalize')
    thresholds = traits.List(traits.Int())
    absolute_threshold = File(
        argstr='-Thresh %f %s', suffix='_thresh',
        name_source="in_file", xor=_thresh_opts)
    var_absolute_threshold = File(
        argstr='-VarThresh %f %f %f %s', suffix='_varthresh',
        name_source="in_file", xor=_thresh_opts)
    var_absolute_threshold_normalize = File(
        argstr='-VarThreshN %f %f %f %s', suffix='_varthreshn',
        name_source="in_file", xor=_thresh_opts)

    correlation_maps = File(
        argstr='-CorrMap %s', name_source="in_file")
    correlation_maps_masked = File(
        argstr='-CorrMask %s', name_source="in_file")

    _expr_opts = ('average_expr', 'average_expr_nonzero', 'sum_expr')
    expr = traits.Str()
    average_expr = File(
        argstr='-Aexpr %s %s', suffix='_aexpr',
        xor=_expr_opts)
    average_expr_nonzero = File(
        argstr='-Cexpr %s %s', suffix='_cexpr',
        xor=_expr_opts)
    sum_expr = File(
        argstr='-Sexpr %s %s', suffix='_sexpr',
        xor=_expr_opts)
    histogram_bin_numbers = traits.Int()
    histogram = File(
        argstr='-Hist %d %s', suffix='_hist')


class TCorrMapOutputSpec(TraitedSpec):

    mean_file = File()
    zmean = File()
    qmean = File()
    pmean = File()
    absolute_threshold = File()
    var_absolute_threshold = File()
    var_absolute_threshold_normalize = File()
    correlation_maps = File()
    correlation_maps_masked = File()
    average_expr = File()
    average_expr_nonzero = File()
    sum_expr = File()
    histogram = File()


class TCorrMap(AFNICommand):
    """ For each voxel time series, computes the correlation between it
    and all other voxels, and combines this set of values into the
    output dataset(s) in some way.

    For complete details, see the `3dTcorrMap Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTcorrMap.html>

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> tcm = afni.TcorrMap()
    >>> tcm.inputs.in_file = 'functional.nii'
    >>> tcm.inputs.mask = 'mask.nii'
    >>> tcm.mean_file = '%s_meancorr.nii'
    >>> res = tcm.run()   # doctest: +SKIP

    """

    _cmd = '3dTcorrMap'
    input_spec = TCorrMapInputSpec
    output_spec = TCorrMapOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if name in self.inputs._thresh_opts:
            return trait_spec.argstr % self.inputs.thresholds + [value]
        elif name in self.inputs._expr_opts:
            return trait_spec.argstr % (self.inputs.expr, value)
        else:
            return super(TCorrMap, self)._format_arg(name, trait_spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for o in self._outputs().get().keys():
            ov = getattr(self.inputs, o)
            if not isdefined(ov):
                ov = self._gen_fname(
                    o, suffix=self.input_spec.class_traits()[o].suffix)
            outputs[o] = ov
        return outputs

    def _parse_inputs(self, skip=None):
        outs = self._list_outputs()
        # skip under
        if skip == None:
            skip = []
        skip.extend([k for k in self._outputs()
                    .get().keys() if not isdefined(outs[k])])
        return super(TCorrMap, self)._parse_inputs(skip=skip)

    def _gen_filename(self, name):
        if hasattr(self.inputs, name) and \
                not isdefined(getattr(self.inputs, name)):
            return Undefined
        return super(TCorrMap, self)._gen_filename(name)


class AutoboxInputSpec(AFNICommandInputSpec):
    in_file = File(exists=True, mandatory=True, argstr='-input %s',
                   desc='input file')
    padding = traits.Int(
        argstr='-npad %d',
        desc='Number of extra voxels to pad on each side of box')
    out_file = File(argstr="-prefix %s", name_source="in_file")
    no_clustering = traits.Bool(
        argstr='-noclust',
        desc="""Don't do any clustering to find box. Any non-zero
                voxel will be preserved in the cropped volume.
                The default method uses some clustering to find the
                cropping box, and will clip off small isolated blobs.""")


class AutoboxOuputSpec(TraitedSpec):  # out_file not mandatory
    x_min = traits.Int()
    x_max = traits.Int()
    y_min = traits.Int()
    y_max = traits.Int()
    z_min = traits.Int()
    z_max = traits.Int()

    out_file = File(desc='output file')


class Autobox(AFNICommand):
    """ Computes size of a box that fits around the volume.
    Also can be used to crop the volume to that box.

    For complete details, see the `3dAutobox Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAutobox.html>

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> abox = afni.Autobox()
    >>> abox.inputs.in_file = 'structural.nii'
    >>> abox.inputs.padding = 5
    >>> res = abox.run()   # doctest: +SKIP

    """

    _cmd = '3dAutobox'
    input_spec = AutoboxInputSpec
    output_spec = AutoboxOuputSpec

    def aggregate_outputs(self, runtime=None, needed_outputs=None):
        outputs = self._outputs()
        pattern = 'x=(?P<x_min>-?\d+)\.\.(?P<x_max>-?\d+)  y=(?P<y_min>-?\d+)\.\.(?P<y_max>-?\d+)  z=(?P<z_min>-?\d+)\.\.(?P<z_max>-?\d+)'
        for line in runtime.stderr.split('\n'):
            m = re.search(pattern, line)
            if m:
                d = m.groupdict()
                for k in d.keys():
                    d[k] = int(d[k])
                outputs.set(**d)
        outputs.set(out_file=self._gen_filename('out_file'))
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file' and (not isdefined(self.inputs.out_file)):
            return Undefined
        return super(Autobox, self)._gen_filename(name)
