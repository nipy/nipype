# -*- coding: utf-8 -*-
"""The dcm2nii module provides basic functions for dicom conversion

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
   >>> os.chdir(datadir)
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import str, open
import os
import re
from copy import deepcopy

from ..utils.filemanip import split_filename
from .base import (CommandLine, CommandLineInputSpec, InputMultiPath, traits,
                   TraitedSpec, OutputMultiPath, isdefined, File, Directory)


class Dcm2niiInputSpec(CommandLineInputSpec):
    source_names = InputMultiPath(
        File(exists=True),
        argstr="%s",
        position=-1,
        copyfile=False,
        mandatory=True,
        xor=['source_dir'])
    source_dir = Directory(
        exists=True,
        argstr="%s",
        position=-1,
        mandatory=True,
        xor=['source_names'])
    anonymize = traits.Bool(
        True,
        argstr='-a',
        usedefault=True,
        desc="Remove identifying information")
    config_file = File(
        exists=True,
        argstr="-b %s",
        genfile=True,
        desc="Load settings from specified inifile")
    collapse_folders = traits.Bool(
        True, argstr='-c', usedefault=True, desc="Collapse input folders")
    date_in_filename = traits.Bool(
        True, argstr='-d', usedefault=True, desc="Date in filename")
    events_in_filename = traits.Bool(
        True,
        argstr='-e',
        usedefault=True,
        desc="Events (series/acq) in filename")
    source_in_filename = traits.Bool(
        False, argstr='-f', usedefault=True, desc="Source filename")
    gzip_output = traits.Bool(
        False, argstr='-g', usedefault=True, desc="Gzip output (.gz)")
    id_in_filename = traits.Bool(
        False, argstr='-i', usedefault=True, desc="ID  in filename")
    nii_output = traits.Bool(
        True,
        argstr='-n',
        usedefault=True,
        desc="Save as .nii - if no, create .hdr/.img pair")
    output_dir = Directory(
        exists=True,
        argstr='-o %s',
        genfile=True,
        desc="Output dir - if unspecified, source directory is used")
    protocol_in_filename = traits.Bool(
        True, argstr='-p', usedefault=True, desc="Protocol in filename")
    reorient = traits.Bool(
        argstr='-r', desc="Reorient image to nearest orthogonal")
    spm_analyze = traits.Bool(
        argstr='-s', xor=['nii_output'], desc="SPM2/Analyze not SPM5/NIfTI")
    convert_all_pars = traits.Bool(
        True,
        argstr='-v',
        usedefault=True,
        desc="Convert every image in directory")
    reorient_and_crop = traits.Bool(
        False,
        argstr='-x',
        usedefault=True,
        desc="Reorient and crop 3D images")


class Dcm2niiOutputSpec(TraitedSpec):
    converted_files = OutputMultiPath(File(exists=True))
    reoriented_files = OutputMultiPath(File(exists=True))
    reoriented_and_cropped_files = OutputMultiPath(File(exists=True))
    bvecs = OutputMultiPath(File(exists=True))
    bvals = OutputMultiPath(File(exists=True))


class Dcm2nii(CommandLine):
    """Uses MRIcron's dcm2nii to convert dicom files

    Examples
    ========

    .. testsetup::

    >>> tmp = getfixture('tmpdir')
    >>> old = tmp.chdir() # changing to a temporary directory

    .. doctest::

    >>> from nipype.interfaces.dcm2nii import Dcm2nii
    >>> converter = Dcm2nii()
    >>> converter.inputs.source_names = [os.path.join(datadir, 'functional_1.dcm'), os.path.join(datadir, 'functional_2.dcm')]
    >>> converter.inputs.gzip_output = True
    >>> converter.inputs.output_dir = '.'
    >>> converter.cmdline #doctest: +ELLIPSIS
    'dcm2nii -a y -c y -b config.ini -v y -d y -e y -g y -i n -n y -o . -p y -x n -f n ...functional_1.dcm'

    .. testsetup::

    >>> os.chdir(old.strpath)

    """

    input_spec = Dcm2niiInputSpec
    output_spec = Dcm2niiOutputSpec
    _cmd = 'dcm2nii'

    def _format_arg(self, opt, spec, val):
        if opt in [
                'anonymize', 'collapse_folders', 'date_in_filename',
                'events_in_filename', 'source_in_filename', 'gzip_output',
                'id_in_filename', 'nii_output', 'protocol_in_filename',
                'reorient', 'spm_analyze', 'convert_all_pars',
                'reorient_and_crop'
        ]:
            spec = deepcopy(spec)
            if val:
                spec.argstr += ' y'
            else:
                spec.argstr += ' n'
                val = True
        if opt == 'source_names':
            return spec.argstr % val[0]
        return super(Dcm2nii, self)._format_arg(opt, spec, val)

    def _run_interface(self, runtime):
        self._config_created = False
        new_runtime = super(Dcm2nii, self)._run_interface(runtime)
        (self.output_files, self.reoriented_files,
         self.reoriented_and_cropped_files, self.bvecs,
         self.bvals) = self._parse_stdout(new_runtime.stdout)
        if self._config_created:
            os.remove('config.ini')
        return new_runtime

    def _parse_stdout(self, stdout):
        files = []
        reoriented_files = []
        reoriented_and_cropped_files = []
        bvecs = []
        bvals = []
        skip = False
        last_added_file = None
        for line in stdout.split("\n"):
            if not skip:
                out_file = None
                if line.startswith("Saving "):
                    out_file = line[len("Saving "):]
                elif line.startswith("GZip..."):
                    # for gzipped output files are not absolute
                    fname = line[len("GZip..."):]
                    if len(files) and os.path.basename(
                            files[-1]) == fname[:-3]:
                        # we are seeing a previously reported conversion
                        # as being saved in gzipped form -- remove the
                        # obsolete, uncompressed file
                        files.pop()
                    if isdefined(self.inputs.output_dir):
                        output_dir = self.inputs.output_dir
                    else:
                        output_dir = self._gen_filename('output_dir')
                    out_file = os.path.abspath(os.path.join(output_dir, fname))
                elif line.startswith("Number of diffusion directions "):
                    if last_added_file:
                        base, filename, ext = split_filename(last_added_file)
                        bvecs.append(os.path.join(base, filename + ".bvec"))
                        bvals.append(os.path.join(base, filename + ".bval"))
                elif line.startswith("Removed DWI from DTI scan"):
                    # such line can only follow the 'diffusion' case handled
                    # just above
                    for l in (bvecs, bvals):
                        l[-1] = os.path.join(
                            os.path.dirname(l[-1]),
                            'x%s' % (os.path.basename(l[-1]), ))
                elif re.search('.*->(.*)', line):
                    val = re.search('.*->(.*)', line)
                    val = val.groups()[0]
                    if isdefined(self.inputs.output_dir):
                        output_dir = self.inputs.output_dir
                    else:
                        output_dir = self._gen_filename('output_dir')
                    val = os.path.join(output_dir, val)
                    if os.path.exists(val):
                        out_file = val

                if out_file:
                    if out_file not in files:
                        files.append(out_file)
                        last_added_file = out_file
                    continue

                if line.startswith("Reorienting as "):
                    reoriented_files.append(line[len("Reorienting as "):])
                    skip = True
                    continue
                elif line.startswith("Cropping NIfTI/Analyze image "):
                    base, filename = os.path.split(
                        line[len("Cropping NIfTI/Analyze image "):])
                    filename = "c" + filename
                    if os.path.exists(os.path.join(
                            base, filename)) or self.inputs.reorient_and_crop:
                        # if reorient&crop is true but the file doesn't exist, this errors when setting outputs
                        reoriented_and_cropped_files.append(
                            os.path.join(base, filename))
                        skip = True
                        continue

            skip = False
        return files, reoriented_files, reoriented_and_cropped_files, bvecs, bvals

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['converted_files'] = self.output_files
        outputs['reoriented_files'] = self.reoriented_files
        outputs[
            'reoriented_and_cropped_files'] = self.reoriented_and_cropped_files
        outputs['bvecs'] = self.bvecs
        outputs['bvals'] = self.bvals
        return outputs

    def _gen_filename(self, name):
        if name == 'output_dir':
            return os.getcwd()
        elif name == 'config_file':
            self._config_created = True
            config_file = "config.ini"
            with open(config_file, "w") as f:
                # disable interactive mode
                f.write("[BOOL]\nManualNIfTIConv=0\n")
            return config_file
        return None


class Dcm2niixInputSpec(CommandLineInputSpec):
    source_names = InputMultiPath(
        File(exists=True),
        argstr="%s",
        position=-1,
        copyfile=False,
        mandatory=True,
        xor=['source_dir'])
    source_dir = Directory(
        exists=True,
        argstr="%s",
        position=-1,
        mandatory=True,
        xor=['source_names'])
    out_filename = traits.Str(
        '%t%p', argstr="-f %s", usedefault=True, desc="Output filename")
    output_dir = Directory(
        exists=True, argstr='-o %s', genfile=True, desc="Output directory")
    bids_format = traits.Bool(
        True, argstr='-b', usedefault=True, desc="Create a BIDS sidecar file")
    compress = traits.Enum(
        'i', ['y', 'i', 'n'],
        argstr='-z %s',
        usedefault=True,
        desc="Gzip compress images - [y=pigz, i=internal, n=no]")
    merge_imgs = traits.Bool(
        False,
        argstr='-m',
        usedefault=True,
        desc="merge 2D slices from same series")
    single_file = traits.Bool(
        False,
        argstr='-s',
        usedefault=True,
        desc="Convert only one image (filename as last input")
    verbose = traits.Bool(
        False, argstr='-v', usedefault=True, desc="Verbose output")
    crop = traits.Bool(
        False, argstr='-x', usedefault=True, desc="Crop 3D T1 acquisitions")
    has_private = traits.Bool(
        False,
        argstr='-t',
        usedefault=True,
        desc="Flag if text notes includes private patient details")


class Dcm2niixOutputSpec(TraitedSpec):
    converted_files = OutputMultiPath(File(exists=True))
    bvecs = OutputMultiPath(File(exists=True))
    bvals = OutputMultiPath(File(exists=True))
    bids = OutputMultiPath(File(exists=True))


class Dcm2niix(CommandLine):
    """Uses Chris Rorden's dcm2niix to convert dicom files

    Examples
    ========

    >>> from nipype.interfaces.dcm2nii import Dcm2niix
    >>> converter = Dcm2niix()
    >>> converter.inputs.source_names = ['functional_1.dcm', 'functional_2.dcm']
    >>> converter.inputs.compress = 'i'
    >>> converter.inputs.single_file = True
    >>> converter.inputs.output_dir = '.'
    >>> converter.cmdline # doctest: +SKIP
    'dcm2niix -b y -z i -x n -t n -m n -f %t%p -o . -s y -v n functional_1.dcm'

    >>> flags = '-'.join([val.strip() + ' ' for val in sorted(' '.join(converter.cmdline.split()[1:-1]).split('-'))])
    >>> flags
    ' -b y -f %t%p -m n -o . -s y -t n -v n -x n -z i '
    """

    input_spec = Dcm2niixInputSpec
    output_spec = Dcm2niixOutputSpec
    _cmd = 'dcm2niix'

    def _format_arg(self, opt, spec, val):
        if opt in [
                'bids_format', 'merge_imgs', 'single_file', 'verbose', 'crop',
                'has_private'
        ]:
            spec = deepcopy(spec)
            if val:
                spec.argstr += ' y'
            else:
                spec.argstr += ' n'
                val = True
        if opt == 'source_names':
            return spec.argstr % val[0]
        return super(Dcm2niix, self)._format_arg(opt, spec, val)

    def _run_interface(self, runtime):
        new_runtime = super(Dcm2niix, self)._run_interface(runtime)
        if self.inputs.bids_format:
            (self.output_files, self.bvecs, self.bvals,
             self.bids) = self._parse_stdout(new_runtime.stdout)
        else:
            (self.output_files, self.bvecs, self.bvals) = self._parse_stdout(
                new_runtime.stdout)
        return new_runtime

    def _parse_stdout(self, stdout):
        files = []
        bvecs = []
        bvals = []
        bids = []
        skip = False
        find_b = False
        for line in stdout.split("\n"):
            if not skip:
                out_file = None
                if line.startswith("Convert "):  # output
                    fname = str(re.search('\S+/\S+', line).group(0))
                    if isdefined(self.inputs.output_dir):
                        output_dir = self.inputs.output_dir
                    else:
                        output_dir = self._gen_filename('output_dir')
                    out_file = os.path.abspath(os.path.join(output_dir, fname))
                    # extract bvals
                    if find_b:
                        bvecs.append(out_file + ".bvec")
                        bvals.append(out_file + ".bval")
                        find_b = False
                # next scan will have bvals/bvecs
                elif 'DTI gradients' in line or 'DTI gradient directions' in line or 'DTI vectors' in line:
                    find_b = True
                else:
                    pass
                if out_file:
                    if self.inputs.compress == 'n':
                        files.append(out_file + ".nii")
                    else:
                        files.append(out_file + ".nii.gz")
                    if self.inputs.bids_format:
                        bids.append(out_file + ".json")
                    continue
            skip = False
        # just return what was done
        if not bids:
            return files, bvecs, bvals
        else:
            return files, bvecs, bvals, bids

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['converted_files'] = self.output_files
        outputs['bvecs'] = self.bvecs
        outputs['bvals'] = self.bvals
        if self.inputs.bids_format:
            outputs['bids'] = self.bids
        return outputs

    def _gen_filename(self, name):
        if name == 'output_dir':
            return os.getcwd()
        return None
