# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import pickle
import os.path as op

import numpy as np
import nibabel as nb
import networkx as nx

from ... import logging
from ...utils.filemanip import split_filename

from ..base import (
    BaseInterface,
    BaseInterfaceInputSpec,
    traits,
    File,
    TraitedSpec,
    Directory,
    OutputMultiPath,
    isdefined,
)

iflogger = logging.getLogger("nipype.interface")


def length(xyz, along=False):
    """
    Euclidean length of track line

    Parameters
    ----------
    xyz : array-like shape (N,3)
       array representing x,y,z of N points in a track
    along : bool, optional
       If True, return array giving cumulative length along track,
       otherwise (default) return scalar giving total length.

    Returns
    -------
    L : scalar or array shape (N-1,)
       scalar in case of `along` == False, giving total length, array if
       `along` == True, giving cumulative lengths.

    Examples
    --------
    >>> xyz = np.array([[1,1,1],[2,3,4],[0,0,0]])
    >>> expected_lens = np.sqrt([1+2**2+3**2, 2**2+3**2+4**2])
    >>> length(xyz) == expected_lens.sum()
    True
    >>> len_along = length(xyz, along=True)
    >>> np.allclose(len_along, expected_lens.cumsum())
    True
    >>> length([])
    0
    >>> length([[1, 2, 3]])
    0
    >>> length([], along=True)
    array([0])
    """
    xyz = np.asarray(xyz)
    if xyz.shape[0] < 2:
        if along:
            return np.array([0])
        return 0
    dists = np.sqrt((np.diff(xyz, axis=0) ** 2).sum(axis=1))
    if along:
        return np.cumsum(dists)
    return np.sum(dists)


def get_rois_crossed(pointsmm, roiData, voxelSize):
    n_points = len(pointsmm)
    rois_crossed = []
    for j in range(0, n_points):
        # store point
        x = int(pointsmm[j, 0] / float(voxelSize[0]))
        y = int(pointsmm[j, 1] / float(voxelSize[1]))
        z = int(pointsmm[j, 2] / float(voxelSize[2]))
        if not roiData[x, y, z] == 0:
            rois_crossed.append(roiData[x, y, z])
    rois_crossed = list(
        dict.fromkeys(rois_crossed).keys()
    )  # Removed duplicates from the list
    return rois_crossed


def get_connectivity_matrix(n_rois, list_of_roi_crossed_lists):
    connectivity_matrix = np.zeros((n_rois, n_rois), dtype=np.uint)
    for rois_crossed in list_of_roi_crossed_lists:
        for idx_i, roi_i in enumerate(rois_crossed):
            for idx_j, roi_j in enumerate(rois_crossed):
                if idx_i > idx_j:
                    if not roi_i == roi_j:
                        connectivity_matrix[roi_i - 1, roi_j - 1] += 1
    connectivity_matrix = connectivity_matrix + connectivity_matrix.T
    return connectivity_matrix


def create_allpoints_cmat(streamlines, roiData, voxelSize, n_rois):
    """ Create the intersection arrays for each fiber
    """
    n_fib = len(streamlines)
    pc = -1
    # Computation for each fiber
    final_fiber_ids = []
    list_of_roi_crossed_lists = []
    for i, fiber in enumerate(streamlines):
        pcN = int(round(float(100 * i) / n_fib))
        if pcN > pc and pcN % 1 == 0:
            pc = pcN
            print("%4.0f%%" % (pc))
        rois_crossed = get_rois_crossed(fiber[0], roiData, voxelSize)
        if len(rois_crossed) > 0:
            list_of_roi_crossed_lists.append(list(rois_crossed))
            final_fiber_ids.append(i)

    connectivity_matrix = get_connectivity_matrix(n_rois, list_of_roi_crossed_lists)
    dis = n_fib - len(final_fiber_ids)
    iflogger.info(
        "Found %i (%f percent out of %i fibers) fibers that start or "
        "terminate in a voxel which is not labeled. (orphans)",
        dis,
        dis * 100.0 / n_fib,
        n_fib,
    )
    iflogger.info(
        "Valid fibers: %i (%f percent)", n_fib - dis, 100 - dis * 100.0 / n_fib
    )
    iflogger.info("Returning the intersecting point connectivity matrix")
    return connectivity_matrix, final_fiber_ids


def create_endpoints_array(fib, voxelSize):
    """ Create the endpoints arrays for each fiber.

    Parameters
    ----------
    fib : array-like
      the fibers data
    voxelSize : tuple
      3-tuple containing the voxel size of the ROI image

    Returns
    -------
    endpoints : ndarray of size [#fibers, 2, 3]
      containing for each fiber the index of its first and last point in the voxelSize volume
    endpointsmm : ndarray of size [#fibers, 2, 3]
      endpoints in millimeter coordinates

    """
    # Init
    n = len(fib)
    endpoints = np.zeros((n, 2, 3))
    endpointsmm = np.zeros((n, 2, 3))

    # Computation for each fiber
    for i, fi in enumerate(fib):
        f = fi[0]

        # store startpoint
        endpoints[i, 0, :] = f[0, :]
        # store endpoint
        endpoints[i, 1, :] = f[-1, :]

        # store startpoint
        endpointsmm[i, 0, :] = f[0, :]
        # store endpoint
        endpointsmm[i, 1, :] = f[-1, :]

        # Translate from mm to index
        endpoints[i, 0, 0] = int(endpoints[i, 0, 0] / float(voxelSize[0]))
        endpoints[i, 0, 1] = int(endpoints[i, 0, 1] / float(voxelSize[1]))
        endpoints[i, 0, 2] = int(endpoints[i, 0, 2] / float(voxelSize[2]))
        endpoints[i, 1, 0] = int(endpoints[i, 1, 0] / float(voxelSize[0]))
        endpoints[i, 1, 1] = int(endpoints[i, 1, 1] / float(voxelSize[1]))
        endpoints[i, 1, 2] = int(endpoints[i, 1, 2] / float(voxelSize[2]))

    # Return the matrices
    iflogger.info("Returning the endpoint matrix")
    return (endpoints, endpointsmm)


