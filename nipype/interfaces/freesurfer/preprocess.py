# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provides interfaces to various commands provided by FreeSurfer
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import range

import os
import os.path as op
from glob import glob
import shutil

import numpy as np
from nibabel import load

from ... import logging, LooseVersion
from ...utils.filemanip import fname_presuffix, check_depends
from ..io import FreeSurferSource
from ..base import (TraitedSpec, File, traits, Directory, InputMultiPath,
                    OutputMultiPath, CommandLine, CommandLineInputSpec,
                    isdefined)
from .base import (FSCommand, FSTraitedSpec, FSTraitedSpecOpenMP,
                   FSCommandOpenMP, Info)
from .utils import copy2subjdir

__docformat__ = 'restructuredtext'
iflogger = logging.getLogger('nipype.interface')

# Keeping this to avoid breaking external programs that depend on it, but
# this should not be used internally
FSVersion = Info.looseversion().vstring


class ParseDICOMDirInputSpec(FSTraitedSpec):
    dicom_dir = Directory(
        exists=True,
        argstr='--d %s',
        mandatory=True,
        desc='path to siemens dicom directory')
    dicom_info_file = File(
        'dicominfo.txt',
        argstr='--o %s',
        usedefault=True,
        desc='file to which results are written')
    sortbyrun = traits.Bool(argstr='--sortbyrun', desc='assign run numbers')
    summarize = traits.Bool(
        argstr='--summarize', desc='only print out info for run leaders')


class ParseDICOMDirOutputSpec(TraitedSpec):
    dicom_info_file = File(
        exists=True, desc='text file containing dicom information')


class ParseDICOMDir(FSCommand):
    """Uses mri_parse_sdcmdir to get information from dicom directories

    Examples
    --------

    >>> from nipype.interfaces.freesurfer import ParseDICOMDir
    >>> dcminfo = ParseDICOMDir()
    >>> dcminfo.inputs.dicom_dir = '.'
    >>> dcminfo.inputs.sortbyrun = True
    >>> dcminfo.inputs.summarize = True
    >>> dcminfo.cmdline
    'mri_parse_sdcmdir --d . --o dicominfo.txt --sortbyrun --summarize'

   """

    _cmd = 'mri_parse_sdcmdir'
    input_spec = ParseDICOMDirInputSpec
    output_spec = ParseDICOMDirOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.dicom_info_file):
            outputs['dicom_info_file'] = os.path.join(
                os.getcwd(), self.inputs.dicom_info_file)
        return outputs


class UnpackSDICOMDirInputSpec(FSTraitedSpec):
    source_dir = Directory(
        exists=True,
        argstr='-src %s',
        mandatory=True,
        desc='directory with the DICOM files')
    output_dir = Directory(
        argstr='-targ %s',
        desc='top directory into which the files will be unpacked')
    run_info = traits.Tuple(
        traits.Int,
        traits.Str,
        traits.Str,
        traits.Str,
        mandatory=True,
        argstr='-run %d %s %s %s',
        xor=('run_info', 'config', 'seq_config'),
        desc='runno subdir format name : spec unpacking rules on cmdline')
    config = File(
        exists=True,
        argstr='-cfg %s',
        mandatory=True,
        xor=('run_info', 'config', 'seq_config'),
        desc='specify unpacking rules in file')
    seq_config = File(
        exists=True,
        argstr='-seqcfg %s',
        mandatory=True,
        xor=('run_info', 'config', 'seq_config'),
        desc='specify unpacking rules based on sequence')
    dir_structure = traits.Enum(
        'fsfast',
        'generic',
        argstr='-%s',
        desc='unpack to specified directory structures')
    no_info_dump = traits.Bool(
        argstr='-noinfodump', desc='do not create infodump file')
    scan_only = File(
        exists=True,
        argstr='-scanonly %s',
        desc='only scan the directory and put result in file')
    log_file = File(
        exists=True, argstr='-log %s', desc='explicilty set log file')
    spm_zeropad = traits.Int(
        argstr='-nspmzeropad %d',
        desc='set frame number zero padding width for SPM')
    no_unpack_err = traits.Bool(
        argstr='-no-unpackerr', desc='do not try to unpack runs with errors')


class UnpackSDICOMDir(FSCommand):
    """Use unpacksdcmdir to convert dicom files

    Call unpacksdcmdir -help from the command line to see more information on
    using this command.

    Examples
    --------

    >>> from nipype.interfaces.freesurfer import UnpackSDICOMDir
    >>> unpack = UnpackSDICOMDir()
    >>> unpack.inputs.source_dir = '.'
    >>> unpack.inputs.output_dir = '.'
    >>> unpack.inputs.run_info = (5, 'mprage', 'nii', 'struct')
    >>> unpack.inputs.dir_structure = 'generic'
    >>> unpack.cmdline
    'unpacksdcmdir -generic -targ . -run 5 mprage nii struct -src .'
    """
    _cmd = 'unpacksdcmdir'
    input_spec = UnpackSDICOMDirInputSpec


class MRIConvertInputSpec(FSTraitedSpec):
    read_only = traits.Bool(argstr='--read_only', desc='read the input volume')
    no_write = traits.Bool(argstr='--no_write', desc='do not write output')
    in_info = traits.Bool(argstr='--in_info', desc='display input info')
    out_info = traits.Bool(argstr='--out_info', desc='display output info')
    in_stats = traits.Bool(argstr='--in_stats', desc='display input stats')
    out_stats = traits.Bool(argstr='--out_stats', desc='display output stats')
    in_matrix = traits.Bool(argstr='--in_matrix', desc='display input matrix')
    out_matrix = traits.Bool(
        argstr='--out_matrix', desc='display output matrix')
    in_i_size = traits.Int(argstr='--in_i_size %d', desc='input i size')
    in_j_size = traits.Int(argstr='--in_j_size %d', desc='input j size')
    in_k_size = traits.Int(argstr='--in_k_size %d', desc='input k size')
    force_ras = traits.Bool(
        argstr='--force_ras_good',
        desc='use default when orientation info absent')
    in_i_dir = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr='--in_i_direction %f %f %f',
        desc='<R direction> <A direction> <S direction>')
    in_j_dir = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr='--in_j_direction %f %f %f',
        desc='<R direction> <A direction> <S direction>')
    in_k_dir = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr='--in_k_direction %f %f %f',
        desc='<R direction> <A direction> <S direction>')
    _orientations = [
        'LAI', 'LIA', 'ALI', 'AIL', 'ILA', 'IAL', 'LAS', 'LSA', 'ALS', 'ASL',
        'SLA', 'SAL', 'LPI', 'LIP', 'PLI', 'PIL', 'ILP', 'IPL', 'LPS', 'LSP',
        'PLS', 'PSL', 'SLP', 'SPL', 'RAI', 'RIA', 'ARI', 'AIR', 'IRA', 'IAR',
        'RAS', 'RSA', 'ARS', 'ASR', 'SRA', 'SAR', 'RPI', 'RIP', 'PRI', 'PIR',
        'IRP', 'IPR', 'RPS', 'RSP', 'PRS', 'PSR', 'SRP', 'SPR'
    ]
    # _orientations = [comb for comb in itertools.chain(*[[''.join(c) for c in itertools.permutations(s)] for s in [a+b+c for a in 'LR' for b in 'AP' for c in 'IS']])]
    in_orientation = traits.Enum(
        _orientations,
        argstr='--in_orientation %s',
        desc='specify the input orientation')
    in_center = traits.List(
        traits.Float,
        maxlen=3,
        argstr='--in_center %s',
        desc='<R coordinate> <A coordinate> <S coordinate>')
    sphinx = traits.Bool(
        argstr='--sphinx', desc='change orientation info to sphinx')
    out_i_count = traits.Int(
        argstr='--out_i_count %d', desc='some count ?? in i direction')
    out_j_count = traits.Int(
        argstr='--out_j_count %d', desc='some count ?? in j direction')
    out_k_count = traits.Int(
        argstr='--out_k_count %d', desc='some count ?? in k direction')
    vox_size = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr='-voxsize %f %f %f',
        desc=
        '<size_x> <size_y> <size_z> specify the size (mm) - useful for upsampling or downsampling'
    )
    out_i_size = traits.Int(argstr='--out_i_size %d', desc='output i size')
    out_j_size = traits.Int(argstr='--out_j_size %d', desc='output j size')
    out_k_size = traits.Int(argstr='--out_k_size %d', desc='output k size')
    out_i_dir = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr='--out_i_direction %f %f %f',
        desc='<R direction> <A direction> <S direction>')
    out_j_dir = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr='--out_j_direction %f %f %f',
        desc='<R direction> <A direction> <S direction>')
    out_k_dir = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr='--out_k_direction %f %f %f',
        desc='<R direction> <A direction> <S direction>')
    out_orientation = traits.Enum(
        _orientations,
        argstr='--out_orientation %s',
        desc='specify the output orientation')
    out_center = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr='--out_center %f %f %f',
        desc='<R coordinate> <A coordinate> <S coordinate>')
    out_datatype = traits.Enum(
        'uchar',
        'short',
        'int',
        'float',
        argstr='--out_data_type %s',
        desc='output data type <uchar|short|int|float>')
    resample_type = traits.Enum(
        'interpolate',
        'weighted',
        'nearest',
        'sinc',
        'cubic',
        argstr='--resample_type %s',
        desc=
        '<interpolate|weighted|nearest|sinc|cubic> (default is interpolate)')
    no_scale = traits.Bool(
        argstr='--no_scale 1', desc='dont rescale values for COR')
    no_change = traits.Bool(
        argstr='--nochange',
        desc="don't change type of input to that of template")
    tr = traits.Int(argstr='-tr %d', desc='TR in msec')
    te = traits.Int(argstr='-te %d', desc='TE in msec')
    ti = traits.Int(argstr='-ti %d', desc='TI in msec (note upper case flag)')
    autoalign_matrix = File(
        exists=True,
        argstr='--autoalign %s',
        desc='text file with autoalign matrix')
    unwarp_gradient = traits.Bool(
        argstr='--unwarp_gradient_nonlinearity',
        desc='unwarp gradient nonlinearity')
    apply_transform = File(
        exists=True, argstr='--apply_transform %s', desc='apply xfm file')
    apply_inv_transform = File(
        exists=True,
        argstr='--apply_inverse_transform %s',
        desc='apply inverse transformation xfm file')
    devolve_transform = traits.Str(argstr='--devolvexfm %s', desc='subject id')
    crop_center = traits.Tuple(
        traits.Int,
        traits.Int,
        traits.Int,
        argstr='--crop %d %d %d',
        desc='<x> <y> <z> crop to 256 around center (x, y, z)')
    crop_size = traits.Tuple(
        traits.Int,
        traits.Int,
        traits.Int,
        argstr='--cropsize %d %d %d',
        desc='<dx> <dy> <dz> crop to size <dx, dy, dz>')
    cut_ends = traits.Int(
        argstr='--cutends %d', desc='remove ncut slices from the ends')
    slice_crop = traits.Tuple(
        traits.Int,
        traits.Int,
        argstr='--slice-crop %d %d',
        desc='s_start s_end : keep slices s_start to s_end')
    slice_reverse = traits.Bool(
        argstr='--slice-reverse',
        desc='reverse order of slices, update vox2ras')
    slice_bias = traits.Float(
        argstr='--slice-bias %f', desc='apply half-cosine bias field')
    fwhm = traits.Float(
        argstr='--fwhm %f', desc='smooth input volume by fwhm mm')
    _filetypes = [
        'cor', 'mgh', 'mgz', 'minc', 'analyze', 'analyze4d', 'spm', 'afni',
        'brik', 'bshort', 'bfloat', 'sdt', 'outline', 'otl', 'gdf', 'nifti1',
        'nii', 'niigz'
    ]
    _infiletypes = [
        'ge', 'gelx', 'lx', 'ximg', 'siemens', 'dicom', 'siemens_dicom'
    ]
    in_type = traits.Enum(
        _filetypes + _infiletypes,
        argstr='--in_type %s',
        desc='input file type')
    out_type = traits.Enum(
        _filetypes, argstr='--out_type %s', desc='output file type')
    ascii = traits.Bool(
        argstr='--ascii', desc='save output as ascii col>row>slice>frame')
    reorder = traits.Tuple(
        traits.Int,
        traits.Int,
        traits.Int,
        argstr='--reorder %d %d %d',
        desc='olddim1 olddim2 olddim3')
    invert_contrast = traits.Float(
        argstr='--invert_contrast %f',
        desc='threshold for inversting contrast')
    in_file = File(
        exists=True,
        mandatory=True,
        position=-2,
        argstr='--input_volume %s',
        desc='File to read/convert')
    out_file = File(
        argstr='--output_volume %s',
        position=-1,
        genfile=True,
        desc='output filename or True to generate one')
    conform = traits.Bool(
        argstr='--conform',
        desc=
        'conform to 1mm voxel size in coronal slice direction with 256^3 or more'
    )
    conform_min = traits.Bool(
        argstr='--conform_min', desc='conform to smallest size')
    conform_size = traits.Float(
        argstr='--conform_size %s', desc='conform to size_in_mm')
    cw256 = traits.Bool(
        argstr='--cw256', desc='confrom to dimensions of 256^3')
    parse_only = traits.Bool(argstr='--parse_only', desc='parse input only')
    subject_name = traits.Str(
        argstr='--subject_name %s', desc='subject name ???')
    reslice_like = File(
        exists=True,
        argstr='--reslice_like %s',
        desc='reslice output to match file')
    template_type = traits.Enum(
        _filetypes + _infiletypes,
        argstr='--template_type %s',
        desc='template file type')
    split = traits.Bool(
        argstr='--split',
        desc='split output frames into separate output files.')
    frame = traits.Int(
        argstr='--frame %d', desc='keep only 0-based frame number')
    midframe = traits.Bool(
        argstr='--mid-frame', desc='keep only the middle frame')
    skip_n = traits.Int(argstr='--nskip %d', desc='skip the first n frames')
    drop_n = traits.Int(argstr='--ndrop %d', desc='drop the last n frames')
    frame_subsample = traits.Tuple(
        traits.Int,
        traits.Int,
        traits.Int,
        argstr='--fsubsample %d %d %d',
        desc='start delta end : frame subsampling (end = -1 for end)')
    in_scale = traits.Float(
        argstr='--scale %f', desc='input intensity scale factor')
    out_scale = traits.Float(
        argstr='--out-scale %d', desc='output intensity scale factor')
    in_like = File(exists=True, argstr='--in_like %s', desc='input looks like')
    fill_parcellation = traits.Bool(
        argstr='--fill_parcellation', desc='fill parcellation')
    smooth_parcellation = traits.Bool(
        argstr='--smooth_parcellation', desc='smooth parcellation')
    zero_outlines = traits.Bool(argstr='--zero_outlines', desc='zero outlines')
    color_file = File(exists=True, argstr='--color_file %s', desc='color file')
    no_translate = traits.Bool(argstr='--no_translate', desc='???')
    status_file = File(
        argstr='--status %s', desc='status file for DICOM conversion')
    sdcm_list = File(
        exists=True,
        argstr='--sdcmlist %s',
        desc='list of DICOM files for conversion')
    template_info = traits.Bool(
        argstr='--template_info', desc='dump info about template')
    crop_gdf = traits.Bool(argstr='--crop_gdf', desc='apply GDF cropping')
    zero_ge_z_offset = traits.Bool(
        argstr='--zero_ge_z_offset', desc='zero ge z offset ???')


