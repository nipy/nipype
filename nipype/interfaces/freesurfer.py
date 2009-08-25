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
from nipype.interfaces.base import Bunch, CommandLine
from nipype.utils.filemanip import fname_presuffix

def freesurferversion():
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

def fssubjectsdir(subjects_dir=None):
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
        os.environ['SUBJECTS_DIR'] = os.path.abspath(subjects_dir)
    subjects_dir = os.getenv('SUBJECTS_DIR')
    print 'SUBJECTS_DIR = %s'%subjects_dir
    return subjects_dir

class FSCommandLine(CommandLine):

    def __init__(self):
        super(FSCommandLine,self).__init__()
        self._cmdline = ''
        
    @property
    def cmdline(self):
        # This handles args like ['bet', '-f 0.2'] without crashing
        return self._cmdline

    def run(self):
        """Execute the command.
        
        Returns
        -------
        results : InterfaceResult
            A `InterfaceResult` object with a copy of self in `interface`

        """
        # This is expected to populate `_cmdline` for _runner to work
        self._compile_command()
        result = self._runner(cwd=self.inputs.get('cwd','.'))
        result.outputs = self.aggregate_outputs()
        return result
    
class Dicom2Nifti(FSCommandLine):
    """use fs mri_convert to convert dicom files to nifti-1 files

    Options
    -------

    To see optianl arguments
    Dicom2Nifti().inputs_help()


    Examples
    --------
    >>> cvt = freesurfer.Dicom2Nifti()
    >>> cvt.inputs.dicomdir = '/software/data/STUT/RAWDATA/TrioTim-35115-20090428-081900-234000/'
    >>> cvt.inputs.file_mapping = [('nifti','*.nii'),('info','dicom*.txt'),('dti','*dti.bv*')]
    >>> out = cvt.run()
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
            Example: [('niftifiles','*.nii'),('dtiinfo','*mghdti.bv*')]
        flags = unsupported flags, use at your own risk

        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        self.inputs = Bunch(dicomdir=None,
                            base_output_dir=None,
                            subject_dir_template=None,
                            subject_id=None,
                            file_mapping=None,
                            flags=None)

    def _parseinputs(self):
        """validate fsl bet options
        if set to None ignore
        """
        out_inputs = {'dicomfiles':None}
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.iteritems() if v is not None ]
        for opt in inputs:
            if opt is 'dicomdir':
                out_inputs['dicomfiles'] = glob(os.path.abspath(os.path.join(inputs[opt],'*-1.dcm')))
                continue
            if opt is 'base_output_dir':
                continue
            if opt is 'subject_dir_template':
                continue
            if opt is 'subject_id':
                continue
            if opt is 'file_mapping':
                continue
            if opt is 'flags':
                continue
            print 'option %s not supported'%(opt)
        
        return out_inputs

    def _compile_command(self):
        """validates fsl options and generates command line argument"""
        valid_inputs = self._parseinputs()
        subjid = self.inputs.subject_id
        if subjid is None:
            path,fname = os.path.split(valid_inputs['dicomfiles'][0])
            subjid = fname.split('-')[0]
        if self.inputs.subject_dir_template is not None:
            subjid  = self.inputs.subject_dir_template % subjid
        basedir=self.inputs.base_output_dir
        if basedir is None:
            basedir = os.path.abspath('.')
        outdir = os.path.abspath(os.path.join(basedir,subjid))
        cmd = []
        if not os.path.exists(outdir):
            cmdstr = 'mkdir %s;' % outdir
            cmd.extend([cmdstr])
        cmdstr = 'dcmdir-info-mgh %s > %s;' % (self.inputs.dicomdir,os.path.join(outdir,'dicominfo.txt'))
        cmd.extend([cmdstr])
        for f in valid_inputs['dicomfiles']:
            head,fname = os.path.split(f)
            fname,ext  = os.path.splitext(fname)
            outfile = os.path.join(outdir,''.join((fname,'.nii')))
            if not os.path.exists(outfile):
                single_cmd = '%s %s %s;' % (self.cmd, f, outfile)
                cmd.extend([single_cmd])
        self._cmdline =  ' '.join(cmd)
        return self._cmdline,outdir

    def aggregate_outputs(self):
        cmd,outdir = self._compile_command()
        outputs = Bunch()
        if self.inputs.file_mapping is not None:
            for field,template in self.inputs.file_mapping:
                outputs[field] = sorted(glob(os.path.join(outdir,template)))
        return outputs
        

class Resample(FSCommandLine):
    """use fs mri_convert to up or down-sample image files

    Options
    -------

    To see optianl arguments
    Resample().inputs_help()


    Examples
    --------
    >>> resampler = freesurfer.Resample()
    >>> resampler.inputs.infile = 'infile.nii'
    >>> resampler.voxel_size = [2,2,2]
    >>> out = resampler.run()
   """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mri_convert'


    def inputs_help(self):
        """
        Optional Parameters
        -------------------
        (all default to None and are unset)
             
        infile : string or list
            file(s) to resample
        voxel_size: 3-element list
            size of x, y and z voxels in mm of resampled image
        outfile_postfix : string
            string appended to input file name to generate output file
            name. Default: '_fsresample'
        flags = unsupported flags, use at your own risk

        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        self.inputs = Bunch(infile=None,
                            voxel_size=None,
                            outfile_postfix='_fsresample',
                            flags=None)

    def _parseinputs(self):
        """validate fsl bet options
        if set to None ignore
        """
        out_inputs = {'infile':[]}
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.iteritems() if v is not None ]
        for opt in inputs:
            if opt is 'infile':
                out_inputs['infile'] = inputs[opt]
                if type(inputs[opt]) is not type([]):
                    out_inputs['infile'] = [inputs[opt]]
                continue
            if opt is 'voxel_size':
                continue
            if opt is 'outfile_postfix':
                continue
            if opt is 'flags':
                continue
            print 'option %s not supported'%(opt)
        
        return out_inputs

    def outputs_help(self):
        """
        outfile : string or list
            resampled file(s)
        """
        print self.outputs_help.__doc__

    def _compile_command(self):
        """validates fsl options and generates command line argument"""
        valid_inputs = self._parseinputs()
        cmd = []
        vs = self.inputs.voxel_size
        outfile = []
        for i,f in enumerate(valid_inputs['infile']):
            path,fname = os.path.split(f)
            outfile.insert(i,fname_presuffix(fname,suffix=self.inputs.outfile_postfix))
            outfile[i] = os.path.abspath(os.path.join(self.inputs.get('cwd','.'),outfile[i]))
            single_cmd = '%s -vs %d %d %d %s %s;' % (self.cmd, vs[0],vs[1],vs[2], f, outfile[i])
            cmd.extend([single_cmd])
        self._cmdline =  ' '.join(cmd)
        return self._cmdline

    def aggregate_outputs(self):
        outputs = Bunch(outfile=[])
        for i,f in enumerate(self.inputs.infile):
            path,fname = os.path.split(f)
            f = fname_presuffix(fname,suffix=self.inputs.outfile_postfix)
            f = os.path.abspath(os.path.join(self.inputs.get('cwd','.'),f))
            assert glob(f)==[f], 'outputfile %s was not generated'%f
            outputs.outfile.insert(i,f)
        if len(outfile)==1:
            outputs.outfile = outputs.outfile[0]
        return outputs
        

