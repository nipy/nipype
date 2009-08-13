.. _tutorial:

=========
 Tutorial
=========

CommandLine interface example
-----------------------------
CommandLine in interfaces.base is a basic interface for running
command line calls through python

You typically generate an instance of CommandLine, and then call
.run() on it.

.. sourcecode:: ipython
   
   from nipype.interfaces.base import CommandLine
   cl = CommandLine(args=['echo hello'])
   print cl.inputs.args
   clout = cl.run()
   print clout.runtime.messages
   print clout.runtime.returncode
   print clout.runtime.errmessages
   print clout.interface.cmdline
   

   cl.inputs.args = ['echo', 'goodbye']


   clout = CommandLine().run('ls -l')
   clout = CommandLine('ls').run('-l)
   clout = CommandLine(args=['ls', '-l'], cwd='.').run()

.. Note:
   
   If you pass args as a key, value pair to .run(), it will overwrite
   the existing inputs.args, not append to it....however any new
   single args will just be appended

   For example in the code below, the final command line argument
   will be
   *'echo hello'* , NOT 'ls echo hello'

.. sourcecode:: ipython

   clout.CommandLine(args=['ls']).run(args=['echo','hello'])


   

FSL interface example
---------------------

SPM interface example
---------------------

Running a pipeline
-------------------

