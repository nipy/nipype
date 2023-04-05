# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Miscellaneous algorithms."""
import os
import os.path as op

import nibabel as nb
import numpy as np
from math import floor, ceil
import itertools
import warnings

from .. import logging
from . import metrics as nam
from ..interfaces.base import (
    BaseInterface,
    traits,
    TraitedSpec,
    File,
    InputMultiPath,
    OutputMultiPath,
    BaseInterfaceInputSpec,
    isdefined,
    DynamicTraitedSpec,
    Undefined,
)
from ..utils.filemanip import fname_presuffix, split_filename, ensure_list

from . import confounds

iflogger = logging.getLogger("nipype.interface")


class PickAtlasInputSpec(BaseInterfaceInputSpec):
    atlas = File(
        exists=True, desc="Location of the atlas that will be used.", mandatory=True
    )
    labels = traits.Either(
        traits.Int,
        traits.List(traits.Int),
        desc=(
            "Labels of regions that will be included in the mask. Must be\
        compatible with the atlas used."
        ),
        mandatory=True,
    )
    hemi = traits.Enum(
        "both",
        "left",
        "right",
        desc="Restrict the mask to only one hemisphere: left or right",
        usedefault=True,
    )
    dilation_size = traits.Int(
        usedefault=True,
        desc="Defines how much the mask will be dilated (expanded in 3D).",
    )
    output_file = File(desc="Where to store the output mask.")


class PickAtlasOutputSpec(TraitedSpec):
    mask_file = File(exists=True, desc="output mask file")


class PickAtlas(BaseInterface):
    """Returns ROI masks given an atlas and a list of labels. Supports dilation
    and left right masking (assuming the atlas is properly aligned).
    """

    input_spec = PickAtlasInputSpec
    output_spec = PickAtlasOutputSpec

    def _run_interface(self, runtime):
        nim = self._get_brodmann_area()
        nb.save(nim, self._gen_output_filename())

        return runtime

    def _gen_output_filename(self):
        if not isdefined(self.inputs.output_file):
            output = fname_presuffix(
                fname=self.inputs.atlas,
                suffix="_mask",
                newpath=os.getcwd(),
                use_ext=True,
            )
        else:
            output = os.path.realpath(self.inputs.output_file)
        return output

    def _get_brodmann_area(self):
        nii = nb.load(self.inputs.atlas)
        origdata = np.asanyarray(nii.dataobj)
        newdata = np.zeros(origdata.shape)

        if not isinstance(self.inputs.labels, list):
            labels = [self.inputs.labels]
        else:
            labels = self.inputs.labels
        for lab in labels:
            newdata[origdata == lab] = 1
        if self.inputs.hemi == "right":
            newdata[int(floor(float(origdata.shape[0]) / 2)) :, :, :] = 0
        elif self.inputs.hemi == "left":
            newdata[: int(ceil(float(origdata.shape[0]) / 2)), :, :] = 0

        if self.inputs.dilation_size != 0:
            from scipy.ndimage.morphology import grey_dilation

            newdata = grey_dilation(
                newdata,
                (
                    2 * self.inputs.dilation_size + 1,
                    2 * self.inputs.dilation_size + 1,
                    2 * self.inputs.dilation_size + 1,
                ),
            )

        return nb.Nifti1Image(newdata, nii.affine, nii.header)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["mask_file"] = self._gen_output_filename()
        return outputs


class SimpleThresholdInputSpec(BaseInterfaceInputSpec):
    volumes = InputMultiPath(
        File(exists=True), desc="volumes to be thresholded", mandatory=True
    )
    threshold = traits.Float(
        desc="volumes to be thresholdedeverything below this value will be set\
        to zero",
        mandatory=True,
    )


class SimpleThresholdOutputSpec(TraitedSpec):
    thresholded_volumes = OutputMultiPath(File(exists=True), desc="thresholded volumes")


class SimpleThreshold(BaseInterface):
    """Applies a threshold to input volumes"""

    input_spec = SimpleThresholdInputSpec
    output_spec = SimpleThresholdOutputSpec

    def _run_interface(self, runtime):
        for fname in self.inputs.volumes:
            img = nb.load(fname)
            data = img.get_fdata()

            active_map = data > self.inputs.threshold

            thresholded_map = np.zeros(data.shape)
            thresholded_map[active_map] = data[active_map]

            new_img = nb.Nifti1Image(thresholded_map, img.affine, img.header)
            _, base, _ = split_filename(fname)
            nb.save(new_img, base + "_thresholded.nii")

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["thresholded_volumes"] = []
        for fname in self.inputs.volumes:
            _, base, _ = split_filename(fname)
            outputs["thresholded_volumes"].append(
                os.path.abspath(base + "_thresholded.nii")
            )
        return outputs


class ModifyAffineInputSpec(BaseInterfaceInputSpec):
    volumes = InputMultiPath(
        File(exists=True),
        desc="volumes which affine matrices will be modified",
        mandatory=True,
    )
    transformation_matrix = traits.Array(
        value=np.eye(4),
        shape=(4, 4),
        desc="transformation matrix that will be left multiplied by the\
        affine matrix",
        usedefault=True,
    )


class ModifyAffineOutputSpec(TraitedSpec):
    transformed_volumes = OutputMultiPath(File(exist=True))


class ModifyAffine(BaseInterface):
    """Left multiplies the affine matrix with a specified values. Saves the volume
    as a nifti file.
    """

    input_spec = ModifyAffineInputSpec
    output_spec = ModifyAffineOutputSpec

    def _gen_output_filename(self, name):
        _, base, _ = split_filename(name)
        return os.path.abspath(base + "_transformed.nii")

    def _run_interface(self, runtime):
        for fname in self.inputs.volumes:
            img = nb.load(fname)

            affine = img.affine
            affine = np.dot(self.inputs.transformation_matrix, affine)

            nb.save(
                nb.Nifti1Image(img.dataobj, affine, img.header),
                self._gen_output_filename(fname),
            )

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["transformed_volumes"] = []
        for fname in self.inputs.volumes:
            outputs["transformed_volumes"].append(self._gen_output_filename(fname))
        return outputs


