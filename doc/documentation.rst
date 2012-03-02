.. _documentation:

=============
Documentation
=============

.. htmlonly::

   :Release: |version|
   :Date: |today|


.. container:: doc2

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
