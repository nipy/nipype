# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provides interfaces to various commands provided by diffusion toolkit

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)

"""
import re
from nipype.utils.filemanip import fname_presuffix, split_filename, copyfile
import os
from nipype.utils.misc import isdefined
__docformat__ = 'restructuredtext'

from nipype.interfaces.base import (TraitedSpec, File, traits, CommandLine,
    CommandLineInputSpec)

def _create_gradient_matrix(bvecs_file, bvals_file):
    _gradient_matrix_file = 'gradient_matrix.txt'
    bvals = [val for val in  re.split('\s+', open(bvals_file).readline().strip())]
    bvecs_f = open(bvecs_file)
    bvecs_x = [val for val in  re.split('\s+', bvecs_f.readline().strip())]
    bvecs_y = [val for val in  re.split('\s+', bvecs_f.readline().strip())]
    bvecs_z = [val for val in  re.split('\s+', bvecs_f.readline().strip())]
    bvecs_f.close()
    gradient_matrix_f = open(_gradient_matrix_file, 'w')
    for i in range(len(bvals)):
        gradient_matrix_f.write("%s, %s, %s, %s\n"%(bvecs_x[i], bvecs_y[i], bvecs_z[i], bvals[i]))
    gradient_matrix_f.close()
    return _gradient_matrix_file

class DTIReconInputSpec(CommandLineInputSpec):
    dwi = File(desc='Input diffusion volume', argstr='%s',exists=True, mandatory=True,position=1)
    out_prefix = traits.Str("dti", desc='Output file prefix', argstr='%s', usedefault=True,position=2)
    output_type = traits.Enum('nii', 'analyze', 'ni1', 'nii.gz', argstr='-ot %s', desc='output file type', usedefault=True)    
    bvecs = File(exists=True, desc = 'b vectors file',
                argstr='-gm %s', mandatory=True)
    bvals = File(exists=True,desc = 'b values file', mandatory=True)
    n_averages = traits.Int(desc='Number of averages', argstr='-nex %s')
    image_orientation_vectors = traits.List(traits.Float(), minlen=6, maxlen=6, desc="""specify image orientation vectors. if just one argument given,
will treat it as filename and read the orientation vectors from
the file. if 6 arguments are given, will treat them as 6 float
numbers and construct the 1st and 2nd vector and calculate the 3rd
one automatically.
this information will be used to determine image orientation,
as well as to adjust gradient vectors with oblique angle when""", argstr="-iop %f")
    oblique_correction = traits.Bool(desc="""when oblique angle(s) applied, some SIEMENS dti protocols do not
adjust gradient accordingly, thus it requires adjustment for correct
diffusion tensor calculation""", argstr="-oc")
    b0_threshold = traits.Float(desc="""program will use b0 image with the given threshold to mask out high
background of fa/adc maps. by default it will calculate threshold
automatically. but if it failed, you need to set it manually.""", argstr="-b0_th")
    
    
class DTIReconOutputSpec(TraitedSpec):
    ADC = File(exists=True)
    B0 = File(exists=True)
    L1 = File(exists=True)
    L2 = File(exists=True)
    L3 = File(exists=True)
    exp = File(exists=True)
    FA = File(exists=True)
    FA_color = File(exists=True)
    tensor = File(exists=True)
    V1 = File(exists=True)
    V2 = File(exists=True)
    V3 = File(exists=True)

class DTIRecon(CommandLine):
    """Use dti_recon to generate tensors and other maps
    """
    
    input_spec=DTIReconInputSpec
    output_spec=DTIReconOutputSpec
    
    _cmd = 'dti_recon'
    
    def _format_arg(self, name, spec, value):
        if name == "bvecs":
            new_val = _create_gradient_matrix(self.inputs.bvecs, self.inputs.bvals)
            return super(DTIRecon, self)._format_arg("bvecs", spec, new_val)
        return super(DTIRecon, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        out_prefix = self.inputs.out_prefix
        output_type = self.inputs.output_type

        outputs = self.output_spec().get()
        outputs['ADC'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_adc.'+ output_type))
        outputs['B0'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_b0.'+ output_type))
        outputs['L1'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_e1.'+ output_type))
        outputs['L2'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_e2.'+ output_type))
        outputs['L3'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_e3.'+ output_type))
        outputs['exp'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_exp.'+ output_type))
        outputs['FA'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_fa.'+ output_type))
        outputs['FA_color'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_fa_color.'+ output_type))
        outputs['tensor'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_tensor.'+ output_type))
        outputs['V1'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_v1.'+ output_type))
        outputs['V2'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_v2.'+ output_type))
        outputs['V3'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_v3.'+ output_type))

        return outputs
    
class DTITrackerInputSpec(CommandLineInputSpec):
    tensor_file = File(exists=True, desc="reconstructed tensor file" )
    input_type = traits.Enum('nii', 'analyze', 'ni1', 'nii.gz', desc="""input and output file type. accepted values are:
