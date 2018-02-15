# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft = python sts = 4 ts = 4 sw = 4 et:
"""AFNI utility interfaces

Examples
--------
See the docstrings of the individual classes for examples.
  .. testsetup::
    # Change directory to provide relative paths for doctests
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import str, bytes

import os
import os.path as op
import re
import numpy as np

from ...utils.filemanip import (load_json, save_json, split_filename)
from ..base import (CommandLineInputSpec, CommandLine, Directory, TraitedSpec,
                    traits, isdefined, File, InputMultiPath, Undefined, Str)
from ...external.due import BibTeX
from .base import (AFNICommandBase, AFNICommand, AFNICommandInputSpec,
                   AFNICommandOutputSpec, AFNIPythonCommandInputSpec,
                   AFNIPythonCommand)


class ABoverlapInputSpec(AFNICommandInputSpec):
    in_file_a = File(
        desc='input file A',
        argstr='%s',
        position=-3,
        mandatory=True,
        exists=True,
        copyfile=False)
    in_file_b = File(
        desc='input file B',
        argstr='%s',
        position=-2,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        desc='collect output to a file', argstr=' |& tee %s', position=-1)
    no_automask = traits.Bool(
        desc='consider input datasets as masks', argstr='-no_automask')
    quiet = traits.Bool(
        desc='be as quiet as possible (without being entirely mute)',
        argstr='-quiet')
    verb = traits.Bool(
        desc='print out some progress reports (to stderr)', argstr='-verb')


class ABoverlap(AFNICommand):
    """Output (to screen) is a count of various things about how
    the automasks of datasets A and B overlap or don't overlap.

    For complete details, see the `3dABoverlap Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dABoverlap.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> aboverlap = afni.ABoverlap()
    >>> aboverlap.inputs.in_file_a = 'functional.nii'
    >>> aboverlap.inputs.in_file_b = 'structural.nii'
    >>> aboverlap.inputs.out_file =  'out.mask_ae_overlap.txt'
    >>> aboverlap.cmdline
    '3dABoverlap functional.nii structural.nii  |& tee out.mask_ae_overlap.txt'
    >>> res = aboverlap.run()  # doctest: +SKIP

    """

    _cmd = '3dABoverlap'
    input_spec = ABoverlapInputSpec
    output_spec = AFNICommandOutputSpec


class AFNItoNIFTIInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3dAFNItoNIFTI',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        name_template='%s.nii',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file',
        hash_files=False)
    float_ = traits.Bool(
        desc='Force the output dataset to be 32-bit floats. This option '
        'should be used when the input AFNI dataset has different float '
        'scale factors for different sub-bricks, an option that '
        'NIfTI-1.1 does not support.',
        argstr='-float')
    pure = traits.Bool(
        desc='Do NOT write an AFNI extension field into the output file. Only '
        'use this option if needed. You can also use the \'nifti_tool\' '
        'program to strip extensions from a file.',
        argstr='-pure')
    denote = traits.Bool(
        desc='When writing the AFNI extension field, remove text notes that '
        'might contain subject identifying information.',
        argstr='-denote')
    oldid = traits.Bool(
        desc='Give the new dataset the input dataset'
        's AFNI ID code.',
        argstr='-oldid',
        xor=['newid'])
    newid = traits.Bool(
        desc='Give the new dataset a new AFNI ID code, to distinguish it from '
        'the input dataset.',
        argstr='-newid',
        xor=['oldid'])


class AFNItoNIFTI(AFNICommand):
    """Converts AFNI format files to NIFTI format. This can also convert 2D or
    1D data, which you can numpy.squeeze() to remove extra dimensions.

    For complete details, see the `3dAFNItoNIFTI Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAFNItoNIFTI.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> a2n = afni.AFNItoNIFTI()
    >>> a2n.inputs.in_file = 'afni_output.3D'
    >>> a2n.inputs.out_file =  'afni_output.nii'
    >>> a2n.cmdline
    '3dAFNItoNIFTI -prefix afni_output.nii afni_output.3D'
    >>> res = a2n.run()  # doctest: +SKIP

    """

    _cmd = '3dAFNItoNIFTI'
    input_spec = AFNItoNIFTIInputSpec
    output_spec = AFNICommandOutputSpec

    def _overload_extension(self, value):
        path, base, ext = split_filename(value)
        if ext.lower() not in ['.nii', '.nii.gz', '.1d', '.1D']:
            ext += '.nii'
        return os.path.join(path, base + ext)

    def _gen_filename(self, name):
        return os.path.abspath(super(AFNItoNIFTI, self)._gen_filename(name))


class AutoboxInputSpec(AFNICommandInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr='-input %s',
        desc='input file',
        copyfile=False)
    padding = traits.Int(
        argstr='-npad %d',
        desc='Number of extra voxels to pad on each side of box')
    out_file = File(
        argstr='-prefix %s', name_source='in_file', name_template='%s_autobox')
    no_clustering = traits.Bool(
        argstr='-noclust',
        desc='Don\'t do any clustering to find box. Any non-zero voxel will '
        'be preserved in the cropped volume. The default method uses '
        'some clustering to find the cropping box, and will clip off '
        'small isolated blobs.')


class AutoboxOutputSpec(TraitedSpec):  # out_file not mandatory
    x_min = traits.Int()
    x_max = traits.Int()
    y_min = traits.Int()
    y_max = traits.Int()
    z_min = traits.Int()
    z_max = traits.Int()

    out_file = File(desc='output file')


class Autobox(AFNICommand):
    """Computes size of a box that fits around the volume.
    Also can be used to crop the volume to that box.

    For complete details, see the `3dAutobox Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAutobox.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> abox = afni.Autobox()
    >>> abox.inputs.in_file = 'structural.nii'
    >>> abox.inputs.padding = 5
    >>> abox.cmdline
    '3dAutobox -input structural.nii -prefix structural_autobox -npad 5'
    >>> res = abox.run()  # doctest: +SKIP

    """

    _cmd = '3dAutobox'
    input_spec = AutoboxInputSpec
    output_spec = AutoboxOutputSpec

    def aggregate_outputs(self, runtime=None, needed_outputs=None):
        outputs = super(Autobox, self).aggregate_outputs(
            runtime, needed_outputs)
        pattern = 'x=(?P<x_min>-?\d+)\.\.(?P<x_max>-?\d+)  '\
                  'y=(?P<y_min>-?\d+)\.\.(?P<y_max>-?\d+)  '\
                  'z=(?P<z_min>-?\d+)\.\.(?P<z_max>-?\d+)'
        for line in runtime.stderr.split('\n'):
            m = re.search(pattern, line)
            if m:
                d = m.groupdict()
                outputs.trait_set(**{k: int(d[k]) for k in d.keys()})
        return outputs


class BrickStatInputSpec(CommandLineInputSpec):
    in_file = File(
        desc='input file to 3dmaskave',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True)
    mask = File(
        desc='-mask dset = use dset as mask to include/exclude voxels',
        argstr='-mask %s',
        position=2,
        exists=True)
    min = traits.Bool(
        desc='print the minimum value in dataset', argstr='-min', position=1)
    slow = traits.Bool(
        desc='read the whole dataset to find the min and max values',
        argstr='-slow')
    max = traits.Bool(
        desc='print the maximum value in the dataset', argstr='-max')
    mean = traits.Bool(
        desc='print the mean value in the dataset', argstr='-mean')
    sum = traits.Bool(
        desc='print the sum of values in the dataset', argstr='-sum')
    var = traits.Bool(desc='print the variance in the dataset', argstr='-var')
    percentile = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        desc='p0 ps p1 write the percentile values starting '
        'at p0% and ending at p1% at a step of ps%. '
        'only one sub-brick is accepted.',
        argstr='-percentile %.3f %.3f %.3f')


class BrickStatOutputSpec(TraitedSpec):
    min_val = traits.Float(desc='output')


class BrickStat(AFNICommandBase):
    """Computes maximum and/or minimum voxel values of an input dataset.
    TODO Add optional arguments.

    For complete details, see the `3dBrickStat Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dBrickStat.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> brickstat = afni.BrickStat()
    >>> brickstat.inputs.in_file = 'functional.nii'
    >>> brickstat.inputs.mask = 'skeleton_mask.nii.gz'
    >>> brickstat.inputs.min = True
    >>> brickstat.cmdline
    '3dBrickStat -min -mask skeleton_mask.nii.gz functional.nii'
    >>> res = brickstat.run()  # doctest: +SKIP

    """
    _cmd = '3dBrickStat'
    input_spec = BrickStatInputSpec
    output_spec = BrickStatOutputSpec

    def aggregate_outputs(self, runtime=None, needed_outputs=None):

        outputs = self._outputs()

        outfile = os.path.join(os.getcwd(), 'stat_result.json')

        if runtime is None:
            try:
                min_val = load_json(outfile)['stat']
            except IOError:
                return self.run().outputs
        else:
            min_val = []
            for line in runtime.stdout.split('\n'):
                if line:
                    values = line.split()
                    if len(values) > 1:
                        min_val.append([float(val) for val in values])
                    else:
                        min_val.extend([float(val) for val in values])

            if len(min_val) == 1:
                min_val = min_val[0]
            save_json(outfile, dict(stat=min_val))
        outputs.min_val = min_val

        return outputs


class BucketInputSpec(AFNICommandInputSpec):
    in_file = traits.List(
        traits.Tuple(
            (File(exists=True, copyfile=False), traits.Str(argstr="'%s'")),
            artstr="%s%s"),
        position=-1,
        mandatory=True,
        argstr="%s",
        desc='List of tuples of input datasets and subbrick selection strings'
        'as described in more detail in the following afni help string'
        'Input dataset specified using one of these forms:'
        '   \'prefix+view\', \'prefix+view.HEAD\', or \'prefix+view.BRIK\'.'
        'You can also add a sub-brick selection list after the end of the'
        'dataset name.  This allows only a subset of the sub-bricks to be'
        'included into the output (by default, all of the input dataset'
        'is copied into the output).  A sub-brick selection list looks like'
        'one of the following forms:'
        '  fred+orig[5]                     ==> use only sub-brick #5'
        '  fred+orig[5,9,17]                ==> use #5, #9, and #17'
        '  fred+orig[5..8]     or [5-8]     ==> use #5, #6, #7, and #8'
        '  fred+orig[5..13(2)] or [5-13(2)] ==> use #5, #7, #9, #11, and #13'
        'Sub-brick indexes start at 0.  You can use the character \'$\''
        'to indicate the last sub-brick in a dataset; for example, you'
        'can select every third sub-brick by using the selection list'
        '  fred+orig[0..$(3)]'
        'N.B.: The sub-bricks are output in the order specified, which may'
        ' not be the order in the original datasets.  For example, using'
        '  fred+orig[0..$(2),1..$(2)]'
        ' will cause the sub-bricks in fred+orig to be output into the'
        ' new dataset in an interleaved fashion.  Using'
        '  fred+orig[$..0]'
        ' will reverse the order of the sub-bricks in the output.'
        'N.B.: Bucket datasets have multiple sub-bricks, but do NOT have'
        ' a time dimension.  You can input sub-bricks from a 3D+time dataset'
        ' into a bucket dataset.  You can use the \'3dinfo\' program to see'
        ' how many sub-bricks a 3D+time or a bucket dataset contains.'
        'N.B.: In non-bucket functional datasets (like the \'fico\' datasets'
        ' output by FIM, or the \'fitt\' datasets output by 3dttest), sub-brick'
        ' [0] is the \'intensity\' and sub-brick [1] is the statistical parameter'
        ' used as a threshold.  Thus, to create a bucket dataset using the'
        ' intensity from dataset A and the threshold from dataset B, and'
        ' calling the output dataset C, you would type'
        '    3dbucket -prefix C -fbuc \'A+orig[0]\' -fbuc \'B+orig[1]\''
        'WARNING: using this program, it is possible to create a dataset that'
        '         has different basic datum types for different sub-bricks'
        '         (e.g., shorts for brick 0, floats for brick 1).'
        '         Do NOT do this!  Very few AFNI programs will work correctly'
        '         with such datasets!')
    out_file = File(argstr='-prefix %s', name_template='buck')


class Bucket(AFNICommand):
    """Concatenate sub-bricks from input datasets into one big
    'bucket' dataset.

    For complete details, see the `3dbucket Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dbucket.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> bucket = afni.Bucket()
    >>> bucket.inputs.in_file = [('functional.nii',"{2..$}"), ('functional.nii',"{1}")]
    >>> bucket.inputs.out_file = 'vr_base'
    >>> bucket.cmdline
    "3dbucket -prefix vr_base functional.nii'{2..$}' functional.nii'{1}'"
    >>> res = bucket.run()  # doctest: +SKIP

    """

    _cmd = '3dbucket'
    input_spec = BucketInputSpec
    output_spec = AFNICommandOutputSpec

    def _format_arg(self, name, spec, value):
        if name == 'in_file':
            return spec.argstr % (
                ' '.join([i[0] + "'" + i[1] + "'" for i in value]))
        return super(Bucket, self)._format_arg(name, spec, value)


class CalcInputSpec(AFNICommandInputSpec):
    in_file_a = File(
        desc='input file to 3dcalc',
        argstr='-a %s',
        position=0,
        mandatory=True,
        exists=True)
    in_file_b = File(
        desc='operand file to 3dcalc', argstr='-b %s', position=1, exists=True)
    in_file_c = File(
        desc='operand file to 3dcalc', argstr='-c %s', position=2, exists=True)
    out_file = File(
        name_template='%s_calc',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file_a')
    expr = Str(desc='expr', argstr='-expr "%s"', position=3, mandatory=True)
    start_idx = traits.Int(
        desc='start index for in_file_a', requires=['stop_idx'])
    stop_idx = traits.Int(
        desc='stop index for in_file_a', requires=['start_idx'])
    single_idx = traits.Int(desc='volume index for in_file_a')
    overwrite = traits.Bool(desc='overwrite output', argstr='-overwrite')
    other = File(desc='other options', argstr='')


class Calc(AFNICommand):
    """This program does voxel-by-voxel arithmetic on 3D datasets.

    For complete details, see the `3dcalc Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dcalc.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> calc = afni.Calc()
    >>> calc.inputs.in_file_a = 'functional.nii'
    >>> calc.inputs.in_file_b = 'functional2.nii'
    >>> calc.inputs.expr='a*b'
    >>> calc.inputs.out_file =  'functional_calc.nii.gz'
    >>> calc.inputs.outputtype = 'NIFTI'
    >>> calc.cmdline  # doctest: +ELLIPSIS
    '3dcalc -a functional.nii -b functional2.nii -expr "a*b" -prefix functional_calc.nii.gz'
    >>> res = calc.run()  # doctest: +SKIP

    >>> from nipype.interfaces import afni
    >>> calc = afni.Calc()
    >>> calc.inputs.in_file_a = 'functional.nii'
    >>> calc.inputs.expr = '1'
    >>> calc.inputs.out_file = 'rm.epi.all1'
    >>> calc.inputs.overwrite = True
    >>> calc.cmdline
    '3dcalc -a functional.nii -expr "1" -prefix rm.epi.all1 -overwrite'
    >>> res = calc.run() # doctest: +SKIP

    """

    _cmd = '3dcalc'
    input_spec = CalcInputSpec
    output_spec = AFNICommandOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if name == 'in_file_a':
            arg = trait_spec.argstr % value
            if isdefined(self.inputs.start_idx):
                arg += '[%d..%d]' % (self.inputs.start_idx,
                                     self.inputs.stop_idx)
            if isdefined(self.inputs.single_idx):
                arg += '[%d]' % (self.inputs.single_idx)
            return arg
        return super(Calc, self)._format_arg(name, trait_spec, value)

    def _parse_inputs(self, skip=None):
        """Skip the arguments without argstr metadata
        """
        return super(
            Calc, self)._parse_inputs(skip=('start_idx', 'stop_idx', 'other'))


class CatInputSpec(AFNICommandInputSpec):
    in_files = traits.List(
        File(exists=True), argstr="%s", mandatory=True, position=-2)
    out_file = File(
        argstr='> %s',
        default='catout.1d',
        desc='output (concatenated) file name',
        position=-1,
        mandatory=True)
    omitconst = traits.Bool(
        desc='Omit columns that are identically constant from output.',
        argstr='-nonconst')
    keepfree = traits.Bool(
        desc='Keep only columns that are marked as \'free\' in the '
        '3dAllineate header from \'-1Dparam_save\'. '
        'If there is no such header, all columns are kept.',
        argstr='-nonfixed')
    out_format = traits.Enum(
        'int',
        'nice',
        'double',
        'fint',
        'cint',
        argstr='-form %s',
        desc='specify data type for output. Valid types are \'int\', '
        '\'nice\', \'double\', \'fint\', and \'cint\'.',
        xor=['out_int', 'out_nice', 'out_double', 'out_fint', 'out_cint'])
    stack = traits.Bool(
        desc='Stack the columns of the resultant matrix in the output.',
        argstr='-stack')
    sel = traits.Str(
        desc='Apply the same column/row selection string to all filenames '
        'on the command line.',
        argstr='-sel %s')
    out_int = traits.Bool(
        desc='specifiy int data type for output',
        argstr='-i',
        xor=['out_format', 'out_nice', 'out_double', 'out_fint', 'out_cint'])
    out_nice = traits.Bool(
        desc='specifiy nice data type for output',
        argstr='-n',
        xor=['out_format', 'out_int', 'out_double', 'out_fint', 'out_cint'])
    out_double = traits.Bool(
        desc='specifiy double data type for output',
        argstr='-d',
        xor=['out_format', 'out_nice', 'out_int', 'out_fint', 'out_cint'])
    out_fint = traits.Bool(
        desc='specifiy int, rounded down, data type for output',
        argstr='-f',
        xor=['out_format', 'out_nice', 'out_double', 'out_int', 'out_cint'])
    out_cint = traits.Bool(
        desc='specifiy int, rounded up, data type for output',
        xor=['out_format', 'out_nice', 'out_double', 'out_fint', 'out_int'])


class Cat(AFNICommand):
    """1dcat takes as input one or more 1D files, and writes out a 1D file
    containing the side-by-side concatenation of all or a subset of the
    columns from the input files.

    For complete details, see the `1dcat Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/1dcat.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> cat1d = afni.Cat()
    >>> cat1d.inputs.sel = "'[0,2]'"
    >>> cat1d.inputs.in_files = ['f1.1D', 'f2.1D']
    >>> cat1d.inputs.out_file = 'catout.1d'
    >>> cat1d.cmdline
    "1dcat -sel '[0,2]' f1.1D f2.1D > catout.1d"
    >>> res = cat1d.run()  # doctest: +SKIP

    """

    _cmd = '1dcat'
    input_spec = CatInputSpec
    output_spec = AFNICommandOutputSpec


class CatMatvecInputSpec(AFNICommandInputSpec):
    in_file = traits.List(
        traits.Tuple(traits.Str(), traits.Str()),
        desc="list of tuples of mfiles and associated opkeys",
        mandatory=True,
        argstr="%s",
        position=-2)
    out_file = File(
        desc="File to write concattenated matvecs to",
        argstr=" > %s",
        position=-1,
        mandatory=True)
    matrix = traits.Bool(
        desc="indicates that the resulting matrix will"
        "be written to outfile in the 'MATRIX(...)' format (FORM 3)."
        "This feature could be used, with clever scripting, to input"
        "a matrix directly on the command line to program 3dWarp.",
        argstr="-MATRIX",
        xor=['oneline', 'fourxfour'])
    oneline = traits.Bool(
        desc="indicates that the resulting matrix"
        "will simply be written as 12 numbers on one line.",
        argstr="-ONELINE",
        xor=['matrix', 'fourxfour'])
    fourxfour = traits.Bool(
        desc="Output matrix in augmented form (last row is 0 0 0 1)"
        "This option does not work with -MATRIX or -ONELINE",
        argstr="-4x4",
        xor=['matrix', 'oneline'])


class CatMatvec(AFNICommand):
    """Catenates 3D rotation+shift matrix+vector transformations.

    For complete details, see the `cat_matvec Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/cat_matvec.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> cmv = afni.CatMatvec()
    >>> cmv.inputs.in_file = [('structural.BRIK::WARP_DATA','I')]
    >>> cmv.inputs.out_file = 'warp.anat.Xat.1D'
    >>> cmv.cmdline
    'cat_matvec structural.BRIK::WARP_DATA -I  > warp.anat.Xat.1D'
    >>> res = cmv.run()  # doctest: +SKIP

    """

    _cmd = 'cat_matvec'
    input_spec = CatMatvecInputSpec
    output_spec = AFNICommandOutputSpec

    def _format_arg(self, name, spec, value):
        if name == 'in_file':
            return spec.argstr % (' '.join([i[0] + ' -' + i[1]
                                            for i in value]))
        return super(CatMatvec, self)._format_arg(name, spec, value)


class CenterMassInputSpec(CommandLineInputSpec):
    in_file = File(
        desc='input file to 3dCM',
        argstr='%s',
        position=-2,
        mandatory=True,
        exists=True,
        copyfile=True)
    cm_file = File(
        name_source='in_file',
        name_template='%s_cm.out',
        hash_files=False,
        keep_extension=False,
        desc="File to write center of mass to",
        argstr="> %s",
        position=-1)
    mask_file = File(
        desc='Only voxels with nonzero values in the provided mask will be '
        'averaged.',
        argstr='-mask %s',
        exists=True)
    automask = traits.Bool(
        desc='Generate the mask automatically', argstr='-automask')
    set_cm = traits.Tuple(
        (traits.Float(), traits.Float(), traits.Float()),
        desc='After computing the center of mass, set the origin fields in '
        'the header so that the center of mass will be at (x,y,z) in '
        'DICOM coords.',
        argstr='-set %f %f %f')
    local_ijk = traits.Bool(
        desc='Output values as (i,j,k) in local orienation',
        argstr='-local_ijk')
    roi_vals = traits.List(
        traits.Int,
        desc='Compute center of mass for each blob with voxel value of v0, '
        'v1, v2, etc. This option is handy for getting ROI centers of '
        'mass.',
        argstr='-roi_vals %s')
    all_rois = traits.Bool(
        desc='Don\'t bother listing the values of ROIs you want: The program '
        'will find all of them and produce a full list',
        argstr='-all_rois')


class CenterMassOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='output file')
    cm_file = File(desc='file with the center of mass coordinates')
    cm = traits.List(
        traits.Tuple(traits.Float(), traits.Float(), traits.Float()),
        desc='center of mass')


class CenterMass(AFNICommandBase):
    """Computes center of mass using 3dCM command

    .. note::

      By default, the output is (x,y,z) values in DICOM coordinates. But
      as of Dec, 2016, there are now command line switches for other options.


    For complete details, see the `3dCM Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dCM.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> cm = afni.CenterMass()
    >>> cm.inputs.in_file = 'structural.nii'
    >>> cm.inputs.cm_file = 'cm.txt'
    >>> cm.inputs.roi_vals = [2, 10]
    >>> cm.cmdline
    '3dCM -roi_vals 2 10 structural.nii > cm.txt'
    >>> res = 3dcm.run()  # doctest: +SKIP
    """

    _cmd = '3dCM'
    input_spec = CenterMassInputSpec
    output_spec = CenterMassOutputSpec

    def _list_outputs(self):
        outputs = super(CenterMass, self)._list_outputs()
        outputs['out_file'] = os.path.abspath(self.inputs.in_file)
        outputs['cm_file'] = os.path.abspath(self.inputs.cm_file)
        sout = np.loadtxt(outputs['cm_file'], ndmin=2)
        outputs['cm'] = [tuple(s) for s in sout]
        return outputs


class ConvertDsetInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to ConvertDset',
        argstr='-input %s',
        position=-2,
        mandatory=True,
        exists=True)

    out_file = File(
        desc='output file for ConvertDset',
        argstr='-prefix %s',
        position=-1,
        mandatory=True)

    out_type = traits.Enum(
        ('niml', 'niml_asc', 'niml_bi',
         '1D', '1Dp', '1Dpt',
         'gii', 'gii_asc', 'gii_b64', 'gii_b64gz'),
        desc='output type',
        argstr='-o_%s',
        mandatory=True,
        position=0)


class ConvertDset(AFNICommandBase):
    """Converts a surface dataset from one format to another.

    For complete details, see the `ConvertDset Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/ConvertDset.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> convertdset = afni.ConvertDset()
    >>> convertdset.inputs.in_file = 'lh.pial_converted.gii'
    >>> convertdset.inputs.out_type = 'niml_asc'
    >>> convertdset.inputs.out_file = 'lh.pial_converted.niml.dset'
    >>> convertdset.cmdline
    'ConvertDset -o_niml_asc -input lh.pial_converted.gii -prefix lh.pial_converted.niml.dset'
    >>> res = convertdset.run()  # doctest: +SKIP
    """

    _cmd = 'ConvertDset'
    input_spec = ConvertDsetInputSpec
    output_spec = AFNICommandOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs


class CopyInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3dcopy',
        argstr='%s',
        position=-2,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        name_template='%s_copy',
        desc='output image file name',
        argstr='%s',
        position=-1,
        name_source='in_file')
    verbose = traits.Bool(desc='print progress reports', argstr='-verb')


class Copy(AFNICommand):
    """Copies an image of one type to an image of the same
    or different type using 3dcopy command

    For complete details, see the `3dcopy Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dcopy.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> copy3d = afni.Copy()
    >>> copy3d.inputs.in_file = 'functional.nii'
    >>> copy3d.cmdline
    '3dcopy functional.nii functional_copy'
    >>> res = copy3d.run()  # doctest: +SKIP

    >>> from copy import deepcopy
    >>> copy3d_2 = deepcopy(copy3d)
    >>> copy3d_2.inputs.outputtype = 'NIFTI'
    >>> copy3d_2.cmdline
    '3dcopy functional.nii functional_copy.nii'
    >>> res = copy3d_2.run()  # doctest: +SKIP

    >>> copy3d_3 = deepcopy(copy3d)
    >>> copy3d_3.inputs.outputtype = 'NIFTI_GZ'
    >>> copy3d_3.cmdline
    '3dcopy functional.nii functional_copy.nii.gz'
    >>> res = copy3d_3.run()  # doctest: +SKIP

    >>> copy3d_4 = deepcopy(copy3d)
    >>> copy3d_4.inputs.out_file = 'new_func.nii'
    >>> copy3d_4.cmdline
    '3dcopy functional.nii new_func.nii'
    >>> res = copy3d_4.run()  # doctest: +SKIP

    """

    _cmd = '3dcopy'
    input_spec = CopyInputSpec
    output_spec = AFNICommandOutputSpec


class DotInputSpec(AFNICommandInputSpec):
    in_files = traits.List(
        (File()),
        desc="list of input files, possibly with subbrick selectors",
        argstr="%s ...",
        position=-2)
    out_file = File(
        desc='collect output to a file', argstr=' |& tee %s', position=-1)
    mask = File(desc='Use this dataset as a mask', argstr='-mask %s')
    mrange = traits.Tuple(
        (traits.Float(), traits.Float()),
        desc='Means to further restrict the voxels from \'mset\' so that'
        'only those mask values within this range (inclusive) willbe used.',
        argstr='-mrange %s %s')
    demean = traits.Bool(
        desc=
        'Remove the mean from each volume prior to computing the correlation',
        argstr='-demean')
    docor = traits.Bool(
        desc='Return the correlation coefficient (default).', argstr='-docor')
    dodot = traits.Bool(
        desc='Return the dot product (unscaled).', argstr='-dodot')
    docoef = traits.Bool(
        desc=
        'Return the least square fit coefficients {{a,b}} so that dset2 is approximately a + b*dset1',
        argstr='-docoef')
    dosums = traits.Bool(
        desc=
        'Return the 6 numbers xbar=<x> ybar=<y> <(x-xbar)^2> <(y-ybar)^2> <(x-xbar)(y-ybar)> and the correlation coefficient.',
        argstr='-dosums')
    dodice = traits.Bool(
        desc='Return the Dice coefficient (the Sorensen-Dice index).',
        argstr='-dodice')
    doeta2 = traits.Bool(
        desc='Return eta-squared (Cohen, NeuroImage 2008).', argstr='-doeta2')
    full = traits.Bool(
        desc=
        'Compute the whole matrix. A waste of time, but handy for parsing.',
        argstr='-full')
    show_labels = traits.Bool(
        desc=
        'Print sub-brick labels to help identify what is being correlated. This option is useful when'
        'you have more than 2 sub-bricks at input.',
        argstr='-show_labels')
    upper = traits.Bool(
        desc='Compute upper triangular matrix', argstr='-upper')


class Dot(AFNICommand):
    """Correlation coefficient between sub-brick pairs.
    All datasets in in_files list will be concatenated.
    You can use sub-brick selectors in the file specification.
    Note: This program is not efficient when more than two subbricks are input.
    For complete details, see the `3ddot Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3ddot.html>`_

    >>> from nipype.interfaces import afni
    >>> dot = afni.Dot()
    >>> dot.inputs.in_files = ['functional.nii[0]', 'structural.nii']
    >>> dot.inputs.dodice = True
    >>> dot.inputs.out_file = 'out.mask_ae_dice.txt'
    >>> dot.cmdline
    '3dDot -dodice functional.nii[0]  structural.nii   |& tee out.mask_ae_dice.txt'
    >>> res = copy3d.run()  # doctest: +SKIP

    """
    _cmd = '3dDot'
    input_spec = DotInputSpec
    output_spec = AFNICommandOutputSpec


class Edge3InputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3dedge3',
        argstr='-input %s',
        position=0,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        desc='output image file name', position=-1, argstr='-prefix %s')
    datum = traits.Enum(
        'byte',
        'short',
        'float',
        argstr='-datum %s',
        desc='specify data type for output. Valid types are \'byte\', '
        '\'short\' and \'float\'.')
    fscale = traits.Bool(
        desc='Force scaling of the output to the maximum integer range.',
        argstr='-fscale',
        xor=['gscale', 'nscale', 'scale_floats'])
    gscale = traits.Bool(
        desc='Same as \'-fscale\', but also forces each output sub-brick to '
        'to get the same scaling factor.',
        argstr='-gscale',
        xor=['fscale', 'nscale', 'scale_floats'])
    nscale = traits.Bool(
        desc='Don\'t do any scaling on output to byte or short datasets.',
        argstr='-nscale',
        xor=['fscale', 'gscale', 'scale_floats'])
    scale_floats = traits.Float(
        desc='Multiply input by VAL, but only if the input datum is '
        'float. This is needed when the input dataset '
        'has a small range, like 0 to 2.0 for instance. '
        'With such a range, very few edges are detected due to '
        'what I suspect to be truncation problems. '
        'Multiplying such a dataset by 10000 fixes the problem '
        'and the scaling is undone at the output.',
        argstr='-scale_floats %f',
        xor=['fscale', 'gscale', 'nscale'])
    verbose = traits.Bool(
        desc='Print out some information along the way.', argstr='-verbose')


class Edge3(AFNICommand):
    """Does 3D Edge detection using the library 3DEdge
    by Gregoire Malandain (gregoire.malandain@sophia.inria.fr).

    For complete details, see the `3dedge3 Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dedge3.html>`_

    references_ = [{'entry': BibTeX('@article{Deriche1987,'
                                    'author={R. Deriche},'
                                    'title={Optimal edge detection using recursive filtering},'
                                    'journal={International Journal of Computer Vision},'
                                    'volume={2},',
                                    'pages={167-187},'
                                    'year={1987},'
                                    '}'),
                    'tags': ['method'],
                    },
                   {'entry': BibTeX('@article{MongaDericheMalandainCocquerez1991,'
                                    'author={O. Monga, R. Deriche, G. Malandain, J.P. Cocquerez},'
                                    'title={Recursive filtering and edge tracking: two primary tools for 3D edge detection},'
                                    'journal={Image and vision computing},'
                                    'volume={9},',
                                    'pages={203-214},'
                                    'year={1991},'
                                    '}'),
                    'tags': ['method'],
                    },
                   ]

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> edge3 = afni.Edge3()
    >>> edge3.inputs.in_file = 'functional.nii'
    >>> edge3.inputs.out_file = 'edges.nii'
    >>> edge3.inputs.datum = 'byte'
    >>> edge3.cmdline
    '3dedge3 -input functional.nii -datum byte -prefix edges.nii'
    >>> res = edge3.run()  # doctest: +SKIP

    """

    _cmd = '3dedge3'
    input_spec = Edge3InputSpec
    output_spec = AFNICommandOutputSpec


class EvalInputSpec(AFNICommandInputSpec):
    in_file_a = File(
        desc='input file to 1deval',
        argstr='-a %s',
        position=0,
        mandatory=True,
        exists=True)
    in_file_b = File(
        desc='operand file to 1deval', argstr='-b %s', position=1, exists=True)
    in_file_c = File(
        desc='operand file to 1deval', argstr='-c %s', position=2, exists=True)
    out_file = File(
        name_template='%s_calc',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file_a')
    out1D = traits.Bool(desc='output in 1D', argstr='-1D')
    expr = Str(desc='expr', argstr='-expr "%s"', position=3, mandatory=True)
    start_idx = traits.Int(
        desc='start index for in_file_a', requires=['stop_idx'])
    stop_idx = traits.Int(
        desc='stop index for in_file_a', requires=['start_idx'])
    single_idx = traits.Int(desc='volume index for in_file_a')
    other = File(desc='other options', argstr='')


class Eval(AFNICommand):
    """Evaluates an expression that may include columns of data from one or
    more text files.

    For complete details, see the `1deval Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/1deval.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> eval = afni.Eval()
    >>> eval.inputs.in_file_a = 'seed.1D'
    >>> eval.inputs.in_file_b = 'resp.1D'
    >>> eval.inputs.expr = 'a*b'
    >>> eval.inputs.out1D = True
    >>> eval.inputs.out_file =  'data_calc.1D'
    >>> eval.cmdline
    '1deval -a seed.1D -b resp.1D -expr "a*b" -1D -prefix data_calc.1D'
    >>> res = eval.run()  # doctest: +SKIP

    """

    _cmd = '1deval'
    input_spec = EvalInputSpec
    output_spec = AFNICommandOutputSpec

    def _format_arg(self, name, trait_spec, value):
        if name == 'in_file_a':
            arg = trait_spec.argstr % value
            if isdefined(self.inputs.start_idx):
                arg += '[%d..%d]' % (self.inputs.start_idx,
                                     self.inputs.stop_idx)
            if isdefined(self.inputs.single_idx):
                arg += '[%d]' % (self.inputs.single_idx)
            return arg
        return super(Eval, self)._format_arg(name, trait_spec, value)

    def _parse_inputs(self, skip=None):
        """Skip the arguments without argstr metadata
        """
        return super(
            Eval, self)._parse_inputs(skip=('start_idx', 'stop_idx', 'other'))


class FWHMxInputSpec(CommandLineInputSpec):
    in_file = File(
        desc='input dataset', argstr='-input %s', mandatory=True, exists=True)
    out_file = File(
        argstr='> %s',
        name_source='in_file',
        name_template='%s_fwhmx.out',
        position=-1,
        keep_extension=False,
        desc='output file')
    out_subbricks = File(
        argstr='-out %s',
        name_source='in_file',
        name_template='%s_subbricks.out',
        keep_extension=False,
        desc='output file listing the subbricks FWHM')
    mask = File(
        desc='use only voxels that are nonzero in mask',
        argstr='-mask %s',
        exists=True)
    automask = traits.Bool(
        False,
        usedefault=True,
        argstr='-automask',
        desc='compute a mask from THIS dataset, a la 3dAutomask')
    detrend = traits.Either(
        traits.Bool(),
        traits.Int(),
        default=False,
        argstr='-detrend',
        xor=['demed'],
        usedefault=True,
        desc='instead of demed (0th order detrending), detrend to the '
        'specified order.  If order is not given, the program picks '
        'q=NT/30. -detrend disables -demed, and includes -unif.')
    demed = traits.Bool(
        False,
        argstr='-demed',
        xor=['detrend'],
        desc='If the input dataset has more than one sub-brick (e.g., has a '
        'time axis), then subtract the median of each voxel\'s time '
        'series before processing FWHM. This will tend to remove '
        'intrinsic spatial structure and leave behind the noise.')
    unif = traits.Bool(
        False,
        argstr='-unif',
        desc='If the input dataset has more than one sub-brick, then '
        'normalize each voxel\'s time series to have the same MAD before '
        'processing FWHM.')
    out_detrend = File(
        argstr='-detprefix %s',
        name_source='in_file',
        name_template='%s_detrend',
        keep_extension=False,
        desc='Save the detrended file into a dataset')
    geom = traits.Bool(
        argstr='-geom',
        xor=['arith'],
        desc='if in_file has more than one sub-brick, compute the final '
        'estimate as the geometric mean of the individual sub-brick FWHM '
        'estimates')
    arith = traits.Bool(
        argstr='-arith',
        xor=['geom'],
        desc='if in_file has more than one sub-brick, compute the final '
        'estimate as the arithmetic mean of the individual sub-brick '
        'FWHM estimates')
    combine = traits.Bool(
        argstr='-combine',
        desc='combine the final measurements along each axis')
    compat = traits.Bool(
        argstr='-compat', desc='be compatible with the older 3dFWHM')
    acf = traits.Either(
        traits.Bool(),
        File(),
        traits.Tuple(File(exists=True), traits.Float()),
        default=False,
        usedefault=True,
        argstr='-acf',
        desc='computes the spatial autocorrelation')


class FWHMxOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='output file')
    out_subbricks = File(exists=True, desc='output file (subbricks)')
    out_detrend = File(desc='output file, detrended')
    fwhm = traits.Either(
        traits.Tuple(traits.Float(), traits.Float(), traits.Float()),
        traits.Tuple(traits.Float(), traits.Float(), traits.Float(),
                     traits.Float()),
        desc='FWHM along each axis')
    acf_param = traits.Either(
        traits.Tuple(traits.Float(), traits.Float(), traits.Float()),
        traits.Tuple(traits.Float(), traits.Float(), traits.Float(),
                     traits.Float()),
        desc='fitted ACF model parameters')
    out_acf = File(exists=True, desc='output acf file')


class FWHMx(AFNICommandBase):
    """
    Unlike the older 3dFWHM, this program computes FWHMs for all sub-bricks
    in the input dataset, each one separately.  The output for each one is
    written to the file specified by '-out'.  The mean (arithmetic or geometric)
    of all the FWHMs along each axis is written to stdout.  (A non-positive
    output value indicates something bad happened; e.g., FWHM in z is meaningless
    for a 2D dataset; the estimation method computed incoherent intermediate results.)

    For complete details, see the `3dFWHMx Documentation.
    <https://afni.nimh.nih.gov/pub../pub/dist/doc/program_help/3dFWHMx.html>`_

    Examples
    --------

    >>> from nipype.interfaces import afni
    >>> fwhm = afni.FWHMx()
    >>> fwhm.inputs.in_file = 'functional.nii'
    >>> fwhm.cmdline
    '3dFWHMx -input functional.nii -out functional_subbricks.out > functional_fwhmx.out'
    >>> res = fwhm.run()  # doctest: +SKIP


    (Classic) METHOD:

      * Calculate ratio of variance of first differences to data variance.
      * Should be the same as 3dFWHM for a 1-brick dataset.
        (But the output format is simpler to use in a script.)


    .. note:: IMPORTANT NOTE [AFNI > 16]

      A completely new method for estimating and using noise smoothness values is
      now available in 3dFWHMx and 3dClustSim. This method is implemented in the
      '-acf' options to both programs.  'ACF' stands for (spatial) AutoCorrelation
      Function, and it is estimated by calculating moments of differences out to
      a larger radius than before.

      Notably, real FMRI data does not actually have a Gaussian-shaped ACF, so the
      estimated ACF is then fit (in 3dFWHMx) to a mixed model (Gaussian plus
      mono-exponential) of the form

        .. math::

          ACF(r) = a * exp(-r*r/(2*b*b)) + (1-a)*exp(-r/c)


      where :math:`r` is the radius, and :math:`a, b, c` are the fitted parameters.
      The apparent FWHM from this model is usually somewhat larger in real data
      than the FWHM estimated from just the nearest-neighbor differences used
      in the 'classic' analysis.

      The longer tails provided by the mono-exponential are also significant.
      3dClustSim has also been modified to use the ACF model given above to generate
      noise random fields.


    .. note:: TL;DR or summary

      The take-awaymessage is that the 'classic' 3dFWHMx and
      3dClustSim analysis, using a pure Gaussian ACF, is not very correct for
      FMRI data -- I cannot speak for PET or MEG data.


    .. warning::

      Do NOT use 3dFWHMx on the statistical results (e.g., '-bucket') from
      3dDeconvolve or 3dREMLfit!!!  The function of 3dFWHMx is to estimate
      the smoothness of the time series NOISE, not of the statistics. This
      proscription is especially true if you plan to use 3dClustSim next!!


    .. note:: Recommendations

      * For FMRI statistical purposes, you DO NOT want the FWHM to reflect
        the spatial structure of the underlying anatomy.  Rather, you want
        the FWHM to reflect the spatial structure of the noise.  This means
        that the input dataset should not have anatomical (spatial) structure.
      * One good form of input is the output of '3dDeconvolve -errts', which is
        the dataset of residuals left over after the GLM fitted signal model is
        subtracted out from each voxel's time series.
      * If you don't want to go to that much trouble, use '-detrend' to approximately
        subtract out the anatomical spatial structure, OR use the output of 3dDetrend
        for the same purpose.
      * If you do not use '-detrend', the program attempts to find non-zero spatial
        structure in the input, and will print a warning message if it is detected.


    .. note:: Notes on -demend

      * I recommend this option, and it is not the default only for historical
        compatibility reasons.  It may become the default someday.
      * It is already the default in program 3dBlurToFWHM. This is the same detrending
        as done in 3dDespike; using 2*q+3 basis functions for q > 0.
      * If you don't use '-detrend', the program now [Aug 2010] checks if a large number
        of voxels are have significant nonzero means. If so, the program will print a
        warning message suggesting the use of '-detrend', since inherent spatial
        structure in the image will bias the estimation of the FWHM of the image time
        series NOISE (which is usually the point of using 3dFWHMx).


    """
    _cmd = '3dFWHMx'
    input_spec = FWHMxInputSpec
    output_spec = FWHMxOutputSpec

    references_ = [
        {
            'entry':
            BibTeX('@article{CoxReynoldsTaylor2016,'
                   'author={R.W. Cox, R.C. Reynolds, and P.A. Taylor},'
                   'title={AFNI and clustering: false positive rates redux},'
                   'journal={bioRxiv},'
                   'year={2016},'
                   '}'),
            'tags': ['method'],
        },
    ]
    _acf = True

    def _parse_inputs(self, skip=None):
        if not self.inputs.detrend:
            if skip is None:
                skip = []
            skip += ['out_detrend']
        return super(FWHMx, self)._parse_inputs(skip=skip)

    def _format_arg(self, name, trait_spec, value):
        if name == 'detrend':
            if isinstance(value, bool):
                if value:
                    return trait_spec.argstr
                else:
                    return None
            elif isinstance(value, int):
                return trait_spec.argstr + ' %d' % value

        if name == 'acf':
            if isinstance(value, bool):
                if value:
                    return trait_spec.argstr
                else:
                    self._acf = False
                    return None
            elif isinstance(value, tuple):
                return trait_spec.argstr + ' %s %f' % value
            elif isinstance(value, (str, bytes)):
                return trait_spec.argstr + ' ' + value
        return super(FWHMx, self)._format_arg(name, trait_spec, value)

    def _list_outputs(self):
        outputs = super(FWHMx, self)._list_outputs()

        if self.inputs.detrend:
            fname, ext = op.splitext(self.inputs.in_file)
            if '.gz' in ext:
                _, ext2 = op.splitext(fname)
                ext = ext2 + ext
            outputs['out_detrend'] += ext
        else:
            outputs['out_detrend'] = Undefined

        sout = np.loadtxt(outputs['out_file'])

        # handle newer versions of AFNI
        if sout.size == 8:
            outputs['fwhm'] = tuple(sout[0, :])
        else:
            outputs['fwhm'] = tuple(sout)

        if self._acf:
            assert sout.size == 8, "Wrong number of elements in %s" % str(sout)
            outputs['acf_param'] = tuple(sout[1])

            outputs['out_acf'] = op.abspath('3dFWHMx.1D')
            if isinstance(self.inputs.acf, (str, bytes)):
                outputs['out_acf'] = op.abspath(self.inputs.acf)

        return outputs


class MaskToolInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file or files to 3dmask_tool',
        argstr='-input %s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        name_template='%s_mask',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file')
    count = traits.Bool(
        desc='Instead of created a binary 0/1 mask dataset, create one with '
        'counts of voxel overlap, i.e., each voxel will contain the '
        'number of masks that it is set in.',
        argstr='-count',
        position=2)
    datum = traits.Enum(
        'byte',
        'short',
        'float',
        argstr='-datum %s',
        desc='specify data type for output. Valid types are \'byte\', '
        '\'short\' and \'float\'.')
    dilate_inputs = Str(
        desc='Use this option to dilate and/or erode datasets as they are '
        'read. ex. \'5 -5\' to dilate and erode 5 times',
        argstr='-dilate_inputs %s')
    dilate_results = Str(
        desc='dilate and/or erode combined mask at the given levels.',
        argstr='-dilate_results %s')
    frac = traits.Float(
        desc='When combining masks (across datasets and sub-bricks), use '
        'this option to restrict the result to a certain fraction of the '
        'set of volumes',
        argstr='-frac %s')
    inter = traits.Bool(
        desc='intersection, this means -frac 1.0', argstr='-inter')
    union = traits.Bool(desc='union, this means -frac 0', argstr='-union')
    fill_holes = traits.Bool(
        desc='This option can be used to fill holes in the resulting mask, '
        'i.e. after all other processing has been done.',
        argstr='-fill_holes')
    fill_dirs = Str(
        desc='fill holes only in the given directions. This option is for use '
        'with -fill holes. should be a single string that specifies '
        '1-3 of the axes using {x,y,z} labels (i.e. dataset axis order), '
        'or using the labels in {R,L,A,P,I,S}.',
        argstr='-fill_dirs %s',
        requires=['fill_holes'])
    verbose = traits.Int(
        desc='specify verbosity level, for 0 to 3', argstr='-verb %s')


class MaskToolOutputSpec(TraitedSpec):
    out_file = File(desc='mask file', exists=True)


class MaskTool(AFNICommand):
    """3dmask_tool - for combining/dilating/eroding/filling masks

    For complete details, see the `3dmask_tool Documentation.
    <https://afni.nimh.nih.gov/pub../pub/dist/doc/program_help/3dmask_tool.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> masktool = afni.MaskTool()
    >>> masktool.inputs.in_file = 'functional.nii'
    >>> masktool.inputs.outputtype = 'NIFTI'
    >>> masktool.cmdline
    '3dmask_tool -prefix functional_mask.nii -input functional.nii'
    >>> res = automask.run()  # doctest: +SKIP

    """

    _cmd = '3dmask_tool'
    input_spec = MaskToolInputSpec
    output_spec = MaskToolOutputSpec


class MergeInputSpec(AFNICommandInputSpec):
    in_files = InputMultiPath(
        File(desc='input file to 3dmerge', exists=True),
        argstr='%s',
        position=-1,
        mandatory=True,
        copyfile=False)
    out_file = File(
        name_template='%s_merge',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_files')
    doall = traits.Bool(
        desc='apply options to all sub-bricks in dataset', argstr='-doall')
    blurfwhm = traits.Int(
        desc='FWHM blur value (mm)', argstr='-1blur_fwhm %d', units='mm')


class Merge(AFNICommand):
    """Merge or edit volumes using AFNI 3dmerge command

    For complete details, see the `3dmerge Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dmerge.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> merge = afni.Merge()
    >>> merge.inputs.in_files = ['functional.nii', 'functional2.nii']
    >>> merge.inputs.blurfwhm = 4
    >>> merge.inputs.doall = True
    >>> merge.inputs.out_file = 'e7.nii'
    >>> merge.cmdline
    '3dmerge -1blur_fwhm 4 -doall -prefix e7.nii functional.nii functional2.nii'
    >>> res = merge.run()  # doctest: +SKIP

    """

    _cmd = '3dmerge'
    input_spec = MergeInputSpec
    output_spec = AFNICommandOutputSpec


class NotesInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3dNotes',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)
    add = Str(desc='note to add', argstr='-a "%s"')
    add_history = Str(
        desc='note to add to history', argstr='-h "%s"', xor=['rep_history'])
    rep_history = Str(
        desc='note with which to replace history',
        argstr='-HH "%s"',
        xor=['add_history'])
    delete = traits.Int(desc='delete note number num', argstr='-d %d')
    ses = traits.Bool(desc='print to stdout the expanded notes', argstr='-ses')
    out_file = File(desc='output image file name', argstr='%s')


class Notes(CommandLine):
    """A program to add, delete, and show notes for AFNI datasets.

    For complete details, see the `3dNotes Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dNotes.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> notes = afni.Notes()
    >>> notes.inputs.in_file = 'functional.HEAD'
    >>> notes.inputs.add = 'This note is added.'
    >>> notes.inputs.add_history = 'This note is added to history.'
    >>> notes.cmdline
    '3dNotes -a "This note is added." -h "This note is added to history." functional.HEAD'
    >>> res = notes.run()  # doctest: +SKIP
    """

    _cmd = '3dNotes'
    input_spec = NotesInputSpec
    output_spec = AFNICommandOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.in_file)
        return outputs


class NwarpApplyInputSpec(CommandLineInputSpec):
    in_file = traits.Either(
        File(exists=True),
        traits.List(File(exists=True)),
        mandatory=True,
        argstr='-source %s',
        desc='the name of the dataset to be warped '
        'can be multiple datasets')
    warp = traits.String(
        desc='the name of the warp dataset. '
        'multiple warps can be concatenated (make sure they exist)',
        argstr='-nwarp %s',
        mandatory=True)
    inv_warp = traits.Bool(
        desc='After the warp specified in \'-nwarp\' is computed, invert it',
        argstr='-iwarp')
    master = traits.File(
        exists=True,
        desc='the name of the master dataset, which defines the output grid',
        argstr='-master %s')
    interp = traits.Enum(
        'NN',
        'nearestneighbour',
        'nearestneighbor',
        'linear',
        'trilinear',
        'cubic',
        'tricubic',
        'quintic',
        'triquintic',
        'wsinc5',
        desc='defines interpolation method to use during warp',
        argstr='-interp %s',
        default='wsinc5')
    ainterp = traits.Enum(
        'NN',
        'nearestneighbour',
        'nearestneighbor',
        'linear',
        'trilinear',
        'cubic',
        'tricubic',
        'quintic',
        'triquintic',
        'wsinc5',
        desc='specify a different interpolation method than might '
        'be used for the warp',
        argstr='-ainterp %s',
        default='wsinc5')
    out_file = File(
        name_template='%s_Nwarp',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file')
    short = traits.Bool(
        desc='Write output dataset using 16-bit short integers, rather than '
        'the usual 32-bit floats.',
        argstr='-short')
    quiet = traits.Bool(
        desc='don\'t be verbose :(', argstr='-quiet', xor=['verb'])
    verb = traits.Bool(
        desc='be extra verbose :)', argstr='-verb', xor=['quiet'])


class NwarpApply(AFNICommandBase):
    """Program to apply a nonlinear 3D warp saved from 3dQwarp
    (or 3dNwarpCat, etc.) to a 3D dataset, to produce a warped
    version of the source dataset.

    For complete details, see the `3dNwarpApply Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dNwarpApply.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> nwarp = afni.NwarpApply()
    >>> nwarp.inputs.in_file = 'Fred+orig'
    >>> nwarp.inputs.master = 'NWARP'
    >>> nwarp.inputs.warp = "'Fred_WARP+tlrc Fred.Xaff12.1D'"
    >>> nwarp.cmdline
    "3dNwarpApply -source Fred+orig -master NWARP -prefix Fred+orig_Nwarp -nwarp \'Fred_WARP+tlrc Fred.Xaff12.1D\'"
    >>> res = nwarp.run()  # doctest: +SKIP

    """
    _cmd = '3dNwarpApply'
    input_spec = NwarpApplyInputSpec
    output_spec = AFNICommandOutputSpec


class NwarpCatInputSpec(AFNICommandInputSpec):
    in_files = traits.List(
        traits.Either(traits.File(),
                      traits.Tuple(
                          traits.Enum('IDENT', 'INV', 'SQRT', 'SQRTINV'),
                          traits.File())),
        desc="list of tuples of 3D warps and associated functions",
        mandatory=True,
        argstr="%s",
        position=-1)
    space = traits.String(
        desc='string to attach to the output dataset as its atlas space '
        'marker.',
        argstr='-space %s')
    inv_warp = traits.Bool(
        desc='invert the final warp before output', argstr='-iwarp')
    interp = traits.Enum(
        'linear',
        'quintic',
        'wsinc5',
        desc='specify a different interpolation method than might '
        'be used for the warp',
        argstr='-interp %s',
        default='wsinc5')
    expad = traits.Int(
        desc='Pad the nonlinear warps by the given number of voxels voxels in '
        'all directions. The warp displacements are extended by linear '
        'extrapolation from the faces of the input grid..',
        argstr='-expad %d')
    out_file = File(
        name_template='%s_NwarpCat',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_files')
    verb = traits.Bool(desc='be verbose', argstr='-verb')


class NwarpCat(AFNICommand):
    """Catenates (composes) 3D warps defined on a grid, OR via a matrix.

    .. note::

      * All transformations are from DICOM xyz (in mm) to DICOM xyz.

      * Matrix warps are in files that end in '.1D' or in '.txt'.  A matrix
        warp file should have 12 numbers in it, as output (for example), by
        '3dAllineate -1Dmatrix_save'.

      * Nonlinear warps are in dataset files (AFNI .HEAD/.BRIK or NIfTI .nii)
        with 3 sub-bricks giving the DICOM order xyz grid displacements in mm.

      * If all the input warps are matrices, then the output is a matrix
        and will be written to the file 'prefix.aff12.1D'.
        Unless the prefix already contains the string '.1D', in which case
        the filename is just the prefix.

      * If 'prefix' is just 'stdout', then the output matrix is written
        to standard output.
        In any of these cases, the output format is 12 numbers in one row.

      * If any of the input warps are datasets, they must all be defined on
        the same 3D grid!
        And of course, then the output will be a dataset on the same grid.
        However, you can expand the grid using the '-expad' option.

      * The order of operations in the final (output) warp is, for the
        case of 3 input warps:

            OUTPUT(x) = warp3( warp2( warp1(x) ) )

       That is, warp1 is applied first, then warp2, et cetera.
       The 3D x coordinates are taken from each grid location in the
       first dataset defined on a grid.

    For complete details, see the `3dNwarpCat Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dNwarpCat.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> nwarpcat = afni.NwarpCat()
    >>> nwarpcat.inputs.in_files = ['Q25_warp+tlrc.HEAD', ('IDENT', 'structural.nii')]
    >>> nwarpcat.inputs.out_file = 'Fred_total_WARP'
    >>> nwarpcat.cmdline
    "3dNwarpCat -prefix Fred_total_WARP Q25_warp+tlrc.HEAD 'IDENT(structural.nii)'"
    >>> res = nwarpcat.run()  # doctest: +SKIP

    """
    _cmd = '3dNwarpCat'
    input_spec = NwarpCatInputSpec
    output_spec = AFNICommandOutputSpec

    def _format_arg(self, name, spec, value):
        if name == 'in_files':
            return spec.argstr % (' '.join([
                "'" + v[0] + "(" + v[1] + ")'" if isinstance(v, tuple) else v
                for v in value
            ]))
        return super(NwarpCat, self)._format_arg(name, spec, value)

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._gen_fname(
                self.inputs.in_files[0][0], suffix='_NwarpCat')

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_file):
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        else:
            outputs['out_file'] = os.path.abspath(
                self._gen_fname(
                    self.inputs.in_files[0],
                    suffix='_NwarpCat+tlrc',
                    ext='.HEAD'))
        return outputs


class OneDToolPyInputSpec(AFNIPythonCommandInputSpec):
    in_file = File(
        desc='input file to OneDTool',
        argstr='-infile %s',
        mandatory=True,
        exists=True)
    set_nruns = traits.Int(
        desc='treat the input data as if it has nruns', argstr='-set_nruns %d')
    derivative = traits.Bool(
        desc=
        'take the temporal derivative of each vector (done as first backward difference)',
        argstr='-derivative')
    demean = traits.Bool(
        desc='demean each run (new mean of each run = 0.0)', argstr='-demean')
    out_file = File(
        desc='write the current 1D data to FILE',
        argstr='-write %s',
        xor=['show_cormat_warnings'])
    show_censor_count = traits.Bool(
        desc=
        'display the total number of censored TRs  Note : if input is a valid xmat.1D dataset, '
        'then the count will come from the header.  Otherwise the input is assumed to be a binary censor'
        'file, and zeros are simply counted.',
        argstr="-show_censor_count")
    censor_motion = traits.Tuple(
        (traits.Float(), File()),
        desc=
        'Tuple of motion limit and outfile prefix. need to also set set_nruns -r set_run_lengths',
        argstr="-censor_motion %f %s")
    censor_prev_TR = traits.Bool(
        desc='for each censored TR, also censor previous',
        argstr='-censor_prev_TR')
    show_trs_uncensored = traits.Enum(
        'comma',
        'space',
        'encoded',
        'verbose',
        desc=
        'display a list of TRs which were not censored in the specified style',
        argstr='-show_trs_uncensored %s')
    show_cormat_warnings = traits.File(
        desc='Write cormat warnings to a file',
        argstr="-show_cormat_warnings |& tee %s",
        default="out.cormat_warn.txt",
        usedefault=False,
        position=-1,
        xor=['out_file'])
    show_indices_interest = traits.Bool(
        desc="display column indices for regs of interest",
        argstr="-show_indices_interest")
    show_trs_run = traits.Int(
        desc="restrict -show_trs_[un]censored to the given 1-based run",
        argstr="-show_trs_run %d")


class OneDToolPyOutputSpec(AFNICommandOutputSpec):
    out_file = File(desc='output of 1D_tool.py')


class OneDToolPy(AFNIPythonCommand):
    """This program is meant to read/manipulate/write/diagnose 1D datasets.
    Input can be specified using AFNI sub-brick[]/time{} selectors.

    >>> from nipype.interfaces import afni
    >>> odt = afni.OneDToolPy()
    >>> odt.inputs.in_file = 'f1.1D'
    >>> odt.inputs.set_nruns = 3
    >>> odt.inputs.demean = True
    >>> odt.inputs.out_file = 'motion_dmean.1D'
    >>> odt.cmdline # doctest: +ELLIPSIS
    'python2 ...1d_tool.py -demean -infile f1.1D -write motion_dmean.1D -set_nruns 3'
     >>> res = odt.run()  # doctest: +SKIP
"""

    _cmd = '1d_tool.py'

    input_spec = OneDToolPyInputSpec
    output_spec = OneDToolPyOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if isdefined(self.inputs.out_file):
            outputs['out_file'] = os.path.join(os.getcwd(),
                                               self.inputs.out_file)
        if isdefined(self.inputs.show_cormat_warnings):
            outputs['out_file'] = os.path.join(
                os.getcwd(), self.inputs.show_cormat_warnings)
        if isdefined(self.inputs.censor_motion):
            outputs['out_file'] = os.path.join(os.getcwd(),
                                               self.inputs.censor_motion[1] +
                                               '_censor.1D')
        return outputs


class RefitInputSpec(CommandLineInputSpec):
    in_file = File(
        desc='input file to 3drefit',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=True)
    deoblique = traits.Bool(
        desc='replace current transformation matrix with cardinal matrix',
        argstr='-deoblique')
    xorigin = Str(
        desc='x distance for edge voxel offset', argstr='-xorigin %s')
    yorigin = Str(
        desc='y distance for edge voxel offset', argstr='-yorigin %s')
    zorigin = Str(
        desc='z distance for edge voxel offset', argstr='-zorigin %s')
    duporigin_file = File(
        argstr='-duporigin %s',
        exists=True,
        desc='Copies the xorigin, yorigin, and zorigin values from the header '
        'of the given dataset')
    xdel = traits.Float(desc='new x voxel dimension in mm', argstr='-xdel %f')
    ydel = traits.Float(desc='new y voxel dimension in mm', argstr='-ydel %f')
    zdel = traits.Float(desc='new z voxel dimension in mm', argstr='-zdel %f')
    xyzscale = traits.Float(
        desc='Scale the size of the dataset voxels by the given factor',
        argstr='-xyzscale %f')
    space = traits.Enum(
        'TLRC',
        'MNI',
        'ORIG',
        argstr='-space %s',
        desc='Associates the dataset with a specific template type, e.g. '
        'TLRC, MNI, ORIG')
    atrcopy = traits.Tuple(
        traits.File(exists=True),
        traits.Str(),
        argstr='-atrcopy %s %s',
        desc='Copy AFNI header attribute from the given file into the header '
        'of the dataset(s) being modified. For more information on AFNI '
        'header attributes, see documentation file README.attributes. '
        'More than one \'-atrcopy\' option can be used. For AFNI '
        'advanced users only. Do NOT use -atrcopy or -atrstring with '
        'other modification options. See also -copyaux.')
    atrstring = traits.Tuple(
        traits.Str(),
        traits.Str(),
        argstr='-atrstring %s %s',
        desc='Copy the last given string into the dataset(s) being modified, '
        'giving it the attribute name given by the last string.'
        'To be safe, the last string should be in quotes.')
    atrfloat = traits.Tuple(
        traits.Str(),
        traits.Str(),
        argstr='-atrfloat %s %s',
        desc='Create or modify floating point attributes. '
        'The input values may be specified as a single string in quotes '
        'or as a 1D filename or string, example '
        '\'1 0.2 0 0 -0.2 1 0 0 0 0 1 0\' or '
        'flipZ.1D or \'1D:1,0.2,2@0,-0.2,1,2@0,2@0,1,0\'')
    atrint = traits.Tuple(
        traits.Str(),
        traits.Str(),
        argstr='-atrint %s %s',
        desc='Create or modify integer attributes. '
        'The input values may be specified as a single string in quotes '
        'or as a 1D filename or string, example '
        '\'1 0 0 0 0 1 0 0 0 0 1 0\' or '
        'flipZ.1D or \'1D:1,0,2@0,-0,1,2@0,2@0,1,0\'')
    saveatr = traits.Bool(
        argstr='-saveatr',
        desc='(default) Copy the attributes that are known to AFNI into '
        'the dset->dblk structure thereby forcing changes to known '
        'attributes to be present in the output. This option only makes '
        'sense with -atrcopy.')
    nosaveatr = traits.Bool(argstr='-nosaveatr', desc='Opposite of -saveatr')


class Refit(AFNICommandBase):
    """Changes some of the information inside a 3D dataset's header

    For complete details, see the `3drefit Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3drefit.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> refit = afni.Refit()
    >>> refit.inputs.in_file = 'structural.nii'
    >>> refit.inputs.deoblique = True
    >>> refit.cmdline
    '3drefit -deoblique structural.nii'
    >>> res = refit.run()  # doctest: +SKIP

    >>> refit_2 = afni.Refit()
    >>> refit_2.inputs.in_file = 'structural.nii'
    >>> refit_2.inputs.atrfloat = ("IJK_TO_DICOM_REAL", "'1 0.2 0 0 -0.2 1 0 0 0 0 1 0'")
    >>> refit_2.cmdline
    "3drefit -atrfloat IJK_TO_DICOM_REAL '1 0.2 0 0 -0.2 1 0 0 0 0 1 0' structural.nii"
    >>> res = refit_2.run()  # doctest: +SKIP
    """
    _cmd = '3drefit'
    input_spec = RefitInputSpec
    output_spec = AFNICommandOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.in_file)
        return outputs


class ResampleInputSpec(AFNICommandInputSpec):

    in_file = File(
        desc='input file to 3dresample',
        argstr='-inset %s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        name_template='%s_resample',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file')
    orientation = Str(desc='new orientation code', argstr='-orient %s')
    resample_mode = traits.Enum(
        'NN',
        'Li',
        'Cu',
        'Bk',
        argstr='-rmode %s',
        desc='resampling method from set {"NN", "Li", "Cu", "Bk"}. These are '
        'for "Nearest Neighbor", "Linear", "Cubic" and "Blocky"'
        'interpolation, respectively. Default is NN.')
    voxel_size = traits.Tuple(
        *[traits.Float()] * 3,
        argstr='-dxyz %f %f %f',
        desc='resample to new dx, dy and dz')
    master = traits.File(
        argstr='-master %s', desc='align dataset grid to a reference file')


class Resample(AFNICommand):
    """Resample or reorient an image using AFNI 3dresample command

    For complete details, see the `3dresample Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dresample.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> resample = afni.Resample()
    >>> resample.inputs.in_file = 'functional.nii'
    >>> resample.inputs.orientation= 'RPI'
    >>> resample.inputs.outputtype = 'NIFTI'
    >>> resample.cmdline
    '3dresample -orient RPI -prefix functional_resample.nii -inset functional.nii'
    >>> res = resample.run()  # doctest: +SKIP

    """

    _cmd = '3dresample'
    input_spec = ResampleInputSpec
    output_spec = AFNICommandOutputSpec


class TCatInputSpec(AFNICommandInputSpec):
    in_files = InputMultiPath(
        File(exists=True),
        desc='input file to 3dTcat',
        argstr=' %s',
        position=-1,
        mandatory=True,
        copyfile=False)
    out_file = File(
        name_template='%s_tcat',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_files')
    rlt = traits.Enum(
        '',
        '+',
        '++',
        argstr='-rlt%s',
        desc='Remove linear trends in each voxel time series loaded from each '
        'input dataset, SEPARATELY. Option -rlt removes the least squares '
        'fit of \'a+b*t\' to each voxel time series. Option -rlt+ adds '
        'dataset mean back in. Option -rlt++ adds overall mean of all '
        'dataset timeseries back in.',
        position=1)
    verbose = traits.Bool(
        desc='Print out some verbose output as the program', argstr='-verb')


class TCat(AFNICommand):
    """Concatenate sub-bricks from input datasets into one big 3D+time dataset.

    TODO Replace InputMultiPath in_files with Traits.List, if possible. Current
    version adds extra whitespace.

    For complete details, see the `3dTcat Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTcat.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> tcat = afni.TCat()
    >>> tcat.inputs.in_files = ['functional.nii', 'functional2.nii']
    >>> tcat.inputs.out_file= 'functional_tcat.nii'
    >>> tcat.inputs.rlt = '+'
    >>> tcat.cmdline
    '3dTcat -rlt+ -prefix functional_tcat.nii functional.nii functional2.nii'
    >>> res = tcat.run()  # doctest: +SKIP

    """

    _cmd = '3dTcat'
    input_spec = TCatInputSpec
    output_spec = AFNICommandOutputSpec


class TCatSBInputSpec(AFNICommandInputSpec):
    in_files = traits.List(
        traits.Tuple(File(exists=True), Str()),
        desc='List of tuples of file names and subbrick selectors as strings.'
        'Don\'t forget to protect the single quotes in the subbrick selector'
        'so the contents are protected from the command line interpreter.',
        argstr='%s%s ...',
        position=-1,
        mandatory=True,
        copyfile=False)
    out_file = File(
        desc='output image file name', argstr='-prefix %s', genfile=True)
    rlt = traits.Enum(
        '',
        '+',
        '++',
        argstr='-rlt%s',
        desc='Remove linear trends in each voxel time series loaded from each '
        'input dataset, SEPARATELY. Option -rlt removes the least squares '
        'fit of \'a+b*t\' to each voxel time series. Option -rlt+ adds '
        'dataset mean back in. Option -rlt++ adds overall mean of all '
        'dataset timeseries back in.',
        position=1)


class TCatSubBrick(AFNICommand):
    """Hopefully a temporary function to allow sub-brick selection until
    afni file managment is improved.

    For complete details, see the `3dTcat Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTcat.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> tcsb = afni.TCatSubBrick()
    >>> tcsb.inputs.in_files = [('functional.nii', "'{2..$}'"), ('functional2.nii', "'{2..$}'")]
    >>> tcsb.inputs.out_file= 'functional_tcat.nii'
    >>> tcsb.inputs.rlt = '+'
    >>> tcsb.cmdline
    "3dTcat -rlt+ -prefix functional_tcat.nii functional.nii'{2..$}' functional2.nii'{2..$}' "
    >>> res = tcsb.run()  # doctest: +SKIP

    """

    _cmd = '3dTcat'
    input_spec = TCatSBInputSpec
    output_spec = AFNICommandOutputSpec

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._gen_fname(self.inputs.in_files[0][0], suffix='_tcat')


class TStatInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3dTstat',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        name_template='%s_tstat',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file')
    mask = File(desc='mask file', argstr='-mask %s', exists=True)
    options = Str(desc='selected statistical output', argstr='%s')


class TStat(AFNICommand):
    """Compute voxel-wise statistics using AFNI 3dTstat command

    For complete details, see the `3dTstat Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTstat.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> tstat = afni.TStat()
    >>> tstat.inputs.in_file = 'functional.nii'
    >>> tstat.inputs.args = '-mean'
    >>> tstat.inputs.out_file = 'stats'
    >>> tstat.cmdline
    '3dTstat -mean -prefix stats functional.nii'
    >>> res = tstat.run()  # doctest: +SKIP

    """

    _cmd = '3dTstat'
    input_spec = TStatInputSpec
    output_spec = AFNICommandOutputSpec


class To3DInputSpec(AFNICommandInputSpec):
    out_file = File(
        name_template='%s',
        desc='output image file name',
        argstr='-prefix %s',
        name_source=['in_folder'])
    in_folder = Directory(
        desc='folder with DICOM images to convert',
        argstr='%s/*.dcm',
        position=-1,
        mandatory=True,
        exists=True)
    filetype = traits.Enum(
        'spgr',
        'fse',
        'epan',
        'anat',
        'ct',
        'spct',
        'pet',
        'mra',
        'bmap',
        'diff',
        'omri',
        'abuc',
        'fim',
        'fith',
        'fico',
        'fitt',
        'fift',
        'fizt',
        'fict',
        'fibt',
        'fibn',
        'figt',
        'fipt',
        'fbuc',
        argstr='-%s',
        desc='type of datafile being converted')
    skipoutliers = traits.Bool(
        desc='skip the outliers check', argstr='-skip_outliers')
    assumemosaic = traits.Bool(
        desc='assume that Siemens image is mosaic',
        argstr='-assume_dicom_mosaic')
    datatype = traits.Enum(
        'short',
        'float',
        'byte',
        'complex',
        desc='set output file datatype',
        argstr='-datum %s')
    funcparams = Str(
        desc='parameters for functional data', argstr='-time:zt %s alt+z2')


class To3D(AFNICommand):
    """Create a 3D dataset from 2D image files using AFNI to3d command

    For complete details, see the `to3d Documentation
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/to3d.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> to3d = afni.To3D()
    >>> to3d.inputs.datatype = 'float'
    >>> to3d.inputs.in_folder = '.'
    >>> to3d.inputs.out_file = 'dicomdir.nii'
    >>> to3d.inputs.filetype = 'anat'
    >>> to3d.cmdline  # doctest: +ELLIPSIS
    'to3d -datum float -anat -prefix dicomdir.nii ./*.dcm'
    >>> res = to3d.run()  # doctest: +SKIP

   """

    _cmd = 'to3d'
    input_spec = To3DInputSpec
    output_spec = AFNICommandOutputSpec


class UndumpInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3dUndump, whose geometry will determine'
        'the geometry of the output',
        argstr='-master %s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file')
    mask_file = File(
        desc='mask image file name. Only voxels that are nonzero in the mask '
        'can be set.',
        argstr='-mask %s')
    datatype = traits.Enum(
        'short',
        'float',
        'byte',
        desc='set output file datatype',
        argstr='-datum %s')
    default_value = traits.Float(
        desc='default value stored in each input voxel that does not have '
        'a value supplied in the input file',
        argstr='-dval %f')
    fill_value = traits.Float(
        desc='value, used for each voxel in the output dataset that is NOT '
        'listed in the input file',
        argstr='-fval %f')
    coordinates_specification = traits.Enum(
        'ijk',
        'xyz',
        desc='Coordinates in the input file as index triples (i, j, k) '
        'or spatial coordinates (x, y, z) in mm',
        argstr='-%s')
    srad = traits.Float(
        desc='radius in mm of the sphere that will be filled about each input '
        '(x,y,z) or (i,j,k) voxel. If the radius is not given, or is 0, '
        'then each input data line sets the value in only one voxel.',
        argstr='-srad %f')
    orient = traits.Tuple(
        traits.Enum('R', 'L'),
        traits.Enum('A', 'P'),
        traits.Enum('I', 'S'),
        desc='Specifies the coordinate order used by -xyz. '
        'The code must be 3 letters, one each from the pairs '
        '{R,L} {A,P} {I,S}.  The first letter gives the '
        'orientation of the x-axis, the second the orientation '
        'of the y-axis, the third the z-axis: '
        'R = right-to-left         L = left-to-right '
        'A = anterior-to-posterior P = posterior-to-anterior '
        'I = inferior-to-superior  S = superior-to-inferior '
        'If -orient isn\'t used, then the coordinate order of the '
        '-master (in_file) dataset is used to interpret (x,y,z) inputs.',
        argstr='-orient %s')
    head_only = traits.Bool(
        desc='create only the .HEAD file which gets exploited by '
        'the AFNI matlab library function New_HEAD.m',
        argstr='-head_only')


class UndumpOutputSpec(TraitedSpec):
    out_file = File(desc='assembled file', exists=True)


class Undump(AFNICommand):
    """3dUndump - Assembles a 3D dataset from an ASCII list of coordinates and
    (optionally) values.

     The input file(s) are ASCII files, with one voxel specification per
     line.  A voxel specification is 3 numbers (-ijk or -xyz coordinates),
     with an optional 4th number giving the voxel value.  For example:

     1 2 3
     3 2 1 5
     5.3 6.2 3.7
     // this line illustrates a comment

     The first line puts a voxel (with value given by '-dval') at point
     (1,2,3).  The second line puts a voxel (with value 5) at point (3,2,1).
     The third line puts a voxel (with value given by '-dval') at point
     (5.3,6.2,3.7).  If -ijk is in effect, and fractional coordinates
     are given, they will be rounded to the nearest integers; for example,
     the third line would be equivalent to (i,j,k) = (5,6,4).


    For complete details, see the `3dUndump Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dUndump.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> unndump = afni.Undump()
    >>> unndump.inputs.in_file = 'structural.nii'
    >>> unndump.inputs.out_file = 'structural_undumped.nii'
    >>> unndump.cmdline
    '3dUndump -prefix structural_undumped.nii -master structural.nii'
    >>> res = unndump.run()  # doctest: +SKIP

    """

    _cmd = '3dUndump'
    input_spec = UndumpInputSpec
    output_spec = UndumpOutputSpec


class UnifizeInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3dUnifize',
        argstr='-input %s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        name_template='%s_unifized',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file')
    t2 = traits.Bool(
        desc='Treat the input as if it were T2-weighted, rather than '
        'T1-weighted. This processing is done simply by inverting '
        'the image contrast, processing it as if that result were '
        'T1-weighted, and then re-inverting the results '
        'counts of voxel overlap, i.e., each voxel will contain the '
        'number of masks that it is set in.',
        argstr='-T2')
    gm = traits.Bool(
        desc='Also scale to unifize \'gray matter\' = lower intensity voxels '
        '(to aid in registering images from different scanners).',
        argstr='-GM')
    urad = traits.Float(
        desc='Sets the radius (in voxels) of the ball used for the sneaky '
        'trick. Default value is 18.3, and should be changed '
        'proportionally if the dataset voxel size differs significantly '
        'from 1 mm.',
        argstr='-Urad %s')
    scale_file = File(
        desc='output file name to save the scale factor used at each voxel ',
        argstr='-ssave %s')
    no_duplo = traits.Bool(
        desc='Do NOT use the \'duplo down\' step; this can be useful for '
        'lower resolution datasets.',
        argstr='-noduplo')
    epi = traits.Bool(
        desc='Assume the input dataset is a T2 (or T2*) weighted EPI time '
        'series. After computing the scaling, apply it to ALL volumes '
        '(TRs) in the input dataset. That is, a given voxel will be '
        'scaled by the same factor at each TR. '
        'This option also implies \'-noduplo\' and \'-T2\'.'
        'This option turns off \'-GM\' if you turned it on.',
        argstr='-EPI',
        requires=['no_duplo', 't2'],
        xor=['gm'])
    rbt = traits.Tuple(
        traits.Float(),
        traits.Float(),
        traits.Float(),
        desc='Option for AFNI experts only.'
        'Specify the 3 parameters for the algorithm:\n'
        'R = radius; same as given by option \'-Urad\', [default=18.3]\n'
        'b = bottom percentile of normalizing data range, [default=70.0]\n'
        'r = top percentile of normalizing data range, [default=80.0]\n',
        argstr='-rbt %f %f %f')
    t2_up = traits.Float(
        desc='Option for AFNI experts only.'
        'Set the upper percentile point used for T2-T1 inversion. '
        'Allowed to be anything between 90 and 100 (inclusive), with '
        'default to 98.5  (for no good reason).',
        argstr='-T2up %f')
    cl_frac = traits.Float(
        desc='Option for AFNI experts only.'
        'Set the automask \'clip level fraction\'. Must be between '
        '0.1 and 0.9. A small fraction means to make the initial '
        'threshold for clipping (a la 3dClipLevel) smaller, which '
        'will tend to make the mask larger.  [default=0.1]',
        argstr='-clfrac %f')
    quiet = traits.Bool(
        desc='Don\'t print the progress messages.', argstr='-quiet')


class UnifizeOutputSpec(TraitedSpec):
    scale_file = File(desc='scale factor file')
    out_file = File(desc='unifized file', exists=True)


class Unifize(AFNICommand):
    """3dUnifize - for uniformizing image intensity

    * The input dataset is supposed to be a T1-weighted volume,
      possibly already skull-stripped (e.g., via 3dSkullStrip).
      However, this program can be a useful step to take BEFORE
      3dSkullStrip, since the latter program can fail if the input
      volume is strongly shaded -- 3dUnifize will (mostly) remove
      such shading artifacts.

    * The output dataset has the white matter (WM) intensity approximately
      uniformized across space, and scaled to peak at about 1000.

    * The output dataset is always stored in float format!

    * If the input dataset has more than 1 sub-brick, only sub-brick
      #0 will be processed!

    * Want to correct EPI datasets for nonuniformity?
      You can try the new and experimental [Mar 2017] '-EPI' option.

    * The principal motive for this program is for use in an image
      registration script, and it may or may not be useful otherwise.

    * This program replaces the older (and very different) 3dUniformize,
      which is no longer maintained and may sublimate at any moment.
      (In other words, we do not recommend the use of 3dUniformize.)

    For complete details, see the `3dUnifize Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dUnifize.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> unifize = afni.Unifize()
    >>> unifize.inputs.in_file = 'structural.nii'
    >>> unifize.inputs.out_file = 'structural_unifized.nii'
    >>> unifize.cmdline
    '3dUnifize -prefix structural_unifized.nii -input structural.nii'
    >>> res = unifize.run()  # doctest: +SKIP

    """

    _cmd = '3dUnifize'
    input_spec = UnifizeInputSpec
    output_spec = UnifizeOutputSpec


class ZCutUpInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3dZcutup',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        name_template='%s_zcutup',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file')
    keep = Str(desc='slice range to keep in output', argstr='-keep %s')


class ZCutUp(AFNICommand):
    """Cut z-slices from a volume using AFNI 3dZcutup command

    For complete details, see the `3dZcutup Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dZcutup.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> zcutup = afni.ZCutUp()
    >>> zcutup.inputs.in_file = 'functional.nii'
    >>> zcutup.inputs.out_file = 'functional_zcutup.nii'
    >>> zcutup.inputs.keep= '0 10'
    >>> zcutup.cmdline
    '3dZcutup -keep 0 10 -prefix functional_zcutup.nii functional.nii'
    >>> res = zcutup.run()  # doctest: +SKIP

    """

    _cmd = '3dZcutup'
    input_spec = ZCutUpInputSpec
    output_spec = AFNICommandOutputSpec


class GCORInputSpec(CommandLineInputSpec):
    in_file = File(
        desc='input dataset to compute the GCOR over',
        argstr='-input %s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)

    mask = File(
        desc='mask dataset, for restricting the computation',
        argstr='-mask %s',
        exists=True,
        copyfile=False)

    nfirst = traits.Int(
        0, argstr='-nfirst %d', desc='specify number of initial TRs to ignore')
    no_demean = traits.Bool(
        False,
        argstr='-no_demean',
        desc='do not (need to) demean as first step')


class GCOROutputSpec(TraitedSpec):
    out = traits.Float(desc='global correlation value')


class GCOR(CommandLine):
    """
    Computes the average correlation between every voxel
    and ever other voxel, over any give mask.


    For complete details, see the `@compute_gcor Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/@compute_gcor.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> gcor = afni.GCOR()
    >>> gcor.inputs.in_file = 'structural.nii'
    >>> gcor.inputs.nfirst = 4
    >>> gcor.cmdline
    '@compute_gcor -nfirst 4 -input structural.nii'
    >>> res = gcor.run()  # doctest: +SKIP

    """

    _cmd = '@compute_gcor'
    input_spec = GCORInputSpec
    output_spec = GCOROutputSpec

    def _run_interface(self, runtime):
        runtime = super(GCOR, self)._run_interface(runtime)

        gcor_line = [
            line.strip() for line in runtime.stdout.split('\n')
            if line.strip().startswith('GCOR = ')
        ][-1]
        setattr(self, '_gcor', float(gcor_line[len('GCOR = '):]))
        return runtime

    def _list_outputs(self):
        return {'out': getattr(self, '_gcor')}


class AxializeInputSpec(AFNICommandInputSpec):
    in_file = File(
        desc='input file to 3daxialize',
        argstr='%s',
        position=-2,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        name_template='%s_axialize',
        desc='output image file name',
        argstr='-prefix %s',
        name_source='in_file')
    verb = traits.Bool(desc='Print out a progerss report', argstr='-verb')
    sagittal = traits.Bool(
        desc='Do sagittal slice order [-orient ASL]',
        argstr='-sagittal',
        xor=['coronal', 'axial'])
    coronal = traits.Bool(
        desc='Do coronal slice order  [-orient RSA]',
        argstr='-coronal',
        xor=['sagittal', 'axial'])
    axial = traits.Bool(
        desc='Do axial slice order    [-orient RAI]'
        'This is the default AFNI axial order, and'
        'is the one currently required by the'
        'volume rendering plugin; this is also'
        'the default orientation output by this'
        "program (hence the program's name).",
        argstr='-axial',
        xor=['coronal', 'sagittal'])
    orientation = Str(desc='new orientation code', argstr='-orient %s')


class Axialize(AFNICommand):
    """Read in a dataset and write it out as a new dataset
         with the data brick oriented as axial slices.

    For complete details, see the `3dcopy Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3daxialize.html>`_

    Examples
    ========
    >>> from nipype.interfaces import afni
    >>> axial3d = afni.Axialize()
    >>> axial3d.inputs.in_file = 'functional.nii'
    >>> axial3d.inputs.out_file = 'axialized.nii'
    >>> axial3d.cmdline
    '3daxialize -prefix axialized.nii functional.nii'
    >>> res = axial3d.run()  # doctest: +SKIP

    """

    _cmd = '3daxialize'
    input_spec = AxializeInputSpec
    output_spec = AFNICommandOutputSpec


class ZcatInputSpec(AFNICommandInputSpec):
    in_files = InputMultiPath(
        File(desc='input files to 3dZcat', exists=True),
        argstr='%s',
        position=-1,
        mandatory=True,
        copyfile=False)
    out_file = File(
        name_template='%s_zcat',
        desc='output dataset prefix name (default \'zcat\')',
        argstr='-prefix %s',
        name_source='in_files')
    datum = traits.Enum(
        'byte',
        'short',
        'float',
        argstr='-datum %s',
        desc='specify data type for output. Valid types are \'byte\', '
        '\'short\' and \'float\'.')
    verb = traits.Bool(
        desc='print out some verbositiness as the program proceeds.',
        argstr='-verb')
    fscale = traits.Bool(
        desc='Force scaling of the output to the maximum integer '
        'range.  This only has effect if the output datum is '
        'byte or short (either forced or defaulted). This '
        'option is sometimes necessary to eliminate '
        'unpleasant truncation artifacts.',
        argstr='-fscale',
        xor=['nscale'])
    nscale = traits.Bool(
        desc='Don\'t do any scaling on output to byte or short '
        'datasets. This may be especially useful when '
        'operating on mask datasets whose output values '
        'are only 0\'s and 1\'s.',
        argstr='-nscale',
        xor=['fscale'])


class Zcat(AFNICommand):
    """Copies an image of one type to an image of the same
    or different type using 3dZcat command

    For complete details, see the `3dZcat Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dZcat.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> zcat = afni.Zcat()
    >>> zcat.inputs.in_files = ['functional2.nii', 'functional3.nii']
    >>> zcat.inputs.out_file = 'cat_functional.nii'
    >>> zcat.cmdline
    '3dZcat -prefix cat_functional.nii functional2.nii functional3.nii'
    >>> res = zcat.run()  # doctest: +SKIP
    """

    _cmd = '3dZcat'
    input_spec = ZcatInputSpec
    output_spec = AFNICommandOutputSpec


class ZeropadInputSpec(AFNICommandInputSpec):
    in_files = File(
        desc='input dataset',
        argstr='%s',
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False)
    out_file = File(
        name_template='zeropad',
        desc='output dataset prefix name (default \'zeropad\')',
        argstr='-prefix %s')
    I = traits.Int(
        desc='adds \'n\' planes of zero at the Inferior edge',
        argstr='-I %i',
        xor=['master'])
    S = traits.Int(
        desc='adds \'n\' planes of zero at the Superior edge',
        argstr='-S %i',
        xor=['master'])
    A = traits.Int(
        desc='adds \'n\' planes of zero at the Anterior edge',
        argstr='-A %i',
        xor=['master'])
    P = traits.Int(
        desc='adds \'n\' planes of zero at the Posterior edge',
        argstr='-P %i',
        xor=['master'])
    L = traits.Int(
        desc='adds \'n\' planes of zero at the Left edge',
        argstr='-L %i',
        xor=['master'])
    R = traits.Int(
        desc='adds \'n\' planes of zero at the Right edge',
        argstr='-R %i',
        xor=['master'])
    z = traits.Int(
        desc='adds \'n\' planes of zero on EACH of the '
        'dataset z-axis (slice-direction) faces',
        argstr='-z %i',
        xor=['master'])
    RL = traits.Int(
        desc='specify that planes should be added or cut '
        'symmetrically to make the resulting volume have'
        'N slices in the right-left direction',
        argstr='-RL %i',
        xor=['master'])
    AP = traits.Int(
        desc='specify that planes should be added or cut '
        'symmetrically to make the resulting volume have'
        'N slices in the anterior-posterior direction',
        argstr='-AP %i',
        xor=['master'])
    IS = traits.Int(
        desc='specify that planes should be added or cut '
        'symmetrically to make the resulting volume have'
        'N slices in the inferior-superior direction',
        argstr='-IS %i',
        xor=['master'])
    mm = traits.Bool(
        desc='pad counts \'n\' are in mm instead of slices, '
        'where each \'n\' is an integer and at least \'n\' '
        'mm of slices will be added/removed; e.g., n =  3 '
        'and slice thickness = 2.5 mm ==> 2 slices added',
        argstr='-mm',
        xor=['master'])
    master = traits.File(
        desc='match the volume described in dataset '
        '\'mset\', where mset must have the same '
        'orientation and grid spacing as dataset to be '
        'padded. the goal of -master is to make the '
        'output dataset from 3dZeropad match the '
        'spatial \'extents\' of mset by adding or '
        'subtracting slices as needed. You can\'t use '
        '-I,-S,..., or -mm with -master',
        argstr='-master %s',
        xor=['I', 'S', 'A', 'P', 'L', 'R', 'z', 'RL', 'AP', 'IS', 'mm'])


class Zeropad(AFNICommand):
    """Adds planes of zeros to a dataset (i.e., pads it out).

    For complete details, see the `3dZeropad Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dZeropad.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> zeropad = afni.Zeropad()
    >>> zeropad.inputs.in_files = 'functional.nii'
    >>> zeropad.inputs.out_file = 'pad_functional.nii'
    >>> zeropad.inputs.I = 10
    >>> zeropad.inputs.S = 10
    >>> zeropad.inputs.A = 10
    >>> zeropad.inputs.P = 10
    >>> zeropad.inputs.R = 10
    >>> zeropad.inputs.L = 10
    >>> zeropad.cmdline
    '3dZeropad -A 10 -I 10 -L 10 -P 10 -R 10 -S 10 -prefix pad_functional.nii functional.nii'
    >>> res = zeropad.run()  # doctest: +SKIP
    """

    _cmd = '3dZeropad'
    input_spec = ZeropadInputSpec
    output_spec = AFNICommandOutputSpec
