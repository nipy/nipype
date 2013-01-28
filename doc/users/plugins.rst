.. _plugins:

====================
Using Nipype Plugins
====================

The workflow engine supports a plugin architecture for workflow execution. The
available plugins allow local and distributed execution of workflows and
debugging. Each available plugin is described below.

Current plugins are available for Linear, Multiprocessing, IPython_ distributed
processing platforms and for direct processing on SGE_, PBS_, HTCondor_, and LSF_. We
anticipate future plugins for the Soma_ workflow.

.. note::

   The current distributed processing plugins rely on the availability of a
   shared filesystem across computational nodes.

   A variety of config options can control how execution behaves in this
   distributed context. These are listed later on in this page.

All plugins can be executed with::

    workflow.run(plugin=PLUGIN_NAME, plugin_args=ARGS_DICT)

Optional arguments::

    status_callback : a function handle
    max_jobs : maximum number of concurrent jobs
    max_tries : number of times to try submitting a job
    retry_timeout : amount of time to wait between tries

.. note::

   Except for the status_callback, the remaining arguments only apply to the
   distributed plugins: MultiProc/IPython(X)/SGE/PBS/HTCondor/HTCondorDAGMan/LSF

For example:


Plugins
=======

Debug
-----

This plugin provides a simple mechanism to debug certain components of a
workflow without executing any node.

Mandatory arguments::

  callable :  A function handle that receives as arguments a node and a graph

The function callable will called for every node from a topological sort of the
execution graph.

Linear
------

This plugin runs the workflow one node at a time in a single process locally.
The order of the nodes is determined by a topological sort of the workflow::

    workflow.run(plugin='Linear')

MultiProc
---------

Uses the Python_ multiprocessing library to distribute jobs as new processes on
a local system.

Optional arguments::

  n_procs :  Number of processes to launch in parallel, if not set number of 
  processors/threads will be automatically detected

To distribute processing on a multicore machine, simply call::

  workflow.run(plugin='MultiProc')

This will use all available CPUs. If on the other hand you would like to restrict
the number of used resources (to say 2 CPUs), you can call::

  workflow.run(plugin='MultiProc', plugin_args={'n_procs' : 2}

IPython
-------

This plugin provide access to distributed computing using IPython_ parallel
machinery.

.. note::

  We provide backward compatibility with IPython_ versions earlier than
  0.10.1 using the IPythonX plugin.

  Please read the IPython_ documentation to determine how to setup your cluster
  for distributed processing. This typically involves calling ipcluster.

Once the clients have been started, any pipeline executed with::

  workflow.run(plugin='IPython')


SGE/PBS
-------

In order to use nipype with SGE_ or PBS_ you simply need to call::

       workflow.run(plugin='SGE')
       workflow.run(plugin='PBS')

Optional arguments::

  template: custom template file to use
  qsub_args: any other command line args to be passed to qsub.

For example, the following snippet executes the workflow on myqueue with
a custom template::
 
       workflow.run(plugin='SGE',
          plugin_args=dict(template='mytemplate.sh', qsub_args='-q myqueue')

In addition to overall workflow configuration, you can use node level
configuration for PBS/SGE::

    node.plugin_args = {'qsub_args': '-l nodes=1:ppn=3'}

this would apply only to the node and is useful in situations, where a
particular node might use more resources than other nodes in a workflow.

.. note::

  Setting the keyword `overwrite` would overwrite any global configuration with
  this local configuration::

     node.plugin_args = {'qsub_args': '-l nodes=1:ppn=3', 'overwrite': True}

LSF
---

Submitting via LSF is almost identical to SGE above:

       workflow.run(plugin='LSF')

Optional arguments::

  template: custom template file to use
  bsub_args: any other command line args to be passed to bsub.

HTCondor
--------

DAGMan
~~~~~~

With its DAGMan_ component HTCondor_ (previously Condor) allows for submitting
entire graphs of dependent jobs at once. With the ``CondorDAGMan`` plug-in
Nipype can utilize this functionality to submit complete workflows directly and
in a single step.  Consequently, and in contrast to other plug-ins, workflow
execution returns almost instantaneously -- Nipype is only used to generate the
workflow graph, while job scheduling and dependency resolution are entirely
managed by HTCondor_.

Please note that although DAGMan_ supports specification of data dependencies
as well as data provisioning on compute nodes this functionality is currently
not supported by this plug-in. As with all other batch systems supported by
Nipype, only HTCondor pools with a shared file system can be used to process
Nipype workflows.

Workflow execution with HTCondor DAGMan is done by calling::

       workflow.run(plugin='CondorDAGMan')

Job execution behavior can be tweaked with the following optional plug-in
arguments::

  template : submit spec template to use for job submission. The template
             all generated submit specs are appended to this template. This
             can be a str or a filename.
  submit_specs : additional submit specs that are appended to the generated
                 submit specs to allow for overriding or extending the defaults.
                 This can be a str or a filename.
  dagman_args : arguments to be prepended to the job execution script in the
                dagman call

Please see the `HTCondor documentation`_ for details on possible configuration
options and command line arguments.

``qsub`` emulation
~~~~~~~~~~~~~~~~~~

.. note::

  This plug-in is deprecated and users should migrate to the more robust and
  more versatile ``CondorDAGMan`` plug-in.

Despite the differences between HTCondor and SGE-like batch systems the plugin
usage (incl. supported arguments) is almost identical. The HTCondor plugin relies
on a ``qsub`` emulation script for HTCondor, called ``condor_qsub`` that can be
obtained from a `Git repository on git.debian.org`_. This script is currently
not shipped with a standard HTCondor distribution, but is included in the HTCondor
package from http://neuro.debian.net. It is sufficient to download this script
and install it in any location on a system that is included in the ``PATH``
configuration.

.. _Git repository on git.debian.org: http://anonscm.debian.org/gitweb/?p=pkg-exppsy/condor.git;a=blob_plain;f=debian/condor_qsub;hb=HEAD

Running a workflow in a HTCondor pool is done by calling::

       workflow.run(plugin='Condor')

The plugin supports a limited set of qsub arguments (``qsub_args``) that cover
the most common use cases. The ``condor_qsub`` emulation script translates qsub
arguments into the corresponding HTCondor terminology and handles the actual job
submission. For details on supported options see the manpage of ``condor_qsub``.

Optional arguments::

  qsub_args: any other command line args to be passed to condor_qsub.

.. include:: ../links_names.txt

.. _SGE: http://www.oracle.com/us/products/tools/oracle-grid-engine-075549.html
.. _OGE: http://www.oracle.com/us/products/tools/oracle-grid-engine-075549.html
.. _Soma: http://brainvisa.info/soma/soma-workflow/
.. _PBS: http://www.clusterresources.com/products/torque-resource-manager.php
.. _LSF: http://www.platform.com/Products/platform-lsf
.. _HTCondor: http://www.cs.wisc.edu/htcondor/
.. _DAGMan: http://research.cs.wisc.edu/htcondor/dagman/dagman.html
.. _HTCondor documentation: http://research.cs.wisc.edu/htcondor/manual
