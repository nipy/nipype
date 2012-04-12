# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft = python sts = 4 ts = 4 sw = 4 et:
"""Afni preprocessing interfaces

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
    >>> os.chdir(datadir)
"""
import warnings
import os
from .base import AFNITraitedSpec, AFNICommand
from ..base import (Directory, CommandLineInputSpec, CommandLine, TraitedSpec,
                    traits, isdefined, File)
from ...utils.filemanip import (load_json, save_json, split_filename)

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class To3DInputSpec(AFNITraitedSpec):
    infolder = Directory(desc='folder with DICOM images to convert',
        argstr='%s/*.dcm',
        position=-1,
        mandatory=True,
        exists=True)

    outfile = File(desc='converted image file',
        argstr='-prefix %s',
        position=-2,
        mandatory=True)

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


class To3DOutputSpec(TraitedSpec):
    out_file = File(desc='converted file',
        exists=True)


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
    >>> res = To3D.run() #doctest: +SKIP

   """

    _cmd = 'to3d'
    input_spec = To3DInputSpec
    output_spec = To3DOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.outfile
        return outputs


class TShiftInputSpec(AFNITraitedSpec):
    in_file = File(desc='input file to 3dTShift',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)
    out_file = File(desc='output file from 3dTshift',
        argstr='-prefix %s',
        position=0,
        genfile=True)

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

    suffix = traits.Str(desc="out_file suffix")
        # todo: give it a default-value


class TShiftOutputSpec(TraitedSpec):
    out_file = File(desc='post slice time shifted 4D image')


class TShift(AFNICommand):
    """Shifts voxel time series from input
    so that seperate slices are aligned to the same
    temporal origin

    For complete details, see the `3dTshift Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTshift.html>

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> tshift = afni.TShift()
    >>> tshift.inputs.in_file = example_data('functional.nii')
    >>> tshift.inputs.out_file = 'functional_tshift.nii'
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
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(outputs['out_file']):

            if isdefined(self.inputs.suffix):
                suffix = self.inputs.suffix
            else:
                suffix = "_tshift"
        outputs['out_file'] = self._gen_fname(self.inputs.in_file,
             suffix=suffix)
        return outputs


class RefitInputSpec(AFNITraitedSpec):
    in_file = File(desc='input file to 3drefit',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=True)

    deoblique = traits.Bool(desc='replace current transformation' +
        ' matrix with cardinal matrix',
        argstr='-deoblique')

    xorigin = traits.Str(desc='x distance for edge voxel offset',
        argstr='-xorigin %s')

    yorigin = traits.Str(desc='y distance for edge voxel offset',
        argstr='-yorigin %s')
    zorigin = traits.Str(desc='z distance for edge voxel offset',
        argstr='-zorigin %s')


class RefitOutputSpec(TraitedSpec):
    out_file = File(desc='Same file as original infile with modified matrix',
        exists=True)


class Refit(AFNICommand):
    """Changes some of the information inside a 3D dataset's header

    For complete details, see the `3drefit Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3drefit.html>

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> refit = afni.Refit()
    >>> refit.inputs.in_file = example_data('structural.nii')
    >>> refit.inputs.deoblique=True
    >>> res = refit.run() # doctest: +SKIP

    """

    _cmd = '3drefit'
    input_spec = RefitInputSpec
    output_spec = RefitOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.in_file
        return outputs


class WarpInputSpec(AFNITraitedSpec):

    in_file = File(desc='input file to 3dWarp',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)

    out_file = File(desc='output file from 3dWarp',
        argstr='-prefix %s',
        position=0,
        genfile=True)

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
        argstr="-zpad %s")

    suffix = traits.Str(desc="out_file suffix")
        # todo: give it a default-value


class WarpOutputSpec(TraitedSpec):
    out_file = File(desc='spatially transformed input image', exists=True)


class Warp(AFNICommand):
    """Use 3dWarp for spatially transforming a dataset

    For complete details, see the `3dWarp Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dWarp.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> warp = afni.Warp()
    >>> warp.inputs.in_file = example_data('structural.nii')
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
            if isdefined(self.inputs.suffix):
                suffix = self.inputs.suffix
            else:
                suffix = "_warp"
            outputs['out_file'] = self._gen_fname(
                self.inputs.in_file, suffix=suffix)
        else:
            outputs['out_file'] = self.inputs.out_file
        return outputs


class ResampleInputSpec(AFNITraitedSpec):

    in_file = File(desc='input file to 3dresample',
        argstr='-inset %s',
        position=-1,
        mandatory=True,
        exists=True)

    out_file = File(desc='output file from 3dresample',
        argstr='-prefix %s',
        position=-2,
        genfile=True)

    orientation = traits.Str(desc='new orientation code',
        argstr='-orient %s')

    suffix = traits.Str(desc="out_file suffix")
        # todo: give it a default-value


class ResampleOutputSpec(TraitedSpec):
    out_file = File(desc='reoriented or resampled file',
        exists=True)


class Resample(AFNICommand):
    """Resample or reorient an image using AFNI 3dresample command

    For complete details, see the `3dresample Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dresample.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> resample = afni.Resample()
    >>> resample.inputs.in_file = example_data('functional.nii')
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
            if isdefined(self.inputs.suffix):
                suffix = self.inputs.suffix
            else:
                suffix = []  # allow for resampling command later!
                if self.inputs.orientation:
                    suffix.append("_RPI")
                suffix = "".join(suffix)
            outputs['out_file'] = self._gen_fname(
                self.inputs.in_file, suffix=suffix)
        else:
            outputs['out_file'] = self.inputs.out_file
        return outputs


