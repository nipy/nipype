# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import range, open

import os
from glob import glob
from shutil import rmtree
from string import Template

import numpy as np
from nibabel import load

from ... import LooseVersion
from ...utils.filemanip import list_to_filename, filename_to_list
from ...utils.misc import human_order_sorted
from ...external.due import BibTeX
from ..base import (File, traits, isdefined, TraitedSpec, BaseInterface,
                    Directory, InputMultiPath, OutputMultiPath,
                    BaseInterfaceInputSpec)
from .base import FSLCommand, FSLCommandInputSpec, Info


class Level1DesignInputSpec(BaseInterfaceInputSpec):
    interscan_interval = traits.Float(
        mandatory=True, desc='Interscan  interval (in secs)')
    session_info = traits.Any(
        mandatory=True,
        desc=('Session specific information generated '
              'by ``modelgen.SpecifyModel``'))
    bases = traits.Either(
        traits.Dict(
            traits.Enum('dgamma'),
            traits.Dict(traits.Enum('derivs'), traits.Bool)),
        traits.Dict(
            traits.Enum('gamma'),
            traits.Dict(traits.Enum('derivs', 'gammasigma', 'gammadelay'))),
        traits.Dict(
            traits.Enum('custom'),
            traits.Dict(traits.Enum('bfcustompath'), traits.Str)),
        traits.Dict(traits.Enum('none'), traits.Dict()),
        traits.Dict(traits.Enum('none'), traits.Enum(None)),
        mandatory=True,
        desc=("name of basis function and options e.g., "
              "{'dgamma': {'derivs': True}}"),
    )
    orthogonalization = traits.Dict(
        traits.Int,
        traits.Dict(traits.Int, traits.Either(traits.Bool, traits.Int)),
        desc=("which regressors to make orthogonal e.g., "
              "{1: {0:0,1:0,2:0}, 2: {0:1,1:1,2:0}} to make the second "
              "regressor in a 2-regressor model orthogonal to the first."),
        default={})
    model_serial_correlations = traits.Bool(
        desc="Option to model serial correlations using an \
autoregressive estimator (order 1). Setting this option is only \
useful in the context of the fsf file. If you set this to False, you need to \
repeat this option for FILMGLS by setting autocorr_noestimate to True",
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
        desc="List of contrasts with each contrast being a list of the form - \
[('name', 'stat', [condition list], [weight list], [session list])]. if \
session list is None or not provided, all sessions are used. For F \
contrasts, the condition list should contain previously defined \
T-contrasts.")


class Level1DesignOutputSpec(TraitedSpec):
    fsf_files = OutputMultiPath(
        File(exists=True), desc='FSL feat specification files')
    ev_files = OutputMultiPath(
        traits.List(File(exists=True)), desc='condition information files')


class Level1Design(BaseInterface):
    """Generate FEAT specific files

    Examples
    --------

    >>> level1design = Level1Design()
    >>> level1design.inputs.interscan_interval = 2.5
    >>> level1design.inputs.bases = {'dgamma':{'derivs': False}}
    >>> level1design.inputs.session_info = 'session_info.npz'
    >>> level1design.run() # doctest: +SKIP

    """

    input_spec = Level1DesignInputSpec
    output_spec = Level1DesignOutputSpec

    def _create_ev_file(self, evfname, evinfo):
        f = open(evfname, 'wt')
        for i in evinfo:
            if len(i) == 3:
                f.write('%f %f %f\n' % (i[0], i[1], i[2]))
            else:
                f.write('%f\n' % i[0])
        f.close()

    def _create_ev_files(self, cwd, runinfo, runidx, ev_parameters,
                         orthogonalization, contrasts, do_tempfilter,
                         basis_key):
        """Creates EV files from condition and regressor information.

           Parameters:
           -----------

           runinfo : dict
               Generated by `SpecifyModel` and contains information
               about events and other regressors.
           runidx  : int
               Index to run number
           ev_parameters : dict
               A dictionary containing the model parameters for the
               given design type.
           orthogonalization : dict
               A dictionary of dictionaries specifying orthogonal EVs.
           contrasts : list of lists
               Information on contrasts to be evaluated
        """
        conds = {}
        evname = []
        if basis_key == "dgamma":
            basis_key = "hrf"
        elif basis_key == "gamma":
            try:
                _ = ev_parameters['gammasigma']
            except KeyError:
                ev_parameters['gammasigma'] = 3
            try:
                _ = ev_parameters['gammadelay']
            except KeyError:
                ev_parameters['gammadelay'] = 6
        ev_template = load_template('feat_ev_' + basis_key + '.tcl')
        ev_none = load_template('feat_ev_none.tcl')
        ev_ortho = load_template('feat_ev_ortho.tcl')
        ev_txt = ''
        # generate sections for conditions and other nuisance
        # regressors
        num_evs = [0, 0]
        for field in ['cond', 'regress']:
            for i, cond in enumerate(runinfo[field]):
                name = cond['name']
                evname.append(name)
                evfname = os.path.join(cwd, 'ev_%s_%d_%d.txt' % (name, runidx,
                                                                 len(evname)))
                evinfo = []
                num_evs[0] += 1
                num_evs[1] += 1
                if field == 'cond':
                    for j, onset in enumerate(cond['onset']):
                        try:
                            amplitudes = cond['amplitudes']
                            if len(amplitudes) > 1:
                                amp = amplitudes[j]
                            else:
                                amp = amplitudes[0]
                        except KeyError:
                            amp = 1
                        if len(cond['duration']) > 1:
                            evinfo.insert(j, [onset, cond['duration'][j], amp])
                        else:
                            evinfo.insert(j, [onset, cond['duration'][0], amp])
                    ev_parameters['cond_file'] = evfname
                    ev_parameters['ev_num'] = num_evs[0]
                    ev_parameters['ev_name'] = name
                    ev_parameters['tempfilt_yn'] = do_tempfilter
                    if 'basisorth' not in ev_parameters:
                        ev_parameters['basisorth'] = 1
                    if 'basisfnum' not in ev_parameters:
                        ev_parameters['basisfnum'] = 1
                    try:
                        ev_parameters['fsldir'] = os.environ['FSLDIR']
                    except KeyError:
                        if basis_key == 'flobs':
                            raise Exception(
                                'FSL environment variables not set')
                        else:
                            ev_parameters['fsldir'] = '/usr/share/fsl'
                    ev_parameters['temporalderiv'] = int(
                        bool(ev_parameters.get('derivs', False)))
                    if ev_parameters['temporalderiv']:
                        evname.append(name + 'TD')
                        num_evs[1] += 1
                    ev_txt += ev_template.substitute(ev_parameters)
                elif field == 'regress':
                    evinfo = [[j] for j in cond['val']]
                    ev_txt += ev_none.substitute(
                        ev_num=num_evs[0],
                        ev_name=name,
                        tempfilt_yn=do_tempfilter,
                        cond_file=evfname)
                ev_txt += "\n"
                conds[name] = evfname
                self._create_ev_file(evfname, evinfo)
        # add ev orthogonalization
        for i in range(1, num_evs[0] + 1):
            for j in range(0, num_evs[0] + 1):
                try:
                    orthogonal = int(orthogonalization[i][j])
                except (KeyError, TypeError, ValueError, IndexError):
                    orthogonal = 0
                ev_txt += ev_ortho.substitute(
                    c0=i, c1=j, orthogonal=orthogonal)
                ev_txt += "\n"
        # add contrast info to fsf file
        if isdefined(contrasts):
            contrast_header = load_template('feat_contrast_header.tcl')
            contrast_prolog = load_template('feat_contrast_prolog.tcl')
            contrast_element = load_template('feat_contrast_element.tcl')
            contrast_ftest_element = load_template(
                'feat_contrast_ftest_element.tcl')
            contrastmask_header = load_template('feat_contrastmask_header.tcl')
            contrastmask_footer = load_template('feat_contrastmask_footer.tcl')
            contrastmask_element = load_template(
                'feat_contrastmask_element.tcl')
            # add t/f contrast info
            ev_txt += contrast_header.substitute()
            con_names = []
            for j, con in enumerate(contrasts):
                con_names.append(con[0])
            con_map = {}
            ftest_idx = []
            ttest_idx = []
            for j, con in enumerate(contrasts):
                if con[1] == 'F':
                    ftest_idx.append(j)
                    for c in con[2]:
                        if c[0] not in list(con_map.keys()):
                            con_map[c[0]] = []
                        con_map[c[0]].append(j)
                else:
                    ttest_idx.append(j)

            for ctype in ['real', 'orig']:
                for j, con in enumerate(contrasts):
                    if con[1] == 'F':
                        continue
                    tidx = ttest_idx.index(j) + 1
                    ev_txt += contrast_prolog.substitute(
                        cnum=tidx, ctype=ctype, cname=con[0])
                    count = 0
                    for c in range(1, len(evname) + 1):
                        if evname[c - 1].endswith('TD') and ctype == 'orig':
                            continue
                        count = count + 1
                        if evname[c - 1] in con[2]:
                            val = con[3][con[2].index(evname[c - 1])]
                        else:
                            val = 0.0
                        ev_txt += contrast_element.substitute(
                            cnum=tidx, element=count, ctype=ctype, val=val)
                        ev_txt += "\n"

                    for fconidx in ftest_idx:
                        fval = 0
                        if (con[0] in con_map.keys()
                                and fconidx in con_map[con[0]]):
                            fval = 1
                        ev_txt += contrast_ftest_element.substitute(
                            cnum=ftest_idx.index(fconidx) + 1,
                            element=tidx,
                            ctype=ctype,
                            val=fval)
                        ev_txt += "\n"

            # add contrast mask info
            ev_txt += contrastmask_header.substitute()
            for j, _ in enumerate(contrasts):
                for k, _ in enumerate(contrasts):
                    if j != k:
                        ev_txt += contrastmask_element.substitute(
                            c1=j + 1, c2=k + 1)
            ev_txt += contrastmask_footer.substitute()
        return num_evs, ev_txt

    def _format_session_info(self, session_info):
        if isinstance(session_info, dict):
            session_info = [session_info]
        return session_info

    def _get_func_files(self, session_info):
        """Returns functional files in the order of runs
        """
        func_files = []
        for i, info in enumerate(session_info):
            func_files.insert(i, info['scans'])
        return func_files

    def _run_interface(self, runtime):
        cwd = os.getcwd()
        fsf_header = load_template('feat_header_l1.tcl')
        fsf_postscript = load_template('feat_nongui.tcl')

        prewhiten = 0
        if isdefined(self.inputs.model_serial_correlations):
            prewhiten = int(self.inputs.model_serial_correlations)
        basis_key = list(self.inputs.bases.keys())[0]
        ev_parameters = dict(self.inputs.bases[basis_key])
        session_info = self._format_session_info(self.inputs.session_info)
        func_files = self._get_func_files(session_info)
        n_tcon = 0
        n_fcon = 0
        if isdefined(self.inputs.contrasts):
            for i, c in enumerate(self.inputs.contrasts):
                if c[1] == 'T':
                    n_tcon += 1
                elif c[1] == 'F':
                    n_fcon += 1

        for i, info in enumerate(session_info):
            do_tempfilter = 1
            if info['hpf'] == np.inf:
                do_tempfilter = 0
            num_evs, cond_txt = self._create_ev_files(
                cwd, info, i, ev_parameters, self.inputs.orthogonalization,
                self.inputs.contrasts, do_tempfilter, basis_key)
            nim = load(func_files[i])
            (_, _, _, timepoints) = nim.shape
            fsf_txt = fsf_header.substitute(
                run_num=i,
                interscan_interval=self.inputs.interscan_interval,
                num_vols=timepoints,
                prewhiten=prewhiten,
                num_evs=num_evs[0],
                num_evs_real=num_evs[1],
                num_tcon=n_tcon,
                num_fcon=n_fcon,
                high_pass_filter_cutoff=info['hpf'],
                temphp_yn=do_tempfilter,
                func_file=func_files[i])
            fsf_txt += cond_txt
            fsf_txt += fsf_postscript.substitute(overwrite=1)

            f = open(os.path.join(cwd, 'run%d.fsf' % i), 'w')
            f.write(fsf_txt)
            f.close()

        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        cwd = os.getcwd()
        outputs['fsf_files'] = []
        outputs['ev_files'] = []
        basis_key = list(self.inputs.bases.keys())[0]
        ev_parameters = dict(self.inputs.bases[basis_key])
        for runno, runinfo in enumerate(
                self._format_session_info(self.inputs.session_info)):
            outputs['fsf_files'].append(os.path.join(cwd, 'run%d.fsf' % runno))
            outputs['ev_files'].insert(runno, [])
            evname = []
            for field in ['cond', 'regress']:
                for i, cond in enumerate(runinfo[field]):
                    name = cond['name']
                    evname.append(name)
                    evfname = os.path.join(cwd,
                                           'ev_%s_%d_%d.txt' % (name, runno,
                                                                len(evname)))
                    if field == 'cond':
                        ev_parameters['temporalderiv'] = int(
                            bool(ev_parameters.get('derivs', False)))
                        if ev_parameters['temporalderiv']:
                            evname.append(name + 'TD')
                    outputs['ev_files'][runno].append(
                        os.path.join(cwd, evfname))
        return outputs


