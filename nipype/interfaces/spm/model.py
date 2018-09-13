# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The spm module provides basic functions for interfacing with matlab
and spm to access spm tools.
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import str, bytes

# Standard library imports
import os
from glob import glob

# Third-party imports
import numpy as np
import scipy.io as sio

# Local imports
from ... import logging
from ...utils.filemanip import (ensure_list, simplify_list,
                                split_filename)
from ..base import (Bunch, traits, TraitedSpec, File, Directory,
                    OutputMultiPath, InputMultiPath, isdefined)
from .base import (SPMCommand, SPMCommandInputSpec, scans_for_fnames,
                   ImageFileSPM)

__docformat__ = 'restructuredtext'
iflogger = logging.getLogger('nipype.interface')


class Level1DesignInputSpec(SPMCommandInputSpec):
    spm_mat_dir = Directory(
        exists=True, field='dir', desc='directory to store SPM.mat file (opt)')
    timing_units = traits.Enum(
        'secs',
        'scans',
        field='timing.units',
        desc='units for specification of onsets',
        mandatory=True)
    interscan_interval = traits.Float(
        field='timing.RT', desc='Interscan interval in secs', mandatory=True)
    microtime_resolution = traits.Int(
        field='timing.fmri_t',
        desc=('Number of time-bins per scan '
              'in secs (opt)'))
    microtime_onset = traits.Float(
        field='timing.fmri_t0',
        desc=('The onset/time-bin in seconds for '
              'alignment (opt)'))
    session_info = traits.Any(
        field='sess',
        desc=('Session specific information generated '
              'by ``modelgen.SpecifyModel``'),
        mandatory=True)
    factor_info = traits.List(
        traits.Dict(traits.Enum('name', 'levels')),
        field='fact',
        desc=('Factor specific information '
              'file (opt)'))
    bases = traits.Dict(
        traits.Enum('hrf', 'fourier', 'fourier_han', 'gamma', 'fir'),
        field='bases',
        desc="""
            dict {'name':{'basesparam1':val,...}}
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
""",
        mandatory=True)
    volterra_expansion_order = traits.Enum(
        1, 2, field='volt', desc=('Model interactions - '
                                  'yes:1, no:2'))
    global_intensity_normalization = traits.Enum(
        'none',
        'scaling',
        field='global',
        desc=('Global intensity '
              'normalization - '
              'scaling or none'))
    mask_image = File(
        exists=True,
        field='mask',
        desc='Image  for  explicitly  masking the analysis')
    mask_threshold = traits.Either(
        traits.Enum('-Inf'),
        traits.Float(),
        desc="Thresholding for the mask",
        default='-Inf',
        usedefault=True)
    model_serial_correlations = traits.Enum(
        'AR(1)',
        'FAST',
        'none',
        field='cvi',
        desc=('Model serial correlations '
              'AR(1), FAST or none. FAST '
              'is available in SPM12'))


class Level1DesignOutputSpec(TraitedSpec):
    spm_mat_file = File(exists=True, desc='SPM mat file')


class Level1Design(SPMCommand):
    """Generate an SPM design matrix

    http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=59

    Examples
    --------

    >>> level1design = Level1Design()
    >>> level1design.inputs.timing_units = 'secs'
    >>> level1design.inputs.interscan_interval = 2.5
    >>> level1design.inputs.bases = {'hrf':{'derivs': [0,0]}}
    >>> level1design.inputs.session_info = 'session_info.npz'
    >>> level1design.run() # doctest: +SKIP

    """

    input_spec = Level1DesignInputSpec
    output_spec = Level1DesignOutputSpec

    _jobtype = 'stats'
    _jobname = 'fmri_spec'

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt in ['spm_mat_dir', 'mask_image']:
            return np.array([str(val)], dtype=object)
        if opt in ['session_info']:  # , 'factor_info']:
            if isinstance(val, dict):
                return [val]
            else:
                return val
        return super(Level1Design, self)._format_arg(opt, spec, val)

    def _parse_inputs(self):
        """validate spm realign options if set to None ignore
        """
        einputs = super(Level1Design,
                        self)._parse_inputs(skip=('mask_threshold'))
        for sessinfo in einputs[0]['sess']:
            sessinfo['scans'] = scans_for_fnames(
                ensure_list(sessinfo['scans']), keep4d=False)
        if not isdefined(self.inputs.spm_mat_dir):
            einputs[0]['dir'] = np.array([str(os.getcwd())], dtype=object)
        return einputs

    def _make_matlab_command(self, content):
        """validates spm options and generates job structure
        if mfile is True uses matlab .m file
        else generates a job structure and saves in .mat
        """
        if isdefined(self.inputs.mask_image):
            # SPM doesn't handle explicit masking properly, especially
            # when you want to use the entire mask image
            postscript = "load SPM;\n"
            postscript += ("SPM.xM.VM = spm_vol('%s');\n" % simplify_list(
                self.inputs.mask_image))
            postscript += "SPM.xM.I = 0;\n"
            postscript += "SPM.xM.T = [];\n"
            postscript += ("SPM.xM.TH = ones(size(SPM.xM.TH))*(%s);\n" %
                           self.inputs.mask_threshold)
            postscript += ("SPM.xM.xs = struct('Masking', "
                           "'explicit masking only');\n")
            postscript += "save SPM SPM;\n"
        else:
            postscript = None
        return super(Level1Design, self)._make_matlab_command(
            content, postscript=postscript)

    def _list_outputs(self):
        outputs = self._outputs().get()
        spm = os.path.join(os.getcwd(), 'SPM.mat')
        outputs['spm_mat_file'] = spm
        return outputs


