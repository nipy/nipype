# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provides interfaces to various commands provided by Camino
"""

# We use position args here as list indices - so a negative number will put something on the end
## CHANGE File position for each input parameter for each command!!!!
#
import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import os                                    # system functions
from nipype.interfaces.camino.base import CaminoCommand, CaminoCommandInputSpec

import re
from glob import glob
from nibabel import load
from nipype.utils.filemanip import fname_presuffix, split_filename, copyfile
from nipype.utils.misc import isdefined
__docformat__ = 'restructuredtext'

from nipype.interfaces.base import (TraitedSpec, File, traits, CommandLine,
    CommandLineInputSpec)

class fsl2schemeInputSpec(CaminoCommandInputSpec):
	""" fsl2scheme -bvecfile <bvecs> -bvalfile <bvals> -diffusiontime <secs> -bscale <factor> [-flipx] [-flipy] [-flipz] [-usegradmod] 
	* fsl2scheme - converts b-vectors and b-values from FSL format to a Camino scheme file. 
	-bvecfile <bvecs>
		The file containing the b-vectors. This is a text file of format


		 x(1) x(2)... x(N+M)
		 y(1) y(2) ... y(N+M)
		 z(1) z(2) ... z(N+M)

		where the gradient direction for measurement (i) is [x(i), y(i), z(i)], and there are M unweighted and N diffusion-weighted measurements.

	-bvalfile <bvals>
		The file containing the b-values. This is a text file of format

		b(1) b(2) ... b(N+M)

		where there are M unweighted (b = 0) and N diffusion-weighted measurements.

	-bscale <factor>
		Scaling factor to convert the b-values into different units. Default is 10^6.

	-flipx
		Negate the x component of all the vectors.

	-flipy
		Negate the y component of all the vectors.

	-flipz
		Negate the z component of all the vectors.

	-interleave
		Interleave repeated scans. Only used with -numscans. If this is selected, the output will be interleaved, so you will have measurement 0 repeated numScans times, then measurement 1, etc.

	-numscans <number>
		Output all measurements number times, used when combining multiple scans from the same imaging session. The default behaviour is to repeat the entire block of measurements, like you'd get from copying and pasting the scheme number times. If -interleave is specified, then identical measurements are grouped together.

	-usegradmod
		Use the gradient magnitude to scale b. This option has no effect if your gradient directions have unit magnitude. It should only be used if your scanner does not normalize the gradient directions. 
	"""

	bvec_file = File(exists=True, argstr='-bvecfile %s',
					mandatory=True, position=1,
					desc='b vector file')
					
	bval_file = File(exists=True, argstr='-bvalfile %s',
					mandatory=True, position=2,
					desc='b value file')
					
	out_file = File(exists=False, argstr='-outputfile %s', genfile=True, desc='Name of output scheme file', position=3) 
					
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
	
class fsl2schemeOutputSpec(TraitedSpec):
	scheme = File(exists=True, desc='Scheme file') 

class fsl2scheme(CaminoCommand):
	_cmd = 'fsl2scheme'	
	input_spec=fsl2schemeInputSpec
	output_spec=fsl2schemeOutputSpec

	def _list_outputs(self):	
		outputs = self.output_spec().get()
		outputs['scheme'] = self.inputs.out_file
		if not isdefined(outputs['scheme']):
			outputs['scheme'] = self._gen_fname('scheme')
		return outputs
	
	def _run_interface(self, runtime):		
		if not isdefined(self.inputs.out_file):
		    self.inputs.out_file = self._gen_fname('scheme')
		runtime = super(fsl2scheme, self)._run_interface(runtime)
		# FSL_ToScheme seems to log warnings to stderr even on success
		#if runtime.stderr:
		#    runtime.returncode = 1
		return runtime
	
	def _gen_filename(self, name):
		if name is 'out_file':
		    return self._list_outputs()['scheme']
		else:
		    return None

class image2voxelInputSpec(CaminoCommandInputSpec):
	"""	image2voxel -4dimage <file> | -imagelist <file> [options] 
	 
	 * Converts Analyze / NIFTI / MHA files to voxel order. 
	 * Either takes a 4D file (all measurements in single image) 
	 * or a list of 3D images.
	 
	 http://web4.cs.ucl.ac.uk/research/medic/camino/pmwiki/pmwiki.php?n=Man.Image2voxel
	 
	 OPTIONS
	-4dimage <file>
		Path to the input image file or header. 
		This should be used when converting 4D / 5D files where each 3D volume is an image from a single diffusion-weighted measurement. 
		The order of the measurement volumes must correspond to the accompanying scheme file.

	-imagelist <filename>
		Name of a file containing a list of 3D images, each containing a single diffusion-weighted measurement. 
		The order of the headers in the list must match the order of the corresponding measurements in the scheme file.

	-imageprefix <prefix>
		Path to prepend onto filenames in the imagelist. 
		Has no effect on paths specified on the command line with -4dimage. 
		The default prefix is the directory containing the image list. 
		This option is used when the imagelist is not in the same directory as the images it describes.

	-outputdatatype <data type of output>
		Specifies the data type of the output data. 
		The data type can be any of the following strings: "char", "short", "int", "long", "float" or "double". 
		The default output data type is float.
	"""

	in_file = File(exists=True, argstr='-4dimage %s',
					mandatory=True, position=1,
					desc='4d image file')
	
	imagelist = File(exists=False, argstr='-imagelist %s',
					mandatory=False, position=1,
					desc='Name of a file containing a list of 3D images')
	
	imageprefix = File(exists=False, argstr='-imageprefix %s',
					mandatory=False, position=2,
					desc='Path to prepend onto filenames in the imagelist.')
	
	out_file = File(exists=False, argstr='> %s', mandatory=False, genfile=True, desc='"Name of output file"')

	output_type = traits.Str("float", desc=' Specifies the data type of the output data, e.g. "char", "short", "int", "long",  "float"  or  "double". The default is float.', argstr='-outputdatatype %s', usedefault=True) 

class image2voxelOutputSpec(TraitedSpec):
	"""Use image2voxel to convert NIFTI images to voxel order
	"""
	voxel_order = File(exists=True, desc='output path/name of 4D volume in voxel order') 
    
class image2voxel(CaminoCommand):
	"""Use image2voxel to convert NIFTI images to voxel order
	"""
	_cmd = 'image2voxel'	
	input_spec=image2voxelInputSpec
	output_spec=image2voxelOutputSpec

	def _list_outputs(self):
		outputs = self.output_spec().get()
		outputs['voxel_order'] = self.inputs.out_file
		if not isdefined(outputs['voxel_order']):
			outputs['voxel_order'] = self._gen_fname(self.inputs.in_file,suffix = '_vox.',ext = self.inputs.output_type)
		return outputs
	
	def _run_interface(self, runtime):
		if not isdefined(self.inputs.out_file):
		    self.inputs.out_file = self._gen_fname(self.inputs.in_file,suffix = '_vox.',ext = self.inputs.output_type)
		runtime = super(image2voxel, self)._run_interface(runtime)
		if runtime.stderr:
		    runtime.returncode = 1
		return runtime

	def _gen_filename(self, name):
		if name is 'out_file':
		    return self._list_outputs()['voxel_order']
		else:
		    return None
		
class dtfitInputSpec(CaminoCommandInputSpec):
	"""
	* Reads diffusion MRI data, acquired using the acquisition scheme detailed in the scheme file, from the data file. 
	* For help with scheme files, please see the section "scheme files" in camino(1).  OPTIONS

	dtfit <data file> <scheme file> [-nonlinear] [options] --nonlinear
	
	    Use non-linear fitting instead of the default linear regression to the log measurements. 
	The data file stores the diffusion MRI data in voxel order with the measurements stored in big-endian format and ordered as in the scheme file.
	The default input data type is four-byte float. The default output data type is eight-byte double.
	See modelfit and camino for the format of the data file and scheme file.
	The program fits the diffusion tensor to each voxel and outputs the results, 
	in voxel order and as big-endian eight-byte doubles, to the standard output. 
	The program outputs eight values in each voxel: [exit code, ln(S(0)), D_xx, D_xy, D_xz, D_yy, D_yz, D_zz]. 
	An exit code of zero indicates no problems. For a list of other exit codes, see modelfit(1). The entry S(0) is an estimate of the signal at q=0. 
	"""
	
	in_file = File(exists=True, argstr='%s',
					mandatory=True, position=1,
					desc='voxel-order data filename')
	
	scheme_file = File(exists=False, argstr='%s',
					mandatory=False, position=2,
					desc='Camino scheme file (b values / vectors, see camino.fsl2scheme)')
	
	nonlinear = traits.Bool(argstr='-nonlinear', position=3, desc="Use non-linear fitting instead of the default linear regression to the log measurements. ")
	
	out_file = File(exists=False, argstr='> %s',
				mandatory=False, position=4,
				desc='name of tensor fitted output file')				
			
class dtfitOutputSpec(TraitedSpec):
	"""Use dtfit to fit tensors to each voxel
	"""
	tensor_fitted = File(exists=True, desc='tensor fitted output file') 

class dtfit(CaminoCommand):
	"""Use dtfit to fit tensors to each voxel
	"""
	_cmd = 'dtfit'
	input_spec=dtfitInputSpec
	output_spec=dtfitOutputSpec
	
	def _list_outputs(self):
		outputs = self.output_spec().get()
		return outputs
	
	def _run_interface(self, runtime):
		if not isdefined(self.inputs.out_file):
		    self.inputs.out_file = self._gen_fname(self.inputs.in_file,suffix = '_dt.double')
		runtime = super(dtfit, self)._run_interface(runtime)
		if runtime.stderr:
		    runtime.returncode = 1
		return runtime

	def _gen_filename(self, name):
		if name is 'out_file':
		    return self._list_outputs()['tensor_fitted']
		else:
		    return None
		
class trackInputSpec(CaminoCommandInputSpec):
	"""
	* track - Performs streamline tractography.
	* track [options]
		
	-inputmodel <model>
		One of the following:
		dt - diffusion tensor data, as produced by dtfit.
		multitensor - diffusion tensor data, as produced by multitenfit. 
			  Presently, track supports a maximum of two tensors per voxel for PICo.
			  Three tensors per voxel is allowed for streamline tracking.
			  The maximum number of tensor components in a voxel is controlled by the maxcomponents option, and the default is 2.
		pds - principal directions, as produced by sfpeaks. 
			  The maximum number of PDs in a voxel (if different from the default of 3) is specified by the numpds option.
		pico - PICo PDFs, as produced by picopdfs.
		bootstrap - raw data to be bootstrapped.
		ballstick - as produced by ballstickfit.
		bayesdirac - raw data for Bayesian tracking.

	-inputdatatype <type>
		If any bootstrapping options are specified, the default input data type is "float". Otherwise, it is "double".

	-numpds <number>
		The maximum number of PDs in a voxel for input models pds and pico. 
		The default is 3 for input model pds and 1 for input model pico.
		This option determines the size of the voxels in the input file and does not affect tracking.
		For tensor data, this option is not used. If the input model is "dt", the number of PDs in each voxel is 1.
		If the input model is "multitensor", the number of PDs is specified by the -maxcomponents option.

	-maxcomponents <number>
		The maximum number of tensor components in a voxel.
		This determines the size of the input file and does not say anything about the voxel classification.
		The default is 2 if the input model is multitensor and 1 if the input model is dt.

	-datadims <x> <y> <z>
		The x, y, and z dimension of the data, in voxels.
		Not required if a seed file is used, unless the seed dimensions do not agree with the diffusion dimensions.
		In either case, the physical coordinates of seed space MUST be aligned to diffusion space,
		i.e. a point in mm must be the same location in both, even if the voxel coordinates are different.

	-voxeldims <x> <y> <z>
		The x, y, and z dimension of each voxel, in millimetres.
		Not required if a seed file is used, unless the seed dimensions do not agree with the diffusion dimensions.
		In either case, the physical coordinates of seed space MUST be aligned to diffusion space, 
		i.e. a point in mm must be the same location in both, even if the voxel coordinates are different. 
		
		
		
	**************	OUTPUT OPTIONS   **************

	-gzip
		Compress output using the gzip algorithm.

	-outputtracts <format>
		Output streamlines, in one of the following formats: raw binary, voxels, oogl, or ooglbinary. The default is to output raw tracts.
		The raw streamline format is 32 bit float. For each streamline, the program outputs the number of points N in the streamline, 
		the index of the seed point, followed by the (x,y,z) coordinates (in mm) of each point: 
		[<N>, <seed point index>, <x_1>, <y_1>, <z_1>,...,<x_numPoints>, <y_N>, <z_N>, <N>,...,<z_N>], 
		where the <seed point index> is the point on the streamline where tracking began.

		The voxels format is 16-bit signed integer, and lists the integer indices of all M voxels that the streamline passes through, 
		in the format [<M>, <seed point index>, <vx_1>, <vy_1>, <vz_1>,...,<vx_M>, <vy_M>, <vz_M>, M,...,<vz_M>].
		The voxels are defined in the seed space.

		The OOGL format option, oogl, outputs a LIST of OOGL VECT objects in ASCII format. 
		The colour at each point on the streamline is an RGB vector that describes the local orientation as a combination of red (x), green (y) and blue (z). 
		The ooglbinary option outputs the same objects in the OOGL binary format.

	-outputroot <string>
		Prepended onto all output file names. Used to segregate output by ROI. 
		If this is not specified, all output goes to the file specified with the -outputfile option. 
		If no output file is specified, the output goes to stdout.

	-outputfile <string>
		Name of the file to which all output should be written. This option is ignored if -outputroot is set. 

	"""

	inputmodel = traits.Enum('dt', 'multitensor', 'pds', 'pico', 'bootstrap', 'ballstick', 'bayesdirac', 
							argstr='-inputmodel %s', position=1, desc='input model type', usedefault=True)    
	
	inputdatatype = traits.Enum('float', 'double', argstr='-inputdatatype %s', desc='input file type', usedefault=True)    
	
	in_file = File(exists=True, argstr='-inputfile %s',
					mandatory=True, position=3,
					desc='data file')
	
	seed_file = File(exists=True, argstr='-seedfile %s',
					mandatory=False, position=2,
					desc='seed file')
					
	maxcomponents = traits.Int(argstr='-maxcomponents %d', units='NA',
				desc="maximum number of components")
	
	numpds = traits.Int(argstr='-numpds %d', units='NA',
				desc="number of principal directions")
							
	datadims = traits.List(traits.Int, desc = 'data dimensions in voxels',
				 argstr='-datadims %s', minlen=3, maxlen=3,
				 units='voxels')
							 
	voxeldims = traits.List(traits.Int, desc = 'voxel dimensions in mm',
				 argstr='-voxeldims %s', minlen=3, maxlen=3,
				 units='mm')				 
    
class trackOutputSpec(TraitedSpec):
	#outputfile = File(exists=True, argstr='-outputfile %s',
	#				mandatory=True, position=1,
	#				desc='output data file')

	outputtracts = traits.Enum('float', 'double', 'oogl', argstr='-outputtracts %s', desc='output tract file type', usedefault=True)

	outputroot = File(exists=False, argstr='-outputroot %s',
				mandatory=False, position=1,
				desc='root directory for output')
				
	gzip = traits.Bool(argstr='-gzip', desc="save the output image in gzip format")
	out_file = File(exists=True, desc='path/name of 4D volume') 

class track(CaminoCommand):
	_cmd = 'track'    
	input_spec=trackInputSpec
	output_spec=trackOutputSpec
	
	def _list_outputs(self):
		out_prefix = self.inputs.out_prefix
		output_type = self.inputs.output_type
	
		outputs = self.output_spec().get()
		return outputs
	def _run_interface(self, runtime):
		if not isdefined(self.inputs.out_file):
		    self.inputs.out_file = self._gen_fname(self.inputs.in_file,suffix = '_tracked')
		runtime = super(track, self)._run_interface(runtime)
		if runtime.stderr:
		    runtime.returncode = 1
		return runtime
	
	def _gen_filename(self, name):
		if name is 'out_file':
		    return self._list_outputs()['tracts']
		else:
		    return None

class procstreamlinesInputSpec(CaminoCommandInputSpec):
	""" procstreamlines [options]
	 * This program does post-processing of streamline output from track. It can either output streamlines or connection probability maps. 
	 * http://web4.cs.ucl.ac.uk/research/medic/camino/pmwiki/pmwiki.php?n=Man.procstreamlines
	 
	 OPTIONS

	The following list details the options pertaining to the input data, the tractography parameters, the output, and the PICo parameters.

	DATA OPTIONS

	-inputmodel <model>
		One of the following:


		  raw - raw streamline data (default).
		  voxels - voxel lists.

	-datadims <x> <y> <z>
		The x, y, and z dimension of the data, in voxels. Not required if a seed, exclusion, waypoint or target file is given.

	-voxeldims <x> <y> <z>
		The x, y, and z dimension of each voxel, in millimetres. Not required if a seed, exclusion, waypoint or target file is given.

	-mintractpoints <minpoints>

		Streamlines that consist of fewer than minpoints will be discarded.

	-mintractlength <minlength>

		Streamlines are discarded if their length is less than minlength mm.

	-maxtractpoints <maxpoints>

		Streamlines that consist of more than maxpoints will be truncated to maxpoint in length. Specifying this option will automatically disable resampling of tracts.

	-maxtractlength <maxlength>

		Streamlines longer than maxlength mm will be truncated. This calculation is done before resampling, so the truncation is accurate to the original resolution of the tract.

	 
	SEED OPTIONS

	-seedpointmm <x> <y> <z>
		The coordinates of a single seed point for tractography, in mm.

	-seedpointvox <x> <y> <z>
		The voxel coordinates of a single seed point for tractography. Tracking will proceed from the centre of voxel (x,,y,x,z). This option overrides -seedpointmm. The voxel indices are numbered from 0 to (data dimension) - 1.

	-seedfile <file.[hdr | nii | mha | mhd]>
		Image containing seed points. If an output root is specified, the output is grouped according to the intensity of the seed in this image. This option overrides -seedpointvox and -seedpointmm.

	-regionindex <index>
		Process the specified region in the seed file.

	 
	OTHER OPTIONS

	-iterations
		Number of streamlines generated for each seed. Not required when outputting streamlines, but needed to create PICo images. The default is 1 if the output is streamlines, and 5000 if the output is connection probability images.

	-targetfile <file>
		Image containing target volumes. Targets are defined as regions of the image with the same intensity. If this option is given, the PICo maps will only localise connection probability to the volumes bounded by the targets. The connection probability to a target from a seed is the fraction of streamlines that pass anywhere within the target volume.

	-allowmultitargets
		Allows streamlines to connect to multiple target volumes. By default, the program only counts the first entry to a target volume.

	-directional <X> <Y> <Z>
		Splits the streamlines at the seed point and computes separate connection probabilities for each segment. Streamline segments are grouped according to their dot product with the vector (X, Y, Z). The ideal vector will be tangential to the streamline trajectory at the seed, such that the streamline projects from the seed along (X, Y, Z) and -(X, Y, Z). However, it is only necessary for the streamline trajectory to not be orthogonal to (X, Y, Z).

	-waypointfile <file.[hdr | nii | mha | mhd]>
		Image containing waypoints. Waypoints are defined as regions of the image with the same intensity, where 0 is background and any value > 0 is a waypoint. Streamlines are discarded if they do not pass through at least one voxel of each waypoint volume.

	-truncateloops
		This option allows streamlines to enter a waypoint exactly once. After the streamline leaves the waypoint, it is truncated upon a second entry to the waypoint. For the purposes of this operation, the streamline is divided into two segments at the seed point. Each segment is allowed to enter each waypoint once and the segment is truncated at a second entry.

	-discardloops
		This option allows streamlines to enter a waypoint exactly once. After the streamline leaves the waypoint, the entire streamline is discarded upon a second entry to the waypoint. For the purposes of this operation, the streamline is divided into two segments at the seed point. Each segment is allowed to enter each waypoint once and the entire streamline is discarded if either segment enters a waypoint twice.

	-exclusionfile <file.[hdr | nii | mha | mhd]>
		Image containing exclusion ROIs. This should be an Analyze 7.5 header / image file.hdr and file.img. By default, exclusion ROIs are treated as anti-waypoints - streamlines that enter any exclusion ROI are discarded. if the -truncateinexclusion option is given, streamlines are truncated upon entry to an exclusion ROI, but not discarded.

	-truncateinexclusion
		Retain segments of a streamline before entry to an exclusion ROI. If this is not specified, streamlines that enter an exclusion ROI are discarded.

	-endpointfile <file.[hdr | nii | mha | mhd]>
		Image containing endpoint ROIs. This should be an Analyze 7.5 header / image file.hdr and file.img. Endpoint ROIs are defined as regions of the image with the same intensity, where 0 is background and any value > 0 is an endpoint ROI. Streamlines are discarded if they do not connect two different endpoint ROIs.

	-resamplestepsize <size>
		Each point on a streamline is tested for entry into target, exclusion or waypoint volumes. If the length between points on a tract is not much smaller than the voxel length, then streamlines may pass through part of a voxel without being counted. To avoid this, the program resamples streamlines such that the step size is one tenth of the smallest voxel dimension in the image. This increases the size of raw or oogl streamline output and incurs some performance penalty. The resample resolution can be controlled with this option or disabled altogether by passing a negative step size or by passing the -noresample option.

	-noresample
		Disables resampling of input streamlines. Resampling is automatically disabled if the input model is voxels.

	 
	OUTPUT OPTIONS

	-gzip
		Compress output using the gzip algorithm.

	-outputtracts <format>

		Output streamlines, in one of the following formats: raw binary, voxels, or oogl. If neither -outputtracts nor -outputcp is specified, the default is to output raw tracts.

	-outputcp
		Output the connection probability map for each seed. The map is an Analyze image with data type float. If targets are specified, then the image values in each target voxel are the fraction of streamlines that connect to that target. Without targets, the image is the fraction of streamlines that connect to each voxel.

	-outputsc
		Output the connection probability map for each seed. The output is the same as with -outputcp except that the values are not normalized, so the image contains the raw streamline counts. The map is an Analyze image with data type int.

	-outputacm
		Combine all tracts in the input into a single connection probability map. Outputs a single Analyze image where each voxel contains the number of streamlines that enter the voxel. If -outputcp is also specified, the values are divided by the total number of streamlines in the input.

	-outputcbs
		Perform connectivity based segmentation. This option produces outputs. The first is
		 an image where each seed point in the ROI is labelled with the value of the target  to which the seed is most likely to connect. The second is an image where each seed point is labelled with the streamline count (default) or connection probability (if -outputcp is also specified) to the labelled target. A target file is required for this option.

	-outputroot <string>
		Prepended onto all output file names. If the output is streamlines, then using this option tells the program to separate streamlines by ROI. See track(1). 
	"""

	inputmodel = traits.Enum('raw', 'voxels', argstr='-inputmodel %s', desc='input model type (raw or voxels)', usedefault=True)    
	
	in_file = File(exists=True, argstr='%s',
					mandatory=True, position=1,
					desc='data file')
					
	maxtractpoints= traits.Int(argstr='-maxtractpoints %d', units='NA',
				desc="maximum number of tract points")
	mintractpoints= traits.Int(argstr='-mintractpoints %d', units='NA',
				desc="minimum number of tract points")
	maxtractpoints= traits.Int(argstr='-maxtractpoints %d', units='mm',
				desc="maximum length of tracts")
	mintractpoints= traits.Int(argstr='-mintractpoints %d', units='mm',
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

class procstreamlinesOutputSpec(TraitedSpec):
	"""OUTPUT OPTIONS

	-gzip
		Compress output using the gzip algorithm.

	-outputtracts <format>

		Output streamlines, in one of the following formats: raw binary, voxels, or oogl. If neither -outputtracts nor -outputcp is specified, the default is to output raw tracts.

	-outputcp
		Output the connection probability map for each seed. The map is an Analyze image with data type float. If targets are specified, then the image values in each target voxel are the fraction of streamlines that connect to that target. Without targets, the image is the fraction of streamlines that connect to each voxel.

	-outputsc
		Output the connection probability map for each seed. The output is the same as with -outputcp except that the values are not normalized, so the image contains the raw streamline counts. The map is an Analyze image with data type int.

	-outputacm
		Combine all tracts in the input into a single connection probability map. Outputs a single Analyze image where each voxel contains the number of streamlines that enter the voxel. If -outputcp is also specified, the values are divided by the total number of streamlines in the input.

	-outputcbs
		Perform connectivity based segmentation. This option produces outputs. The first is
		 an image where each seed point in the ROI is labelled with the value of the target  to which the seed is most likely to connect. The second is an image where each seed point is labelled with the streamline count (default) or connection probability (if -outputcp is also specified) to the labelled target. A target file is required for this option.

	-outputroot <string>
		Prepended onto all output file names. If the output is streamlines, then using this option tells the program to separate streamlines by ROI. See track(1). 
	"""

	outputfile = File(exists=True, argstr='-outputfile %s',
					mandatory=True, position=1,
					desc='output data file')
	
	outputtracts = traits.Enum('raw', 'voxels', 'oogl', argstr='-outputtracts %s', desc='output tract file type', usedefault=True)
	
	outputroot = File(exists=False, argstr='-outputroot %s',
					mandatory=False, position=1,
					desc='root directory for output')
					
	gzip = traits.Bool(argstr='-gzip', desc="save the output image in gzip format")
	outputcp = traits.Bool(argstr='-outputcp', desc="output the connection probability map (Analyze image, float)")
	outputsc = traits.Bool(argstr='-outputsc', desc="output the connection probability map (raw streamlines, int)")
	outputacm = traits.Bool(argstr='-outputacm', desc="output all tracts in a single connection probability map (Analyze image)")
	outputcbs = traits.Bool(argstr='-outputcbs', desc="outputs connectivity-based segmentation maps; requires target outputfile")
	out_file = File(exists=True, desc='path/name of 4D volume in voxel order') 

class procstreamlines(CaminoCommand):
	"""Use procstreamlines to perform postprocessing on tract files from track
	"""
	_cmd = 'procstreamlines'
	input_spec=procstreamlinesInputSpec
	output_spec=procstreamlinesOutputSpec
	
	def _list_outputs(self):
		out_prefix = self.inputs.out_prefix
		output_type = self.inputs.output_type
	
		outputs = self.output_spec().get()
		return outputs
	def _run_interface(self, runtime):
		if not isdefined(self.inputs.out_file):
		    self.inputs.out_file = self._gen_fname(self.inputs.in_file,suffix = '_tractpostproc')
		runtime = super(procstreamlines, self)._run_interface(runtime)
		if runtime.stderr:
		    runtime.returncode = 1
		return runtime

	def _gen_filename(self, name):
		if name is 'out_file':
		    return self._list_outputs()['tractpostproc']
		else:
		    return None

class conmapInputSpec(CaminoCommandInputSpec):
	in_file = File(exists=True, argstr='-inputfile %s',
					mandatory=True, position=1,
					desc='tract filename')
		
	roi_file = File(exists=True, argstr='-roifile %s',
					mandatory=True, position=2,
					desc='roi filename')
	
	index_file = File(exists=True, argstr='-indexfile %s',
					mandatory=False, position=3,
					desc='index filename (.txt)')
	
	label_file = File(exists=True, argstr='-labelfile %s',
					mandatory=False, position=4,
					desc='label filename (.txt)')
	
	threshold = traits.Int(argstr='-threshold %d', units='NA',
				desc="threshold indicates the minimum number of fiber connections that has to be drawn in the graph.")
		
class conmapOutputSpec(TraitedSpec):
	out_file = File(exists=False, desc='path/name of 4D volume in voxel order') 

	output_txt = File(exists=False, argstr='%s',
			mandatory=False, position=1,
			desc='connectivity matrix in text file')

	output_png = File(exists=False, argstr='%s',
			mandatory=False, position=1,
			desc='2D connectivity matrix in PNG image')

class conmap(CaminoCommand):
	_cmd = 'conmap'
	input_spec=conmapInputSpec
	output_spec=conmapOutputSpec
			
	def _list_outputs(self):
		out_prefix = self.inputs.out_prefix
		output_type = self.inputs.output_type
	
		outputs = self.output_spec().get()
		return outputs
	def _run_interface(self, runtime):
		if not isdefined(self.inputs.out_file):
		    self.inputs.out_file = self._gen_fname(self.inputs.in_file,suffix = '_conmap')
		runtime = super(conmap, self)._run_interface(runtime)
		if runtime.stderr:
		    runtime.returncode = 1
		return runtime
	
	def _gen_filename(self, name):
		if name is 'out_file':
		    return self._list_outputs()['conmap']
		else:
		    return None

class vtkstreamlinesInputSpec(CaminoCommandInputSpec):
	""" vtkstreamlines  [options]
	* Use vtkstreamlines to convert raw or voxel format streamlines to VTK polydata
	
	-colourorient
		Each point on the streamline is coloured by the local orientation. The colour coding scheme is the same as described in pdview(1).

	-scalarfile
		An Analyze image that is in the same physical space as the tracts. Each point of the streamline has the scalar value from the corresponding point in the image.

	-interpolatescalars, -interpolate
		With this option, the scalar value at each point on the streamline is calculated by trilinear interpolation. By default, nearest-neighbour interpolation is used. Smoothness of the scalar values may be increased by using this option and by running the streamlines through procstreamlines with resampling enabled.

	-seedfile
		Seed ROI used to generate the tracts, as defined in track(1).

	-targetfile
		An Analyze image containing integer-valued target regions, as defined in track(1).

	-voxeldims <x> <y> <z>
		The x, y, and z dimension of each voxel, in millimetres. Not required if any Analyze file is used.

	-inputmodel <model>
		One of the following:
		  raw - raw streamline data (default).
		  voxels - voxel lists. 
	"""

	inputmodel = traits.Enum('raw', 'voxels', argstr='-inputmodel %s', desc='input model type (raw or voxels)', usedefault=True)    
	
	in_file = File(exists=True, argstr='%s',
					mandatory=True, position=1,
					desc='data file')
										 
	voxeldims = traits.List(traits.Int, desc = 'voxel dimensions in mm',
				 argstr='-voxeldims %s', minlen=3, maxlen=3,
				 units='mm')
	
	seed_file = File(exists=False, argstr='-seedfile %s',
					mandatory=False, position=1,
					desc='image containing seed points')						 
	
	target_file = File(exists=False, argstr='-targetfile %s',
					mandatory=False, position=1,
					desc='image containing integer-valued target regions')						 
	
	scalar_file = File(exists=False, argstr='-scalarfile %s',
					mandatory=False, position=1,
					desc='image that is in the same physical space as the tracts')
					
	colourorient = traits.Bool(argstr='-colourorient', desc="Each point on the streamline is coloured by the local orientation.")
	interpolatescalars = traits.Bool(argstr='-interpolatescalars', desc="the scalar value at each point on the streamline is calculated by trilinear interpolation")
	interpolate = traits.Bool(argstr='-interpolate', desc="the scalar value at each point on the streamline is calculated by trilinear interpolation")

class vtkstreamlinesOutputSpec(TraitedSpec):
	"""Use vtkstreamlines to convert raw or voxel format streamlines to VTK polydata
	"""
	out_file = File(exists=True, desc='path/name of 4D volume in voxel order') 
    
class vtkstreamlines(CaminoCommand):
	"""Use vtkstreamlines to convert raw or voxel format streamlines to VTK polydata
	"""
		
	_cmd = 'vtkstreamlines'
	input_spec=vtkstreamlinesInputSpec
	output_spec=vtkstreamlinesOutputSpec

	def _list_outputs(self):
		out_prefix = self.inputs.out_prefix
		output_type = self.inputs.output_type
	
		outputs = self.output_spec().get()
		return outputs
	def _run_interface(self, runtime):
		if not isdefined(self.inputs.out_file):
		    self.inputs.out_file = self._gen_fname(self.inputs.in_file,suffix = '_vtk')
		runtime = super(vtkstreamlines, self)._run_interface(runtime)
		if runtime.stderr:
		    runtime.returncode = 1
		return runtime

	def _gen_filename(self, name):
		if name is 'out_file':
		    return self._list_outputs()['vtk']
		else:
		    return None