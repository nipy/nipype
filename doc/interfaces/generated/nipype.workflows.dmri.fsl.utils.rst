.. AUTO-GENERATED FILE -- DO NOT EDIT!

workflows.dmri.fsl.utils
========================


.. module:: nipype.workflows.dmri.fsl.utils


.. _nipype.workflows.dmri.fsl.utils.apply_all_corrections:

:func:`apply_all_corrections`
-----------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L136>`__



Combines two lists of linear transforms with the deformation field
map obtained typically after the SDC process.
Additionally, computes the corresponding bspline coefficients and
the map of determinants of the jacobian.


Graph
~~~~~

.. graphviz::

	digraph UnwarpArtifacts{

	  label="UnwarpArtifacts";

	  UnwarpArtifacts_inputnode[label="inputnode (utility)"];

	  UnwarpArtifacts_SplitDWIs[label="SplitDWIs (fsl)"];

	  UnwarpArtifacts_Reference[label="Reference (utility)"];

	  UnwarpArtifacts_ConvertWarp[label="ConvertWarp (fsl)"];

	  UnwarpArtifacts_CoeffComp[label="CoeffComp (fsl)"];

	  UnwarpArtifacts_JacobianComp[label="JacobianComp (fsl)"];

	  UnwarpArtifacts_UnwarpDWIs[label="UnwarpDWIs (fsl)"];

	  UnwarpArtifacts_ModulateDWIs[label="ModulateDWIs (fsl)"];

	  UnwarpArtifacts_RemoveNegative[label="RemoveNegative (fsl)"];

	  UnwarpArtifacts_MergeDWIs[label="MergeDWIs (fsl)"];

	  UnwarpArtifacts_outputnode[label="outputnode (utility)"];

	  UnwarpArtifacts_inputnode -> UnwarpArtifacts_ConvertWarp;

	  UnwarpArtifacts_inputnode -> UnwarpArtifacts_ConvertWarp;

	  UnwarpArtifacts_inputnode -> UnwarpArtifacts_ConvertWarp;

	  UnwarpArtifacts_inputnode -> UnwarpArtifacts_ConvertWarp;

	  UnwarpArtifacts_inputnode -> UnwarpArtifacts_SplitDWIs;

	  UnwarpArtifacts_SplitDWIs -> UnwarpArtifacts_Reference;

	  UnwarpArtifacts_SplitDWIs -> UnwarpArtifacts_UnwarpDWIs;

	  UnwarpArtifacts_Reference -> UnwarpArtifacts_CoeffComp;

	  UnwarpArtifacts_Reference -> UnwarpArtifacts_UnwarpDWIs;

	  UnwarpArtifacts_Reference -> UnwarpArtifacts_JacobianComp;

	  UnwarpArtifacts_ConvertWarp -> UnwarpArtifacts_CoeffComp;

	  UnwarpArtifacts_ConvertWarp -> UnwarpArtifacts_UnwarpDWIs;

	  UnwarpArtifacts_ConvertWarp -> UnwarpArtifacts_outputnode;

	  UnwarpArtifacts_CoeffComp -> UnwarpArtifacts_JacobianComp;

	  UnwarpArtifacts_CoeffComp -> UnwarpArtifacts_outputnode;

	  UnwarpArtifacts_JacobianComp -> UnwarpArtifacts_ModulateDWIs;

	  UnwarpArtifacts_JacobianComp -> UnwarpArtifacts_outputnode;

	  UnwarpArtifacts_UnwarpDWIs -> UnwarpArtifacts_ModulateDWIs;

	  UnwarpArtifacts_ModulateDWIs -> UnwarpArtifacts_RemoveNegative;

	  UnwarpArtifacts_RemoveNegative -> UnwarpArtifacts_MergeDWIs;

	  UnwarpArtifacts_MergeDWIs -> UnwarpArtifacts_outputnode;

	}


.. _nipype.workflows.dmri.fsl.utils.cleanup_edge_pipeline:

:func:`cleanup_edge_pipeline`
-----------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L11>`__



Perform some de-spiking filtering to clean up the edge of the fieldmap
(copied from fsl_prepare_fieldmap)


Graph
~~~~~

