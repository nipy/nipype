.. _parallel_processing:

====================================
 Distributed processing with nipype
====================================


Using the pipeline engine and IPython
-------------------------------------

The pipeline engine provides a mechanism to distribute processes
across multiple cores and machines in a cluster employing a consistent
login system and a shared file system. Currently, the login process
needs to be ssh-able.

Please read the IPython_ documentation to determine how to setup your
cluster for distributed processing. This typically involves calling
ipcluster. For example the following command will start an eight client
cluster locally and log all client messages to the file in
/tmp/pipeline.::

        ipcluster local -n 8 --logdir /tmp/pipeline
        ipcluster ssh -n 8 --ipclusterfile=clusterfile.py --sshx=loginprofile.sh

Once the clients have been started, any pipeline executed with the run
command or the run_with_manager command will automatically start
getting distributed to the clients. The pipeline engine handles
dependencies between processes.


Notes
~~~~~

In order to avail of this functionality, one has to ensure that no
script defined functions or classes are passed as inputs to interface
nodes. The following example will result in failure to execute.::

       # test_parallel.py
       def myfunc():  
           return 1
       node = nw.NodeWrapper(interface=SomeInterface())
       node.inputs.someinput = myfunc
       pipeline.add_modules([node])
       pipeline.run_with_manager() # will fail

instead such functions should be embedded in pipeline.connect()

Sending environment updates to hosts over ssh::

        from IPython.kernel.client import MultiEngineClient
        mec = MultiEngineClient()
        mec.get_ids()
        env = dict(DISPLAY='hostname:displayport',
           FSLOUTPUTTYPE='NIFTI')
        mec.push(dict(env=env))
        mec.execute('import os')
        mec.execute('os.environ.update(env)')
        # or for fun
        mec.execute('os.system("xeyes")')

Using other distribution engines with nipype
--------------------------------------------

Other distributed processing mechanisms (e.g., SGE, Ruffus,
StarCluster) may be used to parallelize modular functionality.


.. include:: ../links_names.txt
