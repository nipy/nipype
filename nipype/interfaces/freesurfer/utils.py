# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Interfaces to assorted Freesurfer utility programs.

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)

"""
__docformat__ = 'restructuredtext'

import os
import re
from nipype.utils.filemanip import fname_presuffix, split_filename

from nipype.interfaces.freesurfer.base import FSCommand, FSTraitedSpec
from nipype.interfaces.base import TraitedSpec, File, traits, OutputMultiPath, isdefined

filemap = dict(cor='cor', mgh='mgh', mgz='mgz', minc='mnc',
               afni='brik', brik='brik', bshort='bshort',
               spm='img', analyze='img', analyze4d='img',
               bfloat='bfloat', nifti1='img', nii='nii',
               niigz='nii.gz')

filetypes = ['cor', 'mgh', 'mgz', 'minc', 'analyze',
             'analyze4d', 'spm', 'afni', 'brik', 'bshort',
             'bfloat', 'sdt', 'outline', 'otl', 'gdf',
             'nifti1', 'nii', 'niigz']


class SampleToSurfaceInputSpec(FSTraitedSpec):

    source_file = File(exists=True, mandatory=True, argstr="--mov %s",
                         desc="volume to sample values from")
    reference_file = File(exists=True, argstr="--ref %s",
                          desc="reference volume (default is orig.mgz)")

    hemi = traits.Enum("lh", "rh", mandatory=True, argstr="--hemi %s",
                       desc="target hemisphere")
    surface = traits.String(argstr="--surf", desc="target surface (default is white)")

    reg_xors = ["reg_file", "reg_header", "mni152reg"]
    reg_file = File(exists=True, argstr="--reg %s", required=True, xor=reg_xors,
                    desc="source-to-reference registration file")
    reg_header = traits.Bool(argstr="--regheader %s", requires=["subject_id"],
                             required=True, xor=reg_xors,
                             desc="register based on header geometry")
    mni152reg = traits.Bool(argstr="--mni152reg",
                            required=True, xor=reg_xors,
                            desc="source volume is in MNI152 space")

    apply_rot = traits.Tuple(traits.Float, traits.Float, traits.Float,
                             argstr="--rot %.3f %.3f %.3f",
                             desc="rotation angles (in degrees) to apply to reg matrix")
    apply_trans = traits.Tuple(traits.Float, traits.Float, traits.Float,
                             argstr="--trans %.3f %.3f %.3f",
                             desc="translation (in mm) to apply to reg matrix")
    override_reg_subj = traits.Bool(argstr="--srcsubject %s", requires=["subject_id"],
                        desc="override the subject in the reg file header")

    sampling_method = traits.Enum("point", "max", "average",
                                  mandatory=True, argstr="%s", xor=["projection_stem"],
                                  requires=["sampling_range", "sampling_units"],
               desc="how to sample -- at a point or at the max or average over a range")
    sampling_range = traits.Either(traits.Float,
                                   traits.Tuple(traits.Float, traits.Float, traits.Float),
                                   desc="sampling range - a point or a tuple of (min, max, step)")
    sampling_units = traits.Enum("mm", "frac", desc="sampling range type -- either 'mm' or 'frac'")
    projection_stem = traits.String(mandatory=True, xor=["sampling_method"],
                            desc="stem for precomputed linear estimates and volume fractions")

    smooth_vol = traits.Float(argstr="--fwhm %.3f", desc="smooth input volume (mm fwhm)")
    smooth_surf = traits.Float(argstr="--surf-fwhm %.3f", desc="smooth output surface (mm fwhm)")

    interp_method = traits.Enum("nearest", "trilinear", argstr="--interp %s",
                                desc="interpolation method")

    cortex_mask = traits.Bool(argstr="--cortex", xor=["mask_label"],
                              desc="mask the target surface with hemi.cortex.label")
    mask_label = File(exists=True, argstr="--mask %s", xor=["cortex_mask"],
                      desc="label file to mask output with")

    float2int_method = traits.Enum("round", "tkregister", argstr="--float2int %s",
                        desc="method to convert reg matrix values (default is round)")
    fix_tk_reg = traits.Bool(argstr="--fixtkreg", desc="make reg matrix round-compatible")

    subject_id = traits.String(desc="subject id")
    target_subject = traits.String(argstr="--trgsubject %s",
                     desc="sample to surface of different subject than source")
    surf_reg = traits.Bool(argstr="--surfreg", requires=["target_subject"],
                           desc="use surface registration to target subject")
    ico_order = traits.Int(argstr="--icoorder %d", requires=["target_subject"],
                           desc="icosahedron order when target_subject is 'ico'")

    reshape = traits.Bool(argstr="--reshape", xor=["no_reshape"],
                          desc="reshape surface vector to fit in non-mgh format")
    no_reshape = traits.Bool(argstr="--noreshape", xor=["reshape"],
                             desc="do not reshape surface vector (default)")
    reshape_slices = traits.Int(argstr="--rf %d", desc="number of 'slices' for reshaping")
    scale_input = traits.Float(argstr="--scale %.3f",
                               desc="multiple all intensities by scale factor")
    frame = traits.Int(argstr="--frame %d", desc="save only one frame (0-based)")

    out_file = File(argstr="--o %s", genfile=True, desc="surface file to write")
    out_type = traits.Enum(filetypes, argstr="--out_type %s", desc="output file type")
    hits_file = traits.Either(traits.Bool, File(exists=True), argstr="--srchit %s",
                              desc="save image with number of hits at each voxel")
    hits_type = traits.Enum(filetypes, argstr="--srchit_type", desc="hits file type")
    vox_file = traits.Either(traits.Bool, File, argstr="--nvox %s",
                           desc="text file with the number of voxels intersecting the surface")


class SampleToSurfaceOutputSpec(TraitedSpec):

    out_file = File(exists=True, desc="surface file")
    hits_file = File(exists=True, desc="image with number of hits at each voxel")
    vox_file = File(exists=True,
                    desc="text file with the number of voxels intersecting the surface")


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
    >>> res = sampler.run() # doctest: +SKIP

    """
    _cmd = "mri_vol2surf"
    input_spec = SampleToSurfaceInputSpec
    output_spec = SampleToSurfaceOutputSpec

    filemap = dict(cor='cor', mgh='mgh', mgz='mgz', minc='mnc',
                   afni='brik', brik='brik', bshort='bshort',
                   spm='img', analyze='img', analyze4d='img',
                   bfloat='bfloat', nifti1='img', nii='nii',
                   niigz='nii.gz')

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
        return super(SampleToSurface, self)._format_arg(name, spec, value)

    def _get_outfilename(self, opt="out_file"):
        outfile = getattr(self.inputs, opt)
        if not isdefined(outfile) or isinstance(outfile, bool):
            if isdefined(self.inputs.out_type):
                if opt == "hits_file":
                    suffix = '_hits.' + self.filemap[self.inputs.out_type]
                else:
                    suffix = '.' + self.filemap[self.inputs.out_type]
            elif opt == "hits_file":
                suffix = "_hits.mgz"
            else:
                suffix = '.mgz'
            outfile = fname_presuffix(self.inputs.source_file,
                                      newpath=os.getcwd(),
                                      prefix=self.inputs.hemi + ".",
                                      suffix=suffix,
                                      use_ext=False)
        return outfile

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = self._get_outfilename()
        hitsfile = self.inputs.hits_file
        if isdefined(hitsfile):
            outputs["hits_file"] = hitsfile
            if isinstance(hitsfile, bool):
                hitsfile = self._get_outfilename("hits_file")
        voxfile = self.inputs.vox_file
        if isdefined(voxfile):
            if isinstance(voxfile, bool):
                voxfile = fname_presuffix(self.inputs.source_file,
                                          newpath=os.getcwd(),
                                          prefix=self.inputs.hemi + ".",
                                          suffix="_vox.txt",
                                          use_ext=False)
            outputs["vox_file"] = voxfile
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()[name]
        return None


