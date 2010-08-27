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
import os
from nipype.utils.filemanip import fname_presuffix
__docformat__ = 'restructuredtext'

from nipype.interfaces.base import (TraitedSpec, File, traits, CommandLine,
    CommandLineInputSpec)
from nipype.utils.misc import isdefined

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
    
    _gradient_matrix_file = 'gradient_matrix.txt'
    _cmd = 'dti_recon'
    
    def _format_arg(self, name, spec, value):
        if name == "bvecs":
            new_val = self._create_gradient_matrix(self.inputs.bvecs, self.inputs.bvals)
            return super(DTIRecon, self)._format_arg("bvecs", spec, new_val)
        return super(DTIRecon, self)._format_arg(name, spec, value)
        
    def _create_gradient_matrix(self, bvecs_file, bvals_file):
        bvals = [val for val in  re.split('\s+', open(bvals_file).readline().strip())]
        bvecs_f = open(bvecs_file)
        bvecs_x = [val for val in  re.split('\s+', bvecs_f.readline().strip())]
        bvecs_y = [val for val in  re.split('\s+', bvecs_f.readline().strip())]
        bvecs_z = [val for val in  re.split('\s+', bvecs_f.readline().strip())]
        bvecs_f.close()
        gradient_matrix_f = open(self._gradient_matrix_file, 'w')
        print len(bvals), len(bvecs_x), len(bvecs_y), len(bvecs_z)
        for i in range(len(bvals)):
            gradient_matrix_f.write("%s, %s, %s, %s\n"%(bvecs_x[i], bvecs_y[i], bvecs_z[i], bvals[i]))
        gradient_matrix_f.close()
        return self._gradient_matrix_file

    def _list_outputs(self):
        out_prefix = self.inputs.out_prefix
        output_type = self.inputs.output_type

        outputs = self.output_spec().get()
        outputs['ADC'] = fname_presuffix("",  prefix=out_prefix, suffix='_adc.'+ output_type)
        outputs['B0'] = fname_presuffix("",  prefix=out_prefix, suffix='_b0.'+ output_type)
        outputs['L1'] = fname_presuffix("",  prefix=out_prefix, suffix='_e1.'+ output_type)
        outputs['L2'] = fname_presuffix("",  prefix=out_prefix, suffix='_e2.'+ output_type)
        outputs['L3'] = fname_presuffix("",  prefix=out_prefix, suffix='_e3.'+ output_type)
        outputs['exp'] = fname_presuffix("",  prefix=out_prefix, suffix='_exp.'+ output_type)
        outputs['FA'] = fname_presuffix("",  prefix=out_prefix, suffix='_fa.'+ output_type)
        outputs['FA_color'] = fname_presuffix("",  prefix=out_prefix, suffix='_fa_color.'+ output_type)
        outputs['tensor'] = fname_presuffix("",  prefix=out_prefix, suffix='_tensor.'+ output_type)
        outputs['V1'] = fname_presuffix("",  prefix=out_prefix, suffix='_v1.'+ output_type)
        outputs['V2'] = fname_presuffix("",  prefix=out_prefix, suffix='_v2.'+ output_type)
        outputs['V3'] = fname_presuffix("",  prefix=out_prefix, suffix='_v3.'+ output_type)

        return outputs
    
class HARDIMatInputSpec(CommandLineInputSpec):
    bvecs = File(exists=True, desc = 'b vectors file', argstr='%s', mandatory=True, position=1)    
    out_file = File(desc = 'output matrix file', argstr='%s', genfile=True, position=2)
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
    
    def _get_outfilename(self):
        outfile = self.inputs.out_file
        if not isdefined(outfile):            
            outfile = fname_presuffix(self.inputs.bvecs,
                                      newpath=os.getcwd(),
                                      suffix='_out',
                                      use_ext=False)
        return outfile
        
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outfile = self._get_outfilename()
        outputs['out_file'] = outfile
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._get_outfilename()
        return None        
    

class ODFReconInputSpec(CommandLineInputSpec):
    raw_data = File(desc='Input raw data', argstr='%s',exists=True, mandatory=True,position=1)
    n_directions = traits.Int(desc='Number of directions', argstr='%s', mandatory=True, position=2)
    n_output_directions = traits.Int(desc='Number of output directions', argstr='%s', mandatory=True, position=3)
    out_prefix = traits.Str("odf", desc='Output file prefix', argstr='%s', usedefault=True, position=4)
    matrix = File(argstr='-mat %s', exists=True, desc="""use given file as reconstruction matrix. by default the program
will pick matrix file automatically by the given number of
diffusion and output directions""")
    n_b0 = traits.Int(argstr='-b0 %s', desc="""number of b0 scans. by default the program gets this information
from the number of directions and number of volume files in
the raw data directory. useful when dealing with incomplete raw
data set or only using part of raw data set to reconstruct""")
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
        outputs['B0'] = fname_presuffix("",  prefix=out_prefix, suffix='_b0.'+ output_type)
        outputs['DWI'] = fname_presuffix("",  prefix=out_prefix, suffix='_dwi.'+ output_type)
        outputs['MAX'] = fname_presuffix("",  prefix=out_prefix, suffix='_max.'+ output_type)
        outputs['ODF'] = fname_presuffix("",  prefix=out_prefix, suffix='_odf.'+ output_type)
        if isdefined(self.inputs.output_entropy):
            outputs['ENTROPY'] = fname_presuffix("",  prefix=out_prefix, suffix='_entropy.'+ output_type)
       
        return outputs

class ODFTrackerInputSpec(CommandLineInputSpec):
    recon_data_prefix = traits.Str(desc='recon data prefix', argstr='%s', mandatory=True, position=1)
    out_file = File(desc = 'output track file', argstr='%s', genfile=True, position=2)
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
    mask = traits.List(traits.Str(), minlen=1, maxlen=2, desc="""<mask_image> [<mask_threshold>] threshold for mask image.  The
first argument is the mask image and the second is the threshold.  If the threshold is not provided, then the program will
automatically try to find the threshold""", argstr='-m %s')
    mask2 = traits.List(traits.Str(), minlen=1, maxlen=2, desc="""<mask_image> [<mask_threshold>] threshold for second mask image.  The
first argument is the mask image and the second is the threshold.  If the threshold is not provided, then the program will
automatically try to find the threshold""", argstr='-m %s')
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
    out_file = File(exists=True, desc='output track file')

class ODFTracker(CommandLine):
    """Use odf_tracker to generate track file
    """
    
    input_spec=ODFTrackerInputSpec
    output_spec=ODFTrackerOutputSpec
    
    _cmd = 'odf_tracker'

    def _get_outfilename(self):
        outfile = self.inputs.out_file
        if not isdefined(outfile):         
            outfile = fname_presuffix("",  prefix=self.inputs.recon_data_prefix, suffix='.trk')               
        return outfile
        
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outfile = self._get_outfilename()
        outputs['out_file'] = outfile
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._get_outfilename()
        return None        

class SplineFilterInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, desc='Input track file',position=1)
    step_length = traits.Float(argstr='%f', mandatory=True, desc='Step length', position=2)
    out_file = File(argstr='%s', genfile=True, desc = 'output track file', position=3)

class SplineFilterOutputSpec(CommandLineInputSpec):
    out_file = File(exists=True, desc='output track file')

class SplineFilter(CommandLine):
    """Use spline_filter to clean up original track file
    """
    
    input_spec=SplineFilterInputSpec
    output_spec=SplineFilterOutputSpec
    
    _cmd = 'spline_filter'

    def _get_outfilename(self):
        outfile = self.inputs.out_file
        if not isdefined(outfile):         
            outfile = fname_presuffix("",  prefix=self.inputs.in_file, suffix='_filtered.trk')               
        return outfile
        
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outfile = self._get_outfilename()
        outputs['out_file'] = outfile
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._get_outfilename()
        return None        
    
    