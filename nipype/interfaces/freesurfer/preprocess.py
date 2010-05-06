"""The freesurfer module provides basic functions for interfacing with freesurfer tools.

Currently these tools are supported:

     * Dicom2Nifti: using mri_convert
     * Resample: using mri_convert
     
Examples
--------
See the docstrings for the individual classes for 'working' examples.

"""
__docformat__ = 'restructuredtext'

import os
from glob import glob

from nipype.externals.pynifti import load
from nipype.interfaces.base import Bunch
from nipype.utils.docparse import get_doc
from nipype.utils.filemanip import fname_presuffix, FileNotFoundError
from nipype.interfaces.io import FreeSurferSource

from nipype.interfaces.freesurfer.base import NEW_FSCommand, FSTraitedSpec
from nipype.interfaces.base import (Bunch, TraitedSpec, File, traits,
                                    Directory, InputMultiPath)
from nipype.utils.misc import isdefined


class ParseDicomDirInputSpec(FSTraitedSpec):
    dicomdir = Directory(exists=True, argstr='--d %s', mandatory=True,
                         desc='path to siemens dicom directory')
    outfile = File('dicominfo.txt', argstr='--o %s', usedefault=True,
                   desc='write results to outfile')
    sortbyrun = traits.Bool(argstr='--sortbyrun', desc='assign run numbers')
    summarize = traits.Bool(argstr='--summarize',
                            desc='only print out info for run leaders')

class ParseDicomDirOutputSpec(TraitedSpec):
    outfile = File(exists=True,
                   desc='text file containing dicom information')

class ParseDicomDir(NEW_FSCommand):
    """uses mri_parse_sdcmdir to get information from dicom directories
    
    Examples
    --------

    >>> from nipype.interfaces.freesurfer import ParseDicomDir
    >>> import os
    >>> dcminfo = ParseDicomDir()
    >>> dcminfo.inputs.dicomdir = '.'
    >>> dcminfo.inputs.sortbyrun = True
    >>> dcminfo.inputs.summarize = True
    >>> dcminfo.cmdline
    'mri_parse_sdcmdir --d . --o dicominfo.txt --sortbyrun --summarize'
    
   """

    _cmd = 'mri_parse_sdcmdir'
    input_spec = ParseDicomDirInputSpec
    output_spec = ParseDicomDirOutputSpec
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.outfile):
            outputs['outfile'] = self.inputs.outfile
        return outputs

class UnpackSDcmdirInputSpec(FSTraitedSpec):
    srcdir = Directory(exists=True, argstr='-src %s',
                       mandatory=True,
                       desc='directory with the DICOM files')
    targdir = Directory(argstr='-targ %s',
        desc='top directory into which the files will be unpacked')
    runinfo = traits.Tuple(traits.Int, traits.Str, traits.Str, traits.Str,
                           mandatory=True,
                           argstr='-run %d %s %s %s',
                           xor = ('runinfo', 'config', 'seqconfig'),
        desc='runno subdir format name : spec unpacking rules on cmdline')
    config = File(exists=True, argstr='-cfg %s',
                  mandatory=True,
                  xor = ('runinfo', 'config', 'seqconfig'),
                  desc='specify unpacking rules in file')
    seqconfig = File(exists=True, argstr='-seqcfg %s',
                     mandatory=True,
                     xor = ('runinfo', 'config', 'seqconfig'),
                     desc='specify unpacking rules based on sequence')
    dirstruct = traits.Enum('fsfast', 'generic', argstr='-%s',
                     desc='unpack to specified directory structures')
    noinfodump = traits.Bool(argstr='-noinfodump',
                             desc='do not create infodump file')
    scanonly = File(exists=True, argstr='-scanonly %s',
                    desc='only scan the directory and put result in file')
    logfile = File(exists=True, argstr='-log %s',
                   desc='explicilty set log file')
    spmzeropad = traits.Int(argstr='-nspmzeropad %d',
                            desc='set frame number zero padding width for SPM')
    nounpackerr = traits.Bool(argstr='-no-unpackerr',
                              desc='do not try to unpack runs with errors')

class UnpackSDcmdir(NEW_FSCommand):
    """use fs unpacksdcmdir to convert dicom files

    Examples
    --------
    """
    _cmd = 'unpacksdcmdir'
    input_spec = UnpackSDcmdirInputSpec