class TStatInputSpec(AFNITraitedSpec):
    in_file = File(desc='input file to 3dTstat',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)

    out_file = File(desc='output file from 3dTstat',
        argstr='-prefix %s',
        position=-2,
        genfile=True)

    options = traits.Str(desc='selected statistical output',
        argstr='%s')


class TStatOutputSpec(TraitedSpec):
    out_file = File(desc='statistical file',
        exists=True)


class TStat(AFNICommand):
    """Compute voxel-wise statistics using AFNI 3dTstat command

    For complete details, see the `3dTstat Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTstat.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> tstat = afni.TStat()
    >>> tstat.inputs.in_file = example_data('functional.nii')
    >>> tstat.inputs.options= '-mean'
    >>> res = tstat.run() # doctest: +SKIP

    """

    _cmd = '3dTstat'
    input_spec = TStatInputSpec
    output_spec = TStatOutputSpec

    def _gen_filename(self, name):
        """Generate output file name
        """

        if name == 'out_file':
            _, fname, ext = split_filename(self.inputs.in_file)
            return os.path.join(os.getcwd(), ''.join((fname, '_3dT', ext)))

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_filename('out_file')
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class DetrendInputSpec(AFNITraitedSpec):
    in_file = File(desc='input file to 3dDetrend',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)
    out_file = File(desc='output file from 3dDetrend',
         argstr='-prefix %s',
         position=-2,
         genfile=True)
    options = traits.Str(desc='selected statistical output',
        argstr='%s')


class DetrendOutputSpec(TraitedSpec):
    out_file = File(desc='statistical file',
        exists=True)


class Detrend(AFNICommand):
    """This program removes components from voxel time series using
    linear least squares

    For complete details, see the `3dDetrend Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDetrend.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> detrend = afni.Detrend()
    >>> detrend.inputs.in_file = example_data('functional.nii')
    >>> detrend.inputs.options = '-polort 2'
    >>> res = detrend.run() # doctest: +SKIP

    """

    _cmd = '3dDetrend'
    input_spec = DetrendInputSpec
    output_spec = DetrendOutputSpec

    def _gen_filename(self, name):
        """Generate output file name
        """

        if name == 'out_file':
            _, fname, ext = split_filename(self.inputs.in_file)
            return os.path.join(os.getcwd(), ''.join((fname, '_3dD', ext)))

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_filename('out_file')
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class DespikeInputSpec(AFNITraitedSpec):
    in_file = File(desc='input file to 3dDespike',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)

    out_file = File(desc='output file from 3dDespike',
         argstr='-prefix %s',
         position=-2,
         genfile=True)

    options = traits.Str(desc='additional args',
        argstr='%s')


class DespikeOutputSpec(TraitedSpec):
    out_file = File(desc='despiked img',
               exists=True)


