# -*- coding: utf-8 -*-
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from ....interfaces.utility import Function, IdentityInterface, Merge
from ....pipeline import engine as pe
from ....interfaces.freesurfer import *
from .utils import copy_file


def copy_ltas(in_file, subjects_dir, subject_id, long_template):
    import os
    out_file = copy_file(in_file,
                         os.path.basename(in_file).replace(
                             long_template, subject_id))
    return out_file


def create_AutoRecon2(name="AutoRecon2",
                      longitudinal=False,
                      plugin_args=None,
                      fsvernum=5.3,
                      stop=None,
                      shrink=None,
                      distance=None):
    # AutoRecon2
    # Workflow
    ar2_wf = pe.Workflow(name=name)

    inputspec = pe.Node(
        IdentityInterface(fields=[
            'orig',
            'nu',  # version < 6
            'brainmask',
            'transform',
            'subject_id',
            'template_talairach_lta',
            'template_talairach_m3z',
            'template_label_intensities',
            'template_aseg',
            'subj_to_template_lta',
            'alltps_to_template_ltas',
            'template_lh_white',
            'template_rh_white',
            'template_lh_pial',
            'template_rh_pial',
            'init_wm',
            'timepoints',
            'alltps_segs',
            'alltps_segs_noCC',
            'alltps_norms',
            'num_threads',
            'reg_template',
            'reg_template_withskull'
        ]),
        run_without_submitting=True,
        name='inputspec')

    # Input node
    if longitudinal:
        # TODO: Work on longitudinal workflow
        inputspec.inputs.timepoints = config['timepoints']

    if fsvernum >= 6:
        # NU Intensity Correction
        """
        Non-parametric Non-uniform intensity Normalization (N3), corrects for
        intensity non-uniformity in MR data, making relatively few assumptions about
        the data. This runs the MINC tool 'nu_correct'.
        """
        intensity_correction = pe.Node(
            MNIBiasCorrection(), name="Intensity_Correction")
        intensity_correction.inputs.out_file = 'nu.mgz'
        ar2_wf.connect([(inputspec, intensity_correction,
                         [('orig', 'in_file'), ('brainmask', 'mask'),
                          ('transform', 'transform')])])

        # intensity correction parameters are more specific in 6+
        intensity_correction.inputs.iterations = 1
        intensity_correction.inputs.protocol_iterations = 1000
        if stop:
            intensity_correction.inputs.stop = stop
        if shrink:
            intensity_correction.inputs.shrink = shrink
        intensity_correction.inputs.distance = distance

        add_to_header_nu = pe.Node(AddXFormToHeader(), name="Add_XForm_to_NU")
        add_to_header_nu.inputs.copy_name = True
        add_to_header_nu.inputs.out_file = 'nu.mgz'
        ar2_wf.connect([(intensity_correction, add_to_header_nu, [
            ('out_file', 'in_file'),
        ]), (inputspec, add_to_header_nu, [('transform', 'transform')])])

    # EM Registration
    """
    Computes the transform to align the mri/nu.mgz volume to the default GCA
    atlas found in FREESURFER_HOME/average (see -gca flag for more info).
    """
    if longitudinal:
        align_transform = pe.Node(
            Function(['in_file', 'out_file'], ['out_file'], copy_file),
            name='Copy_Talairach_lta')
        align_transform.inputs.out_file = 'talairach.lta'

        ar2_wf.connect([(inputspec, align_transform,
                         [('template_talairach_lta', 'in_file')])])
    else:
        align_transform = pe.Node(EMRegister(), name="Align_Transform")
        align_transform.inputs.out_file = 'talairach.lta'
        align_transform.inputs.nbrspacing = 3
        if plugin_args:
            align_transform.plugin_args = plugin_args
        ar2_wf.connect([(inputspec, align_transform,
                         [('brainmask', 'mask'), ('reg_template', 'template'),
                          ('num_threads', 'num_threads')])])
        if fsvernum >= 6:
            ar2_wf.connect([(add_to_header_nu, align_transform,
                             [('out_file', 'in_file')])])
        else:
            ar2_wf.connect([(inputspec, align_transform, [('nu', 'in_file')])])

    # CA Normalize
    """
    Further normalization, based on GCA model. The normalization is based on an
    estimate of the most certain segmentation voxels, which it then uses to
    estimate the bias field/scalings. Creates mri/norm.mgz.
    """
    ca_normalize = pe.Node(CANormalize(), name='CA_Normalize')
    ca_normalize.inputs.out_file = 'norm.mgz'
    if not longitudinal:
        ca_normalize.inputs.control_points = 'ctrl_pts.mgz'
    else:
        copy_template_aseg = pe.Node(
            Function(['in_file', 'out_file'], ['out_file'], copy_file),
            name='Copy_Template_Aseg')
        copy_template_aseg.inputs.out_file = 'aseg_{0}.mgz'.format(
            config['long_template'])

        ar1_wf.connect(
            [(inputspec, copy_template, [('template_aseg', 'in_file')]),
             (copy_template, ca_normalize, [('out_file', 'long_file')])])

    ar2_wf.connect([(align_transform, ca_normalize, [('out_file',
                                                      'transform')]),
                    (inputspec, ca_normalize, [('brainmask', 'mask'),
                                               ('reg_template', 'atlas')])])
    if fsvernum >= 6:
        ar2_wf.connect([(add_to_header_nu, ca_normalize, [('out_file',
                                                           'in_file')])])
    else:
        ar2_wf.connect([(inputspec, ca_normalize, [('nu', 'in_file')])])

    # CA Register
    # Computes a nonlinear transform to align with GCA atlas.
    ca_register = pe.Node(CARegister(), name='CA_Register')
    ca_register.inputs.align = 'after'
    ca_register.inputs.no_big_ventricles = True
    ca_register.inputs.out_file = 'talairach.m3z'
    if plugin_args:
        ca_register.plugin_args = plugin_args
    ar2_wf.connect([(ca_normalize, ca_register, [('out_file', 'in_file')]),
                    (inputspec, ca_register,
                     [('brainmask', 'mask'), ('num_threads', 'num_threads'),
                      ('reg_template', 'template')])])
    if not longitudinal:
        ar2_wf.connect([(align_transform, ca_register, [('out_file',
                                                         'transform')])])
    else:
        ca_register.inputs.levels = 2
        ca_register.inputs.A = 1
        ar2_wf.connect([(inputspec, ca_register, [('template_talairach_m3z',
                                                   'l_files')])])

    # Remove Neck
    """
    The neck region is removed from the NU-corrected volume mri/nu.mgz. Makes use
    of transform computed from prior CA Register stage.
    """
    remove_neck = pe.Node(RemoveNeck(), name='Remove_Neck')
    remove_neck.inputs.radius = 25
    remove_neck.inputs.out_file = 'nu_noneck.mgz'
    ar2_wf.connect([(ca_register, remove_neck, [('out_file', 'transform')]),
                    (inputspec, remove_neck, [('reg_template', 'template')])])
    if fsvernum >= 6:
        ar2_wf.connect([(add_to_header_nu, remove_neck, [('out_file',
                                                          'in_file')])])
    else:
        ar2_wf.connect([(inputspec, remove_neck, [('nu', 'in_file')])])

    # SkullLTA (EM Registration, with Skull)
    # Computes transform to align volume mri/nu_noneck.mgz with GCA volume
    # possessing the skull.
    em_reg_withskull = pe.Node(EMRegister(), name='EM_Register_withSkull')
    em_reg_withskull.inputs.skull = True
    em_reg_withskull.inputs.out_file = 'talairach_with_skull_2.lta'
    if plugin_args:
        em_reg_withskull.plugin_args = plugin_args
    ar2_wf.connect([(align_transform, em_reg_withskull, [('out_file',
                                                          'transform')]),
                    (remove_neck, em_reg_withskull, [('out_file', 'in_file')]),
                    (inputspec, em_reg_withskull,
                     [('num_threads', 'num_threads'),
                      ('reg_template_withskull', 'template')])])

    # SubCort Seg (CA Label)
    # Labels subcortical structures, based in GCA model.
    if longitudinal:
        copy_long_ltas = pe.MapNode(
            Function(
                ['in_file', 'subjects_dir', 'subject_id', 'long_template'],
                ['out_file'], copy_ltas),
            iterfield=['in_file'],
            name='Copy_long_ltas')
        ar2_wf.connect([(inputspec, copy_long_ltas,
                         [('alltps_to_template_ltas', 'in_file'),
                          ('subjects_dir', 'subjects_dir'), ('subject_id',
                                                             'subject_id')])])
        copy_long_ltas.inputs.long_template = config['long_template']

        merge_norms = pe.Node(Merge(2), name="Merge_Norms")

        ar2_wf.connect([(inputspec, merge_norms, [('alltps_norms', 'in1')]),
                        (ca_normalize, merge_norms, [('out_file', 'in2')])])

        fuse_segmentations = pe.Node(
            FuseSegmentations(), name="Fuse_Segmentations")

        ar2_wf.connect([(inputspec, fuse_segmentations, [
            ('timepoints', 'timepoints'), ('alltps_segs', 'in_segmentations'),
            ('alltps_segs_noCC', 'in_segmentations_noCC'), ('subject_id',
                                                            'subject_id')
        ]), (merge_norms, fuse_segmentations, [('out', 'in_norms')])])
        fuse_segmentations.inputs.out_file = 'aseg.fused.mgz'

    ca_label = pe.Node(CALabel(), name='CA_Label')
    if fsvernum >= 6:
        ca_label.inputs.relabel_unlikely = (9, .3)
        ca_label.inputs.prior = 0.5
    ca_label.inputs.align = True
    ca_label.inputs.out_file = 'aseg.auto_noCCseg.mgz'
    if plugin_args:
        ca_label.plugin_args = plugin_args
    ar2_wf.connect([(ca_normalize, ca_label, [('out_file', 'in_file')]),
                    (ca_register, ca_label, [('out_file', 'transform')]),
                    (inputspec, ca_label, [('num_threads', 'num_threads'),
                                           ('reg_template', 'template')])])

    if longitudinal:
        ar2_wf.connect([(fuse_segmentations, ca_label, [('out_file',
                                                         'in_vol')]),
                        (inputspec, ca_label, [('template_label_intensities',
                                                'intensities')])])

    # mri_cc - segments the corpus callosum into five separate labels in the
    # subcortical segmentation volume 'aseg.mgz'
    segment_cc = pe.Node(SegmentCC(), name="Segment_CorpusCallosum")
    segment_cc.inputs.out_rotation = 'cc_up.lta'
    segment_cc.inputs.out_file = 'aseg.auto.mgz'
    segment_cc.inputs.copy_inputs = True
    ar2_wf.connect([
        (ca_label, segment_cc, [('out_file', 'in_file')]),
        (ca_normalize, segment_cc, [('out_file', 'in_norm')]),
    ])

    copy_cc = pe.Node(
        Function(['in_file', 'out_file'], ['out_file'], copy_file),
        name='Copy_CCSegmentation')
    copy_cc.inputs.out_file = 'aseg.presurf.mgz'

    ar2_wf.connect([(segment_cc, copy_cc, [('out_file', 'in_file')])])

    # Normalization2
    """
    Performs a second (major) intensity correction using only the brain volume a
    s the input (so that it has to be done after the skull strip). Intensity
    normalization works better when the skull has been removed. Creates a new
    brain.mgz volume. The -autorecon2-cp stage begins here.
    """
    normalization2 = pe.Node(Normalize(), name="Normalization2")
    normalization2.inputs.out_file = 'brain.mgz'
    ar2_wf.connect([(copy_cc, normalization2, [('out_file', 'segmentation')]),
                    (inputspec, normalization2, [('brainmask', 'mask')]),
                    (ca_normalize, normalization2, [('out_file', 'in_file')])])

    # Mask Brain Final Surface

    # Applies brainmask.mgz to brain.mgz to create brain.finalsurfs.mgz.
    mri_mask = pe.Node(ApplyMask(), name="Mask_Brain_Final_Surface")
    mri_mask.inputs.mask_thresh = 5
    mri_mask.inputs.out_file = 'brain.finalsurfs.mgz'

    ar2_wf.connect([(normalization2, mri_mask, [('out_file', 'in_file')]),
                    (inputspec, mri_mask, [('brainmask', 'mask_file')])])

    # WM Segmentation
    """
    Attempts to separate white matter from everything else. The input is
    mri/brain.mgz, and the output is mri/wm.mgz. Uses intensity, neighborhood,
    and smoothness constraints. This is the volume that is edited when manually
    fixing defects. Calls mri_segment, mri_edit_wm_with_aseg, and mri_pretess.
    """

    wm_seg = pe.Node(SegmentWM(), name="Segment_WM")
    wm_seg.inputs.out_file = 'wm.seg.mgz'
    ar2_wf.connect([(normalization2, wm_seg, [('out_file', 'in_file')])])

    edit_wm = pe.Node(EditWMwithAseg(), name='Edit_WhiteMatter')
    edit_wm.inputs.out_file = 'wm.asegedit.mgz'
    edit_wm.inputs.keep_in = True
    ar2_wf.connect([(wm_seg, edit_wm, [('out_file', 'in_file')]),
                    (copy_cc, edit_wm, [('out_file', 'seg_file')]),
                    (normalization2, edit_wm, [('out_file', 'brain_file')])])

    pretess = pe.Node(MRIPretess(), name="MRI_Pretess")
    pretess.inputs.out_file = 'wm.mgz'
    pretess.inputs.label = 'wm'
    ar2_wf.connect([(edit_wm, pretess, [('out_file', 'in_filled')]),
                    (ca_normalize, pretess, [('out_file', 'in_norm')])])

    if longitudinal:
        transfer_init_wm = pe.Node(ApplyMask(), name="Transfer_Initial_WM")
        transfer_init_wm.inputs.transfer = 255
        transfer_init_wm.inputs.keep_mask_deletion_edits = True
        transfer_init_wm.inputs.out_file = 'wm.mgz'
        ar2_wf.connect([(pretess, transfer_init_wm, [('out_file', 'in_file')]),
                        (inputspec, transfer_init_wm,
                         [('init_wm', 'mask_file'), ('subj_to_template_lta',
                                                     'xfm_file')])])
        # changing the pretess variable so that the rest of the connections still work!!!
        pretess = transfer_init_wm

    # Fill
    """ This creates the subcortical mass from which the orig surface is created.
    The mid brain is cut from the cerebrum, and the hemispheres are cut from each
    other. The left hemisphere is binarized to 255. The right hemisphere is binarized
    to 127. The input is mri/wm.mgz and the output is mri/filled.mgz. Calls mri_fill.
    """

    fill = pe.Node(MRIFill(), name="Fill")
    fill.inputs.log_file = 'ponscc.cut.log'
    fill.inputs.out_file = 'filled.mgz'

    ar2_wf.connect([
        (pretess, fill, [('out_file', 'in_file')]),
        (align_transform, fill, [('out_file', 'transform')]),
        (ca_label, fill, [('out_file', 'segmentation')]),
    ])

    ar2_lh = pe.Workflow("AutoRecon2_Left")
    ar2_rh = pe.Workflow("AutoRecon2_Right")

    # iterate by hemisphere
    for hemisphere in ['lh', 'rh']:
        if hemisphere == 'lh':
            label = 255
            hemi_wf = ar2_lh
        else:
            label = 127
            hemi_wf = ar2_rh

        hemi_inputspec = pe.Node(
            IdentityInterface(fields=[
                'norm', 'filled', 'aseg', 't1', 'wm', 'brain', 'num_threads'
            ]),
            name="inputspec")

        if longitudinal:
            # Make White Surf
            # Copy files from longitudinal base
            copy_template_white = pe.Node(
                Function(['in_file', 'out_file'], ['out_file'], copy_file),
                name='Copy_Template_White')
            copy_template_white.inputs.out_file = '{0}.orig'.format(hemisphere)

            copy_template_orig_white = pe.Node(
                Function(['in_file', 'out_file'], ['out_file'], copy_file),
                name='Copy_Template_Orig_White')
            copy_template_orig_white.inputs.out_file = '{0}.orig_white'.format(
                hemisphere)

            copy_template_orig_pial = pe.Node(
                Function(['in_file', 'out_file'], ['out_file'], copy_file),
                name='Copy_Template_Orig_Pial')
            copy_template_orig_pial.inputs.out_file = '{0}.orig_pial'.format(
                hemisphere)

            # White

            # This function implicitly calls other inputs based on the subject_id
            # wf attempts to make sure files are data sinked to the correct
            # folders before calling
            make_surfaces = pe.Node(MakeSurfaces(), name="Make_Surfaces")
            make_surfaces.inputs.noaparc = True
            make_surfaces.inputs.mgz = True
            make_surfaces.inputs.white_only = True
            make_surfaces.inputs.hemisphere = hemisphere
            make_surfaces.inputs.maximum = 3.5
            make_surfaces.inputs.longitudinal = True
            make_surfaces.inputs.copy_inputs = True

            hemi_wf.connect([(copy_template_orig_white, make_surfaces,
                              [('out_file', 'orig_white')]),
                             (copy_template_white, make_surfaces,
                              [('out_file', 'in_orig')])])

        else:
            # If running single session
            # Tessellate by hemisphere
            """
            This is the step where the orig surface (ie, surf/?h.orig.nofix) is created.
            The surface is created by covering the filled hemisphere with triangles.
            Runs mri_pretess to create a connected WM volume (neighboring voxels must
            have faces in common) and then mri_tessellate to create the surface. The
            places where the points of the triangles meet are called vertices. Creates
            the file surf/?h.orig.nofix Note: the topology fixer will create the surface
            ?h.orig. Finally mris_extract_main_component will remove small surface
            components, not connected to the main body.
            """
            pretess2 = pe.Node(MRIPretess(), name='Pretess2')
            pretess2.inputs.out_file = 'filled-pretess{0}.mgz'.format(label)
            pretess2.inputs.label = label

            hemi_wf.connect([(hemi_inputspec, pretess2,
                              [('norm', 'in_norm'), ('filled', 'in_filled')])])

            tesselate = pe.Node(MRITessellate(), name="Tesselation")
            tesselate.inputs.out_file = "{0}.orig.nofix".format(hemisphere)
            tesselate.inputs.label_value = label
            hemi_wf.connect([(pretess2, tesselate, [('out_file', 'in_file')])])

            extract_main_component = pe.Node(
                ExtractMainComponent(), name="Extract_Main_Component")
            extract_main_component.inputs.out_file = "{0}.orig.nofix".format(
                hemisphere)
            hemi_wf.connect([(tesselate, extract_main_component,
                              [('surface', 'in_file')])])

            copy_orig = pe.Node(
                Function(['in_file', 'out_file'], ['out_file'], copy_file),
                name='Copy_Orig')
            copy_orig.inputs.out_file = '{0}.orig'.format(hemisphere)
            hemi_wf.connect([(extract_main_component, copy_orig,
                              [('out_file', 'in_file')])])

            # Orig Surface Smoothing 1
            """
            After tesselation, the orig surface is very jagged because each triangle is
            on the edge of a voxel face and so are at right angles to each other. The
            vertex positions are adjusted slightly here to reduce the angle. This is
            only necessary for the inflation processes. Creates surf/?h.smoothwm(.nofix).
            Calls mris_smooth. Smooth1 is the step just after tessellation.
            """

            smooth1 = pe.Node(SmoothTessellation(), name="Smooth1")
            smooth1.inputs.disable_estimates = True
            smooth1.inputs.seed = 1234
            smooth1.inputs.out_file = '{0}.smoothwm.nofix'.format(hemisphere)
            hemi_wf.connect([(extract_main_component, smooth1, [('out_file',
                                                                 'in_file')])])

            # Inflation 1
            """
            Inflation of the surf/?h.smoothwm(.nofix) surface to create surf/?h.inflated.
            The inflation attempts to minimize metric distortion so that distances and
            areas are preserved (ie, the surface is not stretched). In this sense, it is
            like inflating a paper bag and not a balloon. Inflate1 is the step just after
            tessellation.
            """

            inflate1 = pe.Node(MRIsInflate(), name="inflate1")
            inflate1.inputs.no_save_sulc = True
            inflate1.inputs.out_file = '{0}.inflated.nofix'.format(hemisphere)

            copy_inflate1 = pe.Node(
                Function(['in_file', 'out_file'], ['out_file'], copy_file),
                name='Copy_Inflate1')
            copy_inflate1.inputs.out_file = '{0}.inflated'.format(hemisphere)
            hemi_wf.connect([
                (smooth1, inflate1, [('surface', 'in_file')]),
                (inflate1, copy_inflate1, [('out_file', 'in_file')]),
            ])

            # Sphere
            """
            This is the initial step of automatic topology fixing. It is a
            quasi-homeomorphic spherical transformation of the inflated surface designed
            to localize topological defects for the subsequent automatic topology fixer.
            Calls mris_sphere.
            """

            qsphere = pe.Node(Sphere(), name="Sphere")
            qsphere.inputs.seed = 1234
            qsphere.inputs.magic = True
            qsphere.inputs.out_file = '{0}.qsphere.nofix'.format(hemisphere)
            if plugin_args:
                qsphere.plugin_args = plugin_args
            hemi_wf.connect([(inflate1, qsphere, [('out_file', 'in_file')]),
                             (hemi_inputspec, qsphere, [('num_threads',
                                                         'num_threads')])])

            # Automatic Topology Fixer
            """
            Finds topological defects (ie, holes in a filled hemisphere) using
            surf/?h.qsphere.nofix, and changes the orig surface (surf/?h.orig.nofix) to
            remove the defects. Changes the number of vertices. All the defects will be
            removed, but the user should check the orig surface in the volume to make
            sure that it looks appropriate.

            This mris_fix_topology does not take in the {lh,rh}.orig file, but instead takes in the
            subject ID and hemisphere and tries to find it from the subjects
            directory.
            """
            fix_topology = pe.Node(FixTopology(), name="Fix_Topology")
            fix_topology.inputs.mgz = True
            fix_topology.inputs.ga = True
            fix_topology.inputs.seed = 1234
            fix_topology.inputs.hemisphere = hemisphere
            fix_topology.inputs.copy_inputs = True
            hemi_wf.connect([(copy_orig, fix_topology,
                              [('out_file',
                                'in_orig')]), (copy_inflate1, fix_topology,
                                               [('out_file', 'in_inflated')]),
                             (qsphere, fix_topology, [('out_file', 'sphere')]),
                             (hemi_inputspec, fix_topology,
                              [('wm', 'in_wm'), ('brain', 'in_brain')])])

            # TODO: halt workflow for bad euler number
            euler_number = pe.Node(EulerNumber(), name="Euler_Number")

            hemi_wf.connect([
                (fix_topology, euler_number, [('out_file', 'in_file')]),
            ])

            remove_intersection = pe.Node(
                RemoveIntersection(), name="Remove_Intersection")
            remove_intersection.inputs.out_file = "{0}.orig".format(hemisphere)

            hemi_wf.connect([(euler_number, remove_intersection,
                              [('out_file', 'in_file')])])

            # White

            # This function implicitly calls other inputs based on the subject_id
            # need to make sure files are data sinked to the correct folders before
            # calling
            make_surfaces = pe.Node(MakeSurfaces(), name="Make_Surfaces")
            make_surfaces.inputs.noaparc = True
            make_surfaces.inputs.mgz = True
            make_surfaces.inputs.white_only = True
            make_surfaces.inputs.hemisphere = hemisphere
            make_surfaces.inputs.copy_inputs = True
            hemi_wf.connect([(remove_intersection, make_surfaces,
                              [('out_file', 'in_orig')]),
                             (hemi_inputspec, make_surfaces,
                              [('aseg', 'in_aseg'), ('t1', 'in_T1'),
                               ('filled', 'in_filled'), ('wm', 'in_wm')])])
            # end of non-longitudinal specific steps

        # Orig Surface Smoothing 2
        """
        After tesselation, the orig surface is very jagged because each triangle is on
        the edge of a voxel face and so are at right angles to each other. The vertex
        positions are adjusted slightly here to reduce the angle. This is only necessary
        for the inflation processes. Smooth2 is the step just after topology
        fixing.
        """
        smooth2 = pe.Node(SmoothTessellation(), name="Smooth2")
        smooth2.inputs.disable_estimates = True
        smooth2.inputs.smoothing_iterations = 3
        smooth2.inputs.seed = 1234
        smooth2.inputs.out_file = '{0}.smoothwm'.format(hemisphere)
        hemi_wf.connect([(make_surfaces, smooth2, [('out_white', 'in_file')])])

        # Inflation 2
        """
        Inflation of the surf/?h.smoothwm(.nofix) surface to create surf/?h.inflated.
        The inflation attempts to minimize metric distortion so that distances and areas
        are preserved (ie, the surface is not stretched). In this sense, it is like
        inflating a paper bag and not a balloon. Inflate2 is the step just after
        topology fixing.
        """
        inflate2 = pe.Node(MRIsInflate(), name="inflate2")
        inflate2.inputs.out_sulc = '{0}.sulc'.format(hemisphere)
        inflate2.inputs.out_file = '{0}.inflated'.format(hemisphere)
        hemi_wf.connect([
            (smooth2, inflate2, [('surface', 'in_file')]),
        ])

        # Compute Curvature
        """No documentation on this step"""

        curvature1 = pe.Node(Curvature(), name="Curvature1")
        curvature1.inputs.save = True
        curvature1.inputs.copy_input = True
        hemi_wf.connect([
            (make_surfaces, curvature1, [('out_white', 'in_file')]),
        ])

        curvature2 = pe.Node(Curvature(), name="Curvature2")
        curvature2.inputs.threshold = .999
        curvature2.inputs.n = True
        curvature2.inputs.averages = 5
        curvature2.inputs.save = True
        curvature2.inputs.distances = (10, 10)
        curvature1.inputs.copy_input = True
        hemi_wf.connect([
            (inflate2, curvature2, [('out_file', 'in_file')]),
        ])

        curvature_stats = pe.Node(CurvatureStats(), name="Curvature_Stats")
        curvature_stats.inputs.min_max = True
        curvature_stats.inputs.write = True
        curvature_stats.inputs.values = True
        curvature_stats.inputs.hemisphere = hemisphere
        curvature_stats.inputs.copy_inputs = True
        curvature_stats.inputs.out_file = '{0}.curv.stats'.format(hemisphere)
        hemi_wf.connect([
            (smooth2, curvature_stats, [('surface', 'surface')]),
            (make_surfaces, curvature_stats, [('out_curv', 'curvfile1')]),
            (inflate2, curvature_stats, [('out_sulc', 'curvfile2')]),
        ])

        if longitudinal:
            ar2_wf.connect([(inputspec, hemi_wf,
                             [('template_{0}_white'.format(hemisphere),
                               'Copy_Template_White.in_file'),
                              ('template_{0}_white'.format(hemisphere),
                               'Copy_Template_Orig_White.in_file'),
                              ('template_{0}_pial'.format(hemisphere),
                               'Copy_Template_Pial.in_file')])])

        # Connect inputs for the hemisphere workflows
        ar2_wf.connect(
            [(ca_normalize, hemi_wf,
              [('out_file', 'inputspec.norm')]), (fill, hemi_wf, [
                  ('out_file', 'inputspec.filled')
              ]), (copy_cc, hemi_wf, [('out_file', 'inputspec.aseg')]),
             (mri_mask, hemi_wf, [('out_file', 'inputspec.t1')]),
             (pretess, hemi_wf, [('out_file',
                                  'inputspec.wm')]), (normalization2, hemi_wf,
                                                      [('out_file',
                                                        'inputspec.brain')]),
             (inputspec, hemi_wf, [('num_threads', 'inputspec.num_threads')])])

        # Outputs for hemisphere workflow
        hemi_outputs = [
            'orig_nofix', 'orig', 'smoothwm_nofix', 'inflated_nofix',
            'qsphere_nofix', 'white', 'curv', 'area', 'cortex', 'pial_auto',
            'thickness', 'smoothwm', 'sulc', 'inflated', 'white_H', 'white_K',
            'inflated_H', 'inflated_K', 'curv_stats'
        ]

        hemi_outputspec = pe.Node(
            IdentityInterface(fields=hemi_outputs), name="outputspec")

        hemi_wf.connect(
            [(extract_main_component, hemi_outputspec,
              [('out_file', 'orig_nofix')]), (inflate1, hemi_outputspec, [
                  ('out_file', 'inflated_nofix')
              ]), (smooth1, hemi_outputspec, [('surface', 'smoothwm_nofix')]),
             (qsphere, hemi_outputspec, [('out_file', 'qsphere_nofix')]),
             (remove_intersection, hemi_outputspec,
              [('out_file', 'orig')]), (make_surfaces, hemi_outputspec, [
                  ('out_white', 'white'), ('out_curv', 'curv'),
                  ('out_area', 'area'), ('out_cortex', 'cortex'), ('out_pial',
                                                                   'pial_auto')
              ]), (smooth2, hemi_outputspec,
                   [('surface', 'smoothwm')]), (inflate2, hemi_outputspec,
                                                [('out_sulc', 'sulc'),
                                                 ('out_file', 'inflated')]),
             (curvature1, hemi_outputspec,
              [('out_mean', 'white_H'),
               ('out_gauss', 'white_K')]), (curvature2, hemi_outputspec, [
                   ('out_mean', 'inflated_H'), ('out_gauss', 'inflated_K')
               ]), (curvature_stats, hemi_outputspec, [('out_file',
                                                        'curv_stats')])])

    outputs = [
        'nu', 'tal_lta', 'norm', 'ctrl_pts', 'tal_m3z', 'nu_noneck',
        'talskull2', 'aseg_noCC', 'cc_up', 'aseg_auto', 'aseg_presurf',
        'brain', 'brain_finalsurfs', 'wm_seg', 'wm_aseg', 'wm', 'ponscc_log',
        'filled'
    ]
    for hemi in ('lh', 'rh'):
        for field in hemi_outputs:
            outputs.append("{0}_".format(hemi) + field)
    outputspec = pe.Node(IdentityInterface(fields=outputs), name="outputspec")

    if fsvernum >= 6:
        ar2_wf.connect([(add_to_header_nu, outputspec, [('out_file', 'nu')])])
    else:
        # add to outputspec to perserve datasinking
        ar2_wf.connect([(inputspec, outputspec, [('nu', 'nu')])])

    ar2_wf.connect([
        (align_transform, outputspec, [('out_file', 'tal_lta')]),
        (ca_normalize, outputspec, [('out_file', 'norm')]),
        (ca_normalize, outputspec, [('control_points', 'ctrl_pts')]),
        (ca_register, outputspec, [('out_file', 'tal_m3z')]),
        (remove_neck, outputspec, [('out_file', 'nu_noneck')]),
        (em_reg_withskull, outputspec, [('out_file', 'talskull2')]),
        (ca_label, outputspec, [('out_file', 'aseg_noCC')]),
        (segment_cc, outputspec, [('out_rotation', 'cc_up'), ('out_file',
                                                              'aseg_auto')]),
        (copy_cc, outputspec, [('out_file', 'aseg_presurf')]),
        (normalization2, outputspec, [('out_file', 'brain')]),
        (mri_mask, outputspec, [('out_file', 'brain_finalsurfs')]),
        (wm_seg, outputspec, [('out_file', 'wm_seg')]),
        (edit_wm, outputspec, [('out_file', 'wm_aseg')]),
        (pretess, outputspec, [('out_file', 'wm')]),
        (fill, outputspec, [('out_file', 'filled'), ('log_file',
                                                     'ponscc_log')]),
    ])

    for hemi, hemi_wf in [('lh', ar2_lh), ('rh', ar2_rh)]:
        for field in hemi_outputs:
            output = "{0}_".format(hemi) + field
            ar2_wf.connect([(hemi_wf, outputspec, [("outputspec." + field,
                                                    output)])])

    return ar2_wf, outputs
