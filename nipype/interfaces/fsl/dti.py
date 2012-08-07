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

import os
import shutil
import warnings

from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec, Info
from nipype.interfaces.base import (TraitedSpec, isdefined, File, Directory,
                                    InputMultiPath, OutputMultiPath, traits)
from nipype.utils.filemanip import fname_presuffix, split_filename, copyfile

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class DTIFitInputSpec(FSLCommandInputSpec):

    dwi = File(exists=True, desc='diffusion weighted image data file',
                  argstr='-k %s', position=0, mandatory=True)
    base_name = traits.Str("dtifit_", desc='base_name that all output files will start with',
                           argstr='-o %s', position=1, usedefault=True)
    mask = File(exists=True, desc='bet binary mask file',
                argstr='-m %s', position=2, mandatory=True)
    bvecs = File(exists=True, desc='b vectors file',
                argstr='-r %s', position=3, mandatory=True)
    bvals = File(exists=True, desc='b values file',
                argstr='-b %s', position=4, mandatory=True)
    min_z = traits.Int(argstr='-z %d', desc='min z')
    max_z = traits.Int(argstr='-Z %d', desc='max z')
    min_y = traits.Int(argstr='-y %d', desc='min y')
    max_y = traits.Int(argstr='-Y %d', desc='max y')
    min_x = traits.Int(argstr='-x %d', desc='min x')
    max_x = traits.Int(argstr='-X %d', desc='max x')
    save_tensor = traits.Bool(desc='save the elements of the tensor',
                        argstr='--save_tensor')
    sse = traits.Bool(desc='output sum of squared errors', argstr='--sse')
    cni = File(exists=True, desc='input counfound regressors', argstr='-cni %s')
    little_bit = traits.Bool(desc='only process small area of brain',
                             argstr='--littlebit')


class DTIFitOutputSpec(TraitedSpec):

    V1 = File(exists=True, desc='path/name of file with the 1st eigenvector')
    V2 = File(exists=True, desc='path/name of file with the 2nd eigenvector')
    V3 = File(exists=True, desc='path/name of file with the 3rd eigenvector')
    L1 = File(exists=True, desc='path/name of file with the 1st eigenvalue')
    L2 = File(exists=True, desc='path/name of file with the 2nd eigenvalue')
    L3 = File(exists=True, desc='path/name of file with the 3rd eigenvalue')
    MD = File(exists=True, desc='path/name of file with the mean diffusivity')
    FA = File(exists=True, desc='path/name of file with the fractional anisotropy')
    MO = File(exists=True, desc='path/name of file with the mode of anisotropy')
    S0 = File(exists=True, desc='path/name of file with the raw T2 signal with no ' +
                                'diffusion weighting')
    tensor = File(exists=True, desc='path/name of file with the 4D tensor volume')


class DTIFit(FSLCommand):
    """ Use FSL  dtifit command for fitting a diffusion tensor model at each
    voxel

    Example
    -------

    >>> from nipype.interfaces import fsl
    >>> dti = fsl.DTIFit()
    >>> dti.inputs.dwi = 'diffusion.nii'
    >>> dti.inputs.bvecs = 'bvecs'
    >>> dti.inputs.bvals = 'bvals'
    >>> dti.inputs.base_name = 'TP'
    >>> dti.inputs.mask = 'mask.nii'
    >>> dti.cmdline
    'dtifit -k diffusion.nii -o TP -m mask.nii -r bvecs -b bvals'

    """

    _cmd = 'dtifit'
    input_spec = DTIFitInputSpec
    output_spec = DTIFitOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for k in outputs.keys():
            if k not in ('outputtype', 'environ', 'args'):
                if k != 'tensor' or (isdefined(self.inputs.save_tensor)
                                          and self.inputs.save_tensor):
                    outputs[k] = self._gen_fname(self.inputs.base_name, suffix='_' + k)
        return outputs


class EddyCorrectInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, desc='4D input file', argstr='%s', position=0, mandatory=True)
    out_file = File(desc='4D output file', argstr='%s', position=1, genfile=True, hash_files=False)
    ref_num = traits.Int(argstr='%d', position=2, desc='reference number', mandatory=True)


class EddyCorrectOutputSpec(TraitedSpec):
    eddy_corrected = File(exists=True, desc='path/name of 4D eddy corrected output file')


class EddyCorrect(FSLCommand):
    """  Deprecated! Please use create_eddy_correct_pipeline instead

    Example
    -------

    >>> from nipype.interfaces import fsl
    >>> eddyc = fsl.EddyCorrect(in_file='diffusion.nii', out_file="diffusion_edc.nii", ref_num=0)
    >>> eddyc.cmdline
    'eddy_correct diffusion.nii diffusion_edc.nii 0'

    """
    _cmd = 'eddy_correct'
    input_spec = EddyCorrectInputSpec
    output_spec = EddyCorrectOutputSpec

    def __init__(self, **inputs):
        warnings.warn("Deprecated: Please use create_eddy_correct_pipeline instead", DeprecationWarning)
        return super(EddyCorrect, self).__init__(**inputs)

    def _run_interface(self, runtime):
        if not isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_fname(self.inputs.in_file, suffix='_edc')
        runtime = super(EddyCorrect, self)._run_interface(runtime)
        if runtime.stderr:
            self.raise_exception(runtime)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['eddy_corrected'] = self.inputs.out_file
        if not isdefined(outputs['eddy_corrected']):
            outputs['eddy_corrected'] = self._gen_fname(self.inputs.in_file, suffix='_edc')
        outputs['eddy_corrected'] = os.path.abspath(outputs['eddy_corrected'])
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._list_outputs()['eddy_corrected']
        else:
            return None