class CreateNiftiInputSpec(BaseInterfaceInputSpec):
    data_file = File(exists=True, mandatory=True, desc="ANALYZE img file")
    header_file = File(
        exists=True, mandatory=True, desc="corresponding ANALYZE hdr file"
    )
    affine = traits.Array(desc="affine transformation array")


class CreateNiftiOutputSpec(TraitedSpec):
    nifti_file = File(exists=True)


class CreateNifti(BaseInterface):
    """Creates a nifti volume"""

    input_spec = CreateNiftiInputSpec
    output_spec = CreateNiftiOutputSpec

    def _gen_output_file_name(self):
        _, base, _ = split_filename(self.inputs.data_file)
        return os.path.abspath(base + ".nii")

    def _run_interface(self, runtime):
        with open(self.inputs.header_file, "rb") as hdr_file:
            hdr = nb.AnalyzeHeader.from_fileobj(hdr_file)

        if isdefined(self.inputs.affine):
            affine = self.inputs.affine
        else:
            affine = None

        with open(self.inputs.data_file, "rb") as data_file:
            data = hdr.data_from_fileobj(data_file)

        img = nb.Nifti1Image(data, affine, hdr)
        nb.save(img, self._gen_output_file_name())

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["nifti_file"] = self._gen_output_file_name()
        return outputs


class GzipInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True, desc="file to (de)compress")
    mode = traits.Enum(
        "compress", "decompress", usedefault=True, desc="compress or decompress"
    )


class GzipOutputSpec(TraitedSpec):
    out_file = File()


class Gzip(BaseInterface):
    """Gzip wrapper

    >>> from nipype.algorithms.misc import Gzip
    >>> gzip = Gzip(in_file='tpms_msk.nii.gz', mode="decompress")
    >>> res = gzip.run()
    >>> res.outputs.out_file  # doctest: +ELLIPSIS
    '.../tpms_msk.nii'

    >>> gzip = Gzip(in_file='tpms_msk.nii')
    >>> res = gzip.run()
    >>> res.outputs.out_file  # doctest: +ELLIPSIS
    '.../tpms_msk.nii.gz'

    .. testcleanup::

    >>> os.unlink('tpms_msk.nii')
    """

    input_spec = GzipInputSpec
    output_spec = GzipOutputSpec

    def _gen_output_file_name(self):
        _, base, ext = split_filename(self.inputs.in_file)
        if self.inputs.mode == "decompress" and ext[-3:].lower() == ".gz":
            ext = ext[:-3]
        elif self.inputs.mode == "compress":
            ext = f"{ext}.gz"
        return os.path.abspath(base + ext)

    def _run_interface(self, runtime):
        import gzip
        import shutil

        if self.inputs.mode == "compress":
            open_input, open_output = open, gzip.open
        else:
            open_input, open_output = gzip.open, open

        with open_input(self.inputs.in_file, "rb") as in_file:
            with open_output(self._gen_output_file_name(), "wb") as out_file:
                shutil.copyfileobj(in_file, out_file)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = self._gen_output_file_name()
        return outputs


class GunzipInputSpec(GzipInputSpec):
    mode = traits.Enum("decompress", usedefault=True, desc="decompress or compress")


class Gunzip(Gzip):
    """Gunzip wrapper

    >>> from nipype.algorithms.misc import Gunzip
    >>> gunzip = Gunzip(in_file='tpms_msk.nii.gz')
    >>> res = gunzip.run()
    >>> res.outputs.out_file  # doctest: +ELLIPSIS
    '.../tpms_msk.nii'

    .. testcleanup::

    >>> os.unlink('tpms_msk.nii')
    """

    input_spec = GunzipInputSpec


def replaceext(in_list, ext):
    out_list = list()
    for filename in in_list:
        path, name, _ = split_filename(op.abspath(filename))
        out_name = op.join(path, name) + ext
        out_list.append(out_name)
    return out_list


def _matlab2csv(in_array, name, reshape):
    output_array = np.asarray(in_array)
    if reshape:
        if len(np.shape(output_array)) > 1:
            output_array = np.reshape(
                output_array, (np.shape(output_array)[0] * np.shape(output_array)[1], 1)
            )
            iflogger.info(np.shape(output_array))
    output_name = op.abspath(name + ".csv")
    np.savetxt(output_name, output_array, delimiter=",")
    return output_name


class Matlab2CSVInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True, desc="Input MATLAB .mat file")
    reshape_matrix = traits.Bool(
        True,
        usedefault=True,
        desc="The output of this interface is meant for R, so matrices will be\
        reshaped to vectors by default.",
    )


class Matlab2CSVOutputSpec(TraitedSpec):
    csv_files = OutputMultiPath(
        File(
            desc="Output CSV files for each variable saved in the input .mat\
        file"
        )
    )


class Matlab2CSV(BaseInterface):
    """
    Save the components of a MATLAB .mat file as a text file with comma-separated values (CSVs).

    CSV files are easily loaded in R, for use in statistical processing.
    For further information, see cran.r-project.org/doc/manuals/R-data.pdf

    Example
    -------
    >>> from nipype.algorithms import misc
    >>> mat2csv = misc.Matlab2CSV()
    >>> mat2csv.inputs.in_file = 'cmatrix.mat'
    >>> mat2csv.run() # doctest: +SKIP

    """

    input_spec = Matlab2CSVInputSpec
    output_spec = Matlab2CSVOutputSpec

    def _run_interface(self, runtime):
        import scipy.io as sio

        in_dict = sio.loadmat(op.abspath(self.inputs.in_file))

        # Check if the file has multiple variables in it. If it does, loop
        # through them and save them as individual CSV files.
        # If not, save the variable as a single CSV file using the input file
        # name and a .csv extension.

        saved_variables = list()
        for key in list(in_dict.keys()):
            if not key.startswith("__"):
                if isinstance(in_dict[key][0], np.ndarray):
                    saved_variables.append(key)
                else:
                    iflogger.info(
                        "One of the keys in the input file, %s, is "
                        "not a Numpy array",
                        key,
                    )

        if len(saved_variables) > 1:
            iflogger.info("%i variables found:", len(saved_variables))
            iflogger.info(saved_variables)
            for variable in saved_variables:
                iflogger.info(
                    "...Converting %s - type %s - to CSV",
                    variable,
                    type(in_dict[variable]),
                )
                _matlab2csv(in_dict[variable], variable, self.inputs.reshape_matrix)
        elif len(saved_variables) == 1:
            _, name, _ = split_filename(self.inputs.in_file)
            variable = saved_variables[0]
            iflogger.info(
                "Single variable found %s, type %s:", variable, type(in_dict[variable])
            )
            iflogger.info(
                "...Converting %s to CSV from %s", variable, self.inputs.in_file
            )
            _matlab2csv(in_dict[variable], name, self.inputs.reshape_matrix)
        else:
            iflogger.error("No values in the MATLAB file?!")
        return runtime

    def _list_outputs(self):
        import scipy.io as sio

        outputs = self.output_spec().get()
        in_dict = sio.loadmat(op.abspath(self.inputs.in_file))
        saved_variables = list()
        for key in list(in_dict.keys()):
            if not key.startswith("__"):
                if isinstance(in_dict[key][0], np.ndarray):
                    saved_variables.append(key)
                else:
                    iflogger.error(
                        "One of the keys in the input file, %s, is "
                        "not a Numpy array",
                        key,
                    )

        if len(saved_variables) > 1:
            outputs["csv_files"] = replaceext(saved_variables, ".csv")
        elif len(saved_variables) == 1:
            _, name, ext = split_filename(self.inputs.in_file)
            outputs["csv_files"] = op.abspath(name + ".csv")
        else:
            iflogger.error("No values in the MATLAB file?!")
        return outputs


