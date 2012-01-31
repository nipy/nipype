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

      import config
      config.enable_debug_mode()

   as the first import of your nipype script.

#. There are several configuration options that can help with debugging. See
   :ref:`config_file` for more details::

       keep_inputs
       remove_unnecessary_outputs
       stop_on_first_crash
       stop_on_first_rerun

#. When running in distributed mode on cluster engines, it is possible for a
   node to fail without generating a crash file in the crashdump directory. In
   such cases, it will store a crash file in the `batch` directory.

#. All Nipype crashfiles can be inspected with the `nipype_display_crash`
   utility.

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

.. include:: ../links_names.txt