class MriConvertInputSpec(FSTraitedSpec):
    readonly = traits.Bool(argstr='--read_only',
                            desc='read the input volume')
    nowrite = traits.Bool(argstr='--no_write',
                           desc='do not write output')
    ininfo = traits.Bool(argstr='--in_info',
                         desc='display input info')
    outinfo = traits.Bool(argstr='--out_info',
                          desc='display output info')
    instats = traits.Bool(argstr='--in_stats',
                          desc='display input stats')
    outstats = traits.Bool(argstr='--out_stats',
                           desc='display output stats')
    inmatrix = traits.Bool(argstr='--in_matrix',
                           desc='display input matrix')
    outmatrix = traits.Bool(argstr='--out_matrix',
                            desc='display output matrix')
    in_i_size = traits.Int(argstr='--in_i_size %d',
                           desc='input i size')
    in_j_size = traits.Int(argstr='--in_j_size %d',
                           desc='input j size')
    in_k_size = traits.Int(argstr='--in_k_size %d',
                           desc='input k size')
    forceras = traits.Bool(argstr='--force_ras_good',
                           desc='use default when orientation info absent')
    in_i_dir = traits.Tuple(traits.Float, traits.Float,traits.Float,
                           argstr='--in_i_direction %f %f %f',
                           desc='<R direction> <A direction> <S direction>')
    in_j_dir = traits.Tuple(traits.Float, traits.Float,traits.Float,
                           argstr='--in_j_direction %f %f %f',
                           desc='<R direction> <A direction> <S direction>')
    in_k_dir = traits.Tuple(traits.Float, traits.Float,traits.Float,
                           argstr='--in_k_direction %f %f %f',
                           desc='<R direction> <A direction> <S direction>')
    #[''.join([i['x'],i['y'],i['z']]) for i in \
    #    walk(dict(x=lambda:['L','R'],y=lambda:['A','P'],z=lambda:['I','S']).items())]
    _orientations = ['LAI', 'LAS', 'RAI', 'RAS', 'LPI', 'LPS', 'RPI', 'RPS']
    inorientation = traits.Enum(_orientations,
                                argstr='--in_orientation %s',
                                desc='specify the input orientation')
    incenter = traits.List(traits.Float, maxlen=3,
                           argstr='--in_center %s',
                           desc='<R coordinate> <A coordinate> <S coordinate>')
    sphinx = traits.Bool(argstr='--sphinx',
                         desc='change orientation info to sphinx')
    out_i_count = traits.Int(argstr='--out_i_count %d',
                             desc='some count ?? in i direction')
    out_j_count = traits.Int(argstr='--out_j_count %d',
                             desc='some count ?? in j direction')
    out_k_count = traits.Int(argstr='--out_k_count %d',
                             desc='some count ?? in k direction')
    voxsize = traits.Tuple(traits.Float, traits.Float,traits.Float,
                           argstr='--voxsize %f %f %f',
                           desc='<size_x> <size_y> <size_z> specify the size (mm) - useful for upsampling or downsampling')
    out_i_size = traits.Int(argstr='--out_i_size %d',
                            desc='output i size')
    out_j_size = traits.Int(argstr='--out_j_size %d',
                            desc='output j size')
    out_k_size = traits.Int(argstr='--out_k_size %d',
                            desc='output k size')
    out_i_dir = traits.Tuple(traits.Float, traits.Float,traits.Float,
                           argstr='--out_i_direction %f %f %f',
                           desc='<R direction> <A direction> <S direction>')
    out_j_dir = traits.Tuple(traits.Float, traits.Float,traits.Float,
                           argstr='--out_j_direction %f %f %f',
                           desc='<R direction> <A direction> <S direction>')
    out_k_dir = traits.Tuple(traits.Float, traits.Float,traits.Float,
                             argstr='--out_k_direction %f %f %f',
                             desc='<R direction> <A direction> <S direction>')
    outorientation = traits.Enum(_orientations,
                                argstr='--out_orientation %s',
                                desc='specify the output orientation')
    outcenter = traits.Tuple(traits.Float, traits.Float,traits.Float,
                           argstr='--out_center %f %f %f',
                           desc='<R coordinate> <A coordinate> <S coordinate>')
    outdatatype = traits.Enum('uchar', 'short', 'int', 'float',
                              argstr='--out_data_type %s',
                              descr='output data type <uchar|short|int|float>')
    resampletype = traits.Enum('interpolate', 'weighted', 'nearest', 'sinc', 'cubic',
                               argstr='--resample_type %s',
                               desc='<interpolate|weighted|nearest|sinc|cubic> (default is interpolate)')
    noscale = traits.Bool(argstr='--no_scale 1',
                          desc='dont rescale values for COR')
    nochange = traits.Bool(argstr='--nochange',
                           desc="don't change type of input to that of template")
    autoalignmtx = File(exists=True, argstr='--autoalign %s',
                        desc='text file with autoalign matrix')
    unwarpgradient = traits.Bool(argstr='--unwarp_gradient_nonlinearity',
                                 desc='unwarp gradient nonlinearity')
    applyxfm = File(exists=True, argstr='--apply_transform %s',
                    desc='apply xfm file')
    applyinvxfm = File(exists=True, argstr='--apply_inverse_transform %s',
                       desc='apply inverse transformation xfm file')
    devolvexfm = traits.Str(argstr='--devolvexfm %s',
                            desc='subject id')
    cropcenter = traits.Tuple(traits.Int, traits.Int, traits.Int,
                              argstr='--crop %d %d %d',
                              desc='<x> <y> <z> crop to 256 around center (x,y,z)')
    cropsize = traits.Tuple(traits.Int, traits.Int, traits.Int,
                            argstr='--cropsize %d %d %d',
                            desc='<dx> <dy> <dz> crop to size <dx, dy, dz>')
    cutends = traits.Int(argstr='--cutends %d',
                         desc='remove ncut slices from the ends')
    slicecrop = traits.Tuple(traits.Int, traits.Int,
                             argstr='--slice-crop %d %d',
                             desc='s_start s_end : keep slices s_start to s_end')
    slicereverse = traits.Bool(argstr='--slice-reverse',
                               desc='reverse order of slices, update vox2ras')
    slicebias = traits.Float(argstr='--slice-bias %f',
                             desc='apply half-cosine bias field')
    fwhm = traits.Float(argstr='--fwhm %f',
                        desc='smooth input volume by fwhm mm')
    _filetypes = ['cor', 'mgh', 'mgz', 'minc', 'analyze',
                  'analyze4d', 'spm', 'afni', 'brik', 'bshort',
                  'bfloat', 'sdt', 'outline', 'otl', 'gdf',
                  'nifti1', 'nii', 'niigz']
    _infiletypes = ['ge', 'gelx', 'lx','ximg', 'siemens', 'dicom', 'siemens+dicom']
    intype = traits.Enum(_filetypes + _infiletypes, argstr='--in_type %s',
                        desc='input file type')
    outtype = traits.Enum(_filetypes, argstr='--out_type %s',
                        desc='output file type')
    ascii = traits.Bool(argstr='--ascii',
                        desc='save output as ascii col>row>slice>frame')
    reorder = traits.Tuple(traits.Int, traits.Int, traits.Int,
                           argstr='--reorder %d %d %d',
                           desc='olddim1 olddim2 olddim3')
    invertcontrast = traits.Float(argstr='--invert_contrast %f',
                                  desc='threshold for inversting contrast')
    infile = File(exists=True, mandatory=True,
                  position=-2,
                  argstr='--input_volume %s',
                  desc='File to read/convert')
    outfile = File(argstr='--output_volume %s', 
                   position=-1, genfile=True,
                   desc='output filename or True to generate one')
    conform = traits.Bool(argstr='--conform',
                          desc='conform to 256^3')
    conformmin = traits.Bool(argstr='--conform_min',
                             desc='conform to smallest size')
    conformsize = traits.Float(argstr='--conform_size %s',
                               desc='conform to size_in_mm')
    parseonly = traits.Bool(argstr='--parse_only',
                            desc='parse input only')
    subjectname = traits.Str(argstr='--subject_name %s',
                             desc = 'subject name ???')
    reslicelike = File(exists=True, argstr='--reslice_like %s',
                       desc='reslice output to match file')
    templatetype = traits.Enum(_filetypes + _infiletypes,
                               argstr='--template_type %s',
                               desc='template file type')
    split = traits.Bool(argstr='--split',
                        desc='split output frames into separate output files.')
    frame = traits.Int(argstr='--frame %d',
                       desc='keep only 0-based frame number')
    midframe = traits.Bool(argstr='--mid-frame',
                           desc='keep only the middle frame')
    skipn = traits.Int(argstr='--nskip %d',
                       desc='skip the first n frames')
    dropn = traits.Int(argstr='--ndrop %d',
                       desc='drop the last n frames')
    framesubsample = traits.Tuple(traits.Int, traits.Int, traits.Int,
                                  argstr='--fsubsample %d %d %d',
                                  desc='start delta end : frame subsampling (end = -1 for end)')
    inscale = traits.Float(argstr='--scale %f',
                         desc='input intensity scale factor')
    outscale = traits.Float(argstr='--out-scale %d',
                            desc='output intensity scale factor')
    inlike = File(exists=True, argstr='--in_like %s',
                  desc='input looks like')
    fillparcellation = traits.Bool(argstr='--fill_parcellation',
                                   desc='fill parcellation')
    smoothparcellation = traits.Bool(argstr='--smooth_parcellation',
                                     desc='smooth parcellation')
    zerooutlines = traits.Bool(argstr='--zero_outlines',
                               desc='zero outlines')
    colorfile = File(exists=True, argstr='--color_file %s',
                     desc='color file')
    notranslate = traits.Bool(argstr='--no_translate',
                              desc='???')
    statusfile = File(argstr='--status %s',
                      desc='status file for DICOM conversion')
    sdcmlist = File(exists=True, argstr='--sdcmlist %s',
                    desc='list of DICOM files for conversion')
    templateinfo = traits.Bool('--template_info',
                               desc='dump info about template')
    crop_gdf = traits.Bool(argstr='--crop_gdf',
                           desc='apply GDF cropping')
    zerogezoffset = traits.Bool(argstr='--zero_ge_z_offset',
                               desc='zero ge z offset ???')

