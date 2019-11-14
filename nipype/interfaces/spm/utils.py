# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import numpy as np

from ...utils.filemanip import (
    split_filename,
    fname_presuffix,
    ensure_list,
    simplify_list,
)
from ..base import TraitedSpec, isdefined, File, traits, OutputMultiPath, InputMultiPath
from .base import SPMCommandInputSpec, SPMCommand, scans_for_fnames, scans_for_fname


class Analyze2niiInputSpec(SPMCommandInputSpec):
    analyze_file = File(exists=True, mandatory=True)


class Analyze2niiOutputSpec(SPMCommandInputSpec):
    nifti_file = File(exists=True)


class Analyze2nii(SPMCommand):

    input_spec = Analyze2niiInputSpec
    output_spec = Analyze2niiOutputSpec

    def _make_matlab_command(self, _):
        script = "V = spm_vol('%s');\n" % self.inputs.analyze_file
        _, name, _ = split_filename(self.inputs.analyze_file)
        self.output_name = os.path.join(os.getcwd(), name + ".nii")
        script += "[Y, XYZ] = spm_read_vols(V);\n"
        script += "V.fname = '%s';\n" % self.output_name
        script += "spm_write_vol(V, Y);\n"

        return script

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["nifti_file"] = self.output_name
        return outputs


class CalcCoregAffineInputSpec(SPMCommandInputSpec):
    target = File(
        exists=True, mandatory=True, desc="target for generating affine transform"
    )
    moving = File(
        exists=True,
        mandatory=True,
        copyfile=False,
        desc=("volume transform can be applied to register with " "target"),
    )
    mat = File(desc="Filename used to store affine matrix")
    invmat = File(desc="Filename used to store inverse affine matrix")


class CalcCoregAffineOutputSpec(TraitedSpec):
    mat = File(exists=True, desc="Matlab file holding transform")
    invmat = File(desc="Matlab file holding inverse transform")


class CalcCoregAffine(SPMCommand):
    """ Uses SPM (spm_coreg) to calculate the transform mapping
    moving to target. Saves Transform in mat (matlab binary file)
    Also saves inverse transform

    Examples
    --------

    >>> import nipype.interfaces.spm.utils as spmu
    >>> coreg = spmu.CalcCoregAffine(matlab_cmd='matlab-spm8')
    >>> coreg.inputs.target = 'structural.nii'
    >>> coreg.inputs.moving = 'functional.nii'
    >>> coreg.inputs.mat = 'func_to_struct.mat'
    >>> coreg.run() # doctest: +SKIP

    .. note::

     * the output file mat is saves as a matlab binary file
     * calculating the transforms does NOT change either input image
       it does not **move** the moving image, only calculates the transform
       that can be used to move it
    """

    input_spec = CalcCoregAffineInputSpec
    output_spec = CalcCoregAffineOutputSpec

    def _make_inv_file(self):
        """ makes filename to hold inverse transform if not specified"""
        invmat = fname_presuffix(self.inputs.mat, prefix="inverse_")
        return invmat

    def _make_mat_file(self):
        """ makes name for matfile if doesn exist"""
        pth, mv, _ = split_filename(self.inputs.moving)
        _, tgt, _ = split_filename(self.inputs.target)
        mat = os.path.join(pth, "%s_to_%s.mat" % (mv, tgt))
        return mat

    def _make_matlab_command(self, _):
        """checks for SPM, generates script"""
        if not isdefined(self.inputs.mat):
            self.inputs.mat = self._make_mat_file()
        if not isdefined(self.inputs.invmat):
            self.inputs.invmat = self._make_inv_file()
        script = """
        target = '%s';
        moving = '%s';
        targetv = spm_vol(target);
        movingv = spm_vol(moving);
        x = spm_coreg(targetv, movingv);
        M = spm_matrix(x);
        save('%s' , 'M' );
        M = inv(M);
        save('%s','M')
        """ % (
            self.inputs.target,
            self.inputs.moving,
            self.inputs.mat,
            self.inputs.invmat,
        )
        return script

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["mat"] = os.path.abspath(self.inputs.mat)
        outputs["invmat"] = os.path.abspath(self.inputs.invmat)
        return outputs


class ApplyTransformInputSpec(SPMCommandInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        copyfile=True,
        desc="file to apply transform to, (only updates header)",
    )
    mat = File(exists=True, mandatory=True, desc="file holding transform to apply")
    out_file = File(desc="output file name for transformed data", genfile=True)


class ApplyTransformOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="Transformed image file")


