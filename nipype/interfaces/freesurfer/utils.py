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
from nipype.interfaces.base import TraitedSpec, File, traits, OutputMultiPath
from nipype.utils.misc import isdefined

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

    source_file = File(exists=True,mandatory=True,argstr="--mov %s",
                         desc="volume to sample values from")
    reference_file = File(exists=True, argstr="--ref %s", 
                          desc="reference volume (default is orig.mgz)")
    
    hemi = traits.Enum("lh","rh", mandatory=True, argstr="--hemi %s",
                       desc="target hemisphere")
    surface = traits.String(argstr="--surf", desc="target surface (default is white)")

    reg_xors = ["reg_file","reg_header","mni152reg"]
    reg_file = File(exists=True, argstr="--reg %s",required=True,xor=reg_xors,
                    desc="source-to-reference registration file")
    reg_header = traits.Bool(argstr="--regheader %s", requires=["subject_id"],
                             required=True,xor=reg_xors,
                             desc="register based on header geometry")
    mni152reg = traits.Bool(argstr="--mni152reg",
                            required=True,xor=reg_xors,
                            desc="source volume is in MNI152 space")
    
    apply_rot = traits.Tuple(traits.Float,traits.Float,traits.Float,
                             argstr="--rot %.3f %.3f %.3f",
                             desc="rotation angles (in degrees) to apply to reg matrix")
    apply_trans = traits.Tuple(traits.Float,traits.Float,traits.Float,
                             argstr="--trans %.3f %.3f %.3f",
                             desc="translation (in mm) to apply to reg matrix")
    override_reg_subj = traits.Bool(argstr="--srcsubject %s",requires=["subject_id"],
                        desc="override the subject in the reg file header")

    sampling_method = traits.Enum("point","max","average",
                                  mandatory=True,argstr="%s",xor=["projection_stem"],
                                  requires=["sampling_range","sampling_units"],
               desc="how to sample -- at a point or at the max or average over a range")
    sampling_range = traits.Either(traits.Float,
                                   traits.Tuple(traits.Float,traits.Float,traits.Float),
                                   desc="sampling range - a point or a tuple of (min, max, step)")
    sampling_units = traits.Enum("mm","frac",desc="sampling range type -- either 'mm' or 'frac'")
    projection_stem = traits.String(mandatory=True,xor=["sampling_method"],
                            desc="stem for precomputed linear estimates and volume fractions")

    smooth_vol = traits.Float(argstr="--fwhm %.3f",desc="smooth input volume (mm fwhm)")
    smooth_surf = traits.Float(argstr="--surf-fwhm %.3f",desc="smooth output surface (mm fwhm)")
    
    interp_method = traits.Enum("nearest","trilinear",desc="interpolation method")

    cortex_mask = traits.Bool(argstr="--cortex",xor=["mask_label"],
                              desc="mask the target surface with hemi.cortex.label")
    mask_label = File(exists=True,argstr="--mask %s",xor=["cortex_mask"],
                      desc="label file to mask output with")

    float2int_method = traits.Enum("round","tkregister",argstr="--float2int %s",
                        desc="method to convert reg matrix values (default is round)")
    fix_tk_reg = traits.Bool(argstr="--fixtkreg",desc="make reg matrix round-compatible")

    subject_id = traits.String(desc="subject id")
    target_subject = traits.String(argstr="--trgsubject %s",
                     desc="sample to surface of different subject than source")
    surf_reg = traits.Bool(argstr="--surfreg",requires=["target_subject"],
                           desc="use surface registration to target subject")
    ico_order = traits.Int(argstr="--icoorder %d",requires=["target_subject"],
                           desc="icosahedron order when target_subject is 'ico'")

    reshape = traits.Bool(argstr="--reshape",xor=["no_reshape"],
                          desc="reshape surface vector to fit in non-mgh format")
    no_reshape = traits.Bool(argstr="--noreshape",xor=["reshape"],
                             desc="do not reshape surface vector (default)")
    reshape_slices = traits.Int(argstr="--rf %d",desc="number of 'slices' for reshaping")
    scale_input = traits.Float(argstr="--scale %.3f",
                               desc="multiple all intensities by scale factor")
    frame = traits.Int(argstr="--frame %d",desc="save only one frame (0-based)")


    out_file = File(argstr="--o %s",genfile=True,desc="surface file to write")
    out_type = traits.Enum(filetypes,argstr="--out_type %s", desc="output file type")
    hits_file = traits.Either(traits.Bool, File(exists=True),argstr="--srchit %s",
                              desc="save image with number of hits at each voxel")
    hits_type = traits.Enum(filetypes,argstr="--srchit_type", desc="hits file type")
    vox_file = traits.Either(traits.Bool,File,argstr="--nvox %s",
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
    import nipype.interfaces.freesurfer as fs
    sampler = fs.SampleToSurface(hemi="lh")
    sampler.inputs.in_file = "cope1.nii.gz"
    sampler.inputs.reg_file = "register.dat"
    sampler.inputs.sampling_method = "average"
    sampler.inputs.sampling_rage = 1
    sampler.inputs.sampling_units = "frac"
    res = sampler.run() # doctest: +SKIP
   
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
                range = "%.3f %.3f %.3f"%range
            else:
                range = "%.3f"%range
            method = dict(point="",max="-max",average="-avg")[value]
            return "--proj%s%s %s"%(units, method, range)

        if name == "reg_header":
            return spec.argstr%self.inputs.subject_id
        if name == "override_reg_subj":
            return spec.argstr%self.inputs.subject_id
        if name in ["hits_file", "vox_file"]:
            return spec.argstr%self._get_outfilename(name)
        return super(SampleToSurface, self)._format_arg(name, spec, value)

    def _get_outfilename(self,opt="out_file"):
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

    in_file = File(mandatory=True,argstr="--sval %s",desc="source surface file")
    subject_id = traits.String(mandatory=True,argstr="--s %s",desc="subject id of surface file")
    hemi = traits.Enum("lh","rh",argstr="--hemi %s",mandatory=True,desc="hemisphere to operate on")
    fwhm = traits.Float(argstr="--fwhm %.4f",xor=["smooth_iters"],
                        desc="effective FWHM of the smoothing process")
    smooth_iters = traits.Int(argstr="--smooth %d",xor=["fwhm"],
                              desc="iterations of the smoothing process")
    cortex = traits.Bool(True,argstr="--cortex",usedefault=True,desc="only smooth within $hemi.cortex.label")
    reshape = traits.Bool(argstr="--reshape",
                          desc="reshape surface vector to fit in non-mgh format")
    out_file = File(argstr="--tval %s",genfile=True,desc="surface file to write")

class SurfaceSmoothOutputSpec(TraitedSpec):

    out_file = File(exists=True, desc="smoothed surface file")

class SurfaceSmooth(FSCommand):
    """Smooth a surface image with mri_surf2surf.

    The surface is smoothed by an interative process of averaging the
    value at each vertex with those of its adjacent neighbors. You may supply
    either the number of iterations to run or a desired effective FWHM of the
    smoothing process.  If the latter, the underlying program will calculate 
    the correct number of iterations internally.

    Examples
    --------
    import nipype.interfaces.freesurfer as fs
    smoother = fs.SurfaceSmooth()
    smoother.inputs.in_file = "lh.cope1.mgz"
    smoother.inputs.subject_id = "subj_1"
    smoother.inputs.hemi = "lh"
    smoother.inputs.fwhm = 5
    smoother.run() # doctest: +SKIP

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
                                                  suffix="_smooth%d"%kernel,
                                                  newpath=os.getcwd())
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()[name]
        return None


class SurfaceTransformInputSpec(FSTraitedSpec):

    source_file = File(exists=True,mandatory=True,argstr="--sval %s",
                       help="surface file with source values")
    source_subject = traits.String(mandatory=True,argstr="--srcsubject %s",
                                   help="subject id for source surface")
    hemi = traits.Enum("lh","rh",argstr="--hemi %s",mandatory=True,
                       desc="hemisphere to transform")
    target_subject = traits.String(mandatory=True,argstr="--trgsubject %s",
                                   help="subject id of target surface")
    target_ico_order = traits.Enum(1,2,3,4,5,6,7, argstr="--trgicoorder %d",
                                   help="order of the icosahedron if target_subject is 'ico'")
    target_type = traits.Enum(filetypes, help="output format")
    reshape = traits.Bool(argstr="--reshape",help="reshape output surface to conform with Nifti")
    reshape_factor = traits.Int(argstr="--reshape-factor",help="number of slices in reshaped image")
    out_file = File(argstr="--tval %s",genfile=True,desc="surface file to write")

class SurfaceTransformOutputSpec(TraitedSpec):

    out_file = File(exists=True, desc="transformed surface file")

class SurfaceTransform(FSCommand):
    """Transform a surface file from one subject to another via a spherical registration.

    Both the source and target subject must reside in your Subjects Directory,
    and they must have been processed with recon-all, unless you are transforming
    to one of the icosahedron meshes.

    Examples
    --------
    from nipype.interfaces.freesurfer import SurfaceTransform
    sxfm = SurfaceTransfrom()
    sxfm.inputs.source_file = "lh.cope1.nii.gz"
    sxfm.inputs.source_subject = "my_subject"
    sxfm.inputs.target_subject = "fsaverage"
    sxfm.inputs.hemi = "lh"
    sxfm.run() # doctest: +SKIP

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
            bad_extensions = [".%s"%e for e in ["area", "mid", "pial", "avg_curv", "curv", "inflated",
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
                                                  suffix=".%s%s"%(self.inputs.target_subject,ext),
                                                  newpath=os.getcwd(),
                                                  use_ext=use_ext)
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()[name]
        return None


class SurfaceSnapshotsInputSpec(FSTraitedSpec):

    subject_id = traits.String(position=1,argstr="%s",mandatory=True,
                               desc="subject to visualize")
    hemi = traits.Enum("lh","rh",position=2,argstr="%s",mandatory=True,
                       desc="hemisphere to visualize")
    surface = traits.String(position=3,argstr="%s",mandatory=True,
                            desc="surface to visualize")
    
    show_curv = traits.Bool(argstr="-curv",desc="show curvature",xor=["show_gray_curv"])
    show_gray_curv = traits.Bool(argstr="-gray",desc="show curvature in gray",xor=["show_curv"])
    
    overlay = File(exists=True,argstr="-overlay %s",desc="load an overlay volume/surface",
                   requires=["overlay_range"])
    reg_xors = ["overlay_reg","identity_reg","find_reg","mni152_reg"]
    overlay_reg = traits.File(exists=True,argstr="-overlay-reg %s",xor=reg_xors,
                              desc="registration matrix file to register overlay to surface")
    identity_reg = traits.Bool(argstr="-overlay-reg-identity",xor=reg_xors,
                   desc="use the identity matrix to register the overlay to the surface")
    mni152_reg = traits.Bool(argstr="-mni152reg",xor=reg_xors,
                 desc="use to display a volume in MNI152 space on the average subject")
   
    overlay_range = traits.Either(traits.Float,
                                  traits.Tuple(traits.Float, traits.Float),
                                  traits.Tuple(traits.Float, traits.Float, traits.Float),
                                  desc="overlay range--either min, (min,max) or (min,mid,max)",
                                  argstr="%s")
    overlay_range_offset = traits.Float(argstr="-foffset %.3f",
                           desc="overlay range will be symettric around offset value")

    truncate_overlay = traits.Bool(argstr="-truncphaseflag 1",
                                   desc="truncate the overlay display")
    reverse_overlay = traits.Bool(argstr="-revphaseflag 1",
                                  desc="reverse the overlay display")
    invert_overlay = traits.Bool(argstr="-invphaseflag 1",
                                 desc="invert the overlay display")
    demean_overlay = traits.Bool(argstr="-zm",desc="remove mean from overlay")

    annot_file = File(exists=True,argstr="-annotation %s",xor=["annot_name"],
                      desc="path to annotation file to display")
    annot_name = traits.String(argstr="-annotation %s",xor=["annot_file"],
            desc="name of annotation to display (must be in $subject/label directory")
    
    label_file = File(exists=True,argstr="-label %s",xor=["label_name"],
                      desc="path to label file to display")
    label_name = traits.String(argstr="-label %s",xor=["label_file"],
            desc="name of label to display (must be in $subject/label directory")

    colortable = File(exists=True,argstr="-colortable %s",desc="load colortable file")
    label_under = traits.Bool(argstr="-labels-under",desc="draw label/annotation under overlay")
    label_outline = traits.Bool(argstr="-label-outline",desc="draw label/annotation as outline")

    patch_file = File(exists=True,argstr="-patch %s",desc="load a patch")

    orig_suffix = traits.String(argstr="-orig %s",desc="set the orig surface suffix string")
    sphere_suffix = traits.String(argstr="-sphere %s",desc="set the sphere.reg suffix string")
    
    show_color_scale = traits.Bool(argstr="-colscalebarflag 1",
                                   desc="display the color scale bar")
    show_color_text = traits.Bool(argstr="-colscaletext 1",
                                  desc="display text in the color scale bar")
   
    six_images = traits.Bool(desc="also take anterior and posterior snapshots")
    screenshot_stem = traits.String(desc="stem to use for screenshot file names")
    stem_template_args = traits.List(traits.String,requires=["screenshot_stem"],
                    desc="input names to use as arguments for a string-formated stem template")
    tcl_script = File(exists=True, argstr="%s",genfile=True, 
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
    import nipype.interfaces.freesurfer as fs
    shots = fs.SurfaceSnapshots(subject_id="fsaverage", hemi="lh", surface="pial")
    shots.inputs.overlay = "zstat1.nii.gz"
    shots.inputs.overlay_range = (2.3, 6)
    shots.inputs.overlay_reg = "register.dat"
    res = shots.run() # doctest: +SKIP
    
    """
    _cmd = "tksurfer"
    input_spec = SurfaceSnapshotsInputSpec
    output_spec = SurfaceSnapshotsOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "tcl_script":
            if not isdefined(value):
                return "-tcl snapshots.tcl"
            else:
                return "-tcl %s"%value
        elif name == "overlay_range":
            if isinstance(value, float):
                return "-fthresh %.3f"%value
            else:
                if len(value) == 2:
                    return "-fminmax %.3f %.3f"%value
                else:
                    return "-fminmax %.3f %.3f -fmid %.3f"%(value[0],value[2],value[1])
        elif name == "annot_name" and isdefined(value):
            # Matching annot by name needs to strip the leading hemi and trailing 
            # extension strings
            if value.endswith(".annot"):
                value = value[:-6]
            if re.match("%s[\.\-_]"%self.inputs.hemi, value[:3]):
                value = value[3:]
            return "-annotation %s"%value
        return super(SurfaceSnapshots, self)._format_arg(name, spec, value)
    
    def _run_interface(self, runtime):
        if not isdefined(self.inputs.screenshot_stem):
            stem = "%s_%s_%s"%(
                    self.inputs.subject_id, self.inputs.hemi, self.inputs.surface)
        else:
            stem = self.inputs.screenshot_stem
            stem_args = self.inputs.stem_template_args
            if isdefined(stem_args):
                args = tuple([getattr(self.inputs, arg) for arg in stem_args])
                stem = stem%args
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
                raise RuntimeError("Could not open display")
        # Tksurfer always (or at least always when you run a tcl script)
        # exits with a nonzero returncode.  We have to force it to 0 here.
        runtime.returncode = 0
        return runtime

    def _write_tcl_script(self):
        fid = open("snapshots.tcl","w")
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
            stem = "%s_%s_%s"%(self.inputs.subject_id, self.inputs.hemi, self.inputs.surface)
        else:
            stem = self.inputs.screenshot_stem
            stem_args = self.inputs.stem_template_args
            if isdefined(stem_args):
                args = tuple([getattr(self.inputs, arg) for arg in stem_args])
                stem = stem%args
        snapshots = ["%s-lat.tif","%s-med.tif","%s-dor.tif","%s-ven.tif"]
        if self.inputs.six_images:
            snapshots.extend(["%s-pos.tif","%s-ant.tif"])
        snapshots = [self._gen_fname(f%stem,suffix="") for f in snapshots]
        outputs["snapshots"] = snapshots
        return outputs

    def _gen_filename(self, name):
        if name == "tcl_script":
            return "snapshots.tcl"
        return None

class ImageInfoInputSpec(FSTraitedSpec):

    in_file = File(exists=True,position=1,argstr="%s",desc="image to query")

class ImageInfoOutputSpec(TraitedSpec):

    info = traits.Any(desc="output of mri_info")
    out_file = File(exists=True,desc="text file with image information")
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
        m = re.search("%s\s*:\s+(.+?)%s"%(field,delim), info) 
        if m:
            return m.group(1)
        else:
            return None

    def aggregate_outputs(self, runtime=None):
        outputs = self._outputs()
        info = runtime.stdout
        outputs.info = info
        
        # Pulse sequence parameters
        for field in ["TE", "TR", "TI"]:
            fieldval = self.info_regexp(info, field, ",")
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
        ftype, dtype = re.findall("%s\s*:\s+(.+?)\n"%"type", info)
        outputs.file_format = ftype
        outputs.data_type = dtype

        return outputs