class MriConvertOutputSpec(TraitedSpec):
    outfile = File(exists=True, desc='converted output file')

class MriConvert(NEW_FSCommand):
    """use fs mri_convert to manipulate files

    adds niigz as an output type option

    Examples
    --------

    >>> from nipype.interfaces.freesurfer import MriConvert
    >>> mc = MriConvert()
    >>> mc.inputs.infile = 'anatomical.nii'
    >>> mc.inputs.outtype = 'mgz'
    >>> mc.cmdline
    'mri_convert --out_type mgz --input_volume struct.nii --output_volume struct_out.mgz'
    
    """
    _cmd = 'mri_convert'
    input_spec = MriConvertInputSpec
    output_spec = MriConvertOutputSpec

    filemap = dict(cor='cor', mgh='mgh', mgz='mgz', minc='mnc',
                   afni='brik', brik='brik', bshort='bshort',
                   spm='img', analyze='img', analyze4d='img',
                   bfloat='bfloat', nifti1='img', nii='nii',
                   niigz='nii.gz')

    def _format_arg(self, name, spec, value):
        if name in ['intype', 'outtype', 'templatetype']:
            if value == 'niigz':
                return spec.argstr % 'nii'
        return super(MriConvert, self)._format_arg(name, spec, value)
    
    def _get_outfilename(self):
        outfile = self.inputs.outfile
        if not isdefined(outfile):
            if isdefined(self.inputs.outtype):
                suffix = '_out.' + self.filemap[self.inputs.outtype]
            else:
                suffix = '_out.nii.gz'
            outfile = fname_presuffix(self.inputs.infile,
                                      newpath=os.getcwd(),
                                      suffix=suffix,
                                      use_ext=False)
        return outfile
        
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outfile = self._get_outfilename()
        if isdefined(self.inputs.outtype):
            if self.inputs.outtype in ['spm', 'analyze']:
                # generate all outputs
                size = load(self.inputs.infile).get_shape()
                if len(size)==3:
                    tp = 1
                else:
                    tp = size[-1]
                # have to take care of all the frame manipulations
                warn('Not taking frame manipulations into account')
                outfiles = []
                for i in range(tp):
                    outfiles.append(fname_presuffix(outfile,
                                                    suffix='%03d'%(i+1)))
                outfile = outfiles
        outputs['outfile'] = outfile
        return outputs

    def _gen_filename(self, name):
        if name == 'outfile':
            return self._get_outfilename()
        return None    

