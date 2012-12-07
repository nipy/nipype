# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import tempfile
import shutil

from nipype.testing import (assert_equal, assert_not_equal, assert_raises,
                            skipif)

from nipype.utils.filemanip import split_filename
import nipype.interfaces.fsl.preprocess as fsl
from nipype.interfaces.fsl import Info
from nipype.interfaces.base import File, TraitError, Undefined
from nipype.interfaces.fsl import no_fsl


@skipif(no_fsl)
def fsl_name(obj, fname):
    """Create valid fsl name, including file extension for output type.
    """
    ext = Info.output_type_to_ext(obj.inputs.output_type)
    return fname + ext

tmp_infile = None
tmp_dir = None

@skipif(no_fsl)
def setup_infile():
    global tmp_infile, tmp_dir
    ext = Info.output_type_to_ext(Info.output_type())
    tmp_dir = tempfile.mkdtemp()
    tmp_infile = os.path.join(tmp_dir, 'foo' + ext)
    file(tmp_infile, 'w')
    return tmp_infile, tmp_dir

def teardown_infile(tmp_dir):
    shutil.rmtree(tmp_dir)

# test BET
#@with_setup(setup_infile, teardown_infile)
#broken in nose with generators
@skipif(no_fsl)
def test_bet():
    tmp_infile, tp_dir = setup_infile()
    better = fsl.BET()
    yield assert_equal, better.cmd, 'bet'

    # Test raising error with mandatory args absent
    yield assert_raises, ValueError, better.run

    # Test generated outfile name
    better.inputs.in_file = tmp_infile
    outfile = fsl_name(better, 'foo_brain')
    outpath = os.path.join(os.getcwd(), outfile)
    realcmd = 'bet %s %s' % (tmp_infile, outpath)
    yield assert_equal, better.cmdline, realcmd
    # Test specified outfile name
    outfile = fsl_name(better, '/newdata/bar')
    better.inputs.out_file = outfile
    realcmd = 'bet %s %s' % (tmp_infile, outfile)
    yield assert_equal, better.cmdline, realcmd

    # infile foo.nii doesn't exist
    def func():
        better.run(in_file='foo2.nii', out_file='bar.nii')
    yield assert_raises, TraitError, func

    # Our options and some test values for them
    # Should parallel the opt_map structure in the class for clarity
    opt_map = {
        'outline':            ('-o', True),
        'mask':               ('-m', True),
        'skull':              ('-s', True),
        'no_output':           ('-n', True),
        'frac':               ('-f 0.40', 0.4),
        'vertical_gradient':  ('-g 0.75', 0.75),
        'radius':             ('-r 20', 20),
        'center':             ('-c 54 75 80', [54, 75, 80]),
        'threshold':          ('-t', True),
        'mesh':               ('-e', True),
        'surfaces':           ('-A', True)
        #'verbose':            ('-v', True),
        #'flags':              ('--i-made-this-up', '--i-made-this-up'),
            }
    # Currently we don't test -R, -S, -B, -Z, -F, -A or -A2

    # test each of our arguments
    better = fsl.BET()
    outfile = fsl_name(better, 'foo_brain')
    outpath = os.path.join(os.getcwd(), outfile)
    for name, settings in opt_map.items():
        better = fsl.BET(**{name: settings[1]})
        # Add mandatory input
        better.inputs.in_file = tmp_infile
        realcmd =  ' '.join([better.cmd, tmp_infile, outpath, settings[0]])
        yield assert_equal, better.cmdline, realcmd
    teardown_infile(tmp_dir)