class EstimateModelInputSpec(SPMCommandInputSpec):
    spm_mat_file = File(
        exists=True,
        field='spmmat',
        copyfile=True,
        mandatory=True,
        desc='Absolute path to SPM.mat')
    estimation_method = traits.Dict(
        traits.Enum('Classical', 'Bayesian2', 'Bayesian'),
        field='method',
        mandatory=True,
        desc=('Dictionary of either Classical: 1, Bayesian: 1, '
              'or Bayesian2: 1 (dict)'))
    write_residuals = traits.Bool(
        field='write_residuals', desc="Write individual residual images")
    flags = traits.Dict(desc='Additional arguments')


class EstimateModelOutputSpec(TraitedSpec):
    mask_image = ImageFileSPM(
        exists=True, desc='binary mask to constrain estimation')
    beta_images = OutputMultiPath(
        ImageFileSPM(exists=True), desc='design parameter estimates')
    residual_image = ImageFileSPM(
        exists=True, desc='Mean-squared image of the residuals')
    residual_images = OutputMultiPath(
        ImageFileSPM(exists=True),
        desc="individual residual images (requires `write_residuals`")
    RPVimage = ImageFileSPM(exists=True, desc='Resels per voxel image')
    spm_mat_file = File(exists=True, desc='Updated SPM mat file')
    labels = ImageFileSPM(exists=True, desc="label file")
    SDerror = OutputMultiPath(
        ImageFileSPM(exists=True),
        desc="Images of the standard deviation of the error")
    ARcoef = OutputMultiPath(
        ImageFileSPM(exists=True), desc="Images of the AR coefficient")
    Cbetas = OutputMultiPath(
        ImageFileSPM(exists=True), desc="Images of the parameter posteriors")
    SDbetas = OutputMultiPath(
        ImageFileSPM(exists=True),
        desc="Images of the standard deviation of parameter posteriors")


class EstimateModel(SPMCommand):
    """Use spm_spm to estimate the parameters of a model

    http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=69

    Examples
    --------
    >>> est = EstimateModel()
    >>> est.inputs.spm_mat_file = 'SPM.mat'
    >>> est.inputs.estimation_method = {'Classical': 1}
    >>> est.run() # doctest: +SKIP
    """
    input_spec = EstimateModelInputSpec
    output_spec = EstimateModelOutputSpec
    _jobtype = 'stats'
    _jobname = 'fmri_est'

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt == 'spm_mat_file':
            return np.array([str(val)], dtype=object)
        if opt == 'estimation_method':
            if isinstance(val, (str, bytes)):
                return {'{}'.format(val): 1}
            else:
                return val
        return super(EstimateModel, self)._format_arg(opt, spec, val)

    def _parse_inputs(self):
        """validate spm realign options if set to None ignore
        """
        einputs = super(EstimateModel, self)._parse_inputs(skip=('flags'))
        if isdefined(self.inputs.flags):
            einputs[0].update(
                {flag: val
                 for (flag, val) in self.inputs.flags.items()})
        return einputs

    def _list_outputs(self):
        outputs = self._outputs().get()
        pth = os.path.dirname(self.inputs.spm_mat_file)
        outtype = 'nii' if '12' in self.version.split('.')[0] else 'img'
        spm = sio.loadmat(self.inputs.spm_mat_file, struct_as_record=False)

        betas = [vbeta.fname[0] for vbeta in spm['SPM'][0, 0].Vbeta[0]]
        if ('Bayesian' in self.inputs.estimation_method.keys()
                or 'Bayesian2' in self.inputs.estimation_method.keys()):
            outputs['labels'] = os.path.join(pth, 'labels.{}'.format(outtype))
            outputs['SDerror'] = glob(os.path.join(pth, 'Sess*_SDerror*'))
            outputs['ARcoef'] = glob(os.path.join(pth, 'Sess*_AR_*'))
            if betas:
                outputs['Cbetas'] = [
                    os.path.join(pth, 'C{}'.format(beta)) for beta in betas
                ]
                outputs['SDbetas'] = [
                    os.path.join(pth, 'SD{}'.format(beta)) for beta in betas
                ]

        if 'Classical' in self.inputs.estimation_method.keys():
            outputs['residual_image'] = os.path.join(
                pth, 'ResMS.{}'.format(outtype))
            outputs['RPVimage'] = os.path.join(pth, 'RPV.{}'.format(outtype))
            if self.inputs.write_residuals:
                outputs['residual_images'] = glob(os.path.join(pth, 'Res_*'))
            if betas:
                outputs['beta_images'] = [
                    os.path.join(pth, beta) for beta in betas
                ]

        outputs['mask_image'] = os.path.join(pth, 'mask.{}'.format(outtype))
        outputs['spm_mat_file'] = os.path.join(pth, 'SPM.mat')
        return outputs