class ApplyTransform(SPMCommand):
    """ Uses SPM to apply transform stored in a .mat file to given file

    Examples
    --------

    >>> import nipype.interfaces.spm.utils as spmu
    >>> applymat = spmu.ApplyTransform()
    >>> applymat.inputs.in_file = 'functional.nii'
    >>> applymat.inputs.mat = 'func_to_struct.mat'
    >>> applymat.run() # doctest: +SKIP

    """

    input_spec = ApplyTransformInputSpec
    output_spec = ApplyTransformOutputSpec

    def _make_matlab_command(self, _):
        """checks for SPM, generates script"""
        outputs = self._list_outputs()
        self.inputs.out_file = outputs["out_file"]
        script = """
        infile = '%s';
        outfile = '%s'
        transform = load('%s');

        V = spm_vol(infile);
        X = spm_read_vols(V);
        [p n e v] = spm_fileparts(V.fname);
        V.mat = transform.M * V.mat;
        V.fname = fullfile(outfile);
        spm_write_vol(V,X);

        """ % (
            self.inputs.in_file,
            self.inputs.out_file,
            self.inputs.mat,
        )
        # img_space = spm_get_space(infile);
        # spm_get_space(infile, transform.M * img_space);
        return script

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] = os.path.abspath(self._gen_outfilename())
        else:
            outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_trans.nii"


class ResliceInputSpec(SPMCommandInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        desc="file to apply transform to, (only updates header)",
    )
    space_defining = File(
        exists=True, mandatory=True, desc="Volume defining space to slice in_file into"
    )

    interp = traits.Range(
        low=0,
        high=7,
        usedefault=True,
        desc="degree of b-spline used for interpolation"
        "0 is nearest neighbor (default)",
    )

    out_file = File(desc="Optional file to save resliced volume")


class ResliceOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="resliced volume")


class Reslice(SPMCommand):
    """ uses  spm_reslice to resample in_file into space of space_defining"""

    input_spec = ResliceInputSpec
    output_spec = ResliceOutputSpec

    def _make_matlab_command(self, _):
        """ generates script"""
        if not isdefined(self.inputs.out_file):
            self.inputs.out_file = fname_presuffix(self.inputs.in_file, prefix="r")
        script = """
        flags.mean = 0;
        flags.which = 1;
        flags.mask = 0;
        flags.interp = %d;
        infiles = strvcat(\'%s\', \'%s\');
        invols = spm_vol(infiles);
        spm_reslice(invols, flags);
        """ % (
            self.inputs.interp,
            self.inputs.space_defining,
            self.inputs.in_file,
        )
        return script

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


class ApplyInverseDeformationInput(SPMCommandInputSpec):
    in_files = InputMultiPath(
        File(exists=True),
        mandatory=True,
        field="fnames",
        desc="Files on which deformation is applied",
    )
    target = File(
        exists=True, field="comp{1}.inv.space", desc="File defining target space"
    )
    deformation = File(
        exists=True,
        field="comp{1}.inv.comp{1}.sn2def.matname",
        desc="SN SPM deformation file",
        xor=["deformation_field"],
    )
    deformation_field = File(
        exists=True,
        field="comp{1}.inv.comp{1}.def",
        desc="SN SPM deformation file",
        xor=["deformation"],
    )
    interpolation = traits.Range(
        low=0, high=7, field="interp", desc="degree of b-spline used for interpolation"
    )

    bounding_box = traits.List(
        traits.Float(),
        field="comp{1}.inv.comp{1}.sn2def.bb",
        minlen=6,
        maxlen=6,
        desc="6-element list (opt)",
    )
    voxel_sizes = traits.List(
        traits.Float(),
        field="comp{1}.inv.comp{1}.sn2def.vox",
        minlen=3,
        maxlen=3,
        desc="3-element list (opt)",
    )


class ApplyInverseDeformationOutput(TraitedSpec):
    out_files = OutputMultiPath(File(exists=True), desc="Transformed files")


class ApplyInverseDeformation(SPMCommand):
    """ Uses spm to apply inverse deformation stored in a .mat file or a
    deformation field to a given file

    Examples
    --------

    >>> import nipype.interfaces.spm.utils as spmu
    >>> inv = spmu.ApplyInverseDeformation()
    >>> inv.inputs.in_files = 'functional.nii'
    >>> inv.inputs.deformation = 'struct_to_func.mat'
    >>> inv.inputs.target = 'structural.nii'
    >>> inv.run() # doctest: +SKIP
    """

    input_spec = ApplyInverseDeformationInput
    output_spec = ApplyInverseDeformationOutput

    _jobtype = "util"
    _jobname = "defs"

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt == "in_files":
            return scans_for_fnames(ensure_list(val))
        if opt == "target":
            return scans_for_fname(ensure_list(val))
        if opt == "deformation":
            return np.array([simplify_list(val)], dtype=object)
        if opt == "deformation_field":
            return np.array([simplify_list(val)], dtype=object)
        return val

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_files"] = []
        for filename in self.inputs.in_files:
            _, fname = os.path.split(filename)
            outputs["out_files"].append(os.path.realpath("w%s" % fname))
        return outputs


