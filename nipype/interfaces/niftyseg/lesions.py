# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
Nipype interface for seg_FillLesions.

The fusion module provides higher-level interfaces to some of the operations
that can be performed with the seg_FillLesions command-line program.

Examples
--------
See the docstrings of the individual classes for examples.

Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""

import os
import warnings

from ..base import TraitedSpec, File, traits, isdefined, CommandLineInputSpec
from .base import NiftySegCommand, get_custom_path


warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class FillLesionsInputSpec(CommandLineInputSpec):
    """Input Spec for FillLesions."""
    # Mandatory input arguments
    in_file = File(argstr='-i %s', exists=True, mandatory=True,
                   desc='Input image to fill lesions', position=1)

    lesion_mask = File(argstr='-l %s', exists=True, mandatory=True,
                       desc='Lesion mask', position=2)

    # Output file name
    out_file = File(desc='The output filename of the fill lesions results',
                    argstr='-o %s', position=3)

    # Optional arguments
    desc = "Dilate the mask <int> times (in voxels, by default 0)"
    in_dilation = traits.Int(desc=desc, argstr='-dil %d', mandatory=False)

    desc = 'Percentage of minimum number of voxels between patches <float> \
(by default 0.5).'
    match = traits.Float(desc=desc, argstr='-match %f', mandatory=False)

    desc = 'Minimum percentage of valid voxels in target patch <float> \
(by default 0).'
    search = traits.Float(desc=desc, argstr='-search %f', mandatory=False)

    desc = 'Smoothing by <float> (in minimal 6-neighbourhood voxels \
(by default 0.1)).'
    smooth = traits.Float(desc=desc, argstr='-smo %f', mandatory=False)

    desc = 'Search regions size respect biggest patch size (by default 4).'
    size = traits.Int(desc=desc, argstr='-size %d', mandatory=False)

    desc = 'Patch cardinality weighting factor (by default 2).'
    cwf = traits.Float(desc=desc, argstr='-cwf %f', mandatory=False)

    desc = 'Give a binary mask with the valid search areas.'
    bin_mask = File(desc=desc, argstr='-mask %s', mandatory=False)

    desc = "Guizard et al. (FIN 2015) method, it doesn't include the \
multiresolution/hierarchical inpainting part, this part needs to be done \
with some external software such as reg_tools and reg_resample from NiftyReg. \
By default it uses the method presented in Prados et al. (Neuroimage 2016)."
    other = traits.Bool(desc=desc, argstr='-other', mandatory=False)

    debug = traits.Bool(desc='Save all intermidium files (by default OFF).',
                        argstr='-debug', mandatory=False)

    desc = 'Set output <datatype> (char, short, int, uchar, ushort, uint, \
float, double).'
    out_datatype = traits.String(desc=desc, argstr='-odt %s', mandatory=False)

    verbose = traits.Bool(desc='Verbose (by default OFF).',
                          argstr='-v', mandatory=False)

    # Set the number of omp thread to use
    omp_core = traits.Int(desc='Number of openmp thread to use. Default: 4',
                          argstr='-omp %d')


class FillLesionsOutputSpec(TraitedSpec):
    """Output Spec for FillLesions."""
    out_file = File(desc="Output segmentation")


class FillLesions(NiftySegCommand):
    """Interface for executable seg_FillLesions from NiftySeg platform.

    Fill all the masked lesions with WM intensity average.

    For source code, see http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg
    For Documentation, see:
        http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation

    Examples
    --------
    >>> from nipype.interfaces import niftyseg
    >>> node = niftyseg.FillLesions()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.lesion_mask = 'im2.nii'
    >>> node.cmdline  # doctest: +ELLIPSIS +ALLOW_UNICODE
    'seg_FillLesions -i im1.nii -l im2.nii -o .../im1_lesions_filled.nii'

    """
    _cmd = get_custom_path('seg_FillLesions')
    input_spec = FillLesionsInputSpec
    output_spec = FillLesionsOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_filename('out_file')
        outputs['out_file'] = os.path.abspath(outputs['out_file'])
        return outputs

    def _parse_inputs(self, skip=None):
        """Set non-mandatory inputs if not given by user."""
        skip = []
        if not isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_filename('out_file')
        return super(FillLesions, self)._parse_inputs(skip=skip)

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._gen_fname(self.inputs.in_file,
                                   suffix='_lesions_filled')
        return None