class MRIConvertOutputSpec(TraitedSpec):
    out_file = OutputMultiPath(File(exists=True), desc='converted output file')


class MRIConvert(FSCommand):
    """use fs mri_convert to manipulate files

    .. note::
       Adds niigz as an output type option

    Examples
    --------

    >>> mc = MRIConvert()
    >>> mc.inputs.in_file = 'structural.nii'
    >>> mc.inputs.out_file = 'outfile.mgz'
    >>> mc.inputs.out_type = 'mgz'
    >>> mc.cmdline
    'mri_convert --out_type mgz --input_volume structural.nii --output_volume outfile.mgz'

    """
    _cmd = 'mri_convert'
    input_spec = MRIConvertInputSpec
    output_spec = MRIConvertOutputSpec

    filemap = dict(
        cor='cor',
        mgh='mgh',
        mgz='mgz',
        minc='mnc',
        afni='brik',
        brik='brik',
        bshort='bshort',
        spm='img',
        analyze='img',
        analyze4d='img',
        bfloat='bfloat',
        nifti1='img',
        nii='nii',
        niigz='nii.gz')

    def _format_arg(self, name, spec, value):
        if name in ['in_type', 'out_type', 'template_type']:
            if value == 'niigz':
                return spec.argstr % 'nii'
        return super(MRIConvert, self)._format_arg(name, spec, value)

    def _get_outfilename(self):
        outfile = self.inputs.out_file
        if not isdefined(outfile):
            if isdefined(self.inputs.out_type):
                suffix = '_out.' + self.filemap[self.inputs.out_type]
            else:
                suffix = '_out.nii.gz'
            outfile = fname_presuffix(
                self.inputs.in_file,
                newpath=os.getcwd(),
                suffix=suffix,
                use_ext=False)
        return os.path.abspath(outfile)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outfile = self._get_outfilename()
        if isdefined(self.inputs.split) and self.inputs.split:
            size = load(self.inputs.in_file).shape
            if len(size) == 3:
                tp = 1
            else:
                tp = size[-1]
            if outfile.endswith('.mgz'):
                stem = outfile.split('.mgz')[0]
                ext = '.mgz'
            elif outfile.endswith('.nii.gz'):
                stem = outfile.split('.nii.gz')[0]
                ext = '.nii.gz'
            else:
                stem = '.'.join(outfile.split('.')[:-1])
                ext = '.' + outfile.split('.')[-1]
            outfile = []
            for idx in range(0, tp):
                outfile.append(stem + '%04d' % idx + ext)
        if isdefined(self.inputs.out_type):
            if self.inputs.out_type in ['spm', 'analyze']:
                # generate all outputs
                size = load(self.inputs.in_file).shape
                if len(size) == 3:
                    tp = 1
                else:
                    tp = size[-1]
                    # have to take care of all the frame manipulations
                    raise Exception(
                        'Not taking frame manipulations into account- please warn the developers'
                    )
                outfiles = []
                outfile = self._get_outfilename()
                for i in range(tp):
                    outfiles.append(
                        fname_presuffix(outfile, suffix='%03d' % (i + 1)))
                outfile = outfiles
        outputs['out_file'] = outfile
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._get_outfilename()
        return None


class DICOMConvertInputSpec(FSTraitedSpec):
    dicom_dir = Directory(
        exists=True,
        mandatory=True,
        desc='dicom directory from which to convert dicom files')
    base_output_dir = Directory(
        mandatory=True,
        desc='directory in which subject directories are created')
    subject_dir_template = traits.Str(
        'S.%04d', usedefault=True, desc='template for subject directory name')
    subject_id = traits.Any(desc='subject identifier to insert into template')
    file_mapping = traits.List(
        traits.Tuple(traits.Str, traits.Str),
        desc='defines the output fields of interface')
    out_type = traits.Enum(
        'niigz',
        MRIConvertInputSpec._filetypes,
        usedefault=True,
        desc='defines the type of output file produced')
    dicom_info = File(
        exists=True,
        desc='File containing summary information from mri_parse_sdcmdir')
    seq_list = traits.List(
        traits.Str,
        requires=['dicom_info'],
        desc='list of pulse sequence names to be converted.')
    ignore_single_slice = traits.Bool(
        requires=['dicom_info'],
        desc='ignore volumes containing a single slice')


class DICOMConvert(FSCommand):
    """use fs mri_convert to convert dicom files

    Examples
    --------

    >>> from nipype.interfaces.freesurfer import DICOMConvert
    >>> cvt = DICOMConvert()
    >>> cvt.inputs.dicom_dir = 'dicomdir'
    >>> cvt.inputs.file_mapping = [('nifti', '*.nii'), ('info', 'dicom*.txt'), ('dti', '*dti.bv*')]

    """
    _cmd = 'mri_convert'
    input_spec = DICOMConvertInputSpec

    def _get_dicomfiles(self):
        """validate fsl bet options
        if set to None ignore
        """
        return glob(
            os.path.abspath(os.path.join(self.inputs.dicom_dir, '*-1.dcm')))

    def _get_outdir(self):
        """returns output directory"""
        subjid = self.inputs.subject_id
        if not isdefined(subjid):
            path, fname = os.path.split(self._get_dicomfiles()[0])
            subjid = int(fname.split('-')[0])
        if isdefined(self.inputs.subject_dir_template):
            subjid = self.inputs.subject_dir_template % subjid
        basedir = self.inputs.base_output_dir
        if not isdefined(basedir):
            basedir = os.path.abspath('.')
        outdir = os.path.abspath(os.path.join(basedir, subjid))
        return outdir

    def _get_runs(self):
        """Returns list of dicom series that should be converted.

        Requires a dicom info summary file generated by ``DicomDirInfo``

        """
        seq = np.genfromtxt(self.inputs.dicom_info, dtype=object)
        runs = []
        for s in seq:
            if self.inputs.seq_list:
                if self.inputs.ignore_single_slice:
                    if (int(s[8]) > 1) and any(
                        [s[12].startswith(sn) for sn in self.inputs.seq_list]):
                        runs.append(int(s[2]))
                else:
                    if any(
                        [s[12].startswith(sn) for sn in self.inputs.seq_list]):
                        runs.append(int(s[2]))
            else:
                runs.append(int(s[2]))
        return runs

    def _get_filelist(self, outdir):
        """Returns list of files to be converted"""
        filemap = {}
        for f in self._get_dicomfiles():
            head, fname = os.path.split(f)
            fname, ext = os.path.splitext(fname)
            fileparts = fname.split('-')
            runno = int(fileparts[1])
            out_type = MRIConvert.filemap[self.inputs.out_type]
            outfile = os.path.join(outdir, '.'.join(
                ('%s-%02d' % (fileparts[0], runno), out_type)))
            filemap[runno] = (f, outfile)
        if self.inputs.dicom_info:
            files = [filemap[r] for r in self._get_runs()]
        else:
            files = [filemap[r] for r in list(filemap.keys())]
        return files

    @property
    def cmdline(self):
        """ `command` plus any arguments (args)
        validates arguments and generates command line"""
        self._check_mandatory_inputs()
        outdir = self._get_outdir()
        cmd = []
        if not os.path.exists(outdir):
            cmdstr = 'python -c "import os; os.makedirs(\'%s\')"' % outdir
            cmd.extend([cmdstr])
        infofile = os.path.join(outdir, 'shortinfo.txt')
        if not os.path.exists(infofile):
            cmdstr = 'dcmdir-info-mgh %s > %s' % (self.inputs.dicom_dir,
                                                  infofile)
            cmd.extend([cmdstr])
        files = self._get_filelist(outdir)
        for infile, outfile in files:
            if not os.path.exists(outfile):
                single_cmd = '%s%s %s %s' % (self._cmd_prefix, self.cmd,
                                             infile, os.path.join(outdir,
                                                                  outfile))
                cmd.extend([single_cmd])
        return '; '.join(cmd)


class ResampleInputSpec(FSTraitedSpec):
    in_file = File(
        exists=True,
        argstr='-i %s',
        mandatory=True,
        desc='file to resample',
        position=-2)
    resampled_file = File(
        argstr='-o %s', desc='output filename', genfile=True, position=-1)
    voxel_size = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr='-vs %.2f %.2f %.2f',
        desc='triplet of output voxel sizes',
        mandatory=True)


class ResampleOutputSpec(TraitedSpec):
    resampled_file = File(exists=True, desc='output filename')


class Resample(FSCommand):
    """Use FreeSurfer mri_convert to up or down-sample image files

    Examples
    --------

    >>> from nipype.interfaces import freesurfer
    >>> resampler = freesurfer.Resample()
    >>> resampler.inputs.in_file = 'structural.nii'
    >>> resampler.inputs.resampled_file = 'resampled.nii'
    >>> resampler.inputs.voxel_size = (2.1, 2.1, 2.1)
    >>> resampler.cmdline
    'mri_convert -vs 2.10 2.10 2.10 -i structural.nii -o resampled.nii'

    """

    _cmd = 'mri_convert'
    input_spec = ResampleInputSpec
    output_spec = ResampleOutputSpec

    def _get_outfilename(self):
        if isdefined(self.inputs.resampled_file):
            outfile = self.inputs.resampled_file
        else:
            outfile = fname_presuffix(
                self.inputs.in_file, newpath=os.getcwd(), suffix='_resample')
        return outfile

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['resampled_file'] = self._get_outfilename()
        return outputs

    def _gen_filename(self, name):
        if name == 'resampled_file':
            return self._get_outfilename()
        return None


