# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft = python sts = 4 ts = 4 sw = 4 et:
"""Afni preprocessing interfaces

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""
import string
import os
import re
import warnings

from .base import AFNICommandInputSpec, AFNICommand
from ..base import (Directory, CommandLineInputSpec, CommandLine, TraitedSpec, traits,
                    isdefined, File, InputMultiPath, DynamicTraitedSpec)
from nipype.interfaces.io import add_traits
from ...utils.filemanip import (load_json, save_json, split_filename)
from nipype.utils.filemanip import fname_presuffix

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class To3DInputSpec(AFNICommandInputSpec):
    prefix = traits.File(argstr='-prefix %s', mandatory=False, genfile=True, hash_file=False,
                         desc='Output file prefix')
    suffix = traits.Str(argstr='%s', mandatory=False, desc='Output file suffix')
    infolder = Directory(desc='folder with DICOM images to convert', argstr='%s/*.dcm',
                         position=-1, mandatory=True, exists=True)
    filetype = traits.Enum('spgr', 'fse', 'epan', 'anat', 'ct', 'spct', 'pet', 'mra',
                           'bmap', 'diff', 'omri', 'abuc', 'fim', 'fith', 'fico', 'fitt',
                           'fift', 'fizt', 'fict', 'fibt', 'fibn', 'figt', 'fipt', 'fbuc',
                           argstr='-%s', mandatory=True, usedefault=False,
                           desc='declare images to contain data of a given type')
    skipoutliers = traits.Bool(argstr='-skip_outliers', desc='Tells the program to skip the \
    outlier check that is automatically performed for 3D+time datasets.  You can also turn \
    this feature off by setting the environment variable AFNI_TO3D_OUTLIERS to "No"')
    assume_dicom_mosaic = traits.Bool(argstr='-assume_dicom_mosaic',
                                      desc='If present, this tells the program that any \
    Siemens DICOM file is a potential MOSAIC image, even without the indicator string')
    datum = traits.Enum('short', 'float', 'byte', 'complex', argstr='-datum %s',
                        mandatory=True, usedefault=False, desc='Set the voxel data type. \
    If -datum is not used, then the datum type of the first input image will determine \
    what is used.  In that case, the first input image will determine the type as follows:\n\
    \tbyte\t\t--> byte\n\
    \tshort\t\t--> short\n\
    \tint, float\t--> float\n\
    \tcomplex\t\t--> complex\n\
    If -datum IS specified (mandatory for Nipype), then all input images will be \
    converted to the desired type.  Note that the list of allowed types may grow in the \
    future, so you should not rely on the automatic conversion scheme.  Also note that \
    floating point datasets may not be portable between CPU architecturesset output file \
    datatype')
    orient = traits.Str(argstr='%s', desc='Tells the orientation of the 3D volumes.  The \
    code must be 3 letters, one each from the pairs {R,L} {A,P} {I,S}.  The first letter \
    gives the orientation of the x-axis, the second the orientation of the y-axis, the \
    third the z-axis: \n\
    \tR = right-to-left \t\t L = left-to-right\n\
    \tA = anterior-to-posterior \t\t P = posterior-to-anterior\n\
    \tI = inferior-to-superior \t\t S = superior-to-inferior\n\
    Note that the -xFOV, -zSLAB constructions can convey this information.')
    funcparams = traits.Str(argstr='-time:zt %s alt+z2', desc='parameters for functional data')


class To3DOutputSpec(TraitedSpec):
    out_file = File(desc='converted file')


class To3D(AFNICommand):
    """
    Create a 3D dataset from 2D image files using AFNI to3d command

    For complete details, see the `to3d Documentation
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/to3d.html>`_

    Examples
    ========

    >>> import os.path as path
    >>> from nipype.interfaces import afni
    >>> from nipype.testing import basedir
    >>> To3D = afni.To3D()
    >>> To3D.inputs.datum = 'float'
    >>> To3D.inputs.infolder = path.join(basedir, 'data')
    >>> To3D.inputs.filetype = 'anat'
    >>> To3D.inputs.orient = 'RAS'
    >>> To3D.inputs.funcparams = '-time:zt %s alt+z2'
    >>> res = To3D.run() #doctest: +SKIP

   """
    _cmd = 'to3d'
    input_spec = To3DInputSpec
    output_spec = To3DOutputSpec

    def _format_arg(self, opt, spec, val):
        if opt == 'orient':
            rl = set(['R','L'])
            ap = set(['A','P'])
            si = set(['S','I'])
            if len(val) == 3 and rl.intersection(val[0].upper()) and \
              ap.intersection(val[1].upper()) and si.intersection(val[2].upper()):
              return "-orient %s" % val.upper()
            else:
                raise ValueError("Invalid orient flag for AFNI's To3D() node: %s" % val.upper())
        elif opt == 'infolder':
            return os.path.join(self.inputs.infolder, '*.dcm')
        return super(To3D, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        self.inputs.outputtype = 'AFNI'
        outputs['out_file'] = self._gen_fname(basename=self.inputs.prefix,
                                              suffix='')
        return outputs


class TShiftInputSpec(AFNICommandInputSpec):
    in_file = File(argstr='%s', position=-1, mandatory=True, exists=True,
                   desc='input file to 3dTShift')
    prefix = File(argstr='-prefix %s', position=0, genfile=True, hash_files=False,
                    desc='output file from 3dTshift')
    tr = traits.Str(argstr='-TR %s', desc='manually set the TR. You can attach suffix \
    "s" for seconds or "ms" for milliseconds.')
    tzero = traits.Float(argstr='-tzero %s', xor=['tslice'],
                         desc='align each slice to given time offset',)
    tslice = traits.Int(argstr='-slice %s', xor=['tzero'],
                        desc='align each slice to time offset of given slice')
    ignore = traits.Int(argstr='-ignore %s',
                        desc='ignore the first set of points specified')
    interp = traits.Enum('Fourier', 'linear', 'cubic', 'quintic', 'heptic', argstr='-%s',
                         usedefault=True, desc='different interpolation methods (see \
                         3dTShift for details) default = Fourier')
    tpattern = traits.Enum('alt+z', 'alt+z2', 'alt-z', 'alt-z2', 'seq+z', 'seq-z',
                           argstr='-tpattern %s',
                           desc='use specified slice time pattern rather than one in header')
    rlt = traits.Bool(argstr="-rlt",
                      desc='Before shifting, remove the mean and linear trend')
    rltplus = traits.Bool(argstr="-rlt+",
                          desc='Before shifting, remove the mean and linear trend and \
    later put back the mean')
    suffix = traits.Str(argstr='%s', default='_tshift', mandatory=False,
                        desc='Output file suffix')

class TShiftOutputSpec(TraitedSpec):
    out_file = File(desc='post slice time shifted 4D image')


class TShift(AFNICommand):
    """
    Shifts voxel time series from input so that seperate slices are aligned to the same
    temporal origin

    For complete details, see the `3dTshift Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTshift.html>

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import example_data
    >>> tshift = afni.TShift()
    >>> tshift.inputs.in_file = example_data('functional.nii')
    >>> tshift.inputs.prefix = 'functional_tshift.nii'
    >>> tshift.inputs.tpattern = 'alt+z'
    >>> tshift.inputs.tzero = 0.0
    >>> res = tshift.run()   # doctest: +SKIP

    """

    _cmd = '3dTshift'
    input_spec = TShiftInputSpec
    output_spec = TShiftOutputSpec

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                suffix = self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class RefitInputSpec(AFNICommandInputSpec):
    """
    3drefit writes over the data generated by To3D(), so we need to copy the input file
    (and it's .HEAD file) and use the copy as the input
    """
    in_file = File(desc='input file to 3drefit', argstr='%s', position=-1, mandatory=True,
                   exists=True, copyfile=True)
    deoblique = traits.Bool(argstr='-deoblique',
                            desc='replace current transformation matrix with cardinal matrix')
    xorigin = traits.Str(argstr='-xorigin %s', desc='x distance for edge voxel offset')
    yorigin = traits.Str(argstr='-yorigin %s', desc='y distance for edge voxel offset')
    zorigin = traits.Str(argstr='-zorigin %s', desc='z distance for edge voxel offset')


class RefitOutputSpec(TraitedSpec):
    out_file = File(desc='Same file as original in_file with modified matrix',
                    exists=True)


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

    NOTE: If the previous node is To3D(), the outputtype MUST be 'AFNI'
    """
    _cmd = '3drefit'
    input_spec = RefitInputSpec
    output_spec = RefitOutputSpec

    # def _format_arg(self, opt, spec, val):
    #     if opt == 'in_file':
    #         return self._gen_fname(val, suffix='_refit')

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.in_file
        return outputs


class WarpInputSpec(AFNICommandInputSpec):

    in_file = File(desc='input file to 3dWarp',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)

    out_file = File(desc='output file from 3dWarp',
        argstr='-prefix %s',
        position=0,
        genfile=True,
        hash_files=False)

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

    suffix = traits.Str('_warp',desc="out_file suffix",usedefault=True)

class WarpOutputSpec(TraitedSpec):
    out_file = File(desc='spatially transformed input image')


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
    output_spec = WarpOutputSpec

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                suffix = self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class ResampleInputSpec(AFNICommandInputSpec):

    in_file = File(desc='input file to 3dresample',
        argstr='-inset %s',
        position=-1,
        mandatory=True,
        exists=True)

    out_file = File(desc='output file from 3dresample',
        argstr='-prefix %s',
        position=-2,
        genfile=True,
        hash_files=False)

    orientation = traits.Str(desc='new orientation code',
        argstr='-orient %s')

    suffix = traits.Str('_resample', desc="out_file suffix",usedefault=True)


class ResampleOutputSpec(TraitedSpec):
    out_file = File(desc='reoriented or resampled file')


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
    output_spec = ResampleOutputSpec

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                suffix = self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class TStatInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dTstat', argstr='%s', position=-1, mandatory=True, exists=True)
    out_file = File(desc='output file from 3dTstat', argstr='-prefix %s', position=-2, genfile=True, hash_files=False)
    mask_file = File(desc='use the dataset "mset" as a mask', argstr='-mask %s', exists=True)
    suffix = traits.Str('_tstat', desc="out_file suffix", usedefault=True)


class TStatOutputSpec(TraitedSpec):
    out_file = File(desc='statistical file')


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
    output_spec = TStatOutputSpec

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                suffix = self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class DetrendInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dDetrend',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)
    out_file = File(desc='output file from 3dDetrend',
         argstr='-prefix %s',
         position=-2,
         genfile=True,
         hash_files=False)
    suffix = traits.Str('_detrend', desc="out_file suffix", usedefault=True)


class DetrendOutputSpec(TraitedSpec):
    out_file = File(desc='statistical file')


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
    output_spec = DetrendOutputSpec

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            basename = self.inputs.in_file
        else:
            basename = self.inputs.out_file
        outputs['out_file'] = self._gen_fname(basename=basename,
                suffix=self.inputs.suffix)
        return outputs


class DespikeInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dDespike', argstr='%s', position=-1,
                   mandatory=True, exists=True)
    out_file = File(desc='output file from 3dDespike', argstr='-prefix %s',
         position=-2, genfile=True, hash_files=False)
    suffix = traits.Str('_despike', desc="out_file suffix", usedefault=True)
    ignore = traits.Int(desc='Number of volumes to skip in the analysis',
                        argstr='-ignore %d')
    start = traits.Int(mandatory=False, requires=['end'],
                       desc='The first of timepoint volumes to include in the output, \
    Ex. "4" would include the fifth timepoint volume')
    end = traits.Int(mandatory=False, requires=['start'],
                     desc='The last of timepoint volumes to include in the output, \
    Ex. "99" would include the 100th timepoint volume')


class DespikeOutputSpec(TraitedSpec):
    out_file = File(desc='despiked img')


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
    output_spec = DespikeOutputSpec

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None

    def _format_arg(self, opt, spec, val):
        if opt == 'in_file':
            if isdefined(self.inputs.start):
                return "%s'[%d..%d]'" % (self.inputs.in_file, self.inputs.start, self.inputs.end)
            return '%s' % (self.inputs.in_file)
        return super(Despike, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                suffix = self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class AutomaskInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dAutomask',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)

    out_file = File(desc='output file from 3dAutomask (a brain mask)',
        argstr='-prefix %s',
        position=-2,
        genfile=True,
        hash_files=False)

    apply_mask = File(desc="output file from 3dAutomask",
                      argstr='-apply_prefix %s',
                      genfile=True,
                      hash_files=False)

    clfrac = traits.Float(desc='sets the clip level fraction' +
        ' (must be 0.1-0.9). ' +
        'A small value will tend to make the mask larger [default = 0.5].',
        argstr="-dilate %s")

    dilate = traits.Int(desc='dilate the mask outwards',
        argstr="-dilate %s")

    erode = traits.Int(desc='erode the mask inwards',
        argstr="-erode %s")

    mask_suffix = traits.Str('_mask',desc="out_file suffix",usedefault=True)
    apply_suffix = traits.Str('_masked',desc="out_file suffix",usedefault=True)



class AutomaskOutputSpec(TraitedSpec):
    out_file = File(desc='mask file')
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
    >>> res = automask.run() # doctest: +SKIP

    """

    _cmd = '3dAutomask'
    input_spec = AutomaskInputSpec
    output_spec = AutomaskOutputSpec

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        if name == 'apply_mask':
            return self._list_outputs()['brain_file']
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(
                self.inputs.in_file, suffix=self.inputs.mask_suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)

        if not isdefined(self.inputs.apply_mask):
            outputs['brain_file'] = self._gen_fname(self.inputs.in_file,
                                                suffix=self.inputs.apply_suffix)
        else:
            outputs['brain_file'] = os.path.abspath(self.inputs.apply_mask)
        return outputs


class VolregInputSpec(AFNICommandInputSpec):
    """

    """
    in_file = File(desc='input file to 3dvolreg', argstr='%s', position=-1,
                   mandatory=True, exists=True)
    out_file = File(desc='output file from 3dvolreg', argstr='-prefix %s', position=-2,
                    genfile=True, hash_files=False)
    basefile = File(desc='base file for registration', argstr='-base %s', position=-6,
                    exists=True)
    zpad = traits.Int(desc='Zeropad around the edges by "n" voxels during rotations',
                      argstr='-zpad %d', position=-5)
    md1dfile = File(desc='max displacement output file', argstr='-maxdisp1D %s',
                    position=-4)
    oned_file = File(desc='1D movement parameters output file', argstr='-1Dfile %s',
                     position=-3, genfile=True, hash_files=False)
    verbose = traits.Bool(desc='more detailed description of the process',
                          argstr='-verbose')
    timeshift = traits.Bool(desc='time shift to mean slice time offset',
                            argstr='-tshift 0')
    copyorigin = traits.Bool(desc='copy base file origin coords to output',
                             argstr='-twodup')
    suffix = traits.Str('_volreg', desc="out_file suffix", usedefault=True)
    interp = traits.Enum('Fourier', 'hepatic', 'cubic', 'quintic', argstr='-%s',
                         desc='Interpolation to use for alignments')
    final = traits.Enum('Fourier', 'hepatic', 'cubic', 'quintic', 'NN', argstr='-%s',
                         desc='Interpolation to use for fianl alignment',
                         requires=['interp'], usedefault=False)
    maxite = traits.Int(19, desc="Allow up to 'm' iterations for convergence",
                        argstr='-maxite %d')
    thresh = traits.Float(0.02, desc="Iterations converge when maximum movement is \
                          less than 'x' voxels", argstr='-x_thresh %g')
    rot_thresh = traits.Float(0.03, desc="Iterations converge when maximum rotation \
                              is less than 'r' degrees", argstr='-rot_thresh %g')
    delta = traits.Float(0.7, desc='Distance, in voxel size, used to compute image \
                         derivatives using finite differences', argstr='-delta %g')
    twopass = traits.Bool(argstr='-twopass', desc="\
    Do two passes of the registration algorithm: \n\
    \t(1) with smoothed base and data bricks, with linear interpolation, then\n\
    \t(2) with the input base and data bricks, to get a fine alignment.\n\
    This method is useful when aligning high-resolution datasets that may need to be \
    moved more than a few voxels to be aligned.")
    twodup = traits.Bool(argstr='-twodup', requires=['twopass'], desc="If True, then the \
    output dataset will have its xyz-axes origins reset to those of the base dataset.  \
    This is equivalent to using '3drefit -duporigin' on the output.")
    coarse = traits.List([traits.Int(default=10), traits.Int(default=2, max=4)], minlen=2,
                         maxlen=2, argstr='%s', desc="coarse.[0] is the size of shift \
    steps, in voxels; \n\tcoarse.[1] is the number of these steps along each direction.  \
    The default values are 10 and 2, respectively.  If you don't want this step performed, \
    set coarse.[1] == 0.\nNote that the amount of computation grows as coarse.[1]**3\n\
    N.B.: The first parameter cannot be larger than 10% of the smallest dimension of the \
    input dataset.")
    coarserot = traits.Bool(argstr='-coarserot', desc='Do a coarse rotational search before\
    the initial registration')
    base = traits.Either(traits.Int(0, argstr='-base %d'),
                         traits.Str(argstr="-base '%s'"), desc='') # TODO: Format string to 'bset[n]'


class VolregOutputSpec(TraitedSpec):
    out_file = File(desc='registered file')
    md1d_file = File(desc='max displacement info file')
    oned_file = File(desc='movement parameters info file')


class Volreg(AFNICommand):
    """Register input volumes to a base volume using AFNI 3dvolreg command

    For complete details, see the `3dvolreg Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dvolreg.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> volreg = afni.Volreg()
    >>> volreg.inputs.in_file = example_data('functional.nii')
    >>> volreg.inputs.interp = 'quintic'
    >>> volreg.inputs.final = 'Fourier'
    >>> volreg.inputs.twopass = True
    >>> volreg.inputs.zpad = 4
    >>> res = volreg.run() # doctest: +SKIP

    """

    _cmd = '3dvolreg'
    input_spec = VolregInputSpec
    output_spec = VolregOutputSpec

    def _format_arg(self, opt, spec, val):
        if opt == 'coarse':
            return '-coarse %d %d' % (self.inputs.coarse[0], self.inputs.coarse[1])
        return super(Volreg, self)._format_arg(opt, spec, val)

    def _gen_filename(self, name):
        if name == 'out_file' or name == 'oned_file':
            return self._list_outputs()[name]

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                                                     suffix=self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        if not isdefined(self.inputs.oned_file): # TODO: check for '.1D' extension
            outputs['oned_file'] = self._gen_fname(self.inputs.in_file,
                                            suffix = '%s.1D' % self.inputs.suffix)
        else:
            outputs['oned_file'] = os.path.abspath(self.inputs.oned_file)
        return outputs


class MergeInputSpec(AFNICommandInputSpec):
    in_files = InputMultiPath(
        File(desc='input file to 3dmerge', exists=True),
        argstr='%s',
        position=-1,
        mandatory=True)
    out_file = File(desc='output file from 3dmerge',
         argstr='-prefix %s',
         position=-2,
         genfile=True,
         hash_files=False)
    doall = traits.Bool(desc='apply options to all sub-bricks in dataset',
        argstr='-doall')
    blurfwhm = traits.Float(desc='FWHM blur value (mm)',
          argstr='-1blur_fwhm %g',
          units='mm')
    suffix = traits.Str('_merge', desc="out_file suffix", usedefault=True)


class MergeOutputSpec(TraitedSpec):
    out_file = File(desc='smoothed file')


class Merge(AFNICommand):
    """Merge or edit volumes using AFNI 3dmerge command

    For complete details, see the `3dmerge Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dmerge.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import example_data
    >>> merge = afni.Merge()
    >>> merge.inputs.in_files = example_data('functional.nii')
    >>> merge.inputs.blurfwhm = 4.0
    >>> merge.inputs.doall = True
    >>> merge.inputs.out_file = 'e7.nii'
    >>> res = merge.run() # doctest: +SKIP

    """

    _cmd = '3dmerge'
    input_spec = MergeInputSpec
    output_spec = MergeOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_files[0],
                                                  suffix=self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]


class CopyInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dcopy',
        argstr='%s',
        position=-2,
        mandatory=True,
        exists=True)
    out_file = File(desc='output file from 3dcopy',
        argstr='%s',
        position=-1,
        genfile=True,
        hash_files=False)
    suffix = traits.Str('_copy', desc="out_file suffix", usedefault=True)


class CopyOutputSpec(TraitedSpec):
    out_file = File(desc='copied file')


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
    output_spec = CopyOutputSpec

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


class FourierInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dFourier',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)
    out_file = File(desc='output file from 3dFourier',
         argstr='-prefix %s',
         position=2, #-2,
         genfile=True,
         hash_files=False)
    lowpass = traits.Float(desc='lowpass',
        argstr='-lowpass %f',
        position=0,
        mandatory=True)
    highpass = traits.Float(desc='highpass',
        argstr='-highpass %f',
        position=1,
        mandatory=True)
    suffix = traits.Str('_fourier', desc="out_file suffix", usedefault=True)


class FourierOutputSpec(TraitedSpec):
    out_file = File(desc='band-pass filtered file')


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
    output_spec = FourierOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                suffix = self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None


class ZCutUpInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dZcutup',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)
    out_file = File(desc='output file from 3dZcutup',
         argstr='-prefix %s',
         position=-2,
         mandatory=True,
         hash_files=False)
    keep = traits.Str(desc='slice range to keep in output',
            argstr='-keep %s')
    suffix = traits.Str('_zcutup', desc="out_file suffix", usedefault=True)


class ZCutUpOutputSpec(TraitedSpec):
    out_file = File(desc='cut file')


class ZCutUp(AFNICommand):
    """Cut z-slices from a volume using AFNI 3dZcutup command

    For complete details, see the `3dZcutup Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dZcutup.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import example_data
    >>> zcutup = afni.ZCutUp()
    >>> zcutup.inputs.in_file = example_data('functional.nii')
    >>> zcutup.inputs.out_file = 'functional_zcutup.nii'
    >>> zcutup.inputs.keep = '0 10'
    >>> res = zcutup.run() # doctest: +SKIP

    """

    _cmd = '3dZcutup'
    input_spec = ZCutUpInputSpec
    output_spec = ZCutUpOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                suffix = self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]


class AllineateInputSpec(AFNICommandInputSpec):
    base_file = File(desc='target file to register in_file to', argstr='-base %s',
                     mandatory=False, exists=True)
    master_file = File(desc='grid space file to write the out_file to',
                     argstr='-master %s', mandatory=False, exists=True)
    in_file = File(desc='input file to 3dAllineate', argstr='-source %s',
                   position=-1, mandatory=True, exists=True)
    out_file = File(desc='output file from 3dAllineate', argstr='-prefix %s',
                    position=-2, hash_files=False)
    onedmatrix = File(desc='1D matrix to align input file', argstr='-1Dmatrix_apply %s',
                      position=-3, exists=True)
    suffix = traits.Str('_allineate', desc="out_file suffix", usedefault=True)
    warp = traits.Enum('affine_general', 'shift_rotate_scale', 'shift_rotate',
                       'shift_only', argstr='-warp %s', usedefault=True)
    cost = traits.Enum('hellinger', 'corratio_uns', 'corratio_add', 'norm_mutualinfo',
                       'corration_mul', 'mutualinfo', 'leastsq', argstr='-cost %s',
                       usedefault=True)
    cmass = traits.Bool(default=False, argstr='-cmass')
    interp = traits.Enum('trilinear', 'nearestneighbor', 'tricubic', 'triquintic',
                         argstr='-interp %s', usedefault=True)
    final = traits.Enum('tricubic', 'nearestneighbor', 'trilinear', 'triquintic', 'wsinc5',
                        argstr='-final %s', usedefault=True)
    onedmatrix_save = traits.Bool(default=False, argstr='%s', usedefault=True)


class AllineateOutputSpec(TraitedSpec):
    out_file = File(desc='cut file')
    onedmatrix_out = File(desc='output file from -1Dmatrix_save')


class Allineate(AFNICommand):
    """Program to align one dataset (the 'source') to a base dataset

    For complete details, see the `3dAllineate Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAllineate.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> allineate = afni.Allineate()
    >>> allineate.inputs.in_file = example_data('functional.nii')
    >>> allineate.inputs.out_file = 'functional_allineate.nii'
    >>> allineate.inputs.onedmatrix = example_data('cmatrix.mat')
    >>> allineate.inputs.onedmatrix_save = True # doctest: +SKIP
    >>> res = allineate.run() # doctest: +SKIP

    """

    _cmd = '3dAllineate'
    input_spec = AllineateInputSpec
    output_spec = AllineateOutputSpec

    def _format_arg(self, opt, spec, val):
        if opt == 'onedmatrix_save':
            if self.inputs.onedmatrix_save:
                return '-1Dmatrix_save %s' % self.gen_oned_filename(self.inputs.in_file)
            else:
                return ''
        elif opt == 'suffix':
            return ''
        return super(Allineate, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                                                  suffix=self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        if self.inputs.onedmatrix_save:
            outputs['onedmatrix_out'] = self.gen_oned_filename(self.inputs.in_file)
        return outputs

    def gen_oned_filename(self, baseInput):
        oneDname = []
        fName = self._gen_fname(baseInput, suffix=self.inputs.suffix)
        parts = fName.split('.')
        for part in parts[0:-1]:
            oneDname.append(part)
        oneDname.append('aff12.1D')
        return '.'.join(oneDname)


class MaskaveInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dmaskave',
        argstr='%s',
        position=-2,
        mandatory=True,
        exists=True)
    out_file = File(desc='output to the file',
                    argstr='> %s', # Overwrites class def
                    position=-1,
                    genfile=True,
                    hash_files=False)
    mask = File(desc='matrix to align input file',
        argstr='-mask %s',
        position=1,
        exists=True)

    quiet = traits.Bool(desc='matrix to align input file',
        argstr='-quiet',
        position=2)
    suffix = traits.Str('_maskave', desc="out_file suffix", usedefault=True)


class MaskaveOutputSpec(TraitedSpec):
    out_file = File(desc='outfile')


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
    >>> maskave.inputs.out_file= 'maskave.1D'
    >>> res = maskave.run() # doctest: +SKIP

    """

    _cmd = '3dmaskave'
    input_spec = MaskaveInputSpec
    output_spec = MaskaveOutputSpec


    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                suffix = self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]

class SkullStripInputSpec(AFNICommandInputSpec):
    in_file = File(argstr='-input %s', position=1, mandatory=True, exists=True,
                   desc='input file to 3dSkullStrip')
    out_file = File(argstr='%s', position=-1, genfile=True, hash_files=False,
                    desc='output to the file')
    suffix = traits.Str('_skullstrip', desc="out_file suffix", usedefault=True)


class SkullStripOutputSpec(TraitedSpec):
    out_file = File(desc='outfile')


class SkullStrip(AFNICommand):
    """A program to extract the brain from surrounding
    tissue from MRI T1-weighted images

    For complete details, see the `3dSkullStrip Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dSkullStrip.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import example_data
    >>> skullstrip = afni.SkullStrip()
    >>> skullstrip.inputs.in_file = example_data('functional.nii')
    >>> skullstrip.inputs.args = '-o_ply'
    >>> skullstrip.inputs.out_file = 'benchmark'
    >>> res = skullstrip.run() # doctest: +SKIP

    """
    _cmd = '3dSkullStrip'
    input_spec = SkullStripInputSpec
    output_spec = SkullStripOutputSpec


    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                suffix = self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]


class TCatInputSpec(AFNICommandInputSpec):
    in_files = InputMultiPath(File(exists=True), argstr=' %s', position=-1,
                              mandatory=True, desc='input file to 3dTcat')
    out_file = File(argstr='-prefix %s', position=-2, genfile=True,
                    hash_files=False, desc='output to the file')
    rlt = traits.Str(desc='options', argstr='-rlt%s', position=1)
    suffix = traits.Str('_tcat', desc="out_file suffix", usedefault=True)


class TCatOutputSpec(TraitedSpec):
    out_file = File(desc='outfile')


class TCat(AFNICommand):
    """Concatenate sub-bricks from input datasets into
    one big 3D+time dataset

    For complete details, see the `3dTcat Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTcat.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import example_data
    >>> tcat = afni.TCat()
    >>> tcat.inputs.in_files = example_data('functional.nii')
    >>> tcat.inputs.out_file = 'functional_tcat.nii'
    >>> tcat.inputs.rlt = '+'
    >>> res = tcat.run() # doctest: +SKIP

    """

    _cmd = '3dTcat'
    input_spec = TCatInputSpec
    output_spec = TCatOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_files[0],
                                                  suffix=self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]


class FimInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dfim+',
        argstr=' -input %s',
        position=1,
        mandatory=True,
        exists=True)
    ideal_file = File(desc='ideal time series file name',
        argstr='-ideal_file %s',
        position=2,
        mandatory=True,
        exists=True)
    fim_thr = traits.Float(desc='fim internal mask threshold value',
        argstr='-fim_thr %f', position=3)

    out = traits.Str(desc='Flag to output the specified parameter',
        argstr='-out %s', position=4)

    out_file = File(desc='output file from 3dfim+',
                    argstr='-bucket %s', # Overwrites class def
                    position=-1,
                    genfile=True,
                    hash_files=False)
    suffix = traits.Str('_fim', desc="out_file suffix", usedefault=True)


class FimOutputSpec(TraitedSpec):
    out_file = File(desc='outfile')


class Fim(AFNICommand):
    """Program to calculate the cross-correlation of
    an ideal reference waveform with the measured FMRI
    time series for each voxel

    For complete details, see the `3dfim+ Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dfim+.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import example_data
    >>> fim = afni.Fim()
    >>> fim.inputs.in_file = example_data('functional.nii')
    >>> fim.inputs.ideal_file = example_data('seed.1D') #doctest: +SKIP
    >>> fim.inputs.out_file = 'functional_corr.nii'
    >>> fim.inputs.out = 'Correlation'
    >>> fim.inputs.fim_thr = 0.0009
    >>> res = fim.run() # doctest: +SKIP

    """

    _cmd = '3dfim+'
    input_spec = FimInputSpec
    output_spec = FimOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                suffix = self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]


class TCorrelateInputSpec(AFNICommandInputSpec):
    xset = File(argstr='%s', position=-2, mandatory=True, exists=True, desc='input xset')
    yset = File(argstr='%s', position=-1, mandatory=True, exists=True, desc='input yset')
    correlation = traits.Enum('pearson', 'spearman', 'quadrant', 'ktaub', argstr='-%s', usedefault=True,
                              position=1, desc='Correlation is "pearson", "spearman", "quadrant", or "ktaub"')
    covariance = traits.Bool(default=False, usedefault=True, xor=['correlation'], argstr='-covariance',
                             desc='Use covariance instead of correlation')
    polort = traits.Int(argstr='-polort %d', position=2, desc='Remove polynomical trend of order m')
    prefix = File(argstr='-prefix %s', position=3, genfile=True, hash_files=False,
                  desc='Save output into dataset with prefix')
    suffix = traits.Str('_tcor', desc="out_file suffix", usedefault=True)


class TCorrelateOutputSpec(TraitedSpec):
    out_file = File(desc='outfile')


class TCorrelate(AFNICommand):
    """Computes the correlation coefficient between corresponding voxel
    time series in two input 3D+time datasets 'xset' and 'yset'

    For complete details, see the `3dTcorrelate Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTcorrelate.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> tcorrelate = afni.TCorrelate()
    >>> tcorrelate.inputs.xset= example_data('u_rc1s1_Template.nii')
    >>> tcorrelate.inputs.yset = example_data('u_rc1s2_Template.nii')
    >>> tcorrelate.inputs.prefix = 'functional_tcorrelate.nii.gz'
    >>> tcorrelate.inputs.polort = -1
    >>> tcorrelate.inputs.correlation = 'pearson'
    >>> res = tcarrelate.run() # doctest: +SKIP

    """

    _cmd = '3dTcorrelate'
    input_spec = TCorrelateInputSpec
    output_spec = TCorrelateOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.xset,
                                                  suffix=self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]


class BrickStatInputSpec(AFNICommandInputSpec):
    ### TODO: Doesn't use out_file!
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


class BrickStat(AFNICommand):
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


class ROIStatsInputSpec(AFNICommandInputSpec):
    # TODO: Doesn't use out_file
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
    stats = File(desc='output')


class ROIStats(AFNICommand):
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

    def _format_arg(self, opt, spec, val):
        if opt == 'in_file':
            outputs = self._list_outputs()
            return '%s>%s' % (self.inputs.in_file, outputs['stats'])
        return super(ROIStats, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['stats'] = self._gen_fname(basename=self.inputs.in_file, suffix='roiStat')
        return outputs

class CalcInputSpec(DynamicTraitedSpec, AFNICommandInputSpec):
    in_file_a = File(position=0,argstr='-a %s', mandatory=True, exists=True)
    in_file_b = File(position=1,argstr='-b %s', mandatory=True, exists=True)
    in_file_c = File(position=2,argstr='-c %s', mandatory=False, exists=True)
    expr = traits.Str(desc='expr', argstr="-expr '%s'", mandatory=True)
    out_file = File(desc='output file from 3dFourier', argstr='-prefix %s',
        position=-1, genfile=True)
    start_idx = traits.Int(desc='start index for in_file_a',
        requires=['stop_idx'])
    stop_idx = traits.Int(desc='stop index for in_file_a',
        requires=['start_idx'])
    single_idx = traits.Int(desc='volume index for in_file_a')
    suffix = traits.Str('_calc', desc="out_file suffix", usedefault=True)


class CalcOutputSpec(TraitedSpec):
    out_file = File(desc=' output file')


class Calc(AFNICommand):
    """This program does voxel-by-voxel arithmetic on 3D datasets

    For complete details, see the `3dcalc Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dcalc.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import example_data
    >>> calc = afni.Calc(['a','b'])
    >>> calc.inputs.in_file_a = example_data('functional.nii')
    >>> calc.inputs.in_file_b = example_data('functional2.nii')
    >>> calc.inputs.expr='a*b'
    >>> calc.inputs.out_file = 'functional_calc.nii.gz'
    >>> res = calc.run() # doctest: +SKIP

    """

    _cmd = '3dcalc'
    input_spec = CalcInputSpec
    output_spec = CalcOutputSpec

    # def __init__(self, letters=['a', 'b'], **inputs):
    #     super(Calc, self).__init__(**inputs)
    #     unique = self._formatLetters(letters)
    #     assert (unique is not None), 'Calc cannot be initialized with an empty list'
    #     self._add_in_files(unique)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file_a,
                                                  suffix=self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]

    # def _formatLetters(self, letters):
    #     """
    #     Returns a sorted list of unique letters in the expression
    #     """
    #     unique = list(set(letters))
    #     unique.sort()
    #     for letter in unique:
    #         assert (letter in string.ascii_lowercase), 'Calc only takes in lowercase ASCII letters: %s' % letter
    #         assert (len(letter) == 1), 'Calc takes in a list of single letters only: %s' % letter
    #     return unique

    # def _add_in_files(self, unique):
    #     for letter in unique:
    #         argstr = '-{0} %s'.format(letter)
    #         add_traits(self.inputs, ['in_file_%s' % letter],
    #                trait_type=File(position=unique.index(letter),
    #                                argstr=argstr, mandatory=True,
    #                                exists=True))

    def _format_arg(self, name, trait_spec, value):
        # if name == 'expr':
        #     self._add_in_file_traits(self_findExprLetters())
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