class SurfaceSmoothInputSpec(FSTraitedSpec):

    in_file = File(mandatory=True, argstr="--sval %s", desc="source surface file")
    subject_id = traits.String(mandatory=True, argstr="--s %s", desc="subject id of surface file")
    hemi = traits.Enum("lh", "rh", argstr="--hemi %s", mandatory=True, desc="hemisphere to operate on")
    fwhm = traits.Float(argstr="--fwhm %.4f", xor=["smooth_iters"],
                        desc="effective FWHM of the smoothing process")
    smooth_iters = traits.Int(argstr="--smooth %d", xor=["fwhm"],
                              desc="iterations of the smoothing process")
    cortex = traits.Bool(True, argstr="--cortex", usedefault=True, desc="only smooth within $hemi.cortex.label")
    reshape = traits.Bool(argstr="--reshape",
                          desc="reshape surface vector to fit in non-mgh format")
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

    .. seealso::

        SmoothTessellation() Interface
            For smoothing a tessellated surface (e.g. in gifti or .stl)

    Examples
    --------

    >>> import nipype.interfaces.freesurfer as fs
    >>> smoother = fs.SurfaceSmooth()
    >>> smoother.inputs.in_file = "lh.cope1.mgz"
    >>> smoother.inputs.subject_id = "subj_1"
    >>> smoother.inputs.hemi = "lh"
    >>> smoother.inputs.fwhm = 5
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
            outputs["out_file"] = fname_presuffix(in_file,
                                                  suffix="_smooth%d" % kernel,
                                                  newpath=os.getcwd())
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()[name]
        return None


