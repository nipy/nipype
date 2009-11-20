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
from scipy.signal import convolve
from scipy.special import gammaln
#from scipy.stats.distributions import gamma

# Local imports
from nipype.interfaces.base import Bunch, InterfaceResult, Interface
from nipype.utils import setattr_on_read
from nipype.externals.pynifti import load
from nipype.interfaces.matlab import MatlabCommandLine
from nipype.utils.filemanip import (fname_presuffix, fnames_presuffix, 
                                    filename_to_list, list_to_filename)
from nipype.utils.spm_docs import grab_doc

def scans_for_fname(fname):
    """Reads a nifti file and converts it to a numpy array storing
    individual nifti volumes
    
    Opens images so will fail if they are not found
    """
    img = load(fname)
    if len(img.get_shape()) == 3:
        flist = [['%s,1'%fname]]
        return np.array([flist],dtype=object)
    else:
        n_scans = img.get_shape()[3]
        scans = []
        for sno in range(n_scans):
            scans.insert(sno,['%s,%d'% (fname, sno+1)])
        return np.array([scans],dtype=object)

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
    if keep4d:
        #flist = [[f] for f in fnames]
        #return np.array([flist],dtype=object)
        if not separate_sessions:
            flist = [np.array((f,),dtype=object) for f in fnames]
        else:
            flist = np.array((tuple([np.array((f,),dtype=object) for f in fnames]),),dtype=object)
        return np.array((flist,),dtype=object)
    else:
        n_sess = len(fnames)
        scans = None
        for sess in range(n_sess):
            if scans is None:
                scans = scans_for_fname(fnames[sess])[0]
            else:
                scans = np.concatenate((scans,scans_for_fname(fnames[sess])[0]))
        return np.array([scans],dtype=object)

class SpmInfo(object):
    """ Return the path to the spm directory in the matlab path
        If path not found, prints error asn returns None
    """
    @setattr_on_read
    def spm_path(self):
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
            return path
        else:
            print out.runtime.stderr
            return None

spm_info = SpmInfo()

class SpmMatlabCommandLine(MatlabCommandLine):
    """ Extends the `MatlabCommandLine` class to handle SPM specific
    formatting of matlab scripts.
    """

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
        """reset the base matlab command
        """
        self.mfile = use_mfile

    def run(self, **inputs):
        """Executes the SPM function using MATLAB
        """
        results = super(SpmMatlabCommandLine,self).run()
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs() 
        return results

    def _parseinputs(self):
        raise NotImplementedError
    
    def _compile_command(self):
        """Assembles the matlab code for SPM function
        
        Virtual function that needs to be implemented by the
        subclass
        """ 
        self._cmdline, mscript = self._make_matlab_command(self._parseinputs())
    
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
                if type(value) == dict:
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
        if type(contents) == type([]):
            for i,value in enumerate(contents):
                newprefix = "%s(%d)" % (prefix, i+1)
                jobstring += self._generate_job(newprefix, value)
            return jobstring
        if type(contents) == type({}):
            for key,value in contents.items():
                newprefix = "%s.%s" % (prefix, key)
                jobstring += self._generate_job(newprefix, value)
            return jobstring
        if type(contents) == type(np.empty(1)):
            # XXX TODO Assumes list of filenames embedded in a numpy array
            # does not support dicts embedded within a numpy array
            jobstring += "%s = {...\n"%(prefix)
            for item in contents[0]:
                for i,f in enumerate(item):
                    if type(f) == type(''):
                        jobstring += '\'%s\';...\n'%(f)
                    if type(f) == type(np.empty(1)):
                        if type(f[0]) == type(''):
                            jobstring += '{'
                        else:
                            jobstring += '['
                        for v in f:
                            if type(v) == type(''):
                                jobstring += '\'%s\';'%v
                            else:
                                jobstring += '%s;'%str(v)
                        if type(f[0]) == type(''):
                            jobstring += '};...\n'
                        else:
                            jobstring += '];...\n'
            jobstring += '};\n'
            return jobstring
        if type(contents) == type(''):
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

            Note that unlike calls to Popen, cwd=None will still check
            self.inputs.cwd!  Use an alternative like '.' if you need it

        Returns
        -------
        cmdline : string
            string representing command passed to shell
            as generated by matlab.MatlabCommandLine()._gen_matlab_command

        mscript : string
            contents of a script called by matlab
        """
        if cwd is None:
            cwd = self.inputs.get('cwd', '.')

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
            if self.jobname in ['smooth','preproc','fmri_spec','fmri_est'] :
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

    def outputs_help(self):
        """ Prints the help of outputs
        """
        print self.outputs.__doc__

    def outputs(self):
        """
        """
        raise NotImplementedError

class Realign(SpmMatlabCommandLine):
    """Use spm_realign for estimating within modality rigid body alignment

    See Realign().spm_doc() for more information.

    Parameters
    ----------
    inputs : dict
        key, value pairs that will update the Realign.inputs attributes.
        See self.inputs_help() for a list of attributes
    
    Attributes
    ----------
    inputs : :class:`nipype.interfaces.base.Bunch`
        Options that can be passed to spm_realign via a job structure
    cmdline : str
        String used to call matlab/spm via SpmMatlabCommandLine interface
    

    Other Parameters
    --------------- 

    To see optional arguments
    Realign().inputs_help()

    To see output fields
    Realign().outputs_help()

    Examples
    --------

    >>> import nipype.interfaces.spm as spm
    >>> realign = spm.Realign()
    >>> realign.inputs.infile = 'a.nii'
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

    def inputs_help(self):
        """
        Parameters
        ----------
        
        infile: string, list
            list of filenames to realign
        write : bool, optional
            if True updates headers and generates
            resliced files prepended with  'r'
            if False just updates header files
            (default == True, will reslice)
        quality : float, optional
            0.1 = fastest, 1.0 = most precise
            (spm5 default = 0.9)
        fwhm : float, optional
            full width half maximum gaussian kernel 
            used to smooth images before realigning
            (spm default = 5.0)
        separation : float, optional
            separation in mm used to sample images
            (spm default = 4.0)
        register_to_mean: Bool, optional
            rtm if True uses a two pass method
            realign -> calc mean -> realign all to mean
            (spm default = False)
        weight_img : file, optional
            filename of weighting image
            if empty, no weighting 
            (spm default = None)
        wrap : list, optional
            Check if interpolation should wrap in [x,y,z]
            (spm default [0,0,0])
        interp : float, optional
            degree of b-spline used for interpolation
            (spm default = 2.0)
        write_which : list of len()==2, optional
            if write is true, 
            [inputimgs, mean]
            [2,0] reslices all images, but not mean
            [2,1] reslices all images, and mean
            [1,0] reslices imgs 2:end, but not mean
            [0,1] doesnt reslice any but generates resliced mean
        write_interp : float, optional
            degree of b-spline used for interpolation when
            writing resliced images
            (spm default = 4.0)
        write_wrap : list, optional
            Check if interpolation should wrap in [x,y,z]
            (spm default [0,0,0])
        write_mask : bool, optional
            if True, mask output image
            if False, do not mask
        flags : USE AT OWN RISK, optional
            #eg:'flags':{'eoptions':{'suboption':value}}
        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        """ Initializes the input fields of this interface.
        """
        self.inputs = Bunch(infile=None,
                          write=True,
                          quality=None,
                          fwhm=None,
                          separation=None,
                          register_to_mean=None,
                          weight_img=None,
                          interp=None,
                          wrap=None,
                          write_which=None,
                          write_interp=None,
                          write_wrap=None,
                          write_mask=None,
                          flags=None)
        

    def get_input_info(self):
        """ Provides information about inputs
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='infile',copy=True)]
        return info
    
    def _parseinputs(self):
        """validate spm realign options if set to None ignore
        """
        out_inputs = []
        inputs = {}
        einputs = {'data':[],'eoptions':{},'roptions':{}}

        [inputs.update({k:v}) for k, v in self.inputs.iteritems() 
         if v is not None ]

        for opt in inputs:
            if opt is 'flags':
                einputs.update(inputs[opt])
                continue
            if opt is 'infile':
                einputs['data'] = scans_for_fnames(filename_to_list(inputs[opt]),
                                                   keep4d=True,separate_sessions=True) 
                continue
            if opt is 'write':
                continue
            if opt is 'quality':
                einputs['eoptions'].update({'quality': float(inputs[opt])})
                continue
            if opt is 'fwhm':
                einputs['eoptions'].update({'fwhm': float(inputs[opt])})
                continue
            if opt is 'separation':
                einputs['eoptions'].update({'sep': float(inputs[opt])})
                continue
            if opt is 'register_to_mean':
                einputs['eoptions'].update({'rtm': int(inputs[opt])})
                continue
            if opt is 'weight_img':
                einputs['eoptions'].update({'weight': inputs[opt]})
                continue
            if opt is 'interp':
                einputs['eoptions'].update({'interp': float(inputs[opt])})
                continue
            if opt is 'wrap':
                if not len(inputs[opt]) == 3:
                    raise ValueError('wrap must have 3 elements')
                einputs['eoptions'].update({'wrap': inputs[opt]})
                continue
            if opt is 'write_which':
                if not len(inputs[opt]) == 2:
                    raise ValueError('write_which must have 2 elements')
                einputs['roptions'].update({'which': inputs[opt]})
                continue
            if opt is 'write_interp':
                einputs['roptions'].update({'interp': inputs[opt]})
                continue
            if opt is 'write_wrap':
                if not len(inputs[opt]) == 3:
                    raise ValueError('write_wrap must have 3 elements')
                einputs['roptions'].update({'wrap': inputs[opt]})
                continue
            if opt is 'write_mask':
                einputs['roptions'].update({'mask': int(inputs[opt])})
                continue
                
            print 'option %s not supported'%(opt)
        if self.inputs.write:
            jobtype = 'estwrite'
        else:
            jobtype = 'estimate'
        einputs = [{'%s'%(jobtype):einputs}]
        return einputs

    def outputs(self):
        """
        Parameters
        ----------

        realigned_files :
            list of realigned files
        mean_image : 
            mean image file from the realignment process
        realignment_parameters : rp*.txt
            files containing the estimated translation and rotation
            parameters 
        """
        outputs = Bunch(realigned_files=None,
                        realignment_parameters=None,
                        mean_image=None)
        return outputs

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
        # The following line should call the run function of Realign's parent class.
        return super(Realign,self).run()
    
    def aggregate_outputs(self):
        """ Initializes the output fields for this interface and then
        searches for and stores the data that go into those fields.
        """
        outputs = self.outputs()
        outputs.realigned_files = []
        outputs.realignment_parameters = []
        if type(self.inputs.infile) == list:
            filelist = self.inputs.infile
        else:
            filelist = [self.inputs.infile]
        outputs.mean_image = glob(fname_presuffix(filelist[0],prefix='mean'))[0]
        for f in filelist:
            r_file = glob(fname_presuffix(f, prefix='r', suffix='.nii',
                                          use_ext=False))
            assert len(r_file) == 1, 'No realigned file generated by SPM Realign'
            outputs.realigned_files.append(r_file[0])
            rp_file = glob(fname_presuffix(f,prefix='rp_',suffix='.txt',use_ext=False))
            assert len(rp_file) == 1, 'No realignment parameter file generated by SPM Realign'
            outputs.realignment_parameters.append(rp_file[0])
        return outputs

