==========
 Planning
==========

This document will contain the results of different planning
discussions and design meetings we have.  This document will serve as
a more detailed version of our `Roadmap
<https://sourceforge.net/apps/trac/nipy/roadmap>`_.


Milestone 0.2
-------------

* Move common functionality up to CommandLine (from FSLCommandLine and
  SPMCommandLine).  The FSL and SPM interfaces have diverged some,
  pull together the 'best of' functionality and move this to the base
  classes so all interfaces inherit them.  This will also unify the
  interfaces.

* Update the way we hash the *inputs*.  We'll hash the contents of
  image files so we're sure we know when they've changed. And we'll
  change the hash files to store 3 columns of data:

    input_key, input_value, md5hash_if_input_is_file

  For example::

    cwd, nipype-tutorial/workingdir/_subject_id_s1/Realign.spm, 
    flags, None,
    fwhm, None,
    infile, nipype-tutorial/data/s1/f3.nii, a3c80eb0260e7501b1458c462f51c77f

  .. note:: 
  
    File paths should be absolute paths, I shortened them in the
    example above so they'd fit nicely in this doc.
 
  .. note::

    How do we deal with the case where the input_key has multiple
    values?  This is particularly difficult in the case of *infiles*,
    where the value is a list of files.  Do then have a list of
    corresponding hashes?

* FSL Tutorial.  Dav has some analysis pipelines using nipype with FSL
  which he'll turn into a tutorial.

Milestone 0.3
-------------

* Cleanup aggregate_outputs.  Split aggregate_outputs into two
  functions:

  * build output bunch and do checking to see if it's generated
  * fill in output bunch

* Add a dry-run option.  This will allow someone to set up a pipeline
  script and then run it in dry-run mode and then look at the log and
  verify that all the inputs/outputs map correctly, appropriate files
  are generated, etc...  Since the interfaces won't actually execute
  and generate the output files, we'll need to figure out how to
  handle this in the pipeline where the inputs and ouputs are
  validated.

* Cleanup inputs/outputs specifications and semantics.  Also allow a
  generic python object for an interface if a user wants to add their
  own interface object to a pypeline.  (This last bit may not make it
  into 0.3 release.)

* Any changes to 'cwd' param.

* Logging.  Move messages sent to stdout from print statements into a
  log.  Logging detail should be sufficient to use for debugging.  For
  example, it would say like "Called the spm.Realign interface with
  these inputs ... got back these outputs ...".  Not exactly like
  that, but would contain that information.


Somewhere in the future
-----------------------

* Have a *server* object that handles all the data wrangling:
  interface with a database, check if we need to download new data or
  not and if so, handle the download, perform the functionality
  currently in aggregate_outputs (collect output files from one
  pipeline node).