def merge_csvs(in_list):
    for idx, in_file in enumerate(in_list):
        try:
            in_array = np.loadtxt(in_file, delimiter=",")
        except ValueError:
            try:
                in_array = np.loadtxt(in_file, delimiter=",", skiprows=1)
            except ValueError:
                with open(in_file, "r") as first:
                    header_line = first.readline()

                header_list = header_line.split(",")
                n_cols = len(header_list)
                try:
                    in_array = np.loadtxt(
                        in_file,
                        delimiter=",",
                        skiprows=1,
                        usecols=list(range(1, n_cols)),
                    )
                except ValueError:
                    in_array = np.loadtxt(
                        in_file,
                        delimiter=",",
                        skiprows=1,
                        usecols=list(range(1, n_cols - 1)),
                    )
        if idx == 0:
            out_array = in_array
        else:
            out_array = np.dstack((out_array, in_array))
    out_array = np.squeeze(out_array)
    iflogger.info("Final output array shape:")
    iflogger.info(np.shape(out_array))
    return out_array


def remove_identical_paths(in_files):
    import os.path as op
    from ..utils.filemanip import split_filename

    if len(in_files) > 1:
        out_names = list()
        commonprefix = op.commonprefix(in_files)
        lastslash = commonprefix.rfind("/")
        commonpath = commonprefix[0 : (lastslash + 1)]
        for fileidx, in_file in enumerate(in_files):
            path, name, ext = split_filename(in_file)
            in_file = op.join(path, name)
            name = in_file.replace(commonpath, "")
            name = name.replace("_subject_id_", "")
            out_names.append(name)
    else:
        path, name, ext = split_filename(in_files[0])
        out_names = [name]
    return out_names


def maketypelist(rowheadings, shape, extraheadingBool, extraheading):
    typelist = []
    if rowheadings:
        typelist.append(("heading", "a40"))
    if len(shape) > 1:
        for idx in range(1, (min(shape) + 1)):
            typelist.append((str(idx), float))
    else:
        for idx in range(1, (shape[0] + 1)):
            typelist.append((str(idx), float))
    if extraheadingBool:
        typelist.append((extraheading, "a40"))
    iflogger.info(typelist)
    return typelist


def makefmtlist(output_array, typelist, rowheadingsBool, shape, extraheadingBool):
    fmtlist = []
    if rowheadingsBool:
        fmtlist.append("%s")
    if len(shape) > 1:
        output = np.zeros(max(shape), typelist)
        for idx in range(1, min(shape) + 1):
            output[str(idx)] = output_array[:, idx - 1]
            fmtlist.append("%f")
    else:
        output = np.zeros(1, typelist)
        for idx in range(1, len(output_array) + 1):
            output[str(idx)] = output_array[idx - 1]
            fmtlist.append("%f")
    if extraheadingBool:
        fmtlist.append("%s")
    fmt = ",".join(fmtlist)
    return fmt, output


class MergeCSVFilesInputSpec(TraitedSpec):
    in_files = InputMultiPath(
        File(exists=True),
        mandatory=True,
        desc="Input comma-separated value (CSV) files",
    )
    out_file = File(
        "merged.csv", usedefault=True, desc="Output filename for merged CSV file"
    )
    column_headings = traits.List(
        traits.Str,
        desc="List of column headings to save in merged CSV file\
        (must be equal to number of input files). If left undefined, these\
        will be pulled from the input filenames.",
    )
    row_headings = traits.List(
        traits.Str,
        desc="List of row headings to save in merged CSV file\
        (must be equal to number of rows in the input files).",
    )
    row_heading_title = traits.Str(
        "label",
        usedefault=True,
        desc="Column heading for the row headings\
         added",
    )
    extra_column_heading = traits.Str(desc="New heading to add for the added field.")
    extra_field = traits.Str(
        desc="New field to add to each row. This is useful for saving the\
        group or subject ID in the file."
    )


class MergeCSVFilesOutputSpec(TraitedSpec):
    csv_file = File(desc="Output CSV file containing columns ")


