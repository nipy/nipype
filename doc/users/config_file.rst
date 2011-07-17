.. _config_file:

=======================
 Configuration File
=======================

Some of the system wide options of NiPyPe can be configured using a
configuration file. NiPyPe looks for the file in the local folder under the name
``nipype.cfg`` and in ``~/.nipype.cfg`` (in this order). If an option will not
be specified a default value will be assumed. The file is divided into following
sections:

Logging
~~~~~~~~~

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
*log_directory*
	Where to store logs. (string, default value: home directory)
*log_size*
	Size of a single log file. (integer, default value: 254000)
*log_rotate*
	How many rotation should the log file make. (integer, default value: 4)

Execution
~~~~~~~~~~~

*plugin*
	This defines which execution plugin to use. (possible values: 
    ``Linear``, ``MultiProc``, ``SGE``, ``IPython``; default value: ``Linear``)

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
	This will remove any interface outputs not needed by the
    workflow. If the required outputs from a node changes, rerunning
    the workflow will rerun the node. (possible values: ``true`` and
    ``false``; default value: ``true``)

*use_relative_paths*
	Should the paths stored in results (and used to look for inputs)
	be relative or absolute. Relative paths allow moving the whole
	working directory around but may cause problems with
	symlinks. (possible values: ``true`` and ``false``; default
	value: ``false``)

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

Additionally you can set some config options by setting the workflow.config. This, however, currently does not work for options related to logging levels. Those will be always read from .cfg files.

Workflow.config property has a form of a nested dictionary reflecting the structure of the .cfg file.

::
  
  myworkflow = pe.Workflow()
  myworkflow.config['execution'] = {'stop_on_first_rerun': 'True', 
                                     'hash_method': 'timestamp'}

You can also directly set config options in your workflow script. An
example is shown below. This needs to be called before you import the
pipeline or the logger. Otherwise logging level will not be reset.

::

  from nipype.utils.config import config
  from StringIO import StringIO
  cfg = StringIO("""
  [logging]
        workflow_level = DEBUG

  [execution]
  stop_on_first_crash = false
  hash_method = content
  """)
  
  config.readfp(cfg)


.. include:: ../links_names.txt
