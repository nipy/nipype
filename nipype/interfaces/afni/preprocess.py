__docformat__ = 'restructuredtext'
import warnings
import os
import nibabel as nb
import numpy as np
from string import Template
from nipype.utils.filemanip import split_filename
from nipype.interfaces.matlab import MatlabCommand
from nipype.interfaces.base import BaseInterface, BaseInterfaceInputSpec
from nipype.interfaces.afni.base import AFNITraitedSpec, AFNICommand, Info
from nipype.interfaces.base import Bunch, TraitedSpec, File, Directory, traits, isdefined
from nipype.interfaces.base import (CommandLineInputSpec, CommandLine, TraitedSpec, traits, isdefined, File)
from nipype.utils.filemanip import load_json, save_json, split_filename, fname_presuffix
warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class AFNICommandGenFile(AFNICommand):
	def _gen_fname(self, basename, cwd=None, suffix=None, change_ext=True, ext=None):
"""Generate a filename based on the given parameters.

The filename will take the form: cwd/basename<suffix><ext>.
If change_ext is True, it will use the extensions specified in
<instance>inputs.outputtype.

Parameters
----------
basename : str
Filename to base the new filename on.
cwd : str
Path to prefix to the new filename. (default is os.getcwd())
suffix : str
Suffix to add to the `basename`. (default is '')
change_ext : bool
Flag to change the filename extension to the AFNI output type.
(default True)

Returns
-------
fname : str
New filename based on given parameters.

"""

		if basename == '':
			msg = 'Unable to generate filename for command %s. ' % self.cmd
			msg += 'basename is not set!'
			raise ValueError(msg)
        
		if cwd is None:
			cwd = os.getcwd()
        
		if ext is None:
			ext = Info.outputtype_to_ext(self.inputs.outputtype)

		if change_ext:
			if suffix:
				suffix = ''.join((suffix, ext))
			else:
				suffix = ext
 
		if suffix is None:
			suffix = ''

		fname = fname_presuffix(basename, suffix = suffix,
					use_ext = False, newpath = cwd)
        	
		return fname
        
	def _gen_filename(self, name):
		if name == 'out_file':
			return self._gen_outfilename()
		return None


class To3dInputSpec(AFNITraitedSpec):
	infolder = Directory(desc = 'folder with DICOM images to convert',
		argstr = '%s/*.dcm',
		position = -1,
		mandatory = True,
		exists = True)
	
	outfile = File(desc = 'converted image file',
		argstr = '-prefix %s',
		position = -2,
		mandatory = True)

	filetype = traits.Enum('spgr', 'fse', 'epan', 'anat', 'ct', 'spct','pet', 'mra', 'bmap', 'diff',
		'omri', 'abuc','fim', 'fith', 'fico', 'fitt', 'fift','fizt', 'fict', 'fibt',
		'fibn','figt','fipt','fbuc', argstr = '-%s', desc='type of datafile being converted')

	'''use xor'''
	skipoutliers = traits.Bool(desc = 'skip the outliers check',
		argstr = '-skip_outliers')

	assumemosaic = traits.Bool(desc = 'assume that Siemens image is mosaic',
		argstr = '-assume_dicom_mosaic')
    

	datatype = traits.Enum('short', 'float', 'byte', 'complex', desc = 'set output file datatype',
		argstr = '-datum %s')

	funcparams = traits.Str(desc = 'parameters for functional data',
		argstr = '-time:zt %s alt+z2')


class To3dOutputSpec(TraitedSpec):
	out_file = File(desc = 'converted file',
		exists = True)

class To3d(AFNICommand):
"""Create a 3D dataset from 2D image files using AFNI to3d command.

For complete details, see the `to3d Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/to3d.html>`_

To print out the command line help, use:
To3d().inputs_help()

Examples
--------
>>> from nipype.interfaces import afni
>>> to3d = afni.To3d()
AFNI has no environment variable that sets filetype
Nipype uses NIFTI_GZ as default
>>> to3d.inputs.datatype = 'float'
>>> to3d.inputs.infolder='dicomdir'
>>> to3d.inputs.filetype="anat"
>>> res = to3d.run() #doctest: +SKIP

"""

	_cmd = 'to3d'
	input_spec = To3dInputSpec
	output_spec = To3dOutputSpec

	def _list_outputs(self):
		outputs = self.output_spec().get()
		outputs['out_file'] = self.inputs.outfile
		return outputs


