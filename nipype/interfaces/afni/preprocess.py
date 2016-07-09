# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft = python sts = 4 ts = 4 sw = 4 et:
"""Afni preprocessing interfaces

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""

import os
import os.path as op
import re
import numpy as np

from .base import (AFNICommandBase, AFNICommand, AFNICommandInputSpec, AFNICommandOutputSpec,
                   Info, no_afni)
from ..base import (CommandLineInputSpec, CommandLine, Directory, TraitedSpec,
                    traits, isdefined, File, InputMultiPath, Undefined)
from ...external.six import string_types
from ...utils.filemanip import (load_json, save_json, split_filename)

class BlurToFWHMInputSpec(AFNICommandInputSpec):
    in_file = File(desc='The dataset that will be smoothed', argstr='-input %s', mandatory=True, exists=True)

    automask = traits.Bool(desc='Create an automask from the input dataset.', argstr='-automask')
    fwhm = traits.Float(desc='Blur until the 3D FWHM reaches this value (in mm)', argstr='-FWHM %f')
    fwhmxy = traits.Float(desc='Blur until the 2D (x,y)-plane FWHM reaches this value (in mm)', argstr='-FWHMxy %f')
    blurmaster = File(desc='The dataset whose smoothness controls the process.', argstr='-blurmaster %s', exists=True)
    mask = File(desc='Mask dataset, if desired. Voxels NOT in mask will be set to zero in output.', argstr='-blurmaster %s', exists=True)


class BlurToFWHM(AFNICommand):
    """Blurs a 'master' dataset until it reaches a specified FWHM smoothness (approximately).

    For complete details, see the `to3d Documentation
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dBlurToFWHM.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> blur = afni.preprocess.BlurToFWHM()
    >>> blur.inputs.in_file = 'epi.nii'
    >>> blur.inputs.fwhm = 2.5
    >>> blur.cmdline #doctest: +ELLIPSIS
    '3dBlurToFWHM -FWHM 2.500000 -input epi.nii -prefix epi_afni'

    """

    _cmd = '3dBlurToFWHM'
    input_spec = BlurToFWHMInputSpec
    output_spec = AFNICommandOutputSpec

class To3DInputSpec(AFNICommandInputSpec):
    out_file = File(name_template="%s", desc='output image file name',
                    argstr='-prefix %s', name_source=["in_folder"])
    in_folder = Directory(desc='folder with DICOM images to convert',
                          argstr='%s/*.dcm',
                          position=-1,
                          mandatory=True,
                          exists=True)

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
    >>> To3D.inputs.in_folder = '.'
    >>> To3D.inputs.out_file = 'dicomdir.nii'
    >>> To3D.inputs.filetype = "anat"
    >>> To3D.cmdline #doctest: +ELLIPSIS
    'to3d -datum float -anat -prefix dicomdir.nii ./*.dcm'
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
                   exists=True,
                   copyfile=False)

    out_file = File(name_template="%s_tshift", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file")

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

    tpattern = traits.Str(desc='use specified slice time pattern rather than one in header',
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
    >>> tshift.cmdline #doctest:
    '3dTshift -prefix functional_tshift -tpattern alt+z -tzero 0.0 functional.nii'
    >>> res = tshift.run()   # doctest: +SKIP

    """

    _cmd = '3dTshift'
    input_spec = TShiftInputSpec
    output_spec = AFNICommandOutputSpec


class RefitInputSpec(CommandLineInputSpec):
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

    xdel = traits.Float(desc='new x voxel dimension in mm',
                        argstr='-xdel %f')

    ydel = traits.Float(desc='new y voxel dimension in mm',
                        argstr='-ydel %f')

    zdel = traits.Float(desc='new z voxel dimension in mm',
                        argstr='-zdel %f')

    space = traits.Enum('TLRC', 'MNI', 'ORIG',
                        argstr='-space %s',
                        desc='Associates the dataset with a specific' +
                        ' template type, e.g. TLRC, MNI, ORIG')


class Refit(AFNICommandBase):
    """Changes some of the information inside a 3D dataset's header

    For complete details, see the `3drefit Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3drefit.html>

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> refit = afni.Refit()
    >>> refit.inputs.in_file = 'structural.nii'
    >>> refit.inputs.deoblique = True
    >>> refit.cmdline
    '3drefit -deoblique structural.nii'
    >>> res = refit.run() # doctest: +SKIP

    """

    _cmd = '3drefit'
    input_spec = RefitInputSpec
    output_spec = AFNICommandOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = os.path.abspath(self.inputs.in_file)
        return outputs


class WarpInputSpec(AFNICommandInputSpec):

    in_file = File(desc='input file to 3dWarp',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True,
                   copyfile=False)

    out_file = File(name_template="%s_warp", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file")

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

    newgrid = traits.Float(desc="specify grid of this size (mm)",
                           argstr="-newgrid %f")

    zpad = traits.Int(desc="pad input dataset with N planes" +
                      " of zero on all sides.",
                      argstr="-zpad %d")


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
    >>> warp.inputs.out_file = "trans.nii.gz"
    >>> warp.cmdline
    '3dWarp -deoblique -prefix trans.nii.gz structural.nii'

    >>> warp_2 = afni.Warp()
    >>> warp_2.inputs.in_file = 'structural.nii'
    >>> warp_2.inputs.newgrid = 1.0
    >>> warp_2.inputs.out_file = "trans.nii.gz"
    >>> warp_2.cmdline
    '3dWarp -newgrid 1.000000 -prefix trans.nii.gz structural.nii'

    """

    _cmd = '3dWarp'
    input_spec = WarpInputSpec
    output_spec = AFNICommandOutputSpec