.. graphviz::

	digraph Cleanup{

	  label="Cleanup";

	  Cleanup_inputnode[label="inputnode (utility)"];

	  Cleanup_MskErode[label="MskErode (fsl)"];

	  Cleanup_Despike[label="Despike (fsl)"];

	  Cleanup_NewMask[label="NewMask (fsl)"];

	  Cleanup_ApplyMask[label="ApplyMask (fsl)"];

	  Cleanup_Merge[label="Merge (utility)"];

	  Cleanup_AddEdge[label="AddEdge (fsl)"];

	  Cleanup_outputnode[label="outputnode (utility)"];

	  Cleanup_inputnode -> Cleanup_NewMask;

	  Cleanup_inputnode -> Cleanup_Despike;

	  Cleanup_inputnode -> Cleanup_Despike;

	  Cleanup_inputnode -> Cleanup_AddEdge;

	  Cleanup_inputnode -> Cleanup_MskErode;

	  Cleanup_MskErode -> Cleanup_NewMask;

	  Cleanup_MskErode -> Cleanup_Merge;

	  Cleanup_Despike -> Cleanup_ApplyMask;

	  Cleanup_NewMask -> Cleanup_ApplyMask;

	  Cleanup_ApplyMask -> Cleanup_Merge;

	  Cleanup_Merge -> Cleanup_AddEdge;

	  Cleanup_AddEdge -> Cleanup_outputnode;

	}


.. _nipype.workflows.dmri.fsl.utils.dwi_flirt:

:func:`dwi_flirt`
-----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L79>`__



Generates a workflow for linear registration of dwi volumes


Graph
~~~~~

.. graphviz::

	digraph DWICoregistration{

	  label="DWICoregistration";

	  DWICoregistration_inputnode[label="inputnode (utility)"];

	  DWICoregistration_Bias[label="Bias (ants)"];

	  DWICoregistration_InitXforms[label="InitXforms (utility)"];

	  DWICoregistration_B0Equalize[label="B0Equalize (utility)"];

	  DWICoregistration_MskDilate[label="MskDilate (fsl)"];

	  DWICoregistration_SplitDWIs[label="SplitDWIs (fsl)"];

	  DWICoregistration_DWEqualize[label="DWEqualize (utility)"];

	  DWICoregistration_CoRegistration[label="CoRegistration (fsl)"];

	  DWICoregistration_RemoveNegative[label="RemoveNegative (fsl)"];

	  DWICoregistration_MergeDWIs[label="MergeDWIs (fsl)"];

	  DWICoregistration_outputnode[label="outputnode (utility)"];

	  DWICoregistration_inputnode -> DWICoregistration_SplitDWIs;

	  DWICoregistration_inputnode -> DWICoregistration_Bias;

	  DWICoregistration_inputnode -> DWICoregistration_Bias;

	  DWICoregistration_inputnode -> DWICoregistration_MskDilate;

	  DWICoregistration_inputnode -> DWICoregistration_InitXforms;

	  DWICoregistration_inputnode -> DWICoregistration_InitXforms;

	  DWICoregistration_inputnode -> DWICoregistration_B0Equalize;

	  DWICoregistration_Bias -> DWICoregistration_B0Equalize;

	  DWICoregistration_InitXforms -> DWICoregistration_CoRegistration;

	  DWICoregistration_B0Equalize -> DWICoregistration_CoRegistration;

	  DWICoregistration_MskDilate -> DWICoregistration_DWEqualize;

	  DWICoregistration_MskDilate -> DWICoregistration_CoRegistration;

	  DWICoregistration_MskDilate -> DWICoregistration_CoRegistration;

	  DWICoregistration_SplitDWIs -> DWICoregistration_DWEqualize;

	  DWICoregistration_DWEqualize -> DWICoregistration_CoRegistration;

	  DWICoregistration_CoRegistration -> DWICoregistration_RemoveNegative;

	  DWICoregistration_CoRegistration -> DWICoregistration_outputnode;

	  DWICoregistration_RemoveNegative -> DWICoregistration_MergeDWIs;

	  DWICoregistration_MergeDWIs -> DWICoregistration_outputnode;

	}


.. _nipype.workflows.dmri.fsl.utils.vsm2warp:

:func:`vsm2warp`
----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L50>`__



Converts a voxel shift map (vsm) to a displacements field (warp).


Graph
~~~~~

.. graphviz::

	digraph Shiftmap2Warping{

	  label="Shiftmap2Warping";

	  Shiftmap2Warping_inputnode[label="inputnode (utility)"];

	  Shiftmap2Warping_Fix_hdr[label="Fix_hdr (utility)"];

	  Shiftmap2Warping_ScaleField[label="ScaleField (fsl)"];

	  Shiftmap2Warping_vsm2dfm[label="vsm2dfm (fsl)"];

	  Shiftmap2Warping_outputnode[label="outputnode (utility)"];

	  Shiftmap2Warping_inputnode -> Shiftmap2Warping_ScaleField;

	  Shiftmap2Warping_inputnode -> Shiftmap2Warping_Fix_hdr;

	  Shiftmap2Warping_inputnode -> Shiftmap2Warping_Fix_hdr;

	  Shiftmap2Warping_inputnode -> Shiftmap2Warping_vsm2dfm;

	  Shiftmap2Warping_inputnode -> Shiftmap2Warping_vsm2dfm;

	  Shiftmap2Warping_Fix_hdr -> Shiftmap2Warping_ScaleField;

	  Shiftmap2Warping_ScaleField -> Shiftmap2Warping_vsm2dfm;

	  Shiftmap2Warping_vsm2dfm -> Shiftmap2Warping_outputnode;

	}


