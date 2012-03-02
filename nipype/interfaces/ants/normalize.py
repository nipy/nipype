# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The ants module provides basic functions for interfacing with ants functions.

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)

"""

__docformat__ = 'restructuredtext'

# Standard library imports
import logging
import os
from glob import glob

# Third-party imports
import numpy as np
import scipy.io as sio

# Local imports
from nipype.interfaces.base import (TraitedSpec, File, traits,
                                    Directory, InputMultiPath,
                                    OutputMultiPath, CommandLine,
                                    CommandLineInputSpec, isdefined)
from nipype.utils.filemanip import (filename_to_list,copyfiles, list_to_filename,
                                    split_filename, fname_presuffix)

class BuildTemplateInputSpec(CommandLineInputSpec):
    dimension = traits.Enum(3, 2, argstr='-d %d',usedefault=True,
                             desc='image dimension (2 or 3)', position=1)
    out_prefix = traits.Str('antsTMPL_',argstr='-o %s',usedefault=True,
                             desc='Prefix that is prepended to all output files '
                             '(default = antsTMPL_)')
    in_files = traits.List(File(exists=True), mandatory=True,
                             desc='list of images to generate template from',argstr='%s',position=-1)
    parallelization = traits.Enum(0,1,2,argstr='-c %d',usedefault=True,
                             desc='control for parallel processing (0 = serial, '
                             '1 = use PBS, 2 = use PEXEC, 3 = use Apple XGrid')
    gradient_step_size = traits.Float(argstr='-g %f',desc='smaller magnitude '
                             'results in more cautious steps (default = .25)')
    iteration_limit = traits.Int(argstr='-i %d',desc='iterations of template '
                             'construction (default 4)')
    num_cores = traits.Int(argstr='-j %d',requires=['parallelization'],desc='Requires parallelization = 2 (PEXEC). '
                             'Sets number of cpu cores to use (default 2)')
    max_iterations = traits.List(traits.Int,argstr='-m %s',sep='x',
                             desc='maximum number of iterations (must be list of integers '
                             'in the form [J,K,L...]: J = coarsest resolution iterations, '
                             'K = middle resolution interations, L = fine resolution '
                             'iterations')
    bias_field_correction = traits.Bool(argstr = '-n 1',
                             desc='Applies bias field correction to moving image')
    rigid_body_registration = traits.Bool(argstr='-r 1',
                             desc='registers inputs before creating template (useful'
                             'if no initial template available)')
    similarity_metric = traits.Enum('PR','CC','MI','MSQ',argstr='-s %s',
                             desc='Type of similartiy metric used for registration '
                             '(CC = cross correlation, MI = mutual information, '
                             'PR = probability mapping, MSQ = mean square difference)')
    transformation_model = traits.Enum('GR','EL','SY','S2','EX','DD',argstr='-t %s',usedefault=True,
                             desc='Type of transofmration model used for registration '
                             '(EL = elastic transformation model, SY = SyN with time, '
                             'arbitrary number of time points, S2 =  SyN with time '
                             'optimized for 2 time points, GR = greedy SyN, EX = '
                             'exponential, DD = diffeomorphic demons style exponential '
                             'mapping')
    use_first_as_target = traits.Bool(desc='uses first volume as target of all inputs. '
                             'When not used, an unbiased average image is used to start.')

class BuildTemplateOutputSpec(TraitedSpec):
    final_template_file = File(exists=True, desc='final ANTS template')
    template_files = traits.Either(traits.List(File(exists=True)),
                             File(exists=True), desc='Templates from different stages of iteration')
    subject_outfiles = output_images = traits.Either(traits.List(File(exists=True)),
                             File(exists=True), desc='Outputs for each input image. '
                             'Includes warp field, inverse warp, Affine, original image (repaired) '
                             'and warped image (deformed)')


class BuildTemplate(CommandLine):
    """Uses the ANTS command buildtemplateparallel.sh to generate a template from the files listed in in_files.
    Note: This can take a VERY long time to complete
    Examples
    --------

    >>> from nipype.interfaces.ants import BuildTemplate
    >>> tmpl = BuildTemplate()
    >>> tmpl.inputs.in_files = ['foo.nii','bar.nii']
    >>> tmpl.inputs.max_iterations = [30,90,20]
    >>> tpml.cmdline
    'buildtemplateparallel.sh -d 3 -m 30x90x20 -o antsTMPL_ -c 0 -t GR foo.nii bar.nii'

    """

    _cmd = 'buildtemplateparallel.sh'
    input_spec = BuildTemplateInputSpec
    output_spec = BuildTemplateOutputSpec



    def _format_arg(self, opt, spec, val):
        if opt == 'num_cores':
            if self.inputs.parallelization == 2:
                return '-j '+val
            else: 
                return ''
        if opt == 'in_files':
            if self.inputs.use_first_as_target:
                start='-z '
            else:
                start=''
            return start+' '.join([os.path.split(name)[1] for name in val])
        return super(BuildTemplate,self)._format_arg(opt,spec,val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['template_files'] = []
        for i in range(len(glob(os.path.realpath('*iteration*')))):
            temp = os.path.realpath('%s_iteration_%d/%stemplate.nii.gz'%(self.inputs.transformation_model,i,self.inputs.out_prefix))
            os.rename(temp,os.path.realpath('%s_iteration_%d/%stemplate_i%d.nii.gz'%(self.inputs.transformation_model,i,self.inputs.out_prefix,i)))
            outputs['template_files'].append(os.path.realpath('%s_iteration_%d/%stemplate_i%d.nii.gz'%(self.inputs.transformation_model,i,self.inputs.out_prefix,i)))
        outputs['final_template_file'] = os.path.realpath('%stemplate.nii.gz'%self.inputs.out_prefix)
        outputs['subject_outfiles'] = []
        for filename in self.inputs.in_files:
            pth, base, ext = split_filename(filename)
            temp = glob(os.path.realpath('%s%s*'%(self.inputs.out_prefix,base)))
            for file_ in temp:
                outputs['subject_outfiles'].append(file_)
        return outputs
 



class WarpImageMultiTransformInputSpec(CommandLineInputSpec):
    dimension = traits.Enum(3, 2, argstr='%d',usedefault=True,
                             desc='image dimension (2 or 3)',position=1)
    moving_image = File(argstr='%s',desc='image to apply transformation '
                             'to (generally a coregistered functional)',
                              mandatory=True, copyfile=True)
    out_postfix = traits.Str('_wimt',argstr='%s',
                             desc='Postfix that is prepended to all output files '
                             '(default = _wimt)',usedefault=True)
    reference_image = File(argstr='-R %s',desc='reference image space that you '
                             'wish to warp INTO',xor=['tightest_box'])
    tightest_box = traits.Bool(argstr='--tightest-bounding-box',
                             desc='computes tightest bounding box (overrided by '
                             'reference_image if given)',xor=['reference_image'])
    reslice_by_header = traits.Bool(argstr='--reslice-by-header',
                             desc='Uses orientation matrix and origin encoded in '
                             'reference image file header. Not typically used with '
                             'additional transforms')
    use_nearest = traits.Bool(argstr='--use-NN',desc='Use nearest neighbor interpolation')
    use_bspline = traits.Bool(argstr='--use-Bspline',desc='Use 3rd order'
                             'B-Spline interpolation')
    transformation_series = InputMultiPath(File(exists=True),argstr='%s',
                             desc='transformation file(s) to be applied',
                             mandatory=True, copyfile=False)
    invert_affine = traits.List(traits.Int, desc='List of Affine transformations to invert. '
                             'E.g.: [1,4,5] inverts the 1st, 4th, and 5th Affines '
                             'found in transformation_series')





class WarpImageMultiTransformOutputSpec(TraitedSpec):
    output_images = traits.Either(traits.List(File(exists=True)),
                             File(exists=True))

class WarpImageMultiTransform(CommandLine):
    """Uses the ANTS command WarpImageMultiTransform to warp an image (moving image) from one space to another (fixed/template space)

    Examples
    --------

    >>> from nipype.interfaces.ants import WarpImageMultiTransform
    >>> wimt = WarpImageMultiTransform()
    >>> wimt.inputs.moving_image = 'foo.nii'
    >>> wimt.inputs.reference_image = 'ants_deformed.nii.gz'
    >>> wimt.inputs.transformation_series = ['ants_Warp.nii.gz','ants_Affine.txt']
    >>> wimt.cmdline
    'WarpImageMultiTransform 3 foo.nii foo_wimt.nii -R ants_deformed.nii.gz ants_Warp.nii.gz ants_Affine.txt'

    """

    _cmd = 'WarpImageMultiTransform'
    input_spec = WarpImageMultiTransformInputSpec
    output_spec = WarpImageMultiTransformOutputSpec

    def _format_arg(self, opt, spec, val):
        if opt == 'out_postfix':
            return os.path.split(self.inputs.moving_image)[-1].partition('.')[0]+val+'.'+os.path.split(self.inputs.moving_image)[-1].partition('.')[2]
        if opt == 'transformation_series':
            series = ''
            affine_counter = 0
            for transformation in val:
                if transformation.find('Affine')!=-1 and isdefined(self.inputs.invert_affine):
                     affine_counter = affine_counter + 1
                     if self.inputs.invert_affine.__contains__(affine_counter):
                         series=series+'-i '+transformation+' '
                     else:
                         series=series+transformation+' '
                else:
                     series=series+transformation+' '
                
            return series
        return super(WarpImageMultiTransform,self)._format_arg(opt,spec,val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_images'] = glob(os.path.join(os.getcwd(),os.path.split(self.inputs.moving_image)[-1].partition('.')[0]+self.inputs.out_postfix+'*'))[0]
        print outputs['output_images']
        return outputs    


class AntsIntroductionInputSpec(CommandLineInputSpec):
    dimension = traits.Enum(3, 2, argstr='-d %d',usedefault=True,
                             desc='image dimension (2 or 3)', position=1)
    reference_image = File(argstr='-r %s',desc='template file to warp to',
                             mandatory=True, copyfile=True)
    input_image = File(argstr='-i %s',desc='input image to warp to template',
                             mandatory=True, copyfile=False)
    force_proceed = traits.Bool(argstr='-f 1',
                             desc='force script to proceed even if headers may '
                             'be incompatible')
    inverse_warp_template_labels = traits.Bool(argstr='-l', 
                             desc='Applies inverse warp to the template labels '
                             'to estimate label positions in target space (use '
                             'for template-based segmentation)')
    max_iterations = traits.List(traits.Int,argstr='-m %s',sep='x',
                             desc='maximum number of iterations (must be list of integers '
                             'in the form [J,K,L...]: J = coarsest resolution iterations, '
                             'K = middle resolution interations, L = fine resolution '
                             'iterations')
    bias_field_correction = traits.Bool(argstr='-n 1', 
                             desc='Applies bias field correction to moving image')
    out_prefix = traits.Str('ants_',argstr='-o %s', usedefault=True,
                             desc='Prefix that is prepended to all output files '
                             '(default = ants_)')
    quality_check = traits.Bool(argstr='-q 1', 
                             desc='Perform a quality check of the result')
    similarity_metric = traits.Enum('PR','CC','MI','MSQ',argstr='-s %s',
                             desc='Type of similartiy metric used for registration '
                             '(CC = cross correlation, MI = mutual information, '
                             'PR = probability mapping, MSQ = mean square difference)')
    transformation_model = traits.Enum('GR','EL','SY','S2','EX','DD','RI','RA',argstr='-t %s',
                             desc='Type of transofmration model used for registration '
                             '(EL = elastic transformation model, SY = SyN with time, '
                             'arbitrary number of time points, S2 =  SyN with time '
                             'optimized for 2 time points, GR = greedy SyN, EX = '
                             'exponential, DD = diffeomorphic demons style exponential '
                             'mapping, RI = purely rigid, RA = affine rigid')

class AntsIntroductionOutputSpec(TraitedSpec):
    affine_transformation = File(exists=True, desc='affine (prefix_Affine.txt)')
    warp_field = File(exists=True, desc='warp field (prefix_Warp.nii)')
    inverse_warp_field = File(exists=True, desc='inverse warp field (prefix_InverseWarp.nii)')
    input_file = File(exists=True, desc='input image (prefix_repaired.nii)')
    output_file = File(exists=True, desc='output image (prefix_deformed.nii)')

class GenWarpFields(CommandLine):
    """Uses the ANTS command antsIntroduction to generate warp and inverse warp fields that transform structural data
    from anatomical images of a subject to the input template space.

    Examples
    --------

    >>> from nipype.interfaces.ants import GenWarpFields
    >>> warp = GenWarpFields()
    >>> warp.inputs.reference_image = 'template.nii'
    >>> warp.inputs.input_image = 'brain.nii'
    >>> warp.inputs.max_iterations = [30,90,20]
    >>> warp.cmdline
    'antsIntroduction -d 3 -i brain.nii -m 30x90x20 -o ants_ -r template.nii'

    """

    _cmd = 'antsIntroduction.sh'
    input_spec = AntsIntroductionInputSpec
    output_spec = AntsIntroductionOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()

        outputs['affine_transformation'] = os.path.join(os.getcwd(),self.inputs.out_prefix+'Affine.txt')
        outputs['warp_field'] = os.path.join(os.getcwd(),self.inputs.out_prefix+'Warp.nii.gz')
        outputs['inverse_warp_field'] = os.path.join(os.getcwd(),self.inputs.out_prefix+'InverseWarp.nii.gz')
        outputs['input_file'] = os.path.join(os.getcwd(),self.inputs.out_prefix+'repaired.nii.gz')
        outputs['output_file'] = os.path.join(os.getcwd(),self.inputs.out_prefix+'deformed.nii.gz')

        return outputs    


