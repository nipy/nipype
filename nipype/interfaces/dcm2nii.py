# -*- coding: utf-8 -*-
"""dcm2nii converts images from the proprietary scanner DICOM format to NIfTI."""
import os
import re
from copy import deepcopy
import itertools as it
import glob
from glob import iglob

from ..utils.filemanip import split_filename
from .base import (
    CommandLine,
    CommandLineInputSpec,
    InputMultiPath,
    traits,
    TraitedSpec,
    OutputMultiPath,
    isdefined,
    File,
    Directory,
    PackageInfo,
)


class Info(PackageInfo):
    """Handle dcm2niix version information"""

    version_cmd = "dcm2niix"

    @staticmethod
    def parse_version(raw_info):
        m = re.search(r"version (\S+)", raw_info)
        return m.groups()[0] if m else None


class Dcm2niiInputSpec(CommandLineInputSpec):
    source_names = InputMultiPath(
        File(exists=True),
        argstr="%s",
        position=-1,
        copyfile=False,
        mandatory=True,
        xor=["source_dir"],
    )
    source_dir = Directory(
        exists=True, argstr="%s", position=-1, mandatory=True, xor=["source_names"]
    )
    anonymize = traits.Bool(
        True, argstr="-a", usedefault=True, desc="Remove identifying information"
    )
    config_file = File(
        exists=True,
        argstr="-b %s",
        genfile=True,
        desc="Load settings from specified inifile",
    )
    collapse_folders = traits.Bool(
        True, argstr="-c", usedefault=True, desc="Collapse input folders"
    )
    date_in_filename = traits.Bool(
        True, argstr="-d", usedefault=True, desc="Date in filename"
    )
    events_in_filename = traits.Bool(
        True, argstr="-e", usedefault=True, desc="Events (series/acq) in filename"
    )
    source_in_filename = traits.Bool(
        False, argstr="-f", usedefault=True, desc="Source filename"
    )
    gzip_output = traits.Bool(
        False, argstr="-g", usedefault=True, desc="Gzip output (.gz)"
    )
    id_in_filename = traits.Bool(
        False, argstr="-i", usedefault=True, desc="ID  in filename"
    )
    nii_output = traits.Bool(
        True,
        argstr="-n",
        usedefault=True,
        desc="Save as .nii - if no, create .hdr/.img pair",
    )
    output_dir = Directory(
        exists=True,
        argstr="-o %s",
        genfile=True,
        desc="Output dir - if unspecified, source directory is used",
    )
    protocol_in_filename = traits.Bool(
        True, argstr="-p", usedefault=True, desc="Protocol in filename"
    )
    reorient = traits.Bool(argstr="-r", desc="Reorient image to nearest orthogonal")
    spm_analyze = traits.Bool(
        argstr="-s", xor=["nii_output"], desc="SPM2/Analyze not SPM5/NIfTI"
    )
    convert_all_pars = traits.Bool(
        True, argstr="-v", usedefault=True, desc="Convert every image in directory"
    )
    reorient_and_crop = traits.Bool(
        False, argstr="-x", usedefault=True, desc="Reorient and crop 3D images"
    )


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

    >>> from nipype.interfaces.dcm2nii import Dcm2nii
    >>> converter = Dcm2nii()
    >>> converter.inputs.source_names = ['functional_1.dcm', 'functional_2.dcm']
    >>> converter.inputs.gzip_output = True
    >>> converter.inputs.output_dir = '.'
    >>> converter.cmdline  # doctest: +ELLIPSIS
    'dcm2nii -a y -c y -b config.ini -v y -d y -e y -g y -i n -n y -o . -p y -x n -f n functional_1.dcm'
    """

    input_spec = Dcm2niiInputSpec
    output_spec = Dcm2niiOutputSpec
    _cmd = "dcm2nii"

    def _format_arg(self, opt, spec, val):
        if opt in [
            "anonymize",
            "collapse_folders",
            "date_in_filename",
            "events_in_filename",
            "source_in_filename",
            "gzip_output",
            "id_in_filename",
            "nii_output",
            "protocol_in_filename",
            "reorient",
            "spm_analyze",
            "convert_all_pars",
            "reorient_and_crop",
        ]:
            spec = deepcopy(spec)
            if val:
                spec.argstr += " y"
            else:
                spec.argstr += " n"
                val = True
        if opt == "source_names":
            return spec.argstr % val[0]
        return super(Dcm2nii, self)._format_arg(opt, spec, val)

    def _run_interface(self, runtime):
        self._config_created = False
        new_runtime = super(Dcm2nii, self)._run_interface(runtime)
        (
            self.output_files,
            self.reoriented_files,
            self.reoriented_and_cropped_files,
            self.bvecs,
            self.bvals,
        ) = self._parse_stdout(new_runtime.stdout)
        if self._config_created:
            os.remove("config.ini")
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
                    out_file = line[len("Saving ") :]
                elif line.startswith("GZip..."):
                    # for gzipped output files are not absolute
                    fname = line[len("GZip...") :]
                    if len(files) and os.path.basename(files[-1]) == fname[:-3]:
                        # we are seeing a previously reported conversion
                        # as being saved in gzipped form -- remove the
                        # obsolete, uncompressed file
                        files.pop()
                    if isdefined(self.inputs.output_dir):
                        output_dir = self.inputs.output_dir
                    else:
                        output_dir = self._gen_filename("output_dir")
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
                            os.path.dirname(l[-1]), "x%s" % (os.path.basename(l[-1]),)
                        )
                elif re.search(".*->(.*)", line):
                    val = re.search(".*->(.*)", line)
                    val = val.groups()[0]
                    if isdefined(self.inputs.output_dir):
                        output_dir = self.inputs.output_dir
                    else:
                        output_dir = self._gen_filename("output_dir")
                    val = os.path.join(output_dir, val)
                    if os.path.exists(val):
                        out_file = val

                if out_file:
                    if out_file not in files:
                        files.append(out_file)
                        last_added_file = out_file
                    continue

                if line.startswith("Reorienting as "):
                    reoriented_files.append(line[len("Reorienting as ") :])
                    skip = True
                    continue
                elif line.startswith("Cropping NIfTI/Analyze image "):
                    base, filename = os.path.split(
                        line[len("Cropping NIfTI/Analyze image ") :]
                    )
                    filename = "c" + filename
                    if (
                        os.path.exists(os.path.join(base, filename))
                        or self.inputs.reorient_and_crop
                    ):
                        # if reorient&crop is true but the file doesn't exist, this errors when setting outputs
                        reoriented_and_cropped_files.append(
                            os.path.join(base, filename)
                        )
                        skip = True
                        continue

            skip = False
        return files, reoriented_files, reoriented_and_cropped_files, bvecs, bvals

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["converted_files"] = self.output_files
        outputs["reoriented_files"] = self.reoriented_files
        outputs["reoriented_and_cropped_files"] = self.reoriented_and_cropped_files
        outputs["bvecs"] = self.bvecs
        outputs["bvals"] = self.bvals
        return outputs

    def _gen_filename(self, name):
        if name == "output_dir":
            return os.getcwd()
        elif name == "config_file":
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
        desc=(
            "A set of filenames to be converted. Note that the current "
            "version (1.0.20180328) of dcm2niix converts any files in the "
            "directory. To only convert specific files they should be in an "
            "isolated directory"
        ),
        xor=["source_dir"],
    )
    source_dir = Directory(
        exists=True,
        argstr="%s",
        position=-1,
        mandatory=True,
        desc="A directory containing dicom files to be converted",
        xor=["source_names"],
    )
    out_filename = traits.Str(
        argstr="-f %s",
        desc="Output filename template ("
        "%a=antenna (coil) number, "
        "%c=comments, "
        "%d=description, "
        "%e=echo number, "
        "%f=folder name, "
        "%i=ID of patient, "
        "%j=seriesInstanceUID, "
        "%k=studyInstanceUID, "
        "%m=manufacturer, "
        "%n=name of patient, "
        "%p=protocol, "
        "%s=series number, "
        "%t=time, "
        "%u=acquisition number, "
        "%v=vendor, "
        "%x=study ID; "
        "%z=sequence name)",
    )
    output_dir = Directory(
        ".", usedefault=True, exists=True, argstr="-o %s", desc="Output directory"
    )
    bids_format = traits.Bool(
        True, argstr="-b", usedefault=True, desc="Create a BIDS sidecar file"
    )
    anon_bids = traits.Bool(
        argstr="-ba", requires=["bids_format"], desc="Anonymize BIDS"
    )
    compress = traits.Enum(
        "y",
        "i",
        "n",
        "3",
        argstr="-z %s",
        usedefault=True,
        desc="Gzip compress images - [y=pigz, i=internal, n=no, 3=no,3D]",
    )
    merge_imgs = traits.Bool(
        False, argstr="-m", usedefault=True, desc="merge 2D slices from same series"
    )
    single_file = traits.Bool(
        False, argstr="-s", usedefault=True, desc="Single file mode"
    )
    verbose = traits.Bool(False, argstr="-v", usedefault=True, desc="Verbose output")
    crop = traits.Bool(
        False, argstr="-x", usedefault=True, desc="Crop 3D T1 acquisitions"
    )
    has_private = traits.Bool(
        False,
        argstr="-t",
        usedefault=True,
        desc="Text notes including private patient details",
    )
    compression = traits.Enum(
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        argstr="-%d",
        desc="Gz compression level (1=fastest, 9=smallest)",
    )
    comment = traits.Str(argstr="-c %s", desc="Comment stored as NIfTI aux_file")
    ignore_deriv = traits.Bool(
        argstr="-i", desc="Ignore derived, localizer and 2D images"
    )
    series_numbers = InputMultiPath(
        traits.Str(),
        argstr="-n %s...",
        desc="Selectively convert by series number - can be used up to 16 times",
    )
    philips_float = traits.Bool(
        argstr="-p", desc="Philips precise float (not display) scaling"
    )
    to_nrrd = traits.Bool(argstr="-e", desc="Export as NRRD instead of NIfTI")


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
    >>> converter.inputs.source_dir = 'dicomdir'
    >>> converter.inputs.compression = 5
    >>> converter.inputs.output_dir = 'ds005'
    >>> converter.cmdline
    'dcm2niix -b y -z y -5 -x n -t n -m n -o ds005 -s n -v n dicomdir'
    >>> converter.run() # doctest: +SKIP

    In the example below, we note that the current version of dcm2niix
    converts any files in the directory containing the files in the list. We
    also do not support nested filenames with this option. **Thus all files
    must have a common root directory.**

    >>> converter = Dcm2niix()
    >>> converter.inputs.source_names = ['functional_1.dcm', 'functional_2.dcm']
    >>> converter.inputs.compression = 5
    >>> converter.inputs.output_dir = 'ds005'
    >>> converter.cmdline
    'dcm2niix -b y -z y -5 -x n -t n -m n -o ds005 -s n -v n .'
    >>> converter.run() # doctest: +SKIP
    """

    input_spec = Dcm2niixInputSpec
    output_spec = Dcm2niixOutputSpec
    _cmd = "dcm2niix"

    @property
    def version(self):
        return Info.version()

    def _format_arg(self, opt, spec, val):
        bools = [
            "bids_format",
            "merge_imgs",
            "single_file",
            "verbose",
            "crop",
            "has_private",
            "anon_bids",
            "ignore_deriv",
            "philips_float",
            "to_nrrd",
        ]
        if opt in bools:
            spec = deepcopy(spec)
            if val:
                spec.argstr += " y"
            else:
                spec.argstr += " n"
                val = True
        if opt == "source_names":
            return spec.argstr % (os.path.dirname(val[0]) or ".")
        return super(Dcm2niix, self)._format_arg(opt, spec, val)

    def _run_interface(self, runtime):
        # may use return code 1 despite conversion
        runtime = super(Dcm2niix, self)._run_interface(
            runtime, correct_return_codes=(0, 1)
        )
        self._parse_files(self._parse_stdout(runtime.stdout))
        return runtime

    def _parse_stdout(self, stdout):
        filenames = []
        for line in stdout.split("\n"):
            if line.startswith("Convert "):  # output
                fname = str(re.search(r"\S+/\S+", line).group(0))
                filenames.append(os.path.abspath(fname))
        return filenames

    def _parse_files(self, filenames):
        outfiles, bvals, bvecs, bids = [], [], [], []
        outtypes = [".bval", ".bvec", ".json", ".txt"]
        if self.inputs.to_nrrd:
            outtypes += [".nrrd", ".nhdr", ".raw.gz"]
        else:
            outtypes += [".nii", ".nii.gz"]

        for filename in filenames:
            # search for relevant files, and sort accordingly
            for fl in search_files(filename, outtypes):
                if (
                    fl.endswith(".nii")
                    or fl.endswith(".gz")
                    or fl.endswith(".nrrd")
                    or fl.endswith(".nhdr")
                ):
                    outfiles.append(fl)
                elif fl.endswith(".bval"):
                    bvals.append(fl)
                elif fl.endswith(".bvec"):
                    bvecs.append(fl)
                elif fl.endswith(".json") or fl.endswith(".txt"):
                    bids.append(fl)
        self.output_files = outfiles
        self.bvecs = bvecs
        self.bvals = bvals
        self.bids = bids

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["converted_files"] = self.output_files
        outputs["bvecs"] = self.bvecs
        outputs["bvals"] = self.bvals
        outputs["bids"] = self.bids
        return outputs


# https://stackoverflow.com/a/4829130
def search_files(prefix, outtypes):
    return it.chain.from_iterable(
        iglob(glob.escape(prefix + outtype)) for outtype in outtypes
    )
