.. _documentation:

=============
Documentation
=============

.. htmlonly::

   :Release: |version|
   :Date: |today|

Previous versions: `1.1.0 <http://nipype.readthedocs.io/en/1.1.0/>`_ `1.0.4 <http://nipype.readthedocs.io/en/1.0.4/>`_


.. container:: doc2

  .. admonition:: Michael Notter's Nipype guide

    Be sure to read `Michael's excellent tutorials <https://miykael.github.io/nipype_tutorial/>`_.

  .. admonition:: Guides

    .. hlist::
       :columns: 2

       * User

         .. toctree::
            :maxdepth: 2

            users/index

         .. toctree::
            :maxdepth: 1

            changes

       * Developer

         .. toctree::
            :maxdepth: 2

            api/index
            devel/index


  .. admonition:: Interfaces, Workflows and Examples

    .. hlist::
       :columns: 2

       * Workflows

         .. toctree::
            :maxdepth: 1
            :glob:

            interfaces/generated/*workflows*
       * Examples

         .. toctree::
            :maxdepth: 1
            :glob:

            users/examples/*
       * Interfaces

         .. toctree::
            :maxdepth: 1
            :glob:

            interfaces/generated/*algorithms*
            interfaces/generated/*interfaces*

.. include:: links_names.txt
