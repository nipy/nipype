.. _parallel_processing:

====================================
 Distributed processing with nipype
====================================


Using the pipeline engine and IPython
-------------------------------------

The pipeline engine provides a mechanism to distribute processes across
multiple cores and machines in a cluster employing a consistent login
system and a shared file system. Currently, the login process needs to
be ssh-able via public key authentication.

Please read the IPython_ documentation to determine how to setup your
cluster for distributed processing. This typically involves calling
ipcluster. For example the following command will start an eight client
cluster locally and log all client messages to the file in
/tmp/pipeline::

        ipcluster local -n 8 --logdir /tmp/pipeline
        
If you use a more complicated environment distributed over ssh try using the following configuration::

        ipcluster ssh  --ipclusterfile=clusterfile.py --sshx=loginprofile.sh

clusterfile.py example::

    send_furl = False
    half_cores = { 'xxx.mit.edu' : 4,
                          'yyy.mit.edu' : 4,
                          'zzz.mit.edu' : 4}
    all_cores = { 'xxx.mit.edu' : 4,
                       'yyy.mit.edu' : 8,
                       'zzz.mit.edu' : 8}
    xxx_only = { 'xxx.mit.edu' : 4}
    engines = all_cores

loginprofile.sh example::

    #!/bin/sh                                                                                                           
    source /software/python/SetupNiPy26new.sh                                                                           
    "$@" &> /dev/null &                                                                                                 
    echo $!  

Once the clients have been started, any pipeline executed with the run
command command will automatically start getting distributed to the
clients. The pipeline engine handles dependencies between processes.

Using other distribution engines with nipype
--------------------------------------------

Other distributed processing mechanisms (e.g., SGE, Ruffus,
StarCluster) may be used to parallelize modular functionality.


.. include:: ../links_names.txt
