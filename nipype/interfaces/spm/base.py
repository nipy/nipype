"""The spm module provides basic functions for interfacing with matlab
and spm to access spm tools.

"""
__docformat__ = 'restructuredtext'

# Standard library imports
import os
from copy import deepcopy
import re

# Third-party imports
import numpy as np
from scipy.io import savemat

# Local imports
from nipype.interfaces.base import Bunch, NEW_BaseInterface, traits, TraitedSpec
from nipype.externals.pynifti import load
from nipype.interfaces.matlab import MatlabCommandLine
from nipype.interfaces.matlab import NEW_MatlabCommand
                                    
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

    def _outputs(self):
        return self.outputs()
    
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

######################
# 
# NEW classes
#
######################

class NEW_Info(object):
    """ Return the path to the spm directory in the matlab path
        If path not found, prints error asn returns None
    """
    __path = None
    @classmethod
    def spm_path(cls):
        if cls.__path == None:
            mlab = NEW_MatlabCommand()
            mlab.inputs.script_file = 'spminfo'
            mlab.inputs.script = """
    if isempty(which('spm')), throw(MException('SPMCheck:NotFound','SPM not in matlab path'));end;
    spm_path = spm('dir');
    fprintf(1, '<PATH>%s</PATH>', spm_path);
    """
            out = mlab.run()
            if out.runtime.returncode == 0:
                path = re.match('<PATH>(.*)</PATH>',out.runtime.stdout[out.runtime.stdout.find('<PATH>'):])
                if path is not None:
                    path = path.groups()[0]
                cls.__path = path
            else:
                logger(out.runtime.stderr)
                return None
            
        return cls.__path

class NEW_SPMCommand(NEW_BaseInterface):
    """ Extends `NEW_BaseInterface` class to implement SPM specific interfaces.
    """

    paths = None

    def __init__(self, matlab_cmd=None, paths=None,
                 mfile = True, **inputs): 
        super(NEW_SPMCommand, self).__init__(**inputs)
        self.mlab = NEW_MatlabCommand(matlab_cmd=matlab_cmd)
        self.mlab.inputs.mfile = mfile
        if paths:
            self.paths = paths
        if self.paths:
            self.mlab.inputs.paths = self.paths
        self.mlab.inputs.script_file = 'pyscript_%s.m' % \
            self.__class__.__name__.split('.')[-1].lower()

    @property
    def jobtype(cls):
        return cls._jobtype

    @property
    def jobname(cls):
        return cls._jobname

    def use_mfile(self, use_mfile):
        """boolean,
        if true generates a matlab <filename>.m file
        if false generates a binary .mat file
        """
        self.mlab.inputs.mfile = use_mfile

    def run(self, **inputs):
        """Executes the SPM function using MATLAB
        """
        self.inputs.set(**inputs)
        self.mlab.inputs.script = self._make_matlab_command(deepcopy(self._parse_inputs()))
        results = self.mlab.run()
        if results.runtime.returncode == 0:
            results.outputs = self.aggregate_outputs() 
        return results
    
    def _list_outputs(self):
        """ Determine the expected outputs based on inputs """
        raise NotImplementedError
    
    def aggregate_outputs(self):
        """ Initializes the output fields for this interface and then
        searches for and stores the data that go into those fields.
        """
        outputs = self._outputs()
        for key, val in self._list_outputs().items():
            setattr(outputs, key, val)
        return outputs
        
    def _format_arg(self, opt, val):
        """Convert input to appropriate format for spm
        """
        return val
    
    def _parse_inputs(self, skip=()):
        spmdict = {}
        for name, trait_spec in self.inputs.items():
            if skip and name in skip:
                continue
            value = getattr(self.inputs, name)
            if value == trait_spec.default and \
                    not (trait_spec.usedefault or name in self.inputs.explicitset):
                continue
            field = trait_spec.field
            if '.' in field:
                fields = field.split('.')
                if fields[0] not in spmdict.keys():
                    spmdict[fields[0]] = {}
                spmdict[fields[0]][fields[1]] = self._format_arg(name, value)
            else:
                spmdict[field] = self._format_arg(name, value)
        return [spmdict]
    
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
        
        """
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
    
    def _make_matlab_command(self, contents, postscript=None):
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
        if self.mlab.inputs.mfile:
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
        return mscript