class ThreedTshiftInputSpec(AFNITraitedSpec):
	in_file = File(desc = 'input file to 3dTShift',
		argstr = '%s',
		position = -1,
		mandatory = True,
		exists = True)
	out_file = File(desc = 'output file from 3dTshift',
		argstr = '-prefix %s',
		position = 0,
		genfile = True)

	tr = traits.Str(desc = 'manually set the TR instead of looking in the header. ' +
		'You can attach suffix "s" for seconds or "ms" for milliseconds.',
		argstr = '-TR %s')

	tzero = traits.Float(desc = 'align each slice to given time offset',
		argstr = '-tzero %s',
		xor = ['tslice'])
    
	tslice = traits.Int(desc = 'align each slice to time offset of given slice',
		argstr = '-slice %s',
		xor = ['tzero'])
    
	ignore = traits.Int(desc = 'ignore the first set of points specified',
		argstr = '-ignore %s')

	interp = traits.Enum(('Fourier', 'linear', 'cubic', 'quintic', 'heptic'),
		desc='different interpolation methods (see 3dTShift for details)' +
		' default=Fourier', argstr='-%s')

	tpattern = traits.Enum(('alt+z', 'alt+z2', 'alt-z', 'alt-z2', 'seq+z', 'seq-z'),
		desc='use specified slice time pattern rather than one in header',
		argstr='-tpattern %s')
    
	rlt = traits.Bool(desc='Before shifting, remove the mean and linear trend',
		argstr="-rlt")
    
	rltplus = traits.Bool(desc='Before shifting, remove the mean and linear trend and ' +
		'later put back the mean',
		argstr="-rlt+")

	suffix = traits.Str(desc="out_file suffix") # todo: give it a default-value


class ThreedTshiftOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'post slice time shifted 4D image')
    

class ThreedTshift(AFNICommand):
"""Shifts voxel time series from input so that seperate slices are aligned to the same
temporal origin.
For complete details, see the `3dTshift Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTshift.html>`_
"""
    
	_cmd = '3dTshift'
	input_spec = ThreedTshiftInputSpec
	output_spec = ThreedTshiftOutputSpec
    
	def _gen_filename(self, name):
		if name == 'out_file':
			return self._list_outputs()[name]
		return None
    
	def _list_outputs(self):
		outputs = self.output_spec().get()
		outputs['out_file'] = self.inputs.out_file
		if not isdefined(outputs['out_file']):

			if isdefined(self.inputs.suffix):
				suffix = self.inputs.suffix
			else:
				suffix = "_tshift"
		outputs['out_file'] = self._gen_fname(self.inputs.in_file, suffix=suffix)
		return outputs
    

class ThreedrefitInputSpec(AFNITraitedSpec):
	in_file = File(desc = 'input file to 3drefit',
		argstr = '%s',
		position = -1,
		mandatory = True,
		exists = True,
		copyfile = True)
    
	deoblique = traits.Bool(desc = 'replace current transformation matrix with cardinal matrix',
		argstr = '-deoblique')

	xorigin = traits.Str(desc = 'x distance for edge voxel offset',
		argstr = '-xorigin %s')

	yorigin = traits.Str(desc = 'y distance for edge voxel offset',
		argstr = '-yorigin %s')
	zorigin = traits.Str(desc = 'z distance for edge voxel offset',
		argstr = '-zorigin %s')

class ThreedrefitOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'Same file as original infile with modified matrix',
		exists = True)

class Threedrefit(AFNICommand):
""" Use 3drefit for altering header info.
NOTES
-----
The original file is returned but it is CHANGED
"""
    
	_cmd = '3drefit'
	input_spec = ThreedrefitInputSpec
	output_spec = ThreedrefitOutputSpec
    
	def _list_outputs(self):
		outputs = self.output_spec().get()
		outputs['out_file'] = self.inputs.in_file
		return outputs
    

class ThreedWarpInputSpec(AFNITraitedSpec):

	in_file = File(desc = 'input file to 3dWarp',
		argstr = '%s',
		position = -1,
		mandatory = True,
		exists = True)

	out_file = File(desc = 'output file from 3dWarp',
		argstr = '-prefix %s',
		position = 0,
		genfile = True)

	tta2mni = traits.Bool(desc = 'transform dataset from Talairach to MNI152',
		argstr = '-tta2mni')
    
	mni2tta = traits.Bool(desc = 'transform dataset from MNI152 to Talaraich',
		argstr = '-mni2tta')

	matparent = File(desc = "apply transformation from 3dWarpDrive",
		argstr = "-matparent %s",
		exists = True)
    
	deoblique = traits.Bool(desc = 'transform dataset from oblique to cardinal',
		argstr = '-deoblique')
    
	interp = traits.Enum(('linear', 'cubic', 'NN', 'quintic'),
		desc='spatial interpolation methods [default=linear]',
		argstr='-%s')
    
	gridset = File(desc = "copy grid of specified dataset",
		argstr = "-gridset %s",
		exists = True)
    
	zpad = traits.Int(desc="pad input dataset with N planes of zero on all sides.",
		argstr="-zpad %s")
    
	suffix = traits.Str(desc="out_file suffix") # todo: give it a default-value

class ThreedWarpOutputSpec(AFNITraitedSpec):
    out_file = File(desc = 'spatially transformed input image', exists=True)

