# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

Examples
--------
See the docstrings of the individual classes for examples.
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import map, range

import os
import os.path as op
import re
from glob import glob
import tempfile

import numpy as np

from ...utils.filemanip import (load_json, save_json, split_filename,
                                fname_presuffix)
from ..base import (traits, TraitedSpec, OutputMultiPath, File, CommandLine,
                    CommandLineInputSpec, isdefined)
from .base import FSLCommand, FSLCommandInputSpec, Info


class CopyGeomInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=0,
        desc="source image")
    dest_file = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=1,
        desc="destination image",
        copyfile=True,
        output_name='out_file',
        name_source='dest_file',
        name_template='%s')
    ignore_dims = traits.Bool(
        desc='Do not copy image dimensions', argstr='-d', position="-1")


class CopyGeomOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="image with new geometry header")


class CopyGeom(FSLCommand):
    """Use fslcpgeom to copy the header geometry information to another image.
    Copy certain parts of the header information (image dimensions, voxel
    dimensions, voxel dimensions units string, image orientation/origin or
    qform/sform info) from one image to another. Note that only copies from
    Analyze to Analyze or Nifti to Nifti will work properly. Copying from
    different files will result in loss of information or potentially incorrect
    settings.
    """
    _cmd = "fslcpgeom"
    input_spec = CopyGeomInputSpec
    output_spec = CopyGeomOutputSpec


class RobustFOVInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        desc='input filename',
        argstr='-i %s',
        position=0,
        mandatory=True)
    out_roi = File(
        desc="ROI volume output name",
        argstr="-r %s",
        name_source=['in_file'],
        hash_files=False,
        name_template='%s_ROI')
    brainsize = traits.Int(
        desc=('size of brain in z-dimension (default '
              '170mm/150mm)'),
        argstr='-b %d')
    out_transform = File(
        desc=("Transformation matrix in_file to out_roi "
              "output name"),
        argstr="-m %s",
        name_source=['in_file'],
        hash_files=False,
        name_template='%s_to_ROI')


class RobustFOVOutputSpec(TraitedSpec):
    out_roi = File(exists=True, desc="ROI volume output name")
    out_transform = File(
        exists=True,
        desc=("Transformation matrix in_file to out_roi "
              "output name"))


class RobustFOV(FSLCommand):
    """Automatically crops an image removing lower head and neck.

    Interface is stable 5.0.0 to 5.0.9, but default brainsize changed from
    150mm to 170mm.
    """

    _cmd = 'robustfov'
    input_spec = RobustFOVInputSpec
    output_spec = RobustFOVOutputSpec


class ImageMeantsInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        desc='input file for computing the average timeseries',
        argstr='-i %s',
        position=0,
        mandatory=True)
    out_file = File(
        desc='name of output text matrix',
        argstr='-o %s',
        genfile=True,
        hash_files=False)
    mask = File(exists=True, desc='input 3D mask', argstr='-m %s')
    spatial_coord = traits.List(
        traits.Int,
        desc=('<x y z>  requested spatial coordinate '
              '(instead of mask)'),
        argstr='-c %s')
    use_mm = traits.Bool(
        desc=('use mm instead of voxel coordinates (for -c '
              'option)'),
        argstr='--usemm')
    show_all = traits.Bool(
        desc=('show all voxel time series (within mask) '
              'instead of averaging'),
        argstr='--showall')
    eig = traits.Bool(
        desc=('calculate Eigenvariate(s) instead of mean (output will have 0 '
              'mean)'),
        argstr='--eig')
    order = traits.Int(
        1,
        desc='select number of Eigenvariates',
        argstr='--order=%d',
        usedefault=True)
    nobin = traits.Bool(
        desc=('do not binarise the mask for calculation of '
              'Eigenvariates'),
        argstr='--no_bin')
    transpose = traits.Bool(
        desc=('output results in transpose format (one row per voxel/mean)'),
        argstr='--transpose')


class ImageMeantsOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="path/name of output text matrix")


class ImageMeants(FSLCommand):
    """ Use fslmeants for printing the average timeseries (intensities) to
        the screen (or saves to a file). The average is taken over all voxels
        in the mask (or all voxels in the image if no mask is specified)

    """
    _cmd = 'fslmeants'
    input_spec = ImageMeantsInputSpec
    output_spec = ImageMeantsOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(outputs['out_file']):
            outputs['out_file'] = self._gen_fname(
                self.inputs.in_file, suffix='_ts', ext='.txt', change_ext=True)
        outputs['out_file'] = os.path.abspath(outputs['out_file'])
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None


class SmoothInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, argstr="%s", position=0, mandatory=True)
    sigma = traits.Float(
        argstr="-kernel gauss %.03f -fmean",
        position=1,
        xor=['fwhm'],
        mandatory=True,
        desc='gaussian kernel sigma in mm (not voxels)')
    fwhm = traits.Float(
        argstr="-kernel gauss %.03f -fmean",
        position=1,
        xor=['sigma'],
        mandatory=True,
        desc=('gaussian kernel fwhm, will be converted to sigma in mm '
              '(not voxels)'))
    smoothed_file = File(
        argstr="%s",
        position=2,
        name_source=['in_file'],
        name_template='%s_smooth',
        hash_files=False)


class SmoothOutputSpec(TraitedSpec):
    smoothed_file = File(exists=True)


class Smooth(FSLCommand):
    """
    Use fslmaths to smooth the image

    Examples
    --------

    Setting the kernel width using sigma:

    >>> sm = Smooth()
    >>> sm.inputs.output_type = 'NIFTI_GZ'
    >>> sm.inputs.in_file = 'functional2.nii'
    >>> sm.inputs.sigma = 8.0
    >>> sm.cmdline # doctest: +ELLIPSIS
    'fslmaths functional2.nii -kernel gauss 8.000 -fmean functional2_smooth.nii.gz'

    Setting the kernel width using fwhm:

    >>> sm = Smooth()
    >>> sm.inputs.output_type = 'NIFTI_GZ'
    >>> sm.inputs.in_file = 'functional2.nii'
    >>> sm.inputs.fwhm = 8.0
    >>> sm.cmdline # doctest: +ELLIPSIS
    'fslmaths functional2.nii -kernel gauss 3.397 -fmean functional2_smooth.nii.gz'

    One of sigma or fwhm must be set:

    >>> from nipype.interfaces.fsl import Smooth
    >>> sm = Smooth()
    >>> sm.inputs.output_type = 'NIFTI_GZ'
    >>> sm.inputs.in_file = 'functional2.nii'
    >>> sm.cmdline #doctest: +ELLIPSIS
    Traceback (most recent call last):
     ...
    ValueError: Smooth requires a value for one of the inputs ...

    """

    input_spec = SmoothInputSpec
    output_spec = SmoothOutputSpec
    _cmd = 'fslmaths'

    def _format_arg(self, name, trait_spec, value):
        if name == 'fwhm':
            sigma = float(value) / np.sqrt(8 * np.log(2))
            return super(Smooth, self)._format_arg(name, trait_spec, sigma)
        return super(Smooth, self)._format_arg(name, trait_spec, value)


class SliceInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, argstr="%s", position=0, mandatory=True,
                   desc="input filename", copyfile=False)
    out_base_name = traits.Str(argstr="%s", position=1, desc="outputs prefix")


class SliceOutputSpec(TraitedSpec):
    out_files = OutputMultiPath(File(exists=True))


class Slice(FSLCommand):
    """Use fslslice to split a 3D file into lots of 2D files (along z-axis).


    Examples
    --------

    >>> from nipype.interfaces.fsl import Slice
    >>> slice = Slice()
    >>> slice.inputs.in_file = 'functional.nii'
    >>> slice.inputs.out_base_name = 'sl'
    >>> slice.cmdline
    'fslslice functional.nii sl'


    """

    _cmd = 'fslslice'
    input_spec = SliceInputSpec
    output_spec = SliceOutputSpec

    def _list_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------

        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs = self._outputs().get()
        ext = Info.output_type_to_ext(self.inputs.output_type)
        suffix = '_slice_*' + ext
        if isdefined(self.inputs.out_base_name):
            fname_template = os.path.abspath(
                self.inputs.out_base_name + suffix)
        else:
            fname_template = fname_presuffix(self.inputs.in_file,
                                             suffix=suffix, use_ext=False)

        outputs['out_files'] = sorted(glob(fname_template))

        return outputs


class MergeInputSpec(FSLCommandInputSpec):
    in_files = traits.List(
        File(exists=True), argstr="%s", position=2, mandatory=True)
    dimension = traits.Enum(
        't',
        'x',
        'y',
        'z',
        'a',
        argstr="-%s",
        position=0,
        desc=("dimension along which to merge, optionally "
              "set tr input when dimension is t"),
        mandatory=True)
    tr = traits.Float(
        position=-1,
        argstr='%.2f',
        desc=('use to specify TR in seconds (default is 1.00 '
              'sec), overrides dimension and sets it to tr'))
    merged_file = File(
        argstr="%s",
        position=1,
        name_source='in_files',
        name_template='%s_merged',
        hash_files=False)


class MergeOutputSpec(TraitedSpec):
    merged_file = File(exists=True)


class Merge(FSLCommand):
    """Use fslmerge to concatenate images

    Images can be concatenated across time, x, y, or z dimensions. Across the
    time (t) dimension the TR is set by default to 1 sec.

    Note: to set the TR to a different value, specify 't' for dimension and
    specify the TR value in seconds for the tr input. The dimension will be
    automatically updated to 'tr'.

    Examples
    --------

    >>> from nipype.interfaces.fsl import Merge
    >>> merger = Merge()
    >>> merger.inputs.in_files = ['functional2.nii', 'functional3.nii']
    >>> merger.inputs.dimension = 't'
    >>> merger.inputs.output_type = 'NIFTI_GZ'
    >>> merger.cmdline
    'fslmerge -t functional2_merged.nii.gz functional2.nii functional3.nii'
    >>> merger.inputs.tr = 2.25
    >>> merger.cmdline
    'fslmerge -tr functional2_merged.nii.gz functional2.nii functional3.nii 2.25'


    """

    _cmd = 'fslmerge'
    input_spec = MergeInputSpec
    output_spec = MergeOutputSpec

    def _format_arg(self, name, spec, value):
        if name == 'tr':
            if self.inputs.dimension != 't':
                raise ValueError('When TR is specified, dimension must be t')
            return spec.argstr % value
        if name == 'dimension':
            if isdefined(self.inputs.tr):
                return '-tr'
            return spec.argstr % value
        return super(Merge, self)._format_arg(name, spec, value)


class ExtractROIInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        position=0,
        desc="input file",
        mandatory=True)
    roi_file = File(
        argstr="%s",
        position=1,
        desc="output file",
        genfile=True,
        hash_files=False)
    x_min = traits.Int(argstr="%d", position=2)
    x_size = traits.Int(argstr="%d", position=3)
    y_min = traits.Int(argstr="%d", position=4)
    y_size = traits.Int(argstr="%d", position=5)
    z_min = traits.Int(argstr="%d", position=6)
    z_size = traits.Int(argstr="%d", position=7)
    t_min = traits.Int(argstr="%d", position=8)
    t_size = traits.Int(argstr="%d", position=9)
    _crop_xor = [
        'x_min', 'x_size', 'y_min', 'y_size', 'z_min', 'z_size', 't_min',
        't_size'
    ]
    crop_list = traits.List(
        traits.Tuple(traits.Int, traits.Int),
        argstr="%s",
        position=2,
        xor=_crop_xor,
        desc="list of two tuples specifying crop options")


class ExtractROIOutputSpec(TraitedSpec):
    roi_file = File(exists=True)


class ExtractROI(FSLCommand):
    """Uses FSL Fslroi command to extract region of interest (ROI)
    from an image.

    You can a) take a 3D ROI from a 3D data set (or if it is 4D, the
    same ROI is taken from each time point and a new 4D data set is
    created), b) extract just some time points from a 4D data set, or
    c) control time and space limits to the ROI.  Note that the
    arguments are minimum index and size (not maximum index).  So to
    extract voxels 10 to 12 inclusive you would specify 10 and 3 (not
    10 and 12).


    Examples
    --------

    >>> from nipype.interfaces.fsl import ExtractROI
    >>> from nipype.testing import anatfile
    >>> fslroi = ExtractROI(in_file=anatfile, roi_file='bar.nii', t_min=0,
    ...                     t_size=1)
    >>> fslroi.cmdline == 'fslroi %s bar.nii 0 1' % anatfile
    True


    """

    _cmd = 'fslroi'
    input_spec = ExtractROIInputSpec
    output_spec = ExtractROIOutputSpec

    def _format_arg(self, name, spec, value):

        if name == "crop_list":
            return " ".join(map(str, sum(list(map(list, value)), [])))
        return super(ExtractROI, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.


        Returns
        -------

        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs = self._outputs().get()
        outputs['roi_file'] = self.inputs.roi_file
        if not isdefined(outputs['roi_file']):
            outputs['roi_file'] = self._gen_fname(
                self.inputs.in_file, suffix='_roi')
        outputs['roi_file'] = os.path.abspath(outputs['roi_file'])
        return outputs

    def _gen_filename(self, name):
        if name == 'roi_file':
            return self._list_outputs()[name]
        return None


class SplitInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        position=0,
        mandatory=True,
        desc="input filename")
    out_base_name = traits.Str(argstr="%s", position=1, desc="outputs prefix")
    dimension = traits.Enum(
        't',
        'x',
        'y',
        'z',
        argstr="-%s",
        position=2,
        mandatory=True,
        desc="dimension along which the file will be split")


class SplitOutputSpec(TraitedSpec):
    out_files = OutputMultiPath(File(exists=True))


