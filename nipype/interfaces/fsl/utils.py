# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

Examples
--------
See the docstrings of the individual classes for examples.

"""

import os
from glob import glob
import warnings

import numpy as np

from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec, Info
from nipype.interfaces.base import (traits, TraitedSpec, OutputMultiPath, File,
                                    isdefined)
from nipype.utils.filemanip import load_json, save_json, split_filename, fname_presuffix

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class ImageMeantsInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, desc='input file for computing the average timeseries',
                   argstr='-i %s', position=0, mandatory=True)
    out_file = File(desc='name of output text matrix', argstr='-o %s', genfile=True)
    mask = File(exists=True, desc='input 3D mask', argstr='-m %s')
    spatial_coord = traits.List(traits.Int, desc='<x y z>	requested spatial coordinate (instead of mask)',
                               argstr='-c %s')
    use_mm = traits.Bool(desc='use mm instead of voxel coordinates (for -c option)',
                        argstr='--usemm')
    show_all = traits.Bool(desc='show all voxel time series (within mask) instead of averaging',
                          argstr='--showall')
    eig = traits.Bool(desc='calculate Eigenvariate(s) instead of mean (output will have 0 mean)',
                      argstr='--eig')
    order = traits.Int(1, desc='select number of Eigenvariates', argstr='--order=%d', usedefault=True)
    nobin = traits.Bool(desc='do not binarise the mask for calculation of Eigenvariates',
                        argstr='--no_bin')
    transpose = traits.Bool(desc='output results in transpose format (one row per voxel/mean)',
                            argstr='--transpose')


class ImageMeantsOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="path/name of output text matrix")


class ImageMeants(FSLCommand):
    """ Use fslmeants for printing the average timeseries (intensities) to
        the screen (or saves to a file). The average is taken over all voxels in the
        mask (or all voxels in the image if no mask is specified)

    """
    _cmd = 'fslmeants'
    input_spec = ImageMeantsInputSpec
    output_spec = ImageMeantsOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(outputs['out_file']):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                                                  suffix='_ts',
                                                  ext='.txt',
                                                  change_ext=True)
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None


class SmoothInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, argstr="%s", position=0, mandatory=True)
    fwhm = traits.Float(argstr="-kernel gauss %f -fmean", position=1,
                        mandatory=True)
    smoothed_file = File(argstr="%s", position=2, genfile=True)


class SmoothOutputSpec(TraitedSpec):
    smoothed_file = File(exists=True)


class Smooth(FSLCommand):
    '''Use fslmaths to smooth the image
    '''

    input_spec = SmoothInputSpec
    output_spec = SmoothOutputSpec
    _cmd = 'fslmaths'

    def _gen_filename(self, name):
        if name == 'smoothed_file':
            return self._list_outputs()['smoothed_file']
        return None

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['smoothed_file'] = self.inputs.smoothed_file
        if not isdefined(outputs['smoothed_file']):
            outputs['smoothed_file'] = self._gen_fname(self.inputs.in_file,
                                              suffix='_smooth')
        return outputs

    def _format_arg(self, name, trait_spec, value):
        if name == 'fwhm':
            # ohinds: convert fwhm to stddev
            return super(Smooth, self)._format_arg(name, trait_spec, float(value) / np.sqrt(8 * np.log(2)))
        return super(Smooth, self)._format_arg(name, trait_spec, value)


class MergeInputSpec(FSLCommandInputSpec):
    in_files = traits.List(File(exists=True), argstr="%s", position=2, mandatory=True)
    dimension = traits.Enum('t', 'x', 'y', 'z', argstr="-%s", position=0,
                            desc="dimension along which the file will be merged",
                            mandatory=True)
    merged_file = File(argstr="%s", position=1, genfile=True)


class MergeOutputSpec(TraitedSpec):
    merged_file = File(exists=True)


class Merge(FSLCommand):
    """Use fslmerge to concatenate images
    """

    _cmd = 'fslmerge'
    input_spec = MergeInputSpec
    output_spec = MergeOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['merged_file'] = self.inputs.merged_file
        if not isdefined(outputs['merged_file']):
            outputs['merged_file'] = self._gen_fname(self.inputs.in_files[0],
                                              suffix='_merged')
        else:
            outputs['merged_file'] = os.path.realpath(self.inputs.merged_file)

        return outputs

    def _gen_filename(self, name):
        if name == 'merged_file':
            return self._list_outputs()[name]
        return None


class ExtractROIInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, argstr="%s", position=0, desc="input file", mandatory=True)
    roi_file = File(argstr="%s", position=1, desc="output file", genfile=True)
    x_min = traits.Int(argstr="%d", position=2)
    x_size = traits.Int(argstr="%d", position=3)
    y_min = traits.Int(argstr="%d", position=4)
    y_size = traits.Int(argstr="%d", position=5)
    z_min = traits.Int(argstr="%d", position=6)
    z_size = traits.Int(argstr="%d", position=7)
    t_min = traits.Int(argstr="%d", position=8)
    t_size = traits.Int(argstr="%d", position=9)
    _crop_xor = ['x_min', 'x_size', 'y_min', 'y_size', 'z_min', 'z_size', 't_min', 't_size']
    crop_list = traits.List(traits.Tuple(traits.Int, traits.Int),
                            argstr="%s", position=2, xor=_crop_xor,
                            help="list of two tuples specifying crop options")


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
    >>> fslroi = ExtractROI(in_file=anatfile, roi_file='bar.nii', t_min=0, t_size=1)
    >>> fslroi.cmdline == 'fslroi %s bar.nii 0 1'%anatfile
    True
    """

    _cmd = 'fslroi'
    input_spec = ExtractROIInputSpec
    output_spec = ExtractROIOutputSpec

    def _format_arg(self, name, spec, value):

        if name == "crop_list":
            return " ".join(map(str, sum(map(list, value), [])))
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
            outputs['roi_file'] = self._gen_fname(self.inputs.in_file,
                                              suffix='_roi')
        return outputs

    def _gen_filename(self, name):
        if name == 'roi_file':
            return self._list_outputs()[name]
        return None


class SplitInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, argstr="%s", position=0, mandatory=True,
                   desc="input filename")
    out_base_name = traits.Str(argstr="%s", position=1, desc="outputs prefix")
    dimension = traits.Enum('t', 'x', 'y', 'z', argstr="-%s", position=2,
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
        outputs['out_files'] = sorted(glob(os.path.join(os.getcwd(),
                                                    outbase + ext)))
        return outputs


class ImageMathsInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, argstr="%s", mandatory=True, position=1)
    in_file2 = File(exists=True, argstr="%s", position=3)
    out_file = File(argstr="%s", position=4, genfile=True)
    op_string = traits.Str(argstr="%s", position=2,
                           desc="string defining the operation, i. e. -add")
    suffix = traits.Str(desc="out_file suffix")
    out_data_type = traits.Enum('char', 'short', 'int', 'float', 'double',
                                'input', argstr="-odt %s", position=5,
                                desc="output datatype, one of (char, short, int, float, double, input)")


class ImageMathsOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class ImageMaths(FSLCommand):
    """Use FSL fslmaths command to allow mathematical manipulation of images

    `FSL info <http://www.fmrib.ox.ac.uk/fslcourse/lectures/practicals/intro/index.htm#fslutils>`_

    Examples
    --------

    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import anatfile
    >>> maths = fsl.ImageMaths(in_file=anatfile, op_string= '-add 5', \
                               out_file='foo_maths.nii')
    >>> maths.cmdline == 'fslmaths %s -add 5 foo_maths.nii'%anatfile
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
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                                              suffix=suffix)
        return outputs


class FilterRegressorInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, argstr="-i %s", desc="input file name (4D image)", mandatory=True, position=1)
    out_file = File(argstr="-o %s", desc="output file name for the filtered data", genfile=True, position=2)
    design_file = File(exists=True, argstr="-d %s", position=3, mandatory=True,
                       desc="name of the matrix with time courses (e.g. GLM design or MELODIC mixing matrix)")
    filter_columns = traits.List(traits.Int, argstr="-f '%s'", xor=["filter_all"], mandatory=True, position=4,
                        desc="(1-based) column indices to filter out of the data")
    filter_all = traits.Bool(mandatory=True, argstr="-f '%s'", xor=["filter_columns"], position=4,
                             desc="use all columns in the design file in denoising")
    mask = File(exists=True, argstr="-m %s", desc="mask image file name")
    var_norm = traits.Bool(argstr="--vn", desc="perform variance-normalization on data")
    out_vnscales = traits.Bool(argstr="--out_vnscales", desc="output scaling factors for variance normalization")


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
            return trait_spec.argstr % ",".join(map(str, range(1, n_cols + 1)))
        return super(FilterRegressor, self)._format_arg(name, trait_spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(outputs['out_file']):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file, suffix='_regfilt')
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None


class ImageStatsInputSpec(FSLCommandInputSpec):
    split_4d = traits.Bool(argstr='-t', position=1,
                           desc='give a separate output line for each 3D volume of a 4D timeseries')
    in_file = File(exists=True, argstr="%s", mandatory=True, position=2,
                   desc='input file to generate stats of')
    op_string = traits.Str(argstr="%s", mandatory=True, position=3,
                           desc="string defining the operation, options are " \
    "applied in order, e.g. -M -l 10 -M will report the non-zero mean, apply a" \
    "threshold and then report the new nonzero mean")
    mask_file = File(exists=True, argstr="", desc='mask file used for option -k %s')


class ImageStatsOutputSpec(TraitedSpec):
    out_stat = traits.Any(desc='stats output')


class ImageStats(FSLCommand):
    """Use FSL fslstats command to calculate stats from images

    `FSL info <http://www.fmrib.ox.ac.uk/fslcourse/lectures/practicals/intro/index.htm#fslutils>`_

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
                    raise ValueError('-k %s option in op_string requires mask_file')
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


