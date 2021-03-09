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
    """
    CAT12: Segmentation
    This toolbox is an extension to the default segmentation in SPM12, but uses a completely different segmentation
    approach.
    The segmentation approach is based on an Adaptive Maximum A Posterior (MAP) technique without the need for a priori
    information about tissue probabilities. That is, the Tissue Probability Maps (TPM) are not used constantly in the
    sense of the classical Unified Segmentation approach (Ashburner et. al. 2005), but just for spatial normalization.
    The following AMAP estimation is adaptive in the sense that local variations of the parameters (i.e., means and
    variance) are modeled as slowly varying spatial functions (Rajapakse et al. 1997). This not only accounts for
    intensity inhomogeneities but also for other local variations of intensity.
    Additionally, the segmentation approach uses a Partial Volume Estimation (PVE) with a simplified mixed model of at
    most two tissue types (Tohka et al. 2004). We start with an initial segmentation into three pure classes: gray
    matter (GM), white matter (WM), and cerebrospinal fluid (CSF) based on the above described AMAP estimation. The
    initial segmentation is followed by a PVE of two additional mixed classes: GM-WM and GM-CSF. This results in an
    estimation of the amount (or fraction) of each pure tissue type present in every voxel (as single voxels - given by
    Another important extension to the SPM12 segmentation is the integration of the Dartel or Geodesic Shooting
    registration into the toolbox by an already existing Dartel/Shooting template in MNI space. This template was
    derived from 555 healthy control subjects of the IXI-database (http://www.brain-development.org) and provides the
    several Dartel or Shooting iterations. Thus, for the majority of studies the creation of sample-specific templates
    is not necessary anymore and is mainly recommended for children data.'};

    http://www.neuro.uni-jena.de/cat12/CAT12-Manual.pdf#page=15

    Examples
    --------
    >>> path_mr = 'structural.nii'
    >>> cat = CAT12Segment(in_files=path_mr)
    >>> cat.run() # doctest: +SKIP
    """

    in_files = InputMultiPath(ImageFileSPM(exists=True), field="data", desc="file to segment", mandatory=True,
                              copyfile=False)

    help_tpm = 'Tissue Probability Map. Select the tissue probability image that includes 6 tissue probability ' \
               'classes for (1) grey matter, (2) white matter, (3) cerebrospinal fluid, (4) bone, (5) non-brain soft ' \
               'tissue, and (6) the background.  CAT uses the TPM only for the initial SPM segmentation.'
    tpm = InputMultiPath(ImageFileSPM(exists=True), field="tpm", desc=help_tpm, mandatory=False,
                         copyfile=False)

    n_jobs = traits.trait_types.Int(1, usedefault=True, mandatory=True, field="nproc", desc="Number of threads")
    use_prior = traits.trait_types.Str(field="useprior", usedefault=True)

    affine_reg_help = 'Affine Regularization. The procedure is a local optimisation, so it needs reasonable initial ' \
                      'starting estimates. Images should be placed in approximate alignment using the Display ' \
                      'function of SPM before beginning.  A Mutual Information affine registration with the tissue ' \
                      'probability maps (D''Agostino et al, 2004) is used to achieve approximate alignment.'
    affine_regularization = traits.trait_types.Str(default_value="mni",
                                                   field="opts.affreg", usedefault=True, desc=affine_reg_help)

    bias_acc_help = "Strength of the SPM inhomogeneity (bias) correction that simultaneously controls the SPM biasreg, " \
                    "biasfwhm, samp (resolution), and tol (iteration) parameter."
    power_spm_inhomogeneity_correction = traits.trait_types.Float(default_value=0.5, field='opts.biasacc',
                                                                  usedefault=True,
                                                                  desc=bias_acc_help)
    # Extended options for CAT12 preprocessing
    help_app = 'Affine registration and SPM preprocessing can fail in some subjects with deviating anatomy (e.g. ' \
               'other species/neonates) or in images with strong signal inhomogeneities, or untypical intensities ' \
               '(e.g. synthetic images). An initial bias correction can help to reduce such problems (see details ' \
               'below). Recommended are the "default" and "full" option.'
    affine_preprocessing = traits.trait_types.Int(1070, field="extopts.APP", desc=help_app, usedefault=True)

    help_initial_seg = 'In rare cases the Unified Segmentation can fail in highly abnormal brains, where e.g. the ' \
                       'cerebrospinal fluid of superlarge ventricles (hydrocephalus) were classified as white matter.' \
                       ' However, if the affine registration is correct, the AMAP segmentation with an ' \
                       'prior-independent k-means initialization can be used to replace the SPM brain tissue ' \
                       'classification. Moreover, if the default Dartel and Shooting registrations will fail then the' \
                       ' "Optimized Shooting - superlarge ventricles" option for "Spatial registration" is required! ' \
                       'Values: \nnone: 0;\nlight: 1;\nfull: 2;\ndefault: 1070.'
    initial_segmentation = traits.trait_types.Int(0, field="extopts.spm_kamap", desc=help_initial_seg, usedefault=True)

    help_las = 'Additionally to WM-inhomogeneities, GM intensity can vary across different regions such as the motor' \
               ' cortex, the basal ganglia, or the occipital lobe. These changes have an anatomical background ' \
               '(e.g. iron content, myelinization), but are dependent on the MR-protocol and often lead to ' \
               'underestimation of GM at higher intensities and overestimation of CSF at lower intensities. ' \
               'Therefore, a local intensity transformation of all tissue classes is used to reduce these effects in ' \
               'the image. This local adaptive segmentation (LAS) is applied before the final AMAP segmentation.' \
               'Possible Values: \nSPM Unified Segmentation: 0 \nk-means AMAP: 2'
    local_adaptive_seg = traits.trait_types.Float(0.5, field="extopts.LASstr", usedefault=True, desc=help_las)

    help_gcutstr = 'Method of initial skull-stripping before AMAP segmentation. The SPM approach works quite stable ' \
                   'for the majority of data. However, in some rare cases parts of GM (i.e. in frontal lobe) might ' \
                   'be cut. If this happens the GCUT approach is a good alternative. GCUT is a graph-cut/region-' \
                   'growing approach starting from the WM area. APRG (adaptive probability region-growing) is a new' \
                   ' method that refines the probability maps of the SPM approach by region-growing techniques of ' \
                   'the gcut approach with a final surface-based optimization strategy. This is currently the method ' \
                   'with the most accurate and reliable results. If you use already skull-stripped data you can turn' \
                   ' off skull-stripping although this is automaticaly detected in most cases. Please note that the' \
                   ' choice of the skull-stripping method will also influence the estimation of TIV, because the' \
                   ' methods mainly differ in the handling of the outer CSF around the cortical surface. ' \
                   '\nPossible Values:\n - none (already skull-stripped): -1;\n - SPM approach: 0; ' \
                   '\n - GCUT approach: 0.50; \n - APRG approach: 2'
    skull_strip = traits.trait_types.Float(2, field="extopts.gcutstr", desc=help_gcutstr, usedefault=True)

    help_wmhc = 'WARNING: Please note that the detection of WM hyperintensies is still under development and does ' \
                'not have the same accuracy as approaches that additionally consider FLAIR images (e.g. Lesion ' \
                'Segmentation Toolbox)! In aging or (neurodegenerative) diseases WM intensity can be reduced ' \
                'locally in T1 or increased in T2/PD images. These so-called WM hyperintensies (WMHs) can lead to ' \
                'preprocessing errors. Large GM areas next to the ventricle can cause normalization problems. ' \
                'Therefore, a temporary correction for normalization is useful if WMHs are expected. CAT allows ' \
                'different ways to handle WMHs: ' \
                '\n0) No Correction (handled as GM). \n1) Temporary (internal) correction as WM for spatial ' \
                'normalization and estimation of cortical thickness. \n2) Permanent correction to WM. '
    wm_hyper_intensity_correction = traits.trait_types.Int(1, field="extopts.WMHC", desc=help_wmhc, usedefault=True)

    help_vox = 'The (isotropic) voxel sizes of any spatially normalised written images. A non-finite value will be ' \
               'replaced by the average voxel size of the tissue probability maps used by the segmentation.'
    voxel_size = traits.trait_types.Float(1.5, field="extopts.vox", desc=help_vox, usedefault=True)

    help_resampling = 'Internal resampling for preprocessing.\n The default fixed image resolution offers a good ' \
                      'trade-off between optimal quality and preprocessing time and memory demands. Standard ' \
                      'structural data with a voxel resolution around 1 mm or even data with high in-plane resolution' \
                      ' and large slice thickness (e.g. 0.5x0.5x1.5 mm) will benefit from this setting. If you have' \
                      ' higher native resolutions the highres option "Fixed 0.8 mm" will sometimes offer slightly' \
                      ' better preprocessing quality with an increase of preprocessing time and memory demands. In' \
                      ' case of even higher resolutions and high signal-to-noise ratio (e.g. for 7 T data) the ' \
                      '"Best native" option will process the data on the highest native resolution. I.e. a resolution' \
                      ' of 0.4x0.7x1.0 mm will be interpolated to 0.4x0.4x0.4 mm. A tolerance range of 0.1 mm is used' \
                      ' to avoid interpolation artifacts, i.e. a resolution of 0.95x1.01x1.08 mm will not be ' \
                      'interpolated in case of the "Fixed 1.0 mm"! This "optimal" option prefers an isotropic voxel ' \
                      'size with at least 1.1 mm that is controlled by the median voxel size and a volume term that ' \
                      'penalizes highly anisotropic voxels.' \
                      'Values:\nOptimal: [1.0 0.1]\nFixed 1.0 mm: [1.0 0.1];\nFixed 0.8 mm:[0.8 0.1]' \
                      '\nBest native: [0.5 0.1]'
    internal_resampling_process = traits.trait_types.Tuple(traits.trait_types.Float(1), traits.trait_types.Float(0.1),
                                                           minlen=2, maxlen=2,
                                                           field="extopts.restypes.optimal", desc="help_resampling",
                                                           usedefault=True)
    errors_help = 'Error handling.\nTry to catch preprocessing errors and continue with the next data set or ignore ' \
                  'all warnings (e.g., bad intensities) and use an experimental pipeline which is still in ' \
                  'development. In case of errors, CAT continues with the next subject if this option is enabled. If ' \
                  'the experimental option with backup functions is selected and warnings occur, CAT will try to use' \
                  ' backup routines and skip some processing steps which require good T1 contrasts (e.g., LAS). If ' \
                  'you want to avoid processing of critical data and ensure that only the main pipeline is used then' \
                  ' select the option "Ignore errors (continue with the next subject)". It is strongly recommended to' \
                  ' check for preprocessing problems, especially with non-T1 contrasts. ' \
                  '\nValues:\nnone: 0,\ndefault: 1,\ndetails: 2.'
    ignore_errors = traits.trait_types.Int(1, field="extopts.ignoreErrors", desc=errors_help, usedefault=True)

    # Writing options
    help_surf = 'Surface and thickness estimation. \nUse projection-based thickness (PBT) (Dahnke et al. 2012) to' \
                ' estimate cortical thickness and to create the central cortical surface for left and right ' \
                'hemisphere. Surface reconstruction includes topology correction (Yotter et al. 2011), spherical ' \
                'inflation (Yotter et al.) and spherical registration. Additionally you can also estimate surface ' \
                'parameters such as gyrification, cortical complexity or sulcal depth that can be subsequently ' \
                'analyzed at each vertex of the surface. Please note, that surface reconstruction and spherical ' \
                'registration additionally requires about 20-60 min of computation time. A fast (1-3 min) surface ' \
                'pipeline is available for visual preview (e.g., to check preprocessing quality) in the ' \
                'cross-sectional, but not in the longitudinal pipeline.  Only the initial surfaces are created with a' \
                ' lower resolution and without topology correction, spherical mapping and surface registration. ' \
                'Please note that the files with the estimated surface thickness can therefore not be used for ' \
                'further analysis!  For distinction, these files contain "preview" in their filename and they' \
                ' are not available as batch dependencies objects. '
    surface_and_thickness_estimation = traits.trait_types.Int(1, field="surface", desc=help_surf, usedefault=True)
    surface_measures = traits.trait_types.Int(1, field="output.surf_measures", usedefault=True)

    # Templates
    neuromorphometrics = traits.trait_types.Bool(True, field="output.ROImenu.atlases.neuromorphometrics",
                                                 usedefault=True)
    lpba40 = traits.trait_types.Bool(False, field="output.ROImenu.atlases.lpba40", usedefault=True)
    cobra = traits.trait_types.Bool(True, field="output.ROImenu.atlases.hammers", usedefault=True)
    hammers = traits.trait_types.Bool(False, field="output.ROImenu.atlases.cobra", usedefault=True)
    own_atlas = InputMultiPath(ImageFileSPM(exists=True), field="output.ROImenu.atlases.ownatlas",
                               desc="Own Atlas", mandatory=False, copyfile=False)

    dartel_help = 'This option is to export data into a form that can be used with DARTEL. The SPM default is to ' \
                  'only apply rigid body transformation. However, a more appropriate option is to apply affine ' \
                  'transformation, because the additional scaling of the images requires less deformations to ' \
                  'non-linearly register brains to the template.'

    # Grey matter
    gm_desc = 'Options to save grey matter images.'
    gm_output_native = traits.trait_types.Bool(False, field="output.GM.native", usedefault=True, desc=gm_desc)
    gm_output_modulated = traits.trait_types.Bool(True, field="output.GM.mod", usedefault=True, desc=gm_desc)
    gm_output_dartel = traits.trait_types.Bool(False, field="output.GM.dartel", usedefault=True, desc=gm_desc)

    # White matter
    wm_desc = 'Options to save white matter images.'
    wm_output_native = traits.trait_types.Bool(False, field="output.WM.native", usedefault=True, desc=wm_desc)
    wm_output_modulated = traits.trait_types.Bool(True, field="output.WM.mod", usedefault=True, desc=wm_desc)
    wm_output_dartel = traits.trait_types.Bool(False, field="output.WM.dartel", usedefault=True, desc=wm_desc)

    # CSF matter
    csf_desc = 'Options to save CSF images.'
    csf_output_native = traits.trait_types.Bool(False, field="output.CSF.native", usedefault=True, desc=csf_desc)
    csf_output_modulated = traits.trait_types.Bool(True, field="output.CSF.mod", usedefault=True, desc=csf_desc)
    csf_output_dartel = traits.trait_types.Bool(False, field="output.CSF.dartel", usedefault=True, desc=csf_desc)

    # Labels
    label_desc = 'This is the option to save a labeled version of your segmentations for fast visual comparision. ' \
                 'Labels are saved as Partial Volume Estimation (PVE) values with different mix classes for GM-WM ' \
                 '(2.5) and GM-CSF (1.5). BG=0, CSF=1, GM=2, WM=3, WMH=4 (if WMHC=3), SL=1.5 (if SLC)'
    label_native = traits.trait_types.Bool(False, field="output.label.native", usedefault=True, desc=label_desc)
    label_warped = traits.trait_types.Bool(True, field="output.label.warped", usedefault=True, desc=label_desc)
    label_dartel = traits.trait_types.Bool(False, field="output.label.dartel", usedefault=True, desc=label_desc)
    output_labelnative = traits.trait_types.Bool(False, field="output.labelnative", usedefault=True, desc=label_desc)

    # Bias
    save_bias_corrected = traits.trait_types.Bool(True, field="output.bias.warped", usedefault=True)

    # las
    las_desc = 'This is the option to save a bias, noise, and local intensity corrected version of the original T1' \
               ' image. MR images are usually corrupted by a smooth, spatially varying artifact that modulates the' \
               ' intensity of the image (bias). These artifacts, although not usually a problem for visual ' \
               'inspection, can impede automated processing of the images. The bias corrected version should have ' \
               'more uniform intensities within the different types of tissues and can be saved in native space ' \
               'and/or normalised. Noise is corrected by an adaptive non-local mean (NLM) filter (Manjon 2008, ' \
               'Medical Image Analysis 12).'
    las_native = traits.trait_types.Bool(False, field="output.las.native", usedefault=True, desc=las_desc)
    las_warped = traits.trait_types.Bool(True, field="output.las.warped", usedefault=True, desc=las_desc)
    las_dartel = traits.trait_types.Bool(False, field="output.las.dartel", usedefault=True, desc=las_desc)

    # Jacobian Warped
    help_jacobian = 'This is the option to save the Jacobian determinant, which expresses local volume changes. This' \
                    ' image can be used in a pure deformation based morphometry (DBM) design. Please note that the' \
                    ' affine part of the deformation field is ignored. Thus, there is no need for any additional' \
                    ' correction for different brain sizes using ICV.'
    jacobianwarped = traits.trait_types.Bool(True, field="output.jacobianwarped", usedefault=True, desc=help_jacobian)

    # Deformation Fields
    help_warp = 'Deformation fields can be saved to disk, and used by the Deformations Utility and/or applied to ' \
                'coregistered data from other modalities (e.g. fMRI). For spatially normalising images to MNI space,' \
                ' you will need the forward deformation, whereas for spatially normalising (eg) GIFTI surface files,' \
                ' you''ll need the inverse. It is also possible to transform data in MNI space on to the individual' \
                ' subject, which also requires the inverse transform. Deformations are saved as .nii files, which' \
                ' contain three volumes to encode the x, y and z coordinates.' \
                '\nValues: No:[0 0];\nImage->Template (forward): [1 0];\nTemplate->Image (inverse): [0 1]; ' \
                '\ninverse + forward: [1 1]'
    warps = traits.trait_types.Tuple(traits.trait_types.Int(1), traits.trait_types.Int(0), minlen=2, maxlen=2,
                                     field="output.warps", usedefault=True, desc=help_warp)