class Coregister(SpmMatlabCommandLine):
    """Use spm_coreg for estimating cross-modality rigid body alignment

    See Coregister().spm_doc() for more information.

    Parameters
    ----------
    inputs : dict 
        key, value pairs that will update the Coregister.inputs attributes.
        See self.inputs_help() for a list of Coregister.inputs attributes
    
    Attributes
    ----------
    inputs : :class:`nipype.interfaces.base.Bunch`
        Options that can be passed to spm_coreg via a job structure
    cmdline : str
        String used to call matlab/spm via SpmMatlabSpmMatlabCommandLine 
        interface

    Other Parameters
    ----------------
    To see optional arguments
    Coregister().inputs_help()

    To see output fields
    Coregister().outputs_help()

    Examples
    --------
    
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
        
    def inputs_help(self):
        """
        Parameters
        ----------
        
        target : string
            Filename of nifti image to coregister to.  Also referred
            to as the *reference image* or the *template image*.
        source : string
            Filename of nifti image to coregister to the target image.
        apply_to_files : list, optional
            list of filenames to apply the estimated rigid body
            transform from source to target
        write : bool, optional
            if True updates headers and generates resliced files
            prepended with  'r' if False just updates header files
            (default == True, will reslice)
        cost_function : string, optional
            maximise or minimise some objective
            function. Valid options are Mutual
            Information (mi), Normalised Mutual
            Information (nmi), or  Entropy Correlation
            Coefficient (ecc) and Normalised Cross Correlation (ncc).
            (spm default = nmi)
        separation : float, optional
            separation in mm used to sample images (spm default = 4.0) 
        tolerance : list of 12 floats
            The acceptable tolerance for each of the 12 parameters.
        fwhm : float, optional
            full width half maximum gaussian kernel used to smooth
            images before coregistering (spm default = 5.0)
        write_interp : int, optional
            degree of b-spline used for interpolation when writing
            resliced images (0 - Nearest neighbor, 1 - Trilinear, 2-7
            - degree of b-spline) (spm default = 0 - Nearest Neighbor)
        write_wrap : list, optional
            Check if interpolation should wrap in [x,y,z]
            (spm default [0,0,0])
        write_mask : bool, optional
            if True, mask output image, if False, do not mask.
            (spm default = False)
        flags : USE AT OWN RISK
        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        """ Initializes the input fields of this interface.
        """
        self.inputs = Bunch(target=None,
                            source=None,
                            apply_to_files=None,
                            write=True,
                            cost_function=None,
                            separation=None,
                            tolerance=None,
                            fwhm=None,
                            write_interp=None,
                            write_wrap=None,
                            write_mask=None,
                            flags=None)

    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='target',copy=False),
                Bunch(key='source',copy=True),
                Bunch(key='apply_to_files',copy=True)]
        return info

    def _parseinputs(self):
        """validate spm coregister options
        if set to None ignore
        """
        out_inputs = []
        inputs = {}
        einputs = {'ref':'','source':'','other':[],'eoptions':{},'roptions':{}}

        [inputs.update({k:v}) for k, v in self.inputs.iteritems() if v is not None ]
        for opt in inputs:
            if opt is 'target':
                #einputs['ref'] = list_to_filename(inputs[opt])
                einputs['ref'] = scans_for_fnames(filename_to_list(inputs[opt]),keep4d=True)
                continue
            if opt is 'source':
                #einputs['source'] = list_to_filename(inputs[opt])
                einputs['source'] = scans_for_fnames(filename_to_list(inputs[opt]),keep4d=True)
                continue
            if opt is 'apply_to_files':
                sess_scans = scans_for_fnames(filename_to_list(inputs[opt]))
                einputs['other'] = sess_scans
                continue
            if opt is 'write':
                continue
            if opt is 'cost_function':
                einputs['eoptions'].update({'cost_fun': inputs[opt]})
                continue
            if opt is 'separation':
                einputs['eoptions'].update({'sep': float(inputs[opt])})
                continue
            if opt is 'tolerance':
                einputs['eoptions'].update({'tol': inputs[opt]})
                continue
            if opt is 'fwhm':
                einputs['eoptions'].update({'fwhm': float(inputs[opt])})
                continue
            if opt is 'write_interp':
                einputs['roptions'].update({'interp': inputs[opt]})
                continue
            if opt is 'write_wrap':
                if not len(inputs[opt]) == 3:
                    raise ValueError('write_wrap must have 3 elements')
                einputs['roptions'].update({'wrap': inputs[opt]})
                continue
            if opt is 'write_mask':
                einputs['roptions'].update({'mask': int(inputs[opt])})
                continue
            if opt is 'flags':
                einputs.update(inputs[opt])
                continue
            print 'option %s not supported'%(opt)
        if self.inputs.write:
            jobtype = 'estwrite'
        else:
            jobtype = 'estimate'
        einputs = [{'%s'%(jobtype):einputs}]
        return einputs

    def outputs(self):
        """
        Parameters
        ----------

        coregistered_source :
            coregistered source file
        coregistered_files :
            coregistered files corresponding to inputs.infile
        """
        outputs = Bunch(coregistered_source=None,
                        coregistered_files=None)
        return outputs
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        if self.inputs.write is False:
            outputs.coregistered_files = self.inputs.apply_to_files
        else:
            c_source = glob(fname_presuffix(self.inputs.source,prefix='r',suffix='.nii',use_ext=False))
            assert len(c_source) == 1, 'No coregistered files generated by SPM Coregister'
            outputs.coregistered_source = c_source[0]
            outputs.coregistered_files = []
            if self.inputs.apply_to_files is not None:
                if type(self.inputs.apply_to_files) == type([]):
                    filelist = self.inputs.apply_to_files
                else:
                    filelist = [self.inputs.apply_to_files]
                for f in filelist:
                    c_file = glob(fname_presuffix(f,prefix='r',suffix='.nii',use_ext=False))
                    assert len(c_file) == 1, 'No coregistered file generated by SPM Coregister'
                    outputs.coregistered_files.append(c_file[0])
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
        return super(Coregister,self).run()


