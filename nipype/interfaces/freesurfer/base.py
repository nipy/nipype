"""The freesurfer module provides basic functions for interfacing with
freesurfer tools.

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

import numpy as np

from nipype.interfaces.base import Bunch, CommandLine, OptMapCommand
from nipype.utils.docparse import get_doc
from nipype.utils.filemanip import FileNotFoundError, fname_presuffix
from nipype.interfaces.base import NEW_CommandLine, traits, TraitedSpec,\
    BaseInterfaceInputSpec, isdefined


class FSInfo(object):
    __subjectsdir = os.getenv('SUBJECTS_DIR')
    @staticmethod
    def version():
        """Check for freesurfer version on system
    
        Parameters
        ----------
        
        None
    
        Returns
        -------
        
        version : string
           version number as string 
           or None if freesurfer version not found
    
        """
        # find which freesurfer is being used....and get version from
        # /path/to/freesurfer/
        fs_home = os.getenv('FREESURFER_HOME')
        if fs_home is None:
            return fs_home
        versionfile = os.path.join(fs_home,'build-stamp.txt')
        if not os.path.exists(versionfile):
            return None
        fid = open(versionfile,'rt')
        version = fid.readline()
        fid.close()
        return version.split('-v')[1].strip('\n')
    
    @classmethod
    def subjectsdir(cls, subjects_dir=None):
        """Check and or set the global SUBJECTS_DIR
        
        Parameters
        ----------
        
        subjects_dir :  string
            The system defined subjects directory
    
        Returns
        -------
        
        subject_dir : string
            Represents the current environment setting of SUBJECTS_DIR
    
        """
        if subjects_dir is not None:
            # set environment setting
            cls.__subjectsdir = os.path.abspath(subjects_dir)
        return cls.__subjectsdir
    
class FSCommand(OptMapCommand):
    '''General support for FreeSurfer commands'''
    
    def __init__(self, *args, **inputs):
        super(FSCommand,self).__init__(**inputs)
        
        if 'subjectsdir' not in inputs or inputs['subjectsdir'] == None:
            subjectsdir = FSInfo.subjectsdir()
        else:
            subjectsdir = os.path.abspath(inputs['subjectsdir'])
        self._subjectsdir = subjectsdir
        
    def run(self):
        """Execute the command.

        Returns
        -------
        results : InterfaceResult
            An :class:`nipype.interfaces.base.InterfaceResult` object
            with a copy of self in `interface`

        """
        self._environ = {'SUBJECTS_DIR':self._subjectsdir}
        return super(FSCommand,self).run()

class FSCommandLine(CommandLine):

    def __init__(self):
        super(FSCommandLine,self).__init__()
        self._cmdline = None
        
    @property
    def cmdline(self):
        # This handles args like ['bet', '-f 0.2'] without crashing
        if not self._cmdline:
            self._cmdline = self._compile_command()
        return self._cmdline

    def run(self, **inputs):
        """Execute the command.
        
        Returns
        -------
        results : InterfaceResult
            A `InterfaceResult` object with a copy of self in `interface`

        """
        # This is expected to populate `_cmdline` for _runner to work
        self._compile_command()
        result = self._runner(cwd=os.getcwd())
        if result.runtime.returncode == 0:
            result.outputs = self.aggregate_outputs()
        return result
    
    def _compile_command(self):
        """Virtual function"""
        raise NotImplementedError(
                'Subclasses of FSCommandLine must implement _compile_command')

class DicomDirInfo(FSCommand):
    """uses mri_parse_sdcmdir to get information from dicom
    directories
    
    Parameters
    ----------
    To see optional arguments
    DicomDirInfo().inputs_help()


    Examples
    --------

    >>> from nipype.interfaces import freesurfer
    >>> dcminfo = freesurfer.DicomDirInfo()
    >>> dcminfo.inputs.dicomdir = 'dicomdir'
    >>> dcminfo.inputs.outfile = 'dicominfo.txt'
    >>> dcminfo.inputs.sortbyrun = True
    >>> dcminfo.inputs.summarize = True
    >>> dcminfo.cmdline
    'mri_parse_sdcmdir --d dicomdir --o dicominfo.txt --sortbyrun --summarize'
    
   """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mri_parse_sdcmdir'

    def inputs_help(self):
        """Print command line documentation for mri_parse_sdcmdir."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    opt_map = {
        'dicomdir':       '--d %s',
        'outfile':        '--o %s',
        'sortbyrun':      '--sortbyrun',
        'summarize':      '--summarize',  
        'flags':           '%s'}

    def _get_outfile_name(self):
        return os.path.join(os.getcwd(),'dicominfo.txt')
    
    def _parse_inputs(self):
        """validate fs bbregister options"""
        allargs = super(DicomDirInfo, self)._parse_inputs()
        # Add outfile to the args if not specified
        if not self.inputs.outfile:
            allargs.extend(['--o', self._get_outfile_name()])
        return allargs
    
    def run(self, dicomdir=None, **inputs):
        """Execute the command.
        """
        if dicomdir:
            self.inputs.dicomdir = dicomdir
        if not self.inputs.dicomdir:
            raise AttributeError('DicomDirInfo requires a dicomdir input')
        self.inputs.update(**inputs)
        return super(DicomDirInfo, self).run()

    def outputs(self):
        """
        dicominfo: filename
            file containing dicom information
        """
        return Bunch(dicominfo=None)

    def aggregate_outputs(self):
        outputs = self.outputs()
        if not self.inputs.outfile:
            outfile = self._get_outfile_name()
        if isinstance(self.inputs.outfile,str):
            outfile = self.inputs.outfile
        try:
            outputs.dicominfo = glob(outfile)[0]
        except IndexError:
            raise FileNotFoundError(outfile)
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