class MergeCSVFiles(BaseInterface):
    """
    Merge several CSV files into a single CSV file.

    This interface is designed to facilitate data loading in the R environment.
    If provided, it will also incorporate column heading names into the
    resulting CSV file.
    CSV files are easily loaded in R, for use in statistical processing.
    For further information, see cran.r-project.org/doc/manuals/R-data.pdf

    Example
    -------
    >>> from nipype.algorithms import misc
    >>> mat2csv = misc.MergeCSVFiles()
    >>> mat2csv.inputs.in_files = ['degree.mat','clustering.mat']
    >>> mat2csv.inputs.column_headings = ['degree','clustering']
    >>> mat2csv.run() # doctest: +SKIP

    """

    input_spec = MergeCSVFilesInputSpec
    output_spec = MergeCSVFilesOutputSpec

    def _run_interface(self, runtime):
        extraheadingBool = False
        extraheading = ""
        rowheadingsBool = False
        """
        This block defines the column headings.
        """
        if isdefined(self.inputs.column_headings):
            iflogger.info("Column headings have been provided:")
            headings = self.inputs.column_headings
        else:
            iflogger.info("Column headings not provided! Pulled from input filenames:")
            headings = remove_identical_paths(self.inputs.in_files)

        if isdefined(self.inputs.extra_field):
            if isdefined(self.inputs.extra_column_heading):
                extraheading = self.inputs.extra_column_heading
                iflogger.info("Extra column heading provided: %s", extraheading)
            else:
                extraheading = "type"
                iflogger.info('Extra column heading was not defined. Using "type"')
            headings.append(extraheading)
            extraheadingBool = True

        if len(self.inputs.in_files) == 1:
            iflogger.warning("Only one file input!")

        if isdefined(self.inputs.row_headings):
            iflogger.info(
                'Row headings have been provided. Adding "labels"' "column header."
            )
            prefix = '"{p}","'.format(p=self.inputs.row_heading_title)
            csv_headings = prefix + '","'.join(itertools.chain(headings)) + '"\n'
            rowheadingsBool = True
        else:
            iflogger.info("Row headings have not been provided.")
            csv_headings = '"' + '","'.join(itertools.chain(headings)) + '"\n'

        iflogger.info("Final Headings:")
        iflogger.info(csv_headings)
        """
        Next we merge the arrays and define the output text file
        """

        output_array = merge_csvs(self.inputs.in_files)
        _, name, ext = split_filename(self.inputs.out_file)
        if not ext == ".csv":
            ext = ".csv"

        out_file = op.abspath(name + ext)
        with open(out_file, "w") as file_handle:
            file_handle.write(csv_headings)

        shape = np.shape(output_array)
        typelist = maketypelist(rowheadingsBool, shape, extraheadingBool, extraheading)
        fmt, output = makefmtlist(
            output_array, typelist, rowheadingsBool, shape, extraheadingBool
        )

        if rowheadingsBool:
            row_heading_list = self.inputs.row_headings
            row_heading_list_with_quotes = []
            for row_heading in row_heading_list:
                row_heading_with_quotes = '"' + row_heading + '"'
                row_heading_list_with_quotes.append(row_heading_with_quotes)
            row_headings = np.array(row_heading_list_with_quotes, dtype="|S40")
            output["heading"] = row_headings

        if isdefined(self.inputs.extra_field):
            extrafieldlist = []
            if len(shape) > 1:
                mx = shape[0]
            else:
                mx = 1
            for idx in range(0, mx):
                extrafieldlist.append(self.inputs.extra_field)
            iflogger.info(len(extrafieldlist))
            output[extraheading] = extrafieldlist
        iflogger.info(output)
        iflogger.info(fmt)
        with open(out_file, "a") as file_handle:
            np.savetxt(file_handle, output, fmt, delimiter=",")

        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        _, name, ext = split_filename(self.inputs.out_file)
        if not ext == ".csv":
            ext = ".csv"
        out_file = op.abspath(name + ext)
        outputs["csv_file"] = out_file
        return outputs


class AddCSVColumnInputSpec(TraitedSpec):
    in_file = File(
        exists=True, mandatory=True, desc="Input comma-separated value (CSV) files"
    )
    out_file = File(
        "extra_heading.csv", usedefault=True, desc="Output filename for merged CSV file"
    )
    extra_column_heading = traits.Str(desc="New heading to add for the added field.")
    extra_field = traits.Str(
        desc="New field to add to each row. This is useful for saving the\
        group or subject ID in the file."
    )


class AddCSVColumnOutputSpec(TraitedSpec):
    csv_file = File(desc="Output CSV file containing columns ")


class AddCSVColumn(BaseInterface):
    """
    Short interface to add an extra column and field to a text file.

    Example
    -------
    >>> from nipype.algorithms import misc
    >>> addcol = misc.AddCSVColumn()
    >>> addcol.inputs.in_file = 'degree.csv'
    >>> addcol.inputs.extra_column_heading = 'group'
    >>> addcol.inputs.extra_field = 'male'
    >>> addcol.run() # doctest: +SKIP

    """

    input_spec = AddCSVColumnInputSpec
    output_spec = AddCSVColumnOutputSpec

    def _run_interface(self, runtime):
        in_file = open(self.inputs.in_file, "r")
        _, name, ext = split_filename(self.inputs.out_file)
        if not ext == ".csv":
            ext = ".csv"
        out_file = op.abspath(name + ext)

        out_file = open(out_file, "w")
        firstline = in_file.readline()
        firstline = firstline.replace("\n", "")
        new_firstline = firstline + ',"' + self.inputs.extra_column_heading + '"\n'
        out_file.write(new_firstline)
        for line in in_file:
            new_line = line.replace("\n", "")
            new_line = new_line + "," + self.inputs.extra_field + "\n"
            out_file.write(new_line)
        in_file.close()
        out_file.close()
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        _, name, ext = split_filename(self.inputs.out_file)
        if not ext == ".csv":
            ext = ".csv"
        out_file = op.abspath(name + ext)
        outputs["csv_file"] = out_file
        return outputs


class AddCSVRowInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    in_file = File(mandatory=True, desc="Input comma-separated value (CSV) files")
    _outputs = traits.Dict(traits.Any, value={}, usedefault=True)

    def __setattr__(self, key, value):
        if key not in self.copyable_trait_names():
            if not isdefined(value):
                super(AddCSVRowInputSpec, self).__setattr__(key, value)
            self._outputs[key] = value
        else:
            if key in self._outputs:
                self._outputs[key] = value
            super(AddCSVRowInputSpec, self).__setattr__(key, value)


class AddCSVRowOutputSpec(TraitedSpec):
    csv_file = File(desc="Output CSV file containing rows ")


