====================
 Planning - OUTDATED
====================

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
  
  For each interface, create two separate functions. 
      1) outputs() will return a bunch object containing all the possible
      output fields. 

      2) aggregate_outputs() will fill in appropriate fields of the outputs
      bunch and raise exceptions if proper outputs relative to the inputs  are
      not generated.  

  This will get simplified greatly in the trait[let]s version.

* Cleanup inputs/outputs specifications and semantics. 

  Replace all input and output field names consistently. Anytime an input field
  accepts 1 or more inputs, it will have a plural form (e.g., volumes, files,
  surfaces). no in or out prepended because they are already part of a meta
  structure (inputs/outputs).  

  Create a dict to store mappings of old names to new names with version info 

* Changes to 'cwd' param.

  Interfaces will no longer support cwd as an input parameter for run or
  aggregate_outputs. It is the repsonsibility of the user or workflow tools to
  execute the interface in the appropriate working directory. Interfaces will
  use os.getcwd() whenever they need current directory access. 
  
* Logging.  Move messages sent to stdout from print statements into a log.
  Logging detail should be sufficient to use for debugging.   

  Logging is available for pipelines and nodewrapper functionality. Needs to be
  extended to interfaces. This may happen through a generic logging module that
  both the pipeline and interfaces use to generate logs. 

* doc cleanup:

  * fix all tutorials

  * new documentation for pipeline creation, execution and debugging

  * add link to nightly docs/build/regression tests

  * install guide for python novice
  

Functional changes
~~~~~~~~~~~~~~~~~~

mostly to be finished by SG

* extract spm field props limits from spm_config

* add utility nodes to pipeline (combine, split, select)

* add nodes for reading experiment condition and contrast information

* add node for grabbing contrast files

* add nightly regression tests

* finish basic pymvpa searchlight functionality

* clean iterable specification blah.iterables = [(fieldname1, list1),
  (fieldname2, list2), ...] (remove dict/lambda)

* ability to attach pipelines


Structural changes
~~~~~~~~~~~~~~~~~~

* split fsl/spm/freesurfer into multiple files:

  * preprocessing
  * model spec/estimate/analysis
  * dti
  * utils

This still exposes fsl.Smooth as fsl.Smooth instead of fsl.preproc.Smooth.

Administrative changes
~~~~~~~~~~~~~~~~~~~~~~

* create a nipy user mailing list

* create a repo for pipeline scripts

* ease of install (what's our requirements) -pypi packaging


Somewhere in the future
-----------------------

* Have a *server* object that handles all the data wrangling:
  interface with a database, check if we need to download new data or
  not and if so, handle the download, perform the functionality
  currently in aggregate_outputs (collect output files from one
  pipeline node).

* Add a dry-run option.  This will allow someone to set up a pipeline
  script and then run it in dry-run mode and then look at the log and
  verify that all the inputs/outputs map correctly, appropriate files
  are generated, etc...  Since the interfaces won't actually execute
  and generate the output files, we'll need to figure out how to
  handle this in the pipeline where the inputs and ouputs are
  validated.

* ability to run arbitrary interface code from urls

*  Also allow a generic python object for an interface if a user wants to add
   their own interface object to a pypeline.  (This last bit may not make it  
   into 0.3 release.)

* repository for people to dump interfaces

* split input/output spec into separate files 

Packages yet to be wrapped
--------------------------

* AFNI

* Camino