class DicomConvertInputSpec(FSTraitedSpec):
    dicomdir = Directory(exists=True, mandatory=True,
                         desc='dicom directory from which to convert dicom files')
    base_output_dir = Directory(mandatory=True,
            desc='directory in which subject directories are created')
    subject_dir_template = traits.Str('S.%04d', usedefault=True,
                          desc='template for subject directory name')
    subject_id = traits.Any(desc = 'subject identifier to insert into template')
    file_mapping = traits.List(traits.Tuple(traits.Str, traits.Str),
               desc='defines the output fields of interface')
    out_type = traits.Enum('niigz', MriConvertInputSpec._filetypes,
                           usedefault=True,
               desc='defines the type of output file produced')
    dicominfo = File(exists=True,
               desc='File containing summary information from mri_parse_sdcmdir')
    seq_list = traits.List(traits.Str,
                           requires=['dicominfo'],
               desc='list of pulse sequence names to be converted.')
    ignore_single_slice = traits.Bool(requires=['dicominfo'],
               desc='ignore volumes containing a single slice')

class DicomConvert(NEW_FSCommand):
    """use fs mri_convert to convert dicom files

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import DicomConvert
    >>> cvt = DicomConvert()
    >>> cvt.inputs.dicomdir = '/incoming/TrioTim-35115-2009-1900-123456/'
    >>> cvt.inputs.file_mapping = [('nifti','*.nii'),('info','dicom*.txt'),('dti','*dti.bv*')]

    """
    _cmd = 'mri_convert'
    input_spec = DicomConvertInputSpec

    def _get_dicomfiles(self):
        """validate fsl bet options
        if set to None ignore
        """
        return glob(os.path.abspath(os.path.join(self.inputs.dicomdir,
                                                 '*-1.dcm')))

    def _get_outdir(self):
        """returns output directory"""
        subjid = self.inputs.subject_id
        if not isdefined(subjid):
            path,fname = os.path.split(self._get_dicomfiles()[0])
            subjid = int(fname.split('-')[0])
        if isdefined(self.inputs.subject_dir_template):
            subjid  = self.inputs.subject_dir_template % subjid
        basedir=self.inputs.base_output_dir
        if not isdefined(basedir):
            basedir = os.path.abspath('.')
        outdir = os.path.abspath(os.path.join(basedir,subjid))
        return outdir

    def _get_runs(self):
        """Returns list of dicom series that should be converted.

        Requires a dicom info summary file generated by ``DicomDirInfo``

        """
        seq = np.genfromtxt(self.inputs.dicominfo, dtype=object)
        runs = []
        for s in seq:
            if self.inputs.seq_list:
                if self.inputs.ignore_single_slice:
                    if (int(s[8]) > 1) and any([s[12].startswith(sn) for sn in self.inputs.seq_list]):
                        runs.append(int(s[2]))
                else:
                    if any([s[12].startswith(sn) for sn in self.inputs.seq_list]):
                        runs.append(int(s[2]))
            else:
                runs.append(int(s[2]))
        return runs

    def _get_filelist(self, outdir):
        """Returns list of files to be converted"""
        filemap = {}
        for f in self._get_dicomfiles():
            head,fname = os.path.split(f)
            fname,ext = os.path.splitext(fname)
            fileparts = fname.split('-')
            runno = int(fileparts[1])
            out_type = MriConvert.filemap[self.inputs.out_type]
            outfile = os.path.join(outdir,'.'.join(('%s-%02d'% (fileparts[0],
                                                                runno),
                                                    out_type)))
            filemap[runno] = (f,outfile)
        if self.inputs.dicominfo:
            files = [filemap[r] for r in self._get_runs()]
        else:
            files = [filemap[r] for r in filemap.keys()]
        return files

    @property
    def cmdline(self):
        """ `command` plus any arguments (args)
        validates arguments and generates command line"""
        self._check_mandatory_inputs()
        outdir = self._get_outdir()
        cmd = []
        if not os.path.exists(outdir):
            cmdstr = 'python -c "import os; os.makedirs(\'%s\')"' % outdir
            cmd.extend([cmdstr])
        infofile = os.path.join(outdir, 'shortinfo.txt')
        if not os.path.exists(infofile):
            cmdstr = 'dcmdir-info-mgh %s > %s' % (self.inputs.dicomdir,
                                                  infofile)
            cmd.extend([cmdstr])
        files = self._get_filelist(outdir)
        for infile,outfile in files:
            if not os.path.exists(outfile):
                single_cmd = '%s %s %s' % (self.cmd, infile,
                                           os.path.join(outdir, outfile))
                cmd.extend([single_cmd])
        return  '; '.join(cmd)

