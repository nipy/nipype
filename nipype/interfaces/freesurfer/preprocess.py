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

from nipype.interfaces.base import Bunch
from nipype.utils.docparse import get_doc
from nipype.utils.filemanip import fname_presuffix, FileNotFoundError
from nipype.interfaces.io import FreeSurferSource
from nipype.interfaces.freesurfer import FSCommand

from nipype.interfaces.freesurfer.base import FSCommandLine, NEW_FSCommand, FSTraitedSpec
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

class DicomConvert(FSCommandLine):
    """use fs mri_convert to convert dicom files

    Parameters
    ----------

    To see optional arguments
    DicomConvert().inputs_help()


    Examples
    --------
    >>> from nipype.interfaces import freesurfer
    >>> cvt = freesurfer.DicomConvert()
    >>> cvt.inputs.dicomdir = '/incoming/TrioTim-35115-2009-1900-123456/'
    >>> cvt.inputs.file_mapping = [('nifti','*.nii'),('info','dicom*.txt'),('dti','*dti.bv*')]

   """
    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mri_convert'


    def inputs_help(self):
        """
        Parameters
        ----------
        
        (all default to None and are unset)
        
        dicomdir : /path/to/dicomfiles
            directory from which to convert dicom files
        base_output_dir : /path/to/outputdir
            base output directory in which subject specific
            directories are created to store the nifti files
        subject_dir_template : string
            template for subject directory name
            Default:'S.%04d'
        subject_id : string or int
            subject identifier to insert into template. For the
            example above template subject_identifier should be an
            integer. Default: id from Dicom file name 
        file_mapping : list of tuples
            defines the output fields of interface and the kind of
            file type they store
            Example:  [('niftifiles','*.nii'),('dtiinfo','*mghdti.bv*')]
        out_type : string
            defines the type of output file produced.
            possible options nii, nii.gz, mgz (default: nii)
        dicominfo : file
            File containing summary information from mri_parse_sdcmdir
        seq_list : list of strings
            list of pulse sequence names to be converted.
        ignore_single_slice : boolean
            ignores volumes containing a single slice. dicominfo needs to be
            available. 
        flags = unsupported flags, use at your own risk

        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        self.inputs = Bunch(dicomdir=None,
                            base_output_dir=None,
                            subject_dir_template=None,
                            subject_id=None,
                            file_mapping=None,
                            out_type='nii',
                            dicominfo=None,
                            seq_list=None,
                            ignore_single_slice=None,
                            flags=None)

    def _parseinputs(self):
        """validate fsl bet options
        if set to None ignore
        """
        out_inputs = {'dicomfiles':None}
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.items() if v]
        for opt in inputs:
            if opt == 'dicomdir':
                out_inputs['dicomfiles'] = glob(os.path.abspath(os.path.join(inputs[opt],'*-1.dcm')))
                continue
            if opt in ['base_output_dir', 'subject_dir_template', 'subject_id', \
                           'file_mapping', 'out_type', 'dicominfo', 'seq_list', \
                           'ignore_single_slice', 'flags']:
                continue
            print 'option %s not supported'%(opt)
        
        return out_inputs

    def _get_outdir(self):
        """returns output directory"""
        valid_inputs = self._parseinputs()
        subjid = self.inputs.subject_id
        if not subjid:
            path,fname = os.path.split(valid_inputs['dicomfiles'][0])
            subjid = fname.split('-')[0]
        if self.inputs.subject_dir_template:
            subjid  = self.inputs.subject_dir_template % subjid
        basedir=self.inputs.base_output_dir
        if not basedir:
            basedir = os.path.abspath('.')
        outdir = os.path.abspath(os.path.join(basedir,subjid))
        return outdir

    def _get_runs(self):
        """Returns list of dicom series that should be converted.

        Requires a dicom info summary file generated by ``DicomDirInfo``

        """
        seq = np.genfromtxt(self.inputs.dicominfo,dtype=object)
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
        valid_inputs = self._parseinputs()
        filemap = {}
        for f in valid_inputs['dicomfiles']:
            head,fname = os.path.split(f)
            fname,ext = os.path.splitext(fname)
            fileparts = fname.split('-')
            runno = int(fileparts[1])
            outfile = os.path.join(outdir,'.'.join(('%s-%02d'% (fileparts[0],
                                                                runno),
                                                    self.inputs.out_type)))
            filemap[runno] = (f,outfile)
        if self.inputs.dicominfo:
            files = [filemap[r] for r in self._get_runs()]
        else:
            files = [filemap[r] for r in filemap.keys()]
        return files

    def _compile_command(self):
        """validates fsl options and generates command line argument"""
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
        self._cmdline =  '; '.join(cmd)
        return self._cmdline

    def outputs(self):
        return Bunch()

    def aggregate_outputs(self):
        outdir = self._get_outdir()
        outputs = self.outputs()
        if self.inputs.file_mapping:
            for field,template in self.inputs.file_mapping:
                setattr(outputs, field, sorted(glob(os.path.join(outdir,
                                                                 template))))
        return outputs

class Dicom2Nifti(FSCommandLine):
    """use fs mri_convert to convert dicom files to nifti-1 files

    Parameters
    ----------

    To see optional arguments
    Dicom2Nifti().inputs_help()


    Examples
    --------
    >>> from nipype.interfaces import freesurfer
    >>> cvt = freesurfer.Dicom2Nifti()
    >>> cvt.inputs.dicomdir = '/software/data/STUT/RAWDATA/TrioTim-35115-20090428-081900-234000/'
    >>> cvt.inputs.file_mapping = [('nifti','*.nii'),('info','dicom*.txt'),('dti','*dti.bv*')]
    >>> #out = cvt.run() # commented out as above directories are not installed

   """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mri_convert'


    def inputs_help(self):
        """
        Parameters
        ----------
        
        (all default to None and are unset)
        
        dicomdir : /path/to/dicomfiles
            directory from which to convert dicom files
        base_output_dir : /path/to/outputdir
            base output directory in which subject specific
            directories are created to store the nifti files
        subject_dir_template : string
            template for subject directory name
            Default:'S.%04d'
        subject_id : string or int
            subject identifier to insert into template. For the
            example above template subject_identifier should be an
            integer. Default: id from Dicom file name 
        file_mapping : list of tuples
            defines the output fields of interface and the kind of
            file type they store
            Example:  [('niftifiles','*.nii'),('dtiinfo','*mghdti.bv*')]
        out_type : string
            defines the type of output file produced.
            possible options nii, nii.gz, mgz (default: nii)
        flags = unsupported flags, use at your own risk

        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        self.inputs = Bunch(dicomdir=None,
                            base_output_dir=None,
                            subject_dir_template=None,
                            subject_id=None,
                            file_mapping=None,
                            out_type='nii',
                            flags=None)

    def _parseinputs(self):
        """validate fsl bet options
        if set to None ignore
        """
        out_inputs = {'dicomfiles':None}
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.items() if v is not None ]
        for opt in inputs:
            if opt == 'dicomdir':
                out_inputs['dicomfiles'] = glob(os.path.abspath(os.path.join(inputs[opt],'*-1.dcm')))
                continue
            if opt == 'base_output_dir':
                continue
            if opt == 'subject_dir_template':
                continue
            if opt == 'subject_id':
                continue
            if opt == 'file_mapping':
                continue
            if opt == 'out_type':
                continue
            if opt == 'flags':
                continue
            print 'option %s not supported'%(opt)
        
        return out_inputs

    def _get_outdir(self):
        """returns output directory"""
        valid_inputs = self._parseinputs()
        subjid = self.inputs.subject_id
        if not subjid:
            path,fname = os.path.split(valid_inputs['dicomfiles'][0])
            subjid = fname.split('-')[0]
        if self.inputs.subject_dir_template:
            subjid  = self.inputs.subject_dir_template % subjid
        basedir=self.inputs.base_output_dir
        if not basedir:
            basedir = os.path.abspath('.')
        outdir = os.path.abspath(os.path.join(basedir,subjid))
        return outdir
    
    def _compile_command(self):
        """validates fsl options and generates command line argument"""
        valid_inputs = self._parseinputs()
        outdir = self._get_outdir()
        cmd = []
        if not os.path.exists(outdir):
            cmdstr = 'python -c "import os; os.makedirs(\'%s\')";' % outdir
            cmd.extend([cmdstr])
        dicominfotxt = os.path.join(outdir,'dicominfo.txt')
        if not os.path.exists(dicominfotxt):
            cmdstr = 'dcmdir-info-mgh %s > %s;' % (self.inputs.dicomdir, dicominfotxt)
            cmd.extend([cmdstr])
        for f in valid_inputs['dicomfiles']:
            head,fname = os.path.split(f)
            fname,ext  = os.path.splitext(fname)
            outfile = os.path.join(outdir,'.'.join((fname,self.inputs.out_type)))
            if not os.path.exists(outfile):
                single_cmd = '%s %s %s;' % (self.cmd, f, outfile)
                cmd.extend([single_cmd])
        self._cmdline =  ' '.join(cmd)
        return self._cmdline

    def outputs(self):
        return Bunch()

    def aggregate_outputs(self):
        outdir = self._get_outdir()
        outputs = self.outputs()
        if self.inputs.file_mapping:
            for field,template in self.inputs.file_mapping:
                setattr(outputs, field, sorted(glob(os.path.join(outdir,
                                                                 template))))
        return outputs

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
                      mandatory=True)
    init_reg = traits.Either(traits.Enum('spm', 'fsl', 'header'),
                              File(exists=True),argstr = '',
                       desc='initialize registration spm, fsl, header or existing File',
                              mandatory=True,)
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
            return '--o %s' % fname
        if name == 'init_reg':
            if os.path.isfile(value):
                return '--init-reg %s' % value
            else:
                return '--init-%s' % value
        return super(BBRegister, self)._format_arg(name, spec, value)
    
    def _gen_filename(self, name):
        if name == 'outregfile':
            return self._list_outputs()[name]
        return None    