################
# NEW CLASSES
################

class Info(object):
    """Handle freesurfer subject directory and version information.
    """
    
    @staticmethod
    def version():
        """Check for freesurfer version on system
    
        Parameters
        ----------
        
        None
    
        Returns
        -------
        
        version : string
           version number as string 
           or None if freesurfer version not found
    
        """
        # find which freesurfer is being used....and get version from
        # /path/to/freesurfer/
        fs_home = os.getenv('FREESURFER_HOME')
        if fs_home is None:
            return fs_home
        versionfile = os.path.join(fs_home,'build-stamp.txt')
        if not os.path.exists(versionfile):
            return None
        fid = open(versionfile,'rt')
        version = fid.readline()
        fid.close()
        return version #.split('-v')[1].strip('\n')
    
    @classmethod
    def subjectsdir(cls):
        """Check and or set the global SUBJECTS_DIR
        
        Parameters
        ----------
        
        subjects_dir :  string
            The system defined subjects directory
    
        Returns
        -------
        
        subject_dir : string
            Represents the current environment setting of SUBJECTS_DIR
    
        """
        if cls.version():
            return os.environ['SUBJECTS_DIR']
        return None


class FSTraitedSpec(BaseInterfaceInputSpec):
    subjectsdir =  traits.Directory(exists=True, desc='subjects directory')
    
class NEW_FSCommand(NEW_CommandLine):
    '''General support for FS commands. Every FS command accepts
    'subjectsdir' input. For example:
    '''
    
    input_spec = FSTraitedSpec
    
    _subjectsdir = None

    def __init__(self, **inputs):
        super(NEW_FSCommand, self).__init__(**inputs)
        self.inputs.on_trait_change(self._subjectsdir_update, 'subjectsdir')
        if not self._subjectsdir:
            self._subjectsdir = Info.subjectsdir()
        if not isdefined(self.inputs.subjectsdir) and self._subjectsdir:
            self.inputs.subjectsdir = self._subjectsdir
        self._subjectsdir_update()

    def _subjectsdir_update(self):
        if self.inputs.subjectsdir:
            self.inputs.environ.update({'SUBJECTS_DIR':
                                            self.inputs.subjectsdir})
    
    @classmethod
    def set_default_subjectsdir(cls, subjectsdir):
        cls._subjectsdir = subjectsdir

    def _gen_fname(self, basename, fname=None, cwd=None, suffix='_fs', use_ext=True):
        '''Define a generic mapping for a single outfile

        The filename is potentially autogenerated by suffixing inputs.infile

        Parameters
        ----------
        basename : string (required)
            filename to base the new filename on
        fname : string
            if not None, just use this fname
        cwd : string
            prefix paths with cwd, otherwise os.getcwd()
        suffix : string
            default suffix
        '''
        if basename == '':
            msg = 'Unable to generate filename for command %s. ' % self.cmd
            msg += 'basename is not set!'
            raise ValueError(msg)
        if cwd is None:
            cwd = os.getcwd()
        fname = fname_presuffix(basename, suffix=suffix,
                                use_ext=use_ext, newpath=cwd)
        return fname