def cmat(
    track_file,
    roi_file,
    resolution_network_file,
    matrix_name,
    matrix_mat_name,
    endpoint_name,
    intersections=False,
):
    """ Create the connection matrix for each resolution using fibers and ROIs. """
    import scipy.io as sio

    stats = {}
    iflogger.info("Running cmat function")
    # Identify the endpoints of each fiber
    en_fname = op.abspath(endpoint_name + "_endpoints.npy")
    en_fnamemm = op.abspath(endpoint_name + "_endpointsmm.npy")

    iflogger.info("Reading Trackvis file %s", track_file)
    fib, hdr = nb.trackvis.read(track_file, False)
    stats["orig_n_fib"] = len(fib)

    roi = nb.load(roi_file)
    # Preserve on-disk type unless scaled
    roiData = np.asanyarray(roi.dataobj)
    roiVoxelSize = roi.header.get_zooms()
    (endpoints, endpointsmm) = create_endpoints_array(fib, roiVoxelSize)

    # Output endpoint arrays
    iflogger.info("Saving endpoint array: %s", en_fname)
    np.save(en_fname, endpoints)
    iflogger.info("Saving endpoint array in mm: %s", en_fnamemm)
    np.save(en_fnamemm, endpointsmm)

    n = len(fib)
    iflogger.info("Number of fibers: %i", n)

    # Create empty fiber label array
    fiberlabels = np.zeros((n, 2))
    final_fiberlabels = []
    final_fibers_idx = []

    # Add node information from specified parcellation scheme
    path, name, ext = split_filename(resolution_network_file)
    if ext == ".pck":
        gp = nx.read_gpickle(resolution_network_file)
    elif ext == ".graphml":
        gp = nx.read_graphml(resolution_network_file)
    else:
        raise TypeError("Unable to read file:", resolution_network_file)
    nROIs = len(gp.nodes())

    # add node information from parcellation
    if "dn_position" in gp.nodes[list(gp.nodes())[0]]:
        G = gp.copy()
    else:
        G = nx.Graph()
        for u, d in gp.nodes(data=True):
            G.add_node(int(u), **d)
            # compute a position for the node based on the mean position of the
            # ROI in voxel coordinates (segmentation volume )
            xyz = tuple(
                np.mean(
                    np.where(np.flipud(roiData) == int(d["dn_correspondence_id"])),
                    axis=1,
                )
            )
            G.nodes[int(u)]["dn_position"] = tuple([xyz[0], xyz[2], -xyz[1]])

    if intersections:
        iflogger.info("Filtering tractography from intersections")
        intersection_matrix, final_fiber_ids = create_allpoints_cmat(
            fib, roiData, roiVoxelSize, nROIs
        )
        finalfibers_fname = op.abspath(
            endpoint_name + "_intersections_streamline_final.trk"
        )
        stats["intersections_n_fib"] = save_fibers(
            hdr, fib, finalfibers_fname, final_fiber_ids
        )
        intersection_matrix = np.matrix(intersection_matrix)
        I = G.copy()
        H = nx.from_numpy_matrix(np.matrix(intersection_matrix))
        H = nx.relabel_nodes(H, lambda x: x + 1)  # relabel nodes so they start at 1
        I.add_weighted_edges_from(
            ((u, v, d["weight"]) for u, v, d in H.edges(data=True))
        )

    dis = 0
    for i in range(endpoints.shape[0]):

        # ROI start => ROI end
        try:
            startROI = int(
                roiData[endpoints[i, 0, 0], endpoints[i, 0, 1], endpoints[i, 0, 2]]
            )
            endROI = int(
                roiData[endpoints[i, 1, 0], endpoints[i, 1, 1], endpoints[i, 1, 2]]
            )
        except IndexError:
            iflogger.error(
                "AN INDEXERROR EXCEPTION OCCURED FOR FIBER %s. "
                "PLEASE CHECK ENDPOINT GENERATION",
                i,
            )
            break

        # Filter
        if startROI == 0 or endROI == 0:
            dis += 1
            fiberlabels[i, 0] = -1
            continue

        if startROI > nROIs or endROI > nROIs:
            iflogger.error(
                "Start or endpoint of fiber terminate in a voxel which is labeled higher"
            )
            iflogger.error("than is expected by the parcellation node information.")
            iflogger.error("Start ROI: %i, End ROI: %i", startROI, endROI)
            iflogger.error("This needs bugfixing!")
            continue

        # Update fiber label
        # switch the rois in order to enforce startROI < endROI
        if endROI < startROI:
            tmp = startROI
            startROI = endROI
            endROI = tmp

        fiberlabels[i, 0] = startROI
        fiberlabels[i, 1] = endROI

        final_fiberlabels.append([startROI, endROI])
        final_fibers_idx.append(i)

        # Add edge to graph
        if G.has_edge(startROI, endROI) and "fiblist" in G.edge[startROI][endROI]:
            G.edge[startROI][endROI]["fiblist"].append(i)
        else:
            G.add_edge(startROI, endROI, fiblist=[i])

    # create a final fiber length array
    finalfiberlength = []
    if intersections:
        final_fibers_indices = final_fiber_ids
    else:
        final_fibers_indices = final_fibers_idx

    for idx in final_fibers_indices:
        # compute length of fiber
        finalfiberlength.append(length(fib[idx][0]))

    # convert to array
    final_fiberlength_array = np.array(finalfiberlength)

    # make final fiber labels as array
    final_fiberlabels_array = np.array(final_fiberlabels, dtype=int)

    iflogger.info(
        "Found %i (%f percent out of %i fibers) fibers that start or "
        "terminate in a voxel which is not labeled. (orphans)",
        dis,
        dis * 100.0 / n,
        n,
    )
    iflogger.info("Valid fibers: %i (%f%%)", n - dis, 100 - dis * 100.0 / n)

    numfib = nx.Graph()
    numfib.add_nodes_from(G)
    fibmean = numfib.copy()
    fibmedian = numfib.copy()
    fibdev = numfib.copy()
    for u, v, d in G.edges(data=True):
        G.remove_edge(u, v)
        di = {}
        if "fiblist" in d:
            di["number_of_fibers"] = len(d["fiblist"])
            idx = np.where(
                (final_fiberlabels_array[:, 0] == int(u))
                & (final_fiberlabels_array[:, 1] == int(v))
            )[0]
            di["fiber_length_mean"] = float(np.mean(final_fiberlength_array[idx]))
            di["fiber_length_median"] = float(np.median(final_fiberlength_array[idx]))
            di["fiber_length_std"] = float(np.std(final_fiberlength_array[idx]))
        else:
            di["number_of_fibers"] = 0
            di["fiber_length_mean"] = 0
            di["fiber_length_median"] = 0
            di["fiber_length_std"] = 0
        if not u == v:  # Fix for self loop problem
            G.add_edge(u, v, **di)
            if "fiblist" in d:
                numfib.add_edge(u, v, weight=di["number_of_fibers"])
                fibmean.add_edge(u, v, weight=di["fiber_length_mean"])
                fibmedian.add_edge(u, v, weight=di["fiber_length_median"])
                fibdev.add_edge(u, v, weight=di["fiber_length_std"])

    iflogger.info("Writing network as %s", matrix_name)
    nx.write_gpickle(G, op.abspath(matrix_name))

    numfib_mlab = nx.to_numpy_matrix(numfib, dtype=int)
    numfib_dict = {"number_of_fibers": numfib_mlab}
    fibmean_mlab = nx.to_numpy_matrix(fibmean, dtype=np.float64)
    fibmean_dict = {"mean_fiber_length": fibmean_mlab}
    fibmedian_mlab = nx.to_numpy_matrix(fibmedian, dtype=np.float64)
    fibmedian_dict = {"median_fiber_length": fibmedian_mlab}
    fibdev_mlab = nx.to_numpy_matrix(fibdev, dtype=np.float64)
    fibdev_dict = {"fiber_length_std": fibdev_mlab}

    if intersections:
        path, name, ext = split_filename(matrix_name)
        intersection_matrix_name = op.abspath(name + "_intersections") + ext
        iflogger.info("Writing intersection network as %s", intersection_matrix_name)
        nx.write_gpickle(I, intersection_matrix_name)

    path, name, ext = split_filename(matrix_mat_name)
    if not ext == ".mat":
        ext = ".mat"
        matrix_mat_name = matrix_mat_name + ext

    iflogger.info("Writing matlab matrix as %s", matrix_mat_name)
    sio.savemat(matrix_mat_name, numfib_dict)

    if intersections:
        intersect_dict = {"intersections": intersection_matrix}
        intersection_matrix_mat_name = op.abspath(name + "_intersections") + ext
        iflogger.info("Writing intersection matrix as %s", intersection_matrix_mat_name)
        sio.savemat(intersection_matrix_mat_name, intersect_dict)

    mean_fiber_length_matrix_name = op.abspath(name + "_mean_fiber_length") + ext
    iflogger.info(
        "Writing matlab mean fiber length matrix as %s", mean_fiber_length_matrix_name
    )
    sio.savemat(mean_fiber_length_matrix_name, fibmean_dict)

    median_fiber_length_matrix_name = op.abspath(name + "_median_fiber_length") + ext
    iflogger.info(
        "Writing matlab median fiber length matrix as %s",
        median_fiber_length_matrix_name,
    )
    sio.savemat(median_fiber_length_matrix_name, fibmedian_dict)

    fiber_length_std_matrix_name = op.abspath(name + "_fiber_length_std") + ext
    iflogger.info(
        "Writing matlab fiber length deviation matrix as %s",
        fiber_length_std_matrix_name,
    )
    sio.savemat(fiber_length_std_matrix_name, fibdev_dict)

    fiberlengths_fname = op.abspath(endpoint_name + "_final_fiberslength.npy")
    iflogger.info("Storing final fiber length array as %s", fiberlengths_fname)
    np.save(fiberlengths_fname, final_fiberlength_array)

    fiberlabels_fname = op.abspath(endpoint_name + "_filtered_fiberslabel.npy")
    iflogger.info("Storing all fiber labels (with orphans) as %s", fiberlabels_fname)
    np.save(fiberlabels_fname, np.array(fiberlabels, dtype=np.int32))

    fiberlabels_noorphans_fname = op.abspath(endpoint_name + "_final_fiberslabels.npy")
    iflogger.info(
        "Storing final fiber labels (no orphans) as %s", fiberlabels_noorphans_fname
    )
    np.save(fiberlabels_noorphans_fname, final_fiberlabels_array)

    iflogger.info("Filtering tractography - keeping only no orphan fibers")
    finalfibers_fname = op.abspath(endpoint_name + "_streamline_final.trk")
    stats["endpoint_n_fib"] = save_fibers(hdr, fib, finalfibers_fname, final_fibers_idx)
    stats["endpoints_percent"] = (
        float(stats["endpoint_n_fib"]) / float(stats["orig_n_fib"]) * 100
    )
    stats["intersections_percent"] = (
        float(stats["intersections_n_fib"]) / float(stats["orig_n_fib"]) * 100
    )

    out_stats_file = op.abspath(endpoint_name + "_statistics.mat")
    iflogger.info("Saving matrix creation statistics as %s", out_stats_file)
    sio.savemat(out_stats_file, stats)


