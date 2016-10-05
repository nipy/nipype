# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The regutils module provides classes for interfacing with the `niftyreg
<http://niftyreg.sourceforge.net>`_ utility command line tools.
The interfaces were written to work with niftyreg version 1.4
"""

import warnings

from nipype.interfaces.niftyreg.base import (get_custom_path, NiftyRegCommand)
from nipype.utils.filemanip import split_filename
from nipype.interfaces.base import (TraitedSpec, File,  InputMultiPath,
                                    traits, isdefined, CommandLineInputSpec)

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class RegResampleInputSpec(CommandLineInputSpec):
    # Input reference file
    ref_file = File(exists=True, desc='The input reference/target image',
                    argstr='-ref %s', mandatory=True)
    # Input floating file
    flo_file = File(exists=True, desc='The input floating/source image',
                    argstr='-flo %s', mandatory=True)
    # Input deformation field
    trans_file = File(exists=True, desc='The input transformation file',
                      argstr='-trans %s')

    type = traits.Enum('res', 'blank', default='res', argstr='-%s', position=-2,
                       usedefault=True, desc='Type of output')
    # Output file name
    out_file = File(genfile=True, desc='The output filename of the transformed image',
                    argstr='%s', position=-1)
    # Interpolation type
    inter_val = traits.Enum('NN', 'LIN', 'CUB', 'SINC', desc='Interpolation type',
                            argstr='-inter %d')
    # Padding value
    pad_val = traits.Float(desc='Padding value', argstr='-pad %f')
    # Tensor flag
    tensor_flag = traits.Bool(desc='Resample Tensor Map', 
                              argstr='-tensor ')
    # Verbosity off
    verbosity_off_flag = traits.Bool(argstr='-voff', desc='Turn off verbose output')
    # Set the number of omp thread to use
    omp_core_val = traits.Int(desc='Number of openmp thread to use',
                              argstr='-omp %i')


class RegResampleOutputSpec(TraitedSpec):
    out_file = File(desc='The output filename of the transformed image')


class RegResample(NiftyRegCommand):
    _cmd = get_custom_path('reg_resample')
    input_spec = RegResampleInputSpec
    output_spec = RegResampleOutputSpec

    # Need this overload to properly constraint the interpolation type input
    def _format_arg(self, name, spec, value):
        if name == 'inter_val':
            return spec.argstr % {'NN': 0, 'LIN': 1, 'CUB': 3, 'SINC': 5}[value]
        else:
            return super(RegResample, self)._format_arg(name, spec, value)

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._gen_fname(self.inputs.flo_file, suffix='_' + self.inputs.type, ext='.nii.gz')
        return None


class RegJacobianInputSpec(CommandLineInputSpec):
    # Reference file name
    ref_file = File(exists=True, desc='Reference/target file (required if specifying CPP transformations',
                    argstr='-ref %s')
    # Input transformation file
    trans_file = File(exists=True, desc='The input non-rigid transformation',
                      argstr='-trans %s', mandatory=True)
    type = traits.Enum('jac', 'jacL', 'jacM', default='jac', argstr='-%s', position=-2,
                       usedefault=True, desc='Type of jacobian outcome')
    out_file = File(genfile=True, desc='The output jacobian determinant file name',
                    argstr='%s', position=-1)
    # Set the number of omp thread to use
    omp_core_val = traits.Int(desc='Number of openmp thread to use',
                              argstr='-omp %i')


class RegJacobianOutputSpec(TraitedSpec):
    out_file = File(desc='The output file')


class RegJacobian(NiftyRegCommand):
    _cmd = get_custom_path('reg_jacobian')
    input_spec = RegJacobianInputSpec
    output_spec = RegJacobianOutputSpec

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._gen_fname(self.inputs.trans_file, suffix='_' + self.inputs.type, ext='.nii.gz')
        return None


class RegToolsInputSpec(CommandLineInputSpec):
    # Input image file
    in_file = File(exists=True, desc='The input image file path',
                   argstr='-in %s', mandatory=True)
    # Output file path
    out_file = File(genfile=True, desc='The output file name', argstr='-out %s')
    # Make the output image isotropic
    iso_flag = traits.Bool(argstr='-iso', desc='Make output image isotropic')
    # Set scale, slope to 0 and 1.
    noscl_flag = traits.Bool(argstr='-noscl', desc='Set scale, slope to 0 and 1')
    # Values outside the mask are set to NaN
    mask_file = File(exists=True, desc='Values outside the mask are set to NaN',
                     argstr='-nan %s')
    # Threshold the input image
    thr_val = traits.Float(desc='Binarise the input image with the given threshold', 
                           argstr='-thr %f')
    # Binarise the input image
    bin_flag = traits.Bool(argstr='-bin', desc='Binarise the input image')
    # Compute the mean RMS between the two images
    rms_val = File(exists=True, desc='Compute the mean RMS between the images',
                   argstr='-rms %s')
    # Perform division by image or value
    div_val = traits.Either(traits.Float, File(exists=True), 
                            desc='Divide the input by image or value', argstr='-div %s')
    # Perform multiplication by image or value
    mul_val = traits.Either(traits.Float, File(exists=True), 
                            desc='Multiply the input by image or value', argstr='-mul %s')
    # Perform addition by image or value
    add_val = traits.Either(traits.Float, File(exists=True), 
                            desc='Add to the input image or value', argstr='-add %s')
    # Perform subtraction by image or value
    sub_val = traits.Either(traits.Float, File(exists=True), 
                            desc='Add to the input image or value', argstr='-sub %s')
    # Downsample the image by a factor of 2.
    down_flag = traits.Bool(desc='Downsample the image by a factor of 2', argstr='-down')
    # Smoothing using spline kernel
    smo_s_val = traits.Tuple(traits.Float, traits.Float, traits.Float,
                             desc='Smooth the input image using a cubic spline kernel',
                             argstr='-smoS %f %f %f')
    # Change the resolution of the input image
    chg_res_val = traits.Tuple(traits.Float, traits.Float, traits.Float,
                               desc='Change the resolution of the input image',
                               argstr='-chgres %f %f %f')
    # Smoothing using Gaussian kernel
    smo_g_val = traits.Tuple(traits.Float, traits.Float, traits.Float,
                             desc='Smooth the input image using a Gaussian kernel',
                             argstr='-smoG %f %f %f')
    # Set the number of omp thread to use
    omp_core_val = traits.Int(desc='Number of openmp thread to use',
                              argstr='-omp %i')


class RegToolsOutputSpec(TraitedSpec):
    out_file = File(desc='The output file', exists=True)


class RegTools(NiftyRegCommand):
    _cmd = get_custom_path('reg_tools')
    input_spec = RegToolsInputSpec
    output_spec = RegToolsOutputSpec
    _suffix = '_tools'


# reg_average wrapper interface
class RegAverageInputSpec(CommandLineInputSpec):

    avg_files = traits.List(File(exist=True), position=1, argstr='-avg %s', sep=' ',
                            xor=['avg_lts_files', 'avg_ref_file', 'demean1_ref_file', 'demean2_ref_file',
                                 'demean3_ref_file', 'warp_files'],
                            desc='Averaging of images/affine transformations')

    avg_lts_files = traits.List(File(exist=True), position=1, argstr='-avg_lts %s', sep=' ',
                                xor=['avg_files', 'avg_ref_file', 'demean1_ref_file', 'demean2_ref_file',
                                     'demean3_ref_file', 'warp_files'],
                                desc='Robust average of affine transformations')

    avg_ref_file = File(position=1, argstr='-avg_tran %s',
                        xor=['avg_files', 'avg_lts_files', 'demean1_ref_file', 'demean2_ref_file', 'demean3_ref_file'],
                        requires=['warp_files'],
                        desc='All input images are resampled into the space of <reference image> and averaged. ' +
                             'A cubic spline interpolation scheme is used for resampling')
    demean1_ref_file = File(position=1, argstr='-demean1 %s',
                            xor=['avg_files', 'avg_lts_files', 'avg_ref_file', 'demean2_ref_file', 'demean3_ref_file'],
                            requires=['warp_files'],
                            desc='Average images and demean average image that have affine transformations to a ' +
                                 'common space')
    demean2_ref_file = File(position=1, argstr='-demean2 %s',
                            xor=['avg_files', 'avg_lts_files', 'avg_ref_file', 'demean1_ref_file', 'demean3_ref_file'],
                            requires=['warp_files'],
                            desc='Average images and demean average image that have non-rigid transformations to ' +
                                 'a common space')
    demean3_ref_file = File(position=1, argstr='-demean3 %s',
                            xor=['avg_files', 'avg_lts_files', 'avg_ref_file', 'demean1_ref_file', 'demean2_ref_file'],
                            requires=['warp_files'],
                            desc='Average images and demean average image that have linear and non-rigid ' +
                                 'transformations to a common space')
    warp_files = traits.List(File(exist=True), position=-1, argstr='%s', sep=' ',
                             xor=['avg_files', 'avg_lts_files'],
                             desc='transformation files and floating image pairs/triplets to the reference space')

    out_file = File(genfile=True, position=0, desc='Output file name', argstr='%s')


class RegAverageOutputSpec(TraitedSpec):
    out_file = File(desc='Output file name')


class RegAverage(NiftyRegCommand):
    _cmd = get_custom_path('reg_average')
    input_spec = RegAverageInputSpec
    output_spec = RegAverageOutputSpec
    _suffix = 'avg_out'
    
    def _gen_filename(self, name):
        if name == 'out_file':
            if isdefined(self.inputs.avg_lts_files):
                return self._gen_fname(self._suffix, ext='.txt')
            elif isdefined(self.inputs.avg_files):
                _, _, ext = split_filename(self.inputs.avg_files[0])
                if ext not in ['.nii', '.nii.gz', '.hdr', '.img', '.img.gz']:
                    return self._gen_fname(self._suffix, ext=ext)
            return self._gen_fname(self._suffix, ext='.nii.gz')
        return None


class RegTransformInputSpec(CommandLineInputSpec):

    ref1_file = File(exists=True, 
                     desc='The input reference/target image',
                     argstr='-ref %s', 
                     position=0)
    ref2_file = File(exists=True, 
                     desc='The input second reference/target image',
                     argstr='-ref2 %s',
                     position=1,
                     requires=['ref1_file'])

    def_input = File(exists=True, argstr='-def %s', position=-2,
                     desc='Compute deformation field from transformation',
                     xor=['disp_input', 'flow_input', 'comp_input', 'upd_s_form_input', 'inv_aff_input',
                          'inv_nrr_input', 'half_input', 'make_aff_input', 'aff_2_rig_input', 'flirt_2_nr_input'])
    disp_input = File(exists=True, argstr='-disp %s', position=-2,
                      desc='Compute displacement field from transformation',
                      xor=['def_input', 'flow_input', 'comp_input', 'upd_s_form_input', 'inv_aff_input',
                           'inv_nrr_input', 'half_input', 'make_aff_input', 'aff_2_rig_input', 'flirt_2_nr_input'])
    flow_input = File(exists=True, argstr='-flow %s', position=-2,
                      desc='Compute flow field from spline SVF',
                      xor=['def_input', 'disp_input', 'comp_input', 'upd_s_form_input', 'inv_aff_input',
                           'inv_nrr_input', 'half_input', 'make_aff_input', 'aff_2_rig_input', 'flirt_2_nr_input'])

    comp_input = File(exists=True, argstr='-comp %s', position=-3,
                      desc='compose two transformations',
                      xor=['def_input', 'disp_input', 'flow_input', 'upd_s_form_input', 'inv_aff_input',
                           'inv_nrr_input', 'half_input', 'make_aff_input', 'aff_2_rig_input', 'flirt_2_nr_input'],
                      requires=['comp_input2'])
    comp_input2 = File(exists=True, argstr='%s', position=-2,
                       desc='compose two transformations')

    upd_s_form_input = File(exists=True, argstr='-updSform %s', position=-3,
                            desc='Update s-form using the affine transformation',
                            xor=['def_input', 'disp_input', 'flow_input', 'comp_input',
                                 'inv_aff_input', 'inv_nrr_input', 'half_input', 'make_aff_input',
                                 'aff_2_rig_input', 'flirt_2_nr_input'],
                            requires=['upd_s_form_input2'])
    upd_s_form_input2 = File(exists=True, argstr='%s', position=-2,
                             desc='Update s-form using the affine transformation', 
                             requires=['upd_s_form_input'])

    inv_aff_input = File(exists=True, argstr='-invAff %s', position=-2,
                         desc='Invert an affine transformation',
                         xor=['def_input', 'disp_input', 'flow_input', 'comp_input', 'upd_s_form_input',
                              'inv_nrr_input', 'half_input', 'make_aff_input', 'aff_2_rig_input', 'flirt_2_nr_input'])

    inv_nrr_input = traits.Tuple(File(exists=True), File(exists=True),
                                 desc='Invert a non-linear transformation', 
                                 argstr='-invNrr %s %s', position=-2,
                                 xor=['def_input', 'disp_input', 'flow_input', 'comp_input',
                                      'upd_s_form_input', 'inv_aff_input', 'half_input', 'make_aff_input',
                                      'aff_2_rig_input', 'flirt_2_nr_input'])

    half_input = File(exists=True, argstr='-half %s', position=-2,
                      desc='Half way to the input transformation', 
                      xor=['def_input', 'disp_input', 'flow_input', 'comp_input', 'upd_s_form_input',
                           'inv_aff_input', 'inv_nrr_input', 'make_aff_input', 'aff_2_rig_input', 'flirt_2_nr_input'])

    make_aff_input = traits.Tuple(traits.Float, traits.Float, traits.Float, traits.Float,
                                  traits.Float, traits.Float, traits.Float, traits.Float, traits.Float, traits.Float,
                                  traits.Float, traits.Float,
                                  argstr='-makeAff %f %f %f %f %f %f %f %f %f %f %f %f', position=-2,
                                  desc='Make an affine transformation matrix',
                                  xor=['def_input', 'disp_input', 'flow_input', 'comp_input',
                                       'upd_s_form_input', 'inv_aff_input', 'inv_nrr_input',
                                       'half_input', 'aff_2_rig_input', 'flirt_2_nr_input'])

    aff_2_rig_input = File(exists=True, argstr='-aff2rig %s', position=-2,
                           desc='Extract the rigid component from affine transformation',
                           xor=['def_input', 'disp_input', 'flow_input', 'comp_input',
                                'upd_s_form_input', 'inv_aff_input', 'inv_nrr_input', 'half_input',
                                'make_aff_input', 'flirt_2_nr_input'])

    flirt_2_nr_input = traits.Tuple(File(exists=True), File(exists=True), File(exists=True),
                                    argstr='-flirtAff2NR %s %s %s', position=-2,
                                    desc='Convert a FLIRT affine transformation to niftyreg affine transformation',
                                    xor=['def_input', 'disp_input', 'flow_input', 'comp_input',
                                         'upd_s_form_input', 'inv_aff_input', 'inv_nrr_input',
                                         'half_input', 'make_aff_input', 'aff_2_rig_input'])

    out_file = File(genfile=True, position=-1, argstr='%s', desc='transformation file to write')
    # Set the number of omp thread to use
    omp_core_val = traits.Int(desc='Number of openmp thread to use',
                              argstr='-omp %i')


class RegTransformOutputSpec(TraitedSpec):
    out_file = File(desc='Output File (transformation in any format)', exists=True)


class RegTransform(NiftyRegCommand):

    _cmd = get_custom_path('reg_transform')
    input_spec = RegTransformInputSpec
    output_spec = RegTransformOutputSpec
    _suffix = '_trans'

    def _find_input(self):
        inputs = [self.inputs.def_input, self.inputs.disp_input, self.inputs.flow_input, self.inputs.comp_input,
                  self.inputs.comp_input2, self.inputs.upd_s_form_input, self.inputs.inv_aff_input,
                  self.inputs.inv_nrr_input, self.inputs.half_input, self.inputs.make_aff_input,
                  self.inputs.aff_2_rig_input, self.inputs.flirt_2_nr_input]
        entries = []
        for entry in inputs:
            if isdefined(entry):
                entries.append(entry)
                _, _, ext = split_filename(entry)
                if ext == '.nii' or ext == '.nii.gz' or ext == '.hdr':
                    return entry
        if len(entries):
            return entries[0]
        return None

    def _gen_filename(self, name):
        if name == 'out_file':
            if isdefined(self.inputs.make_aff_input):
                return self._gen_fname('matrix', suffix=self._suffix, ext='.txt')
            if isdefined(self.inputs.comp_input) and isdefined(self.inputs.comp_input2):
                _, bn1, ext1 = split_filename(self.inputs.comp_input)
                _, _, ext2 = split_filename(self.inputs.comp_input2)
                if ext1 in ['.nii', '.nii.gz', '.hdr', '.img', '.img.gz'] \
                        or ext2 in ['.nii', '.nii.gz', '.hdr', '.img', '.img.gz']:
                    return self._gen_fname(bn1, suffix=self._suffix, ext='.nii.gz')
                else:
                    return self._gen_fname(bn1, suffix=self._suffix, ext=ext1)
            if isdefined(self.inputs.flirt_2_nr_input):
                return self._gen_fname(self.inputs.flirt_2_nr_input[0], suffix=self._suffix, ext='.txt')
            input_to_use = self._find_input()
            _, _, ext = split_filename(input_to_use)
            if ext not in ['.nii', '.nii.gz', '.hdr', '.img', '.img.gz']:
                return self._gen_fname(input_to_use, suffix=self._suffix, ext=ext)
            else:
                return self._gen_fname(input_to_use, suffix=self._suffix, ext='.nii.gz')
        return None
                
    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_file):
            outputs['out_file'] = self.inputs.out_file
        else:
            outputs['out_file'] = self._gen_filename('out_file')
        return outputs


class RegMeasureInputSpec(CommandLineInputSpec):
    # Input reference file
    ref_file = File(exists=True, desc='The input reference/target image',
                    argstr='-ref %s', mandatory=True)
    # Input floating file
    flo_file = File(exists=True, desc='The input floating/source image',
                    argstr='-flo %s', mandatory=True)
    measure_type = traits.Enum('ncc', 'lncc', 'nmi', 'ssd',
                               mandatory=True, argstr='-%s',
                               desc='Measure of similarity to compute')
    out_file = File(genfile=True, argstr='-out %s',
                    desc='The output text file containing the measure')
    # Set the number of omp thread to use
    omp_core_val = traits.Int(desc='Number of openmp thread to use',
                              argstr='-omp %i')


class RegMeasureOutputSpec(TraitedSpec):
    out_file = File(desc='The output text file containing the measure')


class RegMeasure(NiftyRegCommand):
    _cmd = get_custom_path('reg_measure')
    input_spec = RegMeasureInputSpec
    output_spec = RegMeasureOutputSpec

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._gen_fname(self.inputs.flo_file, suffix='_' + self.inputs.measure_type, ext='.txt')
        return None