class OverlayInputSpec(FSLCommandInputSpec):
    transparency = traits.Bool(desc='make overlay colors semi-transparent',
                               position=1, argstr='%s', usedefault=True, default_value=True)
    out_type = traits.Enum('float', 'int', position=2, usedefault=True, argstr='%s',
                            desc='write output with float or int')
    use_checkerboard = traits.Bool(desc='use checkerboard mask for overlay',
                                   argstr='-c', position=3)
    background_image = File(exists=True, position=4, mandatory=True, argstr='%s',
                            desc='image to use as background')
    _xor_inputs = ('auto_thresh_bg', 'full_bg_range', 'bg_thresh')
    auto_thresh_bg = traits.Bool(desc='automatically threhsold the background image',
                                 argstr='-a', position=5, xor=_xor_inputs, mandatory=True)
    full_bg_range = traits.Bool(desc='use full range of background image',
                                argstr='-A', position=5, xor=_xor_inputs, mandatory=True)
    bg_thresh = traits.Tuple(traits.Float, traits.Float, argstr='%.3f %.3f', position=5,
                             desc='min and max values for background intensity',
                             xor=_xor_inputs, mandatory=True)
    stat_image = File(exists=True, position=6, mandatory=True, argstr='%s',
                             desc='statistical image to overlay in color')
    stat_thresh = traits.Tuple(traits.Float, traits.Float, position=7, mandatory=True,
                               desc='min and max values for the statistical overlay',
                               argstr='%.2f %.2f')
    show_negative_stats = traits.Bool(desc='display negative statistics in overlay',
                                      xor=['stat_image2'], argstr='%s', position=8)
    stat_image2 = File(exists=True, position=9, xor=['show_negative_stats'], argstr='%s',
                              desc='second statistical image to overlay in color')
    stat_thresh2 = traits.Tuple(traits.Float, traits.Float, position=10,
                                desc='min and max values for second statistical overlay',
                                argstr='%.2f %.2f')
    out_file = File(desc='combined image volume', position=-1, argstr='%s', genfile=True)


class OverlayOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='combined image volume')