class EstimateContrastInputSpec(SPMCommandInputSpec):
    spm_mat_file = File(
        exists=True,
        field='spmmat',
        desc='Absolute path to SPM.mat',
        copyfile=True,
        mandatory=True)
    contrasts = traits.List(
        traits.Either(
            traits.Tuple(traits.Str, traits.Enum('T'), traits.List(traits.Str),
                         traits.List(traits.Float)),
            traits.Tuple(traits.Str, traits.Enum('T'), traits.List(traits.Str),
                         traits.List(traits.Float), traits.List(traits.Float)),
            traits.Tuple(traits.Str, traits.Enum('F'),
                         traits.List(
                             traits.Either(
                                 traits.Tuple(traits.Str, traits.Enum('T'),
                                              traits.List(traits.Str),
                                              traits.List(traits.Float)),
                                 traits.Tuple(traits.Str, traits.Enum('T'),
                                              traits.List(traits.Str),
                                              traits.List(traits.Float),
                                              traits.List(traits.Float)))))),
        desc="""List of contrasts with each contrast being a list of the form:
            [('name', 'stat', [condition list], [weight list], [session list])]
            If session list is None or not provided, all sessions are used. For
            F contrasts, the condition list should contain previously defined
            T-contrasts.""",
        mandatory=True)
    beta_images = InputMultiPath(
        File(exists=True),
        desc=('Parameter estimates of the '
              'design matrix'),
        copyfile=False,
        mandatory=True)
    residual_image = File(
        exists=True,
        desc='Mean-squared image of the residuals',
        copyfile=False,
        mandatory=True)
    use_derivs = traits.Bool(
        desc='use derivatives for estimation', xor=['group_contrast'])
    group_contrast = traits.Bool(
        desc='higher level contrast', xor=['use_derivs'])


class EstimateContrastOutputSpec(TraitedSpec):
    con_images = OutputMultiPath(
        File(exists=True), desc='contrast images from a t-contrast')
    spmT_images = OutputMultiPath(
        File(exists=True), desc='stat images from a t-contrast')
    ess_images = OutputMultiPath(
        File(exists=True), desc='contrast images from an F-contrast')
    spmF_images = OutputMultiPath(
        File(exists=True), desc='stat images from an F-contrast')
    spm_mat_file = File(exists=True, desc='Updated SPM mat file')


