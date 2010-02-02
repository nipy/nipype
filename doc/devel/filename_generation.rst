==========================
 Auto-generated filenames
==========================

In refactoring the inputs in the traitlets branch I'm working through
the different ways that filenames are generated and want to make sure
the interface is consistent.  The notes below are all using fsl.Bet as
that's the first class we're Traiting. Other interface classes may
handle this differently, but should agree on a convention and apply it
across all Interfaces (if possible).

Current Rules
-------------

These rules are for fsl.Bet, but it appears they are the same for all
fsl and spm Interfaces.

Bet has two mandatory parameters, ``infile`` and ``outfile``.  These
are the rules for how they are handled in different use cases.

1. If ``infile`` or ``outfile`` are absolute paths, they are used
   as-is and never changed.  This allows users to override any
   filename/path generation.

2. If ``outfile`` is not specified, a filename is generated.

3. Generated filenames (at least for ``outfile``) are based on:

  * ``infile``, the filename minus the extensions.

  * A suffix specified by the Interface. For example Bet uses
    *_brain* suffix.

  * The current working directory, os.getcwd().  Example:

    If ``infile`` == 'foo.nii' and the cwd is ``/home/cburns`` then
    generated ``outfile`` for Bet will be
    ``/home/cburns/foo_brain.nii.gz``

4. If ``outfile`` is not an absolute path, for instance just a
   filename, the absolute path is generated using
   ``os.path.realpath``. This absolute path is needed to make sure the
   packages (Bet in this case) write the output file to a location of
   our choosing.  The generated absolute path is only used in the
   ``cmdline`` at runtime and does __not__ overwrite the class attr
   ``self.inputs.outfile``.  It is generated only when the ``cmdline``
   is invoked.


Walking through some examples
-----------------------------

In this example we assign ``infile`` directly but ``outfile`` is
generated in ``Bet._parse_inputs`` based on ``infile``.  The generated
``outfile`` is only used in the cmdline at runtime and not stored in
``self.inputs.outfile``.  This seems correct.

.. sourcecode:: ipython

    In [15]: from nipype.interfaces import fsl

    In [16]: mybet = fsl.Bet()

    In [17]: mybet.inputs.infile = 'foo.nii'

    In [18]: res = mybet.run()

    In [19]: res.runtime.cmdline
    Out[19]: 'bet foo.nii /Users/cburns/src/nipy-sf/nipype/trunk/nipype/interfaces/tests/foo_brain.nii.gz'

    In [21]: mybet.inputs
    Out[21]: Bunch(center=None, flags=None, frac=None, functional=None,
    infile='foo.nii', mask=None, mesh=None, nooutput=None, outfile=None,
    outline=None, radius=None, reduce_bias=None, skull=None, threshold=None,
    verbose=None, vertical_gradient=None)

    In [24]: mybet.cmdline
    Out[24]: 'bet foo.nii /Users/cburns/src/nipy-sf/nipype/trunk/nipype/interfaces/tests/foo_brain.nii.gz'

    In [25]: mybet.inputs.outfile

    In [26]: mybet.inputs.infile
    Out[26]: 'foo.nii'


We get the same behavior here when we assign ``infile`` at initialization:

.. sourcecode:: ipython

    In [28]: mybet = fsl.Bet(infile='foo.nii')

    In [29]: mybet.cmdline
    Out[29]: 'bet foo.nii /Users/cburns/src/nipy-sf/nipype/trunk/nipype/interfaces/tests/foo_brain.nii.gz'

    In [30]: mybet.inputs
    Out[30]: Bunch(center=None, flags=None, frac=None, functional=None,
    infile='foo.nii', mask=None, mesh=None, nooutput=None, outfile=None,
    outline=None, radius=None, reduce_bias=None, skull=None, threshold=None,
    verbose=None, vertical_gradient=None)

    In [31]: res = mybet.run()

    In [32]: res.runtime.cmdline
    Out[32]: 'bet foo.nii /Users/cburns/src/nipy-sf/nipype/trunk/nipype/interfaces/tests/foo_brain.nii.gz'


Here we specify absolute paths for both ``infile`` and
``outfile``. The command line's look as expected:

.. sourcecode:: ipython

    In [53]: import os

    In [54]: mybet = fsl.Bet()

    In [55]: mybet.inputs.infile = os.path.join('/Users/cburns/tmp/junk', 'foo.nii')
    In [56]: mybet.inputs.outfile = os.path.join('/Users/cburns/tmp/junk', 'bar.nii')

    In [57]: mybet.cmdline
    Out[57]: 'bet /Users/cburns/tmp/junk/foo.nii /Users/cburns/tmp/junk/bar.nii'

    In [58]: res = mybet.run()

    In [59]: res.runtime.cmdline
    Out[59]: 'bet /Users/cburns/tmp/junk/foo.nii /Users/cburns/tmp/junk/bar.nii'


Here passing in a new ``outfile`` in the ``run`` method will update
``mybet.inputs.outfile`` to the passed in value.  Should this be the
case?

.. sourcecode:: ipython

    In [110]: mybet = fsl.Bet(infile='foo.nii', outfile='bar.nii')

    In [111]: mybet.inputs.outfile
    Out[111]: 'bar.nii'

    In [112]: mybet.cmdline
    Out[112]: 'bet foo.nii /Users/cburns/src/nipy-sf/nipype/trunk/nipype/interfaces/tests/bar.nii'

    In [113]: res = mybet.run(outfile = os.path.join('/Users/cburns/tmp/junk', 'not_bar.nii'))

    In [114]: mybet.inputs.outfile
    Out[114]: '/Users/cburns/tmp/junk/not_bar.nii'

    In [115]: mybet.cmdline
    Out[115]: 'bet foo.nii /Users/cburns/tmp/junk/not_bar.nii'


In this case we provide ``outfile`` but not as an absolue path, so the
absolue path is generated and used for the ``cmdline`` when run, but
``mybet.inputs.outfile`` is not updated with the absolute path.

.. sourcecode:: ipython

    In [74]: mybet = fsl.Bet(infile='foo.nii', outfile='bar.nii')

    In [75]: mybet.inputs.outfile
    Out[75]: 'bar.nii'

    In [76]: mybet.cmdline
    Out[76]: 'bet foo.nii /Users/cburns/src/nipy-sf/nipype/trunk/nipype/interfaces/tests/bar.nii'

    In [77]: res = mybet.run()

    In [78]: res.runtime.cmdline
    Out[78]: 'bet foo.nii /Users/cburns/src/nipy-sf/nipype/trunk/nipype/interfaces/tests/bar.nii'

    In [80]: res.interface.inputs.outfile
    Out[80]: 'bar.nii'