class FEATInputSpec(FSLCommandInputSpec):
    fsf_file = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=0,
        desc="File specifying the feat design spec file")


class FEATOutputSpec(TraitedSpec):
    feat_dir = Directory(exists=True)


class FEAT(FSLCommand):
    """Uses FSL feat to calculate first level stats
    """
    _cmd = 'feat'
    input_spec = FEATInputSpec
    output_spec = FEATOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        is_ica = False
        outputs['feat_dir'] = None
        with open(self.inputs.fsf_file, 'rt') as fp:
            text = fp.read()
            if "set fmri(inmelodic) 1" in text:
                is_ica = True
            for line in text.split('\n'):
                if line.find("set fmri(outputdir)") > -1:
                    try:
                        outputdir_spec = line.split('"')[-2]
                        if os.path.exists(outputdir_spec):
                            outputs['feat_dir'] = outputdir_spec

                    except:
                        pass
        if not outputs['feat_dir']:
            if is_ica:
                outputs['feat_dir'] = glob(os.path.join(os.getcwd(),
                                                        '*ica'))[0]
            else:
                outputs['feat_dir'] = glob(os.path.join(os.getcwd(),
                                                        '*feat'))[0]
        print('Outputs from FEATmodel:', outputs)
        return outputs


class FEATModelInputSpec(FSLCommandInputSpec):
    fsf_file = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=0,
        desc="File specifying the feat design spec file",
        copyfile=False)
    ev_files = traits.List(
        File(exists=True),
        mandatory=True,
        argstr="%s",
        desc="Event spec files generated by level1design",
        position=1,
        copyfile=False)


class FEATModelOutpuSpec(TraitedSpec):
    design_file = File(
        exists=True, desc='Mat file containing ascii matrix for design')
    design_image = File(
        exists=True, desc='Graphical representation of design matrix')
    design_cov = File(
        exists=True, desc='Graphical representation of design covariance')
    con_file = File(
        exists=True, desc='Contrast file containing contrast vectors')
    fcon_file = File(desc='Contrast file containing contrast vectors')


class FEATModel(FSLCommand):
    """Uses FSL feat_model to generate design.mat files
    """
    _cmd = 'feat_model'
    input_spec = FEATModelInputSpec
    output_spec = FEATModelOutpuSpec

    def _format_arg(self, name, trait_spec, value):
        if name == 'fsf_file':
            return super(FEATModel,
                         self)._format_arg(name, trait_spec,
                                           self._get_design_root(value))
        elif name == 'ev_files':
            return ''
        else:
            return super(FEATModel, self)._format_arg(name, trait_spec, value)

    def _get_design_root(self, infile):
        _, fname = os.path.split(infile)
        return fname.split('.')[0]

    def _list_outputs(self):
        # TODO: figure out file names and get rid off the globs
        outputs = self._outputs().get()
        root = self._get_design_root(list_to_filename(self.inputs.fsf_file))
        design_file = glob(os.path.join(os.getcwd(), '%s*.mat' % root))
        assert len(design_file) == 1, 'No mat file generated by FEAT Model'
        outputs['design_file'] = design_file[0]
        design_image = glob(os.path.join(os.getcwd(), '%s.png' % root))
        assert len(
            design_image) == 1, 'No design image generated by FEAT Model'
        outputs['design_image'] = design_image[0]
        design_cov = glob(os.path.join(os.getcwd(), '%s_cov.png' % root))
        assert len(
            design_cov) == 1, 'No covariance image generated by FEAT Model'
        outputs['design_cov'] = design_cov[0]
        con_file = glob(os.path.join(os.getcwd(), '%s*.con' % root))
        assert len(con_file) == 1, 'No con file generated by FEAT Model'
        outputs['con_file'] = con_file[0]
        fcon_file = glob(os.path.join(os.getcwd(), '%s*.fts' % root))
        if fcon_file:
            assert len(fcon_file) == 1, 'No fts file generated by FEAT Model'
            outputs['fcon_file'] = fcon_file[0]
        return outputs


class FILMGLSInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        position=-3,
        argstr='%s',
        desc='input data file')
    design_file = File(
        exists=True, position=-2, argstr='%s', desc='design matrix file')
    threshold = traits.Range(
        default=1000.,
        low=0.0,
        argstr='%f',
        position=-1,
        usedefault=True,
        desc='threshold')
    smooth_autocorr = traits.Bool(
        argstr='-sa', desc='Smooth auto corr estimates')
    mask_size = traits.Int(argstr='-ms %d', desc="susan mask size")
    brightness_threshold = traits.Range(
        low=0,
        argstr='-epith %d',
        desc=('susan brightness threshold, '
              'otherwise it is estimated'))
    full_data = traits.Bool(argstr='-v', desc='output full data')
    _estimate_xor = [
        'autocorr_estimate_only', 'fit_armodel', 'tukey_window',
        'multitaper_product', 'use_pava', 'autocorr_noestimate'
    ]
    autocorr_estimate_only = traits.Bool(
        argstr='-ac',
        xor=_estimate_xor,
        desc=('perform autocorrelation '
              'estimatation only'))
    fit_armodel = traits.Bool(
        argstr='-ar',
        xor=_estimate_xor,
        desc=('fits autoregressive model - default is '
              'to use tukey with M=sqrt(numvols)'))
    tukey_window = traits.Int(
        argstr='-tukey %d',
        xor=_estimate_xor,
        desc='tukey window size to estimate autocorr')
    multitaper_product = traits.Int(
        argstr='-mt %d',
        xor=_estimate_xor,
        desc=('multitapering with slepian tapers '
              'and num is the time-bandwidth '
              'product'))
    use_pava = traits.Bool(
        argstr='-pava', desc='estimates autocorr using PAVA')
    autocorr_noestimate = traits.Bool(
        argstr='-noest', xor=_estimate_xor, desc='do not estimate autocorrs')
    output_pwdata = traits.Bool(
        argstr='-output_pwdata',
        desc=('output prewhitened data and average '
              'design matrix'))
    results_dir = Directory(
        'results',
        argstr='-rn %s',
        usedefault=True,
        desc='directory to store results in')


class FILMGLSInputSpec505(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        position=-3,
        argstr='--in=%s',
        desc='input data file')
    design_file = File(
        exists=True, position=-2, argstr='--pd=%s', desc='design matrix file')
    threshold = traits.Range(
        default=1000.,
        low=0.0,
        argstr='--thr=%f',
        position=-1,
        usedefault=True,
        desc='threshold')
    smooth_autocorr = traits.Bool(
        argstr='--sa', desc='Smooth auto corr estimates')
    mask_size = traits.Int(argstr='--ms=%d', desc="susan mask size")
    brightness_threshold = traits.Range(
        low=0,
        argstr='--epith=%d',
        desc=('susan brightness threshold, '
              'otherwise it is estimated'))
    full_data = traits.Bool(argstr='-v', desc='output full data')
    _estimate_xor = [
        'autocorr_estimate_only', 'fit_armodel', 'tukey_window',
        'multitaper_product', 'use_pava', 'autocorr_noestimate'
    ]
    autocorr_estimate_only = traits.Bool(
        argstr='--ac',
        xor=_estimate_xor,
        desc=('perform autocorrelation '
              'estimation only'))
    fit_armodel = traits.Bool(
        argstr='--ar',
        xor=_estimate_xor,
        desc=('fits autoregressive model - default is '
              'to use tukey with M=sqrt(numvols)'))
    tukey_window = traits.Int(
        argstr='--tukey=%d',
        xor=_estimate_xor,
        desc='tukey window size to estimate autocorr')
    multitaper_product = traits.Int(
        argstr='--mt=%d',
        xor=_estimate_xor,
        desc=('multitapering with slepian tapers '
              'and num is the time-bandwidth '
              'product'))
    use_pava = traits.Bool(
        argstr='--pava', desc='estimates autocorr using PAVA')
    autocorr_noestimate = traits.Bool(
        argstr='--noest', xor=_estimate_xor, desc='do not estimate autocorrs')
    output_pwdata = traits.Bool(
        argstr='--outputPWdata',
        desc=('output prewhitened data and average '
              'design matrix'))
    results_dir = Directory(
        'results',
        argstr='--rn=%s',
        usedefault=True,
        desc='directory to store results in')