class Despike(AFNICommand):
    """Removes 'spikes' from the 3D+time input dataset

    For complete details, see the `3dDespike Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDespike.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> despike = afni.Despike()
    >>> despike.inputs.in_file = example_data('functional.nii')
    >>> res = despike.run() # doctest: +SKIP

    """

    _cmd = '3dDespike'
    input_spec = DespikeInputSpec
    output_spec = DespikeOutputSpec

    def _gen_filename(self, name):
        """Generate output file name
        """
        if name == 'out_file':
            _, fname, ext = split_filename(self.inputs.in_file)
            return os.path.join(os.getcwd(), ''.join((fname, '_3dDe', ext)))

    def _list_outputs(self):
        outputs = self.output_spec().get()
        #outputs['out_file'] = os.path.abspath(self.inputs.out_file)

        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_filename('out_file')
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class AutomaskInputSpec(AFNITraitedSpec):
    in_file = File(desc='input file to 3dAutomask',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)

    out_file = File(desc='output file from 3dAutomask (a brain mask)',
        argstr='-prefix %s',
        position=-2,
        genfile=True)

    apply_mask = File(desc="output file from 3dAutomask",
        argstr='-apply_prefix %s')

    clfrac = traits.Float(desc='sets the clip level fraction' +
        ' (must be 0.1-0.9). ' +
        'A small value will tend to make the mask larger [default = 0.5].',
        argstr="-dilate %s")

    dilate = traits.Int(desc='dilate the mask outwards',
        argstr="-dilate %s")

    erode = traits.Int(desc='erode the mask inwards',
        argstr="-erode %s")

    options = traits.Str(desc='automask settings',
        argstr='%s')

    suffix = traits.Str(desc="out_file suffix")
        # todo: give it a default-value


class AutomaskOutputSpec(TraitedSpec):
    out_file = File(desc='mask file',
        exists=True)

    brain_file = File(desc='brain file (skull stripped)',
        exists=True)


class Automask(AFNICommand):
    """Create a brain-only mask of the image using AFNI 3dAutomask command

    For complete details, see the `3dAutomask Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAutomask.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> automask = afni.Automask()
    >>> automask.inputs.in_file = example_data('functional.nii')
    >>> automask.inputs.dilate = 1
    >>> res = automask.run() # doctest: +SKIP

    """

    _cmd = '3dAutomask'
    input_spec = AutomaskInputSpec
    output_spec = AutomaskOutputSpec

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['brain_file'] = self.inputs.apply_mask

        if not isdefined(self.inputs.out_file):
            if isdefined(self.inputs.suffix):
                suffix = self.inputs.suffix
            else:
                suffix = "_automask"

            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                suffix=suffix)
        else:
            outputs['out_file'] = self.inputs.out_file
        return outputs


class VolregInputSpec(AFNITraitedSpec):

    in_file = File(desc='input file to 3dvolreg',
       argstr='%s',
       position=-1,
       mandatory=True,
       exists=True)
    out_file = File(desc='output file from 3dvolreg',
       argstr='-prefix %s',
       position=-2,
       genfile=True)
    basefile = File(desc='base file for registration',
        argstr='-base %s',
        position=-6)
    zpad = File(desc='Zeropad around the edges' +
        ' by \'n\' voxels during rotations',
        argstr='-zpad %s',
        position=-5)
    md1dfile = File(desc='max displacement output file',
        argstr='-maxdisp1D %s',
        position=-4)
    oned_file = File(desc='1D movement parameters output file',
        argstr='-1Dfile %s',
        position=-3,
        genfile=True)
    verbose = traits.Bool(desc='more detailed description of the process',
        argstr='-verbose')
    timeshift = traits.Bool(desc='time shift to mean slice time offset',
        argstr='-tshift 0')
    copyorigin = traits.Bool(desc='copy base file origin coords to output',
        argstr='-twodup')
    other = traits.Str(desc='other options',
        argstr='%s')


class VolregOutputSpec(TraitedSpec):
    out_file = File(desc='registered file',
        exists=True)
    md1d_file = File(desc='max displacement info file')
    oned_file = File(desc='movement parameters info file')