class ThreedWarp(AFNICommand):
""" Use 3dWarp for spatially transforming a dataset
For complete details, see the `3dTshift Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dWarp.html>`_
"""
    
	_cmd = '3dWarp'
	input_spec = ThreedWarpInputSpec
	output_spec = ThreedWarpOutputSpec
    
	def _gen_filename(self, name):
		if name == 'out_file':
			return self._list_outputs()[name]
		return None
    
	def _list_outputs(self):
		outputs = self.output_spec().get()
		outputs['out_file'] = self.inputs.out_file
 		if not isdefined(outputs['out_file']):
			if isdefined(self.inputs.suffix):
				suffix = self.inputs.suffix
			else:
				suffix = "_warp"
		outputs['out_file'] = self._gen_fname(self.inputs.in_file, suffix=suffix)
		return outputs

    

class ThreedresampleInputSpec(AFNITraitedSpec):
    
	in_file = File(desc = 'input file to 3dresample',
		argstr = '-inset %s',
		position = -1,
		mandatory = True,
		exists = True)
    
	out_file = File(desc = 'output file from 3dresample',
		argstr = '-prefix %s',
		position = -2,
		genfile = True)
    
	orientation = traits.Str(desc = 'new orientation code',
		argstr = '-orient %s')

	suffix = traits.Str(desc="out_file suffix") # todo: give it a default-value

class ThreedresampleOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'reoriented or resampled file',
		exists = True)

class Threedresample(AFNICommand):
    """Resample or reorient an image using AFNI 3dresample command.
For complete details, see the `3dresample Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dresample.html>`_
"""
    
	_cmd = '3dresample'
	input_spec = ThreedresampleInputSpec
	output_spec = ThreedresampleOutputSpec
    
	def _gen_filename(self, name):
		if name == 'out_file':
			return self._list_outputs()[name]
		return None
    
	def _list_outputs(self):
		outputs = self.output_spec().get()
		outputs['out_file'] = self.inputs.out_file
		if not isdefined(outputs['out_file']):
			if isdefined(self.inputs.suffix):
				suffix = self.inputs.suffix
			else:
				suffix = [] # allow for resampling command later!
				if self.inputs.orientation:
					suffix.append("_RPI")
				suffix = "".join(suffix)
		outputs['out_file'] = self._gen_fname(self.inputs.in_file, suffix=suffix)
        	return outputs
    

class ThreedTstatInputSpec(AFNITraitedSpec):
	in_file = File(desc = 'input file to 3dTstat',
		argstr = '%s',
		position = -1,
		mandatory = True,
		exists = True)

	out_file = File(desc = 'output file from 3dTstat',
		argstr = '-prefix %s',
		position = -2,
		genfile = True)

	options = traits.Str(desc = 'selected statistical output',
		argstr = '%s')

class ThreedTstatOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'statistical file',
		exists = True)

class ThreedTstat(AFNICommand):
"""Compute voxel-wise statistics using AFNI 3dTstat command.

For complete details, see the `3dTstat Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTstat.html>`_
"""

	_cmd = '3dTstat'
	input_spec = ThreedTstatInputSpec
	output_spec = ThreedTstatOutputSpec

	def _gen_filename(self, name):
	"""Generate output file name
	"""
        
		if name == 'out_file':
			_, fname, ext = split_filename(self.inputs.in_file)
			return os.path.join(os.getcwd(), ''.join((fname, '_3dT',ext)))
    

	def _list_outputs(self):
		outputs = self.output_spec().get()
		#outputs['out_file'] = os.path.abspath(self.inputs.out_file)
		if not isdefined(self.inputs.out_file):
			outputs['out_file'] = self._gen_filename('out_file')
		else:
			outputs['out_file'] = os.path.abspath(self.inputs.out_file)
		return outputs


class ThreedDetrendInputSpec(AFNITraitedSpec):
	in_file = File(desc = 'input file to 3dDetrend',
		argstr = '%s',
		position = -1,
		mandatory = True,
		exists = True)
	out_file = File(desc = 'output file from 3dTstat',
 		argstr = '-prefix %s',
 		position = -2,
 		genfile = True)
	options = traits.Str(desc = 'selected statistical output',
		argstr = '%s')

class ThreedDetrendOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'statistical file',
		exists = True)

class ThreedDetrend(AFNICommand):
"""Compute voxel-wise statistics using AFNI 3dTstat command.

For complete details, see the `3dTstat Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTstat.html>`_
"""

	_cmd = '3dDetrend'
	input_spec = ThreedDetrendInputSpec
	output_spec = ThreedDetrendOutputSpec


	def _gen_filename(self, name):
        """Generate output file name
	"""
        
	if name == 'out_file':
		_, fname, ext = split_filename(self.inputs.in_file)
		return os.path.join(os.getcwd(), ''.join((fname, '_3dD',ext)))


	def _list_outputs(self):
		outputs = self.output_spec().get()
		#outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        
		if not isdefined(self.inputs.out_file):
			outputs['out_file'] = self._gen_filename('out_file')
		else:
			outputs['out_file'] = os.path.abspath(self.inputs.out_file)
		return outputs


class ThreedDespikeInputSpec(AFNITraitedSpec):
	in_file = File(desc = 'input file to 3dDespike',
		argstr = '%s',
		position = -1,
		mandatory = True,
		exists = True)

	out_file = File(desc = 'output file from 3dDespike',
 		argstr = '-prefix %s',
 		position = -2,
 		genfile = True)

	options = traits.Str(desc = 'additional args',
		argstr = '%s')

