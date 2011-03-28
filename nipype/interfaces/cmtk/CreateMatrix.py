import numpy as np
import nibabel
import networkx as nx
import os, os.path as op

from nipype.interfaces.base import (TraitedSpec, BaseInterface, File)
from nipype.utils.filemanip import split_filename

def create_endpoints_array(fib, voxelSize):
    """ Create the endpoints arrays for each fiber
    Parameters
    ----------
    fib: the fibers data
    voxelSize: 3-tuple containing the voxel size of the ROI image
    Returns
    -------
    (endpoints: matrix of size [#fibers, 2, 3] containing for each fiber the
    index of its first and last point in the voxelSize volume
    endpointsmm) : endpoints in milimeter coordinates
    """

    
    # Init
    n = len(fib)
    endpoints = np.zeros( (n, 2, 3) )
    endpointsmm = np.zeros( (n, 2, 3) )
    pc = -1

    # Computation for each fiber
    for i, fi in enumerate(fib):
    
        # Percent counter
        pcN = int(round( float(100*i)/n ))
        if pcN > pc and pcN%1 == 0:
            pc = pcN

        f = fi[0]
    
        # store startpoint
        endpoints[i,0,:] = f[0,:]
        # store endpoint
        endpoints[i,1,:] = f[-1,:]
        
        # store startpoint
        endpointsmm[i,0,:] = f[0,:]
        # store endpoint
        endpointsmm[i,1,:] = f[-1,:]
        
        # Translate from mm to index
        endpoints[i,0,0] = int( endpoints[i,0,0] / float(voxelSize[0]))
        endpoints[i,0,1] = int( endpoints[i,0,1] / float(voxelSize[1]))
        endpoints[i,0,2] = int( endpoints[i,0,2] / float(voxelSize[2]))
        endpoints[i,1,0] = int( endpoints[i,1,0] / float(voxelSize[0]))
        endpoints[i,1,1] = int( endpoints[i,1,1] / float(voxelSize[1]))
        endpoints[i,1,2] = int( endpoints[i,1,2] / float(voxelSize[2]))
        
    # Return the matrices
    return (endpoints, endpointsmm)
    

def save_fibers(oldhdr, oldfib, fname, indices):
    """ Stores a new trackvis file fname using only given indices """

    hdrnew = oldhdr.copy()

    outstreams = []
    for i in indices:
        outstreams.append( oldfib[i] )

    n_fib_out = len(outstreams)
    hdrnew['n_count'] = n_fib_out

    nibabel.trackvis.write(fname, outstreams, hdrnew)

    
