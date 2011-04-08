from nipype.interfaces.base import CommandLineInputSpec, CommandLine, traits, TraitedSpec, File,\
    StdOutCommandLine, StdOutCommandLineInputSpec
from nipype.utils.filemanip import split_filename
import os
import nibabel as nb

class Image2VoxelInputSpec(StdOutCommandLineInputSpec):
    in_file = File(exists=True, argstr='-4dimage %s',
                    mandatory=True, position=1,
                    desc='4d image file')
#TODO convert list of files on the fly
#    imagelist = File(exists=True, argstr='-imagelist %s',
#                    mandatory=True, position=1,
#                    desc='Name of a file containing a list of 3D images')
#
#    imageprefix = traits.Str(argstr='-imageprefix %s', position=3,
#                    desc='Path to prepend onto filenames in the imagelist.')

    out_type = traits.Enum("float", "char", "short", "int", "long", "double", argstr='-outputdatatype %s', position=2,
                           desc='"i.e. Bfloat". Can be "char", "short", "int", "long", "float" or "double"', usedefault=True)

class Image2VoxelOutputSpec(TraitedSpec):
    voxel_order = File(exists=True, desc='path/name of 4D volume in voxel order')

class Image2Voxel(StdOutCommandLine):
    """
    Converts Analyze / NIFTI / MHA files to voxel order.

    Converts scanner-order data in a supported image format to voxel-order data.
    Either takes a 4D file (all measurements in single image)
    or a list of 3D images.

    Examples
    --------

    >>> import nipype.interfaces.camino as cmon
    >>> img2vox = cmon.Image2Voxel()
    >>> img2vox.inputs.in_file = '4d_dwi.nii'
    >>> img2vox.run()
    """
    _cmd = 'image2voxel'
    input_spec = Image2VoxelInputSpec
    output_spec = Image2VoxelOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['voxel_order'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '.B'+ self.inputs.out_type

class FSL2SchemeInputSpec(StdOutCommandLineInputSpec):
    bvec_file = File(exists=True, argstr='-bvecfile %s',
                    mandatory=True, position=1,
                    desc='b vector file')

    bval_file = File(exists=True, argstr='-bvalfile %s',
                    mandatory=True, position=2,
                    desc='b value file')

    numscans = traits.Int(argstr='-numscans %d', units='NA',
                desc="Output all measurements numerous (n) times, used when combining multiple scans from the same imaging session.")

    interleave = traits.Bool(argstr='-interleave', desc="Interleave repeated scans. Only used with -numscans.")

    bscale = traits.Float(argstr='-bscale %d', units='NA',
                desc="Scaling factor to convert the b-values into different units. Default is 10^6.")

    diffusiontime = traits.Float(argstr = '-diffusiontime %f', units = 'NA',
                desc="Diffusion time")

    flipx = traits.Bool(argstr='-flipx', desc="Negate the x component of all the vectors.")
    flipy = traits.Bool(argstr='-flipy', desc="Negate the y component of all the vectors.")
    flipz = traits.Bool(argstr='-flipz', desc="Negate the z component of all the vectors.")
    usegradmod = traits.Bool(argstr='-usegradmod', desc="Use the gradient magnitude to scale b. This option has no effect if your gradient directions have unit magnitude.")

class FSL2SchemeOutputSpec(TraitedSpec):
    scheme = File(exists=True, desc='Scheme file')

class FSL2Scheme(StdOutCommandLine):
    """
    Converts b-vectors and b-values from FSL format to a Camino scheme file.

    Examples
    --------

    >>> import nipype.interfaces.camino as cmon
    >>> makescheme = cmon.FSL2Scheme()
    >>> makescheme.inputs.bvec_file = 'bvecs'
    >>> makescheme.inputs.bvec_file = 'bvals'
    >>> makescheme.run()

    """
    _cmd = 'fsl2scheme'
    input_spec=FSL2SchemeInputSpec
    output_spec=FSL2SchemeOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['scheme'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.bvec_file)
        return name + '.scheme'

class VtkStreamlinesInputSpec(StdOutCommandLineInputSpec):
    inputmodel = traits.Enum('raw', 'voxels', argstr='-inputmodel %s', desc='input model type (raw or voxels)', usedefault=True)

    in_file = File(exists=True, argstr=' < %s',
                    mandatory=True, position=-2,
                    desc='data file')

    voxeldims = traits.List(traits.Int, desc = 'voxel dimensions in mm',
                 argstr='-voxeldims %s', minlen=3, maxlen=3, position=4,
                 units='mm')

    seed_file = File(exists=False, argstr='-seedfile %s',
                    mandatory=False, position=1,
                    desc='image containing seed points')

    target_file = File(exists=False, argstr='-targetfile %s',
                    mandatory=False, position=2,
                    desc='image containing integer-valued target regions')

    scalar_file = File(exists=False, argstr='-scalarfile %s',
                    mandatory=False, position=3,
                    desc='image that is in the same physical space as the tracts')

    colourorient = traits.Bool(argstr='-colourorient', desc="Each point on the streamline is coloured by the local orientation.")
    interpolatescalars = traits.Bool(argstr='-interpolatescalars', desc="the scalar value at each point on the streamline is calculated by trilinear interpolation")
    interpolate = traits.Bool(argstr='-interpolate', desc="the scalar value at each point on the streamline is calculated by trilinear interpolation")

class VtkStreamlinesOutputSpec(TraitedSpec):
    vtk = File(exists=True, desc='Streamlines in VTK format')

class VtkStreamlines(StdOutCommandLine):
    """
    Use vtkstreamlines to convert raw or voxel format streamlines to VTK polydata

    Examples
    --------

    >>> import nipype.interfaces.camino as cmon
    >>> vtk = cmon.VtkStreamlines()
    >>> vtk.inputs.in_file = 'tract_data.Bfloat'
    >>> vtk.inputs.voxeldims = [1,1,1]
    >>> vtk.run()
    """
    _cmd = 'vtkstreamlines'
    input_spec=VtkStreamlinesInputSpec
    output_spec=VtkStreamlinesOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['vtk'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '.vtk'

class ProcStreamlinesInputSpec(StdOutCommandLineInputSpec):
    inputmodel = traits.Enum('raw', 'voxels', argstr='-inputmodel %s', desc='input model type (raw or voxels)', usedefault=True)

    in_file = File(exists=True, argstr='-inputfile %s',
                    mandatory=True, position=1,
                    desc='data file')

    maxtractpoints= traits.Int(argstr='-maxtractpoints %d', units='NA',
                desc="maximum number of tract points")
    mintractpoints= traits.Int(argstr='-mintractpoints %d', units='NA',
                desc="minimum number of tract points")
    maxtractlength= traits.Int(argstr='-maxtractlength %d', units='mm',
                desc="maximum length of tracts")
    mintractlength= traits.Int(argstr='-mintractlength %d', units='mm',
                desc="minimum length of tracts")
    datadims = traits.List(traits.Int, desc = 'data dimensions in voxels',
                 argstr='-datadims %s', minlen=3, maxlen=3,
                 units='voxels')
    voxeldims = traits.List(traits.Int, desc = 'voxel dimensions in mm',
                 argstr='-voxeldims %s', minlen=3, maxlen=3,
                 units='mm')
    seedpointmm = traits.List(traits.Int, desc = 'The coordinates of a single seed point for tractography in mm',
                 argstr='-seedpointmm %s', minlen=3, maxlen=3,
                 units='mm')
    seedpointvox = traits.List(traits.Int, desc = 'The coordinates of a single seed point for tractography in voxels',
                             argstr='-seedpointvox %s', minlen=3, maxlen=3,
                             units='voxels')
    seedfile = File(exists=False, argstr='-seedfile %s',
                    mandatory=False, position=1,
                    desc='Image Containing Seed Points')
    regionindex = traits.Int(argstr='-regionindex %d', units='mm',
                desc="index of specific region to process")
    iterations = traits.Float(argstr='-iterations %d', units='NA',
                desc="Number of streamlines generated for each seed. Not required when outputting streamlines, but needed to create PICo images. The default is 1 if the output is streamlines, and 5000 if the output is connection probability images.")
    targetfile = File(exists=False, argstr='-targetfile %s',
                    mandatory=False, position=1,
                    desc='Image containing target volumes.')
    allowmultitargets = traits.Bool(argstr='-allowmultitargets', desc="Allows streamlines to connect to multiple target volumes.")
    directional = traits.List(traits.Int, desc = 'Splits the streamlines at the seed point and computes separate connection probabilities for each segment. Streamline segments are grouped according to their dot product with the vector (X, Y, Z). The ideal vector will be tangential to the streamline trajectory at the seed, such that the streamline projects from the seed along (X, Y, Z) and -(X, Y, Z). However, it is only necessary for the streamline trajectory to not be orthogonal to (X, Y, Z).',
                 argstr='-directional %s', minlen=3, maxlen=3,
                 units='NA')
    waypointfile = File(exists=False, argstr='-waypointfile %s',
                    mandatory=False, position=1,
                    desc='Image containing waypoints. Waypoints are defined as regions of the image with the same intensity, where 0 is background and any value > 0 is a waypoint.')
    truncateloops = traits.Bool(argstr='-truncateloops', desc="This option allows streamlines to enter a waypoint exactly once. After the streamline leaves the waypoint, it is truncated upon a second entry to the waypoint.")
    discardloops = traits.Bool(argstr='-discardloops', desc="This option allows streamlines to enter a waypoint exactly once. After the streamline leaves the waypoint, the entire streamline is discarded upon a second entry to the waypoint.")
    exclusionfile = File(exists=False, argstr='-exclusionfile %s',
                    mandatory=False, position=1,
                    desc='Image containing exclusion ROIs. This should be an Analyze 7.5 header / image file.hdr and file.img.')
    truncateinexclusion = traits.Bool(argstr='-truncateinexclusion', desc="Retain segments of a streamline before entry to an exclusion ROI.")

    endpointfile = File(exists=False, argstr='-endpointfile %s',
                    mandatory=False, position=1,
                    desc='Image containing endpoint ROIs. This should be an Analyze 7.5 header / image file.hdr and file.img.')

    resamplestepsize = traits.Float(argstr='-resamplestepsize %d', units='NA',
                desc="Each point on a streamline is tested for entry into target, exclusion or waypoint volumes. If the length between points on a tract is not much smaller than the voxel length, then streamlines may pass through part of a voxel without being counted. To avoid this, the program resamples streamlines such that the step size is one tenth of the smallest voxel dimension in the image. This increases the size of raw or oogl streamline output and incurs some performance penalty. The resample resolution can be controlled with this option or disabled altogether by passing a negative step size or by passing the -noresample option.")

    noresample = traits.Bool(argstr='-noresample', desc="Disables resampling of input streamlines. Resampling is automatically disabled if the input model is voxels.")
    outputtracts = traits.Enum('raw', 'voxels', 'oogl', argstr='-outputtracts %s', desc='output tract file type', usedefault=True)

    outputroot = File(exists=False, argstr='-outputroot %s',
                    mandatory=False, position=1,
                    desc='root directory for output')

    gzip = traits.Bool(argstr='-gzip', desc="save the output image in gzip format")
    outputcp = traits.Bool(argstr='-outputcp', desc="output the connection probability map (Analyze image, float)")
    outputsc = traits.Bool(argstr='-outputsc', desc="output the connection probability map (raw streamlines, int)")
    outputacm = traits.Bool(argstr='-outputacm', desc="output all tracts in a single connection probability map (Analyze image)")
    outputcbs = traits.Bool(argstr='-outputcbs', desc="outputs connectivity-based segmentation maps; requires target outputfile")

class ProcStreamlinesOutputSpec(TraitedSpec):
    proc = File(exists=True, desc='Processed Streamlines')

class ProcStreamlines(StdOutCommandLine):
    """
    Process streamline data

    This program does post-processing of streamline output from track. It can either output streamlines or connection probability maps.
     * http://web4.cs.ucl.ac.uk/research/medic/camino/pmwiki/pmwiki.php?n=Man.procstreamlines

    Examples
    --------

    >>> import nipype.interfaces.camino as cmon
    >>> proc = cmon.ProcStreamlines()
    >>> proc.inputs.in_file = 'tract_data.Bfloat'
    >>> proc.inputs.outputtracts = 'oogl'
    >>> proc.run()
    """
    _cmd = 'procstreamlines'
    input_spec=ProcStreamlinesInputSpec
    output_spec=ProcStreamlinesOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['proc'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '_proc'

class TractShredderInputSpec(StdOutCommandLineInputSpec):
    in_file = File(exists=True, argstr='< %s', mandatory=True, position=-2, desc='tract file')

    offset = traits.Int(argstr='%d', units='NA',
        desc='initial offset of offset tracts', position=1)

    bunchsize = traits.Int(argstr='%d', units='NA',
        desc='reads and outputs a group of bunchsize tracts', position=2)

    space = traits.Int(argstr='%d', units='NA',
        desc='skips space tracts', position=3)

class TractShredderOutputSpec(TraitedSpec):
    shredded = File(exists=True, desc='Shredded tract file')

class TractShredder(StdOutCommandLine):
    """
    Extracts bunches of streamlines.

    tractshredder works in a similar way to shredder, but processes streamlines instead of scalar data.
    The input is raw streamlines, in the format produced by track or procstreamlines.

    The program first makes an initial offset of offset tracts.  It then reads and outputs a group of
    bunchsize tracts, skips space tracts, and repeats until there is no more input.

    Examples
    --------

    >>> import nipype.interfaces.camino as cmon
    >>> shred = cmon.TractShredder()
    >>> shred.inputs.in_file = 'tract_data.Bfloat'
    >>> shred.inputs.offset = 0
    >>> shred.inputs.bunchsize = 1
    >>> shred.inputs.space = 2
    >>> shred.run()
    """
    _cmd = 'tractshredder'
    input_spec=TractShredderInputSpec
    output_spec=TractShredderOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['shredded'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '_shredded'
