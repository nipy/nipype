"""The spm module provides basic functions for interfacing with matlab
and spm to access spm tools.

These functions include:
    
* Realign: within-modality registration

* Coregister: between modality registration
    
* Normalize: non-linear warping to standard space

* Segment: bias correction, segmentation

* Smooth: smooth with Gaussian kernel

"""
__docformat__ = 'restructuredtext'

# Standard library imports
import os
from glob import glob
from copy import deepcopy
import re

# Third-party imports
import numpy as np
from scipy.io import savemat

# Local imports
from nipype.interfaces.base import Bunch, InterfaceResult, Interface
from nipype.utils import setattr_on_read
from nipype.externals.pynifti import load
from nipype.interfaces.matlab import MatlabCommandLine
from nipype.utils.filemanip import (fname_presuffix, fnames_presuffix, 
                                    filename_to_list, list_to_filename,
                                    loadflat)
from nipype.utils.spm_docs import grab_doc
import logging
logger = logging.getLogger('spmlogger')

def scans_for_fname(fname):
    """Reads a nifti file and converts it to a numpy array storing
    individual nifti volumes
    
    Opens images so will fail if they are not found
    """
    if isinstance(fname,list):
        scans = np.zeros((len(fname),),dtype=object)
        for sno,f in enumerate(fname):
            scans[sno] = '%s,1'%f
        return scans
    img = load(fname)
    if len(img.get_shape()) == 3:
        return np.array(('%s,1'%fname,),dtype=object)
    else:
        n_scans = img.get_shape()[3]
        scans = np.zeros((n_scans,),dtype=object)
        for sno in range(n_scans):
            scans[sno] = '%s,%d'% (fname, sno+1)
        return scans

def scans_for_fnames(fnames,keep4d=False,separate_sessions=False):
    """Converts a list of files to a concatenated numpy array for each
    volume.

    keep4d : boolean
        keeps the entries of the numpy array as 4d files instead of
        extracting the individual volumes.
    separate_sessions: boolean
        if 4d nifti files are being used, then separate_sessions
        ensures a cell array per session is created in the structure.
    """
    flist = None
    if separate_sessions or keep4d:
        flist = np.zeros((len(fnames),),dtype=object)
    for i,f in enumerate(fnames):
        if separate_sessions:
            if keep4d:
                flist[i] = np.array([f],dtype=object)
            else:
                flist[i] = scans_for_fname(f)
        else:
            if keep4d:
                flist[i] = f
            else:
                scans = scans_for_fname(f)
                if flist is None:
                    flist = scans
                else:
                    flist = np.concatenate((flist,scans))
    return flist

class SpmInfo(object):
    """ Return the path to the spm directory in the matlab path
        If path not found, prints error asn returns None
    """
    __path = None
    @classmethod
    def spm_path(cls):
        if cls.__path == None:
            mlab = MatlabCommandLine()
            mlab.inputs.script_name = 'spminfo'
            mlab.inputs.script_lines = """
    if isempty(which('spm')), throw(MException('SPMCheck:NotFound','SPM not in matlab path'));end;
    spm_path = spm('dir');
    fprintf(1, '<PATH>%s</PATH>', spm_path);
    """
            mlab.inputs.mfile = False
            out = mlab.run()
            if out.runtime.returncode == 0:
                path = re.match('<PATH>(.*)</PATH>',out.runtime.stdout[out.runtime.stdout.find('<PATH>'):])
                if path is not None:
                    path = path.groups()[0]
                cls.__path = path
            else:
                print out.runtime.stderr
                return None
            
        return cls.__path