class AddCSVRow(BaseInterface):
    """
    Simple interface to add an extra row to a CSV file.

    .. note:: Requires `pandas <http://pandas.pydata.org/>`_

    .. warning:: Multi-platform thread-safe execution is possible with
        `lockfile <https://pythonhosted.org/lockfile/lockfile.html>`_. Please
        recall that (1) this module is alpha software; and (2) it should be
        installed for thread-safe writing.
        If lockfile is not installed, then the interface is not thread-safe.


    Example
    -------
    >>> from nipype.algorithms import misc
    >>> addrow = misc.AddCSVRow()
    >>> addrow.inputs.in_file = 'scores.csv'
    >>> addrow.inputs.si = 0.74
    >>> addrow.inputs.di = 0.93
    >>> addrow.inputs.subject_id = 'S400'
    >>> addrow.inputs.list_of_values = [ 0.4, 0.7, 0.3 ]
    >>> addrow.run() # doctest: +SKIP

    """

    input_spec = AddCSVRowInputSpec
    output_spec = AddCSVRowOutputSpec

    def __init__(self, infields=None, force_run=True, **kwargs):
        super(AddCSVRow, self).__init__(**kwargs)
        undefined_traits = {}
        self._infields = infields
        self._have_lock = False
        self._lock = None

        if infields:
            for key in infields:
                self.inputs.add_trait(key, traits.Any)
                self.inputs._outputs[key] = Undefined
                undefined_traits[key] = Undefined
        self.inputs.trait_set(trait_change_notify=False, **undefined_traits)

        if force_run:
            self._always_run = True

    def _run_interface(self, runtime):
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "This interface requires pandas " "(http://pandas.pydata.org/) to run."
            ) from e

        try:
            from filelock import SoftFileLock

            self._have_lock = True
        except ImportError:
            from warnings import warn

            warn(
                (
                    "Python module filelock was not found: AddCSVRow will not be"
                    " thread-safe in multi-processor execution"
                )
            )

        input_dict = {}
        for key, val in list(self.inputs._outputs.items()):
            # expand lists to several columns
            if key == "trait_added" and val in self.inputs.copyable_trait_names():
                continue

            if isinstance(val, list):
                for i, v in enumerate(val):
                    input_dict["%s_%d" % (key, i)] = v
            else:
                input_dict[key] = val

        df = pd.DataFrame([input_dict])

        if self._have_lock:
            self._lock = SoftFileLock("%s.lock" % self.inputs.in_file)

            # Acquire lock
            self._lock.acquire()

        if op.exists(self.inputs.in_file):
            formerdf = pd.read_csv(self.inputs.in_file, index_col=0)
            df = pd.concat([formerdf, df], ignore_index=True)

        with open(self.inputs.in_file, "w") as f:
            df.to_csv(f)

        if self._have_lock:
            self._lock.release()

        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["csv_file"] = self.inputs.in_file
        return outputs

    def _outputs(self):
        return self._add_output_traits(super(AddCSVRow, self)._outputs())

    def _add_output_traits(self, base):
        return base


class CalculateNormalizedMomentsInputSpec(TraitedSpec):
    timeseries_file = File(
        exists=True,
        mandatory=True,
        desc="Text file with timeseries in columns and timepoints in rows,\
        whitespace separated",
    )
    moment = traits.Int(
        mandatory=True,
        desc="Define which moment should be calculated, 3 for skewness, 4 for\
        kurtosis.",
    )


class CalculateNormalizedMomentsOutputSpec(TraitedSpec):
    moments = traits.List(traits.Float(), desc="Moments")


class CalculateNormalizedMoments(BaseInterface):
    """
    Calculates moments of timeseries.

    Example
    -------
    >>> from nipype.algorithms import misc
    >>> skew = misc.CalculateNormalizedMoments()
    >>> skew.inputs.moment = 3
    >>> skew.inputs.timeseries_file = 'timeseries.txt'
    >>> skew.run() # doctest: +SKIP

    """

    input_spec = CalculateNormalizedMomentsInputSpec
    output_spec = CalculateNormalizedMomentsOutputSpec

    def _run_interface(self, runtime):
        self._moments = calc_moments(self.inputs.timeseries_file, self.inputs.moment)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["skewness"] = self._moments
        return outputs


def calc_moments(timeseries_file, moment):
    """Returns nth moment (3 for skewness, 4 for kurtosis) of timeseries
    (list of values; one per timeseries).

    Keyword arguments:
    timeseries_file -- text file with white space separated timepoints in rows

    """
    import scipy.stats as stats

    timeseries = np.genfromtxt(timeseries_file)

    m2 = stats.moment(timeseries, 2, axis=0)
    m3 = stats.moment(timeseries, moment, axis=0)
    zero = m2 == 0
    return np.where(zero, 0, m3 / m2 ** (moment / 2.0))


class AddNoiseInputSpec(TraitedSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        desc="input image that will be corrupted with noise",
    )
    in_mask = File(
        exists=True,
        desc=("input mask, voxels outside this mask " "will be considered background"),
    )
    snr = traits.Float(10.0, desc="desired output SNR in dB", usedefault=True)
    dist = traits.Enum(
        "normal",
        "rician",
        usedefault=True,
        mandatory=True,
        desc=("desired noise distribution"),
    )
    bg_dist = traits.Enum(
        "normal",
        "rayleigh",
        usedefault=True,
        mandatory=True,
        desc=("desired noise distribution, currently " "only normal is implemented"),
    )
    out_file = File(desc="desired output filename")


class AddNoiseOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="corrupted image")