class ResampleInputSpec(AFNICommandInputSpec):

    in_file = File(desc='input file to 3dresample',
                   argstr='-inset %s',
                   position=-1,
                   mandatory=True,
                   exists=True,
                   copyfile=False)

    out_file = File(name_template="%s_resample", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file")

    orientation = traits.Str(desc='new orientation code',
                             argstr='-orient %s')

    resample_mode = traits.Enum('NN', 'Li', 'Cu', 'Bk',
                                argstr='-rmode %s',
                                desc="resampling method from set {'NN', 'Li', 'Cu', 'Bk'}.  These are for 'Nearest Neighbor', 'Linear', 'Cubic' and 'Blocky' interpolation, respectively. Default is NN.")

    voxel_size = traits.Tuple(*[traits.Float()] * 3,
                              argstr='-dxyz %f %f %f',
                              desc="resample to new dx, dy and dz")

    master = traits.File(argstr='-master %s',
                         desc='align dataset grid to a reference file')


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
    >>> resample.inputs.outputtype = "NIFTI"
    >>> resample.cmdline
    '3dresample -orient RPI -prefix functional_resample.nii -inset functional.nii'
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
                   exists=True,
                   copyfile=False)

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

    out_file = File(name_template="%s_similarity_matrix.1D", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file")


class AutoTcorrelate(AFNICommand):
    """Computes the correlation coefficient between the time series of each
    pair of voxels in the input dataset, and stores the output into a
    new anatomical bucket dataset [scaled to shorts to save memory space].

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> corr = afni.AutoTcorrelate()
    >>> corr.inputs.in_file = 'functional.nii'
    >>> corr.inputs.polort = -1
    >>> corr.inputs.eta2 = True
    >>> corr.inputs.mask = 'mask.nii'
    >>> corr.inputs.mask_only_targets = True
    >>> corr.cmdline # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    '3dAutoTcorrelate -eta2 -mask mask.nii -mask_only_targets -prefix functional_similarity_matrix.1D -polort -1 functional.nii'
    >>> res = corr.run() # doctest: +SKIP
    """
    input_spec = AutoTcorrelateInputSpec
    output_spec = AFNICommandOutputSpec
    _cmd = '3dAutoTcorrelate'

    def _overload_extension(self, value, name=None):
        path, base, ext = split_filename(value)
        if ext.lower() not in [".1d", ".nii.gz", ".nii"]:
            ext = ext + ".1D"
        return os.path.join(path, base + ext)


class TStatInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dTstat',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True,
                   copyfile=False)

    out_file = File(name_template="%s_tstat", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file")

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
    >>> tstat.inputs.out_file = "stats"
    >>> tstat.cmdline
    '3dTstat -mean -prefix stats functional.nii'
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
                   exists=True,
                   copyfile=False)

    out_file = File(name_template="%s_detrend", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file")


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
    >>> detrend.inputs.outputtype = "AFNI"
    >>> detrend.cmdline
    '3dDetrend -polort 2 -prefix functional_detrend functional.nii'
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
                   exists=True,
                   copyfile=False)

    out_file = File(name_template="%s_despike", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file")


class Despike(AFNICommand):
    """Removes 'spikes' from the 3D+time input dataset

    For complete details, see the `3dDespike Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDespike.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> despike = afni.Despike()
    >>> despike.inputs.in_file = 'functional.nii'
    >>> despike.cmdline
    '3dDespike -prefix functional_despike functional.nii'
    >>> res = despike.run() # doctest: +SKIP

    """

    _cmd = '3dDespike'
    input_spec = DespikeInputSpec
    output_spec = AFNICommandOutputSpec


class CentralityInputSpec(AFNICommandInputSpec):
    """Common input spec class for all centrality-related commmands
    """


    mask = File(desc='mask file to mask input data',
                   argstr="-mask %s",
                   exists=True)

    thresh = traits.Float(desc='threshold to exclude connections where corr <= thresh',
                          argstr='-thresh %f')

    polort = traits.Int(desc='', argstr='-polort %d')

    autoclip = traits.Bool(desc='Clip off low-intensity regions in the dataset',
                           argstr='-autoclip')

    automask = traits.Bool(desc='Mask the dataset to target brain-only voxels',
                           argstr='-automask')


class DegreeCentralityInputSpec(CentralityInputSpec):
    """DegreeCentrality inputspec
    """

    in_file = File(desc='input file to 3dDegreeCentrality',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True,
                   copyfile=False)

    sparsity = traits.Float(desc='only take the top percent of connections',
                            argstr='-sparsity %f')

    oned_file = traits.Str(desc='output filepath to text dump of correlation matrix',
                           argstr='-out1D %s')


class DegreeCentralityOutputSpec(AFNICommandOutputSpec):
    """DegreeCentrality outputspec
    """

    oned_file = File(desc='The text output of the similarity matrix computed'\
                          'after thresholding with one-dimensional and '\
                          'ijk voxel indices, correlations, image extents, '\
                          'and affine matrix')


class DegreeCentrality(AFNICommand):
    """Performs degree centrality on a dataset using a given maskfile
    via 3dDegreeCentrality

    For complete details, see the `3dDegreeCentrality Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDegreeCentrality.html>

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> degree = afni.DegreeCentrality()
    >>> degree.inputs.in_file = 'functional.nii'
    >>> degree.inputs.mask = 'mask.nii'
    >>> degree.inputs.sparsity = 1 # keep the top one percent of connections
    >>> degree.inputs.out_file = 'out.nii'
    >>> degree.cmdline
    '3dDegreeCentrality -mask mask.nii -prefix out.nii -sparsity 1.000000 functional.nii'
    >>> res = degree.run() # doctest: +SKIP
    """

    _cmd = '3dDegreeCentrality'
    input_spec = DegreeCentralityInputSpec
    output_spec = DegreeCentralityOutputSpec

    # Re-define generated inputs
    def _list_outputs(self):
        # Import packages
        import os

        # Update outputs dictionary if oned file is defined
        outputs = super(DegreeCentrality, self)._list_outputs()
        if self.inputs.oned_file:
            outputs['oned_file'] = os.path.abspath(self.inputs.oned_file)

        return outputs


class ECMInputSpec(CentralityInputSpec):
    """ECM inputspec
    """

    in_file = File(desc='input file to 3dECM',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True,
                   copyfile=False)

    sparsity = traits.Float(desc='only take the top percent of connections',
                            argstr='-sparsity %f')

    full = traits.Bool(desc='Full power method; enables thresholding; '\
                            'automatically selected if -thresh or -sparsity '\
                            'are set',
                       argstr='-full')

    fecm = traits.Bool(desc='Fast centrality method; substantial speed '\
                            'increase but cannot accomodate thresholding; '\
                            'automatically selected if -thresh or -sparsity '\
                            'are not set',
                       argstr='-fecm')

    shift = traits.Float(desc='shift correlation coefficients in similarity '\
                              'matrix to enforce non-negativity, s >= 0.0; '\
                              'default = 0.0 for -full, 1.0 for -fecm',
                            argstr='-shift %f')

    scale = traits.Float(desc='scale correlation coefficients in similarity '\
                              'matrix to after shifting, x >= 0.0; '\
                              'default = 1.0 for -full, 0.5 for -fecm',
                            argstr='-scale %f')

    eps = traits.Float(desc='sets the stopping criterion for the power '\
                            'iteration; l2|v_old - v_new| < eps*|v_old|; '\
                            'default = 0.001',
                            argstr='-eps %f')

    max_iter = traits.Int(desc='sets the maximum number of iterations to use '\
                               'in the power iteration; default = 1000',
                          argstr='-max_iter %d')

    memory = traits.Float(desc='Limit memory consumption on system by setting '\
                               'the amount of GB to limit the algorithm to; '\
                               'default = 2GB',
                          argstr='-memory %f')


class ECM(AFNICommand):
    """Performs degree centrality on a dataset using a given maskfile
    via the 3dLFCD command

    For complete details, see the `3dECM Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dECM.html>

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> ecm = afni.ECM()
    >>> ecm.inputs.in_file = 'functional.nii'
    >>> ecm.inputs.mask = 'mask.nii'
    >>> ecm.inputs.sparsity = 0.1 # keep top 0.1% of connections
    >>> ecm.inputs.out_file = 'out.nii'
    >>> ecm.cmdline
    '3dECM -mask mask.nii -prefix out.nii -sparsity 0.100000 functional.nii'
    >>> res = ecm.run() # doctest: +SKIP
    """

    _cmd = '3dECM'
    input_spec = ECMInputSpec
    output_spec = AFNICommandOutputSpec


class LFCDInputSpec(CentralityInputSpec):
    """LFCD inputspec
    """

    in_file = File(desc='input file to 3dLFCD',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True,
                   copyfile=False)


class LFCD(AFNICommand):
    """Performs degree centrality on a dataset using a given maskfile
    via the 3dLFCD command

    For complete details, see the `3dLFCD Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dLFCD.html>

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> lfcd = afni.LFCD()
    >>> lfcd.inputs.in_file = 'functional.nii'
    >>> lfcd.inputs.mask = 'mask.nii'
    >>> lfcd.inputs.thresh = 0.8 # keep all connections with corr >= 0.8
    >>> lfcd.inputs.out_file = 'out.nii'
    >>> lfcd.cmdline
    '3dLFCD -mask mask.nii -prefix out.nii -thresh 0.800000 functional.nii'
    >>> res = lfcd.run() # doctest: +SKIP
    """

    _cmd = '3dLFCD'
    input_spec = LFCDInputSpec
    output_spec = AFNICommandOutputSpec


class AutomaskInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dAutomask',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True,
                   copyfile=False)

    out_file = File(name_template="%s_mask", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file")

    brain_file = File(name_template="%s_masked",
                      desc="output file from 3dAutomask",
                      argstr='-apply_prefix %s',
                      name_source="in_file")

    clfrac = traits.Float(desc='sets the clip level fraction' +
                          ' (must be 0.1-0.9). ' +
                          'A small value will tend to make the mask larger [default = 0.5].',
                          argstr="-clfrac %s")

    dilate = traits.Int(desc='dilate the mask outwards',
                        argstr="-dilate %s")

    erode = traits.Int(desc='erode the mask inwards',
                       argstr="-erode %s")


class AutomaskOutputSpec(TraitedSpec):
    out_file = File(desc='mask file',
                    exists=True)

    brain_file = File(desc='brain file (skull stripped)', exists=True)


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
    >>> automask.cmdline #doctest: +ELLIPSIS
    '3dAutomask -apply_prefix functional_masked.nii -dilate 1 -prefix functional_mask.nii functional.nii'
    >>> res = automask.run() # doctest: +SKIP

    """

    _cmd = '3dAutomask'
    input_spec = AutomaskInputSpec
    output_spec = AutomaskOutputSpec


class VolregInputSpec(AFNICommandInputSpec):

    in_file = File(desc='input file to 3dvolreg',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True,
                   copyfile=False)
    out_file = File(name_template="%s_volreg", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file")
    basefile = File(desc='base file for registration',
                    argstr='-base %s',
                    position=-6,
                    exists=True)
    zpad = traits.Int(desc='Zeropad around the edges' +
                      ' by \'n\' voxels during rotations',
                      argstr='-zpad %d',
                      position=-5)
    md1d_file = File(name_template='%s_md.1D', desc='max displacement output file',
                     argstr='-maxdisp1D %s', name_source="in_file",
                     keep_extension=True, position=-4)
    oned_file = File(name_template='%s.1D', desc='1D movement parameters output file',
                     argstr='-1Dfile %s',
                     name_source="in_file",
                     keep_extension=True)
    verbose = traits.Bool(desc='more detailed description of the process',
                          argstr='-verbose')
    timeshift = traits.Bool(desc='time shift to mean slice time offset',
                            argstr='-tshift 0')
    copyorigin = traits.Bool(desc='copy base file origin coords to output',
                             argstr='-twodup')
    oned_matrix_save = File(name_template='%s.aff12.1D',
                            desc='Save the matrix transformation',
                            argstr='-1Dmatrix_save %s',
                            keep_extension=True,
                            name_source="in_file")


class VolregOutputSpec(TraitedSpec):
    out_file = File(desc='registered file', exists=True)
    md1d_file = File(desc='max displacement info file', exists=True)
    oned_file = File(desc='movement parameters info file', exists=True)
    oned_matrix_save = File(desc='matrix transformation from base to input', exists=True)


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
    >>> volreg.cmdline #doctest: +ELLIPSIS
    '3dvolreg -Fourier -twopass -1Dfile functional.1D -1Dmatrix_save functional.aff12.1D -prefix functional_volreg.nii -zpad 4 -maxdisp1D functional_md.1D functional.nii'
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
        mandatory=True,
        copyfile=False)
    out_file = File(name_template="%s_merge", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file")
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
                   exists=True,
                   copyfile=False)
    out_file = File(name_template="%s_copy", desc='output image file name',
                    argstr='%s', position=-1, name_source="in_file")


class Copy(AFNICommand):
    """Copies an image of one type to an image of the same
    or different type using 3dcopy command

    For complete details, see the `3dcopy Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dcopy.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> copy3d = afni.Copy()
    >>> copy3d.inputs.in_file = 'functional.nii'
    >>> copy3d.cmdline
    '3dcopy functional.nii functional_copy'

    >>> from copy import deepcopy
    >>> copy3d_2 = deepcopy(copy3d)
    >>> copy3d_2.inputs.outputtype = 'NIFTI'
    >>> copy3d_2.cmdline
    '3dcopy functional.nii functional_copy.nii'

    >>> copy3d_3 = deepcopy(copy3d)
    >>> copy3d_3.inputs.outputtype = 'NIFTI_GZ'
    >>> copy3d_3.cmdline
    '3dcopy functional.nii functional_copy.nii.gz'

    >>> copy3d_4 = deepcopy(copy3d)
    >>> copy3d_4.inputs.out_file = 'new_func.nii'
    >>> copy3d_4.cmdline
    '3dcopy functional.nii new_func.nii'
    """

    _cmd = '3dcopy'
    input_spec = CopyInputSpec
    output_spec = AFNICommandOutputSpec


class FourierInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dFourier',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True,
                   copyfile=False)
    out_file = File(name_template="%s_fourier", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file")
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
        exists=True,
        copyfile=False)
    out_file = File(
        name_template='%s_bp',
        desc='output file from 3dBandpass',
        argstr='-prefix %s',
        position=1,
        name_source='in_file',
        genfile=True)
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
        argstr="-dt %f",
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
                   exists=True,
                   copyfile=False)
    out_file = File(name_template="%s_zcupup", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file")
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
                   exists=True,
                   copyfile=False)
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
                    'poly3', 'poly5', 'poly7', 'poly9']  # same non-hellenistic
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
    >>> allineate.inputs.in_matrix= 'cmatrix.mat'
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
            outputs['out_file'] = self._gen_filename(self.inputs.in_file,
                                                     suffix=self.inputs.suffix)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)

        if isdefined(self.inputs.out_matrix):
            outputs['matrix'] = os.path.abspath(os.path.join(os.getcwd(),\
                                         self.inputs.out_matrix +".aff12.1D"))
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]


class MaskaveInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dmaskave',
                   argstr='%s',
                   position=-2,
                   mandatory=True,
                   exists=True,
                   copyfile=False)
    out_file = File(name_template="%s_maskave.1D", desc='output image file name',
                    keep_extension=True,
                    argstr="> %s", name_source="in_file", position=-1)
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
    >>> maskave.cmdline #doctest: +ELLIPSIS
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
                   exists=True,
                   copyfile=False)
    out_file = File(name_template="%s_skullstrip", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file")


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
    _redirect_x = True
    input_spec = SkullStripInputSpec
    output_spec = AFNICommandOutputSpec

    def __init__(self, **inputs):
        super(SkullStrip, self).__init__(**inputs)
        if not no_afni():
            v = Info.version()

            # As of AFNI 16.0.00, redirect_x is not needed
            if isinstance(v[0], int) and v[0] > 15:
                self._redirect_x = False


class TCatInputSpec(AFNICommandInputSpec):
    in_files = InputMultiPath(
        File(exists=True),
        desc='input file to 3dTcat',
        argstr=' %s',
        position=-1,
        mandatory=True,
        copyfile=False)
    out_file = File(name_template="%s_tcat", desc='output image file name',
                    argstr='-prefix %s', name_source="in_files")
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
                   exists=True,
                   copyfile=False)
    out_file = File(name_template="%s_fim", desc='output image file name',
                    argstr='-bucket %s', name_source="in_file")
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


class TCorrelateInputSpec(AFNICommandInputSpec):
    xset = File(desc='input xset',
                argstr=' %s',
                position=-2,
                mandatory=True,
                exists=True,
                copyfile=False)
    yset = File(desc='input yset',
                argstr=' %s',
                position=-1,
                mandatory=True,
                exists=True,
                copyfile=False)
    out_file = File(name_template="%s_tcorr", desc='output image file name',
                    argstr='-prefix %s', name_source="xset")
    pearson = traits.Bool(desc='Correlation is the normal' +
                          ' Pearson correlation coefficient',
                          argstr='-pearson',
                          position=1)
    polort = traits.Int(desc='Remove polynomical trend of order m',
                        argstr='-polort %d', position=2)


class TCorrelate(AFNICommand):
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


class TCorr1DInputSpec(AFNICommandInputSpec):
    xset = File(desc='3d+time dataset input',
                argstr=' %s',
                position=-2,
                mandatory=True,
                exists=True,
                copyfile=False)
    y_1d = File(desc='1D time series file input',
                argstr=' %s',
                position=-1,
                mandatory=True,
                exists=True)
    out_file = File(desc='output filename prefix',
                    name_template='%s_correlation.nii.gz',
                    argstr='-prefix %s',
                    name_source='xset',
                    keep_extension=True)
    pearson = traits.Bool(desc='Correlation is the normal' +
                          ' Pearson correlation coefficient',
                          argstr=' -pearson',
                          xor=['spearman', 'quadrant', 'ktaub'],
                          position=1)
    spearman = traits.Bool(desc='Correlation is the' +
                           ' Spearman (rank) correlation coefficient',
                           argstr=' -spearman',
                           xor=['pearson', 'quadrant', 'ktaub'],
                           position=1)
    quadrant = traits.Bool(desc='Correlation is the' +
                           ' quadrant correlation coefficient',
                           argstr=' -quadrant',
                           xor=['pearson', 'spearman', 'ktaub'],
                           position=1)
    ktaub = traits.Bool(desc='Correlation is the' +
                        ' Kendall\'s tau_b correlation coefficient',
                        argstr=' -ktaub',
                        xor=['pearson', 'spearman', 'quadrant'],
                        position=1)


class TCorr1DOutputSpec(TraitedSpec):
    out_file = File(desc='output file containing correlations',
                    exists=True)


class TCorr1D(AFNICommand):
    """Computes the correlation coefficient between each voxel time series
    in the input 3D+time dataset.
    For complete details, see the `3dTcorr1D Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTcorr1D.html>`_

    >>> from nipype.interfaces import afni as afni
    >>> tcorr1D = afni.TCorr1D()
    >>> tcorr1D.inputs.xset= 'u_rc1s1_Template.nii'
    >>> tcorr1D.inputs.y_1d = 'seed.1D'
    >>> tcorr1D.cmdline
    '3dTcorr1D -prefix u_rc1s1_Template_correlation.nii.gz  u_rc1s1_Template.nii  seed.1D'
    >>> res = tcorr1D.run() # doctest: +SKIP
    """

    _cmd = '3dTcorr1D'
    input_spec = TCorr1DInputSpec
    output_spec = TCorr1DOutputSpec


class BrickStatInputSpec(AFNICommandInputSpec):
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


class ClipLevelInputSpec(CommandLineInputSpec):
    in_file = File(desc='input file to 3dClipLevel',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True)

    mfrac = traits.Float(desc='Use the number ff instead of 0.50 in the algorithm',
                  argstr='-mfrac %s',
                  position=2)

    doall = traits.Bool(desc='Apply the algorithm to each sub-brick separately',
                        argstr='-doall',
                        position=3,
                        xor=('grad'))

    grad = traits.File(desc='also compute a \'gradual\' clip level as a function of voxel position, and output that to a dataset',
                       argstr='-grad %s',
                       position=3,
                       xor=('doall'))


class ClipLevelOutputSpec(TraitedSpec):
    clip_val = traits.Float(desc='output')


class ClipLevel(AFNICommandBase):
    """Estimates the value at which to clip the anatomical dataset so
       that background regions are set to zero.

    For complete details, see the `3dClipLevel Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dClipLevel.html>`_

    Examples
    ========

    >>> from nipype.interfaces.afni import preprocess
    >>> cliplevel = preprocess.ClipLevel()
    >>> cliplevel.inputs.in_file = 'anatomical.nii'
    >>> res = cliplevel.run() # doctest: +SKIP

    """
    _cmd = '3dClipLevel'
    input_spec = ClipLevelInputSpec
    output_spec = ClipLevelOutputSpec

    def aggregate_outputs(self, runtime=None, needed_outputs=None):

        outputs = self._outputs()

        outfile = os.path.join(os.getcwd(), 'stat_result.json')

        if runtime is None:
            try:
                clip_val = load_json(outfile)['stat']
            except IOError:
                return self.run().outputs
        else:
            clip_val = []
            for line in runtime.stdout.split('\n'):
                if line:
                    values = line.split()
                    if len(values) > 1:
                        clip_val.append([float(val) for val in values])
                    else:
                        clip_val.extend([float(val) for val in values])

            if len(clip_val) == 1:
                clip_val = clip_val[0]
            save_json(outfile, dict(stat=clip_val))
        outputs.clip_val = clip_val

        return outputs


class MaskToolInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file or files to 3dmask_tool',
                   argstr='-input %s',
                   position=-1,
                   mandatory=True,
                   exists=True,
                   copyfile=False)

    out_file = File(name_template="%s_mask", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file")

    count = traits.Bool(desc='Instead of created a binary 0/1 mask dataset, '+
                             'create one with. counts of voxel overlap, i.e '+
                             'each voxel will contain the number of masks ' +
                             'that it is set in.',
                        argstr='-count',
                        position=2)

    datum = traits.Enum('byte','short','float',
                        argstr='-datum %s',
                        desc='specify data type for output. Valid types are '+
                             '\'byte\', \'short\' and \'float\'.')

    dilate_inputs = traits.Str(desc='Use this option to dilate and/or erode '+
                                    'datasets as they are read. ex. ' +
                                    '\'5 -5\' to dilate and erode 5 times',
                               argstr='-dilate_inputs %s')

    dilate_results = traits.Str(desc='dilate and/or erode combined mask at ' +
                                     'the given levels.',
                                argstr='-dilate_results %s')

    frac = traits.Float(desc='When combining masks (across datasets and ' +
                             'sub-bricks), use this option to restrict the ' +
                             'result to a certain fraction of the set of ' +
                             'volumes',
                        argstr='-frac %s')

    inter = traits.Bool(desc='intersection, this means -frac 1.0',
                        argstr='-inter')

    union = traits.Bool(desc='union, this means -frac 0',
                        argstr='-union')

    fill_holes = traits.Bool(desc='This option can be used to fill holes ' +
                                  'in the resulting mask, i.e. after all ' +
                                  'other processing has been done.',
                             argstr='-fill_holes')

    fill_dirs = traits.Str(desc='fill holes only in the given directions. ' +
                                'This option is for use with -fill holes. ' +
                                'should be a single string that specifies ' +
                                '1-3 of the axes using {x,y,z} labels (i.e. '+
                                'dataset axis order), or using the labels ' +
                                'in {R,L,A,P,I,S}.',
                           argstr='-fill_dirs %s',
                           requires=['fill_holes'])


class MaskToolOutputSpec(TraitedSpec):
    out_file = File(desc='mask file',
                    exists=True)


class MaskTool(AFNICommand):
    """3dmask_tool - for combining/dilating/eroding/filling masks

    For complete details, see the `3dmask_tool Documentation.
    <https://afni.nimh.nih.gov/pub../pub/dist/doc/program_help/3dmask_tool.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> automask = afni.Automask()
    >>> automask.inputs.in_file = 'functional.nii'
    >>> automask.inputs.dilate = 1
    >>> automask.inputs.outputtype = "NIFTI"
    >>> automask.cmdline #doctest: +ELLIPSIS
    '3dAutomask -apply_prefix functional_masked.nii -dilate 1 -prefix functional_mask.nii functional.nii'
    >>> res = automask.run() # doctest: +SKIP

    """

    _cmd = '3dmask_tool'
    input_spec = MaskToolInputSpec
    output_spec = MaskToolOutputSpec


class SegInputSpec(CommandLineInputSpec):
    in_file = File(desc='ANAT is the volume to segment',
                   argstr='-anat %s',
                   position=-1,
                   mandatory=True,
                   exists=True,
                   copyfile=True)

    mask = traits.Either(traits.Enum('AUTO'),
                         File(exists=True),
                         desc=('only non-zero voxels in mask are analyzed. '
                               'mask can either be a dataset or the string '
                               '"AUTO" which would use AFNI\'s automask '
                               'function to create the mask.'),
                         argstr='-mask %s',
                         position=-2,
                         mandatory=True)

    blur_meth = traits.Enum('BFT', 'BIM',
                            argstr='-blur_meth %s',
                            desc='set the blurring method for bias field estimation')

    bias_fwhm = traits.Float(desc='The amount of blurring used when estimating the field bias with the Wells method',
                             argstr='-bias_fwhm %f')

    classes = traits.Str(desc='CLASS_STRING is a semicolon delimited string of class labels',
                         argstr='-classes %s')

    bmrf = traits.Float(desc='Weighting factor controlling spatial homogeneity of the classifications',
                        argstr='-bmrf %f')

    bias_classes = traits.Str(desc='A semcolon demlimited string of classes that contribute to the estimation of the bias field',
                              argstr='-bias_classes %s')

    prefix = traits.Str(desc='the prefix for the output folder containing all output volumes',
                        argstr='-prefix %s')

    mixfrac = traits.Str(desc='MIXFRAC sets up the volume-wide (within mask) tissue fractions while initializing the segmentation (see IGNORE for exception)',
                              argstr='-mixfrac %s')

    mixfloor = traits.Float(desc='Set the minimum value for any class\'s mixing fraction',
                            argstr='-mixfloor %f')

    main_N = traits.Int(desc='Number of iterations to perform.',
                        argstr='-main_N %d')


class Seg(AFNICommandBase):
    """3dSeg segments brain volumes into tissue classes. The program allows
       for adding a variety of global and voxelwise priors. However for the
       moment, only mixing fractions and MRF are documented.

    For complete details, see the `3dSeg Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dSeg.html>

    Examples
    ========

    >>> from nipype.interfaces.afni import preprocess
    >>> seg = preprocess.Seg()
    >>> seg.inputs.in_file = 'structural.nii'
    >>> seg.inputs.mask = 'AUTO'
    >>> res = seg.run() # doctest: +SKIP

    """

    _cmd = '3dSeg'
    input_spec = SegInputSpec
    output_spec = AFNICommandOutputSpec

    def aggregate_outputs(self, runtime=None, needed_outputs=None):

        import glob

        outputs = self._outputs()

        if isdefined(self.inputs.prefix):
            outfile = os.path.join(os.getcwd(), self.inputs.prefix, 'Classes+*.BRIK')
        else:
            outfile = os.path.join(os.getcwd(), 'Segsy', 'Classes+*.BRIK')

        outputs.out_file = glob.glob(outfile)[0]

        return outputs


class ROIStatsInputSpec(CommandLineInputSpec):
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

    terminal_output = traits.Enum('allatonce',
                                  desc=('Control terminal output:'
                                        '`allatonce` - waits till command is '
                                        'finished to display output'),
                                  nohash=True, mandatory=True, usedefault=True)


class ROIStatsOutputSpec(TraitedSpec):
    stats = File(desc='output tab separated values file', exists=True)


class ROIStats(AFNICommandBase):
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
        output_filename = "roi_stats.csv"
        f = open(output_filename, "w")
        f.write(runtime.stdout)
        f.close()

        outputs.stats = os.path.abspath(output_filename)
        return outputs


class CalcInputSpec(AFNICommandInputSpec):
    in_file_a = File(desc='input file to 3dcalc',
                     argstr='-a %s', position=0, mandatory=True, exists=True)
    in_file_b = File(desc='operand file to 3dcalc',
                     argstr=' -b %s', position=1, exists=True)
    in_file_c = File(desc='operand file to 3dcalc',
                     argstr=' -c %s', position=2, exists=True)
    out_file = File(name_template="%s_calc", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file_a")
    expr = traits.Str(desc='expr', argstr='-expr "%s"', position=3,
                      mandatory=True)
    start_idx = traits.Int(desc='start index for in_file_a',
                           requires=['stop_idx'])
    stop_idx = traits.Int(desc='stop index for in_file_a',
                          requires=['start_idx'])
    single_idx = traits.Int(desc='volume index for in_file_a')
    other = File(desc='other options', argstr='')


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
    >>> calc.cmdline #doctest: +ELLIPSIS
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
        exists=True,
        copyfile=False)
    out_file = File(name_template='%s_blur', desc='output to the file', argstr='-prefix %s',
                    name_source='in_file', position=-1)
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
    >>> bim.cmdline #doctest: +ELLIPSIS
    '3dBlurInMask -input functional.nii -FWHM 5.000000 -mask mask.nii -prefix functional_blur'
    >>> res = bim.run()   # doctest: +SKIP

    """

    _cmd = '3dBlurInMask'
    input_spec = BlurInMaskInputSpec
    output_spec = AFNICommandOutputSpec


class TCorrMapInputSpec(AFNICommandInputSpec):
    in_file = File(exists=True, argstr='-input %s', mandatory=True, copyfile=False)
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
        name_source='in_file', xor=_expr_opts)
    average_expr_nonzero = File(
        argstr='-Cexpr %s %s', suffix='_cexpr',
        name_source='in_file', xor=_expr_opts)
    sum_expr = File(
        argstr='-Sexpr %s %s', suffix='_sexpr',
        name_source='in_file', xor=_expr_opts)
    histogram_bin_numbers = traits.Int()
    histogram = File(
        name_source='in_file', argstr='-Hist %d %s', suffix='_hist')


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
    >>> tcm = afni.TCorrMap()
    >>> tcm.inputs.in_file = 'functional.nii'
    >>> tcm.inputs.mask = 'mask.nii'
    >>> tcm.mean_file = '%s_meancorr.nii'
    >>> res = tcm.run()   # doctest: +SKIP

    """

    _cmd = '3dTcorrMap'
    input_spec = TCorrMapInputSpec
    output_spec = TCorrMapOutputSpec
    _additional_metadata = ['suffix']

    def _format_arg(self, name, trait_spec, value):
        if name in self.inputs._thresh_opts:
            return trait_spec.argstr % self.inputs.thresholds + [value]
        elif name in self.inputs._expr_opts:
            return trait_spec.argstr % (self.inputs.expr, value)
        elif name == 'histogram':
            return trait_spec.argstr % (self.inputs.histogram_bin_numbers,
                                        value)
        else:
            return super(TCorrMap, self)._format_arg(name, trait_spec, value)


class AutoboxInputSpec(AFNICommandInputSpec):
    in_file = File(exists=True, mandatory=True, argstr='-input %s',
                   desc='input file', copyfile=False)
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
                for k in list(d.keys()):
                    d[k] = int(d[k])
                outputs.set(**d)
        outputs.set(out_file=self._gen_filename('out_file'))
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file' and (not isdefined(self.inputs.out_file)):
            return Undefined
        return super(Autobox, self)._gen_filename(name)


class RetroicorInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dretroicor',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True,
                   copyfile=False)
    out_file = File(desc='output image file name', argstr='-prefix %s', mandatory=True, position=1)
    card = File(desc='1D cardiac data file for cardiac correction',
                argstr='-card %s',
                position=-2,
                exists=True)
    resp = File(desc='1D respiratory waveform data for correction',
                argstr='-resp %s',
                position=-3,
                exists=True)
    threshold = traits.Int(desc='Threshold for detection of R-wave peaks in input (Make sure it is above the background noise level, Try 3/4 or 4/5 times range plus minimum)',
                           argstr='-threshold %d',
                           position=-4)
    order = traits.Int(desc='The order of the correction (2 is typical)',
                       argstr='-order %s',
                       position=-5)

    cardphase = File(desc='Filename for 1D cardiac phase output',
                     argstr='-cardphase %s',
                     position=-6,
                     hash_files=False)
    respphase = File(desc='Filename for 1D resp phase output',
                     argstr='-respphase %s',
                     position=-7,
                     hash_files=False)


class Retroicor(AFNICommand):
    """Performs Retrospective Image Correction for physiological
    motion effects, using a slightly modified version of the
    RETROICOR algorithm

    The durations of the physiological inputs are assumed to equal
    the duration of the dataset. Any constant sampling rate may be
    used, but 40 Hz seems to be acceptable. This program's cardiac
    peak detection algorithm is rather simplistic, so you might try
    using the scanner's cardiac gating output (transform it to a
    spike wave if necessary).

    This program uses slice timing information embedded in the
    dataset to estimate the proper cardiac/respiratory phase for
    each slice. It makes sense to run this program before any
    program that may destroy the slice timings (e.g. 3dvolreg for
    motion correction).

    For complete details, see the `3dretroicor Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dretroicor.html>`_

    Examples
    ========
    >>> from nipype.interfaces import afni as afni
    >>> ret = afni.Retroicor()
    >>> ret.inputs.in_file = 'functional.nii'
    >>> ret.inputs.card = 'mask.1D'
    >>> ret.inputs.resp = 'resp.1D'
    >>> res = ret.run()   # doctest: +SKIP
    """

    _cmd = '3dretroicor'
    input_spec = RetroicorInputSpec
    output_spec = AFNICommandOutputSpec


class AFNItoNIFTIInputSpec(AFNICommandInputSpec):
    in_file = File(desc='input file to 3dAFNItoNIFTI',
                   argstr='%s',
                   position=-1,
                   mandatory=True,
                   exists=True,
                   copyfile=False)
    out_file = File(name_template="%s.nii", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file")
    hash_files = False


class AFNItoNIFTI(AFNICommand):
    """Changes AFNI format files to NIFTI format using 3dAFNItoNIFTI

    see AFNI Documentation: <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAFNItoNIFTI.html>
    this can also convert 2D or 1D data, which you can numpy.squeeze() to remove extra dimensions

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> a2n = afni.AFNItoNIFTI()
    >>> a2n.inputs.in_file = 'afni_output.3D'
    >>> a2n.inputs.out_file =  'afni_output.nii'
    >>> a2n.cmdline
    '3dAFNItoNIFTI -prefix afni_output.nii afni_output.3D'

    """

    _cmd = '3dAFNItoNIFTI'
    input_spec = AFNItoNIFTIInputSpec
    output_spec = AFNICommandOutputSpec

    def _overload_extension(self, value):
        path, base, ext = split_filename(value)
        if ext.lower() not in [".1d", ".nii.gz", ".1D"]:
            ext = ext + ".nii"
        return os.path.join(path, base + ext)

    def _gen_filename(self, name):
        return os.path.abspath(super(AFNItoNIFTI, self)._gen_filename(name))


class EvalInputSpec(AFNICommandInputSpec):
    in_file_a = File(desc='input file to 1deval',
                     argstr='-a %s', position=0, mandatory=True, exists=True)
    in_file_b = File(desc='operand file to 1deval',
                     argstr=' -b %s', position=1, exists=True)
    in_file_c = File(desc='operand file to 1deval',
                     argstr=' -c %s', position=2, exists=True)
    out_file = File(name_template="%s_calc", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file_a")
    out1D = traits.Bool(desc="output in 1D",
                        argstr='-1D')
    expr = traits.Str(desc='expr', argstr='-expr "%s"', position=3,
                      mandatory=True)
    start_idx = traits.Int(desc='start index for in_file_a',
                           requires=['stop_idx'])
    stop_idx = traits.Int(desc='stop index for in_file_a',
                          requires=['start_idx'])
    single_idx = traits.Int(desc='volume index for in_file_a')
    other = File(desc='other options', argstr='')


class Eval(AFNICommand):
    """Evaluates an expression that may include columns of data from one or more text files

    see AFNI Documentation: <http://afni.nimh.nih.gov/pub/dist/doc/program_help/1deval.html>

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> eval = afni.Eval()
    >>> eval.inputs.in_file_a = 'seed.1D'
    >>> eval.inputs.in_file_b = 'resp.1D'
    >>> eval.inputs.expr='a*b'
    >>> eval.inputs.out1D = True
    >>> eval.inputs.out_file =  'data_calc.1D'
    >>> calc.cmdline #doctest: +SKIP
    '3deval -a timeseries1.1D  -b timeseries2.1D -expr "a*b" -1D -prefix data_calc.1D'

    """

    _cmd = '1deval'
    input_spec = EvalInputSpec
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
        return super(Eval, self)._format_arg(name, trait_spec, value)

    def _parse_inputs(self, skip=None):
        """Skip the arguments without argstr metadata
        """
        return super(Eval, self)._parse_inputs(
            skip=('start_idx', 'stop_idx', 'out1D', 'other'))


class MeansInputSpec(AFNICommandInputSpec):
    in_file_a = File(desc='input file to 3dMean',
                     argstr='%s',
                     position=0,
                     mandatory=True,
                     exists=True)
    in_file_b = File(desc='another input file to 3dMean',
                     argstr='%s',
                     position=1,
                     exists=True)
    out_file = File(name_template="%s_mean", desc='output image file name',
                    argstr='-prefix %s', name_source="in_file_a")
    scale = traits.Str(desc='scaling of output', argstr='-%sscale')
    non_zero = traits.Bool(desc='use only non-zero values', argstr='-non_zero')
    std_dev = traits.Bool(desc='calculate std dev', argstr='-stdev')
    sqr = traits.Bool(desc='mean square instead of value', argstr='-sqr')
    summ = traits.Bool(desc='take sum, (not average)', argstr='-sum')
    count = traits.Bool(desc='compute count of non-zero voxels', argstr='-count')
    mask_inter = traits.Bool(desc='create intersection mask', argstr='-mask_inter')
    mask_union = traits.Bool(desc='create union mask', argstr='-mask_union')


class Means(AFNICommand):
    """Takes the voxel-by-voxel mean of all input datasets using 3dMean

    see AFNI Documentation: <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dMean.html>

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> means = afni.Means()
    >>> means.inputs.in_file_a = 'im1.nii'
    >>> means.inputs.in_file_b = 'im2.nii'
    >>> means.inputs.out_file =  'output.nii'
    >>> means.cmdline
    '3dMean im1.nii im2.nii -prefix output.nii'

    """

    _cmd = '3dMean'
    input_spec = MeansInputSpec
    output_spec = AFNICommandOutputSpec


class HistInputSpec(CommandLineInputSpec):
    in_file = File(
        desc='input file to 3dHist', argstr='-input %s', position=1, mandatory=True,
        exists=True, copyfile=False)
    out_file = File(
        desc='Write histogram to niml file with this prefix', name_template='%s_hist',
        keep_extension=False, argstr='-prefix %s', name_source=['in_file'])
    showhist = traits.Bool(False, usedefault=True, desc='write a text visual histogram',
                           argstr='-showhist')
    out_show = File(
        name_template="%s_hist.out", desc='output image file name', keep_extension=False,
        argstr="> %s", name_source="in_file", position=-1)
    mask = File(desc='matrix to align input file', argstr='-mask %s', exists=True)
    nbin = traits.Int(desc='number of bins', argstr='-nbin %d')
    max_value = traits.Float(argstr='-max %f', desc='maximum intensity value')
    min_value = traits.Float(argstr='-min %f', desc='minimum intensity value')
    bin_width = traits.Float(argstr='-binwidth %f', desc='bin width')

class HistOutputSpec(TraitedSpec):
    out_file = File(desc='output file', exists=True)
    out_show = File(desc='output visual histogram')


class Hist(AFNICommandBase):
    """Computes average of all voxels in the input dataset
    which satisfy the criterion in the options list

    For complete details, see the `3dHist Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dHist.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> hist = afni.Hist()
    >>> hist.inputs.in_file = 'functional.nii'
    >>> hist.cmdline
    '3dHist -input functional.nii -prefix functional_hist'
    >>> res = hist.run() # doctest: +SKIP

    """

    _cmd = '3dHist'
    input_spec = HistInputSpec
    output_spec = HistOutputSpec
    _redirect_x = True

    def __init__(self, **inputs):
        super(Hist, self).__init__(**inputs)
        if not no_afni():
            version = Info.version()

            # As of AFNI 16.0.00, redirect_x is not needed
            if isinstance(version[0], int) and version[0] > 15:
                self._redirect_x = False

    def _parse_inputs(self, skip=None):
        if not self.inputs.showhist:
            if skip is None:
                skip = []
            skip += ['out_show']
        return super(Hist, self)._parse_inputs(skip=skip)


    def _list_outputs(self):
        outputs = super(Hist, self)._list_outputs()
        outputs['out_file'] += '.niml.hist'
        if not self.inputs.showhist:
            outputs['out_show'] = Undefined
        return outputs


class FWHMxInputSpec(CommandLineInputSpec):
    in_file = File(desc='input dataset', argstr='-input %s', mandatory=True, exists=True)
    out_file = File(argstr='> %s', name_source='in_file', name_template='%s_fwhmx.out',
                    position=-1, keep_extension=False, desc='output file')
    out_subbricks = File(argstr='-out %s', name_source='in_file', name_template='%s_subbricks.out',
                         keep_extension=False, desc='output file listing the subbricks FWHM')
    mask = File(desc='use only voxels that are nonzero in mask', argstr='-mask %s', exists=True)
    automask = traits.Bool(False, usedefault=True, argstr='-automask',
                           desc='compute a mask from THIS dataset, a la 3dAutomask')
    detrend = traits.Either(
        traits.Bool(), traits.Int(), default=False, argstr='-detrend', xor=['demed'], usedefault=True,
        desc='instead of demed (0th order detrending), detrend to the specified order.  If order '
             'is not given, the program picks q=NT/30. -detrend disables -demed, and includes '
             '-unif.')
    demed = traits.Bool(
        False, argstr='-demed', xor=['detrend'],
        desc='If the input dataset has more than one sub-brick (e.g., has a time axis), then '
             'subtract the median of each voxel\'s time series before processing FWHM. This will '
             'tend to remove intrinsic spatial structure and leave behind the noise.')
    unif = traits.Bool(False, argstr='-unif',
                       desc='If the input dataset has more than one sub-brick, then normalize each'
                            ' voxel\'s time series to have the same MAD before processing FWHM.')
    out_detrend = File(argstr='-detprefix %s', name_source='in_file', name_template='%s_detrend',
                       keep_extension=False, desc='Save the detrended file into a dataset')
    geom = traits.Bool(argstr='-geom', xor=['arith'],
                       desc='if in_file has more than one sub-brick, compute the final estimate as'
                            'the geometric mean of the individual sub-brick FWHM estimates')
    arith = traits.Bool(argstr='-arith', xor=['geom'],
                        desc='if in_file has more than one sub-brick, compute the final estimate as'
                             'the arithmetic mean of the individual sub-brick FWHM estimates')
    combine = traits.Bool(argstr='-combine', desc='combine the final measurements along each axis')
    compat = traits.Bool(argstr='-compat', desc='be compatible with the older 3dFWHM')
    acf = traits.Either(
        traits.Bool(), File(), traits.Tuple(File(exists=True), traits.Float()),
        default=False, usedefault=True, argstr='-acf', desc='computes the spatial autocorrelation')


class FWHMxOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='output file')
    out_subbricks = File(exists=True, desc='output file (subbricks)')
    out_detrend = File(desc='output file, detrended')
    fwhm = traits.Either(
        traits.Tuple(traits.Float(), traits.Float(), traits.Float()),
        traits.Tuple(traits.Float(), traits.Float(), traits.Float(), traits.Float()),
        desc='FWHM along each axis')
    acf_param = traits.Either(
        traits.Tuple(traits.Float(), traits.Float(), traits.Float()),
        traits.Tuple(traits.Float(), traits.Float(), traits.Float(), traits.Float()),
        desc='fitted ACF model parameters')
    out_acf = File(exists=True, desc='output acf file')


class FWHMx(AFNICommandBase):
    """
    Unlike the older 3dFWHM, this program computes FWHMs for all sub-bricks
    in the input dataset, each one separately.  The output for each one is
    written to the file specified by '-out'.  The mean (arithmetic or geometric)
    of all the FWHMs along each axis is written to stdout.  (A non-positive
    output value indicates something bad happened; e.g., FWHM in z is meaningless
    for a 2D dataset; the estimation method computed incoherent intermediate results.)

    Examples
    --------

    >>> from nipype.interfaces import afni as afp
    >>> fwhm = afp.FWHMx()
    >>> fwhm.inputs.in_file = 'functional.nii'
    >>> fwhm.cmdline
    '3dFWHMx -input functional.nii -out functional_subbricks.out > functional_fwhmx.out'


    (Classic) METHOD:

      * Calculate ratio of variance of first differences to data variance.
      * Should be the same as 3dFWHM for a 1-brick dataset.
        (But the output format is simpler to use in a script.)


    .. note:: IMPORTANT NOTE [AFNI > 16]

      A completely new method for estimating and using noise smoothness values is
      now available in 3dFWHMx and 3dClustSim. This method is implemented in the
      '-acf' options to both programs.  'ACF' stands for (spatial) AutoCorrelation
      Function, and it is estimated by calculating moments of differences out to
      a larger radius than before.

      Notably, real FMRI data does not actually have a Gaussian-shaped ACF, so the
      estimated ACF is then fit (in 3dFWHMx) to a mixed model (Gaussian plus
      mono-exponential) of the form

        .. math::

          ACF(r) = a * exp(-r*r/(2*b*b)) + (1-a)*exp(-r/c)


      where :math:`r` is the radius, and :math:`a, b, c` are the fitted parameters.
      The apparent FWHM from this model is usually somewhat larger in real data
      than the FWHM estimated from just the nearest-neighbor differences used
      in the 'classic' analysis.

      The longer tails provided by the mono-exponential are also significant.
      3dClustSim has also been modified to use the ACF model given above to generate
      noise random fields.


    .. note:: TL;DR or summary

      The take-awaymessage is that the 'classic' 3dFWHMx and
      3dClustSim analysis, using a pure Gaussian ACF, is not very correct for
      FMRI data -- I cannot speak for PET or MEG data.


    .. warning::

      Do NOT use 3dFWHMx on the statistical results (e.g., '-bucket') from
      3dDeconvolve or 3dREMLfit!!!  The function of 3dFWHMx is to estimate
      the smoothness of the time series NOISE, not of the statistics. This
      proscription is especially true if you plan to use 3dClustSim next!!


    .. note:: Recommendations

      * For FMRI statistical purposes, you DO NOT want the FWHM to reflect
        the spatial structure of the underlying anatomy.  Rather, you want
        the FWHM to reflect the spatial structure of the noise.  This means
        that the input dataset should not have anatomical (spatial) structure.
      * One good form of input is the output of '3dDeconvolve -errts', which is
        the dataset of residuals left over after the GLM fitted signal model is
        subtracted out from each voxel's time series.
      * If you don't want to go to that much trouble, use '-detrend' to approximately
        subtract out the anatomical spatial structure, OR use the output of 3dDetrend
        for the same purpose.
      * If you do not use '-detrend', the program attempts to find non-zero spatial
        structure in the input, and will print a warning message if it is detected.


    .. note:: Notes on -demend

      * I recommend this option, and it is not the default only for historical
        compatibility reasons.  It may become the default someday.
      * It is already the default in program 3dBlurToFWHM. This is the same detrending
        as done in 3dDespike; using 2*q+3 basis functions for q > 0.
      * If you don't use '-detrend', the program now [Aug 2010] checks if a large number
        of voxels are have significant nonzero means. If so, the program will print a
        warning message suggesting the use of '-detrend', since inherent spatial
        structure in the image will bias the estimation of the FWHM of the image time
        series NOISE (which is usually the point of using 3dFWHMx).


    """
    _cmd = '3dFWHMx'
    input_spec = FWHMxInputSpec
    output_spec = FWHMxOutputSpec
    _acf = True

    def _parse_inputs(self, skip=None):
        if not self.inputs.detrend:
            if skip is None:
                skip = []
            skip += ['out_detrend']
        return super(FWHMx, self)._parse_inputs(skip=skip)

    def _format_arg(self, name, trait_spec, value):
        if name == 'detrend':
            if isinstance(value, bool):
                if value:
                    return trait_spec.argstr
                else:
                    return None
            elif isinstance(value, int):
                return trait_spec.argstr + ' %d' % value

        if name == 'acf':
            if isinstance(value, bool):
                if value:
                    return trait_spec.argstr
                else:
                    self._acf = False
                    return None
            elif isinstance(value, tuple):
                return trait_spec.argstr + ' %s %f' % value
            elif isinstance(value, string_types):
                return trait_spec.argstr + ' ' + value
        return super(FWHMx, self)._format_arg(name, trait_spec, value)

    def _list_outputs(self):
        outputs = super(FWHMx, self)._list_outputs()

        if self.inputs.detrend:
            fname, ext = op.splitext(self.inputs.in_file)
            if '.gz' in ext:
                _, ext2 = op.splitext(fname)
                ext = ext2 + ext
            outputs['out_detrend'] += ext
        else:
            outputs['out_detrend'] = Undefined

        sout = np.loadtxt(outputs['out_file'])  #pylint: disable=E1101
        if self._acf:
            outputs['acf_param'] = tuple(sout[1])
            sout = tuple(sout[0])

            outputs['out_acf'] = op.abspath('3dFWHMx.1D')
            if isinstance(self.inputs.acf, string_types):
                outputs['out_acf'] = op.abspath(self.inputs.acf)

        outputs['fwhm'] = tuple(sout)
        return outputs


class OutlierCountInputSpec(CommandLineInputSpec):
    in_file = File(argstr='%s', mandatory=True, exists=True, position=-2, desc='input dataset')
    mask = File(exists=True, argstr='-mask %s', xor=['autoclip', 'automask'],
                desc='only count voxels within the given mask')
    qthr = traits.Range(value=1e-3, low=0.0, high=1.0, argstr='-qthr %.5f',
                        desc='indicate a value for q to compute alpha')

    autoclip = traits.Bool(False, usedefault=True, argstr='-autoclip', xor=['in_file'],
                           desc='clip off small voxels')
    automask = traits.Bool(False, usedefault=True, argstr='-automask', xor=['in_file'],
                           desc='clip off small voxels')

    fraction = traits.Bool(False, usedefault=True, argstr='-fraction',
                           desc='write out the fraction of masked voxels'
                                ' which are outliers at each timepoint')
    interval = traits.Bool(False, usedefault=True, argstr='-range',
                           desc='write out the median + 3.5 MAD of outlier'
                                ' count with each timepoint')
    save_outliers = traits.Bool(False, usedefault=True, desc='enables out_file option')
    outliers_file = File(
        name_template="%s_outliers", argstr='-save %s', name_source=["in_file"],
        output_name='out_outliers', keep_extension=True, desc='output image file name')

    polort = traits.Int(argstr='-polort %d',
                        desc='detrend each voxel timeseries with polynomials')
    legendre = traits.Bool(False, usedefault=True, argstr='-legendre',
                           desc='use Legendre polynomials')
    out_file = File(
        name_template='%s_outliers', name_source=['in_file'], argstr='> %s',
        keep_extension=False, position=-1, desc='capture standard output')


class OutlierCountOutputSpec(TraitedSpec):
    out_outliers = File(exists=True, desc='output image file name')
    out_file = File(
        name_template='%s_tqual', name_source=['in_file'], argstr='> %s',
        keep_extension=False, position=-1, desc='capture standard output')


class OutlierCount(CommandLine):
    """Create a 3D dataset from 2D image files using AFNI to3d command

    For complete details, see the `to3d Documentation
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/to3d.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> toutcount = afni.OutlierCount()
    >>> toutcount.inputs.in_file = 'functional.nii'
    >>> toutcount.cmdline #doctest: +ELLIPSIS
    '3dToutcount functional.nii > functional_outliers'
    >>> res = toutcount.run() #doctest: +SKIP

   """

    _cmd = '3dToutcount'
    input_spec = OutlierCountInputSpec
    output_spec = OutlierCountOutputSpec

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []

        if not self.inputs.save_outliers:
            skip += ['outliers_file']
        return super(OutlierCount, self)._parse_inputs(skip)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if self.inputs.save_outliers:
            outputs['out_outliers'] = op.abspath(self.inputs.outliers_file)
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs


class QualityIndexInputSpec(CommandLineInputSpec):
    in_file = File(argstr='%s', mandatory=True, exists=True, position=-2, desc='input dataset')
    mask = File(exists=True, argstr='-mask %s', xor=['autoclip', 'automask'],
                desc='compute correlation only across masked voxels')
    spearman = traits.Bool(False, usedefault=True, argstr='-spearman',
                           desc='Quality index is 1 minus the Spearman (rank) '
                                'correlation coefficient of each sub-brick '
                                'with the median sub-brick. (default)')
    quadrant = traits.Bool(False, usedefault=True, argstr='-quadrant',
                           desc='Similar to -spearman, but using 1 minus the '
                                'quadrant correlation coefficient as the '
                                'quality index.')
    autoclip = traits.Bool(False, usedefault=True, argstr='-autoclip', xor=['mask'],
                           desc='clip off small voxels')
    automask = traits.Bool(False, usedefault=True, argstr='-automask', xor=['mask'],
                           desc='clip off small voxels')
    clip = traits.Float(argstr='-clip %f', desc='clip off values below')

    interval = traits.Bool(False, usedefault=True, argstr='-range',
                           desc='write out the median + 3.5 MAD of outlier'
                                ' count with each timepoint')
    out_file = File(
        name_template='%s_tqual', name_source=['in_file'], argstr='> %s',
        keep_extension=False, position=-1, desc='capture standard output')


class QualityIndexOutputSpec(TraitedSpec):
    out_file = File(desc='file containing the caputured standard output')


class QualityIndex(CommandLine):
    """Create a 3D dataset from 2D image files using AFNI to3d command

    For complete details, see the `to3d Documentation
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/to3d.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> tqual = afni.QualityIndex()
    >>> tqual.inputs.in_file = 'functional.nii'
    >>> tqual.cmdline #doctest: +ELLIPSIS
    '3dTqual functional.nii > functional_tqual'
    >>> res = tqual.run() #doctest: +SKIP

   """

    _cmd = '3dTqual'
    input_spec = QualityIndexInputSpec
    output_spec = QualityIndexOutputSpec
