.. _config_file:

=======================
 Configuration File
=======================

Some of the system wide options of Nipype can be configured using a
configuration file. Nipype looks for the file in the local folder under the name
``nipype.cfg`` and in ``~/.nipype/nipype.cfg`` (in this order). If an option
will not be specified a default value will be assumed. The file is divided into
following sections:

Logging
~~~~~~~

*workflow_level*
	How detailed the logs regarding workflow should be (possible values:
	``INFO`` and ``DEBUG``; default value: ``INFO``)
*filemanip_level*
	How detailed the logs regarding file operations (for example overwriting
	warning) should be (possible values: ``INFO`` and ``DEBUG``; default value:
	``INFO``)
*interface_level*
	How detailed the logs regarding interface execution should be (possible
	values: ``INFO`` and ``DEBUG``; default value: ``INFO``)
*log_to_file*
    Indicates whether logging should also send the output to a file (possible
    values: ``true`` and ``false``; default value: ``false``)
*log_directory*
	Where to store logs. (string, default value: home directory)
*log_size*
	Size of a single log file. (integer, default value: 254000)
*log_rotate*
	How many rotation should the log file make. (integer, default value: 4)

Execution
~~~~~~~~~

*plugin*
	This defines which execution plugin to use. (possible values: ``Linear``,
	``MultiProc``, ``SGE``, ``IPython``; default value: ``Linear``)

*stop_on_first_crash*
	Should the workflow stop upon first node crashing or try to execute as many
	nodes as possible? (possible values: ``true`` and ``false``; default value:
	``false``)

*stop_on_first_rerun*
	Should the workflow stop upon first node trying to recompute (by that we
	mean rerunning a node that has been run before - this can happen due changed
	inputs and/or hash_method since the last run). (possible values: ``true``
	and ``false``; default value: ``false``)

*hash_method*
	Should the input files be checked for changes using their content (slow, but
	100% accurate) or just their size and modification date (fast, but
	potentially prone to errors)? (possible values: ``content`` and
	``timestamp``; default value: ``content``)

*keep_inputs*
    Ensures that all inputs that are created in the nodes working directory are
    kept after node execution (possible values: ``true`` and ``false``; default
    value: ``false``)

*single_thread_matlab*
	Should all of the Matlab interfaces (including SPM) use only one thread?
	This is useful if you are parallelizing your workflow using MultiProc or
	IPython on a single multicore machine. (possible values: ``true`` and
	``false``; default value: ``true``)

*display_variable*
	What ``DISPLAY`` variable should all command line interfaces be
	run with. This is useful if you are using `xnest
	<http://www.x.org/archive/X11R7.5/doc/man/man1/Xnest.1.html>`_
	or `Xvfb <http://www.x.org/archive/X11R6.8.1/doc/Xvfb.1.html>`_
	and you would like to redirect all spawned windows to
	it. (possible values: any X server address; default value: not
	set)

*remove_unnecessary_outputs*
	This will remove any interface outputs not needed by the workflow. If the
	required outputs from a node changes, rerunning the workflow will rerun the
	node. Outputs of leaf nodes (nodes whose outputs are not connected to any 
	other nodes) will never be deleted independent of this parameter. (possible 
	values: ``true`` and ``false``; default value: ``true``)

*use_relative_paths*
	Should the paths stored in results (and used to look for inputs)
	be relative or absolute. Relative paths allow moving the whole
	working directory around but may cause problems with
	symlinks. (possible values: ``true`` and ``false``; default
	value: ``false``)

*local_hash_check*
    Perform the hash check on the job submission machine. This option minimizes
    the number of jobs submitted to a cluster engine or a multiprocessing pool
    to only those that need to be rerun. (possible values: ``true`` and
    ``false``; default value: ``false``)

*job_finished_timeout*
    When batch jobs are submitted through, SGE/PBS/Condor they could be killed
    externally. Nipype checks to see if a results file exists to determine if
    the node has completed. This timeout determines for how long this check is
    done after a job finish is detected. (float in seconds; default value: 5)

*remove_node_directories (EXPERIMENTAL)*
	Removes directories whose outputs have already been used
	up. Doesn't work with IdentiInterface or any node that patches
	data through (without copying) (possible values: ``true`` and
	``false``; default value: ``false``)

Example
~~~~~~~

::

	[logging]
	workflow_level = DEBUG
	
	[execution]
	stop_on_first_crash = true
	hash_method = timestamp
	display_variable = :1

Workflow.config property has a form of a nested dictionary reflecting the
structure of the .cfg file.

::
  
  myworkflow = pe.Workflow()
  myworkflow.config['execution'] = {'stop_on_first_rerun': 'True', 
                                     'hash_method': 'timestamp'}

You can also directly set global config options in your workflow script. An
example is shown below. This needs to be called before you import the
pipeline or the logger. Otherwise logging level will not be reset.

::

  from nipype import config
  cfg = dict(logging=dict(workflow_level = 'DEBUG'),
             execution={'stop_on_first_crash': False,
                        'hash_method': 'content'})
  config.update_config(cfg)

Enabling logging to file
~~~~~~~~~~~~~~~~~~~~~~~~

By default, logging to file is disabled. One can enable and write the file to
a location of choice as in the example below.

::

    import os
    from nipype import config, logging
    config.update_config({'logging': {'log_directory': os.getcwd(),
                                      'log_to_file': True}})
    logging.update_logging(config)

The logging update line is necessary to change the behavior of logging such as
output directory, logging level, etc.,.

Debug configuration
~~~~~~~~~~~~~~~~~~~

To enable debug mode, one can insert the following lines::

  from nipype import config, logging
  config.enable_debug_mode()
  logging.update_logging(config)

In this mode the following variables are set::

  config.set('execution', 'stop_on_first_crash', 'true')
  config.set('execution', 'remove_unnecessary_outputs', 'false')
  config.set('logging', 'workflow_level', 'DEBUG')
  config.set('logging', 'interface_level', 'DEBUG')


.. include:: ../links_names.txt