class EstimateContrast(SPMCommand):
    """Use spm_contrasts to estimate contrasts of interest

    Examples
    --------
    >>> import nipype.interfaces.spm as spm
    >>> est = spm.EstimateContrast()
    >>> est.inputs.spm_mat_file = 'SPM.mat'
    >>> cont1 = ('Task>Baseline','T', ['Task-Odd','Task-Even'],[0.5,0.5])
    >>> cont2 = ('Task-Odd>Task-Even','T', ['Task-Odd','Task-Even'],[1,-1])
    >>> contrasts = [cont1,cont2]
    >>> est.inputs.contrasts = contrasts
    >>> est.run() # doctest: +SKIP

    """

    input_spec = EstimateContrastInputSpec
    output_spec = EstimateContrastOutputSpec
    _jobtype = 'stats'
    _jobname = 'con'

    def _make_matlab_command(self, _):
        """validates spm options and generates job structure
        """
        contrasts = []
        cname = []
        for i, cont in enumerate(self.inputs.contrasts):
            cname.insert(i, cont[0])
            contrasts.insert(i,
                             Bunch(
                                 name=cont[0],
                                 stat=cont[1],
                                 conditions=cont[2],
                                 weights=None,
                                 sessions=None))
            if len(cont) >= 4:
                contrasts[i].weights = cont[3]
            if len(cont) >= 5:
                contrasts[i].sessions = cont[4]
        script = "% generated by nipype.interfaces.spm\n"
        script += "spm_defaults;\n"
        script += ("jobs{1}.stats{1}.con.spmmat  = {'%s'};\n" %
                   self.inputs.spm_mat_file)
        script += "load(jobs{1}.stats{1}.con.spmmat{:});\n"
        script += "SPM.swd = '%s';\n" % os.getcwd()
        script += "save(jobs{1}.stats{1}.con.spmmat{:},'SPM');\n"
        script += "names = SPM.xX.name;\n"
        # get names for columns
        if (isdefined(self.inputs.group_contrast)
                and self.inputs.group_contrast):
            script += "condnames=names;\n"
        else:
            if self.inputs.use_derivs:
                script += "pat = 'Sn\([0-9]*\) (.*)';\n"
            else:
                script += ("pat = 'Sn\([0-9]*\) (.*)\*bf\(1\)|Sn\([0-9]*\) "
                           ".*\*bf\([2-9]\)|Sn\([0-9]*\) (.*)';\n")
            script += "t = regexp(names,pat,'tokens');\n"
            # get sessidx for columns
            script += "pat1 = 'Sn\(([0-9].*)\)\s.*';\n"
            script += "t1 = regexp(names,pat1,'tokens');\n"
            script += ("for i0=1:numel(t),condnames{i0}='';condsess(i0)=0;if "
                       "~isempty(t{i0}{1}),condnames{i0} = t{i0}{1}{1};"
                       "condsess(i0)=str2num(t1{i0}{1}{1});end;end;\n")
        # BUILD CONTRAST SESSION STRUCTURE
        for i, contrast in enumerate(contrasts):
            if contrast.stat == 'T':
                script += ("consess{%d}.tcon.name   = '%s';\n" %
                           (i + 1, contrast.name))
                script += (
                    "consess{%d}.tcon.convec = zeros(1,numel(names));\n" %
                    (i + 1))
                for c0, cond in enumerate(contrast.conditions):
                    script += ("idx = strmatch('%s',condnames,'exact');\n" %
                               (cond))
                    script += (("if isempty(idx), throw(MException("
                                "'CondName:Chk', sprintf('Condition %%s not "
                                "found in design','%s'))); end;\n") % cond)
                    if contrast.sessions:
                        for sno, sw in enumerate(contrast.sessions):
                            script += ("sidx = find(condsess(idx)==%d);\n" %
                                       (sno + 1))
                            script += (("consess{%d}.tcon.convec(idx(sidx)) "
                                        "= %f;\n") %
                                       (i + 1, sw * contrast.weights[c0]))
                    else:
                        script += ("consess{%d}.tcon.convec(idx) = %f;\n" %
                                   (i + 1, contrast.weights[c0]))
        for i, contrast in enumerate(contrasts):
            if contrast.stat == 'F':
                script += ("consess{%d}.fcon.name   =  '%s';\n" %
                           (i + 1, contrast.name))
                for cl0, fcont in enumerate(contrast.conditions):
                    try:
                        tidx = cname.index(fcont[0])
                    except:
                        Exception("Contrast Estimate: could not get index of"
                                  " T contrast. probably not defined prior "
                                  "to the F contrasts")
                    script += (("consess{%d}.fcon.convec{%d} = "
                                "consess{%d}.tcon.convec;\n") %
                               (i + 1, cl0 + 1, tidx + 1))
        script += "jobs{1}.stats{1}.con.consess = consess;\n"
        script += ("if strcmp(spm('ver'),'SPM8'), spm_jobman('initcfg');"
                   "jobs=spm_jobman('spm5tospm8',{jobs});end\n")
        script += "spm_jobman('run',jobs);"
        return script

    def _list_outputs(self):
        outputs = self._outputs().get()
        pth, _ = os.path.split(self.inputs.spm_mat_file)
        spm = sio.loadmat(self.inputs.spm_mat_file, struct_as_record=False)
        con_images = []
        spmT_images = []
        for con in spm['SPM'][0, 0].xCon[0]:
            con_images.append(str(os.path.join(pth, con.Vcon[0, 0].fname[0])))
            spmT_images.append(str(os.path.join(pth, con.Vspm[0, 0].fname[0])))
        if con_images:
            outputs['con_images'] = con_images
            outputs['spmT_images'] = spmT_images
        spm12 = '12' in self.version.split('.')[0]
        if spm12:
            ess = glob(os.path.join(pth, 'ess*.nii'))
        else:
            ess = glob(os.path.join(pth, 'ess*.img'))
        if len(ess) > 0:
            outputs['ess_images'] = sorted(ess)
        if spm12:
            spmf = glob(os.path.join(pth, 'spmF*.nii'))
        else:
            spmf = glob(os.path.join(pth, 'spmF*.img'))
        if len(spmf) > 0:
            outputs['spmF_images'] = sorted(spmf)
        outputs['spm_mat_file'] = self.inputs.spm_mat_file
        return outputs


class ThresholdInputSpec(SPMCommandInputSpec):
    spm_mat_file = File(
        exists=True,
        desc='absolute path to SPM.mat',
        copyfile=True,
        mandatory=True)
    stat_image = File(
        exists=True, desc='stat image', copyfile=False, mandatory=True)
    contrast_index = traits.Int(
        mandatory=True, desc='which contrast in the SPM.mat to use')
    use_fwe_correction = traits.Bool(
        True,
        usedefault=True,
        desc=('whether to use FWE (Bonferroni) '
              'correction for initial threshold '
              '(height_threshold_type has to be '
              'set to p-value)'))
    use_topo_fdr = traits.Bool(
        True,
        usedefault=True,
        desc=('whether to use FDR over cluster extent '
              'probabilities'))
    height_threshold = traits.Float(
        0.05,
        usedefault=True,
        desc=('value for initial thresholding '
              '(defining clusters)'))
    height_threshold_type = traits.Enum(
        'p-value',
        'stat',
        usedefault=True,
        desc=('Is the cluster forming '
              'threshold a stat value or '
              'p-value?'))
    extent_fdr_p_threshold = traits.Float(
        0.05,
        usedefault=True,
        desc=('p threshold on FDR corrected '
              'cluster size probabilities'))
    extent_threshold = traits.Int(
        0, usedefault=True, desc='Minimum cluster size in voxels')
    force_activation = traits.Bool(
        False,
        usedefault=True,
        desc=('In case no clusters survive the '
              'topological inference step this '
              'will pick a culster with the highes '
              'sum of t-values. Use with care.'))