analyze -> analyze format 7.5
ni1     -> nifti format saved in seperate .hdr and .img file
nii     -> nifti format with one .nii file
nii.gz  -> nifti format with compression
default type is 'nii'""", argstr = "-it %s")
    tracking_method = traits.Enum('fact', 'rk2', 'tl', 'sl', desc="""fact -> use FACT method for tracking. this is the default method.
rk2  -> use 2nd order runge-kutta method for tracking.
tl   -> use tensorline method for tracking.
sl   -> use interpolated streamline method with fixed step-length""", argstr="-%s")
    step_length = traits.Float(desc="""set step length, in the unit of minimum voxel size.
default value is 0.5 for interpolated streamline method
and 0.1 for other methods""", argstr="-l %f")
    angle_threshold = traits.Float(desc="set angle threshold. default value is 35 degree", argstr="-at %f")
    angle_threshold_weight = traits.Float(desc="set angle threshold weighting factor. weighting will be be applied \
on top of the angle_threshold", argstr = "-atw %f")
    random_seed = traits.Int(desc = "use random location in a voxel instead of the center of the voxel \
          to seed. can also define number of seed per voxel. default is 1", argstr="-rseed")
    invert_x = traits.Bool(desc="invert x component of the vector", argstr = "-ix")
    invert_y = traits.Bool(desc="invert y component of the vector", argstr = "-iy")
    invert_z = traits.Bool(desc="invert z component of the vector", argstr = "-iz")
    swap_xy = traits.Bool(desc="swap x & y vectors while tracking", argstr = "-sxy")
    swap_yz = traits.Bool(desc="swap y & z vectors while tracking", argstr = "-syz")
    swap_xz = traits.Bool(desc="swap x & z vectors while tracking", argstr = "-sxz")
    mask1_file = File(desc="first mask image", mandatory=True, argstr="-m %s", position=2)
    mask1_threshold = traits.Float(desc="threshold value for the first mask image, if not given, the program will \
try automatically find the threshold", position=3)
    mask2_file = File(desc="second mask image", argstr="-m2 %s", position=4)
    mask2_threshold = traits.Float(desc="threshold value for the second mask image, if not given, the program will \
try automatically find the threshold", position=5)
    input_data_prefix = traits.Str("dti", desc="for internal naming use only", position=0, argstr="%s", usedefault=True)
    output_file = File("tracks.trk", "file containing tracks", argstr="%s", position=1, usedefault=True)
    output_mask = File(desc="output a binary mask file in analyze format", argstr="-om %s")
    primary_vector = traits.Enum('v2', 'v3', desc = "which vector to use for fibre tracking: v2 or v3. If not set use v1", argstr="-%s")

class DTITrackerOutputSpec(TraitedSpec):
    track_file = File(exists=True)
    mask_file = File(exists=True)
    
class DTITracker(CommandLine):
    input_spec=DTITrackerInputSpec
    output_spec=DTITrackerOutputSpec
    
    _cmd = 'dti_tracker'
    
    def _run_interface(self, runtime):
        _, _, ext = split_filename(self.inputs.tensor_file)
        copyfile(self.inputs.tensor_file, os.path.abspath(self.inputs.input_data_prefix + "_tensor" + ext), copy=False)
        
        return super(DTITracker, self)._run_interface(runtime)
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['track_file'] = os.path.abspath(self.inputs.output_file)
        if isdefined(self.inputs.output_mask) and self.inputs.output_mask:
            outputs['mask_file'] = os.path.abspath(self.inputs.output_mask)
        
        return outputs
            
class SplineFilterInputSpec(CommandLineInputSpec):
    track_file = File(exists=True, desc="file containing tracks to be filtered", position=0, argstr="%s", mandatory=True)
    step_length = traits.Float(desc="in the unit of minimum voxel size", position=1, argstr="%f", mandatory=True)
    output_file = File("spline_tracks.trk", desc="target file for smoothed tracks", position=2, argstr="%s", usedefault=True)
    
class SplineFilterOutputSpec(TraitedSpec):
    smoothed_track_file = File(exists=True)
    
class SplineFilter(CommandLine):
    input_spec=SplineFilterInputSpec
    output_spec=SplineFilterOutputSpec
    
    _cmd = "spline_filter"
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['smoothed_track_file'] = os.path.abspath(self.inputs.output_file)
        return outputs

class HARDIMatInputSpec(CommandLineInputSpec):
    bvecs = File(exists=True, desc = 'b vectors file',
                argstr='%s', position=1, mandatory=True)
    bvals = File(exists=True,desc = 'b values file', mandatory=True)   
    out_file = File("recon_mat.dat", desc = 'output matrix file', argstr='%s', usedefault=True, position=2)
    order = traits.Int(argsstr='-order %s', desc="""maximum order of spherical harmonics. must be even number. default