def cmat(track_file, roi_file):
    """ Create the connection matrix for each resolution using fibers and ROIs. """
              
    filename = os.path.abspath(track_file)
    # create the endpoints for each fibers
    en_fname = op.join(filename, 'endpoints.npy')
    en_fnamemm = op.join(filename, 'endpointsmm.npy')
    ep_fname = op.join(filename, 'lengths.npy')
    curv_fname = op.join(filename, 'meancurvature.npy')
    #intrk = op.join(gconf.get_cmp_fibers(), 'streamline_filtered.trk')
    intrk = track_file

    fib, hdr = nibabel.trackvis.read(intrk, False)
    
    # Previously, load_endpoints_from_trk() used the voxel size stored
    # in the track hdr to transform the endpoints to ROI voxel space.
    # This only works if the ROI voxel size is the same as the DSI/DTI
    # voxel size. In the case of DTI, it is not.
    # We do, however, assume that all of the ROI images have the same
    # voxel size, so this code just loads the first one to determine
    # what it should be
    firstROIFile = roi_file
    firstROI = nibabel.load(firstROIFile)
    roiVoxelSize = firstROI.get_header().get_zooms()
    (endpoints,endpointsmm) = create_endpoints_array(fib, roiVoxelSize)
    np.save(en_fname, endpoints)
    np.save(en_fnamemm, endpointsmm)

    # only compute curvature if required
    if gconf.compute_curvature:
        meancurv = compute_curvature_array(fib)
        np.save(curv_fname, meancurv)
    
    n = len(fib)
    
    resolution = gconf.parcellation.keys()

    for r in resolution:
        
        # create empty fiber label array
        fiberlabels = np.zeros( (n, 2) )
        final_fiberlabels = []
        final_fibers_idx = []
        
        # Open the corresponding ROI
        roi_fname = op.join(gconf.get_cmp_tracto_mask_tob0(), r, 'ROI_HR_th.nii.gz')
        roi = nibabel.load(roi_fname)
        roiData = roi.get_data()
      
        # Create the matrix
        nROIs = gconf.parcellation[r]['number_of_regions']
        G = nx.Graph()

        # add node information from parcellation
        gp = nx.read_graphml(gconf.parcellation[r]['node_information_graphml'])
        for u,d in gp.nodes_iter(data=True):
            G.add_node(int(u), d)

        dis = 0
        
        for i in range(endpoints.shape[0]):
    
            # ROI start => ROI end
            try:
                startROI = int(roiData[endpoints[i, 0, 0], endpoints[i, 0, 1], endpoints[i, 0, 2]])
                endROI = int(roiData[endpoints[i, 1, 0], endpoints[i, 1, 1], endpoints[i, 1, 2]])
            except IndexError:
                sys.stderr.write("AN INDEXERROR EXCEPTION OCCURED FOR FIBER %s. PLEASE CHECK ENDPOINT GENERATION" % i)
                continue
            
            # Filter
            if startROI == 0 or endROI == 0:
                dis += 1
                fiberlabels[i,0] = -1
                continue
            
            if startROI > nROIs or endROI > nROIs:
                sys.stderr.write("Start or endpoint of fiber terminate in a voxel which is labeled higher")
                sys.stderr.write("than is expected by the parcellation node information.")
                sys.stderr.write("Start ROI: %i, End ROI: %i" % (startROI, endROI))
                sys.stderr.write("This needs bugfixing!")
                continue
            
            # Update fiber label
            # switch the rois in order to enforce startROI < endROI
            if endROI < startROI:
                tmp = startROI
                startROI = endROI
                endROI = tmp

            fiberlabels[i,0] = startROI
            fiberlabels[i,1] = endROI

            final_fiberlabels.append( [ startROI, endROI ] )
            final_fibers_idx.append(i)


            # Add edge to graph
            if G.has_edge(startROI, endROI):
                G.edge[startROI][endROI]['fiblist'].append(i)
            else:
                G.add_edge(startROI, endROI, fiblist = [i])
                
        # create a final fiber length array
        finalfiberlength = []
        for idx in final_fibers_idx:
            # compute length of fiber
            finalfiberlength.append( length(fib[idx][0]) )

        # convert to array
        final_fiberlength_array = np.array( finalfiberlength )
        
        # make final fiber labels as array
        final_fiberlabels_array = np.array(final_fiberlabels, dtype = np.int32)

        # update edges
        # measures to add here
        for u,v,d in G.edges_iter(data=True):
            G.remove_edge(u,v)
            di = { 'number_of_fibers' : len(d['fiblist']), }
            
            # additional measures
            # compute mean/std of fiber measure
            idx = np.where( (final_fiberlabels_array[:,0] == int(u)) & (final_fiberlabels_array[:,1] == int(v)) )[0]

            di['fiber_length_mean'] = np.mean(final_fiberlength_array[idx])
            di['fiber_length_std'] = np.std(final_fiberlength_array[idx])

            G.add_edge(u,v, di)

        # storing network
        nx.write_gpickle(G, op.join(gconf.get_cmp_matrices(), 'connectome_%s.gpickle' % r))

        fiberlabels_fname = op.join(filename, 'final_fiberslength_%s.npy' % str(r))
        np.save(fiberlabels_fname, final_fiberlength_array)

        fiberlabels_fname = op.join(filename, 'filtered_fiberslabel_%s.npy' % str(r))
        np.save(fiberlabels_fname, np.array(fiberlabels, dtype = np.int32), )

        fiberlabels_noorphans_fname = op.join(filename, 'final_fiberlabels_%s.npy' % str(r))
        np.save(fiberlabels_noorphans_fname, final_fiberlabels_array)


        finalfibers_fname = op.join(filename, 'streamline_final_%s.trk' % str(r))
        save_fibers(hdr, fib, finalfibers_fname, final_fibers_idx)



class CreateMatrixInputSpec(TraitedSpec):

    track_file = File(desc='Filename of TrackVis file', exists=True, mandatory=True)

    roi_file = File(desc='Filename of ROI file', exists=True, mandatory=True)

    label_file = File(desc='Filename of file containing dictionary of labels', exists=True)

                      
class CreateMatrixOutputSpec(TraitedSpec):
    
    network_file = File(desc = 'File containing networkx graph')
    
    conmat_file = File(desc = 'Matlab .mat file containing the connectivity matrix')
    
    
class CreateMatrix(BaseInterface):

    input_spec = CreateMatrixInputSpec
    output_spec = CreateMatrixOutputSpec
    
    def _run_interface(self, runtime):
        """ Run the connection matrix module """
        cmat(self.inputs.track_file, self.inputs.roi_file)
        #vol = nibabel.load(self.inputs.roi_file).get_data()
        return runtime
    
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['network_file']=self._gen_outfilename('graph')
        outputs['conmat_file']=self._gen_outfilename('mat')
        return outputs
    
    def _gen_outfilename(self, ext):
        _, name , _ = split_filename(self.inputs.track_file)
        return name + "." + ext

