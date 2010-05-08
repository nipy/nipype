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

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class SmoothInputSpec(FSLCommandInputSpec):
    infile = File(exists=True, argstr="%s", position=0, mandatory=True)
    fwhm = traits.Float(argstr="-kernel gauss %f -fmean", position=1,
                            mandatory=True)
    outfile = File(argstr="%s", position=2, genfile=True)

class SmoothOutputSpec(TraitedSpec):
    smoothedimage = File(exists=True)

class Smooth(FSLCommand):
    '''Use fslmaths to smooth the image

    This is dumb, of course - we should use nipy for such things! But it is a
    step along the way to get the "standard" FSL pipeline in place.

    This is meant to be a throwaway class, so it's not currently very robust.
    Effort would be better spent integrating basic numpy into nipype'''
    
    input_spec = SmoothInputSpec
    output_spec = SmoothOutputSpec
    _cmd = 'fslmaths'

    def _gen_filename(self, name):
        if name == 'outfile':
            return self._list_outputs()['smoothedimage']
        return None

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['smoothedimage'] = self.inputs.outfile
        if not isdefined(outputs['smoothedimage']):
            outputs['smoothedimage'] = self._gen_fname(self.inputs.infile,
                                              suffix = '_smooth')
        return outputs
    
    def _format_arg(self, name, trait_spec, value):
        if name == 'fwhm':
            # ohinds: convert fwhm to stddev
            return super(Smooth, self)._format_arg(name, trait_spec, float(value) / np.sqrt(8 * np.log(2)))
        else:
            return super(Smooth, self)._format_arg(name, trait_spec, value)

class MergeInputSpec(FSLCommandInputSpec):
    infiles = traits.List(File(exists=True), argstr="%s", position=2, mandatory=True)
    dimension = traits.Enum('t', 'x', 'y', 'z', argstr="-%s", position=0,
                            desc="dimension along which the file will be merged",
                            mandatory=True)
    outfile = File(argstr="%s", position=1, genfile=True)

class MergeOutputSpec(TraitedSpec):
    outfile = File(exists=True)

class Merge(FSLCommand):
    """Use fslmerge to concatenate images
    """

    _cmd = 'fslmerge'
    input_spec = MergeInputSpec
    output_spec = MergeOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['outfile'] = self.inputs.outfile
        if not isdefined(outputs['outfile']):
            outputs['outfile'] = self._gen_fname(self.inputs.infile,
                                              suffix = '_merged')
        return outputs
    
    def _gen_filename(self, name):
        if name == 'outfile':
            return self._list_outputs()[name]
        return None


class ExtractRoiInputSpec(FSLCommandInputSpec):
    infile = File(exists=True, argstr="%s", position=0, desc="input file", mandatory=True)
    outfile = File(argstr="%s", position=1, desc="output file", genfile=True)
    xmin = traits.Float(argstr="%f", position=2)
    xsize = traits.Float(argstr="%f", position=3)
    ymin = traits.Float(argstr="%f", position=4)
    ysize = traits.Float(argstr="%f", position=5)
    zmin = traits.Float(argstr="%f", position=6)
    zsize = traits.Float(argstr="%f", position=7)
    tmin = traits.Int(argstr="%d", position=8)
    tsize = traits.Int(argstr="%d", position=9)
    
class ExtractRoiOutputSpec(TraitedSpec):
    outfile = File(exists=True)

class ExtractRoi(FSLCommand):
    """Uses FSL Fslroi command to extract region of interest (ROI)
    from an image.

    You can a) take a 3D ROI from a 3D data set (or if it is 4D, the
    same ROI is taken from each time point and a new 4D data set is
    created), b) extract just some time points from a 4D data set, or
    c) control time and space limits to the ROI.  Note that the
    arguments are minimum index and size (not maximum index).  So to
    extract voxels 10 to 12 inclusive you would specify 10 and 3 (not
    10 and 12).
    
    >>> from nipype.interfaces import fsl
    >>> fslroi = fsl.ExtractRoi(infile='foo.nii', outfile='bar.nii', \
                                tmin=0, tsize=1)
    >>> fslroi.cmdline
    'fslroi foo.nii bar.nii 0 1'
    """
    
    _cmd = 'fslroi'
    input_spec = ExtractRoiInputSpec
    output_spec = ExtractRoiOutputSpec

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
        outputs['outfile'] = self.inputs.outfile
        if not isdefined(outputs['outfile']):
            outputs['outfile'] = self._gen_fname(self.inputs.infile,
                                              suffix = '_roi')
        return outputs
    
    def _gen_filename(self, name):
        if name == 'outfile':
            return self._list_outputs()[name]
        return None

class SplitInputSpec(FSLCommandInputSpec):
    infile = File(exists=True, argstr="%s", position = 0, desc="input filename")
    outbasename = traits.Str(argstr="%s", position=1, desc="outputs prefix")
    dimension = traits.Enum('t','x','y','z', argstr="-%s", position=2, desc="dimension along which the file will be split")
    
class SplitOutputSpec(TraitedSpec):
    outfiles = OutputMultiPath(File(exists=True))

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
        ext =  Info.outputtype_to_ext(self.inputs.outputtype)
        outbase = 'vol*'
        if isdefined(self.inputs.outbasename):
            outbase = '%s*' % self.inputs.outbasename
        outputs['outfiles'] = sorted(glob(os.path.join(os.getcwd(),
                                                    outbase + ext)))
        return outputs
    
class ImageMathsInputSpec(FSLCommandInputSpec):
    infile = File(exists=True, argstr="%s", mandatory=True, position=0)
    infile2 = File(exists=True, argstr="%s", position=2)
    outfile = File(argstr="%s", position=3, genfile=True)
    optstring = traits.Str(argstr="%s", mandatory=True, position=1,
                           desc="string defining the operation, i. e. -add")
    suffix = traits.Str(desc="outfile suffix")
    outdatatype = traits.Enum('char', 'short', 'int', 'float', 'double',
                              'input', argstr="-odt %s", position=4,
                              desc="output datatype, one of (char, short, int, float, double, input)")

class ImageMathsOutputSpec(TraitedSpec):
    outfile = File(exists=True)

class ImageMaths(FSLCommand):
    """Use FSL fslmaths command to allow mathematical manipulation of images
    Example:
    >>> from nipype.interfaces import fsl
    >>> import os
    >>> maths = fsl.ImageMaths(infile='foo.nii', optstring= '-add 5', \
                               outfile='foo_maths.nii')
    >>> maths.cmdline
    'fslmaths foo.nii -add 5 foo_maths.nii'

    """
    input_spec = ImageMathsInputSpec
    output_spec = ImageMathsOutputSpec

    _cmd = 'fslmaths'

    def _gen_filename(self, name):
        if name == 'outfile':
            return self._list_outputs()[name]
        return None
    
    def _parse_inputs(self, skip=None):
        return super(ImageMaths, self)._parse_inputs(skip=['suffix'])

    def _list_outputs(self):
        suffix = '_maths'  # ohinds: build suffix
        if isdefined(self.inputs.suffix):
            suffix = self.inputs.suffix
        outputs = self._outputs().get()
        outputs['outfile'] = self.inputs.outfile
        if not isdefined(outputs['outfile']):
            outputs['outfile'] = self._gen_fname(self.inputs.infile,
                                              suffix=suffix)
        return outputs