class ThreedDespikeOutputSpec(AFNITraitedSpec):
    out_file = File(desc = 'despiked img',
    		   exists = True)

class ThreedDespike(AFNICommand):
"""Compute voxel-wise statistics using AFNI 3dTstat command.

For complete details, see the `3dDespike Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDespike.html>`_
"""

	_cmd = '3dDespike'
	input_spec = ThreedDespikeInputSpec
	output_spec = ThreedDespikeOutputSpec

	def _gen_filename(self, name):
        """Generate output file name
	"""
		if name == 'out_file':
			_, fname, ext = split_filename(self.inputs.in_file)
			return os.path.join(os.getcwd(), ''.join((fname, '_3dDe',ext)))

	def _list_outputs(self):
		outputs = self.output_spec().get()
		#outputs['out_file'] = os.path.abspath(self.inputs.out_file)

		if not isdefined(self.inputs.out_file):
			outputs['out_file'] = self._gen_filename('out_file')
		else:
			outputs['out_file'] = os.path.abspath(self.inputs.out_file)
		return outputs

class ThreedAutomaskInputSpec(AFNITraitedSpec):
	in_file = File(desc = 'input file to 3dAutomask',
		argstr = '%s',
		position = -1,
		mandatory = True,
		exists = True)
    
	out_file = File(desc = 'output file from 3dAutomask (a brain mask)',
		argstr = '-prefix %s',
		position = -2,
		genfile = True)
    
	apply_mask = File(desc = "output file from 3dAutomask (masked version of input dataset)",
		argstr = '-apply_prefix %s')
    
	clfrac = traits.Float(desc = 'sets the clip level fraction (must be 0.1-0.9). ' +
		'A small value will tend to make the mask larger [default=0.5].',
		argstr = "-dilate %s")
    
	dilate = traits.Int(desc = 'dilate the mask outwards',
		argstr = "-dilate %s")
    
	erode = traits.Int(desc = 'erode the mask inwards',
		argstr = "-erode %s")
    
	options = traits.Str(desc = 'automask settings',
		argstr = '%s')
    
	suffix = traits.Str(desc="out_file suffix") # todo: give it a default-value

class ThreedAutomaskOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'mask file',
		exists = True)
    
	brain_file = File(desc = 'brain file (skull stripped)',
		exists = True)

class ThreedAutomask(AFNICommand):
"""Create a brain-only mask of the image using AFNI 3dAutomask command.
For complete details, see the `3dAutomask Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAutomask.html>`_
"""
    
	_cmd = '3dAutomask'
	input_spec = ThreedAutomaskInputSpec
	output_spec = ThreedAutomaskOutputSpec
    
	def _gen_filename(self, name):
		if name == 'out_file':
			return self._list_outputs()[name]
		return None
    
    
	def _list_outputs(self):
		outputs = self.output_spec().get()
		outputs['brain_file'] = self.inputs.apply_mask
		outputs['out_file'] = self.inputs.out_file
        
		if not isdefined(outputs['out_file']):
			if isdefined(self.inputs.suffix):
				suffix = self.inputs.suffix
			else:
				suffix = "_automask"
            
		outputs['out_file'] = self._gen_fname(self.inputs.in_file, suffix=suffix)
	return outputs
    

class ThreedvolregInputSpec(AFNITraitedSpec):
    
	in_file = File(desc = 'input file to 3dvolreg',
		argstr = '%s',
		position = -1,
		mandatory = True,
		exists = True)
	out_file = File(desc = 'output file from 3dvolreg',
 		argstr = '-prefix %s',
 		position = -2,
 		genfile = True)
	basefile = File(desc = 'base file for registration',
  		argstr = '-base %s',
  		position = -6)
	zpad = File(desc = 'Zeropad around the edges by \'n\' voxels during rotations',
  		argstr = '-zpad %s',
  		position = -5)
	md1dfile = File(desc = 'max displacement output file',
  		argstr = '-maxdisp1D %s',
  		position = -4)
	oned_file = File(desc = '1D movement parameters output file',
  		argstr = '-1Dfile %s',
  		position = -3,
		genfile = True)
	verbose = traits.Bool(desc = 'more detailed description of the process',
		argstr = '-verbose')
	timeshift = traits.Bool(desc = 'time shift to mean slice time offset',
		argstr = '-tshift 0')
	copyorigin = traits.Bool(desc = 'copy base file origin coords to output',
		argstr = '-twodup')
	other = traits.Str(desc = 'other options',
		argstr = '%s')

class ThreedvolregOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'registered file',
		exists = True)
	md1d_file = File(desc = 'max displacement info file')
	oned_file = File(desc = 'movement parameters info file')

