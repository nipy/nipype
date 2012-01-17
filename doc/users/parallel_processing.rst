.. _parallel_processing:

====================================
 Distributed processing with nipype
====================================

The workflow engine is designed to support plugin interfaces for
distributed processing. Current plugins are available for multiprocessing,
IPython_ (0.10.1/2) distributed processing platforms and for direct
processing on SGE_/OGE_, PBS_, and Condor_. We anticipate future plugins for the Soma_ workflow,
and LSF_.

Parallel distributed processing relies on the availability of a shared
filesystem across computational nodes.

Using the pipeline engine with multiprocessing
----------------------------------------------

To use local distributed processing on a multicore machine, simply call::

  workflow.run(plugin='MultiProc', plugin_args={'n_procs' : 2})

where n_procs defines how many processes to use in parallel. Currently, the
multiprocessing plugin dumps outputs on the command window in an interleaved
manner.

Using the pipeline engine with IPython
--------------------------------------

The pipeline engine provides a mechanism to distribute processes across
multiple cores and machines in a cluster employing a consistent login
system and a shared file system. Currently, the login process needs to
be ssh-able via public key authentication. This document now reflects use 
with IPython_ 0.10.1/2.

Please read the IPython_ documentation to determine how to setup your
cluster for distributed processing. This typically involves calling
ipcluster. For example the following command will start an eight client
cluster locally and log all client messages to the file in
/tmp/pipeline::

        ipcluster local -n 8 --logdir /tmp/pipeline
        
If you use a more complicated environment distributed over ssh try using the
following configuration::

        ipcluster ssh -e --clusterfile=clusterfile.py

clusterfile.py example::

    send_furl = False
    # define cluster configurations
    half_cores = { 'xxx.mit.edu' : 4,
                          'yyy.mit.edu' : 4,
                          'zzz.mit.edu' : 4}
    all_cores = { 'xxx.mit.edu' : 4,
                       'yyy.mit.edu' : 8,
                       'zzz.mit.edu' : 8}
    xxx_only = { 'xxx.mit.edu' : 4}
    # choose cluster configurations
    engines = all_cores # this is the primary information that ipcluster needs

Once the clients have been started, any pipeline executed with::

 workflow.run(plugin='IPython')

will automatically start getting distributed to the
clients. Alternatively, a config file may be used to define the
plugin. See :ref:`config_file` for details.

To prevent prevent parallel execution type::

    workflow.run(plugin='Linear')

Using the pipeline engine with SGE/OGE/PBS
------------------------------------------

In order to use nipype with SGE_/OGE_ (not tested) or PBS_ you simply need to
call::

       workflow.run(plugin='SGE')
       workflow.run(plugin='PBS)
 
you can also pass additional arguments to the SGE/PBS plugin through the
keyword argument (plugin_args). Currentyl the SGE/PBS managers, supports
sending a dictionary containing any of the following keys::

 template - custom template file. by
 qsub_args - any other command line args to be passed to qsub.

For example, the following snippet executes the workflow on myqueue with
a custom template::
 
       workflow.run(plugin='SGE',
          plugin_args=dict(template='mytemplate.sh', qsub_args='-q myqueue')

Using the pipeline engine with Condor
-------------------------------------

Despite the differences between Condor and SGE-like batch systems the plugin
usage (incl. supported arguments) is almost identical. The Condor plugin relies
on a ``qsub`` emulation script for Condor, called ``condor_qsub`` that can be
obtained from a `Git repository on git.debian.org`_. This script is currently
not shipped with a standard Condor distribution, but is included in the Condor
package from http://neuro.debian.net. It is sufficient to download this script
and install it in any location on a system that is included in the ``PATH``
configuration.

.. _Git repository on git.debian.org: http://anonscm.debian.org/gitweb/?p=pkg-exppsy/condor.git;a=blob_plain;f=debian/condor_qsub;hb=HEAD

Running a workflow in a Condor pool is done by calling::

       workflow.run(plugin='Condor')

The plugin supports a limited set of qsub arguments (``qsub_args``) that cover
the most common use cases. The ``condor_qsub`` emulation script translates qsub
arguments into the corresponding Condor terminology and handles the actual job
submission. For details on supported options see the manpage of ``condor_qsub``.



.. include:: ../links_names.txt

.. _SGE: http://www.oracle.com/us/products/tools/oracle-grid-engine-075549.html
.. _OGE: http://www.oracle.com/us/products/tools/oracle-grid-engine-075549.html
.. _Soma: http://brainvisa.info/soma/soma-workflow/
.. _PBS: http://www.clusterresources.com/products/torque-resource-manager.php
.. _LSF: http://www.platform.com/Products/platform-lsf
.. _Condor: http://www.cs.wisc.edu/condor/
