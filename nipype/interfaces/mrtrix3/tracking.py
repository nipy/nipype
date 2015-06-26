# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# -*- coding: utf-8 -*-

"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname(os.path.realpath(__file__ ))
    >>> datadir = os.path.realpath(os.path.join(filepath,
    ...                            '../../testing/data'))
    >>> os.chdir(datadir)

"""
import os
import os.path as op

from nipype.interfaces.base import (
    CommandLineInputSpec, CommandLine, traits, TraitedSpec, File)

from nipype.utils.filemanip import split_filename
from nipype.interfaces.traits_extension import isdefined


class TractographyInputSpec(CommandLineInputSpec):
    sph_trait = traits.Tuple(traits.Float, traits.Float, traits.Float,
                             traits.Float, argstr='%f,%f,%f,%f')

    in_file = File(exists=True, argstr='%s', mandatory=True, position=-2,
                   desc='input file to be processed')

    out_file = File('tracked.tck', argstr='%s', mandatory=True, position=-1,
                    usedefault=True, desc='output file containing tracks')

    algorithm = traits.Enum(
        'iFOD2', 'FACT', 'iFOD1', 'Nulldist', 'SD_Stream', 'Tensor_Det',
        'Tensor_Prob', usedefault=True, argstr='-algorithm %s',
        desc='tractography algorithm to be used')

    # ROIs processing options
    roi_incl = traits.Either(
        File(exists=True), sph_trait, argstr='-include %s',
        desc=('specify an inclusion region of interest, streamlines must'
              ' traverse ALL inclusion regions to be accepted'))
    roi_excl = traits.Either(
        File(exists=True), sph_trait, argstr='-exclude %s',
        desc=('specify an exclusion region of interest, streamlines that'
              ' enter ANY exclude region will be discarded'))
    roi_mask = traits.Either(
        File(exists=True), sph_trait, argstr='-mask %s',
        desc=('specify a masking region of interest. If defined,'
              'streamlines exiting the mask will be truncated'))

    # Here streamlines tractography

    # Anatomically-Constrained Tractography options
    act_file = File(
        exists=True, argstr='-act %s',
        desc=('use the Anatomically-Constrained Tractography framework during'
              ' tracking; provided image must be in the 5TT '
              '(five - tissue - type) format'))
    backtrack = traits.Bool(argstr='-backtrack',
                            desc='allow tracks to be truncated')

    crop_at_gmwmi = traits.Bool(
        argstr='-crop_at_gmwmi',
        desc=('crop streamline endpoints more '
              'precisely as they cross the GM-WM interface'))

    # Tractography seeding options
    seed_sphere = traits.Tuple(
        traits.Float, traits.Float, traits.Float, traits.Float,
        argstr='-seed_sphere %f,%f,%f,%f', desc='spherical seed')
    seed_image = File(exists=True, argstr='-seed_image %s',
                      desc='seed streamlines entirely at random within mask')
    seed_rnd_voxel = traits.Enum(
        traits.Int(), File(exists=True),
        argstr='-seed_random_per_voxel %s %d',
        xor=['seed_image', 'seed_grid_voxel'],
        desc=('seed a fixed number of streamlines per voxel in a mask '
              'image; random placement of seeds in each voxel'))
    seed_grid_voxel = traits.Enum(
        traits.Int(), File(exists=True),
        argstr='-seed_grid_per_voxel %s %d',
        xor=['seed_image', 'seed_rnd_voxel'],
        desc=('seed a fixed number of streamlines per voxel in a mask '
              'image; place seeds on a 3D mesh grid (grid_size argument '
              'is per axis; so a grid_size of 3 results in 27 seeds per'
              ' voxel)'))

    # missing opts: seed_rejection, seed_gmwmi, seed_dynamic, max_seed_attempts
    out_seeds = File(
        'out_seeds.nii.gz', argstr='-output_seeds %s',
        desc=('output the seed location of all successful streamlines to'
              ' a file'))

    # DW gradient table import options
    grad_file = File(exists=True, argstr='-grad %s',
                     desc='dw gradient scheme (MRTrix format')
    grad_fsl = traits.Tuple(
        File(exists=True), File(exists=True), argstr='-fslgrad %s %s',
        desc='(bvecs, bvals) dw gradient scheme (FSL format')
    bval_scale = traits.Enum(
        'yes', 'no', argstr='-bvalue_scaling %s',
        desc=('specifies whether the b - values should be scaled by the square'
              ' of the corresponding DW gradient norm, as often required for '
              'multishell or DSI DW acquisition schemes. The default action '
              'can also be set in the MRtrix config file, under the '
              'BValueScaling entry. Valid choices are yes / no, true / '
              'false, 0 / 1 (default: true).'))


class TractographyOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='the output filtered tracks')
    out_seeds = File(desc=('output the seed location of all successful'
                           ' streamlines to a file'))


class Tractography(CommandLine):

    """
    Performs tractography after selecting the appropriate algorithm

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> tk = mrt.Tractography()
    >>> tk.inputs.in_file = 'fods.mif'
    >>> tk.inputs.roi_mask = 'mask.nii.gz'
    >>> tk.inputs.seed_sphere = (80, 100, 70, 10)
    >>> tk.cmdline                               # doctest: +ELLIPSIS
    'tckgen -algorithm iFOD2 -include mask.nii.gz \
-seed_sphere 80.000000,100.000000,70.000000,10.000000 \
./fods.nii.gz tracked.tck'
    >>> tk.run()                                 # doctest: +SKIP
    """

    _cmd = 'tckgen'
    input_spec = TractographyInputSpec
    output_spec = TractographyOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if 'roi_' in name and isinstance(value, tuple):
            value = ['%f' % v for v in value]
            return trait_spec.argstr % ','.join(value)

        return super(Tractography, self)._format_arg(name, trait_spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs
