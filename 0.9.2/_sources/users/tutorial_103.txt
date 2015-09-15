.. _tutorial_103:

============
Pipeline 103
============

Modifying inputs to pipeline nodes
==================================

Two nodes can be connected as shown below.

.. testcode::
   
    workflow.connect(realigner, 'realigned_files', smoother, 'infile')

The connection mechanism allows for a function to be evaluated on the
output field ('realigned files') of the source node (realigner) and
have its result be sent to the input field ('infile') of the
destination node (smoother).

.. testcode::
   
   def reverse_order(inlist):
       inlist.reverse()
       return inlist
   
   workflow.connect(realigner, ('realigned_files', reverse_order),
                    smoother, 'infile')

This can be extended to provide additional arguments to the
function. For example:

.. testcode::
   
   def reorder(inlist, order):
      return [inlist[item] for item in order]
   
   workflow.connect(realigner, ('realigned_files', reorder, [2, 3, 0, 1]),
                    smoother, 'infile')

In this example, we assume the realigned_files produces a list of 4
files. We can reorder these files in a particular order using the
modifier. Since such modifications are not tracked, they should be
used with extreme care and only in cases where absolutely
necessary. Often, one may find that it is better to insert a node
rather than a function.


Distributed computation
=======================

The pipeline engine has built-in support for distributed computation on
clusters. This can be achieved via plugin-modules for Python_ multiprocessing or
the IPython_ distributed computing interface or SGE/PBS/Condor, provided the
user sets up a workflow on a shared filesystem. These modules can take arguments
that specify additional distribution engine parameters. For IPython_ the
environment needs to be configured for distributed operation. Details are
available at :ref:`plugins`.

The default behavior is to run in series using the Linear plugin.

.. testcode::

   workflow.run()

In some cases it may be advantageous to run the workflow in series locally
(e.g., debugging, small-short pipelines, large memory only interfaces,
relocating working directory/updating hashes).

Debugging
=========

When a crash happens while running a pipeline, a crashdump is stored in
the pipeline's working directory unless the config option 'crashdumpdir'
has been set (see :ref:config_options). 

The crashdump is a compressed numpy file that stores a dictionary
containing three fields:

  1. node - the node that failed
  2. execgraph - the graph that the node came from
  3. traceback - from local or remote session for the failure.

We keep extending the information contained in the file and making
it easier to troubleshoot the failures. However, in the meantime the following
can help to recover information related to the failure.

in IPython_ do (``%pdb`` in IPython_ is similar to ``dbstop`` if error in
Matlab):

.. testcode::

   from nipype.utils.filemanip import loadflat
   crashinfo = loadflat('crashdump....npz')
   %pdb
   crashinfo['node'].run()  # re-creates the crash
   pdb> up  #typically, but not necessarily the crash is one stack frame up
   pdb> inspect variables
   pdb>quit

Relocation of workdir
=====================

In some circumstances, one might decide to move their entire working
directory to a new location. It would be convenient to rerun only
necessary components of the pipeline, instead of running all the nodes
all over again. It is possible to do that with the
:func:`~nipype.pipeline.engine.Pipeline.updatehash` function.

.. testcode::

   workflow.run(updatehash=True)

This will execute the workflow and update all the hash values that
were stored without actually running any of the interfaces.

.. include:: ../links_names.txt
