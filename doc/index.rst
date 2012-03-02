.. list-table::

 * -  .. image:: images/nipype_architecture_overview2.png
         :width: 100 %
   -  .. container::

      Current neuroimaging software offer users an incredible opportunity to
      analyze data using a variety of different algorithms. However, this has
      resulted in a heterogeneous collection of specialized applications
      without transparent interoperability or a uniform operating interface.

      *Nipype*, an open-source, community-developed initiative under the
      umbrella of NiPy_, is a Python project that provides a uniform interface
      to existing neuroimaging software and facilitates interaction between
      these packages within a single workflow. Nipype provides an environment
      that encourages interactive exploration of algorithms from different
      packages (e.g., SPM_, FSL_, FreeSurfer_, Camino_, MRtrix_, AFNI_, Slicer_),
      eases the design of workflows within and between packages, and reduces the
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

.. admonition:: Reference

   Gorgolewski K, Burns CD, Madison C, Clark D, Halchenko YO, Waskom ML, Ghosh SS.
   (2011). Nipype: a flexible, lightweight and extensible neuroimaging data
   processing framework in Python. Front. Neuroimform. 5:13. `Download`__

   __ paper_

.. tip::

   To get started, click Quickstart above. The Links box on the right is
   available on any page of this website.

.. include:: links_names.txt