class Volreg(AFNICommand):
    """Register input volumes to a base volume using AFNI 3dvolreg command

    For complete details, see the `3dvolreg Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dvolreg.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> volreg = afni.Volreg()
    >>> volreg.inputs.in_file = example_data('functional.nii')
    >>> volreg.inputs.other = '-Fourier -twopass'
    >>> volreg.inputs.zpad = '4'
    >>> res = volreg.run() # doctest: +SKIP

    """

    _cmd = '3dvolreg'
    input_spec = VolregInputSpec
    output_spec = VolregOutputSpec

    def _gen_filename(self, name):
        """Generate output file name
        """
        if name == 'out_file':
            _, fname, ext = split_filename(self.inputs.in_file)
            return os.path.join(os.getcwd(), ''.join((fname, '_3dv', ext)))

        if name == 'oned_file':
            _, fname, ext = split_filename(self.inputs.in_file)
            return os.path.join(os.getcwd(), ''.join((fname, '_3dv1D', '.1D')))

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_filename('out_file')
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)

        if not isdefined(self.inputs.oned_file):
            outputs['oned_file'] = self._gen_filename('oned_file')
        else:
            outputs['oned_file'] = os.path.abspath(self.inputs.oned_file)

        return outputs


class MergeInputSpec(AFNITraitedSpec):
    infile = File(desc='input file to 3dvolreg',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)
    outfile = File(desc='output file from 3dvolreg',
         argstr='-prefix %s',
         position=-2,
         mandatory=True)
    doall = traits.Bool(desc='apply options to all sub-bricks in dataset',
        argstr='-doall')
    blurfwhm = traits.Int(desc='FWHM blur value (mm)',
          argstr='-1blur_fwhm %d',
          units='mm')
    other = traits.Str(desc='other options',
         argstr='%s')


class MergeOutputSpec(TraitedSpec):
    out_file = File(desc='smoothed file',
        exists=True)


class Merge(AFNICommand):
    """Merge or edit volumes using AFNI 3dmerge command

    For complete details, see the `3dmerge Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dmerge.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> merge = afni.Merge()
    >>> merge.inputs.infile = example_data('functional.nii')
    >>> merge.inputs.blurfwhm = 4.0
    >>> merge.inputs.doall = True
    >>> merge.inputs.outfile = 'e7.nii'
    >>> res = merge.run() # doctest: +SKIP

    """

    _cmd = '3dmerge'
    input_spec = MergeInputSpec
    output_spec = MergeOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.outfile
        return outputs