class Threedvolreg(AFNICommand):
"""Register input volumes to a base volume using AFNI 3dvolreg command.

For complete details, see the `3dvolreg Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dvolreg.html>`_
"""

	_cmd = '3dvolreg'
	input_spec = ThreedvolregInputSpec
	output_spec = ThreedvolregOutputSpec

	def _gen_filename(self, name):
        """Generate output file name
	"""
		if name == 'out_file':
			_, fname, ext = split_filename(self.inputs.in_file)
			return os.path.join(os.getcwd(), ''.join((fname, '_3dv',ext)))
    
        
		if name == 'oned_file':
			_, fname, ext = split_filename(self.inputs.in_file)
			return os.path.join(os.getcwd(), ''.join((fname, '_3dv1D','.1D')))
    
    
	def _list_outputs(self):
		outputs = self.output_spec().get()
#		outputs['out_file'] = os.path.abspath(self.inputs.out_file)
#		outputs['oned_file'] = os.path.abspath(self.inputs.oned_file)
        
		if not isdefined(self.inputs.out_file):
			outputs['out_file'] = self._gen_filename('out_file')
		else:
			outputs['out_file'] = os.path.abspath(self.inputs.out_file)

        
		if not isdefined(self.inputs.oned_file):
			outputs['oned_file'] = self._gen_filename('oned_file')
		else:
			outputs['oned_file'] = os.path.abspath(self.inputs.oned_file)
        
		return outputs


class ThreedmergeInputSpec(AFNITraitedSpec):
	infile = File(desc = 'input file to 3dvolreg',
		argstr = '%s',
		position = -1,
		mandatory = True,
		exists = True)
	outfile = File(desc = 'output file from 3dvolreg',
 		argstr = '-prefix %s',
 		position = -2,
 		mandatory = True)
	doall = traits.Bool(desc = 'apply options to all sub-bricks in dataset',
		argstr = '-doall')
	blurfwhm = traits.Int(desc = 'FWHM blur value (mm)',
  		argstr = '-1blur_fwhm %d',
  		units = 'mm')
	other = traits.Str(desc = 'other options',
 		argstr = '%s')

class ThreedmergeOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'smoothed file',
		exists = True)

class Threedmerge(AFNICommand):
"""Merge or edit volumes using AFNI 3dmerge command.

For complete details, see the `3dmerge Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dmerge.html>`_
"""

	_cmd = '3dmerge'
	input_spec = ThreedmergeInputSpec
	output_spec = ThreedmergeOutputSpec

	def _list_outputs(self):
		outputs = self.output_spec().get()
		outputs['out_file'] = self.inputs.outfile
		return outputs


class ThreedcopyInputSpec(AFNITraitedSpec):
	in_file = File(desc = 'input file to 3dcopy',
		argstr = '%s',
		position = -2,
		mandatory = True,
		exists = True)
	out_file = File(desc = 'output file from 3dcopy',
		argstr = '%s',
		position = -1,
		genfile = True)

class ThreedcopyOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'copied file')

class Threedcopy(AFNICommandGenFile):
"""Copies an image of one type to an image of the same or different type
using 3dcopy command."""
    
	_cmd = '3dcopy'
	input_spec = ThreedcopyInputSpec
	output_spec = ThreedcopyOutputSpec
    
	def _list_outputs(self):
		outputs = self.output_spec().get()
		outputs['out_file'] = self._gen_outfilename()
		return outputs
    
	def _gen_outfilename(self):
		out_file = self.inputs.out_file
		if not isdefined(out_file) and isdefined(self.inputs.in_file):
			out_file = self._gen_fname(self.inputs.in_file, suffix="_copy")
		return out_file



class ThreedFourierInputSpec(AFNITraitedSpec):
	in_file = File(desc = 'input file to 3dFourier',
		argstr = '%s',
		position = -1,
		mandatory = True,
		exists = True)
	out_file = File(desc = 'output file from 3dFourier',
 		argstr = '-prefix %s',
 		position = -2,
 		genfile = True)
	lowpass = traits.Float(desc = 'lowpass',
		argstr = '-lowpass %f',
		position = 0,
		mandatory = True)
	highpass = traits.Float(desc = 'highpass',
		argstr = '-highpass %f',
		position = 1,
		mandatory = True)
	other = traits.Str(desc = 'other options',
		argstr = '%s')

class ThreedFourierOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'band-pass filtered file',
		exists = True)

class ThreedFourier(AFNICommand):
"""Merge or edit volumes using AFNI 3dmerge command.

For complete details, see the `3dmerge Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dmerge.html>`_
"""

	_cmd = '3dFourier'
	input_spec = ThreedFourierInputSpec
	output_spec = ThreedFourierOutputSpec

	def _gen_filename(self, name):
        """Generate output file name
	"""
	if name == 'out_file':
    		_, fname, ext = split_filename(self.inputs.in_file)
    		return os.path.join(os.getcwd(), ''.join((fname, '_3dF',ext)))
	def _list_outputs(self):
		outputs = self.output_spec().get()
		#outputs['out_file'] = os.path.abspath(self.inputs.out_file)

		if not isdefined(self.inputs.out_file):
			outputs['out_file'] = self._gen_filename('out_file')
		else:
			outputs['out_file'] = os.path.abspath(self.inputs.out_file)
		return outputs