class Normalize(SpmMatlabCommandLine):
    """use spm_normalise for warping an image to a template

    See Normalize().spm_doc() for more information.
    
    Parameters
    ----------
    inputs : dict 
        key, value pairs that will update the Normalize.inputs attributes.
        See self.inputs_help() for a list of Normalize.inputs attributes.
    
    Attributes
    ----------
    inputs : :class:`nipype.interfaces.base.Bunch`
        Options that can be passed to spm_normalise via a job structure
    cmdline : str
        String used to call matlab/spm via SpmMatlabCommandLine interface
    
    Other Parameters
    ----------------

    To see optional arguments
    Normalize().inputs_help()


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
    

    def inputs_help(self):
        """
        Parameters
        ----------
        
        template : string
            filename of nifti image to normalize to
        source : string
            filename of nifti image to normalize
        apply_to_files : list, optional
            list of filenames to apply the estimated normalization
        write : bool, optional
            if True updates headers and generates resliced files
            prepended with  'r' if False just updates header files
            (default == True, will reslice)
        source_weight : string, optional
            name of weighting image for source
        template_weight : string, optional
            name of weighting image for template
        source_image_smoothing : float, optional
        template_image_smoothing : float, optional
        affine_regularization_type : string, optional
            ICBM space template (mni), average sized template
            (size), no regularization (none)
        DCT_period_cutoff : int, optional
            Cutoff of for DCT bases.
            spm default = 25
        num_nonlinear_iterations : int, optional
            Number of iterations of nonlinear warping
            spm default = 16
        nonlinear_regularization : float, optional
            min = 0  max = 1
            spm default = 1
        write_preserve : boolean, optional
            Indicates whether warped images are modulated. 
            spm default = 0
        write_bounding_box : 6-element list, optional
        write_voxel_sizes : 3-element list, optional
        write_interp : int, optional
            degree of b-spline used for interpolation when
            writing resliced images (0 - Nearest neighbor, 1 -
            Trilinear, 2-7 - degree of b-spline)
            (spm default = 0 - Nearest Neighbor)
        write_wrap : list, optional
            Check if interpolation should wrap in [x,y,z]
            (spm default [0,0,0])
        flags : USE AT OWN RISK, optional
            #eg:'flags':{'eoptions':{'suboption':value}}
        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        """ Initializes the input fields of this interface.
        """
        self.inputs = Bunch(template=None,
                            source=None,
                            apply_to_files=None,
                            write=True,
                            source_weight=None,
                            template_weight=None,
                            source_image_smoothing=None,
                            template_image_smoothing=None,
                            affine_regularization_type=None,
                            DCT_period_cutoff=None,
                            num_nonlinear_iterations=None,
                            nonlinear_regularization=None,
                            write_preserve=None,
                            write_bounding_box=None,
                            write_voxel_sizes=None,
                            write_interp=None,
                            write_wrap=None,
                            flags=None)

    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='source',copy=False),
                Bunch(key='apply_to_files',copy=False)]
        return info
        
    def _parseinputs(self):
        """validate spm normalize options
        if set to None ignore
        """
        out_inputs = []
        inputs = {}
        einputs = {'subj':{'resample':[]},'eoptions':{},'roptions':{}}

        [inputs.update({k:v}) for k, v in self.inputs.iteritems() if v is not None ]
        for opt in inputs:
            if opt is 'template':
                einputs['eoptions'].update({'template': scans_for_fname(list_to_filename(inputs[opt]))})
                continue
            if opt is 'source':
                einputs['subj'].update({'source': scans_for_fname(list_to_filename(inputs[opt]))})
                continue
            if opt is 'apply_to_files':
                inputfiles = deepcopy(filename_to_list(inputs[opt]))
                inputfiles.append(list_to_filename(self.inputs.source))
                einputs['subj']['resample'] = scans_for_fnames(inputfiles)
                continue
            if opt is 'write':
                if inputs[opt]:
                    if self.inputs.apply_to_files is None:
                        # SPM requires at least one file to normalize
                        # if estwrite is being used.
                        einputs['subj']['resample'] = scans_for_fname(self.inputs.source)
                continue
            if opt is 'source_weight':
                einputs['subj'].update({'wtsrc': inputs[opt]})
                continue
            if opt is 'template_weight':
                einputs['eoptions'].update({'weight': inputs[opt]})
                continue
            if opt is 'source_image_smoothing':
                einputs['eoptions'].update({'smosrc': float(inputs[opt])})
                continue
            if opt is 'template_image_smoothing':
                einputs['eoptions'].update({'smoref': float(inputs[opt])})
                continue
            if opt is 'affine_regularization_type':
                einputs['eoptions'].update({'regtype': inputs[opt]})
                continue
            if opt is 'DCT_period_cutoff':
                einputs['eoptions'].update({'cutoff': inputs[opt]})
                continue
            if opt is 'num_nonlinear_iterations':
                einputs['eoptions'].update({'nits': inputs[opt]})
                continue
            if opt is 'nonlinear_regularization':
                einputs['eoptions'].update({'reg': float(inputs[opt])})
                continue
            if opt is 'write_preserve':
                einputs['roptions'].update({'preserve': inputs[opt]})
                continue
            if opt is 'write_bounding_box':
                einputs['roptions'].update({'bb': inputs[opt]})
                continue
            if opt is 'write_voxel_sizes':
                einputs['roptions'].update({'vox': inputs[opt]})
                continue
            if opt is 'write_interp':
                einputs['roptions'].update({'interp': inputs[opt]})
                continue
            if opt is 'write_wrap':
                if not len(inputs[opt]) == 3:
                    raise ValueError('write_wrap must have 3 elements')
                einputs['roptions'].update({'wrap': inputs[opt]})
                continue
            if opt is 'flags':
                einputs.update(inputs[opt])
                continue
            print 'option %s not supported'%(opt)
        if self.inputs.write:
            jobtype = 'estwrite'
        else:
            jobtype = 'est'
        einputs = [{'%s'%(jobtype):einputs}]
        return einputs

    def run(self, template=None, source=None, **inputs):
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
        if not self.inputs.template:
            raise AttributeError('Normalize requires a target file')
        if source:
            self.inputs.source = source
        if not self.inputs.source:
            raise AttributeError('Realign requires a source file')
        self.inputs.update(**inputs)
        return super(Normalize,self).run()
    

    def outputs(self):
        """
        Parameters
        ----------
        (all default to None)

        normalization_parameters :
            MAT file containing the normalization parameters
        normalized_source :
            normalized source file
        normalized_files :
            normalized files corresponding to inputs.apply_to_files
        """
        outputs = Bunch(normalization_parameters=None,
                        normalized_source=None,
                        normalized_files=None)
        return outputs
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        sourcefile = list_to_filename(self.inputs.source)
        n_param = glob(fname_presuffix(sourcefile,suffix='_sn.mat',use_ext=False))
        assert len(n_param) == 1, 'No normalization parameter files generated by SPM Normalize'
        outputs.normalization_parameters = n_param
        n_source = glob(fname_presuffix(sourcefile,prefix='w',suffix='.nii',use_ext=False))
        outputs.normalized_source = list_to_filename(n_source)
        outputs.normalized_files = []
        if self.inputs.apply_to_files is not None:
            filelist = filename_to_list(self.inputs.apply_to_files)
            for f in filelist:
                n_file = glob(fname_presuffix(f,prefix='w',suffix='.nii',use_ext=False))
                assert len(n_file) == 1, 'No normalized file %s generated by SPM Normalize'%n_file
                outputs.normalized_files.append(n_file[0])
        return outputs
        