class BEDPOSTXInputSpec(FSLCommandInputSpec):
    dwi = File(exists=True, desc='diffusion weighted image data file', mandatory=True)
    mask = File(exists=True, desc='bet binary mask file', mandatory=True)
    bvecs = File(exists=True, desc='b vectors file', mandatory=True)
    bvals = File(exists=True, desc='b values file', mandatory=True)
    bpx_directory = Directory('bedpostx', argstr='%s', usedefault=True,
                             desc='the name for this subject''s bedpostx folder')

    fibres = traits.Int(1, argstr='-n %d', desc='number of fibres per voxel')
    weight = traits.Float(1.00, argstr='-w %.2f',
                          desc='ARD weight, more weight means less' +
                               ' secondary fibres per voxel')
    burn_period = traits.Int(1000, argstr='-b %d', desc='burnin period')
    jumps = traits.Int(1250, argstr='-j %d', desc='number of jumps')
    sampling = traits.Int(25, argstr='-s %d', desc='sample every')


class BEDPOSTXOutputSpec(TraitedSpec):
    bpx_out_directory = Directory(exists=True, field='dir',
                                  desc='path/name of directory with all ' +
                                       'bedpostx output files for this subject')
    xfms_directory = Directory(exists=True, field='dir',
                              desc='path/name of directory with the ' +
                                   'tranformation matrices')
    merged_thsamples = traits.List(File, exists=True,
                                   desc='a list of path/name of 4D volume ' +
                                        'with samples from the distribution ' +
                                        'on theta')
    merged_phsamples = traits.List(File, exists=True,
                                   desc='a list of path/name of file with '
                                        'samples from the distribution on phi')
    merged_fsamples = traits.List(File, exists=True,
                                   desc='a list of path/name of 4D volume ' +
                                        'with samples from the distribution ' +
                                        'on anisotropic volume fraction')
    mean_thsamples = traits.List(File, exists=True,
                                 desc='a list of path/name of 3D volume with mean of distribution on theta')
    mean_phsamples = traits.List(File, exists=True,
                                 desc='a list of path/name of 3D volume with mean of distribution on phi')
    mean_fsamples = traits.List(File, exists=True,
                                 desc='a list of path/name of 3D volume with mean of distribution on f anisotropy')
    dyads = traits.List(File, exists=True,  desc='a list of path/name of mean of PDD distribution in vector form')


class BEDPOSTX(FSLCommand):
    """ Deprecated! Please use create_bedpostx_pipeline instead

    Example
    -------

    >>> from nipype.interfaces import fsl
    >>> bedp = fsl.BEDPOSTX(bpx_directory='subjdir', bvecs='bvecs', bvals='bvals', dwi='diffusion.nii', \
    mask='mask.nii', fibres=1)
    >>> bedp.cmdline
    'bedpostx subjdir -n 1'

    """

    _cmd = 'bedpostx'
    input_spec = BEDPOSTXInputSpec
    output_spec = BEDPOSTXOutputSpec
    _can_resume = True

    def __init__(self, **inputs):
        warnings.warn("Deprecated: Please use create_bedpostx_pipeline instead", DeprecationWarning)
        return super(BEDPOSTX, self).__init__(**inputs)

    def _run_interface(self, runtime):

        #create the subject specific bpx_directory
        bpx_directory = os.path.join(os.getcwd(), self.inputs.bpx_directory)
        self.inputs.bpx_directory = bpx_directory
        if not os.path.exists(bpx_directory):
            os.makedirs(bpx_directory)

            _, _, ext = split_filename(self.inputs.mask)
            shutil.copyfile(self.inputs.mask,
                            os.path.join(self.inputs.bpx_directory,
                                         'nodif_brain_mask' + ext))
            _, _, ext = split_filename(self.inputs.dwi)
            shutil.copyfile(self.inputs.dwi,
                            os.path.join(self.inputs.bpx_directory, 'data' + ext))
            shutil.copyfile(self.inputs.bvals,
                            os.path.join(self.inputs.bpx_directory, 'bvals'))
            shutil.copyfile(self.inputs.bvecs,
                            os.path.join(self.inputs.bpx_directory, 'bvecs'))

        runtime = super(BEDPOSTX, self)._run_interface(runtime)
        if runtime.stderr:
            self.raise_exception(runtime)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['bpx_out_directory'] = os.path.join(os.getcwd(),
                                    self.inputs.bpx_directory + '.bedpostX')
        outputs['xfms_directory'] = os.path.join(os.getcwd(),
                                    self.inputs.bpx_directory + '.bedpostX',
                                    'xfms')

        for k in outputs.keys():
            if k not in ('outputtype', 'environ', 'args', 'bpx_out_directory',
                         'xfms_directory'):
                outputs[k] = []

        for n in range(self.inputs.fibres):
            outputs['merged_thsamples'].append(self._gen_fname('merged_th' + repr(n + 1)
                                                               + 'samples', suffix='',
                                               cwd=outputs['bpx_out_directory']))
            outputs['merged_phsamples'].append(self._gen_fname('merged_ph' + repr(n + 1)
                                                               + 'samples', suffix='',
                                                               cwd=outputs['bpx_out_directory']))
            outputs['merged_fsamples'].append(self._gen_fname('merged_f' + repr(n + 1)
                                                              + 'samples', suffix='',
                                                              cwd=outputs['bpx_out_directory']))
            outputs['mean_thsamples'].append(self._gen_fname('mean_th' + repr(n + 1)
                                                              + 'samples', suffix='',
                                                              cwd=outputs['bpx_out_directory']))
            outputs['mean_phsamples'].append(self._gen_fname('mean_ph' + repr(n + 1)
                                                             + 'samples', suffix='',
                                                             cwd=outputs['bpx_out_directory']))
            outputs['mean_fsamples'].append(self._gen_fname('mean_f' + repr(n + 1)
                                                            + 'samples', suffix='',
                                                            cwd=outputs['bpx_out_directory']))
            outputs['dyads'].append(self._gen_fname('dyads' + repr(n + 1),
                                                            suffix='',
                                                            cwd=outputs['bpx_out_directory']))
        return outputs