# test fast
@skipif(no_fsl)
def test_fast():
    tmp_infile, tp_dir = setup_infile()
    faster = fsl.FAST()
    faster.inputs.verbose = True
    fasted = fsl.FAST(in_files=tmp_infile, verbose = True)
    fasted2 = fsl.FAST(in_files=[tmp_infile, tmp_infile], verbose = True)

    yield assert_equal, faster.cmd, 'fast'
    yield assert_equal, faster.inputs.verbose, True
    yield assert_equal, faster.inputs.manual_seg , Undefined
    yield assert_not_equal, faster.inputs, fasted.inputs
    yield assert_equal, fasted.cmdline, 'fast -v -S 1 %s'%(tmp_infile)
    yield assert_equal, fasted2.cmdline, 'fast -v -S 2 %s %s'%(tmp_infile,
                                                                  tmp_infile)

    faster = fsl.FAST()
    faster.inputs.in_files = tmp_infile
    yield assert_equal, faster.cmdline, 'fast -S 1 %s'%(tmp_infile)
    faster.inputs.in_files = [tmp_infile, tmp_infile]
    yield assert_equal, faster.cmdline, 'fast -S 2 %s %s'%(tmp_infile, tmp_infile)

    # Our options and some test values for them
    # Should parallel the opt_map structure in the class for clarity
    opt_map = {'number_classes':       ('-n 4', 4),
               'bias_iters':           ('-I 5', 5),
               'bias_lowpass':         ('-l 15', 15),
               'img_type':             ('-t 2', 2),
               'init_seg_smooth':      ('-f 0.035', 0.035),
               'segments':             ('-g', True),
               'init_transform':       ('-a %s'%(tmp_infile), '%s'%(tmp_infile)),
               'other_priors':         ('-A %s %s %s'%(tmp_infile, tmp_infile,
                                                       tmp_infile),
                                        (['%s'%(tmp_infile),
                                          '%s'%(tmp_infile),
                                          '%s'%(tmp_infile)])),
               'no_pve':                ('--nopve', True),
               'output_biasfield':     ('-b', True),
               'output_biascorrected': ('-B', True),
               'no_bias':               ('-N', True),
               'out_basename':         ('-o fasted', 'fasted'),
               'use_priors':           ('-P', True),
               'segment_iters':        ('-W 14', 14),
               'mixel_smooth':         ('-R 0.25', 0.25),
               'iters_afterbias':      ('-O 3', 3),
               'hyper':                ('-H 0.15', 0.15),
               'verbose':              ('-v', True),
               'manual_seg':            ('-s %s'%(tmp_infile),
                       '%s'%(tmp_infile)),
               'probability_maps':     ('-p', True),
              }

    # test each of our arguments
    for name, settings in opt_map.items():
        faster = fsl.FAST(in_files=tmp_infile, **{name: settings[1]})
        yield assert_equal, faster.cmdline, ' '.join([faster.cmd,
                                                      settings[0],
                                                      "-S 1 %s"%tmp_infile])
    teardown_infile(tmp_dir)
@skipif(no_fsl)
def setup_flirt():
    ext = Info.output_type_to_ext(Info.output_type())
    tmpdir = tempfile.mkdtemp()
    _, infile = tempfile.mkstemp(suffix = ext, dir = tmpdir)
    _, reffile = tempfile.mkstemp(suffix = ext, dir = tmpdir)
    return tmpdir, infile, reffile

def teardown_flirt(tmpdir):
    shutil.rmtree(tmpdir)

