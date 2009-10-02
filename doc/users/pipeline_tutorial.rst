.. _pipeline_tutorial:

=====================
 Tutorial : Pipeline
=====================


Running a pipeline
-------------------

This is a step by step guide to setting up and running a pipelined
analysis. For this tutorial we will be using a slightly modified
version of the FBIRN Phase I travelling data set. The tutorial is
based on an SPM analysis, with a few non-SPM things thrown into the
mix. 

Requirements

#. Release 0.1 of nipype and it's dependencies have been installed

#. FSL and matlab are available and callable from the command line

#. SPM 5 is installed and callable in matlab

#. 2.5 GB of space

Step 0.
~~~~~~~

Download and extract the `Pipeline tutorial data. 
<http://some.domain/nipype-tutorial.tgz>`_

Step 1.
~~~~~~~

Ensure that all programs are available by calling ``bet``, ``matlab``
and then ``which spm`` within matlab to ensure you have spm5 in your
matlab path.

Step 2.
~~~~~~~

You can now run the tutorial by typing ``python tutorial_script.py``
within the nipype-tutorial directory. This will run a full first level
analysis on two subjects following by a 1-sample t-test on their first
level results. The next section goes through each section of the
tutorial script and describes what it is doing.


The anatomy of a pipeline script
--------------------------------

In nipype, a pipeline is represented as an acyclic, directed data-flow
graph, where each node of the graph is a process (e.g., realignment,
smoothing) and the connections between the nodes control how data
flows between the processes. 

.. literalinclude:: ../examples/tutorial1.py

.. include:: ../links_names.txt