class Segment(SpmMatlabCommandLine):
    """use spm_segment to separate structural images into different
    tissue classes.

    See Segment().spm_doc() for more information.

    Parameters
    ----------
    inputs : dict 
        key, value pairs that will update the Segment.inputs attributes.
        See self.inputs_help() for a list of Segment.inputs attributes.
    
    Attributes
    ----------
    inputs : :class:`nipype.interfaces.base.Bunch`
        Options that can be passed to spm_segment via a job structure
    cmdline : str
        String used to call matlab/spm via SpmMatlabCommandLine interface

    Other Parameters
    ----------------
    To see optional arguments
    Segment().inputs_help()

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

    def inputs_help(self):
        """
        Parameters
        ----------

        data : structural image file
            One scan per subject
        gm_output_type : 3-element list, optional
            Options to produce grey matter images: c1*.img,
            wc1*.img and mwc1*.img. None: [0,0,0], Native Space:
            [0,0,1], Unmodulated Normalised: [0,1,0], Modulated
            Normalised: [1,0,0], Native + Unmodulated Normalised:
            [0,1,1], Native + Modulated Normalised: [1,0,1],
            Native + Modulated + Unmodulated: [1,1,1], Modulated +
            Unmodulated Normalised: [1,1,0] 
        wm_output_type : 3-element list, optional
            Options to produce white matter images: c2*.img,
            wc2*.img and mwc2*.img. Same as GM options
        csf_output_type : 3-element list, optional
            Options to produce CSF images: c3*.img, wc3*.img and
            mwc3*.img. Same as GM options
        save_bias_corrected : bool, optional
            Option to produce a bias corrected image.
        clean_masks : int, optional
            Option to clean the gray and white matter masks using an
            estimated brain mask. Dont do cleanup (0), Light Clean
            (1), Thorough Clean (2)
        tissue_prob_maps : list of filenames, optional
            Provide maps of grey matter, white matter and
            cerebro-spinal fluid probability. 
        gaussians_per_class : 4-element list, optional
            The number of Gaussians used to represent the
            intensity distribution for each tissue class.
        affine_regularization : string, optional
            No Affine Registration (''), ICBM space template -
            European brains (mni), ICBM space template - East
            Asian brains (eastern), Average sized template:
            (subj), No regularisation (none)
        warping_regularization : float, optional
            Controls balance between parameters and data.
            spm default = 1
        warp_frequency_cutoff : int, optional
            Cutoff of DCT bases.
        bias_regularization : float, optional
            no regularisation (0), extremely light
            regularisation (0.00001), very light regularisation
            (0.0001), light regularisation (0.001), medium
            regularisation (0.01), heavy regularisation (0.1),
            very heavy regularisation (1), extremely heavy
            regularisation (10).
        bias_fwhm : int, optional
            FWHM of Gaussian smoothness of bias. 30mm to 150mm
            cutoff: (30-150 in steps of 10), No correction (inf).
        sampling_distance : float, optional
            Sampling distance on data for parameter estimation.
        mask_image : filename, optional
            An binary image to restrict parameter estimation to
            certain parts of the brain.
        flags : USE AT OWN RISK, optional
            #eg:'flags':{'eoptions':{'suboption':value}}
        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        """ Initializes the input fields of this interface.
        """
        self.inputs = Bunch(data=None,
                            gm_output_type=None,
                            wm_output_type=None,
                            csf_output_type=None,
                            save_bias_corrected=None,
                            clean_masks=None,
                            tissue_prob_maps=None,
                            gaussians_per_class=None,
                            affine_regularization=None,
                            warping_regularization=None,
                            warp_frequency_cutoff=None,
                            bias_regularization=None,
                            bias_fwhm=None,
                            sampling_distance=None,
                            mask_image=None,
                            flags=None)

    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='data',copy=False)]
        return info
    
    def _parseinputs(self):
        """validate spm segment options
        if set to None ignore
        """
        out_inputs = []
        inputs = {}
        einputs = {'data':[],'output':{},'opts':{}}

        [inputs.update({k:v}) for k, v in self.inputs.iteritems() if v is not None ]
        for opt in inputs:
            if opt is 'data':
                if type(inputs[opt]) == type([]):
                    sess_scans = scans_for_fnames(inputs[opt])
                else:
                    sess_scans = scans_for_fname(inputs[opt])
                einputs['data'] = sess_scans
                continue
            if opt is 'gm_output_type':
                einputs['output']['GM'] = inputs[opt]
                continue
            if opt is 'wm_output_type':
                einputs['output']['WM'] = inputs[opt]
                continue
            if opt is 'csf_output_type':
                einputs['output']['CSF'] = inputs[opt]
                continue
            if opt is 'save_bias_corrected':
                einputs['output']['biascor'] = int(inputs[opt])
                continue
            if opt is 'clean_masks':
                einputs['output']['cleanup'] = inputs[opt]
                continue
            if opt is 'tissue_prob_maps':
                if type(inputs[opt]) == type([]):
                    sess_scans = scans_for_fnames(inputs[opt])
                else:
                    sess_scans = scans_for_fname(inputs[opt])
                einputs['opts']['tpm'] = sess_scans
                continue
            if opt is 'gaussians_per_class':
                einputs['opts']['ngaus'] = inputs[opt]
                continue
            if opt is 'affine_regularization':
                einputs['opts']['regtype'] = inputs[opt]
                continue
            if opt is 'warping_regularization':
                einputs['opts']['warpreg'] = inputs[opt]
                continue
            if opt is 'warp_frequency_cutoff':
                einputs['opts']['warpco'] = inputs[opt]
                continue
                continue
            if opt is 'bias_regularization':
                einputs['opts']['biasreg'] = inputs[opt]
                continue
            if opt is 'bias_fwhm':
                einputs['opts']['biasfwhm'] = inputs[opt]
                continue
            if opt is 'sampling_distance':
                einputs['opts']['samp'] = inputs[opt]
                continue
            if opt is 'mask_image':
                einputs['opts']['msk'] = scans_for_fname(inputs[opt])
                continue
            if opt is 'flags':
                einputs.update(inputs[opt])
                continue
            print 'option %s not supported'%(opt)
        return [einputs]

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

    def outputs(self):
        """
        Parameters
        ----------
        (all default to None)

        native_class_images :
            native space images for each of the three tissue types
        normalized_class_images :
            normalized class images for each of the three tissue 
            types
        modulated_class_images :
            modulated, normalized class images for each of the three tissue
            types
        modulated_input_images :
            modulated version of input image
        transformation_mat :
            Transformation file for normalizing image
        inverse_transformation_mat :
            Transformation file for inverse normalizing an image
        """
        outputs = Bunch(native_class_images=None,
                        normalized_class_images=None,
                        modulated_class_images=None,
                        modulated_input_image=None,
                        transformation_mat=None,
                        inverse_transformation_mat=None)
        return outputs
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        f = self.inputs.data
        m_file = glob(fname_presuffix(f,prefix='m',suffix='.nii',use_ext=False))
        outputs.modulated_input_image = m_file
        c_files = glob(fname_presuffix(f,prefix='c*',suffix='.nii',use_ext=False))
        outputs.native_class_images = c_files
        wc_files = glob(fname_presuffix(f,prefix='wc*',suffix='.nii',use_ext=False))
        outputs.normalized_class_images = wc_files
        mwc_files = glob(fname_presuffix(f,prefix='mwc*',suffix='.nii',use_ext=False))
        outputs.modulated_class_images = mwc_files
        t_mat = glob(fname_presuffix(f,suffix='_seg_sn.mat',use_ext=False))
        outputs.transformation_mat = t_mat
        invt_mat = glob(fname_presuffix(f,suffix='_seg_inv_sn.mat',use_ext=False))
        outputs.inverse_transformation_mat = invt_mat
        return outputs

class Smooth(SpmMatlabCommandLine):
    """use spm_smooth for 3D Gaussian smoothing of image volumes.

    See Smooth().spm_doc() for more information.

    Parameters
    ----------
    inputs : dict 
        key, value pairs that will update the Smooth.inputs attributes.
        See self.inputs_help() for a list of Smooth.inputs attributes.
    
    Attributes
    ----------
    inputs : :class:`nipype.interfaces.base.Bunch`
        Options that can be passed to spm_smooth via a job structure
    cmdline : str
        String used to call matlab/spm via SpmMatlabCommandLine interface

    Other Parameters
    ----------------
    To see optional arguments
    Smooth().inputs_help()

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

    def inputs_help(self):
        """
        Parameters
        ----------
        
        infile : list
            list of filenames to apply smoothing
        fwhm : 3-list, optional
            list of fwhm for each dimension
        data_type : int, optional
            Data type of the output images. A value of 0 specifies to
            use the same data type as the original images.  Integer
            values are based on the NIfTI-1 specification::

               2 = uint8
               4 = int16
               8 = int32
              16 = float32
              64 = float64
             256 = int8
             512 = uint16
             768 = uint32

            (spm default = 0, same data type as original image)

        flags : USE AT OWN RISK, optional
            #eg:'flags':{'eoptions':{'suboption':value}}
        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        """ Initializes the input fields of this interface.
        """
        self.inputs = Bunch(infile=None,
                            fwhm=None,
                            data_type=None,
                            flags=None)

    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='infile',copy=False)]
        return info
        
    def _parseinputs(self):
        """validate spm smooth options
        if set to None ignore
        """
        out_inputs = []
        inputs = {}
        einputs = {'data':[],'fwhm':[],'dtype':0}

        [inputs.update({k:v}) for k, v in self.inputs.iteritems() if v is not None ]
        for opt in inputs:
            if opt is 'infile':
                sess_scans = scans_for_fnames(filename_to_list(inputs[opt]))
                einputs['data'] = sess_scans
                continue
            if opt is 'fwhm':
                einputs['fwhm'] = inputs[opt]
                continue
            if opt is 'data_type':
                einputs['dtype'] = inputs[opt]
                continue
            if opt is 'flags':
                einputs.update(inputs[opt])
                continue
            print 'option %s not supported'%(opt)
        return [einputs]

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

    def outputs(self):
        """
        Parameters
        ----------
        (all default to None)
        
        smoothed_files :
            smooth files corresponding to inputs.infile
        """
        outputs = Bunch(smoothed_files=None)
        return outputs
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.smoothed_files = []
        if type(self.inputs.infile) == type([]):
            filelist = self.inputs.infile
        else:
            filelist = [self.inputs.infile]
        for f in filelist:
            s_file = glob(fname_presuffix(f,prefix='s',suffix='.nii',use_ext=False))
            assert len(s_file) == 1, 'No smoothed file generated by SPM Smooth'
            outputs.smoothed_files.append(s_file[0])
        return outputs

