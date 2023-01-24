# -*- coding: utf-8 -*-
"""dcmstack allows series of DICOM images to be stacked into multi-dimensional arrays."""

import os
from os import path as op
import string
import errno
from glob import glob

import nibabel as nb
import imghdr

from .base import (
    TraitedSpec,
    DynamicTraitedSpec,
    InputMultiPath,
    File,
    Directory,
    traits,
    BaseInterface,
    isdefined,
    Undefined,
)

have_dcmstack = True
try:
    import pydicom
    import dcmstack
    from dcmstack.dcmmeta import NiftiWrapper
except ImportError:
    have_dcmstack = False


def sanitize_path_comp(path_comp):
    result = []
    for char in path_comp:
        if char not in string.ascii_letters + string.digits + "-_.":
            result.append("_")
        else:
            result.append(char)
    return "".join(result)


class NiftiGeneratorBaseInputSpec(TraitedSpec):
    out_format = traits.Str(
        desc="String which can be formatted with "
        "meta data to create the output filename(s)"
    )
    out_ext = traits.Str(".nii.gz", usedefault=True, desc="Determines output file type")
    out_path = Directory(desc="output path, current working directory if not set")


class NiftiGeneratorBase(BaseInterface):
    """Base class for interfaces that produce Nifti files, potentially with
    embedded meta data."""

    def _get_out_path(self, meta, idx=None):
        """Return the output path for the generated Nifti."""
        if self.inputs.out_format:
            out_fmt = self.inputs.out_format
        else:
            # If no out_format is specified, use a sane default that will work
            # with the provided meta data.
            out_fmt = []
            if idx is not None:
                out_fmt.append("%03d" % idx)
            if "SeriesNumber" in meta:
                out_fmt.append("%(SeriesNumber)03d")
            if "ProtocolName" in meta:
                out_fmt.append("%(ProtocolName)s")
            elif "SeriesDescription" in meta:
                out_fmt.append("%(SeriesDescription)s")
            else:
                out_fmt.append("sequence")
            out_fmt = "-".join(out_fmt)
        out_fn = (out_fmt % meta) + self.inputs.out_ext
        out_fn = sanitize_path_comp(out_fn)

        out_path = os.getcwd()
        if isdefined(self.inputs.out_path):
            out_path = op.abspath(self.inputs.out_path)

            # now, mkdir -p $out_path
            try:
                os.makedirs(out_path)
            except OSError as exc:  # Python >2.5
                if exc.errno == errno.EEXIST and op.isdir(out_path):
                    pass
                else:
                    raise

        return op.join(out_path, out_fn)


class DcmStackInputSpec(NiftiGeneratorBaseInputSpec):
    dicom_files = traits.Either(
        InputMultiPath(File(exists=True)),
        Directory(exists=True),
        traits.Str(),
        mandatory=True,
    )
    embed_meta = traits.Bool(desc="Embed DICOM meta data into result")
    exclude_regexes = traits.List(
        desc="Meta data to exclude, suplementing " "any default exclude filters"
    )
    include_regexes = traits.List(
        desc="Meta data to include, overriding any " "exclude filters"
    )
    force_read = traits.Bool(
        True, usedefault=True, desc=("Force reading files without DICM marker")
    )


class DcmStackOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class DcmStack(NiftiGeneratorBase):
    """Create one Nifti file from a set of DICOM files. Can optionally embed
    meta data.

    Example
    -------

    >>> from nipype.interfaces.dcmstack import DcmStack
    >>> stacker = DcmStack()
    >>> stacker.inputs.dicom_files = 'path/to/series/'
    >>> stacker.run() # doctest: +SKIP
    >>> result.outputs.out_file # doctest: +SKIP
    '/path/to/cwd/sequence.nii.gz'
    """

    input_spec = DcmStackInputSpec
    output_spec = DcmStackOutputSpec

    def _get_filelist(self, trait_input):
        if isinstance(trait_input, (str, bytes)):
            if op.isdir(trait_input):
                return glob(op.join(trait_input, "*.dcm"))
            else:
                return glob(trait_input)

        return trait_input

    def _run_interface(self, runtime):
        src_paths = self._get_filelist(self.inputs.dicom_files)
        include_regexes = dcmstack.default_key_incl_res
        if isdefined(self.inputs.include_regexes):
            include_regexes += self.inputs.include_regexes
        exclude_regexes = dcmstack.default_key_excl_res
        if isdefined(self.inputs.exclude_regexes):
            exclude_regexes += self.inputs.exclude_regexes
        meta_filter = dcmstack.make_key_regex_filter(exclude_regexes, include_regexes)
        stack = dcmstack.DicomStack(meta_filter=meta_filter)
        for src_path in src_paths:
            if not imghdr.what(src_path) == "gif":
                src_dcm = pydicom.dcmread(src_path, force=self.inputs.force_read)
                stack.add_dcm(src_dcm)
        nii = stack.to_nifti(embed_meta=True)
        nw = NiftiWrapper(nii)
        self.out_path = self._get_out_path(
            nw.meta_ext.get_class_dict(("global", "const"))
        )
        if not self.inputs.embed_meta:
            nw.remove_extension()
        nb.save(nii, self.out_path)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = self.out_path
        return outputs


