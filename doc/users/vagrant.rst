.. _debug:

======================
Running Nipype in a VM
======================

.. tip::

   Creating the Vagrant VM as described below requires an active internet
   connection.

Container technologies (Vagrant_, Docker_) allow creating and manipulating
lightweight virtual environments. The Nipype_ source now contains a Vagrantfile
to launch a Vagrant_ VM.

Requirements:

* Vagrant_
* Virtualbox_

After you have installed Vagrant and Virtualbox, you simply need to download the
latest Nipype source and unzip/tar/compress it. Go into your terminal and switch
to the nipype source directory. Make sure the Vagrantfile is in the directory.
Now you can execute::

  vagrant up

This will launch and provision the virtual machine.

The default virtual machine is built using Ubuntu Precise 64, linked to the
NeuroDebian_ source repo and contains a 2 node Grid Engine for cluster
execution.

The machine has a default IP address of `192.168.100.20` . From the vagrant
startup directory you can log into the machine using::

  vagrant ssh

Now you can install your favorite software using::

  sudo apt-get install fsl afni

Also note that the directory in which you call `vagrant up` will be mounted
under `/vagrant` inside the virtual machine. You can also copy the Vagrantfile
or modify it in order to mount a different directory/directories.

Please read through Vagrant_ documentation on other features. The python
environment is built using a `miniconda <http://repo.continuum.io/miniconda/>`_
distribution. Hence `conda` can be used to do your python package management
inside the VM.

.. include:: ../links_names.txt