is 4""")
    odf_file = File(exists=True, argstr='-odf %s', desc="""filename that contains the reconstruction points on a HEMI-sphere.
use the pre-set 181 points by default""")
    reference_file = File(exists=True, argstr='-ref %s', desc="""provide a dicom or nifti image as the reference for the program to
figure out the image orientation information. if no such info was
found in the given image header, the next 5 options -info, etc.,
will be used if provided. if image orientation info can be found
in the given reference, all other 5 image orientation options will 
be IGNORED""")
    image_info = File(exists=True, argstr='-info %s', desc="""specify image information file. the image info file is generated
from original dicom image by diff_unpack program and contains image
orientation and other information needed for reconstruction and
tracking. by default will look into the image folder for .info file""")
    image_orientation_vectors = traits.List(traits.Float(), minlen=6, maxlen=6, desc="""specify image orientation vectors. if just one argument given,
will treat it as filename and read the orientation vectors from
the file. if 6 arguments are given, will treat them as 6 float
numbers and construct the 1st and 2nd vector and calculate the 3rd
one automatically.
this information will be used to determine image orientation,
as well as to adjust gradient vectors with oblique angle when""", argstr="-iop %f")    
    oblique_correction = traits.Bool(desc="""when oblique angle(s) applied, some SIEMENS dti protocols do not
adjust gradient accordingly, thus it requires adjustment for correct
diffusion tensor calculation""", argstr="-oc")

class HARDIMatOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='output matrix file')
    

class HARDIMat(CommandLine):
    """Use hardi_mat to calculate a reconstruction matrix from a gradient table
    """
    input_spec=HARDIMatInputSpec
    output_spec=HARDIMatOutputSpec
    
    _cmd = 'hardi_mat'
    
    def _format_arg(self, name, spec, value):
        if name == "bvecs":
            new_val = _create_gradient_matrix(self.inputs.bvecs, self.inputs.bvals)
            return super(HARDIMat, self)._format_arg("bvecs", spec, new_val)
        return super(HARDIMat, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs

class ODFReconInputSpec(CommandLineInputSpec):
    dwi = File(desc='Input raw data', argstr='%s',exists=True, mandatory=True,position=1)
    n_directions = traits.Int(desc='Number of directions', argstr='%s', mandatory=True, position=2)
    n_output_directions = traits.Int(desc='Number of output directions', argstr='%s', mandatory=True, position=3)
    out_prefix = traits.Str("odf", desc='Output file prefix', argstr='%s', usedefault=True, position=4)
    matrix = File(argstr='-mat %s', exists=True, desc="""use given file as reconstruction matrix.""", mandatory=True)
    n_b0 = traits.Int(argstr='-b0 %s', desc="""number of b0 scans. by default the program gets this information