class AddNoise(BaseInterface):
    """
    Corrupts with noise the input image.


    Example
    -------
    >>> from nipype.algorithms.misc import AddNoise
    >>> noise = AddNoise()
    >>> noise.inputs.in_file = 'T1.nii'
    >>> noise.inputs.in_mask = 'mask.nii'
    >>> noise.snr = 30.0
    >>> noise.run() # doctest: +SKIP

    """

    input_spec = AddNoiseInputSpec
    output_spec = AddNoiseOutputSpec

    def _run_interface(self, runtime):
        in_image = nb.load(self.inputs.in_file)
        in_data = in_image.get_fdata()
        snr = self.inputs.snr

        if isdefined(self.inputs.in_mask):
            in_mask = np.asanyarray(nb.load(self.inputs.in_mask).dataobj)
        else:
            in_mask = np.ones_like(in_data)

        result = self.gen_noise(
            in_data,
            mask=in_mask,
            snr_db=snr,
            dist=self.inputs.dist,
            bg_dist=self.inputs.bg_dist,
        )
        res_im = nb.Nifti1Image(result, in_image.affine, in_image.header)
        res_im.to_filename(self._gen_output_filename())
        return runtime

    def _gen_output_filename(self):
        if not isdefined(self.inputs.out_file):
            _, base, ext = split_filename(self.inputs.in_file)
            out_file = os.path.abspath("%s_SNR%03.2f%s" % (base, self.inputs.snr, ext))
        else:
            out_file = self.inputs.out_file

        return out_file

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = self._gen_output_filename()
        return outputs

    def gen_noise(self, image, mask=None, snr_db=10.0, dist="normal", bg_dist="normal"):
        """
        Generates a copy of an image with a certain amount of
        added gaussian noise (rayleigh for background in mask)
        """
        from math import sqrt

        snr = sqrt(np.power(10.0, snr_db / 10.0))

        if mask is None:
            mask = np.ones_like(image)
        else:
            mask[mask > 0] = 1
            mask[mask < 1] = 0

            if mask.ndim < image.ndim:
                mask = np.rollaxis(np.array([mask] * image.shape[3]), 0, 4)

        signal = image[mask > 0].reshape(-1)

        if dist == "normal":
            signal = signal - signal.mean()
            sigma_n = sqrt(signal.var() / snr)
            noise = np.random.normal(size=image.shape, scale=sigma_n)

            if (np.any(mask == 0)) and (bg_dist == "rayleigh"):
                bg_noise = np.random.rayleigh(size=image.shape, scale=sigma_n)
                noise[mask == 0] = bg_noise[mask == 0]

            im_noise = image + noise

        elif dist == "rician":
            sigma_n = signal.mean() / snr
            n_1 = np.random.normal(size=image.shape, scale=sigma_n)
            n_2 = np.random.normal(size=image.shape, scale=sigma_n)
            stde_1 = n_1 / sqrt(2.0)
            stde_2 = n_2 / sqrt(2.0)
            im_noise = np.sqrt((image + stde_1) ** 2 + (stde_2) ** 2)
        else:
            raise NotImplementedError(
                ("Only normal and rician distributions " "are supported")
            )

        return im_noise


class NormalizeProbabilityMapSetInputSpec(TraitedSpec):
    in_files = InputMultiPath(
        File(exists=True, mandatory=True, desc="The tpms to be normalized")
    )
    in_mask = File(exists=True, desc="Masked voxels must sum up 1.0, 0.0 otherwise.")


class NormalizeProbabilityMapSetOutputSpec(TraitedSpec):
    out_files = OutputMultiPath(File(exists=True), desc="normalized maps")


class NormalizeProbabilityMapSet(BaseInterface):
    """
    Returns the input tissue probability maps (tpms, aka volume fractions).

    The tissue probability maps are normalized to sum up 1.0 at each voxel within the mask.

    .. note:: Please recall this is not a spatial normalization algorithm


    Example
    -------
    >>> from nipype.algorithms import misc
    >>> normalize = misc.NormalizeProbabilityMapSet()
    >>> normalize.inputs.in_files = [ 'tpm_00.nii.gz', 'tpm_01.nii.gz', \
'tpm_02.nii.gz' ]
    >>> normalize.inputs.in_mask = 'tpms_msk.nii.gz'
    >>> normalize.run() # doctest: +SKIP

    """

    input_spec = NormalizeProbabilityMapSetInputSpec
    output_spec = NormalizeProbabilityMapSetOutputSpec

    def _run_interface(self, runtime):
        mask = None

        if isdefined(self.inputs.in_mask):
            mask = self.inputs.in_mask

        self._out_filenames = normalize_tpms(self.inputs.in_files, mask)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_files"] = self._out_filenames
        return outputs


class SplitROIsInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True, desc="file to be split")
    in_mask = File(exists=True, desc="only process files inside mask")
    roi_size = traits.Tuple(traits.Int, traits.Int, traits.Int, desc="desired ROI size")


class SplitROIsOutputSpec(TraitedSpec):
    out_files = OutputMultiPath(File(exists=True), desc="the resulting ROIs")
    out_masks = OutputMultiPath(
        File(exists=True), desc="a mask indicating valid values"
    )
    out_index = OutputMultiPath(
        File(exists=True), desc="arrays keeping original locations"
    )


class SplitROIs(BaseInterface):
    """
    Splits a 3D image in small chunks to enable parallel processing.

    ROIs keep time series structure in 4D images.

    Example
    -------
    >>> from nipype.algorithms import misc
    >>> rois = misc.SplitROIs()
    >>> rois.inputs.in_file = 'diffusion.nii'
    >>> rois.inputs.in_mask = 'mask.nii'
    >>> rois.run() # doctest: +SKIP

    """

    input_spec = SplitROIsInputSpec
    output_spec = SplitROIsOutputSpec

    def _run_interface(self, runtime):
        mask = None
        roisize = None
        self._outnames = {}

        if isdefined(self.inputs.in_mask):
            mask = self.inputs.in_mask
        if isdefined(self.inputs.roi_size):
            roisize = self.inputs.roi_size

        res = split_rois(self.inputs.in_file, mask, roisize)
        self._outnames["out_files"] = res[0]
        self._outnames["out_masks"] = res[1]
        self._outnames["out_index"] = res[2]
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for k, v in list(self._outnames.items()):
            outputs[k] = v
        return outputs


class MergeROIsInputSpec(TraitedSpec):
    in_files = InputMultiPath(
        File(exists=True, mandatory=True, desc="files to be re-merged")
    )
    in_index = InputMultiPath(
        File(exists=True, mandatory=True), desc="array keeping original locations"
    )
    in_reference = File(exists=True, desc="reference file")


class MergeROIsOutputSpec(TraitedSpec):
    merged_file = File(exists=True, desc="the recomposed file")


class MergeROIs(BaseInterface):
    """
    Splits a 3D image in small chunks to enable parallel processing.

    ROIs keep time series structure in 4D images.

    Example
    -------
    >>> from nipype.algorithms import misc
    >>> rois = misc.MergeROIs()
    >>> rois.inputs.in_files = ['roi%02d.nii' % i for i in range(1, 6)]
    >>> rois.inputs.in_reference = 'mask.nii'
    >>> rois.inputs.in_index = ['roi%02d_idx.npz' % i for i in range(1, 6)]
    >>> rois.run() # doctest: +SKIP

    """

    input_spec = MergeROIsInputSpec
    output_spec = MergeROIsOutputSpec

    def _run_interface(self, runtime):
        res = merge_rois(
            self.inputs.in_files, self.inputs.in_index, self.inputs.in_reference
        )
        self._merged = res
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["merged_file"] = self._merged
        return outputs


