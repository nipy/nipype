# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""SPM wrappers for preprocessing data
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import range

import os
from copy import deepcopy

# Third-party imports
import numpy as np

# Local imports
from ...utils.filemanip import (fname_presuffix, ensure_list,
                                simplify_list, split_filename)
from ..base import (OutputMultiPath, TraitedSpec, isdefined,
                    traits, InputMultiPath, InputMultiObject, File, Str)
from .base import (SPMCommand, scans_for_fname, func_is_3d,
                   scans_for_fnames, SPMCommandInputSpec, ImageFileSPM)

__docformat__ = 'restructuredtext'


class FieldMapInputSpec(SPMCommandInputSpec):
    jobtype = traits.Enum('calculatevdm', 'applyvdm', usedefault=True,
        desc='one of: calculatevdm, applyvdm')
    phase_file = File(mandatory=True, exists=True, copyfile=False,
        field='subj.data.presubphasemag.phase',
        desc='presubstracted phase file')
    magnitude_file = File(mandatory=True, exists=True, copyfile=False,
        field='subj.data.presubphasemag.magnitude',
        desc='presubstracted magnitude file')
    echo_times = traits.Tuple(traits.Float, traits.Float, mandatory=True,
        field='subj.defaults.defaultsval.et',
        desc='short and long echo times')
    maskbrain = traits.Bool(True, usedefault=True,
        field='subj.defaults.defaultsval.maskbrain',
        desc='masking or no masking of the brain')
    blip_direction = traits.Enum(1, -1, mandatory=True,
        field='subj.defaults.defaultsval.blipdir',
        desc='polarity of the phase-encode blips')
    total_readout_time = traits.Float(mandatory=True,
        field='subj.defaults.defaultsval.tert',
        desc='total EPI readout time')
    epifm = traits.Bool(False, usedefault=True,
        field='subj.defaults.defaultsval.epifm',
        desc='epi-based field map');
    jacobian_modulation = traits.Bool(False, usedefault=True,
        field='subj.defaults.defaultsval.ajm',
        desc='jacobian modulation');
    # Unwarping defaults parameters
    method = traits.Enum('Mark3D', 'Mark2D', 'Huttonish', usedefault=True,
        desc='One of: Mark3D, Mark2D, Huttonish',
        field='subj.defaults.defaultsval.uflags.method');
    unwarp_fwhm = traits.Range(low=0, value=10, usedefault=True,
        field='subj.defaults.defaultsval.uflags.fwhm',
        desc='gaussian smoothing kernel width');
    pad = traits.Range(low=0, value=0, usedefault=True,
        field='subj.defaults.defaultsval.uflags.pad',
        desc='padding kernel width');
    ws = traits.Bool(True, usedefault=True,
        field='subj.defaults.defaultsval.uflags.ws',
        desc='weighted smoothing');
    # Brain mask defaults parameters
    template = File(copyfile=False, exists=True,
        field='subj.defaults.defaultsval.mflags.template',
        desc='template image for brain masking');
    mask_fwhm = traits.Range(low=0, value=5, usedefault=True,
        field='subj.defaults.defaultsval.mflags.fwhm',
        desc='gaussian smoothing kernel width');
    nerode = traits.Range(low=0, value=2, usedefault=True,
        field='subj.defaults.defaultsval.mflags.nerode',
        desc='number of erosions');
    ndilate = traits.Range(low=0, value=4, usedefault=True,
        field='subj.defaults.defaultsval.mflags.ndilate',
        desc='number of erosions');
    thresh = traits.Float(0.5, usedefault=True,
        field='subj.defaults.defaultsval.mflags.thresh',
        desc='threshold used to create brain mask from segmented data');
    reg = traits.Float(0.02, usedefault=True,
        field='subj.defaults.defaultsval.mflags.reg',
        desc='regularization value used in the segmentation');
    # EPI unwarping for quality check
    epi_file = File(copyfile=False, exists=True, mandatory=True,
        field='subj.session.epi',
        desc='EPI to unwarp');
    matchvdm = traits.Bool(True, usedefault=True,
        field='subj.matchvdm',
        desc='match VDM to EPI');
    sessname = Str('_run-', usedefault=True,
        field='subj.sessname',
        desc='VDM filename extension');
    writeunwarped = traits.Bool(False, usedefault=True,
        field='subj.writeunwarped',
        desc='write unwarped EPI');
    anat_file = File(copyfile=False, exists=True,
        field='subj.anat',
        desc='anatomical image for comparison');
    matchanat = traits.Bool(True, usedefault=True,
        field='subj.matchanat',
        desc='match anatomical image to EPI');


class FieldMapOutputSpec(TraitedSpec):
    vdm = File(exists=True, desc='voxel difference map')


class FieldMap(SPMCommand):
    """Use the fieldmap toolbox from spm to calculate the voxel displacement map (VDM).

    http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=173

    To do
    -----
    Deal with real/imag magnitude images and with the two phase files case.

    Examples
    --------
    >>> from nipype.interfaces.spm import FieldMap
    >>> fm = FieldMap()
    >>> fm.inputs.phase_file = 'phase.nii'
    >>> fm.inputs.magnitude_file = 'magnitude.nii'
    >>> fm.inputs.echo_times = (5.19, 7.65)
    >>> fm.inputs.blip_direction = 1
    >>> fm.inputs.total_readout_time = 15.6
    >>> fm.inputs.epi_file = 'epi.nii'
    >>> fm.run() # doctest: +SKIP

    """

    input_spec = FieldMapInputSpec
    output_spec = FieldMapOutputSpec
    _jobtype = 'tools'
    _jobname = 'fieldmap'

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt in ['phase_file', 'magnitude_file', 'anat_file', 'epi_file']:
            return scans_for_fname(ensure_list(val))

        return super(FieldMap, self)._format_arg(opt, spec, val)

    def _parse_inputs(self):
        """validate spm fieldmap options if set to None ignore
        """
        einputs = super(FieldMap, self)._parse_inputs()
        return [{self.inputs.jobtype: einputs[0]}]

    def _list_outputs(self):
        outputs = self._outputs().get()
        jobtype = self.inputs.jobtype
        if jobtype == "calculatevdm":
            outputs['vdm'] = fname_presuffix(self.inputs.phase_file, prefix='vdm5_sc')

        return outputs


class SliceTimingInputSpec(SPMCommandInputSpec):
    in_files = InputMultiPath(
        traits.Either(
            traits.List(ImageFileSPM(exists=True)), ImageFileSPM(exists=True)),
        field='scans',
        desc='list of filenames to apply slice timing',
        mandatory=True,
        copyfile=False)
    num_slices = traits.Int(
        field='nslices', desc='number of slices in a volume', mandatory=True)
    time_repetition = traits.Float(
        field='tr',
        desc=('time between volume acquisitions'
              '(start to start time)'),
        mandatory=True)
    time_acquisition = traits.Float(
        field='ta',
        desc=('time of volume acquisition. usually'
              'calculated as TR-(TR/num_slices)'),
        mandatory=True)
    slice_order = traits.List(
        traits.Float(),
        field='so',
        desc=('1-based order or onset (in ms) in which '
              'slices are acquired'),
        mandatory=True)
    ref_slice = traits.Int(
        field='refslice',
        desc='1-based Number of the reference slice or '
        'reference time point if slice_order is in '
        'onsets (ms)',
        mandatory=True)
    out_prefix = traits.String(
        'a', field='prefix', usedefault=True, desc='slicetimed output prefix')


class SliceTimingOutputSpec(TraitedSpec):
    timecorrected_files = OutputMultiPath(
        traits.Either(traits.List(File(exists=True)), File(exists=True)),
        desc='slice time corrected files')