class Overlay(FSLCommand):
    """ Use FSL's overlay command to combine background and statistical images into one volume

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
                    stem = "%s_and_%s" % (split_filename(self.inputs.stat_image)[1],
                                          split_filename(self.inputs.stat_image2)[1])
            else:
                stem = split_filename(self.inputs.stat_image)[1]
            out_file = self._gen_fname(stem, suffix='_overlay')
        outputs['out_file'] = out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        return None


class SlicerInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, position=1, argstr='%s', mandatory=True,
                   desc='input volume')
    image_edges = File(exists=True, position=2, argstr='%s',
        desc='volume to display edge overlay for (useful for checking registration')
    label_slices = traits.Bool(position=3, argstr='-L', desc='display slice number',
                               usedefault=True, default_value=True)
    colour_map = File(exists=True, position=4, argstr='-l %s',
                      desc='use different colour map from that stored in nifti header')
    intensity_range = traits.Tuple(traits.Float, traits.Float, position=5, argstr='-i %.3f %.3f',
                                   desc='min and max intensities to display')
    threshold_edges = traits.Float(position=6, argstr='-e %.3f', desc='use threshold for edges')
    dither_edges = traits.Bool(position=7, argstr='-t',
                               desc='produce semi-transparaent (dithered) edges')
    nearest_neighbour = traits.Bool(position=8, argstr='-n',
                                    desc='use nearest neighbour interpolation for output')
    show_orientation = traits.Bool(position=9, argstr='%s', usedefault=True, default_value=True,
                                    desc='label left-right orientation')
    _xor_options = ('single_slice', 'middle_slices', 'all_axial', 'sample_axial')
    single_slice = traits.Enum('x', 'y', 'z', position=10, argstr='-%s',
                               xor=_xor_options, requires=['slice_number'],
                               desc='output picture of single slice in the x, y, or z plane')
    slice_number = traits.Int(position=11, argstr='-%d', desc='slice number to save in picture')
    middle_slices = traits.Bool(position=10, argstr='-a', xor=_xor_options,
                                desc='output picture of mid-sagital, axial, and coronal slices')
    all_axial = traits.Bool(position=10, argstr='-A', xor=_xor_options, requires=['image_width'],
                            desc='output all axial slices into one picture')
    sample_axial = traits.Int(position=10, argstr='-S %d',
                              xor=_xor_options, requires=['image_width'],
                              desc='output every n axial slices into one picture')
    image_width = traits.Int(position=-2, argstr='%d', desc='max picture width')
    out_file = File(position=-1, genfile=True, argstr='%s', desc='picture to write')
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
        outputs['out_file'] = out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        return None


class PlotTimeSeriesInputSpec(FSLCommandInputSpec):

    in_file = traits.Either(File(exists=True), traits.List(File(exists=True)),
                           mandatory=True, argstr="%s", position=1,
                           desc="file or list of files with columns of timecourse information")
    plot_start = traits.Int(argstr="--start=%d", xor=("plot_range",),
                            desc="first column from in-file to plot")
    plot_finish = traits.Int(argstr="--finish=%d", xor=("plot_range",),
                             desc="final column from in-file to plot")
    plot_range = traits.Tuple(traits.Int, traits.Int, argstr="%s", xor=("plot_start", "plot_finish"),
                              desc="first and last columns from the in-file to plot")
    title = traits.Str(argstr="%s", desc="plot title")
    legend_file = File(exists=True, argstr="--legend=%s", desc="legend file")
    labels = traits.Either(traits.Str, traits.List(traits.Str),
                           argstr="%s", desc="label or list of labels")
    y_min = traits.Float(argstr="--ymin=%.2f", desc="minumum y value", xor=("y_range",))
    y_max = traits.Float(argstr="--ymax=%.2f", desc="maximum y value", xor=("y_range",))
    y_range = traits.Tuple(traits.Float, traits.Float, argstr="%s", xor=("y_min", "y_max"),
                           desc="min and max y axis values")
    x_units = traits.Int(argstr="-u %d", usedefault=True, default_value=1,
                         desc="scaling units for x-axis (between 1 and length of in file)")
    plot_size = traits.Tuple(traits.Int, traits.Int, argstr="%s",
                             desc="plot image height and width")
    x_precision = traits.Int(argstr="--precision=%d", desc="precision of x-axis labels")
    sci_notation = traits.Bool(argstr="--sci", desc="switch on scientific notation")
    out_file = File(argstr="-o %s", genfile=True, desc="image to write")


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
        outputs['out_file'] = out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        return None


class PlotMotionParamsInputSpec(FSLCommandInputSpec):

    in_file = traits.Either(File(exists=True), traits.List(File(exists=True)),
                            mandatory=True, argstr="%s", position=1,
                            desc="file with motion parameters")
    in_source = traits.Enum("spm", "fsl", mandatory=True,
                            desc="which program generated the motion parameter file - fsl, spm")
    plot_type = traits.Enum("rotations", "translations", "displacement", argstr="%s", mandatory=True,
                         desc="which motion type to plot - rotations, translations, displacement")
    plot_size = traits.Tuple(traits.Int, traits.Int, argstr="%s",
                             desc="plot image height and width")
    out_file = File(argstr="-o %s", genfile=True, desc="image to write")


class PlotMotionParamsOutputSpec(TraitedSpec):

    out_file = File(exists=True, desc='image to write')


class PlotMotionParams(FSLCommand):
    """Use fsl_tsplot to plot the estimated motion parameters from a realignment program.

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
    The 'in_source' attribute determines the order of columns that are expected in the
    source file.  FSL prints motion parameters in the order rotations, translations,
    while SPM prints them in the opposite order.  This interface should be able to
    plot timecourses of motion parameters generated from other sources as long as
    they fall under one of these two patterns.  For more flexibilty, see the
    :class:`fsl.PlotTimeSeries` interface.

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

            # Get the right starting and ending position depending on source package
            sfdict = dict(fsl_rot=(1, 3), fsl_tra=(4, 6), spm_rot=(4, 6), spm_tra=(1, 3))

            # Format the title properly
            sfstr = "--start=%d --finish=%d" % sfdict["%s_%s" % (source, value[:3])]
            titledict = dict(fsl="MCFLIRT", spm="Realign")
            unitdict = dict(rot="radians", tra="mm")

            title = "\'%s estimated %s (%s)\'" % (titledict[source], value, unitdict[value[:3]])

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
            plttype = dict(rot="rot", tra="trans", dis="disp")[self.inputs.plot_type[:3]]
            out_file = fname_presuffix(infile, suffix="_%s.png" % plttype, use_ext=False)
        outputs['out_file'] = out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        return None


