# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The minc module provides classes for interfacing with the `MINC
<http://www.bic.mni.mcgill.ca/ServicesSoftware/MINC>`_ command line tools.  This
module was written to work with MINC version 2.2.00.

Author: `Carlo Hamalainen <http://carlo-hamalainen.net>`__
"""
import glob
import os
import os.path
import re
import warnings

from ..base import (
    TraitedSpec,
    CommandLineInputSpec,
    CommandLine,
    StdOutCommandLineInputSpec,
    StdOutCommandLine,
    File,
    Directory,
    InputMultiPath,
    OutputMultiPath,
    traits,
    isdefined,
)
from .base import aggregate_filename

warnings.filterwarnings("always", category=UserWarning)


class ExtractInputSpec(StdOutCommandLineInputSpec):
    input_file = File(
        desc="input file", exists=True, mandatory=True, argstr="%s", position=-2,
    )

    output_file = File(
        desc="output file",
        position=-1,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s.raw",
        keep_extension=False,
    )

    _xor_write = (
        "write_ascii",
        "write_ascii",
        "write_byte",
        "write_short",
        "write_int",
        "write_long",
        "write_float",
        "write_double",
        "write_signed",
        "write_unsigned",
    )

    write_ascii = traits.Bool(
        desc="Write out data as ascii strings (default).",
        argstr="-ascii",
        xor=_xor_write,
    )

    write_byte = traits.Bool(
        desc="Write out data as bytes.", argstr="-byte", xor=_xor_write
    )

    write_short = traits.Bool(
        desc="Write out data as short integers.", argstr="-short", xor=_xor_write
    )

    write_int = traits.Bool(
        desc="Write out data as 32-bit integers.", argstr="-int", xor=_xor_write
    )

    write_long = traits.Bool(
        desc="Superseded by write_int.", argstr="-long", xor=_xor_write
    )

    write_float = traits.Bool(
        desc="Write out data as single precision floating-point values.",
        argstr="-float",
        xor=_xor_write,
    )

    write_double = traits.Bool(
        desc="Write out data as double precision floating-point values.",
        argstr="-double",
        xor=_xor_write,
    )

    _xor_signed = ("write_signed", "write_unsigned")

    write_signed = traits.Bool(
        desc="Write out signed data.", argstr="-signed", xor=_xor_signed
    )

    write_unsigned = traits.Bool(
        desc="Write out unsigned data.", argstr="-unsigned", xor=_xor_signed
    )

    write_range = traits.Tuple(
        traits.Float,
        traits.Float,
        argstr="-range %s %s",
        desc="Specify the range of output values\nDefault value: 1.79769e+308 1.79769e+308.",
    )

    _xor_normalize = (
        "normalize",
        "nonormalize",
    )

    normalize = traits.Bool(
        desc="Normalize integer pixel values to file max and min.",
        argstr="-normalize",
        xor=_xor_normalize,
    )

    nonormalize = traits.Bool(
        desc="Turn off pixel normalization.", argstr="-nonormalize", xor=_xor_normalize
    )

    image_range = traits.Tuple(
        traits.Float,
        traits.Float,
        desc="Specify the range of real image values for normalization.",
        argstr="-image_range %s %s",
    )

    image_minimum = traits.Float(
        desc=(
            "Specify the minimum real image value for normalization."
            "Default value: 1.79769e+308."
        ),
        argstr="-image_minimum %s",
    )

    image_maximum = traits.Float(
        desc=(
            "Specify the maximum real image value for normalization."
            "Default value: 1.79769e+308."
        ),
        argstr="-image_maximum %s",
    )

    start = InputMultiPath(
        traits.Int,
        desc="Specifies corner of hyperslab (C conventions for indices).",
        sep=",",
        argstr="-start %s",
    )

    count = InputMultiPath(
        traits.Int,
        desc="Specifies edge lengths of hyperslab to read.",
        sep=",",
        argstr="-count %s",
    )

    # FIXME Can we make sure that len(start) == len(count)?

    _xor_flip = (
        "flip_positive_direction",
        "flip_negative_direction",
        "flip_any_direction",
    )

    flip_positive_direction = traits.Bool(
        desc="Flip images to always have positive direction.",
        argstr="-positive_direction",
        xor=_xor_flip,
    )
    flip_negative_direction = traits.Bool(
        desc="Flip images to always have negative direction.",
        argstr="-negative_direction",
        xor=_xor_flip,
    )
    flip_any_direction = traits.Bool(
        desc="Do not flip images (Default).", argstr="-any_direction", xor=_xor_flip
    )

    _xor_x_flip = ("flip_x_positive", "flip_x_negative", "flip_x_any")

    flip_x_positive = traits.Bool(
        desc="Flip images to give positive xspace:step value (left-to-right).",
        argstr="+xdirection",
        xor=_xor_x_flip,
    )
    flip_x_negative = traits.Bool(
        desc="Flip images to give negative xspace:step value (right-to-left).",
        argstr="-xdirection",
        xor=_xor_x_flip,
    )
    flip_x_any = traits.Bool(
        desc="Don't flip images along x-axis (default).",
        argstr="-xanydirection",
        xor=_xor_x_flip,
    )

    _xor_y_flip = ("flip_y_positive", "flip_y_negative", "flip_y_any")

    flip_y_positive = traits.Bool(
        desc="Flip images to give positive yspace:step value (post-to-ant).",
        argstr="+ydirection",
        xor=_xor_y_flip,
    )
    flip_y_negative = traits.Bool(
        desc="Flip images to give negative yspace:step value (ant-to-post).",
        argstr="-ydirection",
        xor=_xor_y_flip,
    )
    flip_y_any = traits.Bool(
        desc="Don't flip images along y-axis (default).",
        argstr="-yanydirection",
        xor=_xor_y_flip,
    )

    _xor_z_flip = ("flip_z_positive", "flip_z_negative", "flip_z_any")

    flip_z_positive = traits.Bool(
        desc="Flip images to give positive zspace:step value (inf-to-sup).",
        argstr="+zdirection",
        xor=_xor_z_flip,
    )
    flip_z_negative = traits.Bool(
        desc="Flip images to give negative zspace:step value (sup-to-inf).",
        argstr="-zdirection",
        xor=_xor_z_flip,
    )
    flip_z_any = traits.Bool(
        desc="Don't flip images along z-axis (default).",
        argstr="-zanydirection",
        xor=_xor_z_flip,
    )


class ExtractOutputSpec(TraitedSpec):
    output_file = File(desc="output file in raw/text format", exists=True)


class Extract(StdOutCommandLine):
    """Dump a hyperslab of MINC file data.

    Examples
    --------

    >>> from nipype.interfaces.minc import Extract
    >>> from nipype.interfaces.minc.testdata import minc2Dfile

    >>> extract = Extract(input_file=minc2Dfile)
    >>> extract.run() # doctest: +SKIP

    >>> extract = Extract(input_file=minc2Dfile, start=[3, 10, 5], count=[4, 4, 4]) # extract a 4x4x4 slab at offset [3, 10, 5]
    >>> extract.run() # doctest: +SKIP
    """

    input_spec = ExtractInputSpec
    output_spec = ExtractOutputSpec
    _cmd = "mincextract"


class ToRawInputSpec(StdOutCommandLineInputSpec):
    input_file = File(
        desc="input file", exists=True, mandatory=True, argstr="%s", position=-2,
    )

    output_file = File(
        desc="output file",
        position=-1,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s.raw",
        keep_extension=False,
    )

    _xor_write = (
        "write_byte",
        "write_short",
        "write_int",
        "write_long",
        "write_float",
        "write_double",
    )

    write_byte = traits.Bool(
        desc="Write out data as bytes.", argstr="-byte", xor=_xor_write
    )

    write_short = traits.Bool(
        desc="Write out data as short integers.", argstr="-short", xor=_xor_write
    )

    write_int = traits.Bool(
        desc="Write out data as 32-bit integers.", argstr="-int", xor=_xor_write
    )

    write_long = traits.Bool(
        desc="Superseded by write_int.", argstr="-long", xor=_xor_write
    )

    write_float = traits.Bool(
        desc="Write out data as single precision floating-point values.",
        argstr="-float",
        xor=_xor_write,
    )

    write_double = traits.Bool(
        desc="Write out data as double precision floating-point values.",
        argstr="-double",
        xor=_xor_write,
    )

    _xor_signed = ("write_signed", "write_unsigned")

    write_signed = traits.Bool(
        desc="Write out signed data.", argstr="-signed", xor=_xor_signed
    )

    write_unsigned = traits.Bool(
        desc="Write out unsigned data.", argstr="-unsigned", xor=_xor_signed
    )

    write_range = traits.Tuple(
        traits.Float,
        traits.Float,
        argstr="-range %s %s",
        desc=(
            "Specify the range of output values."
            "Default value: 1.79769e+308 1.79769e+308."
        ),
    )

    _xor_normalize = (
        "normalize",
        "nonormalize",
    )

    normalize = traits.Bool(
        desc="Normalize integer pixel values to file max and min.",
        argstr="-normalize",
        xor=_xor_normalize,
    )

    nonormalize = traits.Bool(
        desc="Turn off pixel normalization.", argstr="-nonormalize", xor=_xor_normalize
    )


class ToRawOutputSpec(TraitedSpec):
    output_file = File(desc="output file in raw format", exists=True)


class ToRaw(StdOutCommandLine):
    """Dump a chunk of MINC file data. This program is largely
    superceded by mincextract (see Extract).

    Examples
    --------

    >>> from nipype.interfaces.minc import ToRaw
    >>> from nipype.interfaces.minc.testdata import minc2Dfile

    >>> toraw = ToRaw(input_file=minc2Dfile)
    >>> toraw.run() # doctest: +SKIP

    >>> toraw = ToRaw(input_file=minc2Dfile, write_range=(0, 100))
    >>> toraw.run() # doctest: +SKIP
    """

    input_spec = ToRawInputSpec
    output_spec = ToRawOutputSpec
    _cmd = "minctoraw"


class ConvertInputSpec(CommandLineInputSpec):
    input_file = File(
        desc="input file for converting",
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-2,
    )

    output_file = File(
        desc="output file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_convert_output.mnc",
    )

    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )
    two = traits.Bool(desc="Create a MINC 2 output file.", argstr="-2")

    template = traits.Bool(
        desc=(
            "Create a template file. The dimensions, variables, and"
            "attributes of the input file are preserved but all data it set to zero."
        ),
        argstr="-template",
    )

    compression = traits.Enum(
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        argstr="-compress %s",
        desc="Set the compression level, from 0 (disabled) to 9 (maximum).",
    )

    chunk = traits.Range(
        low=0,
        desc="Set the target block size for chunking (0 default, >1 block size).",
        argstr="-chunk %d",
    )


class ConvertOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)


class Convert(CommandLine):
    """convert between MINC 1 to MINC 2 format.

    Examples
    --------

    >>> from nipype.interfaces.minc import Convert
    >>> from nipype.interfaces.minc.testdata import minc2Dfile
    >>> c = Convert(input_file=minc2Dfile, output_file='/tmp/out.mnc', two=True) # Convert to MINC2 format.
    >>> c.run() # doctest: +SKIP
    """

    input_spec = ConvertInputSpec
    output_spec = ConvertOutputSpec
    _cmd = "mincconvert"


class CopyInputSpec(CommandLineInputSpec):
    input_file = File(
        desc="input file to copy",
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-2,
    )

    output_file = File(
        desc="output file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_copy.mnc",
    )

    _xor_pixel = ("pixel_values", "real_values")

    pixel_values = traits.Bool(
        desc="Copy pixel values as is.", argstr="-pixel_values", xor=_xor_pixel
    )

    real_values = traits.Bool(
        desc="Copy real pixel intensities (default).",
        argstr="-real_values",
        xor=_xor_pixel,
    )


class CopyOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)


class Copy(CommandLine):
    """
    Copy image values from one MINC file to another. Both the input
    and output files must exist, and the images in both files must
    have an equal number dimensions and equal dimension lengths.

    NOTE: This program is intended primarily for use with scripts
    such as mincedit. It does not follow the typical design rules of
    most MINC command-line tools and therefore should be used only
    with caution.
    """

    input_spec = CopyInputSpec
    output_spec = CopyOutputSpec
    _cmd = "minccopy"


class ToEcatInputSpec(CommandLineInputSpec):
    input_file = File(
        desc="input file to convert",
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-2,
    )

    output_file = File(
        desc="output file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_to_ecat.v",
        keep_extension=False,
    )

    ignore_patient_variable = traits.Bool(
        desc="Ignore informations from the minc patient variable.",
        argstr="-ignore_patient_variable",
    )

    ignore_study_variable = traits.Bool(
        desc="Ignore informations from the minc study variable.",
        argstr="-ignore_study_variable",
    )

    ignore_acquisition_variable = traits.Bool(
        desc="Ignore informations from the minc acquisition variable.",
        argstr="-ignore_acquisition_variable",
    )

    ignore_ecat_acquisition_variable = traits.Bool(
        desc="Ignore informations from the minc ecat_acquisition variable.",
        argstr="-ignore_ecat_acquisition_variable",
    )

    ignore_ecat_main = traits.Bool(
        desc="Ignore informations from the minc ecat-main variable.",
        argstr="-ignore_ecat_main",
    )

    ignore_ecat_subheader_variable = traits.Bool(
        desc="Ignore informations from the minc ecat-subhdr variable.",
        argstr="-ignore_ecat_subheader_variable",
    )

    no_decay_corr_fctr = traits.Bool(
        desc="Do not compute the decay correction factors",
        argstr="-no_decay_corr_fctr",
    )

    voxels_as_integers = traits.Bool(
        desc=(
            "Voxel values are treated as integers, scale and"
            "calibration factors are set to unity"
        ),
        argstr="-label",
    )


class ToEcatOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)


class ToEcat(CommandLine):
    """Convert a 2D image, a 3D volumes or a 4D dynamic volumes
    written in MINC file format to a 2D, 3D or 4D Ecat7 file.

    Examples
    --------

    >>> from nipype.interfaces.minc import ToEcat
    >>> from nipype.interfaces.minc.testdata import minc2Dfile

    >>> c = ToEcat(input_file=minc2Dfile)
    >>> c.run() # doctest: +SKIP

    >>> c = ToEcat(input_file=minc2Dfile, voxels_as_integers=True)
    >>> c.run() # doctest: +SKIP

    """

    input_spec = ToEcatInputSpec
    output_spec = ToEcatOutputSpec
    _cmd = "minctoecat"


class DumpInputSpec(StdOutCommandLineInputSpec):
    input_file = File(
        desc="input file", exists=True, mandatory=True, argstr="%s", position=-2,
    )

    output_file = File(
        desc="output file",
        position=-1,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_dump.txt",
        keep_extension=False,
    )

    _xor_coords_or_header = (
        "coordinate_data",
        "header_data",
    )

    coordinate_data = traits.Bool(
        desc="Coordinate variable data and header information.",
        argstr="-c",
        xor=_xor_coords_or_header,
    )

    header_data = traits.Bool(
        desc="Header information only, no data.", argstr="-h", xor=_xor_coords_or_header
    )

    _xor_annotations = (
        "annotations_brief",
        "annotations_full",
    )

    annotations_brief = traits.Enum(
        "c",
        "f",
        argstr="-b %s",
        desc="Brief annotations for C or Fortran indices in data.",
        xor=_xor_annotations,
    )

    annotations_full = traits.Enum(
        "c",
        "f",
        argstr="-f %s",
        desc="Full annotations for C or Fortran indices in data.",
        xor=_xor_annotations,
    )

    variables = InputMultiPath(
        traits.Str,
        desc="Output data for specified variables only.",
        sep=",",
        argstr="-v %s",
    )

    line_length = traits.Range(
        low=0, desc="Line length maximum in data section (default 80).", argstr="-l %d"
    )

    netcdf_name = traits.Str(
        desc="Name for netCDF (default derived from file name).", argstr="-n %s"
    )

    precision = traits.Either(
        traits.Int(),
        traits.Tuple(traits.Int, traits.Int),
        desc="Display floating-point values with less precision",
        argstr="%s",
    )  # See _format_arg in Dump for actual formatting.


class DumpOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)


class Dump(StdOutCommandLine):
    """Dump a MINC file. Typically used in conjunction with mincgen (see Gen).

    Examples
    --------

    >>> from nipype.interfaces.minc import Dump
    >>> from nipype.interfaces.minc.testdata import minc2Dfile

    >>> dump = Dump(input_file=minc2Dfile)
    >>> dump.run() # doctest: +SKIP

    >>> dump = Dump(input_file=minc2Dfile, output_file='/tmp/out.txt', precision=(3, 4))
    >>> dump.run() # doctest: +SKIP

    """

    input_spec = DumpInputSpec
    output_spec = DumpOutputSpec
    _cmd = "mincdump"

    def _format_arg(self, name, spec, value):
        if name == "precision":
            if isinstance(value, int):
                return "-p %d" % value
            elif (
                isinstance(value, tuple)
                and isinstance(value[0], int)
                and isinstance(value[1], int)
            ):
                return "-p %d,%d" % (value[0], value[1],)
            else:
                raise ValueError("Invalid precision argument: " + str(value))
        return super(Dump, self)._format_arg(name, spec, value)


class AverageInputSpec(CommandLineInputSpec):
    _xor_input_files = ("input_files", "filelist")

    input_files = InputMultiPath(
        File(exists=True),
        desc="input file(s)",
        mandatory=True,
        sep=" ",
        argstr="%s",
        position=-2,
        xor=_xor_input_files,
    )

    filelist = File(
        desc="Specify the name of a file containing input file names.",
        argstr="-filelist %s",
        exists=True,
        mandatory=True,
        xor=_xor_input_files,
    )

    output_file = File(
        desc="output file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["input_files"],
        hash_files=False,
        name_template="%s_averaged.mnc",
    )

    two = traits.Bool(desc="Create a MINC 2 output file.", argstr="-2")

    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )

    _xor_verbose = (
        "verbose",
        "quiet",
    )

    verbose = traits.Bool(
        desc="Print out log messages (default).", argstr="-verbose", xor=_xor_verbose
    )
    quiet = traits.Bool(
        desc="Do not print out log messages.", argstr="-quiet", xor=_xor_verbose
    )

    debug = traits.Bool(desc="Print out debugging messages.", argstr="-debug")

    _xor_check_dimensions = (
        "check_dimensions",
        "no_check_dimensions",
    )

    check_dimensions = traits.Bool(
        desc="Check that dimension info matches across files (default).",
        argstr="-check_dimensions",
        xor=_xor_check_dimensions,
    )
    no_check_dimensions = traits.Bool(
        desc="Do not check dimension info.",
        argstr="-nocheck_dimensions",
        xor=_xor_check_dimensions,
    )

    _xor_format = (
        "format_filetype",
        "format_byte",
        "format_short",
        "format_int",
        "format_long",
        "format_float",
        "format_double",
        "format_signed",
        "format_unsigned",
    )

    format_filetype = traits.Bool(
        desc="Use data type of first file (default).",
        argstr="-filetype",
        xor=_xor_format,
    )
    format_byte = traits.Bool(
        desc="Write out byte data.", argstr="-byte", xor=_xor_format
    )
    format_short = traits.Bool(
        desc="Write out short integer data.", argstr="-short", xor=_xor_format
    )
    format_int = traits.Bool(
        desc="Write out 32-bit integer data.", argstr="-int", xor=_xor_format
    )
    format_long = traits.Bool(
        desc="Superseded by -int.", argstr="-long", xor=_xor_format
    )
    format_float = traits.Bool(
        desc="Write out single-precision floating-point data.",
        argstr="-float",
        xor=_xor_format,
    )
    format_double = traits.Bool(
        desc="Write out double-precision floating-point data.",
        argstr="-double",
        xor=_xor_format,
    )
    format_signed = traits.Bool(
        desc="Write signed integer data.", argstr="-signed", xor=_xor_format
    )
    format_unsigned = traits.Bool(
        desc="Write unsigned integer data (default).",
        argstr="-unsigned",
        xor=_xor_format,
    )

    max_buffer_size_in_kb = traits.Range(
        low=0,
        desc="Specify the maximum size of the internal buffers (in kbytes).",
        value=4096,
        usedefault=True,
        argstr="-max_buffer_size_in_kb %d",
    )

    _xor_normalize = (
        "normalize",
        "nonormalize",
    )

    normalize = traits.Bool(
        desc="Normalize data sets for mean intensity.",
        argstr="-normalize",
        xor=_xor_normalize,
    )
    nonormalize = traits.Bool(
        desc="Do not normalize data sets (default).",
        argstr="-nonormalize",
        xor=_xor_normalize,
    )

    voxel_range = traits.Tuple(
        traits.Int,
        traits.Int,
        argstr="-range %d %d",
        desc="Valid range for output data.",
    )

    sdfile = File(desc="Specify an output sd file (default=none).", argstr="-sdfile %s")

    _xor_copy_header = ("copy_header", "no_copy_header")

    copy_header = traits.Bool(
        desc="Copy all of the header from the first file (default for one file).",
        argstr="-copy_header",
        xor=_xor_copy_header,
    )
    no_copy_header = traits.Bool(
        desc="Do not copy all of the header from the first file (default for many files)).",
        argstr="-nocopy_header",
        xor=_xor_copy_header,
    )

    avgdim = traits.Str(
        desc="Specify a dimension along which we wish to average.", argstr="-avgdim %s"
    )

    binarize = traits.Bool(
        desc="Binarize the volume by looking for values in a given range.",
        argstr="-binarize",
    )

    binrange = traits.Tuple(
        traits.Float,
        traits.Float,
        argstr="-binrange %s %s",
        desc="Specify a range for binarization. Default value: 1.79769e+308 -1.79769e+308.",
    )

    binvalue = traits.Float(
        desc=(
            "Specify a target value (+/- 0.5) for"
            "binarization. Default value: -1.79769e+308"
        ),
        argstr="-binvalue %s",
    )

    weights = InputMultiPath(
        traits.Str,
        desc='Specify weights for averaging ("<w1>,<w2>,...").',
        sep=",",
        argstr="-weights %s",
    )

    width_weighted = traits.Bool(
        desc="Weight by dimension widths when -avgdim is used.",
        argstr="-width_weighted",
        requires=("avgdim",),
    )


class AverageOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)


class Average(CommandLine):
    """Average a number of MINC files.

    Examples
    --------

    >>> from nipype.interfaces.minc import Average
    >>> from nipype.interfaces.minc.testdata import nonempty_minc_data

    >>> files = [nonempty_minc_data(i) for i in range(3)]
    >>> average = Average(input_files=files, output_file='/tmp/tmp.mnc')
    >>> average.run() # doctest: +SKIP

    """

    input_spec = AverageInputSpec
    output_spec = AverageOutputSpec
    _cmd = "mincaverage"


class BlobInputSpec(CommandLineInputSpec):
    input_file = File(
        desc="input file to blob",
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-2,
    )

    output_file = File(
        desc="output file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_blob.mnc",
    )

    trace = traits.Bool(
        desc="compute the trace (approximate growth and shrinkage) -- FAST",
        argstr="-trace",
    )
    determinant = traits.Bool(
        desc="compute the determinant (exact growth and shrinkage) -- SLOW",
        argstr="-determinant",
    )
    translation = traits.Bool(
        desc="compute translation (structure displacement)", argstr="-translation"
    )
    magnitude = traits.Bool(
        desc="compute the magnitude of the displacement vector", argstr="-magnitude"
    )


class BlobOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)


class Blob(CommandLine):
    """Calculate blobs from minc deformation grids.

    Examples
    --------

    >>> from nipype.interfaces.minc import Blob
    >>> from nipype.interfaces.minc.testdata import minc2Dfile

    >>> blob = Blob(input_file=minc2Dfile, output_file='/tmp/tmp.mnc', trace=True)
    >>> blob.run() # doctest: +SKIP
    """

    input_spec = BlobInputSpec
    output_spec = BlobOutputSpec
    _cmd = "mincblob"


class CalcInputSpec(CommandLineInputSpec):
    _xor_input_files = ("input_files", "filelist")

    input_files = InputMultiPath(
        File(exists=True),
        desc="input file(s) for calculation",
        mandatory=True,
        sep=" ",
        argstr="%s",
        position=-2,
    )

    output_file = File(
        desc="output file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["input_files"],
        hash_files=False,
        name_template="%s_calc.mnc",
    )

    two = traits.Bool(desc="Create a MINC 2 output file.", argstr="-2")

    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )

    _xor_verbose = (
        "verbose",
        "quiet",
    )

    verbose = traits.Bool(
        desc="Print out log messages (default).", argstr="-verbose", xor=_xor_verbose
    )
    quiet = traits.Bool(
        desc="Do not print out log messages.", argstr="-quiet", xor=_xor_verbose
    )

    debug = traits.Bool(desc="Print out debugging messages.", argstr="-debug")

    filelist = File(
        desc="Specify the name of a file containing input file names.",
        argstr="-filelist %s",
        mandatory=True,
        xor=_xor_input_files,
    )

    _xor_copy_header = ("copy_header", "no_copy_header")

    copy_header = traits.Bool(
        desc="Copy all of the header from the first file.",
        argstr="-copy_header",
        xor=_xor_copy_header,
    )
    no_copy_header = traits.Bool(
        desc="Do not copy all of the header from the first file.",
        argstr="-nocopy_header",
        xor=_xor_copy_header,
    )

    _xor_format = (
        "format_filetype",
        "format_byte",
        "format_short",
        "format_int",
        "format_long",
        "format_float",
        "format_double",
        "format_signed",
        "format_unsigned",
    )

    format_filetype = traits.Bool(
        desc="Use data type of first file (default).",
        argstr="-filetype",
        xor=_xor_format,
    )
    format_byte = traits.Bool(
        desc="Write out byte data.", argstr="-byte", xor=_xor_format
    )
    format_short = traits.Bool(
        desc="Write out short integer data.", argstr="-short", xor=_xor_format
    )
    format_int = traits.Bool(
        desc="Write out 32-bit integer data.", argstr="-int", xor=_xor_format
    )
    format_long = traits.Bool(
        desc="Superseded by -int.", argstr="-long", xor=_xor_format
    )
    format_float = traits.Bool(
        desc="Write out single-precision floating-point data.",
        argstr="-float",
        xor=_xor_format,
    )
    format_double = traits.Bool(
        desc="Write out double-precision floating-point data.",
        argstr="-double",
        xor=_xor_format,
    )
    format_signed = traits.Bool(
        desc="Write signed integer data.", argstr="-signed", xor=_xor_format
    )
    format_unsigned = traits.Bool(
        desc="Write unsigned integer data (default).",
        argstr="-unsigned",
        xor=_xor_format,
    )

    voxel_range = traits.Tuple(
        traits.Int,
        traits.Int,
        argstr="-range %d %d",
        desc="Valid range for output data.",
    )

    max_buffer_size_in_kb = traits.Range(
        low=0,
        desc="Specify the maximum size of the internal buffers (in kbytes).",
        argstr="-max_buffer_size_in_kb %d",
    )

    _xor_check_dimensions = (
        "check_dimensions",
        "no_check_dimensions",
    )

    check_dimensions = traits.Bool(
        desc="Check that files have matching dimensions (default).",
        argstr="-check_dimensions",
        xor=_xor_check_dimensions,
    )
    no_check_dimensions = traits.Bool(
        desc="Do not check that files have matching dimensions.",
        argstr="-nocheck_dimensions",
        xor=_xor_check_dimensions,
    )

    # FIXME Is it sensible to use ignore_nan and propagate_nan at the same
    # time? Document this.
    ignore_nan = traits.Bool(
        desc="Ignore invalid data (NaN) for accumulations.", argstr="-ignore_nan"
    )
    propagate_nan = traits.Bool(
        desc="Invalid data in any file at a voxel produces a NaN (default).",
        argstr="-propagate_nan",
    )

    # FIXME Double-check that these are mutually exclusive?
    _xor_nan_zero_illegal = ("output_nan", "output_zero", "output_illegal_value")

    output_nan = traits.Bool(
        desc="Output NaN when an illegal operation is done (default).",
        argstr="-nan",
        xor=_xor_nan_zero_illegal,
    )
    output_zero = traits.Bool(
        desc="Output zero when an illegal operation is done.",
        argstr="-zero",
        xor=_xor_nan_zero_illegal,
    )
    output_illegal = traits.Bool(
        desc="Value to write out when an illegal operation is done. Default value: 1.79769e+308",
        argstr="-illegal_value",
        xor=_xor_nan_zero_illegal,
    )

    _xor_expression = ("expression", "expfile")

    expression = traits.Str(
        desc="Expression to use in calculations.",
        argstr="-expression '%s'",
        xor=_xor_expression,
        mandatory=True,
    )
    expfile = File(
        desc="Name of file containing expression.",
        argstr="-expfile %s",
        xor=_xor_expression,
        mandatory=True,
    )

    # FIXME test this one, the argstr will probably need tweaking, see
    # _format_arg.
    outfiles = traits.List(
        traits.Tuple(
            traits.Str,
            File,
            argstr="-outfile %s %s",
            desc=(
                "List of (symbol, file) tuples indicating that output should be written"
                "to the specified file, taking values from the symbol which should be"
                "created in the expression (see the EXAMPLES section). If this option"
                "is given, then all non-option arguments are taken as input files."
                "This option can be used multiple times for multiple output files."
            ),
        )
    )

    eval_width = traits.Int(
        desc="Number of voxels to evaluate simultaneously.", argstr="-eval_width %s"
    )


class CalcOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)


class Calc(CommandLine):
    """Compute an expression using MINC files as input.

    Examples
    --------

    >>> from nipype.interfaces.minc import Calc
    >>> from nipype.interfaces.minc.testdata import nonempty_minc_data

    >>> file0 = nonempty_minc_data(0)
    >>> file1 = nonempty_minc_data(1)
    >>> calc = Calc(input_files=[file0, file1], output_file='/tmp/calc.mnc', expression='A[0] + A[1]') # add files together
    >>> calc.run() # doctest: +SKIP
    """

    input_spec = CalcInputSpec
    output_spec = CalcOutputSpec
    _cmd = "minccalc"


# FIXME mincbbox produces output like
#
#   -5.000000 -5.000000 -5.000000    4.800000 2.800000 8.800000
#
# so perhaps this would be better returned as a pair of Python
# lists instead of sending to an output file?


class BBoxInputSpec(StdOutCommandLineInputSpec):
    input_file = File(
        desc="input file", exists=True, mandatory=True, argstr="%s", position=-2,
    )

    output_file = File(
        desc="output file containing bounding box corners",
        position=-1,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_bbox.txt",
        keep_extension=False,
    )

    threshold = traits.Int(
        0,
        desc="VIO_Real value threshold for bounding box. Default value: 0.",
        argstr="-threshold",
    )

    _xor_one_two = ("one_line", "two_lines")

    one_line = traits.Bool(
        desc="Output on one line (default): start_x y z width_x y z",
        argstr="-one_line",
        xor=_xor_one_two,
    )
    two_lines = traits.Bool(
        desc="""Write output with two rows (start and width).""",
        argstr="-two_lines",
        xor=_xor_one_two,
    )

    format_mincresample = traits.Bool(
        desc="Output format for mincresample: (-step x y z -start x y z -nelements x y z",
        argstr="-mincresample",
    )
    format_mincreshape = traits.Bool(
        desc="Output format for mincreshape: (-start x,y,z -count dx,dy,dz",
        argstr="-mincreshape",
    )
    format_minccrop = traits.Bool(
        desc="Output format for minccrop: (-xlim x1 x2 -ylim y1 y2 -zlim z1 z2",
        argstr="-minccrop",
    )

    # FIXME Not implemented, will clash with our parsing of the output?
    # Command-specific options:
    # Options for logging progress. Default = -verbose.
    #  -verbose:      Write messages indicating progress
    #  -quiet:        Do not write log messages
    #  -debug:        Print out debug info.


class BBoxOutputSpec(TraitedSpec):
    output_file = File(desc="output file containing bounding box corners", exists=True)


class BBox(StdOutCommandLine):
    """Determine a bounding box of image.

    Examples
    --------
    >>> from nipype.interfaces.minc import BBox
    >>> from nipype.interfaces.minc.testdata import nonempty_minc_data

    >>> file0 = nonempty_minc_data(0)
    >>> bbox = BBox(input_file=file0)
    >>> bbox.run() # doctest: +SKIP

    """

    input_spec = BBoxInputSpec
    output_spec = BBoxOutputSpec
    _cmd = "mincbbox"


class BeastInputSpec(CommandLineInputSpec):
    """

    TODO:

    Command-specific options:
     -verbose:          Enable verbose output.
     -positive:         Specify mask of positive segmentation (inside mask) instead of the default mask.
     -output_selection: Specify file to output selected files.
     -count:            Specify file to output the patch count.
     -mask:             Specify a segmentation mask instead of the the default mask.
     -no_mask:          Do not apply a segmentation mask. Perform the segmentation over the entire image.
     -no_positive:      Do not apply a positive mask.
    Generic options for all commands:
     -help:             Print summary of command-line options and abort
     -version:          Print version number of program and exit
    Copyright (C) 2011	Simon Fristed Eskildsen, Vladimir Fonov,
                Pierrick Coupe, Jose V. Manjon

    This program comes with ABSOLUTELY NO WARRANTY; for details type 'cat COPYING'.
    This is free software, and you are welcome to redistribute it under certain
    conditions; type 'cat COPYING' for details.

    Usage: mincbeast [options] <library dir> <input> <output>
           mincbeast -help

    Get this example to work?

    https://github.com/BIC-MNI/BEaST/blob/master/README.library


        2.3 Source the minc-toolkit (if installed):
        $ source /opt/minc/minc-toolkit-config.sh

        2.4 Generate library by running:
        $ beast_prepareADNIlib -flip <ADNI download directory> <BEaST library directory>
        Example:
        $ sudo beast_prepareADNIlib -flip Downloads/ADNI /opt/minc/share/beast-library-1.1

        3. Test the setup
        3.1 Normalize your data
        $ beast_normalize -modeldir /opt/minc/share/icbm152_model_09c input.mnc normal.mnc normal.xfm
        3.2 Run BEaST
        $ mincbeast /opt/minc/share/beast-library-1.1 normal.mnc brainmask.mnc -conf /opt/minc/share/beast-library-1.1/default.2mm.conf -same_res
    """

    probability_map = traits.Bool(
        desc="Output the probability map instead of crisp mask.", argstr="-probability"
    )
    flip_images = traits.Bool(
        desc="Flip images around the mid-sagittal plane to increase patch count.",
        argstr="-flip",
    )
    load_moments = traits.Bool(
        desc=(
            "Do not calculate moments instead use precalculated"
            "library moments. (for optimization purposes)"
        ),
        argstr="-load_moments",
    )
    fill_holes = traits.Bool(desc="Fill holes in the binary output.", argstr="-fill")
    median_filter = traits.Bool(
        desc="Apply a median filter on the probability map.", argstr="-median"
    )
    nlm_filter = traits.Bool(
        desc="Apply an NLM filter on the probability map (experimental).",
        argstr="-nlm_filter",
    )

    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )

    configuration_file = File(
        desc="Specify configuration file.", argstr="-configuration %s"
    )

    voxel_size = traits.Int(
        4,
        usedefault=True,
        desc=(
            "Specify voxel size for calculations (4, 2, or 1)."
            "Default value: 4. Assumes no multiscale. Use configuration"
            "file for multiscale."
        ),
        argstr="-voxel_size %s",
    )

    abspath = traits.Bool(
        desc="File paths in the library are absolute (default is relative to library root).",
        argstr="-abspath",
        usedefault=True,
        default_value=True,
    )

    patch_size = traits.Int(
        1,
        usedefault=True,
        desc="Specify patch size for single scale approach. Default value: 1.",
        argstr="-patch_size %s",
    )

    search_area = traits.Int(
        2,
        usedefault=True,
        desc="Specify size of search area for single scale approach. Default value: 2.",
        argstr="-search_area %s",
    )

    confidence_level_alpha = traits.Float(
        0.5,
        usedefault=True,
        desc="Specify confidence level Alpha. Default value: 0.5",
        argstr="-alpha %s",
    )
    smoothness_factor_beta = traits.Float(
        0.5,
        usedefault=True,
        desc="Specify smoothness factor Beta. Default value: 0.25",
        argstr="-beta %s",
    )
    threshold_patch_selection = traits.Float(
        0.95,
        usedefault=True,
        desc="Specify threshold for patch selection. Default value: 0.95",
        argstr="-threshold %s",
    )
    number_selected_images = traits.Int(
        20,
        usedefault=True,
        desc="Specify number of selected images. Default value: 20",
        argstr="-selection_num %s",
    )

    same_resolution = traits.Bool(
        desc="Output final mask with the same resolution as input file.",
        argstr="-same_resolution",
    )

    library_dir = Directory(
        desc="library directory", position=-3, argstr="%s", mandatory=True
    )
    input_file = File(desc="input file", position=-2, argstr="%s", mandatory=True)
    output_file = File(
        desc="output file",
        position=-1,
        argstr="%s",
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_beast_mask.mnc",
    )


class BeastOutputSpec(TraitedSpec):
    output_file = File(desc="output mask file", exists=True)


class Beast(CommandLine):
    """Extract brain image using BEaST (Brain Extraction using
    non-local Segmentation Technique).

    Examples
    --------

    >>> from nipype.interfaces.minc import Beast
    >>> from nipype.interfaces.minc.testdata import nonempty_minc_data

    >>> file0 = nonempty_minc_data(0)
    >>> beast = Beast(input_file=file0)
    >>> beast .run() # doctest: +SKIP
    """

    input_spec = BeastInputSpec
    output_spec = BeastOutputSpec
    _cmd = "mincbeast"


class PikInputSpec(CommandLineInputSpec):
    input_file = File(
        desc="input file", exists=True, mandatory=True, argstr="%s", position=-2,
    )

    _xor_image_type = ("jpg", "png")

    jpg = traits.Bool(desc="Output a jpg file.", xor=_xor_image_type)
    png = traits.Bool(desc="Output a png file (default).", xor=_xor_image_type)

    output_file = File(
        desc="output file",
        argstr="%s",
        genfile=True,
        position=-1,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s.png",
        keep_extension=False,
    )

    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )

    # FIXME not implemented: --verbose
    #                        --fake
    #                        --lookup    ==> arguments to pass to minclookup

    scale = traits.Int(
        2,
        usedefault=True,
        desc=(
            "Scaling factor for resulting image. By default images are"
            "output at twice their original resolution."
        ),
        argstr="--scale %s",
    )

    width = traits.Int(
        desc="Autoscale the resulting image to have a fixed image width (in pixels).",
        argstr="--width %s",
    )

    depth = traits.Enum(
        8,
        16,
        desc="Bitdepth for resulting image 8 or 16 (MSB machines only!)",
        argstr="--depth %s",
    )

    _xor_title = ("title_string", "title_with_filename")

    title = traits.Either(
        traits.Bool(desc="Use input filename as title in resulting image."),
        traits.Str(desc="Add a title to the resulting image."),
        argstr="%s",
    )  # see _format_arg for actual arg string

    title_size = traits.Int(
        desc="Font point size for the title.",
        argstr="--title_size %s",
        requires=["title"],
    )

    annotated_bar = traits.Bool(
        desc="create an annotated bar to match the image (use height of the output image)",
        argstr="--anot_bar",
    )

    # FIXME tuple of floats? Not voxel values? Man page doesn't specify.
    minc_range = traits.Tuple(
        traits.Float,
        traits.Float,
        desc="Valid range of values for MINC file.",
        argstr="--range %s %s",
    )

    _xor_image_range = ("image_range", "auto_range")

    image_range = traits.Tuple(
        traits.Float,
        traits.Float,
        desc="Range of image values to use for pixel intensity.",
        argstr="--image_range %s %s",
        xor=_xor_image_range,
    )

    auto_range = traits.Bool(
        desc="Automatically determine image range using a 5 and 95% PcT. (histogram)",
        argstr="--auto_range",
        xor=_xor_image_range,
    )

    start = traits.Int(
        desc="Slice number to get. (note this is in voxel co-ordinates).",
        argstr="--slice %s",
    )  # FIXME Int is correct?

    _xor_slice = ("slice_z", "slice_y", "slice_x")

    slice_z = traits.Bool(
        desc="Get an axial/transverse (z) slice.", argstr="-z", xor=_xor_slice
    )
    slice_y = traits.Bool(desc="Get a coronal (y) slice.", argstr="-y", xor=_xor_slice)
    slice_x = traits.Bool(
        desc="Get a sagittal (x) slice.", argstr="-x", xor=_xor_slice
    )  # FIXME typo in man page? sagital?

    triplanar = traits.Bool(
        desc="Create a triplanar view of the input file.", argstr="--triplanar"
    )
    tile_size = traits.Int(
        desc="Pixel size for each image in a triplanar.", argstr="--tilesize %s"
    )

    _xor_sagittal_offset = ("sagittal_offset", "sagittal_offset_perc")

    sagittal_offset = traits.Int(
        desc="Offset the sagittal slice from the centre.", argstr="--sagittal_offset %s"
    )
    sagittal_offset_perc = traits.Range(
        low=0,
        high=100,
        desc="Offset the sagittal slice by a percentage from the centre.",
        argstr="--sagittal_offset_perc %d",
    )

    _xor_vertical_horizontal = ("vertical_triplanar_view", "horizontal_triplanar_view")

    vertical_triplanar_view = traits.Bool(
        desc="Create a vertical triplanar view (Default).",
        argstr="--vertical",
        xor=_xor_vertical_horizontal,
    )
    horizontal_triplanar_view = traits.Bool(
        desc="Create a horizontal triplanar view.",
        argstr="--horizontal",
        xor=_xor_vertical_horizontal,
    )

    lookup = traits.Str(desc="Arguments to pass to minclookup", argstr="--lookup %s")


class PikOutputSpec(TraitedSpec):
    output_file = File(desc="output image", exists=True)


class Pik(CommandLine):
    """Generate images from minc files.

    Mincpik uses Imagemagick to generate images
    from Minc files.

    Examples
    --------

    >>> from nipype.interfaces.minc import Pik
    >>> from nipype.interfaces.minc.testdata import nonempty_minc_data

    >>> file0 = nonempty_minc_data(0)
    >>> pik = Pik(input_file=file0, title='foo')
    >>> pik .run() # doctest: +SKIP

    """

    input_spec = PikInputSpec
    output_spec = PikOutputSpec
    _cmd = "mincpik"

    def _format_arg(self, name, spec, value):
        if name == "title":
            if isinstance(value, bool) and value:
                return "--title"
            elif isinstance(value, str):
                return "--title --title_text %s" % (value,)
            else:
                raise ValueError('Unknown value for "title" argument: ' + str(value))
        return super(Pik, self)._format_arg(name, spec, value)


class BlurInputSpec(CommandLineInputSpec):
    input_file = File(
        desc="input file", exists=True, mandatory=True, argstr="%s", position=-2,
    )

    output_file_base = File(desc="output file base", argstr="%s", position=-1)

    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )

    _xor_kernel = ("gaussian", "rect")

    gaussian = traits.Bool(
        desc="Use a gaussian smoothing kernel (default).",
        argstr="-gaussian",
        xor=_xor_kernel,
    )
    rect = traits.Bool(
        desc="Use a rect (box) smoothing kernel.", argstr="-rect", xor=_xor_kernel
    )

    gradient = traits.Bool(
        desc="Create the gradient magnitude volume as well.", argstr="-gradient"
    )
    partial = traits.Bool(
        desc="Create the partial derivative and gradient magnitude volumes as well.",
        argstr="-partial",
    )

    no_apodize = traits.Bool(
        desc="Do not apodize the data before blurring.", argstr="-no_apodize"
    )

    _xor_main_options = ("fwhm", "fwhm3d", "standard_dev")

    fwhm = traits.Float(
        0,
        desc="Full-width-half-maximum of gaussian kernel. Default value: 0.",
        argstr="-fwhm %s",
        xor=_xor_main_options,
        mandatory=True,
    )

    standard_dev = traits.Float(
        0,
        desc="Standard deviation of gaussian kernel. Default value: 0.",
        argstr="-standarddev %s",
        xor=_xor_main_options,
        mandatory=True,
    )

    fwhm3d = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr="-3dfwhm %s %s %s",
        desc=(
            "Full-width-half-maximum of gaussian kernel."
            "Default value: -1.79769e+308 -1.79769e+308 -1.79769e+308."
        ),
        xor=_xor_main_options,
        mandatory=True,
    )

    dimensions = traits.Enum(
        3,
        1,
        2,
        desc="Number of dimensions to blur (either 1,2 or 3). Default value: 3.",
        argstr="-dimensions %s",
    )


class BlurOutputSpec(TraitedSpec):
    output_file = File(desc="Blurred output file.", exists=True)

    gradient_dxyz = File(desc="Gradient dxyz.")
    partial_dx = File(desc="Partial gradient dx.")
    partial_dy = File(desc="Partial gradient dy.")
    partial_dz = File(desc="Partial gradient dz.")
    partial_dxyz = File(desc="Partial gradient dxyz.")


class Blur(StdOutCommandLine):
    """
    Convolve an input volume with a Gaussian blurring kernel of
    user-defined width.  Optionally, the first partial derivatives
    and the gradient magnitude volume can be calculated.

    Examples
    --------

    >>> from nipype.interfaces.minc import Blur
    >>> from nipype.interfaces.minc.testdata import minc3Dfile

    (1) Blur  an  input  volume with a 6mm fwhm isotropic Gaussian
    blurring kernel:

    >>> blur = Blur(input_file=minc3Dfile, fwhm=6, output_file_base='/tmp/out_6')
    >>> blur.run() # doctest: +SKIP

    mincblur will create /tmp/out_6_blur.mnc.

    (2) Calculate the blurred and gradient magnitude data:

    >>> blur = Blur(input_file=minc3Dfile, fwhm=6, gradient=True, output_file_base='/tmp/out_6')
    >>> blur.run() # doctest: +SKIP

    will create /tmp/out_6_blur.mnc and /tmp/out_6_dxyz.mnc.

    (3) Calculate the blurred data, the partial derivative volumes
    and  the gradient magnitude for the same data:

    >>> blur = Blur(input_file=minc3Dfile, fwhm=6, partial=True, output_file_base='/tmp/out_6')
    >>> blur.run() # doctest: +SKIP

    will create /tmp/out_6_blur.mnc, /tmp/out_6_dx.mnc,
    /tmp/out_6_dy.mnc, /tmp/out_6_dz.mnc and /tmp/out_6_dxyz.mnc.
    """

    input_spec = BlurInputSpec
    output_spec = BlurOutputSpec
    _cmd = "mincblur"

    def _gen_output_base(self):
        output_file_base = self.inputs.output_file_base

        if isdefined(output_file_base):
            return output_file_base
        else:
            base_file_name = os.path.split(self.inputs.input_file)[1]  # e.g. 'foo.mnc'
            base_file_name_no_ext = os.path.splitext(base_file_name)[0]  # e.g. 'foo'
            output_base = os.path.join(
                os.getcwd(), base_file_name_no_ext + "_bluroutput"
            )  # e.g. '/tmp/blah/foo_bluroutput'
            # return os.path.splitext(self.inputs.input_file)[0] +
            # '_bluroutput'
            return output_base

    def _list_outputs(self):
        outputs = self.output_spec().get()

        output_file_base = self._gen_output_base()

        outputs["output_file"] = output_file_base + "_blur.mnc"

        if isdefined(self.inputs.gradient):
            outputs["gradient_dxyz"] = output_file_base + "_dxyz.mnc"

        if isdefined(self.inputs.partial):
            outputs["partial_dx"] = output_file_base + "_dx.mnc"
            outputs["partial_dy"] = output_file_base + "_dy.mnc"
            outputs["partial_dz"] = output_file_base + "_dz.mnc"
            outputs["partial_dxyz"] = output_file_base + "_dxyz.mnc"

        return outputs

    @property
    def cmdline(self):
        output_file_base = self.inputs.output_file_base
        orig_cmdline = super(Blur, self).cmdline

        if isdefined(output_file_base):
            return orig_cmdline
        else:
            # FIXME this seems like a bit of a hack. Can we force output_file
            # to show up in cmdline by default, even if it isn't specified in
            # the instantiation of Pik?
            return "%s %s" % (orig_cmdline, self._gen_output_base())


class MathInputSpec(CommandLineInputSpec):
    _xor_input_files = ("input_files", "filelist")

    input_files = InputMultiPath(
        File(exists=True),
        desc="input file(s) for calculation",
        mandatory=True,
        sep=" ",
        argstr="%s",
        position=-2,
        xor=_xor_input_files,
    )

    output_file = File(
        desc="output file",
        argstr="%s",
        genfile=True,
        position=-1,
        name_source=["input_files"],
        hash_files=False,
        name_template="%s_mincmath.mnc",
    )

    filelist = File(
        desc="Specify the name of a file containing input file names.",
        argstr="-filelist %s",
        exists=True,
        mandatory=True,
        xor=_xor_input_files,
    )

    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )

    two = traits.Bool(desc="Create a MINC 2 output file.", argstr="-2")

    _xor_copy_header = ("copy_header", "no_copy_header")

    copy_header = traits.Bool(
        desc="Copy all of the header from the first file (default for one file).",
        argstr="-copy_header",
        xor=_xor_copy_header,
    )
    no_copy_header = traits.Bool(
        desc="Do not copy all of the header from the first file (default for many files)).",
        argstr="-nocopy_header",
        xor=_xor_copy_header,
    )

    _xor_format = (
        "format_filetype",
        "format_byte",
        "format_short",
        "format_int",
        "format_long",
        "format_float",
        "format_double",
        "format_signed",
        "format_unsigned",
    )

    format_filetype = traits.Bool(
        desc="Use data type of first file (default).",
        argstr="-filetype",
        xor=_xor_format,
    )
    format_byte = traits.Bool(
        desc="Write out byte data.", argstr="-byte", xor=_xor_format
    )
    format_short = traits.Bool(
        desc="Write out short integer data.", argstr="-short", xor=_xor_format
    )
    format_int = traits.Bool(
        desc="Write out 32-bit integer data.", argstr="-int", xor=_xor_format
    )
    format_long = traits.Bool(
        desc="Superseded by -int.", argstr="-long", xor=_xor_format
    )
    format_float = traits.Bool(
        desc="Write out single-precision floating-point data.",
        argstr="-float",
        xor=_xor_format,
    )
    format_double = traits.Bool(
        desc="Write out double-precision floating-point data.",
        argstr="-double",
        xor=_xor_format,
    )
    format_signed = traits.Bool(
        desc="Write signed integer data.", argstr="-signed", xor=_xor_format
    )
    format_unsigned = traits.Bool(
        desc="Write unsigned integer data (default).",
        argstr="-unsigned",
        xor=_xor_format,
    )

    voxel_range = traits.Tuple(
        traits.Int,
        traits.Int,
        argstr="-range %d %d",
        desc="Valid range for output data.",
    )

    max_buffer_size_in_kb = traits.Range(
        low=0,
        desc="Specify the maximum size of the internal buffers (in kbytes).",
        value=4096,
        usedefault=True,
        argstr="-max_buffer_size_in_kb %d",
    )

    _xor_check_dimensions = (
        "check_dimensions",
        "no_check_dimensions",
    )

    check_dimensions = traits.Bool(
        desc="Check that dimension info matches across files (default).",
        argstr="-check_dimensions",
        xor=_xor_check_dimensions,
    )
    no_check_dimensions = traits.Bool(
        desc="Do not check dimension info.",
        argstr="-nocheck_dimensions",
        xor=_xor_check_dimensions,
    )

    dimension = traits.Str(
        desc="Specify a dimension along which we wish to perform a calculation.",
        argstr="-dimension %s",
    )

    # FIXME Is it sensible to use ignore_nan and propagate_nan at the same
    # time? Document this.
    ignore_nan = traits.Bool(
        desc="Ignore invalid data (NaN) for accumulations.", argstr="-ignore_nan"
    )
    propagate_nan = traits.Bool(
        desc="Invalid data in any file at a voxel produces a NaN (default).",
        argstr="-propagate_nan",
    )

    # FIXME Double-check that these are mutually exclusive?
    _xor_nan_zero_illegal = ("output_nan", "output_zero", "output_illegal_value")

    output_nan = traits.Bool(
        desc="Output NaN when an illegal operation is done (default).",
        argstr="-nan",
        xor=_xor_nan_zero_illegal,
    )
    output_zero = traits.Bool(
        desc="Output zero when an illegal operation is done.",
        argstr="-zero",
        xor=_xor_nan_zero_illegal,
    )
    output_illegal = traits.Bool(
        desc=(
            "Value to write out when an illegal operation"
            "is done. Default value: 1.79769e+308"
        ),
        argstr="-illegal_value",
        xor=_xor_nan_zero_illegal,
    )

    # FIXME A whole bunch of the parameters will be mutually exclusive, e.g. surely can't do sqrt and abs at the same time?
    # Or does mincmath do one and then the next?

    ##########################################################################
    # Traits that expect a bool (compare two volumes) or constant (manipulate one volume) #
    ##########################################################################

    bool_or_const_traits = [
        "test_gt",
        "test_lt",
        "test_eq",
        "test_ne",
        "test_ge",
        "test_le",
        "calc_add",
        "calc_sub",
        "calc_mul",
        "calc_div",
    ]

    test_gt = traits.Either(
        traits.Bool(),
        traits.Float(),
        desc="Test for vol1 > vol2 or vol1 > constant.",
        argstr="-gt",
    )
    test_lt = traits.Either(
        traits.Bool(),
        traits.Float(),
        desc="Test for vol1 < vol2 or vol1 < constant.",
        argstr="-lt",
    )
    test_eq = traits.Either(
        traits.Bool(),
        traits.Float(),
        desc="Test for integer vol1 == vol2 or vol1 == constant.",
        argstr="-eq",
    )
    test_ne = traits.Either(
        traits.Bool(),
        traits.Float(),
        desc="Test for integer vol1 != vol2 or vol1 != const.",
        argstr="-ne",
    )
    test_ge = traits.Either(
        traits.Bool(),
        traits.Float(),
        desc="Test for vol1 >= vol2 or vol1 >= const.",
        argstr="-ge",
    )
    test_le = traits.Either(
        traits.Bool(),
        traits.Float(),
        desc="Test for vol1 <= vol2 or vol1 <= const.",
        argstr="-le",
    )

    calc_add = traits.Either(
        traits.Bool(),
        traits.Float(),
        desc="Add N volumes or volume + constant.",
        argstr="-add",
    )
    calc_sub = traits.Either(
        traits.Bool(),
        traits.Float(),
        desc="Subtract 2 volumes or volume - constant.",
        argstr="-sub",
    )
    calc_mul = traits.Either(
        traits.Bool(),
        traits.Float(),
        desc="Multiply N volumes or volume * constant.",
        argstr="-mult",
    )
    calc_div = traits.Either(
        traits.Bool(),
        traits.Float(),
        desc="Divide 2 volumes or volume / constant.",
        argstr="-div",
    )

    ######################################
    # Traits that expect a single volume #
    ######################################

    single_volume_traits = [
        "invert",
        "calc_not",
        "sqrt",
        "square",
        "abs",
        "exp",
        "log",
        "scale",
        "clamp",
        "segment",
        "nsegment",
        "isnan",
        "isnan",
    ]  # FIXME enforce this in _parse_inputs and check for other members

    invert = traits.Either(
        traits.Float(), desc="Calculate 1/c.", argstr="-invert -const %s"
    )

    calc_not = traits.Bool(desc="Calculate !vol1.", argstr="-not")

    sqrt = traits.Bool(desc="Take square root of a volume.", argstr="-sqrt")
    square = traits.Bool(desc="Take square of a volume.", argstr="-square")
    abs = traits.Bool(desc="Take absolute value of a volume.", argstr="-abs")

    exp = traits.Tuple(
        traits.Float,
        traits.Float,
        argstr="-exp -const2 %s %s",
        desc="Calculate c2*exp(c1*x). Both constants must be specified.",
    )

    log = traits.Tuple(
        traits.Float,
        traits.Float,
        argstr="-log -const2 %s %s",
        desc="Calculate log(x/c2)/c1. The constants c1 and c2 default to 1.",
    )

    scale = traits.Tuple(
        traits.Float,
        traits.Float,
        argstr="-scale -const2 %s %s",
        desc="Scale a volume: volume * c1 + c2.",
    )

    clamp = traits.Tuple(
        traits.Float,
        traits.Float,
        argstr="-clamp -const2 %s %s",
        desc="Clamp a volume to lie between two values.",
    )

    segment = traits.Tuple(
        traits.Float,
        traits.Float,
        argstr="-segment -const2 %s %s",
        desc="Segment a volume using range of -const2: within range = 1, outside range = 0.",
    )

    nsegment = traits.Tuple(
        traits.Float,
        traits.Float,
        argstr="-nsegment -const2 %s %s",
        desc="Opposite of -segment: within range = 0, outside range = 1.",
    )

    isnan = traits.Bool(desc="Test for NaN values in vol1.", argstr="-isnan")

    nisnan = traits.Bool(desc="Negation of -isnan.", argstr="-nisnan")

    ############################################
    # Traits that expect precisely two volumes #
    ############################################

    two_volume_traits = ["percentdiff"]

    percentdiff = traits.Float(
        desc="Percent difference between 2 volumes, thresholded (const def=0.0).",
        argstr="-percentdiff",
    )

    #####################################
    # Traits that expect N >= 1 volumes #
    #####################################

    n_volume_traits = ["count_valid", "maximum", "minimum", "calc_add", "calc_or"]

    count_valid = traits.Bool(
        desc="Count the number of valid values in N volumes.", argstr="-count_valid"
    )

    maximum = traits.Bool(desc="Find maximum of N volumes.", argstr="-maximum")
    minimum = traits.Bool(desc="Find minimum of N volumes.", argstr="-minimum")

    calc_and = traits.Bool(desc="Calculate vol1 && vol2 (&& ...).", argstr="-and")
    calc_or = traits.Bool(desc="Calculate vol1 || vol2 (|| ...).", argstr="-or")


class MathOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)


class Math(StdOutCommandLine):
    """
    Various mathematical operations supplied by mincmath.

    Examples
    --------

    >>> from nipype.interfaces.minc import Math
    >>> from nipype.interfaces.minc.testdata import minc2Dfile

    Scale: volume*3.0 + 2:

    >>> scale = Math(input_files=[minc2Dfile], scale=(3.0, 2))
    >>> scale.run() # doctest: +SKIP

    Test if >= 1.5:

    >>> gt = Math(input_files=[minc2Dfile], test_gt=1.5)
    >>> gt.run() # doctest: +SKIP
    """

    input_spec = MathInputSpec
    output_spec = MathOutputSpec
    _cmd = "mincmath"

    def _format_arg(self, name, spec, value):
        assert value is not None

        if name in self.input_spec.bool_or_const_traits:
            # t is unused, what was I trying to do with it?
            # t = self.inputs.__getattribute__(name)

            if isinstance(value, bool) and value:
                return spec.argstr
            elif isinstance(value, bool) and not value:
                raise ValueError("Does not make sense to specify %s=False" % (name,))
            elif isinstance(value, float):
                return "%s -const %s" % (spec.argstr, value,)
            else:
                raise ValueError("Invalid %s argument: %s" % (name, value,))

        return super(Math, self)._format_arg(name, spec, value)

    def _parse_inputs(self):
        """A number of the command line options expect precisely one or two files.
        """

        nr_input_files = len(self.inputs.input_files)

        for n in self.input_spec.bool_or_const_traits:
            t = self.inputs.__getattribute__(n)

            if isdefined(t):
                if isinstance(t, bool):
                    if nr_input_files != 2:
                        raise ValueError(
                            "Due to the %s option we expected 2 files but input_files is of length %d"
                            % (n, nr_input_files,)
                        )
                elif isinstance(t, float):
                    if nr_input_files != 1:
                        raise ValueError(
                            "Due to the %s option we expected 1 file but input_files is of length %d"
                            % (n, nr_input_files,)
                        )
                else:
                    raise ValueError(
                        "Argument should be a bool or const, but got: %s" % t
                    )

        for n in self.input_spec.single_volume_traits:
            t = self.inputs.__getattribute__(n)

            if isdefined(t):
                if nr_input_files != 1:
                    raise ValueError(
                        "Due to the %s option we expected 1 file but input_files is of length %d"
                        % (n, nr_input_files,)
                    )

        for n in self.input_spec.two_volume_traits:
            t = self.inputs.__getattribute__(n)

            if isdefined(t):
                if nr_input_files != 2:
                    raise ValueError(
                        "Due to the %s option we expected 2 files but input_files is of length %d"
                        % (n, nr_input_files,)
                    )

        for n in self.input_spec.n_volume_traits:
            t = self.inputs.__getattribute__(n)

            if isdefined(t):
                if not nr_input_files >= 1:
                    raise ValueError(
                        "Due to the %s option we expected at least one file but input_files is of length %d"
                        % (n, nr_input_files,)
                    )

        return super(Math, self)._parse_inputs()


class ResampleInputSpec(CommandLineInputSpec):
    """
    not implemented:
     -size:                    synonym for -nelements)
     -xsize:                   synonym for -xnelements
     -ysize:                   synonym for -ynelements
     -zsize:                   synonym for -ynelements

    """

    input_file = File(
        desc="input file for resampling",
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-2,
    )

    output_file = File(
        desc="output file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_resample.mnc",
    )

    # This is a dummy input.
    input_grid_files = InputMultiPath(File, desc="input grid file(s)",)

    two = traits.Bool(desc="Create a MINC 2 output file.", argstr="-2")

    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )

    _xor_interpolation = (
        "trilinear_interpolation",
        "tricubic_interpolation",
        "nearest_neighbour_interpolation",
        "sinc_interpolation",
    )

    trilinear_interpolation = traits.Bool(
        desc="Do trilinear interpolation.", argstr="-trilinear", xor=_xor_interpolation
    )
    tricubic_interpolation = traits.Bool(
        desc="Do tricubic interpolation.", argstr="-tricubic", xor=_xor_interpolation
    )

    nearest_neighbour_interpolation = traits.Bool(
        desc="Do nearest neighbour interpolation.",
        argstr="-nearest_neighbour",
        xor=_xor_interpolation,
    )

    sinc_interpolation = traits.Bool(
        desc="Do windowed sinc interpolation.", argstr="-sinc", xor=_xor_interpolation
    )

    half_width_sinc_window = traits.Enum(
        5,
        1,
        2,
        3,
        4,
        6,
        7,
        8,
        9,
        10,
        desc="Set half-width of sinc window (1-10). Default value: 5.",
        argstr="-width %s",
        requires=["sinc_interpolation"],
    )

    _xor_sinc_window_type = ("sinc_window_hanning", "sinc_window_hamming")

    sinc_window_hanning = traits.Bool(
        desc="Set sinc window type to Hanning.",
        argstr="-hanning",
        xor=_xor_sinc_window_type,
        requires=["sinc_interpolation"],
    )

    sinc_window_hamming = traits.Bool(
        desc="Set sinc window type to Hamming.",
        argstr="-hamming",
        xor=_xor_sinc_window_type,
        requires=["sinc_interpolation"],
    )

    transformation = File(
        desc="File giving world transformation. (Default = identity).",
        exists=True,
        argstr="-transformation %s",
    )

    invert_transformation = traits.Bool(
        desc="Invert the transformation before using it.",
        argstr="-invert_transformation",
    )

    _xor_input_sampling = ("vio_transform", "no_input_sampling")

    vio_transform = traits.Bool(
        desc="VIO_Transform the input sampling with the transform (default).",
        argstr="-tfm_input_sampling",
        xor=_xor_input_sampling,
    )

    no_input_sampling = traits.Bool(
        desc="Use the input sampling without transforming (old behaviour).",
        argstr="-use_input_sampling",
        xor=_xor_input_sampling,
    )

    like = File(
        desc="Specifies a model file for the resampling.",
        argstr="-like %s",
        exists=True,
    )

    _xor_format = (
        "format_byte",
        "format_short",
        "format_int",
        "format_long",
        "format_float",
        "format_double",
        "format_signed",
        "format_unsigned",
    )

    format_byte = traits.Bool(
        desc="Write out byte data.", argstr="-byte", xor=_xor_format
    )
    format_short = traits.Bool(
        desc="Write out short integer data.", argstr="-short", xor=_xor_format
    )
    format_int = traits.Bool(
        desc="Write out 32-bit integer data.", argstr="-int", xor=_xor_format
    )
    format_long = traits.Bool(
        desc="Superseded by -int.", argstr="-long", xor=_xor_format
    )
    format_float = traits.Bool(
        desc="Write out single-precision floating-point data.",
        argstr="-float",
        xor=_xor_format,
    )
    format_double = traits.Bool(
        desc="Write out double-precision floating-point data.",
        argstr="-double",
        xor=_xor_format,
    )
    format_signed = traits.Bool(
        desc="Write signed integer data.", argstr="-signed", xor=_xor_format
    )
    format_unsigned = traits.Bool(
        desc="Write unsigned integer data (default).",
        argstr="-unsigned",
        xor=_xor_format,
    )

    output_range = traits.Tuple(
        traits.Float,
        traits.Float,
        argstr="-range %s %s",
        desc="Valid range for output data. Default value: -1.79769e+308 -1.79769e+308.",
    )

    _xor_slices = ("transverse", "sagittal", "coronal")

    transverse_slices = traits.Bool(
        desc="Write out transverse slices.", argstr="-transverse", xor=_xor_slices
    )

    sagittal_slices = traits.Bool(
        desc="Write out sagittal slices", argstr="-sagittal", xor=_xor_slices
    )

    coronal_slices = traits.Bool(
        desc="Write out coronal slices", argstr="-coronal", xor=_xor_slices
    )

    _xor_fill = ("nofill", "fill")

    no_fill = traits.Bool(
        desc="Use value zero for points outside of input volume.",
        argstr="-nofill",
        xor=_xor_fill,
    )
    fill = traits.Bool(
        desc="Use a fill value for points outside of input volume.",
        argstr="-fill",
        xor=_xor_fill,
    )

    fill_value = traits.Float(
        desc=(
            "Specify a fill value for points outside of input volume."
            "Default value: 1.79769e+308."
        ),
        argstr="-fillvalue %s",
        requires=["fill"],
    )

    _xor_scale = ("keep_real_range", "nokeep_real_range")

    keep_real_range = traits.Bool(
        desc="Keep the real scale of the input volume.",
        argstr="-keep_real_range",
        xor=_xor_scale,
    )

    nokeep_real_range = traits.Bool(
        desc="Do not keep the real scale of the data (default).",
        argstr="-nokeep_real_range",
        xor=_xor_scale,
    )

    _xor_spacetype = ("spacetype", "talairach")

    spacetype = traits.Str(
        desc="Set the spacetype attribute to a specified string.",
        argstr="-spacetype %s",
    )
    talairach = traits.Bool(desc="Output is in Talairach space.", argstr="-talairach")

    origin = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        desc=(
            "Origin of first pixel in 3D space."
            "Default value: 1.79769e+308 1.79769e+308 1.79769e+308."
        ),
        argstr="-origin %s %s %s",
    )

    standard_sampling = traits.Bool(
        desc="Set the sampling to standard values (step, start and dircos).",
        argstr="-standard_sampling",
    )  # FIXME Bool?
    units = traits.Str(
        desc="Specify the units of the output sampling.", argstr="-units %s"
    )  # FIXME String?

    # Elements along each dimension.
    # FIXME Ints? Ranges?
    # FIXME Check that this xor behaves correctly.
    _xor_nelements = ("nelements", "nelements_x_y_or_z")

    # nr elements along each dimension
    nelements = traits.Tuple(
        traits.Int,
        traits.Int,
        traits.Int,
        desc="Number of elements along each dimension (X, Y, Z).",
        argstr="-nelements %s %s %s",
        xor=_xor_nelements,
    )

    # FIXME Is mincresample happy if we only specify one of these, or do we
    # need the requires=...?
    xnelements = traits.Int(
        desc="Number of elements along the X dimension.",
        argstr="-xnelements %s",
        requires=("ynelements", "znelements"),
        xor=_xor_nelements,
    )

    ynelements = traits.Int(
        desc="Number of elements along the Y dimension.",
        argstr="-ynelements %s",
        requires=("xnelements", "znelements"),
        xor=_xor_nelements,
    )

    znelements = traits.Int(
        desc="Number of elements along the Z dimension.",
        argstr="-znelements %s",
        requires=("xnelements", "ynelements"),
        xor=_xor_nelements,
    )

    # step size along each dimension
    _xor_step = ("step", "step_x_y_or_z")

    step = traits.Tuple(
        traits.Int,
        traits.Int,
        traits.Int,
        desc="Step size along each dimension (X, Y, Z). Default value: (0, 0, 0).",
        argstr="-step %s %s %s",
        xor=_xor_nelements,
    )

    # FIXME Use the requires=...?
    xstep = traits.Int(
        desc="Step size along the X dimension. Default value: 0.",
        argstr="-xstep %s",
        requires=("ystep", "zstep"),
        xor=_xor_step,
    )

    ystep = traits.Int(
        desc="Step size along the Y dimension. Default value: 0.",
        argstr="-ystep %s",
        requires=("xstep", "zstep"),
        xor=_xor_step,
    )

    zstep = traits.Int(
        desc="Step size along the Z dimension. Default value: 0.",
        argstr="-zstep %s",
        requires=("xstep", "ystep"),
        xor=_xor_step,
    )

    # start point along each dimension
    _xor_start = ("start", "start_x_y_or_z")

    start = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        desc=(
            "Start point along each dimension (X, Y, Z)."
            "Default value: 1.79769e+308 1.79769e+308 1.79769e+308."
        ),
        argstr="-start %s %s %s",
        xor=_xor_nelements,
    )

    # FIXME Use the requires=...?
    xstart = traits.Float(
        desc="Start point along the X dimension. Default value: 1.79769e+308.",
        argstr="-xstart %s",
        requires=("ystart", "zstart"),
        xor=_xor_start,
    )

    ystart = traits.Float(
        desc="Start point along the Y dimension. Default value: 1.79769e+308.",
        argstr="-ystart %s",
        requires=("xstart", "zstart"),
        xor=_xor_start,
    )

    zstart = traits.Float(
        desc="Start point along the Z dimension. Default value: 1.79769e+308.",
        argstr="-zstart %s",
        requires=("xstart", "ystart"),
        xor=_xor_start,
    )

    # dircos along each dimension
    _xor_dircos = ("dircos", "dircos_x_y_or_z")

    dircos = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        desc=(
            "Direction cosines along each dimension (X, Y, Z). Default value:"
            "1.79769e+308 1.79769e+308 1.79769e+308 1.79769e+308 ..."
            "  1.79769e+308 1.79769e+308 1.79769e+308 1.79769e+308 1.79769e+308."
        ),
        argstr="-dircos %s %s %s",
        xor=_xor_nelements,
    )

    # FIXME Use the requires=...?
    xdircos = traits.Float(
        desc=(
            "Direction cosines along the X dimension."
            "Default value: 1.79769e+308 1.79769e+308 1.79769e+308."
        ),
        argstr="-xdircos %s",
        requires=("ydircos", "zdircos"),
        xor=_xor_dircos,
    )

    ydircos = traits.Float(
        desc=(
            "Direction cosines along the Y dimension."
            "Default value: 1.79769e+308 1.79769e+308 1.79769e+308."
        ),
        argstr="-ydircos %s",
        requires=("xdircos", "zdircos"),
        xor=_xor_dircos,
    )

    zdircos = traits.Float(
        desc=(
            "Direction cosines along the Z dimension."
            "Default value: 1.79769e+308 1.79769e+308 1.79769e+308."
        ),
        argstr="-zdircos %s",
        requires=("xdircos", "ydircos"),
        xor=_xor_dircos,
    )


class ResampleOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)


class Resample(StdOutCommandLine):
    """
    Resample a minc file.'

    Examples
    --------

    >>> from nipype.interfaces.minc import Resample
    >>> from nipype.interfaces.minc.testdata import minc2Dfile
    >>> r = Resample(input_file=minc2Dfile, output_file='/tmp/out.mnc') # Resample the file.
    >>> r.run() # doctest: +SKIP

    """

    input_spec = ResampleInputSpec
    output_spec = ResampleOutputSpec
    _cmd = "mincresample"


class NormInputSpec(CommandLineInputSpec):
    """

    Not implemented:

       -version         print version and exit
       -verbose         be verbose
       -noverbose       opposite of -verbose [default]
       -quiet           be quiet
       -noquiet         opposite of -quiet [default]
       -fake            do a dry run, (echo cmds only)
       -nofake          opposite of -fake [default]
    """

    input_file = File(
        desc="input file to normalise",
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-2,
    )

    output_file = File(
        desc="output file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_norm.mnc",
    )

    output_threshold_mask = File(
        desc="File in which to store the threshold mask.",
        argstr="-threshold_mask %s",
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_norm_threshold_mask.mnc",
    )

    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )

    # Normalisation Options
    mask = File(
        desc="Calculate the image normalisation within a mask.",
        argstr="-mask %s",
        exists=True,
    )
    clamp = traits.Bool(
        desc="Force the ouput range between limits [default].",
        argstr="-clamp",
        usedefault=True,
        default_value=True,
    )

    cutoff = traits.Range(
        low=0.0,
        high=100.0,
        desc="Cutoff value to use to calculate thresholds by a histogram PcT in %. [default: 0.01]",
        argstr="-cutoff %s",
    )

    lower = traits.Float(desc="Lower real value to use.", argstr="-lower %s")
    upper = traits.Float(desc="Upper real value to use.", argstr="-upper %s")

    out_floor = traits.Float(
        desc="Output files maximum [default: 0]", argstr="-out_floor %s"
    )  # FIXME is this a float?
    out_ceil = traits.Float(
        desc="Output files minimum [default: 100]", argstr="-out_ceil %s"
    )  # FIXME is this a float?

    # Threshold Options
    threshold = traits.Bool(
        desc="Threshold the image (set values below threshold_perc to -out_floor).",
        argstr="-threshold",
    )

    threshold_perc = traits.Range(
        low=0.0,
        high=100.0,
        desc="Threshold percentage (0.1 == lower 10% of intensity range) [default: 0.1].",
        argstr="-threshold_perc %s",
    )

    threshold_bmt = traits.Bool(
        desc="Use the resulting image BiModalT as the threshold.",
        argstr="-threshold_bmt",
    )

    threshold_blur = traits.Float(
        desc="Blur FWHM for intensity edges then thresholding [default: 2].",
        argstr="-threshold_blur %s",
    )


class NormOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)
    output_threshold_mask = File(desc="threshold mask file")


class Norm(CommandLine):
    """Normalise a file between a max and minimum (possibly)
       using two histogram pct's.

    Examples
    --------

    >>> from nipype.interfaces.minc import Norm
    >>> from nipype.interfaces.minc.testdata import minc2Dfile
    >>> n = Norm(input_file=minc2Dfile, output_file='/tmp/out.mnc') # Normalise the file.
    >>> n.run() # doctest: +SKIP
    """

    input_spec = NormInputSpec
    output_spec = NormOutputSpec
    _cmd = "mincnorm"


"""
| volcentre will centre a MINC image's sampling about a point (0,0,0 typically)
|
| NB: It will modify the file in-place unless an outfile is given
|
| Problems or comments should be sent to: a.janke@gmail.com