def normalize_tpms(in_files, in_mask=None, out_files=None):
    """
    Returns the input tissue probability maps (tpms, aka volume fractions)
    normalized to sum up 1.0 at each voxel within the mask.
    """
    import nibabel as nb
    import numpy as np
    import os.path as op

    in_files = np.atleast_1d(in_files).tolist()

    if out_files is None:
        out_files = []

    if len(out_files) != len(in_files):
        for i, finname in enumerate(in_files):
            fname, fext = op.splitext(op.basename(finname))
            if fext == ".gz":
                fname, fext2 = op.splitext(fname)
                fext = fext2 + fext

            out_file = op.abspath("%s_norm_%02d%s" % (fname, i, fext))
            out_files += [out_file]

    imgs = [nb.load(fim) for fim in in_files]

    if len(in_files) == 1:
        img_data = imgs[0].get_fdata(dtype=np.float32)
        img_data[img_data > 0.0] = 1.0
        hdr = imgs[0].header.copy()
        hdr.set_data_dtype(np.float32)
        nb.save(nb.Nifti1Image(img_data, imgs[0].affine, hdr), out_files[0])
        return out_files[0]

    img_data = np.stack(
        [im.get_fdata(caching="unchanged", dtype=np.float32) for im in imgs]
    )
    # img_data[img_data>1.0] = 1.0
    img_data[img_data < 0.0] = 0.0
    weights = np.sum(img_data, axis=0)

    msk = np.ones(imgs[0].shape)
    msk[weights <= 0] = 0

    if in_mask is not None:
        msk = np.asanyarray(nb.load(in_mask).dataobj)
        msk[msk <= 0] = 0
        msk[msk > 0] = 1

    msk = np.ma.masked_equal(msk, 0)

    for i, out_file in enumerate(out_files):
        data = np.ma.masked_equal(img_data[i], 0)
        probmap = data / weights
        hdr = imgs[i].header.copy()
        hdr.set_data_dtype("float32")
        nb.save(
            nb.Nifti1Image(probmap.astype(np.float32), imgs[i].affine, hdr), out_file
        )

    return out_files


def split_rois(in_file, mask=None, roishape=None):
    """
    Splits an image in ROIs for parallel processing
    """
    import nibabel as nb
    import numpy as np
    from math import sqrt, ceil
    import os.path as op

    if roishape is None:
        roishape = (10, 10, 1)

    im = nb.load(in_file)
    imshape = im.shape
    dshape = imshape[:3]
    nvols = imshape[-1]
    roisize = roishape[0] * roishape[1] * roishape[2]
    droishape = (roishape[0], roishape[1], roishape[2], nvols)

    if mask is not None:
        mask = np.asanyarray(nb.load(mask).dataobj)
        mask[mask > 0] = 1
        mask[mask < 1] = 0
    else:
        mask = np.ones(dshape)

    mask = mask.reshape(-1).astype(np.uint8)
    nzels = np.nonzero(mask)
    els = np.sum(mask)
    nrois = int(ceil(els / float(roisize)))

    data = np.asanyarray(im.dataobj).reshape((mask.size, -1))
    data = np.squeeze(data.take(nzels, axis=0))
    nvols = data.shape[-1]

    roidefname = op.abspath("onesmask.nii.gz")
    nb.Nifti1Image(np.ones(roishape, dtype=np.uint8), None, None).to_filename(
        roidefname
    )

    out_files = []
    out_mask = []
    out_idxs = []

    for i in range(nrois):
        first = i * roisize
        last = (i + 1) * roisize
        fill = 0

        if last > els:
            fill = last - els
            last = els

        droi = data[first:last, ...]
        iname = op.abspath("roi%010d_idx" % i)
        out_idxs.append(iname + ".npz")
        np.savez(iname, (nzels[0][first:last],))

        if fill > 0:
            droi = np.vstack(
                (droi, np.zeros((int(fill), int(nvols)), dtype=np.float32))
            )
            partialmsk = np.ones((roisize,), dtype=np.uint8)
            partialmsk[-int(fill) :] = 0
            partname = op.abspath("partialmask.nii.gz")
            nb.Nifti1Image(partialmsk.reshape(roishape), None, None).to_filename(
                partname
            )
            out_mask.append(partname)
        else:
            out_mask.append(roidefname)

        fname = op.abspath("roi%010d.nii.gz" % i)
        nb.Nifti1Image(droi.reshape(droishape), None, None).to_filename(fname)
        out_files.append(fname)
    return out_files, out_mask, out_idxs


def merge_rois(in_files, in_idxs, in_ref, dtype=None, out_file=None):
    """
    Re-builds an image resulting from a parallelized processing
    """
    import nibabel as nb
    import numpy as np
    import os.path as op
    import subprocess as sp

    if out_file is None:
        out_file = op.abspath("merged.nii.gz")

    if dtype is None:
        dtype = np.float32

    # if file is compressed, uncompress using os
    # to avoid memory errors
    if op.splitext(in_ref)[1] == ".gz":
        try:
            iflogger.info("uncompress %s", in_ref)
            sp.check_call(["gunzip", in_ref], stdout=sp.PIPE, shell=True)
            in_ref = op.splitext(in_ref)[0]
        except:
            pass

    ref = nb.load(in_ref)
    aff = ref.affine
    hdr = ref.header.copy()
    rsh = ref.shape
    del ref
    npix = rsh[0] * rsh[1] * rsh[2]
    fcimg = nb.load(in_files[0])

    if len(fcimg.shape) == 4:
        ndirs = fcimg.shape[-1]
    else:
        ndirs = 1
    newshape = (rsh[0], rsh[1], rsh[2], ndirs)
    hdr.set_data_dtype(dtype)
    hdr.set_xyzt_units("mm", "sec")

    if ndirs < 300:
        data = np.zeros((npix, ndirs), dtype=dtype)
        for cname, iname in zip(in_files, in_idxs):
            f = np.load(iname)
            idxs = np.squeeze(f["arr_0"])
            cdata = np.asanyarray(nb.load(cname).dataobj).reshape(-1, ndirs)
            nels = len(idxs)
            idata = (idxs,)
            try:
                data[idata, ...] = cdata[0:nels, ...]
            except:
                print(
                    (
                        "Consistency between indexes and chunks was "
                        "lost: data=%s, chunk=%s"
                    )
                    % (str(data.shape), str(cdata.shape))
                )
                raise

        nb.Nifti1Image(data.reshape(newshape), aff, hdr).to_filename(out_file)

    else:
        hdr.set_data_shape(rsh[:3])
        nii = []
        for d in range(ndirs):
            fname = op.abspath("vol%06d.nii" % d)
            nb.Nifti1Image(np.zeros(rsh[:3]), aff, hdr).to_filename(fname)
            nii.append(fname)

        for cname, iname in zip(in_files, in_idxs):
            f = np.load(iname)
            idxs = np.squeeze(f["arr_0"])

            for d, fname in enumerate(nii):
                data = np.asanyarray(nb.load(fname).dataobj).reshape(-1)
                cdata = nb.load(cname).dataobj[..., d].reshape(-1)
                nels = len(idxs)
                idata = (idxs,)
                data[idata] = cdata[0:nels]
                nb.Nifti1Image(data.reshape(rsh[:3]), aff, hdr).to_filename(fname)

        imgs = [nb.load(im) for im in nii]
        allim = nb.concat_images(imgs)
        allim.to_filename(out_file)

    return out_file