class CopyInputSpec(AFNITraitedSpec):
    in_file = File(desc='input file to 3dcopy',
        argstr='%s',
        position=-2,
        mandatory=True,
        exists=True)
    out_file = File(desc='output file from 3dcopy',
        argstr='%s',
        position=-1,
        genfile=True)


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
    >>> from nipype.testing import  example_data
    >>> copy = afni.Copy()
    >>> copy.inputs.in_file = example_data('functional.nii')
    >>> copy.inputs.out_file = 'new_func.nii'
    >>> res = copy.run() # doctest: +SKIP

    """

    _cmd = '3dcopy'
    input_spec = CopyInputSpec
    output_spec = CopyOutputSpec

    def _gen_filename(self, name):
        """Generate output file name
        """
        if name == 'out_file':
            _, fname, ext = split_filename(self.inputs.in_file)
            return os.path.join(os.getcwd(), ''.join((fname, '_copy', ext)))

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_filename('out_file')
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class FourierInputSpec(AFNITraitedSpec):
    in_file = File(desc='input file to 3dFourier',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)
    out_file = File(desc='output file from 3dFourier',
         argstr='-prefix %s',
         position=-2,
         genfile=True)
    lowpass = traits.Float(desc='lowpass',
        argstr='-lowpass %f',
        position=0,
        mandatory=True)
    highpass = traits.Float(desc='highpass',
        argstr='-highpass %f',
        position=1,
        mandatory=True)
    other = traits.Str(desc='other options',
        argstr='%s')


class FourierOutputSpec(TraitedSpec):
    out_file = File(desc='band-pass filtered file',
        exists=True)


class Fourier(AFNICommand):
    """Program to lowpass and/or highpass each voxel time series in a
    dataset, via the FFT

    For complete details, see the `3dFourier Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dfourier.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> fourier = afni.Fourier()
    >>> fourier.inputs.in_file = example_data('functional.nii')
    >>> fourier.inputs.other = '-retrend'
    >>> fourier.inputs.highpass = 0.005
    >>> fourier.inputs.lowpass = 0.1
    >>> res = fourier.run() # doctest: +SKIP

    """

    _cmd = '3dFourier'
    input_spec = FourierInputSpec
    output_spec = FourierOutputSpec

    def _gen_filename(self, name):
        """Generate output file name
        """
        if name == 'out_file':
            _, fname, ext = split_filename(self.inputs.in_file)
            return os.path.join(os.getcwd(), ''.join((fname, '_3dF', ext)))

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_filename('out_file')
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class ZCutUpInputSpec(AFNITraitedSpec):
    infile = File(desc='input file to 3dZcutup',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)
    outfile = File(desc='output file from 3dZcutup',
         argstr='-prefix %s',
         position=-2,
         mandatory=True)
    keep = traits.Str(desc='slice range to keep in output',
            argstr='-keep %s')
    other = traits.Str(desc='other options',
               argstr='%s')


class ZCutUpOutputSpec(TraitedSpec):
    out_file = File(desc='cut file',
        exists=True)


class ZCutUp(AFNICommand):
    """Cut z-slices from a volume using AFNI 3dZcutup command

    For complete details, see the `3dZcutup Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dZcutup.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> zcutup = afni.Zcutup()
    >>> zcutup.inputs.infile = example_data('functional.nii')
    >>> zcutup.inputs.outfile= 'functional_zcutup.nii'
    >>> zcutup.inputs.keep= '0 10'
    >>> res = zcutup.run() # doctest: +SKIP

    """

    _cmd = '3dZcutup'
    input_spec = ZCutUpInputSpec
    output_spec = ZCutUpOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.outfile
        return outputs


class AllineateInputSpec(AFNITraitedSpec):
    infile = File(desc='input file to 3dAllineate',
        argstr='-source %s',
        position=-1,
        mandatory=True,
        exists=True)
    outfile = File(desc='output file from 3dAllineate',
         argstr='-prefix %s',
         position=-2,
         mandatory=True)
    matrix = File(desc='matrix to align input file',
        argstr='-1dmatrix_apply %s',
        position=-3)


class AllineateOutputSpec(TraitedSpec):
    out_file = File(desc='cut file',
          exists=True)


class Allineate(AFNICommand):
    """Program to align one dataset (the 'source') to a base dataset

    For complete details, see the `3dAllineate Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAllineate.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> allineate = afni.Allineate()
    >>> allineate.inputs.infile = example_data('functional.nii')
    >>> allineate.inputs.outfile= 'functional_allineate.nii'
    >>> allineate.inputs.matrix= example_data('cmatrix.mat')
    >>> res = allineate.run() # doctest: +SKIP

    """

    _cmd = '3dAllineate'
    input_spec = AllineateInputSpec
    output_spec = AllineateOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.outfile
        return outputs


class MaskaveInputSpec(AFNITraitedSpec):
    in_file = File(desc='input file to 3dmaskave',
        argstr='%s',
        position=-2,
        mandatory=True,
        exists=True)
    out_file = File(desc='output to the file',
         argstr='> %s',
         position=-1,
         genfile=True)
    mask = File(desc='matrix to align input file',
        argstr='-mask %s',
        position=1)

    quiet = traits.Bool(desc='matrix to align input file',
        argstr='-quiet',
        position=2)


class MaskaveOutputSpec(TraitedSpec):
    out_file = File(desc='outfile',
          exists=True)


class Maskave(AFNICommand):
    """Computes average of all voxels in the input dataset
    which satisfy the criterion in the options list

    For complete details, see the `3dmaskave Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dmaskave.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> maskave = afni.Maskave()
    >>> maskave.inputs.in_file = example_data('functional.nii')
    >>> maskave.inputs.mask= example_data('seed_mask.nii')
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
            out_file = self._gen_filename('out_file')
        else:
            out_file = os.path.abspath(self.inputs.out_file)
        outputs['out_file'] = out_file
        return outputs

    def _gen_filename(self, name):
        """Generate output file name
        """
        if name == 'out_file':
            _, fname, ext = split_filename(self.inputs.in_file)
            return os.path.join(os.getcwd(), ''.join((fname, '_3dm', '.1D')))


class SkullStripInputSpec(AFNITraitedSpec):
    in_file = File(desc='input file to 3dSkullStrip',
        argstr='-input %s',
        position=1,
        mandatory=True,
        exists=True)
    out_file = File(desc='output to the file',
         argstr='%s',
         position=-1,
        genfile=True)
    options = traits.Str(desc='options', argstr='%s', position=2)


class SkullStripOutputSpec(TraitedSpec):
    out_file = File(desc='outfile',
        exists=True)


