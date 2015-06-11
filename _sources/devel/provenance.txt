================
W3C PROV support
================

Overview
--------

We're using the the `W3C PROV data model <http://www.w3.org/TR/prov-dm/>`_ to
capture and represent provenance in Nipype.

For an overview see:

`PROV-DM overview <http://slideviewer.herokuapp.com/url/raw.github.com/ni-/notebooks/master/NIDMIntro.ipynb>`_

Each interface writes out a provenance.json (currently prov-json) or
provenance.rdf (if rdflib is available) file. The workflow engine can also
write out a provenance of the workflow if instructed.

This is very much an experimental feature as we continue to refine how exactly
the provenance should be stored and how such information can be used for
reporting or reconstituting workflows. By default provenance writing is disabled
for the 0.9 release, to enable insert the following code at the top of your
script::

   >>> from nipype import config
   >>> config.enable_provenance()