class SurfaceTransformInputSpec(FSTraitedSpec):
    source_file = File(exists=True, mandatory=True, argstr="--sval %s",
                       xor=['source_annot_file'],
                       help="surface file with source values")
    source_annot_file = File(exists=True, mandatory=True, argstr="--sval-annot %s",
                             xor=['source_file'],
                             help="surface annotation file")
    source_subject = traits.String(mandatory=True, argstr="--srcsubject %s",
                                   help="subject id for source surface")
    hemi = traits.Enum("lh", "rh", argstr="--hemi %s", mandatory=True,
                       desc="hemisphere to transform")
    target_subject = traits.String(mandatory=True, argstr="--trgsubject %s",
                                   help="subject id of target surface")
    target_ico_order = traits.Enum(1, 2, 3, 4, 5, 6, 7, argstr="--trgicoorder %d",
                                   help="order of the icosahedron if target_subject is 'ico'")
    source_type = traits.Enum(filetypes, argstr='--sfmt %s', requires=['source_file'],
                              help="source file format")
    target_type = traits.Enum(filetypes, argstr='--tfmt %s', help="output format")
    reshape = traits.Bool(argstr="--reshape", help="reshape output surface to conform with Nifti")
    reshape_factor = traits.Int(argstr="--reshape-factor", help="number of slices in reshaped image")
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

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = self.inputs.out_file
        if not isdefined(outputs["out_file"]):
            source = self.inputs.source_file
            # Some recon-all files don't have a proper extension (e.g. "lh.thickness")
            # so we have to account for that here
            bad_extensions = [".%s" % e for e in ["area", "mid", "pial", "avg_curv", "curv", "inflated",
                                                  "jacobian_white", "orig", "nofix", "smoothwm", "crv",
                                                  "sphere", "sulc", "thickness", "volume", "white"]]
            use_ext = True
            if split_filename(source)[2] in bad_extensions:
                source = source + ".stripme"
                use_ext = False
            ext = ""
            if isdefined(self.inputs.target_type):
                ext = "." + filemap[self.inputs.target_type]
                use_ext = False
            outputs["out_file"] = fname_presuffix(source,
                                                  suffix=".%s%s" % (self.inputs.target_subject, ext),
                                                  newpath=os.getcwd(),
                                                  use_ext=use_ext)
        else:
            outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()[name]
        return None


class ApplyMaskInputSpec(FSTraitedSpec):

    in_file = File(exists=True, mandatory=True, position=-3, argstr="%s",
                   desc="input image (will be masked)")
    mask_file = File(exists=True, mandatory=True, position=-2, argstr="%s",
                     desc="image defining mask space")
    out_file = File(genfile=True, position=-1, argstr="%s",
                    desc="final image to write")
    xfm_file = File(exists=True, argstr="-xform %s",
                    desc="LTA-format transformation matrix to align mask with input")
    invert_xfm = traits.Bool(argstr="-invert", desc="invert transformation")
    xfm_source = File(exists=True, argstr="-lta_src %s", desc="image defining transform source space")
    xfm_target = File(exists=True, argstr="-lta_dst %s", desc="image defining transform target space")
    use_abs = traits.Bool(argstr="-abs", desc="take absolute value of mask before applying")
    mask_thresh = traits.Float(argstr="-T %.4f", desc="threshold mask before applying")


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

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = self.inputs.out_file
        if not isdefined(outputs["out_file"]):
            outputs["out_file"] = fname_presuffix(self.inputs.in_file,
                                                  suffix="_masked",
                                                  newpath=os.getcwd(),
                                                  use_ext=True)
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()[name]
        return None


