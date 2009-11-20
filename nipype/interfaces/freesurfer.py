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
from nipype.interfaces.fsl import FSLCommand
from nipype.utils.docparse import get_doc
from nipype.utils.filemanip import fname_presuffix, filename_to_list

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
    return subjects_dir

class FSCommandLine(CommandLine):

    def __init__(self):
        super(FSCommandLine,self).__init__()
        self._cmdline = ''
        
    @property
    def cmdline(self):
        # This handles args like ['bet', '-f 0.2'] without crashing
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
        result = self._runner(cwd=self.inputs.get('cwd','.'))
        if result.runtime.returncode == 0:
            result.outputs = self.aggregate_outputs()
        return result
    
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
    """Use FreeSurfer mri_convert to up or down-sample image files

    Parameters
    ----------
    To see optional arguments
    Resample().inputs_help()


    Examples
    --------
    >>> from nipype.interfaces import freesurfer
    >>> resampler = freesurfer.Resample()
    >>> resampler.inputs.infile = 'infile.nii'
    >>> resampler.inputs.voxel_size = [2, 2, 2]
    >>> out = resampler.run()
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
        [inputs.update({k:v}) for k, v in self.inputs.iteritems() 
         if v is not None ]
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
            outfile.insert(i, fname_presuffix(fname, suffix=self.inputs.outfile_postfix))
            outfile[i] = os.path.abspath(os.path.join(self.inputs.get('cwd','.'),outfile[i]))
            single_cmd = '%s -vs %d %d %d %s %s;' % (self.cmd, vs[0],vs[1],vs[2], f, outfile[i])
            cmd.extend([single_cmd])
        self._cmdline =  ' '.join(cmd)
        return self._cmdline

    def aggregate_outputs(self):
        outputs = Bunch(outfile=[])
        for i,f in enumerate(filename_to_list(self.inputs.infile)):
            path,fname = os.path.split(f)
            f = fname_presuffix(fname, suffix=self.inputs.outfile_postfix)
            f = os.path.abspath(os.path.join(self.inputs.get('cwd','.'),f))
            assert glob(f)==[f], 'outputfile %s was not generated'%f
            outputs.outfile.insert(i,f)
        if len(outfile)==1:
            outputs.outfile = outputs.outfile[0]
        return outputs
        

class ReconAll(FSCommandLine):
    """Use FreeSurfer recon-all to generate surfaces and parcellations of
    structural data from an anatomical image of a subject.

    Parameters
    ----------

    To see optional arguments
    ReconAll().inputs_help()


    Examples
    --------
    >>> from nipype.interfaces import freesurfer
    >>> reconall = freesurfer.ReconAll()
    >>> reconall.inputs.subject_id = 'foo'
    >>> reconall.inputs.directive  = '-all'
    >>> reconall.inputs.parent_dir = '.'
    >>> reconall.inputs.T1files = 'structfile.nii'
    >>> out = reconall.run() # doctest +SKIP
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
                            parent_dir=None,
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

        if '-sd' not in out_inputs:
                out_inputs.extend(['-sd',os.path.abspath(fssubjectsdir())])

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