class Level1Design(SpmMatlabCommandLine):
    """Generate an SPM design matrix

    See Level1Design().spm_doc() for more information.
    
    Parameters
    ----------
    inputs : dict 
        key, value pairs that will update the Level1Design.inputs attributes.
        See self.inputs_help() for a list of Level1Design.inputs attributes.
    
    Attributes
    ----------
    inputs : :class:`nipype.interfaces.base.Bunch`
        Options that can be passed to spm_smooth via a job structure
    cmdline : str
        String used to call matlab/spm via SpmMatlabCommandLine interface

    Other Parameters
    ----------------
    To see optional arguments
    Level1Design().inputs_help()

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

    def inputs_help(self):
        """
        Parameters
        ----------
        
        spmmat_dir : string
            directory in which to store the SPM.mat file
        timing_units : string
            units for specification of onsets or blocks
            (scans or secs) 
        interscan_interval : float (in secs)
            Interscan  interval,  TR.
        microtime_resolution : float (in secs)
            Specifies the number of time-bins per scan when building
            regressors. 
            spm default = 16
        microtime_onset : float (in secs)
            Specifies the onset/time-bin to which the regressors are
            aligned.
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
        volterra_expansion_order : int
            Do not model interactions (1) or model interactions (2)
            SPM default = 1
        global_intensity_normalization : string
            Global intensity normalization (scaling or none)
            SPM default  = none
        mask_image : filename
            Specify  an  image  for  explicitly  masking  the
            analysis. NOTE: spm will still threshold within this mask.
        mask_threshold : float
            Option to modify SPM's default thresholding for the mask.
        model_serial_correlations : string
            Option to model serial correlations using an
            autoregressive estimator. AR(1) or none
            SPM default = AR(1) 
        flags : USE AT OWN RISK
               #eg:'flags':{'eoptions':{'suboption':value}}
        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        """ Initializes the input fields of this interface.
        """
        self.inputs = Bunch(spmmat_dir=None,
                            timing_units=None,
                            interscan_interval=None,
                            microtime_resolution=None,
                            microtime_onset=None,
                            session_info=None,
                            factor_info=None,
                            bases=None,
                            volterra_expansion_order=None,
                            global_intensity_normalization=None,
                            mask_image=None,
                            model_serial_correlations=None,
                            flags=None)
        
    def _parseinputs(self):
        """validate spm normalize options
        if set to None ignore
        """
        out_inputs = []
        inputs = {}
        einputs = {'dir':'','timing':{},'sess':[],'fact':{},'bases':{},
                   'volt':{},'global':{},'mask':{}}

        [inputs.update({k:v}) for k, v in self.inputs.iteritems() if v is not None ]
        for opt in inputs:
            if opt is 'spmmat_dir':
                einputs['dir'] = np.array([[[str(inputs[opt])]]],dtype=object)
                continue
            if opt is 'timing_units':
                einputs['timing'].update(units=inputs[opt])
                continue
            if opt is 'interscan_interval':
                einputs['timing'].update(RT=inputs[opt])
                continue
            if opt is 'microtime_resolution':
                einputs['timing'].update(fmri_t=inputs[opt])
                continue
            if opt is 'microtime_onset':
                einputs['timing'].update(fmri_t0=inputs[opt])
                continue
            if opt is 'session_info':
                einputs['sess'] = inputs[opt]
                continue
            if opt is 'factor_info':
                einputs['fact'] = inputs[opt]
                continue
            if opt is 'bases':
                einputs['bases'] = inputs[opt]
                continue
            if opt is 'volterra_expansion_order':
                einputs['volt'] = inputs[opt]
                continue
            if opt is 'global_intensity_normalization':
                einputs['global'] = inputs[opt]
                continue
            if opt is 'mask_image':
                einputs['mask'] = np.array([[[str(inputs[opt])]]],dtype=object)
                continue
            if opt is 'model_serial_correlations':
                einputs['cvi'] = inputs[opt]
                continue
            if opt is 'flags':
                einputs.update(inputs[opt])
                continue
            print 'option %s not supported'%(opt)
            if einputs['dir'] == '':
                einputs['dir'] = np.array([[[str(self.inputs.get('cwd','.'))]]],dtype=object)
        return [einputs]

    def _compile_command(self):
        """validates spm options and generates job structure
        if mfile is True uses matlab .m file
        else generates a job structure and saves in .mat
        """
        if self.inputs.mask_image is not None:
            # SPM doesn't handle explicit masking properly, especially
            # when you want to use the entire mask image
            postscript = "load SPM;\n"
            postscript += "SPM.xM.VM = spm_vol('%s');\n"%self.inputs.mask_image
            postscript += "SPM.xM.I = 0;\n"
            postscript += "SPM.xM.T = [];\n"
            postscript += "SPM.xM.TH = ones(size(SPM.xM.TH))*(-Inf);\n"
            postscript += "SPM.xM.xs = struct('Masking', 'explicit masking only');\n"
            postscript += "save SPM SPM;\n"
        else:
            postscript = None
        self._cmdline, mscript =self._make_matlab_command(self._parseinputs(),
                                                          postscript=postscript)
            
    def outputs(self):
        """
        Parameters
        ----------
        spm_mat_file : str
            SPM mat file
        """
        outputs = Bunch(spm_mat_file=None)
        return outputs
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        spm = glob(os.path.join(self.inputs.get('cwd',os.getcwd()),'SPM.mat'))
        outputs.spm_mat_file = spm[0]
        return outputs
    
class EstimateModel(SpmMatlabCommandLine):
    """Use spm_spm to estimate the parameters of a model

    See EstimateModel().spm_doc() for more information.

    Parameters
    ----------
    inputs : dict
        key, value pairs that will update the EstimateModel.inputs attributes.
        See self.inputs_help() for a list of attributes.

    Attributes
    ----------
    inputs : :class:`nipype.interfaces.base.Bunch`
        Options that can be passed to spm_spm via a job structure
    cmdline : string
        string used to call matlab/spm via SpmMatlabCommandLine interface

    Other Parameters
    ----------------
    To see optional arguments EstimateModel().inputs_help()

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

    def inputs_help(self):
        """
        Parameters
        ----------
        spm_design_file : filename
            Filename containing absolute path to SPM.mat
        estimation_method: dict
            Estimate the specified model using one of three
            different SPM options::

                {'Classical' : 1}
                {'Bayesian2' : 1}
                {'Bayesian' : dict}
                    USE IF YOU KNOW HOW TO SPECIFY PARAMETERS

        flags : USE AT OWN RISK
            #eg:'flags':{'eoptions':{'suboption':value}}
        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        """ Initializes the input fields of this interface.
        """
        self.inputs = Bunch(spm_design_file=None,
                            estimation_method=None,
                            flags=None)
        
    def get_input_info(self):
        """ Provides information about inputs as a dict
            info = [Bunch(key=string,copy=bool,ext='.nii'),...]
        """
        info = [Bunch(key='spm_design_file',copy=True)]
        return info
    
    def _parseinputs(self):
        """validate spm normalize options
        if set to None ignore
        """
        out_inputs = []
        inputs = {}
        einputs = {'spmmat':'','method':{}}

        [inputs.update({k:v}) for k, v in self.inputs.iteritems() if v is not None ]
        for opt in inputs:
            if opt is 'spm_design_file':
                einputs['spmmat'] = np.array([[[str(inputs[opt])]]],dtype=object)
                continue
            if opt is 'estimation_method':
                einputs['method'].update(inputs[opt])
                continue
            if opt is 'flags':
                einputs.update(inputs[opt])
                continue
            print 'option %s not supported'%(opt)
        return [einputs]
    
    def outputs(self):
        """
            Parameters
            ----------
            (all default to None)

            mask_image:
                binary brain mask within which estimation was
                performed
            beta_images:
                Parameter estimates for each column of the design matrix
            residual_image:
                Mean-squared image of the residuals from each time point
            RPVimage:
                Resels per voxel image
            spm_mat_file:
                Updated SPM mat file
        """
        outputs = Bunch(mask_image=None,
                        beta_images=None,
                        residual_image=None,
                        RPVimage=None,
                        spm_mat_file=None)
        return outputs
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        pth, fname = os.path.split(self.inputs.spm_design_file)
        mask = glob(os.path.join(pth,'mask.*'))
        assert len(mask) == 2, 'No mask image file generated by SPM Estimate'
        outputs.mask_image = mask
        betas = glob(os.path.join(pth,'beta*.*'))
        assert len(betas) >= 2, 'No beta image files generated by SPM Estimate'
        outputs.beta_images = betas
        resms = glob(os.path.join(pth,'ResMS.*'))
        assert len(resms) == 2, 'No residual image files generated by SPM Estimate'
        outputs.residual_image = resms
        rpv = glob(os.path.join(pth,'RPV.*'))
        assert len(rpv) == 2, 'No residual image files generated by SPM Estimate'
        outputs.RPVimage = rpv
        spm = glob(os.path.join(pth,'SPM.mat'))
        assert len(spm) == 1, 'No spm mat files generated by SPM Estimate'
        outputs.spm_mat_file = spm[0]
        return outputs

