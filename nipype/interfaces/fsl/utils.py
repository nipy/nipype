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

from nipype.interfaces.fsl.base import FSLCommand,\
    FSLCommandInputSpec, Info
from nipype.interfaces.base import traits, TraitedSpec,\
    OutputMultiPath, File
from nipype.utils.misc import isdefined
from nipype.utils.filemanip import load_json, save_json

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class ImageMeantsInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, desc = 'input file for computing the average timeseries',
                  argstr='-i %s', position=0, mandatory=True)
    out_file = File(desc = 'name of output text matrix',argstr='-o %s', genfile=True)
    mask = File(exists=True, desc='input 3D mask',argstr='-m %s')
    spatial_coord = traits.List(traits.Int, desc='<x y z>	requested spatial coordinate (instead of mask)',
                               argstr='-c %s')
    use_mm = traits.Bool(desc='use mm instead of voxel coordinates (for -c option)',
                        argstr='--usemm')
    show_all = traits.Bool(desc='show all voxel time series (within mask) instead of averaging',
                          argstr='--showall')
    eig = traits.Bool(desc='calculate Eigenvariate(s) instead of mean (output will have 0 mean)',
                      argstr='--eig')
    order = traits.Int(1,desc='select number of Eigenvariates',argstr='--order=%d',usedefault=True)
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
                                                  suffix = '_ts',
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
                                              suffix = '_smooth')
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
                                              suffix = '_merged')
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
                                              suffix = '_roi')
        return outputs

    def _gen_filename(self, name):
        if name == 'roi_file':
            return self._list_outputs()[name]
        return None

class SplitInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, argstr="%s", position = 0, desc="input filename")
    out_base_name = traits.Str(argstr="%s", position=1, desc="outputs prefix")
    dimension = traits.Enum('t','x','y','z', argstr="-%s", position=2, desc="dimension along which the file will be split")

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
        ext =  Info.output_type_to_ext(self.inputs.output_type)
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
    in_file = File(exists=True,argst="-i %s",desc="input file name (4D image)",mandatory=True)
    out_file = File(argst="-o %s",desc="output file name for the filtered data",genfile=True)
    design_file = File(exists=True,argst="-d %s",desc="design	file name of the matrix with "\
                       "time courses (e.g. GLM design or MELODIC mixing matrix)",mandatory=True)
    filter_out = traits.List(traits.Int,argst="-f %s",desc="filter out part of the "\
                             "regression model, e.g. -f '1,2,3'",mandatory=True)
    mask = File(exists=True,argst="-m %s",desc="mask image file name")
    var_norm = traits.Bool(argst="--vn",desc="perform variance-normalization on data")
    out_file = traits.Bool(argst="--out_data",desc="output data")
    out_vnscales = traits.Bool(argst="--out_vnscales",desc="output scaling factors for variance normalization")

class FilterRegressorOutputSpec(TraitedSpec):
    out_file = File(exists=True,desc="output file name for the filtered data")

class FilterRegressor(FSLCommand):
    """Data de-noising by regressing out part of a design matrix
    
    Uses simple OLS regression on 4D images
    """
    input_spec = FilterRegressorInputSpec
    output_spec = FilterRegressorOutputSpec
    _cmd = 'fsl_regfilt'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(outputs['out_file']):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,suffix='_regfilt')
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
                    return self.inputs.op_string%self.inputs.mask_file
                else:
                    raise ValueError('-k %s option in op_string requires mask_file')
        return super(ImageStats, self)._format_arg(name, trait_spec, value)
    
    def aggregate_outputs(self, runtime=None):
        outputs = self._outputs()
        outfile = os.path.join(os.getcwd(), 'stat_result.json')
        if runtime is None:
            out_stat = load_json(outfile)['stat']
        else:
            out_stat = []
            for line in runtime.stdout.split('\n'):
                if line:
                    values = line.split()
                    if len(values)>1:
                        out_stat.append([float(val) for val in values])
                    else:
                        out_stat.extend([float(val) for val in values])
            if len(out_stat)==1:
                out_stat = out_stat[0]
            save_json(outfile, dict(stat=out_stat))
        outputs.out_stat = out_stat
        return outputs