class FILMGLSInputSpec507(FILMGLSInputSpec505):
    threshold = traits.Float(
        default=-1000.,
        argstr='--thr=%f',
        position=-1,
        usedefault=True,
        desc='threshold')
    tcon_file = File(
        exists=True,
        argstr='--con=%s',
        desc='contrast file containing T-contrasts')
    fcon_file = File(
        exists=True,
        argstr='--fcon=%s',
        desc='contrast file containing F-contrasts')
    mode = traits.Enum(
        'volumetric',
        'surface',
        argstr="--mode=%s",
        desc="Type of analysis to be done")
    surface = File(
        exists=True,
        argstr="--in2=%s",
        desc=("input surface for autocorr smoothing in "
              "surface-based analyses"))


class FILMGLSOutputSpec(TraitedSpec):
    param_estimates = OutputMultiPath(
        File(exists=True),
        desc=('Parameter estimates for each '
              'column of the design matrix'))
    residual4d = File(
        exists=True,
        desc=('Model fit residual mean-squared error for each '
              'time point'))
    dof_file = File(exists=True, desc='degrees of freedom')
    sigmasquareds = File(
        exists=True, desc='summary of residuals, See Woolrich, et. al., 2001')
    results_dir = Directory(
        exists=True, desc='directory storing model estimation output')
    corrections = File(
        exists=True,
        desc=('statistical corrections used within FILM '
              'modeling'))
    thresholdac = File(exists=True, desc='The FILM autocorrelation parameters')
    logfile = File(exists=True, desc='FILM run logfile')


class FILMGLSOutputSpec507(TraitedSpec):
    param_estimates = OutputMultiPath(
        File(exists=True),
        desc=('Parameter estimates for each '
              'column of the design matrix'))
    residual4d = File(
        exists=True,
        desc=('Model fit residual mean-squared error for each '
              'time point'))
    dof_file = File(exists=True, desc='degrees of freedom')
    sigmasquareds = File(
        exists=True, desc='summary of residuals, See Woolrich, et. al., 2001')
    results_dir = Directory(
        exists=True, desc='directory storing model estimation output')
    thresholdac = File(exists=True, desc='The FILM autocorrelation parameters')
    logfile = File(exists=True, desc='FILM run logfile')
    copes = OutputMultiPath(
        File(exists=True), desc='Contrast estimates for each contrast')
    varcopes = OutputMultiPath(
        File(exists=True), desc='Variance estimates for each contrast')
    zstats = OutputMultiPath(
        File(exists=True), desc='z-stat file for each contrast')
    tstats = OutputMultiPath(
        File(exists=True), desc='t-stat file for each contrast')
    fstats = OutputMultiPath(
        File(exists=True), desc='f-stat file for each contrast')
    zfstats = OutputMultiPath(
        File(exists=True), desc='z-stat file for each F contrast')


class FILMGLS(FSLCommand):
    """Use FSL film_gls command to fit a design matrix to voxel timeseries

    Examples
    --------

    Initialize with no options, assigning them when calling run:

    >>> from nipype.interfaces import fsl
    >>> fgls = fsl.FILMGLS()
    >>> res = fgls.run('in_file', 'design_file', 'thresh', rn='stats') #doctest: +SKIP

    Assign options through the ``inputs`` attribute:

    >>> fgls = fsl.FILMGLS()
    >>> fgls.inputs.in_file = 'functional.nii'
    >>> fgls.inputs.design_file = 'design.mat'
    >>> fgls.inputs.threshold = 10
    >>> fgls.inputs.results_dir = 'stats'
    >>> res = fgls.run() #doctest: +SKIP

    Specify options when creating an instance:

    >>> fgls = fsl.FILMGLS(in_file='functional.nii', \
design_file='design.mat', \
threshold=10, results_dir='stats')
    >>> res = fgls.run() #doctest: +SKIP

    """

    _cmd = 'film_gls'
    input_spec = FILMGLSInputSpec
    output_spec = FILMGLSOutputSpec
    if Info.version() and LooseVersion(Info.version()) > LooseVersion('5.0.6'):
        input_spec = FILMGLSInputSpec507
        output_spec = FILMGLSOutputSpec507
    elif (Info.version()
          and LooseVersion(Info.version()) > LooseVersion('5.0.4')):
        input_spec = FILMGLSInputSpec505

    def _get_pe_files(self, cwd):
        files = None
        if isdefined(self.inputs.design_file):
            fp = open(self.inputs.design_file, 'rt')
            for line in fp.readlines():
                if line.startswith('/NumWaves'):
                    numpes = int(line.split()[-1])
                    files = []
                    for i in range(numpes):
                        files.append(
                            self._gen_fname('pe%d.nii' % (i + 1), cwd=cwd))
                    break
            fp.close()
        return files

    def _get_numcons(self):
        numtcons = 0
        numfcons = 0
        if isdefined(self.inputs.tcon_file):
            fp = open(self.inputs.tcon_file, 'rt')
            for line in fp.readlines():
                if line.startswith('/NumContrasts'):
                    numtcons = int(line.split()[-1])
                    break
            fp.close()
        if isdefined(self.inputs.fcon_file):
            fp = open(self.inputs.fcon_file, 'rt')
            for line in fp.readlines():
                if line.startswith('/NumContrasts'):
                    numfcons = int(line.split()[-1])
                    break
            fp.close()
        return numtcons, numfcons

    def _list_outputs(self):
        outputs = self._outputs().get()
        cwd = os.getcwd()
        results_dir = os.path.join(cwd, self.inputs.results_dir)
        outputs['results_dir'] = results_dir
        pe_files = self._get_pe_files(results_dir)
        if pe_files:
            outputs['param_estimates'] = pe_files
        outputs['residual4d'] = self._gen_fname('res4d.nii', cwd=results_dir)
        outputs['dof_file'] = os.path.join(results_dir, 'dof')
        outputs['sigmasquareds'] = self._gen_fname(
            'sigmasquareds.nii', cwd=results_dir)
        outputs['thresholdac'] = self._gen_fname(
            'threshac1.nii', cwd=results_dir)
        if (Info.version()
                and LooseVersion(Info.version()) < LooseVersion('5.0.7')):
            outputs['corrections'] = self._gen_fname(
                'corrections.nii', cwd=results_dir)
        outputs['logfile'] = self._gen_fname(
            'logfile', change_ext=False, cwd=results_dir)

        if (Info.version()
                and LooseVersion(Info.version()) > LooseVersion('5.0.6')):
            pth = results_dir
            numtcons, numfcons = self._get_numcons()
            base_contrast = 1
            copes = []
            varcopes = []
            zstats = []
            tstats = []
            for i in range(numtcons):
                copes.append(
                    self._gen_fname(
                        'cope%d.nii' % (base_contrast + i), cwd=pth))
                varcopes.append(
                    self._gen_fname(
                        'varcope%d.nii' % (base_contrast + i), cwd=pth))
                zstats.append(
                    self._gen_fname(
                        'zstat%d.nii' % (base_contrast + i), cwd=pth))
                tstats.append(
                    self._gen_fname(
                        'tstat%d.nii' % (base_contrast + i), cwd=pth))
            if copes:
                outputs['copes'] = copes
                outputs['varcopes'] = varcopes
                outputs['zstats'] = zstats
                outputs['tstats'] = tstats
            fstats = []
            zfstats = []
            for i in range(numfcons):
                fstats.append(
                    self._gen_fname(
                        'fstat%d.nii' % (base_contrast + i), cwd=pth))
                zfstats.append(
                    self._gen_fname(
                        'zfstat%d.nii' % (base_contrast + i), cwd=pth))
            if fstats:
                outputs['fstats'] = fstats
                outputs['zfstats'] = zfstats
        return outputs


class FEATRegisterInputSpec(BaseInterfaceInputSpec):
    feat_dirs = InputMultiPath(
        Directory(exists=True), desc="Lower level feat dirs", mandatory=True)
    reg_image = File(
        exists=True,
        desc="image to register to (will be treated as standard)",
        mandatory=True)
    reg_dof = traits.Int(
        12, desc="registration degrees of freedom", usedefault=True)


class FEATRegisterOutputSpec(TraitedSpec):
    fsf_file = File(exists=True, desc="FSL feat specification file")


class FEATRegister(BaseInterface):
    """Register feat directories to a specific standard
    """
    input_spec = FEATRegisterInputSpec
    output_spec = FEATRegisterOutputSpec

    def _run_interface(self, runtime):
        fsf_header = load_template('featreg_header.tcl')
        fsf_footer = load_template('feat_nongui.tcl')
        fsf_dirs = load_template('feat_fe_featdirs.tcl')

        num_runs = len(self.inputs.feat_dirs)
        fsf_txt = fsf_header.substitute(
            num_runs=num_runs,
            regimage=self.inputs.reg_image,
            regdof=self.inputs.reg_dof)
        for i, rundir in enumerate(filename_to_list(self.inputs.feat_dirs)):
            fsf_txt += fsf_dirs.substitute(
                runno=i + 1, rundir=os.path.abspath(rundir))
        fsf_txt += fsf_footer.substitute()
        f = open(os.path.join(os.getcwd(), 'register.fsf'), 'wt')
        f.write(fsf_txt)
        f.close()

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['fsf_file'] = os.path.abspath(
            os.path.join(os.getcwd(), 'register.fsf'))
        return outputs