class ThreedZcutupInputSpec(AFNITraitedSpec):
	infile = File(desc = 'input file to 3dZcutup',
		argstr = '%s',
		position = -1,
		mandatory = True,
		exists = True)
	outfile = File(desc = 'output file from 3dZcutup',
 		argstr = '-prefix %s',
 		position = -2,
 		mandatory = True)
	keep = traits.Str(desc = 'slice range to keep in output',
    		argstr = '-keep %s')
	other = traits.Str(desc = 'other options',
       		argstr = '%s')

class ThreedZcutupOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'cut file',
		exists = True)

class ThreedZcutup(AFNICommand):
"""Cut z-slices from a volume using AFNI 3dZcutup command.

For complete details, see the `3dZcutup Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dZcutup.html>`_
"""

	_cmd = '3dZcutup'
	input_spec = ThreedZcutupInputSpec
	output_spec = ThreedZcutupOutputSpec

	def _list_outputs(self):
		outputs = self.output_spec().get()
		outputs['out_file'] = self.inputs.outfile
		return outputs


class ThreedAllineateInputSpec(AFNITraitedSpec):
	infile = File(desc = 'input file to 3dAllineate',
		argstr = '-source %s',
		position = -1,
		mandatory = True,
		exists = True)
	outfile = File(desc = 'output file from 3dAllineate',
 		argstr = '-prefix %s',
 		position = -2,
 		mandatory = True)
	matrix = File(desc = 'matrix to align input file',
		argstr = '-1dmatrix_apply %s',
		position = -3)

class ThreedAllineateOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'cut file',
  		exists = True)

class ThreedAllineate(AFNICommand):
"""
For complete details, see the `3dAllineate Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAllineate.html>`_
"""

	_cmd = '3dAllineate'
	input_spec = ThreedAllineateInputSpec
	output_spec = ThreedAllineateOutputSpec

	def _list_outputs(self):
		outputs = self.output_spec().get()
        	outputs['out_file'] = self.inputs.outfile
        	return outputs


class ThreedMaskaveInputSpec(AFNITraitedSpec):
	in_file = File(desc = 'input file to 3dmaskave',
		argstr = '%s',
		position = -2,
		mandatory = True,
		exists = True)
	out_file = File(desc = 'output to the file',
 		argstr = '> %s',
 		position = -1,
 		genfile = True)
	mask = File(desc = 'matrix to align input file',
		argstr = '-mask %s',
		position = 1)

	quiet = traits.Bool(desc = 'matrix to align input file',
		argstr = '-quiet',
		position = 2)


class ThreedMaskaveOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'outfile',
  		exists = True)

class ThreedMaskave(AFNICommand):
"""
For complete details, see the `3dmaskave Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dmaskave.html>`_
"""

	_cmd = '3dmaskave'
	input_spec = ThreedMaskaveInputSpec
	output_spec = ThreedMaskaveOutputSpec

	def _list_outputs(self):
		outputs = self.output_spec().get()
		if not isdefined(self.inputs.out_file):
			out_file = self._gen_filename('out_file')
		else:
			out_file = os.path.abspath(self.inputs.out_file)
		outputs['out_file'] = out_file
		return outputs

	def _gen_filename(self, name):
        """Generate output file name
	"""
		if name == 'out_file':
			_, fname, ext = split_filename(self.inputs.in_file)
			return os.path.join(os.getcwd(), ''.join((fname, '_3dm','.1D')))

class ThreedSkullStripInputSpec(AFNITraitedSpec):
	in_file = File(desc = 'input file to 3dSkullStrip',
		argstr = '-input %s',
		position = 1,
		mandatory = True,
		exists = True)
	out_file = File(desc = 'output to the file',
 		argstr = '%s',
 		position = -1,
		genfile = True)
	options = traits.Str(desc = 'options', argstr = '%s', position = 2)



class ThreedSkullStripOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'outfile',
		exists = True)

class ThreedSkullStrip(AFNICommandGenFile):

	_cmd = '3dSkullStrip'
	input_spec = ThreedSkullStripInputSpec
	output_spec = ThreedSkullStripOutputSpec

	def _list_outputs(self):
		outputs = self.output_spec().get()
		outputs['out_file'] = self._gen_outfilename()
		return outputs

	def _gen_outfilename(self):
		out_file = self.inputs.out_file
		
		if not isdefined(out_file) and isdefined(self.inputs.in_file):
			out_file = self._gen_fname(self.inputs.in_file, suffix="_surf")
			#out_file = self._gen_fname(self.inputs.in_file, suffix="_surf")
		return out_file
	

class ThreedTcatInputSpec(AFNITraitedSpec):
	in_file = File(desc = 'input file to 3dTcat',
		argstr = ' %s',
		position = -1,
		mandatory = True,
		exists = True)
	out_file = File(desc = 'output to the file',
 		argstr = '-prefix %s',
 		position = -2,
 		genfile = True)
	rlt = traits.Str(desc = 'options', argstr = '-rlt%s', position = 1)



class ThreedTcatOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'outfile',
		exists = True)