def save_fibers(oldhdr, oldfib, fname, indices):
    """ Stores a new trackvis file fname using only given indices """
    hdrnew = oldhdr.copy()
    outstreams = []
    for i in indices:
        outstreams.append(oldfib[i])
    n_fib_out = len(outstreams)
    hdrnew["n_count"] = n_fib_out
    iflogger.info("Writing final non-orphan fibers as %s", fname)
    nb.trackvis.write(fname, outstreams, hdrnew)
    return n_fib_out


class CreateMatrixInputSpec(TraitedSpec):
    roi_file = File(exists=True, mandatory=True, desc="Freesurfer aparc+aseg file")
    tract_file = File(exists=True, mandatory=True, desc="Trackvis tract file")
    resolution_network_file = File(
        exists=True,
        mandatory=True,
        desc="Parcellation files from Connectome Mapping Toolkit",
    )
    count_region_intersections = traits.Bool(
        False,
        usedefault=True,
        desc="Counts all of the fiber-region traversals in the connectivity matrix (requires significantly more computational time)",
    )
    out_matrix_file = File(
        genfile=True, desc="NetworkX graph describing the connectivity"
    )
    out_matrix_mat_file = File(
        "cmatrix.mat", usedefault=True, desc="Matlab matrix describing the connectivity"
    )
    out_mean_fiber_length_matrix_mat_file = File(
        genfile=True,
        desc="Matlab matrix describing the mean fiber lengths between each node.",
    )
    out_median_fiber_length_matrix_mat_file = File(
        genfile=True,
        desc="Matlab matrix describing the mean fiber lengths between each node.",
    )
    out_fiber_length_std_matrix_mat_file = File(
        genfile=True,
        desc="Matlab matrix describing the deviation in fiber lengths connecting each node.",
    )
    out_intersection_matrix_mat_file = File(
        genfile=True,
        desc="Matlab connectivity matrix if all region/fiber intersections are counted.",
    )
    out_endpoint_array_name = File(
        genfile=True, desc="Name for the generated endpoint arrays"
    )


