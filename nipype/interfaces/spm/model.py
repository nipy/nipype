"""The spm module provides basic functions for interfacing with matlab
and spm to access spm tools.

"""
__docformat__ = 'restructuredtext'

# Standard library imports
import os
from glob import glob

# Third-party imports
import numpy as np

# Local imports
from nipype.interfaces.spm import SpmMatlabCommandLine
from nipype.interfaces.base import Bunch
from nipype.utils.filemanip import (filename_to_list, list_to_filename,
                                    loadflat)
from nipype.utils.spm_docs import grab_doc
import logging
logger = logging.getLogger('spmlogger')

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
                raise Exception("Contrast Estimate: Unknown stat %s for " \
                                    "contrast %d" % (contrast.stat, i))
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
                                                 script_name='pyscript_twosamplettest') 

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

class MultipleRegression(SpmMatlabCommandLine):
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

    opt_map = {'images': (None, 'con images from group 1'),
               'covariates': (None, 'dict of covariates {vectors, names, centering}'),
               'contrasts' : (None, 'similar to list of contrasts for level1 design'),
               'include_intercept': (None,
                             'Include intercept in model (opt, True)',),
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
        script += "jobs{1}.stats{1}.factorial_design.des.mreg.scans = {};\n"
        for f in filename_to_list(self.inputs.images):
            script += "jobs{1}.stats{1}.factorial_design.des.mreg.scans{end+1,1} = '%s';\n" % f
        script += "jobs{1}.stats{1}.factorial_design.des.mreg.mcov = [];\n"
        for i, name in enumerate(self.inputs.covariates['names']):
            script += "names{%d} = '%s';\n" % (i+1, name)
            script += "jobs{1}.stats{1}.factorial_design.des.mreg.mcov(end+1,1).cname = '%s';\n" % name
            centering = self.inputs.covariates['centering'][i]
            script += "jobs{1}.stats{1}.factorial_design.des.mreg.mcov(end,1).iCC = %d;\n" % centering
            for j, v in enumerate(self.inputs.covariates['vectors'][i]):
                script += "jobs{1}.stats{1}.factorial_design.des.mreg.mcov(end,1).c(%d,1)" \
                    " = %f;\n" % (j+1, v)
        if self.inputs.include_intercept or self.inputs.include_intercept is None:
            script += "names{end+1} = 'mean';\n"
        if self.inputs.include_intercept is not None:
            script += "jobs{1}.stats{1}.factorial_design.des.mreg.incint = %d;\n" % self.inputs.include_intercept
        (head,fname) = os.path.split(f)
        (conname,ext) = os.path.splitext(fname)
        script += "\n% Estimate Model;\n"
        script += "jobs{2}.stats{1}.fmri_est(1).spmmat = {'%s'};\n\n" % os.path.join(cwd,'SPM.mat')
        script += "% Estimate Contrast;\n"
        script += "jobs{3}.stats{1}.con.spmmat = {'%s'};\n"  % os.path.join(cwd,'SPM.mat')
        contrasts = []
        cname = []
        for i,cont in enumerate(self.inputs.contrasts):
            cname.insert(i,cont[0])
            contrasts.insert(i,Bunch(name=cont[0],
                                     stat=cont[1],
                                     conditions=cont[2],
                                     weights=None))
            if len(cont)>=4:
                contrasts[i].weights = cont[3]
        for i,contrast in enumerate(contrasts):
            if contrast.stat == 'T':
                script += "consess{%d}.tcon.name   = '%s';\n" % (i+1,contrast.name)
                script += "consess{%d}.tcon.convec = zeros(1,numel(names));\n" % (i+1)
                for c0,cond in enumerate(contrast.conditions):
                    script += "idx = strmatch('%s',names,'exact');\n" % (cond)
                    script += "consess{%d}.tcon.convec(idx) = %f;\n" % (i+1,contrast.weights[c0])
            elif contrast.stat == 'F':
                script += "consess{%d}.fcon.name   =  '%s';\n" % (i+1,contrast.name)
                for cl0,fcont in enumerate(contrast.conditions):
                    tidx = cname.index(fcont[0])
                    script += "consess{%d}.fcon.convec{%d} = consess{%d}.tcon.convec;\n" % (i+1,cl0+1,tidx+1)
            else:
                raise Exception("Contrast Estimate: Unknown stat %s"%contrast.stat)
        script += "jobs{3}.stats{1}.con.consess = consess;\n"
        script += "if strcmp(spm('ver'),'SPM8'), spm_jobman('initcfg');jobs=spm_jobman('spm5tospm8',{jobs});end\n" 
        script += "spm_jobman('run',jobs);\n"
        self._cmdline = self._gen_matlab_command(script,
                                                cwd=cwd,
                                                script_name='pyscript_multipleregression') 

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