class ThreedTcat(AFNICommand):
"""
For complete details, see the `3dTcat Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTcat.html>`_
"""

	_cmd = '3dTcat'
	input_spec = ThreedTcatInputSpec
	output_spec = ThreedTcatOutputSpec

	def _list_outputs(self):
		outputs = self.output_spec().get()
		if not isdefined(self.inputs.out_file):
			out_file = self._gen_filename('out_file')
		else:
			out_file = os.path.abspath(self.inputs.out_file)
	
		outputs['out_file'] = out_file
		return outputs


	def _gen_filename(self, name):
        """Generate output file name
	"""
		if name == 'out_file':
			_, fname, ext = split_filename(self.inputs.in_file)
		return os.path.join(os.getcwd(), ''.join((fname, '_3dT',ext)))


class ThreedfimInputSpec(AFNITraitedSpec):
	in_file = File(desc = 'input file to 3dfim+',
		argstr = ' -input %s',
		position = 1,
		mandatory = True,
		exists = True)
	ideal_file = File(desc = 'output to the file',
 		argstr = '-ideal_file %s',
 		position = 2,
 		mandatory = True)
	fim_thr = traits.Float(desc = 'fim internal mask threshold value', argstr = '-fim_thr %f', position = 3)

	out = traits.Str(desc = 'Flag to output the specified parameter', argstr = '-out %s', position = 4)

	out_file = File(desc = 'output file from 3dfim+', argstr = '-bucket %s',
  		position = -1, genfile=True)


class ThreedfimOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'outfile',
		exists = True)

class Threedfim(AFNICommand):
"""
For complete details, see the `3dfim+ Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dfim+.html>`_
"""

	_cmd = '3dfim+'
	input_spec = ThreedfimInputSpec
	output_spec = ThreedfimOutputSpec

	def _list_outputs(self):
		outputs = self.output_spec().get()
        
		if not isdefined(self.inputs.out_file):
			out_file = self._gen_filename('out_file')
		else:
			out_file = os.path.abspath(self.inputs.out_file)
	
		outputs['out_file'] = out_file
		return outputs

	def _gen_filename(self, name):
        """Generate output file name
	"""
		if name == 'out_file':
			_, fname, ext = split_filename(self.inputs.in_file)
			return os.path.join(os.getcwd(), ''.join((fname, '_3df',ext)))



class ThreedTcorrelateInputSpec(AFNITraitedSpec):
	xset = File(desc = 'input xset',
		argstr = ' %s',
		position = -2,
		mandatory = True,
		exists = True)
	yset = File(desc = 'input yset',
		argstr = ' %s',
		position = -1,
		mandatory = True,
		exists = True)
	pearson = traits.Bool(desc = 'Correlation is the normal Pearson correlation coefficient',
		argstr = '-pearson',
		position = 1)
	polort = traits.Int(desc = 'Remove polynomical trend of order m', argstr = '-polort %d', position = 2)

	out_file = File(desc = 'Save output into dataset with prefix ', argstr = '-prefix %s',
		position = 3, genfile=True)

	options = traits.Str(desc = 'other options',
		argstr = '%s', position = 4)


class ThreedTcorrelateOutputSpec(AFNITraitedSpec):
	out_file = File(desc = 'outfile',
		exists = True)

class ThreedTcorrelate(AFNICommand):
"""
For complete details, see the `3dfim+ Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dfim+.html>`_
"""

	_cmd = '3dTcorrelate'
	input_spec = ThreedTcorrelateInputSpec
	output_spec = ThreedTcorrelateOutputSpec

	def _list_outputs(self):
		outputs = self.output_spec().get()
		outputs['out_file'] = os.path.abspath(self.inputs.out_file)
		if not isdefined(outputs['out_file']):
			outputs['out_file'] = self._gen_filename('out_file')
		return outputs

	def _gen_filename(self, name):
	"""Generate output file name
	"""
        if name == 'out_file':
            _, fname, ext = split_filename(self.inputs.xset)
            return os.path.join(os.getcwd(), ''.join((fname, '_3dTcor',ext)))



class ThreedBrickStatInputSpec(AFNITraitedSpec):
	in_file = File(desc = 'input file to 3dmaskave',
		argstr = '%s',
		position = -1,
		mandatory = True,
		exists = True)

	mask = File(desc = '-mask dset = use dset as mask to include/exclude voxels',
		argstr = '-mask %s',
		position = 2)

	min = traits.Bool(desc = 'print the minimum value in dataset',
		argstr = '-min',
		position = 1)


class ThreedBrickStatOutputSpec(AFNITraitedSpec):
	min_val = traits.Float(desc = 'output')

class ThreedBrickStat(AFNICommand):
	_cmd = '3dBrickStat'
	input_spec = ThreedBrickStatInputSpec
	output_spec = ThreedBrickStatOutputSpec

	def aggregate_outputs(self,runtime = None,  needed_outputs=None):

		outputs = self._outputs()

		outfile = os.path.join(os.getcwd(),'stat_result.json')

		if runtime is None:
			try:
				min_val = load_json(outfile)['stat']
			except IOError:
				return self.run().outputs
		else:
			min_val = []
			for line in runtime.stdout.split('\n'):
				if line:
					values = line.split()
					if len(values) > 1:
						min_val.append([float(val) for val in values])
					else:
						min_val.extend([float(val) for val in values])

			if len(min_val) == 1:
				min_val = min_val[0]
			save_json(outfile,dict(stat=min_val))
		outputs.min_val = min_val
		
		return outputs