class ReconAll(FSCommandLine):
    """use fs recon-all to generate surfaces and parcellations of
    structural data from an anatomical image of a subject.

    Options

    To see optianl arguments
    ReconAll().inputs_help()


    Examples
    --------
    
    >>> reconall = freesurfer.ReconAll()
    >>> reconall.inputs.subject_id = 'foo'
    >>> reconall.inputs.directive  = '-all'
    >>> reconall.inputs.parent_dir = '.'
    >>> reconall.inputs.T1file = 'structfile.nii'
    >>> out = reconall.run()
   """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'recon-all'


    def inputs_help(self):
        """
        Parameters
        ----------
        (all default to None and are unset)
        subject_id: string or int
            Identifier for subject
        directive: string
            Which part of the process to run 

            Fully-Automated Directive


            -all           : performs all stages of cortical reconstruction
            -autorecon-all : same as -all

            Manual-Intervention Workflow Directives


            -autorecon1    : process stages 1-5 (see below)
            -autorecon2    : process stages 6-24
                   after autorecon2, check final surfaces:
                     a. if wm edit was required, then run -autorecon2-wm
                     b. if control points added, then run -autorecon2-cp
                     c. if edits made to correct pial, then run -autorecon2-pial
                     d. proceed to run -autorecon3
            -autorecon2-cp : process stages 12-24 (uses -f w/ mri_normalize, -keep w/ mri_seg)
            -autorecon2-wm : process stages 15-24
            -autorecon2-inflate1 : 6-18
            -autorecon2-perhemi : tess, sm1, inf1, q, fix, sm2, inf2, finalsurf, ribbon
            -autorecon3    : process stages 25-31


        Parameters
        ----------
        (all default to None and are unset)
             
        T1files: filename(s)
            T1 file or list of files to extract surfaces from. The T1
            files must come from the same subject
        hemi: string
            just do lh or rh (default is to do both)
        parent_dir: string
            defaults to SUBJECTS_DIR environment variable. If the variable is
            not set, it defaults to current working directory.
        test:
            Do everything but execute each command
        flags:
            unsupported flags, use at your own risk
        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        self.inputs = Bunch(subject_id=None,
                            directive=None,
                            T1files=None,
                            hemi=None,
                            parent_dir=fssubjectsdir(),
                            test=None,
                            flags=None)

    def _parseinputs(self):
        """validate fsl bet options
        if set to None ignore
        """
        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.iteritems() if v is not None ]
        for opt in inputs:
            if opt is 'subject_id':
                out_inputs.extend(['-subjid',inputs[opt]])
                continue
            if opt is 'directive':
                out_inputs.extend([inputs[opt]])
                continue
            if opt is 'T1files':
                if type(inputs[opt]) is not type([]):
                    files = [inputs[opt]]
                else:
                    files = inputs[opt]
                for f in files:
                    out_inputs.extend(['-i',f])
                continue
            if opt is 'hemi':
                out_inputs.extend(['-hemi',inputs[opt]])
                continue
            if opt is 'parent_dir':
                out_inputs.extend(['-sd',os.path.abspath(inputs[opt])])
                continue
            if opt is 'flags':
                out_inputs.extend([inputs[opt]])
            print 'option %s not supported'%(opt)
        
        return out_inputs

    def outputs_help(self):
        """
        No outputs
        """
        print self.outputs_help.__doc__

    def _compile_command(self):
        """validates fsl options and generates command line argument"""
        valid_inputs = self._parseinputs()
        allargs =  [self.cmd] + valid_inputs
        self._cmdline = ' '.join(allargs)
        return self._cmdline
        
    def aggregate_outputs(self):
        return None

class BBRegister(FSCommandLine):
    """use fs bbregister to register a volume two a surface mesh

    This program performs within-subject, cross-modal registration using a
    boundary-based cost function. The registration is constrained to be 6
    DOF (rigid). It is required that you have an anatomical scan of the
    subject that has been analyzed in freesurfer.

    Options
    -------

    To see optional arguments
    BBRegister().inputs_help()


    Examples
    --------
   """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'bbregister'


    def inputs_help(self):
        """
        Parameters
        ----------
        
        (all default to None and are unset)
        subject_id: string or int
            Identifier for subject
        sourcefile: string
            Filename of image volume that will be registered to
        surface
        initialize_with: string
            One of the following options is required.
            --init-fsl : initialize the registration with FSL
            --init-spm : initialize the registration with SPM
            --init-header : initialize the registration based on header goemetry
            --init-reg initregfile : explicitly pass registration
        contrast_type: string
            One of the following is required.
            --t1 : assume t1 contrast, ie, WM brighter than GM
            --t2 : assume t2 contrast, ie, GM brighter than WM (default)
            --bold : same as --t2
            --dti  : same as --t2

        Parameters
        ----------
        
        (all default to None and are unset)
        outregfile: filename
            Name of output registration file. By default the extension
        of the sourcefile is replaced by _reg_[subject_id].dat
        outfile: boolean or filename
            Resampled source is saved as outfile. If set to True, an
        outputfile is created with _bbout added to the filename.
        flags:
            unsupported flags, use at your own risk
        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        self.inputs = Bunch(subject_id=None,
                            sourcefile=None,
                            initialize_with=None,
                            contrast_type=None,
                            outregfile=None,
                            outfile=None,
                            flags=None)

    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='sourcefile',copy=False)]
        return info
    
    def _parseinputs(self):
        """validate bbregister options
        if set to None ignore
        """
        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.iteritems() if v is not None ]
        for opt in inputs:
            if opt is 'subject_id':
                out_inputs.extend(['--s',inputs[opt]])
                continue
            if opt is 'sourcefile':
                out_inputs.extend(['--mov',inputs[opt]])
                continue
            if opt is 'initialize_with':
                out_inputs.extend([inputs[opt]])
                continue
            if opt is 'contrast_type':
                out_inputs.extend([inputs[opt]])
                continue
            if opt is 'outregfile':
                out_inputs.extend(['--reg',inputs[opt]])
                continue
            if opt is 'outfile':
                if type(inputs[opt]) is type(''):
                    out_inputs.extend(['--o',inputs[opt]])
                continue
            if opt is 'flags':
                out_inputs.extend([inputs[opt]])
            print 'option %s not supported'%(opt)
        if self.inputs.outregfile is None:
            out_inputs.extend(['--reg',fname_presuffix(self.inputs.sourcefile,
                                                       suffix='_reg_%s.dat'%self.inputs.subject_id,
                                                       use_ext=False)])
        if self.inputs.outfile is True:
            out_inputs.extend(['--o',fname_presuffix(self.inputs.sourcefile,suffix='_bbout'%self.inputs.subject_id)])
        return out_inputs

    def _compile_command(self):
        """validates fsl options and generates command line argument"""
        valid_inputs = self._parseinputs()
        allargs =  [self.cmd] + valid_inputs
        self._cmdline = ' '.join(allargs)
        return self._cmdline

    def outputs_help(self):
        """
        outregfile: filename
            Output registration file
        outfile: filename
            Registered and resampled source file
        """
        print self.outputs_help.__doc__

    def aggregate_outputs(self):
        outputs = Bunch(outregfile=None,
                        outfile=None)
        if self.inputs.outregfile is None:
            outregfile = fname_presuffix(self.inputs.sourcefile,
                                         suffix='_reg_%s.dat'%self.inputs.subject_id,
                                         use_ext=False)
        else:
            outregfile = self.inputs.outregfile
        assert len(glob(outregfile))==1, "No output registration file %s created"%outregfile
        outputs.outregfile = outregfile
        if self.inputs.outfile is True:
            outfile = glob(fname_presuffix(self.inputs.sourcefile,suffix='_bbout'%self.inputs.subject_id))
            assert len(outfile)==1, "No output file %s created"%outfile
            outputs.outfile = outfile[0]
        if type(self.inputs.outfile) == type(''):
            outfile = glob(self.inputs.outfile)
            assert len(outfile)==1, "No output file %s created"%outfile
            outputs.outfile = outfile[0]
    
        