class FLAMEOInputSpec(FSLCommandInputSpec):
    cope_file = File(
        exists=True,
        argstr='--copefile=%s',
        mandatory=True,
        desc='cope regressor data file')
    var_cope_file = File(
        exists=True,
        argstr='--varcopefile=%s',
        desc='varcope weightings data file')
    dof_var_cope_file = File(
        exists=True,
        argstr='--dofvarcopefile=%s',
        desc='dof data file for varcope data')
    mask_file = File(
        exists=True, argstr='--maskfile=%s', mandatory=True, desc='mask file')
    design_file = File(
        exists=True,
        argstr='--designfile=%s',
        mandatory=True,
        desc='design matrix file')
    t_con_file = File(
        exists=True,
        argstr='--tcontrastsfile=%s',
        mandatory=True,
        desc='ascii matrix specifying t-contrasts')
    f_con_file = File(
        exists=True,
        argstr='--fcontrastsfile=%s',
        desc='ascii matrix specifying f-contrasts')
    cov_split_file = File(
        exists=True,
        argstr='--covsplitfile=%s',
        mandatory=True,
        desc='ascii matrix specifying the groups the covariance is split into')
    run_mode = traits.Enum(
        'fe',
        'ols',
        'flame1',
        'flame12',
        argstr='--runmode=%s',
        mandatory=True,
        desc='inference to perform')
    n_jumps = traits.Int(
        argstr='--njumps=%d', desc='number of jumps made by mcmc')
    burnin = traits.Int(
        argstr='--burnin=%d',
        desc=('number of jumps at start of mcmc to be '
              'discarded'))
    sample_every = traits.Int(
        argstr='--sampleevery=%d', desc='number of jumps for each sample')
    fix_mean = traits.Bool(argstr='--fixmean', desc='fix mean for tfit')
    infer_outliers = traits.Bool(
        argstr='--inferoutliers', desc='infer outliers - not for fe')
    no_pe_outputs = traits.Bool(
        argstr='--nopeoutput', desc='do not output pe files')
    sigma_dofs = traits.Int(
        argstr='--sigma_dofs=%d',
        desc=('sigma (in mm) to use for Gaussian '
              'smoothing the DOFs in FLAME 2. Default is '
              '1mm, -1 indicates no smoothing'))
    outlier_iter = traits.Int(
        argstr='--ioni=%d',
        desc=('Number of max iterations to use when '
              'inferring outliers. Default is 12.'))
    log_dir = Directory("stats", argstr='--ld=%s', usedefault=True)  # ohinds
    # no support for ven, vef


class FLAMEOOutputSpec(TraitedSpec):
    pes = OutputMultiPath(
        File(exists=True),
        desc=("Parameter estimates for each column of the "
              "design matrix for each voxel"))
    res4d = OutputMultiPath(
        File(exists=True),
        desc=("Model fit residual mean-squared error for "
              "each time point"))
    copes = OutputMultiPath(
        File(exists=True), desc="Contrast estimates for each contrast")
    var_copes = OutputMultiPath(
        File(exists=True), desc="Variance estimates for each contrast")
    zstats = OutputMultiPath(
        File(exists=True), desc="z-stat file for each contrast")
    tstats = OutputMultiPath(
        File(exists=True), desc="t-stat file for each contrast")
    zfstats = OutputMultiPath(
        File(exists=True), desc="z stat file for each f contrast")
    fstats = OutputMultiPath(
        File(exists=True), desc="f-stat file for each contrast")
    mrefvars = OutputMultiPath(
        File(exists=True),
        desc=("mean random effect variances for each "
              "contrast"))
    tdof = OutputMultiPath(
        File(exists=True), desc="temporal dof file for each contrast")
    weights = OutputMultiPath(
        File(exists=True), desc="weights file for each contrast")
    stats_dir = Directory(
        File(exists=True), desc="directory storing model estimation output")


class FLAMEO(FSLCommand):
    """Use FSL flameo command to perform higher level model fits

    Examples
    --------

    Initialize FLAMEO with no options, assigning them when calling run:

    >>> from nipype.interfaces import fsl
    >>> flameo = fsl.FLAMEO()
    >>> flameo.inputs.cope_file = 'cope.nii.gz'
    >>> flameo.inputs.var_cope_file = 'varcope.nii.gz'
    >>> flameo.inputs.cov_split_file = 'cov_split.mat'
    >>> flameo.inputs.design_file = 'design.mat'
    >>> flameo.inputs.t_con_file = 'design.con'
    >>> flameo.inputs.mask_file = 'mask.nii'
    >>> flameo.inputs.run_mode = 'fe'
    >>> flameo.cmdline
    'flameo --copefile=cope.nii.gz --covsplitfile=cov_split.mat --designfile=design.mat --ld=stats --maskfile=mask.nii --runmode=fe --tcontrastsfile=design.con --varcopefile=varcope.nii.gz'

    """

    _cmd = 'flameo'
    input_spec = FLAMEOInputSpec
    output_spec = FLAMEOOutputSpec

    references_ = [{
        'entry':
        BibTeX(
            '@article{BeckmannJenkinsonSmith2003,'
            'author={C.F. Beckmann, M. Jenkinson, and S.M. Smith},'
            'title={General multilevel linear modeling for group analysis in FMRI.},'
            'journal={NeuroImage},'
            'volume={20},'
            'pages={1052-1063},'
            'year={2003},'
            '}'),
        'tags': ['method'],
    }, {
        'entry':
        BibTeX(
            '@article{WoolrichBehrensBeckmannJenkinsonSmith2004,'
            'author={M.W. Woolrich, T.E. Behrens, '
            'C.F. Beckmann, M. Jenkinson, and S.M. Smith},'
            'title={Multilevel linear modelling for FMRI group analysis using Bayesian inference.},'
            'journal={NeuroImage},'
            'volume={21},'
            'pages={1732-1747},'
            'year={2004},'
            '}'),
        'tags': ['method'],
    }]

    # ohinds: 2010-04-06
    def _run_interface(self, runtime):
        log_dir = self.inputs.log_dir
        cwd = os.getcwd()
        if os.access(os.path.join(cwd, log_dir), os.F_OK):
            rmtree(os.path.join(cwd, log_dir))

        return super(FLAMEO, self)._run_interface(runtime)

    # ohinds: 2010-04-06
    # made these compatible with flameo
    def _list_outputs(self):
        outputs = self._outputs().get()
        pth = os.path.join(os.getcwd(), self.inputs.log_dir)

        pes = human_order_sorted(glob(os.path.join(pth, 'pe[0-9]*.*')))
        assert len(pes) >= 1, 'No pe volumes generated by FSL Estimate'
        outputs['pes'] = pes

        res4d = human_order_sorted(glob(os.path.join(pth, 'res4d.*')))
        assert len(res4d) == 1, 'No residual volume generated by FSL Estimate'
        outputs['res4d'] = res4d[0]

        copes = human_order_sorted(glob(os.path.join(pth, 'cope[0-9]*.*')))
        assert len(copes) >= 1, 'No cope volumes generated by FSL CEstimate'
        outputs['copes'] = copes

        var_copes = human_order_sorted(
            glob(os.path.join(pth, 'varcope[0-9]*.*')))
        assert len(
            var_copes) >= 1, 'No varcope volumes generated by FSL CEstimate'
        outputs['var_copes'] = var_copes

        zstats = human_order_sorted(glob(os.path.join(pth, 'zstat[0-9]*.*')))
        assert len(zstats) >= 1, 'No zstat volumes generated by FSL CEstimate'
        outputs['zstats'] = zstats

        if isdefined(self.inputs.f_con_file):
            zfstats = human_order_sorted(
                glob(os.path.join(pth, 'zfstat[0-9]*.*')))
            assert len(
                zfstats) >= 1, 'No zfstat volumes generated by FSL CEstimate'
            outputs['zfstats'] = zfstats

            fstats = human_order_sorted(
                glob(os.path.join(pth, 'fstat[0-9]*.*')))
            assert len(
                fstats) >= 1, 'No fstat volumes generated by FSL CEstimate'
            outputs['fstats'] = fstats

        tstats = human_order_sorted(glob(os.path.join(pth, 'tstat[0-9]*.*')))
        assert len(tstats) >= 1, 'No tstat volumes generated by FSL CEstimate'
        outputs['tstats'] = tstats

        mrefs = human_order_sorted(
            glob(os.path.join(pth, 'mean_random_effects_var[0-9]*.*')))
        assert len(
            mrefs) >= 1, 'No mean random effects volumes generated by FLAMEO'
        outputs['mrefvars'] = mrefs

        tdof = human_order_sorted(glob(os.path.join(pth, 'tdof_t[0-9]*.*')))
        assert len(tdof) >= 1, 'No T dof volumes generated by FLAMEO'
        outputs['tdof'] = tdof

        weights = human_order_sorted(
            glob(os.path.join(pth, 'weights[0-9]*.*')))
        assert len(weights) >= 1, 'No weight volumes generated by FLAMEO'
        outputs['weights'] = weights

        outputs['stats_dir'] = pth

        return outputs


class ContrastMgrInputSpec(FSLCommandInputSpec):
    tcon_file = File(
        exists=True,
        mandatory=True,
        argstr='%s',
        position=-1,
        desc='contrast file containing T-contrasts')
    fcon_file = File(
        exists=True,
        argstr='-f %s',
        desc='contrast file containing F-contrasts')
    param_estimates = InputMultiPath(
        File(exists=True),
        argstr='',
        copyfile=False,
        mandatory=True,
        desc=('Parameter estimates for each '
              'column of the design matrix'))
    corrections = File(
        exists=True,
        copyfile=False,
        mandatory=True,
        desc='statistical corrections used within FILM modelling')
    dof_file = File(
        exists=True,
        argstr='',
        copyfile=False,
        mandatory=True,
        desc='degrees of freedom')
    sigmasquareds = File(
        exists=True,
        argstr='',
        position=-2,
        copyfile=False,
        mandatory=True,
        desc=('summary of residuals, See Woolrich, et. al., '
              '2001'))
    contrast_num = traits.Range(
        low=1,
        argstr='-cope',
        desc=('contrast number to start labeling '
              'copes from'))
    suffix = traits.Str(
        argstr='-suffix %s',
        desc=('suffix to put on the end of the cope filename '
              'before the contrast number, default is '
              'nothing'))


class ContrastMgrOutputSpec(TraitedSpec):
    copes = OutputMultiPath(
        File(exists=True), desc='Contrast estimates for each contrast')
    varcopes = OutputMultiPath(
        File(exists=True), desc='Variance estimates for each contrast')
    zstats = OutputMultiPath(
        File(exists=True), desc='z-stat file for each contrast')
    tstats = OutputMultiPath(
        File(exists=True), desc='t-stat file for each contrast')
    fstats = OutputMultiPath(
        File(exists=True), desc='f-stat file for each contrast')
    zfstats = OutputMultiPath(
        File(exists=True), desc='z-stat file for each F contrast')
    neffs = OutputMultiPath(
        File(exists=True), desc='neff file ?? for each contrast')


