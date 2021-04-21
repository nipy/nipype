# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Interfaces to assorted Freesurfer utility programs.
"""
import os
import re
import shutil

from ... import logging
from ...utils.filemanip import fname_presuffix, split_filename
from ..base import (
    TraitedSpec,
    Directory,
    File,
    traits,
    OutputMultiPath,
    isdefined,
    CommandLine,
    CommandLineInputSpec,
)
from .base import (
    FSCommand,
    FSTraitedSpec,
    FSSurfaceCommand,
    FSScriptCommand,
    FSScriptOutputSpec,
    FSTraitedSpecOpenMP,
    FSCommandOpenMP,
)

__docformat__ = "restructuredtext"

filemap = dict(
    cor="cor",
    mgh="mgh",
    mgz="mgz",
    minc="mnc",
    afni="brik",
    brik="brik",
    bshort="bshort",
    spm="img",
    analyze="img",
    analyze4d="img",
    bfloat="bfloat",
    nifti1="img",
    nii="nii",
    niigz="nii.gz",
    gii="gii",
)

filetypes = [
    "cor",
    "mgh",
    "mgz",
    "minc",
    "analyze",
    "analyze4d",
    "spm",
    "afni",
    "brik",
    "bshort",
    "bfloat",
    "sdt",
    "outline",
    "otl",
    "gdf",
    "nifti1",
    "nii",
    "niigz",
]
implicit_filetypes = ["gii"]

logger = logging.getLogger("nipype.interface")


def copy2subjdir(cls, in_file, folder=None, basename=None, subject_id=None):
    """Method to copy an input to the subjects directory"""
    # check that the input is defined
    if not isdefined(in_file):
        return in_file
    # check that subjects_dir is defined
    if isdefined(cls.inputs.subjects_dir):
        subjects_dir = cls.inputs.subjects_dir
    else:
        subjects_dir = os.getcwd()  # if not use cwd
    # check for subject_id
    if not subject_id:
        if isdefined(cls.inputs.subject_id):
            subject_id = cls.inputs.subject_id
        else:
            subject_id = "subject_id"  # default
    # check for basename
    if basename is None:
        basename = os.path.basename(in_file)
    # check which folder to put the file in
    if folder is not None:
        out_dir = os.path.join(subjects_dir, subject_id, folder)
    else:
        out_dir = os.path.join(subjects_dir, subject_id)
    # make the output folder if it does not exist
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    out_file = os.path.join(out_dir, basename)
    if not os.path.isfile(out_file):
        shutil.copy(in_file, out_file)
    return out_file


def createoutputdirs(outputs):
    """create all output directories. If not created, some freesurfer interfaces fail"""
    for output in list(outputs.values()):
        dirname = os.path.dirname(output)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)


class SampleToSurfaceInputSpec(FSTraitedSpec):

    source_file = File(
        exists=True,
        mandatory=True,
        argstr="--mov %s",
        desc="volume to sample values from",
    )
    reference_file = File(
        exists=True, argstr="--ref %s", desc="reference volume (default is orig.mgz)"
    )

    hemi = traits.Enum(
        "lh", "rh", mandatory=True, argstr="--hemi %s", desc="target hemisphere"
    )
    surface = traits.String(
        argstr="--surf %s", desc="target surface (default is white)"
    )

    reg_xors = ["reg_file", "reg_header", "mni152reg"]
    reg_file = File(
        exists=True,
        argstr="--reg %s",
        mandatory=True,
        xor=reg_xors,
        desc="source-to-reference registration file",
    )
    reg_header = traits.Bool(
        argstr="--regheader %s",
        requires=["subject_id"],
        mandatory=True,
        xor=reg_xors,
        desc="register based on header geometry",
    )
    mni152reg = traits.Bool(
        argstr="--mni152reg",
        mandatory=True,
        xor=reg_xors,
        desc="source volume is in MNI152 space",
    )

    apply_rot = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr="--rot %.3f %.3f %.3f",
        desc="rotation angles (in degrees) to apply to reg matrix",
    )
    apply_trans = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr="--trans %.3f %.3f %.3f",
        desc="translation (in mm) to apply to reg matrix",
    )
    override_reg_subj = traits.Bool(
        argstr="--srcsubject %s",
        requires=["subject_id"],
        desc="override the subject in the reg file header",
    )

    sampling_method = traits.Enum(
        "point",
        "max",
        "average",
        mandatory=True,
        argstr="%s",
        xor=["projection_stem"],
        requires=["sampling_range", "sampling_units"],
        desc="how to sample -- at a point or at the max or average over a range",
    )
    sampling_range = traits.Either(
        traits.Float,
        traits.Tuple(traits.Float, traits.Float, traits.Float),
        desc="sampling range - a point or a tuple of (min, max, step)",
    )
    sampling_units = traits.Enum(
        "mm", "frac", desc="sampling range type -- either 'mm' or 'frac'"
    )
    projection_stem = traits.String(
        mandatory=True,
        xor=["sampling_method"],
        desc="stem for precomputed linear estimates and volume fractions",
    )

    smooth_vol = traits.Float(
        argstr="--fwhm %.3f", desc="smooth input volume (mm fwhm)"
    )
    smooth_surf = traits.Float(
        argstr="--surf-fwhm %.3f", desc="smooth output surface (mm fwhm)"
    )

    interp_method = traits.Enum(
        "nearest", "trilinear", argstr="--interp %s", desc="interpolation method"
    )

    cortex_mask = traits.Bool(
        argstr="--cortex",
        xor=["mask_label"],
        desc="mask the target surface with hemi.cortex.label",
    )
    mask_label = File(
        exists=True,
        argstr="--mask %s",
        xor=["cortex_mask"],
        desc="label file to mask output with",
    )

    float2int_method = traits.Enum(
        "round",
        "tkregister",
        argstr="--float2int %s",
        desc="method to convert reg matrix values (default is round)",
    )
    fix_tk_reg = traits.Bool(
        argstr="--fixtkreg", desc="make reg matrix round-compatible"
    )

    subject_id = traits.String(desc="subject id")
    target_subject = traits.String(
        argstr="--trgsubject %s",
        desc="sample to surface of different subject than source",
    )
    surf_reg = traits.Either(
        traits.Bool,
        traits.Str(),
        argstr="--surfreg %s",
        requires=["target_subject"],
        desc="use surface registration to target subject",
    )
    ico_order = traits.Int(
        argstr="--icoorder %d",
        requires=["target_subject"],
        desc="icosahedron order when target_subject is 'ico'",
    )

    reshape = traits.Bool(
        argstr="--reshape",
        xor=["no_reshape"],
        desc="reshape surface vector to fit in non-mgh format",
    )
    no_reshape = traits.Bool(
        argstr="--noreshape",
        xor=["reshape"],
        desc="do not reshape surface vector (default)",
    )
    reshape_slices = traits.Int(
        argstr="--rf %d", desc="number of 'slices' for reshaping"
    )
    scale_input = traits.Float(
        argstr="--scale %.3f", desc="multiple all intensities by scale factor"
    )
    frame = traits.Int(argstr="--frame %d", desc="save only one frame (0-based)")

    out_file = File(argstr="--o %s", genfile=True, desc="surface file to write")
    out_type = traits.Enum(
        filetypes + implicit_filetypes, argstr="--out_type %s", desc="output file type"
    )
    hits_file = traits.Either(
        traits.Bool,
        File(exists=True),
        argstr="--srchit %s",
        desc="save image with number of hits at each voxel",
    )
    hits_type = traits.Enum(filetypes, argstr="--srchit_type", desc="hits file type")
    vox_file = traits.Either(
        traits.Bool,
        File,
        argstr="--nvox %s",
        desc="text file with the number of voxels intersecting the surface",
    )


class SampleToSurfaceOutputSpec(TraitedSpec):

    out_file = File(exists=True, desc="surface file")
    hits_file = File(exists=True, desc="image with number of hits at each voxel")
    vox_file = File(
        exists=True, desc="text file with the number of voxels intersecting the surface"
    )


class SampleToSurface(FSCommand):
    """Sample a volume to the cortical surface using Freesurfer's mri_vol2surf.

    You must supply a sampling method, range, and units.  You can project
    either a given distance (in mm) or a given fraction of the cortical
    thickness at that vertex along the surface normal from the target surface,
    and then set the value of that vertex to be either the value at that point
    or the average or maximum value found along the projection vector.

    By default, the surface will be saved as a vector with a length equal to the
    number of vertices on the target surface.  This is not a problem for Freesurfer
    programs, but if you intend to use the file with interfaces to another package,
    you must set the ``reshape`` input to True, which will factor the surface vector
    into a matrix with dimensions compatible with proper Nifti files.

    Examples
    --------

    >>> import nipype.interfaces.freesurfer as fs
    >>> sampler = fs.SampleToSurface(hemi="lh")
    >>> sampler.inputs.source_file = "cope1.nii.gz"
    >>> sampler.inputs.reg_file = "register.dat"
    >>> sampler.inputs.sampling_method = "average"
    >>> sampler.inputs.sampling_range = 1
    >>> sampler.inputs.sampling_units = "frac"
    >>> sampler.cmdline  # doctest: +ELLIPSIS
    'mri_vol2surf --hemi lh --o ...lh.cope1.mgz --reg register.dat --projfrac-avg 1.000 --mov cope1.nii.gz'
    >>> res = sampler.run() # doctest: +SKIP

    """

    _cmd = "mri_vol2surf"
    input_spec = SampleToSurfaceInputSpec
    output_spec = SampleToSurfaceOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "sampling_method":
            range = self.inputs.sampling_range
            units = self.inputs.sampling_units
            if units == "mm":
                units = "dist"
            if isinstance(range, tuple):
                range = "%.3f %.3f %.3f" % range
            else:
                range = "%.3f" % range
            method = dict(point="", max="-max", average="-avg")[value]
            return "--proj%s%s %s" % (units, method, range)

        if name == "reg_header":
            return spec.argstr % self.inputs.subject_id
        if name == "override_reg_subj":
            return spec.argstr % self.inputs.subject_id
        if name in ["hits_file", "vox_file"]:
            return spec.argstr % self._get_outfilename(name)
        if name == "out_type":
            if isdefined(self.inputs.out_file):
                _, base, ext = split_filename(self._get_outfilename())
                if ext != filemap[value]:
                    if ext in filemap.values():
                        raise ValueError(
                            "Cannot create {} file with extension "
                            "{}".format(value, ext)
                        )
                    else:
                        logger.warning(
                            "Creating %s file with extension %s: %s%s",
                            value,
                            ext,
                            base,
                            ext,
                        )

            if value in implicit_filetypes:
                return ""
        if name == "surf_reg":
            if value is True:
                return spec.argstr % "sphere.reg"

        return super(SampleToSurface, self)._format_arg(name, spec, value)

    def _get_outfilename(self, opt="out_file"):
        outfile = getattr(self.inputs, opt)
        if not isdefined(outfile) or isinstance(outfile, bool):
            if isdefined(self.inputs.out_type):
                if opt == "hits_file":
                    suffix = "_hits." + filemap[self.inputs.out_type]
                else:
                    suffix = "." + filemap[self.inputs.out_type]
            elif opt == "hits_file":
                suffix = "_hits.mgz"
            else:
                suffix = ".mgz"
            outfile = fname_presuffix(
                self.inputs.source_file,
                newpath=os.getcwd(),
                prefix=self.inputs.hemi + ".",
                suffix=suffix,
                use_ext=False,
            )
        return outfile

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self._get_outfilename())
        hitsfile = self.inputs.hits_file
        if isdefined(hitsfile):
            outputs["hits_file"] = hitsfile
            if isinstance(hitsfile, bool):
                hitsfile = self._get_outfilename("hits_file")
        voxfile = self.inputs.vox_file
        if isdefined(voxfile):
            if isinstance(voxfile, bool):
                voxfile = fname_presuffix(
                    self.inputs.source_file,
                    newpath=os.getcwd(),
                    prefix=self.inputs.hemi + ".",
                    suffix="_vox.txt",
                    use_ext=False,
                )
            outputs["vox_file"] = voxfile
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()[name]
        return None


class SurfaceSmoothInputSpec(FSTraitedSpec):

    in_file = File(mandatory=True, argstr="--sval %s", desc="source surface file")
    subject_id = traits.String(
        mandatory=True, argstr="--s %s", desc="subject id of surface file"
    )
    hemi = traits.Enum(
        "lh", "rh", argstr="--hemi %s", mandatory=True, desc="hemisphere to operate on"
    )
    fwhm = traits.Float(
        argstr="--fwhm %.4f",
        xor=["smooth_iters"],
        desc="effective FWHM of the smoothing process",
    )
    smooth_iters = traits.Int(
        argstr="--smooth %d", xor=["fwhm"], desc="iterations of the smoothing process"
    )
    cortex = traits.Bool(
        True,
        argstr="--cortex",
        usedefault=True,
        desc="only smooth within ``$hemi.cortex.label``",
    )
    reshape = traits.Bool(
        argstr="--reshape", desc="reshape surface vector to fit in non-mgh format"
    )
    out_file = File(argstr="--tval %s", genfile=True, desc="surface file to write")


class SurfaceSmoothOutputSpec(TraitedSpec):

    out_file = File(exists=True, desc="smoothed surface file")


class SurfaceSmooth(FSCommand):
    """Smooth a surface image with mri_surf2surf.

    The surface is smoothed by an interative process of averaging the
    value at each vertex with those of its adjacent neighbors. You may supply
    either the number of iterations to run or a desired effective FWHM of the
    smoothing process.  If the latter, the underlying program will calculate
    the correct number of iterations internally.

    See Also
    --------
    `nipype.interfaces.freesurfer.utils.SmoothTessellation`_ interface for
    smoothing a tessellated surface (e.g. in gifti or .stl)

    Examples
    --------
    >>> import nipype.interfaces.freesurfer as fs
    >>> smoother = fs.SurfaceSmooth()
    >>> smoother.inputs.in_file = "lh.cope1.mgz"
    >>> smoother.inputs.subject_id = "subj_1"
    >>> smoother.inputs.hemi = "lh"
    >>> smoother.inputs.fwhm = 5
    >>> smoother.cmdline # doctest: +ELLIPSIS
    'mri_surf2surf --cortex --fwhm 5.0000 --hemi lh --sval lh.cope1.mgz --tval ...lh.cope1_smooth5.mgz --s subj_1'
    >>> smoother.run() # doctest: +SKIP

    """

    _cmd = "mri_surf2surf"
    input_spec = SurfaceSmoothInputSpec
    output_spec = SurfaceSmoothOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = self.inputs.out_file
        if not isdefined(outputs["out_file"]):
            in_file = self.inputs.in_file
            if isdefined(self.inputs.fwhm):
                kernel = self.inputs.fwhm
            else:
                kernel = self.inputs.smooth_iters
            outputs["out_file"] = fname_presuffix(
                in_file, suffix="_smooth%d" % kernel, newpath=os.getcwd()
            )
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()[name]
        return None


class SurfaceTransformInputSpec(FSTraitedSpec):
    source_file = File(
        exists=True,
        mandatory=True,
        argstr="--sval %s",
        xor=["source_annot_file"],
        desc="surface file with source values",
    )
    source_annot_file = File(
        exists=True,
        mandatory=True,
        argstr="--sval-annot %s",
        xor=["source_file"],
        desc="surface annotation file",
    )
    source_subject = traits.String(
        mandatory=True, argstr="--srcsubject %s", desc="subject id for source surface"
    )
    hemi = traits.Enum(
        "lh", "rh", argstr="--hemi %s", mandatory=True, desc="hemisphere to transform"
    )
    target_subject = traits.String(
        mandatory=True, argstr="--trgsubject %s", desc="subject id of target surface"
    )
    target_ico_order = traits.Enum(
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        argstr="--trgicoorder %d",
        desc=("order of the icosahedron if " "target_subject is 'ico'"),
    )
    source_type = traits.Enum(
        filetypes,
        argstr="--sfmt %s",
        requires=["source_file"],
        desc="source file format",
    )
    target_type = traits.Enum(
        filetypes + implicit_filetypes, argstr="--tfmt %s", desc="output format"
    )
    reshape = traits.Bool(
        argstr="--reshape", desc="reshape output surface to conform with Nifti"
    )
    reshape_factor = traits.Int(
        argstr="--reshape-factor", desc="number of slices in reshaped image"
    )
    out_file = File(argstr="--tval %s", genfile=True, desc="surface file to write")


class SurfaceTransformOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="transformed surface file")


class SurfaceTransform(FSCommand):
    """Transform a surface file from one subject to another via a spherical registration.

    Both the source and target subject must reside in your Subjects Directory,
    and they must have been processed with recon-all, unless you are transforming
    to one of the icosahedron meshes.

    Examples
    --------

    >>> from nipype.interfaces.freesurfer import SurfaceTransform
    >>> sxfm = SurfaceTransform()
    >>> sxfm.inputs.source_file = "lh.cope1.nii.gz"
    >>> sxfm.inputs.source_subject = "my_subject"
    >>> sxfm.inputs.target_subject = "fsaverage"
    >>> sxfm.inputs.hemi = "lh"
    >>> sxfm.run() # doctest: +SKIP

    """

    _cmd = "mri_surf2surf"
    input_spec = SurfaceTransformInputSpec
    output_spec = SurfaceTransformOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "target_type":
            if isdefined(self.inputs.out_file):
                _, base, ext = split_filename(self._list_outputs()["out_file"])
                if ext != filemap[value]:
                    if ext in filemap.values():
                        raise ValueError(
                            "Cannot create {} file with extension "
                            "{}".format(value, ext)
                        )
                    else:
                        logger.warning(
                            "Creating %s file with extension %s: %s%s",
                            value,
                            ext,
                            base,
                            ext,
                        )
            if value in implicit_filetypes:
                return ""
        return super(SurfaceTransform, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = self.inputs.out_file
        if not isdefined(outputs["out_file"]):
            if isdefined(self.inputs.source_file):
                source = self.inputs.source_file
            else:
                source = self.inputs.source_annot_file

            # Some recon-all files don't have a proper extension (e.g. "lh.thickness")
            # so we have to account for that here
            bad_extensions = [
                ".%s" % e
                for e in [
                    "area",
                    "mid",
                    "pial",
                    "avg_curv",
                    "curv",
                    "inflated",
                    "jacobian_white",
                    "orig",
                    "nofix",
                    "smoothwm",
                    "crv",
                    "sphere",
                    "sulc",
                    "thickness",
                    "volume",
                    "white",
                ]
            ]
            use_ext = True
            if split_filename(source)[2] in bad_extensions:
                source = source + ".stripme"
                use_ext = False
            ext = ""
            if isdefined(self.inputs.target_type):
                ext = "." + filemap[self.inputs.target_type]
                use_ext = False
            outputs["out_file"] = fname_presuffix(
                source,
                suffix=".%s%s" % (self.inputs.target_subject, ext),
                newpath=os.getcwd(),
                use_ext=use_ext,
            )
        else:
            outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()[name]
        return None


class Surface2VolTransformInputSpec(FSTraitedSpec):
    source_file = File(
        exists=True,
        argstr="--surfval %s",
        copyfile=False,
        mandatory=True,
        xor=["mkmask"],
        desc="This is the source of the surface values",
    )
    hemi = traits.Str(argstr="--hemi %s", mandatory=True, desc="hemisphere of data")
    transformed_file = File(
        name_template="%s_asVol.nii",
        desc="Output volume",
        argstr="--outvol %s",
        name_source=["source_file"],
        hash_files=False,
    )
    reg_file = File(
        exists=True,
        argstr="--volreg %s",
        mandatory=True,
        desc="tkRAS-to-tkRAS matrix   (tkregister2 format)",
        xor=["subject_id"],
    )
    template_file = File(
        exists=True, argstr="--template %s", desc="Output template volume"
    )
    mkmask = traits.Bool(
        desc="make a mask instead of loading surface values",
        argstr="--mkmask",
        xor=["source_file"],
    )
    vertexvol_file = File(
        name_template="%s_asVol_vertex.nii",
        desc=(
            "Path name of the vertex output volume, which "
            "is the same as output volume except that the "
            "value of each voxel is the vertex-id that is "
            "mapped to that voxel."
        ),
        argstr="--vtxvol %s",
        name_source=["source_file"],
        hash_files=False,
    )
    surf_name = traits.Str(argstr="--surf %s", desc="surfname (default is white)")
    projfrac = traits.Float(argstr="--projfrac %s", desc="thickness fraction")
    subjects_dir = traits.Str(
        argstr="--sd %s",
        desc=("freesurfer subjects directory defaults to " "$SUBJECTS_DIR"),
    )
    subject_id = traits.Str(argstr="--identity %s", desc="subject id", xor=["reg_file"])


class Surface2VolTransformOutputSpec(TraitedSpec):
    transformed_file = File(exists=True, desc="Path to output file if used normally")
    vertexvol_file = File(desc="vertex map volume path id. Optional")


class Surface2VolTransform(FSCommand):
    """Use FreeSurfer mri_surf2vol to apply a transform.

    Examples
    --------

    >>> from nipype.interfaces.freesurfer import Surface2VolTransform
    >>> xfm2vol = Surface2VolTransform()
    >>> xfm2vol.inputs.source_file = 'lh.cope1.mgz'
    >>> xfm2vol.inputs.reg_file = 'register.mat'
    >>> xfm2vol.inputs.hemi = 'lh'
    >>> xfm2vol.inputs.template_file = 'cope1.nii.gz'
    >>> xfm2vol.inputs.subjects_dir = '.'
    >>> xfm2vol.cmdline
    'mri_surf2vol --hemi lh --volreg register.mat --surfval lh.cope1.mgz --sd . --template cope1.nii.gz --outvol lh.cope1_asVol.nii --vtxvol lh.cope1_asVol_vertex.nii'
    >>> res = xfm2vol.run()# doctest: +SKIP

    """

    _cmd = "mri_surf2vol"
    input_spec = Surface2VolTransformInputSpec
    output_spec = Surface2VolTransformOutputSpec


class ApplyMaskInputSpec(FSTraitedSpec):

    in_file = File(
        exists=True,
        mandatory=True,
        position=-3,
        argstr="%s",
        desc="input image (will be masked)",
    )
    mask_file = File(
        exists=True,
        mandatory=True,
        position=-2,
        argstr="%s",
        desc="image defining mask space",
    )
    out_file = File(
        name_source=["in_file"],
        name_template="%s_masked",
        hash_files=True,
        keep_extension=True,
        position=-1,
        argstr="%s",
        desc="final image to write",
    )
    xfm_file = File(
        exists=True,
        argstr="-xform %s",
        desc="LTA-format transformation matrix to align mask with input",
    )
    invert_xfm = traits.Bool(argstr="-invert", desc="invert transformation")
    xfm_source = File(
        exists=True, argstr="-lta_src %s", desc="image defining transform source space"
    )
    xfm_target = File(
        exists=True, argstr="-lta_dst %s", desc="image defining transform target space"
    )
    use_abs = traits.Bool(
        argstr="-abs", desc="take absolute value of mask before applying"
    )
    mask_thresh = traits.Float(argstr="-T %.4f", desc="threshold mask before applying")
    keep_mask_deletion_edits = traits.Bool(
        argstr="-keep_mask_deletion_edits",
        desc="transfer voxel-deletion edits (voxels=1) from mask to out vol",
    )
    transfer = traits.Int(
        argstr="-transfer %d", desc="transfer only voxel value # from mask to out"
    )


class ApplyMaskOutputSpec(TraitedSpec):

    out_file = File(exists=True, desc="masked image")


class ApplyMask(FSCommand):
    """Use Freesurfer's mri_mask to apply a mask to an image.

    The mask file need not be binarized; it can be thresholded above a given
    value before application. It can also optionally be transformed into input
    space with an LTA matrix.

    """

    _cmd = "mri_mask"
    input_spec = ApplyMaskInputSpec
    output_spec = ApplyMaskOutputSpec


class SurfaceSnapshotsInputSpec(FSTraitedSpec):

    subject_id = traits.String(
        position=1, argstr="%s", mandatory=True, desc="subject to visualize"
    )
    hemi = traits.Enum(
        "lh",
        "rh",
        position=2,
        argstr="%s",
        mandatory=True,
        desc="hemisphere to visualize",
    )
    surface = traits.String(
        position=3, argstr="%s", mandatory=True, desc="surface to visualize"
    )

    show_curv = traits.Bool(
        argstr="-curv", desc="show curvature", xor=["show_gray_curv"]
    )
    show_gray_curv = traits.Bool(
        argstr="-gray", desc="show curvature in gray", xor=["show_curv"]
    )

    overlay = File(
        exists=True,
        argstr="-overlay %s",
        desc="load an overlay volume/surface",
        requires=["overlay_range"],
    )
    reg_xors = ["overlay_reg", "identity_reg", "mni152_reg"]
    overlay_reg = File(
        exists=True,
        argstr="-overlay-reg %s",
        xor=reg_xors,
        desc="registration matrix file to register overlay to surface",
    )
    identity_reg = traits.Bool(
        argstr="-overlay-reg-identity",
        xor=reg_xors,
        desc="use the identity matrix to register the overlay to the surface",
    )
    mni152_reg = traits.Bool(
        argstr="-mni152reg",
        xor=reg_xors,
        desc="use to display a volume in MNI152 space on the average subject",
    )

    overlay_range = traits.Either(
        traits.Float,
        traits.Tuple(traits.Float, traits.Float),
        traits.Tuple(traits.Float, traits.Float, traits.Float),
        desc="overlay range--either min, (min, max) or (min, mid, max)",
        argstr="%s",
    )
    overlay_range_offset = traits.Float(
        argstr="-foffset %.3f",
        desc="overlay range will be symettric around offset value",
    )

    truncate_overlay = traits.Bool(
        argstr="-truncphaseflag 1", desc="truncate the overlay display"
    )
    reverse_overlay = traits.Bool(
        argstr="-revphaseflag 1", desc="reverse the overlay display"
    )
    invert_overlay = traits.Bool(
        argstr="-invphaseflag 1", desc="invert the overlay display"
    )
    demean_overlay = traits.Bool(argstr="-zm", desc="remove mean from overlay")

    annot_file = File(
        exists=True,
        argstr="-annotation %s",
        xor=["annot_name"],
        desc="path to annotation file to display",
    )
    annot_name = traits.String(
        argstr="-annotation %s",
        xor=["annot_file"],
        desc="name of annotation to display (must be in $subject/label directory",
    )

    label_file = File(
        exists=True,
        argstr="-label %s",
        xor=["label_name"],
        desc="path to label file to display",
    )
    label_name = traits.String(
        argstr="-label %s",
        xor=["label_file"],
        desc="name of label to display (must be in $subject/label directory",
    )

    colortable = File(exists=True, argstr="-colortable %s", desc="load colortable file")
    label_under = traits.Bool(
        argstr="-labels-under", desc="draw label/annotation under overlay"
    )
    label_outline = traits.Bool(
        argstr="-label-outline", desc="draw label/annotation as outline"
    )

    patch_file = File(exists=True, argstr="-patch %s", desc="load a patch")

    orig_suffix = traits.String(
        argstr="-orig %s", desc="set the orig surface suffix string"
    )
    sphere_suffix = traits.String(
        argstr="-sphere %s", desc="set the sphere.reg suffix string"
    )

    show_color_scale = traits.Bool(
        argstr="-colscalebarflag 1", desc="display the color scale bar"
    )
    show_color_text = traits.Bool(
        argstr="-colscaletext 1", desc="display text in the color scale bar"
    )

    six_images = traits.Bool(desc="also take anterior and posterior snapshots")
    screenshot_stem = traits.String(desc="stem to use for screenshot file names")
    stem_template_args = traits.List(
        traits.String,
        requires=["screenshot_stem"],
        desc="input names to use as arguments for a string-formated stem template",
    )
    tcl_script = File(
        exists=True,
        argstr="%s",
        genfile=True,
        desc="override default screenshot script",
    )


class SurfaceSnapshotsOutputSpec(TraitedSpec):

    snapshots = OutputMultiPath(
        File(exists=True), desc="tiff images of the surface from different perspectives"
    )


class SurfaceSnapshots(FSCommand):
    """Use Tksurfer to save pictures of the cortical surface.

    By default, this takes snapshots of the lateral, medial, ventral,
    and dorsal surfaces.  See the ``six_images`` option to add the
    anterior and posterior surfaces.

    You may also supply your own tcl script (see the Freesurfer wiki for
    information on scripting tksurfer). The screenshot stem is set as the
    environment variable "_SNAPSHOT_STEM", which you can use in your
    own scripts.

    Node that this interface will not run if you do not have graphics
    enabled on your system.

    Examples
    --------

    >>> import nipype.interfaces.freesurfer as fs
    >>> shots = fs.SurfaceSnapshots(subject_id="fsaverage", hemi="lh", surface="pial")
    >>> shots.inputs.overlay = "zstat1.nii.gz"
    >>> shots.inputs.overlay_range = (2.3, 6)
    >>> shots.inputs.overlay_reg = "register.dat"
    >>> res = shots.run() # doctest: +SKIP

    """

    _cmd = "tksurfer"
    input_spec = SurfaceSnapshotsInputSpec
    output_spec = SurfaceSnapshotsOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "tcl_script":
            if not isdefined(value):
                return "-tcl snapshots.tcl"
            else:
                return "-tcl %s" % value
        elif name == "overlay_range":
            if isinstance(value, float):
                return "-fthresh %.3f" % value
            else:
                if len(value) == 2:
                    return "-fminmax %.3f %.3f" % value
                else:
                    return "-fminmax %.3f %.3f -fmid %.3f" % (
                        value[0],
                        value[2],
                        value[1],
                    )
        elif name == "annot_name" and isdefined(value):
            # Matching annot by name needs to strip the leading hemi and trailing
            # extension strings
            if value.endswith(".annot"):
                value = value[:-6]
            if re.match(r"%s[\.\-_]" % self.inputs.hemi, value[:3]):
                value = value[3:]
            return "-annotation %s" % value
        return super(SurfaceSnapshots, self)._format_arg(name, spec, value)

    def _run_interface(self, runtime):
        if not isdefined(self.inputs.screenshot_stem):
            stem = "%s_%s_%s" % (
                self.inputs.subject_id,
                self.inputs.hemi,
                self.inputs.surface,
            )
        else:
            stem = self.inputs.screenshot_stem
            stem_args = self.inputs.stem_template_args
            if isdefined(stem_args):
                args = tuple([getattr(self.inputs, arg) for arg in stem_args])
                stem = stem % args
        # Check if the DISPLAY variable is set -- should avoid crashes (might not?)
        if "DISPLAY" not in os.environ:
            raise RuntimeError("Graphics are not enabled -- cannot run tksurfer")
        runtime.environ["_SNAPSHOT_STEM"] = stem
        self._write_tcl_script()
        runtime = super(SurfaceSnapshots, self)._run_interface(runtime)
        # If a display window can't be opened, this will crash on
        # aggregate_outputs.  Let's try to parse stderr and raise a
        # better exception here if that happened.
        errors = [
            "surfer: failed, no suitable display found",
            "Fatal Error in tksurfer.bin: could not open display",
        ]
        for err in errors:
            if err in runtime.stderr:
                self.raise_exception(runtime)
        # Tksurfer always (or at least always when you run a tcl script)
        # exits with a nonzero returncode.  We have to force it to 0 here.
        runtime.returncode = 0
        return runtime

    def _write_tcl_script(self):
        fid = open("snapshots.tcl", "w")
        script = [
            "save_tiff $env(_SNAPSHOT_STEM)-lat.tif",
            "make_lateral_view",
            "rotate_brain_y 180",
            "redraw",
            "save_tiff $env(_SNAPSHOT_STEM)-med.tif",
            "make_lateral_view",
            "rotate_brain_x 90",
            "redraw",
            "save_tiff $env(_SNAPSHOT_STEM)-ven.tif",
            "make_lateral_view",
            "rotate_brain_x -90",
            "redraw",
            "save_tiff $env(_SNAPSHOT_STEM)-dor.tif",
        ]
        if isdefined(self.inputs.six_images) and self.inputs.six_images:
            script.extend(
                [
                    "make_lateral_view",
                    "rotate_brain_y 90",
                    "redraw",
                    "save_tiff $env(_SNAPSHOT_STEM)-pos.tif",
                    "make_lateral_view",
                    "rotate_brain_y -90",
                    "redraw",
                    "save_tiff $env(_SNAPSHOT_STEM)-ant.tif",
                ]
            )

        script.append("exit")
        fid.write("\n".join(script))
        fid.close()

    def _list_outputs(self):
        outputs = self._outputs().get()
        if not isdefined(self.inputs.screenshot_stem):
            stem = "%s_%s_%s" % (
                self.inputs.subject_id,
                self.inputs.hemi,
                self.inputs.surface,
            )
        else:
            stem = self.inputs.screenshot_stem
            stem_args = self.inputs.stem_template_args
            if isdefined(stem_args):
                args = tuple([getattr(self.inputs, arg) for arg in stem_args])
                stem = stem % args
        snapshots = ["%s-lat.tif", "%s-med.tif", "%s-dor.tif", "%s-ven.tif"]
        if self.inputs.six_images:
            snapshots.extend(["%s-pos.tif", "%s-ant.tif"])
        snapshots = [self._gen_fname(f % stem, suffix="") for f in snapshots]
        outputs["snapshots"] = snapshots
        return outputs

    def _gen_filename(self, name):
        if name == "tcl_script":
            return "snapshots.tcl"
        return None


class ImageInfoInputSpec(FSTraitedSpec):

    in_file = File(exists=True, position=1, argstr="%s", desc="image to query")


class ImageInfoOutputSpec(TraitedSpec):

    info = traits.Any(desc="output of mri_info")
    out_file = File(exists=True, desc="text file with image information")
    data_type = traits.String(desc="image data type")
    file_format = traits.String(desc="file format")
    TE = traits.String(desc="echo time (msec)")
    TR = traits.String(desc="repetition time(msec)")
    TI = traits.String(desc="inversion time (msec)")
    dimensions = traits.Tuple(desc="image dimensions (voxels)")
    vox_sizes = traits.Tuple(desc="voxel sizes (mm)")
    orientation = traits.String(desc="image orientation")
    ph_enc_dir = traits.String(desc="phase encode direction")


class ImageInfo(FSCommand):

    _cmd = "mri_info"
    input_spec = ImageInfoInputSpec
    output_spec = ImageInfoOutputSpec

    def info_regexp(self, info, field, delim="\n"):
        m = re.search(r"%s\s*:\s+(.+?)%s" % (field, delim), info)
        if m:
            return m.group(1)
        else:
            return None

    def aggregate_outputs(self, runtime=None, needed_outputs=None):
        outputs = self._outputs()
        info = runtime.stdout
        outputs.info = info

        # Pulse sequence parameters
        for field in ["TE", "TR", "TI"]:
            fieldval = self.info_regexp(info, field, ", ")
            if fieldval.endswith(" msec"):
                fieldval = fieldval[:-5]
            setattr(outputs, field, fieldval)

        # Voxel info
        vox = self.info_regexp(info, "voxel sizes")
        vox = tuple(vox.split(", "))
        outputs.vox_sizes = vox
        dim = self.info_regexp(info, "dimensions")
        dim = tuple([int(d) for d in dim.split(" x ")])
        outputs.dimensions = dim

        outputs.orientation = self.info_regexp(info, "Orientation")
        outputs.ph_enc_dir = self.info_regexp(info, "PhEncDir")

        # File format and datatype are both keyed by "type"
        ftype, dtype = re.findall(r"%s\s*:\s+(.+?)\n" % "type", info)
        outputs.file_format = ftype
        outputs.data_type = dtype

        return outputs


class MRIsConvertInputSpec(FSTraitedSpec):
    """
    Uses Freesurfer's mris_convert to convert surface files to various formats
    """

    annot_file = File(
        exists=True, argstr="--annot %s", desc="input is annotation or gifti label data"
    )

    parcstats_file = File(
        exists=True,
        argstr="--parcstats %s",
        desc="infile is name of text file containing label/val pairs",
    )

    label_file = File(
        exists=True,
        argstr="--label %s",
        desc="infile is .label file, label is name of this label",
    )

    scalarcurv_file = File(
        exists=True,
        argstr="-c %s",
        desc="input is scalar curv overlay file (must still specify surface)",
    )

    functional_file = File(
        exists=True,
        argstr="-f %s",
        desc="input is functional time-series or other multi-frame data (must specify surface)",
    )

    labelstats_outfile = File(
        exists=False,
        argstr="--labelstats %s",
        desc="outfile is name of gifti file to which label stats will be written",
    )

    patch = traits.Bool(argstr="-p", desc="input is a patch, not a full surface")
    rescale = traits.Bool(
        argstr="-r", desc="rescale vertex xyz so total area is same as group average"
    )
    normal = traits.Bool(argstr="-n", desc="output is an ascii file where vertex data")
    xyz_ascii = traits.Bool(argstr="-a", desc="Print only surface xyz to ascii file")
    vertex = traits.Bool(
        argstr="-v", desc="Writes out neighbors of a vertex in each row"
    )

    scale = traits.Float(argstr="-s %.3f", desc="scale vertex xyz by scale")
    dataarray_num = traits.Int(
        argstr="--da_num %d",
        desc="if input is gifti, 'num' specifies which data array to use",
    )

    talairachxfm_subjid = traits.String(
        argstr="-t %s", desc="apply talairach xfm of subject to vertex xyz"
    )
    origname = traits.String(argstr="-o %s", desc="read orig positions")

    in_file = File(
        exists=True,
        mandatory=True,
        position=-2,
        argstr="%s",
        desc="File to read/convert",
    )
    out_file = File(
        argstr="%s",
        position=-1,
        genfile=True,
        xor=["out_datatype"],
        mandatory=True,
        desc="output filename or True to generate one",
    )

    out_datatype = traits.Enum(
        "asc",
        "ico",
        "tri",
        "stl",
        "vtk",
        "gii",
        "mgh",
        "mgz",
        xor=["out_file"],
        mandatory=True,
        desc="These file formats are supported:  ASCII:       .asc"
        "ICO: .ico, .tri GEO: .geo STL: .stl VTK: .vtk GIFTI: .gii MGH surface-encoded 'volume': .mgh, .mgz",
    )
    to_scanner = traits.Bool(
        argstr="--to-scanner",
        desc="convert coordinates from native FS (tkr) coords to scanner coords",
    )
    to_tkr = traits.Bool(
        argstr="--to-tkr",
        desc="convert coordinates from scanner coords to native FS (tkr) coords",
    )


class MRIsConvertOutputSpec(TraitedSpec):
    """
    Uses Freesurfer's mris_convert to convert surface files to various formats
    """

    converted = File(exists=True, desc="converted output surface")


class MRIsConvert(FSCommand):
    """
    Uses Freesurfer's mris_convert to convert surface files to various formats

    Example
    -------

    >>> import nipype.interfaces.freesurfer as fs
    >>> mris = fs.MRIsConvert()
    >>> mris.inputs.in_file = 'lh.pial'
    >>> mris.inputs.out_datatype = 'gii'
    >>> mris.run() # doctest: +SKIP
    """

    _cmd = "mris_convert"
    input_spec = MRIsConvertInputSpec
    output_spec = MRIsConvertOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "out_file" and not os.path.isabs(value):
            value = os.path.abspath(value)
        return super(MRIsConvert, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["converted"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return os.path.abspath(self._gen_outfilename())
        else:
            return None

    def _gen_outfilename(self):
        if isdefined(self.inputs.out_file):
            return self.inputs.out_file
        elif isdefined(self.inputs.annot_file):
            _, name, ext = split_filename(self.inputs.annot_file)
        elif isdefined(self.inputs.parcstats_file):
            _, name, ext = split_filename(self.inputs.parcstats_file)
        elif isdefined(self.inputs.label_file):
            _, name, ext = split_filename(self.inputs.label_file)
        elif isdefined(self.inputs.scalarcurv_file):
            _, name, ext = split_filename(self.inputs.scalarcurv_file)
        elif isdefined(self.inputs.functional_file):
            _, name, ext = split_filename(self.inputs.functional_file)
        elif isdefined(self.inputs.in_file):
            _, name, ext = split_filename(self.inputs.in_file)

        return name + ext + "_converted." + self.inputs.out_datatype


class MRIsCombineInputSpec(FSTraitedSpec):
    """
    Uses Freesurfer's mris_convert to combine two surface files into one.
    """

    in_files = traits.List(
        File(Exists=True),
        maxlen=2,
        minlen=2,
        mandatory=True,
        position=1,
        argstr="--combinesurfs %s",
        desc="Two surfaces to be combined.",
    )
    out_file = File(
        argstr="%s",
        position=-1,
        genfile=True,
        mandatory=True,
        desc="Output filename. Combined surfaces from in_files.",
    )


class MRIsCombineOutputSpec(TraitedSpec):
    """
    Uses Freesurfer's mris_convert to combine two surface files into one.
    """

    out_file = File(
        exists=True, desc="Output filename. Combined surfaces from " "in_files."
    )


class MRIsCombine(FSSurfaceCommand):
    """
    Uses Freesurfer's ``mris_convert`` to combine two surface files into one.

    For complete details, see the `mris_convert Documentation.
    <https://surfer.nmr.mgh.harvard.edu/fswiki/mris_convert>`_

    If given an ``out_file`` that does not begin with ``'lh.'`` or ``'rh.'``,
    ``mris_convert`` will prepend ``'lh.'`` to the file name.
    To avoid this behavior, consider setting ``out_file = './<filename>'``, or
    leaving out_file blank.

    In a Node/Workflow, ``out_file`` is interpreted literally.

    Example
    -------

    >>> import nipype.interfaces.freesurfer as fs
    >>> mris = fs.MRIsCombine()
    >>> mris.inputs.in_files = ['lh.pial', 'rh.pial']
    >>> mris.inputs.out_file = 'bh.pial'
    >>> mris.cmdline
    'mris_convert --combinesurfs lh.pial rh.pial bh.pial'
    >>> mris.run()  # doctest: +SKIP
    """

    _cmd = "mris_convert"
    input_spec = MRIsCombineInputSpec
    output_spec = MRIsCombineOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()

        # mris_convert --combinesurfs uses lh. as the default prefix
        # regardless of input file names, except when path info is
        # specified
        path, base = os.path.split(self.inputs.out_file)
        if path == "" and base[:3] not in ("lh.", "rh."):
            base = "lh." + base
        outputs["out_file"] = os.path.abspath(os.path.join(path, base))

        return outputs

    def normalize_filenames(self):
        """
        Filename normalization routine to perform only when run in Node
        context.
        Interpret out_file as a literal path to reduce surprise.
        """
        if isdefined(self.inputs.out_file):
            self.inputs.out_file = os.path.abspath(self.inputs.out_file)


class MRITessellateInputSpec(FSTraitedSpec):
    """
    Uses Freesurfer's mri_tessellate to create surfaces by tessellating a given input volume
    """

    in_file = File(
        exists=True,
        mandatory=True,
        position=-3,
        argstr="%s",
        desc="Input volume to tesselate voxels from.",
    )
    label_value = traits.Int(
        position=-2,
        argstr="%d",
        mandatory=True,
        desc='Label value which to tesselate from the input volume. (integer, if input is "filled.mgz" volume, 127 is rh, 255 is lh)',
    )
    out_file = File(
        argstr="%s",
        position=-1,
        genfile=True,
        desc="output filename or True to generate one",
    )
    tesselate_all_voxels = traits.Bool(
        argstr="-a", desc="Tessellate the surface of all voxels with different labels"
    )
    use_real_RAS_coordinates = traits.Bool(
        argstr="-n", desc="Saves surface with real RAS coordinates where c_(r,a,s) != 0"
    )


class MRITessellateOutputSpec(TraitedSpec):
    """
    Uses Freesurfer's mri_tessellate to create surfaces by tessellating a given input volume
    """

    surface = File(exists=True, desc="binary surface of the tessellation ")


class MRITessellate(FSCommand):
    """
    Uses Freesurfer's mri_tessellate to create surfaces by tessellating a given input volume

    Example
    -------

    >>> import nipype.interfaces.freesurfer as fs
    >>> tess = fs.MRITessellate()
    >>> tess.inputs.in_file = 'aseg.mgz'
    >>> tess.inputs.label_value = 17
    >>> tess.inputs.out_file = 'lh.hippocampus'
    >>> tess.run() # doctest: +SKIP
    """

    _cmd = "mri_tessellate"
    input_spec = MRITessellateInputSpec
    output_spec = MRITessellateOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["surface"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        if isdefined(self.inputs.out_file):
            return self.inputs.out_file
        else:
            _, name, ext = split_filename(self.inputs.in_file)
            return name + ext + "_" + str(self.inputs.label_value)


class MRIPretessInputSpec(FSTraitedSpec):
    in_filled = File(
        exists=True,
        mandatory=True,
        position=-4,
        argstr="%s",
        desc=("filled volume, usually wm.mgz"),
    )
    label = traits.Either(
        traits.Str("wm"),
        traits.Int(1),
        argstr="%s",
        default="wm",
        mandatory=True,
        usedefault=True,
        position=-3,
        desc=(
            "label to be picked up, can be a Freesurfer's string like "
            "'wm' or a label value (e.g. 127 for rh or 255 for lh)"
        ),
    )
    in_norm = File(
        exists=True,
        mandatory=True,
        position=-2,
        argstr="%s",
        desc=("the normalized, brain-extracted T1w image. Usually norm.mgz"),
    )
    out_file = File(
        position=-1,
        argstr="%s",
        name_source=["in_filled"],
        name_template="%s_pretesswm",
        keep_extension=True,
        desc="the output file after mri_pretess.",
    )

    nocorners = traits.Bool(
        False,
        argstr="-nocorners",
        desc=("do not remove corner configurations" " in addition to edge ones."),
    )
    keep = traits.Bool(False, argstr="-keep", desc=("keep WM edits"))
    test = traits.Bool(
        False,
        argstr="-test",
        desc=(
            "adds a voxel that should be removed by "
            "mri_pretess. The value of the voxel is set to that of an ON-edited WM, "
            "so it should be kept with -keep. The output will NOT be saved."
        ),
    )


class MRIPretessOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output file after mri_pretess")


class MRIPretess(FSCommand):
    """
    Uses Freesurfer's mri_pretess to prepare volumes to be tessellated.

    Changes white matter (WM) segmentation so that the neighbors of all
    voxels labeled as WM have a face in common - no edges or corners
    allowed.

    Example
    -------
    >>> import nipype.interfaces.freesurfer as fs
    >>> pretess = fs.MRIPretess()
    >>> pretess.inputs.in_filled = 'wm.mgz'
    >>> pretess.inputs.in_norm = 'norm.mgz'
    >>> pretess.inputs.nocorners = True
    >>> pretess.cmdline
    'mri_pretess -nocorners wm.mgz wm norm.mgz wm_pretesswm.mgz'
    >>> pretess.run() # doctest: +SKIP

    """

    _cmd = "mri_pretess"
    input_spec = MRIPretessInputSpec
    output_spec = MRIPretessOutputSpec


class MRIMarchingCubesInputSpec(FSTraitedSpec):
    """
    Uses Freesurfer's mri_mc to create surfaces by tessellating a given input volume
    """

    in_file = File(
        exists=True,
        mandatory=True,
        position=1,
        argstr="%s",
        desc="Input volume to tesselate voxels from.",
    )
    label_value = traits.Int(
        position=2,
        argstr="%d",
        mandatory=True,
        desc='Label value which to tesselate from the input volume. (integer, if input is "filled.mgz" volume, 127 is rh, 255 is lh)',
    )
    connectivity_value = traits.Int(
        1,
        position=-1,
        argstr="%d",
        usedefault=True,
        desc="Alter the marching cubes connectivity: 1=6+,2=18,3=6,4=26 (default=1)",
    )
    out_file = File(
        argstr="./%s",
        position=-2,
        genfile=True,
        desc="output filename or True to generate one",
    )


class MRIMarchingCubesOutputSpec(TraitedSpec):
    """
    Uses Freesurfer's mri_mc to create surfaces by tessellating a given input volume
    """

    surface = File(exists=True, desc="binary surface of the tessellation ")


class MRIMarchingCubes(FSCommand):
    """
    Uses Freesurfer's mri_mc to create surfaces by tessellating a given input volume

    Example
    -------

    >>> import nipype.interfaces.freesurfer as fs
    >>> mc = fs.MRIMarchingCubes()
    >>> mc.inputs.in_file = 'aseg.mgz'
    >>> mc.inputs.label_value = 17
    >>> mc.inputs.out_file = 'lh.hippocampus'
    >>> mc.run() # doctest: +SKIP
    """

    _cmd = "mri_mc"
    input_spec = MRIMarchingCubesInputSpec
    output_spec = MRIMarchingCubesOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["surface"] = self._gen_outfilename()
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        if isdefined(self.inputs.out_file):
            return os.path.abspath(self.inputs.out_file)
        else:
            _, name, ext = split_filename(self.inputs.in_file)
            return os.path.abspath(name + ext + "_" + str(self.inputs.label_value))


class SmoothTessellationInputSpec(FSTraitedSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-2,
        copyfile=True,
        desc="Input volume to tesselate voxels from.",
    )
    curvature_averaging_iterations = traits.Int(
        argstr="-a %d", desc="Number of curvature averaging iterations (default=10)"
    )
    smoothing_iterations = traits.Int(
        argstr="-n %d", desc="Number of smoothing iterations (default=10)"
    )
    snapshot_writing_iterations = traits.Int(
        argstr="-w %d", desc="Write snapshot every *n* iterations"
    )

    use_gaussian_curvature_smoothing = traits.Bool(
        argstr="-g", desc="Use Gaussian curvature smoothing"
    )
    gaussian_curvature_norm_steps = traits.Int(
        argstr="%d", desc="Use Gaussian curvature smoothing"
    )
    gaussian_curvature_smoothing_steps = traits.Int(
        argstr=" %d", desc="Use Gaussian curvature smoothing"
    )

    disable_estimates = traits.Bool(
        argstr="-nw", desc="Disables the writing of curvature and area estimates"
    )
    normalize_area = traits.Bool(
        argstr="-area", desc="Normalizes the area after smoothing"
    )
    use_momentum = traits.Bool(argstr="-m", desc="Uses momentum")

    out_file = File(
        argstr="%s",
        position=-1,
        genfile=True,
        desc="output filename or True to generate one",
    )
    out_curvature_file = File(
        argstr="-c %s", desc='Write curvature to ``?h.curvname`` (default "curv")'
    )
    out_area_file = File(
        argstr="-b %s", desc='Write area to ``?h.areaname`` (default "area")'
    )
    seed = traits.Int(
        argstr="-seed %d", desc="Seed for setting random number generator"
    )


class SmoothTessellationOutputSpec(TraitedSpec):
    """
    This program smooths the tessellation of a surface using 'mris_smooth'
    """

    surface = File(exists=True, desc="Smoothed surface file.")


class SmoothTessellation(FSCommand):
    """
    Smooth a tessellated surface.

    See Also
    --------
    `nipype.interfaces.freesurfer.utils.SurfaceSmooth`_ interface for smoothing a scalar field
    along a surface manifold

    Example
    -------
    >>> import nipype.interfaces.freesurfer as fs
    >>> smooth = fs.SmoothTessellation()
    >>> smooth.inputs.in_file = 'lh.hippocampus.stl'
    >>> smooth.run() # doctest: +SKIP

    """

    _cmd = "mris_smooth"
    input_spec = SmoothTessellationInputSpec
    output_spec = SmoothTessellationOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["surface"] = self._gen_outfilename()
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        if isdefined(self.inputs.out_file):
            return os.path.abspath(self.inputs.out_file)
        else:
            _, name, ext = split_filename(self.inputs.in_file)
            return os.path.abspath(name + "_smoothed" + ext)

    def _run_interface(self, runtime):
        # The returncode is meaningless in BET.  So check the output
        # in stderr and if it's set, then update the returncode
        # accordingly.
        runtime = super(SmoothTessellation, self)._run_interface(runtime)
        if "failed" in runtime.stderr:
            self.raise_exception(runtime)
        return runtime


class MakeAverageSubjectInputSpec(FSTraitedSpec):
    subjects_ids = traits.List(
        traits.Str(),
        argstr="--subjects %s",
        desc="freesurfer subjects ids to average",
        mandatory=True,
        sep=" ",
    )
    out_name = File(
        "average",
        argstr="--out %s",
        desc="name for the average subject",
        usedefault=True,
    )


class MakeAverageSubjectOutputSpec(TraitedSpec):
    average_subject_name = traits.Str(desc="Output registration file")


class MakeAverageSubject(FSCommand):
    """Make an average freesurfer subject

    Examples
    --------

    >>> from nipype.interfaces.freesurfer import MakeAverageSubject
    >>> avg = MakeAverageSubject(subjects_ids=['s1', 's2'])
    >>> avg.cmdline
    'make_average_subject --out average --subjects s1 s2'

    """

    _cmd = "make_average_subject"
    input_spec = MakeAverageSubjectInputSpec
    output_spec = MakeAverageSubjectOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["average_subject_name"] = self.inputs.out_name
        return outputs


class ExtractMainComponentInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True, mandatory=True, argstr="%s", position=1, desc="input surface file"
    )
    out_file = File(
        name_template="%s.maincmp",
        name_source="in_file",
        argstr="%s",
        position=2,
        desc="surface containing main component",
    )


class ExtractMainComponentOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="surface containing main component")


class ExtractMainComponent(CommandLine):
    """Extract the main component of a tesselated surface

    Examples
    --------

    >>> from nipype.interfaces.freesurfer import ExtractMainComponent
    >>> mcmp = ExtractMainComponent(in_file='lh.pial')
    >>> mcmp.cmdline
    'mris_extract_main_component lh.pial lh.maincmp'

    """

    _cmd = "mris_extract_main_component"
    input_spec = ExtractMainComponentInputSpec
    output_spec = ExtractMainComponentOutputSpec


class Tkregister2InputSpec(FSTraitedSpec):
    target_image = File(
        exists=True, argstr="--targ %s", xor=["fstarg"], desc="target volume"
    )
    fstarg = traits.Bool(
        False,
        argstr="--fstarg",
        xor=["target_image"],
        desc="use subject's T1 as reference",
    )

    moving_image = File(
        exists=True, mandatory=True, argstr="--mov %s", desc="moving volume"
    )
    # Input registration file options
    fsl_in_matrix = File(
        exists=True, argstr="--fsl %s", desc="fsl-style registration input matrix"
    )
    xfm = File(
        exists=True,
        argstr="--xfm %s",
        desc="use a matrix in MNI coordinates as initial registration",
    )
    lta_in = File(
        exists=True,
        argstr="--lta %s",
        desc="use a matrix in MNI coordinates as initial registration",
    )
    invert_lta_in = traits.Bool(
        requires=["lta_in"], desc="Invert input LTA before applying"
    )
    # Output registration file options
    fsl_out = traits.Either(
        True,
        File,
        argstr="--fslregout %s",
        desc="compute an FSL-compatible resgitration matrix",
    )
    lta_out = traits.Either(
        True, File, argstr="--ltaout %s", desc="output registration file (LTA format)"
    )
    invert_lta_out = traits.Bool(
        argstr="--ltaout-inv",
        requires=["lta_in"],
        desc="Invert input LTA before applying",
    )

    subject_id = traits.String(argstr="--s %s", desc="freesurfer subject ID")
    noedit = traits.Bool(
        True, argstr="--noedit", usedefault=True, desc="do not open edit window (exit)"
    )
    reg_file = File(
        "register.dat",
        usedefault=True,
        mandatory=True,
        argstr="--reg %s",
        desc="freesurfer-style registration file",
    )
    reg_header = traits.Bool(
        False, argstr="--regheader", desc="compute regstration from headers"
    )
    fstal = traits.Bool(
        False,
        argstr="--fstal",
        xor=["target_image", "moving_image", "reg_file"],
        desc="set mov to be tal and reg to be tal xfm",
    )
    movscale = traits.Float(
        argstr="--movscale %f", desc="adjust registration matrix to scale mov"
    )


class Tkregister2OutputSpec(TraitedSpec):
    reg_file = File(exists=True, desc="freesurfer-style registration file")
    fsl_file = File(desc="FSL-style registration file")
    lta_file = File(desc="LTA-style registration file")


class Tkregister2(FSCommand):
    """

    Examples
    --------
    Get transform matrix between orig (*tkRAS*) and native (*scannerRAS*)
    coordinates in Freesurfer. Implements the first step of mapping surfaces
    to native space in `this guide
    <http://surfer.nmr.mgh.harvard.edu/fswiki/FsAnat-to-NativeAnat>`__.

    >>> from nipype.interfaces.freesurfer import Tkregister2
    >>> tk2 = Tkregister2(reg_file='T1_to_native.dat')
    >>> tk2.inputs.moving_image = 'T1.mgz'
    >>> tk2.inputs.target_image = 'structural.nii'
    >>> tk2.inputs.reg_header = True
    >>> tk2.cmdline
    'tkregister2 --mov T1.mgz --noedit --reg T1_to_native.dat --regheader \
--targ structural.nii'
    >>> tk2.run() # doctest: +SKIP

    The example below uses tkregister2 without the manual editing
    stage to convert FSL-style registration matrix (.mat) to
    FreeSurfer-style registration matrix (.dat)

    >>> from nipype.interfaces.freesurfer import Tkregister2
    >>> tk2 = Tkregister2()
    >>> tk2.inputs.moving_image = 'epi.nii'
    >>> tk2.inputs.fsl_in_matrix = 'flirt.mat'
    >>> tk2.cmdline
    'tkregister2 --fsl flirt.mat --mov epi.nii --noedit --reg register.dat'
    >>> tk2.run() # doctest: +SKIP
    """

    _cmd = "tkregister2"
    input_spec = Tkregister2InputSpec
    output_spec = Tkregister2OutputSpec

    def _format_arg(self, name, spec, value):
        if name == "lta_in" and self.inputs.invert_lta_in:
            spec = "--lta-inv %s"
        if name in ("fsl_out", "lta_out") and value is True:
            value = self._list_outputs()[name]
        return super(Tkregister2, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()
        reg_file = os.path.abspath(self.inputs.reg_file)
        outputs["reg_file"] = reg_file

        cwd = os.getcwd()
        fsl_out = self.inputs.fsl_out
        if isdefined(fsl_out):
            if fsl_out is True:
                outputs["fsl_file"] = fname_presuffix(
                    reg_file, suffix=".mat", newpath=cwd, use_ext=False
                )
            else:
                outputs["fsl_file"] = os.path.abspath(self.inputs.fsl_out)

        lta_out = self.inputs.lta_out
        if isdefined(lta_out):
            if lta_out is True:
                outputs["lta_file"] = fname_presuffix(
                    reg_file, suffix=".lta", newpath=cwd, use_ext=False
                )
            else:
                outputs["lta_file"] = os.path.abspath(self.inputs.lta_out)
        return outputs

    def _gen_outfilename(self):
        if isdefined(self.inputs.out_file):
            return os.path.abspath(self.inputs.out_file)
        else:
            _, name, ext = split_filename(self.inputs.in_file)
            return os.path.abspath(name + "_smoothed" + ext)


class AddXFormToHeaderInputSpec(FSTraitedSpec):

    # required
    in_file = File(
        exists=True, mandatory=True, position=-2, argstr="%s", desc="input volume"
    )
    # transform file does NOT need to exist at the time if using copy_name
    transform = File(
        exists=False, mandatory=True, position=-3, argstr="%s", desc="xfm file"
    )
    out_file = File(
        "output.mgz", position=-1, argstr="%s", usedefault=True, desc="output volume"
    )
    # optional
    copy_name = traits.Bool(
        argstr="-c", desc="do not try to load the xfmfile, just copy name"
    )
    verbose = traits.Bool(argstr="-v", desc="be verbose")


class AddXFormToHeaderOutputSpec(TraitedSpec):

    out_file = File(exists=True, desc="output volume")


class AddXFormToHeader(FSCommand):
    """
    Just adds specified xform to the volume header.

    .. danger ::

        Input transform **MUST** be an absolute path to a DataSink'ed transform or
        the output will reference a transform in the workflow cache directory!

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import AddXFormToHeader
    >>> adder = AddXFormToHeader()
    >>> adder.inputs.in_file = 'norm.mgz'
    >>> adder.inputs.transform = 'trans.mat'
    >>> adder.cmdline
    'mri_add_xform_to_header trans.mat norm.mgz output.mgz'

    >>> adder.inputs.copy_name = True
    >>> adder.cmdline
    'mri_add_xform_to_header -c trans.mat norm.mgz output.mgz'
    >>> adder.run()   # doctest: +SKIP

    References
    ----------
    [https://surfer.nmr.mgh.harvard.edu/fswiki/mri_add_xform_to_header]

    """

    _cmd = "mri_add_xform_to_header"
    input_spec = AddXFormToHeaderInputSpec
    output_spec = AddXFormToHeaderOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "transform":
            return value  # os.path.abspath(value)
        # if name == 'copy_name' and value:
        #     self.input_spec.transform
        return super(AddXFormToHeader, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


class CheckTalairachAlignmentInputSpec(FSTraitedSpec):
    in_file = File(
        argstr="-xfm %s",
        xor=["subject"],
        exists=True,
        mandatory=True,
        position=-1,
        desc="specify the talairach.xfm file to check",
    )
    subject = traits.String(
        argstr="-subj %s",
        xor=["in_file"],
        mandatory=True,
        position=-1,
        desc="specify subject's name",
    )
    # optional
    threshold = traits.Float(
        default_value=0.010,
        usedefault=True,
        argstr="-T %.3f",
        desc="Talairach transforms for subjects with p-values <= T "
        + "are considered as very unlikely default=0.010",
    )


class CheckTalairachAlignmentOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="The input file for CheckTalairachAlignment")


class CheckTalairachAlignment(FSCommand):
    """
    This program detects Talairach alignment failures

    Examples
    ========

    >>> from nipype.interfaces.freesurfer import CheckTalairachAlignment
    >>> checker = CheckTalairachAlignment()

    >>> checker.inputs.in_file = 'trans.mat'
    >>> checker.inputs.threshold = 0.005
    >>> checker.cmdline
    'talairach_afd -T 0.005 -xfm trans.mat'

    >>> checker.run() # doctest: +SKIP
    """

    _cmd = "talairach_afd"
    input_spec = CheckTalairachAlignmentInputSpec
    output_spec = CheckTalairachAlignmentOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = self.inputs.in_file
        return outputs


class TalairachAVIInputSpec(FSTraitedSpec):
    in_file = File(argstr="--i %s", exists=True, mandatory=True, desc="input volume")
    out_file = File(
        argstr="--xfm %s", mandatory=True, exists=False, desc="output xfm file"
    )
    # optional
    atlas = traits.String(
        argstr="--atlas %s", desc="alternate target atlas (in freesurfer/average dir)"
    )


class TalairachAVIOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="The output transform for TalairachAVI")
    out_log = File(exists=False, desc="The output log file for TalairachAVI")
    out_txt = File(exists=False, desc="The output text file for TaliarachAVI")


class TalairachAVI(FSCommand):
    """
    Front-end for Avi Snyders image registration tool. Computes the
    talairach transform that maps the input volume to the MNI average_305.
    This does not add the xfm to the header of the input file. When called
    by recon-all, the xfm is added to the header after the transform is
    computed.

    Examples
    ========

    >>> from nipype.interfaces.freesurfer import TalairachAVI
    >>> example = TalairachAVI()
    >>> example.inputs.in_file = 'norm.mgz'
    >>> example.inputs.out_file = 'trans.mat'
    >>> example.cmdline
    'talairach_avi --i norm.mgz --xfm trans.mat'

    >>> example.run() # doctest: +SKIP
    """

    _cmd = "talairach_avi"
    input_spec = TalairachAVIInputSpec
    output_spec = TalairachAVIOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        outputs["out_log"] = os.path.abspath("talairach_avi.log")
        outputs["out_txt"] = os.path.join(
            os.path.dirname(self.inputs.out_file),
            "talsrcimg_to_" + str(self.inputs.atlas) + "t4_vox2vox.txt",
        )
        return outputs


class TalairachQCInputSpec(FSTraitedSpec):
    log_file = File(
        argstr="%s",
        mandatory=True,
        exists=True,
        position=0,
        desc="The log file for TalairachQC",
    )


class TalairachQC(FSScriptCommand):
    """
    Examples
    ========

    >>> from nipype.interfaces.freesurfer import TalairachQC
    >>> qc = TalairachQC()
    >>> qc.inputs.log_file = 'dirs.txt'
    >>> qc.cmdline
    'tal_QC_AZS dirs.txt'
    """

    _cmd = "tal_QC_AZS"
    input_spec = TalairachQCInputSpec
    output_spec = FSScriptOutputSpec


class RemoveNeckInputSpec(FSTraitedSpec):
    in_file = File(
        argstr="%s",
        exists=True,
        mandatory=True,
        position=-4,
        desc="Input file for RemoveNeck",
    )
    out_file = File(
        argstr="%s",
        exists=False,
        name_source=["in_file"],
        name_template="%s_noneck",
        hash_files=False,
        keep_extension=True,
        position=-1,
        desc="Output file for RemoveNeck",
    )
    transform = File(
        argstr="%s",
        exists=True,
        mandatory=True,
        position=-3,
        desc="Input transform file for RemoveNeck",
    )
    template = File(
        argstr="%s",
        exists=True,
        mandatory=True,
        position=-2,
        desc="Input template file for RemoveNeck",
    )
    # optional
    radius = traits.Int(argstr="-radius %d", desc="Radius")


class RemoveNeckOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Output file with neck removed")


class RemoveNeck(FSCommand):
    """
    Crops the neck out of the mri image

    Examples
    ========

    >>> from nipype.interfaces.freesurfer import TalairachQC
    >>> remove_neck = RemoveNeck()
    >>> remove_neck.inputs.in_file = 'norm.mgz'
    >>> remove_neck.inputs.transform = 'trans.mat'
    >>> remove_neck.inputs.template = 'trans.mat'
    >>> remove_neck.cmdline
    'mri_remove_neck norm.mgz trans.mat trans.mat norm_noneck.mgz'
    """

    _cmd = "mri_remove_neck"
    input_spec = RemoveNeckInputSpec
    output_spec = RemoveNeckOutputSpec

    def _gen_fname(self, name):
        if name == "out_file":
            return os.path.abspath("nu_noneck.mgz")
        return None

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


class MRIFillInputSpec(FSTraitedSpec):
    in_file = File(
        argstr="%s",
        mandatory=True,
        exists=True,
        position=-2,
        desc="Input white matter file",
    )
    out_file = File(
        argstr="%s",
        mandatory=True,
        exists=False,
        position=-1,
        desc="Output filled volume file name for MRIFill",
    )
    # optional
    segmentation = File(
        argstr="-segmentation %s",
        exists=True,
        desc="Input segmentation file for MRIFill",
    )
    transform = File(
        argstr="-xform %s", exists=True, desc="Input transform file for MRIFill"
    )
    log_file = File(argstr="-a %s", desc="Output log file for MRIFill")


class MRIFillOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Output file from MRIFill")
    log_file = File(desc="Output log file from MRIFill")


class MRIFill(FSCommand):
    """
    This program creates hemispheric cutting planes and fills white matter
    with specific values for subsequent surface tesselation.

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import MRIFill
    >>> fill = MRIFill()
    >>> fill.inputs.in_file = 'wm.mgz' # doctest: +SKIP
    >>> fill.inputs.out_file = 'filled.mgz' # doctest: +SKIP
    >>> fill.cmdline # doctest: +SKIP
    'mri_fill wm.mgz filled.mgz'
    """

    _cmd = "mri_fill"
    input_spec = MRIFillInputSpec
    output_spec = MRIFillOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        if isdefined(self.inputs.log_file):
            outputs["log_file"] = os.path.abspath(self.inputs.log_file)
        return outputs


class MRIsInflateInputSpec(FSTraitedSpec):
    in_file = File(
        argstr="%s",
        position=-2,
        mandatory=True,
        exists=True,
        copyfile=True,
        desc="Input file for MRIsInflate",
    )
    out_file = File(
        argstr="%s",
        position=-1,
        exists=False,
        name_source=["in_file"],
        name_template="%s.inflated",
        hash_files=False,
        keep_extension=True,
        desc="Output file for MRIsInflate",
    )
    # optional
    out_sulc = File(exists=False, xor=["no_save_sulc"], desc="Output sulc file")
    no_save_sulc = traits.Bool(
        argstr="-no-save-sulc", xor=["out_sulc"], desc="Do not save sulc file as output"
    )


class MRIsInflateOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Output file for MRIsInflate")
    out_sulc = File(exists=False, desc="Output sulc file")


class MRIsInflate(FSCommand):
    """
    This program will inflate a cortical surface.

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import MRIsInflate
    >>> inflate = MRIsInflate()
    >>> inflate.inputs.in_file = 'lh.pial'
    >>> inflate.inputs.no_save_sulc = True
    >>> inflate.cmdline # doctest: +SKIP
    'mris_inflate -no-save-sulc lh.pial lh.inflated'
    """

    _cmd = "mris_inflate"
    input_spec = MRIsInflateInputSpec
    output_spec = MRIsInflateOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        if not self.inputs.no_save_sulc:
            # if the sulc file will be saved
            outputs["out_sulc"] = os.path.abspath(self.inputs.out_sulc)
        return outputs


class SphereInputSpec(FSTraitedSpecOpenMP):
    in_file = File(
        argstr="%s",
        position=-2,
        copyfile=True,
        mandatory=True,
        exists=True,
        desc="Input file for Sphere",
    )
    out_file = File(
        argstr="%s",
        position=-1,
        exists=False,
        name_source=["in_file"],
        hash_files=False,
        name_template="%s.sphere",
        desc="Output file for Sphere",
    )
    # optional
    seed = traits.Int(
        argstr="-seed %d", desc="Seed for setting random number generator"
    )
    magic = traits.Bool(
        argstr="-q",
        desc="No documentation. Direct questions to analysis-bugs@nmr.mgh.harvard.edu",
    )
    in_smoothwm = File(
        exists=True,
        copyfile=True,
        desc="Input surface required when -q flag is not selected",
    )


class SphereOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Output file for Sphere")


class Sphere(FSCommandOpenMP):
    """
    This program will add a template into an average surface

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import Sphere
    >>> sphere = Sphere()
    >>> sphere.inputs.in_file = 'lh.pial'
    >>> sphere.cmdline
    'mris_sphere lh.pial lh.sphere'
    """

    _cmd = "mris_sphere"
    input_spec = SphereInputSpec
    output_spec = SphereOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


class FixTopologyInputSpec(FSTraitedSpec):
    in_orig = File(
        exists=True, mandatory=True, desc="Undocumented input file <hemisphere>.orig"
    )
    in_inflated = File(
        exists=True,
        mandatory=True,
        desc="Undocumented input file <hemisphere>.inflated",
    )
    in_brain = File(exists=True, mandatory=True, desc="Implicit input brain.mgz")
    in_wm = File(exists=True, mandatory=True, desc="Implicit input wm.mgz")
    hemisphere = traits.String(
        position=-1, argstr="%s", mandatory=True, desc="Hemisphere being processed"
    )
    subject_id = traits.String(
        "subject_id",
        position=-2,
        argstr="%s",
        mandatory=True,
        usedefault=True,
        desc="Subject being processed",
    )
    copy_inputs = traits.Bool(
        mandatory=True,
        desc="If running as a node, set this to True "
        + "otherwise, the topology fixing will be done "
        + "in place.",
    )

    # optional
    seed = traits.Int(
        argstr="-seed %d", desc="Seed for setting random number generator"
    )
    ga = traits.Bool(
        argstr="-ga",
        desc="No documentation. Direct questions to analysis-bugs@nmr.mgh.harvard.edu",
    )
    mgz = traits.Bool(
        argstr="-mgz",
        desc="No documentation. Direct questions to analysis-bugs@nmr.mgh.harvard.edu",
    )
    sphere = File(argstr="-sphere %s", desc="Sphere input file")


class FixTopologyOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Output file for FixTopology")


class FixTopology(FSCommand):
    """
    This program computes a mapping from the unit sphere onto the surface
    of the cortex from a previously generated approximation of the
    cortical surface, thus guaranteeing a topologically correct surface.

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import FixTopology
    >>> ft = FixTopology()
    >>> ft.inputs.in_orig = 'lh.orig' # doctest: +SKIP
    >>> ft.inputs.in_inflated = 'lh.inflated' # doctest: +SKIP
    >>> ft.inputs.sphere = 'lh.qsphere.nofix' # doctest: +SKIP
    >>> ft.inputs.hemisphere = 'lh'
    >>> ft.inputs.subject_id = '10335'
    >>> ft.inputs.mgz = True
    >>> ft.inputs.ga = True
    >>> ft.cmdline # doctest: +SKIP
    'mris_fix_topology -ga -mgz -sphere qsphere.nofix 10335 lh'
    """

    _cmd = "mris_fix_topology"
    input_spec = FixTopologyInputSpec
    output_spec = FixTopologyOutputSpec

    def run(self, **inputs):
        if self.inputs.copy_inputs:
            self.inputs.subjects_dir = os.getcwd()
            if "subjects_dir" in inputs:
                inputs["subjects_dir"] = self.inputs.subjects_dir
            hemi = self.inputs.hemisphere
            copy2subjdir(self, self.inputs.sphere, folder="surf")
            # the orig file is edited in place
            self.inputs.in_orig = copy2subjdir(
                self,
                self.inputs.in_orig,
                folder="surf",
                basename="{0}.orig".format(hemi),
            )
            copy2subjdir(
                self,
                self.inputs.in_inflated,
                folder="surf",
                basename="{0}.inflated".format(hemi),
            )
            copy2subjdir(self, self.inputs.in_brain, folder="mri", basename="brain.mgz")
            copy2subjdir(self, self.inputs.in_wm, folder="mri", basename="wm.mgz")
        return super(FixTopology, self).run(**inputs)

    def _format_arg(self, name, spec, value):
        if name == "sphere":
            # get the basename and take out the hemisphere
            suffix = os.path.basename(value).split(".", 1)[1]
            return spec.argstr % suffix
        return super(FixTopology, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.in_orig)
        return outputs


class EulerNumberInputSpec(FSTraitedSpec):
    in_file = File(
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        desc="Input file for EulerNumber",
    )


class EulerNumberOutputSpec(TraitedSpec):
    euler = traits.Int(
        desc="Euler number of cortical surface. A value of 2 signals a "
        "topologically correct surface model with no holes"
    )
    defects = traits.Int(desc="Number of defects")


class EulerNumber(FSCommand):
    """
    This program computes EulerNumber for a cortical surface

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import EulerNumber
    >>> ft = EulerNumber()
    >>> ft.inputs.in_file = 'lh.pial'
    >>> ft.cmdline
    'mris_euler_number lh.pial'
    """

    _cmd = "mris_euler_number"
    input_spec = EulerNumberInputSpec
    output_spec = EulerNumberOutputSpec

    def _run_interface(self, runtime):
        runtime = super()._run_interface(runtime)
        self._parse_output(runtime.stdout, runtime.stderr)
        return runtime

    def _parse_output(self, stdout, stderr):
        """Parse stdout / stderr and extract defects"""
        m = re.search(r"(?<=total defect index = )\d+", stdout or stderr)
        if m is None:
            raise RuntimeError("Could not fetch defect index")
        self._defects = int(m.group())

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["defects"] = self._defects
        outputs["euler"] = 2 - (2 * self._defects)
        return outputs


class RemoveIntersectionInputSpec(FSTraitedSpec):
    in_file = File(
        argstr="%s",
        position=-2,
        mandatory=True,
        exists=True,
        copyfile=True,
        desc="Input file for RemoveIntersection",
    )
    out_file = File(
        argstr="%s",
        position=-1,
        exists=False,
        name_source=["in_file"],
        name_template="%s",
        hash_files=False,
        keep_extension=True,
        desc="Output file for RemoveIntersection",
    )


class RemoveIntersectionOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Output file for RemoveIntersection")


class RemoveIntersection(FSCommand):
    """
    This program removes the intersection of the given MRI

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import RemoveIntersection
    >>> ri = RemoveIntersection()
    >>> ri.inputs.in_file = 'lh.pial'
    >>> ri.cmdline
    'mris_remove_intersection lh.pial lh.pial'
    """

    _cmd = "mris_remove_intersection"
    input_spec = RemoveIntersectionInputSpec
    output_spec = RemoveIntersectionOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


class MakeSurfacesInputSpec(FSTraitedSpec):
    # required
    hemisphere = traits.Enum(
        "lh",
        "rh",
        position=-1,
        argstr="%s",
        mandatory=True,
        desc="Hemisphere being processed",
    )
    subject_id = traits.String(
        "subject_id",
        usedefault=True,
        position=-2,
        argstr="%s",
        mandatory=True,
        desc="Subject being processed",
    )
    # implicit
    in_orig = File(
        exists=True,
        mandatory=True,
        argstr="-orig %s",
        desc="Implicit input file <hemisphere>.orig",
    )
    in_wm = File(exists=True, mandatory=True, desc="Implicit input file wm.mgz")
    in_filled = File(exists=True, mandatory=True, desc="Implicit input file filled.mgz")
    # optional
    in_white = File(exists=True, desc="Implicit input that is sometimes used")
    in_label = File(
        exists=True,
        xor=["noaparc"],
        desc="Implicit input label/<hemisphere>.aparc.annot",
    )
    orig_white = File(
        argstr="-orig_white %s",
        exists=True,
        desc="Specify a white surface to start with",
    )
    orig_pial = File(
        argstr="-orig_pial %s",
        exists=True,
        requires=["in_label"],
        desc="Specify a pial surface to start with",
    )
    fix_mtl = traits.Bool(argstr="-fix_mtl", desc="Undocumented flag")
    no_white = traits.Bool(argstr="-nowhite", desc="Undocumented flag")
    white_only = traits.Bool(argstr="-whiteonly", desc="Undocumented flage")
    in_aseg = File(argstr="-aseg %s", exists=True, desc="Input segmentation file")
    in_T1 = File(argstr="-T1 %s", exists=True, desc="Input brain or T1 file")
    mgz = traits.Bool(
        argstr="-mgz",
        desc="No documentation. Direct questions to analysis-bugs@nmr.mgh.harvard.edu",
    )
    noaparc = traits.Bool(
        argstr="-noaparc",
        xor=["in_label"],
        desc="No documentation. Direct questions to analysis-bugs@nmr.mgh.harvard.edu",
    )
    maximum = traits.Float(
        argstr="-max %.1f", desc="No documentation (used for longitudinal processing)"
    )
    longitudinal = traits.Bool(
        argstr="-long", desc="No documentation (used for longitudinal processing)"
    )
    white = traits.String(argstr="-white %s", desc="White surface name")
    copy_inputs = traits.Bool(
        desc="If running as a node, set this to True."
        + "This will copy the input files to the node "
        + "directory."
    )


class MakeSurfacesOutputSpec(TraitedSpec):
    out_white = File(exists=False, desc="Output white matter hemisphere surface")
    out_curv = File(exists=False, desc="Output curv file for MakeSurfaces")
    out_area = File(exists=False, desc="Output area file for MakeSurfaces")
    out_cortex = File(exists=False, desc="Output cortex file for MakeSurfaces")
    out_pial = File(exists=False, desc="Output pial surface for MakeSurfaces")
    out_thickness = File(exists=False, desc="Output thickness file for MakeSurfaces")


class MakeSurfaces(FSCommand):
    """
    This program positions the tessellation of the cortical surface at the
    white matter surface, then the gray matter surface and generate
    surface files for these surfaces as well as a 'curvature' file for the
    cortical thickness, and a surface file which approximates layer IV of
    the cortical sheet.

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import MakeSurfaces
    >>> makesurfaces = MakeSurfaces()
    >>> makesurfaces.inputs.hemisphere = 'lh'
    >>> makesurfaces.inputs.subject_id = '10335'
    >>> makesurfaces.inputs.in_orig = 'lh.pial'
    >>> makesurfaces.inputs.in_wm = 'wm.mgz'
    >>> makesurfaces.inputs.in_filled = 'norm.mgz'
    >>> makesurfaces.inputs.in_label = 'aparc+aseg.nii'
    >>> makesurfaces.inputs.in_T1 = 'T1.mgz'
    >>> makesurfaces.inputs.orig_pial = 'lh.pial'
    >>> makesurfaces.cmdline
    'mris_make_surfaces -T1 T1.mgz -orig pial -orig_pial pial 10335 lh'
    """

    _cmd = "mris_make_surfaces"
    input_spec = MakeSurfacesInputSpec
    output_spec = MakeSurfacesOutputSpec

    def run(self, **inputs):
        if self.inputs.copy_inputs:
            self.inputs.subjects_dir = os.getcwd()
            if "subjects_dir" in inputs:
                inputs["subjects_dir"] = self.inputs.subjects_dir
            copy2subjdir(self, self.inputs.in_wm, folder="mri", basename="wm.mgz")
            copy2subjdir(
                self, self.inputs.in_filled, folder="mri", basename="filled.mgz"
            )
            copy2subjdir(
                self,
                self.inputs.in_white,
                "surf",
                "{0}.white".format(self.inputs.hemisphere),
            )
            for originalfile in [self.inputs.in_aseg, self.inputs.in_T1]:
                copy2subjdir(self, originalfile, folder="mri")
            for originalfile in [
                self.inputs.orig_white,
                self.inputs.orig_pial,
                self.inputs.in_orig,
            ]:
                copy2subjdir(self, originalfile, folder="surf")
            if isdefined(self.inputs.in_label):
                copy2subjdir(
                    self,
                    self.inputs.in_label,
                    "label",
                    "{0}.aparc.annot".format(self.inputs.hemisphere),
                )
            else:
                os.makedirs(
                    os.path.join(
                        self.inputs.subjects_dir, self.inputs.subject_id, "label"
                    )
                )
        return super(MakeSurfaces, self).run(**inputs)

    def _format_arg(self, name, spec, value):
        if name in ["in_T1", "in_aseg"]:
            # These inputs do not take full paths as inputs or even basenames
            basename = os.path.basename(value)
            # whent the -mgz flag is specified, it assumes the mgz extension
            if self.inputs.mgz:
                prefix = os.path.splitext(basename)[0]
            else:
                prefix = basename
            if prefix == "aseg":
                return  # aseg is already the default
            return spec.argstr % prefix
        elif name in ["orig_white", "orig_pial"]:
            # these inputs do take full file paths or even basenames
            basename = os.path.basename(value)
            suffix = basename.split(".")[1]
            return spec.argstr % suffix
        elif name == "in_orig":
            if value.endswith("lh.orig") or value.endswith("rh.orig"):
                # {lh,rh}.orig inputs are not sepcified on command line
                return
            else:
                # if the input orig file is different than lh.orig or rh.orig
                # these inputs do take full file paths or even basenames
                basename = os.path.basename(value)
                suffix = basename.split(".")[1]
                return spec.argstr % suffix
        return super(MakeSurfaces, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()
        # Outputs are saved in the surf directory
        dest_dir = os.path.join(
            self.inputs.subjects_dir, self.inputs.subject_id, "surf"
        )
        # labels are saved in the label directory
        label_dir = os.path.join(
            self.inputs.subjects_dir, self.inputs.subject_id, "label"
        )
        if not self.inputs.no_white:
            outputs["out_white"] = os.path.join(
                dest_dir, str(self.inputs.hemisphere) + ".white"
            )
        # The curv and area files must have the hemisphere names as a prefix
        outputs["out_curv"] = os.path.join(
            dest_dir, str(self.inputs.hemisphere) + ".curv"
        )
        outputs["out_area"] = os.path.join(
            dest_dir, str(self.inputs.hemisphere) + ".area"
        )
        # Something determines when a pial surface and thickness file is generated
        # but documentation doesn't say what.
        # The orig_pial input is just a guess
        if isdefined(self.inputs.orig_pial) or self.inputs.white == "NOWRITE":
            outputs["out_curv"] = outputs["out_curv"] + ".pial"
            outputs["out_area"] = outputs["out_area"] + ".pial"
            outputs["out_pial"] = os.path.join(
                dest_dir, str(self.inputs.hemisphere) + ".pial"
            )
            outputs["out_thickness"] = os.path.join(
                dest_dir, str(self.inputs.hemisphere) + ".thickness"
            )
        else:
            # when a pial surface is generated, the cortex label file is not
            # generated
            outputs["out_cortex"] = os.path.join(
                label_dir, str(self.inputs.hemisphere) + ".cortex.label"
            )
        return outputs


class CurvatureInputSpec(FSTraitedSpec):
    in_file = File(
        argstr="%s",
        position=-2,
        mandatory=True,
        exists=True,
        copyfile=True,
        desc="Input file for Curvature",
    )
    # optional
    threshold = traits.Float(argstr="-thresh %.3f", desc="Undocumented input threshold")
    n = traits.Bool(argstr="-n", desc="Undocumented boolean flag")
    averages = traits.Int(
        argstr="-a %d",
        desc="Perform this number iterative averages of curvature measure before saving",
    )
    save = traits.Bool(
        argstr="-w",
        desc="Save curvature files (will only generate screen output without this option)",
    )
    distances = traits.Tuple(
        traits.Int,
        traits.Int,
        argstr="-distances %d %d",
        desc="Undocumented input integer distances",
    )
    copy_input = traits.Bool(desc="Copy input file to current directory")


class CurvatureOutputSpec(TraitedSpec):
    out_mean = File(exists=False, desc="Mean curvature output file")
    out_gauss = File(exists=False, desc="Gaussian curvature output file")


class Curvature(FSCommand):
    """
    This program will compute the second fundamental form of a cortical
    surface. It will create two new files <hemi>.<surface>.H and
    <hemi>.<surface>.K with the mean and Gaussian curvature respectively.

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import Curvature
    >>> curv = Curvature()
    >>> curv.inputs.in_file = 'lh.pial'
    >>> curv.inputs.save = True
    >>> curv.cmdline
    'mris_curvature -w lh.pial'
    """

    _cmd = "mris_curvature"
    input_spec = CurvatureInputSpec
    output_spec = CurvatureOutputSpec

    def _format_arg(self, name, spec, value):
        if self.inputs.copy_input:
            if name == "in_file":
                basename = os.path.basename(value)
                return spec.argstr % basename
        return super(Curvature, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()
        if self.inputs.copy_input:
            in_file = os.path.basename(self.inputs.in_file)
        else:
            in_file = self.inputs.in_file
        outputs["out_mean"] = os.path.abspath(in_file) + ".H"
        outputs["out_gauss"] = os.path.abspath(in_file) + ".K"
        return outputs


class CurvatureStatsInputSpec(FSTraitedSpec):
    surface = File(
        argstr="-F %s", exists=True, desc="Specify surface file for CurvatureStats"
    )
    curvfile1 = File(
        argstr="%s",
        position=-2,
        mandatory=True,
        exists=True,
        desc="Input file for CurvatureStats",
    )
    curvfile2 = File(
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        desc="Input file for CurvatureStats",
    )
    hemisphere = traits.Enum(
        "lh",
        "rh",
        position=-3,
        argstr="%s",
        mandatory=True,
        desc="Hemisphere being processed",
    )
    subject_id = traits.String(
        "subject_id",
        usedefault=True,
        position=-4,
        argstr="%s",
        mandatory=True,
        desc="Subject being processed",
    )
    out_file = File(
        argstr="-o %s",
        exists=False,
        name_source=["hemisphere"],
        name_template="%s.curv.stats",
        hash_files=False,
        desc="Output curvature stats file",
    )
    # optional
    min_max = traits.Bool(
        argstr="-m", desc="Output min / max information for the processed curvature."
    )
    values = traits.Bool(
        argstr="-G", desc="Triggers a series of derived curvature values"
    )
    write = traits.Bool(argstr="--writeCurvatureFiles", desc="Write curvature files")
    copy_inputs = traits.Bool(
        desc="If running as a node, set this to True."
        + "This will copy the input files to the node "
        + "directory."
    )


class CurvatureStatsOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Output curvature stats file")


class CurvatureStats(FSCommand):
    """
    In its simplest usage, 'mris_curvature_stats' will compute a set
    of statistics on its input <curvFile>. These statistics are the
    mean and standard deviation of the particular curvature on the
    surface, as well as the results from several surface-based
    integrals.

    Additionally, 'mris_curvature_stats' can report the max/min
    curvature values, and compute a simple histogram based on
    all curvature values.

    Curvatures can also be normalised and constrained to a given
    range before computation.

    Principal curvature (K, H, k1 and k2) calculations on a surface
    structure can also be performed, as well as several functions
    derived from k1 and k2.

    Finally, all output to the console, as well as any new
    curvatures that result from the above calculations can be
    saved to a series of text and binary-curvature files.

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import CurvatureStats
    >>> curvstats = CurvatureStats()
    >>> curvstats.inputs.hemisphere = 'lh'
    >>> curvstats.inputs.curvfile1 = 'lh.pial'
    >>> curvstats.inputs.curvfile2 = 'lh.pial'
    >>> curvstats.inputs.surface = 'lh.pial'
    >>> curvstats.inputs.out_file = 'lh.curv.stats'
    >>> curvstats.inputs.values = True
    >>> curvstats.inputs.min_max = True
    >>> curvstats.inputs.write = True
    >>> curvstats.cmdline
    'mris_curvature_stats -m -o lh.curv.stats -F pial -G --writeCurvatureFiles subject_id lh pial pial'
    """

    _cmd = "mris_curvature_stats"
    input_spec = CurvatureStatsInputSpec
    output_spec = CurvatureStatsOutputSpec

    def _format_arg(self, name, spec, value):
        if name in ["surface", "curvfile1", "curvfile2"]:
            prefix = os.path.basename(value).split(".")[1]
            return spec.argstr % prefix
        return super(CurvatureStats, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs

    def run(self, **inputs):
        if self.inputs.copy_inputs:
            self.inputs.subjects_dir = os.getcwd()
            if "subjects_dir" in inputs:
                inputs["subjects_dir"] = self.inputs.subjects_dir
            copy2subjdir(self, self.inputs.surface, "surf")
            copy2subjdir(self, self.inputs.curvfile1, "surf")
            copy2subjdir(self, self.inputs.curvfile2, "surf")
        return super(CurvatureStats, self).run(**inputs)


class JacobianInputSpec(FSTraitedSpec):
    # required
    in_origsurf = File(
        argstr="%s", position=-3, mandatory=True, exists=True, desc="Original surface"
    )
    in_mappedsurf = File(
        argstr="%s", position=-2, mandatory=True, exists=True, desc="Mapped surface"
    )
    # optional
    out_file = File(
        argstr="%s",
        exists=False,
        position=-1,
        name_source=["in_origsurf"],
        hash_files=False,
        name_template="%s.jacobian",
        keep_extension=False,
        desc="Output Jacobian of the surface mapping",
    )


class JacobianOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Output Jacobian of the surface mapping")


class Jacobian(FSCommand):
    """
    This program computes the Jacobian of a surface mapping.

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import Jacobian
    >>> jacobian = Jacobian()
    >>> jacobian.inputs.in_origsurf = 'lh.pial'
    >>> jacobian.inputs.in_mappedsurf = 'lh.pial'
    >>> jacobian.cmdline
    'mris_jacobian lh.pial lh.pial lh.jacobian'
    """

    _cmd = "mris_jacobian"
    input_spec = JacobianInputSpec
    output_spec = JacobianOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


class MRIsCalcInputSpec(FSTraitedSpec):
    # required
    in_file1 = File(
        argstr="%s", position=-3, mandatory=True, exists=True, desc="Input file 1"
    )
    action = traits.String(
        argstr="%s",
        position=-2,
        mandatory=True,
        desc="Action to perform on input file(s)",
    )
    out_file = File(
        argstr="-o %s", mandatory=True, desc="Output file after calculation"
    )

    # optional
    in_file2 = File(
        argstr="%s",
        exists=True,
        position=-1,
        xor=["in_float", "in_int"],
        desc="Input file 2",
    )
    in_float = traits.Float(
        argstr="%f", position=-1, xor=["in_file2", "in_int"], desc="Input float"
    )
    in_int = traits.Int(
        argstr="%d", position=-1, xor=["in_file2", "in_float"], desc="Input integer"
    )


class MRIsCalcOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Output file after calculation")


class MRIsCalc(FSCommand):
    """
    'mris_calc' is a simple calculator that operates on FreeSurfer
    curvatures and volumes. In most cases, the calculator functions with
    three arguments: two inputs and an <ACTION> linking them. Some
    actions, however, operate with only one input <file1>. In all cases,
    the first input <file1> is the name of a FreeSurfer curvature overlay
    (e.g. rh.curv) or volume file (e.g. orig.mgz). For two inputs, the
    calculator first assumes that the second input is a file. If, however,
    this second input file doesn't exist, the calculator assumes it refers
    to a float number, which is then processed according to <ACTION>.Note:
    <file1> and <file2> should typically be generated on the same subject.

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import MRIsCalc
    >>> example = MRIsCalc()
    >>> example.inputs.in_file1 = 'lh.area' # doctest: +SKIP
    >>> example.inputs.in_file2 = 'lh.area.pial' # doctest: +SKIP
    >>> example.inputs.action = 'add'
    >>> example.inputs.out_file = 'area.mid'
    >>> example.cmdline # doctest: +SKIP
    'mris_calc -o lh.area.mid lh.area add lh.area.pial'
    """

    _cmd = "mris_calc"
    input_spec = MRIsCalcInputSpec
    output_spec = MRIsCalcOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


class VolumeMaskInputSpec(FSTraitedSpec):
    left_whitelabel = traits.Int(
        argstr="--label_left_white %d", mandatory=True, desc="Left white matter label"
    )
    left_ribbonlabel = traits.Int(
        argstr="--label_left_ribbon %d",
        mandatory=True,
        desc="Left cortical ribbon label",
    )
    right_whitelabel = traits.Int(
        argstr="--label_right_white %d", mandatory=True, desc="Right white matter label"
    )
    right_ribbonlabel = traits.Int(
        argstr="--label_right_ribbon %d",
        mandatory=True,
        desc="Right cortical ribbon label",
    )
    lh_pial = File(mandatory=True, exists=True, desc="Implicit input left pial surface")
    rh_pial = File(
        mandatory=True, exists=True, desc="Implicit input right pial surface"
    )
    lh_white = File(
        mandatory=True, exists=True, desc="Implicit input left white matter surface"
    )
    rh_white = File(
        mandatory=True, exists=True, desc="Implicit input right white matter surface"
    )
    aseg = File(
        exists=True,
        xor=["in_aseg"],
        desc="Implicit aseg.mgz segmentation. "
        + "Specify a different aseg by using the 'in_aseg' input.",
    )
    subject_id = traits.String(
        "subject_id",
        usedefault=True,
        position=-1,
        argstr="%s",
        mandatory=True,
        desc="Subject being processed",
    )
    # optional
    in_aseg = File(
        argstr="--aseg_name %s",
        exists=True,
        xor=["aseg"],
        desc="Input aseg file for VolumeMask",
    )
    save_ribbon = traits.Bool(
        argstr="--save_ribbon",
        desc="option to save just the ribbon for the "
        + "hemispheres in the format ?h.ribbon.mgz",
    )
    copy_inputs = traits.Bool(
        desc="If running as a node, set this to True."
        + "This will copy the implicit input files to the "
        + "node directory."
    )


class VolumeMaskOutputSpec(TraitedSpec):
    out_ribbon = File(exists=False, desc="Output cortical ribbon mask")
    lh_ribbon = File(exists=False, desc="Output left cortical ribbon mask")
    rh_ribbon = File(exists=False, desc="Output right cortical ribbon mask")


class VolumeMask(FSCommand):
    """
    Computes a volume mask, at the same resolution as the
    <subject>/mri/brain.mgz.  The volume mask contains 4 values: LH_WM
    (default 10), LH_GM (default 100), RH_WM (default 20), RH_GM (default
    200).
    The algorithm uses the 4 surfaces situated in <subject>/surf/
    [lh|rh].[white|pial] and labels voxels based on the
    signed-distance function from the surface.

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import VolumeMask
    >>> volmask = VolumeMask()
    >>> volmask.inputs.left_whitelabel = 2
    >>> volmask.inputs.left_ribbonlabel = 3
    >>> volmask.inputs.right_whitelabel = 41
    >>> volmask.inputs.right_ribbonlabel = 42
    >>> volmask.inputs.lh_pial = 'lh.pial'
    >>> volmask.inputs.rh_pial = 'lh.pial'
    >>> volmask.inputs.lh_white = 'lh.pial'
    >>> volmask.inputs.rh_white = 'lh.pial'
    >>> volmask.inputs.subject_id = '10335'
    >>> volmask.inputs.save_ribbon = True
    >>> volmask.cmdline
    'mris_volmask --label_left_ribbon 3 --label_left_white 2 --label_right_ribbon 42 --label_right_white 41 --save_ribbon 10335'
    """

    _cmd = "mris_volmask"
    input_spec = VolumeMaskInputSpec
    output_spec = VolumeMaskOutputSpec

    def run(self, **inputs):
        if self.inputs.copy_inputs:
            self.inputs.subjects_dir = os.getcwd()
            if "subjects_dir" in inputs:
                inputs["subjects_dir"] = self.inputs.subjects_dir
            copy2subjdir(self, self.inputs.lh_pial, "surf", "lh.pial")
            copy2subjdir(self, self.inputs.rh_pial, "surf", "rh.pial")
            copy2subjdir(self, self.inputs.lh_white, "surf", "lh.white")
            copy2subjdir(self, self.inputs.rh_white, "surf", "rh.white")
            copy2subjdir(self, self.inputs.in_aseg, "mri")
            copy2subjdir(self, self.inputs.aseg, "mri", "aseg.mgz")

        return super(VolumeMask, self).run(**inputs)

    def _format_arg(self, name, spec, value):
        if name == "in_aseg":
            return spec.argstr % os.path.basename(value).rstrip(".mgz")
        return super(VolumeMask, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()
        out_dir = os.path.join(self.inputs.subjects_dir, self.inputs.subject_id, "mri")
        outputs["out_ribbon"] = os.path.join(out_dir, "ribbon.mgz")
        if self.inputs.save_ribbon:
            outputs["rh_ribbon"] = os.path.join(out_dir, "rh.ribbon.mgz")
            outputs["lh_ribbon"] = os.path.join(out_dir, "lh.ribbon.mgz")
        return outputs


class ParcellationStatsInputSpec(FSTraitedSpec):
    # required
    subject_id = traits.String(
        "subject_id",
        usedefault=True,
        position=-3,
        argstr="%s",
        mandatory=True,
        desc="Subject being processed",
    )
    hemisphere = traits.Enum(
        "lh",
        "rh",
        position=-2,
        argstr="%s",
        mandatory=True,
        desc="Hemisphere being processed",
    )
    # implicit
    wm = File(
        mandatory=True, exists=True, desc="Input file must be <subject_id>/mri/wm.mgz"
    )
    lh_white = File(
        mandatory=True,
        exists=True,
        desc="Input file must be <subject_id>/surf/lh.white",
    )
    rh_white = File(
        mandatory=True,
        exists=True,
        desc="Input file must be <subject_id>/surf/rh.white",
    )
    lh_pial = File(
        mandatory=True, exists=True, desc="Input file must be <subject_id>/surf/lh.pial"
    )
    rh_pial = File(
        mandatory=True, exists=True, desc="Input file must be <subject_id>/surf/rh.pial"
    )
    transform = File(
        mandatory=True,
        exists=True,
        desc="Input file must be <subject_id>/mri/transforms/talairach.xfm",
    )
    thickness = File(
        mandatory=True,
        exists=True,
        desc="Input file must be <subject_id>/surf/?h.thickness",
    )
    brainmask = File(
        mandatory=True,
        exists=True,
        desc="Input file must be <subject_id>/mri/brainmask.mgz",
    )
    aseg = File(
        mandatory=True,
        exists=True,
        desc="Input file must be <subject_id>/mri/aseg.presurf.mgz",
    )
    ribbon = File(
        mandatory=True,
        exists=True,
        desc="Input file must be <subject_id>/mri/ribbon.mgz",
    )
    cortex_label = File(exists=True, desc="implicit input file {hemi}.cortex.label")
    # optional
    surface = traits.String(
        position=-1, argstr="%s", desc="Input surface (e.g. 'white')"
    )
    mgz = traits.Bool(argstr="-mgz", desc="Look for mgz files")
    in_cortex = File(argstr="-cortex %s", exists=True, desc="Input cortex label")
    in_annotation = File(
        argstr="-a %s",
        exists=True,
        xor=["in_label"],
        desc="compute properties for each label in the annotation file separately",
    )
    in_label = File(
        argstr="-l %s",
        exists=True,
        xor=["in_annotatoin", "out_color"],
        desc="limit calculations to specified label",
    )
    tabular_output = traits.Bool(argstr="-b", desc="Tabular output")
    out_table = File(
        argstr="-f %s",
        exists=False,
        genfile=True,
        requires=["tabular_output"],
        desc="Table output to tablefile",
    )
    out_color = File(
        argstr="-c %s",
        exists=False,
        genfile=True,
        xor=["in_label"],
        desc="Output annotation files's colortable to text file",
    )
    copy_inputs = traits.Bool(
        desc="If running as a node, set this to True."
        + "This will copy the input files to the node "
        + "directory."
    )
    th3 = traits.Bool(
        argstr="-th3",
        requires=["cortex_label"],
        desc="turns on new vertex-wise volume calc for mris_anat_stats",
    )


class ParcellationStatsOutputSpec(TraitedSpec):
    out_table = File(exists=False, desc="Table output to tablefile")
    out_color = File(
        exists=False, desc="Output annotation files's colortable to text file"
    )


class ParcellationStats(FSCommand):
    """
    This program computes a number of anatomical properties.

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import ParcellationStats
    >>> import os
    >>> parcstats = ParcellationStats()
    >>> parcstats.inputs.subject_id = '10335'
    >>> parcstats.inputs.hemisphere = 'lh'
    >>> parcstats.inputs.wm = './../mri/wm.mgz' # doctest: +SKIP
    >>> parcstats.inputs.transform = './../mri/transforms/talairach.xfm' # doctest: +SKIP
    >>> parcstats.inputs.brainmask = './../mri/brainmask.mgz' # doctest: +SKIP
    >>> parcstats.inputs.aseg = './../mri/aseg.presurf.mgz' # doctest: +SKIP
    >>> parcstats.inputs.ribbon = './../mri/ribbon.mgz' # doctest: +SKIP
    >>> parcstats.inputs.lh_pial = 'lh.pial' # doctest: +SKIP
    >>> parcstats.inputs.rh_pial = 'lh.pial' # doctest: +SKIP
    >>> parcstats.inputs.lh_white = 'lh.white' # doctest: +SKIP
    >>> parcstats.inputs.rh_white = 'rh.white' # doctest: +SKIP
    >>> parcstats.inputs.thickness = 'lh.thickness' # doctest: +SKIP
    >>> parcstats.inputs.surface = 'white'
    >>> parcstats.inputs.out_table = 'lh.test.stats'
    >>> parcstats.inputs.out_color = 'test.ctab'
    >>> parcstats.cmdline # doctest: +SKIP
    'mris_anatomical_stats -c test.ctab -f lh.test.stats 10335 lh white'
    """

    _cmd = "mris_anatomical_stats"
    input_spec = ParcellationStatsInputSpec
    output_spec = ParcellationStatsOutputSpec

    def run(self, **inputs):
        if self.inputs.copy_inputs:
            self.inputs.subjects_dir = os.getcwd()
            if "subjects_dir" in inputs:
                inputs["subjects_dir"] = self.inputs.subjects_dir
            copy2subjdir(self, self.inputs.lh_white, "surf", "lh.white")
            copy2subjdir(self, self.inputs.lh_pial, "surf", "lh.pial")
            copy2subjdir(self, self.inputs.rh_white, "surf", "rh.white")
            copy2subjdir(self, self.inputs.rh_pial, "surf", "rh.pial")
            copy2subjdir(self, self.inputs.wm, "mri", "wm.mgz")
            copy2subjdir(
                self,
                self.inputs.transform,
                os.path.join("mri", "transforms"),
                "talairach.xfm",
            )
            copy2subjdir(self, self.inputs.brainmask, "mri", "brainmask.mgz")
            copy2subjdir(self, self.inputs.aseg, "mri", "aseg.presurf.mgz")
            copy2subjdir(self, self.inputs.ribbon, "mri", "ribbon.mgz")
            copy2subjdir(
                self,
                self.inputs.thickness,
                "surf",
                "{0}.thickness".format(self.inputs.hemisphere),
            )
            if isdefined(self.inputs.cortex_label):
                copy2subjdir(
                    self,
                    self.inputs.cortex_label,
                    "label",
                    "{0}.cortex.label".format(self.inputs.hemisphere),
                )
        createoutputdirs(self._list_outputs())
        return super(ParcellationStats, self).run(**inputs)

    def _gen_filename(self, name):
        if name in ["out_table", "out_color"]:
            return self._list_outputs()[name]
        return None

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.out_table):
            outputs["out_table"] = os.path.abspath(self.inputs.out_table)
        else:
            # subject stats directory
            stats_dir = os.path.join(
                self.inputs.subjects_dir, self.inputs.subject_id, "stats"
            )
            if isdefined(self.inputs.in_annotation):
                # if out_table is not defined just tag .stats on the end
                # instead of .annot
                if self.inputs.surface == "pial":
                    basename = os.path.basename(self.inputs.in_annotation).replace(
                        ".annot", ".pial.stats"
                    )
                else:
                    basename = os.path.basename(self.inputs.in_annotation).replace(
                        ".annot", ".stats"
                    )
            elif isdefined(self.inputs.in_label):
                # if out_table is not defined just tag .stats on the end
                # instead of .label
                if self.inputs.surface == "pial":
                    basename = os.path.basename(self.inputs.in_label).replace(
                        ".label", ".pial.stats"
                    )
                else:
                    basename = os.path.basename(self.inputs.in_label).replace(
                        ".label", ".stats"
                    )
            else:
                basename = str(self.inputs.hemisphere) + ".aparc.annot.stats"
            outputs["out_table"] = os.path.join(stats_dir, basename)
        if isdefined(self.inputs.out_color):
            outputs["out_color"] = os.path.abspath(self.inputs.out_color)
        else:
            # subject label directory
            out_dir = os.path.join(
                self.inputs.subjects_dir, self.inputs.subject_id, "label"
            )
            if isdefined(self.inputs.in_annotation):
                # find the annotation name (if it exists)
                basename = os.path.basename(self.inputs.in_annotation)
                for item in ["lh.", "rh.", "aparc.", "annot"]:
                    basename = basename.replace(item, "")
                annot = basename
                # if the out_color table is not defined, one with the annotation
                # name will be created
                if "BA" in annot:
                    outputs["out_color"] = os.path.join(out_dir, annot + "ctab")
                else:
                    outputs["out_color"] = os.path.join(
                        out_dir, "aparc.annot." + annot + "ctab"
                    )
            else:
                outputs["out_color"] = os.path.join(out_dir, "aparc.annot.ctab")
        return outputs


class ContrastInputSpec(FSTraitedSpec):
    # required
    subject_id = traits.String(
        "subject_id",
        argstr="--s %s",
        usedefault=True,
        mandatory=True,
        desc="Subject being processed",
    )
    hemisphere = traits.Enum(
        "lh",
        "rh",
        argstr="--%s-only",
        mandatory=True,
        desc="Hemisphere being processed",
    )
    # implicit
    thickness = File(
        mandatory=True,
        exists=True,
        desc="Input file must be <subject_id>/surf/?h.thickness",
    )
    white = File(
        mandatory=True,
        exists=True,
        desc="Input file must be <subject_id>/surf/<hemisphere>.white",
    )
    annotation = File(
        mandatory=True,
        exists=True,
        desc="Input annotation file must be <subject_id>/label/<hemisphere>.aparc.annot",
    )
    cortex = File(
        mandatory=True,
        exists=True,
        desc="Input cortex label must be <subject_id>/label/<hemisphere>.cortex.label",
    )
    orig = File(exists=True, mandatory=True, desc="Implicit input file mri/orig.mgz")
    rawavg = File(
        exists=True, mandatory=True, desc="Implicit input file mri/rawavg.mgz"
    )
    copy_inputs = traits.Bool(
        desc="If running as a node, set this to True."
        + "This will copy the input files to the node "
        + "directory."
    )


class ContrastOutputSpec(TraitedSpec):
    out_contrast = File(exists=False, desc="Output contrast file from Contrast")
    out_stats = File(exists=False, desc="Output stats file from Contrast")
    out_log = File(exists=True, desc="Output log from Contrast")


class Contrast(FSCommand):
    """
    Compute surface-wise gray/white contrast

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import Contrast
    >>> contrast = Contrast()
    >>> contrast.inputs.subject_id = '10335'
    >>> contrast.inputs.hemisphere = 'lh'
    >>> contrast.inputs.white = 'lh.white' # doctest: +SKIP
    >>> contrast.inputs.thickness = 'lh.thickness' # doctest: +SKIP
    >>> contrast.inputs.annotation = '../label/lh.aparc.annot' # doctest: +SKIP
    >>> contrast.inputs.cortex = '../label/lh.cortex.label' # doctest: +SKIP
    >>> contrast.inputs.rawavg = '../mri/rawavg.mgz' # doctest: +SKIP
    >>> contrast.inputs.orig = '../mri/orig.mgz' # doctest: +SKIP
    >>> contrast.cmdline # doctest: +SKIP
    'pctsurfcon --lh-only --s 10335'
    """

    _cmd = "pctsurfcon"
    input_spec = ContrastInputSpec
    output_spec = ContrastOutputSpec

    def run(self, **inputs):
        if self.inputs.copy_inputs:
            self.inputs.subjects_dir = os.getcwd()
            if "subjects_dir" in inputs:
                inputs["subjects_dir"] = self.inputs.subjects_dir
            hemi = self.inputs.hemisphere
            copy2subjdir(
                self, self.inputs.annotation, "label", "{0}.aparc.annot".format(hemi)
            )
            copy2subjdir(
                self, self.inputs.cortex, "label", "{0}.cortex.label".format(hemi)
            )
            copy2subjdir(self, self.inputs.white, "surf", "{0}.white".format(hemi))
            copy2subjdir(
                self, self.inputs.thickness, "surf", "{0}.thickness".format(hemi)
            )
            copy2subjdir(self, self.inputs.orig, "mri", "orig.mgz")
            copy2subjdir(self, self.inputs.rawavg, "mri", "rawavg.mgz")
        # need to create output directories
        createoutputdirs(self._list_outputs())
        return super(Contrast, self).run(**inputs)

    def _list_outputs(self):
        outputs = self._outputs().get()
        subject_dir = os.path.join(self.inputs.subjects_dir, self.inputs.subject_id)
        outputs["out_contrast"] = os.path.join(
            subject_dir, "surf", str(self.inputs.hemisphere) + ".w-g.pct.mgh"
        )
        outputs["out_stats"] = os.path.join(
            subject_dir, "stats", str(self.inputs.hemisphere) + ".w-g.pct.stats"
        )
        outputs["out_log"] = os.path.join(subject_dir, "scripts", "pctsurfcon.log")
        return outputs


class RelabelHypointensitiesInputSpec(FSTraitedSpec):
    # required
    lh_white = File(
        mandatory=True,
        exists=True,
        copyfile=True,
        desc="Implicit input file must be lh.white",
    )
    rh_white = File(
        mandatory=True,
        exists=True,
        copyfile=True,
        desc="Implicit input file must be rh.white",
    )
    aseg = File(
        argstr="%s", position=-3, mandatory=True, exists=True, desc="Input aseg file"
    )
    surf_directory = Directory(
        ".",
        argstr="%s",
        position=-2,
        exists=True,
        usedefault=True,
        desc="Directory containing lh.white and rh.white",
    )
    out_file = File(
        argstr="%s",
        position=-1,
        exists=False,
        name_source=["aseg"],
        name_template="%s.hypos.mgz",
        hash_files=False,
        keep_extension=False,
        desc="Output aseg file",
    )


class RelabelHypointensitiesOutputSpec(TraitedSpec):
    out_file = File(argstr="%s", exists=False, desc="Output aseg file")


class RelabelHypointensities(FSCommand):
    """
    Relabel Hypointensities

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import RelabelHypointensities
    >>> relabelhypos = RelabelHypointensities()
    >>> relabelhypos.inputs.lh_white = 'lh.pial'
    >>> relabelhypos.inputs.rh_white = 'lh.pial'
    >>> relabelhypos.inputs.surf_directory = '.'
    >>> relabelhypos.inputs.aseg = 'aseg.mgz'
    >>> relabelhypos.cmdline
    'mri_relabel_hypointensities aseg.mgz . aseg.hypos.mgz'
    """

    _cmd = "mri_relabel_hypointensities"
    input_spec = RelabelHypointensitiesInputSpec
    output_spec = RelabelHypointensitiesOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


class Aparc2AsegInputSpec(FSTraitedSpec):
    # required
    subject_id = traits.String(
        "subject_id",
        argstr="--s %s",
        usedefault=True,
        mandatory=True,
        desc="Subject being processed",
    )
    out_file = File(
        argstr="--o %s",
        exists=False,
        mandatory=True,
        desc="Full path of file to save the output segmentation in",
    )
    # implicit
    lh_white = File(
        mandatory=True,
        exists=True,
        desc="Input file must be <subject_id>/surf/lh.white",
    )
    rh_white = File(
        mandatory=True,
        exists=True,
        desc="Input file must be <subject_id>/surf/rh.white",
    )
    lh_pial = File(
        mandatory=True, exists=True, desc="Input file must be <subject_id>/surf/lh.pial"
    )
    rh_pial = File(
        mandatory=True, exists=True, desc="Input file must be <subject_id>/surf/rh.pial"
    )
    lh_ribbon = File(
        mandatory=True,
        exists=True,
        desc="Input file must be <subject_id>/mri/lh.ribbon.mgz",
    )
    rh_ribbon = File(
        mandatory=True,
        exists=True,
        desc="Input file must be <subject_id>/mri/rh.ribbon.mgz",
    )
    ribbon = File(
        mandatory=True,
        exists=True,
        desc="Input file must be <subject_id>/mri/ribbon.mgz",
    )
    lh_annotation = File(
        mandatory=True,
        exists=True,
        desc="Input file must be <subject_id>/label/lh.aparc.annot",
    )
    rh_annotation = File(
        mandatory=True,
        exists=True,
        desc="Input file must be <subject_id>/label/rh.aparc.annot",
    )
    # optional
    filled = File(
        exists=True, desc="Implicit input filled file. Only required with FS v5.3."
    )
    aseg = File(argstr="--aseg %s", exists=True, desc="Input aseg file")
    volmask = traits.Bool(argstr="--volmask", desc="Volume mask flag")
    ctxseg = File(argstr="--ctxseg %s", exists=True, desc="")
    label_wm = traits.Bool(
        argstr="--labelwm",
        desc="""\
For each voxel labeled as white matter in the aseg, re-assign
its label to be that of the closest cortical point if its
distance is less than dmaxctx.""",
    )
    hypo_wm = traits.Bool(argstr="--hypo-as-wm", desc="Label hypointensities as WM")
    rip_unknown = traits.Bool(
        argstr="--rip-unknown", desc="Do not label WM based on 'unknown' corical label"
    )
    a2009s = traits.Bool(argstr="--a2009s", desc="Using the a2009s atlas")
    copy_inputs = traits.Bool(
        desc="If running as a node, set this to True."
        "This will copy the input files to the node "
        "directory."
    )


class Aparc2AsegOutputSpec(TraitedSpec):
    out_file = File(argstr="%s", desc="Output aseg file")


class Aparc2Aseg(FSCommand):
    """
    Maps the cortical labels from the automatic cortical parcellation
    (aparc) to the automatic segmentation volume (aseg). The result can be
    used as the aseg would. The algorithm is to find each aseg voxel
    labeled as cortex (3 and 42) and assign it the label of the closest
    cortical vertex. If the voxel is not in the ribbon (as defined by mri/
    lh.ribbon and rh.ribbon), then the voxel is marked as unknown (0).
    This can be turned off with ``--noribbon``. The cortical parcellation is
    obtained from subject/label/hemi.aparc.annot which should be based on
    the curvature.buckner40.filled.desikan_killiany.gcs atlas. The aseg is
    obtained from subject/mri/aseg.mgz and should be based on the
    RB40_talairach_2005-07-20.gca atlas. If these atlases are used, then the
    segmentations can be viewed with tkmedit and the
    FreeSurferColorLUT.txt color table found in ``$FREESURFER_HOME``. These
    are the default atlases used by ``recon-all``.

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import Aparc2Aseg
    >>> aparc2aseg = Aparc2Aseg()
    >>> aparc2aseg.inputs.lh_white = 'lh.pial'
    >>> aparc2aseg.inputs.rh_white = 'lh.pial'
    >>> aparc2aseg.inputs.lh_pial = 'lh.pial'
    >>> aparc2aseg.inputs.rh_pial = 'lh.pial'
    >>> aparc2aseg.inputs.lh_ribbon = 'label.mgz'
    >>> aparc2aseg.inputs.rh_ribbon = 'label.mgz'
    >>> aparc2aseg.inputs.ribbon = 'label.mgz'
    >>> aparc2aseg.inputs.lh_annotation = 'lh.pial'
    >>> aparc2aseg.inputs.rh_annotation = 'lh.pial'
    >>> aparc2aseg.inputs.out_file = 'aparc+aseg.mgz'
    >>> aparc2aseg.inputs.label_wm = True
    >>> aparc2aseg.inputs.rip_unknown = True
    >>> aparc2aseg.cmdline # doctest: +SKIP
    'mri_aparc2aseg --labelwm  --o aparc+aseg.mgz --rip-unknown --s subject_id'

    """

    _cmd = "mri_aparc2aseg"
    input_spec = Aparc2AsegInputSpec
    output_spec = Aparc2AsegOutputSpec

    def run(self, **inputs):
        if self.inputs.copy_inputs:
            self.inputs.subjects_dir = os.getcwd()
            if "subjects_dir" in inputs:
                inputs["subjects_dir"] = self.inputs.subjects_dir
            copy2subjdir(self, self.inputs.lh_white, "surf", "lh.white")
            copy2subjdir(self, self.inputs.lh_pial, "surf", "lh.pial")
            copy2subjdir(self, self.inputs.rh_white, "surf", "rh.white")
            copy2subjdir(self, self.inputs.rh_pial, "surf", "rh.pial")
            copy2subjdir(self, self.inputs.lh_ribbon, "mri", "lh.ribbon.mgz")
            copy2subjdir(self, self.inputs.rh_ribbon, "mri", "rh.ribbon.mgz")
            copy2subjdir(self, self.inputs.ribbon, "mri", "ribbon.mgz")
            copy2subjdir(self, self.inputs.aseg, "mri")
            copy2subjdir(self, self.inputs.filled, "mri", "filled.mgz")
            copy2subjdir(self, self.inputs.lh_annotation, "label")
            copy2subjdir(self, self.inputs.rh_annotation, "label")

        return super(Aparc2Aseg, self).run(**inputs)

    def _format_arg(self, name, spec, value):
        if name == "aseg":
            # aseg does not take a full filename
            basename = os.path.basename(value).replace(".mgz", "")
            return spec.argstr % basename
        elif name == "out_file":
            return spec.argstr % os.path.abspath(value)

        return super(Aparc2Aseg, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


class Apas2AsegInputSpec(FSTraitedSpec):
    # required
    in_file = File(
        argstr="--i %s", mandatory=True, exists=True, desc="Input aparc+aseg.mgz"
    )
    out_file = File(argstr="--o %s", mandatory=True, desc="Output aseg file")


class Apas2AsegOutputSpec(TraitedSpec):
    out_file = File(argstr="%s", exists=False, desc="Output aseg file")


class Apas2Aseg(FSCommand):
    """
    Converts aparc+aseg.mgz into something like aseg.mgz by replacing the
    cortical segmentations 1000-1035 with 3 and 2000-2035 with 42. The
    advantage of this output is that the cortical label conforms to the
    actual surface (this is not the case with aseg.mgz).

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import Apas2Aseg
    >>> apas2aseg = Apas2Aseg()
    >>> apas2aseg.inputs.in_file = 'aseg.mgz'
    >>> apas2aseg.inputs.out_file = 'output.mgz'
    >>> apas2aseg.cmdline
    'apas2aseg --i aseg.mgz --o output.mgz'

    """

    _cmd = "apas2aseg"
    input_spec = Apas2AsegInputSpec
    output_spec = Apas2AsegOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs


class MRIsExpandInputSpec(FSTraitedSpec):
    # Input spec derived from
    # https://github.com/freesurfer/freesurfer/blob/102e053/mris_expand/mris_expand.c
    in_file = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-3,
        copyfile=False,
        desc="Surface to expand",
    )
    distance = traits.Float(
        mandatory=True,
        argstr="%g",
        position=-2,
        desc="Distance in mm or fraction of cortical thickness",
    )
    out_name = traits.Str(
        "expanded",
        argstr="%s",
        position=-1,
        usedefault=True,
        desc=(
            "Output surface file. "
            "If no path, uses directory of ``in_file``. "
            'If no path AND missing "lh." or "rh.", derive from ``in_file``'
        ),
    )
    thickness = traits.Bool(
        argstr="-thickness", desc="Expand by fraction of cortical thickness, not mm"
    )
    thickness_name = traits.Str(
        argstr="-thickness_name %s",
        copyfile=False,
        desc=(
            'Name of thickness file (implicit: "thickness")\n'
            "If no path, uses directory of ``in_file``\n"
            'If no path AND missing "lh." or "rh.", derive from `in_file`'
        ),
    )
    pial = traits.Str(
        argstr="-pial %s",
        copyfile=False,
        desc=(
            'Name of pial file (implicit: "pial")\n'
            "If no path, uses directory of ``in_file``\n"
            'If no path AND missing "lh." or "rh.", derive from ``in_file``'
        ),
    )
    sphere = traits.Str(
        "sphere",
        copyfile=False,
        usedefault=True,
        desc="WARNING: Do not change this trait",
    )
    spring = traits.Float(argstr="-S %g", desc="Spring term (implicit: 0.05)")
    dt = traits.Float(argstr="-T %g", desc="dt (implicit: 0.25)")
    write_iterations = traits.Int(
        argstr="-W %d", desc="Write snapshots of expansion every N iterations"
    )
    smooth_averages = traits.Int(
        argstr="-A %d", desc="Smooth surface with N iterations after expansion"
    )
    nsurfaces = traits.Int(
        argstr="-N %d", desc="Number of surfacces to write during expansion"
    )
    # # Requires dev version - Re-add when min_ver/max_ver support this
    # # https://github.com/freesurfer/freesurfer/blob/9730cb9/mris_expand/mris_expand.c
    # navgs = traits.Tuple(
    #     traits.Int, traits.Int,
    #     argstr='-navgs %d %d',
    #     desc=('Tuple of (n_averages, min_averages) parameters '
    #           '(implicit: (16, 0))'))
    # target_intensity = traits.Tuple(
    #     traits.Float, File(exists=True),
    #     argstr='-intensity %g %s',
    #     desc='Tuple of intensity and brain volume to crop to target intensity')


class MRIsExpandOutputSpec(TraitedSpec):
    out_file = File(desc="Output surface file")


class MRIsExpand(FSSurfaceCommand):
    """
    Expands a surface (typically ?h.white) outwards while maintaining
    smoothness and self-intersection constraints.

    Examples
    ========
    >>> from nipype.interfaces.freesurfer import MRIsExpand
    >>> mris_expand = MRIsExpand(thickness=True, distance=0.5)
    >>> mris_expand.inputs.in_file = 'lh.white'
    >>> mris_expand.cmdline
    'mris_expand -thickness lh.white 0.5 expanded'
    >>> mris_expand.inputs.out_name = 'graymid'
    >>> mris_expand.cmdline
    'mris_expand -thickness lh.white 0.5 graymid'
    """

    _cmd = "mris_expand"
    input_spec = MRIsExpandInputSpec
    output_spec = MRIsExpandOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = self._associated_file(
            self.inputs.in_file, self.inputs.out_name
        )
        return outputs

    def normalize_filenames(self):
        """
        Filename normalization routine to perform only when run in Node
        context.
        Find full paths for pial, thickness and sphere files for copying.
        """
        in_file = self.inputs.in_file

        pial = self.inputs.pial
        if not isdefined(pial):
            pial = "pial"
        self.inputs.pial = self._associated_file(in_file, pial)

        if isdefined(self.inputs.thickness) and self.inputs.thickness:
            thickness_name = self.inputs.thickness_name
            if not isdefined(thickness_name):
                thickness_name = "thickness"
            self.inputs.thickness_name = self._associated_file(in_file, thickness_name)

        self.inputs.sphere = self._associated_file(in_file, self.inputs.sphere)


class LTAConvertInputSpec(CommandLineInputSpec):
    # Inputs
    _in_xor = ("in_lta", "in_fsl", "in_mni", "in_reg", "in_niftyreg", "in_itk")
    in_lta = traits.Either(
        File(exists=True),
        "identity.nofile",
        argstr="--inlta %s",
        mandatory=True,
        xor=_in_xor,
        desc="input transform of LTA type",
    )
    in_fsl = File(
        exists=True,
        argstr="--infsl %s",
        mandatory=True,
        xor=_in_xor,
        desc="input transform of FSL type",
    )
    in_mni = File(
        exists=True,
        argstr="--inmni %s",
        mandatory=True,
        xor=_in_xor,
        desc="input transform of MNI/XFM type",
    )
    in_reg = File(
        exists=True,
        argstr="--inreg %s",
        mandatory=True,
        xor=_in_xor,
        desc="input transform of TK REG type (deprecated format)",
    )
    in_niftyreg = File(
        exists=True,
        argstr="--inniftyreg %s",
        mandatory=True,
        xor=_in_xor,
        desc="input transform of Nifty Reg type (inverse RAS2RAS)",
    )
    in_itk = File(
        exists=True,
        argstr="--initk %s",
        mandatory=True,
        xor=_in_xor,
        desc="input transform of ITK type",
    )
    # Outputs
    out_lta = traits.Either(
        traits.Bool,
        File,
        argstr="--outlta %s",
        desc="output linear transform (LTA Freesurfer format)",
    )
    out_fsl = traits.Either(
        traits.Bool, File, argstr="--outfsl %s", desc="output transform in FSL format"
    )
    out_mni = traits.Either(
        traits.Bool,
        File,
        argstr="--outmni %s",
        desc="output transform in MNI/XFM format",
    )
    out_reg = traits.Either(
        traits.Bool,
        File,
        argstr="--outreg %s",
        desc="output transform in reg dat format",
    )
    out_itk = traits.Either(
        traits.Bool, File, argstr="--outitk %s", desc="output transform in ITK format"
    )
    # Optional flags
    invert = traits.Bool(argstr="--invert")
    ltavox2vox = traits.Bool(argstr="--ltavox2vox", requires=["out_lta"])
    source_file = File(exists=True, argstr="--src %s")
    target_file = File(exists=True, argstr="--trg %s")
    target_conform = traits.Bool(argstr="--trgconform")


class LTAConvertOutputSpec(TraitedSpec):
    out_lta = File(exists=True, desc="output linear transform (LTA Freesurfer format)")
    out_fsl = File(exists=True, desc="output transform in FSL format")
    out_mni = File(exists=True, desc="output transform in MNI/XFM format")
    out_reg = File(exists=True, desc="output transform in reg dat format")
    out_itk = File(exists=True, desc="output transform in ITK format")


class LTAConvert(CommandLine):
    """Convert different transformation formats.
    Some formats may require you to pass an image if the geometry information
    is missing form the transform file format.

    For complete details, see the `lta_convert documentation.
    <https://ftp.nmr.mgh.harvard.edu/pub/docs/html/lta_convert.help.xml.html>`_
    """

    input_spec = LTAConvertInputSpec
    output_spec = LTAConvertOutputSpec
    _cmd = "lta_convert"

    def _format_arg(self, name, spec, value):
        if name.startswith("out_") and value is True:
            value = self._list_outputs()[name]
        return super(LTAConvert, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name, default in (
            ("out_lta", "out.lta"),
            ("out_fsl", "out.mat"),
            ("out_mni", "out.xfm"),
            ("out_reg", "out.dat"),
            ("out_itk", "out.txt"),
        ):
            attr = getattr(self.inputs, name)
            if attr:
                fname = default if attr is True else attr
                outputs[name] = os.path.abspath(fname)

        return outputs