class SpecifyModel(Interface):
    """Makes a model specification SPM specific

    See SpecifyModel().spm_doc() for more information.

    Parameters
    ----------
    inputs : dict
        key, value pairs that will update the SpecifyModel.inputs
        attributes. See self.inputs_help() for a list attributes.
    
    Attributes
    ----------
    inputs : :class:`nipype.interfaces.base.Bunch`
        Options that can be passed to spm_spm via a job structure
    cmdline : str
        String used to call matlab/spm via SpmMatlabCommandLine
        interface
        
    Other Parameters
    ----------------
    To see optional arguments SpecifyModel().inputs_help()

    """
    
    def spm_doc(self):
        """Print out SPM documentation."""
        print grab_doc('fMRI model specification')

    def __init__(self, *args, **inputs):
        self._populate_inputs()
        self.inputs.update(**inputs)

    def inputs_help(self):
        """
        Parameters
        ----------
        subject_id : string or int
            Subject identifier used as a parameter to the
            subject_info_func.
        subject_info_func : function
            Returns subject specific condition information. If all
            subjects had the same stimulus presentation schedule,
            then this function can return the same structure
            independent of the subject. This function must retun a
            list of dicts with the list length equal to the number of
            sessions. The dicts should contain the following
            information.

            conditions : list of names

            onsets : lists of onsets corresponding to each
                condition

            durations : lists of durations corresponding to each
                condition. Should be left to a single 0 if all
                events are being modeled as impulses.

            amplitudes : lists of amplitudes for each event. This
                is ignored by SPM

            tmod : lists of conditions that should be temporally
               modulated. Should default to None if not being used.

            pmod : list of dicts corresponding to conditions
                name : name of parametric modulator

                param : values of the modulator

                poly : degree of modulation

            regressors : list of dicts or matfile
                names : list of names corresponding to each
                   column. Should be None if automatically
                   assigned.

                values : lists of values for each regressor

                matfile : MAT-file containing names and a matrix
                    called R

        realignment_parameters : list of files
            Realignment parameters returned by some motion
            correction algorithm. Assumes that each file is a text
            file containing a row of translation and rotation
            parameters.
        outlier_files : list of files
            A list of files containing outliers that should be
            tossed. One file per session.
        functional_runs : list of files
            List of data files for model. One file per session
        input_units : string
            Units of event onsets and durations (secs or scans) as
            returned by the subject_info_func
        output_units : string
            Units of event onsets and durations (secs or scans) as
            sent to SPM design
        high_pass_filter_cutoff : float, optional
            High-pass filter cutoff in secs
        polynomial_order : int, optional
            Number of polynomial functions used to model high pass
            filter. 
        concatenate_runs : boolean, optional
            Allows concatenating all runs to look like a single
            expermental session.
        time_repetition : float
            Time between the start of one volume to the start of
            the next image volume. If a clustered acquisition is
            used, then this should be the time between the start
            of acquisition of one cluster to the start of
            acquisition of the next cluster.

        Sparse and clustered-sparse specific options

        time_acquisition : float
            Time in seconds to acquire a single image volume
        volumes_in_cluster : int
            If number of volumes in a cluster is greater than one,
            then a sparse-clustered acquisition is being assumed.
        model_hrf : boolean
            Whether to model hrf for sparse clustered analysis
        stimuli_as_impulses : boolean
            Whether to treat each stimulus to be impulse like. If
            not, the stimuli are convolved with their respective
            durations.
        scan_onset : float
            Start of scanning relative to onset of run in
            secs. default = 0 
        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        """ Initializes the input fields of this interface.
        """
        self.inputs = Bunch(subject_id=None,
                            subject_info_func=None,
                            realignment_parameters=None,
                            outlier_files=None,
                            functional_runs=None,
                            input_units=None,
                            output_units=None,
                            concatenate_runs=None,
                            time_repetition=None,
                            time_acquisition=None,
                            high_pass_filter_cutoff=None,
                            volumes_in_cluster=None,
                            model_hrf=None,
                            stimuli_as_impulses=True,
                            scan_onset=0.)
        
    def outputs(self):
        """
            Parameters
            ----------
            (all default to None)

            session_info:
                Python dict storing session info for input to
                spm.Level1Design.inputs.session_info 
        """
        outputs = Bunch(session_info=None)
        return outputs

    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.session_info = self._generate_design()
        return outputs

    def _scaletimings(self,timelist,input_units=None,output_units=None):
        if input_units is None:
            input_units = self.inputs.input_units
        if output_units is None:
            output_units = self.inputs.output_units
        if input_units==output_units:
            self._scalefactor = 1.
        if (input_units == 'scans') and (output_units == 'secs'):
            if self.inputs.volumes_in_cluster > 1:
                raise NotImplementedError("cannot scale timings if times are scans and acquisition is clustered")
            else:
                self._scalefactor = self.inputs.time_repetition
        if (input_units == 'secs') and (output_units == 'scans'):
            self._scalefactor = 1./self.inputs.time_repetition

        if self._scalefactor > 1:
            timelist = [self._scalefactor*t for t in timelist]
        else:
            timelist = [round(self._scalefactor*t) for t in timelist]
            
        return timelist
    
    def _gcd(self,a,b):
        """Returns the greates common divisor of two integers

        uses Euclid's algorithm
        """
        while b > 0: a,b = b, a%b
        return a

    def _spm_hrf(self,RT,P=[],fMRI_T=16):
        """ python implementation of spm_hrf
        see spm_hrf for implementation details

        % RT   - scan repeat time
        % p    - parameters of the response function (two gamma
        % functions)
        % defaults  (seconds)
        %	p(0) - delay of response (relative to onset)	   6
        %	p(1) - delay of undershoot (relative to onset)    16
        %	p(2) - dispersion of response			   1
        %	p(3) - dispersion of undershoot			   1
        %	p(4) - ratio of response to undershoot		   6
        %	p(5) - onset (seconds)				   0
        %	p(6) - length of kernel (seconds)		  32
        %
        % hrf  - hemodynamic response function
        % p    - parameters of the response function
        
        >>> import nipype.interfaces.spm as spm
        >>> print spm.SpecifyModel()._spm_hrf(2)
        [  0.00000000e+00   8.65660810e-02   3.74888236e-01   3.84923382e-01
           2.16117316e-01   7.68695653e-02   1.62017720e-03  -3.06078117e-02
          -3.73060781e-02  -3.08373716e-02  -2.05161334e-02  -1.16441637e-02
          -5.82063147e-03  -2.61854250e-03  -1.07732374e-03  -4.10443522e-04
          -1.46257507e-04]
        """
        p     = np.array([6,16,1,1,6,0,32],dtype=float)
        if len(P)>0:
            p[0:len(P)] = P

        _spm_Gpdf = lambda x,h,l: np.exp(h*np.log(l)+(h-1)*np.log(x)-(l*x)-gammaln(h))
        # modelled hemodynamic response function - {mixture of Gammas}
        dt    = RT/float(fMRI_T)
        u     = np.arange(0,int(p[6]/dt+1)) - p[5]/dt
        # the following code using scipy.stats.distributions.gamma
        # doesn't return the same result as the spm_Gpdf function
        # hrf   = gamma.pdf(u,p[0]/p[2],scale=dt/p[2]) - gamma.pdf(u,p[1]/p[3],scale=dt/p[3])/p[4]
        hrf   = _spm_Gpdf(u,p[0]/p[2],dt/p[2]) - _spm_Gpdf(u,p[1]/p[3],dt/p[3])/p[4]
        idx   = np.arange(0,int((p[6]/RT)+1))*fMRI_T
        hrf   = hrf[idx]
        hrf   = hrf/np.sum(hrf)
        return hrf
        
    def _gen_regress(self,i_onsets,i_durations,nscans,bplot=False):
        """Generates a regressor for a sparse/clustered-sparse acquisition

           see Ghosh et al. (2009) OHBM 2009
        """
        if bplot:
            import matplotlib.pyplot as plt
        TR = np.round(self.inputs.time_repetition*1000)  # in ms
        if self.inputs.time_acquisition is None:
            TA = TR # in ms
        else:
            TA = np.round(self.inputs.time_acquisition*1000) # in ms
        nvol = self.inputs.volumes_in_cluster
        SCANONSET = np.round(self.inputs.scan_onset*1000)
        total_time = TR*(nscans-nvol)/nvol + TA*nvol + SCANONSET
        SILENCE = TR-TA*nvol
        dt = TA/10.;
        durations  = np.round(np.array(i_durations)*1000)
        if len(durations) == 1:
            durations = durations*np.ones((len(i_onsets)))
        onsets = np.round(np.array(i_onsets)*1000)
        dttemp = self._gcd(TA,self._gcd(SILENCE,TR))
        if dt < dttemp:
            if dttemp % dt != 0:
                dt = self._gcd(dttemp,dt)
        if dt < 1:
            raise Exception("Time multiple less than 1 ms")
        print "Setting dt = %d ms\n" % dt
        npts = int(total_time/dt)
        times = np.arange(0,total_time,dt)*1e-3
        timeline = np.zeros((npts))
        timeline2 = np.zeros((npts))
        hrf = self._spm_hrf(dt*1e-3)
        for i,t in enumerate(onsets):
            idx = int(t/dt)
            timeline2[idx] = 1
            if bplot:
                plt.subplot(4,1,1)
                plt.plot(times,timeline2)
            if not self.inputs.stimuli_as_impulses:
                if durations[i] == 0:
                    durations[i] = TA*nvol
                stimdur = np.ones((int(durations[i]/dt)))
                timeline2 = convolve(timeline2,stimdur)[0:len(timeline2)]
            timeline += timeline2
            timeline2[:] = 0
        if bplot:
            plt.subplot(4,1,2)
            plt.plot(times,timeline)
        if self.inputs.model_hrf:
            timeline = convolve(timeline,hrf)[0:len(timeline)]
        if bplot:
            plt.subplot(4,1,3)
            plt.plot(times,timeline)
        # sample timeline
        timeline2 = np.zeros((npts))
        reg = []
        for i,trial in enumerate(np.arange(nscans)/nvol):
            scanstart = int((SCANONSET + trial*TR + (i%nvol)*TA)/dt)
            #print total_time/dt, SCANONSET, TR, TA, scanstart, trial, i%2, int(TA/dt)
            scanidx = scanstart+np.arange(int(TA/dt))
            timeline2[scanidx] = np.max(timeline)
            reg.insert(i,np.mean(timeline[scanidx]))
        if bplot:
            plt.subplot(4,1,3)
            plt.plot(times,timeline2)
            plt.subplot(4,1,4)
            plt.bar(np.arange(len(reg)),reg,width=0.5)
        return reg

    def _cond_to_regress(self,info,nscans):
        """Converts condition information to full regressors
        """
        reg = []
        regnames = info.conditions
        for i,c in enumerate(info.conditions):
            reg.insert(i,self._gen_regress(self._scaletimings(info.onsets[i],output_units='secs'),
                                           self._scaletimings(info.durations[i],output_units='secs'),
                                           nscans))
            # need to deal with temporal and parametric modulators
        # for sparse-clustered acquisitions enter T1-effect regressors
        nvol = self.inputs.volumes_in_cluster
        if nvol > 1:
            for i in range(nvol-1):
                treg = np.zeros((nscans/nvol,nvol))
                treg[:,i] = 1
                reg.insert(len(reg),treg.ravel().tolist())
        return reg,regnames
    
    def _generate_clustered_design(self,infolist):
        """Generates condition information for sparse-clustered
        designs.
        
        """
        infoout = deepcopy(infolist)
        for i,info in enumerate(infolist):
            infoout[i].conditions = None
            infoout[i].onsets = None
            infoout[i].durations = None
            if info.conditions is not None:
                img = load(self.inputs.functional_runs[i])
                nscans = img.get_shape()[3]
                reg,regnames = self._cond_to_regress(info,nscans)
                if infoout[i].regressors is None:
                    infoout[i].regressors = []
                    infoout[i].regressor_names = []
                else:
                    if infoout[i].regressor_names is None:
                        infoout[i].regressor_names = ['R%d'%j for j in range(len(infoout[i].regressors))] 
                for j,r in enumerate(reg):
                    regidx = len(infoout[i].regressors)
                    infoout[i].regressor_names.insert(regidx,regnames[j])
                    infoout[i].regressors.insert(regidx,r)
        return infoout
    
    def _generate_standard_design(self,infolist,
                                  functional_runs=None,
                                  realignment_parameters=None,
                                  outliers=None):
        """ Generates a standard design matrix paradigm
        """
        sessinfo = []
        for i,info in enumerate(infolist):
            sessinfo.insert(i,dict(cond=[]))
            if self.inputs.high_pass_filter_cutoff is not None:
                sessinfo[i]['hpf'] = np.float(self.inputs.high_pass_filter_cutoff)
            if info.conditions is not None:
                for cid,cond in enumerate(info.conditions):
                    sessinfo[i]['cond'].insert(cid,dict())
                    sessinfo[i]['cond'][cid]['name']  = info.conditions[cid]
                    sessinfo[i]['cond'][cid]['onset'] = self._scaletimings(info.onsets[cid])
                    sessinfo[i]['cond'][cid]['duration'] = self._scaletimings(info.durations[cid])
                    if info.tmod is not None:
                        sessinfo[i]['cond'][cid]['tmod'] = info.tmod[cid]
                    if (info.pmod is not None) and info.pmod.has_key(cid+1):
                        sessinfo[i]['cond'][cid]['pmod'] = []
                        for j in range(len(info.pmod[cid+1].name)):
                            sessinfo[i]['cond'][cid]['pmod'].insert(j,dict())
                        for key,data in info.pmod[cid+1].iteritems():
                            for k,val in enumerate(data):
                                sessinfo[i]['cond'][cid]['pmod'][k][key] = val
            sessinfo[i]['regress']= []
            if info.regressors is not None:
                for j,r in enumerate(info.regressors):
                    sessinfo[i]['regress'].insert(j,dict(name='',val=[]))
                    if info.regressor_names is not None:
                        sessinfo[i]['regress'][j]['name'] = info.regressor_names[j]
                    else:
                        sessinfo[i]['regress'][j]['name'] = 'UR%d'%(j+1)
                    sessinfo[i]['regress'][j]['val'] = info.regressors[j]
            if functional_runs is not None:
                sessinfo[i]['scans'] = scans_for_fnames(filename_to_list(functional_runs[i]),keep4d=False)
            else:
                raise Exception("No functional data information provided for model")
        if realignment_parameters is not None:
            for i,rp in enumerate(realignment_parameters):
                mc = realignment_parameters[i]
                for col in range(mc.shape[1]):
                    colidx = len(sessinfo[i]['regress'])
                    sessinfo[i]['regress'].insert(colidx,dict(name='',val=[]))
                    sessinfo[i]['regress'][colidx]['name'] = 'Realign%d'%(col+1)
                    sessinfo[i]['regress'][colidx]['val']  = mc[:,col].tolist()
        if outliers is not None:
            for i,out in enumerate(outliers):
                numscans = sessinfo[i]['scans'][0].shape[0] 
                for j,scanno in enumerate(out):
                    if True:
                        colidx = len(sessinfo[i]['regress'])
                        sessinfo[i]['regress'].insert(colidx,dict(name='',val=[]))
                        sessinfo[i]['regress'][colidx]['name'] = 'Outlier%d'%(j+1)
                        sessinfo[i]['regress'][colidx]['val']  = np.zeros((1,numscans))[0].tolist()
                        sessinfo[i]['regress'][colidx]['val'][int(scanno)] = 1
                    else:
                        cid = len(sessinfo[i]['cond'])
                        sessinfo[i]['cond'].insert(cid,dict())
                        sessinfo[i]['cond'][cid]['name'] = "O%d"%(j+1)
                        sessinfo[i]['cond'][cid]['onset'] = self._scaletimings([scanno])
                        sessinfo[i]['cond'][cid]['duration'] = [0]
        return sessinfo
    
    def _concatenate_info(self,infolist):
        nscans = []
        for i,f in enumerate(self.inputs.functional_runs):
            img = load(f)
            nscans.insert(i,img.get_shape()[3])
            # now combine all fields into 1
            # names,onsets,durations,amplitudes,pmod,tmod,regressor_names,regressors
        infoout = infolist[0]
        for i,info in enumerate(infolist[1:]):
                #info.[conditions,tmod] remain the same
            if info.onsets is not None:
                for j,val in enumerate(info.onsets):
                    if self.inputs.input_units == 'secs':
                        infoout.onsets[j].extend((np.array(info.onsets[j])+
                                                  self.inputs.time_repetition*sum(nscans[0:(i+1)])).tolist())
                    else:
                        infoout.onsets[j].extend((np.array(info.onsets[j])+sum(nscans[0:(i+1)])).tolist())
                for j,val in enumerate(info.durations):
                    if len(val) > 1:
                        infoout.durations[j].extend(info.durations[j])
                if info.pmod is not None:
                    for key,data in info.pmod.items():
                        for j,v in enumerate(data.param):
                            infoout.pmod[key].param[j].extend(v)
            if info.regressors is not None:
                #assumes same ordering of regressors across different
                #runs and the same names for the regressors
                for j,v in enumerate(info.regressors):
                    infoout.regressors[j].extend(info.regressors[j])
            #insert session regressors
            if True:
                if infoout.regressors is None:
                    infoout.regressors = []
                onelist = np.zeros((1,sum(nscans)))
                onelist[0,sum(nscans[0:(i)]):sum(nscans[0:(i+1)])] = 1
                infoout.regressors.insert(len(infoout.regressors),onelist.tolist()[0])
            else:
                infoout.conditions.append('Session%d'%i)
                infoout.onsets.insert(len(infoout.onsets),[sum(nscans[0:i])])
                infoout.durations.insert(len(infoout.durations),[nscans[i]])
                if infoout.tmod is not None:
                    infoout.tmod.insert(len(infoout.tmod),0)
            # insert outliers as new regressors
        return [infoout],nscans
    
    def _generate_design(self):
        if callable(self.inputs.subject_info_func):
            infolist = self.inputs.subject_info_func(self.inputs.subject_id)
        else:
            infolist = self.inputs.subject_info_func
        if self.inputs.concatenate_runs:
            infolist,nscans = self._concatenate_info(infolist)
            functional_runs = [self.inputs.functional_runs]
        else:
            functional_runs = self.inputs.functional_runs
        realignment_parameters = []
        if self.inputs.realignment_parameters is not None:
            rpfiles = filename_to_list(self.inputs.realignment_parameters)
            realignment_parameters.insert(0,np.loadtxt(rpfiles[0]))
            for rpf in rpfiles[1:]:
                mc = np.loadtxt(rpf)
                if self.inputs.concatenate_runs:
                    realignment_parameters[0] = np.concatenate((realignment_parameters[0],mc))
                else:
                    realignment_parameters.insert(len(realignment_parameters),mc)
        outliers = []
        if self.inputs.outlier_files is not None:
            outfiles = filename_to_list(self.inputs.outlier_files)
            try:
                outindices = np.loadtxt(outfiles[0],dtype=int)
                if outindices.size == 1:
                    outliers.insert(0,[outindices.tolist()])
                else:
                    outliers.insert(0,outindices.tolist())
            except IOError:
                outliers.insert(0,[])
            for i,rpf in enumerate(outfiles[1:]):
                try:
                    out = np.loadtxt(rpf,dtype=int)
                except IOError:
                    out = np.array([])
                if self.inputs.concatenate_runs:
                    if out.size>0:
                        if out.size == 1:
                            outliers[0].extend([(np.array(out)+sum(nscans[0:(i+1)])).tolist()])
                        else:
                            outliers[0].extend((np.array(out)+sum(nscans[0:(i+1)])).tolist())
                else:
                    if out.size == 1:
                        outliers.insert(len(outliers),[out.tolist()])
                    else:
                        outliers.insert(len(outliers),out.tolist())
        if self.inputs.volumes_in_cluster is not None:
            infolist = self._generate_clustered_design(infolist)
        sessinfo = self._generate_standard_design(infolist,
                                                  functional_runs=functional_runs,
                                                  realignment_parameters=realignment_parameters,
                                                  outliers=outliers)
        return sessinfo
    
    def run(self, **inputs):
        """
        """
        runtime = Bunch(returncode=0,
                        messages=None,
                        errmessages=None)
        outputs=self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)
    

class EstimateContrast(SpmMatlabCommandLine):
    """use spm_contrasts to estimate contrasts of interest

    Parameters
    ----------
    inputs : dict 
        key, value pairs that will update the EstimateContrast.inputs 
        attributes.  See self.inputs_help() for a list of 
        EstimateContrast.inputs attributes.
    
    Attributes
    ----------
    inputs : :class:`nipype.interfaces.base.Bunch`
        Options that can be passed to spm_spm via a job structure
    cmdline : str
        String used to call matlab/spm via SpmMatlabCommandLine interface

    Other Parameters
    ----------------
    To see optional arguments
    EstimateContrast().inputs_help()

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

    def inputs_help(self):
        """
        Parameters
        ----------
       
        spm_mat_file : filename
            Filename containing absolute path to SPM.mat
        contrasts : list of dicts
            List of contrasts with each contrast being a list
            of the form - ['name', 'stat', [condition list],
            [weight list], [session list]]. if session list is
            None or not provided, all sessions are used. For F
            contrasts, the condition list should contain
            previously defined T-contrasts. 
        beta_images: filenames
            Parameter estimates for each column of the design matrix
        residual_image: filename
            Mean-squared image of the residuals from each time point
        RPVimage: filename
            Resels per voxel image
        ignore_derivs : boolean
            Whether to ignore derivatives from contrast
            estimation. default : True
        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        """ Initializes the input fields of this interface.
        """
        self.inputs = Bunch(spm_mat_file=None,
                            contrasts=None,
                            beta_images=None,
                            residual_image=None,
                            RPVimage=None,
                            ignore_derivs=True)
        
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
    
    def _parseinputs(self):
        """validate spm normalize options
        if set to None ignore
        """
        out_inputs = []
        inputs = {}
        einputs = {'spmmat':'','method':{}}

        [inputs.update({k:v}) for k, v in self.inputs.iteritems() if v is not None ]
        for opt in inputs:
            if opt is 'spm_mat_file':
                einputs['spmmat'] = np.array([[[str(inputs[opt])]]],dtype=object)
                continue
            if opt is 'contrasts':
                continue
            if opt is 'beta_images':
                continue
            if opt is 'residual_image':
                continue
            if opt is 'RPVimage':
                continue
            if opt is 'flags':
                continue
            if opt is 'ignore_derivs':
                continue
            print 'option %s not supported'%(opt)
        return einputs

    def _compile_command(self):
        """validates spm options and generates job structure
        if mfile is True uses matlab .m file
        else generates a job structure and saves in .mat
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
        script += "SPM.swd = '%s';\n" % self.inputs.get('cwd','.')
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
                                                cwd=self.inputs.get('cwd','.'),
                                                script_name='pyscript_contrastestimate') 
    
    def outputs(self):
        """
        Parameters
        ----------
        (all default to None)

        con_images:
            contrast images from a t-contrast
        spmT_images:
            stat images from a t-contrast
        ess_images:
            contrast images from an F-contrast
        spmF_images:
            stat images from an F-contrast
        """
        outputs = Bunch(con_images=None,
                        spmT_images=None,
                        ess_images=None,
                        spmF_images=None)
        return outputs
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        pth, fname = os.path.split(self.inputs.spm_mat_file)
        con = glob(os.path.join(pth,'con*.*'))
        if len(con)>0:
            outputs.con_images = sorted(con)
        spmt = glob(os.path.join(pth,'spmT*.*'))
        if len(spmt)>0:
            outputs.spmT_images = sorted(spmt)
        ess = glob(os.path.join(pth,'ess*.*'))
        if len(ess)>0:
            outputs.ess_images = sorted(ess)
        spmf = glob(os.path.join(pth,'spmF*.*'))
        if len(spmf)>0:
            outputs.spmF_images = sorted(spmf)
        return outputs