class SurfaceSnapshotsInputSpec(FSTraitedSpec):

    subject_id = traits.String(position=1, argstr="%s", mandatory=True,
                               desc="subject to visualize")
    hemi = traits.Enum("lh", "rh", position=2, argstr="%s", mandatory=True,
                       desc="hemisphere to visualize")
    surface = traits.String(position=3, argstr="%s", mandatory=True,
                            desc="surface to visualize")

    show_curv = traits.Bool(argstr="-curv", desc="show curvature", xor=["show_gray_curv"])
    show_gray_curv = traits.Bool(argstr="-gray", desc="show curvature in gray", xor=["show_curv"])

    overlay = File(exists=True, argstr="-overlay %s", desc="load an overlay volume/surface",
                   requires=["overlay_range"])
    reg_xors = ["overlay_reg", "identity_reg", "mni152_reg"]
    overlay_reg = traits.File(exists=True, argstr="-overlay-reg %s", xor=reg_xors,
                              desc="registration matrix file to register overlay to surface")
    identity_reg = traits.Bool(argstr="-overlay-reg-identity", xor=reg_xors,
                   desc="use the identity matrix to register the overlay to the surface")
    mni152_reg = traits.Bool(argstr="-mni152reg", xor=reg_xors,
                 desc="use to display a volume in MNI152 space on the average subject")

    overlay_range = traits.Either(traits.Float,
                                  traits.Tuple(traits.Float, traits.Float),
                                  traits.Tuple(traits.Float, traits.Float, traits.Float),
                                  desc="overlay range--either min, (min, max) or (min, mid, max)",
                                  argstr="%s")
    overlay_range_offset = traits.Float(argstr="-foffset %.3f",
                           desc="overlay range will be symettric around offset value")

    truncate_overlay = traits.Bool(argstr="-truncphaseflag 1",
                                   desc="truncate the overlay display")
    reverse_overlay = traits.Bool(argstr="-revphaseflag 1",
                                  desc="reverse the overlay display")
    invert_overlay = traits.Bool(argstr="-invphaseflag 1",
                                 desc="invert the overlay display")
    demean_overlay = traits.Bool(argstr="-zm", desc="remove mean from overlay")

    annot_file = File(exists=True, argstr="-annotation %s", xor=["annot_name"],
                      desc="path to annotation file to display")
    annot_name = traits.String(argstr="-annotation %s", xor=["annot_file"],
            desc="name of annotation to display (must be in $subject/label directory")

    label_file = File(exists=True, argstr="-label %s", xor=["label_name"],
                      desc="path to label file to display")
    label_name = traits.String(argstr="-label %s", xor=["label_file"],
            desc="name of label to display (must be in $subject/label directory")

    colortable = File(exists=True, argstr="-colortable %s", desc="load colortable file")
    label_under = traits.Bool(argstr="-labels-under", desc="draw label/annotation under overlay")
    label_outline = traits.Bool(argstr="-label-outline", desc="draw label/annotation as outline")

    patch_file = File(exists=True, argstr="-patch %s", desc="load a patch")

    orig_suffix = traits.String(argstr="-orig %s", desc="set the orig surface suffix string")
    sphere_suffix = traits.String(argstr="-sphere %s", desc="set the sphere.reg suffix string")

    show_color_scale = traits.Bool(argstr="-colscalebarflag 1",
                                   desc="display the color scale bar")
    show_color_text = traits.Bool(argstr="-colscaletext 1",
                                  desc="display text in the color scale bar")

    six_images = traits.Bool(desc="also take anterior and posterior snapshots")
    screenshot_stem = traits.String(desc="stem to use for screenshot file names")
    stem_template_args = traits.List(traits.String, requires=["screenshot_stem"],
                    desc="input names to use as arguments for a string-formated stem template")
    tcl_script = File(exists=True, argstr="%s", genfile=True,
                             desc="override default screenshot script")


