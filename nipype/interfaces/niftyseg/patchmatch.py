# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
The fusion module provides higher-level interfaces to some of the operations
that can be performed with the seg_DetectLesions command-line program.

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


class PatchMatchInputSpec(CommandLineInputSpec):
    """Input Spec for PatchMatch."""
    # Mandatory input arguments
    in_file = File(argstr='-i %s',
                   exists=True,
                   mandatory=True,
                   desc='Input image to segment',
                   position=1)

    mask_file = File(argstr='-m %s',
                     exists=True,
                     mandatory=True,
                     desc='Input mask for the area where applies PatchMatch',
                     position=2)

    database_file = File(argstr='-db %s',
                         genfile=True,
                         mandatory=True,
                         desc='Database with the segmentations',
                         position=3)

    # Output file name
    out_file = File(desc='The output filename of the patchmatch results',
                    argstr='-o %s',
                    position=4,
                    genfile=True)

    # Optional arguments
    patch_size = traits.Int(desc="Patch size, #voxels",
                            argstr='-size %i',
                            mandatory=False)

    desc = "Constrained search area size, number of times bigger than the \
patchsize"
    cs_size = traits.Int(desc=desc,
                         argstr='-cs %i',
                         mandatory=False)

    match_num = traits.Int(desc="Number of better matching",
                           argstr='-match %i',
                           mandatory=False)

    pm_num = traits.Int(desc="Number of patchmatch executions",
                        argstr='-pm %i',
                        mandatory=False)

    desc = "Number of iterations for the patchmatch algorithm"
    it_num = traits.Int(desc=desc,
                        argstr='-it %i',
                        mandatory=False)


class PatchMatchOutputSpec(TraitedSpec):
    """OutputSpec for PatchMatch."""
    out_file = File(desc="Output segmentation")


class PatchMatch(NiftySegCommand):
    """Interface for executable seg_PatchMatch from NiftySeg platform.

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

    For source code, see http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg
    For Documentation, see:
        http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation

    Examples
    --------
    >>> from nipype.interfaces import niftyseg
    >>> node = niftyseg.PatchMatch()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.mask_file = 'im2.nii'
    >>> node.inputs.database_file = 'db.xml'
    >>> node.cmdline  # doctest: +ELLIPSIS +ALLOW_UNICODE
    'seg_PatchMatch -i im1.nii -m im2.nii -db db.xml -o .../im1_pm.nii'

    """
    _cmd = get_custom_path('seg_PatchMatch')
    input_spec = PatchMatchInputSpec
    output_spec = PatchMatchOutputSpec
    _suffix = '_pm'

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
