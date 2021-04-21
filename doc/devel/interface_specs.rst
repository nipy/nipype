.. _interface_specs:

========================
Interface Specifications
========================

Before you start
----------------

Nipype is maintained by an enthusiastic group of developers, and we're excited to have you join us!
In case of trouble, we encourage you to post on `NeuroStars <https://neurostars.org>`_ with the `nipype` tag.
NeuroStars.org is a platform similar to StackOverflow but dedicated to neuroinformatics.
You can also post on the nipype developers mailing list: http://mail.python.org/mailman/listinfo/neuroimaging.
As we are sharing a mailing list with the nipy community, please add ``[nipype]`` to the message title.
Alternatively, you're welcome to chat with us in the Nipype
`Gitter <https://gitter.im/nipy/nipype>`_ channel or in the
BrainHack `Slack <https://brainhack.slack.com/messages/C1FR76RAL>`_ channel.
(Click `here <https://brainhack-slack-invite.herokuapp.com>`_ to join the Slack workspace.)


Overview
--------

We're using the `Traits <http://docs.enthought.com/traits/traits_user_manual/intro.html>`_
(formerly known as Enthought Traits) package for all of our
inputs and outputs.  Traits allows us to validate user inputs and
provides a mechanism to handle all the *special cases* in a simple and
concise way though metadata.  With the metadata, each input/output can
have an optional set of metadata attributes (described in more detail
below).  The machinery for handling the metadata is located in the
base classes, so all subclasses use the same code to handle these
cases.  This is in contrast to our previous code where every class
defined it's own _parse_inputs, run and aggregate_outputs methods to
handle these cases.  Which of course leads to a dozen different ways
to solve the same problem.

Traits is a big package with a lot to learn in order to take full
advantage of.  But don't be intimidated!  To write a Nipype Trait
Specification, you only need to learn a few of the basics of Traits.
Here are a few starting points in the documentation:

* What are Traits?  The `Introduction in the User Manual
  <http://docs.enthought.com/traits/traits_user_manual/intro.html>`_
  gives a brief description of the functionality traits provides.

* Traits and metadata.  The `second section of the User Manual
  <http://docs.enthought.com/traits/traits_user_manual/defining.html>`_
  gives more details on traits and how to use them.  Plus there a
  section describing metadata, including the metadata all traits have.

* If your interested in more of a *big picture* overview, `Gael wrote
  a good tutorial
  <http://docs.enthought.com/traitsui/tutorials/traits_ui_scientific_app.html>`_
  that shows how to write a scientific application using traits for
  the benefit of the generated UI components.  (For now, Nipype is not
  taking advantage of the generated UI feature of traits.)

Traits version
^^^^^^^^^^^^^^

We're using Traits version 4.x which can be installed from `pypi
<https://pypi.python.org/pypi/traits>`_

More documentation
^^^^^^^^^^^^^^^^^^

Not everything is documented in the User Manual, in those cases the
the `API docs
<http://docs.enthought.com/traits/traits_api_reference/index.html>`_
is your next place to look.

Nipype Interface Specifications
-------------------------------

Each interface class defines two specifications: 1) an InputSpec and
2) an OutputSpec.  Each of these are prefixed with the class name of
the interfaces.  For example, Bet has these specs:

  - BETInputSpec
  - BETOutputSpec

Each of these Specs are classes, derived from a base TraitedSpec class
(more on these below). The InputSpec consists of attributes which
correspond to different parameters for the tool they wrap/interface.
In the case of a command-line tool like Bet, the InputSpec attributes
correspond to the different command-line parameters that can be passed
to Bet.
When an interfaces class is instantiated, the InputSpec is bound to the
``inputs`` attribute of that object.  Below is an example of how the
``inputs`` appear to a user for Bet::

  >>> from nipype.interfaces import fsl
  >>> bet = fsl.BET()
  >>> type(bet.inputs)
  <class 'nipype.interfaces.fsl.preprocess.BETInputSpec'>
  >>> bet.inputs.<TAB>
  bet.inputs.__class__           bet.inputs.center
  bet.inputs.__delattr__         bet.inputs.environ
  bet.inputs.__doc__             bet.inputs.frac
  bet.inputs.__getattribute__    bet.inputs.functional
  bet.inputs.__hash__            bet.inputs.hashval
  bet.inputs.__init__            bet.inputs.infile
  bet.inputs.__new__             bet.inputs.items
  bet.inputs.__reduce__          bet.inputs.mask
  bet.inputs.__reduce_ex__       bet.inputs.mesh
  bet.inputs.__repr__            bet.inputs.nooutput
  bet.inputs.__setattr__         bet.inputs.outfile
  bet.inputs.__str__             bet.inputs.outline
  bet.inputs._generate_handlers  bet.inputs.outputtype
  bet.inputs._get_hashval        bet.inputs.radius
  bet.inputs._hash_infile        bet.inputs.reduce_bias
  bet.inputs._xor_inputs         bet.inputs.skull
  bet.inputs._xor_warn           bet.inputs.threshold
  bet.inputs.args                bet.inputs.vertical_gradient


