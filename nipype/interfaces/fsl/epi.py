# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 5.0.4.

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname(os.path.realpath(__file__))
    >>> datadir = os.path.realpath(os.path.join(filepath,
    ...                            '../../testing/data'))
    >>> os.chdir(datadir)
"""

import os
from glob import glob

import numpy as np
import nibabel as nib

from ..fsl.base import FSLCommand, FSLCommandInputSpec, Info
from ..base import (traits, TraitedSpec, InputMultiPath, File, GenFile,
                    isdefined, Undefined)
from ...utils.filemanip import (load_json, save_json, split_filename,
                                fname_presuffix)
from ... import logging
IFLOGGER = logging.getLogger('interface')


class PrepareFieldmapInputSpec(FSLCommandInputSpec):
    scanner = traits.String('SIEMENS', argstr='%s', position=1,
                            desc='must be SIEMENS', usedefault=True)
    in_phase = File(exists=True, argstr='%s', position=2, mandatory=True,
                    desc=('Phase difference map, in SIEMENS format range from '
                          '0-4096 or 0-8192)'))
    in_magnitude = File(exists=True, argstr='%s', position=3, mandatory=True,
                        desc='Magnitude difference map, brain extracted')
    delta_TE = traits.Float(2.46, usedefault=True, mandatory=True, argstr='%f',
                            position=-2,
                            desc=('echo time difference of the '
                                  'fieldmap sequence in ms. (usually 2.46ms in'
                                  ' Siemens)'))
    nocheck = traits.Bool(False, position=-1, argstr='--nocheck', usedefault=True,
                          desc=('do not perform sanity checks for image '
                                'size/range/dimensions'))
    out_fieldmap = GenFile(template='{in_phase}_fslprepared{output_type_}', argstr='%s',
                           position=4, desc='output name for prepared fieldmap')


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
    >>> prepare.cmdline #doctest: +ELLIPSIS
    'fsl_prepare_fieldmap SIEMENS phase.nii magnitude.nii \
phase_fslprepared.nii.gz 2.460000'
    >>> res = prepare.run() # doctest: +SKIP


    """
    _cmd = 'fsl_prepare_fieldmap'
    _input_spec = PrepareFieldmapInputSpec
    _output_spec = PrepareFieldmapOutputSpec

    def _run_interface(self, runtime):
        runtime = super(PrepareFieldmap, self)._run_interface(runtime)

        if runtime.returncode == 0:
            # Add an empty volume to the output, since downstream software
            # expects two GRE images to compute the difference
            out_file = self.inputs.out_fieldmap
            im = nib.load(out_file)
            dumb_img = nib.Nifti1Image(np.zeros(im.shape), im.affine,
                                       im.header)
            out_nii = nib.funcs.concat_images((im, dumb_img))
            nib.save(out_nii, out_file)

        return runtime


class TOPUPInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, mandatory=True,
                   desc='name of 4D file with images', argstr='--imain=%s')
    encoding_file = File(
        template='{in_file}_encfile.txt', hash_files=False,
        output_name='out_enc_file', mandatory=True, xor=['encoding_direction'],
        argstr='--datain=%s', desc='name of text file with PE directions/times')

    encoding_direction = traits.List(traits.Enum(
        'y', 'x', 'z', 'x-', 'y-', 'z-'), mandatory=True, xor=['encoding_file'],
        requires=['readout_times'], desc='encoding direction for automatic '
                                         'generation of encoding_file')
    readout_times = InputMultiPath(
        traits.Float, requires=['encoding_direction'], xor=['encoding_file'],
        mandatory=True, desc='readout times (dwell times by # phase-encode '
                             'steps minus 1)')

    # TODO: the following traits admit values separated by commas, one value
    # per registration level inside topup.
    warp_res = traits.Float(10.0, argstr='--warpres=%f',
                            desc=('(approximate) resolution (in mm) of warp '
                                  'basis for the different sub-sampling levels'
                                  '.'))
    subsamp = traits.Int(1, argstr='--subsamp=%d',
                         desc='sub-sampling scheme')
    fwhm = traits.Float(8.0, argstr='--fwhm=%f',
                        desc='FWHM (in mm) of gaussian smoothing kernel')
    config = traits.String('b02b0.cnf', argstr='--config=%s', usedefault=True,
                           desc=('Name of config file specifying command line '
                                 'arguments'))
    max_iter = traits.Int(5, argstr='--miter=%d',
                          desc='max # of non-linear iterations')
    reg_lambda = traits.Float(1.0, argstr='--miter=%0.f',
                              desc=('lambda weighting value of the '
                                    'regularisation term'))
    ssqlambda = traits.Enum(1, 0, argstr='--ssqlambda=%d',
                            desc=('Weight lambda by the current value of the '
                                  'ssd. If used (=1), the effective weight of '
                                  'regularisation term becomes higher for the '
                                  'initial iterations, therefore initial steps'
                                  ' are a little smoother than they would '
                                  'without weighting. This reduces the '
                                  'risk of finding a local minimum.'))
    regmod = traits.Enum('bending_energy', 'membrane_energy',
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
    estmov = traits.Enum(1, 0, argstr='--estmov=%d',
                         desc='estimate movements if set')
    minmet = traits.Enum(0, 1, argstr='--minmet=%d',
                         desc=('Minimisation method 0=Levenberg-Marquardt, '
                               '1=Scaled Conjugate Gradient'))
    splineorder = traits.Int(3, argstr='--splineorder=%d',
                             desc=('order of spline, 2->Qadratic spline, '
                                   '3->Cubic spline'))
    numprec = traits.Enum('double', 'float', argstr='--numprec=%s',
                          desc=('Precision for representing Hessian, double '
                                'or float.'))
    interp = traits.Enum('spline', 'linear', argstr='--interp=%s',
                         desc='Image interpolation model, linear or spline.')
    scale = traits.Enum(0, 1, argstr='--scale=%d',
                        desc=('If set (=1), the images are individually scaled'
                              ' to a common mean'))
    regrid = traits.Enum(1, 0, argstr='--regrid=%d',
                         desc=('If set (=1), the calculations are done in a '
                               'different grid'))

    # Outputs
    out_base = GenFile(
        template='{in_file}_base', argstr='--out=%s', hash_files=False,
        desc='base-name of output files (spline coefficients (Hz) and movement parameters)')
    out_field = GenFile(
        template='{in_file}_field{output_type_}', argstr='--fout=%s', hash_files=False,
        desc='name of image file with field (Hz)')
    out_corrected = GenFile(
        template='{in_file}_corrected{output_type_}', argstr='--iout=%s', hash_files=False,
        desc='name of 4D image file with unwarped images')
    out_logfile = GenFile(
        template='{in_file}_topup.log', argstr='--logout=%s', hash_files=False,
        desc='name of log-file')

    out_fieldcoef = GenFile(
        template='{out_base}_fieldcoef{output_type_}', hash_files=False,
        desc='file containing the field coefficients')
    out_movpar = GenFile(
        template='{out_base}_movpar.txt', hash_files=False,
        desc='file containing the field coefficients')

class TOPUPOutputSpec(TraitedSpec):
    out_fieldcoef = File(exists=True,
                         desc='file containing the field coefficients')
    out_movpar = File(exists=True, desc='movpar.txt output file')
    out_enc_file = File(desc='encoding directions file output for applytopup')
    out_field = File(desc='name of image file with field (Hz)')
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
    >>> topup.cmdline #doctest: +ELLIPSIS
    'topup --config=b02b0.cnf --datain=topup_encoding.txt \
--imain=b0_b0rev.nii --out=b0_b0rev_base --iout=b0_b0rev_corrected.nii.gz \
--fout=b0_b0rev_field.nii.gz --logout=b0_b0rev_topup.log'
    >>> res = topup.run() # doctest: +SKIP

    """
    _cmd = 'topup'
    _input_spec = TOPUPInputSpec
    _output_spec = TOPUPOutputSpec

    def _run_interface(self, runtime):
        if not os.path.isfile(self.inputs.encoding_file):
            topup_generate_encfile(
                self.inputs.readout_times,
                self.inputs.encoding_direction,
                self.inputs.encoding_file)
        return super(TOPUP, self)._run_interface(runtime)


class ApplyTOPUPInputSpec(FSLCommandInputSpec):
    in_files = InputMultiPath(File(exists=True), mandatory=True,
                              desc='name of 4D file with images',
                              argstr='--imain=%s', sep=',')
    encoding_file = File(exists=True, mandatory=True,
                         desc='name of text file with PE directions/times',
                         argstr='--datain=%s')
    in_index = traits.List(traits.Int, argstr='--inindex=%s', sep=',',
                           mandatory=True,
                           desc=('comma separated list of indicies into '
                                 '--datain of the input image (to be '
                                 'corrected)'))
    in_topup_fieldcoef = File(exists=True, argstr="--topup=%s", copyfile=False,
                              requires=['in_topup_movpar'],
                              desc=('topup file containing the field '
                                    'coefficients'))
    in_topup_movpar = File(exists=True, requires=['in_topup_fieldcoef'],
                           copyfile=False, desc='topup movpar.txt file')
    out_corrected = GenFile(
        template='{in_files[0]}_corrected{output_type_}', argstr='--out=%s',
        desc='output (warped) image')
    method = traits.Enum('jac', 'lsr', argstr='--method=%s',
                         desc=('use jacobian modulation (jac) or least-squares'
                               ' resampling (lsr)'))
    interp = traits.Enum('trilinear', 'spline', argstr='--interp=%s',
                         desc='interpolation method')
    datatype = traits.Enum('char', 'short', 'int', 'float', 'double',
                           argstr='-d=%s', desc='force output data type')


    def _format_arg(self, name, spec, value):
        if name == 'in_topup_fieldcoef':
            return spec.argstr % value.split('_fieldcoef')[0]
        return super(ApplyTOPUPInputSpec, self)._format_arg(name, spec, value)

class ApplyTOPUPOutputSpec(TraitedSpec):
    out_corrected = File(exists=True, desc=('name of 4D image file with '
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
    >>> applytopup.inputs.in_index = [1,2]
    >>> applytopup.inputs.in_topup_fieldcoef = "topup_fieldcoef.nii.gz"
    >>> applytopup.inputs.in_topup_movpar = "topup_movpar.txt"
    >>> applytopup.inputs.output_type = "NIFTI_GZ"
    >>> applytopup.cmdline #doctest: +ELLIPSIS
    'applytopup --datain=topup_encoding.txt --imain=epi.nii,epi_rev.nii \
--inindex=1,2 --topup=topup --out=epi_corrected.nii.gz'
    >>> res = applytopup.run() # doctest: +SKIP

    """
    _cmd = 'applytopup'
    _input_spec = ApplyTOPUPInputSpec
    _output_spec = ApplyTOPUPOutputSpec


class EddyInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, mandatory=True, argstr='--imain=%s',
                   desc=('File containing all the images to estimate '
                         'distortions for'))
    in_mask = File(exists=True, mandatory=True, argstr='--mask=%s',
                   desc='Mask to indicate brain')
    in_index = File(exists=True, mandatory=True, argstr='--index=%s',
                    desc=('File containing indices for all volumes in --imain '
                          'into --acqp and --topup'))
    in_acqp = File(exists=True, mandatory=True, argstr='--acqp=%s',
                   desc='File containing acquisition parameters')
    in_bvec = File(exists=True, mandatory=True, argstr='--bvecs=%s',
                   desc=('File containing the b-vectors for all volumes in '
                         '--imain'))
    in_bval = File(exists=True, mandatory=True, argstr='--bvals=%s',
                   desc=('File containing the b-values for all volumes in '
                         '--imain'))
    out_base = traits.Str('eddy_corrected', argstr='--out=%s',
                          usedefault=True,
                          desc=('basename for output (warped) image'))
    session = File(exists=True, argstr='--session=%s',
                   desc=('File containing session indices for all volumes in '
                         '--imain'))
    in_topup_fieldcoef = File(exists=True, argstr="--topup=%s",
                              requires=['in_topup_movpar'],
                              desc=('topup file containing the field '
                                    'coefficients'))
    in_topup_movpar = File(exists=True, requires=['in_topup_fieldcoef'],
                           desc='topup movpar.txt file')

    flm = traits.Enum('linear', 'quadratic', 'cubic', argstr='--flm=%s',
                      desc='First level EC model')

    fwhm = traits.Float(desc=('FWHM for conditioning filter when estimating '
                              'the parameters'), argstr='--fwhm=%s')

    niter = traits.Int(5, argstr='--niter=%s', desc='Number of iterations')

    method = traits.Enum('jac', 'lsr', argstr='--resamp=%s',
                         desc=('Final resampling method (jacobian/least '
                               'squares)'))
    repol = traits.Bool(False, argstr='--repol',
                        desc='Detect and replace outlier slices')
    num_threads = traits.Int(1, usedefault=True, nohash=True,
                             desc="Number of openmp threads to use")