class CreateMatrixOutputSpec(TraitedSpec):
    matrix_file = File(desc="NetworkX graph describing the connectivity", exists=True)
    intersection_matrix_file = File(
        desc="NetworkX graph describing the connectivity", exists=True
    )
    matrix_files = OutputMultiPath(
        File(
            desc="All of the gpickled network files output by this interface",
            exists=True,
        )
    )
    matlab_matrix_files = OutputMultiPath(
        File(desc="All of the MATLAB .mat files output by this interface", exists=True)
    )
    matrix_mat_file = File(
        desc="Matlab matrix describing the connectivity", exists=True
    )
    intersection_matrix_mat_file = File(
        desc="Matlab matrix describing the mean fiber lengths between each node.",
        exists=True,
    )
    mean_fiber_length_matrix_mat_file = File(
        desc="Matlab matrix describing the mean fiber lengths between each node.",
        exists=True,
    )
    median_fiber_length_matrix_mat_file = File(
        desc="Matlab matrix describing the median fiber lengths between each node.",
        exists=True,
    )
    fiber_length_std_matrix_mat_file = File(
        desc="Matlab matrix describing the deviation in fiber lengths connecting each node.",
        exists=True,
    )
    endpoint_file = File(
        desc="Saved Numpy array with the endpoints of each fiber", exists=True
    )
    endpoint_file_mm = File(
        desc="Saved Numpy array with the endpoints of each fiber (in millimeters)",
        exists=True,
    )
    fiber_length_file = File(
        desc="Saved Numpy array with the lengths of each fiber", exists=True
    )
    fiber_label_file = File(
        desc="Saved Numpy array with the labels for each fiber", exists=True
    )
    fiber_labels_noorphans = File(
        desc="Saved Numpy array with the labels for each non-orphan fiber", exists=True
    )
    filtered_tractography = File(
        desc="TrackVis file containing only those fibers originate in one and terminate in another region",
        exists=True,
    )
    filtered_tractography_by_intersections = File(
        desc="TrackVis file containing all fibers which connect two regions",
        exists=True,
    )
    filtered_tractographies = OutputMultiPath(
        File(
            desc="TrackVis file containing only those fibers originate in one and terminate in another region",
            exists=True,
        )
    )
    stats_file = File(
        desc="Saved Matlab .mat file with the number of fibers saved at each stage",
        exists=True,
    )