class Split(FSLCommand):
    """Uses FSL Fslsplit command to separate a volume into images in
    time, x, y or z dimension.
    """
    _cmd = 'fslsplit'
    input_spec = SplitInputSpec
    output_spec = SplitOutputSpec

    def _list_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------

        outputs : Bunch object
            Bunch object containing all possible files generated by
            interface object.

            If None, file was not generated
            Else, contains path, filename of generated outputfile

        """
        outputs = self._outputs().get()
        ext = Info.output_type_to_ext(self.inputs.output_type)
        outbase = 'vol*'
        if isdefined(self.inputs.out_base_name):
            outbase = '%s*' % self.inputs.out_base_name
        outputs['out_files'] = sorted(
            glob(os.path.join(os.getcwd(), outbase + ext)))
        return outputs


class ImageMathsInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, argstr="%s", mandatory=True, position=1)
    in_file2 = File(exists=True, argstr="%s", position=3)
    mask_file = File(exists=True, argstr='-mas %s',
                     desc='use (following image>0) to mask current image')
    out_file = File(argstr="%s", position=-2, genfile=True, hash_files=False)
    op_string = traits.Str(
        argstr="%s",
        position=2,
        desc="string defining the operation, i. e. -add")
    suffix = traits.Str(desc="out_file suffix")
    out_data_type = traits.Enum(
        'char',
        'short',
        'int',
        'float',
        'double',
        'input',
        argstr="-odt %s",
        position=-1,
        desc=("output datatype, one of (char, short, "
              "int, float, double, input)"))


class ImageMathsOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class ImageMaths(FSLCommand):
    """Use FSL fslmaths command to allow mathematical manipulation of images
    `FSL info <http://www.fmrib.ox.ac.uk/fslcourse/lectures/practicals/intro/index.htm#fslutils>`_


    Examples
    --------

    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import anatfile
    >>> maths = fsl.ImageMaths(in_file=anatfile, op_string= '-add 5',
    ...                        out_file='foo_maths.nii')
    >>> maths.cmdline == 'fslmaths %s -add 5 foo_maths.nii' % anatfile
    True


    """
    input_spec = ImageMathsInputSpec
    output_spec = ImageMathsOutputSpec

    _cmd = 'fslmaths'

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None

    def _parse_inputs(self, skip=None):
        return super(ImageMaths, self)._parse_inputs(skip=['suffix'])

    def _list_outputs(self):
        suffix = '_maths'  # ohinds: build suffix
        if isdefined(self.inputs.suffix):
            suffix = self.inputs.suffix
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(outputs['out_file']):
            outputs['out_file'] = self._gen_fname(
                self.inputs.in_file, suffix=suffix)
        outputs['out_file'] = os.path.abspath(outputs['out_file'])
        return outputs


class FilterRegressorInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        argstr="-i %s",
        desc="input file name (4D image)",
        mandatory=True,
        position=1)
    out_file = File(
        argstr="-o %s",
        desc="output file name for the filtered data",
        genfile=True,
        position=2,
        hash_files=False)
    design_file = File(
        exists=True,
        argstr="-d %s",
        position=3,
        mandatory=True,
        desc=("name of the matrix with time courses (e.g. GLM "
              "design or MELODIC mixing matrix)"))
    filter_columns = traits.List(
        traits.Int,
        argstr="-f '%s'",
        xor=["filter_all"],
        mandatory=True,
        position=4,
        desc=("(1-based) column indices to filter out of the data"))
    filter_all = traits.Bool(
        mandatory=True,
        argstr="-f '%s'",
        xor=["filter_columns"],
        position=4,
        desc=("use all columns in the design file in "
              "denoising"))
    mask = File(exists=True, argstr="-m %s", desc="mask image file name")
    var_norm = traits.Bool(
        argstr="--vn", desc="perform variance-normalization on data")
    out_vnscales = traits.Bool(
        argstr="--out_vnscales",
        desc=("output scaling factors for variance "
              "normalization"))


class FilterRegressorOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output file name for the filtered data")


class FilterRegressor(FSLCommand):
    """Data de-noising by regressing out part of a design matrix

    Uses simple OLS regression on 4D images
    """
    input_spec = FilterRegressorInputSpec
    output_spec = FilterRegressorOutputSpec
    _cmd = 'fsl_regfilt'

    def _format_arg(self, name, trait_spec, value):
        if name == 'filter_columns':
            return trait_spec.argstr % ",".join(map(str, value))
        elif name == "filter_all":
            design = np.loadtxt(self.inputs.design_file)
            try:
                n_cols = design.shape[1]
            except IndexError:
                n_cols = 1
            return trait_spec.argstr % ",".join(
                map(str, list(range(1, n_cols + 1))))
        return super(FilterRegressor, self)._format_arg(
            name, trait_spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(outputs['out_file']):
            outputs['out_file'] = self._gen_fname(
                self.inputs.in_file, suffix='_regfilt')
        outputs['out_file'] = os.path.abspath(outputs['out_file'])
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None


class ImageStatsInputSpec(FSLCommandInputSpec):
    split_4d = traits.Bool(
        argstr='-t',
        position=1,
        desc=('give a separate output line for each 3D '
              'volume of a 4D timeseries'))
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=2,
        desc='input file to generate stats of')
    op_string = traits.Str(
        argstr="%s",
        mandatory=True,
        position=3,
        desc=("string defining the operation, options are "
              "applied in order, e.g. -M -l 10 -M will "
              "report the non-zero mean, apply a threshold "
              "and then report the new nonzero mean"))
    mask_file = File(
        exists=True, argstr="", desc='mask file used for option -k %s')


class ImageStatsOutputSpec(TraitedSpec):
    out_stat = traits.Any(desc='stats output')


class ImageStats(FSLCommand):
    """Use FSL fslstats command to calculate stats from images
    `FSL info
    <http://www.fmrib.ox.ac.uk/fslcourse/lectures/practicals/intro/index.htm#fslutils>`_


    Examples
    --------

    >>> from nipype.interfaces.fsl import ImageStats
    >>> from nipype.testing import funcfile
    >>> stats = ImageStats(in_file=funcfile, op_string= '-M')
    >>> stats.cmdline == 'fslstats %s -M'%funcfile
    True


    """
    input_spec = ImageStatsInputSpec
    output_spec = ImageStatsOutputSpec

    _cmd = 'fslstats'

    def _format_arg(self, name, trait_spec, value):
        if name == 'mask_file':
            return ''
        if name == 'op_string':
            if '-k %s' in self.inputs.op_string:
                if isdefined(self.inputs.mask_file):
                    return self.inputs.op_string % self.inputs.mask_file
                else:
                    raise ValueError(
                        '-k %s option in op_string requires mask_file')
        return super(ImageStats, self)._format_arg(name, trait_spec, value)

    def aggregate_outputs(self, runtime=None, needed_outputs=None):
        outputs = self._outputs()
        # local caching for backward compatibility
        outfile = os.path.join(os.getcwd(), 'stat_result.json')
        if runtime is None:
            try:
                out_stat = load_json(outfile)['stat']
            except IOError:
                return self.run().outputs
        else:
            out_stat = []
            for line in runtime.stdout.split('\n'):
                if line:
                    values = line.split()
                    if len(values) > 1:
                        out_stat.append([float(val) for val in values])
                    else:
                        out_stat.extend([float(val) for val in values])
            if len(out_stat) == 1:
                out_stat = out_stat[0]
            save_json(outfile, dict(stat=out_stat))
        outputs.out_stat = out_stat
        return outputs


class AvScaleInputSpec(CommandLineInputSpec):
    all_param = traits.Bool(False, argstr='--allparams')
    mat_file = File(
        exists=True, argstr='%s', desc='mat file to read', position=-2)
    ref_file = File(
        exists=True,
        argstr='%s',
        position=-1,
        desc='reference file to get center of rotation')


class AvScaleOutputSpec(TraitedSpec):
    rotation_translation_matrix = traits.List(
        traits.List(traits.Float), desc='Rotation and Translation Matrix')
    scales = traits.List(traits.Float, desc='Scales (x,y,z)')
    skews = traits.List(traits.Float, desc='Skews')
    average_scaling = traits.Float(desc='Average Scaling')
    determinant = traits.Float(desc='Determinant')
    forward_half_transform = traits.List(
        traits.List(traits.Float), desc='Forward Half Transform')
    backward_half_transform = traits.List(
        traits.List(traits.Float), desc='Backwards Half Transform')
    left_right_orientation_preserved = traits.Bool(
        desc='True if LR orientation preserved')
    rot_angles = traits.List(traits.Float, desc='rotation angles')
    translations = traits.List(traits.Float, desc='translations')


class AvScale(CommandLine):
    """Use FSL avscale command to extract info from mat file output of FLIRT

    Examples
    --------

    >>> avscale = AvScale()
    >>> avscale.inputs.mat_file = 'flirt.mat'
    >>> res = avscale.run()  # doctest: +SKIP


    """
    input_spec = AvScaleInputSpec
    output_spec = AvScaleOutputSpec

    _cmd = 'avscale'

    def _run_interface(self, runtime):
        runtime = super(AvScale, self)._run_interface(runtime)

        expr = re.compile(
            'Rotation\ &\ Translation\ Matrix:\n(?P<rot_tran_mat>[0-9\.\ \n-]+)[\s\n]*'
            '(Rotation\ Angles\ \(x,y,z\)\ \[rads\]\ =\ (?P<rot_angles>[0-9\.\ -]+))?[\s\n]*'
            '(Translations\ \(x,y,z\)\ \[mm\]\ =\ (?P<translations>[0-9\.\ -]+))?[\s\n]*'
            'Scales\ \(x,y,z\)\ =\ (?P<scales>[0-9\.\ -]+)[\s\n]*'
            'Skews\ \(xy,xz,yz\)\ =\ (?P<skews>[0-9\.\ -]+)[\s\n]*'
            'Average\ scaling\ =\ (?P<avg_scaling>[0-9\.-]+)[\s\n]*'
            'Determinant\ =\ (?P<determinant>[0-9\.-]+)[\s\n]*'
            'Left-Right\ orientation:\ (?P<lr_orientation>[A-Za-z]+)[\s\n]*'
            'Forward\ half\ transform\ =[\s]*\n'
            '(?P<fwd_half_xfm>[0-9\.\ \n-]+)[\s\n]*'
            'Backward\ half\ transform\ =[\s]*\n'
            '(?P<bwd_half_xfm>[0-9\.\ \n-]+)[\s\n]*')
        out = expr.search(runtime.stdout).groupdict()
        outputs = {}
        outputs['rotation_translation_matrix'] = [[
            float(v) for v in r.strip().split(' ')
        ] for r in out['rot_tran_mat'].strip().split('\n')]
        outputs['scales'] = [
            float(s) for s in out['scales'].strip().split(' ')
        ]
        outputs['skews'] = [float(s) for s in out['skews'].strip().split(' ')]
        outputs['average_scaling'] = float(out['avg_scaling'].strip())
        outputs['determinant'] = float(out['determinant'].strip())
        outputs['left_right_orientation_preserved'] = out[
            'lr_orientation'].strip() == 'preserved'
        outputs['forward_half_transform'] = [[
            float(v) for v in r.strip().split(' ')
        ] for r in out['fwd_half_xfm'].strip().split('\n')]
        outputs['backward_half_transform'] = [[
            float(v) for v in r.strip().split(' ')
        ] for r in out['bwd_half_xfm'].strip().split('\n')]

        if self.inputs.all_param:
            outputs['rot_angles'] = [
                float(r) for r in out['rot_angles'].strip().split(' ')
            ]
            outputs['translations'] = [
                float(r) for r in out['translations'].strip().split(' ')
            ]

        setattr(self, '_results', outputs)
        return runtime

    def _list_outputs(self):
        return self._results


class OverlayInputSpec(FSLCommandInputSpec):
    transparency = traits.Bool(
        desc='make overlay colors semi-transparent',
        position=1,
        argstr='%s',
        usedefault=True,
        default_value=True)
    out_type = traits.Enum(
        'float',
        'int',
        position=2,
        usedefault=True,
        argstr='%s',
        desc='write output with float or int')
    use_checkerboard = traits.Bool(
        desc='use checkerboard mask for overlay', argstr='-c', position=3)
    background_image = File(
        exists=True,
        position=4,
        mandatory=True,
        argstr='%s',
        desc='image to use as background')
    _xor_inputs = ('auto_thresh_bg', 'full_bg_range', 'bg_thresh')
    auto_thresh_bg = traits.Bool(
        desc=('automatically threshold the background image'),
        argstr='-a',
        position=5,
        xor=_xor_inputs,
        mandatory=True)
    full_bg_range = traits.Bool(
        desc='use full range of background image',
        argstr='-A',
        position=5,
        xor=_xor_inputs,
        mandatory=True)
    bg_thresh = traits.Tuple(
        traits.Float,
        traits.Float,
        argstr='%.3f %.3f',
        position=5,
        desc='min and max values for background intensity',
        xor=_xor_inputs,
        mandatory=True)
    stat_image = File(
        exists=True,
        position=6,
        mandatory=True,
        argstr='%s',
        desc='statistical image to overlay in color')
    stat_thresh = traits.Tuple(
        traits.Float,
        traits.Float,
        position=7,
        mandatory=True,
        argstr='%.2f %.2f',
        desc=('min and max values for the statistical '
              'overlay'))
    show_negative_stats = traits.Bool(
        desc=('display negative statistics in '
              'overlay'),
        xor=['stat_image2'],
        argstr='%s',
        position=8)
    stat_image2 = File(
        exists=True,
        position=9,
        xor=['show_negative_stats'],
        argstr='%s',
        desc='second statistical image to overlay in color')
    stat_thresh2 = traits.Tuple(
        traits.Float,
        traits.Float,
        position=10,
        desc=('min and max values for second '
              'statistical overlay'),
        argstr='%.2f %.2f')
    out_file = File(
        desc='combined image volume',
        position=-1,
        argstr='%s',
        genfile=True,
        hash_files=False)


class OverlayOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='combined image volume')


class Overlay(FSLCommand):
    """ Use FSL's overlay command to combine background and statistical images
        into one volume


    Examples
    --------

    >>> from nipype.interfaces import fsl
    >>> combine = fsl.Overlay()
    >>> combine.inputs.background_image = 'mean_func.nii.gz'
    >>> combine.inputs.auto_thresh_bg = True
    >>> combine.inputs.stat_image = 'zstat1.nii.gz'
    >>> combine.inputs.stat_thresh = (3.5, 10)
    >>> combine.inputs.show_negative_stats = True
    >>> res = combine.run() #doctest: +SKIP


    """
    _cmd = 'overlay'
    input_spec = OverlayInputSpec
    output_spec = OverlayOutputSpec

    def _format_arg(self, name, spec, value):
        if name == 'transparency':
            if value:
                return '1'
            else:
                return '0'
        if name == 'out_type':
            if value == 'float':
                return '0'
            else:
                return '1'
        if name == 'show_negative_stats':
            return '%s %.2f %.2f' % (self.inputs.stat_image,
                                     self.inputs.stat_thresh[0] * -1,
                                     self.inputs.stat_thresh[1] * -1)
        return super(Overlay, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()
        out_file = self.inputs.out_file
        if not isdefined(out_file):
            if isdefined(self.inputs.stat_image2) and (
                    not isdefined(self.inputs.show_negative_stats)
                    or not self.inputs.show_negative_stats):
                stem = "%s_and_%s" % (
                    split_filename(self.inputs.stat_image)[1],
                    split_filename(self.inputs.stat_image2)[1])
            else:
                stem = split_filename(self.inputs.stat_image)[1]
            out_file = self._gen_fname(stem, suffix='_overlay')
        outputs['out_file'] = os.path.abspath(out_file)
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        return None


class SlicerInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        position=1,
        argstr='%s',
        mandatory=True,
        desc='input volume')
    image_edges = File(
        exists=True,
        position=2,
        argstr='%s',
        desc=('volume to display edge overlay for (useful for '
              'checking registration'))
    label_slices = traits.Bool(
        position=3,
        argstr='-L',
        desc='display slice number',
        usedefault=True,
        default_value=True)
    colour_map = File(
        exists=True,
        position=4,
        argstr='-l %s',
        desc=('use different colour map from that stored in '
              'nifti header'))
    intensity_range = traits.Tuple(
        traits.Float,
        traits.Float,
        position=5,
        argstr='-i %.3f %.3f',
        desc='min and max intensities to display')
    threshold_edges = traits.Float(
        position=6, argstr='-e %.3f', desc='use threshold for edges')
    dither_edges = traits.Bool(
        position=7,
        argstr='-t',
        desc=('produce semi-transparent (dithered) '
              'edges'))
    nearest_neighbour = traits.Bool(
        position=8,
        argstr='-n',
        desc=('use nearest neighbor interpolation '
              'for output'))
    show_orientation = traits.Bool(
        position=9,
        argstr='%s',
        usedefault=True,
        default_value=True,
        desc='label left-right orientation')
    _xor_options = ('single_slice', 'middle_slices', 'all_axial',
                    'sample_axial')
    single_slice = traits.Enum(
        'x',
        'y',
        'z',
        position=10,
        argstr='-%s',
        xor=_xor_options,
        requires=['slice_number'],
        desc=('output picture of single slice in the x, y, or z plane'))
    slice_number = traits.Int(
        position=11, argstr='-%d', desc='slice number to save in picture')
    middle_slices = traits.Bool(
        position=10,
        argstr='-a',
        xor=_xor_options,
        desc=('output picture of mid-sagittal, axial, '
              'and coronal slices'))
    all_axial = traits.Bool(
        position=10,
        argstr='-A',
        xor=_xor_options,
        requires=['image_width'],
        desc='output all axial slices into one picture')
    sample_axial = traits.Int(
        position=10,
        argstr='-S %d',
        xor=_xor_options,
        requires=['image_width'],
        desc=('output every n axial slices into one '
              'picture'))
    image_width = traits.Int(
        position=-2, argstr='%d', desc='max picture width')
    out_file = File(
        position=-1,
        genfile=True,
        argstr='%s',
        desc='picture to write',
        hash_files=False)
    scaling = traits.Float(position=0, argstr='-s %f', desc='image scale')


class SlicerOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='picture to write')


class Slicer(FSLCommand):
    """Use FSL's slicer command to output a png image from a volume.


    Examples
    --------

    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import example_data
    >>> slice = fsl.Slicer()
    >>> slice.inputs.in_file = example_data('functional.nii')
    >>> slice.inputs.all_axial = True
    >>> slice.inputs.image_width = 750
    >>> res = slice.run() #doctest: +SKIP


    """
    _cmd = 'slicer'
    input_spec = SlicerInputSpec
    output_spec = SlicerOutputSpec

    def _format_arg(self, name, spec, value):
        if name == 'show_orientation':
            if value:
                return ''
            else:
                return '-u'
        elif name == "label_slices":
            if value:
                return '-L'
            else:
                return ''
        return super(Slicer, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()
        out_file = self.inputs.out_file
        if not isdefined(out_file):
            out_file = self._gen_fname(self.inputs.in_file, ext='.png')
        outputs['out_file'] = os.path.abspath(out_file)
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        return None


class PlotTimeSeriesInputSpec(FSLCommandInputSpec):

    in_file = traits.Either(
        File(exists=True),
        traits.List(File(exists=True)),
        mandatory=True,
        argstr="%s",
        position=1,
        desc=("file or list of files with columns of "
              "timecourse information"))
    plot_start = traits.Int(
        argstr="--start=%d",
        xor=("plot_range", ),
        desc="first column from in-file to plot")
    plot_finish = traits.Int(
        argstr="--finish=%d",
        xor=("plot_range", ),
        desc="final column from in-file to plot")
    plot_range = traits.Tuple(
        traits.Int,
        traits.Int,
        argstr="%s",
        xor=("plot_start", "plot_finish"),
        desc=("first and last columns from the in-file "
              "to plot"))
    title = traits.Str(argstr="%s", desc="plot title")
    legend_file = File(exists=True, argstr="--legend=%s", desc="legend file")
    labels = traits.Either(
        traits.Str,
        traits.List(traits.Str),
        argstr="%s",
        desc="label or list of labels")
    y_min = traits.Float(
        argstr="--ymin=%.2f", desc="minumum y value", xor=("y_range", ))
    y_max = traits.Float(
        argstr="--ymax=%.2f", desc="maximum y value", xor=("y_range", ))
    y_range = traits.Tuple(
        traits.Float,
        traits.Float,
        argstr="%s",
        xor=("y_min", "y_max"),
        desc="min and max y axis values")
    x_units = traits.Int(
        argstr="-u %d",
        usedefault=True,
        default_value=1,
        desc=("scaling units for x-axis (between 1 and length of in file)"))
    plot_size = traits.Tuple(
        traits.Int,
        traits.Int,
        argstr="%s",
        desc="plot image height and width")
    x_precision = traits.Int(
        argstr="--precision=%d", desc="precision of x-axis labels")
    sci_notation = traits.Bool(
        argstr="--sci", desc="switch on scientific notation")
    out_file = File(
        argstr="-o %s", genfile=True, desc="image to write", hash_files=False)


class PlotTimeSeriesOutputSpec(TraitedSpec):

    out_file = File(exists=True, desc='image to write')


class PlotTimeSeries(FSLCommand):
    """Use fsl_tsplot to create images of time course plots.

    Examples
    --------

    >>> import nipype.interfaces.fsl as fsl
    >>> plotter = fsl.PlotTimeSeries()
    >>> plotter.inputs.in_file = 'functional.par'
    >>> plotter.inputs.title = 'Functional timeseries'
    >>> plotter.inputs.labels = ['run1', 'run2']
    >>> plotter.run() #doctest: +SKIP


    """
    _cmd = "fsl_tsplot"
    input_spec = PlotTimeSeriesInputSpec
    output_spec = PlotTimeSeriesOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "in_file":
            if isinstance(value, list):
                args = ",".join(value)
                return "-i %s" % args
            else:
                return "-i %s" % value
        elif name == "labels":
            if isinstance(value, list):
                args = ",".join(value)
                return "-a %s" % args
            else:
                return "-a %s" % value
        elif name == "title":
            return "-t \'%s\'" % value
        elif name == "plot_range":
            return "--start=%d --finish=%d" % value
        elif name == "y_range":
            return "--ymin=%d --ymax=%d" % value
        elif name == "plot_size":
            return "-h %d -w %d" % value
        return super(PlotTimeSeries, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()
        out_file = self.inputs.out_file
        if not isdefined(out_file):
            if isinstance(self.inputs.in_file, list):
                infile = self.inputs.in_file[0]
            else:
                infile = self.inputs.in_file
            out_file = self._gen_fname(infile, ext='.png')
        outputs['out_file'] = os.path.abspath(out_file)
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        return None


class PlotMotionParamsInputSpec(FSLCommandInputSpec):

    in_file = traits.Either(
        File(exists=True),
        traits.List(File(exists=True)),
        mandatory=True,
        argstr="%s",
        position=1,
        desc="file with motion parameters")
    in_source = traits.Enum(
        "spm",
        "fsl",
        mandatory=True,
        desc=("which program generated the motion "
              "parameter file - fsl, spm"))
    plot_type = traits.Enum(
        "rotations",
        "translations",
        "displacement",
        argstr="%s",
        mandatory=True,
        desc=("which motion type to plot - rotations, "
              "translations, displacement"))
    plot_size = traits.Tuple(
        traits.Int,
        traits.Int,
        argstr="%s",
        desc="plot image height and width")
    out_file = File(
        argstr="-o %s", genfile=True, desc="image to write", hash_files=False)


class PlotMotionParamsOutputSpec(TraitedSpec):

    out_file = File(exists=True, desc='image to write')


class PlotMotionParams(FSLCommand):
    """Use fsl_tsplot to plot the estimated motion parameters from a
    realignment program.


    Examples
    --------

    >>> import nipype.interfaces.fsl as fsl
    >>> plotter = fsl.PlotMotionParams()
    >>> plotter.inputs.in_file = 'functional.par'
    >>> plotter.inputs.in_source = 'fsl'
    >>> plotter.inputs.plot_type = 'rotations'
    >>> res = plotter.run() #doctest: +SKIP


    Notes
    -----

    The 'in_source' attribute determines the order of columns that are expected
    in the source file.  FSL prints motion parameters in the order rotations,
    translations, while SPM prints them in the opposite order.  This interface
    should be able to plot timecourses of motion parameters generated from
    other sources as long as they fall under one of these two patterns.  For
    more flexibilty, see the :class:`fsl.PlotTimeSeries` interface.

    """
    _cmd = 'fsl_tsplot'
    input_spec = PlotMotionParamsInputSpec
    output_spec = PlotMotionParamsOutputSpec

    def _format_arg(self, name, spec, value):

        if name == "plot_type":
            source = self.inputs.in_source

            if self.inputs.plot_type == 'displacement':
                title = '-t \'MCFLIRT estimated mean displacement (mm)\''
                labels = '-a abs,rel'
                return '%s %s' % (title, labels)

            # Get the right starting and ending position depending on source
            # package
            sfdict = dict(
                fsl_rot=(1, 3), fsl_tra=(4, 6), spm_rot=(4, 6), spm_tra=(1, 3))

            # Format the title properly
            sfstr = "--start=%d --finish=%d" % sfdict["%s_%s" % (source,
                                                                 value[:3])]
            titledict = dict(fsl="MCFLIRT", spm="Realign")
            unitdict = dict(rot="radians", tra="mm")

            title = "\'%s estimated %s (%s)\'" % (titledict[source], value,
                                                  unitdict[value[:3]])

            return "-t %s %s -a x,y,z" % (title, sfstr)
        elif name == "plot_size":
            return "-h %d -w %d" % value
        elif name == "in_file":
            if isinstance(value, list):
                args = ",".join(value)
                return "-i %s" % args
            else:
                return "-i %s" % value

        return super(PlotMotionParams, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()
        out_file = self.inputs.out_file
        if not isdefined(out_file):
            if isinstance(self.inputs.in_file, list):
                infile = self.inputs.in_file[0]
            else:
                infile = self.inputs.in_file
            plttype = dict(
                rot="rot", tra="trans", dis="disp")[self.inputs.plot_type[:3]]
            out_file = fname_presuffix(
                infile, suffix="_%s.png" % plttype, use_ext=False)
        outputs['out_file'] = os.path.abspath(out_file)
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        return None


class ConvertXFMInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-1,
        desc="input transformation matrix")
    in_file2 = File(
        exists=True,
        argstr="%s",
        position=-2,
        desc="second input matrix (for use with fix_scale_skew or concat_xfm)")
    _options = ["invert_xfm", "concat_xfm", "fix_scale_skew"]
    invert_xfm = traits.Bool(
        argstr="-inverse",
        position=-3,
        xor=_options,
        desc="invert input transformation")
    concat_xfm = traits.Bool(
        argstr="-concat",
        position=-3,
        xor=_options,
        requires=["in_file2"],
        desc=("write joint transformation of two input "
              "matrices"))
    fix_scale_skew = traits.Bool(
        argstr="-fixscaleskew",
        position=-3,
        xor=_options,
        requires=["in_file2"],
        desc=("use secondary matrix to fix scale and "
              "skew"))
    out_file = File(
        genfile=True,
        argstr="-omat %s",
        position=1,
        desc="final transformation matrix",
        hash_files=False)


class ConvertXFMOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output transformation matrix")


class ConvertXFM(FSLCommand):
    """Use the FSL utility convert_xfm to modify FLIRT transformation matrices.

    Examples
    --------

    >>> import nipype.interfaces.fsl as fsl
    >>> invt = fsl.ConvertXFM()
    >>> invt.inputs.in_file = "flirt.mat"
    >>> invt.inputs.invert_xfm = True
    >>> invt.inputs.out_file = 'flirt_inv.mat'
    >>> invt.cmdline
    'convert_xfm -omat flirt_inv.mat -inverse flirt.mat'


    """

    _cmd = "convert_xfm"
    input_spec = ConvertXFMInputSpec
    output_spec = ConvertXFMOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outfile = self.inputs.out_file
        if not isdefined(outfile):
            _, infile1, _ = split_filename(self.inputs.in_file)
            if self.inputs.invert_xfm:
                outfile = fname_presuffix(
                    infile1,
                    suffix="_inv.mat",
                    newpath=os.getcwd(),
                    use_ext=False)
            else:
                if self.inputs.concat_xfm:
                    _, infile2, _ = split_filename(self.inputs.in_file2)
                    outfile = fname_presuffix(
                        "%s_%s" % (infile1, infile2),
                        suffix=".mat",
                        newpath=os.getcwd(),
                        use_ext=False)
                else:
                    outfile = fname_presuffix(
                        infile1,
                        suffix="_fix.mat",
                        newpath=os.getcwd(),
                        use_ext=False)
        outputs["out_file"] = os.path.abspath(outfile)
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None


class SwapDimensionsInputSpec(FSLCommandInputSpec):

    in_file = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position="1",
        desc="input image")
    _dims = [
        "x", "-x", "y", "-y", "z", "-z", "RL", "LR", "AP", "PA", "IS", "SI"
    ]
    new_dims = traits.Tuple(
        traits.Enum(_dims),
        traits.Enum(_dims),
        traits.Enum(_dims),
        argstr="%s %s %s",
        mandatory=True,
        desc="3-tuple of new dimension order")
    out_file = File(
        genfile=True, argstr="%s", desc="image to write", hash_files=False)


class SwapDimensionsOutputSpec(TraitedSpec):

    out_file = File(exists=True, desc="image with new dimensions")


class SwapDimensions(FSLCommand):
    """Use fslswapdim to alter the orientation of an image.

    This interface accepts a three-tuple corresponding to the new
    orientation.  You may either provide dimension ids in the form of
    (-)x, (-)y, or (-z), or nifti-syle dimension codes
    (RL, LR, AP, PA, IS, SI).

    """
    _cmd = "fslswapdim"
    input_spec = SwapDimensionsInputSpec
    output_spec = SwapDimensionsOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] = self._gen_fname(
                self.inputs.in_file, suffix='_newdims')
        outputs["out_file"] = os.path.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None


class PowerSpectrumInputSpec(FSLCommandInputSpec):
    # We use position args here as list indices - so a negative number
    # will put something on the end
    in_file = File(
        exists=True,
        desc="input 4D file to estimate the power spectrum",
        argstr='%s',
        position=0,
        mandatory=True)
    out_file = File(
        desc='name of output 4D file for power spectrum',
        argstr='%s',
        position=1,
        genfile=True,
        hash_files=False)


class PowerSpectrumOutputSpec(TraitedSpec):
    out_file = File(
        exists=True, desc="path/name of the output 4D power spectrum file")


class PowerSpectrum(FSLCommand):
    """Use FSL PowerSpectrum command for power spectrum estimation.

    Examples
    --------

    >>> from nipype.interfaces import fsl
    >>> pspec = fsl.PowerSpectrum()
    >>> pspec.inputs.in_file = 'functional.nii'
    >>> res = pspec.run() # doctest: +SKIP


    """

    _cmd = 'fslpspec'
    input_spec = PowerSpectrumInputSpec
    output_spec = PowerSpectrumOutputSpec

    def _gen_outfilename(self):
        out_file = self.inputs.out_file
        if not isdefined(out_file) and isdefined(self.inputs.in_file):
            out_file = self._gen_fname(self.inputs.in_file, suffix='_ps')
        return out_file

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._gen_outfilename()
        return None


class SigLossInputSpec(FSLCommandInputSpec):
    in_file = File(
        mandatory=True, exists=True, argstr='-i %s', desc='b0 fieldmap file')
    out_file = File(
        argstr='-s %s', desc='output signal loss estimate file', genfile=True)

    mask_file = File(exists=True, argstr='-m %s', desc='brain mask file')
    echo_time = traits.Float(argstr='--te=%f', desc='echo time in seconds')
    slice_direction = traits.Enum(
        'x', 'y', 'z', argstr='-d %s', desc='slicing direction')


class SigLossOuputSpec(TraitedSpec):
    out_file = File(exists=True, desc='signal loss estimate file')


class SigLoss(FSLCommand):
    """Estimates signal loss from a field map (in rad/s)

    Examples
    --------

    >>> sigloss = SigLoss()
    >>> sigloss.inputs.in_file = "phase.nii"
    >>> sigloss.inputs.echo_time = 0.03
    >>> res = sigloss.run() # doctest: +SKIP


    """
    input_spec = SigLossInputSpec
    output_spec = SigLossOuputSpec
    _cmd = 'sigloss'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(outputs['out_file']) and \
                isdefined(self.inputs.in_file):
            outputs['out_file'] = self._gen_fname(
                self.inputs.in_file, suffix='_sigloss')
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        return None


class Reorient2StdInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, mandatory=True, argstr="%s")
    out_file = File(genfile=True, hash_files=False, argstr="%s")


class Reorient2StdOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class Reorient2Std(FSLCommand):
    """fslreorient2std is a tool for reorienting the image to match the
    approximate orientation of the standard template images (MNI152).


    Examples
    --------

    >>> reorient = Reorient2Std()
    >>> reorient.inputs.in_file = "functional.nii"
    >>> res = reorient.run() # doctest: +SKIP


    """
    _cmd = 'fslreorient2std'
    input_spec = Reorient2StdInputSpec
    output_spec = Reorient2StdOutputSpec

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._gen_fname(self.inputs.in_file, suffix="_reoriented")
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_filename('out_file')
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class InvWarpInputSpec(FSLCommandInputSpec):
    warp = File(
        exists=True,
        argstr='--warp=%s',
        mandatory=True,
        desc=('Name of file containing warp-coefficients/fields. This '
              'would typically be the output from the --cout switch of'
              ' fnirt (but can also use fields, like the output from '
              '--fout).'))
    reference = File(
        exists=True,
        argstr='--ref=%s',
        mandatory=True,
        desc=('Name of a file in target space. Note that the '
              'target space is now different from the target '
              'space that was used to create the --warp file. It '
              'would typically be the file that was specified '
              'with the --in argument when running fnirt.'))
    inverse_warp = File(
        argstr='--out=%s',
        name_source=['warp'],
        hash_files=False,
        name_template='%s_inverse',
        desc=('Name of output file, containing warps that are '
              'the "reverse" of those in --warp. This will be '
              'a field-file (rather than a file of spline '
              'coefficients), and it will have any affine '
              'component included as part of the '
              'displacements.'))
    absolute = traits.Bool(
        argstr='--abs',
        xor=['relative'],
        desc=('If set it indicates that the warps in --warp'
              ' should be interpreted as absolute, provided'
              ' that it is not created by fnirt (which '
              'always uses relative warps). If set it also '
              'indicates that the output --out should be '
              'absolute.'))
    relative = traits.Bool(
        argstr='--rel',
        xor=['absolute'],
        desc=('If set it indicates that the warps in --warp'
              ' should be interpreted as relative. I.e. the'
              ' values in --warp are displacements from the'
              ' coordinates in the --ref space. If set it '
              'also indicates that the output --out should '
              'be relative.'))
    niter = traits.Int(
        argstr='--niter=%d',
        desc=('Determines how many iterations of the '
              'gradient-descent search that should be run.'))
    regularise = traits.Float(
        argstr='--regularise=%f',
        desc='Regularization strength (deafult=1.0).')
    noconstraint = traits.Bool(
        argstr='--noconstraint', desc='Do not apply Jacobian constraint')
    jacobian_min = traits.Float(
        argstr='--jmin=%f',
        desc=('Minimum acceptable Jacobian value for '
              'constraint (default 0.01)'))
    jacobian_max = traits.Float(
        argstr='--jmax=%f',
        desc=('Maximum acceptable Jacobian value for '
              'constraint (default 100.0)'))


class InvWarpOutputSpec(TraitedSpec):
    inverse_warp = File(
        exists=True,
        desc=('Name of output file, containing warps that are '
              'the "reverse" of those in --warp.'))


class InvWarp(FSLCommand):
    """
    Use FSL Invwarp to invert a FNIRT warp


    Examples
    --------

    >>> from nipype.interfaces.fsl import InvWarp
    >>> invwarp = InvWarp()
    >>> invwarp.inputs.warp = "struct2mni.nii"
    >>> invwarp.inputs.reference = "anatomical.nii"
    >>> invwarp.inputs.output_type = "NIFTI_GZ"
    >>> invwarp.cmdline
    'invwarp --out=struct2mni_inverse.nii.gz --ref=anatomical.nii --warp=struct2mni.nii'
    >>> res = invwarp.run() # doctest: +SKIP


    """

    input_spec = InvWarpInputSpec
    output_spec = InvWarpOutputSpec

    _cmd = 'invwarp'


class ComplexInputSpec(FSLCommandInputSpec):
    complex_in_file = File(exists=True, argstr="%s", position=2)
    complex_in_file2 = File(exists=True, argstr="%s", position=3)

    real_in_file = File(exists=True, argstr="%s", position=2)
    imaginary_in_file = File(exists=True, argstr="%s", position=3)
    magnitude_in_file = File(exists=True, argstr="%s", position=2)
    phase_in_file = File(exists=True, argstr='%s', position=3)

    _ofs = [
        'complex_out_file', 'magnitude_out_file', 'phase_out_file',
        'real_out_file', 'imaginary_out_file'
    ]
    _conversion = [
        'real_polar',
        'real_cartesian',
        'complex_cartesian',
        'complex_polar',
        'complex_split',
        'complex_merge',
    ]

    complex_out_file = File(
        genfile=True, argstr="%s", position=-3, xor=_ofs + _conversion[:2])
    magnitude_out_file = File(
        genfile=True,
        argstr="%s",
        position=-4,
        xor=_ofs[:1] + _ofs[3:] + _conversion[1:])
    phase_out_file = File(
        genfile=True,
        argstr="%s",
        position=-3,
        xor=_ofs[:1] + _ofs[3:] + _conversion[1:])
    real_out_file = File(
        genfile=True,
        argstr="%s",
        position=-4,
        xor=_ofs[:3] + _conversion[:1] + _conversion[2:])
    imaginary_out_file = File(
        genfile=True,
        argstr="%s",
        position=-3,
        xor=_ofs[:3] + _conversion[:1] + _conversion[2:])

    start_vol = traits.Int(position=-2, argstr='%d')
    end_vol = traits.Int(position=-1, argstr='%d')

    real_polar = traits.Bool(
        argstr='-realpolar',
        xor=_conversion,
        position=1,
    )
    #        requires=['complex_in_file','magnitude_out_file','phase_out_file'])
    real_cartesian = traits.Bool(
        argstr='-realcartesian',
        xor=_conversion,
        position=1,
    )
    #        requires=['complex_in_file','real_out_file','imaginary_out_file'])
    complex_cartesian = traits.Bool(
        argstr='-complex',
        xor=_conversion,
        position=1,
    )
    #        requires=['real_in_file','imaginary_in_file','complex_out_file'])
    complex_polar = traits.Bool(
        argstr='-complexpolar',
        xor=_conversion,
        position=1,
    )
    #        requires=['magnitude_in_file','phase_in_file',
    #                  'magnitude_out_file','phase_out_file'])
    complex_split = traits.Bool(
        argstr='-complexsplit',
        xor=_conversion,
        position=1,
    )
    #        requires=['complex_in_file','complex_out_file'])
    complex_merge = traits.Bool(
        argstr='-complexmerge',
        xor=_conversion + ['start_vol', 'end_vol'],
        position=1,
    )


#        requires=['complex_in_file','complex_in_file2','complex_out_file'])


class ComplexOuputSpec(TraitedSpec):
    magnitude_out_file = File()
    phase_out_file = File()
    real_out_file = File()
    imaginary_out_file = File()
    complex_out_file = File()


class Complex(FSLCommand):
    """fslcomplex is a tool for converting complex data

    Examples
    --------

    >>> cplx = Complex()
    >>> cplx.inputs.complex_in_file = "complex.nii"
    >>> cplx.real_polar = True
    >>> res = cplx.run() # doctest: +SKIP


    """
    _cmd = 'fslcomplex'
    input_spec = ComplexInputSpec
    output_spec = ComplexOuputSpec

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []
        if self.inputs.real_cartesian:
            skip += self.inputs._ofs[:3]
        elif self.inputs.real_polar:
            skip += self.inputs._ofs[:1] + self.inputs._ofs[3:]
        else:
            skip += self.inputs._ofs[1:]
        return super(Complex, self)._parse_inputs(skip)

    def _gen_filename(self, name):
        if name == 'complex_out_file':
            if self.inputs.complex_cartesian:
                in_file = self.inputs.real_in_file
            elif self.inputs.complex_polar:
                in_file = self.inputs.magnitude_in_file
            elif self.inputs.complex_split or self.inputs.complex_merge:
                in_file = self.inputs.complex_in_file
            else:
                return None
            return self._gen_fname(in_file, suffix="_cplx")
        elif name == 'magnitude_out_file':
            return self._gen_fname(self.inputs.complex_in_file, suffix="_mag")
        elif name == 'phase_out_file':
            return self._gen_fname(
                self.inputs.complex_in_file, suffix="_phase")
        elif name == 'real_out_file':
            return self._gen_fname(self.inputs.complex_in_file, suffix="_real")
        elif name == 'imaginary_out_file':
            return self._gen_fname(self.inputs.complex_in_file, suffix="_imag")
        return None

    def _get_output(self, name):
        output = getattr(self.inputs, name)
        if not isdefined(output):
            output = self._gen_filename(name)
        return os.path.abspath(output)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if self.inputs.complex_cartesian or self.inputs.complex_polar or \
                self.inputs.complex_split or self.inputs.complex_merge:
            outputs['complex_out_file'] = self._get_output('complex_out_file')
        elif self.inputs.real_cartesian:
            outputs['real_out_file'] = self._get_output('real_out_file')
            outputs['imaginary_out_file'] = self._get_output(
                'imaginary_out_file')
        elif self.inputs.real_polar:
            outputs['magnitude_out_file'] = self._get_output(
                'magnitude_out_file')
            outputs['phase_out_file'] = self._get_output('phase_out_file')
        return outputs


class WarpUtilsInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        argstr='--in=%s',
        mandatory=True,
        desc=('Name of file containing warp-coefficients/fields. This '
              'would typically be the output from the --cout switch of '
              'fnirt (but can also use fields, like the output from '
              '--fout).'))
    reference = File(
        exists=True,
        argstr='--ref=%s',
        mandatory=True,
        desc=('Name of a file in target space. Note that the '
              'target space is now different from the target '
              'space that was used to create the --warp file. It '
              'would typically be the file that was specified '
              'with the --in argument when running fnirt.'))

    out_format = traits.Enum(
        'spline',
        'field',
        argstr='--outformat=%s',
        desc=('Specifies the output format. If set to field (default) '
              'the output will be a (4D) field-file. If set to spline '
              'the format will be a (4D) file of spline coefficients.'))

    warp_resolution = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr='--warpres=%0.4f,%0.4f,%0.4f',
        desc=('Specifies the resolution/knot-spacing of the splines pertaining'
              ' to the coefficients in the --out file. This parameter is only '
              'relevant if --outformat is set to spline. It should be noted '
              'that if the --in file has a higher resolution, the resulting '
              'coefficients will pertain to the closest (in a least-squares'
              ' sense) file in the space of fields with the --warpres'
              ' resolution. It should also be noted that the resolution '
              'will always be an integer multiple of the voxel '
              'size.'))

    knot_space = traits.Tuple(
        traits.Int,
        traits.Int,
        traits.Int,
        argstr='--knotspace=%d,%d,%d',
        desc=('Alternative (to --warpres) specification of the resolution of '
              'the output spline-field.'))

    out_file = File(
        argstr='--out=%s',
        position=-1,
        name_source=['in_file'],
        output_name='out_file',
        desc=('Name of output file. The format of the output depends on what '
              'other parameters are set. The default format is a (4D) '
              'field-file. If the --outformat is set to spline the format '
              'will be a (4D) file of spline coefficients.'))

    write_jacobian = traits.Bool(
        False,
        mandatory=True,
        usedefault=True,
        desc='Switch on --jac flag with automatically generated filename')

    out_jacobian = File(
        argstr='--jac=%s',
        desc=('Specifies that a (3D) file of Jacobian determinants '
              'corresponding to --in should be produced and written to '
              'filename.'))

    with_affine = traits.Bool(
        False,
        argstr='--withaff',
        desc=('Specifies that the affine transform (i.e. that which was '
              'specified for the --aff parameter in fnirt) should be '
              'included as displacements in the --out file. That can be '
              'useful for interfacing with software that cannot decode '
              'FSL/fnirt coefficient-files (where the affine transform is '
              'stored separately from the displacements).'))


class WarpUtilsOutputSpec(TraitedSpec):
    out_file = File(
        desc=('Name of output file, containing the warp as field or '
              'coefficients.'))
    out_jacobian = File(
        desc=('Name of output file, containing the map of the determinant of '
              'the Jacobian'))


class WarpUtils(FSLCommand):
    """Use FSL `fnirtfileutils <http://fsl.fmrib.ox.ac.uk/fsl/fsl-4.1.9/fnirt/warp_utils.html>`_
    to convert field->coefficients, coefficients->field, coefficients->other_coefficients etc


    Examples
    --------

    >>> from nipype.interfaces.fsl import WarpUtils
    >>> warputils = WarpUtils()
    >>> warputils.inputs.in_file = "warpfield.nii"
    >>> warputils.inputs.reference = "T1.nii"
    >>> warputils.inputs.out_format = 'spline'
    >>> warputils.inputs.warp_resolution = (10,10,10)
    >>> warputils.inputs.output_type = "NIFTI_GZ"
    >>> warputils.cmdline # doctest: +ELLIPSIS
    'fnirtfileutils --in=warpfield.nii --outformat=spline --ref=T1.nii --warpres=10.0000,10.0000,10.0000 --out=warpfield_coeffs.nii.gz'
    >>> res = invwarp.run() # doctest: +SKIP


    """

    input_spec = WarpUtilsInputSpec
    output_spec = WarpUtilsOutputSpec

    _cmd = 'fnirtfileutils'

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []

        suffix = 'field'
        if (isdefined(self.inputs.out_format)
                and self.inputs.out_format == 'spline'):
            suffix = 'coeffs'

        trait_spec = self.inputs.trait('out_file')
        trait_spec.name_template = "%s_" + suffix

        if self.inputs.write_jacobian:
            if not isdefined(self.inputs.out_jacobian):
                jac_spec = self.inputs.trait('out_jacobian')
                jac_spec.name_source = ['in_file']
                jac_spec.name_template = '%s_jac'
                jac_spec.output_name = 'out_jacobian'
        else:
            skip += ['out_jacobian']

        skip += ['write_jacobian']
        return super(WarpUtils, self)._parse_inputs(skip=skip)


class ConvertWarpInputSpec(FSLCommandInputSpec):
    reference = File(
        exists=True,
        argstr='--ref=%s',
        mandatory=True,
        position=1,
        desc='Name of a file in target space of the full transform.')

    out_file = File(
        argstr='--out=%s',
        position=-1,
        name_source=['reference'],
        name_template='%s_concatwarp',
        output_name='out_file',
        desc=('Name of output file, containing warps that are the combination '
              'of all those given as arguments. The format of this will be a '
              'field-file (rather than spline coefficients) with any affine '
              'components included.'))

    premat = File(
        exists=True,
        argstr='--premat=%s',
        desc='filename for pre-transform (affine matrix)')

    warp1 = File(
        exists=True,
        argstr='--warp1=%s',
        desc='Name of file containing initial '
        'warp-fields/coefficients (follows premat). This could '
        'e.g. be a fnirt-transform from a subjects structural '
        'scan to an average of a group of subjects.')

    midmat = File(
        exists=True,
        argstr="--midmat=%s",
        desc="Name of file containing mid-warp-affine transform")

    warp2 = File(
        exists=True,
        argstr='--warp2=%s',
        desc='Name of file containing secondary warp-fields/coefficients '
        '(after warp1/midmat but before postmat). This could e.g. be a '
        'fnirt-transform from the average of a group of subjects to some '
        'standard space (e.g. MNI152).')

    postmat = File(
        exists=True,
        argstr='--postmat=%s',
        desc='Name of file containing an affine transform (applied last). It '
        'could e.g. be an affine transform that maps the MNI152-space '
        'into a better approximation to the Talairach-space (if indeed '
        'there is one).')

    shift_in_file = File(
        exists=True,
        argstr='--shiftmap=%s',
        desc='Name of file containing a "shiftmap", a non-linear transform '
        'with displacements only in one direction (applied first, before '
        'premat). This would typically be a fieldmap that has been '
        'pre-processed using fugue that maps a subjects functional (EPI) '
        'data onto an undistorted space (i.e. a space that corresponds '
        'to his/her true anatomy).')

    shift_direction = traits.Enum(
        'y-',
        'y',
        'x',
        'x-',
        'z',
        'z-',
        argstr="--shiftdir=%s",
        requires=['shift_in_file'],
        desc='Indicates the direction that the distortions from '
        '--shiftmap goes. It depends on the direction and '
        'polarity of the phase-encoding in the EPI sequence.')

    cons_jacobian = traits.Bool(
        False,
        argstr='--constrainj',
        desc='Constrain the Jacobian of the warpfield to lie within specified '
        'min/max limits.')

    jacobian_min = traits.Float(
        argstr='--jmin=%f',
        desc='Minimum acceptable Jacobian value for '
        'constraint (default 0.01)')
    jacobian_max = traits.Float(
        argstr='--jmax=%f',
        desc='Maximum acceptable Jacobian value for '
        'constraint (default 100.0)')

    abswarp = traits.Bool(
        argstr='--abs',
        xor=['relwarp'],
        desc='If set it indicates that the warps in --warp1 and --warp2 should'
        ' be interpreted as absolute. I.e. the values in --warp1/2 are '
        'the coordinates in the next space, rather than displacements. '
        'This flag is ignored if --warp1/2 was created by fnirt, which '
        'always creates relative displacements.')

    relwarp = traits.Bool(
        argstr='--rel',
        xor=['abswarp'],
        desc='If set it indicates that the warps in --warp1/2 should be '
        'interpreted as relative. I.e. the values in --warp1/2 are '
        'displacements from the coordinates in the next space.')

    out_abswarp = traits.Bool(
        argstr='--absout',
        xor=['out_relwarp'],
        desc='If set it indicates that the warps in --out should be absolute, '
        'i.e. the values in --out are displacements from the coordinates '
        'in --ref.')

    out_relwarp = traits.Bool(
        argstr='--relout',
        xor=['out_abswarp'],
        desc='If set it indicates that the warps in --out should be relative, '
        'i.e. the values in --out are displacements from the coordinates '
        'in --ref.')


class ConvertWarpOutputSpec(TraitedSpec):
    out_file = File(
        exists=True,
        desc='Name of output file, containing the warp as field or '
        'coefficients.')


class ConvertWarp(FSLCommand):
    """Use FSL `convertwarp <http://fsl.fmrib.ox.ac.uk/fsl/fsl-4.1.9/fnirt/warp_utils.html>`_
    for combining multiple transforms into one.


    Examples
    --------

    >>> from nipype.interfaces.fsl import ConvertWarp
    >>> warputils = ConvertWarp()
    >>> warputils.inputs.warp1 = "warpfield.nii"
    >>> warputils.inputs.reference = "T1.nii"
    >>> warputils.inputs.relwarp = True
    >>> warputils.inputs.output_type = "NIFTI_GZ"
    >>> warputils.cmdline # doctest: +ELLIPSIS
    'convertwarp --ref=T1.nii --rel --warp1=warpfield.nii --out=T1_concatwarp.nii.gz'
    >>> res = warputils.run() # doctest: +SKIP


    """

    input_spec = ConvertWarpInputSpec
    output_spec = ConvertWarpOutputSpec
    _cmd = 'convertwarp'


class WarpPointsBaseInputSpec(CommandLineInputSpec):
    in_coords = File(
        exists=True,
        position=-1,
        argstr='%s',
        mandatory=True,
        desc='filename of file containing coordinates')
    xfm_file = File(
        exists=True,
        argstr='-xfm %s',
        xor=['warp_file'],
        desc='filename of affine transform (e.g. source2dest.mat)')
    warp_file = File(
        exists=True,
        argstr='-warp %s',
        xor=['xfm_file'],
        desc='filename of warpfield (e.g. '
        'intermediate2dest_warp.nii.gz)')
    coord_vox = traits.Bool(
        True,
        argstr='-vox',
        xor=['coord_mm'],
        desc='all coordinates in voxels - default')
    coord_mm = traits.Bool(
        False, argstr='-mm', xor=['coord_vox'], desc='all coordinates in mm')
    out_file = File(
        name_source='in_coords',
        name_template='%s_warped',
        output_name='out_file',
        desc='output file name')


class WarpPointsInputSpec(WarpPointsBaseInputSpec):
    src_file = File(
        exists=True,
        argstr='-src %s',
        mandatory=True,
        desc='filename of source image')
    dest_file = File(
        exists=True,
        argstr='-dest %s',
        mandatory=True,
        desc='filename of destination image')


class WarpPointsOutputSpec(TraitedSpec):
    out_file = File(
        exists=True,
        desc='Name of output file, containing the warp as field or '
        'coefficients.')


class WarpPoints(CommandLine):
    """Use FSL `img2imgcoord <http://fsl.fmrib.ox.ac.uk/fsl/fsl-4.1.9/flirt/overview.html>`_
    to transform point sets. Accepts plain text files and vtk files.

    .. Note:: transformation of TrackVis trk files is not yet implemented


    Examples
    --------

    >>> from nipype.interfaces.fsl import WarpPoints
    >>> warppoints = WarpPoints()
    >>> warppoints.inputs.in_coords = 'surf.txt'
    >>> warppoints.inputs.src_file = 'epi.nii'
    >>> warppoints.inputs.dest_file = 'T1.nii'
    >>> warppoints.inputs.warp_file = 'warpfield.nii'
    >>> warppoints.inputs.coord_mm = True
    >>> warppoints.cmdline # doctest: +ELLIPSIS
    'img2imgcoord -mm -dest T1.nii -src epi.nii -warp warpfield.nii surf.txt'
    >>> res = warppoints.run() # doctest: +SKIP


    """

    input_spec = WarpPointsInputSpec
    output_spec = WarpPointsOutputSpec
    _cmd = 'img2imgcoord'
    _terminal_output = 'stream'

    def __init__(self, command=None, **inputs):
        self._tmpfile = None
        self._in_file = None
        self._outformat = None

        super(WarpPoints, self).__init__(command=command, **inputs)

    def _format_arg(self, name, trait_spec, value):
        if name == 'out_file':
            return ''

        return super(WarpPoints, self)._format_arg(name, trait_spec, value)

    def _parse_inputs(self, skip=None):
        fname, ext = op.splitext(self.inputs.in_coords)
        setattr(self, '_in_file', fname)
        setattr(self, '_outformat', ext[1:])
        first_args = super(WarpPoints,
                           self)._parse_inputs(skip=['in_coords', 'out_file'])

        second_args = fname + '.txt'

        if ext in ['.vtk', '.trk']:
            if self._tmpfile is None:
                self._tmpfile = tempfile.NamedTemporaryFile(
                    suffix='.txt', dir=os.getcwd(), delete=False).name
            second_args = self._tmpfile

        return first_args + [second_args]

    def _vtk_to_coords(self, in_file, out_file=None):
        from ..vtkbase import tvtk
        from ...interfaces import vtkbase as VTKInfo

        if VTKInfo.no_tvtk():
            raise ImportError(
                'TVTK is required and tvtk package was not found')

        reader = tvtk.PolyDataReader(file_name=in_file + '.vtk')
        reader.update()
        mesh = VTKInfo.vtk_output(reader)
        points = mesh.points

        if out_file is None:
            out_file, _ = op.splitext(in_file) + '.txt'

        np.savetxt(out_file, points)
        return out_file

    def _coords_to_vtk(self, points, out_file):
        from ..vtkbase import tvtk
        from ...interfaces import vtkbase as VTKInfo

        if VTKInfo.no_tvtk():
            raise ImportError(
                'TVTK is required and tvtk package was not found')

        reader = tvtk.PolyDataReader(file_name=self.inputs.in_file)
        reader.update()

        mesh = VTKInfo.vtk_output(reader)
        mesh.points = points

        writer = tvtk.PolyDataWriter(file_name=out_file)
        VTKInfo.configure_input_data(writer, mesh)
        writer.write()

    def _trk_to_coords(self, in_file, out_file=None):
        from nibabel.trackvis import TrackvisFile
        trkfile = TrackvisFile.from_file(in_file)
        streamlines = trkfile.streamlines

        if out_file is None:
            out_file, _ = op.splitext(in_file)

        np.savetxt(streamlines, out_file + '.txt')
        return out_file + '.txt'

    def _coords_to_trk(self, points, out_file):
        raise NotImplementedError('trk files are not yet supported')

    def _overload_extension(self, value, name):
        if name == 'out_file':
            return '%s.%s' % (value, getattr(self, '_outformat'))

    def _run_interface(self, runtime):
        fname = getattr(self, '_in_file')
        outformat = getattr(self, '_outformat')
        tmpfile = None

        if outformat == 'vtk':
            tmpfile = self._tmpfile
            self._vtk_to_coords(fname, out_file=tmpfile)
        elif outformat == 'trk':
            tmpfile = self._tmpfile
            self._trk_to_coords(fname, out_file=tmpfile)

        runtime = super(WarpPoints, self)._run_interface(runtime)
        newpoints = np.fromstring(
            '\n'.join(runtime.stdout.split('\n')[1:]), sep=' ')

        if tmpfile is not None:
            try:
                os.remove(tmpfile.name)
            except:
                pass

        out_file = self._filename_from_source('out_file')

        if outformat == 'vtk':
            self._coords_to_vtk(newpoints, out_file)
        elif outformat == 'trk':
            self._coords_to_trk(newpoints, out_file)
        else:
            np.savetxt(out_file, newpoints.reshape(-1, 3))

        return runtime


class WarpPointsToStdInputSpec(WarpPointsBaseInputSpec):
    img_file = File(
        exists=True,
        argstr='-img %s',
        mandatory=True,
        desc=('filename of input image'))
    std_file = File(
        exists=True,
        argstr='-std %s',
        mandatory=True,
        desc=('filename of destination image'))
    premat_file = File(
        exists=True,
        argstr='-premat %s',
        desc=('filename of pre-warp affine transform '
              '(e.g. example_func2highres.mat)'))


class WarpPointsToStd(WarpPoints):
    """
    Use FSL `img2stdcoord <http://fsl.fmrib.ox.ac.uk/fsl/fsl-4.1.9/flirt/overview.html>`_
    to transform point sets to standard space coordinates. Accepts plain text
    files and vtk files.

    .. Note:: transformation of TrackVis trk files is not yet implemented


    Examples
    --------

    >>> from nipype.interfaces.fsl import WarpPointsToStd
    >>> warppoints = WarpPointsToStd()
    >>> warppoints.inputs.in_coords = 'surf.txt'
    >>> warppoints.inputs.img_file = 'T1.nii'
    >>> warppoints.inputs.std_file = 'mni.nii'
    >>> warppoints.inputs.warp_file = 'warpfield.nii'
    >>> warppoints.inputs.coord_mm = True
    >>> warppoints.cmdline # doctest: +ELLIPSIS
    'img2stdcoord -mm -img T1.nii -std mni.nii -warp warpfield.nii surf.txt'
    >>> res = warppoints.run() # doctest: +SKIP


    """

    input_spec = WarpPointsToStdInputSpec
    output_spec = WarpPointsOutputSpec
    _cmd = 'img2stdcoord'
    _terminal_output = 'file_split'


class WarpPointsFromStdInputSpec(CommandLineInputSpec):
    img_file = File(
        exists=True,
        argstr='-img %s',
        mandatory=True,
        desc='filename of a destination image')
    std_file = File(
        exists=True,
        argstr='-std %s',
        mandatory=True,
        desc='filename of the image in standard space')
    in_coords = File(
        exists=True,
        position=-2,
        argstr='%s',
        mandatory=True,
        desc='filename of file containing coordinates')
    xfm_file = File(
        exists=True,
        argstr='-xfm %s',
        xor=['warp_file'],
        desc='filename of affine transform (e.g. source2dest.mat)')
    warp_file = File(
        exists=True,
        argstr='-warp %s',
        xor=['xfm_file'],
        desc='filename of warpfield (e.g. '
        'intermediate2dest_warp.nii.gz)')
    coord_vox = traits.Bool(
        True,
        argstr='-vox',
        xor=['coord_mm'],
        desc='all coordinates in voxels - default')
    coord_mm = traits.Bool(
        False, argstr='-mm', xor=['coord_vox'], desc='all coordinates in mm')


class WarpPointsFromStd(CommandLine):
    """
    Use FSL `std2imgcoord <http://fsl.fmrib.ox.ac.uk/fsl/fsl-4.1.9/flirt/overview.html>`_
    to transform point sets to standard space coordinates. Accepts plain text coordinates
    files.


    Examples
    --------

    >>> from nipype.interfaces.fsl import WarpPointsFromStd
    >>> warppoints = WarpPointsFromStd()
    >>> warppoints.inputs.in_coords = 'surf.txt'
    >>> warppoints.inputs.img_file = 'T1.nii'
    >>> warppoints.inputs.std_file = 'mni.nii'
    >>> warppoints.inputs.warp_file = 'warpfield.nii'
    >>> warppoints.inputs.coord_mm = True
    >>> warppoints.cmdline # doctest: +ELLIPSIS
    'std2imgcoord -mm -img T1.nii -std mni.nii -warp warpfield.nii surf.txt'
    >>> res = warppoints.run() # doctest: +SKIP


    """

    input_spec = WarpPointsFromStdInputSpec
    output_spec = WarpPointsOutputSpec
    _cmd = 'std2imgcoord'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath('stdout.nipype')
        return outputs


class MotionOutliersInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        desc="unfiltered 4D image",
        argstr="-i %s")
    out_file = File(
        argstr="-o %s",
        name_source='in_file',
        name_template='%s_outliers.txt',
        keep_extension=True,
        desc='output outlier file name',
        hash_files=False)
    mask = File(
        exists=True, argstr="-m %s", desc="mask image for calculating metric")
    metric = traits.Enum(
        'refrms', ['refrms', 'dvars', 'refmse', 'fd', 'fdrms'],
        argstr="--%s",
        desc='metrics: refrms - RMS intensity difference to reference volume '
        'as metric [default metric], refmse - Mean Square Error version '
        'of refrms (used in original version of fsl_motion_outliers), '
        'dvars - DVARS, fd - frame displacement, fdrms - FD with RMS '
        'matrix calculation')
    threshold = traits.Float(
        argstr="--thresh=%g",
        desc=("specify absolute threshold value "
              "(otherwise use box-plot cutoff = P75 + "
              "1.5*IQR)"))
    no_motion_correction = traits.Bool(
        argstr="--nomoco",
        desc="do not run motion correction (assumed already done)")
    dummy = traits.Int(
        argstr="--dummy=%d",
        desc='number of dummy scans to delete (before running anything and '
        'creating EVs)')
    out_metric_values = File(
        argstr="-s %s",
        name_source='in_file',
        name_template='%s_metrics.txt',
        keep_extension=True,
        desc='output metric values (DVARS etc.) file name',
        hash_files=False)
    out_metric_plot = File(
        argstr="-p %s",
        name_source='in_file',
        name_template='%s_metrics.png',
        hash_files=False,
        keep_extension=True,
        desc='output metric values plot (DVARS etc.) file name')


class MotionOutliersOutputSpec(TraitedSpec):
    out_file = File(exists=True)
    out_metric_values = File(exists=True)
    out_metric_plot = File(exists=True)


class MotionOutliers(FSLCommand):
    """
    Use FSL fsl_motion_outliers`http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FSLMotionOutliers`_ to find outliers in timeseries (4d) data.
    Examples
    --------
    >>> from nipype.interfaces.fsl import MotionOutliers
    >>> mo = MotionOutliers()
    >>> mo.inputs.in_file = "epi.nii"
    >>> mo.cmdline # doctest: +ELLIPSIS
    'fsl_motion_outliers -i epi.nii -o epi_outliers.txt -p epi_metrics.png -s epi_metrics.txt'
    >>> res = mo.run() # doctest: +SKIP
    """

    input_spec = MotionOutliersInputSpec
    output_spec = MotionOutliersOutputSpec
    _cmd = 'fsl_motion_outliers'
