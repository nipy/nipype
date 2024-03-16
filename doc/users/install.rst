.. _install:

====================
Download and install
====================

This page covers the necessary steps to install Nipype.

Using docker
~~~~~~~~~~~~

To get started using Docker, you can follow the `Nipype tutorial
<https://miykael.github.io/nipype_tutorial/>`_, or pull the `nipype/nipype`
image from Docker hub::

    docker pull nipype/nipype

You may also build custom docker containers with specific versions of software
using NeuroDocker_ (see the `Neurodocker tutorial
<https://miykael.github.io/nipype_tutorial/notebooks/introduction_neurodocker.html>`_).

Using conda
~~~~~~~~~~~

Installing nipype from the conda-forge channel can be achieved by::

  conda install --channel conda-forge nipype

It is possible to list all of the versions of nipype available on your platform with::

  conda search nipype --channel conda-forge

For more information, please see https://github.com/conda-forge/nipype-feedstock


Using Pypi
~~~~~~~~~~

The installation process is similar to other Python packages.

If you already have a Python environment set up, you can do::

  pip install nipype

If you want to install all the optional features of ``nipype``,
use the following command::

  pip install nipype[all]

While `all` installs everything, one can also install select components as
listed below::

    'data': ['datalad'],
    'doc': ['dipy', 'ipython', 'matplotlib', 'nbsphinx', 'sphinx-argparse',
            'sphinx>=2.1.2', 'sphinxcontrib-apidoc'],
    'duecredit': ['duecredit'],
    'nipy': ['nitime', 'nilearn', 'dipy', 'nipy', 'matplotlib'],
    'profiler': ['psutil>=5.0'],
    'pybids': ['pybids>=0.7.0'],
    'specs': ['black'],
    'ssh': ['paramiko'],
    'tests': ['codecov', 'coverage<5', 'pytest', 'pytest-cov', 'pytest-env',
              'pytest-timeout'],
    'xvfbwrapper': ['xvfbwrapper'],


Debian and Ubuntu
~~~~~~~~~~~~~~~~~

Add the NeuroDebian_ repository and install
the ``python-nipype`` package using ``apt-get`` or your favorite package
manager.

Mac OS X
~~~~~~~~

The easiest way to get nipype running on Mac OS X is to install Miniconda_ and
follow the instructions above. If you have a non-conda environment you can
install nipype by typing::

  pip install nipype

Note that the above procedure may require availability of gcc on your system
path to compile the traits package.

From source
~~~~~~~~~~~

The most recent release is found here: `<https://github.com/nipy/nipype/releases/latest>`_.

The development version: [`zip <http://github.com/nipy/nipype/zipball/master>`__ `tar.gz
<http://github.com/nipy/nipype/tarball/master>`__]

For previous versions: `prior downloads <http://github.com/nipy/nipype/tags>`_

If you downloaded the source distribution named something
like ``nipype-x.y.tar.gz``, then unpack the tarball, change into the
``nipype-x.y`` directory and install nipype using::

    pip install .

**Note:** Depending on permissions you may need to use ``sudo``.


Testing the install
-------------------

The best way to test the install is checking nipype's version and then running
the tests::

    python -c "import nipype; print(nipype.__version__)"
    python -c "import nipype; nipype.test()"

Interface Dependencies
~~~~~~~~~~~~~~~~~~~~~~

Nipype provides wrappers around many neuroimaging tools and contains some
algorithms. These tools will need to be installed for Nipype to run. You can
create containers with different versions of these tools installed using
NeuroDocker_.

Installation for developers
---------------------------

Developers should start `here <../devel/testing_nipype.rst>`_.

Developers can also use this docker container: `docker pull nipype/nipype:master`

.. include:: ../links_names.txt