class ProbTrackXInputSpec(FSLCommandInputSpec):
    thsamples = InputMultiPath(File(exists=True), mandatory=True)
    phsamples = InputMultiPath(File(exists=True), mandatory=True)
    fsamples = InputMultiPath(File(exists=True), mandatory=True)
    samples_base_name = traits.Str("merged", desc='the rootname/base_name for samples files',
                                   argstr='--samples=%s', usedefault=True)
    mask = File(exists=True, desc='bet binary mask file in diffusion space',
                    argstr='-m %s', mandatory=True)
    seed = traits.Either(File(exists=True), traits.List(File(exists=True)),
                         traits.List(traits.List(traits.Int(), minlen=3, maxlen=3)),
                         desc='seed volume(s), or voxel(s)' +
                         'or freesurfer label file',
                         argstr='--seed=%s', mandatory=True)
    mode = traits.Enum("simple", "two_mask_symm", "seedmask",
                       desc='options: simple (single seed voxel), seedmask (mask of seed voxels), '
                            + 'twomask_symm (two bet binary masks) ',
                       argstr='--mode=%s', genfile=True)
    target_masks = InputMultiPath(File(exits=True), desc='list of target masks - ' +
                       'required for seeds_to_targets classification', argstr='--targetmasks=%s')
    mask2 = File(exists=True, desc='second bet binary mask (in diffusion space) in twomask_symm mode',
                 argstr='--mask2=%s')
    waypoints = File(exists=True, desc='waypoint mask or ascii list of waypoint masks - ' +
                     'only keep paths going through ALL the masks', argstr='--waypoints=%s')
    network = traits.Bool(desc='activate network mode - only keep paths going through ' +
                          'at least one seed mask (required if multiple seed masks)',
                          argstr='--network')
    mesh = File(exists=True, desc='Freesurfer-type surface descriptor (in ascii format)',
                argstr='--mesh=%s')
    seed_ref = File(exists=True, desc='reference vol to define seed space in ' +
                   'simple mode - diffusion space assumed if absent',
                   argstr='--seedref=%s')
    out_dir = Directory(exists=True, argstr='--dir=%s',
                       desc='directory to put the final volumes in', genfile=True)
    force_dir = traits.Bool(True, desc='use the actual directory name given - i.e. ' +
                            'do not add + to make a new directory', argstr='--forcedir',
                            usedefault=True)
    opd = traits.Bool(True, desc='outputs path distributions', argstr='--opd', usedefault=True)
    correct_path_distribution = traits.Bool(desc='correct path distribution for the length of the pathways',
                                            argstr='--pd')
    os2t = traits.Bool(desc='Outputs seeds to targets', argstr='--os2t')
    #paths_file = File('nipype_fdtpaths', usedefault=True, argstr='--out=%s',
    #                 desc='produces an output file (default is fdt_paths)')
    avoid_mp = File(exists=True, desc='reject pathways passing through locations given by this mask',
                    argstr='--avoid=%s')
    stop_mask = File(exists=True, argstr='--stop=%s',
                      desc='stop tracking at locations given by this mask file')
    xfm = File(exists=True, argstr='--xfm=%s',
               desc='transformation matrix taking seed space to DTI space ' +
                '(either FLIRT matrix or FNIRT warp_field) - default is identity')
    inv_xfm = File(argstr='--invxfm=%s', desc='transformation matrix taking DTI space to seed' +
                    ' space (compulsory when using a warp_field for seeds_to_dti)')
    n_samples = traits.Int(5000, argstr='--nsamples=%d',
                           desc='number of samples - default=5000', usedefault=True)
    n_steps = traits.Int(argstr='--nsteps=%d', desc='number of steps per sample - default=2000')
    dist_thresh = traits.Float(argstr='--distthresh=%.3f', desc='discards samples shorter than ' +
                              'this threshold (in mm - default=0)')
    c_thresh = traits.Float(argstr='--cthr=%.3f', desc='curvature threshold - default=0.2')
    sample_random_points = traits.Bool(argstr='--sampvox', desc='sample random points within seed voxels')
    step_length = traits.Float(argstr='--steplength=%.3f', desc='step_length in mm - default=0.5')
    loop_check = traits.Bool(argstr='--loopcheck', desc='perform loop_checks on paths -' +
                            ' slower, but allows lower curvature threshold')
    use_anisotropy = traits.Bool(argstr='--usef', desc='use anisotropy to constrain tracking')
    rand_fib = traits.Enum(0, 1, 2, 3, argstr='--randfib %d',
                           desc='options: 0 - default, 1 - to randomly sample' +
                            ' initial fibres (with f > fibthresh), 2 - to sample in ' +
                            'proportion fibres (with f>fibthresh) to f, 3 - to sample ALL ' +
                            'populations at random (even if f<fibthresh)')
    fibst = traits.Int(argstr='--fibst=%d', desc='force a starting fibre for tracking - ' +
                       'default=1, i.e. first fibre orientation. Only works if randfib==0')
    mod_euler = traits.Bool(argstr='--modeuler', desc='use modified euler streamlining')
    random_seed = traits.Bool(argstr='--rseed', desc='random seed')
    s2tastext = traits.Bool(argstr='--s2tastext', desc='output seed-to-target counts as a' +
                            ' text file (useful when seeding from a mesh)')
    verbose = traits.Enum(0, 1, 2, desc="Verbose level, [0-2]." +
                          "Level 2 is required to output particle files.",
                          argstr="--verbose=%d")