class ThresholdOutputSpec(TraitedSpec):
    thresholded_map = File(exists=True)
    n_clusters = traits.Int()
    pre_topo_fdr_map = File(exists=True)
    pre_topo_n_clusters = traits.Int()
    activation_forced = traits.Bool()
    cluster_forming_thr = traits.Float()


class Threshold(SPMCommand):
    """Topological FDR thresholding based on cluster extent/size. Smoothness is
    estimated from GLM residuals but is assumed to be the same for all of the
    voxels.

    Examples
    --------

    >>> thresh = Threshold()
    >>> thresh.inputs.spm_mat_file = 'SPM.mat'
    >>> thresh.inputs.stat_image = 'spmT_0001.img'
    >>> thresh.inputs.contrast_index = 1
    >>> thresh.inputs.extent_fdr_p_threshold = 0.05
    >>> thresh.run() # doctest: +SKIP
    """
    input_spec = ThresholdInputSpec
    output_spec = ThresholdOutputSpec

    def _gen_thresholded_map_filename(self):
        _, fname, ext = split_filename(self.inputs.stat_image)
        return os.path.abspath(fname + "_thr" + ext)

    def _gen_pre_topo_map_filename(self):
        _, fname, ext = split_filename(self.inputs.stat_image)
        return os.path.abspath(fname + "_pre_topo_thr" + ext)

    def _make_matlab_command(self, _):
        script = "con_index = %d;\n" % self.inputs.contrast_index
        script += "cluster_forming_thr = %f;\n" % self.inputs.height_threshold
        if self.inputs.use_fwe_correction:
            script += "thresDesc  = 'FWE';\n"
        else:
            script += "thresDesc  = 'none';\n"

        if self.inputs.use_topo_fdr:
            script += "use_topo_fdr  = 1;\n"
        else:
            script += "use_topo_fdr  = 0;\n"

        if self.inputs.force_activation:
            script += "force_activation  = 1;\n"
        else:
            script += "force_activation  = 0;\n"
        script += ("cluster_extent_p_fdr_thr = %f;\n" %
                   self.inputs.extent_fdr_p_threshold)
        script += "stat_filename = '%s';\n" % self.inputs.stat_image
        script += ("height_threshold_type = '%s';\n" %
                   self.inputs.height_threshold_type)
        script += "extent_threshold = %d;\n" % self.inputs.extent_threshold

        script += "load %s;\n" % self.inputs.spm_mat_file
        script += """
FWHM  = SPM.xVol.FWHM;
df = [SPM.xCon(con_index).eidf SPM.xX.erdf];
STAT = SPM.xCon(con_index).STAT;
R = SPM.xVol.R;
S = SPM.xVol.S;
n = 1;

switch thresDesc
    case 'FWE'
        cluster_forming_thr = spm_uc(cluster_forming_thr,df,STAT,R,n,S);

    case 'none'
        if strcmp(height_threshold_type, 'p-value')
            cluster_forming_thr = spm_u(cluster_forming_thr^(1/n),df,STAT);
        end
end

stat_map_vol = spm_vol(stat_filename);
[stat_map_data, stat_map_XYZmm] = spm_read_vols(stat_map_vol);

Z = stat_map_data(:)';
[x,y,z] = ind2sub(size(stat_map_data),(1:numel(stat_map_data))');
XYZ = cat(1, x', y', z');

XYZth = XYZ(:, Z >= cluster_forming_thr);
Zth = Z(Z >= cluster_forming_thr);

"""
        script += (("spm_write_filtered(Zth,XYZth,stat_map_vol.dim',"
                    "stat_map_vol.mat,'thresholded map', '%s');\n") %
                   self._gen_pre_topo_map_filename())
        script += """
max_size = 0;
max_size_index = 0;
th_nclusters = 0;
nclusters = 0;
if isempty(XYZth)
    thresholded_XYZ = [];
    thresholded_Z = [];
else
    if use_topo_fdr
        V2R        = 1/prod(FWHM(stat_map_vol.dim > 1));
        [uc,Pc,ue] = spm_uc_clusterFDR(cluster_extent_p_fdr_thr,df,STAT,R,n,Z,XYZ,V2R,cluster_forming_thr);
    end

    voxel_labels = spm_clusters(XYZth);
    nclusters = max(voxel_labels);

    thresholded_XYZ = [];
    thresholded_Z = [];

    for i = 1:nclusters
        cluster_size = sum(voxel_labels==i);
         if cluster_size > extent_threshold && (~use_topo_fdr || (cluster_size - uc) > -1)
            thresholded_XYZ = cat(2, thresholded_XYZ, XYZth(:,voxel_labels == i));
            thresholded_Z = cat(2, thresholded_Z, Zth(voxel_labels == i));
            th_nclusters = th_nclusters + 1;
         end
        if force_activation
            cluster_sum = sum(Zth(voxel_labels == i));
            if cluster_sum > max_size
                max_size = cluster_sum;
                max_size_index = i;
            end
        end
    end
end

activation_forced = 0;
if isempty(thresholded_XYZ)
    if force_activation && max_size ~= 0
        thresholded_XYZ = XYZth(:,voxel_labels == max_size_index);
        thresholded_Z = Zth(voxel_labels == max_size_index);
        th_nclusters = 1;
        activation_forced = 1;
    else
        thresholded_Z = [0];
        thresholded_XYZ = [1 1 1]';
        th_nclusters = 0;
    end
end

fprintf('activation_forced = %d\\n',activation_forced);
fprintf('pre_topo_n_clusters = %d\\n',nclusters);
fprintf('n_clusters = %d\\n',th_nclusters);
fprintf('cluster_forming_thr = %f\\n',cluster_forming_thr);

"""
        script += (("spm_write_filtered(thresholded_Z,thresholded_XYZ,"
                    "stat_map_vol.dim',stat_map_vol.mat,'thresholded map',"
                    " '%s');\n") % self._gen_thresholded_map_filename())

        return script

    def aggregate_outputs(self, runtime=None):
        outputs = self._outputs()
        setattr(outputs, 'thresholded_map',
                self._gen_thresholded_map_filename())
        setattr(outputs, 'pre_topo_fdr_map', self._gen_pre_topo_map_filename())
        for line in runtime.stdout.split('\n'):
            if line.startswith("activation_forced = "):
                setattr(outputs, 'activation_forced',
                        line[len("activation_forced = "):].strip() == "1")
            elif line.startswith("n_clusters = "):
                setattr(outputs, 'n_clusters',
                        int(line[len("n_clusters = "):].strip()))
            elif line.startswith("pre_topo_n_clusters = "):
                setattr(outputs, 'pre_topo_n_clusters',
                        int(line[len("pre_topo_n_clusters = "):].strip()))
            elif line.startswith("cluster_forming_thr = "):
                setattr(outputs, 'cluster_forming_thr',
                        float(line[len("cluster_forming_thr = "):].strip()))
        return outputs

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['thresholded_map'] = self._gen_thresholded_map_filename()
        outputs['pre_topo_fdr_map'] = self._gen_pre_topo_map_filename()
        return outputs