class SkullStrip(AFNICommand):
    """A program to extract the brain from surrounding
    tissue from MRI T1-weighted images

    For complete details, see the `3dSkullStrip Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dSkullStrip.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> skullstrip = afni.Skullstrip()
    >>> skullstrip.inputs.in_file = example_data('functional.nii')
    >>> skullstrip.inputs.options = '-o_ply'
    >>> res = skullstrip.run() # doctest: +SKIP

    """
    _cmd = '3dSkullStrip'
    input_spec = SkullStripInputSpec
    output_spec = SkullStripOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            out_file = self._gen_filename('out_file')
        else:
            out_file = os.path.abspath(self.inputs.out_file)

        outputs['out_file'] = out_file
        return outputs

    def _gen_filename(self, name):
        """Generate output file name
        """
        if name == 'out_file':
            _, fname, ext = split_filename(self.inputs.in_file)
        return os.path.join(os.getcwd(), ''.join((fname, '_3dT', ext)))


class TCatInputSpec(AFNITraitedSpec):
    in_file = File(desc='input file to 3dTcat',
        argstr=' %s',
        position=-1,
        mandatory=True,
        exists=True)
    out_file = File(desc='output to the file',
         argstr='-prefix %s',
         position=-2,
         genfile=True)
    rlt = traits.Str(desc='options', argstr='-rlt%s', position=1)


class TCatOutputSpec(TraitedSpec):
    out_file = File(desc='outfile',
        exists=True)


class TCat(AFNICommand):
    """Concatenate sub-bricks from input datasets into
    one big 3D+time dataset

    For complete details, see the `3dTcat Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTcat.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> tcat = afni.TCat()
    >>> tcat.inputs.in_file = example_data('functional.nii')
    >>> tcat.inputs.out_file= 'functional_tcat.nii'
    >>> tcat.inputs.rlt = '+'
    >>> res = tcat.run() # doctest: +SKIP

    """

    _cmd = '3dTcat'
    input_spec = TCatInputSpec
    output_spec = TCatOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            out_file = self._gen_filename('out_file')
        else:
            out_file = os.path.abspath(self.inputs.out_file)

        outputs['out_file'] = out_file
        return outputs

    def _gen_filename(self, name):
        """Generate output file name
        """
        if name == 'out_file':
            _, fname, ext = split_filename(self.inputs.in_file)
        return os.path.join(os.getcwd(), ''.join((fname, '_3dT', ext)))


class FimInputSpec(AFNITraitedSpec):
    in_file = File(desc='input file to 3dfim+',
        argstr=' -input %s',
        position=1,
        mandatory=True,
        exists=True)
    ideal_file = File(desc='output to the file',
        argstr='-ideal_file %s',
        position=2,
        mandatory=True)
    fim_thr = traits.Float(desc='fim internal mask threshold value',
        argstr='-fim_thr %f', position=3)

    out = traits.Str(desc='Flag to output the specified parameter',
        argstr='-out %s', position=4)

    out_file = File(desc='output file from 3dfim+', argstr='-bucket %s',
        position=-1, genfile=True)


class FimOutputSpec(TraitedSpec):
    out_file = File(desc='outfile',
        exists=True)