class CAT12SegmentOutputSpec(TraitedSpec):
    ##########################################
    # Label XML files
    ##########################################
    label_files = List(File(exists=True), desc="Files with the measures extracted for OI ands ROIs")

    label_rois = File(exists=True, desc="Files with thickness values of ROIs.")
    label_roi = File(exists=True, desc="Files with thickness values of ROI.")

    ##########################################
    # MRI .nii files
    ##########################################

    mri_images = List(File(exists=True), desc="Different segmented images.")

    # Grey Matter
    gm_modulated_image = File(exists=True, desc="Grey matter modulated image.")
    gm_dartel_image = File(exists=True, desc="Grey matter dartel image.")
    gm_native_image = File(exists=True, desc="Grey matter native space.")

    # White Matter
    wm_modulated_image = File(exists=True, desc="White matter modulated image.")
    wm_dartel_image = File(exists=True, desc="White matter dartel image.")
    wm_native_image = File(exists=True, desc="White matter in native space.")

    # CSF
    csf_modulated_image = File(exists=True, desc="CSF modulated image.")
    csf_dartel_image = File(exists=True, desc="CSF dartel image.")
    csf_native_image = File(exists=True, desc="CSF in native space.")

    bias_corrected_image = File(exists=True, desc="Bias corrected image")
    ##########################################
    # Surface files
    ##########################################

    surface_files = List(File(exists=True), desc="Surface files")

    # Right hemisphere
    rh_central_surface = File(exists=True, desc="Central right hemisphere files")
    rh_sphere_surface = File(exists=True, desc="Sphere right hemisphere files")

    # Left hemisphere
    lh_central_surface = File(exists=True, desc="Central left hemisphere files")
    lh_sphere_surface = File(exists=True, desc="Sphere left hemisphere files")

    # Report files
    report_files = List(File(exists=True), desc="Report files.")
    report = File(exists=True, desc="Report file.")


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