Each Spec inherits from a parent Spec.  The parent Specs provide
attribute(s) that are common to all child classes.  For example, FSL
InputSpecs inherit from interfaces.fsl.base.FSLTraitedSpec.
FSLTraitedSpec defines an ``outputtype`` attribute, which stores the
file type (NIFTI, NIFTI_PAIR, etc...) for all generated output files.

InputSpec class hierarchy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Below is the current class hierarchy for InputSpec classes (from
base class down to subclasses).:

  ``TraitedSpec``: Nipype's primary base class for all Specs.
  Provides initialization, some nipype-specific methods and any trait
  handlers we define. Inherits from traits.HasTraits.

	  ``BaseInterfaceInputSpec``: Defines inputs common to all
	  Interfaces (``ignore_exception``). If in doubt inherit from this.

	      ``CommandLineInputSpec``: Defines inputs common to all
	      command-line classes (``args`` and ``environ``)

	        ``FSLTraitedSpec``: Defines inputs common to all FSL classes
	        (``outputtype``)

	        ``SPMCommandInputSpec``: Defines inputs common to all SPM classes (``matlab_cmd``, ``path``, and ``mfile``)

	        ``FSTraitedSpec``: Defines inputs common to all FreeSurfer classes
	        (``sbjects_dir``)

	        ``MatlabInputSpec``: Defines inputs common to all Matlab classes (``script``, ``nodesktop``, ``nosplash``, ``logfile``, ``single_comp_thread``, ``mfile``, ``script_file``, and ``paths``)

	        ``SlicerCommandLineInputSpec``: Defines inputs common to all Slicer classes (``module``)

Most developers will only need to code at the the interface-level (i.e. implementing custom class inheriting from one of the above classes).

Output Specs
^^^^^^^^^^^^

The OutputSpec defines the outputs that are generated, or possibly
generated depending on inputs, by the tool.  OutputSpecs inherit from
``interfaces.base.TraitedSpec`` directly.


Controlling outputs to terminal
-------------------------------

It is very likely that the software wrapped within the interface writes
to the standard output or the standard error of the terminal.
Interfaces provide a means to access and retrieve these outputs, by
using the ``terminal_output`` attribute: ::

  import nipype.interfaces.fsl as fsl
  mybet = fsl.BET(from_file='bet-settings.json')
  mybet.terminal_output = 'file_split'

In the example, the ``terminal_output = 'file_split'`` will redirect the
standard output and the standard error to split files (called
``stdout.nipype`` and ``stderr.nipype`` respectively).
The possible values for ``terminal_output`` are:

*file*
    Redirects both standard output and standard error to the same file
    called ``output.nipype``.
    Messages from both streams will be overlapped as they arrive to
    the file.

*file_split*
    Redirects the output streams separately, to ``stdout.nipype``
    and ``stderr.nipype`` respectively, as described in the example.

*file_stdout*
    Only the standard output will be redirected to ``stdout.nipype``
    and the standard error will be discarded.

*file_stderr*
    Only the standard error will be redirected to ``stderr.nipype``
    and the standard output will be discarded.

*stream*
    Both output streams are redirected to the current logger printing
    their messages interleaved and immediately to the terminal.

*allatonce*
    Both output streams will be forwarded to a buffer and stored
    separately in the `runtime` object that the `run()` method returns.
    No files are written nor streams printed out to terminal.

*none*
    Both outputs are discarded

In all cases, except for the ``'none'`` setting of ``terminal_output``,
the ``run()`` method will return a "runtime" object that will contain
the streams in the corresponding properties (``runtime.stdout``
for the standard output, ``runtime.stderr`` for the standard error, and
``runtime.merged`` for both when streams are mixed, eg. when using the
*file* option). ::

  import nipype.interfaces.fsl as fsl
  mybet = fsl.BET(from_file='bet-settings.json')
  mybet.terminal_output = 'file_split'
  ...
  result = mybet.run()
  result.runtime.stdout
  ' ... captured standard output ...'



Traited Attributes
------------------

