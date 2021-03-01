import os
import sys
import traits
from nipype.interfaces.base import InputMultiPath, TraitedSpec, isdefined
from nipype.interfaces.spm import SPMCommand
from nipype.interfaces.spm.base import SPMCommandInputSpec, ImageFileSPM, scans_for_fnames, scans_for_fname
from nipype.utils.filemanip import split_filename, fname_presuffix
from traits.trait_types import Int, File
from traits.trait_types import List


class CAT12SegmentInputSpec(SPMCommandInputSpec):
    in_files = InputMultiPath(ImageFileSPM(exists=True), field="data", desc="file to segment", mandatory=True,
                              copyfile=False)

    tpm = InputMultiPath(ImageFileSPM(exists=True), field="tpm", desc="Tissue Probability Maps", mandatory=False,
                         copyfile=False)

    n_jobs = traits.trait_types.Int(1, usedefault=True, mandatory=True, field="nproc", desc="Number of threads")
    use_prior = traits.trait_types.Str(field="useprior", usedefault=True)

    affine_regularization = traits.trait_types.Str(default_value="mni",
                                                   field="opts.affreg", usedefault=True)

    power_spm_inhomogeneity_correction = traits.trait_types.Float(default_value=0.5, field='opts.biasacc',
                                                                  usedefault=True)
    # Extended options for CAT12 preprocessing
    affine_preprocessing = traits.trait_types.Int(1070, field="extopts.APP", usedefault=True)
    initial_segmentation = traits.trait_types.Int(0, field="extopts.spm_kamap", usedefault=True)
    local_adaptive_seg = traits.trait_types.Float(0.5, field="extopts.LASstr", usedefault=True)
    skull_strip = traits.trait_types.Float(2, field="extopts.gcutstr", usedefault=True)
    wm_hyper_intensity_correction = traits.trait_types.Int(1, field="extopts.WMHC", usedefault=True)
    spatial_registration = traits.trait_types.Int(1, field="extopts.WMHC", usedefault=True)
    voxel_size = traits.trait_types.Float(1.5, field="extopts.vox", usedefault=True)
    internal_resampling_process = traits.trait_types.Tuple(traits.trait_types.Float(1), traits.trait_types.Float(0.1),
                                                           minlen=2, maxlen=2,
                                                           field="extopts.restypes.optimal", usedefault=True)
    ignore_errors = traits.trait_types.Int(1, field="extopts.ignoreErrors", usedefault=True)

    # Writing options
    surface_and_thickness_estimation = traits.trait_types.Int(1, field="surface", usedefault=True)
    surface_measures = traits.trait_types.Int(1, field="output.surf_measures", usedefault=True)

    # Templates
    neuromorphometrics = traits.trait_types.Bool(True, field="output.ROImenu.atlases.neuromorphometrics",
                                                 usedefault=True)
    lpba40 = traits.trait_types.Bool(False, field="output.ROImenu.atlases.lpba40", usedefault=True)
    cobra = traits.trait_types.Bool(True, field="output.ROImenu.atlases.hammers", usedefault=True)
    hammers = traits.trait_types.Bool(False, field="output.ROImenu.atlases.cobra", usedefault=True)
    own_atlas = InputMultiPath(ImageFileSPM(exists=True), field="output.ROImenu.atlases.ownatlas",
                               desc="Own Atlas", mandatory=False, copyfile=False)

    # Grey matter
    gm_output_native = traits.trait_types.Bool(False, field="output.GM.native", usedefault=True)
    gm_output_modulated = traits.trait_types.Bool(True, field="output.GM.mod", usedefault=True)
    gm_output_dartel = traits.trait_types.Bool(False, field="output.GM.dartel", usedefault=True)

    # White matter
    wm_output_native = traits.trait_types.Bool(False, field="output.WM.native", usedefault=True)
    wm_output_modulated = traits.trait_types.Bool(True, field="output.WM.mod", usedefault=True)
    wm_output_dartel = traits.trait_types.Bool(False, field="output.WM.dartel", usedefault=True)

    # CSF matter
    csf_output_native = traits.trait_types.Bool(False, field="output.CSF.native", usedefault=True)
    csf_output_modulated = traits.trait_types.Bool(True, field="output.CSF.mod", usedefault=True)
    csf_output_dartel = traits.trait_types.Bool(False, field="output.CSF.dartel", usedefault=True)

    # Labels
    label_native = traits.trait_types.Bool(False, field="output.label.native", usedefault=True)
    label_warped = traits.trait_types.Bool(True, field="output.label.warped", usedefault=True)
    label_dartel = traits.trait_types.Bool(False, field="output.label.dartel", usedefault=True)
    output_labelnative = traits.trait_types.Bool(False, field="output.labelnative", usedefault=True)

    # Bias
    save_bias_corrected = traits.trait_types.Bool(True, field="output.bias.warped", usedefault=True)

    # las
    las_native = traits.trait_types.Bool(False, field="output.las.native", usedefault=True)
    las_warped = traits.trait_types.Bool(True, field="output.las.warped", usedefault=True)
    las_dartel = traits.trait_types.Bool(False, field="output.las.dartel", usedefault=True)

    # Jacobian Warped
    jacobianwarped = traits.trait_types.Bool(True, field="output.jacobianwarped", usedefault=True)

    # Deformation Fields
    warps = traits.trait_types.Tuple(traits.trait_types.Int(1), traits.trait_types.Int(0), minlen=2, maxlen=2,
                                     field="output.warps", usedefault=True)


