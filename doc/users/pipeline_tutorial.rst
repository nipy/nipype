.. _pipeline_tutorial:

=====================
 Tutorial : Pipeline
=====================


Running a pipeline
-------------------

This section describes how one might go about doing a first level
analysis using the pipeline approach. Running a first-level analysis
pipeline involves setting up a python script containing a few
different pieces.

#. Setting up the nodes of the pipeline

#. Setting up the connections between nodes

#. Providing subject specific model information

.. literalinclude:: ../examples/tutorial1.py


#. To execute the pipeline, call it's run function.

.. sourcecode:: ipython

   pipeline.run()

.. include:: ../links_names.txt