class ResampleInputSpec(FSTraitedSpec):
    infile = File(exists=True, argstr='-i %s', mandatory=True,
                  desc='file to resample')
    outfile = File(argstr='-o %s', desc='output filename', genfile=True)
    voxelsize = traits.List(argstr='-vs %s', desc='triplet of output voxel sizes',
                     mandatory=True)
        
class ResampleOutputSpec(TraitedSpec):
    outfile = File(exists=True,
                   desc='output filename')
    
class Resample(NEW_FSCommand):
    """Use FreeSurfer mri_convert to up or down-sample image files

    Examples
    --------
    >>> from nipype.interfaces import freesurfer
    >>> resampler = freesurfer.Resample()
    >>> resampler.inputs.infile = 'infile.nii'
    >>> resampler.inputs.voxel_size = [2.1, 2.1, 2.1]
    >>> resampler.cmdline
    'mri_convert -i infile.nii -vs 2.10 2.10 2.10 -o infile_resample.nii'
    
   """

    _cmd = 'mri_convert'
    input_spec = ResampleInputSpec
    output_spec = ResampleOutputSpec

    def _get_outfilename(self):
        if isdefined(self.inputs.outfile):
            outfile = self.inputs.outfile
        else:
            outfile = fname_presuffix(self.inputs.infile,
                                      newpath = os.getcwd(),
                                      suffix='_resample')
        return outfile
            
        
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['outfile'] = self._get_outfilename()
        return outputs
    
    def _gen_filename(self, name):
        if name == 'outfile':
            return self._get_outfilename()
        return None