Each specification attribute is an instance of a Trait class.  These
classes encapsulate many standard Python types like Float and Int, but
with additional behavior like type checking.  (*See the documentation
on traits for more information on these trait types.*) To handle
unique behaviors of our attributes we us traits metadata.  These are
keyword arguments supplied in the initialization of the attributes.
The base classes ``BaseInterface`` and ``CommandLine``
(defined in ``nipype.interfaces.base``) check for the existence/or
value of these metadata and handle the inputs/outputs accordingly.
For example, all mandatory parameters will have the ``mandatory =
True`` metadata::

  class BetInputSpec(FSLTraitedSpec):
    infile = File(exists=True,
                  desc = 'input file to skull strip',
                  argstr='%s', position=0, mandatory=True)


Common
^^^^^^

``exists``
	For files, use ``nipype.interfaces.base.File`` as the trait type.  If
	the file must exist for the tool to execute, specify ``exists = True``
	in the initialization of File (as shown in BetInputSpec above). This
	will trigger the underlying traits code to confirm the file assigned
	to that *input* actually exists.  If it does not exist, the user will
	be presented with an error message::

	    >>> bet.inputs.infile = 'does_not_exist.nii'
	    ------------------------------------------------------------
	    Traceback (most recent call last):
	      File "<ipython console>", line 1, in <module>
	      File "/Users/cburns/local/lib/python2.5/site-packages/nipype/interfaces/base.py", line 76, in validate
	        self.error( object, name, value )
	      File "/Users/cburns/local/lib/python2.5/site-packages/enthought/traits/trait_handlers.py", line 175, in error
	        value )
	    TraitError: The 'infile' trait of a BetInputSpec instance must be a file
	    name, but a value of 'does_not_exist.nii' <type 'str'> was specified.

``hash_files``
	To be used with inputs that are defining output filenames. When this flag
	is set to false any Nipype will not try to hash any files described by this
	input. This is useful to avoid rerunning when the specified output file
	already exists and has changed.

``desc``
	All trait objects have a set of default metadata attributes.  ``desc``
	is one of those and is used as a simple, one-line docstring.  The
	``desc`` is printed when users use the ``help()`` methods.

	**Required:** This metadata is required by all nipype interface
	  classes.

``usedefault``
	Set this metadata to True when the *default value* for the trait type
	of this attribute is an acceptable value.  All trait objects have a
	default value, ``traits.Int`` has a default of ``0``, ``traits.Float``
	has a default of ``0.0``, etc...  You can also define a default value
	when you define the class.  For example, in the code below all objects
	of ``Foo`` will have a default value of 12 for ``x``::

	    >>> import enthought.traits.api as traits
	    >>> class Foo(traits.HasTraits):
	    ...     x = traits.Int(12)
	    ...     y = traits.Int
	    ...
	    >>> foo = Foo()
	    >>> foo.x
	    12
	    >>> foo.y
	    0

	Nipype only passes ``inputs`` on to the underlying package if they
	have been defined (more on this later).  So if you specify
	``usedefault = True``, you are telling the parser to pass the default
	value on to the underlying package.  Let's look at the InputSpec for
	SPM Realign::

	    class RealignInputSpec(BaseInterfaceInputSpec):
	        jobtype = traits.Enum('estwrite', 'estimate', 'write',
	                              desc='one of: estimate, write, estwrite',
	                              usedefault=True)

	Here we've defined ``jobtype`` to be an enumerated trait type,
	``Enum``, which can be set to one of the following: ``estwrite``,
	``estimate``, or ``write``.  In a container, the default is always the
	first element.  So in this case, the default will be ``estwrite``::

	    >>> from nipype.interfaces import spm
	    >>> rlgn = spm.Realign()
	    >>> rlgn.inputs.infile
	    <undefined>
	    >>> rlgn.inputs.jobtype
	    'estwrite'

``xor`` and ``requires``
	Both of these accept a list of trait names. The ``xor`` metadata reflects
	mutually exclusive traits, while the requires metadata reflects traits
	that have to be set together. When a xor-ed trait is set, all other
	traits belonging to the list are set to Undefined. The function
	check_mandatory_inputs ensures that all requirements (both mandatory and
	via the requires metadata are satisfied). These are also reflected in
	the help function.

``copyfile``
	This is metadata for a File or Directory trait that is relevant only in
	the context of wrapping an interface in a `Node` and `MapNode`. `copyfile`
	can be set to either `True` or `False`. `False` indicates that contents
	should be symlinked, while `True` indicates that the contents should be
	copied over.

``min_ver`` and ``max_ver``
    These metadata determine if a particular trait will be available when a
    given version of the underlying interface runs. Note that this check is
    performed at runtime.::

	    class RealignInputSpec(BaseInterfaceInputSpec):
	        jobtype = traits.Enum('estwrite', 'estimate', 'write', min_ver='5',
	                              usedefault=True)