@skipif(no_fsl)
def test_flirt():
    # setup
    tmpdir, infile, reffile = setup_flirt()

    flirter = fsl.FLIRT()
    yield assert_equal, flirter.cmd, 'flirt'

    flirter.inputs.bins = 256
    flirter.inputs.cost = 'mutualinfo'

    flirted = fsl.FLIRT(in_file=infile, reference=reffile,
                          out_file='outfile', out_matrix_file='outmat.mat',
                          bins = 256,
                          cost = 'mutualinfo')
    flirt_est = fsl.FLIRT(in_file=infile, reference=reffile,
                            out_matrix_file='outmat.mat',
                            bins = 256,
                            cost = 'mutualinfo')
    yield assert_not_equal, flirter.inputs, flirted.inputs
    yield assert_not_equal, flirted.inputs, flirt_est.inputs

    yield assert_equal, flirter.inputs.bins, flirted.inputs.bins
    yield assert_equal, flirter.inputs.cost, flirt_est.inputs.cost
    realcmd = 'flirt -in %s -ref %s -out outfile -omat outmat.mat ' \
        '-bins 256 -cost mutualinfo' % (infile, reffile)
    yield assert_equal, flirted.cmdline, realcmd

    flirter = fsl.FLIRT()
    # infile not specified
    yield assert_raises, ValueError, flirter.run
    flirter.inputs.in_file = infile
    # reference not specified
    yield assert_raises, ValueError, flirter.run
    flirter.inputs.reference = reffile
    # Generate outfile and outmatrix
    pth, fname, ext = split_filename(infile)
    outfile = os.path.join(os.getcwd(),
                           fsl_name(flirter, '%s_flirt' %fname))
    outmat = '%s_flirt.mat' % fname
    outmat = os.path.join(os.getcwd(), outmat)
    realcmd = 'flirt -in %s -ref %s -out %s -omat %s' % (infile, reffile,
                                                         outfile, outmat)
    yield assert_equal, flirter.cmdline, realcmd

    _, tmpfile = tempfile.mkstemp(suffix = '.nii', dir = tmpdir)
    # Loop over all inputs, set a reasonable value and make sure the
    # cmdline is updated correctly.
    for key, trait_spec in sorted(fsl.FLIRT.input_spec().traits().items()):
        # Skip mandatory inputs and the trait methods
        if key in ('trait_added', 'trait_modified', 'in_file', 'reference',
                   'environ', 'output_type', 'out_file', 'out_matrix_file',
                   'in_matrix_file', 'apply_xfm', 'ignore_exception'):
            continue
        param = None
        value = None
        if key == 'args':
            param = '-v'
            value = '-v'
        elif isinstance(trait_spec.trait_type, File):
            value = tmpfile
            param = trait_spec.argstr  % value
        elif trait_spec.default is False:
            param = trait_spec.argstr
            value = True
        elif key in ('searchr_x', 'searchr_y', 'searchr_z'):
            value = [-45, 45]
            param = trait_spec.argstr % ' '.join(str(elt) for elt in value)
        else:
            value = trait_spec.default
            param = trait_spec.argstr % value
        cmdline = 'flirt -in %s -ref %s' % (infile, reffile)
        # Handle autogeneration of outfile
        pth, fname, ext = split_filename(infile)
        outfile = os.path.join(os.getcwd(),
                               fsl_name(fsl.FLIRT(),'%s_flirt' % fname))
        outfile = ' '.join(['-out', outfile])
        # Handle autogeneration of outmatrix
        outmatrix = '%s_flirt.mat' % fname
        outmatrix = os.path.join(os.getcwd(), outmatrix)
        outmatrix = ' '.join(['-omat', outmatrix])
        # Build command line
        cmdline = ' '.join([cmdline, outfile, outmatrix, param])
        flirter = fsl.FLIRT(in_file = infile, reference = reffile)
        setattr(flirter.inputs, key, value)
        yield assert_equal, flirter.cmdline, cmdline

    # Test OutputSpec
    flirter = fsl.FLIRT(in_file = infile, reference = reffile)
    pth, fname, ext = split_filename(infile)
    flirter.inputs.out_file = ''.join(['foo', ext])
    flirter.inputs.out_matrix_file = ''.join(['bar', ext])
    outs = flirter._list_outputs()
    yield assert_equal, outs['out_file'], \
          os.path.join(os.getcwd(), flirter.inputs.out_file)
    yield assert_equal, outs['out_matrix_file'], \
          os.path.join(os.getcwd(), flirter.inputs.out_matrix_file)

    teardown_flirt(tmpdir)