class ReconAllInputSpec(CommandLineInputSpec):
    subject_id = traits.Str(
        "recon_all", argstr='-subjid %s', desc='subject name', usedefault=True)
    directive = traits.Enum(
        'all',
        'autorecon1',
        # autorecon2 variants
        'autorecon2',
        'autorecon2-volonly',
        'autorecon2-perhemi',
        'autorecon2-inflate1',
        'autorecon2-cp',
        'autorecon2-wm',
        # autorecon3 variants
        'autorecon3',
        'autorecon3-T2pial',
        # Mix of autorecon2 and autorecon3 steps
        'autorecon-pial',
        'autorecon-hemi',
        # Not "multi-stage flags"
        'localGI',
        'qcache',
        argstr='-%s',
        desc='process directive',
        usedefault=True,
        position=0)
    hemi = traits.Enum(
        'lh', 'rh', desc='hemisphere to process', argstr="-hemi %s")
    T1_files = InputMultiPath(
        File(exists=True),
        argstr='-i %s...',
        desc='name of T1 file to process')
    T2_file = File(
        exists=True,
        argstr="-T2 %s",
        min_ver='5.3.0',
        desc='Convert T2 image to orig directory')
    FLAIR_file = File(
        exists=True,
        argstr="-FLAIR %s",
        min_ver='5.3.0',
        desc='Convert FLAIR image to orig directory')
    use_T2 = traits.Bool(
        argstr="-T2pial",
        min_ver='5.3.0',
        xor=['use_FLAIR'],
        desc='Use T2 image to refine the pial surface')
    use_FLAIR = traits.Bool(
        argstr="-FLAIRpial",
        min_ver='5.3.0',
        xor=['use_T2'],
        desc='Use FLAIR image to refine the pial surface')
    openmp = traits.Int(
        argstr="-openmp %d", desc="Number of processors to use in parallel")
    parallel = traits.Bool(
        argstr="-parallel", desc="Enable parallel execution")
    hires = traits.Bool(
        argstr="-hires",
        min_ver='6.0.0',
        desc="Conform to minimum voxel size (for voxels < 1mm)")
    mprage = traits.Bool(
        argstr='-mprage',
        desc=('Assume scan parameters are MGH MP-RAGE '
              'protocol, which produces darker gray matter'))
    big_ventricles = traits.Bool(
        argstr='-bigventricles',
        desc=('For use in subjects with enlarged '
              'ventricles'))
    brainstem = traits.Bool(
        argstr='-brainstem-structures', desc='Segment brainstem structures')
    hippocampal_subfields_T1 = traits.Bool(
        argstr='-hippocampal-subfields-T1',
        min_ver='6.0.0',
        desc='segment hippocampal subfields using input T1 scan')
    hippocampal_subfields_T2 = traits.Tuple(
        File(exists=True),
        traits.Str(),
        argstr='-hippocampal-subfields-T2 %s %s',
        min_ver='6.0.0',
        desc=('segment hippocampal subfields using T2 scan, identified by '
              'ID (may be combined with hippocampal_subfields_T1)'))
    expert = File(
        exists=True,
        argstr='-expert %s',
        desc="Set parameters using expert file")
    xopts = traits.Enum(
        "use",
        "clean",
        "overwrite",
        argstr='-xopts-%s',
        desc="Use, delete or overwrite existing expert options file")
    subjects_dir = Directory(
        exists=True,
        argstr='-sd %s',
        hash_files=False,
        desc='path to subjects directory',
        genfile=True)
    flags = InputMultiPath(
        traits.Str, argstr='%s', desc='additional parameters')

    # Expert options
    talairach = traits.Str(
        desc="Flags to pass to talairach commands", xor=['expert'])
    mri_normalize = traits.Str(
        desc="Flags to pass to mri_normalize commands", xor=['expert'])
    mri_watershed = traits.Str(
        desc="Flags to pass to mri_watershed commands", xor=['expert'])
    mri_em_register = traits.Str(
        desc="Flags to pass to mri_em_register commands", xor=['expert'])
    mri_ca_normalize = traits.Str(
        desc="Flags to pass to mri_ca_normalize commands", xor=['expert'])
    mri_ca_register = traits.Str(
        desc="Flags to pass to mri_ca_register commands", xor=['expert'])
    mri_remove_neck = traits.Str(
        desc="Flags to pass to mri_remove_neck commands", xor=['expert'])
    mri_ca_label = traits.Str(
        desc="Flags to pass to mri_ca_label commands", xor=['expert'])
    mri_segstats = traits.Str(
        desc="Flags to pass to mri_segstats commands", xor=['expert'])
    mri_mask = traits.Str(
        desc="Flags to pass to mri_mask commands", xor=['expert'])
    mri_segment = traits.Str(
        desc="Flags to pass to mri_segment commands", xor=['expert'])
    mri_edit_wm_with_aseg = traits.Str(
        desc="Flags to pass to mri_edit_wm_with_aseg commands", xor=['expert'])
    mri_pretess = traits.Str(
        desc="Flags to pass to mri_pretess commands", xor=['expert'])
    mri_fill = traits.Str(
        desc="Flags to pass to mri_fill commands", xor=['expert'])
    mri_tessellate = traits.Str(
        desc="Flags to pass to mri_tessellate commands", xor=['expert'])
    mris_smooth = traits.Str(
        desc="Flags to pass to mri_smooth commands", xor=['expert'])
    mris_inflate = traits.Str(
        desc="Flags to pass to mri_inflate commands", xor=['expert'])
    mris_sphere = traits.Str(
        desc="Flags to pass to mris_sphere commands", xor=['expert'])
    mris_fix_topology = traits.Str(
        desc="Flags to pass to mris_fix_topology commands", xor=['expert'])
    mris_make_surfaces = traits.Str(
        desc="Flags to pass to mris_make_surfaces commands", xor=['expert'])
    mris_surf2vol = traits.Str(
        desc="Flags to pass to mris_surf2vol commands", xor=['expert'])
    mris_register = traits.Str(
        desc="Flags to pass to mris_register commands", xor=['expert'])
    mrisp_paint = traits.Str(
        desc="Flags to pass to mrisp_paint commands", xor=['expert'])
    mris_ca_label = traits.Str(
        desc="Flags to pass to mris_ca_label commands", xor=['expert'])
    mris_anatomical_stats = traits.Str(
        desc="Flags to pass to mris_anatomical_stats commands", xor=['expert'])
    mri_aparc2aseg = traits.Str(
        desc="Flags to pass to mri_aparc2aseg commands", xor=['expert'])


class ReconAllOutputSpec(FreeSurferSource.output_spec):
    subjects_dir = Directory(
        exists=True, desc='Freesurfer subjects directory.')
    subject_id = traits.Str(desc='Subject name for whom to retrieve data')


