========================================================
NIPYPE: Neuroimaging in Python: Pipelines and Interfaces
========================================================

.. image:: https://travis-ci.org/nipy/nipype.png?branch=master
  :target: https://travis-ci.org/nipy/nipype

.. image:: https://coveralls.io/repos/nipy/nipype/badge.png
  :target: https://coveralls.io/r/nipy/nipype

.. image:: https://pypip.in/version/nipype/badge.png
    :target: https://pypi.python.org/pypi/nipype/
    :alt: Latest Version

.. image:: https://pypip.in/download/nipype/badge.png
    :target: https://pypi.python.org/pypi/nipype/
    :alt: Downloads

.. image:: https://pypip.in/py_versions/nipype/badge.png
    :target: https://pypi.python.org/pypi/nipype/
    :alt: Supported Python versions

.. image:: https://pypip.in/status/nipype/badge.png
    :target: https://pypi.python.org/pypi/nipype/
    :alt: Development Status

.. image:: https://pypip.in/license/nipype/badge.png
    :target: https://pypi.python.org/pypi/nipype/
    :alt: License

Current neuroimaging software offer users an incredible opportunity to
analyze data using a variety of different algorithms. However, this has
resulted in a heterogeneous collection of specialized applications
without transparent interoperability or a uniform operating interface.

*Nipype*, an open-source, community-developed initiative under the
umbrella of NiPy, is a Python project that provides a uniform interface
to existing neuroimaging software and facilitates interaction between
these packages within a single workflow. Nipype provides an environment
that encourages interactive exploration of algorithms from different
packages (e.g., SPM, FSL, FreeSurfer, AFNI, Slicer), eases the
design of workflows within and between packages, and reduces the
learning curve necessary to use different packages. Nipype is creating a
collaborative platform for neuroimaging software development in a
high-level language and addressing limitations of existing pipeline
systems.

*Nipype* allows you to:

* easily interact with tools from different software packages
* combine processing steps from different software packages
* develop new workflows faster by reusing common steps from old ones
* process data faster by running it in parallel on many cores/machines
* make your research easily reproducible
* share your processing workflows with the community

Documentation
-------------

Please see the ``doc/README.txt`` document for information on our
documentation.

Website
-------

Information specific to NIPYPE is located here::
	    
    http://nipy.org/nipype


Mailing Lists
-------------

For core NIPYPE related issues, please see the developer's list here::
       
       http://projects.scipy.org/mailman/listinfo/nipy-devel

For user NIPYPE related issues, please see the user's list here::

       http://groups.google.com/group/nipy-user

For NIPYPE related issues, please add *NIPYPE* to the subject line


NIPYPE structure
----------------

Currently NIPYPE consists of the following files and directories:

  INSTALL
    NIPYPE prerequisites, installation, development, testing, and 
    troubleshooting.

  README
    This document.

  THANKS
    NIPYPE developers and contributors. Please keep it up to date!!

  LICENSE
    NIPYPE license terms.

  doc/
    Sphinx/reST documentation

  examples/

  nipype/
    Contains the source code.

  setup.py
    Script for building and installing NIPYPE.

License information
-------------------

We use the 3-clause BSD license; the full license is in the file ``LICENSE`` in
the nipype distribution.

There are interfaces to some GNU code but these are entirely optional.

All trademarks referenced herein are property of their respective
holders.

Copyright (c) 2009-2014, NIPY Developers
All rights reserved.
