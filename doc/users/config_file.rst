.. _config_file:

=======================
 Configuration File
=======================

Some of the system wide options of NiPyPe can be configured using a configuration file. NiPyPe looks for the file in the local folder under the name ``nipype.cfg`` and in ``~/.nipype.cfg`` (in this order). If an option will not be specified a default value will be assumed. The file is divided into following sections:

Logging
~~~~~~~~~

*workflow_level*
	How detailed the logs regarding workflow should be (possible values: ``INFO`` and ``DEBUG``; default value: ``INFO``)

*filemanip_level*
	How detailed the logs regarding file operations (for example overwriting warning) should be (possible values: ``INFO`` and ``DEBUG``; default value: ``INFO``)

*interface_level*
	How detailed the logs regarding interface execution should be (possible values: ``INFO`` and ``DEBUG``; default value: ``INFO``)
*log_directory*
	Where to store logs. (string, default value: home directory)
*log_size*
	Size of a single log file. (integer, default value: 254000)
*log_rotate*
	How many rotation should the log file make. (integer, default value: 4)

Execution
~~~~~~~~~~~

*stop_on_first_crash*
	Should the workflow stop upon first node crashing or try to execute as many nodes as possible? (possible values: ``true`` and ``false``; default value: ``false``)
*hash_method*
	Should the input files be checked for changes using their content (slow, but 100% accurate) or just their size and modification date (fast, but potentially prone to errors)? (possible values: ``content`` and ``timestamp``; default value: ``content``)
*single_thread_matlab*
	Should all of the Matlab interfaces (including SPM) use only one thread? This is useful if you are parallelizing your workflow using IPython on a single multicore machine. (possible values: ``true`` and ``false``; default value: ``true``)
*run_in_series*
	Should workflows be executed in series or parallel? (possible values: ``true`` and ``false``; default value: ``false``)
*display_variable*
	What ``DISPLAY`` variable should all command line interfaces be run with. This is useful if you are using `xnest <http://www.x.org/archive/X11R7.5/doc/man/man1/Xnest.1.html>`_ or `Xvfb <http://www.x.org/archive/X11R6.8.1/doc/Xvfb.1.html>`_ and you would like to redirect all spawned windows to it. (possible values: any X server address; default value: not set)
*use_relative_paths*
	Should the paths stored in results (and used to look for inputs) be relative or absolute. Relative paths allow moving the whole working directory around but may cause problems with simlinks. (possible values: ``true`` and ``false``; default value: ``false``)
*remove_node_directories*
	Removes directories whose outputs have already been used up. Doesn't work with IdentiInterface or any node that patches data through (without copying) (possible values: ``true`` and ``false``; default value: ``false``)

Example
~~~~~~~
::

	[logging]
	workflow_level = DEBUG
	
	[execution]
	stop_on_first_crash = true
	hash_method = timestamp
	display_variable = :1

.. include:: ../links_names.txt