class CreateMatrix(BaseInterface):
    """
    Performs connectivity mapping and outputs the result as a NetworkX graph and a Matlab matrix

    Example
    -------

    >>> import nipype.interfaces.cmtk as cmtk
    >>> conmap = cmtk.CreateMatrix()
    >>> conmap.roi_file = 'fsLUT_aparc+aseg.nii'
    >>> conmap.tract_file = 'fibers.trk'
    >>> conmap.run()                 # doctest: +SKIP
    """

    input_spec = CreateMatrixInputSpec
    output_spec = CreateMatrixOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.out_matrix_file):
            path, name, _ = split_filename(self.inputs.out_matrix_file)
            matrix_file = op.abspath(name + ".pck")
        else:
            matrix_file = self._gen_outfilename(".pck")

        matrix_mat_file = op.abspath(self.inputs.out_matrix_mat_file)
        path, name, ext = split_filename(matrix_mat_file)
        if not ext == ".mat":
            ext = ".mat"
            matrix_mat_file = matrix_mat_file + ext

        if isdefined(self.inputs.out_mean_fiber_length_matrix_mat_file):
            mean_fiber_length_matrix_mat_file = op.abspath(
                self.inputs.out_mean_fiber_length_matrix_mat_file
            )
        else:
            mean_fiber_length_matrix_name = op.abspath(
                self._gen_outfilename("_mean_fiber_length.mat")
            )

        if isdefined(self.inputs.out_median_fiber_length_matrix_mat_file):
            median_fiber_length_matrix_mat_file = op.abspath(
                self.inputs.out_median_fiber_length_matrix_mat_file
            )
        else:
            median_fiber_length_matrix_name = op.abspath(
                self._gen_outfilename("_median_fiber_length.mat")
            )

        if isdefined(self.inputs.out_fiber_length_std_matrix_mat_file):
            fiber_length_std_matrix_mat_file = op.abspath(
                self.inputs.out_fiber_length_std_matrix_mat_file
            )
        else:
            fiber_length_std_matrix_name = op.abspath(
                self._gen_outfilename("_fiber_length_std.mat")
            )

        if not isdefined(self.inputs.out_endpoint_array_name):
            _, endpoint_name, _ = split_filename(self.inputs.tract_file)
            endpoint_name = op.abspath(endpoint_name)
        else:
            endpoint_name = op.abspath(self.inputs.out_endpoint_array_name)

        cmat(
            self.inputs.tract_file,
            self.inputs.roi_file,
            self.inputs.resolution_network_file,
            matrix_file,
            matrix_mat_file,
            endpoint_name,
            self.inputs.count_region_intersections,
        )
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_matrix_file):
            path, name, _ = split_filename(self.inputs.out_matrix_file)
            out_matrix_file = op.abspath(name + ".pck")
            out_intersection_matrix_file = op.abspath(name + "_intersections.pck")
        else:
            out_matrix_file = op.abspath(self._gen_outfilename(".pck"))
            out_intersection_matrix_file = op.abspath(
                self._gen_outfilename("_intersections.pck")
            )

        outputs["matrix_file"] = out_matrix_file
        outputs["intersection_matrix_file"] = out_intersection_matrix_file

        matrix_mat_file = op.abspath(self.inputs.out_matrix_mat_file)
        path, name, ext = split_filename(matrix_mat_file)
        if not ext == ".mat":
            ext = ".mat"
            matrix_mat_file = matrix_mat_file + ext

        outputs["matrix_mat_file"] = matrix_mat_file
        if isdefined(self.inputs.out_mean_fiber_length_matrix_mat_file):
            outputs["mean_fiber_length_matrix_mat_file"] = op.abspath(
                self.inputs.out_mean_fiber_length_matrix_mat_file
            )
        else:
            outputs["mean_fiber_length_matrix_mat_file"] = op.abspath(
                self._gen_outfilename("_mean_fiber_length.mat")
            )

        if isdefined(self.inputs.out_median_fiber_length_matrix_mat_file):
            outputs["median_fiber_length_matrix_mat_file"] = op.abspath(
                self.inputs.out_median_fiber_length_matrix_mat_file
            )
        else:
            outputs["median_fiber_length_matrix_mat_file"] = op.abspath(
                self._gen_outfilename("_median_fiber_length.mat")
            )

        if isdefined(self.inputs.out_fiber_length_std_matrix_mat_file):
            outputs["fiber_length_std_matrix_mat_file"] = op.abspath(
                self.inputs.out_fiber_length_std_matrix_mat_file
            )
        else:
            outputs["fiber_length_std_matrix_mat_file"] = op.abspath(
                self._gen_outfilename("_fiber_length_std.mat")
            )

        if isdefined(self.inputs.out_intersection_matrix_mat_file):
            outputs["intersection_matrix_mat_file"] = op.abspath(
                self.inputs.out_intersection_matrix_mat_file
            )
        else:
            outputs["intersection_matrix_mat_file"] = op.abspath(
                self._gen_outfilename("_intersections.mat")
            )

        if isdefined(self.inputs.out_endpoint_array_name):
            endpoint_name = self.inputs.out_endpoint_array_name
            outputs["endpoint_file"] = op.abspath(
                self.inputs.out_endpoint_array_name + "_endpoints.npy"
            )
            outputs["endpoint_file_mm"] = op.abspath(
                self.inputs.out_endpoint_array_name + "_endpointsmm.npy"
            )
            outputs["fiber_length_file"] = op.abspath(
                self.inputs.out_endpoint_array_name + "_final_fiberslength.npy"
            )
            outputs["fiber_label_file"] = op.abspath(
                self.inputs.out_endpoint_array_name + "_filtered_fiberslabel.npy"
            )
            outputs["fiber_labels_noorphans"] = op.abspath(
                self.inputs.out_endpoint_array_name + "_final_fiberslabels.npy"
            )
        else:
            _, endpoint_name, _ = split_filename(self.inputs.tract_file)
            outputs["endpoint_file"] = op.abspath(endpoint_name + "_endpoints.npy")
            outputs["endpoint_file_mm"] = op.abspath(endpoint_name + "_endpointsmm.npy")
            outputs["fiber_length_file"] = op.abspath(
                endpoint_name + "_final_fiberslength.npy"
            )
            outputs["fiber_label_file"] = op.abspath(
                endpoint_name + "_filtered_fiberslabel.npy"
            )
            outputs["fiber_labels_noorphans"] = op.abspath(
                endpoint_name + "_final_fiberslabels.npy"
            )

        if self.inputs.count_region_intersections:
            outputs["matrix_files"] = [out_matrix_file, out_intersection_matrix_file]
            outputs["matlab_matrix_files"] = [
                outputs["matrix_mat_file"],
                outputs["mean_fiber_length_matrix_mat_file"],
                outputs["median_fiber_length_matrix_mat_file"],
                outputs["fiber_length_std_matrix_mat_file"],
                outputs["intersection_matrix_mat_file"],
            ]
        else:
            outputs["matrix_files"] = [out_matrix_file]
            outputs["matlab_matrix_files"] = [
                outputs["matrix_mat_file"],
                outputs["mean_fiber_length_matrix_mat_file"],
                outputs["median_fiber_length_matrix_mat_file"],
                outputs["fiber_length_std_matrix_mat_file"],
            ]

        outputs["filtered_tractography"] = op.abspath(
            endpoint_name + "_streamline_final.trk"
        )
        outputs["filtered_tractography_by_intersections"] = op.abspath(
            endpoint_name + "_intersections_streamline_final.trk"
        )
        outputs["filtered_tractographies"] = [
            outputs["filtered_tractography"],
            outputs["filtered_tractography_by_intersections"],
        ]
        outputs["stats_file"] = op.abspath(endpoint_name + "_statistics.mat")
        return outputs

    def _gen_outfilename(self, ext):
        if ext.endswith("mat") and isdefined(self.inputs.out_matrix_mat_file):
            _, name, _ = split_filename(self.inputs.out_matrix_mat_file)
        elif isdefined(self.inputs.out_matrix_file):
            _, name, _ = split_filename(self.inputs.out_matrix_file)
        else:
            _, name, _ = split_filename(self.inputs.tract_file)
        return name + ext


