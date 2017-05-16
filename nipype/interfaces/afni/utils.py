# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft = python sts = 4 ts = 4 sw = 4 et:
"""AFNI utility interfaces

Examples
--------
See the docstrings of the individual classes for examples.
  .. testsetup::
    # Change directory to provide relative paths for doctests
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""
from __future__ import print_function, division, unicode_literals, absolute_import
from builtins import str, bytes

import os
import os.path as op
import re
import numpy as np

from ...utils.filemanip import (load_json, save_json, split_filename)
from ..base import (
    CommandLineInputSpec, CommandLine, Directory, TraitedSpec,
    traits, isdefined, File, InputMultiPath, Undefined, Str)
from ...external.due import BibTeX

from .base import (
    AFNICommandBase, AFNICommand, AFNICommandInputSpec, AFNICommandOutputSpec)


class AFNItoNIFTIInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3dAFNItoNIFTI',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        name_template='%s.nii',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file',
        hash_files=False)
    float_ = traits.Bool(
        desc='Force the output dataset to be 32-bit floats. This option '
             'should be used when the input AFNI dataset has different float '
             'scale factors for different sub-bricks, an option that '
             'NIfTI-1.1 does not support.',
        argstr='-float')
    pure = traits.Bool(
        desc='Do NOT write an AFNI extension field into the output file. Only '
             'use this option if needed. You can also use the \'nifti_tool\' '
             'program to strip extensions from a file.',
        argstr='-pure')
    denote = traits.Bool(
        desc='When writing the AFNI extension field, remove text notes that '
             'might contain subject identifying information.',
        argstr='-denote')
    oldid = traits.Bool(
        desc='Give the new dataset the input dataset''s AFNI ID code.',
        argstr='-oldid',
        xor=['newid'])
    newid = traits.Bool(
        desc='Give the new dataset a new AFNI ID code, to distinguish it from '
             'the input dataset.',
        argstr='-newid',
        xor=['oldid'])


class AFNItoNIFTI(AFNICommand):
    """Converts AFNI format files to NIFTI format. This can also convert 2D or
    1D data, which you can numpy.squeeze() to remove extra dimensions.

    For complete details, see the `3dAFNItoNIFTI Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAFNItoNIFTI.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> a2n = afni.AFNItoNIFTI()
    >>> a2n.inputs.in_file = 'afni_output.3D'
    >>> a2n.inputs.out_file =  'afni_output.nii'
    >>> a2n.cmdline  # doctest: +ALLOW_UNICODE
    '3dAFNItoNIFTI -prefix afni_output.nii afni_output.3D'
    >>> res = a2n.run()  # doctest: +SKIP

    """

    _cmd = '3dAFNItoNIFTI'
    input_spec = AFNItoNIFTIInputSpec
    output_spec = AFNICommandOutputSpec

    def _overload_extension(self, value):
        path, base, ext = split_filename(value)
        if ext.lower() not in ['.nii', '.nii.gz', '.1d', '.1D']:
            ext += '.nii'
        return os.path.join(path, base + ext)

    def _gen_filename(self, name):
        return os.path.abspath(super(AFNItoNIFTI, self)._gen_filename(name))


class AutoboxInputSpec(AFNICommandInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr='-input %s',
        desc='input file',
        copyfile=False)
    padding = traits.Int(
        argstr='-npad %d',
        desc='Number of extra voxels to pad on each side of box')
    out_file = File(
        argstr='-prefix %s',
        name_source='in_file',
        name_template='%s_autobox')
    no_clustering = traits.Bool(
        argstr='-noclust',
        desc='Don\'t do any clustering to find box. Any non-zero voxel will '
             'be preserved in the cropped volume. The default method uses '
             'some clustering to find the cropping box, and will clip off '
             'small isolated blobs.')


class AutoboxOutputSpec(TraitedSpec):  # out_file not mandatory
    x_min = traits.Int()
    x_max = traits.Int()
    y_min = traits.Int()
    y_max = traits.Int()
    z_min = traits.Int()
    z_max = traits.Int()

    out_file = File(
        desc='output file')


class Autobox(AFNICommand):
    """Computes size of a box that fits around the volume.
    Also can be used to crop the volume to that box.

    For complete details, see the `3dAutobox Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAutobox.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> abox = afni.Autobox()
    >>> abox.inputs.in_file = 'structural.nii'
    >>> abox.inputs.padding = 5
    >>> abox.cmdline  # doctest: +ALLOW_UNICODE
    '3dAutobox -input structural.nii -prefix structural_autobox -npad 5'
    >>> res = abox.run()  # doctest: +SKIP

    """

    _cmd = '3dAutobox'
    input_spec = AutoboxInputSpec
    output_spec = AutoboxOutputSpec

    def aggregate_outputs(self, runtime=None, needed_outputs=None):
        outputs = super(Autobox, self).aggregate_outputs(runtime, needed_outputs)
        pattern = 'x=(?P<x_min>-?\d+)\.\.(?P<x_max>-?\d+)  '\
                  'y=(?P<y_min>-?\d+)\.\.(?P<y_max>-?\d+)  '\
                  'z=(?P<z_min>-?\d+)\.\.(?P<z_max>-?\d+)'
        for line in runtime.stderr.split('\n'):
            m = re.search(pattern, line)
            if m:
                d = m.groupdict()
                for k in list(d.keys()):
                    d[k] = int(d[k])
                outputs.set(**d)
        return outputs



class BrickStatInputSpec(CommandLineInputSpec):
    in_file = File(
        desc='input file to 3dmaskave',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)
    mask = File(
        desc='-mask dset = use dset as mask to include/exclude voxels',
        argstr='-mask %s',
        position=2,
        exists=True)
    min = traits.Bool(
        desc='print the minimum value in dataset',
        argstr='-min',
        position=1)


class BrickStatOutputSpec(TraitedSpec):
    min_val = traits.Float(
        desc='output')


class BrickStat(AFNICommandBase):
    """Computes maximum and/or minimum voxel values of an input dataset.
    TODO Add optional arguments.

    For complete details, see the `3dBrickStat Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dBrickStat.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> brickstat = afni.BrickStat()
    >>> brickstat.inputs.in_file = 'functional.nii'
    >>> brickstat.inputs.mask = 'skeleton_mask.nii.gz'
    >>> brickstat.inputs.min = True
    >>> brickstat.cmdline  # doctest: +ALLOW_UNICODE
    '3dBrickStat -min -mask skeleton_mask.nii.gz functional.nii'
    >>> res = brickstat.run()  # doctest: +SKIP

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


class CalcInputSpec(AFNICommandInputSpec):
    in_file_a = File(
        desc='input file to 3dcalc',
        argstr='-a %s',
        position=0,
        mandatory=True,
        exists=True)
    in_file_b = File(
        desc='operand file to 3dcalc',
        argstr='-b %s',
        position=1,
        exists=True)
    in_file_c = File(
        desc='operand file to 3dcalc',
        argstr='-c %s',
        position=2,
        exists=True)
    out_file = File(
        name_template='%s_calc',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file_a')
    expr = Str(
        desc='expr',
        argstr='-expr "%s"',
        position=3,
        mandatory=True)
    start_idx = traits.Int(
        desc='start index for in_file_a',
        requires=['stop_idx'])
    stop_idx = traits.Int(
        desc='stop index for in_file_a',
        requires=['start_idx'])
    single_idx = traits.Int(
        desc='volume index for in_file_a')
    other = File(
        desc='other options',
        argstr='')


class Calc(AFNICommand):
    """This program does voxel-by-voxel arithmetic on 3D datasets.

    For complete details, see the `3dcalc Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dcalc.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> calc = afni.Calc()
    >>> calc.inputs.in_file_a = 'functional.nii'
    >>> calc.inputs.in_file_b = 'functional2.nii'
    >>> calc.inputs.expr='a*b'
    >>> calc.inputs.out_file =  'functional_calc.nii.gz'
    >>> calc.inputs.outputtype = 'NIFTI'
    >>> calc.cmdline  # doctest: +ELLIPSIS +ALLOW_UNICODE
    '3dcalc -a functional.nii -b functional2.nii -expr "a*b" -prefix functional_calc.nii.gz'
    >>> res = calc.run()  # doctest: +SKIP

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


class CopyInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3dcopy',
        argstr='%s',
        position=-2,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        name_template='%s_copy',
        desc='output image file name',
        argstr='%s',
        position=-1,
        name_source='in_file')


class Copy(AFNICommand):
    """Copies an image of one type to an image of the same
    or different type using 3dcopy command

    For complete details, see the `3dcopy Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dcopy.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> copy3d = afni.Copy()
    >>> copy3d.inputs.in_file = 'functional.nii'
    >>> copy3d.cmdline  # doctest: +ALLOW_UNICODE
    '3dcopy functional.nii functional_copy'
    >>> res = copy3d.run()  # doctest: +SKIP

    >>> from copy import deepcopy
    >>> copy3d_2 = deepcopy(copy3d)
    >>> copy3d_2.inputs.outputtype = 'NIFTI'
    >>> copy3d_2.cmdline  # doctest: +ALLOW_UNICODE
    '3dcopy functional.nii functional_copy.nii'
    >>> res = copy3d_2.run()  # doctest: +SKIP

    >>> copy3d_3 = deepcopy(copy3d)
    >>> copy3d_3.inputs.outputtype = 'NIFTI_GZ'
    >>> copy3d_3.cmdline  # doctest: +ALLOW_UNICODE
    '3dcopy functional.nii functional_copy.nii.gz'
    >>> res = copy3d_3.run()  # doctest: +SKIP

    >>> copy3d_4 = deepcopy(copy3d)
    >>> copy3d_4.inputs.out_file = 'new_func.nii'
    >>> copy3d_4.cmdline  # doctest: +ALLOW_UNICODE
    '3dcopy functional.nii new_func.nii'
    >>> res = copy3d_4.run()  # doctest: +SKIP

    """

    _cmd = '3dcopy'
    input_spec = CopyInputSpec
    output_spec = AFNICommandOutputSpec