class SpmMatlabCommandLine(MatlabCommandLine):
    """ Extends the `MatlabCommandLine` class to handle SPM specific
    formatting of matlab scripts.
    """

    opt_map = {}

    def __init__(self, matlab_cmd=None, **inputs): 
        super(SpmMatlabCommandLine,self).__init__(**inputs)
        self.mfile = True

    @property
    def jobtype(self):
        """the jobtype used by spm/matlab
        to specify the jobtype to run
        jobs{1}.jobtype{1}.jobname"""
        return 'jobtype' 

    @property
    def jobname(self):
        """the jobname used by spm/matlab
        to specify the jobname to run
        jobs{1}.jobtype{1}.jobname"""
        return 'jobname' 

    def _use_mfile(self, use_mfile):
        """boolean,
        if true generates a matlab <filename>.m file
        if false generates a binary .mat file
        """
        self.mfile = use_mfile

    def run(self, **inputs):
        """Executes the SPM function using MATLAB
        """
        results = super(SpmMatlabCommandLine,self).run()
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs() 
        return results

    def _populate_inputs(self):
        self.inputs = Bunch()
        for k,v in self.opt_map.items():
            if len(v)<3:
                setattr(self.inputs, k, None)
            else:
                setattr(self.inputs, k, v[2])
        #self.inputs = Bunch((k,None) for k in self.opt_map.keys())

    @classmethod
    def help(cls):
        cls.inputs_help()
        print ''
        cls.outputs_help()
        
    @classmethod
    def inputs_help(cls):
        helpstr = ['Inputs','------']
        opthelpstr = None
        manhelpstr = None
        for k,v in sorted(cls.opt_map.items()):
            if '(opt' in v[1]:
                if not opthelpstr:
                    opthelpstr = ['','Optional:']
                opthelpstr += ['%s: %s'%(k,v[1])]
            else:
                if not manhelpstr:
                    manhelpstr = ['','Mandatory:']
                manhelpstr += ['%s: %s'%(k,v[1])]
        if manhelpstr:
            helpstr += manhelpstr
        if opthelpstr:
            helpstr += opthelpstr
        print '\n'.join(helpstr)
        #return (helpstr,manhelpstr,opthelpstr)
        
    def _convert_inputs(self, opt, val):
        """Convert input to appropriate format for spm
        """
        return val
    
    def _parse_inputs(self, skip=()):
        spmdict = {}
        inputs = sorted((k, v) for k, v in self.inputs.items()
                            if v is not None and k not in skip)
        for opt, value in inputs:
            try:
                argstr = self.opt_map[opt][0]
                if '.' in argstr:
                    fields = argstr.split('.')
                    if fields[0] not in spmdict.keys():
                        spmdict[fields[0]] = {}
                    spmdict[fields[0]][fields[1]] = self._convert_inputs(opt,value)
                else:
                    spmdict[argstr] = self._convert_inputs(opt,value)
            except KeyError:
                logger.warn("Option '%s' is not supported!" % (opt))
                raise
        return [spmdict]

    @classmethod
    def outputs_help(cls):
        """ Prints the help of outputs
        """
        helpstr = ['Outputs','-------']
        for k,v in sorted(cls.out_map.items()):
            helpstr += ['%s: %s'%(k,v[0])]
        print '\n'.join(helpstr)

    def outputs(self):
        """
        """
        outputs = Bunch()
        for k in self.out_map.keys():
            setattr(outputs, k, None)
        return outputs
    
    def _compile_command(self):
        """Assembles the matlab code for SPM function
        
        Virtual function that needs to be implemented by the
        subclass
        """ 
        self._cmdline, mscript = self._make_matlab_command(deepcopy(self._parse_inputs()))
    
    def aggregate_outputs(self):
        """Collects all the outputs produced by an SPM function
        
        Virtual function that needs to be implemented by the
        subclass to collate outputs created generated by the SPM
        functionality being wrapped.
        """ 
        raise NotImplementedError
    
    def _reformat_dict_for_savemat(self, contents):
        """Encloses a dict representation within hierarchical lists.

        In order to create an appropriate SPM job structure, a Python
        dict storing the job needs to be modified so that each dict
        embedded in dict needs to be enclosed as a list element.

        Examples
        --------
        >>> a = SpmMatlabCommandLine()._reformat_dict_for_savemat(dict(a=1,b=dict(c=2,d=3)))
        >>> print a
        [{'a': 1, 'b': [{'c': 2, 'd': 3}]}]
        
        .. notes: XXX Need to talk to Matthew about cleaning up this code.
        """
        # XXX TODO Satra, I didn't change the semantics, but got rid of extraneous stuff.
        # This seems weird.  Please have a look and make sure you intend to
        # discard empty dicts. -DJC
        # if dict is empty, SPM falls back on defaults
        # ...so empty dicts are discarded -CM
        newdict = {}
        try:
            for key, value in contents.items():
                if isinstance(value, dict):
                    if value:
                        newdict[key] = self._reformat_dict_for_savemat(value)
                    # if value is None, skip
                else:
                    newdict[key] = value
                
            return [newdict]
        except TypeError:
            print 'Requires dict input'

    def _generate_job(self, prefix='', contents=None):
        """ Recursive function to generate spm job specification as a string

        Parameters
        ----------
        prefix : string
            A string that needs to get  
        contents : dict
            A non-tuple Python structure containing spm job
            information gets converted to an appropriate sequence of
            matlab commands.
        """
        jobstring = ''
        if contents is None:
            return jobstring
        if isinstance(contents, list):
            for i,value in enumerate(contents):
                newprefix = "%s(%d)" % (prefix, i+1)
                jobstring += self._generate_job(newprefix, value)
            return jobstring
        if isinstance(contents, dict):
            for key,value in contents.items():
                newprefix = "%s.%s" % (prefix, key)
                jobstring += self._generate_job(newprefix, value)
            return jobstring
        if isinstance(contents, np.ndarray):
            if contents.dtype == np.dtype(object):
                if prefix:
                    jobstring += "%s = {...\n"%(prefix)
                else:
                    jobstring += "{...\n"
                for i,val in enumerate(contents):
                    if isinstance(val, np.ndarray):
                        jobstring += self._generate_job(prefix=None,
                                                        contents=val)
                    elif isinstance(val,str):
                        jobstring += '\'%s\';...\n'%(val)
                    else:
                        jobstring += '%s;...\n'%str(val)
                jobstring += '};\n'
            else:
                for i,val in enumerate(contents):
                    for field in val.dtype.fields:
                        if prefix:
                            newprefix = "%s(%d).%s"%(prefix, i+1, field)
                        else:
                            newprefix = "(%d).%s"%(i+1, field)
                        jobstring += self._generate_job(newprefix,
                                                        val[field])
            return jobstring
        if isinstance(contents, str):
            jobstring += "%s = '%s';\n" % (prefix,contents)
            return jobstring
        jobstring += "%s = %s;\n" % (prefix,str(contents))
        return jobstring
    
    def _make_matlab_command(self, contents, cwd=None, postscript=None):
        """ generates a mfile to build job structure
        Parameters
        ----------

        contents : list
            a list of dicts generated by _parse_inputs
            in each subclass

        cwd : string
            default os.getcwd()

        Returns
        -------
        cmdline : string
            string representing command passed to shell
            as generated by matlab.MatlabCommandLine()._gen_matlab_command

        mscript : string
            contents of a script called by matlab
        """
        if not cwd:
            cwd = os.getcwd()
        mscript  = """
        %% Generated by nipype.interfaces.spm
        if isempty(which('spm')),
             throw(MException('SPMCheck:NotFound','SPM not in matlab path'));
        end
        fprintf('SPM version: %s\\n',spm('ver'));
        fprintf('SPM path: %s\\n',which('spm'));
        spm_defaults;
                  
        if strcmp(spm('ver'),'SPM8'), spm_jobman('initcfg');end\n
        """
        if self.mfile:
            if self.jobname in ['st','smooth','preproc','fmri_spec','fmri_est'] :
                mscript += self._generate_job('jobs{1}.%s{1}.%s(1)' % 
                                             (self.jobtype,self.jobname), contents[0])
            else:
                mscript += self._generate_job('jobs{1}.%s{1}.%s{1}' % 
                                             (self.jobtype,self.jobname), contents[0])
        else:
            jobdef = {'jobs':[{self.jobtype:[{self.jobname:self.reformat_dict_for_savemat
                                         (contents[0])}]}]}
            savemat(os.path.join(cwd,'pyjobs_%s.mat'%self.jobname), jobdef)
            mscript += "load pyjobs_%s;\n\n" % self.jobname
        mscript += """ 
        if strcmp(spm('ver'),'SPM8'), 
           jobs=spm_jobman('spm5tospm8',{jobs});
        end 
        spm_jobman(\'run\',jobs);\n
        """
        if postscript is not None:
            mscript += postscript
        cmdline = self._gen_matlab_command(mscript, cwd=cwd,
                                           script_name='pyscript_%s' % self.jobname,
                                           mfile=self.mfile) 
        return cmdline, mscript


class SliceTiming(SpmMatlabCommandLine):
    """Use spm to perform slice timing correction.

    See SliceTiming().spm_doc() for more information.

    Examples
    --------

    >>> from nipype.interfaces.spm import SliceTiming
    >>> st = SliceTiming()
    >>> st.inputs.infile = 'func.nii'
    >>> st.inputs.num_slices = 32
    >>> st.inputs.time_repetition = 6.0
    >>> st.inputs.time_acquisition = 6. - 6./32.
    >>> st.inputs.slice_order = range(32,0,-1)
    >>> st.inputs.ref_slice = 1
    """

    def spm_doc(self):
        """Print out SPM documentation."""
        print grab_doc('SliceTiming')
    
    @property
    def cmd(self):
        return 'spm_st'

    @property
    def jobtype(self):
        return 'temporal'

    @property
    def jobname(self):
        return 'st'

    opt_map = {'infile': ('scans',
                          'list of filenames to apply slice timing'),
               'num_slices': ('nslices',
                              'number of slices in a volume'),
               'time_repetition': ('tr',
                                   'time between volume acquisitions ' \
                                       '(start to start time)'),
               'time_acquisition': ('ta',
                                    'time of volume acquisition. usually ' \
                                        'calculated as TR-(TR/num_slices)'),
               'slice_order': ('so',
                               '1-based order in which slices are acquired'),
               'ref_slice': ('refslice',
                             '1-based Number of the reference slice')
               }
        
    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='infile',copy=False)]
        return info

    def _convert_inputs(self, opt, val):
        """Convert input to appropriate format for spm
        """
        if opt == 'infile':
            return scans_for_fnames(filename_to_list(val),
                                    separate_sessions=True)
        return val

    def run(self, infile=None, **inputs):
        """Executes the SPM slice timing function using MATLAB
        
        Parameters
        ----------
        
        infile: string, list
            image file(s) to smooth
        """
        if infile:
            self.inputs.infile = infile
        if not self.inputs.infile:
            raise AttributeError('Slice timing requires a file')
        self.inputs.update(**inputs)
        return super(SliceTiming,self).run()

    out_map = {'timecorrected_files' : ('slice time corrected files','infile')}
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.timecorrected_files = []
        filelist = filename_to_list(self.inputs.infile)
        for f in filelist:
            s_file = glob(fname_presuffix(f, prefix='a',
                                          suffix='.nii',use_ext=False))
            assert len(s_file) == 1, 'No slice time corrected file generated by SPM Slice Timing'
            outputs.timecorrected_files.append(s_file[0])
        return outputs
    
