.. AUTO-GENERATED FILE -- DO NOT EDIT!

workflows.dmri.mrtrix.connectivity_mapping
==========================================


.. module:: nipype.workflows.dmri.mrtrix.connectivity_mapping


.. _nipype.workflows.dmri.mrtrix.connectivity_mapping.create_connectivity_pipeline:

:func:`create_connectivity_pipeline`
------------------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/mrtrix/connectivity_mapping.py#L18>`__



Creates a pipeline that does the same connectivity processing as in the
:ref:`example_dmri_connectivity_advanced` example script. Given a subject id (and completed Freesurfer reconstruction)
diffusion-weighted image, b-values, and b-vectors, the workflow will return the subject's connectome
as a Connectome File Format (CFF) file for use in Connectome Viewer (http://www.cmtk.org).

Example
~~~~~~~

>>> from nipype.workflows.dmri.mrtrix.connectivity_mapping import create_connectivity_pipeline
>>> conmapper = create_connectivity_pipeline("nipype_conmap")
>>> conmapper.inputs.inputnode.subjects_dir = '.'
>>> conmapper.inputs.inputnode.subject_id = 'subj1'
>>> conmapper.inputs.inputnode.dwi = 'data.nii.gz'
>>> conmapper.inputs.inputnode.bvecs = 'bvecs'
>>> conmapper.inputs.inputnode.bvals = 'bvals'
>>> conmapper.run()                 # doctest: +SKIP

Inputs::

    inputnode.subject_id
    inputnode.subjects_dir
    inputnode.dwi
    inputnode.bvecs
    inputnode.bvals
    inputnode.resolution_network_file

Outputs::

    outputnode.connectome
    outputnode.cmatrix
    outputnode.networks
    outputnode.fa
    outputnode.struct
    outputnode.tracts
    outputnode.rois
    outputnode.odfs
    outputnode.filtered_tractography
    outputnode.tdi
    outputnode.nxstatscff
    outputnode.nxcsv
    outputnode.cmatrices_csv
    outputnode.mean_fiber_length
    outputnode.median_fiber_length
    outputnode.fiber_length_std


Graph
~~~~~

.. graphviz::

	digraph connectivity{

	  label="connectivity";

	  connectivity_inputnode[label="inputnode (utility)"];

	  connectivity_outputnode[label="outputnode (utility)"];

	  subgraph cluster_mapping_cmats_to_csv {

	      label="cmats_to_csv";

	    connectivity_cmats_to_csv_inputnode[label="inputnode (utility)"];

	    connectivity_cmats_to_csv_Matlab2CSV[label="Matlab2CSV (misc)"];

	    connectivity_cmats_to_csv_MergeCSVFiles[label="MergeCSVFiles (misc)"];

	    connectivity_cmats_to_csv_outputnode[label="outputnode (utility)"];

	    connectivity_cmats_to_csv_inputnode -> connectivity_cmats_to_csv_Matlab2CSV;

	    connectivity_cmats_to_csv_inputnode -> connectivity_cmats_to_csv_MergeCSVFiles;

	    connectivity_cmats_to_csv_Matlab2CSV -> connectivity_cmats_to_csv_MergeCSVFiles;

	    connectivity_cmats_to_csv_MergeCSVFiles -> connectivity_cmats_to_csv_outputnode;

	  }

	  subgraph cluster_connectivity_mapping {

	      label="mapping";

	    connectivity_mapping_inputnode_within[label="inputnode_within (utility)"];

	    connectivity_mapping_fssourceRH[label="fssourceRH (io)"];

	    connectivity_mapping_mris_convertRH[label="mris_convertRH (freesurfer)"];

	    connectivity_mapping_mris_convertRHsphere[label="mris_convertRHsphere (freesurfer)"];

	    connectivity_mapping_mris_convertRHwhite[label="mris_convertRHwhite (freesurfer)"];

	    connectivity_mapping_Parcellate[label="Parcellate (cmtk)"];

	    connectivity_mapping_mri_convert_ROI_scale500[label="mri_convert_ROI_scale500 (freesurfer)"];

	    connectivity_mapping_fssource[label="fssource (io)"];

	    connectivity_mapping_mri_convert_Brain[label="mri_convert_Brain (freesurfer)"];

	    connectivity_mapping_fssourceLH[label="fssourceLH (io)"];

	    connectivity_mapping_mris_convertLHsphere[label="mris_convertLHsphere (freesurfer)"];

	    connectivity_mapping_mris_convertLHlabels[label="mris_convertLHlabels (freesurfer)"];

	    connectivity_mapping_mris_convertLH[label="mris_convertLH (freesurfer)"];

	    connectivity_mapping_mris_convertRHlabels[label="mris_convertRHlabels (freesurfer)"];

	    connectivity_mapping_GiftiLabels[label="GiftiLabels (utility)"];

	    connectivity_mapping_mris_convertLHwhite[label="mris_convertLHwhite (freesurfer)"];

	    connectivity_mapping_mris_convertLHinflated[label="mris_convertLHinflated (freesurfer)"];

	    connectivity_mapping_MRconvert[label="MRconvert (mrtrix)"];

	    connectivity_mapping_threshold_b0[label="threshold_b0 (mrtrix)"];

	    connectivity_mapping_median3d[label="median3d (mrtrix)"];

	    connectivity_mapping_erode_mask_firstpass[label="erode_mask_firstpass (mrtrix)"];

	    connectivity_mapping_erode_mask_secondpass[label="erode_mask_secondpass (mrtrix)"];

	    connectivity_mapping_NiftiVolumes[label="NiftiVolumes (utility)"];

	    connectivity_mapping_coregister[label="coregister (fsl)"];

	    connectivity_mapping_bet_b0[label="bet_b0 (fsl)"];

	    connectivity_mapping_mris_convertRHinflated[label="mris_convertRHinflated (freesurfer)"];

	    connectivity_mapping_GiftiSurfaces[label="GiftiSurfaces (utility)"];

	    connectivity_mapping_fsl2mrtrix[label="fsl2mrtrix (mrtrix)"];

	    connectivity_mapping_gen_WM_mask[label="gen_WM_mask (mrtrix)"];

	    connectivity_mapping_threshold_wmmask[label="threshold_wmmask (mrtrix)"];

	    connectivity_mapping_dwi2tensor[label="dwi2tensor (mrtrix)"];

	    connectivity_mapping_tensor2fa[label="tensor2fa (mrtrix)"];

	    connectivity_mapping_MRmultiply_merge[label="MRmultiply_merge (utility)"];

	    connectivity_mapping_MRmultiply[label="MRmultiply (mrtrix)"];

	    connectivity_mapping_threshold_FA[label="threshold_FA (mrtrix)"];

	    connectivity_mapping_MRconvert_fa[label="MRconvert_fa (mrtrix)"];

	    connectivity_mapping_tensor2vector[label="tensor2vector (mrtrix)"];

	    connectivity_mapping_tensor2adc[label="tensor2adc (mrtrix)"];

	    connectivity_mapping_estimateresponse[label="estimateresponse (mrtrix)"];

	    connectivity_mapping_csdeconv[label="csdeconv (mrtrix)"];

	    connectivity_mapping_probCSDstreamtrack[label="probCSDstreamtrack (mrtrix)"];

	    connectivity_mapping_tracks2prob[label="tracks2prob (mrtrix)"];

	    connectivity_mapping_MRconvert_tracks2prob[label="MRconvert_tracks2prob (mrtrix)"];

	    connectivity_mapping_tck2trk[label="tck2trk (mrtrix)"];

	    connectivity_mapping_trk2tdi[label="trk2tdi (dipy)"];

	    connectivity_mapping_CreateMatrix[label="CreateMatrix (cmtk)"];

	    connectivity_mapping_nfibs_to_csv[label="nfibs_to_csv (misc)"];

	    connectivity_mapping_merge_nfib_csvs[label="merge_nfib_csvs (misc)"];

	    connectivity_mapping_FiberDataArrays[label="FiberDataArrays (utility)"];

	    connectivity_mapping_CFFConverter[label="CFFConverter (cmtk)"];

	    connectivity_mapping_NxStatsCFFConverter[label="NxStatsCFFConverter (cmtk)"];

	    connectivity_mapping_inputnode_within -> connectivity_mapping_fsl2mrtrix;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_fsl2mrtrix;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_merge_nfib_csvs;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_NxStatsCFFConverter;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_fssourceLH;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_fssourceLH;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_fssourceRH;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_fssourceRH;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_CFFConverter;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_Parcellate;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_Parcellate;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_fssource;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_fssource;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_CreateMatrix;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_CreateMatrix;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_CreateMatrix;

	    connectivity_mapping_fssourceRH -> connectivity_mapping_mris_convertRH;

	    connectivity_mapping_fssourceRH -> connectivity_mapping_mris_convertRHsphere;

	    connectivity_mapping_fssourceRH -> connectivity_mapping_mris_convertRHlabels;

	    connectivity_mapping_fssourceRH -> connectivity_mapping_mris_convertRHlabels;

	    connectivity_mapping_fssourceRH -> connectivity_mapping_mris_convertRHwhite;

	    connectivity_mapping_fssourceRH -> connectivity_mapping_mris_convertRHinflated;

	    connectivity_mapping_mris_convertRH -> connectivity_mapping_GiftiSurfaces;

	    connectivity_mapping_mris_convertRHsphere -> connectivity_mapping_GiftiSurfaces;

	    connectivity_mapping_mris_convertRHwhite -> connectivity_mapping_GiftiSurfaces;

	    connectivity_mapping_Parcellate -> connectivity_mapping_mri_convert_ROI_scale500;

	    connectivity_mapping_Parcellate -> connectivity_mapping_CreateMatrix;

	    connectivity_mapping_Parcellate -> connectivity_mapping_NiftiVolumes;

	    connectivity_mapping_fssource -> connectivity_mapping_mri_convert_Brain;

	    connectivity_mapping_mri_convert_Brain -> connectivity_mapping_NiftiVolumes;

	    connectivity_mapping_mri_convert_Brain -> connectivity_mapping_coregister;

	    connectivity_mapping_mri_convert_Brain -> connectivity_mapping_tck2trk;

	    connectivity_mapping_fssourceLH -> connectivity_mapping_mris_convertLHsphere;

	    connectivity_mapping_fssourceLH -> connectivity_mapping_mris_convertLHlabels;

	    connectivity_mapping_fssourceLH -> connectivity_mapping_mris_convertLHlabels;

	    connectivity_mapping_fssourceLH -> connectivity_mapping_mris_convertLHinflated;

	    connectivity_mapping_fssourceLH -> connectivity_mapping_mris_convertLH;

	    connectivity_mapping_fssourceLH -> connectivity_mapping_mris_convertLHwhite;

	    connectivity_mapping_mris_convertLHsphere -> connectivity_mapping_GiftiSurfaces;

	    connectivity_mapping_mris_convertLHlabels -> connectivity_mapping_GiftiLabels;

	    connectivity_mapping_mris_convertLH -> connectivity_mapping_GiftiSurfaces;

	    connectivity_mapping_mris_convertRHlabels -> connectivity_mapping_GiftiLabels;

	    connectivity_mapping_GiftiLabels -> connectivity_mapping_CFFConverter;

	    connectivity_mapping_GiftiLabels -> connectivity_mapping_NxStatsCFFConverter;

	    connectivity_mapping_mris_convertLHwhite -> connectivity_mapping_GiftiSurfaces;

	    connectivity_mapping_mris_convertLHinflated -> connectivity_mapping_GiftiSurfaces;

	    subgraph cluster_connectivity_mapping_eddycorrect {

	            label="eddycorrect";

	        connectivity_mapping_eddycorrect_inputnode[label="inputnode (utility)"];

	        connectivity_mapping_eddycorrect_split[label="split (fsl)"];

	        connectivity_mapping_eddycorrect_pick_ref[label="pick_ref (utility)"];

	        connectivity_mapping_eddycorrect_coregistration[label="coregistration (fsl)"];

	        connectivity_mapping_eddycorrect_merge[label="merge (fsl)"];

	        connectivity_mapping_eddycorrect_outputnode[label="outputnode (utility)"];

	        connectivity_mapping_eddycorrect_inputnode -> connectivity_mapping_eddycorrect_split;

	        connectivity_mapping_eddycorrect_inputnode -> connectivity_mapping_eddycorrect_pick_ref;

	        connectivity_mapping_eddycorrect_split -> connectivity_mapping_eddycorrect_pick_ref;

	        connectivity_mapping_eddycorrect_split -> connectivity_mapping_eddycorrect_coregistration;

	        connectivity_mapping_eddycorrect_pick_ref -> connectivity_mapping_eddycorrect_coregistration;

	        connectivity_mapping_eddycorrect_coregistration -> connectivity_mapping_eddycorrect_merge;

	        connectivity_mapping_eddycorrect_merge -> connectivity_mapping_eddycorrect_outputnode;

	    }

	    connectivity_mapping_MRconvert -> connectivity_mapping_threshold_b0;

	    connectivity_mapping_threshold_b0 -> connectivity_mapping_median3d;

	    connectivity_mapping_median3d -> connectivity_mapping_erode_mask_firstpass;

	    connectivity_mapping_erode_mask_firstpass -> connectivity_mapping_erode_mask_secondpass;

	    connectivity_mapping_erode_mask_secondpass -> connectivity_mapping_MRmultiply_merge;

	    connectivity_mapping_NiftiVolumes -> connectivity_mapping_CFFConverter;

	    connectivity_mapping_NiftiVolumes -> connectivity_mapping_NxStatsCFFConverter;

	    connectivity_mapping_coregister -> connectivity_mapping_tck2trk;

	    connectivity_mapping_bet_b0 -> connectivity_mapping_gen_WM_mask;

	    connectivity_mapping_mris_convertRHinflated -> connectivity_mapping_GiftiSurfaces;

	    connectivity_mapping_GiftiSurfaces -> connectivity_mapping_CFFConverter;

	    connectivity_mapping_GiftiSurfaces -> connectivity_mapping_NxStatsCFFConverter;

	    connectivity_mapping_fsl2mrtrix -> connectivity_mapping_gen_WM_mask;

	    connectivity_mapping_fsl2mrtrix -> connectivity_mapping_dwi2tensor;

	    connectivity_mapping_fsl2mrtrix -> connectivity_mapping_csdeconv;

	    connectivity_mapping_fsl2mrtrix -> connectivity_mapping_estimateresponse;

	    connectivity_mapping_gen_WM_mask -> connectivity_mapping_threshold_wmmask;

	    connectivity_mapping_gen_WM_mask -> connectivity_mapping_csdeconv;

	    connectivity_mapping_threshold_wmmask -> connectivity_mapping_probCSDstreamtrack;

	    connectivity_mapping_dwi2tensor -> connectivity_mapping_tensor2fa;

	    connectivity_mapping_dwi2tensor -> connectivity_mapping_tensor2vector;

	    connectivity_mapping_dwi2tensor -> connectivity_mapping_tensor2adc;

	    connectivity_mapping_tensor2fa -> connectivity_mapping_MRmultiply_merge;

	    connectivity_mapping_tensor2fa -> connectivity_mapping_MRconvert_fa;

	    connectivity_mapping_MRmultiply_merge -> connectivity_mapping_MRmultiply;

	    connectivity_mapping_MRmultiply -> connectivity_mapping_threshold_FA;

	    connectivity_mapping_threshold_FA -> connectivity_mapping_estimateresponse;

	    connectivity_mapping_estimateresponse -> connectivity_mapping_csdeconv;

	    connectivity_mapping_csdeconv -> connectivity_mapping_probCSDstreamtrack;

	    connectivity_mapping_probCSDstreamtrack -> connectivity_mapping_tracks2prob;

	    connectivity_mapping_probCSDstreamtrack -> connectivity_mapping_tck2trk;

	    connectivity_mapping_tracks2prob -> connectivity_mapping_MRconvert_tracks2prob;

	    connectivity_mapping_tck2trk -> connectivity_mapping_trk2tdi;

	    connectivity_mapping_tck2trk -> connectivity_mapping_CreateMatrix;

	    connectivity_mapping_CreateMatrix -> connectivity_mapping_CFFConverter;

	    connectivity_mapping_CreateMatrix -> connectivity_mapping_CFFConverter;

	    connectivity_mapping_CreateMatrix -> connectivity_mapping_nfibs_to_csv;

	    connectivity_mapping_CreateMatrix -> connectivity_mapping_FiberDataArrays;

	    connectivity_mapping_CreateMatrix -> connectivity_mapping_FiberDataArrays;

	    connectivity_mapping_CreateMatrix -> connectivity_mapping_FiberDataArrays;

	    connectivity_mapping_CreateMatrix -> connectivity_mapping_FiberDataArrays;

	    subgraph cluster_connectivity_mapping_cmats_to_csv {

	            label="cmats_to_csv";

	        connectivity_mapping_cmats_to_csv_inputnode[label="inputnode (utility)"];

	        connectivity_mapping_cmats_to_csv_Matlab2CSV[label="Matlab2CSV (misc)"];

	        connectivity_mapping_cmats_to_csv_MergeCSVFiles[label="MergeCSVFiles (misc)"];

	        connectivity_mapping_cmats_to_csv_outputnode[label="outputnode (utility)"];

	        connectivity_mapping_cmats_to_csv_inputnode -> connectivity_mapping_cmats_to_csv_Matlab2CSV;

	        connectivity_mapping_cmats_to_csv_inputnode -> connectivity_mapping_cmats_to_csv_MergeCSVFiles;

	        connectivity_mapping_cmats_to_csv_Matlab2CSV -> connectivity_mapping_cmats_to_csv_MergeCSVFiles;

	        connectivity_mapping_cmats_to_csv_MergeCSVFiles -> connectivity_mapping_cmats_to_csv_outputnode;

	    }

	    connectivity_mapping_nfibs_to_csv -> connectivity_mapping_merge_nfib_csvs;

	    connectivity_mapping_FiberDataArrays -> connectivity_mapping_CFFConverter;

	    connectivity_mapping_FiberDataArrays -> connectivity_mapping_NxStatsCFFConverter;

	    subgraph cluster_connectivity_mapping_networkx {

	            label="networkx";

	        connectivity_mapping_networkx_inputnode[label="inputnode (utility)"];

	        connectivity_mapping_networkx_NetworkXMetrics[label="NetworkXMetrics (cmtk)"];

	        connectivity_mapping_networkx_Matlab2CSV_global[label="Matlab2CSV_global (misc)"];

	        connectivity_mapping_networkx_Matlab2CSV_node[label="Matlab2CSV_node (misc)"];

	        connectivity_mapping_networkx_mergeNetworks[label="mergeNetworks (utility)"];

	        connectivity_mapping_networkx_MergeCSVFiles_global[label="MergeCSVFiles_global (misc)"];

	        connectivity_mapping_networkx_MergeCSVFiles_node[label="MergeCSVFiles_node (misc)"];

	        connectivity_mapping_networkx_mergeCSVs[label="mergeCSVs (utility)"];

	        connectivity_mapping_networkx_outputnode[label="outputnode (utility)"];

	        connectivity_mapping_networkx_inputnode -> connectivity_mapping_networkx_mergeNetworks;

	        connectivity_mapping_networkx_inputnode -> connectivity_mapping_networkx_MergeCSVFiles_global;

	        connectivity_mapping_networkx_inputnode -> connectivity_mapping_networkx_MergeCSVFiles_global;

	        connectivity_mapping_networkx_inputnode -> connectivity_mapping_networkx_NetworkXMetrics;

	        connectivity_mapping_networkx_inputnode -> connectivity_mapping_networkx_MergeCSVFiles_node;

	        connectivity_mapping_networkx_inputnode -> connectivity_mapping_networkx_MergeCSVFiles_node;

	        connectivity_mapping_networkx_inputnode -> connectivity_mapping_networkx_MergeCSVFiles_node;

	        connectivity_mapping_networkx_NetworkXMetrics -> connectivity_mapping_networkx_Matlab2CSV_node;

	        connectivity_mapping_networkx_NetworkXMetrics -> connectivity_mapping_networkx_outputnode;

	        connectivity_mapping_networkx_NetworkXMetrics -> connectivity_mapping_networkx_Matlab2CSV_global;

	        connectivity_mapping_networkx_NetworkXMetrics -> connectivity_mapping_networkx_mergeNetworks;

	        connectivity_mapping_networkx_Matlab2CSV_global -> connectivity_mapping_networkx_MergeCSVFiles_global;

	        connectivity_mapping_networkx_Matlab2CSV_global -> connectivity_mapping_networkx_MergeCSVFiles_global;

	        connectivity_mapping_networkx_Matlab2CSV_node -> connectivity_mapping_networkx_MergeCSVFiles_node;

	        connectivity_mapping_networkx_mergeNetworks -> connectivity_mapping_networkx_outputnode;

	        connectivity_mapping_networkx_MergeCSVFiles_global -> connectivity_mapping_networkx_outputnode;

	        connectivity_mapping_networkx_MergeCSVFiles_global -> connectivity_mapping_networkx_mergeCSVs;

	        connectivity_mapping_networkx_MergeCSVFiles_node -> connectivity_mapping_networkx_outputnode;

	        connectivity_mapping_networkx_MergeCSVFiles_node -> connectivity_mapping_networkx_mergeCSVs;

	        connectivity_mapping_networkx_mergeCSVs -> connectivity_mapping_networkx_outputnode;

	    }

	    connectivity_mapping_eddycorrect_outputnode -> connectivity_mapping_MRconvert;

	    connectivity_mapping_eddycorrect_outputnode -> connectivity_mapping_dwi2tensor;

	    connectivity_mapping_eddycorrect_outputnode -> connectivity_mapping_tracks2prob;

	    connectivity_mapping_eddycorrect_outputnode -> connectivity_mapping_csdeconv;

	    connectivity_mapping_eddycorrect_outputnode -> connectivity_mapping_NiftiVolumes;

	    connectivity_mapping_eddycorrect_outputnode -> connectivity_mapping_gen_WM_mask;

	    connectivity_mapping_eddycorrect_outputnode -> connectivity_mapping_coregister;

	    connectivity_mapping_eddycorrect_outputnode -> connectivity_mapping_bet_b0;

	    connectivity_mapping_eddycorrect_outputnode -> connectivity_mapping_estimateresponse;

	    connectivity_mapping_eddycorrect_outputnode -> connectivity_mapping_tck2trk;

	    connectivity_mapping_networkx_outputnode -> connectivity_mapping_NxStatsCFFConverter;

	    connectivity_mapping_CreateMatrix -> connectivity_mapping_cmats_to_csv_inputnode;

	    connectivity_mapping_CreateMatrix -> connectivity_mapping_networkx_inputnode;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_eddycorrect_inputnode;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_networkx_inputnode;

	    connectivity_mapping_inputnode_within -> connectivity_mapping_cmats_to_csv_inputnode;

	  }

	  subgraph cluster_mapping_networkx {

	      label="networkx";

	    connectivity_networkx_inputnode[label="inputnode (utility)"];

	    connectivity_networkx_NetworkXMetrics[label="NetworkXMetrics (cmtk)"];

	    connectivity_networkx_Matlab2CSV_global[label="Matlab2CSV_global (misc)"];

	    connectivity_networkx_Matlab2CSV_node[label="Matlab2CSV_node (misc)"];

	    connectivity_networkx_mergeNetworks[label="mergeNetworks (utility)"];

	    connectivity_networkx_MergeCSVFiles_global[label="MergeCSVFiles_global (misc)"];

	    connectivity_networkx_MergeCSVFiles_node[label="MergeCSVFiles_node (misc)"];

	    connectivity_networkx_mergeCSVs[label="mergeCSVs (utility)"];

	    connectivity_networkx_outputnode[label="outputnode (utility)"];

	    connectivity_networkx_inputnode -> connectivity_networkx_mergeNetworks;

	    connectivity_networkx_inputnode -> connectivity_networkx_MergeCSVFiles_global;

	    connectivity_networkx_inputnode -> connectivity_networkx_MergeCSVFiles_global;

	    connectivity_networkx_inputnode -> connectivity_networkx_NetworkXMetrics;

	    connectivity_networkx_inputnode -> connectivity_networkx_MergeCSVFiles_node;

	    connectivity_networkx_inputnode -> connectivity_networkx_MergeCSVFiles_node;

	    connectivity_networkx_inputnode -> connectivity_networkx_MergeCSVFiles_node;

	    connectivity_networkx_NetworkXMetrics -> connectivity_networkx_Matlab2CSV_node;

	    connectivity_networkx_NetworkXMetrics -> connectivity_networkx_outputnode;

	    connectivity_networkx_NetworkXMetrics -> connectivity_networkx_Matlab2CSV_global;

	    connectivity_networkx_NetworkXMetrics -> connectivity_networkx_mergeNetworks;

	    connectivity_networkx_Matlab2CSV_global -> connectivity_networkx_MergeCSVFiles_global;

	    connectivity_networkx_Matlab2CSV_global -> connectivity_networkx_MergeCSVFiles_global;

	    connectivity_networkx_Matlab2CSV_node -> connectivity_networkx_MergeCSVFiles_node;

	    connectivity_networkx_mergeNetworks -> connectivity_networkx_outputnode;

	    connectivity_networkx_MergeCSVFiles_global -> connectivity_networkx_outputnode;

	    connectivity_networkx_MergeCSVFiles_global -> connectivity_networkx_mergeCSVs;

	    connectivity_networkx_MergeCSVFiles_node -> connectivity_networkx_outputnode;

	    connectivity_networkx_MergeCSVFiles_node -> connectivity_networkx_mergeCSVs;

	    connectivity_networkx_mergeCSVs -> connectivity_networkx_outputnode;

	  }

	  mapping_networkx_outputnode -> connectivity_outputnode;

	  connectivity_inputnode -> connectivity_mapping_inputnode_within;

	  connectivity_inputnode -> connectivity_mapping_inputnode_within;

	  connectivity_inputnode -> connectivity_mapping_inputnode_within;

	  connectivity_inputnode -> connectivity_mapping_inputnode_within;

	  connectivity_inputnode -> connectivity_mapping_inputnode_within;

	  mapping_cmats_to_csv_outputnode -> connectivity_outputnode;

	  connectivity_mapping_tck2trk -> connectivity_outputnode;

	  connectivity_mapping_CFFConverter -> connectivity_outputnode;

	  connectivity_mapping_NxStatsCFFConverter -> connectivity_outputnode;

	  connectivity_mapping_CreateMatrix -> connectivity_outputnode;

	  connectivity_mapping_CreateMatrix -> connectivity_outputnode;

	  connectivity_mapping_CreateMatrix -> connectivity_outputnode;

	  connectivity_mapping_CreateMatrix -> connectivity_outputnode;

	  connectivity_mapping_CreateMatrix -> connectivity_outputnode;

	  connectivity_mapping_CreateMatrix -> connectivity_outputnode;

	  connectivity_mapping_merge_nfib_csvs -> connectivity_outputnode;

	  connectivity_mapping_mri_convert_ROI_scale500 -> connectivity_outputnode;

	  connectivity_mapping_trk2tdi -> connectivity_outputnode;

	  connectivity_mapping_csdeconv -> connectivity_outputnode;

	  connectivity_mapping_mri_convert_Brain -> connectivity_outputnode;

	  connectivity_mapping_MRconvert_fa -> connectivity_outputnode;

	  connectivity_mapping_MRconvert_tracks2prob -> connectivity_outputnode;

	}