class CalculateMedianInputSpec(BaseInterfaceInputSpec):
    in_files = InputMultiPath(
        File(
            exists=True,
            mandatory=True,
            desc="One or more realigned Nifti 4D timeseries",
        )
    )
    median_file = traits.Str(desc="Filename prefix to store median images")
    median_per_file = traits.Bool(
        False, usedefault=True, desc="Calculate a median file for each Nifti"
    )


class CalculateMedianOutputSpec(TraitedSpec):
    median_files = OutputMultiPath(File(exists=True), desc="One or more median images")


class CalculateMedian(BaseInterface):
    """
    Computes an average of the median across one or more 4D Nifti timeseries

    Example
    -------
    >>> from nipype.algorithms.misc import CalculateMedian
    >>> mean = CalculateMedian()
    >>> mean.inputs.in_files = 'functional.nii'
    >>> mean.run() # doctest: +SKIP

    """

    input_spec = CalculateMedianInputSpec
    output_spec = CalculateMedianOutputSpec

    def __init__(self, *args, **kwargs):
        super(CalculateMedian, self).__init__(*args, **kwargs)
        self._median_files = []

    def _gen_fname(self, suffix, idx=None, ext=None):
        if idx:
            in_file = self.inputs.in_files[idx]
        else:
            if isinstance(self.inputs.in_files, list):
                in_file = self.inputs.in_files[0]
            else:
                in_file = self.inputs.in_files
        fname, in_ext = op.splitext(op.basename(in_file))
        if in_ext == ".gz":
            fname, in_ext2 = op.splitext(fname)
            in_ext = in_ext2 + in_ext
        if ext is None:
            ext = in_ext
        if ext.startswith("."):
            ext = ext[1:]
        if self.inputs.median_file:
            outname = self.inputs.median_file
        else:
            outname = "{}_{}".format(fname, suffix)
        if idx:
            outname += str(idx)
        return op.abspath("{}.{}".format(outname, ext))

    def _run_interface(self, runtime):
        total = None
        self._median_files = []
        for idx, fname in enumerate(ensure_list(self.inputs.in_files)):
            img = nb.load(fname)
            data = np.median(img.get_fdata(), axis=3)
            if self.inputs.median_per_file:
                self._median_files.append(self._write_nifti(img, data, idx))
            else:
                if total is None:
                    total = data
                else:
                    total += data
        if not self.inputs.median_per_file:
            self._median_files.append(self._write_nifti(img, total, idx))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["median_files"] = self._median_files
        return outputs

    def _write_nifti(self, img, data, idx, suffix="median"):
        if self.inputs.median_per_file:
            median_img = nb.Nifti1Image(data, img.affine, img.header)
            filename = self._gen_fname(suffix, idx=idx)
        else:
            median_img = nb.Nifti1Image(data / (idx + 1), img.affine, img.header)
            filename = self._gen_fname(suffix)
        median_img.to_filename(filename)
        return filename


# Deprecated interfaces ------------------------------------------------------


class Distance(nam.Distance):
    """Calculates distance between two volumes.

    .. deprecated:: 0.10.0
       Use :py:class:`nipype.algorithms.metrics.Distance` instead.
    """

    def __init__(self, **inputs):
        super(nam.Distance, self).__init__(**inputs)
        warnings.warn(
            (
                "This interface has been deprecated since 0.10.0,"
                " please use nipype.algorithms.metrics.Distance"
            ),
            DeprecationWarning,
        )


class Overlap(nam.Overlap):
    """Calculates various overlap measures between two maps.

    .. deprecated:: 0.10.0
       Use :py:class:`nipype.algorithms.metrics.Overlap` instead.
    """

    def __init__(self, **inputs):
        super(nam.Overlap, self).__init__(**inputs)
        warnings.warn(
            (
                "This interface has been deprecated since 0.10.0,"
                " please use nipype.algorithms.metrics.Overlap"
            ),
            DeprecationWarning,
        )


class FuzzyOverlap(nam.FuzzyOverlap):
    """Calculates various overlap measures between two maps, using a fuzzy
    definition.

    .. deprecated:: 0.10.0
       Use :py:class:`nipype.algorithms.metrics.FuzzyOverlap` instead.
    """

    def __init__(self, **inputs):
        super(nam.FuzzyOverlap, self).__init__(**inputs)
        warnings.warn(
            (
                "This interface has been deprecated since 0.10.0,"
                " please use nipype.algorithms.metrics.FuzzyOverlap"
            ),
            DeprecationWarning,
        )


class TSNR(confounds.TSNR):
    """
    .. deprecated:: 0.12.1
       Use :py:class:`nipype.algorithms.confounds.TSNR` instead
    """

    def __init__(self, **inputs):
        super(confounds.TSNR, self).__init__(**inputs)
        warnings.warn(
            (
                "This interface has been moved since 0.12.0,"
                " please use nipype.algorithms.confounds.TSNR"
            ),
            UserWarning,
        )