class GroupAndStackOutputSpec(TraitedSpec):
    out_list = traits.List(desc="List of output nifti files")


class GroupAndStack(DcmStack):
    """Create (potentially) multiple Nifti files for a set of DICOM files."""

    input_spec = DcmStackInputSpec
    output_spec = GroupAndStackOutputSpec

    def _run_interface(self, runtime):
        src_paths = self._get_filelist(self.inputs.dicom_files)
        stacks = dcmstack.parse_and_stack(src_paths)

        self.out_list = []
        for key, stack in list(stacks.items()):
            nw = NiftiWrapper(stack.to_nifti(embed_meta=True))
            const_meta = nw.meta_ext.get_class_dict(("global", "const"))
            out_path = self._get_out_path(const_meta)
            if not self.inputs.embed_meta:
                nw.remove_extension()
            nb.save(nw.nii_img, out_path)
            self.out_list.append(out_path)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_list"] = self.out_list
        return outputs


class LookupMetaInputSpec(TraitedSpec):
    in_file = File(mandatory=True, exists=True, desc="The input Nifti file")
    meta_keys = traits.Either(
        traits.List(),
        traits.Dict(),
        mandatory=True,
        desc=(
            "List of meta data keys to lookup, or a "
            "dict where keys specify the meta data "
            "keys to lookup and the values specify "
            "the output names"
        ),
    )


class LookupMeta(BaseInterface):
    """Lookup meta data values from a Nifti with embedded meta data.

    Example
    -------

    >>> from nipype.interfaces import dcmstack
    >>> lookup = dcmstack.LookupMeta()
    >>> lookup.inputs.in_file = 'functional.nii'
    >>> lookup.inputs.meta_keys = {'RepetitionTime' : 'TR', \
                                   'EchoTime' : 'TE'}
    >>> result = lookup.run() # doctest: +SKIP
    >>> result.outputs.TR # doctest: +SKIP
    9500.0
    >>> result.outputs.TE # doctest: +SKIP
    95.0
    """

    input_spec = LookupMetaInputSpec
    output_spec = DynamicTraitedSpec

    def _make_name_map(self):
        if isinstance(self.inputs.meta_keys, list):
            self._meta_keys = {}
            for key in self.inputs.meta_keys:
                self._meta_keys[key] = key
        else:
            self._meta_keys = self.inputs.meta_keys

    def _outputs(self):
        self._make_name_map()
        outputs = super(LookupMeta, self)._outputs()
        undefined_traits = {}
        for out_name in list(self._meta_keys.values()):
            outputs.add_trait(out_name, traits.Any)
            undefined_traits[out_name] = Undefined
        outputs.trait_set(trait_change_notify=False, **undefined_traits)
        # Not sure why this is needed
        for out_name in list(self._meta_keys.values()):
            _ = getattr(outputs, out_name)
        return outputs

    def _run_interface(self, runtime):
        # If the 'meta_keys' input is a list, convert it to a dict
        self._make_name_map()
        nw = NiftiWrapper.from_filename(self.inputs.in_file)
        self.result = {}
        for meta_key, out_name in list(self._meta_keys.items()):
            self.result[out_name] = nw.meta_ext.get_values(meta_key)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs.update(self.result)
        return outputs


class CopyMetaInputSpec(TraitedSpec):
    src_file = File(mandatory=True, exists=True)
    dest_file = File(mandatory=True, exists=True)
    include_classes = traits.List(
        desc="List of specific meta data "
        "classifications to include. If not "
        "specified include everything."
    )
    exclude_classes = traits.List(
        desc="List of meta data " "classifications to exclude"
    )


class CopyMetaOutputSpec(TraitedSpec):
    dest_file = File(exists=True)


