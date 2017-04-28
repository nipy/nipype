.. _install:

======================
 Download and install
======================

This page covers the necessary steps to install Nipype.

Nipype for users
----------------

Using docker
~~~~~~~~~~~~

You can follow the `Nipype tutorial <https://miykael.github.io/nipype_tutorial/>`_

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

Available options are::

    'doc': ['Sphinx>=1.4', 'matplotlib', 'pydotplus'],
    'tests': TESTS_REQUIRES,
    'nipy': ['nitime', 'nilearn', 'dipy', 'nipy', 'matplotlib'],
    'profiler': ['psutil'],
    'duecredit': ['duecredit'],
    'xvfbwrapper': ['xvfbwrapper'],


Debian and Ubuntu
~~~~~~~~~~~~~~~~~

Add the `NeuroDebian <http://neuro.debian.org>`_ repository and install
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

The current release is found here: `<https://github.com/nipy/nipype/releases/latest>`_.

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

Installation for developers
---------------------------

Developers should start `here <../devel/testing_nipype.html>`_.

Recommended Software
--------------------

Strong Recommendations
~~~~~~~~~~~~~~~~~~~~~~

IPython_
  Interactive python environment.

Matplotlib_
  Plotting library

Sphinx_ 1.1
  Required for building the documentation

`Graphviz <http://www.graphviz.org/>`_
  Required for building the documentation.

Interface Dependencies
~~~~~~~~~~~~~~~~~~~~~~

You might not need some of the following packages, depending on what exactly you
want to use nipype for. If you do need any of them, install nipype's wrapper package
(``nipype.interfaces``), then install the programs separately onto your computer, just
like you would install any other app.

FSL_
  4.1.0 or later

matlab_
  2008a or later

SPM_
  SPM5 or later

FreeSurfer_
  FreeSurfer v4.0.0 or later

AFNI_
  2009_12_31_1431 or later

Slicer_
  3.6 or later

Nipy_
  0.4 or later

Nitime_
  (optional)

ANTS_

MRtrix_ and MRtrix3_

Camino_

Camino2Trackvis_

ConnectomeViewer_

.. include:: ../links_names.txt