class ContrastMgr(FSLCommand):
    """Use FSL contrast_mgr command to evaluate contrasts

    In interface mode this file assumes that all the required inputs are in the
    same location. This has deprecated for FSL versions 5.0.7+ as the necessary
    corrections file is no longer generated by FILMGLS.
    """
    if Info.version() and LooseVersion(
            Info.version()) >= LooseVersion("5.0.7"):
        DeprecationWarning("ContrastMgr is deprecated in FSL 5.0.7+")
    _cmd = 'contrast_mgr'
    input_spec = ContrastMgrInputSpec
    output_spec = ContrastMgrOutputSpec

    def _run_interface(self, runtime):
        # The returncode is meaningless in ContrastMgr.  So check the output
        # in stderr and if it's set, then update the returncode
        # accordingly.
        runtime = super(ContrastMgr, self)._run_interface(runtime)
        if runtime.stderr:
            self.raise_exception(runtime)
        return runtime

    def _format_arg(self, name, trait_spec, value):
        if name in ['param_estimates', 'corrections', 'dof_file']:
            return ''
        elif name in ['sigmasquareds']:
            path, _ = os.path.split(value)
            return path
        else:
            return super(ContrastMgr, self)._format_arg(
                name, trait_spec, value)

    def _get_design_root(self, infile):
        _, fname = os.path.split(infile)
        return fname.split('.')[0]

    def _get_numcons(self):
        numtcons = 0
        numfcons = 0
        if isdefined(self.inputs.tcon_file):
            fp = open(self.inputs.tcon_file, 'rt')
            for line in fp.readlines():
                if line.startswith('/NumContrasts'):
                    numtcons = int(line.split()[-1])
                    break
            fp.close()
        if isdefined(self.inputs.fcon_file):
            fp = open(self.inputs.fcon_file, 'rt')
            for line in fp.readlines():
                if line.startswith('/NumContrasts'):
                    numfcons = int(line.split()[-1])
                    break
            fp.close()
        return numtcons, numfcons

    def _list_outputs(self):
        outputs = self._outputs().get()
        pth, _ = os.path.split(self.inputs.sigmasquareds)
        numtcons, numfcons = self._get_numcons()
        base_contrast = 1
        if isdefined(self.inputs.contrast_num):
            base_contrast = self.inputs.contrast_num
        copes = []
        varcopes = []
        zstats = []
        tstats = []
        neffs = []
        for i in range(numtcons):
            copes.append(
                self._gen_fname('cope%d.nii' % (base_contrast + i), cwd=pth))
            varcopes.append(
                self._gen_fname(
                    'varcope%d.nii' % (base_contrast + i), cwd=pth))
            zstats.append(
                self._gen_fname('zstat%d.nii' % (base_contrast + i), cwd=pth))
            tstats.append(
                self._gen_fname('tstat%d.nii' % (base_contrast + i), cwd=pth))
            neffs.append(
                self._gen_fname('neff%d.nii' % (base_contrast + i), cwd=pth))
        if copes:
            outputs['copes'] = copes
            outputs['varcopes'] = varcopes
            outputs['zstats'] = zstats
            outputs['tstats'] = tstats
            outputs['neffs'] = neffs
        fstats = []
        zfstats = []
        for i in range(numfcons):
            fstats.append(
                self._gen_fname('fstat%d.nii' % (base_contrast + i), cwd=pth))
            zfstats.append(
                self._gen_fname('zfstat%d.nii' % (base_contrast + i), cwd=pth))
        if fstats:
            outputs['fstats'] = fstats
            outputs['zfstats'] = zfstats
        return outputs


class L2ModelInputSpec(BaseInterfaceInputSpec):
    num_copes = traits.Range(
        low=1, mandatory=True, desc='number of copes to be combined')


class L2ModelOutputSpec(TraitedSpec):
    design_mat = File(exists=True, desc='design matrix file')
    design_con = File(exists=True, desc='design contrast file')
    design_grp = File(exists=True, desc='design group file')


class L2Model(BaseInterface):
    """Generate subject specific second level model

    Examples
    --------

    >>> from nipype.interfaces.fsl import L2Model
    >>> model = L2Model(num_copes=3) # 3 sessions

    """

    input_spec = L2ModelInputSpec
    output_spec = L2ModelOutputSpec

    def _run_interface(self, runtime):
        cwd = os.getcwd()
        mat_txt = [
            '/NumWaves   1', '/NumPoints  {:d}'.format(self.inputs.num_copes),
            '/PPheights  1', '', '/Matrix'
        ]
        for i in range(self.inputs.num_copes):
            mat_txt += ['1']
        mat_txt = '\n'.join(mat_txt)

        con_txt = [
            '/ContrastName1  group mean',
            '/NumWaves   1',
            '/NumContrasts   1',
            '/PPheights  1',
            '/RequiredEffect     100',  # XX where does this
            # number come from
            '',
            '/Matrix',
            '1'
        ]
        con_txt = '\n'.join(con_txt)

        grp_txt = [
            '/NumWaves   1', '/NumPoints  {:d}'.format(self.inputs.num_copes),
            '', '/Matrix'
        ]
        for i in range(self.inputs.num_copes):
            grp_txt += ['1']
        grp_txt = '\n'.join(grp_txt)

        txt = {
            'design.mat': mat_txt,
            'design.con': con_txt,
            'design.grp': grp_txt
        }

        # write design files
        for i, name in enumerate(['design.mat', 'design.con', 'design.grp']):
            f = open(os.path.join(cwd, name), 'wt')
            f.write(txt[name])
            f.close()

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        for field in list(outputs.keys()):
            outputs[field] = os.path.join(os.getcwd(), field.replace('_', '.'))
        return outputs


class MultipleRegressDesignInputSpec(BaseInterfaceInputSpec):
    contrasts = traits.List(
        traits.Either(
            traits.Tuple(traits.Str, traits.Enum('T'), traits.List(traits.Str),
                         traits.List(traits.Float)),
            traits.Tuple(traits.Str, traits.Enum('F'),
                         traits.List(
                             traits.Tuple(traits.Str, traits.Enum('T'),
                                          traits.List(traits.Str),
                                          traits.List(traits.Float)), ))),
        mandatory=True,
        desc="List of contrasts with each contrast being a list of the form - \
[('name', 'stat', [condition list], [weight list])]. if \
session list is None or not provided, all sessions are used. For F \
contrasts, the condition list should contain previously defined \
T-contrasts without any weight list.")
    regressors = traits.Dict(
        traits.Str,
        traits.List(traits.Float),
        mandatory=True,
        desc=('dictionary containing named lists of '
              'regressors'))
    groups = traits.List(
        traits.Int,
        desc=('list of group identifiers (defaults to single '
              'group)'))


class MultipleRegressDesignOutputSpec(TraitedSpec):
    design_mat = File(exists=True, desc='design matrix file')
    design_con = File(exists=True, desc='design t-contrast file')
    design_fts = File(exists=True, desc='design f-contrast file')
    design_grp = File(exists=True, desc='design group file')


class MultipleRegressDesign(BaseInterface):
    """Generate multiple regression design

    .. note::
      FSL does not demean columns for higher level analysis.

    Please see `FSL documentation
    <http://www.fmrib.ox.ac.uk/fsl/feat5/detail.html#higher>`_
    for more details on model specification for higher level analysis.

    Examples
    --------

    >>> from nipype.interfaces.fsl import MultipleRegressDesign
    >>> model = MultipleRegressDesign()
    >>> model.inputs.contrasts = [['group mean', 'T',['reg1'],[1]]]
    >>> model.inputs.regressors = dict(reg1=[1, 1, 1], reg2=[2.,-4, 3])
    >>> model.run() # doctest: +SKIP

    """

    input_spec = MultipleRegressDesignInputSpec
    output_spec = MultipleRegressDesignOutputSpec

    def _run_interface(self, runtime):
        cwd = os.getcwd()
        regs = sorted(self.inputs.regressors.keys())
        nwaves = len(regs)
        npoints = len(self.inputs.regressors[regs[0]])
        ntcons = sum([1 for con in self.inputs.contrasts if con[1] == 'T'])
        nfcons = sum([1 for con in self.inputs.contrasts if con[1] == 'F'])
        # write mat file
        mat_txt = [
            '/NumWaves       %d' % nwaves,
            '/NumPoints      %d' % npoints
        ]
        ppheights = []
        for reg in regs:
            maxreg = np.max(self.inputs.regressors[reg])
            minreg = np.min(self.inputs.regressors[reg])
            if np.sign(maxreg) == np.sign(minreg):
                regheight = max([abs(minreg), abs(maxreg)])
            else:
                regheight = abs(maxreg - minreg)
            ppheights.append('%e' % regheight)
        mat_txt += ['/PPheights      ' + ' '.join(ppheights)]
        mat_txt += ['', '/Matrix']
        for cidx in range(npoints):
            mat_txt.append(' '.join(
                ['%e' % self.inputs.regressors[key][cidx] for key in regs]))
        mat_txt = '\n'.join(mat_txt) + '\n'
        # write t-con file
        con_txt = []
        counter = 0
        tconmap = {}
        for conidx, con in enumerate(self.inputs.contrasts):
            if con[1] == 'T':
                tconmap[conidx] = counter
                counter += 1
                con_txt += ['/ContrastName%d   %s' % (counter, con[0])]
        con_txt += [
            '/NumWaves       %d' % nwaves,
            '/NumContrasts   %d' % ntcons,
            '/PPheights          %s' % ' '.join(
                ['%e' % 1 for i in range(counter)]),
            '/RequiredEffect     %s' % ' '.join(
                ['%.3f' % 100 for i in range(counter)]), '', '/Matrix'
        ]
        for idx in sorted(tconmap.keys()):
            convals = np.zeros((nwaves, 1))
            for regidx, reg in enumerate(self.inputs.contrasts[idx][2]):
                convals[regs.index(reg)] = self.inputs.contrasts[idx][3][
                    regidx]
            con_txt.append(' '.join(['%e' % val for val in convals]))
        con_txt = '\n'.join(con_txt) + '\n'
        # write f-con file
        fcon_txt = ''
        if nfcons:
            fcon_txt = [
                '/NumWaves       %d' % ntcons,
                '/NumContrasts   %d' % nfcons, '', '/Matrix'
            ]
            for conidx, con in enumerate(self.inputs.contrasts):
                if con[1] == 'F':
                    convals = np.zeros((ntcons, 1))
                    for tcon in con[2]:
                        convals[tconmap[self.inputs.contrasts.index(tcon)]] = 1
                    fcon_txt.append(' '.join(['%d' % val for val in convals]))
                    fcon_txt = '\n'.join(fcon_txt)
            fcon_txt += '\n'
        # write group file
        grp_txt = [
            '/NumWaves       1',
            '/NumPoints      %d' % npoints, '', '/Matrix'
        ]
        for i in range(npoints):
            if isdefined(self.inputs.groups):
                grp_txt += ['%d' % self.inputs.groups[i]]
            else:
                grp_txt += ['1']
        grp_txt = '\n'.join(grp_txt) + '\n'

        txt = {
            'design.mat': mat_txt,
            'design.con': con_txt,
            'design.fts': fcon_txt,
            'design.grp': grp_txt
        }

        # write design files
        for key, val in list(txt.items()):
            if ('fts' in key) and (nfcons == 0):
                continue
            filename = key.replace('_', '.')
            f = open(os.path.join(cwd, filename), 'wt')
            f.write(val)
            f.close()

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        nfcons = sum([1 for con in self.inputs.contrasts if con[1] == 'F'])
        for field in list(outputs.keys()):
            if ('fts' in field) and (nfcons == 0):
                continue
            outputs[field] = os.path.join(os.getcwd(), field.replace('_', '.'))
        return outputs