class ConvertXFMInputSpec(FSLCommandInputSpec):

    in_file = File(exists=True, mandatory=True, argstr="%s", position=-1,
                   desc="input transformation matrix")
    in_file2 = File(exists=True, argstr="%s", position=-2,
                    desc="second input matrix (for use with fix_scale_skew or concat_xfm")
    _options = ["invert_xfm", "concat_xfm", "fix_scale_skew"]
    invert_xfm = traits.Bool(argstr="-inverse", position=-3, xor=_options,
                             desc="invert input transformation")
    concat_xfm = traits.Bool(argstr="-concat", position=-3, xor=_options, requires=["in_file2"],
                             desc="write joint transformation of two input matrices")
    fix_scale_skew = traits.Bool(argstr="-fixscaleskew", position=-3,
                                  xor=_options, requires=["in_file2"],
                                  desc="use secondary matrix to fix scale and skew")
    out_file = File(genfile=True, argstr="-omat %s", position=1,
                    desc="final transformation matrix")


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
            path, infile1, ext = split_filename(self.inputs.in_file)
            if self.inputs.invert_xfm:
                outfile = fname_presuffix(infile1,
                                          suffix="_inv.mat",
                                          newpath=os.getcwd(),
                                          use_ext=False)
            else:
                if self.inputs.concat_xfm:
                    path, infile2, ext = split_filename(self.inputs.in_file2)
                    outfile = fname_presuffix("%s_%s" % (infile1, infile2),
                                              suffix=".mat",
                                              newpath=os.getcwd(),
                                              use_ext=False)
                else:
                    outfile = fname_presuffix(infile1,
                                              suffix="_fix.mat",
                                              newpath=os.getcwd(),
                                              use_ext=False)
        outputs["out_file"] = outfile
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None


class SwapDimensionsInputSpec(FSLCommandInputSpec):

    in_file = File(exists=True, mandatory=True, argstr="%s", position="1",
                   desc="input image")
    _dims = ["x", "-x", "y", "-y", "z", "-z", "RL", "LR", "AP", "PA", "IS", "SI"]
    new_dims = traits.Tuple(traits.Enum(_dims), traits.Enum(_dims), traits.Enum(_dims),
                            argstr="%s %s %s", mandatory=True,
                            desc="3-tuple of new dimension order")
    out_file = File(genfile=True, argstr="%s", desc="image to write")


class SwapDimensionsOutputSpec(TraitedSpec):

    out_file = File(exists=True, desc="image with new dimensions")


class SwapDimensions(FSLCommand):
    """Use fslswapdim to alter the orientation of an image.

    This interface accepts a three-tuple corresponding to the new
    orientation.  You may either provide dimension ids in the form of
    (-)x, (-)y, or (-z), or nifti-syle dimension codes (RL, LR, AP, PA, IS, SI).

    """
    _cmd = "fslswapdim"
    input_spec = SwapDimensionsInputSpec
    output_spec = SwapDimensionsOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] = fname_presuffix(self.inputs.in_file,
                                                  suffix="_newdims",
                                                  use_ext=True,
                                                  newpath=os.getcwd())
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None


class PowerSpectrumInputSpec(FSLCommandInputSpec):
    # We use position args here as list indices - so a negative number
    # will put something on the end
    in_file = File(exists=True,
                  desc="input 4D file to estimate the power spectrum",
                  argstr='%s', position=0, mandatory=True)
    out_file = File(desc='name of output 4D file for power spectrum',
                   argstr='%s', position=1, genfile=True)


class PowerSpectrumOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="path/name of the output 4D power spectrum file")


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
            out_file = self._gen_fname(self.inputs.in_file,
                                       suffix='_ps')
        return out_file

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self._gen_outfilename()
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._gen_outfilename()
        return None