class EddyOutputSpec(TraitedSpec):
    out_corrected = File(exists=True,
                         desc=('4D image file containing all the corrected '
                               'volumes'))
    out_parameter = File(exists=True,
                         desc=('text file with parameters definining the '
                               'field and movement for each scan'))


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
    >>> eddy.cmdline #doctest: +ELLIPSIS
    'eddy --acqp=epi_acqp.txt --bvals=bvals.scheme --bvecs=bvecs.scheme \
--imain=epi.nii --index=epi_index.txt --mask=epi_mask.nii \
--out=eddy_corrected'
    >>> res = eddy.run() # doctest: +SKIP

    """
    _cmd = 'eddy'
    _input_spec = EddyInputSpec
    _output_spec = EddyOutputSpec

    _num_threads = 1

    def __init__(self, **inputs):
        super(Eddy, self).__init__(**inputs)
        self.inputs.on_trait_change(self._num_threads_update, 'num_threads')

        if not isdefined(self.inputs.num_threads):
            self.inputs.num_threads = self._num_threads
        else:
            self._num_threads_update()

    def _num_threads_update(self):
        self._num_threads = self.inputs.num_threads
        if not isdefined(self.inputs.num_threads):
            if 'OMP_NUM_THREADS' in self.environ:
                del self.environ['OMP_NUM_THREADS']
        else:
            self.environ['OMP_NUM_THREADS'] = str(self.inputs.num_threads)

    def _format_arg(self, name, spec, value):
        if name == 'in_topup_fieldcoef':
            return spec.argstr % value.split('_fieldcoef')[0]
        if name == 'out_base':
            return spec.argstr % os.path.abspath(value)
        return super(Eddy, self)._format_arg(name, spec, value)

    def _post_run(self):

        self.outputs.out_corrected = os.path.abspath('%s.nii.gz' % self.inputs.out_base)
        self.outputs.out_parameter = os.path.abspath('%s.eddy_parameters' % self.inputs.out_base)


class SigLossInputSpec(FSLCommandInputSpec):
    in_file = File(mandatory=True,
                   exists=True,
                   argstr='-i %s',
                   desc='b0 fieldmap file')
    out_file = GenFile(
        template='{in_file}_sigloss{output_type_}', argstr='-s %s',
        desc='output signal loss estimate file')

    mask_file = File(exists=True,
                     argstr='-m %s',
                     desc='brain mask file')
    echo_time = traits.Float(argstr='--te=%f',
                             desc='echo time in seconds')
    slice_direction = traits.Enum('x', 'y', 'z',
                                  argstr='-d %s',
                                  desc='slicing direction')


class SigLossOuputSpec(TraitedSpec):
    out_file = File(exists=True,
                    desc='signal loss estimate file')


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
    >>> sigloss.cmdline #doctest: +ELLIPSIS
    'sigloss --te=0.030000 -i phase.nii -s phase_sigloss.nii.gz'
    >>> res = sigloss.run() # doctest: +SKIP


    """
    _input_spec = SigLossInputSpec
    _output_spec = SigLossOuputSpec
    _cmd = 'sigloss'

    def _post_run(self):

        self.outputs.out_file = self.inputs.out_file
        if ((not isdefined(self.outputs.out_file)) and
                (isdefined(self.inputs.in_file))):
            self.outputs.out_file = self._gen_fname(self.inputs.in_file,
                                                  suffix='_sigloss')

    def _gen_filename(self, name):
        if name == 'out_file':
            return self.outputs.out_file
        return None