``deprecated`` and ``new_name``
    This is metadata for removing or renaming an input field from a spec.::

        class RealignInputSpec(BaseInterfaceInputSpec):
            jobtype = traits.Enum('estwrite', 'estimate', 'write',
                                  deprecated='0.8',
                                  desc='one of: estimate, write, estwrite',
                                  usedefault=True)

    In the above example this means that the `jobtype` input is deprecated and
    will be removed in version 0.8. Deprecation should be set to two versions
    from current release. Raises `TraitError` after package version crosses the
    deprecation version.

    For inputs that are being renamed, one can specify the new name of the
    field.::

        class RealignInputSpec(BaseInterfaceInputSpec):
            jobtype = traits.Enum('estwrite', 'estimate', 'write',
                                  deprecated='0.8', new_name='job_type',
                                  desc='one of: estimate, write, estwrite',
                                  usedefault=True)
            job_type = traits.Enum('estwrite', 'estimate', 'write',
                                  desc='one of: estimate, write, estwrite',
                                  usedefault=True)

    In the above example, the `jobtype` field is being renamed to `job_type`.
    When `new_name` is provided it must exist as a trait, otherwise an exception
    will be raised.

.. note::

   The version information for `min_ver`, `max_ver` and `deprecated` has to be
   provided as a string. For example, `min_ver='0.1'`.

CommandLine
^^^^^^^^^^^

``argstr``
	The metadata keyword for specifying the format strings
	for the parameters. This was the *value* string in the opt_map
	dictionaries of Nipype 0.2 code.  If we look at the
	``FlirtInputSpec``, the ``argstr`` for the reference file corresponds
	to the argument string I would need to provide with the command-line
	version of ``flirt``::

	    class FlirtInputSpec(FSLTraitedSpec):
	        reference = File(exists = True, argstr = '-ref %s', mandatory = True,
	                         position = 1, desc = 'reference file')

	**Required:** This metadata is required by all command-line interface classes.

``position``
	This metadata is used to specify the position of arguments.  Both
	positive and negative values are accepted.  ``position = 0`` will
	position this argument as the first parameter after the command
	name. ``position = -1`` will position this argument as the last
	parameter, after all other parameters.

``genfile``
	If True, the ``genfile`` metadata specifies that a filename should be
	generated for this parameter *if-and-only-if* the user did not provide
	one.  The nipype convention is to automatically generate output
	filenames when not specified by the user both as a convenience for the
	user and so the pipeline can easily gather the outputs. Requires
	``_gen_filename()`` method to be implemented. This way should be used if the
	desired file name is dependent on some runtime variables (such as file name
	of one of the inputs, or current working directory). In case when it should
	be fixed it's recommended to just use ``usedefault``.

``sep``
	For List traits the string with which elements of the list will be joined.

``name_source``
    Indicates the list of input fields from which the value of the current File
    output variable will be drawn. This input field must be the name of a File.
    Chaining is allowed, meaning that an input field can point to another as
    ``name_source``, which also points as ``name_source`` to a third field.
    In this situation, the templates for substitutions are also accumulated.

``name_template``
    By default a ``%s_generated`` template is used to create the output
    filename. This metadata keyword allows overriding the generated name.

``keep_extension``
     Use this and set it ``True`` if you want the extension from the input to be
     kept.

SPM
^^^

``field``
	name of the structure refered by the SPM job manager

	**Required:** This metadata is required by all SPM-mediated
	  interface classes.


Defining an interface class
---------------------------

Common
^^^^^^

When you define an interface class, you will define these attributes
and methods:

* ``input_spec``: the InputSpec
* ``output_spec``: the OutputSpec
* ``_list_outputs()``: Returns a dictionary containing names of generated files that are expected after package completes execution.  This is used by ``BaseInterface.aggregate_outputs`` to gather all output files for the pipeline.


CommandLine
^^^^^^^^^^^

For command-line interfaces:

* ``_cmd``: the command-line command

If you used genfile:

* ``_gen_filename(name)``:  Generate filename, used for filenames that nipype generates as a convenience for users.  This is for parameters that are required by the wrapped package, but we're generating from some other parameter. For example, ``BET.inputs.outfile`` is required by BET but we can generate the name from ``BET.inputs.infile``.  Override this method in subclass to handle.

And optionally:

* ``_redirect_x``: If set to True it will make Nipype start Xvfb before running the interface and redirect X output to it. This is useful for commandlines that spawn a graphical user interface.