class ResliceToReferenceInput(SPMCommandInputSpec):
    in_files = InputMultiPath(
        File(exists=True),
        mandatory=True,
        field="fnames",
        desc="Files on which deformation is applied",
    )
    target = File(
        exists=True, field="comp{1}.id.space", desc="File defining target space"
    )
    interpolation = traits.Range(
        low=0, high=7, field="interp", desc="degree of b-spline used for interpolation"
    )

    bounding_box = traits.List(
        traits.Float(),
        field="comp{2}.idbbvox.bb",
        minlen=6,
        maxlen=6,
        desc="6-element list (opt)",
    )
    voxel_sizes = traits.List(
        traits.Float(),
        field="comp{2}.idbbvox.vox",
        minlen=3,
        maxlen=3,
        desc="3-element list (opt)",
    )


class ResliceToReferenceOutput(TraitedSpec):
    out_files = OutputMultiPath(File(exists=True), desc="Transformed files")


class ResliceToReference(SPMCommand):
    """Uses spm to reslice a volume to a target image space or to a provided
    voxel size and bounding box

    Examples
    --------

    >>> import nipype.interfaces.spm.utils as spmu
    >>> r2ref = spmu.ResliceToReference()
    >>> r2ref.inputs.in_files = 'functional.nii'
    >>> r2ref.inputs.target = 'structural.nii'
    >>> r2ref.run() # doctest: +SKIP
    """

    input_spec = ResliceToReferenceInput
    output_spec = ResliceToReferenceOutput

    _jobtype = "util"
    _jobname = "defs"

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt == "in_files":
            return scans_for_fnames(ensure_list(val))
        if opt == "target":
            return scans_for_fname(ensure_list(val))
        if opt == "deformation":
            return np.array([simplify_list(val)], dtype=object)
        if opt == "deformation_field":
            return np.array([simplify_list(val)], dtype=object)
        return val

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_files"] = []
        for filename in self.inputs.in_files:
            _, fname = os.path.split(filename)
            outputs["out_files"].append(os.path.realpath("w%s" % fname))
        return outputs


class DicomImportInputSpec(SPMCommandInputSpec):
    in_files = InputMultiPath(
        File(exists=True),
        mandatory=True,
        field="data",
        desc="dicom files to be converted",
    )
    output_dir_struct = traits.Enum(
        "flat",
        "series",
        "patname",
        "patid_date",
        "patid",
        "date_time",
        field="root",
        usedefault=True,
        desc="directory structure for the output.",
    )
    output_dir = traits.Str(
        "./converted_dicom", field="outdir", usedefault=True, desc="output directory."
    )
    format = traits.Enum(
        "nii", "img", field="convopts.format", usedefault=True, desc="output format."
    )
    icedims = traits.Bool(
        False,
        field="convopts.icedims",
        usedefault=True,
        desc=(
            "If image sorting fails, one can try using "
            "the additional SIEMENS ICEDims information "
            "to create unique filenames. Use this only if "
            "there would be multiple volumes with exactly "
            "the same file names."
        ),
    )


class DicomImportOutputSpec(TraitedSpec):
    out_files = OutputMultiPath(File(exists=True), desc="converted files")


class DicomImport(SPMCommand):
    """ Uses spm to convert DICOM files to nii or img+hdr.

    Examples
    --------

    >>> import nipype.interfaces.spm.utils as spmu
    >>> di = spmu.DicomImport()
    >>> di.inputs.in_files = ['functional_1.dcm', 'functional_2.dcm']
    >>> di.run() # doctest: +SKIP
    """

    input_spec = DicomImportInputSpec
    output_spec = DicomImportOutputSpec

    _jobtype = "util"
    _jobname = "dicom"

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt == "in_files":
            return np.array(val, dtype=object)
        if opt == "output_dir":
            return np.array([val], dtype=object)
        if opt == "output_dir":
            return os.path.abspath(val)
        if opt == "icedims":
            if val:
                return 1
            return 0
        return super(DicomImport, self)._format_arg(opt, spec, val)

    def _run_interface(self, runtime):
        od = os.path.abspath(self.inputs.output_dir)
        if not os.path.isdir(od):
            os.mkdir(od)
        return super(DicomImport, self)._run_interface(runtime)

    def _list_outputs(self):
        from glob import glob

        outputs = self._outputs().get()
        od = os.path.abspath(self.inputs.output_dir)

        ext = self.inputs.format
        if self.inputs.output_dir_struct == "flat":
            outputs["out_files"] = glob(os.path.join(od, "*.%s" % ext))
        elif self.inputs.output_dir_struct == "series":
            outputs["out_files"] = glob(
                os.path.join(od, os.path.join("*", "*.%s" % ext))
            )
        elif self.inputs.output_dir_struct in ["patid", "date_time", "patname"]:
            outputs["out_files"] = glob(
                os.path.join(od, os.path.join("*", "*", "*.%s" % ext))
            )
        elif self.inputs.output_dir_struct == "patid_date":
            outputs["out_files"] = glob(
                os.path.join(od, os.path.join("*", "*", "*", "*.%s" % ext))
            )
        return outputs