class ReconAll(CommandLine):
    """Uses recon-all to generate surfaces and parcellations of structural data
    from anatomical images of a subject.

    Examples
    --------

    >>> from nipype.interfaces.freesurfer import ReconAll
    >>> reconall = ReconAll()
    >>> reconall.inputs.subject_id = 'foo'
    >>> reconall.inputs.directive = 'all'
    >>> reconall.inputs.subjects_dir = '.'
    >>> reconall.inputs.T1_files = 'structural.nii'
    >>> reconall.cmdline
    'recon-all -all -i structural.nii -subjid foo -sd .'
    >>> reconall.inputs.flags = "-qcache"
    >>> reconall.cmdline
    'recon-all -all -i structural.nii -qcache -subjid foo -sd .'
    >>> reconall.inputs.flags = ["-cw256", "-qcache"]
    >>> reconall.cmdline
    'recon-all -all -i structural.nii -cw256 -qcache -subjid foo -sd .'

    Hemisphere may be specified regardless of directive:

    >>> reconall.inputs.flags = []
    >>> reconall.inputs.hemi = 'lh'
    >>> reconall.cmdline
    'recon-all -all -i structural.nii -hemi lh -subjid foo -sd .'

    ``-autorecon-hemi`` uses the ``-hemi`` input to specify the hemisphere
    to operate upon:

    >>> reconall.inputs.directive = 'autorecon-hemi'
    >>> reconall.cmdline
    'recon-all -autorecon-hemi lh -i structural.nii -subjid foo -sd .'

    Hippocampal subfields can accept T1 and T2 images:

    >>> reconall_subfields = ReconAll()
    >>> reconall_subfields.inputs.subject_id = 'foo'
    >>> reconall_subfields.inputs.directive = 'all'
    >>> reconall_subfields.inputs.subjects_dir = '.'
    >>> reconall_subfields.inputs.T1_files = 'structural.nii'
    >>> reconall_subfields.inputs.hippocampal_subfields_T1 = True
    >>> reconall_subfields.cmdline
    'recon-all -all -i structural.nii -hippocampal-subfields-T1 -subjid foo -sd .'
    >>> reconall_subfields.inputs.hippocampal_subfields_T2 = (
    ... 'structural.nii', 'test')
    >>> reconall_subfields.cmdline
    'recon-all -all -i structural.nii -hippocampal-subfields-T1T2 structural.nii test -subjid foo -sd .'
    >>> reconall_subfields.inputs.hippocampal_subfields_T1 = False
    >>> reconall_subfields.cmdline
    'recon-all -all -i structural.nii -hippocampal-subfields-T2 structural.nii test -subjid foo -sd .'
    """

    _cmd = 'recon-all'
    _additional_metadata = ['loc', 'altkey']
    input_spec = ReconAllInputSpec
    output_spec = ReconAllOutputSpec
    _can_resume = True
    force_run = False

    # Steps are based off of the recon-all tables [0,1] describing, inputs,
    # commands, and outputs of each step of the recon-all process,
    # controlled by flags.
    #
    # Each step is a 3-tuple containing (flag, [outputs], [inputs])
    # A step is considered complete if all of its outputs exist and are newer
    # than the inputs. An empty input list indicates input mtimes will not
    # be checked. This may need updating, if users are working with manually
    # edited files.
    #
    # [0] https://surfer.nmr.mgh.harvard.edu/fswiki/ReconAllTableStableV5.3
    # [1] https://surfer.nmr.mgh.harvard.edu/fswiki/ReconAllTableStableV6.0
    _autorecon1_steps = [
        ('motioncor', ['mri/rawavg.mgz', 'mri/orig.mgz'], []),
        (
            'talairach',
            [
                'mri/orig_nu.mgz',
                'mri/transforms/talairach.auto.xfm',
                'mri/transforms/talairach.xfm',
                # 'mri/transforms/talairach_avi.log',
            ],
            []),
        ('nuintensitycor', ['mri/nu.mgz'], []),
        ('normalization', ['mri/T1.mgz'], []),
        ('skullstrip', [
            'mri/transforms/talairach_with_skull.lta',
            'mri/brainmask.auto.mgz', 'mri/brainmask.mgz'
        ], []),
    ]
    if Info.looseversion() < LooseVersion("6.0.0"):
        _autorecon2_volonly_steps = [
            ('gcareg', ['mri/transforms/talairach.lta'], []),
            ('canorm', ['mri/norm.mgz'], []),
            ('careg', ['mri/transforms/talairach.m3z'], []),
            ('careginv', [
                'mri/transforms/talairach.m3z.inv.x.mgz',
                'mri/transforms/talairach.m3z.inv.y.mgz',
                'mri/transforms/talairach.m3z.inv.z.mgz',
            ], []),
            ('rmneck', ['mri/nu_noneck.mgz'], []),
            ('skull-lta', ['mri/transforms/talairach_with_skull_2.lta'], []),
            ('calabel', [
                'mri/aseg.auto_noCCseg.mgz', 'mri/aseg.auto.mgz',
                'mri/aseg.mgz'
            ], []),
            ('normalization2', ['mri/brain.mgz'], []),
            ('maskbfs', ['mri/brain.finalsurfs.mgz'], []),
            ('segmentation',
             ['mri/wm.seg.mgz', 'mri/wm.asegedit.mgz', 'mri/wm.mgz'], []),
            (
                'fill',
                [
                    'mri/filled.mgz',
                    # 'scripts/ponscc.cut.log',
                ],
                []),
        ]
        _autorecon2_lh_steps = [
            ('tessellate', ['surf/lh.orig.nofix'], []),
            ('smooth1', ['surf/lh.smoothwm.nofix'], []),
            ('inflate1', ['surf/lh.inflated.nofix'], []),
            ('qsphere', ['surf/lh.qsphere.nofix'], []),
            ('fix', ['surf/lh.orig'], []),
            ('white', [
                'surf/lh.white', 'surf/lh.curv', 'surf/lh.area',
                'label/lh.cortex.label'
            ], []),
            ('smooth2', ['surf/lh.smoothwm'], []),
            ('inflate2', [
                'surf/lh.inflated', 'surf/lh.sulc', 'surf/lh.inflated.H',
                'surf/lh.inflated.K'
            ], []),
            # Undocumented in ReconAllTableStableV5.3
            ('curvstats', ['stats/lh.curv.stats'], []),
        ]
        _autorecon3_lh_steps = [
            ('sphere', ['surf/lh.sphere'], []),
            ('surfreg', ['surf/lh.sphere.reg'], []),
            ('jacobian_white', ['surf/lh.jacobian_white'], []),
            ('avgcurv', ['surf/lh.avg_curv'], []),
            ('cortparc', ['label/lh.aparc.annot'], []),
            ('pial', [
                'surf/lh.pial', 'surf/lh.curv.pial', 'surf/lh.area.pial',
                'surf/lh.thickness'
            ], []),
            # Misnamed outputs in ReconAllTableStableV5.3: ?h.w-c.pct.mgz
            ('pctsurfcon', ['surf/lh.w-g.pct.mgh'], []),
            ('parcstats', ['stats/lh.aparc.stats'], []),
            ('cortparc2', ['label/lh.aparc.a2009s.annot'], []),
            ('parcstats2', ['stats/lh.aparc.a2009s.stats'], []),
            # Undocumented in ReconAllTableStableV5.3
            ('cortparc3', ['label/lh.aparc.DKTatlas40.annot'], []),
            # Undocumented in ReconAllTableStableV5.3
            ('parcstats3', ['stats/lh.aparc.a2009s.stats'], []),
            ('label-exvivo-ec', ['label/lh.entorhinal_exvivo.label'], []),
        ]
        _autorecon3_added_steps = [
            ('cortribbon',
             ['mri/lh.ribbon.mgz', 'mri/rh.ribbon.mgz', 'mri/ribbon.mgz'], []),
            ('segstats', ['stats/aseg.stats'], []),
            ('aparc2aseg', ['mri/aparc+aseg.mgz', 'mri/aparc.a2009s+aseg.mgz'],
             []),
            ('wmparc', ['mri/wmparc.mgz', 'stats/wmparc.stats'], []),
            ('balabels', ['label/BA.ctab', 'label/BA.thresh.ctab'], []),
        ]
    else:
        _autorecon2_volonly_steps = [
            ('gcareg', ['mri/transforms/talairach.lta'], []),
            ('canorm', ['mri/norm.mgz'], []),
            ('careg', ['mri/transforms/talairach.m3z'], []),
            ('calabel', [
                'mri/aseg.auto_noCCseg.mgz', 'mri/aseg.auto.mgz',
                'mri/aseg.mgz'
            ], []),
            ('normalization2', ['mri/brain.mgz'], []),
            ('maskbfs', ['mri/brain.finalsurfs.mgz'], []),
            ('segmentation',
             ['mri/wm.seg.mgz', 'mri/wm.asegedit.mgz', 'mri/wm.mgz'], []),
            (
                'fill',
                [
                    'mri/filled.mgz',
                    # 'scripts/ponscc.cut.log',
                ],
                []),
        ]
        _autorecon2_lh_steps = [
            ('tessellate', ['surf/lh.orig.nofix'], []),
            ('smooth1', ['surf/lh.smoothwm.nofix'], []),
            ('inflate1', ['surf/lh.inflated.nofix'], []),
            ('qsphere', ['surf/lh.qsphere.nofix'], []),
            ('fix', ['surf/lh.orig'], []),
            ('white', [
                'surf/lh.white.preaparc', 'surf/lh.curv', 'surf/lh.area',
                'label/lh.cortex.label'
            ], []),
            ('smooth2', ['surf/lh.smoothwm'], []),
            ('inflate2', ['surf/lh.inflated', 'surf/lh.sulc'], []),
            ('curvHK', [
                'surf/lh.white.H', 'surf/lh.white.K', 'surf/lh.inflated.H',
                'surf/lh.inflated.K'
            ], []),
            ('curvstats', ['stats/lh.curv.stats'], []),
        ]
        _autorecon3_lh_steps = [
            ('sphere', ['surf/lh.sphere'], []),
            ('surfreg', ['surf/lh.sphere.reg'], []),
            ('jacobian_white', ['surf/lh.jacobian_white'], []),
            ('avgcurv', ['surf/lh.avg_curv'], []),
            ('cortparc', ['label/lh.aparc.annot'], []),
            ('pial', [
                'surf/lh.pial', 'surf/lh.curv.pial', 'surf/lh.area.pial',
                'surf/lh.thickness', 'surf/lh.white'
            ], []),
            ('parcstats', ['stats/lh.aparc.stats'], []),
            ('cortparc2', ['label/lh.aparc.a2009s.annot'], []),
            ('parcstats2', ['stats/lh.aparc.a2009s.stats'], []),
            ('cortparc3', ['label/lh.aparc.DKTatlas.annot'], []),
            ('parcstats3', ['stats/lh.aparc.DKTatlas.stats'], []),
            ('pctsurfcon', ['surf/lh.w-g.pct.mgh'], []),
        ]
        _autorecon3_added_steps = [
            ('cortribbon',
             ['mri/lh.ribbon.mgz', 'mri/rh.ribbon.mgz', 'mri/ribbon.mgz'], []),
            ('hyporelabel', ['mri/aseg.presurf.hypos.mgz'], []),
            ('aparc2aseg', [
                'mri/aparc+aseg.mgz', 'mri/aparc.a2009s+aseg.mgz',
                'mri/aparc.DKTatlas+aseg.mgz'
            ], []),
            ('apas2aseg', ['mri/aseg.mgz'], ['mri/aparc+aseg.mgz']),
            ('segstats', ['stats/aseg.stats'], []),
            ('wmparc', ['mri/wmparc.mgz', 'stats/wmparc.stats'], []),
            # Note that this is a very incomplete list; however the ctab
            # files are last to be touched, so this should be reasonable
            ('balabels', [
                'label/BA_exvivo.ctab', 'label/BA_exvivo.thresh.ctab',
                'label/lh.entorhinal_exvivo.label',
                'label/rh.entorhinal_exvivo.label'
            ], []),
        ]

    # Fill out autorecon2 steps
    _autorecon2_rh_steps = [(step, [out.replace('lh', 'rh')
                                    for out in outs], ins)
                            for step, outs, ins in _autorecon2_lh_steps]
    _autorecon2_perhemi_steps = [(step, [
        of for out in outs for of in (out, out.replace('lh', 'rh'))
    ], ins) for step, outs, ins in _autorecon2_lh_steps]
    _autorecon2_steps = _autorecon2_volonly_steps + _autorecon2_perhemi_steps

    # Fill out autorecon3 steps
    _autorecon3_rh_steps = [(step, [out.replace('lh', 'rh')
                                    for out in outs], ins)
                            for step, outs, ins in _autorecon3_lh_steps]
    _autorecon3_perhemi_steps = [(step, [
        of for out in outs for of in (out, out.replace('lh', 'rh'))
    ], ins) for step, outs, ins in _autorecon3_lh_steps]
    _autorecon3_steps = _autorecon3_perhemi_steps + _autorecon3_added_steps

    # Fill out autorecon-hemi lh/rh steps
    _autorecon_lh_steps = (_autorecon2_lh_steps + _autorecon3_lh_steps)
    _autorecon_rh_steps = (_autorecon2_rh_steps + _autorecon3_rh_steps)

    _steps = _autorecon1_steps + _autorecon2_steps + _autorecon3_steps

    _binaries = [
        'talairach', 'mri_normalize', 'mri_watershed', 'mri_em_register',
        'mri_ca_normalize', 'mri_ca_register', 'mri_remove_neck',
        'mri_ca_label', 'mri_segstats', 'mri_mask', 'mri_segment',
        'mri_edit_wm_with_aseg', 'mri_pretess', 'mri_fill', 'mri_tessellate',
        'mris_smooth', 'mris_inflate', 'mris_sphere', 'mris_fix_topology',
        'mris_make_surfaces', 'mris_surf2vol', 'mris_register', 'mrisp_paint',
        'mris_ca_label', 'mris_anatomical_stats', 'mri_aparc2aseg'
    ]

    def _gen_subjects_dir(self):
        return os.getcwd()

    def _gen_filename(self, name):
        if name == 'subjects_dir':
            return self._gen_subjects_dir()
        return None

    def _list_outputs(self):
        """
        See io.FreeSurferSource.outputs for the list of outputs returned
        """
        if isdefined(self.inputs.subjects_dir):
            subjects_dir = self.inputs.subjects_dir
        else:
            subjects_dir = self._gen_subjects_dir()

        if isdefined(self.inputs.hemi):
            hemi = self.inputs.hemi
        else:
            hemi = 'both'

        outputs = self._outputs().get()

        outputs.update(
            FreeSurferSource(
                subject_id=self.inputs.subject_id,
                subjects_dir=subjects_dir,
                hemi=hemi)._list_outputs())
        outputs['subject_id'] = self.inputs.subject_id
        outputs['subjects_dir'] = subjects_dir
        return outputs

    def _is_resuming(self):
        subjects_dir = self.inputs.subjects_dir
        if not isdefined(subjects_dir):
            subjects_dir = self._gen_subjects_dir()
        if os.path.isdir(
                os.path.join(subjects_dir, self.inputs.subject_id, 'mri')):
            return True
        return False

    def _format_arg(self, name, trait_spec, value):
        if name == 'T1_files':
            if self._is_resuming():
                return None
        if name == 'hippocampal_subfields_T1' and \
                isdefined(self.inputs.hippocampal_subfields_T2):
            return None
        if all((name == 'hippocampal_subfields_T2',
                isdefined(self.inputs.hippocampal_subfields_T1)
                and self.inputs.hippocampal_subfields_T1)):
            argstr = trait_spec.argstr.replace('T2', 'T1T2')
            return argstr % value
        if name == 'directive' and value == 'autorecon-hemi':
            if not isdefined(self.inputs.hemi):
                raise ValueError("Directive 'autorecon-hemi' requires hemi "
                                 "input to be set")
            value += ' ' + self.inputs.hemi
        if all((name == 'hemi', isdefined(self.inputs.directive)
                and self.inputs.directive == 'autorecon-hemi')):
            return None
        return super(ReconAll, self)._format_arg(name, trait_spec, value)

    @property
    def cmdline(self):
        cmd = super(ReconAll, self).cmdline

        # Adds '-expert' flag if expert flags are passed
        # Mutually exclusive with 'expert' input parameter
        cmd += self._prep_expert_file()

        if not self._is_resuming():
            return cmd
        subjects_dir = self.inputs.subjects_dir
        if not isdefined(subjects_dir):
            subjects_dir = self._gen_subjects_dir()

        # Check only relevant steps
        directive = self.inputs.directive
        if not isdefined(directive):
            steps = []
        elif directive == 'autorecon1':
            steps = self._autorecon1_steps
        elif directive == 'autorecon2-volonly':
            steps = self._autorecon2_volonly_steps
        elif directive == 'autorecon2-perhemi':
            steps = self._autorecon2_perhemi_steps
        elif directive.startswith('autorecon2'):
            if isdefined(self.inputs.hemi):
                if self.inputs.hemi == 'lh':
                    steps = (self._autorecon2_volonly_steps +
                             self._autorecon2_lh_steps)
                else:
                    steps = (self._autorecon2_volonly_steps +
                             self._autorecon2_rh_steps)
            else:
                steps = self._autorecon2_steps
        elif directive == 'autorecon-hemi':
            if self.inputs.hemi == 'lh':
                steps = self._autorecon_lh_steps
            else:
                steps = self._autorecon_rh_steps
        elif directive == 'autorecon3':
            steps = self._autorecon3_steps
        else:
            steps = self._steps

        no_run = True
        flags = []
        for step, outfiles, infiles in steps:
            flag = '-{}'.format(step)
            noflag = '-no{}'.format(step)
            if noflag in cmd:
                continue
            elif flag in cmd:
                no_run = False
                continue

            subj_dir = os.path.join(subjects_dir, self.inputs.subject_id)
            if check_depends([os.path.join(subj_dir, f) for f in outfiles],
                             [os.path.join(subj_dir, f) for f in infiles]):
                flags.append(noflag)
            else:
                no_run = False

        if no_run and not self.force_run:
            iflogger.info('recon-all complete : Not running')
            return "echo recon-all: nothing to do"

        cmd += ' ' + ' '.join(flags)
        iflogger.info('resume recon-all : %s', cmd)
        return cmd

    def _prep_expert_file(self):
        if isdefined(self.inputs.expert):
            return ''

        lines = []
        for binary in self._binaries:
            args = getattr(self.inputs, binary)
            if isdefined(args):
                lines.append('{} {}\n'.format(binary, args))

        if lines == []:
            return ''

        contents = ''.join(lines)
        if not isdefined(self.inputs.xopts) and \
                self._get_expert_file() == contents:
            return ' -xopts-use'

        expert_fname = os.path.abspath('expert.opts')
        with open(expert_fname, 'w') as fobj:
            fobj.write(contents)
        return ' -expert {}'.format(expert_fname)

    def _get_expert_file(self):
        # Read pre-existing options file, if it exists
        if isdefined(self.inputs.subjects_dir):
            subjects_dir = self.inputs.subjects_dir
        else:
            subjects_dir = self._gen_subjects_dir()

        xopts_file = os.path.join(subjects_dir, self.inputs.subject_id,
                                  'scripts', 'expert-options')
        if not os.path.exists(xopts_file):
            return ''
        with open(xopts_file, 'r') as fobj:
            return fobj.read()

    @property
    def version(self):
        ver = Info.looseversion()
        if ver > LooseVersion("0.0.0"):
            return ver.vstring


class BBRegisterInputSpec(FSTraitedSpec):
    subject_id = traits.Str(
        argstr='--s %s', desc='freesurfer subject id', mandatory=True)
    source_file = File(
        argstr='--mov %s',
        desc='source file to be registered',
        mandatory=True,
        copyfile=False)
    init = traits.Enum(
        'spm',
        'fsl',
        'header',
        argstr='--init-%s',
        mandatory=True,
        xor=['init_reg_file'],
        desc='initialize registration spm, fsl, header')
    init_reg_file = File(
        exists=True,
        argstr='--init-reg %s',
        desc='existing registration file',
        xor=['init'],
        mandatory=True)
    contrast_type = traits.Enum(
        't1',
        't2',
        'bold',
        'dti',
        argstr='--%s',
        desc='contrast type of image',
        mandatory=True)
    intermediate_file = File(
        exists=True,
        argstr="--int %s",
        desc="Intermediate image, e.g. in case of partial FOV")
    reg_frame = traits.Int(
        argstr="--frame %d",
        xor=["reg_middle_frame"],
        desc="0-based frame index for 4D source file")
    reg_middle_frame = traits.Bool(
        argstr="--mid-frame",
        xor=["reg_frame"],
        desc="Register middle frame of 4D source file")
    out_reg_file = File(
        argstr='--reg %s', desc='output registration file', genfile=True)
    spm_nifti = traits.Bool(
        argstr="--spm-nii",
        desc="force use of nifti rather than analyze with SPM")
    epi_mask = traits.Bool(
        argstr="--epi-mask", desc="mask out B0 regions in stages 1 and 2")
    dof = traits.Enum(
        6, 9, 12, argstr='--%d', desc='number of transform degrees of freedom')
    fsldof = traits.Int(
        argstr='--fsl-dof %d',
        desc='degrees of freedom for initial registration (FSL)')
    out_fsl_file = traits.Either(
        traits.Bool,
        File,
        argstr="--fslmat %s",
        desc="write the transformation matrix in FSL FLIRT format")
    out_lta_file = traits.Either(
        traits.Bool,
        File,
        argstr="--lta %s",
        min_ver='5.2.0',
        desc="write the transformation matrix in LTA format")
    registered_file = traits.Either(
        traits.Bool,
        File,
        argstr='--o %s',
        desc='output warped sourcefile either True or filename')
    init_cost_file = traits.Either(
        traits.Bool,
        File,
        argstr='--initcost %s',
        desc='output initial registration cost file')