class BBRegister(FSLCommand):
    """Use FreeSurfer bbregister to register a volume two a surface mesh

    This program performs within-subject, cross-modal registration using a
    boundary-based cost function. The registration is constrained to be 6
    DOF (rigid). It is required that you have an anatomical scan of the
    subject that has been analyzed in freesurfer.

    Parameters
    ----------

    To see optional arguments
    BBRegister().inputs_help()


    Examples
    --------
    >>> from nipype.interfaces.freesurfer import BBRegister
    >>> bbreg = BBRegister(subject_id='me', sourcefile='foo.nii', \
                           init_header=True, t2_contrast=True)
    >>> bbreg.cmdline
    'bbregister --init-header --mov foo.nii --s me --t2 --reg foo_bbreg_me.dat'

   """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'bbregister'


    def inputs_help(self):
        """Print command line documentation for bbregister."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(subject_id=None,
                            sourcefile=None,
                            init_spm=None,
                            init_fsl=None,
                            init_header=None,
                            init_reg=None,
                            contrast_type=None,
                            outregfile=None,
                            outfile=None,
                            flags=None)

    opt_map = {
        'subject_id':         '--s %s',
        'sourcefile':         '--mov %s',
        'init_spm':           '--init-spm',
        'init_fsl':           '--init-fsl',
        'init_header':        '--init-header',
        'init_reg':           '--init-reg %s',
        't1_contrast':        '--t1',
        't2_contrast':        '--t2',
        'outregfile':         '--reg %s',
        'outfile':            '--o %s',
        'flags':              '%s'}
    
    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='sourcefile',copy=False)]
        return info
    
    def _parse_inputs(self):
        """validate fs bbregister options"""
        allargs = super(BBRegister, self)._parse_inputs(skip=('outfile'))

        # Add infile and outfile to the args if they are specified
        if self.inputs.outregfile is None and self.inputs.sourcefile is not None:
            allargs.extend(['--reg',fname_presuffix(self.inputs.sourcefile,
                                                       suffix='_bbreg_%s.dat'%self.inputs.subject_id,
                                                       use_ext=False)])
        if self.inputs.outfile is True:
            allargs.extend(['--o',fname_presuffix(self.inputs.sourcefile,suffix='_bbreg')])
        return allargs
    
    def run(self, **inputs):
        """Execute the command.
        """
        results = self._runner()
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs()

        return results        

    def outputs(self):
        """
        outregfile: filename
            Output registration file
        outfile: filename
            Registered and resampled source file
        """
        outputs = Bunch(outregfile=None,
                        outfile=None)
        return outputs

    def aggregate_outputs(self):
        outputs = self.outputs()
        if self.inputs.outregfile is None:
            outregfile = fname_presuffix(self.inputs.sourcefile,
                                         suffix='_bbreg_%s.dat'%self.inputs.subject_id,
                                         use_ext=False)
        else:
            outregfile = self.inputs.outregfile
        assert len(glob(outregfile))==1, "No output registration file %s created"%outregfile
        outputs.outregfile = outregfile
        if self.inputs.outfile is True:
            outfile = glob(fname_presuffix(self.inputs.sourcefile,suffix='_bbreg'))
            assert len(outfile)==1, "No output file %s created"%outfile
            outputs.outfile = outfile[0]
        if type(self.inputs.outfile) == type(''):
            outfile = glob(self.inputs.outfile)
            assert len(outfile)==1, "No output file %s created"%outfile
            outputs.outfile = outfile[0]
        return outputs

class ApplyVolTransform(FSLCommand):
    """Use FreeSurfer mri_vol2vol to apply a transform.

    Parameters
    ----------
    To see optional arguments
    ApplyVolTransform().inputs_help()

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import ApplyVolTransform
    >>> applyreg = ApplyVolTransform(tkreg='me.dat', sourcefile='foo.nii', \
                                     fstarg=True)
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

    def _populate_inputs(self):
        self.inputs = Bunch(sourcefile=None,
                            targfile=None,
                            fstarg=None,
                            outfile=None,
                            tkreg=None,
                            fslreg=None,
                            xfmreg=None,
                            noresample=None,
                            inverse=None,
                            flags=None)

    opt_map = {
        'sourcefile':         '--mov %s',
        'targfile':           '--targ %s',
        'outfile':            '--o %s',
        'fstarg':             '--fstarg',
        'tkreg':              '--reg %s',
        'fslreg':             '--fsl %s',
        'xfmreg':             '--xfm %s',
        'noresample':         '--no-resample',
        'inverse':            '--inv', 
        'flags':              '%s'}
    
    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='sourcefile', copy=False)]
        return info
    
    def _parse_inputs(self):
        """validate fs bbregister options"""
        allargs = super(ApplyVolTransform, self)._parse_inputs()

        # Add outfile to the args if not specified
        if self.inputs.outfile is None:
            allargs.extend(['--o', fname_presuffix(self.inputs.sourcefile, 
                                                   suffix='_warped')])
        return allargs
    
    def run(self, **inputs):
        """Execute the command.
        """
        results = self._runner()
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs()

        return results        

    def outputs(self):
        """
        outfile: filename
            Warped source file
        """
        return Bunch(outfile=None)

    def aggregate_outputs(self):
        outputs = self.outputs()
        if self.inputs.outfile is True:
            outfile = glob(fname_presuffix(self.inputs.sourcefile,
                                           suffix='_warped'))
            assert len(outfile)==1, "No output file %s created"%outfile
            outputs.outfile = outfile[0]
        if type(self.inputs.outfile) == type(''):
            outfile = glob(self.inputs.outfile)
            assert len(outfile)==1, "No output file %s created"%outfile
            outputs.outfile = outfile[0]
        return outputs

        
class Smooth(FSLCommand):
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
    >>> smoothvol = Smooth(sourcefile='foo.nii', regfile='reg.dat', \
                           surface_fwhm=10, vol_fwhm=6)
    >>> smoothvol.cmdline
    'mris_volsmooth --reg reg.dat --i foo.nii --fwhm 10 --vol-fwhm 6 --o foo_surfsmooth.nii'
   """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mris_volsmooth'

    def inputs_help(self):
        """Print command line documentation for mris_volsmooth."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(sourcefile=None,
                            regfile=None,
                            outfile=None,
                            surface_fwhm=None,
                            vol_fwhm=None,
                            flags=None)

    opt_map = {
        'sourcefile':         '--i %s',
        'regfile':            '--reg %s',
        'outfile':            '--o %s',
        'surface_fwhm':       '--fwhm %d',
        'vol_fwhm':           '--vol-fwhm %d',
        'flags':              '%s'}
    
    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='sourcefile',copy=False)]
        return info
    
    def _parse_inputs(self):
        """validate fs bbregister options"""
        allargs = super(Smooth, self)._parse_inputs()

        # Add outfile to the args if not specified
        if self.inputs.outfile is None:
            allargs.extend(['--o', fname_presuffix(self.inputs.sourcefile,
                                                   suffix='_surfsmooth')])
        return allargs
    
    def run(self, **inputs):
        """Execute the command.
        """
        results = self._runner()
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs()

        return results        

    def outputs(self):
        """
        outfile: filename
            Smoothed input volume
        """
        return Bunch(outfile=None)

    def aggregate_outputs(self):
        outputs = self.outputs()
        if self.inputs.outfile is None:
            outfile = glob(fname_presuffix(self.inputs.sourcefile,
                                           suffix='_surfsmooth'))
            assert len(outfile)==1, "No output file %s created"%outfile
            outputs.outfile = outfile[0]
        if type(self.inputs.outfile) == type(''):
            outfile = glob(self.inputs.outfile)
            assert len(outfile)==1, "No output file %s created"%outfile
            outputs.outfile = outfile[0]
        return outputs

        