class CAT12SegmentOutputSpec(TraitedSpec):
    ##########################################
    # Label XML files
    ##########################################
    label_files = List(File(exists=True))

    label_rois = File(exists=True, desc="ROIs Volumes")
    label_roi = File(exists=True, desc="ROI volumes")

    ##########################################
    # MRI .nii files
    ##########################################

    mri_images = List(File(exists=True))

    # Grey Matter
    gm_modulated_image = File(exists=True)
    gm_dartel_image = File(exists=True)
    gm_native_image = File(exists=True)

    # White Matter
    wm_modulated_image = File(exists=True)
    wm_dartel_image = File(exists=True)
    wm_native_image = File(exists=True)

    # CSF
    csf_modulated_image = File(exists=True)
    csf_dartel_image = File(exists=True)
    csf_native_image = File(exists=True)

    bias_corrected_image = File(exists=True)
    ##########################################
    # Surface files
    ##########################################

    surface_files = List(File(exists=True))

    # Right hemisphere
    rh_central_surface = File(exists=True)
    rh_sphere_surface = File(exists=True)

    # Left hemisphere
    lh_central_surface = File(exists=True)
    lh_sphere_surface = File(exists=True)

    # Report files
    report_files = List(File(exists=True))
    report = File(exists=True)


class CAT12Segment(SPMCommand):
    input_spec = CAT12SegmentInputSpec
    output_spec = CAT12SegmentOutputSpec

    def __init__(self, **inputs):
        _local_version = SPMCommand().version
        if _local_version and "12." in _local_version:
            self._jobtype = "tools"
            self._jobname = "cat.estwrite"

        SPMCommand.__init__(self, **inputs)

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt in ["in_files"]:
            if isinstance(val, list):
                return scans_for_fnames(val)
            else:
                return scans_for_fname(val)
        return super(CAT12Segment, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        f = self.inputs.in_files[0]
        pth, base, ext = split_filename(f)

        outputs["mri_images"] = [os.path.join(os.path.join(pth, "mri"), f) for f in
                                 os.listdir(os.path.join(pth, "mri"))
                                 if os.path.isfile(os.path.join(os.path.join(pth, "mri"), f))]

        for tidx, tissue in enumerate(["gm", "wm", "csf"]):

            for idx, (image, prefix) in enumerate([("modulated", "mw"), ("dartel", "r"), ("native", "")]):
                outtype = f'{tissue}_output_{image}'
                if isdefined(getattr(self.inputs, outtype)) and getattr(self.inputs, outtype):
                    outfield = f'{tissue}_{image}_image'
                    prefix = os.path.join("mri", f'{prefix}p{tidx + 1}')
                    if image != "dartel":
                        outputs[outfield] = fname_presuffix(f, prefix=prefix)
                    else:
                        outputs[outfield] = fname_presuffix(f, prefix=prefix, suffix="_rigid")

        if isdefined(self.inputs.save_bias_corrected) and self.inputs.save_bias_corrected:
            outputs["bias_corrected_image"] = fname_presuffix(f, prefix=os.path.join("mri", 'mi'))

        outputs["surface_files"] = [os.path.join(os.path.join(pth, "surf"), f) for f in
                                    os.listdir(os.path.join(pth, "surf"))
                                    if os.path.isfile(os.path.join(os.path.join(pth, "surf"), f))]

        for tidx, hemisphere in enumerate(["rh", "lh"]):
            for idx, suffix in enumerate(["central", "sphere"]):
                outfield = f'{hemisphere}_{suffix}_surface'
                outputs[outfield] = fname_presuffix(f, prefix=os.path.join("surf", f'{hemisphere}.{suffix}.'),
                                                    suffix=".gii", use_ext=False)

        outputs["report_files"] = [os.path.join(os.path.join(pth, "report"), f) for f in
                                   os.listdir(os.path.join(pth, "report"))
                                   if os.path.isfile(os.path.join(os.path.join(pth, "report"), f))]
        outputs[f'report'] = fname_presuffix(f, prefix=os.path.join("report", f'cat_'), suffix=".xml", use_ext=False)

        outputs["label_files"] = [os.path.join(os.path.join(pth, "label"), f) for f in
                                  os.listdir(os.path.join(pth, "label"))
                                  if os.path.isfile(os.path.join(os.path.join(pth, "label"), f))]

        outputs['label_rois'] = fname_presuffix(f, prefix=os.path.join("label", f'catROIs_'), suffix=".xml",
                                                use_ext=False)
        outputs['label_roi'] = fname_presuffix(f, prefix=os.path.join("label", f'catROI_'), suffix=".xml",
                                               use_ext=False)

        return outputs


if __name__ == '__main__':
    path_mr = sys.argv[1]
    cat = CAT12Segment(in_files=path_mr)
    cat.run()