class BBRegisterInputSpec6(BBRegisterInputSpec):
    init = traits.Enum(
        'coreg',
        'rr',
        'spm',
        'fsl',
        'header',
        'best',
        argstr='--init-%s',
        xor=['init_reg_file'],
        desc='initialize registration with mri_coreg, spm, fsl, or header')
    init_reg_file = File(
        exists=True,
        argstr='--init-reg %s',
        desc='existing registration file',
        xor=['init'])


class BBRegisterOutputSpec(TraitedSpec):
    out_reg_file = File(exists=True, desc='Output registration file')
    out_fsl_file = File(
        exists=True, desc='Output FLIRT-style registration file')
    out_lta_file = File(exists=True, desc='Output LTA-style registration file')
    min_cost_file = File(
        exists=True, desc='Output registration minimum cost file')
    init_cost_file = File(
        exists=True, desc='Output initial registration cost file')
    registered_file = File(
        exists=True, desc='Registered and resampled source file')


class BBRegister(FSCommand):
    """Use FreeSurfer bbregister to register a volume to the Freesurfer anatomical.

    This program performs within-subject, cross-modal registration using a
    boundary-based cost function. It is required that you have an anatomical
    scan of the subject that has already been recon-all-ed using freesurfer.

    Examples
    --------

    >>> from nipype.interfaces.freesurfer import BBRegister
    >>> bbreg = BBRegister(subject_id='me', source_file='structural.nii', init='header', contrast_type='t2')
    >>> bbreg.cmdline
    'bbregister --t2 --init-header --reg structural_bbreg_me.dat --mov structural.nii --s me'

    """

    _cmd = 'bbregister'
    if LooseVersion('0.0.0') < Info.looseversion() < LooseVersion("6.0.0"):
        input_spec = BBRegisterInputSpec
    else:
        input_spec = BBRegisterInputSpec6
    output_spec = BBRegisterOutputSpec

    def _list_outputs(self):

        outputs = self.output_spec().get()
        _in = self.inputs

        if isdefined(_in.out_reg_file):
            outputs['out_reg_file'] = op.abspath(_in.out_reg_file)
        elif _in.source_file:
            suffix = '_bbreg_%s.dat' % _in.subject_id
            outputs['out_reg_file'] = fname_presuffix(
                _in.source_file, suffix=suffix, use_ext=False)

        if isdefined(_in.registered_file):
            if isinstance(_in.registered_file, bool):
                outputs['registered_file'] = fname_presuffix(
                    _in.source_file, suffix='_bbreg')
            else:
                outputs['registered_file'] = op.abspath(_in.registered_file)

        if isdefined(_in.out_lta_file):
            if isinstance(_in.out_lta_file, bool):
                suffix = '_bbreg_%s.lta' % _in.subject_id
                out_lta_file = fname_presuffix(
                    _in.source_file, suffix=suffix, use_ext=False)
                outputs['out_lta_file'] = out_lta_file
            else:
                outputs['out_lta_file'] = op.abspath(_in.out_lta_file)

        if isdefined(_in.out_fsl_file):
            if isinstance(_in.out_fsl_file, bool):
                suffix = '_bbreg_%s.mat' % _in.subject_id
                out_fsl_file = fname_presuffix(
                    _in.source_file, suffix=suffix, use_ext=False)
                outputs['out_fsl_file'] = out_fsl_file
            else:
                outputs['out_fsl_file'] = op.abspath(_in.out_fsl_file)

        if isdefined(_in.init_cost_file):
            if isinstance(_in.out_fsl_file, bool):
                outputs[
                    'init_cost_file'] = outputs['out_reg_file'] + '.initcost'
            else:
                outputs['init_cost_file'] = op.abspath(_in.init_cost_file)

        outputs['min_cost_file'] = outputs['out_reg_file'] + '.mincost'
        return outputs

    def _format_arg(self, name, spec, value):
        if name in ('registered_file', 'out_fsl_file', 'out_lta_file',
                    'init_cost_file') and isinstance(value, bool):
            value = self._list_outputs()[name]
        return super(BBRegister, self)._format_arg(name, spec, value)

    def _gen_filename(self, name):

        if name == 'out_reg_file':
            return self._list_outputs()[name]
        return None


class ApplyVolTransformInputSpec(FSTraitedSpec):
    source_file = File(
        exists=True,
        argstr='--mov %s',
        copyfile=False,
        mandatory=True,
        desc='Input volume you wish to transform')
    transformed_file = File(
        desc='Output volume', argstr='--o %s', genfile=True)
    _targ_xor = ('target_file', 'tal', 'fs_target')
    target_file = File(
        exists=True,
        argstr='--targ %s',
        xor=_targ_xor,
        desc='Output template volume',
        mandatory=True)
    tal = traits.Bool(
        argstr='--tal',
        xor=_targ_xor,
        mandatory=True,
        desc='map to a sub FOV of MNI305 (with --reg only)')
    tal_resolution = traits.Float(
        argstr="--talres %.10f", desc="Resolution to sample when using tal")
    fs_target = traits.Bool(
        argstr='--fstarg',
        xor=_targ_xor,
        mandatory=True,
        requires=['reg_file'],
        desc='use orig.mgz from subject in regfile as target')
    _reg_xor = ('reg_file', 'lta_file', 'lta_inv_file', 'fsl_reg_file',
                'xfm_reg_file', 'reg_header', 'mni_152_reg', 'subject')
    reg_file = File(
        exists=True,
        xor=_reg_xor,
        argstr='--reg %s',
        mandatory=True,
        desc='tkRAS-to-tkRAS matrix   (tkregister2 format)')
    lta_file = File(
        exists=True,
        xor=_reg_xor,
        argstr='--lta %s',
        mandatory=True,
        desc='Linear Transform Array file')
    lta_inv_file = File(
        exists=True,
        xor=_reg_xor,
        argstr='--lta-inv %s',
        mandatory=True,
        desc='LTA, invert')
    reg_file = File(
        exists=True,
        xor=_reg_xor,
        argstr='--reg %s',
        mandatory=True,
        desc='tkRAS-to-tkRAS matrix   (tkregister2 format)')
    fsl_reg_file = File(
        exists=True,
        xor=_reg_xor,
        argstr='--fsl %s',
        mandatory=True,
        desc='fslRAS-to-fslRAS matrix (FSL format)')
    xfm_reg_file = File(
        exists=True,
        xor=_reg_xor,
        argstr='--xfm %s',
        mandatory=True,
        desc='ScannerRAS-to-ScannerRAS matrix (MNI format)')
    reg_header = traits.Bool(
        xor=_reg_xor,
        argstr='--regheader',
        mandatory=True,
        desc='ScannerRAS-to-ScannerRAS matrix = identity')
    mni_152_reg = traits.Bool(
        xor=_reg_xor,
        argstr='--regheader',
        mandatory=True,
        desc='target MNI152 space')
    subject = traits.Str(
        xor=_reg_xor,
        argstr='--s %s',
        mandatory=True,
        desc='set matrix = identity and use subject for any templates')
    inverse = traits.Bool(desc='sample from target to source', argstr='--inv')
    interp = traits.Enum(
        'trilin',
        'nearest',
        'cubic',
        argstr='--interp %s',
        desc='Interpolation method (<trilin> or nearest)')
    no_resample = traits.Bool(
        desc='Do not resample; just change vox2ras matrix',
        argstr='--no-resample')
    m3z_file = File(
        argstr="--m3z %s",
        desc=('This is the morph to be applied to the volume. '
              'Unless the morph is in mri/transforms (eg.: for '
              'talairach.m3z computed by reconall), you will need '
              'to specify the full path to this morph and use the '
              '--noDefM3zPath flag.'))
    no_ded_m3z_path = traits.Bool(
        argstr="--noDefM3zPath",
        requires=['m3z_file'],
        desc=('To be used with the m3z flag. '
              'Instructs the code not to look for the'
              'm3z morph in the default location '
              '(SUBJECTS_DIR/subj/mri/transforms), '
              'but instead just use the path '
              'indicated in --m3z.'))

    invert_morph = traits.Bool(
        argstr="--inv-morph",
        requires=['m3z_file'],
        desc=('Compute and use the inverse of the '
              'non-linear morph to resample the input '
              'volume. To be used by --m3z.'))


class ApplyVolTransformOutputSpec(TraitedSpec):
    transformed_file = File(
        exists=True, desc='Path to output file if used normally')


class ApplyVolTransform(FSCommand):
    """Use FreeSurfer mri_vol2vol to apply a transform.

    Examples
    --------

    >>> from nipype.interfaces.freesurfer import ApplyVolTransform
    >>> applyreg = ApplyVolTransform()
    >>> applyreg.inputs.source_file = 'structural.nii'
    >>> applyreg.inputs.reg_file = 'register.dat'
    >>> applyreg.inputs.transformed_file = 'struct_warped.nii'
    >>> applyreg.inputs.fs_target = True
    >>> applyreg.cmdline
    'mri_vol2vol --fstarg --reg register.dat --mov structural.nii --o struct_warped.nii'

    """

    _cmd = 'mri_vol2vol'
    input_spec = ApplyVolTransformInputSpec
    output_spec = ApplyVolTransformOutputSpec

    def _get_outfile(self):
        outfile = self.inputs.transformed_file
        if not isdefined(outfile):
            if self.inputs.inverse is True:
                if self.inputs.fs_target is True:
                    src = 'orig.mgz'
                else:
                    src = self.inputs.target_file
            else:
                src = self.inputs.source_file
            outfile = fname_presuffix(
                src, newpath=os.getcwd(), suffix='_warped')
        return outfile

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['transformed_file'] = os.path.abspath(self._get_outfile())
        return outputs

    def _gen_filename(self, name):
        if name == 'transformed_file':
            return self._get_outfile()
        return None


class SmoothInputSpec(FSTraitedSpec):
    in_file = File(
        exists=True, desc='source volume', argstr='--i %s', mandatory=True)
    reg_file = File(
        desc='registers volume to surface anatomical ',
        argstr='--reg %s',
        mandatory=True,
        exists=True)
    smoothed_file = File(desc='output volume', argstr='--o %s', genfile=True)
    proj_frac_avg = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        xor=['proj_frac'],
        desc='average a long normal min max delta',
        argstr='--projfrac-avg %.2f %.2f %.2f')
    proj_frac = traits.Float(
        desc='project frac of thickness a long surface normal',
        xor=['proj_frac_avg'],
        argstr='--projfrac %s')
    surface_fwhm = traits.Range(
        low=0.0,
        requires=['reg_file'],
        mandatory=True,
        xor=['num_iters'],
        desc='surface FWHM in mm',
        argstr='--fwhm %f')
    num_iters = traits.Range(
        low=1,
        xor=['surface_fwhm'],
        mandatory=True,
        argstr='--niters %d',
        desc='number of iterations instead of fwhm')
    vol_fwhm = traits.Range(
        low=0.0,
        argstr='--vol-fwhm %f',
        desc='volume smoothing outside of surface')


class SmoothOutputSpec(TraitedSpec):
    smoothed_file = File(exists=True, desc='smoothed input volume')


class Smooth(FSCommand):
    """Use FreeSurfer mris_volsmooth to smooth a volume

    This function smoothes cortical regions on a surface and non-cortical
    regions in volume.

    .. note::
       Cortical voxels are mapped to the surface (3D->2D) and then the
       smoothed values from the surface are put back into the volume to fill
       the cortical ribbon. If data is smoothed with this algorithm, one has to
       be careful about how further processing is interpreted.

    Examples
    --------

    >>> from nipype.interfaces.freesurfer import Smooth
    >>> smoothvol = Smooth(in_file='functional.nii', smoothed_file = 'foo_out.nii', reg_file='register.dat', surface_fwhm=10, vol_fwhm=6)
    >>> smoothvol.cmdline
    'mris_volsmooth --i functional.nii --reg register.dat --o foo_out.nii --fwhm 10.000000 --vol-fwhm 6.000000'

    """

    _cmd = 'mris_volsmooth'
    input_spec = SmoothInputSpec
    output_spec = SmoothOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outfile = self.inputs.smoothed_file
        if not isdefined(outfile):
            outfile = self._gen_fname(self.inputs.in_file, suffix='_smooth')
        outputs['smoothed_file'] = outfile
        return outputs

    def _gen_filename(self, name):
        if name == 'smoothed_file':
            return self._list_outputs()[name]
        return None