class ThresholdStatisticsInputSpec(SPMCommandInputSpec):
    spm_mat_file = File(
        exists=True,
        desc='absolute path to SPM.mat',
        copyfile=True,
        mandatory=True)
    stat_image = File(
        exists=True, desc='stat image', copyfile=False, mandatory=True)
    contrast_index = traits.Int(
        mandatory=True, desc='which contrast in the SPM.mat to use')
    height_threshold = traits.Float(
        desc=('stat value for initial '
              'thresholding (defining clusters)'),
        mandatory=True)
    extent_threshold = traits.Int(
        0, usedefault=True, desc="Minimum cluster size in voxels")


class ThresholdStatisticsOutputSpec(TraitedSpec):
    voxelwise_P_Bonf = traits.Float()
    voxelwise_P_RF = traits.Float()
    voxelwise_P_uncor = traits.Float()
    voxelwise_P_FDR = traits.Float()
    clusterwise_P_RF = traits.Float()
    clusterwise_P_FDR = traits.Float()


class ThresholdStatistics(SPMCommand):
    """Given height and cluster size threshold calculate theoretical
    probabilities concerning false positives

    Examples
    --------

    >>> thresh = ThresholdStatistics()
    >>> thresh.inputs.spm_mat_file = 'SPM.mat'
    >>> thresh.inputs.stat_image = 'spmT_0001.img'
    >>> thresh.inputs.contrast_index = 1
    >>> thresh.inputs.height_threshold = 4.56
    >>> thresh.run() # doctest: +SKIP
    """
    input_spec = ThresholdStatisticsInputSpec
    output_spec = ThresholdStatisticsOutputSpec

    def _make_matlab_command(self, _):
        script = "con_index = %d;\n" % self.inputs.contrast_index
        script += "cluster_forming_thr = %f;\n" % self.inputs.height_threshold
        script += "stat_filename = '%s';\n" % self.inputs.stat_image
        script += "extent_threshold = %d;\n" % self.inputs.extent_threshold
        script += "load '%s'\n" % self.inputs.spm_mat_file
        script += """
FWHM  = SPM.xVol.FWHM;
df = [SPM.xCon(con_index).eidf SPM.xX.erdf];
STAT = SPM.xCon(con_index).STAT;
R = SPM.xVol.R;
S = SPM.xVol.S;
n = 1;

voxelwise_P_Bonf = spm_P_Bonf(cluster_forming_thr,df,STAT,S,n)
voxelwise_P_RF = spm_P_RF(1,0,cluster_forming_thr,df,STAT,R,n)

stat_map_vol = spm_vol(stat_filename);
[stat_map_data, stat_map_XYZmm] = spm_read_vols(stat_map_vol);

Z = stat_map_data(:);
Zum = Z;

        switch STAT
            case 'Z'
                VPs = (1-spm_Ncdf(Zum)).^n;
                voxelwise_P_uncor = (1-spm_Ncdf(cluster_forming_thr)).^n
            case 'T'
                VPs = (1 - spm_Tcdf(Zum,df(2))).^n;
                voxelwise_P_uncor = (1 - spm_Tcdf(cluster_forming_thr,df(2))).^n
            case 'X'
                VPs = (1-spm_Xcdf(Zum,df(2))).^n;
                voxelwise_P_uncor = (1-spm_Xcdf(cluster_forming_thr,df(2))).^n
            case 'F'
                VPs = (1 - spm_Fcdf(Zum,df)).^n;
                voxelwise_P_uncor = (1 - spm_Fcdf(cluster_forming_thr,df)).^n
        end
        VPs = sort(VPs);

voxelwise_P_FDR = spm_P_FDR(cluster_forming_thr,df,STAT,n,VPs)

V2R        = 1/prod(FWHM(stat_map_vol.dim > 1));

clusterwise_P_RF = spm_P_RF(1,extent_threshold*V2R,cluster_forming_thr,df,STAT,R,n)

[x,y,z] = ind2sub(size(stat_map_data),(1:numel(stat_map_data))');
XYZ = cat(1, x', y', z');

[u, CPs, ue] = spm_uc_clusterFDR(0.05,df,STAT,R,n,Z,XYZ,V2R,cluster_forming_thr);

clusterwise_P_FDR = spm_P_clusterFDR(extent_threshold*V2R,df,STAT,R,n,cluster_forming_thr,CPs')
"""
        return script

    def aggregate_outputs(self, runtime=None, needed_outputs=None):
        outputs = self._outputs()
        cur_output = ""
        for line in runtime.stdout.split('\n'):
            if cur_output != "" and len(line.split()) != 0:
                setattr(outputs, cur_output, float(line))
                cur_output = ""
                continue
            if (len(line.split()) != 0 and line.split()[0] in [
                    "clusterwise_P_FDR", "clusterwise_P_RF",
                    "voxelwise_P_Bonf", "voxelwise_P_FDR", "voxelwise_P_RF",
                    "voxelwise_P_uncor"
            ]):
                cur_output = line.split()[0]
                continue

        return outputs