class SurfaceSnapshotsOutputSpec(TraitedSpec):

    snapshots = OutputMultiPath(File(exists=True),
                    desc="tiff images of the surface from different perspectives")


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
                    return "-fminmax %.3f %.3f -fmid %.3f" % (value[0], value[2], value[1])
        elif name == "annot_name" and isdefined(value):
            # Matching annot by name needs to strip the leading hemi and trailing
            # extension strings
            if value.endswith(".annot"):
                value = value[:-6]
            if re.match("%s[\.\-_]" % self.inputs.hemi, value[:3]):
                value = value[3:]
            return "-annotation %s" % value
        return super(SurfaceSnapshots, self)._format_arg(name, spec, value)

    def _run_interface(self, runtime):
        if not isdefined(self.inputs.screenshot_stem):
            stem = "%s_%s_%s" % (
                    self.inputs.subject_id, self.inputs.hemi, self.inputs.surface)
        else:
            stem = self.inputs.screenshot_stem
            stem_args = self.inputs.stem_template_args
            if isdefined(stem_args):
                args = tuple([getattr(self.inputs, arg) for arg in stem_args])
                stem = stem % args
        # Check if the DISPLAY variable is set -- should avoid crashes (might not?)
        if not "DISPLAY" in os.environ:
            raise RuntimeError("Graphics are not enabled -- cannot run tksurfer")
        runtime.environ["_SNAPSHOT_STEM"] = stem
        self._write_tcl_script()
        runtime = super(SurfaceSnapshots, self)._run_interface(runtime)
        # If a display window can't be opened, this will crash on
        # aggregate_outputs.  Let's try to parse stderr and raise a
        # better exception here if that happened.
        errors = ["surfer: failed, no suitable display found",
                  "Fatal Error in tksurfer.bin: could not open display"]
        for err in errors:
            if err in runtime.stderr:
                self.raise_exception(runtime)
        # Tksurfer always (or at least always when you run a tcl script)
        # exits with a nonzero returncode.  We have to force it to 0 here.
        runtime.returncode = 0
        return runtime

    def _write_tcl_script(self):
        fid = open("snapshots.tcl", "w")
        script = ["save_tiff $env(_SNAPSHOT_STEM)-lat.tif",
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
                  "save_tiff $env(_SNAPSHOT_STEM)-dor.tif"]
        if isdefined(self.inputs.six_images) and self.inputs.six_images:
            script.extend(["make_lateral_view",
                           "rotate_brain_y 90",
                           "redraw",
                           "save_tiff $env(_SNAPSHOT_STEM)-pos.tif",
                           "make_lateral_view",
                           "rotate_brain_y -90",
                           "redraw",
                           "save_tiff $env(_SNAPSHOT_STEM)-ant.tif"])

        script.append("exit")
        fid.write("\n".join(script))
        fid.close()

    def _list_outputs(self):
        outputs = self._outputs().get()
        if not isdefined(self.inputs.screenshot_stem):
            stem = "%s_%s_%s" % (self.inputs.subject_id, self.inputs.hemi, self.inputs.surface)
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
        m = re.search("%s\s*:\s+(.+?)%s" % (field, delim), info)
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
        ftype, dtype = re.findall("%s\s*:\s+(.+?)\n" % "type", info)
        outputs.file_format = ftype
        outputs.data_type = dtype

        return outputs