class OneSampleTTest(SpmMatlabCommandLine):
    """use spm to perform a one-sample ttest on a set of images

    Parameters
    ----------
    inputs : dict 
        key, value pairs that will update the EstimateContrast.inputs 
        attributes.  See self.inputs_help() for a list of 
        EstimateContrast.inputs attributes.
    
    Attributes
    ----------
    inputs : :class:`nipype.interfaces.base.Bunch`
        Options that can be passed to spm_spm via a job structure
    cmdline : str
        String used to call matlab/spm via SpmMatlabCommandLine interface

    Other Parameters
    ----------------
    To see optional arguments
    EstimateContrast().inputs_help()

    Examples
    --------
    
    """
    
    @property
    def cmd(self):
        return 'spm_spm'

    @property
    def jobtype(self):
        return 'stats'

    def inputs_help(self):
        """
        Parameters
        ----------

        con_images: list of filenames
        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        """ Initializes the input fields of this interface.
        """
        self.inputs = Bunch(con_images=None)
        
    def _parseinputs(self):
        """validate spm1 sample t-test options
        if set to None ignore
        """
        out_inputs = []
        inputs = {}
        einputs = {'con_images':''}

        [inputs.update({k:v}) for k, v in self.inputs.iteritems() if v is not None ]
        for opt in inputs:
            if opt is 'con_images':
                continue
            print 'option %s not supported'%(opt)
        return einputs

    def _compile_command(self):
        """validates spm options and generates job structure
        if mfile is True uses matlab .m file
        else generates a job structure and saves in .mat
        """
        cwd = self.inputs.get('cwd','.')
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
    
    def outputs(self):
        """
        Parameters
        ----------
        (all default to None)

        con_images:
            contrast images from a t-contrast
        spmT_images:
            stat images from a t-contrast
        """
        outputs = Bunch(con_images=None,
                        spmT_images=None)
        return outputs
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        pth = self.inputs.get('cwd','.')
        con = glob(os.path.join(pth,'con*.*'))
        if len(con)>0:
            outputs.con_images = sorted(con)
        spmt = glob(os.path.join(pth,'spmT*.*'))
        if len(spmt)>0:
            outputs.spmT_images = sorted(spmt)
        return outputs

class TwoSampleTTest(SpmMatlabCommandLine):
    """use spm to perform a two-sample ttest on a set of images

    Parameters
    ----------
    inputs : dict 
        key, value pairs that will update the EstimateContrast.inputs 
        attributes.  See self.inputs_help() for a list of
        EstimateContrast.inputs attributes.
    
    Attributes
    ----------
    inputs : :class:`nipype.interfaces.base.Bunch`
        Options that can be passed to spm_spm via a job structure
    cmdline : str
        String used to call matlab/spm via SpmMatlabCommandLine interface

    Other Parameters
    ----------------
    To see optional arguments
    EstimateContrast().inputs_help()

    Examples
    --------
    
    """
    
    @property
    def cmd(self):
        return 'spm_spm'

    @property
    def jobtype(self):
        return 'stats'

    def inputs_help(self):
        """
        Parameters
        ----------

        images_group1: list of filenames
        images_group2: list of filenames
        dependent: bool, optional
            are the measurements independent between levels
            SPM default: False
        unequal_variance: bool, optional
            are the variances equal or unequal between groups
            SPM default: True
        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        """ Initializes the input fields of this interface.
        """
        self.inputs = Bunch(images_group1=None,
                            images_group2=None,
                            dependent=None,
                            unequal_variance=None)
        
    def _parseinputs(self):
        """validate spm normalize options
        if set to None ignore
        """
        out_inputs = []
        inputs = {}
        einputs = {'images_group1':None,'images_group2':None}

        [inputs.update({k:v}) for k, v in self.inputs.iteritems() if v is not None ]
        for opt in inputs:
            if opt is 'images_group1':
                continue
            if opt is 'images_group2':
                continue
            print 'option %s not supported'%(opt)
        return einputs

    def _compile_command(self):
        """validates spm options and generates job structure
        if mfile is True uses matlab .m file
        else generates a job structure and saves in .mat
        """
        cwd = self.inputs.get('cwd','.')
        script  = "% generated by nipype.interfaces.spm\n"
        script += "spm_defaults;\n\n"
        script += "% Setup Design;\n"
        script += "jobs{1}.stats{1}.factorial_design.dir  = {'%s'};\n" % cwd
        script += "jobs{1}.stats{1}.factorial_design.des.t2.scans1 = {};\n"
        for f in filename_to_list(self.inputs.group_images1):
            script += "jobs{1}.stats{1}.factorial_design.des.t2.scans1{end+1} = '%s';\n" % f
        script += "jobs{1}.stats{1}.factorial_design.des.t2.scans2 = {};\n"
        for f in filename_to_list(self.inputs.group_images2):
            script += "jobs{1}.stats{1}.factorial_design.des.t2.scans2{end+1} = '%s';\n" % f
        if self.inputs.independent:
            script += "jobs{1}.stats{1}.factorial_design.des.t2.dept = %d;\n" % self.inputs.independent
        if self.inputs.variance:
            script += "jobs{1}.stats{1}.factorial_design.des.t2.variance = %d;\n" % self.inputs.variance
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
        script += "jobs{3}.stats{1}.con.consess{2}.tcon.name = 'Group 1 - Group 2';\n"
        script += "jobs{3}.stats{1}.con.consess{2}.tcon.convec = [1 -1];\n"
        script += "jobs{3}.stats{1}.con.consess{2}.tcon.name = 'Group 2 - Group 1';\n"
        script += "jobs{3}.stats{1}.con.consess{2}.tcon.convec = [-1 1];\n"
        script += "if strcmp(spm('ver'),'SPM8'), spm_jobman('initcfg');jobs=spm_jobman('spm5tospm8',{jobs});end\n" 
        script += "spm_jobman('run',jobs);\n"
        self._cmdline = self._gen_matlab_command(script,
                                                cwd=cwd,
                                                script_name='pyscript_onesamplettest') 
    
    def outputs(self):
        """
        Parameters
        ----------
        (all default to None)

        con_images:
            contrast images from a t-contrast
        spmT_images:
            stat images from a t-contrast
        """
        outputs = Bunch(con_images=None,
                        spmT_images=None)
        return outputs
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        pth = self.inputs.get('cwd','.')
        con = glob(os.path.join(pth,'con*.*'))
        if len(con)>0:
            outputs.con_images = sorted(con)
        spmt = glob(os.path.join(pth,'spmT*.*'))
        if len(spmt)>0:
            outputs.spmT_images = sorted(spmt)
        return outputs
