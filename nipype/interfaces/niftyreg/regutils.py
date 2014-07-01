# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The regutils module provides classes for interfacing with the `niftyreg
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ utility command line tools. The 
interfaces were written to work with niftyreg version 1.4
"""

import os
import os.path as op
import warnings

from nipype.interfaces.niftyreg.base import NIFTYREGCommand, NIFTYREGCommandInputSpec

from nipype.interfaces.base import (TraitedSpec, File, 
                                    InputMultiPath,
                                    OutputMultiPath, Undefined, traits,
                                    isdefined, OutputMultiPath)

from nipype.utils.filemanip import split_filename, fname_presuffix

from nipype.interfaces.niftyreg.base import Info

from nibabel import load

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

# A custom trait class for positive integers
class PositiveInt (traits.BaseInt):

    # Define the default value
    default_value = 0
    # Describe the trait type
    info_text = 'A positive integer'

    def validate ( self, object, name, value ):
        value = super(PositiveInt, self).validate(object, name, value)
        if (value >= 0) == 1:
            return value
            self.error( object, name, value )

#-----------------------------------------------------------
# reg_resample wrapper interface
#-----------------------------------------------------------

# Input spec
class RegResampleInputSpec(NIFTYREGCommandInputSpec):
    # Input reference file
    ref_file = File(exists=True, desc='The input reference/target image',
                    argstr='-ref %s', mandatory=True)
    # Input floating file
    flo_file = File(exists=True, desc='The input floating/source image',
                    argstr='-flo %s', mandatory=True)
    # Input affine transformation
    aff_file = File(exists=True, desc='The input affine transformation',
                    argstr='-aff %s', mandatory=False)
    # Input deformation field
    trans_file = File(exists=True, desc='The input CPP transformation file',
                      argstr='-trans %s', mandatory=False)
    # Output file name
    res_file = File(desc='The output filename of the transformed image',
                    argstr='-res %s', name_source = ['flo_file'], name_template = '%s_res')
    # Deformaed grid file name
    blank_file = File(desc='The output filename of resampled blank grid',
                      argstr='-blank %s')
    # Interpolation type
    inter_val = traits.Enum('NN', 'LIN', 'CUB', desc = 'Interpolation type',
                            argstr='-inter %d')
    # Padding value
    pad_val = traits.Int(desc = 'Padding value', argstr='-pad %d')
    # Verbosity off?
    verbosity_off_flag = traits.Bool(argstr='-voff', desc='Turn off verbose output')

# Output spec
class RegResampleOutputSpec(TraitedSpec):
    res_file = File(desc='The output filename of the transformed image')
    blank_file = File(desc='The output filename of resampled blank grid (if generated)')

# Resampler class
class RegResample(NIFTYREGCommand):
    _cmd = 'reg_resample'
    input_spec = RegResampleInputSpec
    output_spec = RegResampleOutputSpec

    # Need this overload to properly constraint the interpolation type input
    def _format_arg(self, name, spec, value):
        if name == 'inter_val':
            return spec.argstr%{'NN':0, 'LIN':1, 'CUB':2}[value]
        else:
            return super(RegResample, self)._format_arg(name, spec, value)        

    
#-----------------------------------------------------------
# reg_jacobian wrapper interface
#-----------------------------------------------------------
# Input spec
class RegJacobianInputSpec(NIFTYREGCommandInputSpec):
    # Reference file name
    ref_file = File(exists=True, desc='Reference/target file (required if specifying CPP transformations',
                    argstr='-ref %s')
    # Input transformation file
    trans_file = File(exists=True, desc='The input non-rigid transformation',
                      argstr='-trans %s', mandatory=True)
    # Input jacobian determinat file path
    jac_det_file = File(desc='The output jacobian determinant file name',
                        argstr='-jac %s',  name_source=['trans_file'], name_template='%s_jac_det')
    # Input jacobian matrix file name
    jac_mat_file = File(desc='The output jacobian matrix file name',
                        argstr='-jacM %s',name_source=['trans_file'], name_template='%s_jac_mat')
    # Input log of jacobian determinant file name
    jac_log_file = File(desc='The output log of jacobian determinant file name',
                        argstr='-jacL %s', name_source=['trans_file'], name_template='%s_jac_log_det')

# Output spec
class RegJacobianOutputSpec(TraitedSpec):
    jac_det_file = File(desc='The output jacobian determinant file')
    jac_mat_file = File(desc='The output filename of jacobian matrix')
    jac_log_file = File(desc='The output filename of the log of jacobian determinant')
    
# Main interface class
class RegJacobian(NIFTYREGCommand):
    _cmd = 'reg_jacobian'
    input_spec = RegJacobianInputSpec
    output_spec = RegJacobianOutputSpec
    _suffix = '_jacobian_'
    
#-----------------------------------------------------------
# reg_tools wrapper interface
#-----------------------------------------------------------
# Input spec
class RegToolsInputSpec(NIFTYREGCommandInputSpec):
    # Input image file
    in_file = File(exists=True, desc='The input image file path',
                   argstr='-in %s', mandatory=True)
    # Output file path
    out_file = File(desc='The output file name', argstr='-out %s', name_source = ['in_file'], name_template = '%s_out')
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
                             desc = 'Smooth the input image using a cubic spline kernel',
                             argstr='-smoS %f %f %f')
    # Smoothing using Gaussian kernel
    smo_g_val = traits.Tuple(traits.Float, traits.Float, traits.Float,
                             desc = 'Smooth the input image using a Gaussian kernel',
                             argstr='-smoG %f %f %f')

# Output spec    
class RegToolsOutputSpec(TraitedSpec):
    out_file = File(desc='The output file', exists = True)

# Main interface class
class RegTools(NIFTYREGCommand):
    _cmd = 'reg_tools'
    input_spec = RegToolsInputSpec
    output_spec = RegToolsOutputSpec

#-----------------------------------------------------------
# reg_measure wrapper interface
#-----------------------------------------------------------
class RegMeasureInputSpec(NIFTYREGCommandInputSpec):
    ref_file = File(exists=True, desc='The input reference/target image',
                    argstr='-ref %s', mandatory=True)
    flo_file = File(exists=True, desc='The input floating/source image',
                    argstr='-flo %s', mandatory=True)
    ncc_flag = traits.Bool(argstr='-ncc', desc='Compute NCC')
    lncc_flag = traits.Bool(argstr='-lncc', desc='Compute LNCC')
    nmi_flag = traits.Bool(argstr='-nmi', desc='Compute NMI')
    ssd_flag = traits.Bool(argstr='-ssd', desc='Compute SSD')

class RegMeasureOutputSpec(TraitedSpec):
    pass

class RegMeasure(NIFTYREGCommand):
    _cmd = 'reg_measure'
    input_spec = RegMeasureInputSpec
    output_spec = RegMeasureOutputSpec 

#-----------------------------------------------------------
# reg_average wrapper interface
#-----------------------------------------------------------
class RegAverageInputSpec(NIFTYREGCommandInputSpec):

    out_file = File(position=0, desc='Output file name', argstr='%s', genfile=True)

    # If only images/transformation files are passed, do a straight average
    # of all the files in the string (shoudl this be a list of files?)
    in_files = InputMultiPath(position = 1, argstr='-avg %s', sep=' ',
                              desc='Averaging of images/affine transformations', xor=['reg_average_type'])

    # To tidy up the interface to reg_average, have an xor over the
    # different demeaning types with the reference file adjacent
    avg_tran_ref_file = File(position = 1, argstr=' -avg_tran %s', xor=['demean_type'], 
                             desc='All input images are resampled into the space of <reference image> and averaged. A cubic spline interpolation scheme is used for resampling')
    demean1_ref_file = File(position = 1, argstr=' -demean1 %s ', xor=['demean_type'], desc='Average images and demean average image that have affine transformations to a common space')
    demean2_ref_file = File(position = 1, argstr=' -demean2 %s ', xor=['demean_type'], desc='Average images and demean average image that have non-rigid transformations to a common space' )
    demean3_ref_file = File(position = 1, argstr=' -demean3 %s ', xor=['demean_type'], desc='Average images and demean average image that have linear and non-rigid transformations to a common space')
    # If we do not have a list of files beginning with avg, must be a demean
    demean_files = traits.List(traits.Str, position =-1, argstr=' %s ', sep=' ',
                               desc='transformation files and floating image pairs/triplets to the reference space', xor=['reg_average_type'])


class RegAverageOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='Output file name')

class RegAverage(NIFTYREGCommand):
    """ Use RegAverage to average a set of transformations, images or both.
    
    Examples
    --------
    
    >>> from nipype.interfaces import niftyreg
    >>> reg_average = niftyreg.RegAverage()
    >>> 

    """
    _cmd = 'reg_average'
    input_spec = RegAverageInputSpec
    output_spec = RegAverageOutputSpec
    
    def _gen_filename(self, name):
        if name == 'out_file':
            return self._gen_fname('average_output' , ext='.nii.gz')
        return None
            
    def _list_outputs(self):
        outputs = self.output_spec().get()
        
        if isdefined(self.inputs.out_file):
            outputs['out_file'] = self.inputs.out_file
        else:
            outputs['out_file'] = self._gen_filename('out_file')
            
        return outputs

#-----------------------------------------------------------
# reg_aladin wrapper interface
#-----------------------------------------------------------
# Input spec
class RegAladinInputSpec(NIFTYREGCommandInputSpec):
    # Input reference file
    ref_file = File(exists=True, desc='The input reference/target image',
                    argstr='-ref %s', mandatory=True)
    # Input floating file
    flo_file = File(exists=True, desc='The input floating/source image',
                    argstr='-flo %s', mandatory=True)
    # Affine output matrix file
    aff_file = File(genfile = True, desc='The output affine matrix file', argstr='-aff %s')
    # No symmetric flag
    nosym_flag = traits.Bool(argstr='-noSym', desc='Turn off symmetric registration')
    # Rigid only registration
    rig_only_flag = traits.Bool(argstr='-rigOnly', desc='Do only a rigid registration')
    # Directly optimise affine flag
    aff_direct_flag = traits.Bool(argstr='-affDirect', desc='Directly optimise the affine parameters')
    # Input affine
    in_aff_file = File(exists=True, desc='The input affine transformation',
                       argstr='-inaff %s')
    # Input reference mask
    rmask_file = File(exists=True, desc='The input reference mask',
                      argstr='-rmask %s')
    # Input floating mask
    fmask_file = File(exists=True, desc='The input floating mask',
                      argstr='-fmask %s')
    # Result image path
    res_file = File(desc='The affine transformed floating image',
                    argstr='-res %s', name_source = ['flo_file'], name_template = '%s_res')
    # Maximum number of iterations
    maxit_val = PositiveInt(desc='Maximum number of iterations', argstr='-maxit %d')
    # Multiresolution levels
    ln_val = PositiveInt(desc='Number of resolution levels to create', argstr='-ln %d')
    # Number of resolution levels to process
    lp_val = PositiveInt(desc='Number of resolution levels to perform', argstr='-lp %d')
    # Smoothing to apply on reference image
    smoo_r_val = traits.Float(desc='Amount of smoothing to apply to reference image',
                              argstr='-smooR %f')
    # Smoothing to apply on floating image
    smoo_f_val = traits.Float(desc='Amount of smoothing to apply to floating image',
                              argstr='-smooF %f')
    # Use nifti header to initialise transformation
    nac_flag = traits.Bool(desc='Use nifti header to initialise transformaiton',
                           argstr='-nac')
    # Percent of blocks that are considered active.
    v_val = PositiveInt(desc='Percent of blocks that are active', argstr='-%v %d')
    # Percent of inlier blocks
    i_val = PositiveInt(desc='Percent of inlier blocks', argstr='-%i %d')
    # Verbosity off?
    verbosity_off_flag = traits.Bool(argstr='-voff', desc='Turn off verbose output')
    # Lower threshold on reference image
    ref_low_val = traits.Float(desc='Lower threshold value on reference image',
                               argstr='-refLowThr %f')
    # Upper threshold on reference image
    ref_up_val = traits.Float(desc='Upper threshold value on reference image',
                              argstr='-refUpThr %f')
    # Lower threshold on floating image
    flo_low_val = traits.Float(desc='Lower threshold value on floating image',
                               argstr='-floLowThr %f')
    # Upper threshold on floating image
    flo_up_val = traits.Float(desc='Upper threshold value on floating image',
                              argstr='-floUpThr %f')

# Output spec
class RegAladinOutputSpec(TraitedSpec):
    aff_file = File(desc='The output affine file')
    res_file = File(desc='The output transformed image')
    avg_output = traits.String(desc='Output string in the format for reg_average')

# Main interface class
class RegAladin(NIFTYREGCommand):
    """ Use RegAladin to perform linear (rigid or affine) image registration.
    
    Examples
    --------
    
    >>> from nipype.interfaces import niftyreg
    >>> aladin = niftyreg.RegAladin()
    >>> aladin.inputs.flo_image = "floating_image.nii.gz"
    >>> aladin.inputs.ref_image = "reference_image.nii.gz"
    """
    _cmd = 'reg_aladin'
    input_spec = RegAladinInputSpec
    output_spec = RegAladinOutputSpec

    def _gen_filename(self, name):
        if name == 'aff_file':
            return self._gen_fname(self.inputs.flo_file,
                                   suffix='_aff', change_ext=True, ext='.txt')
        return None

    def _list_outputs(self):
        outputs = super(RegAladin, self)._list_outputs()
        
        if isdefined(self.inputs.aff_file):
            outputs['aff_file'] = self.inputs.aff_file
        else:
            outputs['aff_file'] = self._gen_filename('aff_file')
        
        # Make a list of the linear transformation file and the input image
        outputs['avg_output'] = os.path.abspath(outputs['aff_file']) + ' ' + os.path.abspath(self.inputs.flo_file)
        return outputs
        
#-----------------------------------------------------------
# reg_transform wrapper interface
#-----------------------------------------------------------
class RegTransformInputSpec(NIFTYREGCommandInputSpec):

    ref1_file = File(exists=True, 
                     desc='The input reference/target image',
                     argstr='-ref %s', 
                     position = 0)
    ref2_file = File(exists=True, 
                     desc='The input second reference/target image',
                     argstr='-ref2 %s',
                     position = 1,
                     require = ['ref1_file'])

    def_input = File(exists=True, 
                     desc='Compute deformation field from transformation', 
                     argstr='-def %s', 
                     xor = ['disp_input', 'flow_input', 'comp_input', 'upd_s_form_input', 'inv_aff_input', 'inv_nrr_input', 'half_input', 'make_aff_input', 'aff_2_rig_input', 'flirt_2_nr_input'])

    disp_input = File(exists=True, 
                      desc='Compute displacement field from transformation', 
                      argstr='-disp %s',
                      xor = ['def_input', 'flow_input', 'comp_input', 'upd_s_form_input', 'inv_aff_input', 'inv_nrr_input', 'half_input', 'make_aff_input', 'aff_2_rig_input', 'flirt_2_nr_input'])

    flow_input = File(exists=True, 
                      desc='Compute flow field from spline SVF', 
                      argstr='-flow %s',
                      xor = ['def_input', 'disp_input', 'comp_input', 'upd_s_form_input', 'inv_aff_input', 'inv_nrr_input', 'half_input', 'make_aff_input', 'aff_2_rig_input', 'flirt_2_nr_input'])

    comp_input = File(exists = True,
                      desc='compose two transformations', 
                      argstr='-comp %s',
                      position = -3,
                      xor = ['def_input', 'disp_input', 'flow_input', 'upd_s_form_input', 'inv_aff_input', 'inv_nrr_input', 'half_input', 'make_aff_input', 'aff_2_rig_input', 'flirt_2_nr_input'])

    comp_input2 = File(exists = True,
                       desc='compose two transformations', 
                       argstr='%s',
                       position = -2,
                       require = ['comp_input'])

    upd_s_form_input = File(exists=True,
                            desc='Update s-form using the affine transformation', 
                            argstr='-updSform %s',
                            xor = ['def_input', 'disp_input', 'flow_input', 'comp_input', 'inv_aff_input', 'inv_nrr_input', 'half_input', 'make_aff_input', 'aff_2_rig_input', 'flirt_2_nr_input'])
    upd_s_form_input2 = File(exists=True,
                             desc='Update s-form using the affine transformation', 
                             argstr='%s',
                             position = -2,
                             require = ['upd_s_form_input'])

    inv_aff_input = File(exists=True,
                         desc='Invert an affine transformation', 
                         argstr='-invAff %s',
                         xor = ['def_input', 'disp_input', 'flow_input', 'comp_input', 'upd_s_form_input', 'inv_nrr_input', 'half_input', 'make_aff_input', 'aff_2_rig_input', 'flirt_2_nr_input'])

    inv_nrr_input = traits.Tuple(File(exists=True), File(exists=True),
                                 desc='Invert a non-linear transformation', 
                                 argstr='-invNrr %s %s',
                                 xor = ['def_input', 'disp_input', 'flow_input', 'comp_input', 'upd_s_form_input', 'inv_aff_input', 'half_input', 'make_aff_input', 'aff_2_rig_input', 'flirt_2_nr_input'])

    half_input = File(exists=True,
                      desc='Half way to the input transformation', 
                      argstr='-half %s',
                      xor = ['def_input', 'disp_input', 'flow_input', 'comp_input', 'upd_s_form_input', 'inv_aff_input', 'inv_nrr_input', 'make_aff_input', 'aff_2_rig_input', 'flirt_2_nr_input'])

    make_aff_input = traits.Tuple(traits.Float, traits.Float, traits.Float, traits.Float,
                                  traits.Float, traits.Float, traits.Float, traits.Float, traits.Float, traits.Float,
                                  traits.Float, traits.Float, 
                                  desc = 'Make an affine transformation matrix',
                                  argstr='-makeAff %f %f %f %f %f %f %f %f %f %f %f %f',
                                  xor = ['def_input', 'disp_input', 'flow_input', 'comp_input', 'upd_s_form_input', 'inv_aff_input', 'inv_nrr_input', 'half_input', 'aff_2_rig_input', 'flirt_2_nr_input'])

    aff_2_rig_input = File(exists=True, 
                           desc='Extract the rigid component from affine transformation', 
                           argstr='-aff2rig %s',
                           xor = ['def_input', 'disp_input', 'flow_input', 'comp_input', 'upd_s_form_input', 'inv_aff_input', 'inv_nrr_input', 'half_input', 'make_aff_input', 'flirt_2_nr_input'])

    flirt_2_nr_input = traits.Tuple(File(exists=True), File(exists=True), File(exists=True),
                                    desc='Convert a FLIRT affine transformation to niftyreg affine transformation',
                                    argstr='-flirtAff2NR %s %s %s',
                                    xor = ['def_input', 'disp_input', 'flow_input', 'comp_input', 'upd_s_form_input', 'inv_aff_input', 'inv_nrr_input', 'half_input', 'make_aff_input', 'aff_2_rig_input'])


    out_file = File(genfile=True, 
                    position=-1, 
                    argstr='%s', 
                    desc='transformation file to write')

class RegTransformOutputSpec(TraitedSpec):

    out_file = File(desc = 'Output File (transformation in any format)', exists = True)

class RegTransform(NIFTYREGCommand):
    
    """
    
    * * OPTIONS * *
    
    -v Print the subversion revision number
    
    -ref <filename>
    Filename of the reference image
    The Reference image has to be specified when a cubic B-Spline parametrised control point grid is used*.
    -ref2 <filename>
    Filename of the second reference image to be used when dealing with composition
    
    -def <filename1> <filename2>
    Take a transformation of any recognised type* and compute the corresponding deformation field
    filename1 - Input transformation file name
    filename2 - Output deformation field file name
    
    -disp <filename1> <filename2>
    Take a transformation of any recognised type* and compute the corresponding displacement field
    filename1 - Input transformation file name
    filename2 - Output displacement field file name
    
    -flow <filename1> <filename2>
    Take a spline parametrised SVF and compute the corresponding flow field
    filename1 - Input transformation file name
    filename2 - Output flow field file name
    
    -comp <filename1> <filename2> <filename3>
    Compose two transformations of any recognised type* and returns a deformation field.
    Trans3(x) = Trans2(Trans1(x)).
    filename1 - Input transformation 1 file name (associated with -ref if required)
    filename2 - Input transformation 2 file name (associated with -ref2 if required)
    filename3 - Output deformation field file name
    
    -updSform <filename1> <filename2> <filename3>
    Update the sform of an image using an affine transformation.
    Filename1 - Image to be updated
    Filename2 - Affine transformation defined as Affine x Reference = Floating
    Filename3 - Updated image.
    
    -invAff <filename1> <filename2>
    Invert an affine matrix.
    filename1 - Input affine transformation file name
    filename2 - Output inverted affine transformation file name
    
    -invNrr <filename1> <filename2> <filename3>
    Invert a non-rigid transformation and save the result as a deformation field.
    filename1 - Input transformation file name
    filename2 - Input floating (source) image where the inverted transformation is defined
    filename3 - Output inverted transformation file name
    Note that the cubic b-spline grid parametrisations can not be inverted without approximation,
    as a result, they are converted into deformation fields before inversion.
    
    -half <filename1> <filename2>
    The input transformation is halfed and stored using the same transformation type.
    filename1 - Input transformation file name
    filename2 - Output transformation file name
    
    -makeAff <rx> <ry> <rz> <tx> <ty> <tz> <sx> <sy> <sz> <shx> <shy> <shz> <outputFilename>
    Create an affine transformation matrix
    
    -aff2rig <filename1> <filename2>
    Extract the rigid component from an affine transformation matrix
    filename1 - Input transformation file name
    filename2 - Output transformation file name
    
    -flirtAff2NR <filename1> <filename2> <filename3> <filename4>
    Convert a flirt (FSL) affine transformation to a NiftyReg affine transformation
    filename1 - Input FLIRT (FSL) affine transformation file name
    filename2 - Image used as a reference (-ref arg in FLIRT)
    filename3 - Image used as a floating (-in arg in FLIRT)
    filename4 - Output affine transformation file name
    
    * The supported transformation types are:
    - cubic B-Spline parametrised grid (reference image is required)
    - a dense deformation field
    - a dense displacement field
    - a cubic B-Spline parametrised stationary velocity field (reference image is required)
    - a stationary velocity deformation field
    - a stationary velocity displacement field
    - an affine matrix
    
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
    
    """
    _cmd = 'reg_transform'
    input_spec = RegTransformInputSpec
    output_spec = RegTransformOutputSpec
    
    _suffix = '_reg_transform'

    def _find_input(self):
        inputs = [self.inputs.def_input, self.inputs.disp_input, self.inputs.flow_input, self.inputs.comp_input, self.inputs.upd_s_form_input, self.inputs.inv_aff_input, self.inputs.inv_nrr_input, self.inputs.half_input, self.inputs.make_aff_input, self.inputs.aff_2_rig_input, self.inputs.flirt_2_nr_input]
        for entry in inputs:
            if isdefined(entry):
                return entry
        return None

    def _gen_filename(self, name):
        if name == 'out_file':
            input_to_use = self._find_input()
            if isdefined(self.inputs.inv_aff_input):
                return self._gen_fname(input_to_use,
                                       suffix=self._suffix, change_ext=False, ext='.txt')
            else:
                return self._gen_fname(input_to_use,
                                       suffix=self._suffix)
        return None
                
    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_file):
            outputs['out_file'] = self.inputs.out_file
            outputs['out_file'] = os.path.abspath(outputs['out_file'])
        else:
            outputs['out_file'] = self._gen_filename('out_file')
            
        return outputs

#-----------------------------------------------------------
# reg_f3d wrapper interface
#-----------------------------------------------------------
# Input spec
class RegF3DInputSpec(NIFTYREGCommandInputSpec):
    # Input reference file
    ref_file = File(exists=True, desc='The input reference/target image',
                    argstr='-ref %s', mandatory=True)
    # Input floating file
    flo_file = File(exists=True, desc='The input floating/source image',
                    argstr='-flo %s', mandatory=True)
    # Output CPP file
    cpp_file = File(desc='The output CPP file', argstr='-cpp %s', name_source = ['flo_file'], name_template = '%s_cpp')
    # Output image file
    res_file = File(desc='The output resampled image', argstr='-res %s', name_source = ['flo_file'], name_template = '%s_res')
    
    # Input Affine file
    aff_file = File(exists=True, desc='The input affine transformation file', argstr='-aff %s')
    
    # Reference mask
    rmask_file = File(exists=True, desc='Reference image mask', argstr='-rmask %s')
    
    # Smoothing kernel for reference
    ref_smooth_val = traits.Float(desc='Smoothing kernel width for reference image',
                                   argstr='-smooR %f')
    # Smoothing kernel for floating
    flo_smooth_val = traits.Float(desc='Smoothing kernel width for floating image',
                                   argstr='-smooF %f')
    
    # Lower threshold for reference image
    rlwth_thr_val = traits.Float(desc='Lower threshold for reference image',
                                 argstr='--rLwTh %f')
    # Upper threshold for reference image
    rupth_thr_val = traits.Float(desc='Upper threshold for reference image',
                                 argstr='--rUpTh %f')
    # Lower threshold for reference image
    flwth_thr_val = traits.Float(desc='Lower threshold for floating image',
                                 argstr='--fLwTh %f')
    # Upper threshold for reference image
    fupth_thr_val = traits.Float(desc='Upper threshold for floating image',
                                 argstr='--fUpTh %f')

    # Lower threshold for reference image
    rlwth2_thr_val = traits.Tuple(PositiveInt, traits.Float, 
                                  desc='Lower threshold for reference image at the specified time point',
                                  argstr='-rLwTh %d %f')
    # Upper threshold for reference image
    rupth2_thr_val = traits.Tuple(PositiveInt, traits.Float, 
                                  desc='Upper threshold for reference image at the specified time point',
                                  argstr='-rUpTh %d %f')
    # Lower threshold for reference image
    flwth2_thr_val = traits.Tuple(PositiveInt, traits.Float, 
                                  desc='Lower threshold for floating image at the specified time point',
                                  argstr='-fLwTh %d %f')
    # Upper threshold for reference image
    fupth2_thr_val = traits.Tuple(PositiveInt, traits.Float, 
                                  desc='Upper threshold for floating image at the specified time point',
                                  argstr='-fUpTh %d %f')

    # Final grid spacing along the 3 axes
    sx_val = traits.Float(desc='Final grid spacing along the x axes', argstr='-sx %f')
    sy_val = traits.Float(desc='Final grid spacing along the y axes', argstr='-sy %f')
    sz_val = traits.Float(desc='Final grid spacing along the z axes', argstr='-sz %f')

    # Regularisation options
    be_val = traits.Float(desc='Bending energy value', argstr='-be %f')
    le_val = traits.Tuple(traits.Float, traits.Float, desc='Linear elasticity penalty term',
                          argstr='-le %f %f')
    l2_val = traits.Float(desc='L2 norm of displacement penalty value', argstr='-l2 %f')
    jl_val = traits.Float(desc='Log of jacobian of deformation penalty value', argstr='-jl %f')
    no_app_jl_flag = traits.Bool(argstr='-noAppJL', 
                                 desc='Do not approximate the log of jacobian penalty at control points only')

    # Similarity measure options
    nmi_flag = traits.Bool(argstr='--nmi', desc='use NMI even when other options are specified')
    rbn_val = PositiveInt(desc='Number of bins in the histogram for reference image',
                          argstr='--rbn %d')
    fbn_val = PositiveInt(desc='Number of bins in the histogram for reference image',
                          argstr='--fbn %d')
    rbn2_val = traits.Tuple(PositiveInt, PositiveInt,
                            desc='Number of bins in the histogram for reference image for given time point',
                            argstr='-rbn %d %d')

    fbn2_val = traits.Tuple(PositiveInt, PositiveInt, 
                            desc='Number of bins in the histogram for reference image for given time point',
                            argstr='-fbn %d %d')

    lncc_val = traits.Float(desc='SD of the Gaussian for computing LNCC', argstr='--lncc %f')
    lncc2_val = traits.Tuple(PositiveInt, traits.Float, 
                             desc='SD of the Gaussian for computing LNCC for a given time point', argstr='-lncc %d %f')
    
    ssd_flag = traits.Bool(desc='Use SSD as the similarity measure', argstr='--ssd')
    ssd2_flag = PositiveInt(desc='Use SSD as the similarity measure for a given time point', 
                            argstr='-ssd %d')
    kld_flag = traits.Bool(desc='Use KL divergence as the similarity measure', argstr='--kld')
    kld2_flag = PositiveInt(desc='Use KL divergence as the similarity measure for a given time point', 
                            argstr='-kld %d')
    amc_flag = traits.Bool(desc='Use additive NMI', argstr='-amc')
    
    nox_flag = traits.Bool(desc='Dont optimise in x direction', argstr='-nox')
    noy_flag = traits.Bool(desc='Dont optimise in y direction', argstr='-noy')
    noz_flag = traits.Bool(desc='Dont optimise in z direction', argstr='-noz')

    # Optimization options
    maxit_val = PositiveInt(desc='Maximum number of iterations per level', argstr='-maxit %d')
    ln_val = PositiveInt(desc='Number of resolution levels to create', argstr='-ln %d')
    lp_val = PositiveInt(desc='Number of resolution levels to perform', argstr='-lp %d')
    nopy_flag = traits.Bool(desc='Do not use the multiresolution approach', argstr='-nopy')
    noconj_flag = traits.Bool(desc='Use simple GD optimization', argstr='-noConj')
    pert_val = PositiveInt(desc='Add perturbation steps after each optimization step', 
                           argstr='-pert %d')

    # F3d2 options
    vel_flag = traits.Bool(desc='Use velocity field integration', argstr='-vel')
    fmask_file = File(exists=True, desc='Floating image mask', argstr='-fmask %s')

    # Other options
    smooth_grad_val = traits.Float(desc='Kernel width for smoothing the metric gradient',
                                    argstr='-smoothGrad %f')
    # Padding value
    pad_val = traits.Float(desc = 'Padding value', argstr='-pad %f')
    # verbosity off
    verbosity_off_flag = traits.Bool(argstr='-voff', desc='Turn off verbose output')

    output_type = traits.Enum('NIFTI_GZ', Info.ftypes.keys(),
                              desc='NiftyReg output type')

# Output spec
class RegF3DOutputSpec(TraitedSpec):
    cpp_file = File(desc='The output CPP file')
    res_file = File(desc='The output resampled image')
    invcpp_file = File(genfile=True, desc='The output inv CPP file')

# Main interface class
class RegF3D(NIFTYREGCommand):
    _cmd = 'reg_f3d'
    input_spec = RegF3DInputSpec
    output_spec = RegF3DOutputSpec
    
    def _get_basename_without_extension(self, in_file):
        ret = os.path.basename(in_file)
        ret = ret.replace('.nii.gz', '')
        ret = ret.replace('.nii', '')
        return ret

    def _list_outputs(self):
        outputs = super(RegF3D, self)._list_outputs()
        basename = self._get_basename_without_extension (outputs['cpp_file'])
        outputs['invcpp_file'] = os.path.abspath (basename + '_backward.nii.gz')
        return outputs
        