class MRIsConvertInputSpec(FSTraitedSpec):
    """
    Uses Freesurfer's mris_convert to convert surface files to various formats
    """
    annot_file = File(exists=True, argstr="--annot %s",
    desc="input is annotation or gifti label data")

    parcstats_file = File(exists=True, argstr="--parcstats %s",
    desc="infile is name of text file containing label/val pairs")

    label_file = File(exists=True, argstr="--label %s",
    desc="infile is .label file, label is name of this label")

    scalarcurv_file = File(exists=True, argstr="-c %s",
    desc="input is scalar curv overlay file (must still specify surface)")

    functional_file = File(exists=True, argstr="-f %s",
    desc="input is functional time-series or other multi-frame data (must specify surface)")

    labelstats_outfile = File(exists=False, argstr="--labelstats %s",
    desc="outfile is name of gifti file to which label stats will be written")

    patch = traits.Bool(argstr="-p", desc="input is a patch, not a full surface")
    rescale = traits.Bool(argstr="-r", desc="rescale vertex xyz so total area is same as group average")
    normal = traits.Bool(argstr="-n", desc="output is an ascii file where vertex data")
    xyz_ascii = traits.Bool(argstr="-a", desc="Print only surface xyz to ascii file")
    vertex = traits.Bool(argstr="-v", desc="Writes out neighbors of a vertex in each row")

    scale = traits.Float(argstr="-s %.3f", desc="scale vertex xyz by scale")
    dataarray_num = traits.Int(argstr="--da_num %d", desc="if input is gifti, 'num' specifies which data array to use")

    talairachxfm_subjid = traits.String(argstr="-t %s", desc="apply talairach xfm of subject to vertex xyz")
    origname = traits.String(argstr="-o %s", desc="read orig positions")

    in_file = File(exists=True, mandatory=True, position=-2, argstr='%s', desc='File to read/convert')
    out_file = File(argstr='./%s', position=-1, genfile=True, desc='output filename or True to generate one')
    #Not really sure why the ./ is necessary but the module fails without it

    out_datatype = traits.Enum("ico", "tri", "stl", "vtk", "gii", "mgh", "mgz", mandatory=True,
    desc="These file formats are supported:  ASCII:       .asc" \
    "ICO: .ico, .tri GEO: .geo STL: .stl VTK: .vtk GIFTI: .gii MGH surface-encoded 'volume': .mgh, .mgz")


