import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import numpy as np

def create_bedpostx_pipeline(name="bedpostx"):
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
    xfibres.inputs.update_proposals_every = 24
    
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
    
    def transpose(samples_over_fibres):
        a = np.array(samples_over_fibres)
        if len(a.shape)==1:
            a = a.reshape(-1,1)
        return a.T.tolist()
    
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
    return bedpostx