class Fim(AFNICommand):
    """Program to calculate the cross-correlation of
    an ideal reference waveform with the measured FMRI
    time series for each voxel

    For complete details, see the `3dfim+ Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dfim+.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> fim = afni.Fim()
    >>> fim.inputs.in_file = example_data('functional.nii')
    >>> fim.inputs.ideal_file= example_data('seed.1D')
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
            out_file = self._gen_filename('out_file')
        else:
            out_file = os.path.abspath(self.inputs.out_file)

        outputs['out_file'] = out_file
        return outputs

    def _gen_filename(self, name):
        """Generate output file name
        """
        if name == 'out_file':
            _, fname, ext = split_filename(self.inputs.in_file)
            return os.path.join(os.getcwd(), ''.join((fname, '_3df', ext)))


class TCorrelateInputSpec(AFNITraitedSpec):
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
    pearson = traits.Bool(desc='Correlation is the normal' +
        ' Pearson correlation coefficient',
        argstr='-pearson',
        position=1)
    polort = traits.Int(desc='Remove polynomical trend of order m',
        argstr='-polort %d', position=2)

    out_file = File(desc='Save output into dataset with prefix ',
        argstr='-prefix %s',
        position=3, genfile=True)

    options = traits.Str(desc='other options',
        argstr='%s', position=4)


class TCorrelateOutputSpec(TraitedSpec):
    out_file = File(desc='outfile',
        exists=True)


class TCorrelate(AFNICommand):
    """Computes the correlation coefficient between corresponding voxel
    time series in two input 3D+time datasets 'xset' and 'yset'

    For complete details, see the `3dTcorrelate Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTcorrelate.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> tcorrelate = afni.TCorrelate()
    >>> tcorrelate.inputs.in_file = example_data('functional.nii')
    >>> tcorrelate.inputs.xset= example_data('u_rc1s1_Template.nii')
    >>> tcorrelate.inputs.yset = example_data('u_rc1s2_Template.nii')
    >>> tcorrelate.inputs.out_file = 'functional_tcorrelate.nii.gz'
    >>> tcorrelate.inputs.polort = -1
    >>> tcorrelate.inputs.pearson = True
    >>> res = tcarrelate.run() # doctest: +SKIP

    """

    _cmd = '3dTcorrelate'
    input_spec = TCorrelateInputSpec
    output_spec = TCorrelateOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_filename('out_file')
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_filename(self, name):
        """Generate output file name
        """
        if name == 'out_file':
            _, fname, ext = split_filename(self.inputs.xset)
            return os.path.join(os.getcwd(), ''.join((fname, '_3dTcor', ext)))


class BrickStatInputSpec(AFNITraitedSpec):
    in_file = File(desc='input file to 3dmaskave',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)

    mask = File(desc='-mask dset = use dset as mask to include/exclude voxels',
        argstr='-mask %s',
        position=2)

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
    >>> from nipype.testing import  example_data
    >>> brickstat = afni.BrickStat()
    >>> brickstat.inputs.in_file = example_data('functional.nii')
    >>> brickstat.inputs.mask = example_data('skeleton_mask.nii.gz')
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


class ROIStatsInputSpec(AFNITraitedSpec):
    in_file = File(desc='input file to 3dROIstats',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)

    mask = File(desc='input mask',
        argstr='-mask %s',
        position=3)

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
    >>> from nipype.testing import  example_data
    >>> roistats = afni.ROIStats()
    >>> roistats.inputs.in_file = example_data('functional.nii')
    >>> roistats.inputs.mask = example_data('skeleton_mask.nii.gz')
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


class CalcInputSpec(CommandLineInputSpec):
    infile_a = File(desc='input file to 3dcalc',
        argstr='-a %s', position=0, mandatory=True)
    infile_b = File(desc='operand file to 3dcalc',
        argstr=' -b %s', position=1)
    expr = traits.Str(desc='expr', argstr='-expr %s', position=2,
        mandatory=True)
    out_file = File(desc='output file from 3dFourier', argstr='-prefix %s',
        position=-1, genfile=True)
    start_idx = traits.Int(desc='start index for infile_a',
        requires=['stop_idx'])
    stop_idx = traits.Int(desc='stop index for infile_a',
        requires=['start_idx'])
    single_idx = traits.Int(desc='volume index for infile_a')
    other = File(desc='other options', argstr='')


class CalcOutputSpec(TraitedSpec):
    out_file = File(desc=' output file', exists=True)


class Calc(CommandLine):
    """This program does voxel-by-voxel arithmetic on 3D datasets

    For complete details, see the `3dcalc Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dcalc.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> from nipype.testing import  example_data
    >>> calc = afni.Calc()
    >>> calc.inputs.infile_a = example_data('functional.nii')
    >>> calc.inputs.Infile_b = example_data('functional2.nii.gz')
    >>> calc.inputs.expr='a*b'
    >>> calc.inputs.out_file =  'functional_calc.nii.gz'
    >>> res = calc.run() # doctest: +SKIP

    """

    _cmd = '3dcalc'
    input_spec = CalcInputSpec
    output_spec = CalcOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_filename('out_file')
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _format_arg(self, name, trait_spec, value):
        if name == 'infile_a':
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

    def _gen_filename(self, name):
        """Generate output file name
        """
        if name == 'out_file':
            _, fname, ext = split_filename(self.inputs.infile_a)
            return os.path.join(os.getcwd(), ''.join((fname, '_3dc', ext)))
