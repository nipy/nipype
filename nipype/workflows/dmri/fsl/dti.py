import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.fsl as fsl


def transpose(samples_over_fibres):
    import numpy as np
    a = np.array(samples_over_fibres)
    if len(a.shape)==1:
        a = a.reshape(-1,1)
    return a.T.tolist()

def create_bedpostx_pipeline(name="bedpostx"):
    """Creates a pipeline that does the same as bedpostx script from FSL -
    calculates diffusion model parameters (distributions not MLE) voxelwise for
    the whole volume (by splitting it slicewise).

    Example
    -------

    >>> nipype_bedpostx = create_bedpostx_pipeline("nipype_bedpostx")
    >>> nipype_bedpostx.inputs.inputnode.dwi = 'diffusion.nii'
    >>> nipype_bedpostx.inputs.inputnode.mask = 'mask.nii'
    >>> nipype_bedpostx.inputs.inputnode.bvecs = 'bvecs'
    >>> nipype_bedpostx.inputs.inputnode.bvals = 'bvals'
    >>> nipype_bedpostx.inputs.xfibres.n_fibres = 2
    >>> nipype_bedpostx.inputs.xfibres.fudge = 1
    >>> nipype_bedpostx.inputs.xfibres.burn_in = 1000
    >>> nipype_bedpostx.inputs.xfibres.n_jumps = 1250
    >>> nipype_bedpostx.inputs.xfibres.sample_every = 25
    >>> nipype_bedpostx.run() # doctest: +SKIP

    Inputs::

        inputnode.dwi
        inputnode.mask

    Outputs::

        outputnode.thsamples
        outputnode.phsamples
        outputnode.fsamples
        outputnode.mean_thsamples
        outputnode.mean_phsamples
        outputnode.mean_fsamples
        outputnode.dyads
        outputnode.dyads_dispersion

    """


    inputnode = pe.Node(interface = util.IdentityInterface(fields=["dwi", "mask"]),
                        name="inputnode")

    mask_dwi = pe.Node(interface = fsl.ImageMaths(op_string = "-mas"),
                       name="mask_dwi")
    slice_dwi = pe.Node(interface = fsl.Split(dimension="z"), name="slice_dwi")
    slice_mask = pe.Node(interface = fsl.Split(dimension="z"),
                         name="slice_mask")

    preproc = pe.Workflow(name="preproc")

    preproc.connect([(inputnode, mask_dwi, [('dwi', 'in_file')]),
                     (inputnode, mask_dwi, [('mask', 'in_file2')]),
                     (mask_dwi, slice_dwi, [('out_file', 'in_file')]),
                     (inputnode, slice_mask, [('mask', 'in_file')])
                     ])

    xfibres = pe.MapNode(interface=fsl.XFibres(), name="xfibres",
                         iterfield=['dwi', 'mask'])


    # Normal set of parameters
    xfibres.inputs.n_fibres = 2
    xfibres.inputs.fudge = 1
    xfibres.inputs.burn_in = 1000
    xfibres.inputs.n_jumps = 1250
    xfibres.inputs.sample_every = 25
    xfibres.inputs.model = 1
    xfibres.inputs.non_linear = True
    xfibres.inputs.update_proposal_every = 24

    inputnode = pe.Node(interface = util.IdentityInterface(fields=["thsamples",
                                                                   "phsamples",
                                                                   "fsamples",
                                                                   "dyads",
                                                                   "mean_dsamples",
                                                                   "mask"]),
                        name="inputnode")

    merge_thsamples = pe.MapNode(fsl.Merge(dimension="z"),
                                 name="merge_thsamples", iterfield=['in_files'])
    merge_phsamples = pe.MapNode(fsl.Merge(dimension="z"),
                                 name="merge_phsamples", iterfield=['in_files'])
    merge_fsamples = pe.MapNode(fsl.Merge(dimension="z"),
                                name="merge_fsamples", iterfield=['in_files'])


    merge_mean_dsamples = pe.Node(fsl.Merge(dimension="z"),
                                  name="merge_mean_dsamples")

    mean_thsamples = pe.MapNode(fsl.ImageMaths(op_string="-Tmean"),
                                name="mean_thsamples", iterfield=['in_file'])
    mean_phsamples = pe.MapNode(fsl.ImageMaths(op_string="-Tmean"),
                                name="mean_phsamples", iterfield=['in_file'])
    mean_fsamples = pe.MapNode(fsl.ImageMaths(op_string="-Tmean"),
                               name="mean_fsamples", iterfield=['in_file'])
    make_dyads = pe.MapNode(fsl.MakeDyadicVectors(), name="make_dyads",
                            iterfield=['theta_vol', 'phi_vol'])

    postproc = pe.Workflow(name="postproc")

    postproc.connect([(inputnode, merge_thsamples, [(('thsamples',transpose), 'in_files')]),
                      (inputnode, merge_phsamples, [(('phsamples',transpose), 'in_files')]),
                      (inputnode, merge_fsamples, [(('fsamples',transpose), 'in_files')]),
                      (inputnode, merge_mean_dsamples, [('mean_dsamples', 'in_files')]),

                      (merge_thsamples, mean_thsamples, [('merged_file', 'in_file')]),
                      (merge_phsamples, mean_phsamples, [('merged_file', 'in_file')]),
                      (merge_fsamples, mean_fsamples, [('merged_file', 'in_file')]),
                      (merge_thsamples, make_dyads, [('merged_file', 'theta_vol')]),
                      (merge_phsamples, make_dyads, [('merged_file', 'phi_vol')]),
                      (inputnode, make_dyads, [('mask', 'mask')]),
                      ])

    inputnode = pe.Node(interface = util.IdentityInterface(fields=["dwi",
                                                                   "mask",
                                                                   "bvecs",
                                                                   "bvals"]),
                                                           name="inputnode")

    bedpostx = pe.Workflow(name=name)
    bedpostx.connect([(inputnode, preproc, [('mask', 'inputnode.mask')]),
                      (inputnode, preproc, [('dwi', 'inputnode.dwi')]),

                      (preproc, xfibres, [('slice_dwi.out_files', 'dwi'),
                                          ('slice_mask.out_files', 'mask')]),
                      (inputnode, xfibres, [('bvals', 'bvals')]),
                      (inputnode, xfibres, [('bvecs', 'bvecs')]),

                      (inputnode, postproc, [('mask', 'inputnode.mask')]),
                      (xfibres, postproc, [('thsamples','inputnode.thsamples'),
                                           ('phsamples', 'inputnode.phsamples'),
                                           ('fsamples', 'inputnode.fsamples'),
                                           ('dyads', 'inputnode.dyads'),
                                           ('mean_dsamples', 'inputnode.mean_dsamples')]),
                      ])

    outputnode = pe.Node(interface = util.IdentityInterface(fields=["thsamples",
                                                                    "phsamples",
                                                                    "fsamples",
                                                                    "mean_thsamples",
                                                                    "mean_phsamples",
                                                                    "mean_fsamples",
                                                                    "dyads",
                                                                    "dyads_dispersion"]),
                        name="outputnode")
    bedpostx.connect([(postproc, outputnode, [("merge_thsamples.merged_file", "thsamples"),
                                              ("merge_phsamples.merged_file", "phsamples"),
                                              ("merge_fsamples.merged_file", "fsamples"),
                                              ("mean_thsamples.out_file", "mean_thsamples"),
                                              ("mean_phsamples.out_file", "mean_phsamples"),
                                              ("mean_fsamples.out_file", "mean_fsamples"),
                                              ("make_dyads.dyads", "dyads"),
                                              ("make_dyads.dispersion", "dyads_dispersion")])
                      ])
    return bedpostx