class DeconvolveInputSpec(DynamicTraitedSpec, AFNICommandInputSpec):
    in_file = InputMultiPath(File(exists=True), argstr="%s", mandatory=True, desc="Filename(s) of 3D+time input dataset")
    stim_file_1 = File(exists=True, argstr="%s", mandatory=True, desc="HACK")
    mask = File(argstr="-mask %s", exists=True, desc="Filename of 3D mask dataset")
    ignoreWarnings = traits.Either(traits.Bool(),
                                   traits.Int(), desc="GOFORIT [g]: Proceed even if the matrix has \
    problems, optional value 'g' specifies number of warnings to ignore")
    nullHypothesisPolynomialDegree = traits.Either(traits.Enum('auto'),
                                                   traits.Int(), argstr="-polort %d", desc="degree of \
    polynomial corresponding to the null hypothesis")
    full_first = traits.Bool(argstr="-full_first", desc="")
    is_float = traits.Bool(argstr="-float", desc="")
    tout = traits.Bool(argstr="-tout", desc="")
    rout = traits.Bool(argstr="-rout", desc="")
    fout = traits.Bool(argstr="-fout", desc="")
    # TODO: Should all these outputs be mandatory???
    bucket = traits.File(argstr="-bucket %s", mandatory=True, desc="")
    fitts = traits.File(argstr="-fitts %s", mandatory=True, desc="")
    errts = traits.File(argstr="-errts %s", mandatory=True, desc="")


