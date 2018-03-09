# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 5.0.4.
"""
from __future__ import print_function, division, unicode_literals, \
    absolute_import
from builtins import str

import os
import numpy as np
import nibabel as nb
import warnings

from ...utils.filemanip import split_filename
from ...utils import NUMPY_MMAP

from ..base import (traits, TraitedSpec, InputMultiPath, File, isdefined)
from .base import FSLCommand, FSLCommandInputSpec, Info


class PrepareFieldmapInputSpec(FSLCommandInputSpec):
    scanner = traits.String(
        'SIEMENS',
        argstr='%s',
        position=1,
        desc='must be SIEMENS',
        usedefault=True)
    in_phase = File(
        exists=True,
        argstr='%s',
        position=2,
        mandatory=True,
        desc=('Phase difference map, in SIEMENS format range from '
              '0-4096 or 0-8192)'))
    in_magnitude = File(
        exists=True,
        argstr='%s',
        position=3,
        mandatory=True,
        desc='Magnitude difference map, brain extracted')
    delta_TE = traits.Float(
        2.46,
        usedefault=True,
        mandatory=True,
        argstr='%f',
        position=-2,
        desc=('echo time difference of the '
              'fieldmap sequence in ms. (usually 2.46ms in'
              ' Siemens)'))
    nocheck = traits.Bool(
        False,
        position=-1,
        argstr='--nocheck',
        usedefault=True,
        desc=('do not perform sanity checks for image '
              'size/range/dimensions'))
    out_fieldmap = File(
        argstr='%s', position=4, desc='output name for prepared fieldmap')


class PrepareFieldmapOutputSpec(TraitedSpec):
    out_fieldmap = File(exists=True, desc='output name for prepared fieldmap')


class PrepareFieldmap(FSLCommand):
    """
    Interface for the fsl_prepare_fieldmap script (FSL 5.0)

    Prepares a fieldmap suitable for FEAT from SIEMENS data - saves output in
    rad/s format (e.g. ```fsl_prepare_fieldmap SIEMENS
    images_3_gre_field_mapping images_4_gre_field_mapping fmap_rads 2.65```).


    Examples
    --------

    >>> from nipype.interfaces.fsl import PrepareFieldmap
    >>> prepare = PrepareFieldmap()
    >>> prepare.inputs.in_phase = "phase.nii"
    >>> prepare.inputs.in_magnitude = "magnitude.nii"
    >>> prepare.inputs.output_type = "NIFTI_GZ"
    >>> prepare.cmdline # doctest: +ELLIPSIS
    'fsl_prepare_fieldmap SIEMENS phase.nii magnitude.nii \
.../phase_fslprepared.nii.gz 2.460000'
    >>> res = prepare.run() # doctest: +SKIP


    """
    _cmd = 'fsl_prepare_fieldmap'
    input_spec = PrepareFieldmapInputSpec
    output_spec = PrepareFieldmapOutputSpec

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []

        if not isdefined(self.inputs.out_fieldmap):
            self.inputs.out_fieldmap = self._gen_fname(
                self.inputs.in_phase, suffix='_fslprepared')

        if not isdefined(self.inputs.nocheck) or not self.inputs.nocheck:
            skip += ['nocheck']

        return super(PrepareFieldmap, self)._parse_inputs(skip=skip)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_fieldmap'] = self.inputs.out_fieldmap
        return outputs

    def _run_interface(self, runtime):
        runtime = super(PrepareFieldmap, self)._run_interface(runtime)

        if runtime.returncode == 0:
            out_file = self.inputs.out_fieldmap
            im = nb.load(out_file, mmap=NUMPY_MMAP)
            dumb_img = nb.Nifti1Image(np.zeros(im.shape), im.affine, im.header)
            out_nii = nb.funcs.concat_images((im, dumb_img))
            nb.save(out_nii, out_file)

        return runtime


class TOPUPInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        desc='name of 4D file with images',
        argstr='--imain=%s')
    encoding_file = File(
        exists=True,
        mandatory=True,
        xor=['encoding_direction'],
        desc='name of text file with PE directions/times',
        argstr='--datain=%s')
    encoding_direction = traits.List(
        traits.Enum('y', 'x', 'z', 'x-', 'y-', 'z-'),
        mandatory=True,
        xor=['encoding_file'],
        requires=['readout_times'],
        argstr='--datain=%s',
        desc=('encoding direction for automatic '
              'generation of encoding_file'))
    readout_times = InputMultiPath(
        traits.Float,
        requires=['encoding_direction'],
        xor=['encoding_file'],
        mandatory=True,
        desc=('readout times (dwell times by # '
              'phase-encode steps minus 1)'))
    out_base = File(
        desc=('base-name of output files (spline '
              'coefficients (Hz) and movement parameters)'),
        name_source=['in_file'],
        name_template='%s_base',
        argstr='--out=%s',
        hash_files=False)
    out_field = File(
        argstr='--fout=%s',
        hash_files=False,
        name_source=['in_file'],
        name_template='%s_field',
        desc='name of image file with field (Hz)')
    out_warp_prefix = traits.Str(
        "warpfield",
        argstr='--dfout=%s',
        hash_files=False,
        desc='prefix for the warpfield images (in mm)',
        usedefault=True)
    out_mat_prefix = traits.Str(
        "xfm",
        argstr='--rbmout=%s',
        hash_files=False,
        desc='prefix for the realignment matrices',
        usedefault=True)
    out_jac_prefix = traits.Str(
        "jac",
        argstr='--jacout=%s',
        hash_files=False,
        desc='prefix for the warpfield images',
        usedefault=True)
    out_corrected = File(
        argstr='--iout=%s',
        hash_files=False,
        name_source=['in_file'],
        name_template='%s_corrected',
        desc='name of 4D image file with unwarped images')
    out_logfile = File(
        argstr='--logout=%s',
        desc='name of log-file',
        name_source=['in_file'],
        name_template='%s_topup.log',
        keep_extension=True,
        hash_files=False)

    # TODO: the following traits admit values separated by commas, one value
    # per registration level inside topup.
    warp_res = traits.Float(
        10.0,
        argstr='--warpres=%f',
        desc=('(approximate) resolution (in mm) of warp '
              'basis for the different sub-sampling levels'
              '.'))
    subsamp = traits.Int(1, argstr='--subsamp=%d', desc='sub-sampling scheme')
    fwhm = traits.Float(
        8.0,
        argstr='--fwhm=%f',
        desc='FWHM (in mm) of gaussian smoothing kernel')
    config = traits.String(
        'b02b0.cnf',
        argstr='--config=%s',
        usedefault=True,
        desc=('Name of config file specifying command line '
              'arguments'))
    max_iter = traits.Int(
        5, argstr='--miter=%d', desc='max # of non-linear iterations')
    reg_lambda = traits.Float(
        1.0,
        argstr='--miter=%0.f',
        desc=('lambda weighting value of the '
              'regularisation term'))
    ssqlambda = traits.Enum(
        1,
        0,
        argstr='--ssqlambda=%d',
        desc=('Weight lambda by the current value of the '
              'ssd. If used (=1), the effective weight of '
              'regularisation term becomes higher for the '
              'initial iterations, therefore initial steps'
              ' are a little smoother than they would '
              'without weighting. This reduces the '
              'risk of finding a local minimum.'))
    regmod = traits.Enum(
        'bending_energy',
        'membrane_energy',
        argstr='--regmod=%s',
        desc=('Regularisation term implementation. Defaults '
              'to bending_energy. Note that the two functions'
              ' have vastly different scales. The membrane '
              'energy is based on the first derivatives and '
              'the bending energy on the second derivatives. '
              'The second derivatives will typically be much '
              'smaller than the first derivatives, so input '
              'lambda will have to be larger for '
              'bending_energy to yield approximately the same'
              ' level of regularisation.'))
    estmov = traits.Enum(
        1, 0, argstr='--estmov=%d', desc='estimate movements if set')
    minmet = traits.Enum(
        0,
        1,
        argstr='--minmet=%d',
        desc=('Minimisation method 0=Levenberg-Marquardt, '
              '1=Scaled Conjugate Gradient'))
    splineorder = traits.Int(
        3,
        argstr='--splineorder=%d',
        desc=('order of spline, 2->Qadratic spline, '
              '3->Cubic spline'))
    numprec = traits.Enum(
        'double',
        'float',
        argstr='--numprec=%s',
        desc=('Precision for representing Hessian, double '
              'or float.'))
    interp = traits.Enum(
        'spline',
        'linear',
        argstr='--interp=%s',
        desc='Image interpolation model, linear or spline.')
    scale = traits.Enum(
        0,
        1,
        argstr='--scale=%d',
        desc=('If set (=1), the images are individually scaled'
              ' to a common mean'))
    regrid = traits.Enum(
        1,
        0,
        argstr='--regrid=%d',
        desc=('If set (=1), the calculations are done in a '
              'different grid'))


class TOPUPOutputSpec(TraitedSpec):
    out_fieldcoef = File(
        exists=True, desc='file containing the field coefficients')
    out_movpar = File(exists=True, desc='movpar.txt output file')
    out_enc_file = File(desc='encoding directions file output for applytopup')
    out_field = File(desc='name of image file with field (Hz)')
    out_warps = traits.List(File(exists=True), desc='warpfield images')
    out_jacs = traits.List(File(exists=True), desc='Jacobian images')
    out_mats = traits.List(File(exists=True), desc='realignment matrices')
    out_corrected = File(desc='name of 4D image file with unwarped images')
    out_logfile = File(desc='name of log-file')


class TOPUP(FSLCommand):
    """
    Interface for FSL topup, a tool for estimating and correcting
    susceptibility induced distortions. See FSL documentation for
    `reference <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/TOPUP>`_,
    `usage examples
    <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup/ExampleTopupFollowedByApplytopup>`_,
    and `exemplary config files
    <https://github.com/ahheckel/FSL-scripts/blob/master/rsc/fsl/fsl4/topup/b02b0.cnf>`_.

    Examples
    --------

    >>> from nipype.interfaces.fsl import TOPUP
    >>> topup = TOPUP()
    >>> topup.inputs.in_file = "b0_b0rev.nii"
    >>> topup.inputs.encoding_file = "topup_encoding.txt"
    >>> topup.inputs.output_type = "NIFTI_GZ"
    >>> topup.cmdline # doctest: +ELLIPSIS
    'topup --config=b02b0.cnf --datain=topup_encoding.txt \
--imain=b0_b0rev.nii --out=b0_b0rev_base --iout=b0_b0rev_corrected.nii.gz \
--fout=b0_b0rev_field.nii.gz --jacout=jac --logout=b0_b0rev_topup.log \
--rbmout=xfm --dfout=warpfield'
    >>> res = topup.run() # doctest: +SKIP

    """
    _cmd = 'topup'
    input_spec = TOPUPInputSpec
    output_spec = TOPUPOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if name == 'encoding_direction':
            return trait_spec.argstr % self._generate_encfile()
        if name == 'out_base':
            path, name, ext = split_filename(value)
            if path != '':
                if not os.path.exists(path):
                    raise ValueError('out_base path must exist if provided')
        return super(TOPUP, self)._format_arg(name, trait_spec, value)

    def _list_outputs(self):
        outputs = super(TOPUP, self)._list_outputs()
        del outputs['out_base']
        base_path = None
        if isdefined(self.inputs.out_base):
            base_path, base, _ = split_filename(self.inputs.out_base)
            if base_path == '':
                base_path = None
        else:
            base = split_filename(self.inputs.in_file)[1] + '_base'
        outputs['out_fieldcoef'] = self._gen_fname(
            base, suffix='_fieldcoef', cwd=base_path)
        outputs['out_movpar'] = self._gen_fname(
            base, suffix='_movpar', ext='.txt', cwd=base_path)

        n_vols = nb.load(self.inputs.in_file).shape[-1]
        ext = Info.output_type_to_ext(self.inputs.output_type)
        fmt = os.path.abspath('{prefix}_{i:02d}{ext}').format
        outputs['out_warps'] = [
            fmt(prefix=self.inputs.out_warp_prefix, i=i, ext=ext)
            for i in range(1, n_vols + 1)
        ]
        outputs['out_jacs'] = [
            fmt(prefix=self.inputs.out_jac_prefix, i=i, ext=ext)
            for i in range(1, n_vols + 1)
        ]
        outputs['out_mats'] = [
            fmt(prefix=self.inputs.out_mat_prefix, i=i, ext=".mat")
            for i in range(1, n_vols + 1)
        ]

        if isdefined(self.inputs.encoding_direction):
            outputs['out_enc_file'] = self._get_encfilename()
        return outputs

    def _get_encfilename(self):
        out_file = os.path.join(
            os.getcwd(),
            ('%s_encfile.txt' % split_filename(self.inputs.in_file)[1]))
        return out_file

    def _generate_encfile(self):
        """Generate a topup compatible encoding file based on given directions
        """
        out_file = self._get_encfilename()
        durations = self.inputs.readout_times
        if len(self.inputs.encoding_direction) != len(durations):
            if len(self.inputs.readout_times) != 1:
                raise ValueError(('Readout time must be a float or match the'
                                  'length of encoding directions'))
            durations = durations * len(self.inputs.encoding_direction)

        lines = []
        for idx, encdir in enumerate(self.inputs.encoding_direction):
            direction = 1.0
            if encdir.endswith('-'):
                direction = -1.0
            line = [
                float(val[0] == encdir[0]) * direction
                for val in ['x', 'y', 'z']
            ] + [durations[idx]]
            lines.append(line)
        np.savetxt(out_file, np.array(lines), fmt=b'%d %d %d %.8f')
        return out_file

    def _overload_extension(self, value, name=None):
        if name == 'out_base':
            return value
        return super(TOPUP, self)._overload_extension(value, name)


class ApplyTOPUPInputSpec(FSLCommandInputSpec):
    in_files = InputMultiPath(
        File(exists=True),
        mandatory=True,
        desc='name of file with images',
        argstr='--imain=%s',
        sep=',')
    encoding_file = File(
        exists=True,
        mandatory=True,
        desc='name of text file with PE directions/times',
        argstr='--datain=%s')
    in_index = traits.List(
        traits.Int,
        argstr='--inindex=%s',
        sep=',',
        desc='comma separated list of indices corresponding to --datain')
    in_topup_fieldcoef = File(
        exists=True,
        argstr="--topup=%s",
        copyfile=False,
        requires=['in_topup_movpar'],
        desc=('topup file containing the field '
              'coefficients'))
    in_topup_movpar = File(
        exists=True,
        requires=['in_topup_fieldcoef'],
        copyfile=False,
        desc='topup movpar.txt file')
    out_corrected = File(
        desc='output (warped) image',
        name_source=['in_files'],
        name_template='%s_corrected',
        argstr='--out=%s')
    method = traits.Enum(
        'jac',
        'lsr',
        argstr='--method=%s',
        desc=('use jacobian modulation (jac) or least-squares'
              ' resampling (lsr)'))
    interp = traits.Enum(
        'trilinear',
        'spline',
        argstr='--interp=%s',
        desc='interpolation method')
    datatype = traits.Enum(
        'char',
        'short',
        'int',
        'float',
        'double',
        argstr='-d=%s',
        desc='force output data type')


class ApplyTOPUPOutputSpec(TraitedSpec):
    out_corrected = File(
        exists=True, desc=('name of 4D image file with '
                           'unwarped images'))


class ApplyTOPUP(FSLCommand):
    """
    Interface for FSL topup, a tool for estimating and correcting
    susceptibility induced distortions.
    `General reference
    <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup/ApplytopupUsersGuide>`_
    and `use example
    <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup/ExampleTopupFollowedByApplytopup>`_.


    Examples
    --------

    >>> from nipype.interfaces.fsl import ApplyTOPUP
    >>> applytopup = ApplyTOPUP()
    >>> applytopup.inputs.in_files = ["epi.nii", "epi_rev.nii"]
    >>> applytopup.inputs.encoding_file = "topup_encoding.txt"
    >>> applytopup.inputs.in_topup_fieldcoef = "topup_fieldcoef.nii.gz"
    >>> applytopup.inputs.in_topup_movpar = "topup_movpar.txt"
    >>> applytopup.inputs.output_type = "NIFTI_GZ"
    >>> applytopup.cmdline # doctest: +ELLIPSIS
    'applytopup --datain=topup_encoding.txt --imain=epi.nii,epi_rev.nii \
--inindex=1,2 --topup=topup --out=epi_corrected.nii.gz'
    >>> res = applytopup.run() # doctest: +SKIP

    """
    _cmd = 'applytopup'
    input_spec = ApplyTOPUPInputSpec
    output_spec = ApplyTOPUPOutputSpec

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []

        # If not defined, assume index are the first N entries in the
        # parameters file, for N input images.
        if not isdefined(self.inputs.in_index):
            self.inputs.in_index = list(
                range(1,
                      len(self.inputs.in_files) + 1))

        return super(ApplyTOPUP, self)._parse_inputs(skip=skip)

    def _format_arg(self, name, spec, value):
        if name == 'in_topup_fieldcoef':
            return spec.argstr % value.split('_fieldcoef')[0]
        return super(ApplyTOPUP, self)._format_arg(name, spec, value)


class EddyInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr='--imain=%s',
        desc=('File containing all the images to estimate '
              'distortions for'))
    in_mask = File(
        exists=True,
        mandatory=True,
        argstr='--mask=%s',
        desc='Mask to indicate brain')
    in_index = File(
        exists=True,
        mandatory=True,
        argstr='--index=%s',
        desc=('File containing indices for all volumes in --imain '
              'into --acqp and --topup'))
    in_acqp = File(
        exists=True,
        mandatory=True,
        argstr='--acqp=%s',
        desc='File containing acquisition parameters')
    in_bvec = File(
        exists=True,
        mandatory=True,
        argstr='--bvecs=%s',
        desc=('File containing the b-vectors for all volumes in '
              '--imain'))
    in_bval = File(
        exists=True,
        mandatory=True,
        argstr='--bvals=%s',
        desc=('File containing the b-values for all volumes in '
              '--imain'))
    out_base = traits.Str(
        'eddy_corrected',
        argstr='--out=%s',
        usedefault=True,
        desc=('basename for output (warped) image'))
    session = File(
        exists=True,
        argstr='--session=%s',
        desc=('File containing session indices for all volumes in '
              '--imain'))
    in_topup_fieldcoef = File(
        exists=True,
        argstr="--topup=%s",
        requires=['in_topup_movpar'],
        desc=('topup file containing the field '
              'coefficients'))
    in_topup_movpar = File(
        exists=True,
        requires=['in_topup_fieldcoef'],
        desc='topup movpar.txt file')

    flm = traits.Enum(
        'linear',
        'quadratic',
        'cubic',
        argstr='--flm=%s',
        desc='First level EC model')

    slm = traits.Enum(
        'none',
        'linear',
        'quadratic',
        argstr='--slm=%s',
        desc='Second level EC model')

    fep = traits.Bool(
        False, argstr='--fep', desc='Fill empty planes in x- or y-directions')

    interp = traits.Enum(
        'spline',
        'trilinear',
        argstr='--interp=%s',
        desc='Interpolation model for estimation step')

    nvoxhp = traits.Int(
        1000,
        argstr='--nvoxhp=%s',
        desc=('# of voxels used to estimate the '
              'hyperparameters'))

    fudge_factor = traits.Float(
        10.0,
        argstr='--ff=%s',
        desc=('Fudge factor for hyperparameter '
              'error variance'))

    dont_sep_offs_move = traits.Bool(
        False,
        argstr='--dont_sep_offs_move',
        desc=('Do NOT attempt to separate '
              'field offset from subject '
              'movement'))

    dont_peas = traits.Bool(
        False,
        argstr='--dont_peas',
        desc="Do NOT perform a post-eddy alignment of "
        "shells")

    fwhm = traits.Float(
        desc=('FWHM for conditioning filter when estimating '
              'the parameters'),
        argstr='--fwhm=%s')

    niter = traits.Int(5, argstr='--niter=%s', desc='Number of iterations')

    method = traits.Enum(
        'jac',
        'lsr',
        argstr='--resamp=%s',
        desc=('Final resampling method (jacobian/least '
              'squares)'))
    repol = traits.Bool(
        False, argstr='--repol', desc='Detect and replace outlier slices')
    num_threads = traits.Int(
        1,
        usedefault=True,
        nohash=True,
        desc="Number of openmp threads to use")
    is_shelled = traits.Bool(
        False,
        argstr='--data_is_shelled',
        desc="Override internal check to ensure that "
        "date are acquired on a set of b-value "
        "shells")
    field = traits.Str(
        argstr='--field=%s',
        desc="NonTOPUP fieldmap scaled in Hz - filename has "
        "to be provided without an extension. TOPUP is "
        "strongly recommended")
    field_mat = File(
        exists=True,
        argstr='--field_mat=%s',
        desc="Matrix that specifies the relative locations of "
        "the field specified by --field and first volume "
        "in file --imain")
    use_cuda = traits.Bool(False, desc="Run eddy using cuda gpu")


class EddyOutputSpec(TraitedSpec):
    out_corrected = File(
        exists=True, desc='4D image file containing all the corrected volumes')
    out_parameter = File(
        exists=True,
        desc=('text file with parameters definining the field and'
              'movement for each scan'))
    out_rotated_bvecs = File(
        exists=True, desc='File containing rotated b-values for all volumes')
    out_movement_rms = File(
        exists=True, desc='Summary of the "total movement" in each volume')
    out_restricted_movement_rms = File(
        exists=True,
        desc=('Summary of the "total movement" in each volume '
              'disregarding translation in the PE direction'))
    out_shell_alignment_parameters = File(
        exists=True,
        desc=('File containing rigid body movement parameters '
              'between the different shells as estimated by a '
              'post-hoc mutual information based registration'))
    out_outlier_report = File(
        exists=True,
        desc=('Text-file with a plain language report on what '
              'outlier slices eddy has found'))


class Eddy(FSLCommand):
    """
    Interface for FSL eddy, a tool for estimating and correcting eddy
    currents induced distortions. `User guide
    <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/Eddy/UsersGuide>`_ and
    `more info regarding acqp file
    <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/Faq#How_do_I_know_what_to_put_into_my_--acqp_file>`_.

    Examples
    --------

    >>> from nipype.interfaces.fsl import Eddy
    >>> eddy = Eddy()
    >>> eddy.inputs.in_file = 'epi.nii'
    >>> eddy.inputs.in_mask  = 'epi_mask.nii'
    >>> eddy.inputs.in_index = 'epi_index.txt'
    >>> eddy.inputs.in_acqp  = 'epi_acqp.txt'
    >>> eddy.inputs.in_bvec  = 'bvecs.scheme'
    >>> eddy.inputs.in_bval  = 'bvals.scheme'
    >>> eddy.inputs.use_cuda = True
    >>> eddy.cmdline # doctest: +ELLIPSIS
    'eddy_cuda --acqp=epi_acqp.txt --bvals=bvals.scheme --bvecs=bvecs.scheme \
--imain=epi.nii --index=epi_index.txt --mask=epi_mask.nii \
--out=.../eddy_corrected'
    >>> eddy.inputs.use_cuda = False
    >>> eddy.cmdline # doctest: +ELLIPSIS
    'eddy_openmp --acqp=epi_acqp.txt --bvals=bvals.scheme \
--bvecs=bvecs.scheme --imain=epi.nii --index=epi_index.txt \
--mask=epi_mask.nii --out=.../eddy_corrected'
    >>> res = eddy.run() # doctest: +SKIP

    """
    _cmd = 'eddy_openmp'
    input_spec = EddyInputSpec
    output_spec = EddyOutputSpec

    _num_threads = 1

    def __init__(self, **inputs):
        super(Eddy, self).__init__(**inputs)
        self.inputs.on_trait_change(self._num_threads_update, 'num_threads')
        if not isdefined(self.inputs.num_threads):
            self.inputs.num_threads = self._num_threads
        else:
            self._num_threads_update()
        self.inputs.on_trait_change(self._use_cuda, 'use_cuda')
        if isdefined(self.inputs.use_cuda):
            self._use_cuda()

    def _num_threads_update(self):
        self._num_threads = self.inputs.num_threads
        if not isdefined(self.inputs.num_threads):
            if 'OMP_NUM_THREADS' in self.inputs.environ:
                del self.inputs.environ['OMP_NUM_THREADS']
        else:
            self.inputs.environ['OMP_NUM_THREADS'] = str(
                self.inputs.num_threads)

    def _use_cuda(self):
        self._cmd = 'eddy_cuda' if self.inputs.use_cuda else 'eddy_openmp'

    def _run_interface(self, runtime):
        # If 'eddy_openmp' is missing, use 'eddy'
        FSLDIR = os.getenv('FSLDIR', '')
        cmd = self._cmd
        if all((FSLDIR != '', cmd == 'eddy_openmp',
                not os.path.exists(os.path.join(FSLDIR, 'bin', cmd)))):
            self._cmd = 'eddy'
        runtime = super(Eddy, self)._run_interface(runtime)

        # Restore command to avoid side-effects
        self._cmd = cmd
        return runtime

    def _format_arg(self, name, spec, value):
        if name == 'in_topup_fieldcoef':
            return spec.argstr % value.split('_fieldcoef')[0]
        if name == 'out_base':
            return spec.argstr % os.path.abspath(value)
        return super(Eddy, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_corrected'] = os.path.abspath(
            '%s.nii.gz' % self.inputs.out_base)
        outputs['out_parameter'] = os.path.abspath(
            '%s.eddy_parameters' % self.inputs.out_base)

        # File generation might depend on the version of EDDY
        out_rotated_bvecs = os.path.abspath(
            '%s.eddy_rotated_bvecs' % self.inputs.out_base)
        out_movement_rms = os.path.abspath(
            '%s.eddy_movement_rms' % self.inputs.out_base)
        out_restricted_movement_rms = os.path.abspath(
            '%s.eddy_restricted_movement_rms' % self.inputs.out_base)
        out_shell_alignment_parameters = os.path.abspath(
            '%s.eddy_post_eddy_shell_alignment_parameters' %
            self.inputs.out_base)
        out_outlier_report = os.path.abspath(
            '%s.eddy_outlier_report' % self.inputs.out_base)

        if os.path.exists(out_rotated_bvecs):
            outputs['out_rotated_bvecs'] = out_rotated_bvecs
        if os.path.exists(out_movement_rms):
            outputs['out_movement_rms'] = out_movement_rms
        if os.path.exists(out_restricted_movement_rms):
            outputs['out_restricted_movement_rms'] = \
                out_restricted_movement_rms
        if os.path.exists(out_shell_alignment_parameters):
            outputs['out_shell_alignment_parameters'] = \
                out_shell_alignment_parameters
        if os.path.exists(out_outlier_report):
            outputs['out_outlier_report'] = out_outlier_report

        return outputs


class SigLossInputSpec(FSLCommandInputSpec):
    in_file = File(
        mandatory=True, exists=True, argstr='-i %s', desc='b0 fieldmap file')
    out_file = File(
        argstr='-s %s', desc='output signal loss estimate file', genfile=True)

    mask_file = File(exists=True, argstr='-m %s', desc='brain mask file')
    echo_time = traits.Float(argstr='--te=%f', desc='echo time in seconds')
    slice_direction = traits.Enum(
        'x', 'y', 'z', argstr='-d %s', desc='slicing direction')


class SigLossOuputSpec(TraitedSpec):
    out_file = File(exists=True, desc='signal loss estimate file')


class SigLoss(FSLCommand):
    """
    Estimates signal loss from a field map (in rad/s)

    Examples
    --------

    >>> from nipype.interfaces.fsl import SigLoss
    >>> sigloss = SigLoss()
    >>> sigloss.inputs.in_file = "phase.nii"
    >>> sigloss.inputs.echo_time = 0.03
    >>> sigloss.inputs.output_type = "NIFTI_GZ"
    >>> sigloss.cmdline # doctest: +ELLIPSIS
    'sigloss --te=0.030000 -i phase.nii -s .../phase_sigloss.nii.gz'
    >>> res = sigloss.run() # doctest: +SKIP


    """
    input_spec = SigLossInputSpec
    output_spec = SigLossOuputSpec
    _cmd = 'sigloss'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if ((not isdefined(outputs['out_file']))
                and (isdefined(self.inputs.in_file))):
            outputs['out_file'] = self._gen_fname(
                self.inputs.in_file, suffix='_sigloss')
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        return None


class EpiRegInputSpec(FSLCommandInputSpec):
    epi = File(
        exists=True,
        argstr='--epi=%s',
        mandatory=True,
        position=-4,
        desc='EPI image')
    t1_head = File(
        exists=True,
        argstr='--t1=%s',
        mandatory=True,
        position=-3,
        desc='wholehead T1 image')
    t1_brain = File(
        exists=True,
        argstr='--t1brain=%s',
        mandatory=True,
        position=-2,
        desc='brain extracted T1 image')
    out_base = traits.String(
        "epi2struct",
        desc='output base name',
        argstr='--out=%s',
        position=-1,
        usedefault=True)
    fmap = File(
        exists=True, argstr='--fmap=%s', desc='fieldmap image (in rad/s)')
    fmapmag = File(
        exists=True,
        argstr='--fmapmag=%s',
        desc='fieldmap magnitude image - wholehead')
    fmapmagbrain = File(
        exists=True,
        argstr='--fmapmagbrain=%s',
        desc='fieldmap magnitude image - brain extracted')
    wmseg = File(
        exists=True,
        argstr='--wmseg=%s',
        desc='white matter segmentation of T1 image, has to be named \
                 like the t1brain and end on _wmseg')
    echospacing = traits.Float(
        argstr='--echospacing=%f',
        desc='Effective EPI echo spacing  \
                               (sometimes called dwell time) - in seconds')
    pedir = traits.Enum(
        'x',
        'y',
        'z',
        '-x',
        '-y',
        '-z',
        argstr='--pedir=%s',
        desc='phase encoding direction, dir = x/y/z/-x/-y/-z')

    weight_image = File(
        exists=True,
        argstr='--weight=%s',
        desc='weighting image (in T1 space)')
    no_fmapreg = traits.Bool(
        False,
        argstr='--nofmapreg',
        desc='do not perform registration of fmap to T1 \
                        (use if fmap already registered)')
    no_clean = traits.Bool(
        True,
        argstr='--noclean',
        usedefault=True,
        desc='do not clean up intermediate files')


class EpiRegOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='unwarped and coregistered epi input')
    out_1vol = File(
        exists=True, desc='unwarped and coregistered single volume')
    fmap2str_mat = File(
        exists=True, desc='rigid fieldmap-to-structural transform')
    fmap2epi_mat = File(exists=True, desc='rigid fieldmap-to-epi transform')
    fmap_epi = File(exists=True, desc='fieldmap in epi space')
    fmap_str = File(exists=True, desc='fieldmap in structural space')
    fmapmag_str = File(
        exists=True, desc='fieldmap magnitude image in structural space')
    epi2str_inv = File(exists=True, desc='rigid structural-to-epi transform')
    epi2str_mat = File(exists=True, desc='rigid epi-to-structural transform')
    shiftmap = File(exists=True, desc='shiftmap in epi space')
    fullwarp = File(
        exists=True,
        desc='warpfield to unwarp epi and transform into \
                    structural space')
    wmseg = File(
        exists=True, desc='white matter segmentation used in flirt bbr')
    wmedge = File(exists=True, desc='white matter edges for visualization')


class EpiReg(FSLCommand):
    """

    Runs FSL epi_reg script for simultaneous coregistration and fieldmap
    unwarping.

    Examples
    --------

    >>> from nipype.interfaces.fsl import EpiReg
    >>> epireg = EpiReg()
    >>> epireg.inputs.epi='epi.nii'
    >>> epireg.inputs.t1_head='T1.nii'
    >>> epireg.inputs.t1_brain='T1_brain.nii'
    >>> epireg.inputs.out_base='epi2struct'
    >>> epireg.inputs.fmap='fieldmap_phase_fslprepared.nii'
    >>> epireg.inputs.fmapmag='fieldmap_mag.nii'
    >>> epireg.inputs.fmapmagbrain='fieldmap_mag_brain.nii'
    >>> epireg.inputs.echospacing=0.00067
    >>> epireg.inputs.pedir='y'
    >>> epireg.cmdline # doctest: +ELLIPSIS
    'epi_reg --echospacing=0.000670 --fmap=fieldmap_phase_fslprepared.nii \
--fmapmag=fieldmap_mag.nii --fmapmagbrain=fieldmap_mag_brain.nii --noclean \
--pedir=y --epi=epi.nii --t1=T1.nii --t1brain=T1_brain.nii --out=epi2struct'
    >>> epireg.run() # doctest: +SKIP

    """
    _cmd = 'epi_reg'
    input_spec = EpiRegInputSpec
    output_spec = EpiRegOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.join(os.getcwd(),
                                           self.inputs.out_base + '.nii.gz')
        if (not (isdefined(self.inputs.no_fmapreg) and self.inputs.no_fmapreg)
                and isdefined(self.inputs.fmap)):
            outputs['out_1vol'] = os.path.join(
                os.getcwd(), self.inputs.out_base + '_1vol.nii.gz')
            outputs['fmap2str_mat'] = os.path.join(
                os.getcwd(), self.inputs.out_base + '_fieldmap2str.mat')
            outputs['fmap2epi_mat'] = os.path.join(
                os.getcwd(), self.inputs.out_base + '_fieldmaprads2epi.mat')
            outputs['fmap_epi'] = os.path.join(
                os.getcwd(), self.inputs.out_base + '_fieldmaprads2epi.nii.gz')
            outputs['fmap_str'] = os.path.join(
                os.getcwd(), self.inputs.out_base + '_fieldmaprads2str.nii.gz')
            outputs['fmapmag_str'] = os.path.join(
                os.getcwd(), self.inputs.out_base + '_fieldmap2str.nii.gz')
            outputs['shiftmap'] = os.path.join(
                os.getcwd(),
                self.inputs.out_base + '_fieldmaprads2epi_shift.nii.gz')
            outputs['fullwarp'] = os.path.join(
                os.getcwd(), self.inputs.out_base + '_warp.nii.gz')
            outputs['epi2str_inv'] = os.path.join(
                os.getcwd(), self.inputs.out_base + '_inv.mat')

        outputs['epi2str_mat'] = os.path.join(os.getcwd(),
                                              self.inputs.out_base + '.mat')
        outputs['wmedge'] = os.path.join(
            os.getcwd(), self.inputs.out_base + '_fast_wmedge.nii.gz')
        outputs['wmseg'] = os.path.join(
            os.getcwd(), self.inputs.out_base + '_fast_wmseg.nii.gz')

        return outputs


#######################################
# deprecated interfaces
#######################################


class EPIDeWarpInputSpec(FSLCommandInputSpec):
    mag_file = File(
        exists=True,
        desc='Magnitude file',
        argstr='--mag %s',
        position=0,
        mandatory=True)
    dph_file = File(
        exists=True,
        desc='Phase file assumed to be scaled from 0 to 4095',
        argstr='--dph %s',
        mandatory=True)
    exf_file = File(
        exists=True,
        desc='example func volume (or use epi)',
        argstr='--exf %s')
    epi_file = File(
        exists=True, desc='EPI volume to unwarp', argstr='--epi %s')
    tediff = traits.Float(
        2.46,
        usedefault=True,
        desc='difference in B0 field map TEs',
        argstr='--tediff %s')
    esp = traits.Float(
        0.58, desc='EPI echo spacing', argstr='--esp %s', usedefault=True)
    sigma = traits.Int(
        2,
        usedefault=True,
        argstr='--sigma %s',
        desc="2D spatial gaussing smoothing \
                       stdev (default = 2mm)")
    vsm = traits.String(
        genfile=True, desc='voxel shift map', argstr='--vsm %s')
    exfdw = traits.String(
        desc='dewarped example func volume', genfile=True, argstr='--exfdw %s')
    epidw = traits.String(
        desc='dewarped epi volume', genfile=False, argstr='--epidw %s')
    tmpdir = traits.String(genfile=True, desc='tmpdir', argstr='--tmpdir %s')
    nocleanup = traits.Bool(
        True, usedefault=True, desc='no cleanup', argstr='--nocleanup')
    cleanup = traits.Bool(desc='cleanup', argstr='--cleanup')


class EPIDeWarpOutputSpec(TraitedSpec):
    unwarped_file = File(desc="unwarped epi file")
    vsm_file = File(desc="voxel shift map")
    exfdw = File(desc="dewarped functional volume example")
    exf_mask = File(desc="Mask from example functional volume")


class EPIDeWarp(FSLCommand):
    """
    Wraps the unwarping script `epidewarp.fsl
    <http://surfer.nmr.mgh.harvard.edu/fswiki/epidewarp.fsl>`_.

    .. warning:: deprecated in FSL, please use
      :func:`nipype.workflows.dmri.preprocess.epi.sdc_fmb` instead.

    Examples
    --------

    >>> from nipype.interfaces.fsl import EPIDeWarp
    >>> dewarp = EPIDeWarp()
    >>> dewarp.inputs.epi_file = "functional.nii"
    >>> dewarp.inputs.mag_file = "magnitude.nii"
    >>> dewarp.inputs.dph_file = "phase.nii"
    >>> dewarp.inputs.output_type = "NIFTI_GZ"
    >>> dewarp.cmdline # doctest: +ELLIPSIS
    'epidewarp.fsl --mag magnitude.nii --dph phase.nii --epi functional.nii \
--esp 0.58 --exfdw .../exfdw.nii.gz --nocleanup --sigma 2 --tediff 2.46 \
--tmpdir .../temp --vsm .../vsm.nii.gz'
    >>> res = dewarp.run() # doctest: +SKIP


    """
    _cmd = 'epidewarp.fsl'
    input_spec = EPIDeWarpInputSpec
    output_spec = EPIDeWarpOutputSpec

    def __init__(self, **inputs):
        warnings.warn(("Deprecated: Please use "
                       "nipype.workflows.dmri.preprocess.epi.sdc_fmb instead"),
                      DeprecationWarning)
        return super(EPIDeWarp, self).__init__(**inputs)

    def _run_interface(self, runtime):
        runtime = super(EPIDeWarp, self)._run_interface(runtime)
        if runtime.stderr:
            self.raise_exception(runtime)
        return runtime

    def _gen_filename(self, name):
        if name == 'exfdw':
            if isdefined(self.inputs.exf_file):
                return self._gen_fname(self.inputs.exf_file, suffix="_exfdw")
            else:
                return self._gen_fname("exfdw")
        if name == 'epidw':
            if isdefined(self.inputs.epi_file):
                return self._gen_fname(self.inputs.epi_file, suffix="_epidw")
        if name == 'vsm':
            return self._gen_fname('vsm')
        if name == 'tmpdir':
            return os.path.join(os.getcwd(), 'temp')
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.exfdw):
            outputs['exfdw'] = self._gen_filename('exfdw')
        else:
            outputs['exfdw'] = self.inputs.exfdw
        if isdefined(self.inputs.epi_file):
            if isdefined(self.inputs.epidw):
                outputs['unwarped_file'] = self.inputs.epidw
            else:
                outputs['unwarped_file'] = self._gen_filename('epidw')
        if not isdefined(self.inputs.vsm):
            outputs['vsm_file'] = self._gen_filename('vsm')
        else:
            outputs['vsm_file'] = self._gen_fname(self.inputs.vsm)
        if not isdefined(self.inputs.tmpdir):
            outputs['exf_mask'] = self._gen_fname(
                cwd=self._gen_filename('tmpdir'), basename='maskexf')
        else:
            outputs['exf_mask'] = self._gen_fname(
                cwd=self.inputs.tmpdir, basename='maskexf')
        return outputs


class EddyCorrectInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        desc='4D input file',
        argstr='%s',
        position=0,
        mandatory=True)
    out_file = File(
        desc='4D output file',
        argstr='%s',
        position=1,
        name_source=['in_file'],
        name_template='%s_edc',
        output_name='eddy_corrected')
    ref_num = traits.Int(
        0,
        argstr='%d',
        position=2,
        desc='reference number',
        mandatory=True,
        usedefault=True)


class EddyCorrectOutputSpec(TraitedSpec):
    eddy_corrected = File(
        exists=True, desc='path/name of 4D eddy corrected output file')


class EddyCorrect(FSLCommand):
    """

    .. warning:: Deprecated in FSL. Please use
      :class:`nipype.interfaces.fsl.epi.Eddy` instead

    Example
    -------

    >>> from nipype.interfaces.fsl import EddyCorrect
    >>> eddyc = EddyCorrect(in_file='diffusion.nii',
    ...                     out_file="diffusion_edc.nii", ref_num=0)
    >>> eddyc.cmdline
    'eddy_correct diffusion.nii diffusion_edc.nii 0'

    """
    _cmd = 'eddy_correct'
    input_spec = EddyCorrectInputSpec
    output_spec = EddyCorrectOutputSpec

    def __init__(self, **inputs):
        warnings.warn(("Deprecated: Please use nipype.interfaces.fsl.epi.Eddy "
                       "instead"), DeprecationWarning)
        return super(EddyCorrect, self).__init__(**inputs)

    def _run_interface(self, runtime):
        runtime = super(EddyCorrect, self)._run_interface(runtime)
        if runtime.stderr:
            self.raise_exception(runtime)
        return runtime
