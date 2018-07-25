.. _neurodocker_tutorial:

====================
Neurodocker tutorial
====================

This page covers the steps to create containers with Neurodocker_.

Neurodocker_ is a command-line program that enables users to generate Docker_
containers and Singularity_ images that include neuroimaging software.

Requirements:

* Docker_ or Singularity_
* Internet connection


Usage
-----

To view the Neurodocker help message
::
    docker run --rm kaczmarj/neurodocker:0.4.0 generate [docker|singularity] --help

Note: choose between ``docker`` and ``singularity`` in ``[docker|singularity]``.

1. Users must specify a base Docker image and the package manager. Any Docker
   image on DockerHub can be used as your base image. Common base images
   include ``debian:stretch``, ``ubuntu:16.04``, ``centos:7``, and the various
   ``neurodebian`` images. If users would like to install software from the
   NeuroDebian repositories, it is recommended to use a ``neurodebian`` base
   image. The package manager is ``apt`` or ``yum``, depending on the base
   image.
2. Next, users should configure the container to fit their needs. This includes
   installing neuroimaging software, installing packages from the chosen package
   manager, installing Python and Python packages, copying files from the local
   machine into the container, and other operations. The list of supported
   neuroimaging software packages is available in the ``neurodocker`` help
   message.
3. The ``neurodocker`` command will generate a Dockerfile or Singularity recipe.
   The Dockerfile can be used with the ``docker build`` command to build a
   Docker image. The Singularity recipe can be used to build a Singularity
   container with the ``singularity build`` command.


Create a Dockerfile or Singularity recipe with FSL, Python 3.6, and Nipype
--------------------------------------------------------------------------

This command prints a Dockerfile (the specification for a Docker image) or a
Singularity recipe (the specification for a Singularity container) to the
terminal.
::
  $ docker run --rm kaczmarj/neurodocker:0.4.0 generate [docker|singularity] \
    --base debian:stretch --pkg-manager apt \
    --fsl version=5.0.10 \
    --miniconda create_env=neuro \
                conda_install="python=3.6 traits" \
                pip_install="nipype"


Build the Docker image
----------------------

The Dockerfile can be saved and used to build the Docker image
::
  $ docker run --rm kaczmarj/neurodocker:0.4.0 generate docker \
    --base debian:stretch --pkg-manager apt \
    --fsl version=5.0.10 \
    --miniconda create_env=neuro \
                conda_install="python=3.6 traits" \
                pip_install="nipype" > Dockerfile
  $ docker build --tag my_image .
  $ # or
  $ docker build --tag my_image - < Dockerfile


Build the Singularity container
-------------------------------

The Singularity recipe can be saved and used to build the Singularity container
::
  $ docker run --rm kaczmarj/neurodocker:0.4.0 generate singularity \
    --base debian:stretch --pkg-manager apt \
    --fsl version=5.0.10 \
    --miniconda create_env=neuro \
                conda_install="python=3.6 traits" \
                pip_install="nipype" > Singularity
  $ singularity build my_nipype.simg Singularity


Use NeuroDebian
---------------

This example installs AFNI and ANTs from the NeuroDebian repositories. It also
installs ``git`` and ``vim``.
::
  $ docker run --rm kaczmarj/neurodocker:0.4.0 generate [docker|singularity] \
    --base neurodebian:stretch --pkg-manager apt \
    --install afni ants git vim

Note: the ``--install`` option will install software using the package manager.
Because the NeuroDebian repositories are enabled in the chosen base image, AFNI
and ANTs may be installed using the package manager. ``git`` and ``vim`` are
available in the default repositories.


Other examples
--------------

Create a container with ``dcm2niix``, Nipype, and jupyter notebook. Install
Miniconda as a non-root user, and activate the Miniconda environment upon
running the container.
::
  $ docker run --rm kaczmarj/neurodocker:0.4.0 generate docker \
    --base centos:7 --pkg-manager yum \
    --dcm2niix version=master method=source \
    --user neuro \
    --miniconda create_env=neuro conda_install="jupyter traits nipype" \
    > Dockerfile
  $ docker build --tag my_nipype - < Dockerfile


Copy local files into a container.
::
  $ docker run --rm kaczmarj/neurodocker:0.4.0 generate [docker|singularity] \
    --base ubuntu:16.04 --pkg-manager apt \
    --copy relative/path/to/source.txt /absolute/path/to/destination.txt

See the `Neurodocker examples page <https://github.com/kaczmarj/neurodocker/tree/master/examples/>`_ for more.

.. include:: ../links_names.txt