# Mcflirt
@skipif(no_fsl)
def test_mcflirt():
    tmpdir, infile, reffile = setup_flirt()

    frt = fsl.MCFLIRT()
    yield assert_equal, frt.cmd, 'mcflirt'
    # Test generated outfile name

    frt.inputs.in_file = infile
    _, nme = os.path.split(infile)
    outfile = os.path.join(os.getcwd(), nme)
    outfile = frt._gen_fname(outfile, suffix = '_mcf')
    realcmd = 'mcflirt -in ' + infile + ' -out ' + outfile
    yield assert_equal, frt.cmdline, realcmd
    # Test specified outfile name
    outfile2 = '/newdata/bar.nii'
    frt.inputs.out_file = outfile2
    realcmd = 'mcflirt -in ' + infile + ' -out ' + outfile2
    yield assert_equal, frt.cmdline, realcmd

    opt_map = {
        'cost':        ('-cost mutualinfo', 'mutualinfo'),
        'bins':        ('-bins 256', 256),
        'dof':         ('-dof 6', 6),
        'ref_vol':      ('-refvol 2', 2),
        'scaling':     ('-scaling 6.00', 6.00),
        'smooth':      ('-smooth 1.00', 1.00),
        'rotation':    ('-rotation 2', 2),
        'stages':      ('-stages 3', 3),
        'init':        ('-init %s'%(infile), infile),
        'use_gradient': ('-gdt', True),
        'use_contour':  ('-edge', True),
        'mean_vol':     ('-meanvol', True),
        'stats_imgs':   ('-stats', True),
        'save_mats':    ('-mats', True),
        'save_plots':   ('-plots', True),
        }

    for name, settings in opt_map.items():
        fnt = fsl.MCFLIRT(in_file = infile, **{name : settings[1]})
        instr = '-in %s'%(infile)
        outstr = '-out %s'%(outfile)
        if name in ('init', 'cost', 'dof','mean_vol','bins'):
            yield assert_equal, fnt.cmdline, ' '.join([fnt.cmd,
                                                       instr,
                                                       settings[0],
                                                       outstr])
        else:
            yield assert_equal, fnt.cmdline, ' '.join([fnt.cmd,
                                                       instr,
                                                       outstr,
                                                       settings[0]])


    # Test error is raised when missing required args
    fnt = fsl.MCFLIRT()
    yield assert_raises, ValueError, fnt.run
    teardown_flirt(tmpdir)