class Realign(SpmMatlabCommandLine):
    """Use spm_realign for estimating within modality rigid body alignment

    Examples
    --------

    >>> import nipype.interfaces.spm as spm
    >>> realign = spm.Realign()
    >>> realign.inputs.infile = 'a.nii'
    >>> realign.inputs.register_to_mean = True
    >>> realign.run() # doctest: +SKIP

    """

    def spm_doc(self):
        """Print out SPM documentation."""
        print grab_doc('Realign: Estimate & Reslice')

    @property
    def cmd(self):
        return 'spm_realign'

    @property
    def jobtype(self):
         return 'spatial'

    @property
    def jobname(self):
        return 'realign'

    opt_map = {'infile': ('data', 'list of filenames to realign'),
               'jobtype': (None, 'one of: estimate, write, estwrite (opt, estwrite)', 'estwrite'),
               'quality': ('eoptions.quality',
                           '0.1 = fast, 1.0 = precise (opt, 0.9)'),
               'fwhm': ('eoptions.fwhm',
                        'gaussian smoothing kernel width (opt, 5)'),
               'separation': ('eoptions.sep',
                              'sampling separation in mm (opt, 4))'),
               'register_to_mean': ('eoptions.rtm', 'True/False (opt, False)'),
               'weight_img': ('eoptions.weight',
                              'filename of weighting image (opt, None)'),
               'interp': ('eoptions.interp',
                          'degree of b-spline used for interpolation (opt, 2)'),
               'wrap': ('eoptions.wrap',
                        'Check if interpolation should wrap in [x,y,z] (opt, [0,0,0])'),
               'write_which': ('roptions.which',
                               'determines which images to reslice (opt, [2, 1])'),
               'write_interp': ('roptions.interp',
                           'degree of b-spline used for interpolation (opt, 4)'),
               'write_wrap': ('roptions.wrap',
                        'Check if interpolation should wrap in [x,y,z] (opt, [0,0,0])'),
               'write_mask': ('roptions.mask', 'True/False mask output image (opt,)')
               }

    def get_input_info(self):
        """ Provides information about inputs
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='infile',copy=True)]
        return info

    def _convert_inputs(self, opt, val):
        """Convert input to appropriate format for spm
        """
        if opt == 'infile':
            return scans_for_fnames(filename_to_list(val),
                                    keep4d=True,
                                    separate_sessions=True)
        if opt == 'register_to_mean': # XX check if this is necessary
            return int(val)
        if opt in ['wrap','write_wrap']:
            if len(val) != 3:
                raise ValueError('%s must have 3 elements'%opt)
        if opt == 'write_which':
            if len(val) != 2:
                raise ValueError('write_which must have 2 elements')
        return val
    
    def _parse_inputs(self):
        """validate spm realign options if set to None ignore
        """
        einputs = super(Realign, self)._parse_inputs(skip=('jobtype'))
        jobtype =  self.inputs.jobtype
        return [{'%s'%(jobtype):einputs[0]}]

    out_map = {'realigned_files' : ('Realigned files',),
               'mean_image' : ('Mean image file from the realignment',),
               'realignment_parameters' : ('Estimated translation and rotation parameters',)
               }

    def run(self, infile=None,**inputs):
        """Executes the SPM realign function using MATLAB
        
        Parameters
        ----------
        
        infile: string, list
            list of filenames to realign
        """
        if infile:
            self.inputs.infile = infile
        if not self.inputs.infile:
            raise AttributeError('Realign requires an input file')
        self.inputs.update(**inputs)
        # The following line should call the run function of Realign's
        # parent class.
        return super(Realign,self).run()
    
    def aggregate_outputs(self):
        """ Initializes the output fields for this interface and then
        searches for and stores the data that go into those fields.
        """
        outputs = self.outputs()
        outputs.realigned_files = []
        outputs.realignment_parameters = []
        filelist = filename_to_list(self.inputs.infile)
        outputs.mean_image = glob(fname_presuffix(filelist[0],prefix='mean'))[0]
        for f in filelist:
            r_file = glob(fname_presuffix(f, prefix='r', suffix='.nii',
                                          use_ext=False))
            assert len(r_file) == 1, 'No realigned file generated by SPM Realign'
            outputs.realigned_files.append(r_file[0])
            rp_file = glob(fname_presuffix(f,prefix='rp_',suffix='.txt',use_ext=False))
            assert len(rp_file) == 1, 'No realignment parameter file generated by SPM Realign'
            outputs.realignment_parameters.append(rp_file[0])
        outputs.realigned_files = list_to_filename(outputs.realigned_files)
        return outputs

class Coregister(SpmMatlabCommandLine):
    """Use spm_coreg for estimating cross-modality rigid body alignment

    Examples
    --------
    
    >>> import nipype.interfaces.spm as spm
    >>> coreg = spm.Coregister()
    >>> coreg.inputs.infile = 'a.nii'
    >>> coreg.inputs.register_to_mean = True
    >>> coreg.run() # doctest: +SKIP
    
    """
    
    def spm_doc(self):
        """Print out SPM documentation."""
        print grab_doc('Coreg: Estimate & Reslice')

    @property
    def cmd(self):
        return 'spm_coreg'

    @property
    def jobtype(self):
        return 'spatial'

    @property
    def jobname(self):
        return 'coreg'
        
    opt_map = {'target': ('ref', 'reference file to register to'),
               'source': ('source', 'file to register to target'),
               'jobtype': (None, 'one of: estimate, write, estwrite (opt,estwrite)','estwrite'),
               'apply_to_files': ('other', 'files to apply transformation to (opt,)'),
               'cost_function': ('eoptions.cost_fun',
                              'objective cost function (opt, nmi))'),
               'fwhm': ('eoptions.fwhm',
                        'gaussian smoothing kernel width (opt, 5)'),
               'separation': ('eoptions.sep',
                              'sampling separation in mm (opt, 4))'),
               'tolerance': ('eoptions.tol',
                             'acceptable tolerance for each of 12 params (opt,))'),
               'write_interp': ('roptions.interp',
                           'degree of b-spline used for interpolation (opt, 0)'),
               'write_wrap': ('roptions.wrap',
                        'Check if interpolation should wrap in [x,y,z] (opt, [0,0,0])'),
               'write_mask': ('roptions.mask',
                              'True/False mask output image (opt, False)')
               }

    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='target',copy=False),
                Bunch(key='source',copy=True),
                Bunch(key='apply_to_files',copy=True)]
        return info

    def _convert_inputs(self, opt, val):
        """Convert input to appropriate format for spm
        """
        if opt == 'target':
            return scans_for_fnames(filename_to_list(val),keep4d=True)
        if opt == 'source':
            return scans_for_fnames(filename_to_list(val),keep4d=True)
        if opt == 'apply_to_files':
            return scans_for_fnames(filename_to_list(val))
        if opt in ['write_wrap']:
            if len(val) != 3:
                raise ValueError('%s must have 3 elements'%opt)
        return val
    
    def _parse_inputs(self):
        """validate spm realign options if set to None ignore
        """
        einputs = super(Coregister, self)._parse_inputs(skip=('jobtype'))
        jobtype =  self.inputs.jobtype
        return [{'%s'%(jobtype):einputs[0]}]

    out_map = {'coregistered_source' : ('Coregistered source file',),
               'coregistered_files' : ('Coregistered other files',
                                       'apply_to_files')
               }
        
    def aggregate_outputs(self):
        if isinstance(self.inputs.source, list):
            source_ext = self.inputs.source[0][-4:]
        else:
            source_ext = self.inputs.source[-4:]         
        
        outputs = self.outputs()
        if self.inputs.jobtype == "estimate":
            if self.inputs.apply_to_files != None:
                outputs.coregistered_files = self.inputs.apply_to_files
                outputs.coregistered_source = self.inputs.source
            else:
                outputs.coregistered_source = self.inputs.source
        elif self.inputs.jobtype == "write":
            outputs.coregistered_files = []
            filelist = filename_to_list(self.inputs.source)
            for f in filelist:
                c_file = glob(fname_presuffix(f,prefix='r',suffix=source_ext,use_ext=False))
                assert len(c_file) == 1, 'No coregistered file generated by SPM Coregister %s'
                outputs.coregistered_files.append(c_file[0])
        else:
            c_source = glob(fname_presuffix(self.inputs.source,prefix='r',suffix=source_ext,use_ext=False))
            assert len(c_source) == 1, 'No coregistered files generated by SPM Coregister'
            outputs.coregistered_source = c_source[0]
            outputs.coregistered_files = []
            if self.inputs.apply_to_files:
                filelist = filename_to_list(self.inputs.apply_to_files)
                for f in filelist:
                    c_file = glob(fname_presuffix(f,prefix='r',suffix=source_ext,use_ext=False))
                    assert len(c_file) == 1, 'No coregistered file generated by SPM Coregister'
                    outputs.coregistered_files.append(c_file[0])
        outputs.coregistered_files = list_to_filename(outputs.coregistered_files)
        print outputs
        return outputs
        
    def run(self, target=None, source=None, **inputs):
        """Executes the SPM coregister function using MATLAB
        
        Parameters
        ----------
        
        target: string, list
            image file to coregister source to
        source: string, list
            image file that will be coregistered to the template 
        """
        if target:
            self.inputs.target = target
        if not self.inputs.target:
            raise AttributeError('Realign requires a target file')
        if source:
            self.inputs.source = source
        if not self.inputs.source:
            raise AttributeError('Realign requires a source file')
        
        self.inputs.update(**inputs)
        
        if self.inputs.jobtype == 'write':
            if self.inputs.apply_to_files != None:
                raise AttributeError('Reslice does not accept apply_to_files. Use source instead.')
                 
        return super(Coregister,self).run()


class Normalize(SpmMatlabCommandLine):
    """use spm_normalise for warping an image to a template

    Examples
    --------
    
    """
    
    def spm_doc(self):
        """Print out SPM documentation."""
        print grab_doc('Normalise: Estimate & Write')

    @property
    def cmd(self):
        return 'spm_normalise'

    @property
    def jobtype(self):
        return 'spatial'

    @property
    def jobname(self):
        return 'normalise'
    
    opt_map = {'template': ('eoptions.template', 'template file to normalize to'),
               'source': ('subj.source', 'file to normalize to template'),
               'jobtype': (None, 'one of: estimate, write, estwrite (opt, estwrite)', 'estwrite'),
               'apply_to_files': ('subj.resample',
                                  'files to apply transformation to (opt,)'),
               'parameter_file': ('subj.matname',
                                  'normalization parameter file*_sn.mat'),
               'source_weight': ('subj.wtsrc',
                                 'name of weighting image for source (opt)'),
               'template_weight': ('eoptions.weight',
                                   'name of weighting image for template (opt)'),
               'source_image_smoothing': ('eoptions.smosrc',
                                          'source smoothing (opt)'),
               'template_image_smoothing': ('eoptions.smoref',
                                            'template smoothing (opt)'),
               'affine_regularization_type': ('eoptions.regype',
                                              'mni, size, none (opt)'),
               'DCT_period_cutoff': ('eoptions.cutoff',
                                     'Cutoff of for DCT bases (opt, 25)'),
               'nonlinear_iterations': ('eoptions.nits',
                     'Number of iterations of nonlinear warping (opt, 16)'),
               'nonlinear_regularization': ('eoptions.reg',
                                            'min = 0; max = 1 (opt, 1)'),
               'write_preserve': ('roptions.preserve',
                     'True/False warped images are modulated (opt, False)'),
               'write_bounding_box': ('roptions.bb', '6-element list (opt,)'),
               'write_voxel_sizes': ('roptions.vox', '3-element list (opt,)'),
               'write_interp': ('roptions.interp',
                           'degree of b-spline used for interpolation (opt, 0)'),
               'write_wrap': ('roptions.wrap',
                        'Check if interpolation should wrap in [x,y,z] (opt, [0,0,0])'),
               }

    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='source',copy=False),
                Bunch(key='parameter_file',copy=False),
                Bunch(key='apply_to_files',copy=False)]
        return info
        
    def _convert_inputs(self, opt, val):
        """Convert input to appropriate format for spm
        """
        if opt == 'template':
            return scans_for_fname(filename_to_list(val))
        if opt == 'source':
            return scans_for_fname(filename_to_list(val))
        if opt == 'apply_to_files':
            return scans_for_fnames(filename_to_list(val))
        if opt == 'parameter_file':
            return np.array([list_to_filename(val)],dtype=object)
        if opt in ['write_wrap']:
            if len(val) != 3:
                raise ValueError('%s must have 3 elements'%opt)
        return val

    def _parse_inputs(self):
        """validate spm realign options if set to None ignore
        """
        einputs = super(Normalize, self)._parse_inputs(skip=('jobtype',
                                                             'apply_to_files'))
        if self.inputs.apply_to_files:
            inputfiles = deepcopy(filename_to_list(self.inputs.apply_to_files))
            if self.inputs.source:
                inputfiles.append(list_to_filename(self.inputs.source))
            einputs[0]['subj']['resample'] = scans_for_fnames(inputfiles)
        jobtype =  self.inputs.jobtype
        if jobtype in ['estwrite', 'write']:
            if self.inputs.apply_to_files is None:
                if self.inputs.source:
                    einputs[0]['subj']['resample'] = scans_for_fname(self.inputs.source)            
        return [{'%s'%(jobtype):einputs[0]}]

    def run(self, template=None, source=None, parameter_file=None, apply_to_files=None, **inputs):
        """Executes the SPM normalize function using MATLAB
        
        Parameters
        ----------
        
        template: string, list containing 1 filename
            template image file to normalize to
        source: source image file that is normalized
            to template.
        """
        if template:
            self.inputs.template = template
        if source:
            self.inputs.source = source
        if parameter_file:
            self.inputs.parameter_file = parameter_file
        if apply_to_files:
            self.inputs.apply_to_files = apply_to_files
            
        jobtype =  self.inputs.jobtype
        if jobtype.startswith('est'):
            if not self.inputs.template:
                raise AttributeError('Normalize estimation requires a target file')
            if not self.inputs.source:
                raise AttributeError('Realign requires a source file')
        else:
            if not self.inputs.apply_to_files:
                raise AttributeError('Normalize write requires a files to apply')
            if not self.inputs.parameter_file:
                raise AttributeError('Normalize write requires a transformation matrix')
            
        self.inputs.update(**inputs)
        return super(Normalize,self).run()
    

    out_map = {'normalization_parameters' : ('MAT file containing the normalization parameters',),
               'normalized_source' : ('Normalized source file',),
               'normalized_files' : ('Normalized other files',
                                     'apply_to_files')
               }
        
    def aggregate_outputs(self):
           
        outputs = self.outputs()
        jobtype =  self.inputs.jobtype
        if jobtype.startswith('est'):
            sourcefile = list_to_filename(self.inputs.source)
            n_param = glob(fname_presuffix(sourcefile,suffix='_sn.mat',use_ext=False))
            assert len(n_param) == 1, 'No normalization parameter files '\
                'generated by SPM Normalize'
            outputs.normalization_parameters = n_param
        outputs.normalized_files = []
        if self.inputs.source is not None:
            if isinstance(self.inputs.source, list):
                source_ext = self.inputs.source[0][-4:]
            else:
                source_ext = self.inputs.source[-4:]
                
            sourcefile = list_to_filename(self.inputs.source)
            n_source = glob(fname_presuffix(sourcefile,prefix='w',suffix=source_ext,use_ext=False))
            outputs.normalized_source = list_to_filename(n_source)
        if self.inputs.apply_to_files is not None:
            if isinstance(self.inputs.apply_to_files, list):
                files_ext = self.inputs.apply_to_files[0][-4:]
            else:
                files_ext = self.inputs.apply_to_files[-4:]
                
            filelist = filename_to_list(self.inputs.apply_to_files)
            for f in filelist:
                n_file = glob(fname_presuffix(f,prefix='w',suffix=files_ext,use_ext=False))
                assert len(n_file) == 1, 'No normalized file %s generated by SPM Normalize'%n_file
                outputs.normalized_files.append(n_file[0])
        outputs.normalized_files = list_to_filename(outputs.normalized_files)
        return outputs
        
class Segment(SpmMatlabCommandLine):
    """use spm_segment to separate structural images into different
    tissue classes.

    Examples
    --------
    
    """
    
    def spm_doc(self):
        """Print out SPM documentation."""
        print grab_doc('Segment')
    
    @property
    def cmd(self):
        return 'spm_segment'

    @property
    def jobtype(self):
        return 'spatial'

    @property
    def jobname(self):
        return 'preproc'

    #Options to produce grey matter images: c1*.img, wc1*.img and
    #mwc1*.img. None: [0,0,0], Native Space: [0,0,1], Unmodulated Normalised:
    #[0,1,0], Modulated Normalised: [1,0,0], Native + Unmodulated Normalised:
    #[0,1,1], Native + Modulated Normalised: [1,0,1], Native + Modulated +
    #Unmodulated: [1,1,1], Modulated + Unmodulated Normalised: [1,1,0]
    
    opt_map = {'data': ('data', 'one scan per subject'),
               'gm_output_type': ('output.GM', '3-element list (opt,)'),
               'wm_output_type': ('output.WM', '3-element list (opt,)'),
               'csf_output_type': ('output.CSF', '3-element list (opt,)'),
               'save_bias_corrected': ('output.biascor',
                     'True/False produce a bias corrected image (opt, )'),
               'clean_masks': ('output.cleanup',
                     'clean using estimated brain mask 0(no)-2 (opt, )'),
               'tissue_prob_maps': ('opts.tpm',
                     'list of gray, white & csf prob. (opt,)'),
               'gaussians_per_class': ('opts.ngaus',
                     'num Gaussians capture intensity distribution (opt,)'),
               'affine_regularization': ('opts.regtype',
                      'mni, eastern, subj, none (opt,)'),
               'warping_regularization': ('opts.warpreg',
                      'Controls balance between parameters and data (opt, 1)'),
               'warp_frequency_cutoff': ('opts.warpco', 'Cutoff of DCT bases (opt,)'),
               'bias_regularization': ('opts.biasreg',
                      'no(0) - extremely heavy (10), (opt, )'),
               'bias_fwhm': ('opts.biasfwhm',
                      'FWHM of Gaussian smoothness of bias (opt,)'),
               'sampling_distance': ('opts.samp',
                      'Sampling distance on data for parameter estimation (opt,)'),
               'mask_image': ('opts.msk',
                      'Binary image to restrict parameter estimation (opt,)'),
               }

    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='data',copy=False)]
        return info
    
    def _convert_inputs(self, opt, val):
        """Convert input to appropriate format for spm
        """
        if opt in ['data', 'tissue_prob_maps']:
            if isinstance(val, list):
                return scans_for_fnames(val)
            else:
                return scans_for_fname(val)
        if opt == 'save_bias_corrected':
            return int(val)
        if opt == 'mask_image':
            return scans_for_fname(val)
        return val

    def run(self, data=None, **inputs):
        """Executes the SPM segment function using MATLAB
        
        Parameters
        ----------
        
        data: string, list
            image file to segment
        """
        if data:
            self.inputs.data = data
        if not self.inputs.data:
            raise AttributeError('Segment requires a data file')
        self.inputs.update(**inputs)
        return super(Segment,self).run()

    out_map = {'native_class_images' : ('native images for the 3 tissue types',),
               'normalized_class_images' : ('normalized images',),
               'modulated_class_images' : ('modulated, normalized images',),
               'native_gm_image' : ('native space grey probability map',),
               'normalized_gm_image' : ('normalized grey probability map',),
               'modulated_gm_image' : ('modulated, normalized grey probability map',),
               'native_wm_image' : ('native space white probability map',),
               'normalized_wm_image' : ('normalized white probability map',),
               'modulated_wm_image' : ('modulated, normalized white probability map',),
               'native_csf_image' : ('native space csf probability map',),
               'normalized_csf_image' : ('normalized csf probability map',),
               'modulated_csf_image' : ('modulated, normalized csf probability map'),
               'modulated_input_image' : ('modulated version of input image',),
               'transformation_mat' : ('Normalization transformation',),
               'inverse_transformation_mat' : ('Inverse normalization info',),
               }
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        f = self.inputs.data
        files_ext = f[0][-4:]
        m_file = glob(fname_presuffix(f,prefix='m',suffix=files_ext,use_ext=False))
        outputs.modulated_input_image = m_file
        c_files = glob(fname_presuffix(f,prefix='c*',suffix=files_ext,use_ext=False))
        outputs.native_class_images = c_files
        wc_files = glob(fname_presuffix(f,prefix='wc*',suffix=files_ext,use_ext=False))
        outputs.normalized_class_images = wc_files
        mwc_files = glob(fname_presuffix(f,prefix='mwc*',suffix=files_ext,use_ext=False))
        outputs.modulated_class_images = mwc_files
        
        c_files = glob(fname_presuffix(f,prefix='c1',suffix=files_ext,use_ext=False))
        outputs.native_gm_image = c_files
        wc_files = glob(fname_presuffix(f,prefix='wc1',suffix=files_ext,use_ext=False))
        outputs.normalized_gm_image = wc_files
        mwc_files = glob(fname_presuffix(f,prefix='mwc1',suffix=files_ext,use_ext=False))
        outputs.modulated_gm_image = mwc_files
        
        c_files = glob(fname_presuffix(f,prefix='c2',suffix=files_ext,use_ext=False))
        outputs.native_wm_image = c_files
        wc_files = glob(fname_presuffix(f,prefix='wc2',suffix=files_ext,use_ext=False))
        outputs.normalized_wm_image = wc_files
        mwc_files = glob(fname_presuffix(f,prefix='mwc2',suffix=files_ext,use_ext=False))
        outputs.modulated_wm_image = mwc_files
        
        c_files = glob(fname_presuffix(f,prefix='c3',suffix=files_ext,use_ext=False))
        outputs.native_csf_image = c_files
        wc_files = glob(fname_presuffix(f,prefix='wc3',suffix=files_ext,use_ext=False))
        outputs.normalized_csf_image = wc_files
        mwc_files = glob(fname_presuffix(f,prefix='mwc3',suffix=files_ext,use_ext=False))
        outputs.modulated_csf_image = mwc_files
        
        t_mat = glob(fname_presuffix(f,suffix='_seg_sn.mat',use_ext=False))
        outputs.transformation_mat = t_mat
        invt_mat = glob(fname_presuffix(f,suffix='_seg_inv_sn.mat',use_ext=False))
        outputs.inverse_transformation_mat = invt_mat
        return outputs

class Smooth(SpmMatlabCommandLine):
    """use spm_smooth for 3D Gaussian smoothing of image volumes.

    Examples
    --------
    
    """

    def spm_doc(self):
        """Print out SPM documentation."""
        print grab_doc('Smooth')
    
    @property
    def cmd(self):
        return 'spm_smooth'

    @property
    def jobtype(self):
        return 'spatial'

    @property
    def jobname(self):
        return 'smooth'

    opt_map = {'infile': ('data', 'list of files to smooth'),
              'fwhm': ('fwhm', '3-list of fwhm for each dimension (opt, 8)'),
              'data_type': ('dtype', 'Data type of the output images (opt, 0)'),
              }
    
    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='infile',copy=False)]
        return info
        
    def _convert_inputs(self, opt, val):
        """Convert input to appropriate format for spm
        """
        if opt in ['infile']:
            return scans_for_fnames(filename_to_list(val))
        if opt == 'fwhm':
            if not isinstance(val, list):
                return [val,val,val]
            if isinstance(val, list):
                if len(val) == 1:
                    return [val[0],val[0],val[0]]
                else:
                    return val
        return val

    def run(self, infile=None, **inputs):
        """Executes the SPM smooth function using MATLAB
        
        Parameters
        ----------
        
        infile: string, list
            image file(s) to smooth
        """
        if infile:
            self.inputs.infile = infile
        if not self.inputs.infile:
            raise AttributeError('Smooth requires a file')
        self.inputs.update(**inputs)
        return super(Smooth,self).run()

    out_map = {'smoothed_files' : ('smoothed files',)}
    
    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.smoothed_files = []
        filelist = filename_to_list(self.inputs.infile)
        if filelist:
            files_ext = filelist[0][-4:]
        for f in filelist:
            s_file = glob(fname_presuffix(f, prefix='s', suffix=files_ext, use_ext=False))
            assert len(s_file) == 1, 'No smoothed file generated by SPM Smooth'
            outputs.smoothed_files.append(s_file[0])
        return outputs

class Level1Design(SpmMatlabCommandLine):
    """Generate an SPM design matrix

    Parameters
    ----------
        session_info : list of dicts
            Stores session specific information

            Session parameters

            nscan : int
                Number of scans in a session
            scans : list of filenames
                A single 4D nifti file or a list of 3D nifti files
            hpf : float
                High pass filter cutoff
                SPM default = 128 secs
            condition_info : mat filename or list of dicts
                The output of `SpecifyModel` generates this
                information.
            regressor_info : mat/txt filename or list of dicts 
                Stores regressor specific information
                The output of Specify>odel generates this
                information.
        factor_info : list of dicts
            Stores factor specific information

            Factor parameters

            name : string
                Name of factor (use condition name)
            levels: int
                Number of levels for the factor

        bases : dict {'name':{'basesparam1':val,...}}
            name : string
                Name of basis function (hrf, fourier, fourier_han,
                gamma, fir)
                
                hrf :
                    derivs : 2-element list
                        Model  HRF  Derivatives. No derivatives: [0,0],
                        Time derivatives : [1,0], Time and Dispersion
                        derivatives: [1,1]
                fourier, fourier_han, gamma, fir:
                    length : int
                        Post-stimulus window length (in seconds)
                    order : int
                        Number of basis functions

    Examples
    --------
    
    """
    
    def spm_doc(self):
        """Print out SPM documentation."""
        print grab_doc('fMRI model specification (design only)')

    @property
    def cmd(self):
        return 'spm_fmri_design'

    @property
    def jobtype(self):
        return 'stats'

    @property
    def jobname(self):
        return 'fmri_spec'

    opt_map = {'spmmat_dir' : ('dir', 'directory to store SPM.mat file (opt, cwd)'),
               'timing_units' : ('timing.units','units for specification of onsets'),
               'interscan_interval' : ('timing.RT', 'Interscan interval in secs'),
               'microtime_resolution' : ('timing.fmri_t',
                        'Number of time-bins per scan in secs (opt,16)'),
               'microtime_onset' : ('timing.fmri_t0',
                        'The onset/time-bin in seconds for alignment (opt,)'),
               'session_info' : ('sess', 'Session specific information file'),
               'factor_info' : ('fact', 'Factor specific information file (opt,)'),
               'bases' : ('bases', 'Basis function used'),
               'volterra_expansion_order' : ('volt',
                     'Model interactions - yes:1, no:2 (opt, 1)'),
               'global_intensity_normalization' : ('global', 
                      'Global intensity normalization - scaling or none (opt, none)'),
               'mask_image' : ('mask',
                      'Image  for  explicitly  masking the analysis (opt,)'),
               'mask_threshold' : (None,
                      "Thresholding for the mask (opt, '-Inf')",'-Inf'),
               'model_serial_correlations' : ('cvi',
                      'Model serial correlations AR(1) or none (opt, AR(1))'),
               }
    
    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='mask_image',copy=False)]
        return info
        
    def _convert_inputs(self, opt, val):
        """Convert input to appropriate format for spm
        """
        if opt in ['spmmat_dir', 'mask_image']:
            return np.array([str(val)],dtype=object)
        if opt in ['session_info', 'factor_info']:
            data = loadflat(val,opt)
            if isinstance(data[opt],dict):
                return [data[opt]]
            else:
                return data[opt]
        return val
    
    def _parse_inputs(self):
        """validate spm realign options if set to None ignore
        """
        einputs = super(Level1Design, self)._parse_inputs(skip=('mask_threshold'))
        if not self.inputs.spmmat_dir:
            einputs[0]['dir'] = np.array([str(os.getcwd())],dtype=object)
        return einputs

    def _compile_command(self):
        """validates spm options and generates job structure
        if mfile is True uses matlab .m file
        else generates a job structure and saves in .mat
        """
        if self.inputs.mask_image:
            # SPM doesn't handle explicit masking properly, especially
            # when you want to use the entire mask image
            postscript = "load SPM;\n"
            postscript += "SPM.xM.VM = spm_vol('%s');\n"%list_to_filename(self.inputs.mask_image)
            postscript += "SPM.xM.I = 0;\n"
            postscript += "SPM.xM.T = [];\n"
            postscript += "SPM.xM.TH = ones(size(SPM.xM.TH))*(%s);\n"%self.inputs.mask_threshold
            postscript += "SPM.xM.xs = struct('Masking', 'explicit masking only');\n"
            postscript += "save SPM SPM;\n"
        else:
            postscript = None
        self._cmdline, mscript =self._make_matlab_command(self._parse_inputs(),
                                                          postscript=postscript)

    out_map = {'spm_mat_file' : ('SPM mat file',)}
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        spm = glob(os.path.join(os.getcwd(),'SPM.mat'))
        outputs.spm_mat_file = spm[0]
        return outputs
    
class EstimateModel(SpmMatlabCommandLine):
    """Use spm_spm to estimate the parameters of a model

    """
    
    def spm_doc(self):
        """Print out SPM documentation."""
        print grab_doc('Model estimation')

    @property
    def cmd(self):
        return 'spm_spm'

    @property
    def jobtype(self):
        return 'stats'

    @property
    def jobname(self):
        return 'fmri_est'

    opt_map = {'spm_design_file': ('spmmat', 'absolute path to SPM.mat'),
               'estimation_method': ('method',
                                     'Classical, Bayesian2, Bayesian (dict)'),
               'flags': (None, 'optional arguments (opt, None)')
               }

    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='spm_design_file',copy=True)]
        return info
    
    def _convert_inputs(self, opt, val):
        """Convert input to appropriate format for spm
        """
        if opt == 'spm_design_file':
            return np.array([str(val)],dtype=object)
        if opt == 'estimation_method':
            if isinstance(val, str):
                return {'%s'%val:1}
            else:
                return val
        return val
    
    def _parse_inputs(self):
        """validate spm realign options if set to None ignore
        """
        einputs = super(EstimateModel, self)._parse_inputs(skip=('flags'))
        if self.inputs.flags:
            einputs[0].update(self.inputs.flags)
        return einputs

    out_map = {'mask_image' : ('binary mask to constrain estimation',),
               'beta_images' : ('design parameter estimates',),
               'residual_image' : ('Mean-squared image of the residuals',),
               'RPVimage' : ('Resels per voxel image',),
               'spm_mat_file' : ('Updated SPM mat file',)
               }
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        pth, fname = os.path.split(self.inputs.spm_design_file)
        mask = glob(os.path.join(pth,'mask.img'))
        assert len(mask) == 1, 'No mask image file generated by SPM Estimate'
        outputs.mask_image = mask
        betas = glob(os.path.join(pth,'beta*.img'))
        assert len(betas) >= 1, 'No beta image files generated by SPM Estimate'
        outputs.beta_images = betas
        resms = glob(os.path.join(pth,'ResMS.img'))
        assert len(resms) == 1, 'No residual image files generated by SPM Estimate'
        outputs.residual_image = resms
        rpv = glob(os.path.join(pth,'RPV.img'))
        assert len(rpv) == 1, 'No residual image files generated by SPM Estimate'
        outputs.RPVimage = rpv
        spm = glob(os.path.join(pth,'SPM.mat'))
        assert len(spm) == 1, 'No spm mat files generated by SPM Estimate'
        outputs.spm_mat_file = spm[0]
        return outputs

class EstimateContrast(SpmMatlabCommandLine):
    """use spm_contrasts to estimate contrasts of interest


    Parameters
    ----------
    
    contrasts : List of contrasts with each contrast being a list of the form -
    ['name', 'stat', [condition list], [weight list], [session list]]. if
    session list is None or not provided, all sessions are used. For F
    contrasts, the condition list should contain previously defined T-contrasts. 

    Examples
    --------
    
    """
    
    @property
    def cmd(self):
        return 'spm_contrast'

    @property
    def jobtype(self):
        return 'stats'

    @property
    def jobname(self):
        return 'con'

    opt_map = {'spm_mat_file' : ('spmmat','Absolute path to SPM.mat'),
               'contrasts' : (None, 'List of dicts see class docstring'),
               'beta_images' : (None,'Parameter estimates of the design matrix'),
               'residual_image': (None,'Mean-squared image of the residuals'),
               'RPVimage': (None,'Resels per voxel image'),
               'ignore_derivs' : (None,
                                  'ignore derivatives for estimation. (opt,True)',
                                  True),
               }
    
    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='spm_mat_file',copy=True),
                Bunch(key='beta_images',copy=False),
                Bunch(key='residual_image',copy=False),
                Bunch(key='RPVimage',copy=False),
                ]
        return info
    
    def _compile_command(self):
        """validates spm options and generates job structure
        """
        contrasts = []
        cname = []
        for i,cont in enumerate(self.inputs.contrasts):
            cname.insert(i,cont[0])
            contrasts.insert(i,Bunch(name=cont[0],
                                     stat=cont[1],
                                     conditions=cont[2],
                                     weights=None,
                                     sessions=None))
            if len(cont)>=4:
                contrasts[i].weights = cont[3]
            if len(cont)>=5:
                contrasts[i].sessions = cont[4]
        script  = "% generated by nipype.interfaces.spm\n"
        script += "spm_defaults;\n"
        script += "jobs{1}.stats{1}.con.spmmat  = {'%s'};\n" % self.inputs.spm_mat_file
        script += "load(jobs{1}.stats{1}.con.spmmat{:});\n"
        script += "SPM.swd = '%s';\n" % os.getcwd()
        script += "save(jobs{1}.stats{1}.con.spmmat{:},'SPM');\n"
        script += "names = SPM.xX.name;\n"
        # get names for columns
        if self.inputs.ignore_derivs:
            script += "pat = 'Sn\([0-9*]\) (.*)\*bf\(1\)|Sn\([0-9*]\) .*\*bf\([2-9]\)|Sn\([0-9*]\) (.*)';\n"
        else:
            script += "pat = 'Sn\([0-9*]\) (.*)\*bf\([0-9]\)|Sn\([0-9*]\) (.*)';\n"
        script += "t = regexp(names,pat,'tokens');\n"
        # get sessidx for columns
        script += "pat1 = 'Sn\(([0-9].*)\)\s.*';\n"
        script += "t1 = regexp(names,pat1,'tokens');\n"
        script += "for i0=1:numel(t),condnames{i0}='';condsess(i0)=0;if ~isempty(t{i0}{1}),condnames{i0} = t{i0}{1}{1};condsess(i0)=str2num(t1{i0}{1}{1});end;end;\n"
        # BUILD CONTRAST SESSION STRUCTURE
        for i,contrast in enumerate(contrasts):
            if contrast.stat == 'T':
                script += "consess{%d}.tcon.name   = '%s';\n" % (i+1,contrast.name)
                script += "consess{%d}.tcon.convec = zeros(1,numel(names));\n" % (i+1)
                for c0,cond in enumerate(contrast.conditions):
                    script += "idx = strmatch('%s',condnames,'exact');\n" % (cond)
                    if contrast.sessions:
                        for sno,sw in enumerate(contrast.sessions):
                            script += "sidx = find(condsess(idx)==%d);\n" % (sno+1)
                            script += "consess{%d}.tcon.convec(idx(sidx)) = %f;\n" % (i+1,sw*contrast.weights[c0])
                    else:
                        script += "consess{%d}.tcon.convec(idx) = %f;\n" % (i+1,contrast.weights[c0])
            elif contrast.stat == 'F':
                script += "consess{%d}.fcon.name   =  '%s';\n" % (i+1,contrast.name)
                for cl0,fcont in enumerate(contrast.conditions):
                    tidx = cname.index(fcont[0])
                    script += "consess{%d}.fcon.convec{%d} = consess{%d}.tcon.convec;\n" % (i+1,cl0+1,tidx+1)
            else:
                raise Exception("Contrast Estimate: Unknown stat %s"%contrast.stat)
        script += "jobs{1}.stats{1}.con.consess = consess;\n"
        script += "if strcmp(spm('ver'),'SPM8'), spm_jobman('initcfg');jobs=spm_jobman('spm5tospm8',{jobs});end\n" 
        script += "spm_jobman('run',jobs);"
        self._cmdline = self._gen_matlab_command(script,
                                                cwd=os.getcwd(),
                                                script_name='pyscript_contrastestimate') 

    out_map = {'con_images' : ('contrast images from a t-contrast',),
               'spmT_images' : ('stat images from a t-contrast',),
               'ess_images' : ('contrast images from an F-contrast',),
               'spmF_images' : ('stat images from an F-contrast',)
               }
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        pth, fname = os.path.split(self.inputs.spm_mat_file)
        con = glob(os.path.join(pth,'con*.img'))
        if len(con)>0:
            outputs.con_images = sorted(con)
        spmt = glob(os.path.join(pth,'spmT*.img'))
        if len(spmt)>0:
            outputs.spmT_images = sorted(spmt)
        ess = glob(os.path.join(pth,'ess*.img'))
        if len(ess)>0:
            outputs.ess_images = sorted(ess)
        spmf = glob(os.path.join(pth,'spmF*.img'))
        if len(spmf)>0:
            outputs.spmF_images = sorted(spmf)
        return outputs

class OneSampleTTest(SpmMatlabCommandLine):
    """use spm to perform a one-sample ttest on a set of images

    Examples
    --------
    
    """
    
    @property
    def cmd(self):
        return 'spm_spm'

    @property
    def jobtype(self):
        return 'stats'

    opt_map = {'con_images': (None, 'List of contrast images')}

    def _compile_command(self):
        """validates spm options and generates job structure
        """
        cwd = os.getcwd()
        script  = "% generated by nipype.interfaces.spm\n"
        script += "spm_defaults;\n\n"
        script += "% Setup Design;\n"
        script += "jobs{1}.stats{1}.factorial_design.dir  = {'%s'};\n" % cwd
        script += "jobs{1}.stats{1}.factorial_design.des.t1.scans = {};\n"
        for f in filename_to_list(self.inputs.con_images):
            script += "jobs{1}.stats{1}.factorial_design.des.t1.scans{end+1} = '%s';\n" % f
        (head,fname) = os.path.split(f)
        (conname,ext) = os.path.splitext(fname)
        script += "\n% Estimate Model;\n"
        script += "jobs{2}.stats{1}.fmri_est(1).spmmat = {'%s'};\n\n" % os.path.join(cwd,'SPM.mat')
        script += "% Estimate Contrast;\n"
        script += "jobs{3}.stats{1}.con.spmmat = {'%s'};\n"  % os.path.join(cwd,'SPM.mat')
        script += "jobs{3}.stats{1}.con.consess{1}.tcon.name = '%s';\n" % conname
        script += "jobs{3}.stats{1}.con.consess{1}.tcon.convec = [1];\n"
        script += "if strcmp(spm('ver'),'SPM8'), spm_jobman('initcfg');jobs=spm_jobman('spm5tospm8',{jobs});end\n" 
        script += "spm_jobman('run',jobs);\n"
        self._cmdline = self._gen_matlab_command(script,
                                                cwd=cwd,
                                                script_name='pyscript_onesamplettest') 

    out_map = {'con_images' : ('contrast images from a t-contrast',),
               'spmT_images' : ('stat images from a t-contrast',),
               }
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        pth = os.getcwd()
        con = glob(os.path.join(pth,'con*.img'))
        if len(con)>0:
            outputs.con_images = sorted(con)
        spmt = glob(os.path.join(pth,'spmT*.img'))
        if len(spmt)>0:
            outputs.spmT_images = sorted(spmt)
        return outputs

class TwoSampleTTest(SpmMatlabCommandLine):
    """Perform a two-sample ttest using two groups of images

    Examples
    --------
    
    """
    
    @property
    def cmd(self):
        return 'spm_spm'

    @property
    def jobtype(self):
        return 'stats'

    opt_map = {'images_group1': (None, 'con images from group 1'),
               'images_group2': (None, 'con images from group 2'),
               'dependent': (None,
                             'Are the measurements independent between levels (opt, False)',
                             False),
               'unequal_variance': (None,
                                    'Are the variances equal or unequal between groups (opt, True)',
                                    True)
               }

    def _compile_command(self):
        """validates spm options and generates job structure
        if mfile is True uses matlab .m file
        else generates a job structure and saves in .mat
        """
        cwd = os.getcwd()
        script  = "% generated by nipype.interfaces.spm\n"
        script += "spm_defaults;\n\n"
        script += "% Setup Design;\n"
        script += "jobs{1}.stats{1}.factorial_design.dir  = {'%s'};\n" % cwd
        script += "jobs{1}.stats{1}.factorial_design.des.t2.scans1 = {};\n"
        for f in filename_to_list(self.inputs.images_group1):
            script += "jobs{1}.stats{1}.factorial_design.des.t2.scans1{end+1,1} = '%s';\n" % f
        script += "jobs{1}.stats{1}.factorial_design.des.t2.scans2 = {};\n"
        for f in filename_to_list(self.inputs.images_group2):
            script += "jobs{1}.stats{1}.factorial_design.des.t2.scans2{end+1,1} = '%s';\n" % f
        if self.inputs.dependent:
            script += "jobs{1}.stats{1}.factorial_design.des.t2.dept = %d;\n" % self.inputs.dependent
        if self.inputs.unequal_variance:
            script += "jobs{1}.stats{1}.factorial_design.des.t2.variance = %d;\n" % self.inputs.unequal_variance
        (head,fname) = os.path.split(f)
        (conname,ext) = os.path.splitext(fname)
        script += "\n% Estimate Model;\n"
        script += "jobs{2}.stats{1}.fmri_est(1).spmmat = {'%s'};\n\n" % os.path.join(cwd,'SPM.mat')
        script += "% Estimate Contrast;\n"
        script += "jobs{3}.stats{1}.con.spmmat = {'%s'};\n"  % os.path.join(cwd,'SPM.mat')
        script += "jobs{3}.stats{1}.con.consess{1}.tcon.name = 'Group 1';\n"
        script += "jobs{3}.stats{1}.con.consess{1}.tcon.convec = [1 0];\n"
        script += "jobs{3}.stats{1}.con.consess{2}.tcon.name = 'Group 2';\n"
        script += "jobs{3}.stats{1}.con.consess{2}.tcon.convec = [0 1];\n"
        script += "jobs{3}.stats{1}.con.consess{3}.tcon.name = 'Group 1 - Group 2';\n"
        script += "jobs{3}.stats{1}.con.consess{3}.tcon.convec = [1 -1];\n"
        script += "jobs{3}.stats{1}.con.consess{4}.tcon.name = 'Group 2 - Group 1';\n"
        script += "jobs{3}.stats{1}.con.consess{4}.tcon.convec = [-1 1];\n"
        script += "if strcmp(spm('ver'),'SPM8'), spm_jobman('initcfg');jobs=spm_jobman('spm5tospm8',{jobs});end\n" 
        script += "spm_jobman('run',jobs);\n"
        self._cmdline = self._gen_matlab_command(script,
                                                cwd=cwd,
                                                script_name='pyscript_onesamplettest') 

    out_map = {'con_images' : ('contrast images from a t-contrast',),
               'spmT_images' : ('stat images from a t-contrast',)
               }
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        pth = os.getcwd()
        con = glob(os.path.join(pth,'con*.img'))
        if len(con)>0:
            outputs.con_images = sorted(con)
        spmt = glob(os.path.join(pth,'spmT*.img'))
        if len(spmt)>0:
            outputs.spmT_images = sorted(spmt)
        return outputs
