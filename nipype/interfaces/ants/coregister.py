"""The ants module provides basic functions for interfacing with ants functions.

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)

"""

from ..base import (TraitedSpec, File, traits)
from .base import ANTSCommand, ANTSCommandInputSpec
import os


class AntsIntroductionInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='-d %d', usedefault=True,
                             desc='image dimension (2 or 3)', position=1)
    reference_image = File(exists=True,
                           argstr='-r %s', desc='template file to warp to',
                           mandatory=True, copyfile=True)
    input_image = File(exists=True,
                       argstr='-i %s', desc='input image to warp to template',
                       mandatory=True, copyfile=False)
    force_proceed = traits.Bool(argstr='-f 1',
                             desc=('force script to proceed even if headers '
                                   'may be incompatible'))
    inverse_warp_template_labels = traits.Bool(argstr='-l',
                       desc=('Applies inverse warp to the template labels '
                             'to estimate label positions in target space (use '
                             'for template-based segmentation)'))
    max_iterations = traits.List(traits.Int, argstr='-m %s', sep='x',
                             desc=('maximum number of iterations (must be '
                                   'list of integers in the form [J,K,L...]: '
                                   'J = coarsest resolution iterations, K = '
                                   'middle resolution interations, L = fine '
                                   'resolution iterations'))
    bias_field_correction = traits.Bool(argstr='-n 1',
                                desc=('Applies bias field correction to moving '
                                      'image'))
    similarity_metric = traits.Enum('PR', 'CC', 'MI', 'MSQ', argstr='-s %s',
            desc=('Type of similartiy metric used for registration '
                  '(CC = cross correlation, MI = mutual information, '
                  'PR = probability mapping, MSQ = mean square difference)'))
    transformation_model = traits.Enum('GR', 'EL', 'SY', 'S2', 'EX', 'DD', 'RI',
                                       'RA', argstr='-t %s', usedefault=True,
               desc=('Type of transofmration model used for registration '
                     '(EL = elastic transformation model, SY = SyN with time, '
                     'arbitrary number of time points, S2 =  SyN with time '
                     'optimized for 2 time points, GR = greedy SyN, EX = '
                     'exponential, DD = diffeomorphic demons style exponential '
                     'mapping, RI = purely rigid, RA = affine rigid'))
    out_prefix = traits.Str('ants_', argstr='-o %s', usedefault=True,
                             desc=('Prefix that is prepended to all output '
                                   'files (default = ants_)'))
    quality_check = traits.Bool(argstr='-q 1',
                             desc='Perform a quality check of the result')


class AntsIntroductionOutputSpec(TraitedSpec):
    affine_transformation = File(exists=True, desc='affine (prefix_Affine.txt)')
    warp_field = File(exists=True, desc='warp field (prefix_Warp.nii)')
    inverse_warp_field = File(exists=True,
                            desc='inverse warp field (prefix_InverseWarp.nii)')
    input_file = File(exists=True, desc='input image (prefix_repaired.nii)')
    output_file = File(exists=True, desc='output image (prefix_deformed.nii)')


class GenWarpFields(ANTSCommand):
    """Uses ANTS to generate matrices to warp data from one space to another.

    Examples
    --------

    >>> from nipype.interfaces.ants import GenWarpFields
    >>> warp = GenWarpFields()
    >>> warp.inputs.reference_image = 'Template_6.nii'
    >>> warp.inputs.input_image = 'structural.nii'
    >>> warp.inputs.max_iterations = [30,90,20]
    >>> warp.cmdline
    'antsIntroduction.sh -d 3 -i structural.nii -m 30x90x20 -o ants_ -r Template_6.nii -t GR'

    """

    _cmd = 'antsIntroduction.sh'
    input_spec = AntsIntroductionInputSpec
    output_spec = AntsIntroductionOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()

        outputs['affine_transformation'] = os.path.join(os.getcwd(),
                                                        self.inputs.out_prefix +
                                                        'Affine.txt')
        outputs['warp_field'] = os.path.join(os.getcwd(),
                                             self.inputs.out_prefix +
                                             'Warp.nii.gz')
        outputs['inverse_warp_field'] = os.path.join(os.getcwd(),
                                                     self.inputs.out_prefix +
                                                     'InverseWarp.nii.gz')
        outputs['input_file'] = os.path.join(os.getcwd(),
                                             self.inputs.out_prefix +
                                             'repaired.nii.gz')
        outputs['output_file'] = os.path.join(os.getcwd(),
                                              self.inputs.out_prefix +
                                              'deformed.nii.gz')

        return outputs