from the number of directions and number of volumes in
the raw data. useful when dealing with incomplete raw
data set or only using part of raw data set to reconstruct""", mandatory=True)
    output_type = traits.Enum('nii', 'analyze', 'ni1', 'nii.gz', argstr='-ot %s', desc='output file type', usedefault=True)    
    sharpness = traits.Float(desc="""smooth or sharpen the raw data. factor > 0 is smoothing.
factor < 0 is sharpening. default value is 0
NOTE: this option applies to DSI study only""", argstr='-s %f')
    filter = traits.Bool(desc="""apply a filter (e.g. high pass) to the raw image""", argstr='-f')
    subtract_background = traits.Bool(desc="""subtract the background value before reconstruction""", argstr='-bg')
    dsi = traits.Bool(desc="""indicates that the data is dsi""", argstr='-dsi')
    output_entropy = traits.Bool(desc="""output entropy map""", argstr='-oe')
    image_orientation_vectors = traits.List(traits.Float(), minlen=6, maxlen=6, desc="""specify image orientation vectors. if just one argument given,
will treat it as filename and read the orientation vectors from
the file. if 6 arguments are given, will treat them as 6 float
numbers and construct the 1st and 2nd vector and calculate the 3rd
one automatically.
this information will be used to determine image orientation,
as well as to adjust gradient vectors with oblique angle when""", argstr="-iop %f")
    oblique_correction = traits.Bool(desc="""when oblique angle(s) applied, some SIEMENS dti protocols do not
adjust gradient accordingly, thus it requires adjustment for correct
diffusion tensor calculation""", argstr="-oc")
   
    
class ODFReconOutputSpec(TraitedSpec):
    B0 = File(exists=True)
    DWI = File(exists=True)
    MAX = File(exists=True)
    ODF = File(exists=True)
    ENTROPY = File(desc='Output entropy map')

class ODFRecon(CommandLine):
    """Use odf_recon to generate tensors and other maps
    """
    
    input_spec=ODFReconInputSpec
    output_spec=ODFReconOutputSpec
    
    _cmd = 'odf_recon'
        
    def _list_outputs(self):
        out_prefix = self.inputs.out_prefix
        output_type = self.inputs.output_type

        outputs = self.output_spec().get()
        outputs['B0'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_b0.'+ output_type))
        outputs['DWI'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_dwi.'+ output_type))
        outputs['MAX'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_max.'+ output_type))
        outputs['ODF'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_odf.'+ output_type))
        if isdefined(self.inputs.output_entropy):
            outputs['ENTROPY'] = os.path.abspath(fname_presuffix("",  prefix=out_prefix, suffix='_entropy.'+ output_type))
       
        return outputs

class ODFTrackerInputSpec(CommandLineInputSpec):
    MAX = File(exists=True, mandatory=True)
    ODF = File(exists=True, mandatory=True)
    input_data_prefix = traits.Str("odf", desc='recon data prefix', argstr='%s', usedefault=True, position=0)
    out_file = File("tracks.trk", desc = 'output track file', argstr='%s', usedefault=True, position=1)
    input_output_type = traits.Enum('nii', 'analyze', 'ni1', 'nii.gz', argstr='-it %s', desc='input and output file type', usedefault=True)
    runge_kutta2 = traits.Bool(argstr='-rk2', desc="""use 2nd order runge-kutta method for tracking.
default tracking method is non-interpolate streamline""")
    step_length = traits.Float(argstr='-l %f', desc="""set step length, in the unit of minimum voxel size.
default value is 0.1.""")
    angle_threshold = traits.Float(argstr='-at %f',desc="""set angle threshold. default value is 35 degree for
default tracking method and 25 for rk2""")
    random_seed = traits.Int(argstr='-rseed %s', desc="""use random location in a voxel instead of the center of the voxel
to seed. can also define number of seed per voxel. default is 1""")
    invert_x = traits.Bool(argstr='-ix', desc='invert x component of the vector')
    invert_y = traits.Bool(argstr='-iy', desc='invert y component of the vector')
    invert_z = traits.Bool(argstr='-iz', desc='invert z component of the vector')
    swap_xy = traits.Bool(argstr='-sxy', desc='swap x and y vectors while tracking')
    swap_yz = traits.Bool(argstr='-syz', desc='swap y and z vectors while tracking')
    swap_zx = traits.Bool(argstr='-szx', desc='swap x and z vectors while tracking')
    disc = traits.Bool(argstr='-disc', desc='use disc tracking')
    mask1_file = File(desc="first mask image", mandatory=True, argstr="-m %s", position=2)
    mask1_threshold = traits.Float(desc="threshold value for the first mask image, if not given, the program will \
try automatically find the threshold", position=3)
    mask2_file = File(desc="second mask image", argstr="-m2 %s", position=4)
    mask2_threshold = traits.Float(desc="threshold value for the second mask image, if not given, the program will \
try automatically find the threshold", position=5)
    limit = traits.Int(argstr='-limit %d', desc="""in some special case, such as heart data, some track may go into
infinite circle and take long time to stop. this option allows
setting a limit for the longest tracking steps (voxels)""")
    dsi = traits.Bool(argstr='-dsi', desc=""" specify the input odf data is dsi. because dsi recon uses fixed
pre-calculated matrix, some special orientation patch needs to
be applied to keep dti/dsi/q-ball consistent.""")
    image_orientation_vectors = traits.List(traits.Float(), minlen=6, maxlen=6, desc="""specify image orientation vectors. if just one argument given,
will treat it as filename and read the orientation vectors from
the file. if 6 arguments are given, will treat them as 6 float
numbers and construct the 1st and 2nd vector and calculate the 3rd
one automatically.
this information will be used to determine image orientation,
as well as to adjust gradient vectors with oblique angle when""", argstr="-iop %f")
    slice_order = traits.Int(argstr='-sorder %d', desc='set the slice order. 1 means normal, -1 means reversed. default value is 1')
    voxel_order = traits.Enum('RAS', 'RPS', 'RAI', 'RPI', 'LAI', 'LAS', 'LPS', 'LPI', argstr='-vorder %s', desc="""specify the voxel order in RL/AP/IS (human brain) reference. must be
3 letters with no space in between.
for example, RAS means the voxel row is from L->R, the column
is from P->A and the slice order is from I->S.
by default voxel order is determined by the image orientation
(but NOT guaranteed to be correct because of various standards).
for example, siemens axial image is LPS, coronal image is LIP and
sagittal image is PIL.
this information also is NOT needed for tracking but will be saved
in the track file and is essential for track display to map onto
the right coordinates""") 
    
class ODFTrackerOutputSpec(TraitedSpec):
    track_file = File(exists=True, desc='output track file')

class ODFTracker(CommandLine):
    """Use odf_tracker to generate track file
    """
    
    input_spec=ODFTrackerInputSpec
    output_spec=ODFTrackerOutputSpec
    
    _cmd = 'odf_tracker'

    def _run_interface(self, runtime):
        _, _, ext = split_filename(self.inputs.MAX)
        copyfile(self.inputs.MAX, os.path.abspath(self.inputs.input_data_prefix + "_max" + ext), copy=False)
        
        _, _, ext = split_filename(self.inputs.ODF)
        copyfile(self.inputs.ODF, os.path.abspath(self.inputs.input_data_prefix + "_odf" + ext), copy=False)
        
        return super(ODFTracker, self)._run_interface(runtime)
        
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['track_file'] = os.path.abspath(self.inputs.out_file)
        return outputs
    
    