class EvalInputSpec(AFNICommandInputSpec):
    in_file_a = File(
        desc='input file to 1deval',
        argstr='-a %s',
        position=0,
        mandatory=True,
        exists=True)
    in_file_b = File(
        desc='operand file to 1deval',
        argstr='-b %s',
        position=1,
        exists=True)
    in_file_c = File(
        desc='operand file to 1deval',
        argstr='-c %s',
        position=2,
        exists=True)
    out_file = File(
        name_template='%s_calc',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file_a')
    out1D = traits.Bool(
        desc='output in 1D',
        argstr='-1D')
    expr = Str(
        desc='expr',
        argstr='-expr "%s"',
        position=3,
        mandatory=True)
    start_idx = traits.Int(
        desc='start index for in_file_a',
        requires=['stop_idx'])
    stop_idx = traits.Int(
        desc='stop index for in_file_a',
        requires=['start_idx'])
    single_idx = traits.Int(
        desc='volume index for in_file_a')
    other = File(
        desc='other options',
        argstr='')


class Eval(AFNICommand):
    """Evaluates an expression that may include columns of data from one or
    more text files.

    For complete details, see the `1deval Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/1deval.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> eval = afni.Eval()
    >>> eval.inputs.in_file_a = 'seed.1D'
    >>> eval.inputs.in_file_b = 'resp.1D'
    >>> eval.inputs.expr = 'a*b'
    >>> eval.inputs.out1D = True
    >>> eval.inputs.out_file =  'data_calc.1D'
    >>> eval.cmdline  # doctest: +ALLOW_UNICODE
    '1deval -a seed.1D -b resp.1D -expr "a*b" -1D -prefix data_calc.1D'
    >>> res = eval.run()  # doctest: +SKIP

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
            skip=('start_idx', 'stop_idx', 'other'))


class FWHMxInputSpec(CommandLineInputSpec):
    in_file = File(
        desc='input dataset',
        argstr='-input %s',
        mandatory=True,
        exists=True)
    out_file = File(
        argstr='> %s',
        name_source='in_file',
        name_template='%s_fwhmx.out',
        position=-1,
        keep_extension=False,
        desc='output file')
    out_subbricks = File(
        argstr='-out %s',
        name_source='in_file',
        name_template='%s_subbricks.out',
        keep_extension=False,
        desc='output file listing the subbricks FWHM')
    mask = File(
        desc='use only voxels that are nonzero in mask',
        argstr='-mask %s',
        exists=True)
    automask = traits.Bool(
        False,
        usedefault=True,
        argstr='-automask',
        desc='compute a mask from THIS dataset, a la 3dAutomask')
    detrend = traits.Either(
        traits.Bool(), traits.Int(),
        default=False,
        argstr='-detrend',
        xor=['demed'],
        usedefault=True,
        desc='instead of demed (0th order detrending), detrend to the '
             'specified order.  If order is not given, the program picks '
             'q=NT/30. -detrend disables -demed, and includes -unif.')
    demed = traits.Bool(
        False,
        argstr='-demed',
        xor=['detrend'],
        desc='If the input dataset has more than one sub-brick (e.g., has a '
             'time axis), then subtract the median of each voxel\'s time '
             'series before processing FWHM. This will tend to remove '
             'intrinsic spatial structure and leave behind the noise.')
    unif = traits.Bool(
        False,
        argstr='-unif',
        desc='If the input dataset has more than one sub-brick, then '
             'normalize each voxel\'s time series to have the same MAD before '
             'processing FWHM.')
    out_detrend = File(
        argstr='-detprefix %s',
        name_source='in_file',
        name_template='%s_detrend',
        keep_extension=False,
        desc='Save the detrended file into a dataset')
    geom = traits.Bool(
        argstr='-geom',
        xor=['arith'],
        desc='if in_file has more than one sub-brick, compute the final '
             'estimate as the geometric mean of the individual sub-brick FWHM '
             'estimates')
    arith = traits.Bool(
        argstr='-arith',
        xor=['geom'],
        desc='if in_file has more than one sub-brick, compute the final '
             'estimate as the arithmetic mean of the individual sub-brick '
             'FWHM estimates')
    combine = traits.Bool(
        argstr='-combine',
        desc='combine the final measurements along each axis')
    compat = traits.Bool(
        argstr='-compat',
        desc='be compatible with the older 3dFWHM')
    acf = traits.Either(
        traits.Bool(), File(), traits.Tuple(File(exists=True), traits.Float()),
        default=False,
        usedefault=True,
        argstr='-acf',
        desc='computes the spatial autocorrelation')


class FWHMxOutputSpec(TraitedSpec):
    out_file = File(
        exists=True,
        desc='output file')
    out_subbricks = File(
        exists=True,
        desc='output file (subbricks)')
    out_detrend = File(
        desc='output file, detrended')
    fwhm = traits.Either(
        traits.Tuple(traits.Float(), traits.Float(), traits.Float()),
        traits.Tuple(traits.Float(), traits.Float(), traits.Float(), traits.Float()),
        desc='FWHM along each axis')
    acf_param = traits.Either(
        traits.Tuple(traits.Float(), traits.Float(), traits.Float()),
        traits.Tuple(traits.Float(), traits.Float(), traits.Float(), traits.Float()),
        desc='fitted ACF model parameters')
    out_acf = File(
        exists=True,
        desc='output acf file')


class FWHMx(AFNICommandBase):
    """
    Unlike the older 3dFWHM, this program computes FWHMs for all sub-bricks
    in the input dataset, each one separately.  The output for each one is
    written to the file specified by '-out'.  The mean (arithmetic or geometric)
    of all the FWHMs along each axis is written to stdout.  (A non-positive
    output value indicates something bad happened; e.g., FWHM in z is meaningless
    for a 2D dataset; the estimation method computed incoherent intermediate results.)

    For complete details, see the `3dFWHMx Documentation.
    <https://afni.nimh.nih.gov/pub../pub/dist/doc/program_help/3dFWHMx.html>`_

    Examples
    --------

    >>> from nipype.interfaces import afni
    >>> fwhm = afni.FWHMx()
    >>> fwhm.inputs.in_file = 'functional.nii'
    >>> fwhm.cmdline  # doctest: +ALLOW_UNICODE
    '3dFWHMx -input functional.nii -out functional_subbricks.out > functional_fwhmx.out'
    >>> res = fwhm.run()  # doctest: +SKIP


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

    references_ = [{'entry': BibTeX('@article{CoxReynoldsTaylor2016,'
                                    'author={R.W. Cox, R.C. Reynolds, and P.A. Taylor},'
                                    'title={AFNI and clustering: false positive rates redux},'
                                    'journal={bioRxiv},'
                                    'year={2016},'
                                    '}'),
                    'tags': ['method'],
                    },
                   ]
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
            elif isinstance(value, (str, bytes)):
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
            if isinstance(self.inputs.acf, (str, bytes)):
                outputs['out_acf'] = op.abspath(self.inputs.acf)

        outputs['fwhm'] = tuple(sout)
        return outputs


class MaskToolInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file or files to 3dmask_tool',
        argstr='-input %s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        name_template='%s_mask',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file')
    count = traits.Bool(
        desc='Instead of created a binary 0/1 mask dataset, create one with '
             'counts of voxel overlap, i.e., each voxel will contain the '
             'number of masks that it is set in.',
        argstr='-count',
        position=2)
    datum = traits.Enum(
        'byte','short','float',
        argstr='-datum %s',
        desc='specify data type for output. Valid types are \'byte\', '
             '\'short\' and \'float\'.')
    dilate_inputs = Str(
        desc='Use this option to dilate and/or erode datasets as they are '
             'read. ex. \'5 -5\' to dilate and erode 5 times',
        argstr='-dilate_inputs %s')
    dilate_results = Str(
        desc='dilate and/or erode combined mask at the given levels.',
        argstr='-dilate_results %s')
    frac = traits.Float(
        desc='When combining masks (across datasets and sub-bricks), use '
             'this option to restrict the result to a certain fraction of the '
             'set of volumes',
        argstr='-frac %s')
    inter = traits.Bool(
        desc='intersection, this means -frac 1.0',
        argstr='-inter')
    union = traits.Bool(
        desc='union, this means -frac 0',
        argstr='-union')
    fill_holes = traits.Bool(
        desc='This option can be used to fill holes in the resulting mask, '
             'i.e. after all other processing has been done.',
        argstr='-fill_holes')
    fill_dirs = Str(
        desc='fill holes only in the given directions. This option is for use '
             'with -fill holes. should be a single string that specifies '
             '1-3 of the axes using {x,y,z} labels (i.e. dataset axis order), '
             'or using the labels in {R,L,A,P,I,S}.',
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

    >>> from nipype.interfaces import afni
    >>> masktool = afni.MaskTool()
    >>> masktool.inputs.in_file = 'functional.nii'
    >>> masktool.inputs.outputtype = 'NIFTI'
    >>> masktool.cmdline  # doctest: +ALLOW_UNICODE
    '3dmask_tool -prefix functional_mask.nii -input functional.nii'
    >>> res = automask.run()  # doctest: +SKIP

    """

    _cmd = '3dmask_tool'
    input_spec = MaskToolInputSpec
    output_spec = MaskToolOutputSpec


class MergeInputSpec(AFNICommandInputSpec):
    in_files = InputMultiPath(
        File(
            desc='input file to 3dmerge',
            exists=True),
        argstr='%s',
        position=-1,
        mandatory=True,
        copyfile=False)
    out_file = File(
        name_template='%s_merge',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file')
    doall = traits.Bool(
        desc='apply options to all sub-bricks in dataset',
        argstr='-doall')
    blurfwhm = traits.Int(
        desc='FWHM blur value (mm)',
        argstr='-1blur_fwhm %d',
        units='mm')


class Merge(AFNICommand):
    """Merge or edit volumes using AFNI 3dmerge command

    For complete details, see the `3dmerge Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dmerge.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> merge = afni.Merge()
    >>> merge.inputs.in_files = ['functional.nii', 'functional2.nii']
    >>> merge.inputs.blurfwhm = 4
    >>> merge.inputs.doall = True
    >>> merge.inputs.out_file = 'e7.nii'
    >>> merge.cmdline  # doctest: +ALLOW_UNICODE
    '3dmerge -1blur_fwhm 4 -doall -prefix e7.nii functional.nii functional2.nii'
    >>> res = merge.run()  # doctest: +SKIP

    """

    _cmd = '3dmerge'
    input_spec = MergeInputSpec
    output_spec = AFNICommandOutputSpec


class NotesInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3dNotes',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)
    add = Str(
        desc='note to add',
        argstr='-a "%s"')
    add_history = Str(
        desc='note to add to history',
        argstr='-h "%s"',
        xor=['rep_history'])
    rep_history = Str(
        desc='note with which to replace history',
        argstr='-HH "%s"',
        xor=['add_history'])
    delete = traits.Int(
        desc='delete note number num',
        argstr='-d %d')
    ses = traits.Bool(
        desc='print to stdout the expanded notes',
        argstr='-ses')
    out_file = File(
        desc='output image file name',
        argstr='%s')


class Notes(CommandLine):
    """A program to add, delete, and show notes for AFNI datasets.

    For complete details, see the `3dNotes Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dNotes.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> notes = afni.Notes()
    >>> notes.inputs.in_file = 'functional.HEAD'
    >>> notes.inputs.add = 'This note is added.'
    >>> notes.inputs.add_history = 'This note is added to history.'
    >>> notes.cmdline  # doctest: +ALLOW_UNICODE
    '3dNotes -a "This note is added." -h "This note is added to history." functional.HEAD'
    >>> res = notes.run()  # doctest: +SKIP
    """

    _cmd = '3dNotes'
    input_spec = NotesInputSpec
    output_spec = AFNICommandOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.in_file)
        return outputs


class RefitInputSpec(CommandLineInputSpec):
    in_file = File(
        desc='input file to 3drefit',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=True)
    deoblique = traits.Bool(
        desc='replace current transformation matrix with cardinal matrix',
        argstr='-deoblique')
    xorigin = Str(
        desc='x distance for edge voxel offset',
        argstr='-xorigin %s')
    yorigin = Str(
        desc='y distance for edge voxel offset',
        argstr='-yorigin %s')
    zorigin = Str(
        desc='z distance for edge voxel offset',
        argstr='-zorigin %s')
    xdel = traits.Float(
        desc='new x voxel dimension in mm',
        argstr='-xdel %f')
    ydel = traits.Float(
        desc='new y voxel dimension in mm',
        argstr='-ydel %f')
    zdel = traits.Float(
        desc='new z voxel dimension in mm',
        argstr='-zdel %f')
    space = traits.Enum(
        'TLRC', 'MNI', 'ORIG',
        argstr='-space %s',
        desc='Associates the dataset with a specific template type, e.g. '
             'TLRC, MNI, ORIG')


class Refit(AFNICommandBase):
    """Changes some of the information inside a 3D dataset's header

    For complete details, see the `3drefit Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3drefit.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> refit = afni.Refit()
    >>> refit.inputs.in_file = 'structural.nii'
    >>> refit.inputs.deoblique = True
    >>> refit.cmdline  # doctest: +ALLOW_UNICODE
    '3drefit -deoblique structural.nii'
    >>> res = refit.run()  # doctest: +SKIP

    """
    _cmd = '3drefit'
    input_spec = RefitInputSpec
    output_spec = AFNICommandOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.in_file)
        return outputs


class ResampleInputSpec(AFNICommandInputSpec):

    in_file = File(
        desc='input file to 3dresample',
        argstr='-inset %s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        name_template='%s_resample',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file')
    orientation = Str(
        desc='new orientation code',
        argstr='-orient %s')
    resample_mode = traits.Enum(
        'NN', 'Li', 'Cu', 'Bk',
        argstr='-rmode %s',
        desc='resampling method from set {"NN", "Li", "Cu", "Bk"}. These are '
             'for "Nearest Neighbor", "Linear", "Cubic" and "Blocky"'
             'interpolation, respectively. Default is NN.')
    voxel_size = traits.Tuple(
        *[traits.Float()] * 3,
        argstr='-dxyz %f %f %f',
        desc='resample to new dx, dy and dz')
    master = traits.File(
        argstr='-master %s',
        desc='align dataset grid to a reference file')


class Resample(AFNICommand):
    """Resample or reorient an image using AFNI 3dresample command

    For complete details, see the `3dresample Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dresample.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> resample = afni.Resample()
    >>> resample.inputs.in_file = 'functional.nii'
    >>> resample.inputs.orientation= 'RPI'
    >>> resample.inputs.outputtype = 'NIFTI'
    >>> resample.cmdline  # doctest: +ALLOW_UNICODE
    '3dresample -orient RPI -prefix functional_resample.nii -inset functional.nii'
    >>> res = resample.run()  # doctest: +SKIP

    """

    _cmd = '3dresample'
    input_spec = ResampleInputSpec
    output_spec = AFNICommandOutputSpec


class TCatInputSpec(AFNICommandInputSpec):
    in_files = InputMultiPath(
        File(
            exists=True),
        desc='input file to 3dTcat',
        argstr=' %s',
        position=-1,
        mandatory=True,
        copyfile=False)
    out_file = File(
        name_template='%s_tcat',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_files')
    rlt = traits.Enum(
        '', '+', '++',
        argstr='-rlt%s',
        desc='Remove linear trends in each voxel time series loaded from each '
             'input dataset, SEPARATELY. Option -rlt removes the least squares '
             'fit of \'a+b*t\' to each voxel time series. Option -rlt+ adds '
             'dataset mean back in. Option -rlt++ adds overall mean of all '
             'dataset timeseries back in.',
        position=1)


class TCat(AFNICommand):
    """Concatenate sub-bricks from input datasets into one big 3D+time dataset.

    TODO Replace InputMultiPath in_files with Traits.List, if possible. Current
    version adds extra whitespace.

    For complete details, see the `3dTcat Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTcat.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> tcat = afni.TCat()
    >>> tcat.inputs.in_files = ['functional.nii', 'functional2.nii']
    >>> tcat.inputs.out_file= 'functional_tcat.nii'
    >>> tcat.inputs.rlt = '+'
    >>> tcat.cmdline  # doctest: +ALLOW_UNICODE +NORMALIZE_WHITESPACE
    '3dTcat -rlt+ -prefix functional_tcat.nii functional.nii functional2.nii'
    >>> res = tcat.run()  # doctest: +SKIP

    """

    _cmd = '3dTcat'
    input_spec = TCatInputSpec
    output_spec = AFNICommandOutputSpec


class TStatInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3dTstat',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        name_template='%s_tstat',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file')
    mask = File(
        desc='mask file',
        argstr='-mask %s',
        exists=True)
    options = Str(
        desc='selected statistical output',
        argstr='%s')


class TStat(AFNICommand):
    """Compute voxel-wise statistics using AFNI 3dTstat command

    For complete details, see the `3dTstat Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTstat.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> tstat = afni.TStat()
    >>> tstat.inputs.in_file = 'functional.nii'
    >>> tstat.inputs.args = '-mean'
    >>> tstat.inputs.out_file = 'stats'
    >>> tstat.cmdline  # doctest: +ALLOW_UNICODE
    '3dTstat -mean -prefix stats functional.nii'
    >>> res = tstat.run()  # doctest: +SKIP

    """

    _cmd = '3dTstat'
    input_spec = TStatInputSpec
    output_spec = AFNICommandOutputSpec


class To3DInputSpec(AFNICommandInputSpec):
    out_file = File(
        name_template='%s',
        desc='output image file name',
        argstr='-prefix %s',
        name_source=['in_folder'])
    in_folder = Directory(
        desc='folder with DICOM images to convert',
        argstr='%s/*.dcm',
        position=-1,
        mandatory=True,
        exists=True)
    filetype = traits.Enum(
        'spgr', 'fse', 'epan', 'anat', 'ct', 'spct',
        'pet', 'mra', 'bmap', 'diff',
        'omri', 'abuc', 'fim', 'fith', 'fico', 'fitt',
        'fift', 'fizt', 'fict', 'fibt',
        'fibn', 'figt', 'fipt',
        'fbuc',
        argstr='-%s',
        desc='type of datafile being converted')
    skipoutliers = traits.Bool(
        desc='skip the outliers check',
        argstr='-skip_outliers')
    assumemosaic = traits.Bool(
        desc='assume that Siemens image is mosaic',
        argstr='-assume_dicom_mosaic')
    datatype = traits.Enum(
        'short', 'float', 'byte', 'complex',
        desc='set output file datatype',
        argstr='-datum %s')
    funcparams = Str(
        desc='parameters for functional data',
        argstr='-time:zt %s alt+z2')


class To3D(AFNICommand):
    """Create a 3D dataset from 2D image files using AFNI to3d command

    For complete details, see the `to3d Documentation
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/to3d.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> to3d = afni.To3D()
    >>> to3d.inputs.datatype = 'float'
    >>> to3d.inputs.in_folder = '.'
    >>> to3d.inputs.out_file = 'dicomdir.nii'
    >>> to3d.inputs.filetype = 'anat'
    >>> to3d.cmdline  # doctest: +ELLIPSIS +ALLOW_UNICODE
    'to3d -datum float -anat -prefix dicomdir.nii ./*.dcm'
    >>> res = to3d.run()  # doctest: +SKIP

   """

    _cmd = 'to3d'
    input_spec = To3DInputSpec
    output_spec = AFNICommandOutputSpec


class UnifizeInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3dUnifize',
        argstr='-input %s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file')
    t2 = traits.Bool(
        desc='Treat the input as if it were T2-weighted, rather than '
             'T1-weighted. This processing is done simply by inverting '
             'the image contrast, processing it as if that result were '
             'T1-weighted, and then re-inverting the results '
             'counts of voxel overlap, i.e., each voxel will contain the '
             'number of masks that it is set in.',
        argstr='-T2')
    gm = traits.Bool(
        desc='Also scale to unifize \'gray matter\' = lower intensity voxels '
             '(to aid in registering images from different scanners).',
        argstr='-GM')
    urad = traits.Float(
        desc='Sets the radius (in voxels) of the ball used for the sneaky '
             'trick. Default value is 18.3, and should be changed '
             'proportionally if the dataset voxel size differs significantly '
             'from 1 mm.',
        argstr='-Urad %s')
    scale_file = File(
        desc='output file name to save the scale factor used at each voxel ',
        argstr='-ssave %s')
    no_duplo = traits.Bool(
        desc='Do NOT use the \'duplo down\' step; this can be useful for '
             'lower resolution datasets.',
        argstr='-noduplo')
    epi = traits.Bool(
        desc='Assume the input dataset is a T2 (or T2*) weighted EPI time '
             'series. After computing the scaling, apply it to ALL volumes '
             '(TRs) in the input dataset. That is, a given voxel will be '
             'scaled by the same factor at each TR. '
             'This option also implies \'-noduplo\' and \'-T2\'.'
             'This option turns off \'-GM\' if you turned it on.',
        argstr='-EPI',
        requires=['no_duplo', 't2'],
        xor=['gm'])


class UnifizeOutputSpec(TraitedSpec):
    scale_file = File(desc='scale factor file')
    out_file = File(desc='unifized file', exists=True)


class Unifize(AFNICommand):
    """3dUnifize - for uniformizing image intensity

    * The input dataset is supposed to be a T1-weighted volume,
      possibly already skull-stripped (e.g., via 3dSkullStrip).
      However, this program can be a useful step to take BEFORE
      3dSkullStrip, since the latter program can fail if the input
      volume is strongly shaded -- 3dUnifize will (mostly) remove
      such shading artifacts.

    * The output dataset has the white matter (WM) intensity approximately
      uniformized across space, and scaled to peak at about 1000.

    * The output dataset is always stored in float format!

    * If the input dataset has more than 1 sub-brick, only sub-brick
      #0 will be processed!

    * Want to correct EPI datasets for nonuniformity?
      You can try the new and experimental [Mar 2017] '-EPI' option.

    * The principal motive for this program is for use in an image
      registration script, and it may or may not be useful otherwise.

    * This program replaces the older (and very different) 3dUniformize,
      which is no longer maintained and may sublimate at any moment.
      (In other words, we do not recommend the use of 3dUniformize.)

    For complete details, see the `3dUnifize Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dUnifize.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> unifize = afni.Unifize()
    >>> unifize.inputs.in_file = 'structural.nii'
    >>> unifize.inputs.out_file = 'structural_unifized.nii'
    >>> unifize.cmdline  # doctest: +ALLOW_UNICODE
    '3dUnifize -prefix structural_unifized.nii -input structural.nii'
    >>> res = unifize.run()  # doctest: +SKIP

    """

    _cmd = '3dUnifize'
    input_spec = UnifizeInputSpec
    output_spec = UnifizeOutputSpec


class ZCutUpInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3dZcutup',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        name_template='%s_zcutup',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file')
    keep = Str(
        desc='slice range to keep in output',
        argstr='-keep %s')


class ZCutUp(AFNICommand):
    """Cut z-slices from a volume using AFNI 3dZcutup command

    For complete details, see the `3dZcutup Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dZcutup.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> zcutup = afni.ZCutUp()
    >>> zcutup.inputs.in_file = 'functional.nii'
    >>> zcutup.inputs.out_file = 'functional_zcutup.nii'
    >>> zcutup.inputs.keep= '0 10'
    >>> zcutup.cmdline  # doctest: +ALLOW_UNICODE
    '3dZcutup -keep 0 10 -prefix functional_zcutup.nii functional.nii'
    >>> res = zcutup.run()  # doctest: +SKIP

    """

    _cmd = '3dZcutup'
    input_spec = ZCutUpInputSpec
    output_spec = AFNICommandOutputSpec