class SMMInputSpec(FSLCommandInputSpec):
    spatial_data_file = File(
        exists=True,
        position=0,
        argstr='--sdf="%s"',
        mandatory=True,
        desc="statistics spatial map",
        copyfile=False)
    mask = File(
        exists=True,
        position=1,
        argstr='--mask="%s"',
        mandatory=True,
        desc="mask file",
        copyfile=False)
    no_deactivation_class = traits.Bool(
        position=2,
        argstr="--zfstatmode",
        desc="enforces no deactivation class")


class SMMOutputSpec(TraitedSpec):
    null_p_map = File(exists=True)
    activation_p_map = File(exists=True)
    deactivation_p_map = File(exists=True)


class SMM(FSLCommand):
    '''
    Spatial Mixture Modelling. For more detail on the spatial mixture modelling
    see Mixture Models with Adaptive Spatial Regularisation for Segmentation
    with an Application to FMRI Data; Woolrich, M., Behrens, T., Beckmann, C.,
    and Smith, S.; IEEE Trans. Medical Imaging, 24(1):1-11, 2005.
    '''
    _cmd = 'mm --ld=logdir'
    input_spec = SMMInputSpec
    output_spec = SMMOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        # TODO get the true logdir from the stdout
        outputs['null_p_map'] = self._gen_fname(
            basename="w1_mean", cwd="logdir")
        outputs['activation_p_map'] = self._gen_fname(
            basename="w2_mean", cwd="logdir")
        if (not isdefined(self.inputs.no_deactivation_class)
                or not self.inputs.no_deactivation_class):
            outputs['deactivation_p_map'] = self._gen_fname(
                basename="w3_mean", cwd="logdir")
        return outputs


class MELODICInputSpec(FSLCommandInputSpec):
    in_files = InputMultiPath(
        File(exists=True),
        argstr="-i %s",
        mandatory=True,
        position=0,
        desc="input file names (either single file name or a list)",
        sep=",")
    out_dir = Directory(
        argstr="-o %s", desc="output directory name", genfile=True)
    mask = File(
        exists=True, argstr="-m %s", desc="file name of mask for thresholding")
    no_mask = traits.Bool(argstr="--nomask", desc="switch off masking")
    update_mask = traits.Bool(
        argstr="--update_mask", desc="switch off mask updating")
    no_bet = traits.Bool(argstr="--nobet", desc="switch off BET")
    bg_threshold = traits.Float(
        argstr="--bgthreshold=%f",
        desc=("brain/non-brain threshold used to mask non-brain voxels, as a "
              "percentage (only if --nobet selected)"))
    dim = traits.Int(
        argstr="-d %d",
        desc=("dimensionality reduction into #num dimensions (default: "
              "automatic estimation)"))
    dim_est = traits.Str(
        argstr="--dimest=%s",
        desc=("use specific dim. estimation technique: lap, "
              "bic, mdl, aic, mean (default: lap)"))
    sep_whiten = traits.Bool(
        argstr="--sep_whiten", desc="switch on separate whitening")
    sep_vn = traits.Bool(
        argstr="--sep_vn", desc="switch off joined variance normalization")
    migp = traits.Bool(argstr="--migp", desc="switch on MIGP data reduction")
    migpN = traits.Int(
        argstr="--migpN %d", desc="number of internal Eigenmaps")
    migp_shuffle = traits.Bool(
        argstr="--migp_shuffle",
        desc="randomise MIGP file order (default: TRUE)")
    migp_factor = traits.Int(
        argstr="--migp_factor %d",
        desc=
        "Internal Factor of mem-threshold relative to number of Eigenmaps (default: 2)"
    )
    num_ICs = traits.Int(
        argstr="-n %d",
        desc="number of IC's to extract (for deflation approach)")
    approach = traits.Str(
        argstr="-a %s",
        desc="approach for decomposition, 2D: defl, symm (default), 3D: tica "
        "(default), concat")
    non_linearity = traits.Str(
        argstr="--nl=%s", desc="nonlinearity: gauss, tanh, pow3, pow4")
    var_norm = traits.Bool(
        argstr="--vn", desc="switch off variance normalization")
    pbsc = traits.Bool(
        argstr="--pbsc",
        desc="switch off conversion to percent BOLD signal change")
    cov_weight = traits.Float(
        argstr="--covarweight=%f",
        desc=("voxel-wise weights for the covariance matrix (e.g. "
              "segmentation information)"))
    epsilon = traits.Float(argstr="--eps=%f", desc="minimum error change")
    epsilonS = traits.Float(
        argstr="--epsS=%f",
        desc="minimum error change for rank-1 approximation in TICA")
    maxit = traits.Int(
        argstr="--maxit=%d",
        desc="maximum number of iterations before restart")
    max_restart = traits.Int(
        argstr="--maxrestart=%d", desc="maximum number of restarts")
    mm_thresh = traits.Float(
        argstr="--mmthresh=%f",
        desc="threshold for Mixture Model based inference")
    no_mm = traits.Bool(
        argstr="--no_mm", desc="switch off mixture modelling on IC maps")
    ICs = File(
        exists=True,
        argstr="--ICs=%s",
        desc="filename of the IC components file for mixture modelling")
    mix = File(
        exists=True,
        argstr="--mix=%s",
        desc="mixing matrix for mixture modelling / filtering")
    smode = File(
        exists=True,
        argstr="--smode=%s",
        desc="matrix of session modes for report generation")
    rem_cmp = traits.List(
        traits.Int, argstr="-f %d", desc="component numbers to remove")
    report = traits.Bool(argstr="--report", desc="generate Melodic web report")
    bg_image = File(
        exists=True,
        argstr="--bgimage=%s",
        desc="specify background image for report (default: mean image)")
    tr_sec = traits.Float(argstr="--tr=%f", desc="TR in seconds")
    log_power = traits.Bool(
        argstr="--logPower",
        desc="calculate log of power for frequency spectrum")
    t_des = File(
        exists=True,
        argstr="--Tdes=%s",
        desc="design matrix across time-domain")
    t_con = File(
        exists=True,
        argstr="--Tcon=%s",
        desc="t-contrast matrix across time-domain")
    s_des = File(
        exists=True,
        argstr="--Sdes=%s",
        desc="design matrix across subject-domain")
    s_con = File(
        exists=True,
        argstr="--Scon=%s",
        desc="t-contrast matrix across subject-domain")
    out_all = traits.Bool(argstr="--Oall", desc="output everything")
    out_unmix = traits.Bool(argstr="--Ounmix", desc="output unmixing matrix")
    out_stats = traits.Bool(
        argstr="--Ostats", desc="output thresholded maps and probability maps")
    out_pca = traits.Bool(argstr="--Opca", desc="output PCA results")
    out_white = traits.Bool(
        argstr="--Owhite", desc="output whitening/dewhitening matrices")
    out_orig = traits.Bool(argstr="--Oorig", desc="output the original ICs")
    out_mean = traits.Bool(argstr="--Omean", desc="output mean volume")
    report_maps = traits.Str(
        argstr="--report_maps=%s",
        desc="control string for spatial map images (see slicer)")
    remove_deriv = traits.Bool(
        argstr="--remove_deriv",
        desc="removes every second entry in paradigm file (EV derivatives)")


class MELODICOutputSpec(TraitedSpec):
    out_dir = Directory(exists=True)
    report_dir = Directory(exists=True)


class MELODIC(FSLCommand):
    """Multivariate Exploratory Linear Optimised Decomposition into Independent
    Components

    Examples
    --------

    >>> melodic_setup = MELODIC()
    >>> melodic_setup.inputs.approach = 'tica'
    >>> melodic_setup.inputs.in_files = ['functional.nii', 'functional2.nii', 'functional3.nii']
    >>> melodic_setup.inputs.no_bet = True
    >>> melodic_setup.inputs.bg_threshold = 10
    >>> melodic_setup.inputs.tr_sec = 1.5
    >>> melodic_setup.inputs.mm_thresh = 0.5
    >>> melodic_setup.inputs.out_stats = True
    >>> melodic_setup.inputs.t_des = 'timeDesign.mat'
    >>> melodic_setup.inputs.t_con = 'timeDesign.con'
    >>> melodic_setup.inputs.s_des = 'subjectDesign.mat'
    >>> melodic_setup.inputs.s_con = 'subjectDesign.con'
    >>> melodic_setup.inputs.out_dir = 'groupICA.out'
    >>> melodic_setup.cmdline
    'melodic -i functional.nii,functional2.nii,functional3.nii -a tica --bgthreshold=10.000000 --mmthresh=0.500000 --nobet -o groupICA.out --Ostats --Scon=subjectDesign.con --Sdes=subjectDesign.mat --Tcon=timeDesign.con --Tdes=timeDesign.mat --tr=1.500000'
    >>> melodic_setup.run() # doctest: +SKIP


    """
    input_spec = MELODICInputSpec
    output_spec = MELODICOutputSpec
    _cmd = 'melodic'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_dir):
            outputs['out_dir'] = os.path.abspath(self.inputs.out_dir)
        else:
            outputs['out_dir'] = self._gen_filename("out_dir")
        if isdefined(self.inputs.report) and self.inputs.report:
            outputs['report_dir'] = os.path.join(outputs['out_dir'], "report")
        return outputs

    def _gen_filename(self, name):
        if name == "out_dir":
            return os.getcwd()


class SmoothEstimateInputSpec(FSLCommandInputSpec):
    dof = traits.Int(
        argstr='--dof=%d',
        mandatory=True,
        xor=['zstat_file'],
        desc='number of degrees of freedom')
    mask_file = File(
        argstr='--mask=%s',
        exists=True,
        mandatory=True,
        desc='brain mask volume')
    residual_fit_file = File(
        argstr='--res=%s',
        exists=True,
        requires=['dof'],
        desc='residual-fit image file')
    zstat_file = File(
        argstr='--zstat=%s', exists=True, xor=['dof'], desc='zstat image file')


class SmoothEstimateOutputSpec(TraitedSpec):
    dlh = traits.Float(desc='smoothness estimate sqrt(det(Lambda))')
    volume = traits.Int(desc='number of voxels in mask')
    resels = traits.Float(desc='number of resels')