#test fnirt
@skipif(no_fsl)
def test_fnirt():

    tmpdir, infile, reffile = setup_flirt()
    fnirt = fsl.FNIRT()
    yield assert_equal, fnirt.cmd, 'fnirt'

    # Test list parameters
    params = [('subsampling_scheme', '--subsamp', [4,2,2,1],'4,2,2,1'),
              ('max_nonlin_iter', '--miter', [4,4,4,2],'4,4,4,2'),
              ('ref_fwhm', '--reffwhm', [4,2,2,0],'4,2,2,0'),
              ('in_fwhm', '--infwhm', [4,2,2,0],'4,2,2,0'),
              ('apply_refmask', '--applyrefmask', [0,0,1,1],'0,0,1,1'),
              ('apply_inmask', '--applyinmask', [0,0,0,1],'0,0,0,1'),
              ('regularization_lambda', '--lambda', [0.5,0.75],'0.5,0.75')]
    for item, flag, val, strval in params:
        fnirt = fsl.FNIRT(in_file = infile,
                          ref_file = reffile,
                          **{item : val})
        log = fnirt._gen_fname(infile, suffix='_log.txt', change_ext=False)
        iout = fnirt._gen_fname(infile, suffix='_warped')
        if item in ('max_nonlin_iter'):
            cmd = 'fnirt --in=%s '\
                  '--logout=%s'\
                  ' %s=%s --ref=%s'\
                  ' --iout=%s' % (infile, log,
                                  flag, strval, reffile, iout)
        elif item in ('in_fwhm'):
            cmd = 'fnirt --in=%s %s=%s --logout=%s '\
                  '--ref=%s --iout=%s' % (infile, flag,
                                          strval, log,  reffile, iout)
        elif item.startswith('apply'):
            cmd = 'fnirt %s=%s '\
                  '--in=%s '\
                  '--logout=%s '\
                  '--ref=%s --iout=%s' % (flag,strval,
                                                infile, log,
                                                reffile,
                                                iout)

        else:
            cmd = 'fnirt '\
                  '--in=%s --logout=%s '\
                  '--ref=%s %s=%s --iout=%s' % (infile, log,
                                                reffile,
                                                flag, strval,
                                                iout)
        yield assert_equal, fnirt.cmdline, cmd

    # Test ValueError is raised when missing mandatory args
    fnirt = fsl.FNIRT()
    yield assert_raises, ValueError, fnirt.run
    fnirt.inputs.in_file = infile
    fnirt.inputs.ref_file = reffile

    # test files
    opt_map = {
        'affine_file':          ('--aff='),
        'inwarp_file':          ('--inwarp='),
        'in_intensitymap_file': ('--intin='),
        'config_file':          ('--config='),
        'refmask_file':         ('--refmask='),
        'inmask_file':          ('--inmask='),
        'field_file':           ('--fout='),
        'jacobian_file':        ('--jout='),
        'modulatedref_file':    ('--refout='),
        'out_intensitymap_file':('--intout='),
        'log_file':             ('--logout=')}

    for name, settings in opt_map.items():
        fnirt = fsl.FNIRT(in_file = infile,
                          ref_file = reffile,
                          **{name : infile})

        if name in ('config_file', 'affine_file','field_file'):
            cmd = 'fnirt %s%s --in=%s '\
                  '--logout=%s '\
                  '--ref=%s --iout=%s' % (settings, infile, infile, log,
                                          reffile, iout)
        elif name in ('refmask_file'):
            cmd = 'fnirt --in=%s '\
                  '--logout=%s --ref=%s '\
                  '%s%s '\
                  '--iout=%s' % (infile, log,
                                 reffile,
                                 settings,infile,
                                 iout)
        elif name in ('in_intensitymap_file', 'inwarp_file', 'inmask_file', 'jacobian_file'):
            cmd = 'fnirt --in=%s '\
                  '%s%s '\
                  '--logout=%s --ref=%s '\
                  '--iout=%s' % (infile,
                                 settings,infile,
                                 log,
                                 reffile,
                                 iout)
        elif name in ('log_file'):
            cmd = 'fnirt --in=%s '\
                  '%s%s --ref=%s '\
                  '--iout=%s' % (infile,
                                 settings,infile,
                                 reffile,
                                 iout)
        else:
            cmd = 'fnirt --in=%s '\
                  '--logout=%s %s%s '\
                  '--ref=%s --iout=%s' % (infile,log,
                                          settings, infile,
                                          reffile,iout)

        yield assert_equal, fnirt.cmdline, cmd
    teardown_flirt(tmpdir)

@skipif(no_fsl)
def test_applywarp():
    tmpdir, infile, reffile = setup_flirt()
    opt_map = {
        'out_file':          ('--out=bar.nii', 'bar.nii'),
        'premat':            ('--premat=%s'%(reffile), reffile),
        'postmat':           ('--postmat=%s'%(reffile), reffile),
         }

    # in_file, ref_file, field_file mandatory
    for name, settings in opt_map.items():
        awarp = fsl.ApplyWarp(in_file = infile,
                              ref_file = reffile,
                              field_file = reffile,
                              **{name : settings[1]})
        if name == 'out_file':
            realcmd = 'applywarp --warp=%s '\
                      '--in=%s --out=%s '\
                      '--ref=%s'%(reffile, infile,
                                  settings[1],reffile)
        else:
            outfile = awarp._gen_fname(infile, suffix='_warp')
            realcmd = 'applywarp --warp=%s '\
                      '--in=%s --out=%s '\
                      '%s --ref=%s'%(reffile, infile,
                                     outfile, settings[0],
                                     reffile)
        yield assert_equal, awarp.cmdline, realcmd

    awarp = fsl.ApplyWarp(in_file = infile,
                          ref_file = reffile,
                          field_file = reffile)

    teardown_flirt(tmpdir)