class FactorialDesignInputSpec(SPMCommandInputSpec):
    spm_mat_dir = Directory(
        exists=True, field='dir', desc='directory to store SPM.mat file (opt)')
    # Need to make an alias of InputMultiPath; the inputs below are not Path
    covariates = InputMultiPath(
        traits.Dict(
            key_trait=traits.Enum('vector', 'name', 'interaction',
                                  'centering')),
        field='cov',
        desc=('covariate dictionary {vector, name, '
              'interaction, centering}'))
    threshold_mask_none = traits.Bool(
        field='masking.tm.tm_none',
        xor=['threshold_mask_absolute', 'threshold_mask_relative'],
        desc='do not use threshold masking')
    threshold_mask_absolute = traits.Float(
        field='masking.tm.tma.athresh',
        xor=['threshold_mask_none', 'threshold_mask_relative'],
        desc='use an absolute threshold')
    threshold_mask_relative = traits.Float(
        field='masking.tm.tmr.rthresh',
        xor=['threshold_mask_absolute', 'threshold_mask_none'],
        desc=('threshold using a '
              'proportion of the global '
              'value'))
    use_implicit_threshold = traits.Bool(
        field='masking.im',
        desc=('use implicit mask NaNs or '
              'zeros to threshold'))
    explicit_mask_file = File(
        field='masking.em',  # requires cell
        desc='use an implicit mask file to threshold')
    global_calc_omit = traits.Bool(
        field='globalc.g_omit',
        xor=['global_calc_mean', 'global_calc_values'],
        desc='omit global calculation')
    global_calc_mean = traits.Bool(
        field='globalc.g_mean',
        xor=['global_calc_omit', 'global_calc_values'],
        desc='use mean for global calculation')
    global_calc_values = traits.List(
        traits.Float,
        field='globalc.g_user.global_uval',
        xor=['global_calc_mean', 'global_calc_omit'],
        desc='omit global calculation')
    no_grand_mean_scaling = traits.Bool(
        field='globalm.gmsca.gmsca_no',
        desc=('do not perform grand mean '
              'scaling'))
    global_normalization = traits.Enum(
        1,
        2,
        3,
        field='globalm.glonorm',
        desc=('global normalization None-1, '
              'Proportional-2, ANCOVA-3'))


class FactorialDesignOutputSpec(TraitedSpec):
    spm_mat_file = File(exists=True, desc='SPM mat file')


class FactorialDesign(SPMCommand):
    """Base class for factorial designs

    http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=77

    """

    input_spec = FactorialDesignInputSpec
    output_spec = FactorialDesignOutputSpec
    _jobtype = 'stats'
    _jobname = 'factorial_design'

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt in ['spm_mat_dir', 'explicit_mask_file']:
            return np.array([str(val)], dtype=object)
        if opt in ['covariates']:
            outlist = []
            mapping = {
                'name': 'cname',
                'vector': 'c',
                'interaction': 'iCFI',
                'centering': 'iCC'
            }
            for dictitem in val:
                outdict = {}
                for key, keyval in list(dictitem.items()):
                    outdict[mapping[key]] = keyval
                outlist.append(outdict)
            return outlist
        return super(FactorialDesign, self)._format_arg(opt, spec, val)

    def _parse_inputs(self):
        """validate spm realign options if set to None ignore
        """
        einputs = super(FactorialDesign, self)._parse_inputs()
        if not isdefined(self.inputs.spm_mat_dir):
            einputs[0]['dir'] = np.array([str(os.getcwd())], dtype=object)
        return einputs

    def _list_outputs(self):
        outputs = self._outputs().get()
        spm = os.path.join(os.getcwd(), 'SPM.mat')
        outputs['spm_mat_file'] = spm
        return outputs