class ApplyVolTransform(FSCommand):
    """Use FreeSurfer mri_vol2vol to apply a transform.

    Parameters
    ----------
    To see optional arguments
    ApplyVolTransform().inputs_help()

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import ApplyVolTransform
    >>> applyreg = ApplyVolTransform(tkreg='me.dat', sourcefile='foo.nii', fstarg=True)
    >>> applyreg.cmdline
    'mri_vol2vol --fstarg --mov foo.nii --reg me.dat --o foo_warped.nii'

    """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mri_vol2vol'

    def inputs_help(self):
        """Print command line documentation for mri_vol2vol."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    opt_map = {
        'sourcefile':         '--mov %s',
        'targfile':           '--targ %s',
        'outfile':            '--o %s',
        'fstarg':             '--fstarg',
        'tkreg':              '--reg %s',
        'fslreg':             '--fsl %s',
        'xfmreg':             '--xfm %s',
        'interp':             '--interp %s',
        'noresample':         '--no-resample',
        'inverse':            '--inv', 
        'flags':              '%s'}
    
    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='sourcefile', copy=False)]
        return info

    def _get_outfile(self):
        outfile = self.inputs.outfile
        if not outfile:
            outfile = fname_presuffix(self.inputs.sourcefile,
                                      suffix='_warped')
        return outfile
    
    def _parse_inputs(self):
        """validate fs bbregister options"""
        allargs = super(ApplyVolTransform, self)._parse_inputs(skip=('outfile'))
        outfile = self._get_outfile()
        if outfile:
            allargs.extend(['--o', outfile])
        return allargs
    
    def outputs(self):
        """
        outfile: filename
            Warped source file
        """
        return Bunch(outfile=None)

    def aggregate_outputs(self):
        outputs = self.outputs()
        outfile = self._get_outfile()
        if not glob(outfile):
            raise FileNotFoundError(outfile)
        outputs.outfile = outfile
        return outputs

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
    surface_fwhm = traits.Float(min=0,desc='surface FWHM in mm',argstr='--fwhm %d')
    vol_fwhm = traits.Float(min=0, argstr= '--vol-fwhm %d',
                            desc='volumesmoothing outside of surface')
    flags = traits.Str(desc='maps additional commands', argstr='%s')

class SmoothOutputSpec(FSTraitedSpec):
    outfile= File(exist=True,desc='smoothed input volume')	
         
class Smooth(NEW_FSCommand):
    """Use FreeSurfer mris_volsmooth to smooth a volume

    This function smoothes cortical regions on a surface and
    non-cortical regions in volume.

    Parameters
    ----------

    To see optional arguments
    Smooth().inputs_help()


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