class ROIGenInputSpec(BaseInterfaceInputSpec):
    aparc_aseg_file = File(
        exists=True, mandatory=True, desc="Freesurfer aparc+aseg file"
    )
    LUT_file = File(
        exists=True,
        xor=["use_freesurfer_LUT"],
        desc="Custom lookup table (cf. FreeSurferColorLUT.txt)",
    )
    use_freesurfer_LUT = traits.Bool(
        xor=["LUT_file"],
        desc="Boolean value; Set to True to use default Freesurfer LUT, False for custom LUT",
    )
    freesurfer_dir = Directory(
        requires=["use_freesurfer_LUT"], desc="Freesurfer main directory"
    )
    out_roi_file = File(
        genfile=True, desc="Region of Interest file for connectivity mapping"
    )
    out_dict_file = File(genfile=True, desc="Label dictionary saved in Pickle format")


class ROIGenOutputSpec(TraitedSpec):
    roi_file = File(desc="Region of Interest file for connectivity mapping")
    dict_file = File(desc="Label dictionary saved in Pickle format")


class ROIGen(BaseInterface):
    """
    Generates a ROI file for connectivity mapping and a dictionary file containing relevant node information

    Example
    -------

    >>> import nipype.interfaces.cmtk as cmtk
    >>> rg = cmtk.ROIGen()
    >>> rg.inputs.aparc_aseg_file = 'aparc+aseg.nii'
    >>> rg.inputs.use_freesurfer_LUT = True
    >>> rg.inputs.freesurfer_dir = '/usr/local/freesurfer'
    >>> rg.run() # doctest: +SKIP

    The label dictionary is written to disk using Pickle. Resulting data can be loaded using:

    >>> file = open("FreeSurferColorLUT_adapted_aparc+aseg_out.pck", "r")
    >>> file = open("fsLUT_aparc+aseg.pck", "r")
    >>> labelDict = pickle.load(file) # doctest: +SKIP
    >>> labelDict                     # doctest: +SKIP
    """

    input_spec = ROIGenInputSpec
    output_spec = ROIGenOutputSpec

    def _run_interface(self, runtime):
        aparc_aseg_file = self.inputs.aparc_aseg_file
        aparcpath, aparcname, aparcext = split_filename(aparc_aseg_file)
        iflogger.info("Using Aparc+Aseg file: %s", aparcname + aparcext)
        niiAPARCimg = nb.load(aparc_aseg_file)
        # Preserve on-disk type
        niiAPARCdata = np.asanyarray(niiAPARCimg.dataobj)
        niiDataLabels = np.unique(niiAPARCdata)
        numDataLabels = np.size(niiDataLabels)
        iflogger.info("Number of labels in image: %s", numDataLabels)

        write_dict = True
        if self.inputs.use_freesurfer_LUT:
            self.LUT_file = self.inputs.freesurfer_dir + "/FreeSurferColorLUT.txt"
            iflogger.info("Using Freesurfer LUT: %s", self.LUT_file)
            prefix = "fsLUT"
        elif not self.inputs.use_freesurfer_LUT and isdefined(self.inputs.LUT_file):
            self.LUT_file = op.abspath(self.inputs.LUT_file)
            lutpath, lutname, lutext = split_filename(self.LUT_file)
            iflogger.info("Using Custom LUT file: %s", lutname + lutext)
            prefix = lutname
        else:
            prefix = "hardcoded"
            write_dict = False

        if isdefined(self.inputs.out_roi_file):
            roi_file = op.abspath(self.inputs.out_roi_file)
        else:
            roi_file = op.abspath(prefix + "_" + aparcname + ".nii")

        if isdefined(self.inputs.out_dict_file):
            dict_file = op.abspath(self.inputs.out_dict_file)
        else:
            dict_file = op.abspath(prefix + "_" + aparcname + ".pck")

        if write_dict:
            iflogger.info("Lookup table: %s", op.abspath(self.LUT_file))
            LUTlabelsRGBA = np.loadtxt(
                self.LUT_file,
                skiprows=4,
                usecols=[0, 1, 2, 3, 4, 5],
                comments="#",
                dtype={
                    "names": ("index", "label", "R", "G", "B", "A"),
                    "formats": ("int", "|S30", "int", "int", "int", "int"),
                },
            )
            numLUTLabels = np.size(LUTlabelsRGBA)
            if numLUTLabels < numDataLabels:
                iflogger.error(
                    "LUT file provided does not contain all of the regions in the image"
                )
                iflogger.error("Removing unmapped regions")
            iflogger.info("Number of labels in LUT: %s", numLUTLabels)
            LUTlabelDict = {}
            """ Create dictionary for input LUT table"""
            for labels in range(0, numLUTLabels):
                LUTlabelDict[LUTlabelsRGBA[labels][0]] = [
                    LUTlabelsRGBA[labels][1],
                    LUTlabelsRGBA[labels][2],
                    LUTlabelsRGBA[labels][3],
                    LUTlabelsRGBA[labels][4],
                    LUTlabelsRGBA[labels][5],
                ]

            iflogger.info("Printing LUT label dictionary")
            iflogger.info(LUTlabelDict)

        mapDict = {}
        MAPPING = [
            [1, 2012],
            [2, 2019],
            [3, 2032],
            [4, 2014],
            [5, 2020],
            [6, 2018],
            [7, 2027],
            [8, 2028],
            [9, 2003],
            [10, 2024],
            [11, 2017],
            [12, 2026],
            [13, 2002],
            [14, 2023],
            [15, 2010],
            [16, 2022],
            [17, 2031],
            [18, 2029],
            [19, 2008],
            [20, 2025],
            [21, 2005],
            [22, 2021],
            [23, 2011],
            [24, 2013],
            [25, 2007],
            [26, 2016],
            [27, 2006],
            [28, 2033],
            [29, 2009],
            [30, 2015],
            [31, 2001],
            [32, 2030],
            [33, 2034],
            [34, 2035],
            [35, 49],
            [36, 50],
            [37, 51],
            [38, 52],
            [39, 58],
            [40, 53],
            [41, 54],
            [42, 1012],
            [43, 1019],
            [44, 1032],
            [45, 1014],
            [46, 1020],
            [47, 1018],
            [48, 1027],
            [49, 1028],
            [50, 1003],
            [51, 1024],
            [52, 1017],
            [53, 1026],
            [54, 1002],
            [55, 1023],
            [56, 1010],
            [57, 1022],
            [58, 1031],
            [59, 1029],
            [60, 1008],
            [61, 1025],
            [62, 1005],
            [63, 1021],
            [64, 1011],
            [65, 1013],
            [66, 1007],
            [67, 1016],
            [68, 1006],
            [69, 1033],
            [70, 1009],
            [71, 1015],
            [72, 1001],
            [73, 1030],
            [74, 1034],
            [75, 1035],
            [76, 10],
            [77, 11],
            [78, 12],
            [79, 13],
            [80, 26],
            [81, 17],
            [82, 18],
            [83, 16],
        ]
        """ Create empty grey matter mask, Populate with only those regions defined in the mapping."""
        niiGM = np.zeros(niiAPARCdata.shape, dtype=np.uint)
        for ma in MAPPING:
            niiGM[niiAPARCdata == ma[1]] = ma[0]
            mapDict[ma[0]] = ma[1]
        iflogger.info("Grey matter mask created")
        greyMaskLabels = np.unique(niiGM)
        numGMLabels = np.size(greyMaskLabels)
        iflogger.info("Number of grey matter labels: %s", numGMLabels)

        labelDict = {}
        GMlabelDict = {}
        for label in greyMaskLabels:
            try:
                mapDict[label]
                if write_dict:
                    GMlabelDict["originalID"] = mapDict[label]
            except:
                iflogger.info("Label %s not in provided mapping", label)
            if write_dict:
                del GMlabelDict
                GMlabelDict = {}
                GMlabelDict["labels"] = LUTlabelDict[label][0]
                GMlabelDict["colors"] = [
                    LUTlabelDict[label][1],
                    LUTlabelDict[label][2],
                    LUTlabelDict[label][3],
                ]
                GMlabelDict["a"] = LUTlabelDict[label][4]
                labelDict[label] = GMlabelDict

        roi_image = nb.Nifti1Image(niiGM, niiAPARCimg.affine, niiAPARCimg.header)
        iflogger.info("Saving ROI File to %s", roi_file)
        nb.save(roi_image, roi_file)

        if write_dict:
            iflogger.info("Saving Dictionary File to %s in Pickle format", dict_file)
            with open(dict_file, "w") as f:
                pickle.dump(labelDict, f)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.out_roi_file):
            outputs["roi_file"] = op.abspath(self.inputs.out_roi_file)
        else:
            outputs["roi_file"] = op.abspath(self._gen_outfilename("nii"))
        if isdefined(self.inputs.out_dict_file):
            outputs["dict_file"] = op.abspath(self.inputs.out_dict_file)
        else:
            outputs["dict_file"] = op.abspath(self._gen_outfilename("pck"))
        return outputs

    def _gen_outfilename(self, ext):
        _, name, _ = split_filename(self.inputs.aparc_aseg_file)
        if self.inputs.use_freesurfer_LUT:
            prefix = "fsLUT"
        elif not self.inputs.use_freesurfer_LUT and isdefined(self.inputs.LUT_file):
            lutpath, lutname, lutext = split_filename(self.inputs.LUT_file)
            prefix = lutname
        else:
            prefix = "hardcoded"
        return prefix + "_" + name + "." + ext


