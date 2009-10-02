.. _users-guide-index:

============
 User Guide
============
	
:Release: |version|
:Date: |today|

.. toctree::
   :maxdepth: 2

   install
   tutorial
   interface_tutorial



Interfaces
----------

Wrappers around existing software, providing a uniform interface

Pipeline
--------

The pipeline consists of two main parts, nodewrappers, and the engine.

NodeWrappers
~~~~~~~~~~~~

NodeWrappers are bridges between the Interface and the Pipeline. 
They provide added functionality to work with pipelines such as:
  
  #. Adding iterable input values to be passed to interface

  #. Dealing with and generating directories that hold temporary
     processed data. This includes generating hash names that can
     be used to uniquely identify a **specific** process done to the data
     (with specific parameters), so the pipeline can avoid replicating
     redundant processes.  

  #. Validates inputs to each node of the Network exist

  #. Allows user to overwrite existing results

Engine
~~~~~~

This is the machinery that runs the pipeline. Controls the setup 
and execution of the pipeline. the current Engine uses 
`NetworkX <http://networkx.lanl.gov/>`_


 



