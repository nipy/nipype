.. _debug:

==========================
Debugging Nipype Workflows
==========================

Throughout Nipype_ we try to provide meaningful error messages. If you run into
an error that does not have a meaningful error message please let us know so
that we can improve error reporting.

Here are some notes that may help debugging workflows or understanding
performance issues.

#. Always run your workflow first on a single iterable (e.g. subject) and
   gradually increase the execution distribution complexity (Linear->MultiProc->
   SGE).

#. Use the debug config mode. This can be done by setting::

      from nipype import config
      config.enable_debug_mode()

   as the first import of your nipype script.

   .. note::

     Turning on debug will rerun your workflows and will rerun them after
     debugging is turned off.

     Turning on debug mode will also override log levels specified elsewhere,
     such as in the nipype configuration.
     ``workflow``, ``interface`` and ``utils`` loggers will all be set to
     level ```DEBUG``.

#. There are several configuration options that can help with debugging. See
   :ref:`config_file` for more details::

       keep_inputs
       remove_unnecessary_outputs
       stop_on_first_crash
       stop_on_first_rerun

#. When running in distributed mode on cluster engines, it is possible for a
   node to fail without generating a crash file in the crashdump directory. In
   such cases, it will store a crash file in the `batch` directory.

#. All Nipype crashfiles can be inspected with the `nipypecli crash`
   utility.

#. The `nipypecli search` command allows you to search for regular expressions
   in the tracebacks of the Nipype crashfiles within a log folder.

#. Nipype determines the hash of the input state of a node. If any input
   contains strings that represent files on the system path, the hash evaluation
   mechanism will determine the timestamp or content hash of each of those
   files. Thus any node with an input containing huge dictionaries (or lists) of
   file names can cause serious performance penalties.

#. For HUGE data processing, 'stop_on_first_crash':'False', is needed to get the
   bulk of processing done, and then 'stop_on_first_crash':'True', is needed for
   debugging and finding failing cases. Setting  'stop_on_first_crash': 'False'
   is a reasonable option when you would expect 90% of the data to execute
   properly.

#. Sometimes nipype will hang as if nothing is going on and if you hit Ctrl+C
   you will get a `ConcurrentLogHandler` error. Simply remove the pypeline.lock
   file in your home directory and continue.

#. One many clusters with shared NFS mounts synchronization of files across
   clusters may not happen before the typical NFS cache timeouts. When using
   PBS/LSF/SGE/Condor plugins in such cases the workflow may crash because it
   cannot retrieve the node result. Setting the `job_finished_timeout` can help::

       workflow.config['execution']['job_finished_timeout'] = 65

.. include:: ../links_names.txt