def create_nodes(roi_file, resolution_network_file, out_filename):
    G = nx.Graph()
    gp = nx.read_graphml(resolution_network_file)
    roi_image = nb.load(roi_file)
    # Preserve on-disk type unless scaled
    roiData = np.asanyarray(roi_image.dataobj)
    for u, d in gp.nodes(data=True):
        G.add_node(int(u), **d)
        xyz = tuple(
            np.mean(
                np.where(np.flipud(roiData) == int(d["dn_correspondence_id"])), axis=1
            )
        )
        G.nodes[int(u)]["dn_position"] = tuple([xyz[0], xyz[2], -xyz[1]])
    nx.write_gpickle(G, out_filename)
    return out_filename


class CreateNodesInputSpec(BaseInterfaceInputSpec):
    roi_file = File(exists=True, mandatory=True, desc="Region of interest file")
    resolution_network_file = File(
        exists=True,
        mandatory=True,
        desc="Parcellation file from Connectome Mapping Toolkit",
    )
    out_filename = File(
        "nodenetwork.pck",
        usedefault=True,
        desc="Output gpickled network with the nodes defined.",
    )


class CreateNodesOutputSpec(TraitedSpec):
    node_network = File(desc="Output gpickled network with the nodes defined.")


class CreateNodes(BaseInterface):
    """
    Generates a NetworkX graph containing nodes at the centroid of each region in the input ROI file.
    Node data is added from the resolution network file.

    Example
    -------

    >>> import nipype.interfaces.cmtk as cmtk
    >>> mknode = cmtk.CreateNodes()
    >>> mknode.inputs.roi_file = 'ROI_scale500.nii.gz'
    >>> mknode.run() # doctest: +SKIP
    """

    input_spec = CreateNodesInputSpec
    output_spec = CreateNodesOutputSpec

    def _run_interface(self, runtime):
        iflogger.info("Creating nodes...")
        create_nodes(
            self.inputs.roi_file,
            self.inputs.resolution_network_file,
            self.inputs.out_filename,
        )
        iflogger.info("Saving node network to %s", op.abspath(self.inputs.out_filename))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["node_network"] = op.abspath(self.inputs.out_filename)
        return outputs