class SliceTiming(SPMCommand):
    """Use spm to perform slice timing correction.

    http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=19

    Examples
    --------

    >>> from nipype.interfaces.spm import SliceTiming
    >>> st = SliceTiming()
    >>> st.inputs.in_files = 'functional.nii'
    >>> st.inputs.num_slices = 32
    >>> st.inputs.time_repetition = 6.0
    >>> st.inputs.time_acquisition = 6. - 6./32.
    >>> st.inputs.slice_order = list(range(32,0,-1))
    >>> st.inputs.ref_slice = 1
    >>> st.run() # doctest: +SKIP

    """

    input_spec = SliceTimingInputSpec
    output_spec = SliceTimingOutputSpec

    _jobtype = 'temporal'
    _jobname = 'st'

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt == 'in_files':
            return scans_for_fnames(
                ensure_list(val), keep4d=False, separate_sessions=True)
        return super(SliceTiming, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['timecorrected_files'] = []

        filelist = ensure_list(self.inputs.in_files)
        for f in filelist:
            if isinstance(f, list):
                run = [
                    fname_presuffix(in_f, prefix=self.inputs.out_prefix)
                    for in_f in f
                ]
            else:
                run = fname_presuffix(f, prefix=self.inputs.out_prefix)
            outputs['timecorrected_files'].append(run)
        return outputs


class RealignInputSpec(SPMCommandInputSpec):
    in_files = InputMultiPath(
        traits.Either(ImageFileSPM(exists=True),
                      traits.List(ImageFileSPM(exists=True))),
        field='data',
        mandatory=True,
        copyfile=True,
        desc='list of filenames to realign')
    jobtype = traits.Enum(
        'estwrite',
        'estimate',
        'write',
        desc='one of: estimate, write, estwrite',
        usedefault=True)
    quality = traits.Range(
        low=0.0,
        high=1.0,
        field='eoptions.quality',
        desc='0.1 = fast, 1.0 = precise')
    fwhm = traits.Range(
        low=0.0, field='eoptions.fwhm', desc='gaussian smoothing kernel width')
    separation = traits.Range(
        low=0.0, field='eoptions.sep', desc='sampling separation in mm')
    register_to_mean = traits.Bool(
        field='eoptions.rtm',
        desc=('Indicate whether realignment is '
              'done to the mean image'))
    weight_img = File(
        exists=True,
        field='eoptions.weight',
        desc='filename of weighting image')
    interp = traits.Range(
        low=0,
        high=7,
        field='eoptions.interp',
        desc='degree of b-spline used for interpolation')
    wrap = traits.List(
        traits.Int(),
        minlen=3,
        maxlen=3,
        field='eoptions.wrap',
        desc='Check if interpolation should wrap in [x,y,z]')
    write_which = traits.ListInt(
        [2, 1],
        field='roptions.which',
        minlen=2,
        maxlen=2,
        usedefault=True,
        desc='determines which images to reslice')
    write_interp = traits.Range(
        low=0,
        high=7,
        field='roptions.interp',
        desc=('degree of b-spline used for '
              'interpolation'))
    write_wrap = traits.List(
        traits.Int(),
        minlen=3,
        maxlen=3,
        field='roptions.wrap',
        desc=('Check if interpolation should wrap in '
              '[x,y,z]'))
    write_mask = traits.Bool(
        field='roptions.mask', desc='True/False mask output image')
    out_prefix = traits.String(
        'r',
        field='roptions.prefix',
        usedefault=True,
        desc='realigned output prefix')


class RealignOutputSpec(TraitedSpec):
    mean_image = File(exists=True, desc='Mean image file from the realignment')
    modified_in_files = OutputMultiPath(
        traits.Either(traits.List(File(exists=True)), File(exists=True)),
        desc=('Copies of all files passed to '
              'in_files. Headers will have '
              'been modified to align all '
              'images with the first, or '
              'optionally to first do that, '
              'extract a mean image, and '
              're-align to that mean image.'))
    realigned_files = OutputMultiPath(
        traits.Either(traits.List(File(exists=True)), File(exists=True)),
        desc=('If jobtype is write or estwrite, '
              'these will be the resliced files.'
              ' Otherwise, they will be copies '
              'of in_files that have had their '
              'headers rewritten.'))
    realignment_parameters = OutputMultiPath(
        File(exists=True),
        desc=('Estimated translation and '
              'rotation parameters'))


class Realign(SPMCommand):
    """Use spm_realign for estimating within modality rigid body alignment

    http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=25

    Examples
    --------

    >>> import nipype.interfaces.spm as spm
    >>> realign = spm.Realign()
    >>> realign.inputs.in_files = 'functional.nii'
    >>> realign.inputs.register_to_mean = True
    >>> realign.run() # doctest: +SKIP

    """

    input_spec = RealignInputSpec
    output_spec = RealignOutputSpec

    _jobtype = 'spatial'
    _jobname = 'realign'

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt == 'in_files':
            if self.inputs.jobtype == "write":
                separate_sessions = False
            else:
                separate_sessions = True
            return scans_for_fnames(
                val, keep4d=False, separate_sessions=separate_sessions)
        return super(Realign, self)._format_arg(opt, spec, val)

    def _parse_inputs(self):
        """validate spm realign options if set to None ignore
        """
        einputs = super(Realign, self)._parse_inputs()
        return [{'%s' % (self.inputs.jobtype): einputs[0]}]

    def _list_outputs(self):
        outputs = self._outputs().get()
        resliced_all = self.inputs.write_which[0] > 0
        resliced_mean = self.inputs.write_which[1] > 0

        if self.inputs.jobtype != "write":
            if isdefined(self.inputs.in_files):
                outputs['realignment_parameters'] = []
            for imgf in self.inputs.in_files:
                if isinstance(imgf, list):
                    tmp_imgf = imgf[0]
                else:
                    tmp_imgf = imgf
                outputs['realignment_parameters'].append(
                    fname_presuffix(
                        tmp_imgf, prefix='rp_', suffix='.txt', use_ext=False))
                if not isinstance(imgf, list) and func_is_3d(imgf):
                    break
        if self.inputs.jobtype == "estimate":
            outputs['realigned_files'] = self.inputs.in_files
        if (self.inputs.jobtype == "estimate"
                or self.inputs.jobtype == "estwrite"):
            outputs['modified_in_files'] = self.inputs.in_files
        if self.inputs.jobtype == "write" or self.inputs.jobtype == "estwrite":
            if isinstance(self.inputs.in_files[0], list):
                first_image = self.inputs.in_files[0][0]
            else:
                first_image = self.inputs.in_files[0]

            if resliced_mean:
                outputs['mean_image'] = fname_presuffix(
                    first_image, prefix='mean')

            if resliced_all:
                outputs['realigned_files'] = []
                for idx, imgf in enumerate(
                        ensure_list(self.inputs.in_files)):
                    realigned_run = []
                    if isinstance(imgf, list):
                        for i, inner_imgf in enumerate(ensure_list(imgf)):
                            newfile = fname_presuffix(
                                inner_imgf, prefix=self.inputs.out_prefix)
                            realigned_run.append(newfile)
                    else:
                        realigned_run = fname_presuffix(
                            imgf, prefix=self.inputs.out_prefix)
                    outputs['realigned_files'].append(realigned_run)
        return outputs


class RealignUnwarpInputSpec(SPMCommandInputSpec):

    in_files = InputMultiObject(
        traits.Either(ImageFileSPM(exists=True),
                      traits.List(ImageFileSPM(exists=True))),
        field='data.scans',
        mandatory=True, 
        copyfile=True,
        desc='list of filenames to realign and unwarp')
    phase_map = File(
        field='data.pmscan',
        desc='Voxel displacement map to use in unwarping. Unlike SPM standard '
             'behaviour, the same map will be used for all sessions',
        copyfile=False)
    quality = traits.Range(
        low=0.0, 
        high=1.0, 
        field='eoptions.quality',
        desc='0.1 = fast, 1.0 = precise')
    fwhm = traits.Range(
        low=0.0, 
        field='eoptions.fwhm',
        desc='gaussian smoothing kernel width')
    separation = traits.Range(
        low=0.0, 
        field='eoptions.sep',
        desc='sampling separation in mm')
    register_to_mean = traits.Bool(
        field='eoptions.rtm',
        desc='Indicate whether realignment is done to the mean image')
    weight_img = File(
        exists=True, 
        field='eoptions.weight',
        desc='filename of weighting image')
    interp = traits.Range(
        low=0, 
        high=7, 
        field='eoptions.einterp',
        desc='degree of b-spline used for interpolation')
    wrap = traits.List(
        traits.Int(), 
        minlen=3, 
        maxlen=3,
        field='eoptions.ewrap',
        desc='Check if interpolation should wrap in [x,y,z]')
    est_basis_func = traits.List(
        traits.Int(), 
        minlen=2, 
        maxlen=2,
        field='uweoptions.basfcn',
        desc='Number of basis functions to use for each dimension')
    est_reg_order = traits.Range(
        low=0, 
        high=3, 
        field='uweoptions.regorder',
        desc=('This parameter determines how to balance the compromise between likelihood '
              'maximization and smoothness maximization of the estimated field.'))
    est_reg_factor = traits.ListInt(
        [100000], 
        field='uweoptions.lambda',
        minlen=1, 
        maxlen=1,
        usedefault=True,
        desc='Regularisation factor. Default: 100000 (medium).')
    est_jacobian_deformations = traits.Bool(
        field='uweoptions.jm',
        desc=('Jacobian deformations. In theory a good idea to include them, '
             ' in practice a bad idea. Default: No.'))
    est_first_order_effects = traits.List(
        traits.Int(), 
        minlen=1, 
        maxlen=6,
        field='uweoptions.fot',
        desc='First order effects should only depend on pitch and roll, i.e. [4 5]')
    est_second_order_effects = traits.List(
        traits.Int(), 
        minlen=1, 
        maxlen=6,
        field='uweoptions.sot',
        desc='List of second order terms to model second derivatives of.')
    est_unwarp_fwhm = traits.Range(
        low=0.0, 
        field='uweoptions.uwfwhm',
        desc='gaussian smoothing kernel width for unwarp')
    est_re_est_mov_par = traits.Bool(
        field='uweoptions.rem',
        desc='Re-estimate movement parameters at each unwarping iteration.')
    est_num_of_interations = traits.ListInt(
        [5], 
        field='uweoptions.noi',
        minlen=1, 
        maxlen=1, 
        usedfault=True,
        desc='Number of iterations.')
    est_taylor_expansion_point = traits.String(
        'Average', 
        field='uweoptions.expround',
        usedefault=True,
        desc='Point in position space to perform Taylor-expansion around.')
    reslice_which = traits.ListInt(
        [2, 1], 
        field='uwroptions.uwwhich',
        minlen=2, 
        maxlen=2, 
        usedefault=True,
        desc='determines which images to reslice')
    reslice_interp = traits.Range(
        low=0, 
        high=7, 
        field='uwroptions.rinterp',
        desc='degree of b-spline used for interpolation')
    reslice_wrap = traits.List(
        traits.Int(), 
        minlen=3, 
        maxlen=3,
        field='uwroptions.wrap',
        desc='Check if interpolation should wrap in [x,y,z]')
    reslice_mask = traits.Bool(
        field='uwroptions.mask',
        desc='True/False mask output image')
    out_prefix = traits.String(
        'u', 
        field='uwroptions.prefix', 
        usedefault=True,
        desc='realigned and unwarped output prefix')


class RealignUnwarpOutputSpec(TraitedSpec):
    mean_image = File(exists=True, desc='Mean image file from the realignment & unwarping')
    modified_in_files = OutputMultiPath(
        traits.Either(traits.List(File(exists=True)), File(exists=True)),
        desc=('Copies of all files passed to '
              'in_files. Headers will have '
              'been modified to align all '
              'images with the first, or '
              'optionally to first do that, '
              'extract a mean image, and '
              're-align to that mean image.'))
    realigned_unwarped_files = OutputMultiPath(
        traits.Either(traits.List(File(exists=True)), File(exists=True)),
        desc='Realigned and unwarped files written to disc.')
    realignment_parameters = OutputMultiPath(
        File(exists=True),
        desc='Estimated translation and rotation parameters')


class RealignUnwarp(SPMCommand):
    """Use spm_uw_estimate for estimating within subject registration and unwarping
    of time series. Function accepts only one single field map. If in_files is a 
    list of files they will be treated as separate sessions but associated to the
    same fieldmap.

    http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=31

    Examples
    --------

    >>> import nipype.interfaces.spm as spm
    >>> realignUnwarp = spm.RealignUnwarp()
    >>> realignUnwarp.inputs.in_files = ['functional.nii', 'functional2.nii']
    >>> realignUnwarp.inputs.phase_map = 'voxeldisplacemap.vdm'
    >>> realignUnwarp.inputs.register_to_mean = True
    >>> realignUnwarp.run() # doctest: +SKIP

    """

    input_spec = RealignUnwarpInputSpec
    output_spec = RealignUnwarpOutputSpec

    _jobtype = 'spatial'
    _jobname = 'realignunwarp'

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt == 'in_files':
            return scans_for_fnames(ensure_list(val),
                                    keep4d=False,
                                    separate_sessions=True)
        return super(RealignUnwarp, self)._format_arg(opt, spec, val)
   

    def _parse_inputs(self, skip=()):

        spmdict = super(RealignUnwarp, self)._parse_inputs(skip=())[0]

        if isdefined(self.inputs.phase_map):
            pmscan = spmdict['data']['pmscan']
        else:
            pmscan = ''

        if isdefined(self.inputs.in_files):
            if isinstance(self.inputs.in_files, list):
                data = [dict(scans = sess, pmscan = pmscan) 
                                          for sess in spmdict['data']['scans']]
            else:
                data = [dict(scans = spmdict['data']['scans'], pmscan = pmscan)]

        spmdict['data'] = data

        return [spmdict]


    def _list_outputs(self):
        outputs = self._outputs().get()
        resliced_all = self.inputs.reslice_which[0] > 0
        resliced_mean = self.inputs.reslice_which[1] > 0

        if isdefined(self.inputs.in_files):
            outputs['realignment_parameters'] = []
        for imgf in self.inputs.in_files:
            if isinstance(imgf, list):
                tmp_imgf = imgf[0]
            else:
                tmp_imgf = imgf
            outputs['realignment_parameters'].append(fname_presuffix(tmp_imgf,
                                                                     prefix='rp_',
                                                                     suffix='.txt',
                                                                     use_ext=False))
            if not isinstance(imgf, list) and func_is_3d(imgf):
                break

        if isinstance(self.inputs.in_files[0], list):
            first_image = self.inputs.in_files[0][0]
        else:
            first_image = self.inputs.in_files[0]

        if resliced_mean:
            outputs['mean_image'] = fname_presuffix(first_image, prefix='meanu')

        if resliced_all:
            outputs['realigned_unwarped_files'] = []
            for idx, imgf in enumerate(ensure_list(self.inputs.in_files)):
                realigned_run = []
                if isinstance(imgf, list):
                    for i, inner_imgf in enumerate(ensure_list(imgf)):
                        newfile = fname_presuffix(inner_imgf,
                                                  prefix=self.inputs.out_prefix)
                        realigned_run.append(newfile)
                else:
                    realigned_run = fname_presuffix(imgf,
                                                    prefix=self.inputs.out_prefix)
                outputs['realigned_unwarped_files'].append(realigned_run)
        return outputs


class CoregisterInputSpec(SPMCommandInputSpec):
    target = ImageFileSPM(
        exists=True,
        mandatory=True,
        field='ref',
        desc='reference file to register to',
        copyfile=False)
    source = InputMultiPath(
        ImageFileSPM(exists=True),
        field='source',
        desc='file to register to target',
        copyfile=True,
        mandatory=True)
    jobtype = traits.Enum(
        'estwrite',
        'estimate',
        'write',
        desc='one of: estimate, write, estwrite',
        usedefault=True)
    apply_to_files = InputMultiPath(
        File(exists=True),
        field='other',
        desc='files to apply transformation to',
        copyfile=True)
    cost_function = traits.Enum(
        'mi',
        'nmi',
        'ecc',
        'ncc',
        field='eoptions.cost_fun',
        desc="""cost function, one of:
                    'mi' - Mutual Information,
                    'nmi' - Normalised Mutual Information,
                    'ecc' - Entropy Correlation Coefficient,
                    'ncc' - Normalised Cross Correlation""")
    fwhm = traits.List(
        traits.Float(),
        minlen=2,
        maxlen=2,
        field='eoptions.fwhm',
        desc='gaussian smoothing kernel width (mm)')
    separation = traits.List(
        traits.Float(), field='eoptions.sep', desc='sampling separation in mm')
    tolerance = traits.List(
        traits.Float(),
        field='eoptions.tol',
        desc='acceptable tolerance for each of 12 params')
    write_interp = traits.Range(
        low=0,
        high=7,
        field='roptions.interp',
        desc=('degree of b-spline used for '
              'interpolation'))
    write_wrap = traits.List(
        traits.Int(),
        minlen=3,
        maxlen=3,
        field='roptions.wrap',
        desc=('Check if interpolation should wrap in '
              '[x,y,z]'))
    write_mask = traits.Bool(
        field='roptions.mask', desc='True/False mask output image')
    out_prefix = traits.String(
        'r',
        field='roptions.prefix',
        usedefault=True,
        desc='coregistered output prefix')


class CoregisterOutputSpec(TraitedSpec):
    coregistered_source = OutputMultiPath(
        File(exists=True), desc='Coregistered source files')
    coregistered_files = OutputMultiPath(
        File(exists=True), desc='Coregistered other files')


class Coregister(SPMCommand):
    """Use spm_coreg for estimating cross-modality rigid body alignment

    http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=39

    Examples
    --------

    >>> import nipype.interfaces.spm as spm
    >>> coreg = spm.Coregister()
    >>> coreg.inputs.target = 'functional.nii'
    >>> coreg.inputs.source = 'structural.nii'
    >>> coreg.run() # doctest: +SKIP

    """

    input_spec = CoregisterInputSpec
    output_spec = CoregisterOutputSpec
    _jobtype = 'spatial'
    _jobname = 'coreg'

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if (opt == 'target'
                or (opt == 'source' and self.inputs.jobtype != "write")):
            return scans_for_fnames(ensure_list(val), keep4d=True)
        if opt == 'apply_to_files':
            return np.array(ensure_list(val), dtype=object)
        if opt == 'source' and self.inputs.jobtype == "write":
            if isdefined(self.inputs.apply_to_files):
                return scans_for_fnames(val + self.inputs.apply_to_files)
            else:
                return scans_for_fnames(val)
        return super(Coregister, self)._format_arg(opt, spec, val)

    def _parse_inputs(self):
        """validate spm coregister options if set to None ignore
        """
        if self.inputs.jobtype == "write":
            einputs = (super(Coregister, self)
                       ._parse_inputs(skip=('jobtype', 'apply_to_files')))
        else:
            einputs = super(Coregister, self)._parse_inputs(skip=('jobtype'))
        jobtype = self.inputs.jobtype
        return [{'%s' % (jobtype): einputs[0]}]

    def _list_outputs(self):
        outputs = self._outputs().get()

        if self.inputs.jobtype == "estimate":
            if isdefined(self.inputs.apply_to_files):
                outputs['coregistered_files'] = self.inputs.apply_to_files
            outputs['coregistered_source'] = self.inputs.source
        elif (self.inputs.jobtype == "write"
              or self.inputs.jobtype == "estwrite"):
            if isdefined(self.inputs.apply_to_files):
                outputs['coregistered_files'] = []
                for imgf in ensure_list(self.inputs.apply_to_files):
                    (outputs['coregistered_files'].append(
                        fname_presuffix(imgf, prefix=self.inputs.out_prefix)))

            outputs['coregistered_source'] = []
            for imgf in ensure_list(self.inputs.source):
                (outputs['coregistered_source'].append(
                    fname_presuffix(imgf, prefix=self.inputs.out_prefix)))

        return outputs


class NormalizeInputSpec(SPMCommandInputSpec):
    template = File(
        exists=True,
        field='eoptions.template',
        desc='template file to normalize to',
        mandatory=True,
        xor=['parameter_file'],
        copyfile=False)
    source = InputMultiPath(
        ImageFileSPM(exists=True),
        field='subj.source',
        xor=['parameter_file'],
        desc='file to normalize to template',
        mandatory=True,
        copyfile=True)
    jobtype = traits.Enum(
        'estwrite',
        'est',
        'write',
        usedefault=True,
        desc='Estimate, Write or do both')
    apply_to_files = InputMultiPath(
        traits.Either(File(exists=True), traits.List(File(exists=True))),
        field='subj.resample',
        desc='files to apply transformation to',
        copyfile=True)
    parameter_file = File(
        field='subj.matname',
        mandatory=True,
        xor=['source', 'template'],
        desc='normalization parameter file*_sn.mat',
        copyfile=False)
    source_weight = File(
        field='subj.wtsrc',
        desc='name of weighting image for source',
        copyfile=False)
    template_weight = File(
        field='eoptions.weight',
        desc='name of weighting image for template',
        copyfile=False)
    source_image_smoothing = traits.Float(
        field='eoptions.smosrc', desc='source smoothing')
    template_image_smoothing = traits.Float(
        field='eoptions.smoref', desc='template smoothing')
    affine_regularization_type = traits.Enum(
        'mni',
        'size',
        'none',
        field='eoptions.regtype',
        desc='mni, size, none')
    DCT_period_cutoff = traits.Float(
        field='eoptions.cutoff', desc='Cutoff of for DCT bases')
    nonlinear_iterations = traits.Int(
        field='eoptions.nits',
        desc=('Number of iterations of '
              'nonlinear warping'))
    nonlinear_regularization = traits.Float(
        field='eoptions.reg',
        desc=('the amount of the '
              'regularization for the '
              'nonlinear part of the '
              'normalization'))
    write_preserve = traits.Bool(
        field='roptions.preserve',
        desc='True/False warped images are modulated')
    write_bounding_box = traits.List(
        traits.List(traits.Float(), minlen=3, maxlen=3),
        field='roptions.bb',
        minlen=2,
        maxlen=2,
        desc='3x2-element list of lists')
    write_voxel_sizes = traits.List(
        traits.Float(),
        field='roptions.vox',
        minlen=3,
        maxlen=3,
        desc='3-element list')
    write_interp = traits.Range(
        low=0,
        high=7,
        field='roptions.interp',
        desc=('degree of b-spline used for '
              'interpolation'))
    write_wrap = traits.List(
        traits.Int(),
        field='roptions.wrap',
        desc=('Check if interpolation should wrap in '
              '[x,y,z] - list of bools'))
    out_prefix = traits.String(
        'w',
        field='roptions.prefix',
        usedefault=True,
        desc='normalized output prefix')


class NormalizeOutputSpec(TraitedSpec):
    normalization_parameters = OutputMultiPath(
        File(exists=True),
        desc=('MAT files containing '
              'the normalization '
              'parameters'))
    normalized_source = OutputMultiPath(
        File(exists=True), desc='Normalized source files')
    normalized_files = OutputMultiPath(
        File(exists=True), desc='Normalized other files')


class Normalize(SPMCommand):
    """use spm_normalise for warping an image to a template

    http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=203

    Examples
    --------
    >>> import nipype.interfaces.spm as spm
    >>> norm = spm.Normalize()
    >>> norm.inputs.source = 'functional.nii'
    >>> norm.run() # doctest: +SKIP

    """

    input_spec = NormalizeInputSpec
    output_spec = NormalizeOutputSpec
    _jobtype = 'spatial'
    _jobname = 'normalise'

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt == 'template':
            return scans_for_fname(ensure_list(val))
        if opt == 'source':
            return scans_for_fname(ensure_list(val))
        if opt == 'apply_to_files':
            return scans_for_fnames(ensure_list(val))
        if opt == 'parameter_file':
            return np.array([simplify_list(val)], dtype=object)
        if opt in ['write_wrap']:
            if len(val) != 3:
                raise ValueError('%s must have 3 elements' % opt)
        return super(Normalize, self)._format_arg(opt, spec, val)

    def _parse_inputs(self):
        """Validate spm normalize options if set to None ignore
        """
        einputs = super(
            Normalize, self)._parse_inputs(skip=('jobtype', 'apply_to_files'))
        if isdefined(self.inputs.apply_to_files):
            inputfiles = deepcopy(self.inputs.apply_to_files)
            if isdefined(self.inputs.source):
                inputfiles.extend(self.inputs.source)
            einputs[0]['subj']['resample'] = scans_for_fnames(inputfiles)
        jobtype = self.inputs.jobtype
        if jobtype in ['estwrite', 'write']:
            if not isdefined(self.inputs.apply_to_files):
                if isdefined(self.inputs.source):
                    einputs[0]['subj']['resample'] = scans_for_fname(
                        self.inputs.source)
        return [{'%s' % (jobtype): einputs[0]}]

    def _list_outputs(self):
        outputs = self._outputs().get()

        jobtype = self.inputs.jobtype
        if jobtype.startswith('est'):
            outputs['normalization_parameters'] = []
            for imgf in ensure_list(self.inputs.source):
                outputs['normalization_parameters'].append(
                    fname_presuffix(imgf, suffix='_sn.mat', use_ext=False))
            outputs['normalization_parameters'] = simplify_list(
                outputs['normalization_parameters'])

        if self.inputs.jobtype == "estimate":
            if isdefined(self.inputs.apply_to_files):
                outputs['normalized_files'] = self.inputs.apply_to_files
            outputs['normalized_source'] = self.inputs.source
        elif 'write' in self.inputs.jobtype:
            if (isdefined(self.inputs.write_preserve)
                    and self.inputs.write_preserve):
                prefixNorm = ''.join(['m', self.inputs.out_prefix])
            else:
                prefixNorm = self.inputs.out_prefix
            outputs['normalized_files'] = []
            if isdefined(self.inputs.apply_to_files):
                filelist = ensure_list(self.inputs.apply_to_files)
                for f in filelist:
                    if isinstance(f, list):
                        run = [
                            fname_presuffix(in_f, prefix=prefixNorm)
                            for in_f in f
                        ]
                    else:
                        run = [fname_presuffix(f, prefix=prefixNorm)]
                    outputs['normalized_files'].extend(run)
            if isdefined(self.inputs.source):
                outputs['normalized_source'] = []
                for imgf in ensure_list(self.inputs.source):
                    outputs['normalized_source'].append(
                        fname_presuffix(imgf, prefix=prefixNorm))

        return outputs


class Normalize12InputSpec(SPMCommandInputSpec):
    image_to_align = ImageFileSPM(
        exists=True,
        field='subj.vol',
        desc=('file to estimate normalization parameters '
              'with'),
        xor=['deformation_file'],
        mandatory=True,
        copyfile=True)
    apply_to_files = InputMultiPath(
        traits.Either(
            ImageFileSPM(exists=True), traits.List(ImageFileSPM(exists=True))),
        field='subj.resample',
        desc='files to apply transformation to',
        copyfile=True)
    deformation_file = ImageFileSPM(
        field='subj.def',
        mandatory=True,
        xor=['image_to_align', 'tpm'],
        copyfile=False,
        desc=('file y_*.nii containing 3 deformation '
              'fields for the deformation in x, y and z '
              'dimension'))
    jobtype = traits.Enum(
        'estwrite',
        'est',
        'write',
        usedefault=True,
        desc='Estimate, Write or do Both')
    bias_regularization = traits.Enum(
        0,
        0.00001,
        0.0001,
        0.001,
        0.01,
        0.1,
        1,
        10,
        field='eoptions.biasreg',
        desc='no(0) - extremely heavy (10)')
    bias_fwhm = traits.Enum(
        30,
        40,
        50,
        60,
        70,
        80,
        90,
        100,
        110,
        120,
        130,
        140,
        150,
        'Inf',
        field='eoptions.biasfwhm',
        desc='FWHM of Gaussian smoothness of bias')
    tpm = File(
        exists=True,
        field='eoptions.tpm',
        desc=('template in form of tissue probablitiy maps to '
              'normalize to'),
        xor=['deformation_file'],
        copyfile=False)
    affine_regularization_type = traits.Enum(
        'mni', 'size', 'none', field='eoptions.affreg', desc='mni, size, none')
    warping_regularization = traits.List(
        traits.Float(),
        field='eoptions.reg',
        minlen=5,
        maxlen=5,
        desc=('controls balance between '
              'parameters and data'))
    smoothness = traits.Float(
        field='eoptions.fwhm',
        desc=('value (in mm) to smooth the data before '
              'normalization'))
    sampling_distance = traits.Float(
        field='eoptions.samp',
        desc=('Sampling distance on data for '
              'parameter estimation'))
    write_bounding_box = traits.List(
        traits.List(traits.Float(), minlen=3, maxlen=3),
        field='woptions.bb',
        minlen=2,
        maxlen=2,
        desc=('3x2-element list of lists '
              'representing the bounding box '
              '(in mm) to be written'))
    write_voxel_sizes = traits.List(
        traits.Float(),
        field='woptions.vox',
        minlen=3,
        maxlen=3,
        desc=('3-element list representing the '
              'voxel sizes (in mm) of the written '
              'normalised images'))
    write_interp = traits.Range(
        low=0,
        high=7,
        field='woptions.interp',
        desc=('degree of b-spline used for '
              'interpolation'))
    out_prefix = traits.String(
        'w',
        field='woptions.prefix',
        usedefault=True,
        desc='Normalized output prefix')


class Normalize12OutputSpec(TraitedSpec):
    deformation_field = OutputMultiPath(
        File(exists=True),
        desc=('NIfTI file containing 3 '
              'deformation fields for the '
              'deformation in x, y and z '
              'dimension'))
    normalized_image = OutputMultiPath(
        File(exists=True),
        desc=('Normalized file that needed to '
              'be aligned'))
    normalized_files = OutputMultiPath(
        File(exists=True), desc='Normalized other files')


class Normalize12(SPMCommand):
    """uses SPM12's new Normalise routine for warping an image to a template.
    Spatial normalisation is now done via the segmentation routine (which was
    known as ``New Segment`` in SPM8). Note that the normalisation in SPM12
    is done towards a file containing multiple tissue probability maps, which
    was not the case in SPM8.

    http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=49

    Examples
    --------
    >>> import nipype.interfaces.spm as spm
    >>> norm12 = spm.Normalize12()
    >>> norm12.inputs.image_to_align = 'structural.nii'
    >>> norm12.inputs.apply_to_files = 'functional.nii'
    >>> norm12.run() # doctest: +SKIP

    """

    input_spec = Normalize12InputSpec
    output_spec = Normalize12OutputSpec
    _jobtype = 'spatial'
    _jobname = 'normalise'

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt == 'tpm':
            return scans_for_fname(ensure_list(val))
        if opt == 'image_to_align':
            return scans_for_fname(ensure_list(val))
        if opt == 'apply_to_files':
            return scans_for_fnames(ensure_list(val))
        if opt == 'deformation_file':
            return np.array([simplify_list(val)], dtype=object)
        if opt in ['nonlinear_regularization']:
            if len(val) != 5:
                raise ValueError('%s must have 5 elements' % opt)
        return super(Normalize12, self)._format_arg(opt, spec, val)

    def _parse_inputs(self, skip=()):
        """validate spm normalize options if set to None ignore
        """
        einputs = super(
            Normalize12,
            self)._parse_inputs(skip=('jobtype', 'apply_to_files'))
        if isdefined(self.inputs.apply_to_files):
            inputfiles = deepcopy(self.inputs.apply_to_files)
            if isdefined(self.inputs.image_to_align):
                inputfiles.extend([self.inputs.image_to_align])
            einputs[0]['subj']['resample'] = scans_for_fnames(inputfiles)
        jobtype = self.inputs.jobtype
        if jobtype in ['estwrite', 'write']:
            if not isdefined(self.inputs.apply_to_files):
                if isdefined(self.inputs.image_to_align):
                    einputs[0]['subj']['resample'] = scans_for_fname(
                        self.inputs.image_to_align)
        return [{'%s' % (jobtype): einputs[0]}]

    def _list_outputs(self):
        outputs = self._outputs().get()

        jobtype = self.inputs.jobtype
        if jobtype.startswith('est'):
            outputs['deformation_field'] = []
            for imgf in ensure_list(self.inputs.image_to_align):
                outputs['deformation_field'].append(
                    fname_presuffix(imgf, prefix='y_'))
            outputs['deformation_field'] = simplify_list(
                outputs['deformation_field'])

        if self.inputs.jobtype == "estimate":
            if isdefined(self.inputs.apply_to_files):
                outputs['normalized_files'] = self.inputs.apply_to_files
            outputs['normalized_image'] = fname_presuffix(
                self.inputs.image_to_align, prefix='w')
        elif 'write' in self.inputs.jobtype:
            outputs['normalized_files'] = []
            if isdefined(self.inputs.apply_to_files):
                filelist = ensure_list(self.inputs.apply_to_files)
                for f in filelist:
                    if isinstance(f, list):
                        run = [fname_presuffix(in_f, prefix='w') for in_f in f]
                    else:
                        run = [fname_presuffix(f, prefix='w')]
                    outputs['normalized_files'].extend(run)
            if isdefined(self.inputs.image_to_align):
                outputs['normalized_image'] = fname_presuffix(
                    self.inputs.image_to_align, prefix='w')

        return outputs


class SegmentInputSpec(SPMCommandInputSpec):
    data = InputMultiPath(
        ImageFileSPM(exists=True),
        field='data',
        desc='one scan per subject',
        copyfile=False,
        mandatory=True)
    gm_output_type = traits.List(
        traits.Bool(),
        minlen=3,
        maxlen=3,
        field='output.GM',
        desc=
        """Options to produce grey matter images: c1*.img, wc1*.img and mwc1*.img.
            None: [False,False,False],
            Native Space: [False,False,True],
            Unmodulated Normalised: [False,True,False],
            Modulated Normalised: [True,False,False],
            Native + Unmodulated Normalised: [False,True,True],
            Native + Modulated Normalised: [True,False,True],
            Native + Modulated + Unmodulated: [True,True,True],
            Modulated + Unmodulated Normalised: [True,True,False]""")
    wm_output_type = traits.List(
        traits.Bool(),
        minlen=3,
        maxlen=3,
        field='output.WM',
        desc="""
            Options to produce white matter images: c2*.img, wc2*.img and mwc2*.img.
            None: [False,False,False],
            Native Space: [False,False,True],
            Unmodulated Normalised: [False,True,False],
            Modulated Normalised: [True,False,False],
            Native + Unmodulated Normalised: [False,True,True],
            Native + Modulated Normalised: [True,False,True],
            Native + Modulated + Unmodulated: [True,True,True],
            Modulated + Unmodulated Normalised: [True,True,False]""")
    csf_output_type = traits.List(
        traits.Bool(),
        minlen=3,
        maxlen=3,
        field='output.CSF',
        desc="""
            Options to produce CSF images: c3*.img, wc3*.img and mwc3*.img.
            None: [False,False,False],
            Native Space: [False,False,True],
            Unmodulated Normalised: [False,True,False],
            Modulated Normalised: [True,False,False],
            Native + Unmodulated Normalised: [False,True,True],
            Native + Modulated Normalised: [True,False,True],
            Native + Modulated + Unmodulated: [True,True,True],
            Modulated + Unmodulated Normalised: [True,True,False]""")
    save_bias_corrected = traits.Bool(
        field='output.biascor',
        desc=('True/False produce a bias '
              'corrected image'))
    clean_masks = traits.Enum(
        'no',
        'light',
        'thorough',
        field='output.cleanup',
        desc=("clean using estimated brain mask "
              "('no','light','thorough')"))
    tissue_prob_maps = traits.List(
        File(exists=True),
        field='opts.tpm',
        desc=('list of gray, white & csf prob. '
              '(opt,)'))
    gaussians_per_class = traits.List(
        traits.Int(),
        field='opts.ngaus',
        desc=('num Gaussians capture intensity '
              'distribution'))
    affine_regularization = traits.Enum(
        'mni',
        'eastern',
        'subj',
        'none',
        '',
        field='opts.regtype',
        desc=('Possible options: "mni", '
              '"eastern", "subj", "none" '
              '(no reguralisation), "" '
              '(no affine registration)'))
    warping_regularization = traits.Float(
        field='opts.warpreg',
        desc=('Controls balance between '
              'parameters and data'))
    warp_frequency_cutoff = traits.Float(
        field='opts.warpco', desc='Cutoff of DCT bases')
    bias_regularization = traits.Enum(
        0,
        0.00001,
        0.0001,
        0.001,
        0.01,
        0.1,
        1,
        10,
        field='opts.biasreg',
        desc='no(0) - extremely heavy (10)')
    bias_fwhm = traits.Enum(
        30,
        40,
        50,
        60,
        70,
        80,
        90,
        100,
        110,
        120,
        130,
        'Inf',
        field='opts.biasfwhm',
        desc='FWHM of Gaussian smoothness of bias')
    sampling_distance = traits.Float(
        field='opts.samp',
        desc=('Sampling distance on data for '
              'parameter estimation'))
    mask_image = File(
        exists=True,
        field='opts.msk',
        desc='Binary image to restrict parameter estimation ')


class SegmentOutputSpec(TraitedSpec):
    native_gm_image = File(desc='native space grey probability map')
    normalized_gm_image = File(desc='normalized grey probability map', )
    modulated_gm_image = File(
        desc=('modulated, normalized grey '
              'probability map'))
    native_wm_image = File(desc='native space white probability map')
    normalized_wm_image = File(desc='normalized white probability map')
    modulated_wm_image = File(
        desc=('modulated, normalized white '
              'probability map'))
    native_csf_image = File(desc='native space csf probability map')
    normalized_csf_image = File(desc='normalized csf probability map')
    modulated_csf_image = File(
        desc=('modulated, normalized csf '
              'probability map'))
    modulated_input_image = File(
        deprecated='0.10',
        new_name='bias_corrected_image',
        desc='bias-corrected version of input image')
    bias_corrected_image = File(desc='bias-corrected version of input image')
    transformation_mat = File(exists=True, desc='Normalization transformation')
    inverse_transformation_mat = File(
        exists=True, desc='Inverse normalization info')


class Segment(SPMCommand):
    """use spm_segment to separate structural images into different
    tissue classes.

    http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=209

    Examples
    --------
    >>> import nipype.interfaces.spm as spm
    >>> seg = spm.Segment()
    >>> seg.inputs.data = 'structural.nii'
    >>> seg.run() # doctest: +SKIP

    """

    input_spec = SegmentInputSpec
    output_spec = SegmentOutputSpec

    def __init__(self, **inputs):
        _local_version = SPMCommand().version
        if _local_version and '12.' in _local_version:
            self._jobtype = 'tools'
            self._jobname = 'oldseg'
        else:
            self._jobtype = 'spatial'
            self._jobname = 'preproc'

        SPMCommand.__init__(self, **inputs)

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        clean_masks_dict = {'no': 0, 'light': 1, 'thorough': 2}

        if opt in ['data', 'tissue_prob_maps']:
            if isinstance(val, list):
                return scans_for_fnames(val)
            else:
                return scans_for_fname(val)
        if 'output_type' in opt:
            return [int(v) for v in val]
        if opt == 'mask_image':
            return scans_for_fname(val)
        if opt == 'clean_masks':
            return clean_masks_dict[val]
        return super(Segment, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        f = self.inputs.data[0]

        for tidx, tissue in enumerate(['gm', 'wm', 'csf']):
            outtype = '%s_output_type' % tissue
            if isdefined(getattr(self.inputs, outtype)):
                for idx, (image, prefix) in enumerate([('modulated', 'mw'),
                                                       ('normalized',
                                                        'w'), ('native', '')]):
                    if getattr(self.inputs, outtype)[idx]:
                        outfield = '%s_%s_image' % (image, tissue)
                        outputs[outfield] = fname_presuffix(
                            f, prefix='%sc%d' % (prefix, tidx + 1))
        if (isdefined(self.inputs.save_bias_corrected)
                and self.inputs.save_bias_corrected):
            outputs['bias_corrected_image'] = fname_presuffix(f, prefix='m')
        t_mat = fname_presuffix(f, suffix='_seg_sn.mat', use_ext=False)
        outputs['transformation_mat'] = t_mat
        invt_mat = fname_presuffix(f, suffix='_seg_inv_sn.mat', use_ext=False)
        outputs['inverse_transformation_mat'] = invt_mat
        return outputs


class NewSegmentInputSpec(SPMCommandInputSpec):
    channel_files = InputMultiPath(
        ImageFileSPM(exists=True),
        mandatory=True,
        desc="A list of files to be segmented",
        field='channel',
        copyfile=False)
    channel_info = traits.Tuple(
        traits.Float(),
        traits.Float(),
        traits.Tuple(traits.Bool, traits.Bool),
        desc="""A tuple with the following fields:
            - bias reguralisation (0-10)
            - FWHM of Gaussian smoothness of bias
            - which maps to save (Corrected, Field) - a tuple of two boolean values""",
        field='channel')
    tissues = traits.List(
        traits.Tuple(
            traits.Tuple(ImageFileSPM(exists=True), traits.Int()),
            traits.Int(), traits.Tuple(traits.Bool, traits.Bool),
            traits.Tuple(traits.Bool, traits.Bool)),
        desc="""A list of tuples (one per tissue) with the following fields:
            - tissue probability map (4D), 1-based index to frame
            - number of gaussians
            - which maps to save [Native, DARTEL] - a tuple of two boolean values
            - which maps to save [Unmodulated, Modulated] - a tuple of two boolean values""",
        field='tissue')
    affine_regularization = traits.Enum(
        'mni',
        'eastern',
        'subj',
        'none',
        field='warp.affreg',
        desc='mni, eastern, subj, none ')
    warping_regularization = traits.Either(
        traits.List(traits.Float(), minlen=5, maxlen=5),
        traits.Float(),
        field='warp.reg',
        desc=('Warping regularization '
              'parameter(s). Accepts float '
              'or list of floats (the '
              'latter is required by '
              'SPM12)'))
    sampling_distance = traits.Float(
        field='warp.samp',
        desc=('Sampling distance on data for '
              'parameter estimation'))
    write_deformation_fields = traits.List(
        traits.Bool(),
        minlen=2,
        maxlen=2,
        field='warp.write',
        desc=("Which deformation fields to "
              "write:[Inverse, Forward]"))


class NewSegmentOutputSpec(TraitedSpec):
    native_class_images = traits.List(
        traits.List(File(exists=True)), desc='native space probability maps')
    dartel_input_images = traits.List(
        traits.List(File(exists=True)), desc='dartel imported class images')
    normalized_class_images = traits.List(
        traits.List(File(exists=True)), desc='normalized class images')
    modulated_class_images = traits.List(
        traits.List(File(exists=True)),
        desc=('modulated+normalized class '
              'images'))
    transformation_mat = OutputMultiPath(
        File(exists=True), desc='Normalization transformation')
    bias_corrected_images = OutputMultiPath(
        File(exists=True), desc='bias corrected images')
    bias_field_images = OutputMultiPath(
        File(exists=True), desc='bias field images')
    forward_deformation_field = OutputMultiPath(File(exists=True))
    inverse_deformation_field = OutputMultiPath(File(exists=True))


class NewSegment(SPMCommand):
    """Use spm_preproc8 (New Segment) to separate structural images into
    different tissue classes. Supports multiple modalities.

    NOTE: This interface currently supports single channel input only

    http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=43

    Examples
    --------
    >>> import nipype.interfaces.spm as spm
    >>> seg = spm.NewSegment()
    >>> seg.inputs.channel_files = 'structural.nii'
    >>> seg.inputs.channel_info = (0.0001, 60, (True, True))
    >>> seg.run() # doctest: +SKIP

    For VBM pre-processing [http://www.fil.ion.ucl.ac.uk/~john/misc/VBMclass10.pdf],
    TPM.nii should be replaced by /path/to/spm8/toolbox/Seg/TPM.nii

    >>> seg = NewSegment()
    >>> seg.inputs.channel_files = 'structural.nii'
    >>> tissue1 = (('TPM.nii', 1), 2, (True,True), (False, False))
    >>> tissue2 = (('TPM.nii', 2), 2, (True,True), (False, False))
    >>> tissue3 = (('TPM.nii', 3), 2, (True,False), (False, False))
    >>> tissue4 = (('TPM.nii', 4), 2, (False,False), (False, False))
    >>> tissue5 = (('TPM.nii', 5), 2, (False,False), (False, False))
    >>> seg.inputs.tissues = [tissue1, tissue2, tissue3, tissue4, tissue5]
    >>> seg.run() # doctest: +SKIP

    """

    input_spec = NewSegmentInputSpec
    output_spec = NewSegmentOutputSpec

    def __init__(self, **inputs):
        _local_version = SPMCommand().version
        if _local_version and '12.' in _local_version:
            self._jobtype = 'spatial'
            self._jobname = 'preproc'
        else:
            self._jobtype = 'tools'
            self._jobname = 'preproc8'

        SPMCommand.__init__(self, **inputs)

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """

        if opt in ['channel_files', 'channel_info']:
            # structure have to be recreated because of some weird traits error
            new_channel = {}
            new_channel['vols'] = scans_for_fnames(self.inputs.channel_files)
            if isdefined(self.inputs.channel_info):
                info = self.inputs.channel_info
                new_channel['biasreg'] = info[0]
                new_channel['biasfwhm'] = info[1]
                new_channel['write'] = [int(info[2][0]), int(info[2][1])]
            return [new_channel]
        elif opt == 'tissues':
            new_tissues = []
            for tissue in val:
                new_tissue = {}
                new_tissue['tpm'] = np.array(
                    [','.join([tissue[0][0], str(tissue[0][1])])],
                    dtype=object)
                new_tissue['ngaus'] = tissue[1]
                new_tissue['native'] = [int(tissue[2][0]), int(tissue[2][1])]
                new_tissue['warped'] = [int(tissue[3][0]), int(tissue[3][1])]
                new_tissues.append(new_tissue)
            return new_tissues
        elif opt == 'write_deformation_fields':
            return super(NewSegment, self)._format_arg(
                opt, spec, [int(val[0]), int(val[1])])
        else:
            return super(NewSegment, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['native_class_images'] = []
        outputs['dartel_input_images'] = []
        outputs['normalized_class_images'] = []
        outputs['modulated_class_images'] = []
        outputs['transformation_mat'] = []
        outputs['bias_corrected_images'] = []
        outputs['bias_field_images'] = []
        outputs['inverse_deformation_field'] = []
        outputs['forward_deformation_field'] = []

        n_classes = 5
        if isdefined(self.inputs.tissues):
            n_classes = len(self.inputs.tissues)
        for i in range(n_classes):
            outputs['native_class_images'].append([])
            outputs['dartel_input_images'].append([])
            outputs['normalized_class_images'].append([])
            outputs['modulated_class_images'].append([])

        for filename in self.inputs.channel_files:
            pth, base, ext = split_filename(filename)
            if isdefined(self.inputs.tissues):
                for i, tissue in enumerate(self.inputs.tissues):
                    if tissue[2][0]:
                        outputs['native_class_images'][i].append(
                            os.path.join(pth, "c%d%s.nii" % (i + 1, base)))
                    if tissue[2][1]:
                        outputs['dartel_input_images'][i].append(
                            os.path.join(pth, "rc%d%s.nii" % (i + 1, base)))
                    if tissue[3][0]:
                        outputs['normalized_class_images'][i].append(
                            os.path.join(pth, "wc%d%s.nii" % (i + 1, base)))
                    if tissue[3][1]:
                        outputs['modulated_class_images'][i].append(
                            os.path.join(pth, "mwc%d%s.nii" % (i + 1, base)))
            else:
                for i in range(n_classes):
                    outputs['native_class_images'][i].append(
                        os.path.join(pth, "c%d%s.nii" % (i + 1, base)))
            outputs['transformation_mat'].append(
                os.path.join(pth, "%s_seg8.mat" % base))

            if isdefined(self.inputs.write_deformation_fields):
                if self.inputs.write_deformation_fields[0]:
                    outputs['inverse_deformation_field'].append(
                        os.path.join(pth, "iy_%s.nii" % base))
                if self.inputs.write_deformation_fields[1]:
                    outputs['forward_deformation_field'].append(
                        os.path.join(pth, "y_%s.nii" % base))

            if isdefined(self.inputs.channel_info):
                if self.inputs.channel_info[2][0]:
                    outputs['bias_corrected_images'].append(
                        os.path.join(pth, "m%s.nii" % (base)))
                if self.inputs.channel_info[2][1]:
                    outputs['bias_field_images'].append(
                        os.path.join(pth, "BiasField_%s.nii" % (base)))
        return outputs


class SmoothInputSpec(SPMCommandInputSpec):
    in_files = InputMultiPath(
        ImageFileSPM(exists=True),
        field='data',
        desc='list of files to smooth',
        mandatory=True,
        copyfile=False)
    fwhm = traits.Either(
        traits.List(traits.Float(), minlen=3, maxlen=3),
        traits.Float(),
        field='fwhm',
        desc='3-list of fwhm for each dimension')
    data_type = traits.Int(
        field='dtype', desc='Data type of the output images')
    implicit_masking = traits.Bool(
        field='im', desc=('A mask implied by a particular'
                          'voxel value'))
    out_prefix = traits.String(
        's', field='prefix', usedefault=True, desc='smoothed output prefix')


class SmoothOutputSpec(TraitedSpec):
    smoothed_files = OutputMultiPath(File(exists=True), desc='smoothed files')


class Smooth(SPMCommand):
    """Use spm_smooth for 3D Gaussian smoothing of image volumes.

    http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=55

    Examples
    --------
    >>> import nipype.interfaces.spm as spm
    >>> smooth = spm.Smooth()
    >>> smooth.inputs.in_files = 'functional.nii'
    >>> smooth.inputs.fwhm = [4, 4, 4]
    >>> smooth.run() # doctest: +SKIP
    """

    input_spec = SmoothInputSpec
    output_spec = SmoothOutputSpec
    _jobtype = 'spatial'
    _jobname = 'smooth'

    def _format_arg(self, opt, spec, val):
        if opt in ['in_files']:
            return scans_for_fnames(ensure_list(val))
        if opt == 'fwhm':
            if not isinstance(val, list):
                return [val, val, val]
            if isinstance(val, list):
                if len(val) == 1:
                    return [val[0], val[0], val[0]]
                else:
                    return val

        return super(Smooth, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['smoothed_files'] = []

        for imgf in ensure_list(self.inputs.in_files):
            outputs['smoothed_files'].append(
                fname_presuffix(imgf, prefix=self.inputs.out_prefix))
        return outputs


class DARTELInputSpec(SPMCommandInputSpec):
    image_files = traits.List(
        traits.List(ImageFileSPM(exists=True)),
        desc="A list of files to be segmented",
        field='warp.images',
        copyfile=False,
        mandatory=True)
    template_prefix = traits.Str(
        'Template',
        usedefault=True,
        field='warp.settings.template',
        desc='Prefix for template')
    regularization_form = traits.Enum(
        'Linear',
        'Membrane',
        'Bending',
        field='warp.settings.rform',
        desc=('Form of regularization energy '
              'term'))
    iteration_parameters = traits.List(
        traits.Tuple(
            traits.Range(1, 10),
            traits.Tuple(traits.Float, traits.Float, traits.Float),
            traits.Enum(1, 2, 4, 8, 16, 32, 64, 128, 256, 512),
            traits.Enum(0, 0.5, 1, 2, 4, 8, 16, 32)),
        minlen=3,
        maxlen=12,
        field='warp.settings.param',
        desc="""List of tuples for each iteration
                                       - Inner iterations
                                       - Regularization parameters
                                       - Time points for deformation model
                                       - smoothing parameter
                                       """)
    optimization_parameters = traits.Tuple(
        traits.Float,
        traits.Range(1, 8),
        traits.Range(1, 8),
        field='warp.settings.optim',
        desc="""
                                           Optimization settings a tuple
                                           - LM regularization
                                           - cycles of multigrid solver
                                           - relaxation iterations
                                           """)


class DARTELOutputSpec(TraitedSpec):
    final_template_file = File(exists=True, desc='final DARTEL template')
    template_files = traits.List(
        File(exists=True),
        desc=('Templates from different stages of '
              'iteration'))
    dartel_flow_fields = traits.List(
        File(exists=True), desc='DARTEL flow fields')


class DARTEL(SPMCommand):
    """Use spm DARTEL to create a template and flow fields

    http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=185

    Examples
    --------
    >>> import nipype.interfaces.spm as spm
    >>> dartel = spm.DARTEL()
    >>> dartel.inputs.image_files = [['rc1s1.nii','rc1s2.nii'],['rc2s1.nii', 'rc2s2.nii']]
    >>> dartel.run() # doctest: +SKIP

    """

    input_spec = DARTELInputSpec
    output_spec = DARTELOutputSpec
    _jobtype = 'tools'
    _jobname = 'dartel'

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """

        if opt in ['image_files']:
            return scans_for_fnames(val, keep4d=True, separate_sessions=True)
        elif opt == 'regularization_form':
            mapper = {'Linear': 0, 'Membrane': 1, 'Bending': 2}
            return mapper[val]
        elif opt == 'iteration_parameters':
            params = []
            for param in val:
                new_param = {}
                new_param['its'] = param[0]
                new_param['rparam'] = list(param[1])
                new_param['K'] = param[2]
                new_param['slam'] = param[3]
                params.append(new_param)
            return params
        elif opt == 'optimization_parameters':
            new_param = {}
            new_param['lmreg'] = val[0]
            new_param['cyc'] = val[1]
            new_param['its'] = val[2]
            return [new_param]
        else:
            return super(DARTEL, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['template_files'] = []
        for i in range(6):
            outputs['template_files'].append(
                os.path.realpath('%s_%d.nii' % (self.inputs.template_prefix,
                                                i + 1)))
        outputs['final_template_file'] = os.path.realpath(
            '%s_6.nii' % self.inputs.template_prefix)
        outputs['dartel_flow_fields'] = []
        for filename in self.inputs.image_files[0]:
            pth, base, ext = split_filename(filename)
            outputs['dartel_flow_fields'].append(
                os.path.realpath('u_%s_%s%s' %
                                 (base, self.inputs.template_prefix, ext)))
        return outputs


class DARTELNorm2MNIInputSpec(SPMCommandInputSpec):
    template_file = ImageFileSPM(
        exists=True,
        copyfile=False,
        mandatory=True,
        desc="DARTEL template",
        field='mni_norm.template')
    flowfield_files = InputMultiPath(
        ImageFileSPM(exists=True),
        mandatory=True,
        desc="DARTEL flow fields u_rc1*",
        field='mni_norm.data.subjs.flowfields')
    apply_to_files = InputMultiPath(
        ImageFileSPM(exists=True),
        desc="Files to apply the transform to",
        field='mni_norm.data.subjs.images',
        mandatory=True,
        copyfile=False)
    voxel_size = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        desc="Voxel sizes for output file",
        field='mni_norm.vox')
    bounding_box = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        traits.Float,
        traits.Float,
        traits.Float,
        desc="Voxel sizes for output file",
        field='mni_norm.bb')
    modulate = traits.Bool(
        field='mni_norm.preserve',
        desc=("Modulate out images - no modulation "
              "preserves concentrations"))
    fwhm = traits.Either(
        traits.List(traits.Float(), minlen=3, maxlen=3),
        traits.Float(),
        field='mni_norm.fwhm',
        desc='3-list of fwhm for each dimension')


class DARTELNorm2MNIOutputSpec(TraitedSpec):
    normalized_files = OutputMultiPath(
        File(exists=True), desc='Normalized files in MNI space')
    normalization_parameter_file = File(
        exists=True, desc=('Transform parameters to MNI '
                           'space'))


class DARTELNorm2MNI(SPMCommand):
    """Use spm DARTEL to normalize data to MNI space

    http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=188

    Examples
    --------
    >>> import nipype.interfaces.spm as spm
    >>> nm = spm.DARTELNorm2MNI()
    >>> nm.inputs.template_file = 'Template_6.nii'
    >>> nm.inputs.flowfield_files = ['u_rc1s1_Template.nii', 'u_rc1s3_Template.nii']
    >>> nm.inputs.apply_to_files = ['c1s1.nii', 'c1s3.nii']
    >>> nm.inputs.modulate = True
    >>> nm.run() # doctest: +SKIP

    """

    input_spec = DARTELNorm2MNIInputSpec
    output_spec = DARTELNorm2MNIOutputSpec
    _jobtype = 'tools'
    _jobname = 'dartel'

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt in ['template_file']:
            return np.array([val], dtype=object)
        elif opt in ['flowfield_files']:
            return scans_for_fnames(val, keep4d=True)
        elif opt in ['apply_to_files']:
            return scans_for_fnames(val, keep4d=True, separate_sessions=True)
        elif opt == 'voxel_size':
            return list(val)
        elif opt == 'bounding_box':
            return list(val)
        elif opt == 'fwhm':
            if isinstance(val, list):
                return val
            else:
                return [val, val, val]
        else:
            return super(DARTELNorm2MNI, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        pth, base, ext = split_filename(self.inputs.template_file)
        outputs['normalization_parameter_file'] = os.path.realpath(
            base + '_2mni.mat')
        outputs['normalized_files'] = []
        prefix = "w"
        if isdefined(self.inputs.modulate) and self.inputs.modulate:
            prefix = 'm' + prefix
        if not isdefined(self.inputs.fwhm) or self.inputs.fwhm > 0:
            prefix = 's' + prefix
        for filename in self.inputs.apply_to_files:
            pth, base, ext = split_filename(filename)
            outputs['normalized_files'].append(
                os.path.realpath('%s%s%s' % (prefix, base, ext)))

        return outputs


class CreateWarpedInputSpec(SPMCommandInputSpec):
    image_files = InputMultiPath(
        ImageFileSPM(exists=True),
        mandatory=True,
        desc="A list of files to be warped",
        field='crt_warped.images',
        copyfile=False)
    flowfield_files = InputMultiPath(
        ImageFileSPM(exists=True),
        copyfile=False,
        desc="DARTEL flow fields u_rc1*",
        field='crt_warped.flowfields',
        mandatory=True)
    iterations = traits.Range(
        low=0,
        high=9,
        desc=("The number of iterations: log2(number of "
              "time steps)"),
        field='crt_warped.K')
    interp = traits.Range(
        low=0,
        high=7,
        field='crt_warped.interp',
        desc='degree of b-spline used for interpolation')
    modulate = traits.Bool(
        field='crt_warped.jactransf', desc="Modulate images")


class CreateWarpedOutputSpec(TraitedSpec):
    warped_files = traits.List(File(exists=True, desc='final warped files'))


class CreateWarped(SPMCommand):
    """Apply a flow field estimated by DARTEL to create warped images

    http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=190

    Examples
    --------
    >>> import nipype.interfaces.spm as spm
    >>> create_warped = spm.CreateWarped()
    >>> create_warped.inputs.image_files = ['rc1s1.nii', 'rc1s2.nii']
    >>> create_warped.inputs.flowfield_files = ['u_rc1s1_Template.nii', 'u_rc1s2_Template.nii']
    >>> create_warped.run() # doctest: +SKIP

    """

    input_spec = CreateWarpedInputSpec
    output_spec = CreateWarpedOutputSpec
    _jobtype = 'tools'
    _jobname = 'dartel'

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """

        if opt in ['image_files']:
            return scans_for_fnames(val, keep4d=True, separate_sessions=True)
        if opt in ['flowfield_files']:
            return scans_for_fnames(val, keep4d=True)
        else:
            return super(CreateWarped, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['warped_files'] = []
        for filename in self.inputs.image_files:
            pth, base, ext = split_filename(filename)
            if isdefined(self.inputs.modulate) and self.inputs.modulate:
                outputs['warped_files'].append(
                    os.path.realpath('mw%s%s' % (base, ext)))
            else:
                outputs['warped_files'].append(
                    os.path.realpath('w%s%s' % (base, ext)))
        return outputs


class ApplyDeformationFieldInputSpec(SPMCommandInputSpec):
    in_files = InputMultiPath(
        ImageFileSPM(exists=True), mandatory=True, field='fnames')
    deformation_field = File(exists=True, mandatory=True, field='comp{1}.def')
    reference_volume = ImageFileSPM(
        exists=True, mandatory=True, field='comp{2}.id.space')
    interp = traits.Range(
        low=0,
        high=7,
        field='interp',
        desc='degree of b-spline used for interpolation')


class ApplyDeformationFieldOutputSpec(TraitedSpec):
    out_files = OutputMultiPath(File(exists=True))


class ApplyDeformations(SPMCommand):
    input_spec = ApplyDeformationFieldInputSpec
    output_spec = ApplyDeformationFieldOutputSpec

    _jobtype = 'util'
    _jobname = 'defs'

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt in ['deformation_field', 'reference_volume']:
            val = [val]

        if opt in ['deformation_field']:
            return scans_for_fnames(val, keep4d=True, separate_sessions=False)
        if opt in ['in_files', 'reference_volume']:
            return scans_for_fnames(val, keep4d=False, separate_sessions=False)

        else:
            return super(ApplyDeformations, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_files'] = []
        for filename in self.inputs.in_files:
            _, fname = os.path.split(filename)
            outputs['out_files'].append(os.path.realpath('w%s' % fname))
        return outputs


class VBMSegmentInputSpec(SPMCommandInputSpec):

    in_files = InputMultiPath(
        ImageFileSPM(exists=True),
        desc="A list of files to be segmented",
        field='estwrite.data',
        copyfile=False,
        mandatory=True)

    tissues = ImageFileSPM(
        exists=True, field='estwrite.tpm', desc='tissue probability map')
    gaussians_per_class = traits.Tuple(
        (2, 2, 2, 3, 4, 2),
        *([traits.Int()] * 6),
        usedefault=True,
        desc='number of gaussians for each tissue class')
    bias_regularization = traits.Enum(
        0.0001, (0, 0.00001, 0.0001, 0.001, 0.01, 0.1, 1, 10),
        field='estwrite.opts.biasreg',
        usedefault=True,
        desc='no(0) - extremely heavy (10)')

    bias_fwhm = traits.Enum(
        60, (30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 'Inf'),
        field='estwrite.opts.biasfwhm',
        usedefault=True,
        desc='FWHM of Gaussian smoothness of bias')
    sampling_distance = traits.Float(
        3,
        usedefault=True,
        field='estwrite.opts.samp',
        desc='Sampling distance on data for parameter estimation')
    warping_regularization = traits.Float(
        4,
        usedefault=True,
        field='estwrite.opts.warpreg',
        desc='Controls balance between parameters and data')

    spatial_normalization = traits.Enum(
        'high',
        'low',
        usedefault=True,
    )
    dartel_template = ImageFileSPM(
        exists=True, field='estwrite.extopts.dartelwarp.normhigh.darteltpm')
    use_sanlm_denoising_filter = traits.Range(
        0,
        2,
        2,
        usedefault=True,
        field='estwrite.extopts.sanlm',
        desc="0=No denoising, 1=denoising,2=denoising multi-threaded")
    mrf_weighting = traits.Float(
        0.15, usedefault=True, field='estwrite.extopts.mrf')
    cleanup_partitions = traits.Int(
        1,
        usedefault=True,
        field='estwrite.extopts.cleanup',
        desc="0=None,1=light,2=thorough")
    display_results = traits.Bool(
        True, usedefault=True, field='estwrite.extopts.print')

    gm_native = traits.Bool(
        False,
        usedefault=True,
        field='estwrite.output.GM.native',
    )
    gm_normalized = traits.Bool(
        False,
        usedefault=True,
        field='estwrite.output.GM.warped',
    )
    gm_modulated_normalized = traits.Range(
        0,
        2,
        2,
        usedefault=True,
        field='estwrite.output.GM.modulated',
        desc='0=none,1=affine+non-linear(SPM8 default),2=non-linear only')
    gm_dartel = traits.Range(
        0,
        2,
        0,
        usedefault=True,
        field='estwrite.output.GM.dartel',
        desc="0=None,1=rigid(SPM8 default),2=affine")

    wm_native = traits.Bool(
        False,
        usedefault=True,
        field='estwrite.output.WM.native',
    )
    wm_normalized = traits.Bool(
        False,
        usedefault=True,
        field='estwrite.output.WM.warped',
    )
    wm_modulated_normalized = traits.Range(
        0,
        2,
        2,
        usedefault=True,
        field='estwrite.output.WM.modulated',
        desc='0=none,1=affine+non-linear(SPM8 default),2=non-linear only')
    wm_dartel = traits.Range(
        0,
        2,
        0,
        usedefault=True,
        field='estwrite.output.WM.dartel',
        desc="0=None,1=rigid(SPM8 default),2=affine")

    csf_native = traits.Bool(
        False,
        usedefault=True,
        field='estwrite.output.CSF.native',
    )
    csf_normalized = traits.Bool(
        False,
        usedefault=True,
        field='estwrite.output.CSF.warped',
    )
    csf_modulated_normalized = traits.Range(
        0,
        2,
        2,
        usedefault=True,
        field='estwrite.output.CSF.modulated',
        desc='0=none,1=affine+non-linear(SPM8 default),2=non-linear only')
    csf_dartel = traits.Range(
        0,
        2,
        0,
        usedefault=True,
        field='estwrite.output.CSF.dartel',
        desc="0=None,1=rigid(SPM8 default),2=affine")

    bias_corrected_native = traits.Bool(
        False,
        usedefault=True,
        field='estwrite.output.bias.native',
    )
    bias_corrected_normalized = traits.Bool(
        True,
        usedefault=True,
        field='estwrite.output.bias.warped',
    )
    bias_corrected_affine = traits.Bool(
        False,
        usedefault=True,
        field='estwrite.output.bias.affine',
    )

    pve_label_native = traits.Bool(
        False, usedefault=True, field='estwrite.output.label.native')
    pve_label_normalized = traits.Bool(
        False, usedefault=True, field='estwrite.output.label.warped')
    pve_label_dartel = traits.Range(
        0,
        2,
        0,
        usedefault=True,
        field='estwrite.output.label.dartel',
        desc="0=None,1=rigid(SPM8 default),2=affine")

    jacobian_determinant = traits.Bool(
        False, usedefault=True, field='estwrite.jacobian.warped')

    deformation_field = traits.Tuple(
        (0, 0),
        traits.Bool,
        traits.Bool,
        usedefault=True,
        field='estwrite.output.warps',
        desc='forward and inverse field')


class VBMSegmentOuputSpec(TraitedSpec):

    native_class_images = traits.List(
        traits.List(File(exists=True)), desc='native space probability maps')
    dartel_input_images = traits.List(
        traits.List(File(exists=True)), desc='dartel imported class images')
    normalized_class_images = traits.List(
        traits.List(File(exists=True)), desc='normalized class images')
    modulated_class_images = traits.List(
        traits.List(File(exists=True)),
        desc=('modulated+normalized class '
              'images'))
    transformation_mat = OutputMultiPath(
        File(exists=True), desc='Normalization transformation')

    bias_corrected_images = OutputMultiPath(
        File(exists=True), desc='bias corrected images')
    normalized_bias_corrected_images = OutputMultiPath(
        File(exists=True), desc='bias corrected images')

    pve_label_native_images = OutputMultiPath(File(exists=True))
    pve_label_normalized_images = OutputMultiPath(File(exists=True))
    pve_label_registered_images = OutputMultiPath(File(exists=True))

    forward_deformation_field = OutputMultiPath(File(exists=True))
    inverse_deformation_field = OutputMultiPath(File(exists=True))

    jacobian_determinant_images = OutputMultiPath(File(exists=True))


class VBMSegment(SPMCommand):
    """Use VBM8 toolbox to separate structural images into different
    tissue classes.

    Example
    -------
    >>> import nipype.interfaces.spm as spm
    >>> seg = spm.VBMSegment()
    >>> seg.inputs.tissues = 'TPM.nii'
    >>> seg.inputs.dartel_template = 'Template_1_IXI550_MNI152.nii'
    >>> seg.inputs.bias_corrected_native = True
    >>> seg.inputs.gm_native = True
    >>> seg.inputs.wm_native = True
    >>> seg.inputs.csf_native = True
    >>> seg.inputs.pve_label_native = True
    >>> seg.inputs.deformation_field = (True, False)
    >>> seg.run() # doctest: +SKIP
    """

    input_spec = VBMSegmentInputSpec
    output_spec = VBMSegmentOuputSpec

    _jobtype = 'tools'
    _jobname = 'vbm8'

    def _list_outputs(self):
        outputs = self._outputs().get()

        do_dartel = self.inputs.spatial_normalization
        dartel_px = ''
        if do_dartel:
            dartel_px = 'r'

        outputs['native_class_images'] = [[], [], []]
        outputs['dartel_input_images'] = [[], [], []]
        outputs['normalized_class_images'] = [[], [], []]
        outputs['modulated_class_images'] = [[], [], []]

        outputs['transformation_mat'] = []

        outputs['bias_corrected_images'] = []
        outputs['normalized_bias_corrected_images'] = []

        outputs['inverse_deformation_field'] = []
        outputs['forward_deformation_field'] = []
        outputs['jacobian_determinant_images'] = []

        outputs['pve_label_native_images'] = []
        outputs['pve_label_normalized_images'] = []
        outputs['pve_label_registered_images'] = []

        for filename in self.inputs.in_files:
            pth, base, ext = split_filename(filename)

            outputs['transformation_mat'].append(
                os.path.join(pth, "%s_seg8.mat" % base))

            for i, tis in enumerate(['gm', 'wm', 'csf']):
                # native space

                if getattr(self.inputs, '%s_native' % tis):
                    outputs['native_class_images'][i].append(
                        os.path.join(pth, "p%d%s.nii" % (i + 1, base)))
                if getattr(self.inputs, '%s_dartel' % tis) == 1:
                    outputs['dartel_input_images'][i].append(
                        os.path.join(pth, "rp%d%s.nii" % (i + 1, base)))
                elif getattr(self.inputs, '%s_dartel' % tis) == 2:
                    outputs['dartel_input_images'][i].append(
                        os.path.join(pth, "rp%d%s_affine.nii" % (i + 1, base)))

            # normalized space
                if getattr(self.inputs, '%s_normalized' % tis):
                    outputs['normalized_class_images'][i].append(
                        os.path.join(pth, "w%sp%d%s.nii" % (dartel_px, i + 1,
                                                            base)))

                if getattr(self.inputs, '%s_modulated_normalized' % tis) == 1:
                    outputs['modulated_class_images'][i].append(
                        os.path.join(pth, "mw%sp%d%s.nii" % (dartel_px, i + 1,
                                                             base)))
                elif getattr(self.inputs,
                             '%s_modulated_normalized' % tis) == 2:
                    outputs['normalized_class_images'][i].append(
                        os.path.join(pth, "m0w%sp%d%s.nii" % (dartel_px, i + 1,
                                                              base)))

            if self.inputs.pve_label_native:
                outputs['pve_label_native_images'].append(
                    os.path.join(pth, "p0%s.nii" % (base)))
            if self.inputs.pve_label_normalized:
                outputs['pve_label_normalized_images'].append(
                    os.path.join(pth, "w%sp0%s.nii" % (dartel_px, base)))
            if self.inputs.pve_label_dartel == 1:
                outputs['pve_label_registered_images'].append(
                    os.path.join(pth, "rp0%s.nii" % (base)))
            elif self.inputs.pve_label_dartel == 2:
                outputs['pve_label_registered_images'].append(
                    os.path.join(pth, "rp0%s_affine.nii" % (base)))

            if self.inputs.bias_corrected_native:
                outputs['bias_corrected_images'].append(
                    os.path.join(pth, "m%s.nii" % (base)))
            if self.inputs.bias_corrected_normalized:
                outputs['normalized_bias_corrected_images'].append(
                    os.path.join(pth, "wm%s%s.nii" % (dartel_px, base)))

            if self.inputs.deformation_field[0]:
                outputs['forward_deformation_field'].append(
                    os.path.join(pth, "y_%s%s.nii" % (dartel_px, base)))
            if self.inputs.deformation_field[1]:
                outputs['inverse_deformation_field'].append(
                    os.path.join(pth, "iy_%s%s.nii" % (dartel_px, base)))

            if self.inputs.jacobian_determinant and do_dartel:
                outputs['jacobian_determinant_images'].append(
                    os.path.join(pth, "jac_wrp1%s.nii" % (base)))
        return outputs

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt in ['in_files']:
            return scans_for_fnames(val, keep4d=True)
        elif opt in ['spatial_normalization']:
            if val == 'low':
                return {'normlow': []}
        elif opt in ['dartel_template']:
            return np.array([val], dtype=object)
        elif opt in ['deformation_field']:
            return super(VBMSegment, self)._format_arg(
                opt, spec, [int(val[0]), int(val[1])])
        else:
            return super(VBMSegment, self)._format_arg(opt, spec, val)

    def _parse_inputs(self):
        if self.inputs.spatial_normalization == 'low':
            einputs = super(VBMSegment, self)._parse_inputs(
                skip=('spatial_normalization', 'dartel_template'))
            einputs[0]['estwrite']['extopts']['dartelwarp'] = {'normlow': 1}
            return einputs
        else:
            return super(VBMSegment,
                         self)._parse_inputs(skip=('spatial_normalization'))
