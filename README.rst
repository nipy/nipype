========================================================
NIPYPE: Neuroimaging in Python: Pipelines and Interfaces
========================================================

.. image:: https://travis-ci.org/nipy/nipype.svg?branch=master
  :target: https://travis-ci.org/nipy/nipype

.. image:: https://circleci.com/gh/nipy/nipype/tree/master.svg?style=svg
  :target: https://circleci.com/gh/nipy/nipype/tree/master

.. image:: https://codecov.io/gh/nipy/nipype/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/nipy/nipype

.. image:: https://api.codacy.com/project/badge/Grade/452bfc0d4de342c99b177d2c29abda7b
  :target: https://www.codacy.com/app/nipype/nipype?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=nipy/nipype&amp;utm_campaign=Badge_Grade

.. image:: https://img.shields.io/pypi/v/nipype.svg
    :target: https://pypi.python.org/pypi/nipype/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/nipype.svg
    :target: https://pypi.python.org/pypi/nipype/
    :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/status/nipype.svg
    :target: https://pypi.python.org/pypi/nipype/
    :alt: Development Status

.. image:: https://img.shields.io/pypi/l/nipype.svg
    :target: https://pypi.python.org/pypi/nipype/
    :alt: License

.. image:: https://img.shields.io/badge/gitter-join%20chat%20%E2%86%92-brightgreen.svg?style=flat
    :target: http://gitter.im/nipy/nipype
    :alt: Chat

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.596855.svg
   :target: https://doi.org/10.5281/zenodo.596855
   :alt: Citable DOI

Current neuroimaging software offer users an incredible opportunity to
analyze data using a variety of different algorithms. However, this has
resulted in a heterogeneous collection of specialized applications
without transparent interoperability or a uniform operating interface.

*Nipype*, an open-source, community-developed initiative under the
umbrella of NiPy, is a Python project that provides a uniform interface
to existing neuroimaging software and facilitates interaction between
these packages within a single workflow. Nipype provides an environment
that encourages interactive exploration of algorithms from different
packages (e.g., SPM, FSL, FreeSurfer, AFNI, Slicer, ANTS), eases the
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

Information specific to Nipype is located here::

    http://nipy.org/nipype


Support and Communication
-------------------------

If you have a problem or would like to ask a question about how to do something in Nipype please open an issue to
`NeuroStars.org <http://neurostars.org>`_ with a *nipype* tag. `NeuroStars.org <http://neurostars.org>`_  is a
platform similar to StackOverflow but dedicated to neuroinformatics.

To participate in the Nipype development related discussions please use the following mailing list::

       http://mail.python.org/mailman/listinfo/neuroimaging

Please add *[nipype]* to the subject line when posting on the mailing list.

You can even hangout with the Nipype developers in their
`Gitter <https://gitter.im/nipy/nipype>`_ channel or in the BrainHack `Slack <https://brainhack.slack.com/messages/C1FR76RAL>`_ channel. (Click `here <https://brainhack-slack-invite.herokuapp.com>`_ to join the Slack workspace.)


Contributing to the project
---------------------------

If you'd like to contribute to the project please read our `guidelines <https://github.com/nipy/nipype/blob/master/CONTRIBUTING.md>`_. Please also read through our `code of conduct <https://github.com/nipy/nipype/blob/master/CODE_OF_CONDUCT.md>`_.