class SmoothEstimate(FSLCommand):
    """ Estimates the smoothness of an image

    Examples
    --------

    >>> est = SmoothEstimate()
    >>> est.inputs.zstat_file = 'zstat1.nii.gz'
    >>> est.inputs.mask_file = 'mask.nii'
    >>> est.cmdline
    'smoothest --mask=mask.nii --zstat=zstat1.nii.gz'

    """

    input_spec = SmoothEstimateInputSpec
    output_spec = SmoothEstimateOutputSpec
    _cmd = 'smoothest'

    def aggregate_outputs(self, runtime=None, needed_outputs=None):
        outputs = self._outputs()
        stdout = runtime.stdout.split('\n')
        outputs.dlh = float(stdout[0].split()[1])
        outputs.volume = int(stdout[1].split()[1])
        outputs.resels = float(stdout[2].split()[1])
        return outputs


class ClusterInputSpec(FSLCommandInputSpec):
    in_file = File(
        argstr='--in=%s', mandatory=True, exists=True, desc='input volume')
    threshold = traits.Float(
        argstr='--thresh=%.10f',
        mandatory=True,
        desc='threshold for input volume')
    out_index_file = traits.Either(
        traits.Bool,
        File,
        argstr='--oindex=%s',
        desc='output of cluster index (in size order)',
        hash_files=False)
    out_threshold_file = traits.Either(
        traits.Bool,
        File,
        argstr='--othresh=%s',
        desc='thresholded image',
        hash_files=False)
    out_localmax_txt_file = traits.Either(
        traits.Bool,
        File,
        argstr='--olmax=%s',
        desc='local maxima text file',
        hash_files=False)
    out_localmax_vol_file = traits.Either(
        traits.Bool,
        File,
        argstr='--olmaxim=%s',
        desc='output of local maxima volume',
        hash_files=False)
    out_size_file = traits.Either(
        traits.Bool,
        File,
        argstr='--osize=%s',
        desc='filename for output of size image',
        hash_files=False)
    out_max_file = traits.Either(
        traits.Bool,
        File,
        argstr='--omax=%s',
        desc='filename for output of max image',
        hash_files=False)
    out_mean_file = traits.Either(
        traits.Bool,
        File,
        argstr='--omean=%s',
        desc='filename for output of mean image',
        hash_files=False)
    out_pval_file = traits.Either(
        traits.Bool,
        File,
        argstr='--opvals=%s',
        desc='filename for image output of log pvals',
        hash_files=False)
    pthreshold = traits.Float(
        argstr='--pthresh=%.10f',
        requires=['dlh', 'volume'],
        desc='p-threshold for clusters')
    peak_distance = traits.Float(
        argstr='--peakdist=%.10f',
        desc='minimum distance between local maxima/minima, in mm (default 0)')
    cope_file = traits.File(argstr='--cope=%s', desc='cope volume')
    volume = traits.Int(
        argstr='--volume=%d', desc='number of voxels in the mask')
    dlh = traits.Float(
        argstr='--dlh=%.10f', desc='smoothness estimate = sqrt(det(Lambda))')
    fractional = traits.Bool(
        False,
        usedefault=True,
        argstr='--fractional',
        desc='interprets the threshold as a fraction of the robust range')
    connectivity = traits.Int(
        argstr='--connectivity=%d',
        desc='the connectivity of voxels (default 26)')
    use_mm = traits.Bool(
        False,
        usedefault=True,
        argstr='--mm',
        desc='use mm, not voxel, coordinates')
    find_min = traits.Bool(
        False,
        usedefault=True,
        argstr='--min',
        desc='find minima instead of maxima')
    no_table = traits.Bool(
        False,
        usedefault=True,
        argstr='--no_table',
        desc='suppresses printing of the table info')
    minclustersize = traits.Bool(
        False,
        usedefault=True,
        argstr='--minclustersize',
        desc='prints out minimum significant cluster size')
    xfm_file = File(
        argstr='--xfm=%s',
        desc=('filename for Linear: input->standard-space '
              'transform. Non-linear: input->highres transform'))
    std_space_file = File(
        argstr='--stdvol=%s', desc='filename for standard-space volume')
    num_maxima = traits.Int(
        argstr='--num=%d', desc='no of local maxima to report')
    warpfield_file = File(
        argstr='--warpvol=%s', desc='file contining warpfield')


class ClusterOutputSpec(TraitedSpec):
    index_file = File(desc='output of cluster index (in size order)')
    threshold_file = File(desc='thresholded image')
    localmax_txt_file = File(desc='local maxima text file')
    localmax_vol_file = File(desc='output of local maxima volume')
    size_file = File(desc='filename for output of size image')
    max_file = File(desc='filename for output of max image')
    mean_file = File(desc='filename for output of mean image')
    pval_file = File(desc='filename for image output of log pvals')


class Cluster(FSLCommand):
    """ Uses FSL cluster to perform clustering on statistical output

    Examples
    --------

    >>> cl = Cluster()
    >>> cl.inputs.threshold = 2.3
    >>> cl.inputs.in_file = 'zstat1.nii.gz'
    >>> cl.inputs.out_localmax_txt_file = 'stats.txt'
    >>> cl.inputs.use_mm = True
    >>> cl.cmdline
    'cluster --in=zstat1.nii.gz --olmax=stats.txt --thresh=2.3000000000 --mm'

    """
    input_spec = ClusterInputSpec
    output_spec = ClusterOutputSpec
    _cmd = 'cluster'

    filemap = {
        'out_index_file': 'index',
        'out_threshold_file': 'threshold',
        'out_localmax_txt_file': 'localmax.txt',
        'out_localmax_vol_file': 'localmax',
        'out_size_file': 'size',
        'out_max_file': 'max',
        'out_mean_file': 'mean',
        'out_pval_file': 'pval'
    }

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for key, suffix in list(self.filemap.items()):
            outkey = key[4:]
            inval = getattr(self.inputs, key)
            if isdefined(inval):
                if isinstance(inval, bool):
                    if inval:
                        change_ext = True
                        if suffix.endswith('.txt'):
                            change_ext = False
                        outputs[outkey] = self._gen_fname(
                            self.inputs.in_file,
                            suffix='_' + suffix,
                            change_ext=change_ext)
                else:
                    outputs[outkey] = os.path.abspath(inval)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in list(self.filemap.keys()):
            if isinstance(value, bool):
                fname = self._list_outputs()[name[4:]]
            else:
                fname = value
            return spec.argstr % fname
        return super(Cluster, self)._format_arg(name, spec, value)


class DualRegressionInputSpec(FSLCommandInputSpec):
    in_files = InputMultiPath(
        File(exists=True),
        argstr="%s",
        mandatory=True,
        position=-1,
        sep=" ",
        desc="List all subjects' preprocessed, standard-space 4D datasets",
    )
    group_IC_maps_4D = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=1,
        desc="4D image containing spatial IC maps (melodic_IC) from the "
        "whole-group ICA analysis")
    des_norm = traits.Bool(
        True,
        argstr="%i",
        position=2,
        usedefault=True,
        desc="Whether to variance-normalise the timecourses used as the "
        "stage-2 regressors; True is default and recommended")
    one_sample_group_mean = traits.Bool(
        argstr="-1",
        position=3,
        desc="perform 1-sample group-mean test instead of generic "
        "permutation test")
    design_file = File(
        exists=True,
        argstr="%s",
        position=3,
        desc="Design matrix for final cross-subject modelling with "
        "randomise")
    con_file = File(
        exists=True,
        argstr="%s",
        position=4,
        desc="Design contrasts for final cross-subject modelling with "
        "randomise")
    n_perm = traits.Int(
        argstr="%i",
        mandatory=True,
        position=5,
        desc="Number of permutations for randomise; set to 1 for just raw "
        "tstat output, set to 0 to not run randomise at all.")
    out_dir = Directory(
        "output",
        argstr="%s",
        usedefault=True,
        position=6,
        desc="This directory will be created to hold all output and logfiles",
        genfile=True)


class DualRegressionOutputSpec(TraitedSpec):
    out_dir = Directory(exists=True)


class DualRegression(FSLCommand):
    """Wrapper Script for Dual Regression Workflow

    Examples
    --------

    >>> dual_regression = DualRegression()
    >>> dual_regression.inputs.in_files = ["functional.nii", "functional2.nii", "functional3.nii"]
    >>> dual_regression.inputs.group_IC_maps_4D = "allFA.nii"
    >>> dual_regression.inputs.des_norm = False
    >>> dual_regression.inputs.one_sample_group_mean = True
    >>> dual_regression.inputs.n_perm = 10
    >>> dual_regression.inputs.out_dir = "my_output_directory"
    >>> dual_regression.cmdline
    'dual_regression allFA.nii 0 -1 10 my_output_directory functional.nii functional2.nii functional3.nii'
    >>> dual_regression.run() # doctest: +SKIP

    """
    input_spec = DualRegressionInputSpec
    output_spec = DualRegressionOutputSpec
    _cmd = 'dual_regression'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_dir):
            outputs['out_dir'] = os.path.abspath(self.inputs.out_dir)
        else:
            outputs['out_dir'] = self._gen_filename("out_dir")
        return outputs

    def _gen_filename(self, name):
        if name == "out_dir":
            return os.getcwd()


class RandomiseInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        desc='4D input file',
        argstr='-i %s',
        position=0,
        mandatory=True)
    base_name = traits.Str(
        'randomise',
        desc='the rootname that all generated files will have',
        argstr='-o "%s"',
        position=1,
        usedefault=True)
    design_mat = File(
        exists=True, desc='design matrix file', argstr='-d %s', position=2)
    tcon = File(
        exists=True, desc='t contrasts file', argstr='-t %s', position=3)
    fcon = File(exists=True, desc='f contrasts file', argstr='-f %s')
    mask = File(exists=True, desc='mask image', argstr='-m %s')
    x_block_labels = File(
        exists=True, desc='exchangeability block labels file', argstr='-e %s')
    demean = traits.Bool(
        desc='demean data temporally before model fitting', argstr='-D')
    one_sample_group_mean = traits.Bool(
        desc=('perform 1-sample group-mean test instead of generic '
              'permutation test'),
        argstr='-1')
    show_total_perms = traits.Bool(
        desc=('print out how many unique permutations would be generated '
              'and exit'),
        argstr='-q')
    show_info_parallel_mode = traits.Bool(
        desc='print out information required for parallel mode and exit',
        argstr='-Q')
    vox_p_values = traits.Bool(
        desc='output voxelwise (corrected and uncorrected) p-value images',
        argstr='-x')
    tfce = traits.Bool(
        desc='carry out Threshold-Free Cluster Enhancement', argstr='-T')
    tfce2D = traits.Bool(
        desc=('carry out Threshold-Free Cluster Enhancement with 2D '
              'optimisation'),
        argstr='--T2')
    f_only = traits.Bool(desc='calculate f-statistics only', argstr='--f_only')
    raw_stats_imgs = traits.Bool(
        desc='output raw ( unpermuted ) statistic images', argstr='-R')
    p_vec_n_dist_files = traits.Bool(
        desc='output permutation vector and null distribution text files',
        argstr='-P')
    num_perm = traits.Int(
        argstr='-n %d',
        desc='number of permutations (default 5000, set to 0 for exhaustive)')
    seed = traits.Int(
        argstr='--seed=%d',
        desc='specific integer seed for random number generator')
    var_smooth = traits.Int(
        argstr='-v %d', desc='use variance smoothing (std is in mm)')
    c_thresh = traits.Float(
        argstr='-c %.1f', desc='carry out cluster-based thresholding')
    cm_thresh = traits.Float(
        argstr='-C %.1f', desc='carry out cluster-mass-based thresholding')
    f_c_thresh = traits.Float(
        argstr='-F %.2f', desc='carry out f cluster thresholding')
    f_cm_thresh = traits.Float(
        argstr='-S %.2f', desc='carry out f cluster-mass thresholding')
    tfce_H = traits.Float(
        argstr='--tfce_H=%.2f', desc='TFCE height parameter (default=2)')
    tfce_E = traits.Float(
        argstr='--tfce_E=%.2f', desc='TFCE extent parameter (default=0.5)')
    tfce_C = traits.Float(
        argstr='--tfce_C=%.2f', desc='TFCE connectivity (6 or 26; default=6)')