class ProbTrackXOutputSpec(TraitedSpec):
    log = File(exists=True, desc='path/name of a text record of the command that was run')
    fdt_paths = OutputMultiPath(File(exists=True), desc='path/name of a 3D image file containing the output ' +
                     'connectivity distribution to the seed mask')
    way_total = File(exists=True, desc='path/name of a text file containing a single number ' +
                    'corresponding to the total number of generated tracts that ' +
                    'have not been rejected by inclusion/exclusion mask criteria')
    targets = traits.List(File, exists=True, desc='a list with all generated seeds_to_target files')
    particle_files = traits.List(File, exists=True, desc='Files describing ' +
                                 'all of the tract samples. Generated only if ' +
                                 'verbose is set to 2')


class ProbTrackX(FSLCommand):
    """ Use FSL  probtrackx for tractography on bedpostx results

    Examples
    --------

    >>> from nipype.interfaces import fsl
    >>> pbx = fsl.ProbTrackX(samples_base_name='merged', mask='mask.nii', \
    seed='MASK_average_thal_right.nii', mode='seedmask', \
    xfm='trans.mat', n_samples=3, n_steps=10, force_dir=True, opd=True, os2t=True, \
    target_masks = ['targets_MASK1.nii', 'targets_MASK2.nii'], \
    thsamples='merged_thsamples.nii', fsamples='merged_fsamples.nii', phsamples='merged_phsamples.nii', \
    out_dir='.')
    >>> pbx.cmdline
    'probtrackx --forcedir -m mask.nii --mode=seedmask --nsamples=3 --nsteps=10 --opd --os2t --dir=. --samples=merged --seed=MASK_average_thal_right.nii --targetmasks=targets.txt --xfm=trans.mat'

    """

    _cmd = 'probtrackx'
    input_spec = ProbTrackXInputSpec
    output_spec = ProbTrackXOutputSpec

    def __init__(self, **inputs):
        warnings.warn("Deprecated: Please use create_bedpostx_pipeline instead", DeprecationWarning)
        return super(ProbTrackX, self).__init__(**inputs)

    def _run_interface(self, runtime):
        for i in range(1, len(self.inputs.thsamples) + 1):
            _, _, ext = split_filename(self.inputs.thsamples[i - 1])
            copyfile(self.inputs.thsamples[i - 1],
                     self.inputs.samples_base_name + "_th%dsamples" % i + ext,
                     copy=False)
            _, _, ext = split_filename(self.inputs.thsamples[i - 1])
            copyfile(self.inputs.phsamples[i - 1],
                     self.inputs.samples_base_name + "_ph%dsamples" % i + ext,
                     copy=False)
            _, _, ext = split_filename(self.inputs.thsamples[i - 1])
            copyfile(self.inputs.fsamples[i - 1],
                     self.inputs.samples_base_name + "_f%dsamples" % i + ext,
                     copy=False)

        if isdefined(self.inputs.target_masks):
            f = open("targets.txt", "w")
            for target in self.inputs.target_masks:
                f.write("%s\n" % target)
            f.close()
        if isinstance(self.inputs.seed, list):
            f = open("seeds.txt", "w")
            for seed in self.inputs.seed:
                if isinstance(seed, list):
                    f.write("%s\n" % (" ".join([str(s) for s in seed])))
                else:
                    f.write("%s\n" % seed)
            f.close()

        runtime = super(ProbTrackX, self)._run_interface(runtime)
        if runtime.stderr:
            self.raise_exception(runtime)
        return runtime

    def _format_arg(self, name, spec, value):
        if name == 'target_masks' and isdefined(value):
            fname = "targets.txt"
            return super(ProbTrackX, self)._format_arg(name, spec, [fname])
        elif name == 'seed' and isinstance(value, list):
            fname = "seeds.txt"
            return super(ProbTrackX, self)._format_arg(name, spec, fname)
        else:
            return super(ProbTrackX, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_dir):
            out_dir = self._gen_filename("out_dir")
        else:
            out_dir = self.inputs.out_dir

        outputs['log'] = os.path.abspath(os.path.join(out_dir, 'probtrackx.log'))
        #utputs['way_total'] = os.path.abspath(os.path.join(out_dir, 'waytotal'))
        if isdefined(self.inputs.opd == True):
            if isinstance(self.inputs.seed, list) and isinstance(self.inputs.seed[0], list):
                outputs['fdt_paths'] = []
                for seed in self.inputs.seed:
                    outputs['fdt_paths'].append(
                            os.path.abspath(
                                self._gen_fname("fdt_paths_%s" % ("_".join([str(s) for s in seed])),
                                                cwd=out_dir, suffix='')))
            else:
                outputs['fdt_paths'] = os.path.abspath(self._gen_fname("fdt_paths",
                                               cwd=out_dir, suffix=''))

        # handle seeds-to-target output files
        if isdefined(self.inputs.target_masks):
            outputs['targets'] = []
            for target in self.inputs.target_masks:
                outputs['targets'].append(os.path.abspath(
                                                self._gen_fname('seeds_to_' + os.path.split(target)[1],
                                                cwd=out_dir,
                                                suffix='')))
        if isdefined(self.inputs.verbose) and self.inputs.verbose == 2:
            outputs['particle_files'] = [os.path.abspath(
                                            os.path.join(out_dir, 'particle%d' % i))
                                            for i in range(self.inputs.n_samples)]
        return outputs

    def _gen_filename(self, name):
        if name == "out_dir":
            return os.getcwd()
        elif name == "mode":
            if isinstance(self.inputs.seed, list) and isinstance(self.inputs.seed[0], list):
                return "simple"
            else:
                return "seedmask"


class VecRegInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, argstr='-i %s', desc='filename for input vector or tensor field',
                  mandatory=True)
    out_file = File(argstr='-o %s', desc='filename for output registered vector or tensor field',
                   genfile=True, hash_files=False)
    ref_vol = File(exists=True, argstr='-r %s', desc='filename for reference (target) volume',
                  mandatory=True)
    affine_mat = File(exists=True, argstr='-t %s',
                      desc='filename for affine transformation matrix')
    warp_field = File(exists=True, argstr='-w %s',
                      desc='filename for 4D warp field for nonlinear registration')
    rotation_mat = File(exists=True, argstr='--rotmat=%s',
                        desc='filename for secondary affine matrix' +
                  'if set, this will be used for the rotation of the vector/tensor field')
    rotation_warp = File(exists=True, argstr='--rotwarp=%s',
                         desc='filename for secondary warp field' +
                   'if set, this will be used for the rotation of the vector/tensor field')
    interpolation = traits.Enum("nearestneighbour", "trilinear", "sinc", "spline",
                                argstr='--interp=%s',
                                desc='interpolation method : ' +
                                     'nearestneighbour, trilinear (default), sinc or spline')
    mask = File(exists=True, argstr='-m %s', desc='brain mask in input space')
    ref_mask = File(exists=True, argstr='--refmask=%s', desc='brain mask in output space ' +
                    '(useful for speed up of nonlinear reg)')


class VecRegOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='path/name of filename for the registered vector or tensor field')


class VecReg(FSLCommand):
    """Use FSL vecreg for registering vector data
    For complete details, see the FDT Documentation
    <http://www.fmrib.ox.ac.uk/fsl/fdt/fdt_vecreg.html>

    Example
    -------

    >>> from nipype.interfaces import fsl
    >>> vreg = fsl.VecReg(in_file='diffusion.nii', \
                 affine_mat='trans.mat', \
                 ref_vol='mni.nii', \
                 out_file='diffusion_vreg.nii')
    >>> vreg.cmdline
    'vecreg -t trans.mat -i diffusion.nii -o diffusion_vreg.nii -r mni.nii'

    """

    _cmd = 'vecreg'
    input_spec = VecRegInputSpec
    output_spec = VecRegOutputSpec

    def _run_interface(self, runtime):
        if not isdefined(self.inputs.out_file):
            pth, base_name = os.path.split(self.inputs.in_file)
            self.inputs.out_file = self._gen_fname(base_name, cwd=os.path.abspath(pth),
                                                   suffix='_vreg')
        return super(VecReg, self)._run_interface(runtime)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(outputs['out_file']) and isdefined(self.inputs.in_file):
            pth, base_name = os.path.split(self.inputs.in_file)
            outputs['out_file'] = self._gen_fname(base_name, cwd=os.path.abspath(pth),
                                                 suffix='_vreg')
        outputs['out_file'] = os.path.abspath(outputs['out_file'])
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._list_outputs()[name]
        else:
            return None