class CopyMeta(BaseInterface):
    """Copy meta data from one Nifti file to another. Useful for preserving
    meta data after some processing steps."""

    input_spec = CopyMetaInputSpec
    output_spec = CopyMetaOutputSpec

    def _run_interface(self, runtime):
        src_nii = nb.load(self.inputs.src_file)
        src = NiftiWrapper(src_nii, make_empty=True)
        dest_nii = nb.load(self.inputs.dest_file)
        dest = NiftiWrapper(dest_nii, make_empty=True)
        classes = src.meta_ext.get_valid_classes()
        if self.inputs.include_classes:
            classes = [cls for cls in classes if cls in self.inputs.include_classes]
        if self.inputs.exclude_classes:
            classes = [cls for cls in classes if cls not in self.inputs.exclude_classes]

        for cls in classes:
            src_dict = src.meta_ext.get_class_dict(cls)
            dest_dict = dest.meta_ext.get_class_dict(cls)
            dest_dict.update(src_dict)
        # Update the shape and slice dimension to reflect the meta extension
        # update.
        dest.meta_ext.slice_dim = src.meta_ext.slice_dim
        dest.meta_ext.shape = src.meta_ext.shape

        self.out_path = op.join(os.getcwd(), op.basename(self.inputs.dest_file))
        dest.to_filename(self.out_path)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["dest_file"] = self.out_path
        return outputs


class MergeNiftiInputSpec(NiftiGeneratorBaseInputSpec):
    in_files = traits.List(mandatory=True, desc="List of Nifti files to merge")
    sort_order = traits.Either(
        traits.Str(),
        traits.List(),
        desc="One or more meta data keys to " "sort files by.",
    )
    merge_dim = traits.Int(
        desc="Dimension to merge along. If not "
        "specified, the last singular or "
        "non-existent dimension is used."
    )


class MergeNiftiOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="Merged Nifti file")


def make_key_func(meta_keys, index=None):
    def key_func(src_nii):
        result = [src_nii.get_meta(key, index) for key in meta_keys]
        return result

    return key_func


class MergeNifti(NiftiGeneratorBase):
    """Merge multiple Nifti files into one. Merges together meta data
    extensions as well."""

    input_spec = MergeNiftiInputSpec
    output_spec = MergeNiftiOutputSpec

    def _run_interface(self, runtime):
        niis = [nb.load(fn) for fn in self.inputs.in_files]
        nws = [NiftiWrapper(nii, make_empty=True) for nii in niis]
        if self.inputs.sort_order:
            sort_order = self.inputs.sort_order
            if isinstance(sort_order, (str, bytes)):
                sort_order = [sort_order]
            nws.sort(key=make_key_func(sort_order))
        if self.inputs.merge_dim == traits.Undefined:
            merge_dim = None
        else:
            merge_dim = self.inputs.merge_dim
        merged = NiftiWrapper.from_sequence(nws, merge_dim)
        const_meta = merged.meta_ext.get_class_dict(("global", "const"))
        self.out_path = self._get_out_path(const_meta)
        nb.save(merged.nii_img, self.out_path)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = self.out_path
        return outputs


class SplitNiftiInputSpec(NiftiGeneratorBaseInputSpec):
    in_file = File(exists=True, mandatory=True, desc="Nifti file to split")
    split_dim = traits.Int(
        desc="Dimension to split along. If not "
        "specified, the last dimension is used."
    )


class SplitNiftiOutputSpec(TraitedSpec):
    out_list = traits.List(File(exists=True), desc="Split Nifti files")


class SplitNifti(NiftiGeneratorBase):
    """
    Split one Nifti file into many along the specified dimension. Each
    result has an updated meta data extension as well.
    """

    input_spec = SplitNiftiInputSpec
    output_spec = SplitNiftiOutputSpec

    def _run_interface(self, runtime):
        self.out_list = []
        nii = nb.load(self.inputs.in_file)
        nw = NiftiWrapper(nii, make_empty=True)
        split_dim = None
        if self.inputs.split_dim == traits.Undefined:
            split_dim = None
        else:
            split_dim = self.inputs.split_dim
        for split_idx, split_nw in enumerate(nw.split(split_dim)):
            const_meta = split_nw.meta_ext.get_class_dict(("global", "const"))
            out_path = self._get_out_path(const_meta, idx=split_idx)
            nb.save(split_nw.nii_img, out_path)
            self.out_list.append(out_path)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_list"] = self.out_list
        return outputs