Summary of options:
   -version      print version and exit
   -verbose      be verbose
   -noverbose    opposite of -verbose [default]
   -clobber      clobber existing check files
   -noclobber    opposite of -clobber [default]
   -fake         do a dry run, (echo cmds only)
   -nofake       opposite of -fake [default]
   -com          Use the CoM of the volume for the new centre (via mincstats)
   -nocom        opposite of -com [default]
   -centre <float> <float> <float>
                 Centre to use (x,y,z) [default: 0 0 0]
   -zero_dircos  Set the direction cosines to identity [default]
   -nozero_dirco opposite of -zero_dircos

Usage: volcentre [options] <infile.mnc> [<outfile.mnc>]
       volcentre -help to list options

"""


class VolcentreInputSpec(CommandLineInputSpec):
    """
    Not implemented:

    -fake         do a dry run, (echo cmds only)
    -nofake       opposite of -fake [default]

    """

    input_file = File(
        desc="input file to centre",
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-2,
    )

    output_file = File(
        desc="output file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_volcentre.mnc",
    )

    verbose = traits.Bool(
        desc="Print out log messages. Default: False.", argstr="-verbose"
    )
    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )

    com = traits.Bool(
        desc="Use the CoM of the volume for the new centre (via mincstats). Default: False",
        argstr="-com",
    )

    centre = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr="-centre %s %s %s",
        desc="Centre to use (x,y,z) [default: 0 0 0].",
    )

    zero_dircos = traits.Bool(
        desc="Set the direction cosines to identity [default].", argstr="-zero_dircos"
    )


class VolcentreOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)


class Volcentre(CommandLine):
    """Centre a MINC image's sampling about a point, typically (0,0,0).

    Example
    --------

    >>> from nipype.interfaces.minc import Volcentre
    >>> from nipype.interfaces.minc.testdata import minc2Dfile
    >>> vc = Volcentre(input_file=minc2Dfile)
    >>> vc.run() # doctest: +SKIP
    """

    input_spec = VolcentreInputSpec
    output_spec = VolcentreOutputSpec
    _cmd = "volcentre"


class VolpadInputSpec(CommandLineInputSpec):
    """
    Not implemented:

    -fake         do a dry run, (echo cmds only)
    -nofake       opposite of -fake [default]

     | volpad pads a MINC volume
     |
     | Problems or comments should be sent to: a.janke@gmail.com

    Summary of options:

    -- General Options -------------------------------------------------------------
       -verbose          be verbose
       -noverbose        opposite of -verbose [default]
       -clobber          clobber existing files
       -noclobber        opposite of -clobber [default]
       -fake             do a dry run, (echo cmds only)
       -nofake           opposite of -fake [default]


    """

    input_file = File(
        desc="input file to centre",
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-2,
    )

    output_file = File(
        desc="output file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_volpad.mnc",
    )

    verbose = traits.Bool(
        desc="Print out log messages. Default: False.", argstr="-verbose"
    )
    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )

    auto = traits.Bool(
        desc="Automatically determine padding distances (uses -distance as max). Default: False.",
        argstr="-auto",
    )

    auto_freq = traits.Float(
        desc="Frequency of voxels over bimodalt threshold to stop at [default: 500].",
        argstr="-auto_freq %s",
    )

    distance = traits.Int(
        desc="Padding distance (in voxels) [default: 4].", argstr="-distance %s"
    )

    smooth = traits.Bool(
        desc="Smooth (blur) edges before padding. Default: False.", argstr="-smooth"
    )

    smooth_distance = traits.Int(
        desc="Smoothing distance (in voxels) [default: 4].",
        argstr="-smooth_distance %s",
    )


class VolpadOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)


class Volpad(CommandLine):
    """Centre a MINC image's sampling about a point, typically (0,0,0).

    Examples
    --------

    >>> from nipype.interfaces.minc import Volpad
    >>> from nipype.interfaces.minc.testdata import minc2Dfile
    >>> vp = Volpad(input_file=minc2Dfile, smooth=True, smooth_distance=4)
    >>> vp.run() # doctest: +SKIP
    """

    input_spec = VolpadInputSpec
    output_spec = VolpadOutputSpec
    _cmd = "volpad"


class VolisoInputSpec(CommandLineInputSpec):

    input_file = File(
        desc="input file to convert to isotropic sampling",
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-2,
    )

    output_file = File(
        desc="output file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_voliso.mnc",
    )

    verbose = traits.Bool(
        desc="Print out log messages. Default: False.", argstr="--verbose"
    )
    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="--clobber",
        usedefault=True,
        default_value=True,
    )

    maxstep = traits.Float(
        desc="The target maximum step desired in the output volume.",
        argstr="--maxstep %s",
    )

    minstep = traits.Float(
        desc="The target minimum step desired in the output volume.",
        argstr="--minstep %s",
    )

    avgstep = traits.Bool(
        desc="Calculate the maximum step from the average steps of the input volume.",
        argstr="--avgstep",
    )


class VolisoOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)


class Voliso(CommandLine):
    """Changes the steps and starts in order that the output volume
    has isotropic sampling.

    Examples
    --------

    >>> from nipype.interfaces.minc import Voliso
    >>> from nipype.interfaces.minc.testdata import minc2Dfile
    >>> viso = Voliso(input_file=minc2Dfile, minstep=0.1, avgstep=True)
    >>> viso.run() # doctest: +SKIP
    """

    input_spec = VolisoInputSpec
    output_spec = VolisoOutputSpec
    _cmd = "voliso"


class GennlxfmInputSpec(CommandLineInputSpec):
    output_file = File(
        desc="output file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["like"],
        hash_files=False,
        name_template="%s_gennlxfm.xfm",
    )

    verbose = traits.Bool(
        desc="Print out log messages. Default: False.", argstr="-verbose"
    )
    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )

    ident = traits.Bool(
        desc="Generate an identity xfm. Default: False.", argstr="-ident"
    )
    step = traits.Int(desc="Output ident xfm step [default: 1].", argstr="-step %s")

    like = File(
        desc="Generate a nlxfm like this file.", exists=True, argstr="-like %s",
    )


class GennlxfmOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)
    output_grid = File(desc="output grid", exists=True)


class Gennlxfm(CommandLine):
    """Generate nonlinear xfms. Currently only identity xfms
    are supported!

    This tool is part of minc-widgets:

    https://github.com/BIC-MNI/minc-widgets/blob/master/gennlxfm/gennlxfm

    Examples
    --------

    >>> from nipype.interfaces.minc import Gennlxfm
    >>> from nipype.interfaces.minc.testdata import minc2Dfile
    >>> gennlxfm = Gennlxfm(step=1, like=minc2Dfile)
    >>> gennlxfm.run() # doctest: +SKIP

    """

    input_spec = GennlxfmInputSpec
    output_spec = GennlxfmOutputSpec
    _cmd = "gennlxfm"

    def _list_outputs(self):
        outputs = super(Gennlxfm, self)._list_outputs()
        outputs["output_grid"] = re.sub(
            ".(nlxfm|xfm)$", "_grid_0.mnc", outputs["output_file"]
        )
        return outputs


class XfmConcatInputSpec(CommandLineInputSpec):
    input_files = InputMultiPath(
        File(exists=True),
        desc="input file(s)",
        mandatory=True,
        sep=" ",
        argstr="%s",
        position=-2,
    )

    # This is a dummy input.
    input_grid_files = InputMultiPath(File, desc="input grid file(s)",)

    output_file = File(
        desc="output file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["input_files"],
        hash_files=False,
        name_template="%s_xfmconcat.xfm",
    )

    verbose = traits.Bool(
        desc="Print out log messages. Default: False.", argstr="-verbose"
    )
    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )


class XfmConcatOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)
    output_grids = OutputMultiPath(File(exists=True), desc="output grids")


class XfmConcat(CommandLine):
    """Concatenate transforms together. The output transformation
    is equivalent to applying input1.xfm, then input2.xfm, ..., in
    that order.

    Examples
    --------

    >>> from nipype.interfaces.minc import XfmConcat
    >>> from nipype.interfaces.minc.testdata import minc2Dfile
    >>> conc = XfmConcat(input_files=['input1.xfm', 'input1.xfm'])
    >>> conc.run() # doctest: +SKIP
    """

    input_spec = XfmConcatInputSpec
    output_spec = XfmConcatOutputSpec
    _cmd = "xfmconcat"

    def _list_outputs(self):
        outputs = super(XfmConcat, self)._list_outputs()

        if os.path.exists(outputs["output_file"]):
            if "grid" in open(outputs["output_file"], "r").read():
                outputs["output_grids"] = glob.glob(
                    re.sub(".(nlxfm|xfm)$", "_grid_*.mnc", outputs["output_file"])
                )

        return outputs


class BestLinRegInputSpec(CommandLineInputSpec):
    source = File(
        desc="source Minc file", exists=True, mandatory=True, argstr="%s", position=-4,
    )

    target = File(
        desc="target Minc file", exists=True, mandatory=True, argstr="%s", position=-3,
    )

    output_xfm = File(
        desc="output xfm file",
        genfile=True,
        argstr="%s",
        position=-2,
        name_source=["source"],
        hash_files=False,
        name_template="%s_bestlinreg.xfm",
        keep_extension=False,
    )

    output_mnc = File(
        desc="output mnc file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["source"],
        hash_files=False,
        name_template="%s_bestlinreg.mnc",
        keep_extension=False,
    )

    verbose = traits.Bool(
        desc="Print out log messages. Default: False.", argstr="-verbose"
    )
    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )

    # FIXME Very bare implementation, none of these are done yet:
    """
    -init_xfm     initial transformation (default identity)
    -source_mask  source mask to use during fitting
    -target_mask  target mask to use during fitting
    -lsq9         use 9-parameter transformation (default)
    -lsq12        use 12-parameter transformation (default -lsq9)
    -lsq6         use 6-parameter transformation
    """


class BestLinRegOutputSpec(TraitedSpec):
    output_xfm = File(desc="output xfm file", exists=True)
    output_mnc = File(desc="output mnc file", exists=True)


class BestLinReg(CommandLine):
    """Hierachial linear fitting between two files.

    The bestlinreg script is part of the EZminc package:

    https://github.com/BIC-MNI/EZminc/blob/master/scripts/bestlinreg.pl

    Examples
    --------

    >>> from nipype.interfaces.minc import BestLinReg
    >>> from nipype.interfaces.minc.testdata import nonempty_minc_data

    >>> input_file = nonempty_minc_data(0)
    >>> target_file = nonempty_minc_data(1)
    >>> linreg = BestLinReg(source=input_file, target=target_file)
    >>> linreg.run() # doctest: +SKIP
    """

    input_spec = BestLinRegInputSpec
    output_spec = BestLinRegOutputSpec
    _cmd = "bestlinreg"


class NlpFitInputSpec(CommandLineInputSpec):
    source = File(
        desc="source Minc file", exists=True, mandatory=True, argstr="%s", position=-3,
    )

    target = File(
        desc="target Minc file", exists=True, mandatory=True, argstr="%s", position=-2,
    )

    output_xfm = File(desc="output xfm file", genfile=True, argstr="%s", position=-1,)

    # This is a dummy input.
    input_grid_files = InputMultiPath(File, desc="input grid file(s)",)

    config_file = File(
        desc="File containing the fitting configuration use.",
        argstr="-config_file %s",
        mandatory=True,
        exists=True,
    )

    init_xfm = File(
        desc="Initial transformation (default identity).",
        argstr="-init_xfm %s",
        mandatory=True,
        exists=True,
    )

    source_mask = File(
        desc="Source mask to use during fitting.",
        argstr="-source_mask %s",
        mandatory=True,
        exists=True,
    )

    verbose = traits.Bool(
        desc="Print out log messages. Default: False.", argstr="-verbose"
    )
    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )


class NlpFitOutputSpec(TraitedSpec):
    output_xfm = File(desc="output xfm file", exists=True)
    output_grid = File(desc="output grid file", exists=True)


class NlpFit(CommandLine):
    """Hierarchial non-linear fitting with bluring.

    This tool is part of the minc-widgets package:

    https://github.com/BIC-MNI/minc-widgets/blob/master/nlpfit/nlpfit

    Examples
    --------

    >>> from nipype.interfaces.minc import NlpFit
    >>> from nipype.interfaces.minc.testdata import nonempty_minc_data, nlp_config
    >>> from nipype.testing import example_data

    >>> source = nonempty_minc_data(0)
    >>> target = nonempty_minc_data(1)
    >>> source_mask = nonempty_minc_data(2)
    >>> config = nlp_config
    >>> initial = example_data('minc_initial.xfm')
    >>> nlpfit = NlpFit(config_file=config, init_xfm=initial, source_mask=source_mask, source=source, target=target)
    >>> nlpfit.run() # doctest: +SKIP
    """

    input_spec = NlpFitInputSpec
    output_spec = NlpFitOutputSpec
    _cmd = "nlpfit"

    def _gen_filename(self, name):
        if name == "output_xfm":
            output_xfm = self.inputs.output_xfm

            if isdefined(output_xfm):
                return os.path.abspath(output_xfm)
            else:
                return (
                    aggregate_filename(
                        [self.inputs.source, self.inputs.target], "nlpfit_xfm_output"
                    )
                    + ".xfm"
                )
        else:
            raise NotImplemented

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["output_xfm"] = os.path.abspath(self._gen_filename("output_xfm"))

        assert os.path.exists(outputs["output_xfm"])
        if "grid" in open(outputs["output_xfm"], "r").read():
            outputs["output_grid"] = re.sub(
                ".(nlxfm|xfm)$", "_grid_0.mnc", outputs["output_xfm"]
            )

        return outputs


class XfmAvgInputSpec(CommandLineInputSpec):
    input_files = InputMultiPath(
        File(exists=True),
        desc="input file(s)",
        mandatory=True,
        sep=" ",
        argstr="%s",
        position=-2,
    )

    # This is a dummy input.
    input_grid_files = InputMultiPath(File, desc="input grid file(s)",)

    output_file = File(desc="output file", genfile=True, argstr="%s", position=-1,)

    verbose = traits.Bool(
        desc="Print out log messages. Default: False.", argstr="-verbose"
    )
    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )

    # FIXME xor these:

    avg_linear = traits.Bool(
        desc="average the linear part [default].", argstr="-avg_linear"
    )
    avg_nonlinear = traits.Bool(
        desc="average the non-linear part [default].", argstr="-avg_nonlinear"
    )

    ignore_linear = traits.Bool(
        desc="opposite of -avg_linear.", argstr="-ignore_linear"
    )
    ignore_nonlinear = traits.Bool(
        desc="opposite of -avg_nonlinear.", argstr="-ignore_nonline"
    )


class XfmAvgOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)
    output_grid = File(desc="output grid file", exists=True)


class XfmAvg(CommandLine):
    """Average a number of xfm transforms using matrix logs and exponents.
    The program xfmavg calls Octave for numerical work.

    This tool is part of the minc-widgets package:

    https://github.com/BIC-MNI/minc-widgets/tree/master/xfmavg

    Examples
    --------

    >>> from nipype.interfaces.minc import XfmAvg
    >>> from nipype.interfaces.minc.testdata import nonempty_minc_data, nlp_config
    >>> from nipype.testing import example_data

    >>> xfm1 = example_data('minc_initial.xfm')
    >>> xfm2 = example_data('minc_initial.xfm')  # cheating for doctest
    >>> xfmavg = XfmAvg(input_files=[xfm1, xfm2])
    >>> xfmavg.run() # doctest: +SKIP
    """

    input_spec = XfmAvgInputSpec
    output_spec = XfmAvgOutputSpec
    _cmd = "xfmavg"

    def _gen_filename(self, name):
        if name == "output_file":
            output_file = self.inputs.output_file

            if isdefined(output_file):
                return os.path.abspath(output_file)
            else:
                return (
                    aggregate_filename(self.inputs.input_files, "xfmavg_output")
                    + ".xfm"
                )
        else:
            raise NotImplemented

    def _gen_outfilename(self):
        return self._gen_filename("output_file")

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["output_file"] = os.path.abspath(self._gen_outfilename())

        assert os.path.exists(outputs["output_file"])
        if "grid" in open(outputs["output_file"], "r").read():
            outputs["output_grid"] = re.sub(
                ".(nlxfm|xfm)$", "_grid_0.mnc", outputs["output_file"]
            )

        return outputs


class XfmInvertInputSpec(CommandLineInputSpec):
    input_file = File(
        desc="input file", exists=True, mandatory=True, argstr="%s", position=-2
    )

    output_file = File(desc="output file", genfile=True, argstr="%s", position=-1,)

    verbose = traits.Bool(
        desc="Print out log messages. Default: False.", argstr="-verbose"
    )
    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )


class XfmInvertOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)
    output_grid = File(desc="output grid file", exists=True)


class XfmInvert(CommandLine):
    """Invert an xfm transform file.

    Examples
    --------

    >>> from nipype.interfaces.minc import XfmAvg
    >>> from nipype.testing import example_data

    >>> xfm = example_data('minc_initial.xfm')
    >>> invert = XfmInvert(input_file=xfm)
    >>> invert.run() # doctest: +SKIP
    """

    input_spec = XfmInvertInputSpec
    output_spec = XfmInvertOutputSpec
    _cmd = "xfminvert"

    def _gen_filename(self, name):
        if name == "output_file":
            output_file = self.inputs.output_file

            if isdefined(output_file):
                return os.path.abspath(output_file)
            else:
                return (
                    aggregate_filename([self.inputs.input_file], "xfminvert_output")
                    + ".xfm"
                )
        else:
            raise NotImplemented

    def _gen_outfilename(self):
        return self._gen_filename("output_file")

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["output_file"] = os.path.abspath(self._gen_outfilename())

        assert os.path.exists(outputs["output_file"])
        if "grid" in open(outputs["output_file"], "r").read():
            outputs["output_grid"] = re.sub(
                ".(nlxfm|xfm)$", "_grid_0.mnc", outputs["output_file"]
            )

        return outputs


class BigAverageInputSpec(CommandLineInputSpec):
    input_files = InputMultiPath(
        File(exists=True),
        desc="input file(s)",
        mandatory=True,
        sep=" ",
        argstr="%s",
        position=-2,
    )

    output_file = File(
        desc="output file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["input_files"],
        hash_files=False,
        name_template="%s_bigaverage.mnc",
    )

    verbose = traits.Bool(
        desc="Print out log messages. Default: False.", argstr="--verbose"
    )
    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="--clobber",
        usedefault=True,
        default_value=True,
    )

    # FIXME Redumentary implementation, various parameters not implemented.
    # TODO!
    output_float = traits.Bool(
        desc="Output files with float precision.", argstr="--float"
    )

    robust = traits.Bool(
        desc=(
            "Perform robust averaging, features that are outside 1 standard"
            "deviation from the mean are downweighted. Works well for noisy"
            "data with artifacts. see the --tmpdir option if you have a"
            "large number of input files."
        ),
        argstr="-robust",
    )

    # Should Nipype deal with where the temp directory is?
    tmpdir = Directory(desc="temporary files directory", argstr="-tmpdir %s")
    sd_file = File(
        desc="Place standard deviation image in specified file.",
        argstr="--sdfile %s",
        name_source=["input_files"],
        hash_files=False,
        name_template="%s_bigaverage_stdev.mnc",
    )


class BigAverageOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)
    sd_file = File(desc="standard deviation image", exists=True)


class BigAverage(CommandLine):
    """Average 1000's of MINC files in linear time.

    mincbigaverage is designed to discretise the problem of averaging either
    a large number of input files or averaging a smaller number of large
    files. (>1GB each). There is also some code included to perform "robust"
    averaging in which only the most common features are kept via down-weighting
    outliers beyond a standard deviation.

    One advantage of mincbigaverage is that it avoids issues around the number
    of possible open files in HDF/netCDF. In short if you have more than 100
    files open at once while averaging things will slow down significantly.

    mincbigaverage does this via a iterative approach to averaging files and
    is a direct drop in replacement for mincaverage. That said not all the
    arguments of mincaverage are supported in mincbigaverage but they should
    be.

    This tool is part of the minc-widgets package:

    https://github.com/BIC-MNI/minc-widgets/blob/master/mincbigaverage/mincbigaverage

    Examples
    --------

    >>> from nipype.interfaces.minc import BigAverage
    >>> from nipype.interfaces.minc.testdata import nonempty_minc_data

    >>> files = [nonempty_minc_data(i) for i in range(3)]
    >>> average = BigAverage(input_files=files, output_float=True, robust=True)
    >>> average.run() # doctest: +SKIP
    """

    input_spec = BigAverageInputSpec
    output_spec = BigAverageOutputSpec
    _cmd = "mincbigaverage"


class ReshapeInputSpec(CommandLineInputSpec):
    input_file = File(
        desc="input file", exists=True, mandatory=True, argstr="%s", position=-2
    )

    output_file = File(
        desc="output file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_reshape.mnc",
    )

    verbose = traits.Bool(
        desc="Print out log messages. Default: False.", argstr="-verbose"
    )
    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )

    # FIXME MANY options not implemented!

    write_short = traits.Bool(desc="Convert to short integer data.", argstr="-short")


class ReshapeOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)


class Reshape(CommandLine):
    """Cut a hyperslab out of a minc file, with dimension reordering.

    This is also useful for rewriting with a different format, for
    example converting to short (see example below).

    Examples
    --------

    >>> from nipype.interfaces.minc import Reshape
    >>> from nipype.interfaces.minc.testdata import nonempty_minc_data

    >>> input_file = nonempty_minc_data(0)
    >>> reshape_to_short = Reshape(input_file=input_file, write_short=True)
    >>> reshape_to_short.run() # doctest: +SKIP

    """

    input_spec = ReshapeInputSpec
    output_spec = ReshapeOutputSpec
    _cmd = "mincreshape"


class VolSymmInputSpec(CommandLineInputSpec):
    input_file = File(
        desc="input file", exists=True, mandatory=True, argstr="%s", position=-3
    )

    trans_file = File(
        desc="output xfm trans file",
        genfile=True,
        argstr="%s",
        position=-2,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_vol_symm.xfm",
        keep_extension=False,
    )

    output_file = File(
        desc="output file",
        genfile=True,
        argstr="%s",
        position=-1,
        name_source=["input_file"],
        hash_files=False,
        name_template="%s_vol_symm.mnc",
    )

    # This is a dummy input.
    input_grid_files = InputMultiPath(File, desc="input grid file(s)",)

    verbose = traits.Bool(
        desc="Print out log messages. Default: False.", argstr="-verbose"
    )
    clobber = traits.Bool(
        desc="Overwrite existing file.",
        argstr="-clobber",
        usedefault=True,
        default_value=True,
    )

    # FIXME MANY options not implemented!

    fit_linear = traits.Bool(desc="Fit using a linear xfm.", argstr="-linear")
    fit_nonlinear = traits.Bool(desc="Fit using a non-linear xfm.", argstr="-nonlinear")

    # FIXME This changes the input/output behaviour of trans_file! Split into
    # two separate interfaces?
    nofit = traits.Bool(
        desc="Use the input transformation instead of generating one.", argstr="-nofit"
    )

    config_file = File(
        desc="File containing the fitting configuration (nlpfit -help for info).",
        argstr="-config_file %s",
        exists=True,
    )

    x = traits.Bool(desc="Flip volume in x-plane (default).", argstr="-x")
    y = traits.Bool(desc="Flip volume in y-plane.", argstr="-y")
    z = traits.Bool(desc="Flip volume in z-plane.", argstr="-z")


class VolSymmOutputSpec(TraitedSpec):
    output_file = File(desc="output file", exists=True)
    trans_file = File(desc="xfm trans file", exists=True)
    output_grid = File(
        desc="output grid file", exists=True
    )  # FIXME Is exists=True correct?


class VolSymm(CommandLine):
    """Make a volume symmetric about an axis either linearly
    and/or nonlinearly. This is done by registering a volume
    to a flipped image of itself.

    This tool is part of the minc-widgets package:

    https://github.com/BIC-MNI/minc-widgets/blob/master/volsymm/volsymm

    Examples
    --------

    >>> from nipype.interfaces.minc import VolSymm
    >>> from nipype.interfaces.minc.testdata import nonempty_minc_data

    >>> input_file = nonempty_minc_data(0)
    >>> volsymm = VolSymm(input_file=input_file)
    >>> volsymm.run() # doctest: +SKIP

    """

    input_spec = VolSymmInputSpec
    output_spec = VolSymmOutputSpec
    _cmd = "volsymm"

    def _list_outputs(self):
        outputs = super(VolSymm, self)._list_outputs()

        # Have to manually check for the grid files.
        if os.path.exists(outputs["trans_file"]):
            if "grid" in open(outputs["trans_file"], "r").read():
                outputs["output_grid"] = re.sub(
                    ".(nlxfm|xfm)$", "_grid_0.mnc", outputs["trans_file"]
                )

        return outputs