class ProjThreshInputSpec(FSLCommandInputSpec):
    in_files = traits.List(File, exists=True, argstr='%s',
                           desc='a list of input volumes',
                           mandatory=True, position=0)
    threshold = traits.Int(argstr='%d', desc='threshold indicating minimum ' +
                           'number of seed voxels entering this mask region',
                           mandatory=True, position=1)


class ProjThreshOuputSpec(TraitedSpec):
    out_files = traits.List(File, exists=True, desc='path/name of output volume after thresholding')


class ProjThresh(FSLCommand):
    """Use FSL proj_thresh for thresholding some outputs of probtrack
    For complete details, see the FDT Documentation
    <http://www.fmrib.ox.ac.uk/fsl/fdt/fdt_thresh.html>

    Example
    -------

    >>> from nipype.interfaces import fsl
    >>> ldir = ['seeds_to_M1.nii', 'seeds_to_M2.nii']
    >>> pThresh = fsl.ProjThresh(in_files=ldir, threshold=3)
    >>> pThresh.cmdline
    'proj_thresh seeds_to_M1.nii seeds_to_M2.nii 3'

    """

    _cmd = 'proj_thresh'
    input_spec = ProjThreshInputSpec
    output_spec = ProjThreshOuputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_files'] = []
        for name in self.inputs.in_files:
            cwd, base_name = os.path.split(name)
            outputs['out_files'].append(self._gen_fname(base_name, cwd=cwd,
                                                        suffix='_proj_seg_thr_' +
                                                               repr(self.inputs.threshold)))
        return outputs


class FindTheBiggestInputSpec(FSLCommandInputSpec):
    in_files = traits.List(File, exists=True, argstr='%s', desc='a list of input volumes or a singleMatrixFile',
                          position=0, mandatory=True)
    out_file = File(argstr='%s', desc='file with the resulting segmentation', position=2, genfile=True, hash_files=False)


class FindTheBiggestOutputSpec(TraitedSpec):
    out_file = File(exists=True, argstr='%s', desc='output file indexed in order of input files')


class FindTheBiggest(FSLCommand):
    """
    Use FSL find_the_biggest for performing hard segmentation on
    the outputs of connectivity-based thresholding in probtrack.
    For complete details, see the `FDT
    Documentation. <http://www.fmrib.ox.ac.uk/fsl/fdt/fdt_biggest.html>`_

    Example
    -------

    >>> from nipype.interfaces import fsl
    >>> ldir = ['seeds_to_M1.nii', 'seeds_to_M2.nii']
    >>> fBig = fsl.FindTheBiggest(in_files=ldir, out_file='biggestSegmentation')
    >>> fBig.cmdline
    'find_the_biggest seeds_to_M1.nii seeds_to_M2.nii biggestSegmentation'

    """
    _cmd = 'find_the_biggest'
    input_spec = FindTheBiggestInputSpec
    output_spec = FindTheBiggestOutputSpec

    def _run_interface(self, runtime):
        if not isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_fname('biggestSegmentation', suffix='')
        return super(FindTheBiggest, self)._run_interface(runtime)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(outputs['out_file']):
            outputs['out_file'] = self._gen_fname('biggestSegmentation', suffix='')
        outputs['out_file'] = os.path.abspath(outputs['out_file'])
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._list_outputs()[name]
        else:
            return None


class TractSkeletonInputSpec(FSLCommandInputSpec):

    in_file = File(exists=True, mandatory=True, argstr="-i %s",
                   desc="input image (typcially mean FA volume)")
    _proj_inputs = ["threshold", "distance_map", "data_file"]
    project_data = traits.Bool(argstr="-p %.3f %s %s %s %s", requires=_proj_inputs,
                               desc="project data onto skeleton")
    threshold = traits.Float(desc="skeleton threshold value")
    distance_map = File(exists=True, desc="distance map image")
    search_mask_file = File(exists=True, xor=["use_cingulum_mask"],
                            desc="mask in which to use alternate search rule")
    use_cingulum_mask = traits.Bool(True, usedefault=True,
                                    xor=["search_mask_file"],
                                    desc="perform alternate search using built-in cingulum mask")
    data_file = File(exists=True, desc="4D data to project onto skeleton (usually FA)")
    alt_data_file = File(exists=True, argstr="-a %s", desc="4D non-FA data to project onto skeleton")
    alt_skeleton = File(exists=True, argstr="-s %s", desc="alternate skeleton to use")
    projected_data = File(desc="input data projected onto skeleton")
    skeleton_file = traits.Either(traits.Bool, File, argstr="-o %s", desc="write out skeleton image")


class TractSkeletonOutputSpec(TraitedSpec):

    projected_data = File(desc="input data projected onto skeleton")
    skeleton_file = File(desc="tract skeleton image")