@skipif(no_fsl)
def test_fugue():
    input_map = dict(args = dict(argstr='%s',),
                     asym_se_time = dict(argstr='--asym=%.10f',),
                     despike_2dfilter = dict(argstr='--despike',),
                     despike_theshold = dict(argstr='--despikethreshold=%s',),
                     dwell_time = dict(argstr='--dwell=%.10f',),
                     dwell_to_asym_ratio = dict(argstr='--dwelltoasym=%.10f',),
                     environ = dict(usedefault=True,),
                     fmap_in_file = dict(argstr='--loadfmap=%s',),
                     fmap_out_file = dict(argstr='--savefmap=%s',),
                     fourier_order = dict(argstr='--fourier=%d',),
                     icorr = dict(requires=['shift_in_file'],argstr='--icorr',),
                     icorr_only = dict(requires=['unwarped_file'],argstr='--icorronly',),
                     in_file = dict(argstr='--in=%s',),
                     mask_file = dict(argstr='--mask=%s',),
                     median_2dfilter = dict(argstr='--median',),
                     no_extend = dict(argstr='--noextend',),
                     no_gap_fill = dict(argstr='--nofill',),
                     nokspace = dict(argstr='--nokspace',),
                     output_type = dict(),
                     pava = dict(argstr='--pava',),
                     phase_conjugate = dict(argstr='--phaseconj',),
                     phasemap_file = dict(argstr='--phasemap=%s',),
                     poly_order = dict(argstr='--poly=%d',),
                     save_unmasked_fmap = dict(requires=['fmap_out_file'],argstr='--unmaskfmap=%s',),
                     save_unmasked_shift = dict(requires=['shift_out_file'],argstr='--unmaskshift=%s',),
                     shift_in_file = dict(argstr='--loadshift=%s',),
                     shift_out_file = dict(argstr='--saveshift=%s',),
                     smooth2d = dict(argstr='--smooth2=%.2f',),
                     smooth3d = dict(argstr='--smooth3=%.2f',),
                     unwarp_direction = dict(argstr='--unwarpdir=%s',),
                     unwarped_file = dict(argstr='--unwarp=%s',),
                     )
    instance = fsl.FUGUE()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_fsl)
def test_prelude():
    input_map = dict(args = dict(argstr='%s',),
                     complex_phase_file = dict(mandatory=True,xor=['magnitude_file', 'phase_file'],argstr='--complex=%s',),
                     end = dict(argstr='--end=%d',),
                     environ = dict(usedefault=True,),
                     label_file = dict(argstr='--labels=%s',),
                     labelprocess2d = dict(argstr='--labelslices',),
                     magnitude_file = dict(mandatory=True,xor=['complex_phase_file'],argstr='--abs=%s',),
                     mask_file = dict(argstr='--mask=%s',),
                     num_partitions = dict(argstr='--numphasesplit=%d',),
                     output_type = dict(),
                     phase_file = dict(mandatory=True,xor=['complex_phase_file'],argstr='--phase=%s',),
                     process2d = dict(xor=['labelprocess2d'],argstr='--slices',),
                     process3d = dict(xor=['labelprocess2d', 'process2d'],argstr='--force3D',),
                     rawphase_file = dict(argstr='--rawphase=%s',),
                     removeramps = dict(argstr='--removeramps',),
                     savemask_file = dict(argstr='--savemask=%s',),
                     start = dict(argstr='--start=%d',),
                     threshold = dict(argstr='--thresh=%.10f',),
                     unwrapped_phase_file = dict(argstr='--unwrap=%s',),
                     )
    instance = fsl.PRELUDE()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