class EpiRegInputSpec(FSLCommandInputSpec):
    epi = File(exists=True, argstr='--epi=%s', mandatory=True,
               position=-4, desc='EPI image')
    t1_head = File(exists=True, argstr='--t1=%s', mandatory=True,
                   position=-3, desc='wholehead T1 image')
    t1_brain = File(exists=True, argstr='--t1brain=%s', mandatory=True,
                    position=-2, desc='brain extracted T1 image')
    out_base = traits.String("epi2struct", desc='output base name', argstr='--out=%s',
                             position=-1, usedefault=True)
    fmap = File(exists=True, argstr='--fmap=%s',
                desc='fieldmap image (in rad/s)')
    fmapmag = File(exists=True, argstr='--fmapmag=%s',
                   desc='fieldmap magnitude image - wholehead')
    fmapmagbrain = File(exists=True, argstr='--fmapmagbrain=%s',
                        desc='fieldmap magnitude image - brain extracted')
    wmseg = File(exists=True, argstr='--wmseg=%s',
                 desc='white matter segmentation of T1 image, has to be named \
                 like the t1brain and end on _wmseg')
    echospacing = traits.Float(argstr='--echospacing=%f',
                               desc='Effective EPI echo spacing  \
                               (sometimes called dwell time) - in seconds')
    pedir = traits.Enum('x', 'y', 'z', '-x', '-y', '-z', argstr='--pedir=%s',
                        desc='phase encoding direction, dir = x/y/z/-x/-y/-z')

    weight_image = File(exists=True, argstr='--weight=%s',
                        desc='weighting image (in T1 space)')
    no_fmapreg = traits.Bool(False, usedefault=True, argstr='--nofmapreg',
                             desc='do not perform registration of fmap to T1 '
                                  '(use if fmap already registered).')
    no_clean = traits.Bool(True, argstr='--noclean', usedefault=True,
                           desc='do not clean up intermediate files')

    out_file = GenFile(template='{out_base}{output_type_}', keep_extension=False,
                       desc='output file name')
    epi2str_mat = GenFile(template='{out_base}.mat', keep_extension=False,
                          desc='rigid epi-to-structural transform')
    wmedge = GenFile(template='{out_base}_fast_wmedge{output_type_}', keep_extension=False,
                     desc='output file name')
    wmseg = GenFile(template='{out_base}_fast_wmseg{output_type_}', keep_extension=False,
                    desc='output file name')
    # Optional outputs
    out_1vol = GenFile(template='{out_base}_1vol{output_type_}', keep_extension=False,
                       desc='output file name')
    fmap2str_mat = GenFile(template='{out_base}_fieldmap2str.mat', keep_extension=False,
                       desc='output file name')
    fmap2epi_mat = GenFile(template='{out_base}_fieldmaprads2epi.mat', keep_extension=False,
                       desc='output file name')
    fmap_epi = GenFile(template='{out_base}_fieldmaprads2epi{output_type_}', keep_extension=False,
                       desc='output file name')
    fmap_str = GenFile(template='{out_base}_fieldmaprads2str{output_type_}', keep_extension=False,
                       desc='output file name')
    shiftmap = GenFile(template='{out_base}_fieldmaprads2epi_shift{output_type_}',
                       keep_extension=False, desc='output file name')
    fullwarp = GenFile(template='{out_base}_warp{output_type_}', keep_extension=False,
                       desc='output file name')
    epi2str_inv = GenFile(template='{out_base}_inv.mat', keep_extension=False,
                          desc='output file name')