def create_eddy_correct_pipeline(name="eddy_correct"):
    """Creates a pipeline that replaces eddy_correct script in FSL. It takes a
    series of diffusion weighted images and linearly corregisters them to one
    reference image.

    Example
    -------

    >>> nipype_eddycorrect = create_eddy_correct_pipeline("nipype_eddycorrect")
    >>> nipype_eddycorrect.inputs.inputnode.in_file = 'diffusion.nii'
    >>> nipype_eddycorrect.inputs.inputnode.ref_num = 0
    >>> nipype_eddycorrect.run() # doctest: +SKIP

    Inputs::

        inputnode.in_file
        inputnode.ref_num

    Outputs::

        outputnode.eddy_corrected
    """

    inputnode = pe.Node(interface = util.IdentityInterface(fields=["in_file", "ref_num"]),
                        name="inputnode")

    pipeline = pe.Workflow(name=name)

    split = pe.Node(fsl.Split(dimension='t'), name="split")
    pipeline.connect([(inputnode, split, [("in_file", "in_file")])])

    pick_ref = pe.Node(util.Select(), name="pick_ref")
    pipeline.connect([(split, pick_ref, [("out_files", "inlist")]),
                      (inputnode, pick_ref, [("ref_num", "index")])])

    coregistration = pe.MapNode(fsl.FLIRT(no_search=True, padding_size=1), name = "coregistration", iterfield=["in_file"])
    pipeline.connect([(split, coregistration, [("out_files", "in_file")]),
                      (pick_ref, coregistration, [("out", "reference")])])

    merge = pe.Node(fsl.Merge(dimension="t"), name="merge")
    pipeline.connect([(coregistration, merge, [("out_file", "in_files")])
                      ])

    outputnode = pe.Node(interface = util.IdentityInterface(fields=["eddy_corrected"]),
                        name="outputnode")

    pipeline.connect([(merge, outputnode, [("merged_file", "eddy_corrected")])])

    return pipeline