class RobustRegisterInputSpec(FSTraitedSpec):

    source_file = File(
        exists=True,
        mandatory=True,
        argstr='--mov %s',
        desc='volume to be registered')
    target_file = File(
        exists=True,
        mandatory=True,
        argstr='--dst %s',
        desc='target volume for the registration')
    out_reg_file = traits.Either(
        True,
        File,
        default=True,
        usedefault=True,
        argstr='--lta %s',
        desc='registration file; either True or filename')
    registered_file = traits.Either(
        traits.Bool,
        File,
        argstr='--warp %s',
        desc='registered image; either True or filename')
    weights_file = traits.Either(
        traits.Bool,
        File,
        argstr='--weights %s',
        desc='weights image to write; either True or filename')
    est_int_scale = traits.Bool(
        argstr='--iscale',
        desc='estimate intensity scale (recommended for unnormalized images)')
    trans_only = traits.Bool(
        argstr='--transonly', desc='find 3 parameter translation only')
    in_xfm_file = File(
        exists=True,
        argstr='--transform',
        desc='use initial transform on source')
    half_source = traits.Either(
        traits.Bool,
        File,
        argstr='--halfmov %s',
        desc="write source volume mapped to halfway space")
    half_targ = traits.Either(
        traits.Bool,
        File,
        argstr="--halfdst %s",
        desc="write target volume mapped to halfway space")
    half_weights = traits.Either(
        traits.Bool,
        File,
        argstr="--halfweights %s",
        desc="write weights volume mapped to halfway space")
    half_source_xfm = traits.Either(
        traits.Bool,
        File,
        argstr="--halfmovlta %s",
        desc="write transform from source to halfway space")
    half_targ_xfm = traits.Either(
        traits.Bool,
        File,
        argstr="--halfdstlta %s",
        desc="write transform from target to halfway space")
    auto_sens = traits.Bool(
        argstr='--satit',
        xor=['outlier_sens'],
        mandatory=True,
        desc='auto-detect good sensitivity')
    outlier_sens = traits.Float(
        argstr='--sat %.4f',
        xor=['auto_sens'],
        mandatory=True,
        desc='set outlier sensitivity explicitly')
    least_squares = traits.Bool(
        argstr='--leastsquares',
        desc='use least squares instead of robust estimator')
    no_init = traits.Bool(argstr='--noinit', desc='skip transform init')
    init_orient = traits.Bool(
        argstr='--initorient',
        desc='use moments for initial orient (recommended for stripped brains)'
    )
    max_iterations = traits.Int(
        argstr='--maxit %d', desc='maximum # of times on each resolution')
    high_iterations = traits.Int(
        argstr='--highit %d', desc='max # of times on highest resolution')
    iteration_thresh = traits.Float(
        argstr='--epsit %.3f', desc='stop iterations when below threshold')
    subsample_thresh = traits.Int(
        argstr='--subsample %d',
        desc='subsample if dimension is above threshold size')
    outlier_limit = traits.Float(
        argstr='--wlimit %.3f', desc='set maximal outlier limit in satit')
    write_vo2vox = traits.Bool(
        argstr='--vox2vox', desc='output vox2vox matrix (default is RAS2RAS)')
    no_multi = traits.Bool(
        argstr='--nomulti', desc='work on highest resolution')
    mask_source = File(
        exists=True,
        argstr='--maskmov %s',
        desc='image to mask source volume with')
    mask_target = File(
        exists=True,
        argstr='--maskdst %s',
        desc='image to mask target volume with')
    force_double = traits.Bool(
        argstr='--doubleprec', desc='use double-precision intensities')
    force_float = traits.Bool(
        argstr='--floattype', desc='use float intensities')


class RobustRegisterOutputSpec(TraitedSpec):

    out_reg_file = File(exists=True, desc="output registration file")
    registered_file = File(
        exists=True, desc="output image with registration applied")
    weights_file = File(exists=True, desc="image of weights used")
    half_source = File(
        exists=True, desc="source image mapped to halfway space")
    half_targ = File(exists=True, desc="target image mapped to halfway space")
    half_weights = File(
        exists=True, desc="weights image mapped to halfway space")
    half_source_xfm = File(
        exists=True,
        desc="transform file to map source image to halfway space")
    half_targ_xfm = File(
        exists=True,
        desc="transform file to map target image to halfway space")


class RobustRegister(FSCommand):
    """Perform intramodal linear registration (translation and rotation) using
    robust statistics.

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import RobustRegister
    >>> reg = RobustRegister()
    >>> reg.inputs.source_file = 'structural.nii'
    >>> reg.inputs.target_file = 'T1.nii'
    >>> reg.inputs.auto_sens = True
    >>> reg.inputs.init_orient = True
    >>> reg.cmdline # doctest: +ELLIPSIS
    'mri_robust_register --satit --initorient --lta .../structural_robustreg.lta --mov structural.nii --dst T1.nii'

    References
    ----------
    Reuter, M, Rosas, HD, and Fischl, B, (2010). Highly Accurate Inverse
        Consistent Registration: A Robust Approach.  Neuroimage 53(4) 1181-96.

    """

    _cmd = 'mri_robust_register'
    input_spec = RobustRegisterInputSpec
    output_spec = RobustRegisterOutputSpec

    def _format_arg(self, name, spec, value):
        options = ("out_reg_file", "registered_file", "weights_file",
                   "half_source", "half_targ", "half_weights",
                   "half_source_xfm", "half_targ_xfm")
        if name in options and isinstance(value, bool):
            value = self._list_outputs()[name]
        return super(RobustRegister, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        cwd = os.getcwd()
        prefices = dict(
            src=self.inputs.source_file, trg=self.inputs.target_file)
        suffices = dict(
            out_reg_file=("src", "_robustreg.lta", False),
            registered_file=("src", "_robustreg", True),
            weights_file=("src", "_robustweights", True),
            half_source=("src", "_halfway", True),
            half_targ=("trg", "_halfway", True),
            half_weights=("src", "_halfweights", True),
            half_source_xfm=("src", "_robustxfm.lta", False),
            half_targ_xfm=("trg", "_robustxfm.lta", False))
        for name, sufftup in list(suffices.items()):
            value = getattr(self.inputs, name)
            if value:
                if value is True:
                    outputs[name] = fname_presuffix(
                        prefices[sufftup[0]],
                        suffix=sufftup[1],
                        newpath=cwd,
                        use_ext=sufftup[2])
                else:
                    outputs[name] = os.path.abspath(value)
        return outputs


class FitMSParamsInputSpec(FSTraitedSpec):

    in_files = traits.List(
        File(exists=True),
        argstr="%s",
        position=-2,
        mandatory=True,
        desc="list of FLASH images (must be in mgh format)")
    tr_list = traits.List(
        traits.Int, desc="list of TRs of the input files (in msec)")
    te_list = traits.List(
        traits.Float, desc="list of TEs of the input files (in msec)")
    flip_list = traits.List(
        traits.Int, desc="list of flip angles of the input files")
    xfm_list = traits.List(
        File(exists=True),
        desc="list of transform files to apply to each FLASH image")
    out_dir = Directory(
        argstr="%s",
        position=-1,
        genfile=True,
        desc="directory to store output in")


class FitMSParamsOutputSpec(TraitedSpec):

    t1_image = File(
        exists=True, desc="image of estimated T1 relaxation values")
    pd_image = File(
        exists=True, desc="image of estimated proton density values")
    t2star_image = File(exists=True, desc="image of estimated T2* values")


class FitMSParams(FSCommand):
    """Estimate tissue paramaters from a set of FLASH images.

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import FitMSParams
    >>> msfit = FitMSParams()
    >>> msfit.inputs.in_files = ['flash_05.mgz', 'flash_30.mgz']
    >>> msfit.inputs.out_dir = 'flash_parameters'
    >>> msfit.cmdline
    'mri_ms_fitparms  flash_05.mgz flash_30.mgz flash_parameters'

    """
    _cmd = "mri_ms_fitparms"
    input_spec = FitMSParamsInputSpec
    output_spec = FitMSParamsOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "in_files":
            cmd = ""
            for i, file in enumerate(value):
                if isdefined(self.inputs.tr_list):
                    cmd = " ".join((cmd, "-tr %.1f" % self.inputs.tr_list[i]))
                if isdefined(self.inputs.te_list):
                    cmd = " ".join((cmd, "-te %.3f" % self.inputs.te_list[i]))
                if isdefined(self.inputs.flip_list):
                    cmd = " ".join((cmd,
                                    "-fa %.1f" % self.inputs.flip_list[i]))
                if isdefined(self.inputs.xfm_list):
                    cmd = " ".join((cmd, "-at %s" % self.inputs.xfm_list[i]))
                cmd = " ".join((cmd, file))
            return cmd
        return super(FitMSParams, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_dir):
            out_dir = self._gen_filename("out_dir")
        else:
            out_dir = self.inputs.out_dir
        outputs["t1_image"] = os.path.join(out_dir, "T1.mgz")
        outputs["pd_image"] = os.path.join(out_dir, "PD.mgz")
        outputs["t2star_image"] = os.path.join(out_dir, "T2star.mgz")
        return outputs

    def _gen_filename(self, name):
        if name == "out_dir":
            return os.getcwd()
        return None


class SynthesizeFLASHInputSpec(FSTraitedSpec):

    fixed_weighting = traits.Bool(
        position=1,
        argstr="-w",
        desc="use a fixed weighting to generate optimal gray/white contrast")
    tr = traits.Float(
        mandatory=True,
        position=2,
        argstr="%.2f",
        desc="repetition time (in msec)")
    flip_angle = traits.Float(
        mandatory=True,
        position=3,
        argstr="%.2f",
        desc="flip angle (in degrees)")
    te = traits.Float(
        mandatory=True, position=4, argstr="%.3f", desc="echo time (in msec)")
    t1_image = File(
        exists=True,
        mandatory=True,
        position=5,
        argstr="%s",
        desc="image of T1 values")
    pd_image = File(
        exists=True,
        mandatory=True,
        position=6,
        argstr="%s",
        desc="image of proton density values")
    out_file = File(genfile=True, argstr="%s", desc="image to write")


class SynthesizeFLASHOutputSpec(TraitedSpec):

    out_file = File(exists=True, desc="synthesized FLASH acquisition")


class SynthesizeFLASH(FSCommand):
    """Synthesize a FLASH acquisition from T1 and proton density maps.

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import SynthesizeFLASH
    >>> syn = SynthesizeFLASH(tr=20, te=3, flip_angle=30)
    >>> syn.inputs.t1_image = 'T1.mgz'
    >>> syn.inputs.pd_image = 'PD.mgz'
    >>> syn.inputs.out_file = 'flash_30syn.mgz'
    >>> syn.cmdline
    'mri_synthesize 20.00 30.00 3.000 T1.mgz PD.mgz flash_30syn.mgz'

    """
    _cmd = "mri_synthesize"
    input_spec = SynthesizeFLASHInputSpec
    output_spec = SynthesizeFLASHOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_file):
            outputs["out_file"] = self.inputs.out_file
        else:
            outputs["out_file"] = self._gen_fname(
                "synth-flash_%02d.mgz" % self.inputs.flip_angle, suffix="")
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None


class MNIBiasCorrectionInputSpec(FSTraitedSpec):
    # mandatory
    in_file = File(
        exists=True,
        mandatory=True,
        argstr="--i %s",
        desc="input volume. Input can be any format accepted by mri_convert.")
    # optional
    out_file = File(
        argstr="--o %s",
        name_source=['in_file'],
        name_template='%s_output',
        hash_files=False,
        keep_extension=True,
        desc="output volume. Output can be any format accepted by mri_convert. "
        + "If the output format is COR, then the directory must exist.")
    iterations = traits.Int(
        4, usedefault=True,
        argstr="--n %d",
        desc=
        "Number of iterations to run nu_correct. Default is 4. This is the number of times "
        +
        "that nu_correct is repeated (ie, using the output from the previous run as the input for "
        +
        "the next). This is different than the -iterations option to nu_correct."
    )
    protocol_iterations = traits.Int(
        argstr="--proto-iters %d",
        desc=
        "Passes Np as argument of the -iterations flag of nu_correct. This is different "
        +
        "than the --n flag above. Default is not to pass nu_correct the -iterations flag."
    )
    distance = traits.Int(argstr="--distance %d", desc="N3 -distance option")
    no_rescale = traits.Bool(
        argstr="--no-rescale",
        desc="do not rescale so that global mean of output == input global mean"
    )
    mask = File(
        exists=True,
        argstr="--mask %s",
        desc=
        "brainmask volume. Input can be any format accepted by mri_convert.")
    transform = File(
        exists=True,
        argstr="--uchar %s",
        desc="tal.xfm. Use mri_make_uchar instead of conforming")
    stop = traits.Float(
        argstr="--stop %f",
        desc=
        "Convergence threshold below which iteration stops (suggest 0.01 to 0.0001)"
    )
    shrink = traits.Int(
        argstr="--shrink %d",
        desc="Shrink parameter for finer sampling (default is 4)")


class MNIBiasCorrectionOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output volume")