class EpiRegOutputSpec(TraitedSpec):
    out_file = File(exists=True,
                    desc='unwarped and coregistered epi input')
    out_1vol = File(exists=True,
                    desc='unwarped and coregistered single volume')
    fmap2str_mat = File(exists=True,
                        desc='rigid fieldmap-to-structural transform')
    fmap2epi_mat = File(exists=True,
                        desc='rigid fieldmap-to-epi transform')
    fmap_epi = File(exists=True, desc='fieldmap in epi space')
    fmap_str = File(exists=True, desc='fieldmap in structural space')
    fmapmag_str = File(exists=True,
                       desc='fieldmap magnitude image in structural space')
    epi2str_inv = File(exists=True,
                       desc='rigid structural-to-epi transform')
    epi2str_mat = File(exists=True,
                       desc='rigid epi-to-structural transform')
    shiftmap = File(exists=True, desc='shiftmap in epi space')
    fullwarp = File(exists=True,
                    desc='warpfield to unwarp epi and transform into \
                    structural space')
    wmseg = File(exists=True, desc='white matter segmentation used in flirt bbr')
    wmedge = File(exists=True, desc='white matter edges for visualization')

    def _post_run(self):
        if self.inputs.no_fmapreg or not isdefined(self.inputs.fmap):
            self.outputs.out_1vol = Undefined
            self.outputs.fmap2str_mat = Undefined
            self.outputs.fmap2epi_mat = Undefined
            self.outputs.fmap_epi = Undefined
            self.outputs.fmap_str = Undefined
            self.outputs.fmapmag_str = Undefined
            self.outputs.shiftmap = Undefined
            self.outputs.fullwarp = Undefined
            self.outputs.epi2str_inv = Undefined


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
    >>> epireg.cmdline #doctest: +ELLIPSIS
    'epi_reg --echospacing=0.000670 --fmap=fieldmap_phase_fslprepared.nii \
--fmapmag=fieldmap_mag.nii --fmapmagbrain=fieldmap_mag_brain.nii --noclean \
--pedir=y --epi=epi.nii --t1=T1.nii --t1brain=T1_brain.nii --out=epi2struct'
    >>> epireg.run() # doctest: +SKIP

    """
    _cmd = 'epi_reg'
    _input_spec = EpiRegInputSpec
    _output_spec = EpiRegOutputSpec


# Helper functions ------------------------
def topup_generate_encfile(durations, encoding_direction, out_file):
    """Generate a topup compatible encoding file based on given directions
    """
    if len(encoding_direction) != len(durations):
        if len(durations) != 1:
            raise ValueError('Readout time must be a float or match the '
                             'length of encoding directions')
        durations = durations * len(encoding_direction)

    lines = []
    for idx, encdir in enumerate(encoding_direction):
        direction = 1.0
        if encdir.endswith('-'):
            direction = -1.0
        line = [float(val[0] == encdir[0]) * direction
                for val in ['x', 'y', 'z']] + [durations[idx]]
        lines.append(line)
    np.savetxt(out_file, np.array(lines), fmt='%d %d %d %.8f')

#######################################
# deprecated interfaces
#######################################


class EPIDeWarp(FSLCommand):
    """
    Wraps the unwarping script `epidewarp.fsl
    <http://surfer.nmr.mgh.harvard.edu/fswiki/epidewarp.fsl>`_.

    .. warning:: deprecated in FSL, please use
      :func:`nipype.workflows.dmri.preprocess.epi.sdc_fmb` instead.

    >>> from nipype.interfaces import fsl
    >>> fsl.EPIDeWarp()
    Traceback (most recent call last):
    ...
    NotImplementedError: deprecated, please use nipype.workflows.dmri.preprocess.epi.sdc_fmb instead

    """
    _cmd = 'epidewarp.fsl'

    def __init__(self, **inputs):
        raise NotImplementedError(
            'deprecated, please use nipype.workflows.dmri.preprocess.epi.sdc_fmb instead')


class EddyCorrect(FSLCommand):
    """

    .. warning:: Deprecated in FSL. Please use
      :class:`nipype.interfaces.fsl.epi.Eddy` instead

    >>> from nipype.interfaces import fsl
    >>> fsl.EddyCorrect()
    Traceback (most recent call last):
    ...
    NotImplementedError: deprecated, please use nipype.interfaces.fsl.epi.Eddy instead

    """
    _cmd = 'eddy_correct'

    def __init__(self, **inputs):
        raise NotImplementedError(
            'deprecated, please use nipype.interfaces.fsl.epi.Eddy instead')