class ReconAllInputSpec(FSTraitedSpec):
    subject_id = traits.Str(argstr='-subjid %s', desc='subject name',
                            mandatory=True)
    directive = traits.Enum('all', 'autorecon1', 'autorecon2', 'autorecon2-cp',
                            'autorecon2-wm', 'autorecon2-inflate1', 'autorecon2-perhemi',
                            'autorecon3', argstr='-%s', desc='process directive',
                            mandatory=True)
    hemi = traits.Enum('lh', 'rh', desc='hemisphere to process')
    T1file = InputMultiPath(argstr='--i %s...', desc='name of T1 file to process')
    subjectsdir = Directory(exists=True, argstr='-sd %s',
                             desc='path to subjects directory')
    flags = traits.Str(argstr='%s', desc='additional parameters')

class ReconAll(NEW_FSCommand):
    """Use FreeSurfer recon-all to generate surfaces and parcellations of
    structural data from an anatomical image of a subject.

    Examples
    --------
    >>> from nipype.interfaces import freesurfer
    >>> reconall = freesurfer.ReconAll()
    >>> reconall.inputs.subject_id = 'foo'
    >>> reconall.inputs.all  = True
    >>> reconall.inputs.subjects_dir = '.'
    >>> reconall.inputs.T1file = 'structfile.nii'
    >>> reconall.cmdline
    'recon-all --i structfile.nii --all -subjid foo -sd .'
    
   """

    _cmd = 'recon-all'
    input_spec = ReconAllInputSpec
    output_spec = FreeSurferSource.output_spec

    def _list_outputs(self):
        """
        See io.FreeSurferSource.outputs for the list of outputs returned
        """
        FreeSurferSource(subject_id=self.inputs.subject_id,
                         subjects_dir=self.inputs.subjects_dir)._outputs().get()