.. _nipype.workflows.dmri.fsl.utils.add_empty_vol:

:func:`add_empty_vol`
---------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L664>`__



Adds an empty vol to the phase difference image


.. _nipype.workflows.dmri.fsl.utils.b0_average:

:func:`b0_average`
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L429>`__



A function that averages the *b0* volumes from a DWI dataset.
As current dMRI data are being acquired with all b-values > 0.0,
the *lowb* volumes are selected by specifying the parameter max_b.

.. warning:: *b0* should be already registered (head motion artifact should
  be corrected).


.. _nipype.workflows.dmri.fsl.utils.b0_indices:

:func:`b0_indices`
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L420>`__



Extract the indices of slices in a b-values file with a low b value


.. _nipype.workflows.dmri.fsl.utils.compute_readout:

:func:`compute_readout`
-----------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L551>`__



Computes readout time from epi params (see `eddy documentation
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/EDDY/Faq#How_do_I_know_what_to_put_into_my_--acqp_file.3F>`_).

.. warning:: ``params['echospacing']`` should be in *sec* units.


.. _nipype.workflows.dmri.fsl.utils.copy_hdr:

:func:`copy_hdr`
----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L715>`__






.. _nipype.workflows.dmri.fsl.utils.demean_image:

:func:`demean_image`
--------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L633>`__



Demean image data inside mask


.. _nipype.workflows.dmri.fsl.utils.eddy_rotate_bvecs:

:func:`eddy_rotate_bvecs`
-------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L501>`__



Rotates the input bvec file accordingly with a list of parameters sourced
from ``eddy``, as explained `here
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/EDDY/Faq#Will_eddy_rotate_my_bevcs_for_me.3F>`_.


.. _nipype.workflows.dmri.fsl.utils.enhance:

:func:`enhance`
---------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L737>`__






.. _nipype.workflows.dmri.fsl.utils.extract_bval:

:func:`extract_bval`
--------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L197>`__



Writes an image containing only the volumes with b-value specified at
input


.. _nipype.workflows.dmri.fsl.utils.hmc_split:

:func:`hmc_split`
-----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L232>`__



Selects the reference and moving volumes from a dwi dataset
for the purpose of HMC.


.. _nipype.workflows.dmri.fsl.utils.insert_mat:

:func:`insert_mat`
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L316>`__






.. _nipype.workflows.dmri.fsl.utils.rads2radsec:

:func:`rads2radsec`
-------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L611>`__



Converts input phase difference map to rads


.. _nipype.workflows.dmri.fsl.utils.recompose_dwi:

:func:`recompose_dwi`
---------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L326>`__



Recompose back the dMRI data accordingly the b-values table after EC
correction


.. _nipype.workflows.dmri.fsl.utils.recompose_xfm:

:func:`recompose_xfm`
---------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L359>`__



Insert identity transformation matrices in b0 volumes to build up a list


.. _nipype.workflows.dmri.fsl.utils.remove_comp:

:func:`remove_comp`
-------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L278>`__



Removes the volume ``volid`` from the 4D nifti file


.. _nipype.workflows.dmri.fsl.utils.reorient_bvecs:

:func:`reorient_bvecs`
----------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L686>`__



Checks reorientations of ``in_dwi`` w.r.t. ``old_dwi`` and
reorients the in_bvec table accordingly.


.. _nipype.workflows.dmri.fsl.utils.rotate_bvecs:

:func:`rotate_bvecs`
--------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L464>`__



Rotates the input bvec file accordingly with a list of matrices.

.. note:: the input affine matrix transforms points in the destination
  image to their corresponding coordinates in the original image.
  Therefore, this matrix should be inverted first, as we want to know
  the target position of :math:`\vec{r}`.


.. _nipype.workflows.dmri.fsl.utils.siemens2rads:

:func:`siemens2rads`
--------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L575>`__



Converts input phase difference map to rads


.. _nipype.workflows.dmri.fsl.utils.time_avg:

:func:`time_avg`
----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/workflows/dmri/fsl/utils.py#L384>`__



Average the input time-series, selecting the indices given in index

.. warning:: time steps should be already registered (corrected for
  head motion artifacts).

