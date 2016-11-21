# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The fusion module provides higher-level interfaces to some of the operations
that can be performed with the seg_DetectLesions command-line program.
"""
import os
import warnings

from nipype.interfaces.niftyseg.base import NiftySegCommand, get_custom_path
from nipype.interfaces.base import (TraitedSpec, File, traits, isdefined,
                                    CommandLineInputSpec)

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class PatchMatchInputSpec(CommandLineInputSpec):
    """Input Spec for seg_PatchMatch."""
    # Mandatory input arguments
    in_file = File(argstr='-i %s', exists=True, mandatory=True,
                   desc='Input image to segment',
                   position=1)

    mask_file = File(argstr='-m %s', exists=True, mandatory=True,
                     desc='Input mask for the area where applies PatchMatch',
                     position=2)

    database_file = File(argstr='-db %s', genfile=True,  mandatory=True,
                         desc='Database with the segmentations',
                         position=3)

    # Output file name
    out_file = File(desc='The output filename of the patchmatch results',
                    argstr='-o %s', position=4, genfile=True)

    # Optional arguments
    patch_size = traits.Int(desc="Patch size, #voxels",
                            argstr='-size %i', mandatory=False)

    cs_size = traits.Int(desc="Constrained search area size, number of times \
bigger than the patchsize", argstr='-cs %i', mandatory=False)

    match_num = traits.Int(desc="Number of better matching",
                           argstr='-match %i', mandatory=False)

    pm_num = traits.Int(desc="Number of patchmatch executions",
                        argstr='-pm %i', mandatory=False)

    it_num = traits.Int(desc="Number of iterations for the patchmatch \
algorithm", argstr='-it %i', mandatory=False)


class PatchMatchOutputSpec(TraitedSpec):
    """OutputSpec for seg_PatchMatch."""
    out_file = File(desc="Output segmentation")


class PatchMatch(NiftySegCommand):
    """Interface for seg_PatchMatch.

    Usage:	seg_PatchMatch -i <input> -m <input_mask> -db <database>
            -o <output_result> [options].

    * * Considerations * *

    For an extended help, please read the NiftySeg wiki page at:
    http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg
    The database file is a text file and in each line we have a template
    file, a mask with the search region to consider and a file with the
    label to propagate.

    Input image, input mask, template images from database and masks from
    database must have the same 4D resolution (same number of XxYxZ voxels,
    modalities and/or time-points).
    Label files from database must have the same 3D resolution
    (XxYxZ voxels) than input image but can have different number of
    volumes than the input image allowing to propagate multiple labels
    in the same execution.

    DELIMITER can be whitespace, ',', ';' or tab.

    * * Optional parameters * *

    -size		Patch size, #voxels (by default 5).
    -cs			Constrained search area size, number of times bigger than the
                patchsize (by default 4).
    -match		Number of better matching (by default 10).
    -pm			Number of patchmatch executions (by default 10). It should be
                equal or bigger than the number of better matching.
    -it			Number of iterations for the patchmatch algorithm (by default 5).
    -dist		Used distance (by default 0, SSD=0, LNCC=1).
    -debug		Save all intermidium files (by default OFF).
    -odt <datatype> 	Set output <datatype> (char, short, int, uchar, ushort,
                                               uint, float, double).
    -v			Verbose (by default OFF).
    -omp <int>		Number of openmp threads [4]
    --version		Print current source code git hash key and exit
    """
    _cmd = get_custom_path('seg_PatchMatch')
    _suffix = '_pm'
    input_spec = PatchMatchInputSpec
    output_spec = PatchMatchOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                                                  suffix=self._suffix)
        outputs['out_file'] = os.path.abspath(outputs['out_file'])
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        return None