class DeconvolveOutputSpec(TraitedSpec):
    out_file = traits.File(exists=False, desc="")
    out_fitts = traits.File(exists=False, desc="")
    out_errts = traits.File(exists=False, desc="")

class Deconvolve(AFNICommand):
    """
    Calculate the deconvolution of a 4D measurement dataset with a specified input stimulus
    time series

    Nota bene: If stimFileCount != stimSeriesCount, the last file is assumed to be multi-block!

    For complete details, see the `3dDeconvolve Documentation
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDeconvolve.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> Deconv = afni.Deconvolve()
    Traceback (most recent call last):
    ...
    AssertionError: Deconvolve() requires two inputs

    >>> from nipype.interfaces import afni
    >>> Deconv = afni.Deconvolve(2, 1)
    Traceback (most recent call last):
    ...
    AssertionError: The number of stimulus files MUST be <= the number of stimulus series

    >>> from nipype.interfaces import afni
    >>> Deconv = afni.Deconvolve('2', 3.124)
    Traceback (most recent call last):
    ...
    AssertionError: Initial inputs must be integers

    >>> from nipype.interfaces import afni
    >>> from nipype.testing import example_data
    >>> Deconv = afni.Deconvolve(3, 8)
    >>> Deconv.inputs.in_file = example_data('functional.nii')
    >>> Deconv.inputs.mask = example_data('seed_mask.nii')
    >>> Deconv.inputs.ignoreWarnings = 4
    >>> Deconv.inputs.nullHypothesisPolynomialDegree = 1
    >>> Deconv.inputs.stim_file_1 = example_data('functional.nii') #'stim_file1.1D')
    >>> Deconv.inputs.stim_label_1 = 'median_csf'
    >>> Deconv.inputs.is_stim_base_1 = False
    >>> Deconv.inputs.stim_file_2 = example_data('functional.nii') #'stim_file2.1D')
    >>> Deconv.inputs.stim_label_2 = 'median_wm'
    >>> # Deconv.inputs.is_stim_base_2 = False
    >>> Deconv.inputs.stim_file_3 = example_data('functional.nii') #'stim_file3.1D')
    >>> Deconv.inputs.stim_label_3 = 'roll'
    >>> Deconv.inputs.is_stim_base_3 = True
    >>> Deconv.inputs.stim_label_4 = 'pitch'
    >>> Deconv.inputs.is_stim_base_4 = True
    >>> Deconv.inputs.stim_label_5 = 'yaw'
    >>> Deconv.inputs.is_stim_base_5 = True
    >>> Deconv.inputs.stim_label_6 = 'dS'
    >>> Deconv.inputs.is_stim_base_6 = True
    >>> Deconv.inputs.stim_label_7 = 'dL'
    >>> Deconv.inputs.is_stim_base_7 = True
    >>> Deconv.inputs.stim_label_8 = 'dP'
    >>> Deconv.inputs.is_stim_base_8 = True
    >>> result = Deconv.run()                                              # doctest: +SKIP

    """
    _cmd = "3dDeconvolve"
    input_spec = DeconvolveInputSpec
    output_spec = DeconvolveOutputSpec
    _outputtype = 'AFNI'

    def __init__(self, fileCount=0, seriesCount=0, **inputs):
        super(Deconvolve, self).__init__(**inputs)
        assert ((fileCount > 0) and (seriesCount > 0)), "Deconvolve() requires two inputs"
        assert (isinstance(fileCount, int) and isinstance(seriesCount, int)), "Initial inputs must be integers"
        assert (fileCount <= seriesCount), "The number of stimulus files MUST be <= the number of stimulus series"
        self.stimFileCount = fileCount
        self.stimSeriesCount = seriesCount
        self._add_stim_traits()

    def _add_stim_traits(self):
        add_traits(self.inputs, ['stim_file_%d' % (ii + 1) for ii in range(self.stimFileCount)],
                   trait_type=traits.File(exists=True))
        add_traits(self.inputs, ['stim_label_%d' % (jj + 1) for jj in range(self.stimSeriesCount)],
                   trait_type=traits.Str())
        add_traits(self.inputs, ['is_stim_base_%d' % (kk + 1) for kk in range(self.stimSeriesCount)],
                   trait_type=traits.Bool(default=False, usedefault=True))

    def _formatStimulus(self):
        retval = []
        retval.append("-num_stimts %d" % self.stimSeriesCount)
        for count in range(1, self.stimSeriesCount + 1):
            if (count < self.stimFileCount):
                fileValue = getattr(self.inputs, 'stim_file_%d' % count)
                retval.append("-stim_file %d %s" % (count, fileValue))
            elif (count >= self.stimFileCount):
                fileValue = getattr(self.inputs, 'stim_file_%d' % self.stimFileCount)
                retval.append("-stim_file %d %s[%d]" % (count, fileValue,
                                                        count - self.stimFileCount)) # + 1
            labelValue = getattr(self.inputs, 'stim_label_%d' % count)
            retval.append("-stim_label %d %s" % (count, labelValue))
            baseValue = getattr(self.inputs, 'is_stim_base_%d' % count)
            if baseValue:
                retval.append("-stim_base %d" % count)
        return " ".join(retval)

    def _format_arg(self, opt, spec, val):
        if opt == "in_file":
            files = ",".join(self.inputs.in_file)
            return "-input %s" % files
        elif opt == "ignoreWarnings":
            if isinstance(val, bool):
                if val:
                    return "-GOFORIT"
            else:
                return "-GOFORIT %d" % val
        elif opt == "nullHypothesisPolynomialDegree":
            if val == 'auto':
                return "-polort A"
            else:
                return "-polort %d" % val
        elif opt == 'stim_file_1':
            return self._formatStimulus()
        elif opt == 'outputtype':
            pass # TODO: Add user warning here
        return super(Deconvolve, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        # self.inputs.outputtype = 'AFNI'
        # TODO: Add isdefined() tests if not mandatory...
        outputs['out_file'] = self._gen_fname(basename=self.inputs.bucket, suffix='')
        outputs['out_fitts'] = self._gen_fname(basename=self.inputs.fitts, suffix='')
        outputs['out_errts'] = self._gen_fname(basename=self.inputs.errts, change_ext=False)
        return outputs

class ZeropadInputSpec(AFNICommandInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-1, desc="Filename of input")
    out_file = traits.Either(File(genfile=True, hash_files=False), traits.Str(), argstr='-prefix %s',
                             position=1, desc='output file prefix of 3dZeropad')
    plane = traits.Enum('I', 'S', 'A', 'P', 'L' , 'R', 'z', 'IS', 'AP', 'LR', argstr='%s',
                        usedefault=False, position=2, desc="plane(s) to zero pad")
    numberOfPlanes = traits.Int(requires=['plane'])
    is_mm = traits.Bool(argstr='-mm', default=False, position=3,
                        desc='Specify if the plane number is in millimeters or slices')
    master =  File(exists=True, argstr='-master %s', position=2, xor=['plane', 'is_mm'],
                   desc="Filename of volume to match")

class ZeropadOutputSpec(TraitedSpec):
    out_file = traits.File(exists=False, desc="")

class Zeropad(AFNICommand):
    """
    >>> from nipype.interfaces import afni
    >>> from nipype.testing import example_data
    >>> Zpad = afni.Zeropad()
    >>> Zpad.inputs.in_file = example_data('functional.nii')
    >>> Zpad.inputs.out_file = 'zero_pad'
    >>> Zpad.inputs.plane = 'IS'
    >>> Zpad.inputs.numberOfPlanes = 44
    >>> Zpad.inputs.is_mm = False
    >>> Zpad.cmdline # doctest: +ELLIPSIS
    '3dZeropad -prefix zero_pad -IS 44 ...functional.nii'
    >>> result = Zpad.run()  # doctest: +SKIP
    >>> Zpad.inputs.plane = 'z'
    >>> Zpad.inputs.is_mm = True
    >>> Zpad.cmdline # doctest: +ELLIPSIS
    '3dZeropad -prefix zero_pad -z 44 -mm ...functional.nii'
    >>> result = Zpad.run()  # doctest: +SKIP
    """
    _cmd = "3dZeropad"
    input_spec = ZeropadInputSpec
    output_spec = ZeropadOutputSpec

    def _format_arg(self, opt, spec, val):
        if opt == 'plane':
            return '-%s %d' % (val, self.inputs.numberOfPlanes)
        return super(Zeropad, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(basename='zeropad', suffix='')
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs
