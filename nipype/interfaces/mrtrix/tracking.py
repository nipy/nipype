from nipype.interfaces.base import CommandLineInputSpec, CommandLine, traits, TraitedSpec, File
from nipype.utils.filemanip import split_filename
import os

class Tracks2ProbInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-2,
        desc='tract file')
    template_file = File(exists=True, argstr='-template %s', position=1,
        desc='an image file to be used as a template for the output (the output image wil have the same transform and field of view)')
    voxel_dims = traits.List(traits.Float, argstr='-vox %s', sep=',', position=2, minlen=3, maxlen=3,
        desc='Three comma-separated numbers giving the size of each voxel in mm.')
    colour = traits.Bool(argstr='-colour', position=3, desc="add colour to the output image according to the direction of the tracks.")
    fraction = traits.Bool(argstr='-fraction', position=3, desc="produce an image of the fraction of fibres through each voxel (as a proportion of the total number in the file), rather than the count.")
    output_datatype = traits.Enum("nii", "float", "char", "short", "int", "long", "double", argstr='-datatype %s', position=2,
                           desc='"i.e. Bfloat". Can be "char", "short", "int", "long", "float" or "double"') #, usedefault=True)
    resample = traits.Float(argstr='-resample %d', position=3,
        units='mm', desc='resample the tracks at regular intervals using Hermite interpolation. If omitted, the program will select an appropriate interpolation factor automatically.')
    out_filename = File(argstr='%s', position= -1, genfile=True, desc='output data file')

class Tracks2ProbOutputSpec(TraitedSpec):
    tract_image = File(exists=True, desc='Output tract count or track density image')

class Tracks2Prob(CommandLine):
    """
    convert a tract file into a map of the fraction of tracks to enter each voxel.

    Example
    -------

    >>> import nipype.interfaces.camino as cmon                  # doctest: +SKIP
    >>> fit = mrt.Tracks2Prob()                  # doctest: +SKIP
    >>> fit.run()                  # doctest: +SKIP
    """
    _cmd = 'tracks2prob'
    input_spec=Tracks2ProbInputSpec
    output_spec=Tracks2ProbOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['tract_image'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '_TDI.mif'

class StreamlineTrackInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-2, desc='the image containing the source data.' \
    'The type of data required depends on the type of tracking as set in the preceeding argument. For DT methods, ' \
    'the base DWI are needed. For SD methods, the SH harmonic coefficients of the FOD are needed.')
    
    seed_file = File(exists=True, argstr='-seed %s', mandatory=False, position=2, desc='seed file')
    seed_spec = traits.List(traits.Int, desc='seed specification in voxels and radius (x y z r)', position=2,
        argstr='-seed %s', minlen=4, maxlen=4, sep=',', units='voxels')
    include_file = File(exists=True, argstr='-include %s', mandatory=False, position=2, desc='inclusion file')
    include_spec = traits.List(traits.Int, desc='inclusion specification in voxels and radius (x y z r)', position=2,
        argstr='-seed %s', minlen=4, maxlen=4, sep=',', units='voxels')
    exclude_file = File(exists=True, argstr='-exclude %s', mandatory=False, position=2, desc='exclusion file')
    exclude_spec = traits.List(traits.Int, desc='exclusion specification in voxels and radius (x y z r)', position=2,
        argstr='-seed %s', minlen=4, maxlen=4, sep=',', units='voxels')
    mask_file = File(exists=True, argstr='-exclude %s', mandatory=False, position=2, desc='mask file. Only tracks within mask.')
    mask_spec = traits.List(traits.Int, desc='Mask specification in voxels and radius (x y z r). Tracks will be terminated when they leave the ROI.', position=2,
        argstr='-seed %s', minlen=4, maxlen=4, sep=',', units='voxels')

    inputmodel = traits.Enum('DT_STREAM', 'SD_PROB', 'SD_STREAM',
        argstr='%s', desc='input model type', usedefault=True, position=-3)
        
    stop = traits.Bool(argstr='-gzip', desc="stop track as soon as it enters any of the include regions.")
    do_not_precompute = traits.Bool(argstr='-noprecomputed', desc="Turns off precomputation of the legendre polynomial values. Warning: this will slow down the algorithm by a factor of approximately 4.")
    unidirectional = traits.Bool(argstr='-unidirectional', desc="Track from the seed point in one direction only (default is to track in both directions).")
    no_mask_interpolation = traits.Bool(argstr='-nomaskinterp', desc="Turns off trilinear interpolation of mask images.")
    
    step_size = traits.Float(argstr='-step %s', units='mm',
        desc="Set the step size of the algorithm in mm (default is 0.2).")
    minimum_radius_of_curvature = traits.Float(argstr='-curvature %s', units='mm',
        desc="Set the minimum radius of curvature (default is 2 mm for DT_STREAM, 0 for SD_STREAM, 1 mm for SD_PROB and DT_PROB)")
    desired_number_of_tracks = traits.Int(argstr='-number %d', desc='Sets the desired number of tracks.'   \
    'The program will continue to generate tracks until this number of tracks have been selected and written to the output file' \
    '(default is 100 for *_STREAM methods, 1000 for *_PROB methods).')
    maximum_number_of_tracks = traits.Int(argstr='-number %d', desc='Sets the maximum number of tracks to generate.' \
    "The program will not generate more tracks than this number, even if the desired number of tracks hasn't yet been reached" \
    '(default is 100 x number).')

    minimum_tract_length = traits.Float(argstr='-minlength %s', units='mm',
        desc="Sets the minimum length of any track in millimeters (default is 10 mm).")
    maximum_tract_length = traits.Float(argstr='-length %s', units='mm',
        desc="Sets the maximum length of any track in millimeters (default is 200 mm).")

    cutoff_value = traits.Float(argstr='-cutoff %s', units='NA',
        desc="Set the FA or FOD amplitude cutoff for terminating tracks (default is 0.1).")
    initial_cutoff_value = traits.Float(argstr='-initcutoff %s', units='NA',
        desc="Sets the minimum FA or FOD amplitude for initiating tracks (default is twice the normal cutoff).")

    initial_direction = traits.List(traits.Int, desc='Specify the initial tracking direction as a vector',
        argstr='-initdirection %s', minlen=2, maxlen=2, units='voxels')
    out_file = File(argstr='%s', position= -1, genfile=True, desc='output data file')

class StreamlineTrackOutputSpec(TraitedSpec):
    tracked = File(exists=True, desc='output file containing reconstructed tracts')

class StreamlineTrack(CommandLine):
    """
    Performs tractography using one of the following models:
    'dt_prob', 'dt_stream', 'sd_prob', 'sd_stream'

    Example
    -------

    >>> import nipype.interfaces.camino as cmon                  # doctest: +SKIP
    >>> strack = cmon.StreamlineTrack()                  # doctest: +SKIP
    >>> strack.inputs.inputmodel = 'DT_PROB'                  # doctest: +SKIP
    >>> strack.inputs.in_file = 'data.Bfloat'                  # doctest: +SKIP
    >>> strack.inputs.seed_file = 'seed_mask.nii'                  # doctest: +SKIP
    >>> strack.run()                  # doctest: +SKIP
    """

    _cmd = 'streamtrack'

    input_spec = StreamlineTrackInputSpec
    output_spec = StreamlineTrackOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['tracked'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '_tracked'

class DiffusionTensorStreamlineTrackInputSpec(StreamlineTrackInputSpec):
    gradient_encoding_file = File(exists=True, argstr='-grad %s', mandatory=True, position=-2, 
    desc='Gradient encoding, supplied as a 4xN text file with each line is in the format [ X Y Z b ], where [ X Y Z ] describe the direction of the applied gradient, and b gives the b-value in units (1000 s/mm^2). See FSL2MRTrix')	

class DiffusionTensorStreamlineTrack(StreamlineTrack):
    """
    Performs streamline tractography using diffusion tensor data

    Example
    -------

    >>> import nipype.interfaces.camino as cmon                  # doctest: +SKIP
    >>> track = cmon.TrackBallStick()                  # doctest: +SKIP
    >>> track.inputs.in_file = 'ballstickfit_data.Bfloat'                  # doctest: +SKIP
    >>> track.inputs.seed_file = 'seed_mask.nii'                  # doctest: +SKIP
    >>> track.run()                  # doctest: +SKIP
    """
    input_spec = DiffusionTensorStreamlineTrackInputSpec
    
    def __init__(self, command=None, **inputs):
        inputs["inputmodel"] = "DT_STREAM"
        return super(DiffusionTensorStreamlineTrack, self).__init__(command, **inputs)
        
class ProbabilisticSphericallyDeconvolutedStreamlineTrackInputSpec(StreamlineTrackInputSpec):
    maximum_number_of_trials = traits.Int(argstr='-trials %s', units='mm',
        desc="Set the maximum number of sampling trials at each point (only used for probabilistic tracking).")
        
class ProbabilisticSphericallyDeconvolutedStreamlineTrack(StreamlineTrack):
    """
    Performs probabilistic tracking using spherically deconvolved data

    Example
    -------

    >>> import nipype.interfaces.camino as cmon                  # doctest: +SKIP
    >>> track = cmon.ProbabilisticSphericallyDeconvolutedStreamlineTrack()                  # doctest: +SKIP
    >>> track.inputs.in_file = 'ballstickfit_data.Bfloat'                  # doctest: +SKIP
    >>> track.inputs.seed_file = 'seed_mask.nii'                  # doctest: +SKIP
    >>> track.run()                  # doctest: +SKIP
    """
    input_spec = ProbabilisticSphericallyDeconvolutedStreamlineTrackInputSpec
    
    def __init__(self, command=None, **inputs):
        inputs["inputmodel"] = "SD_PROB"
        return super(ProbabilisticSphericallyDeconvolutedStreamlineTrack, self).__init__(command, **inputs)

class SphericallyDeconvolutedStreamlineTrack(StreamlineTrack):
    """
    Performs probabilistic tracking using spherically deconvolved data

    Example
    -------

    >>> import nipype.interfaces.camino as cmon                  # doctest: +SKIP
    >>> track = cmon.SphericallyDeconvolutedStreamlineTrack()                  # doctest: +SKIP
    >>> track.inputs.in_file = 'ballstickfit_data.Bfloat'                  # doctest: +SKIP
    >>> track.inputs.seed_file = 'seed_mask.nii'                  # doctest: +SKIP
    >>> track.run()                  # doctest: +SKIP
    """
    input_spec = StreamlineTrackInputSpec
    
    def __init__(self, command=None, **inputs):
        inputs["inputmodel"] = "SD_STREAM"
        return super(SphericallyDeconvolutedStreamlineTrack, self).__init__(command, **inputs)