class BBRegisterInputSpec(FSTraitedSpec):
    subject_id = traits.Str(argstr='--s %s', desc='freesurfer subject id',
                            mandatory=True)
    sourcefile = File(argstr='--mov %s', desc='source file to be registered',
                      mandatory=True, copyfile=False)
    _reg_inputs = ('init', 'initreg')
    init = traits.Enum('spm', 'fsl', 'header', argstr='--init-%s', xor=_reg_inputs,
                       desc='initialize registration spm, fsl, header')
    initreg = File(exists=True, desc='existing registration file', xor=_reg_inputs,
                   mandatory=True)
    contrast_type = traits.Enum('t1', 't2', argstr='--%s',
                                desc='contrast type of image', mandatory=True)
    outregfile = File(argstr='--reg %s', desc='output registration file',
                      genfile=True)
    outfile = traits.Either(traits.Bool, File, argstr='--o %s',
                            desc='output warped sourcefile either True or filename')
    flags = traits.Str(argstr='%s', desc='any additional flags')

class BBRegisterOutputSpec(TraitedSpec):
    outregfile = File(exists=True, desc='Output registration file')
    outfile = File(desc='Registered and resampled source file')

class BBRegister(NEW_FSCommand):
    """Use FreeSurfer bbregister to register a volume two a surface mesh

    This program performs within-subject, cross-modal registration using a
    boundary-based cost function. The registration is constrained to be 6
    DOF (rigid). It is required that you have an anatomical scan of the
    subject that has been analyzed in freesurfer.

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import BBRegister
    >>> bbreg = BBRegister(subject_id='me', sourcefile='foo.nii', init_header=True, t2_contrast=True)
    >>> bbreg.cmdline
    'bbregister --init-header --mov foo.nii --s me --t2 --reg foo_bbreg_me.dat'

   """

    _cmd = 'bbregister'
    input_spec = BBRegisterInputSpec
    output_spec =  BBRegisterOutputSpec
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['outregfile'] = self.inputs.outregfile
        if not isdefined(self.inputs.outregfile) and self.inputs.sourcefile:
            outputs['outregfile'] = fname_presuffix(self.inputs.sourcefile,
                                         suffix='_bbreg_%s.dat'%self.inputs.subject_id,
                                         use_ext=False)
        if isdefined(self.inputs.outfile):
            outputs['outfile'] = self.inputs.outfile
            if isinstance(self.inputs.outfile, bool):
                outputs['outfile'] = fname_presuffix(self.inputs.sourcefile,suffix='_bbreg')
        return outputs

    def _format_arg(self, name, spec, value):
        if name == 'outfile':
            if isinstance(value, bool):
                fname = self._list_outputs()[name]
            else:
                fname = value
            return spec.argstr % fname
        return super(BBRegister, self)._format_arg(name, spec, value)
    
    def _gen_filename(self, name):
        if name == 'outregfile':
            return self._list_outputs()[name]
        return None    

class ApplyVolTransformInputSpec(FSTraitedSpec):
    sourcefile = File(exists = True, argstr = '--mov %s',
                      copyfile=False, mandatory = True,
                      desc = 'Input volume you wish to transform')
    outfile = File(desc = 'Output volume', argstr='--o %s', genfile=True)
    _targ_xor = ('targetfile', 'tal', 'fstarg')
    targetfile = File(exists = True, argstr = '--targ %s', xor=_targ_xor,
                      desc = 'Output template volume', mandatory=True)
    tal = traits.Bool(argstr='--tal', xor=_targ_xor, mandatory=True,
                      desc='map to a sub FOV of MNI305 (with --reg only)')
    _fstarg_requires = ('fstarg', 'regfile')
    fstarg = traits.Bool(argstr='--fstarg',xor=_targ_xor, mandatory=True,
                         requires=_fstarg_requires,
                         desc='use orig.mgz from subject in regfile as target')
    _reg_xor = ('regfile', 'fslregfile', 'xfmregfile', 'regheader', 'subject')
    regfile = File(exists=True, xor=_reg_xor, argstr='--reg %s',
                   requires=_fstarg_requires,  mandatory=True,
                   desc= 'tkRAS-to-tkRAS matrix   (tkregister2 format)')
    fslregfile = File(exists=True, xor=_reg_xor, argstr='--fsl %s',
                   mandatory=True,
                   desc= 'fslRAS-to-fslRAS matrix (FSL format)')
    xfmregfile = File(exists=True, xor=_reg_xor, argstr='--xfm %s',
                   mandatory=True,
                   desc= 'ScannerRAS-to-ScannerRAS matrix (MNI format)')
    regheader = traits.Bool(xor=_reg_xor, argstr='--regheader',
                   mandatory=True,
                   desc= 'ScannerRAS-to-ScannerRAS matrix = identity')
    subject = traits.Str(xor=_reg_xor, argstr='--s %s',
                   mandatory=True,
                   desc= 'set matrix = identity and use subject for any templates')
    inverse = traits.Bool(desc = 'sample from target to source',
                          argstr = '--inv')
    interp = traits.Enum('trilin', 'nearest', argstr = '--interp %s',
                         desc = 'Interpolation method (<trilin> or nearest)')
    noresample = traits.Bool(desc = 'Do not resample; just change vox2ras matrix',
                             argstr = '--no-resample')
    flags = traits.Str(desc = 'any additional args',
                       argstr = '%s')