class MNIBiasCorrection(FSCommand):
    """ Wrapper for nu_correct, a program from the Montreal Neurological Insitute (MNI)
    used for correcting intensity non-uniformity (ie, bias fields). You must have the
    MNI software installed on your system to run this. See [www.bic.mni.mcgill.ca/software/N3]
    for more info.

    mri_nu_correct.mni uses float internally instead of uchar. It also rescales the output so
    that the global mean is the same as that of the input. These two changes are linked and
    can be turned off with --no-float

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import MNIBiasCorrection
    >>> correct = MNIBiasCorrection()
    >>> correct.inputs.in_file = "norm.mgz"
    >>> correct.inputs.iterations = 6
    >>> correct.inputs.protocol_iterations = 1000
    >>> correct.inputs.distance = 50
    >>> correct.cmdline
    'mri_nu_correct.mni --distance 50 --i norm.mgz --n 6 --o norm_output.mgz --proto-iters 1000'

    References:
    ----------
    [http://freesurfer.net/fswiki/mri_nu_correct.mni]
    [http://www.bic.mni.mcgill.ca/software/N3]
    [https://github.com/BIC-MNI/N3]

    """
    _cmd = "mri_nu_correct.mni"
    input_spec = MNIBiasCorrectionInputSpec
    output_spec = MNIBiasCorrectionOutputSpec


class WatershedSkullStripInputSpec(FSTraitedSpec):
    # required
    in_file = File(
        argstr="%s",
        exists=True,
        mandatory=True,
        position=-2,
        desc="input volume")
    out_file = File(
        'brainmask.auto.mgz',
        argstr="%s",
        exists=False,
        mandatory=True,
        position=-1,
        usedefault=True,
        desc="output volume")
    # optional
    t1 = traits.Bool(
        argstr="-T1", desc="specify T1 input volume (T1 grey value = 110)")
    brain_atlas = File(
        argstr="-brain_atlas %s", exists=True, position=-4, desc="")
    transform = File(
        argstr="%s", exists=False, position=-3, desc="undocumented")


class WatershedSkullStripOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="skull stripped brain volume")


class WatershedSkullStrip(FSCommand):
    """ This program strips skull and other outer non-brain tissue and
    produces the brain volume from T1 volume or the scanned volume.

    The "watershed" segmentation algorithm was used to dertermine the
    intensity values for white matter, grey matter, and CSF.
    A force field was then used to fit a spherical surface to the brain.
    The shape of the surface fit was then evaluated against a previously
    derived template.

    The default parameters are: -w 0.82 -b 0.32 -h 10 -seedpt -ta -wta

    (Segonne 2004)

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import WatershedSkullStrip
    >>> skullstrip = WatershedSkullStrip()
    >>> skullstrip.inputs.in_file = "T1.mgz"
    >>> skullstrip.inputs.t1 = True
    >>> skullstrip.inputs.transform = "transforms/talairach_with_skull.lta"
    >>> skullstrip.inputs.out_file = "brainmask.auto.mgz"
    >>> skullstrip.cmdline
    'mri_watershed -T1 transforms/talairach_with_skull.lta T1.mgz brainmask.auto.mgz'
    """
    _cmd = 'mri_watershed'
    input_spec = WatershedSkullStripInputSpec
    output_spec = WatershedSkullStripOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class NormalizeInputSpec(FSTraitedSpec):
    # required
    in_file = File(
        argstr='%s',
        exists=True,
        mandatory=True,
        position=-2,
        desc="The input file for Normalize")
    out_file = File(
        argstr='%s',
        position=-1,
        name_source=['in_file'],
        name_template='%s_norm',
        hash_files=False,
        keep_extension=True,
        desc="The output file for Normalize")
    # optional
    gradient = traits.Int(
        argstr="-g %d",
        desc="use max intensity/mm gradient g (default=1)")
    mask = File(
        argstr="-mask %s",
        exists=True,
        desc="The input mask file for Normalize")
    segmentation = File(
        argstr="-aseg %s",
        exists=True,
        desc="The input segmentation for Normalize")
    transform = File(
        exists=True, desc="Tranform file from the header of the input file")


class NormalizeOutputSpec(TraitedSpec):
    out_file = traits.File(exists=False, desc="The output file for Normalize")


class Normalize(FSCommand):
    """
    Normalize the white-matter, optionally based on control points. The
    input volume is converted into a new volume where white matter image
    values all range around 110.

    Examples
    ========
    >>> from nipype.interfaces import freesurfer
    >>> normalize = freesurfer.Normalize()
    >>> normalize.inputs.in_file = "T1.mgz"
    >>> normalize.inputs.gradient = 1
    >>> normalize.cmdline
    'mri_normalize -g 1 T1.mgz T1_norm.mgz'
    """
    _cmd = "mri_normalize"
    input_spec = NormalizeInputSpec
    output_spec = NormalizeOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class CANormalizeInputSpec(FSTraitedSpec):
    in_file = File(
        argstr='%s',
        exists=True,
        mandatory=True,
        position=-4,
        desc="The input file for CANormalize")
    out_file = File(
        argstr='%s',
        position=-1,
        name_source=['in_file'],
        name_template='%s_norm',
        hash_files=False,
        keep_extension=True,
        desc="The output file for CANormalize")
    atlas = File(
        argstr='%s',
        exists=True,
        mandatory=True,
        position=-3,
        desc="The atlas file in gca format")
    transform = File(
        argstr='%s',
        exists=True,
        mandatory=True,
        position=-2,
        desc="The tranform file in lta format")
    # optional
    mask = File(
        argstr='-mask %s', exists=True, desc="Specifies volume to use as mask")
    control_points = File(
        argstr='-c %s', desc="File name for the output control points")
    long_file = File(
        argstr='-long %s',
        desc='undocumented flag used in longitudinal processing')


class CANormalizeOutputSpec(TraitedSpec):
    out_file = traits.File(exists=False, desc="The output file for Normalize")
    control_points = File(
        exists=False, desc="The output control points for Normalize")


class CANormalize(FSCommand):
    """This program creates a normalized volume using the brain volume and an
    input gca file.

    For complete details, see the `FS Documentation <http://surfer.nmr.mgh.harvard.edu/fswiki/mri_ca_normalize>`_

    Examples
    ========

    >>> from nipype.interfaces import freesurfer
    >>> ca_normalize = freesurfer.CANormalize()
    >>> ca_normalize.inputs.in_file = "T1.mgz"
    >>> ca_normalize.inputs.atlas = "atlas.nii.gz" # in practice use .gca atlases
    >>> ca_normalize.inputs.transform = "trans.mat" # in practice use .lta transforms
    >>> ca_normalize.cmdline
    'mri_ca_normalize T1.mgz atlas.nii.gz trans.mat T1_norm.mgz'
    """
    _cmd = "mri_ca_normalize"
    input_spec = CANormalizeInputSpec
    output_spec = CANormalizeOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        outputs['control_points'] = os.path.abspath(self.inputs.control_points)
        return outputs


class CARegisterInputSpec(FSTraitedSpecOpenMP):
    # required
    in_file = File(
        argstr='%s',
        exists=True,
        mandatory=True,
        position=-3,
        desc="The input volume for CARegister")
    out_file = File(
        argstr='%s',
        position=-1,
        genfile=True,
        desc="The output volume for CARegister")
    template = File(
        argstr='%s',
        exists=True,
        position=-2,
        desc="The template file in gca format")
    # optional
    mask = File(
        argstr='-mask %s', exists=True, desc="Specifies volume to use as mask")
    invert_and_save = traits.Bool(
        argstr='-invert-and-save',
        position=-4,
        desc=
        "Invert and save the .m3z multi-dimensional talaraich transform to x, y, and z .mgz files"
    )
    no_big_ventricles = traits.Bool(
        argstr='-nobigventricles', desc="No big ventricles")
    transform = File(
        argstr='-T %s', exists=True, desc="Specifies transform in lta format")
    align = traits.String(
        argstr='-align-%s', desc="Specifies when to perform alignment")
    levels = traits.Int(
        argstr='-levels %d',
        desc=
        "defines how many surrounding voxels will be used in interpolations, default is 6"
    )
    A = traits.Int(
        argstr='-A %d',
        desc='undocumented flag used in longitudinal processing')
    l_files = InputMultiPath(
        File(exists=False),
        argstr='-l %s',
        desc='undocumented flag used in longitudinal processing')


class CARegisterOutputSpec(TraitedSpec):
    out_file = traits.File(exists=False, desc="The output file for CARegister")


class CARegister(FSCommandOpenMP):
    """Generates a multi-dimensional talairach transform from a gca file and talairach.lta file

    For complete details, see the `FS Documentation <http://surfer.nmr.mgh.harvard.edu/fswiki/mri_ca_register>`_

    Examples
    ========
    >>> from nipype.interfaces import freesurfer
    >>> ca_register = freesurfer.CARegister()
    >>> ca_register.inputs.in_file = "norm.mgz"
    >>> ca_register.inputs.out_file = "talairach.m3z"
    >>> ca_register.cmdline
    'mri_ca_register norm.mgz talairach.m3z'
    """
    _cmd = "mri_ca_register"
    input_spec = CARegisterInputSpec
    output_spec = CARegisterOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "l_files" and len(value) == 1:
            value.append('identity.nofile')
        return super(CARegister, self)._format_arg(name, spec, value)

    def _gen_fname(self, name):
        if name == 'out_file':
            return os.path.abspath('talairach.m3z')
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class CALabelInputSpec(FSTraitedSpecOpenMP):
    # required
    in_file = File(
        argstr="%s",
        position=-4,
        mandatory=True,
        exists=True,
        desc="Input volume for CALabel")
    out_file = File(
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=False,
        desc="Output file for CALabel")
    transform = File(
        argstr="%s",
        position=-3,
        mandatory=True,
        exists=True,
        desc="Input transform for CALabel")
    template = File(
        argstr="%s",
        position=-2,
        mandatory=True,
        exists=True,
        desc="Input template for CALabel")
    # optional
    in_vol = File(argstr="-r %s", exists=True, desc="set input volume")
    intensities = File(
        argstr="-r %s",
        exists=True,
        desc="input label intensities file(used in longitudinal processing)")
    no_big_ventricles = traits.Bool(
        argstr="-nobigventricles", desc="No big ventricles")
    align = traits.Bool(argstr="-align", desc="Align CALabel")
    prior = traits.Float(argstr="-prior %.1f", desc="Prior for CALabel")
    relabel_unlikely = traits.Tuple(
        traits.Int,
        traits.Float,
        argstr="-relabel_unlikely %d %.1f",
        desc=("Reclassify voxels at least some std"
              " devs from the mean using some size"
              " Gaussian window"))
    label = traits.File(
        argstr="-l %s",
        exists=True,
        desc=
        "Undocumented flag. Autorecon3 uses ../label/{hemisphere}.cortex.label as input file"
    )
    aseg = traits.File(
        argstr="-aseg %s",
        exists=True,
        desc=
        "Undocumented flag. Autorecon3 uses ../mri/aseg.presurf.mgz as input file"
    )


class CALabelOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Output volume from CALabel")


class CALabel(FSCommandOpenMP):
    """
    For complete details, see the `FS Documentation <http://surfer.nmr.mgh.harvard.edu/fswiki/mri_ca_register>`_

    Examples
    ========

    >>> from nipype.interfaces import freesurfer
    >>> ca_label = freesurfer.CALabel()
    >>> ca_label.inputs.in_file = "norm.mgz"
    >>> ca_label.inputs.out_file = "out.mgz"
    >>> ca_label.inputs.transform = "trans.mat"
    >>> ca_label.inputs.template = "Template_6.nii" # in practice use .gcs extension
    >>> ca_label.cmdline
    'mri_ca_label norm.mgz trans.mat Template_6.nii out.mgz'
    """
    _cmd = "mri_ca_label"
    input_spec = CALabelInputSpec
    output_spec = CALabelOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class MRIsCALabelInputSpec(FSTraitedSpecOpenMP):
    # required
    subject_id = traits.String(
        'subject_id',
        argstr="%s",
        position=-5,
        usedefault=True,
        mandatory=True,
        desc="Subject name or ID")
    hemisphere = traits.Enum(
        'lh',
        'rh',
        argstr="%s",
        position=-4,
        mandatory=True,
        desc="Hemisphere ('lh' or 'rh')")
    canonsurf = File(
        argstr="%s",
        position=-3,
        mandatory=True,
        exists=True,
        desc="Input canonical surface file")
    classifier = File(
        argstr="%s",
        position=-2,
        mandatory=True,
        exists=True,
        desc="Classifier array input file")
    smoothwm = File(
        mandatory=True,
        exists=True,
        desc="implicit input {hemisphere}.smoothwm")
    curv = File(
        mandatory=True, exists=True, desc="implicit input {hemisphere}.curv")
    sulc = File(
        mandatory=True, exists=True, desc="implicit input {hemisphere}.sulc")
    out_file = File(
        argstr="%s",
        position=-1,
        exists=False,
        name_source=['hemisphere'],
        keep_extension=True,
        hash_files=False,
        name_template="%s.aparc.annot",
        desc="Annotated surface output file")
    # optional
    label = traits.File(
        argstr="-l %s",
        exists=True,
        desc=
        "Undocumented flag. Autorecon3 uses ../label/{hemisphere}.cortex.label as input file"
    )
    aseg = traits.File(
        argstr="-aseg %s",
        exists=True,
        desc=
        "Undocumented flag. Autorecon3 uses ../mri/aseg.presurf.mgz as input file"
    )
    seed = traits.Int(argstr="-seed %d", desc="")
    copy_inputs = traits.Bool(desc="Copies implicit inputs to node directory "
                              + "and creates a temp subjects_directory. " +
                              "Use this when running as a node")


class MRIsCALabelOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Output volume from MRIsCALabel")