class OneSampleTTestDesignInputSpec(FactorialDesignInputSpec):
    in_files = traits.List(
        File(exists=True),
        field='des.t1.scans',
        mandatory=True,
        minlen=2,
        desc='input files')


class OneSampleTTestDesign(FactorialDesign):
    """Create SPM design for one sample t-test

    Examples
    --------

    >>> ttest = OneSampleTTestDesign()
    >>> ttest.inputs.in_files = ['cont1.nii', 'cont2.nii']
    >>> ttest.run() # doctest: +SKIP
    """

    input_spec = OneSampleTTestDesignInputSpec

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt in ['in_files']:
            return np.array(val, dtype=object)
        return super(OneSampleTTestDesign, self)._format_arg(opt, spec, val)


class TwoSampleTTestDesignInputSpec(FactorialDesignInputSpec):
    # very unlikely that you will have a single image in one group, so setting
    # parameters to require at least two files in each group [SG]
    group1_files = traits.List(
        File(exists=True),
        field='des.t2.scans1',
        mandatory=True,
        minlen=2,
        desc='Group 1 input files')
    group2_files = traits.List(
        File(exists=True),
        field='des.t2.scans2',
        mandatory=True,
        minlen=2,
        desc='Group 2 input files')
    dependent = traits.Bool(
        field='des.t2.dept',
        desc=('Are the measurements dependent between '
              'levels'))
    unequal_variance = traits.Bool(
        field='des.t2.variance',
        desc=('Are the variances equal or unequal '
              'between groups'))


class TwoSampleTTestDesign(FactorialDesign):
    """Create SPM design for two sample t-test

    Examples
    --------

    >>> ttest = TwoSampleTTestDesign()
    >>> ttest.inputs.group1_files = ['cont1.nii', 'cont2.nii']
    >>> ttest.inputs.group2_files = ['cont1a.nii', 'cont2a.nii']
    >>> ttest.run() # doctest: +SKIP
    """

    input_spec = TwoSampleTTestDesignInputSpec

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt in ['group1_files', 'group2_files']:
            return np.array(val, dtype=object)
        return super(TwoSampleTTestDesign, self)._format_arg(opt, spec, val)


class PairedTTestDesignInputSpec(FactorialDesignInputSpec):
    paired_files = traits.List(
        traits.List(File(exists=True), minlen=2, maxlen=2),
        field='des.pt.pair',
        mandatory=True,
        minlen=2,
        desc='List of paired files')
    grand_mean_scaling = traits.Bool(
        field='des.pt.gmsca', desc='Perform grand mean scaling')
    ancova = traits.Bool(
        field='des.pt.ancova', desc='Specify ancova-by-factor regressors')


class PairedTTestDesign(FactorialDesign):
    """Create SPM design for paired t-test

    Examples
    --------

    >>> pttest = PairedTTestDesign()
    >>> pttest.inputs.paired_files = [['cont1.nii','cont1a.nii'],['cont2.nii','cont2a.nii']]
    >>> pttest.run() # doctest: +SKIP
    """

    input_spec = PairedTTestDesignInputSpec

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt in ['paired_files']:
            return [dict(scans=np.array(files, dtype=object)) for files in val]
        return super(PairedTTestDesign, self)._format_arg(opt, spec, val)


class MultipleRegressionDesignInputSpec(FactorialDesignInputSpec):
    in_files = traits.List(
        File(exists=True),
        field='des.mreg.scans',
        mandatory=True,
        minlen=2,
        desc='List of files')
    include_intercept = traits.Bool(
        True,
        field='des.mreg.incint',
        usedefault=True,
        desc='Include intercept in design')
    user_covariates = InputMultiPath(
        traits.Dict(key_trait=traits.Enum('vector', 'name', 'centering')),
        field='des.mreg.mcov',
        desc=('covariate dictionary {vector, '
              'name, centering}'))


class MultipleRegressionDesign(FactorialDesign):
    """Create SPM design for multiple regression

    Examples
    --------

    >>> mreg = MultipleRegressionDesign()
    >>> mreg.inputs.in_files = ['cont1.nii','cont2.nii']
    >>> mreg.run() # doctest: +SKIP
    """

    input_spec = MultipleRegressionDesignInputSpec

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt in ['in_files']:
            return np.array(val, dtype=object)
        if opt in ['user_covariates']:
            outlist = []
            mapping = {'name': 'cname', 'vector': 'c', 'centering': 'iCC'}
            for dictitem in val:
                outdict = {}
                for key, keyval in list(dictitem.items()):
                    outdict[mapping[key]] = keyval
                outlist.append(outdict)
            return outlist
        return (super(MultipleRegressionDesign, self)._format_arg(
            opt, spec, val))