class ThreedROIstatsInputSpec(AFNITraitedSpec):
	in_file = File(desc = 'input file to 3dROIstats',
		argstr = '%s',
		position = -1,
		mandatory = True,
		exists = True)

	mask = File(desc = 'input mask',
		argstr = '-mask %s',
		position = 3)

	mask_f2short = traits.Bool(desc = 'Tells the program to convert a float mask to short integers, by simple rounding.',
		argstr = '-mask_f2short',
		position = 2)

	quiet = traits.Bool(desc = 'execute quietly',
		argstr = '-quiet',
		position = 1)


class ThreedROIstatsOutputSpec(AFNITraitedSpec):
	stats = File(desc = 'output')

class ThreedROIstats(AFNICommand):
	_cmd = '3dROIstats'
	input_spec = ThreedROIstatsInputSpec
	output_spec = ThreedROIstatsOutputSpec

	def aggregate_outputs(self,runtime = None,  needed_outputs=None):

		outputs = self._outputs()

		outfile = os.path.join(os.getcwd(),'stat_result.json')

		if runtime is None:
			try:
				stats = load_json(outfile)['stat']
			except IOError:
				return self.run().outputs
		else:
			stats = []
			for line in runtime.stdout.split('\n'):
				if line:
					values = line.split()
					if len(values) > 1:
						stats.append([float(val) for val in values])
					else:
						stats.extend([float(val) for val in values])

			if len(stats) == 1:
				stats = stats[0]
			of = os.path.join(os.getcwd(),'TS.1D')
			f = open(of,'w')

			for st in stats:
				f.write(str(st) + '\n')
			f.close()
			save_json(outfile,dict(stat=of))
		outputs.stats =of
		
		return outputs


"""
3dcalc -a ${rest}.nii.gz[${TRstart}..${TRend}] -expr 'a' -prefix $
{rest}_dr.nii.gz

3dcalc -a ${rest}_mc.nii.gz -b ${rest}_mask.nii.gz -expr 'a*b' -prefix
${rest}_ss.nii.gz
"""

class ThreedcalcInputSpec(CommandLineInputSpec):
	infile_a = File(desc = 'input file to 3dcalc',
		argstr = '-a %s', position = 0, mandatory = True)
	infile_b = File(desc = 'operand file to 3dcalc',
		argstr = ' -b %s', position = 1)
	infile_b_prime = traits.Str(desc = 'operand file to 3dcalc',
		argstr = ' -b %s', position = 1)
	expr = traits.Str(desc = 'expr', argstr = '-expr %s', position = 2,
		mandatory = True)
	out_file = File(desc = 'output file from 3dFourier', argstr = '-prefix %s',
		position = -1, genfile=True)
	start_idx = traits.Int(desc='start index for infile_a',
		requires=['stop_idx'])
	stop_idx = traits.Int(desc='stop index for infile_a',
		requires=['start_idx'])
	single_idx = traits.Int(desc='volume index for infile_a')
		other = File(desc = 'other options', argstr = '')

class ThreedcalcOutputSpec(TraitedSpec):
	out_file = File(desc = ' output file', exists = True)

class Threedcalc(CommandLine):
"""Merge or edit volumes using AFNI 3dmerge command.

For complete details, see the `3dcalc Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dcalc.html>`_
"""

	_cmd = '3dcalc'
	input_spec = ThreedcalcInputSpec
	output_spec = ThreedcalcOutputSpec

	def _list_outputs(self):
		outputs = self.output_spec().get()
		if not isdefined(self.inputs.out_file):
			outputs['out_file'] = self._gen_filename('out_file')
		else:
			outputs['out_file'] = os.path.abspath(self.inputs.out_file)
		
		return outputs

	def _format_arg(self, name, trait_spec, value):
		if name == 'infile_a':
			arg = trait_spec.argstr%value
			if isdefined(self.inputs.start_idx):
				arg += '[%d..%d]'%(self.inputs.start_idx, self.inputs.stop_idx)
			if isdefined(self.inputs.single_idx):
				arg += '[%d]'%(self.inputs.single_idx)
            		return arg
        	return super(Threedcalc, self)._format_arg(name, trait_spec, value)

	def _parse_inputs(self, skip=None):
        """Skip the arguments without argstr metadata
	"""
		return super(Threedcalc, self)._parse_inputs(skip=('start_idx','stop_idx','other'))

	def _gen_filename(self, name):
        """Generate output file name
	"""
		if name == 'out_file':
			_, fname, ext = split_filename(self.inputs.infile_a)
            		return os.path.join(os.getcwd(), ''.join((fname, '_3dc',ext)))