class SurfConcat(FSLCommand):
    """Use FreeSurfer mris_preproc to prepare a group of contrasts for
    a second level analysis
    
    Parameters
    ----------

    To see optional arguments
    SurfConcat().inputs_help()


    Examples
    --------
   """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mris_preproc'

    def inputs_help(self):
        """Print command line documentation for mris_preproc."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(target=None,
                            hemi=None,
                            outfile=None,
                            outprefix='surfconcat',
                            conimages=None,
                            regs=None,
                            flags=None)

    opt_map = {
        'target':             '--target %s',
        'hemi':               '--hemi %s',
        'outfile':            '--out %s',
        'outprefix':          None,
        'conimages':          '--iv %s',
        'regs':               '--iv %s',
        'flags':              '%s'}
#mris_preproc --target fsaverage --hemi lh --out test_spm_lh.mgh \
#--ivp ../SAD_STUDY_Block/data/SAD_019/firstlevel_novelfaces/con_0001.hdr spm2fsfast/SAD_019_register.dat \

    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = []
        return info
    
    def _parse_inputs(self):
        """validate fs surfconcat options"""
        allargs = super(SurfConcat, self)._parse_inputs(skip=('outfile','outprefix','conimages','regs'))

        # Add outfile to the args if not specified
        if self.inputs.outfile is None:
            fname = os.path.join(os.getcwd(),'_'.join((self.inputs.outprefix,
                                                           self.inputs.target,
                                                           '.'.join((self.inputs.hemi,'mgh')))))
            allargs.extend(['--out', fname])
        for i,conimg in enumerate(self.inputs.conimages):
            allargs.extend(['--iv', conimg, self.inputs.regs[i]])
        return allargs
    
    def run(self, **inputs):
        """Execute the command.
        """
        results = self._runner()
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs()

        return results        

    def outputs(self):
        """
        outfile: filename
            Concatenated volume
        """
        return Bunch(outfile=None)

    def aggregate_outputs(self):
        outputs = self.outputs()
        if self.inputs.outfile is None:
            fname = os.path.join(os.getcwd(),'_'.join((self.inputs.outprefix,
                                                           self.inputs.target,
                                                           '.'.join((self.inputs.hemi,'mgh')))))
            outfile = glob(fname)
            assert len(outfile)==1, "No output file %s created"%outfile
            outputs.outfile = outfile[0]
        if type(self.inputs.outfile) == type(''):
            outfile = glob(self.inputs.outfile)
            assert len(outfile)==1, "No output file %s created"%outfile
            outputs.outfile = outfile[0]
        return outputs

class OneSampleTTest(FSLCommand):
    """Use FreeSurfer mri_glmfit to prepare a group of contrasts for
    a second level analysis
    
    Parameters
    ----------

    To see optional arguments
    SurfConcat().inputs_help()


    Examples
    --------
   """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'mri_glmfit'

    def inputs_help(self):
        """Print command line documentation for mris_preproc."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def _populate_inputs(self):
        self.inputs = Bunch(surf=None,
                            hemi=None,
                            outdir=None,
                            outdirprefix='glm',
                            funcimage=None,
                            onesample=None,
                            design=None,
                            flags=None)

    opt_map = {
        'surf':             '--surf %s',
        'hemi':               '%s',
        'outdir':             '--glmdir %s',
        'outdirprefix':          None,
        'funcimage':          '--y %s',
        'onesample':          '--osgm',
        'design':             '--X %s',
        'flags':              '%s'}

    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = []
        return info
    
    def _parse_inputs(self):
        """validate fs onesamplettest options"""
        allargs = super(OneSampleTTest, self)._parse_inputs(skip=('surf','hemi','outdir','outdirprefix',))

        # Add outfile to the args if not specified
        allargs.extend(['--surf',self.inputs.surf,self.inputs.hemi])
        if self.inputs.outdir is None:
            outdir = os.getcwd()
            allargs.extend(['--glmdir', outdir])
        return allargs
    
    def run(self, cwd=None,**inputs):
        """Execute the command.
        """
        results = self._runner()
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs()

        return results        

    def outputs(self):
        """
        """
        return Bunch()

    def aggregate_outputs(self):
        return self.outputs()
        
