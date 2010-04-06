Trait Specifications
--------------------

We're using the `Enthought Traits
<http://code.enthought.com/projects/traits/>`_ package for all of our
inputs and outputs.  Traits allows us to validate user inputs and
provides a mechanism to handle all the *special cases* in a simple and
concise way though metadata.  With the metadata, each input/output can
have an optional set of metadata attributes (described in more detail
below).  The machinery for handling the metadata is located in the
base classes, so all subclasses use the same code to handle these
cases.  This is in contrast to our previous code where every class
defined it's own _parse_inputs, run and aggregate_outputs methods to
handle these cases.

Traits is a big package.  Below are a few starting points in the
documentation to get a general understanding:

  * `User Manual Introduction <http://code.enthought.com/projects/traits/docs/html/traits_user_manual/intro.html>`_
  * `User Manual Intro to traits and metadata
    <http://code.enthought.com/projects/traits/docs/html/traits_user_manual/defining.html>`_
  * `Gael wrote a good tutorial
    <http://code.enthought.com/projects/traits/docs/html/tutorials/traits_ui_scientific_app.html>`_

We're using Traits version 3.x which can be install as part of `EPD
<http://enthought.com/products/epd.php>`_ or from `pypi
<http://pypi.python.org/pypi/Traits/3.3.0>`_

Not everything is documented in the User Manual, in those cases the
`enthought-dev mailing list
<https://mail.enthought.com/mailman/listinfo/enthought-dev>`_ or the
`API docs
<http://code.enthought.com/projects/files/ETS32_API/enthought.traits.html>`_
is your next place to look.

Specifications
--------------

Each interface subclass defines two specifications: InputSpec and
OutputSpec.  Each of these are prefixed with the class name of the
interfaces.  For example, Bet has these specs:

  - BetInputSpec
  - BetOutputSpec

The InputSpec consists of traited attributes which are the same as the
keys in the opt_map dicts.  These will be the attrs in self.inputs.

FSL InputSpecs inherit from interfaces.fsl.base.FSLTraitedSpec, which
defines an outputtype attr that stores the file type (NIFTI,
NIFTI_PAIR, etc...)  for all generated output files.

OutputSpecs inherit from interfaces.base.TraitedSpec which is the base
class for all traited specifications.  It provides some
initialization, nipype specific methods and any trait handlers.

Traited Attributes
^^^^^^^^^^^^^^^^^^

Individual specification attributes are instances of Trait classes.
These classes encapsulate many standard Python types like Float and
Int, but with additional behavior like type checking.  To handle
unique behaviors of our attributes we us traits metadata.  These are
keyword arguments supplied in the initialization of the attributes.
The base classes NEW_BaseInterface and NEW_CommandLine (in
nipype.interfaces.base) check for the existence/or value of these
metadata and handle the inputs/outputs accordingly.  For example, all
mandatory parameters will have the 'mandatory = True' metadata::

  class BetInputSpec(FSLTraitedSpec):
    infile = File(exists=True,
                  desc = 'input file to skull strip',
                  argstr='%s', position=0, mandatory=True)


File
^^^^

For files, use nipype.interfaces.base.File as the trait type.  If the
file must exist for the package to execute, specify 'exists = True' in
the initialization of File. This will trigger the underlying traits
code to confirm the given file actually exists.

argstr
^^^^^^

Format strings for the parameters, what was the 'value' in the opt_map
dictionaries, are supplied through the 'argstr' metadata.

desc
^^^^

One-line docstrings are given via the 'desc' metadata.  This
information is used in the help() methods.

position
^^^^^^^^

This is used to specify the position of required, positional
arguments.  Both positive and negative values are accepted.  'position
= 0' will position this argument as the first parameter after the
command name. 'position = -1' will position this argument as the last
parameter, after all other parameters.

genfile
^^^^^^^

If True, specifies that a filename should be generated for this
parameter if-and-only-if the user did not provide one.

usedefault
^^^^^^^^^^

Set this metadata to True when the default value for this traited
attribute is an acceptable value.  XXX Add example to clarify.

units
^^^^^

XXX value of units.  How are these used in traits?


NEW_CommandLine._gen_filename
-----------------------------

Generate filename, used for filenames that nipype generates as a
convenience for users.  This is for parameters that are required by
the wrapped package, but we're generating from some other parameter.
For example, Bet.inputs.outfile is required by bet but we can generate
the name from Bet.inputs.infile.  Override this method in subclass to
handle.

NEW_FSLCommand._gen_fname
-------------------------

Generates filenames for FSL commands making sure to use the
appropriate file extension.  Used by subclasses but should not be
overridden.

NEW_Interface._list_outputs
---------------------------

Returns a dictionary containing names of generated files that are
expected after package completes execution.  This is used by
NEW_BaseInterface.aggregate_outputs to gather all output files for the
pipeline.





