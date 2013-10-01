.. _select_files:

==========================
The SelectFiles Interfaces
==========================

Nipype 0.9 introduces a new interface for intelligently finding files on the
disk and feeding them into your workflows: :ref:`SelectFiles
<nipype.interfaces.io.SelectFiles>`. SelectFiles is intended as a simpler
alternative to the :ref:`DataGrabber <nipype.intefaces.io.DataGrabber>`
interface that was discussed previously in :doc:`grabbing_and_sinking`. 

SelectFiles is built on Python `format strings
<http://docs.python.org/2/library/string.html#format-string-syntax>`_, which
are similar to the Python string interpolation feature you are likely already
familiar with, but advantageous in several respects. Format strings allow you
to replace named sections of template strings set off by curly braces (`{}`),
possibly filtered through a set of functions that control how the values are
rendered into the string. As a very basic example, we could write

::

    msg = "This workflow uses {package}"

and then format it with keyword arguments::

    print msg.format(package="FSL")

SelectFiles only requires that you provide templates that can be used to find
your data; the actual formatting happens behind the scenes.

Consider a basic example in which you want to select a T1 image and multple
functional images for a number of subjects. Invoking SelectFiles in this case
is quite straightforward::

    from nipype import SelectFiles
    templates = dict(T1="data/{subject_id}/struct/T1.nii",
                     epi="data/{subject_id}/func/epi_run*.nii")
    sf = SelectFiles(templates)

SelectFiles will take the `templates` dictionary and parse it to determine its
own inputs and oututs. Specifically, each name used in the format spec (here
just `subject_id`) will become an interface input, and each key in the
dictionary (here `T1` and `epi`) will become interface outputs. The `templates`
dictionary thus succinctly links the node inputs to the appropriate outputs.
You'll also note that, as was the case with DataGrabber, you can use basic
`glob <http://docs.python.org/2.7/library/glob.html>`_ syntax to match multiple
files for a given output field. Additionally, any of the conversions outlined in the Python documentation for format strings can be used in the templates.

There are a few other options that help make SelectFiles flexible enough to
deal with any situation where you need to collect data. Like DataGrabber,
SelectFiles has a `base_directory` parameter that allows you to specify a path
that is common to all of the values in the `templates` dictionary.
Additionally, as `glob` does not return a sorted list, there is also a
`sort_filelist` option, taking a boolean, to control whether sorting should be
applied (it is True by default).

The final input is `force_lists`, which controls how SelectFiles behaves in
cases where only a single file matches the template. The default behavior is
that when a template matches multiple files they are returned as a list, while
a single file is returned as a string. There may be situations where you want
to force the outputs to always be returned as a list (for example, you are
writing a workflow that expects to operate on several runs of data, but some of
your subjects only have a single run). In this case, `force_lists` can be used
to tune the outputs of the interface. You can either use a boolean value, which
will be applied to every output the interface has, or you can provide a list of
the output fields that should be coerced to a list. Returning to our basic
example, you may want to ensure that the `epi` files are returned as a list,
but you only ever will have a single `T1` file. In this case, you would do

::

    sf = SelectFiles(templates, force_lists=["epi"])

.. include:: ../links_names.txt