class TractSkeleton(FSLCommand):
    """Use FSL's tbss_skeleton to skeletonise an FA image or project arbitrary values onto a skeleton.

    There are two ways to use this interface.  To create a skeleton from an FA image, just
    supply the ``in_file`` and set ``skeleton_file`` to True (or specify a skeleton filename.
    To project values onto a skeleton, you must set ``project_data`` to True, and then also
    supply values for ``threshold``, ``distance_map``, and ``data_file``. The ``search_mask_file``
    and ``use_cingulum_mask`` inputs are also used in data projection, but ``use_cingulum_mask``
    is set to True by default.  This mask controls where the projection algorithm searches
    within a circular space around a tract, rather than in a single perpindicular direction.

    Example
    -------

    >>> import nipype.interfaces.fsl as fsl
    >>> skeletor = fsl.TractSkeleton()
    >>> skeletor.inputs.in_file = "all_FA.nii.gz"
    >>> skeletor.inputs.skeleton_file = True
    >>> skeletor.run() # doctest: +SKIP

    """

    _cmd = "tbss_skeleton"
    input_spec = TractSkeletonInputSpec
    output_spec = TractSkeletonOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "project_data":
            if isdefined(value) and value:
                _si = self.inputs
                if isdefined(_si.use_cingulum_mask) and _si.use_cingulum_mask:
                    mask_file = Info.standard_image("LowerCingulum_1mm.nii.gz")
                else:
                    mask_file = _si.search_mask_file
                if not isdefined(_si.projected_data):
                    proj_file = self._list_outputs()["projected_data"]
                else:
                    proj_file = _si.projected_data
                return spec.argstr % (_si.threshold, _si.distance_map, mask_file, _si.data_file, proj_file)
        elif name == "skeleton_file":
            if isinstance(value, bool):
                return spec.argstr % self._list_outputs()["skeleton_file"]
            else:
                return spec.argstr % value
        return super(TractSkeleton, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        _si = self.inputs
        if isdefined(_si.project_data) and _si.project_data:
            proj_data = _si.projected_data
            outputs["projected_data"] = proj_data
            if not isdefined(proj_data):
                stem = _si.data_file
                if isdefined(_si.alt_data_file):
                    stem = _si.alt_data_file
                outputs["projected_data"] = fname_presuffix(stem,
                                                            suffix="_skeletonised",
                                                            newpath=os.getcwd(),
                                                            use_ext=True)
        if isdefined(_si.skeleton_file) and _si.skeleton_file:
            outputs["skeleton_file"] = _si.skeleton_file
            if isinstance(_si.skeleton_file, bool):
                outputs["skeleton_file"] = fname_presuffix(_si.in_file,
                                                           suffix="_skeleton",
                                                           newpath=os.getcwd(),
                                                           use_ext=True)
        return outputs


class DistanceMapInputSpec(FSLCommandInputSpec):

    in_file = File(exists=True, mandatory=True, argstr="--in=%s",
                   desc="image to calculate distance values for")
    mask_file = File(exists=True, argstr="--mask=%s",
                     desc="binary mask to contrain calculations")
    invert_input = traits.Bool(argstr="--invert", desc="invert input image")
    local_max_file = traits.Either(traits.Bool, File, argstr="--localmax=%s",
                                   desc="write an image of the local maxima", hash_files=False)
    distance_map = File(genfile=True, argstr="--out=%s", desc="distance map to write", hash_files=False)


class DistanceMapOutputSpec(TraitedSpec):

    distance_map = File(exists=True, desc="value is distance to nearest nonzero voxels")
    local_max_file = File(desc="image of local maxima")


class DistanceMap(FSLCommand):
    """Use FSL's distancemap to generate a map of the distance to the nearest nonzero voxel.

    Example
    -------

    >>> import nipype.interfaces.fsl as fsl
    >>> mapper = fsl.DistanceMap()
    >>> mapper.inputs.in_file = "skeleton_mask.nii.gz"
    >>> mapper.run() # doctest: +SKIP

    """

    _cmd = "distancemap"
    input_spec = DistanceMapInputSpec
    output_spec = DistanceMapOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "local_max_file":
            if isinstance(value, bool):
                return spec.argstr % self._list_outputs()["local_max_file"]
        return super(DistanceMap, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        _si = self.inputs
        outputs["distance_map"] = _si.distance_map
        if not isdefined(_si.distance_map):
            outputs["distance_map"] = fname_presuffix(_si.in_file,
                                                      suffix="_dstmap",
                                                      use_ext=True,
                                                      newpath=os.getcwd())
        outputs["distance_map"] = os.path.abspath(outputs["distance_map"])
        if isdefined(_si.local_max_file):
            outputs["local_max_file"] = _si.local_max_file
            if isinstance(_si.local_max_file, bool):
                outputs["local_max_file"] = fname_presuffix(_si.in_file,
                                                           suffix="_lclmax",
                                                           use_ext=True,
                                                           newpath=os.getcwd())
            outputs["local_max_file"] = os.path.abspath(outputs["local_max_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "distance_map":
            return self._list_outputs()["distance_map"]
        return None


class XFibresInputSpec(FSLCommandInputSpec):
    dwi = File(exists=True, argstr="--data=%s", mandatory=True)
    mask = File(exists=True, argstr="--mask=%s", mandatory=True)
    bvecs = File(exists=True, argstr="--bvecs=%s", mandatory=True)
    bvals = File(exists=True, argstr="--bvals=%s", mandatory=True)
    logdir = Directory("logdir", argstr="--logdir=%s", usedefault=True)
    n_fibres = traits.Range(low=1, argstr="--nfibres=%d",
                            desc="Maximum nukmber of fibres to fit in each voxel")
    fudge = traits.Int(argstr="--fudge=%d",
                         desc="ARD fudge factor")
    n_jumps = traits.Range(low=1, argstr="--njumps=%d",
                           desc="Num of jumps to be made by MCMC")
    burn_in = traits.Range(low=0, argstr="--burnin=%d",
                           desc="Total num of jumps at start of MCMC to be discarded")
    burn_in_no_ard = traits.Range(low=0, argstr="--burninnoard=%d",
                           desc="num of burnin jumps before the ard is imposed")
    sample_every = traits.Range(low=0, argstr="--sampleevery=%d",
                           desc="Num of jumps for each sample (MCMC)")
    update_proposal_every = traits.Range(low=1, argstr="--updateproposalevery=%d",
                           desc="Num of jumps for each update to the proposal density std (MCMC)")
    seed = traits.Int(argstr="--seed=%d", desc="seed for pseudo random number generator")
    model = traits.Int(argstr="--model=%d", desc="Which model to use. \
1=mono-exponential (default and required for single shell). 2=continous \
exponential (for multi-shell experiments)")

    _xor_inputs1 = ('no_ard', 'all_ard')
    no_ard = traits.Bool(argstr="--noard", desc="Turn ARD off on all fibres", xor=_xor_inputs1)
    all_ard = traits.Bool(argstr="--allard", desc="Turn ARD on on all fibres", xor=_xor_inputs1)

    _xor_inputs2 = ('no_spat', 'non_linear')
    no_spat = traits.Bool(argstr="--nospat", desc="Initialise with tensor, not spatially", xor=_xor_inputs2)
    non_linear = traits.Bool(argstr="--nonlinear", desc="Initialise with nonlinear fitting", xor=_xor_inputs2)
    force_dir = traits.Bool(True,
                               desc='use the actual directory name given - i.e. ' +
                                    'do not add + to make a new directory',
                               argstr='--forcedir', usedefault=True)


class XFibresOutputSpec(TraitedSpec):
    dyads = OutputMultiPath(File(exists=True), desc="Mean of PDD distribution in vector form.")
    fsamples = OutputMultiPath(File(exists=True), desc="Samples from the distribution on anisotropic volume fraction")
    mean_dsamples = File(exists=True, desc="Mean of distribution on diffusivity d")
    mean_fsamples = OutputMultiPath(File(exists=True), desc="Mean of distribution on f anisotropy")
    mean_S0samples = File(exists=True, desc="Samples from S0 distribution")
    phsamples = OutputMultiPath(File(exists=True), desc="Samples from the distribution on phi")
    thsamples = OutputMultiPath(File(exists=True), desc="Samples from the distribution on theta")


class XFibres(FSLCommand):
    """Perform model parameters estimation for local (voxelwise) diffusion parameters
    """
    _cmd = "xfibres"
    input_spec = XFibresInputSpec
    output_spec = XFibresOutputSpec

    def _run_interface(self, runtime):
        runtime = super(XFibres, self)._run_interface(runtime)
        if runtime.stderr:
            self.raise_exception(runtime)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["mean_dsamples"] = self._gen_fname("mean_dsamples",
                                                   cwd=self.inputs.logdir)
        outputs["mean_S0samples"] = self._gen_fname("mean_S0samples",
                                                    cwd=self.inputs.logdir)
        outputs["dyads"] = []
        outputs["fsamples"] = []
        outputs["mean_fsamples"] = []
        outputs["phsamples"] = []
        outputs["thsamples"] = []
        for i in range(1, self.inputs.n_fibres + 1):
            outputs["dyads"].append(self._gen_fname("dyads%d" % i, cwd=self.inputs.logdir))
            outputs["fsamples"].append(self._gen_fname("f%dsamples" % i, cwd=self.inputs.logdir))
            outputs["mean_fsamples"].append(self._gen_fname("mean_f%dsamples" % i, cwd=self.inputs.logdir))
            outputs["phsamples"].append(self._gen_fname("ph%dsamples" % i, cwd=self.inputs.logdir))
            outputs["thsamples"].append(self._gen_fname("th%dsamples" % i, cwd=self.inputs.logdir))

        return outputs


class MakeDyadicVectorsInputSpec(FSLCommandInputSpec):
    theta_vol = File(exists=True, mandatory=True, position=0, argstr="%s")
    phi_vol = File(exists=True, mandatory=True, position=1, argstr="%s")
    mask = File(exists=True, position=2, argstr="%s")
    output = File("dyads", position=3, usedefault=True, argstr="%s", hash_files=False)
    perc = traits.Float(desc="the {perc}% angle of the output cone of \
uncertainty (output will be in degrees)",
                        position=4,
                        argstr="%f")


class MakeDyadicVectorsOutputSpec(TraitedSpec):
    dyads = File(exists=True)
    dispersion = File(exists=True)


class MakeDyadicVectors(FSLCommand):
    """Create vector volume representing mean principal diffusion direction
    and its uncertainty (dispersion)"""

    _cmd = "make_dyadic_vectors"
    input_spec = MakeDyadicVectorsInputSpec
    output_spec = MakeDyadicVectorsOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["dyads"] = self._gen_fname(self.inputs.output)
        outputs["dispersion"] = self._gen_fname(self.inputs.output,
                                                suffix="_dispersion")

        return outputs