class RandomiseOutputSpec(TraitedSpec):
    tstat_files = traits.List(
        File(exists=True), desc='t contrast raw statistic')
    fstat_files = traits.List(
        File(exists=True), desc='f contrast raw statistic')
    t_p_files = traits.List(
        File(exists=True), desc='f contrast uncorrected p values files')
    f_p_files = traits.List(
        File(exists=True), desc='f contrast uncorrected p values files')
    t_corrected_p_files = traits.List(
        File(exists=True),
        desc='t contrast FWE (Family-wise error) corrected p values files')
    f_corrected_p_files = traits.List(
        File(exists=True),
        desc='f contrast FWE (Family-wise error) corrected p values files')


class Randomise(FSLCommand):
    """FSL Randomise: feeds the 4D projected FA data into GLM
    modelling and thresholding
    in order to find voxels which correlate with your model

    Example
    -------
    >>> import nipype.interfaces.fsl as fsl
    >>> rand = fsl.Randomise(in_file='allFA.nii', mask = 'mask.nii', tcon='design.con', design_mat='design.mat')
    >>> rand.cmdline
    'randomise -i allFA.nii -o "randomise" -d design.mat -t design.con -m mask.nii'

    """

    _cmd = 'randomise'
    input_spec = RandomiseInputSpec
    output_spec = RandomiseOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['tstat_files'] = glob(
            self._gen_fname('%s_tstat*.nii' % self.inputs.base_name))
        outputs['fstat_files'] = glob(
            self._gen_fname('%s_fstat*.nii' % self.inputs.base_name))
        prefix = False
        if self.inputs.tfce or self.inputs.tfce2D:
            prefix = 'tfce'
        elif self.inputs.vox_p_values:
            prefix = 'vox'
        elif self.inputs.c_thresh or self.inputs.f_c_thresh:
            prefix = 'clustere'
        elif self.inputs.cm_thresh or self.inputs.f_cm_thresh:
            prefix = 'clusterm'
        if prefix:
            outputs['t_p_files'] = glob(
                self._gen_fname('%s_%s_p_tstat*' % (self.inputs.base_name,
                                                    prefix)))
            outputs['t_corrected_p_files'] = glob(
                self._gen_fname('%s_%s_corrp_tstat*.nii' %
                                (self.inputs.base_name, prefix)))

            outputs['f_p_files'] = glob(
                self._gen_fname('%s_%s_p_fstat*.nii' % (self.inputs.base_name,
                                                        prefix)))
            outputs['f_corrected_p_files'] = glob(
                self._gen_fname('%s_%s_corrp_fstat*.nii' %
                                (self.inputs.base_name, prefix)))
        return outputs


class GLMInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        argstr='-i %s',
        mandatory=True,
        position=1,
        desc='input file name (text matrix or 3D/4D image file)')
    out_file = File(
        name_template="%s_glm",
        argstr='-o %s',
        position=3,
        desc=('filename for GLM parameter estimates' + ' (GLM betas)'),
        name_source="in_file",
        keep_extension=True)
    design = File(
        exists=True,
        argstr='-d %s',
        mandatory=True,
        position=2,
        desc=('file name of the GLM design matrix (text time' +
              ' courses for temporal regression or an image' +
              ' file for spatial regression)'))
    contrasts = File(
        exists=True, argstr='-c %s', desc=('matrix of t-statics contrasts'))
    mask = File(
        exists=True,
        argstr='-m %s',
        desc=('mask image file name if input is image'))
    dof = traits.Int(
        argstr='--dof=%d', desc=('set degrees of freedom' + ' explicitly'))
    des_norm = traits.Bool(
        argstr='--des_norm',
        desc=('switch on normalization of the design' +
              ' matrix columns to unit std deviation'))
    dat_norm = traits.Bool(
        argstr='--dat_norm',
        desc=('switch on normalization of the data time series to unit std '
              'deviation'))
    var_norm = traits.Bool(
        argstr='--vn', desc=('perform MELODIC variance-normalisation on data'))
    demean = traits.Bool(
        argstr='--demean', desc=('switch on demeaining of design and data'))
    out_cope = File(
        argstr='--out_cope=%s',
        desc='output file name for COPE (either as txt or image')
    out_z_name = File(
        argstr='--out_z=%s',
        desc='output file name for Z-stats (either as txt or image')
    out_t_name = File(
        argstr='--out_t=%s',
        desc='output file name for t-stats (either as txt or image')
    out_p_name = File(
        argstr='--out_p=%s',
        desc=('output file name for p-values of Z-stats (either as text file '
              'or image)'))
    out_f_name = File(
        argstr='--out_f=%s',
        desc='output file name for F-value of full model fit')
    out_pf_name = File(
        argstr='--out_pf=%s',
        desc='output file name for p-value for full model fit')
    out_res_name = File(
        argstr='--out_res=%s', desc='output file name for residuals')
    out_varcb_name = File(
        argstr='--out_varcb=%s', desc='output file name for variance of COPEs')
    out_sigsq_name = File(
        argstr='--out_sigsq=%s',
        desc=('output file name for residual noise variance sigma-square'))
    out_data_name = File(
        argstr='--out_data=%s', desc='output file name for pre-processed data')
    out_vnscales_name = File(
        argstr='--out_vnscales=%s',
        desc=('output file name for scaling factors for variance '
              'normalisation'))


class GLMOutputSpec(TraitedSpec):
    out_file = File(
        exists=True, desc=('file name of GLM parameters (if generated)'))
    out_cope = OutputMultiPath(
        File(exists=True),
        desc=('output file name for COPEs (either as text file or image)'))
    out_z = OutputMultiPath(
        File(exists=True),
        desc=('output file name for COPEs (either as text file or image)'))
    out_t = OutputMultiPath(
        File(exists=True),
        desc=('output file name for t-stats (either as text file or image)'))
    out_p = OutputMultiPath(
        File(exists=True),
        desc=('output file name for p-values of Z-stats (either as text file '
              'or image)'))
    out_f = OutputMultiPath(
        File(exists=True),
        desc=('output file name for F-value of full model fit'))
    out_pf = OutputMultiPath(
        File(exists=True),
        desc=('output file name for p-value for full model fit'))
    out_res = OutputMultiPath(
        File(exists=True), desc='output file name for residuals')
    out_varcb = OutputMultiPath(
        File(exists=True), desc='output file name for variance of COPEs')
    out_sigsq = OutputMultiPath(
        File(exists=True),
        desc=('output file name for residual noise variance sigma-square'))
    out_data = OutputMultiPath(
        File(exists=True), desc='output file for preprocessed data')
    out_vnscales = OutputMultiPath(
        File(exists=True),
        desc=('output file name for scaling factors for variance '
              'normalisation'))


class GLM(FSLCommand):
    """
    FSL GLM:

    Example
    -------
    >>> import nipype.interfaces.fsl as fsl
    >>> glm = fsl.GLM(in_file='functional.nii', design='maps.nii', output_type='NIFTI')
    >>> glm.cmdline
    'fsl_glm -i functional.nii -d maps.nii -o functional_glm.nii'

    """
    _cmd = 'fsl_glm'
    input_spec = GLMInputSpec
    output_spec = GLMOutputSpec

    def _list_outputs(self):
        outputs = super(GLM, self)._list_outputs()

        if isdefined(self.inputs.out_cope):
            outputs['out_cope'] = os.path.abspath(self.inputs.out_cope)

        if isdefined(self.inputs.out_z_name):
            outputs['out_z'] = os.path.abspath(self.inputs.out_z_name)

        if isdefined(self.inputs.out_t_name):
            outputs['out_t'] = os.path.abspath(self.inputs.out_t_name)

        if isdefined(self.inputs.out_p_name):
            outputs['out_p'] = os.path.abspath(self.inputs.out_p_name)

        if isdefined(self.inputs.out_f_name):
            outputs['out_f'] = os.path.abspath(self.inputs.out_f_name)

        if isdefined(self.inputs.out_pf_name):
            outputs['out_pf'] = os.path.abspath(self.inputs.out_pf_name)

        if isdefined(self.inputs.out_res_name):
            outputs['out_res'] = os.path.abspath(self.inputs.out_res_name)

        if isdefined(self.inputs.out_varcb_name):
            outputs['out_varcb'] = os.path.abspath(self.inputs.out_varcb_name)

        if isdefined(self.inputs.out_sigsq_name):
            outputs['out_sigsq'] = os.path.abspath(self.inputs.out_sigsq_name)

        if isdefined(self.inputs.out_data_name):
            outputs['out_data'] = os.path.abspath(self.inputs.out_data_name)

        if isdefined(self.inputs.out_vnscales_name):
            outputs['out_vnscales'] = os.path.abspath(
                self.inputs.out_vnscales_name)

        return outputs


def load_template(name):
    """Load a template from the model_templates directory

    Parameters
    ----------
    name : str
        The name of the file to load

    Returns
    -------
    template : string.Template

    """
    from pkg_resources import resource_filename as pkgrf
    full_fname = pkgrf('nipype',
                       os.path.join('interfaces', 'fsl', 'model_templates',
                                    name))
    with open(full_fname) as template_file:
        template = Template(template_file.read())

    return template