class MRIsConvertOutputSpec(TraitedSpec):
    """
    Uses Freesurfer's mris_convert to convert surface files to various formats
    """
    converted = File(exists=True, desc='converted output surface')


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
    _cmd = 'mris_convert'
    input_spec = MRIsConvertInputSpec
    output_spec = MRIsConvertOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["converted"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        if isdefined(self.inputs.annot_file):
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

class MRITessellateInputSpec(FSTraitedSpec):
    """
    Uses Freesurfer's mri_tessellate to create surfaces by tessellating a given input volume
    """

    in_file = File(exists=True, mandatory=True, position=-3, argstr='%s', desc='Input volume to tesselate voxels from.')
    label_value = traits.Int(position=-2, argstr='%d', mandatory=True,
        desc='Label value which to tesselate from the input volume. (integer, if input is "filled.mgz" volume, 127 is rh, 255 is lh)')
    out_file = File(argstr='./%s', position=-1, genfile=True, desc='output filename or True to generate one')
    tesselate_all_voxels = traits.Bool(argstr='-a', desc='Tessellate the surface of all voxels with different labels')
    use_real_RAS_coordinates = traits.Bool(argstr='-n', desc='Saves surface with real RAS coordinates where c_(r,a,s) != 0')

class MRITessellateOutputSpec(TraitedSpec):
    """
    Uses Freesurfer's mri_tessellate to create surfaces by tessellating a given input volume
    """
    surface = File(exists=True, desc='binary surface of the tessellation ')


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
    _cmd = 'mri_tessellate'
    input_spec = MRITessellateInputSpec
    output_spec = MRITessellateOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['surface'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        if isdefined(self.inputs.out_file):
            return self.inputs.out_file
        else:
            _, name, ext = split_filename(self.inputs.in_file)
            return name + ext + '_' + str(self.inputs.label_value)

class MRIMarchingCubesInputSpec(FSTraitedSpec):
    """
    Uses Freesurfer's mri_mc to create surfaces by tessellating a given input volume
    """

    in_file = File(exists=True, mandatory=True, position=1, argstr='%s', desc='Input volume to tesselate voxels from.')
    label_value = traits.Int(position=2, argstr='%d', mandatory=True,
        desc='Label value which to tesselate from the input volume. (integer, if input is "filled.mgz" volume, 127 is rh, 255 is lh)')
    connectivity_value = traits.Int(1, position=-1, argstr='%d', usedefault=True,
        desc='Alter the marching cubes connectivity: 1=6+,2=18,3=6,4=26 (default=1)')
    out_file = File(argstr='./%s', position=-2, genfile=True, desc='output filename or True to generate one')

class MRIMarchingCubesOutputSpec(TraitedSpec):
    """
    Uses Freesurfer's mri_mc to create surfaces by tessellating a given input volume
    """
    surface = File(exists=True, desc='binary surface of the tessellation ')


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
    _cmd = 'mri_mc'
    input_spec = MRIMarchingCubesInputSpec
    output_spec = MRIMarchingCubesOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['surface'] = self._gen_outfilename()
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        if isdefined(self.inputs.out_file):
            return os.path.abspath(self.inputs.out_file)
        else:
            _, name, ext = split_filename(self.inputs.in_file)
            return os.path.abspath(name + ext + '_' + str(self.inputs.label_value))

class SmoothTessellationInputSpec(FSTraitedSpec):
    """
    This program smooths the tessellation of a surface using 'mris_smooth'
    """

    in_file = File(exists=True, mandatory=True, argstr='%s', position=1, desc='Input volume to tesselate voxels from.')

    curvature_averaging_iterations = traits.Int(10, usedefault=True, argstr='-a %d', position=-1, desc='Number of curvature averaging iterations (default=10)')
    smoothing_iterations = traits.Int(10, usedefault=True, argstr='-n %d', position=-2, desc='Number of smoothing iterations (default=10)')
    snapshot_writing_iterations = traits.Int(argstr='-w %d', desc='Write snapshot every "n" iterations')

    use_gaussian_curvature_smoothing = traits.Bool(argstr='-g', position=3, desc='Use Gaussian curvature smoothing')
    gaussian_curvature_norm_steps = traits.Int(argstr='%d ', position=4, desc='Use Gaussian curvature smoothing')
    gaussian_curvature_smoothing_steps = traits.Int(argstr='%d', position=5, desc='Use Gaussian curvature smoothing')

    disable_estimates = traits.Bool(argstr='-nw', desc='Disables the writing of curvature and area estimates')
    normalize_area = traits.Bool(argstr='-area', desc='Normalizes the area after smoothing')
    use_momentum = traits.Bool(argstr='-m', desc='Uses momentum')

    out_file = File(argstr='%s', position=2, genfile=True, desc='output filename or True to generate one')
    out_curvature_file = File(argstr='-c %s', desc='Write curvature to ?h.curvname (default "curv")')
    out_area_file = File(argstr='-b %s', desc='Write area to ?h.areaname (default "area")')

class SmoothTessellationOutputSpec(TraitedSpec):
    """
    This program smooths the tessellation of a surface using 'mris_smooth'
    """
    surface = File(exists=True, desc='Smoothed surface file ')


class SmoothTessellation(FSCommand):
    """
    This program smooths the tessellation of a surface using 'mris_smooth'

    .. seealso::

        SurfaceSmooth() Interface
            For smoothing a scalar field along a surface manifold

    Example
    -------

    >>> import nipype.interfaces.freesurfer as fs
    >>> smooth = fs.SmoothTessellation()
    >>> smooth.inputs.in_file = 'lh.hippocampus.stl'
    >>> smooth.run() # doctest: +SKIP
    """
    _cmd = 'mris_smooth'
    input_spec = SmoothTessellationInputSpec
    output_spec = SmoothTessellationOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['surface'] = self._gen_outfilename()
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        if isdefined(self.inputs.out_file):
            return os.path.abspath(self.inputs.out_file)
        else:
            _, name, ext = split_filename(self.inputs.in_file)
            return os.path.abspath(name + '_smoothed' + ext)
    
    def _run_interface(self, runtime):
        # The returncode is meaningless in BET.  So check the output
        # in stderr and if it's set, then update the returncode
        # accordingly.
        runtime = super(SmoothTessellation, self)._run_interface(runtime)
        if "failed" in runtime.stderr:
            self.raise_exception(runtime)
        return runtime


class MakeAverageSubjectInputSpec(FSTraitedSpec):
    subjects_ids = traits.List(traits.Str(), argstr='--subjects %s',
                               desc='freesurfer subjects ids to average',
                               mandatory=True, sep=' ')
    out_name = File('average', argstr='--out %s',
                    desc='name for the average subject', usedefault=True)


class MakeAverageSubjectOutputSpec(TraitedSpec):
    average_subject_name = traits.Str(desc='Output registration file')


class MakeAverageSubject(FSCommand):
    """Make an average freesurfer subject

    Examples
    --------

    >>> from nipype.interfaces.freesurfer import MakeAverageSubject
    >>> avg = MakeAverageSubject(subjects_ids=['s1', 's2'])
    >>> avg.cmdline
    'make_average_subject --out average --subjects s1 s2'

    """

    _cmd = 'make_average_subject'
    input_spec = MakeAverageSubjectInputSpec
    output_spec = MakeAverageSubjectOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['average_subject_name'] = self.inputs.out_name
        return outputs
