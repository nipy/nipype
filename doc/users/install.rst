.. _install:

======================
 Download and install
======================

This page covers the necessary steps to install Nipype.

Nipype for users
----------------

Using conda
~~~~~~~~~~~

Installing nipype from the conda-forge channel can be achieved by adding conda-forge to your channels with::

  conda config --add channels conda-forge


Once the conda-forge channel has been enabled, nipype can be installed with::

  conda install nipype


It is possible to list all of the versions of nipype available on your platform with::

  conda search nipype --channel conda-forge

For more information, please see https://github.com/conda-forge/nipype-feedstock


Using Pypi
~~~~~~~~~~

The installation process is similar to other Python packages.

If you already have a Python environment set up, you can do::

  easy_install nipype

or::

  pip install nipype


If you want to install all the optional features of ``nipype``,
use the following command (only for ``nipype>=0.13``)::

  pip install nipype[all]


Debian and Ubuntu
~~~~~~~~~~~~~~~~~

Add the `NeuroDebian <http://neuro.debian.org>`_ repository and install
the ``python-nipype`` package using ``apt-get`` or your favorite package
manager.

Mac OS X
~~~~~~~~

The easiest way to get nipype running on Mac OS X is to install Anaconda_ or
Canopy_ and then add nipype by executing::

  easy_install nipype


From source
~~~~~~~~~~~

The current release is found here: `<https://github.com/nipy/nipype/releases/latest>`_.

The development version: [`zip <http://github.com/nipy/nipype/zipball/master>`__ `tar.gz
<http://github.com/nipy/nipype/tarball/master>`__]

For previous versions: `prior downloads <http://github.com/nipy/nipype/tags>`_

If you downloaded the source distribution named something
like ``nipype-x.y.tar.gz``, then unpack the tarball, change into the
``nipype-x.y`` directory and install nipype using::

    python setup.py install

**Note:** Depending on permissions you may need to use ``sudo``.


Testing the install
-------------------

The best way to test the install is checking nipype's version ::

    python -c "import nipype; print(nipype.__version__)"


Installation for developers
---------------------------

Developers should start `here <../devel/testing_nipype.html>`_.


Recommended Software
------------

Strong Recommendations
~~~~~~~~~~~~~~~~~~~~~~

IPython_ 0.10.2 - 1.0.0
  Interactive python environment. This is necessary for some parallel
  components of the pipeline engine.

Matplotlib_ 1.0 - 1.2
  Plotting library

`RDFLib <http://rdflib.readthedocs.org/en/latest/>`_ 4.1
  RDFLibrary required for provenance export as RDF

Sphinx_ 1.1
  Required for building the documentation

`Graphviz <http://www.graphviz.org/>`_
  Required for building the documentation. The python wrapper package (``graphviz``)
  and the program itself both need to be installed.

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
  0.1.2+20110404 or later

Nitime_
  (optional)

ANTS_

MRtrix_ and MRtrix3_

Camino_

Camino2Trackvis_

ConnectomeViewer_

.. include:: ../links_names.txt