class MRIsCALabel(FSCommandOpenMP):
    """
    For a single subject, produces an annotation file, in which each
    cortical surface vertex is assigned a neuroanatomical label.This
    automatic procedure employs data from a previously-prepared atlas
    file. An atlas file is created from a training set, capturing region
    data manually drawn by neuroanatomists combined with statistics on
    variability correlated to geometric information derived from the
    cortical model (sulcus and curvature). Besides the atlases provided
    with FreeSurfer, new ones can be prepared using mris_ca_train).

    Examples
    ========

    >>> from nipype.interfaces import freesurfer
    >>> ca_label = freesurfer.MRIsCALabel()
    >>> ca_label.inputs.subject_id = "test"
    >>> ca_label.inputs.hemisphere = "lh"
    >>> ca_label.inputs.canonsurf = "lh.pial"
    >>> ca_label.inputs.curv = "lh.pial"
    >>> ca_label.inputs.sulc = "lh.pial"
    >>> ca_label.inputs.classifier = "im1.nii" # in pracice, use .gcs extension
    >>> ca_label.inputs.smoothwm = "lh.pial"
    >>> ca_label.cmdline
    'mris_ca_label test lh lh.pial im1.nii lh.aparc.annot'
    """
    _cmd = "mris_ca_label"
    input_spec = MRIsCALabelInputSpec
    output_spec = MRIsCALabelOutputSpec

    def run(self, **inputs):
        if self.inputs.copy_inputs:
            self.inputs.subjects_dir = os.getcwd()
            if 'subjects_dir' in inputs:
                inputs['subjects_dir'] = self.inputs.subjects_dir
            copy2subjdir(self, self.inputs.canonsurf, folder='surf')
            copy2subjdir(
                self,
                self.inputs.smoothwm,
                folder='surf',
                basename='{0}.smoothwm'.format(self.inputs.hemisphere))
            copy2subjdir(
                self,
                self.inputs.curv,
                folder='surf',
                basename='{0}.curv'.format(self.inputs.hemisphere))
            copy2subjdir(
                self,
                self.inputs.sulc,
                folder='surf',
                basename='{0}.sulc'.format(self.inputs.hemisphere))

        # The label directory must exist in order for an output to be written
        label_dir = os.path.join(self.inputs.subjects_dir,
                                 self.inputs.subject_id, 'label')
        if not os.path.isdir(label_dir):
            os.makedirs(label_dir)

        return super(MRIsCALabel, self).run(**inputs)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        out_basename = os.path.basename(self.inputs.out_file)
        outputs['out_file'] = os.path.join(self.inputs.subjects_dir,
                                           self.inputs.subject_id, 'label',
                                           out_basename)
        return outputs


class SegmentCCInputSpec(FSTraitedSpec):
    in_file = File(
        argstr="-aseg %s",
        mandatory=True,
        exists=True,
        desc="Input aseg file to read from subjects directory")
    in_norm = File(
        mandatory=True,
        exists=True,
        desc="Required undocumented input {subject}/mri/norm.mgz")
    out_file = File(
        argstr="-o %s",
        exists=False,
        name_source=['in_file'],
        name_template='%s.auto.mgz',
        hash_files=False,
        keep_extension=False,
        desc="Filename to write aseg including CC")
    out_rotation = File(
        argstr="-lta %s",
        mandatory=True,
        exists=False,
        desc="Global filepath for writing rotation lta")
    subject_id = traits.String(
        'subject_id',
        argstr="%s",
        mandatory=True,
        position=-1,
        usedefault=True,
        desc="Subject name")
    copy_inputs = traits.Bool(
        desc="If running as a node, set this to True." +
        "This will copy the input files to the node " + "directory.")


class SegmentCCOutputSpec(TraitedSpec):
    out_file = File(
        exists=False, desc="Output segmentation uncluding corpus collosum")
    out_rotation = File(exists=False, desc="Output lta rotation file")


class SegmentCC(FSCommand):
    """
    This program segments the corpus callosum into five separate labels in
    the subcortical segmentation volume 'aseg.mgz'. The divisions of the
    cc are equally spaced in terms of distance along the primary
    eigendirection (pretty much the long axis) of the cc. The lateral
    extent can be changed with the -T <thickness> parameter, where
    <thickness> is the distance off the midline (so -T 1 would result in
    the who CC being 3mm thick). The default is 2 so it's 5mm thick. The
    aseg.stats values should be volume.

    Examples
    ========
    >>> from nipype.interfaces import freesurfer
    >>> SegmentCC_node = freesurfer.SegmentCC()
    >>> SegmentCC_node.inputs.in_file = "aseg.mgz"
    >>> SegmentCC_node.inputs.in_norm = "norm.mgz"
    >>> SegmentCC_node.inputs.out_rotation = "cc.lta"
    >>> SegmentCC_node.inputs.subject_id = "test"
    >>> SegmentCC_node.cmdline
    'mri_cc -aseg aseg.mgz -o aseg.auto.mgz -lta cc.lta test'
    """

    _cmd = "mri_cc"
    input_spec = SegmentCCInputSpec
    output_spec = SegmentCCOutputSpec

    # mri_cc does not take absolute paths and will look for the
    # input files in  <SUBJECTS_DIR>/<subject_id>/mri/<basename>
    # So, if the files are not there, they will be copied to that
    # location
    def _format_arg(self, name, spec, value):
        if name in ["in_file", "in_norm", "out_file"]:
            # mri_cc can't use abspaths just the basename
            basename = os.path.basename(value)
            return spec.argstr % basename
        return super(SegmentCC, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        outputs['out_rotation'] = os.path.abspath(self.inputs.out_rotation)
        return outputs

    def run(self, **inputs):
        if self.inputs.copy_inputs:
            self.inputs.subjects_dir = os.getcwd()
            if 'subjects_dir' in inputs:
                inputs['subjects_dir'] = self.inputs.subjects_dir
            for originalfile in [self.inputs.in_file, self.inputs.in_norm]:
                copy2subjdir(self, originalfile, folder='mri')
        return super(SegmentCC, self).run(**inputs)

    def aggregate_outputs(self, runtime=None, needed_outputs=None):
        # it is necessary to find the output files and move
        # them to the correct loacation
        predicted_outputs = self._list_outputs()
        for name in ['out_file', 'out_rotation']:
            out_file = predicted_outputs[name]
            if not os.path.isfile(out_file):
                out_base = os.path.basename(out_file)
                if isdefined(self.inputs.subjects_dir):
                    subj_dir = os.path.join(self.inputs.subjects_dir,
                                            self.inputs.subject_id)
                else:
                    subj_dir = os.path.join(os.getcwd(),
                                            self.inputs.subject_id)
                if name == 'out_file':
                    out_tmp = os.path.join(subj_dir, 'mri', out_base)
                elif name == 'out_rotation':
                    out_tmp = os.path.join(subj_dir, 'mri', 'transforms',
                                           out_base)
                else:
                    out_tmp = None
                # move the file to correct location
                if out_tmp and os.path.isfile(out_tmp):
                    if not os.path.isdir(os.path.dirname(out_tmp)):
                        os.makedirs(os.path.dirname(out_tmp))
                    shutil.move(out_tmp, out_file)
        return super(SegmentCC, self).aggregate_outputs(
            runtime, needed_outputs)


class SegmentWMInputSpec(FSTraitedSpec):
    in_file = File(
        argstr="%s",
        exists=True,
        mandatory=True,
        position=-2,
        desc="Input file for SegmentWM")
    out_file = File(
        argstr="%s",
        exists=False,
        mandatory=True,
        position=-1,
        desc="File to be written as output for SegmentWM")


class SegmentWMOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Output white matter segmentation")


class SegmentWM(FSCommand):
    """
    This program segments white matter from the input volume.  The input
    volume should be normalized such that white matter voxels are
    ~110-valued, and the volume is conformed to 256^3.


    Examples
    ========
    >>> from nipype.interfaces import freesurfer
    >>> SegmentWM_node = freesurfer.SegmentWM()
    >>> SegmentWM_node.inputs.in_file = "norm.mgz"
    >>> SegmentWM_node.inputs.out_file = "wm.seg.mgz"
    >>> SegmentWM_node.cmdline
    'mri_segment norm.mgz wm.seg.mgz'
    """

    _cmd = "mri_segment"
    input_spec = SegmentWMInputSpec
    output_spec = SegmentWMOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class EditWMwithAsegInputSpec(FSTraitedSpec):
    in_file = File(
        argstr="%s",
        position=-4,
        mandatory=True,
        exists=True,
        desc="Input white matter segmentation file")
    brain_file = File(
        argstr="%s",
        position=-3,
        mandatory=True,
        exists=True,
        desc="Input brain/T1 file")
    seg_file = File(
        argstr="%s",
        position=-2,
        mandatory=True,
        exists=True,
        desc="Input presurf segmentation file")
    out_file = File(
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=False,
        desc="File to be written as output")
    # optional
    keep_in = traits.Bool(
        argstr="-keep-in", desc="Keep edits as found in input volume")


class EditWMwithAsegOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Output edited WM file")


class EditWMwithAseg(FSCommand):
    """
    Edits a wm file using a segmentation

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import EditWMwithAseg
    >>> editwm = EditWMwithAseg()
    >>> editwm.inputs.in_file = "T1.mgz"
    >>> editwm.inputs.brain_file = "norm.mgz"
    >>> editwm.inputs.seg_file = "aseg.mgz"
    >>> editwm.inputs.out_file = "wm.asegedit.mgz"
    >>> editwm.inputs.keep_in = True
    >>> editwm.cmdline
    'mri_edit_wm_with_aseg -keep-in T1.mgz norm.mgz aseg.mgz wm.asegedit.mgz'
    """
    _cmd = 'mri_edit_wm_with_aseg'
    input_spec = EditWMwithAsegInputSpec
    output_spec = EditWMwithAsegOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs


class ConcatenateLTAInputSpec(FSTraitedSpec):
    # required
    in_lta1 = File(
        exists=True,
        mandatory=True,
        argstr='%s',
        position=-3,
        desc='maps some src1 to dst1')
    in_lta2 = traits.Either(
        File(exists=True),
        'identity.nofile',
        argstr='%s',
        position=-2,
        mandatory=True,
        desc='maps dst1(src2) to dst2')
    out_file = File(
        position=-1,
        argstr='%s',
        hash_files=False,
        name_source=['in_lta1'],
        name_template='%s_concat',
        keep_extension=True,
        desc='the combined LTA maps: src1 to dst2 = LTA2*LTA1')

    # Inversion and transform type
    invert_1 = traits.Bool(
        argstr='-invert1', desc='invert in_lta1 before applying it')
    invert_2 = traits.Bool(
        argstr='-invert2', desc='invert in_lta2 before applying it')
    invert_out = traits.Bool(argstr='-invertout', desc='invert output LTA')
    out_type = traits.Enum(
        'VOX2VOX', 'RAS2RAS', argstr='-out_type %d', desc='set final LTA type')

    # Talairach options
    tal_source_file = traits.File(
        exists=True,
        argstr='-tal %s',
        position=-5,
        requires=['tal_template_file'],
        desc='if in_lta2 is talairach.xfm, specify source for talairach')
    tal_template_file = traits.File(
        exists=True,
        argstr='%s',
        position=-4,
        requires=['tal_source_file'],
        desc='if in_lta2 is talairach.xfm, specify template for talairach')

    subject = traits.Str(
        argstr='-subject %s', desc='set subject in output LTA')
    # Note rmsdiff would be xor out_file, and would be most easily dealt with
    # in a new interface. -CJM 2017.10.05


class ConcatenateLTAOutputSpec(TraitedSpec):
    out_file = File(
        exists=False, desc='the combined LTA maps: src1 to dst2 = LTA2*LTA1')


class ConcatenateLTA(FSCommand):
    """ Concatenates two consecutive LTA transformations into one overall
    transformation

    Out = LTA2*LTA1

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import ConcatenateLTA
    >>> conc_lta = ConcatenateLTA()
    >>> conc_lta.inputs.in_lta1 = 'lta1.lta'
    >>> conc_lta.inputs.in_lta2 = 'lta2.lta'
    >>> conc_lta.cmdline
    'mri_concatenate_lta lta1.lta lta2.lta lta1_concat.lta'

    You can use 'identity.nofile' as the filename for in_lta2, e.g.:

    >>> conc_lta.inputs.in_lta2 = 'identity.nofile'
    >>> conc_lta.inputs.invert_1 = True
    >>> conc_lta.inputs.out_file = 'inv1.lta'
    >>> conc_lta.cmdline
    'mri_concatenate_lta -invert1 lta1.lta identity.nofile inv1.lta'

    To create a RAS2RAS transform:

    >>> conc_lta.inputs.out_type = 'RAS2RAS'
    >>> conc_lta.cmdline
    'mri_concatenate_lta -invert1 -out_type 1 lta1.lta identity.nofile inv1.lta'
    """

    _cmd = 'mri_concatenate_lta'
    input_spec = ConcatenateLTAInputSpec
    output_spec = ConcatenateLTAOutputSpec

    def _format_arg(self, name, spec, value):
        if name == 'out_type':
            value = {'VOX2VOX': 0, 'RAS2RAS': 1}[value]
        return super(ConcatenateLTA, self)._format_arg(name, spec, value)