* ``_format_arg(name, spec, value)``: For extra formatting of the input values before passing them to generic ``_parse_inputs()`` method.

For example this is the class definition for Flirt, minus the docstring::

    class FLIRTInputSpec(FSLCommandInputSpec):
        in_file = File(exists=True, argstr='-in %s', mandatory=True,
                       position=0, desc='input file')
        reference = File(exists=True, argstr='-ref %s', mandatory=True,
                         position=1, desc='reference file')
        out_file = File(argstr='-out %s', desc='registered output file',
                        name_source=['in_file'], name_template='%s_flirt',
                        position=2, hash_files=False)
        out_matrix_file = File(argstr='-omat %s',
                               name_source=['in_file'], keep_extension=True,
                               name_template='%s_flirt.mat',
                               desc='output affine matrix in 4x4 asciii format',
                               position=3, hash_files=False)
        out_log = File(name_source=['in_file'], keep_extension=True,
                       requires=['save_log'],
                       name_template='%s_flirt.log', desc='output log')
        ...

    class FLIRTOutputSpec(TraitedSpec):
        out_file = File(exists=True,
                        desc='path/name of registered file (if generated)')
        out_matrix_file = File(exists=True,
                               desc='path/name of calculated affine transform '
                               '(if generated)')
        out_log = File(desc='path/name of output log (if generated)')

    class Flirt(FSLCommand):
        _cmd = 'flirt'
        input_spec = FlirtInputSpec
        output_spec = FlirtOutputSpec

There are two possible output files ``outfile`` and ``outmatrix``,
both of which can be generated if not specified by the user.

Also notice the use of ``self._gen_fname()`` - a FSLCommand helper method for generating filenames (with extensions conforming with FSLOUTPUTTYPE).

See also :doc:`cmd_interface_devel`.

SPM
^^^

For SPM-mediated interfaces:

* ``_jobtype`` and ``_jobname``: special names used used by the SPM job manager. You can find them by saving your batch job as an .m file and looking up the code.

And optionally:

* ``_format_arg(name, spec, value)``: For extra formatting of the input values before passing them to generic ``_parse_inputs()`` method.

Matlab
^^^^^^

See :doc:`matlab_interface_devel`.

Python
^^^^^^

See :doc:`python_interface_devel`.

Undefined inputs
----------------

All the inputs and outputs that were not explicitly set (And do not have a usedefault flag - see above) will have Undefined value. To check if something is defined you have to explicitly call ``isdefiend`` function (comparing to None will not work).

Example of inputs
-----------------

Below we have an example of using Bet.  We can see from the help which
inputs are mandatory and which are optional, along with the one-line
description provided by the ``desc`` metadata::

    >>> from nipype.interfaces import fsl
    >>> fsl.BET.help()
    Inputs
    ------

    Mandatory:
     infile: input file to skull strip

    Optional:
     args: Additional parameters to the command
     center: center of gravity in voxels
     environ: Environment variables (default={})
     frac: fractional intensity threshold
     functional: apply to 4D fMRI data
     mask: create binary mask image
     mesh: generate a vtk mesh brain surface
     nooutput: Don't generate segmented output
     outfile: name of output skull stripped image
     outline: create surface outline image
     outputtype: None
     radius: head radius
     reduce_bias: bias field and neck cleanup
     skull: create skull image
     threshold: apply thresholding to segmented brain image and mask
     vertical_gradient: vertical gradient in fractional intensity threshold (-1, 1)

    Outputs
    -------
    maskfile: path/name of binary brain mask (if generated)
    meshfile: path/name of vtk mesh file (if generated)
    outfile: path/name of skullstripped file
    outlinefile: path/name of outline file (if generated)


Here we create a bet object and specify the required input. We then
check our inputs to see which are defined and which are not::

    >>> bet = fsl.BET(infile = 'f3.nii')
    >>> bet.inputs
    args = <undefined>
    center = <undefined>
    environ = {'FSLOUTPUTTYPE': 'NIFTI_GZ'}
    frac = <undefined>
    functional = <undefined>
    infile = f3.nii
    mask = <undefined>
    mesh = <undefined>
    nooutput = <undefined>
    outfile = <undefined>
    outline = <undefined>
    outputtype = NIFTI_GZ
    radius = <undefined>
    reduce_bias = <undefined>
    skull = <undefined>
    threshold = <undefined>
    vertical_gradient = <undefined>
    >>> bet.cmdline
    'bet f3.nii /Users/cburns/data/nipype/s1/f3_brain.nii.gz'

We also checked the command-line that will be generated when we run
the command and can see the generated output filename
``f3_brain.nii.gz``.
