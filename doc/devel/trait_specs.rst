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





