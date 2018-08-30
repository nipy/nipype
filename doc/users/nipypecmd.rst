.. _nipypecmd:

============================================================
Running Nipype Interfaces from the command line (nipype_cmd)
============================================================

The primary use of Nipype_ is to build automated non-interactive pipelines.
However, sometimes there is a need to run some interfaces quickly from the command line.
This is especially useful when running Interfaces wrapping code that does not have
command line equivalents (nipy or SPM). Being able to run Nipype interfaces opens new
possibilities such as inclusion of SPM processing steps in bash scripts.

To run Nipype Interfaces you need to use the nipype_cmd tool that should already be installed.
The tool allows you to list Interfaces available in a certain package:

.. testcode::


	$nipype_cmd nipype.interfaces.nipy

	Available Interfaces:
	    SpaceTimeRealigner
	    Similarity
	    ComputeMask
	    FitGLM
	    EstimateContrast

After selecting a particular Interface you can learn what inputs it requires:

.. testcode::


	$nipype_cmd nipype.interfaces.nipy ComputeMask --help

	usage:nipype_cmd nipype.interfaces.nipy ComputeMask [-h] [--M M] [--cc CC]
	                                                     [--ignore_exception IGNORE_EXCEPTION]
	                                                     [--m M]
	                                                     [--reference_volume REFERENCE_VOLUME]
	                                                     mean_volume

	Run ComputeMask

	positional arguments:
	  mean_volume           mean EPI image, used to compute the threshold for the
	                        mask

	optional arguments:
	  -h, --help            show this help message and exit
	  --M M                 upper fraction of the histogram to be discarded
	  --cc CC               Keep only the largest connected component
	  --ignore_exception IGNORE_EXCEPTION
	                        Print an error message instead of throwing an
	                        exception in case the interface fails to run
	  --m M                 lower fraction of the histogram to be discarded
	  --reference_volume REFERENCE_VOLUME
	                        reference volume used to compute the mask. If none is
	                        give, the mean volume is used.

Finally you can run run the Interface:

.. testcode::

	$nipype_cmd nipype.interfaces.nipy ComputeMask mean.nii.gz

All that from the command line without having to start python interpreter manually.

.. include:: ../links_names.txt