class ApplyVolTransformOutputSpec(TraitedSpec):
    outfile = File(exists=True, desc = 'Path to output file if used normally')

class ApplyVolTransform(NEW_FSCommand):
    """Use FreeSurfer mri_vol2vol to apply a transform.

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import ApplyVolTransform
    >>> applyreg = ApplyVolTransform()
    >>> applyreg.inputs.sourcefile = 'struct.nii'
    >>> applyreg.inputs.regfile = 'register.dat'
    >>> applyreg.inputs.fstarg = True
    >>> applyreg.cmdline
    'mri_vol2vol --fstarg --o struct_warped.nii --reg register.dat --mov struct.nii'

    """

    _cmd = 'mri_vol2vol'
    input_spec = ApplyVolTransformInputSpec
    output_spec = ApplyVolTransformOutputSpec

    def _get_outfile(self):
        outfile = self.inputs.outfile
        if not isdefined(outfile):
            if self.inputs.inverse == True:
                if self.inputs.fstarg == True:
                    src = 'orig.mgz'
                else:
                    src = self.inputs.target
            else:
                src = self.inputs.sourcefile
            outfile = fname_presuffix(src,
                                      newpath=os.getcwd(),
                                      suffix='_warped')
        return outfile

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['outfile'] = self._get_outfile()
        return outputs
    
    def _gen_filename(self, name):
        if name == 'outfile':
            return self._get_outfile()
        return None    

class SmoothInputSpec(FSTraitedSpec):
    sourcefile= File(exists=True, desc='source volume',
                     argstr='--i %s',mandatory=True)
    regfile = File(desc='registers volume to surface anatomical ',
                   argstr='--reg %s', mandatory=True,
                   exists=True)
    outfile = File(desc='output volume', argstr='--o %s', genfile=True)
    projfrac_avg=traits.Tuple(traits.Float,traits.Float,traits.Float,
                              desc='average a long normal min max delta',
                              argstr='--projfrac-avg %s')
    projfrac = traits.Float(desc='project frac of thickness a long surface normal',
                          argstr='--projfrac %s')
    surface_fwhm = traits.Float(min=0, desc='surface FWHM in mm', argstr='--fwhm %d')
    vol_fwhm = traits.Float(min=0, argstr= '--vol-fwhm %d',
                            desc='volumesmoothing outside of surface')
    flags = traits.Str(desc='maps additional commands', argstr='%s')

class SmoothOutputSpec(FSTraitedSpec):
    outfile= File(exist=True,desc='smoothed input volume')	
         
class Smooth(NEW_FSCommand):
    """Use FreeSurfer mris_volsmooth to smooth a volume

    This function smoothes cortical regions on a surface and
    non-cortical regions in volume.

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import Smooth
    >>> smoothvol = Smooth(sourcefile='foo.nii', outfile = 'foo_out.nii', regfile='reg.dat', surface_fwhm=10, vol_fwhm=6)
    >>> smoothvol.cmdline
    'mris_volsmooth --o foo_out.nii --reg reg.dat --i foo.nii --fwhm 10 --vol-fwhm 6'
    
    """

    _cmd = 'mris_volsmooth'
    input_spec = SmoothInputSpec
    output_spec = SmoothOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['outfile'] = self.inputs.outfile
        if not isdefined(outputs['outfile']) and isdefined(self.inputs.sourcefile):
            outputs['outfile'] = self._gen_fname(self.inputs.sourcefile,
                                              suffix = '_smooth')
        return outputs

    def _gen_filename(self, name):
        if name == 'outfile':
            return self._list_outputs()[name]
        return None

