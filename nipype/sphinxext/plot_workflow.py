#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
:mod:`nipype.sphinxext.plot_workflow` -- Workflow plotting extension
====================================================================


A directive for including a nipype workflow graph in a Sphinx document.

This code is forked from the plot_figure sphinx extension of matplotlib.

By default, in HTML output, `workflow` will include a .png file with a
link to a high-res .png.  In LaTeX output, it will include a
.pdf.
The source code for the workflow may be included as **inline content** to
the directive `workflow`::

  .. workflow ::
      :graph2use: flat
      :simple_form: no

      from niflow.nipype1.workflows.dmri.camino.connectivity_mapping import create_connectivity_pipeline
      wf = create_connectivity_pipeline()


For example, the following graph has been generated inserting the previous
code block in this documentation:

.. workflow ::
  :graph2use: flat
  :simple_form: no

  from niflow.nipype1.workflows.dmri.camino.connectivity_mapping import create_connectivity_pipeline
  wf = create_connectivity_pipeline()


Options
-------

The ``workflow`` directive supports the following options:
    graph2use : {'hierarchical', 'colored', 'flat', 'orig', 'exec'}
        Specify the type of graph to be generated.
    simple_form: bool
        Whether the graph will be in detailed or simple form.
    format : {'python', 'doctest'}
        Specify the format of the input
    include-source : bool
        Whether to display the source code. The default can be changed
        using the `workflow_include_source` variable in conf.py
    encoding : str
        If this source file is in a non-UTF8 or non-ASCII encoding,
        the encoding must be specified using the `:encoding:` option.
        The encoding will not be inferred using the ``-*- coding -*-``
        metacomment.

Additionally, this directive supports all of the options of the
`image` directive, except for `target` (since workflow will add its own
target).  These include `alt`, `height`, `width`, `scale`, `align` and
`class`.

Configuration options
---------------------

The workflow directive has the following configuration options:
    graph2use
        Select a graph type to use
    simple_form
        determines if the node name shown in the visualization is either of the form nodename
        (package) when set to True or nodename.Class.package when set to False.
    wf_include_source
        Default value for the include-source option
    wf_html_show_source_link
        Whether to show a link to the source in HTML.
    wf_pre_code
        Code that should be executed before each workflow.
    wf_basedir
        Base directory, to which ``workflow::`` file names are relative
        to.  (If None or empty, file names are relative to the
        directory where the file containing the directive is.)
    wf_formats
        File formats to generate. List of tuples or strings::
            [(suffix, dpi), suffix, ...]
        that determine the file format and the DPI. For entries whose
        DPI was omitted, sensible defaults are chosen. When passing from
        the command line through sphinx_build the list should be passed as
        suffix:dpi,suffix:dpi, ....
    wf_html_show_formats
        Whether to show links to the files in HTML.
    wf_rcparams
        A dictionary containing any non-standard rcParams that should
        be applied before each workflow.
    wf_apply_rcparams
        By default, rcParams are applied when `context` option is not used in
        a workflow directive.  This configuration option overrides this behavior
        and applies rcParams before each workflow.
    wf_working_directory
        By default, the working directory will be changed to the directory of
        the example, so the code can get at its data files, if any.  Also its
        path will be added to `sys.path` so it can import any helper modules
        sitting beside it.  This configuration option can be used to specify
        a central directory (also added to `sys.path`) where data files and
        helper modules for all code are located.
    wf_template
        Provide a customized template for preparing restructured text.

"""
import sys
import os
import shutil
import io
import re
import textwrap
from os.path import relpath
from errno import EEXIST
import traceback

missing_imports = []
try:
    from docutils.parsers.rst import directives, Directive
    from docutils.parsers.rst.directives.images import Image

    align = Image.align
except ImportError as e:
    missing_imports = [str(e)]

try:
    # Sphinx depends on either Jinja or Jinja2
    import jinja2

    def format_template(template, **kw):
        return jinja2.Template(template).render(**kw)


except ImportError as e:
    missing_imports.append(str(e))
    try:
        import jinja

        def format_template(template, **kw):
            return jinja.from_string(template, **kw)

        missing_imports.pop()
    except ImportError as e:
        missing_imports.append(str(e))


def _option_boolean(arg):
    if not arg or not arg.strip():
        # no argument given, assume used as a flag
        return True
    elif arg.strip().lower() in ("no", "0", "false"):
        return False
    elif arg.strip().lower() in ("yes", "1", "true"):
        return True
    else:
        raise ValueError('"%s" unknown boolean' % arg)


def _option_graph2use(arg):
    return directives.choice(arg, ("hierarchical", "colored", "flat", "orig", "exec"))


def _option_context(arg):
    if arg in [None, "reset", "close-figs"]:
        return arg
    raise ValueError("argument should be None or 'reset' or 'close-figs'")


def _option_format(arg):
    return directives.choice(arg, ("python", "doctest"))


def _option_align(arg):
    return directives.choice(
        arg, ("top", "middle", "bottom", "left", "center", "right")
    )


def mark_wf_labels(app, document):
    """
    To make graphs referenceable, we need to move the reference from
    the "htmlonly" (or "latexonly") node to the actual figure node
    itself.
    """
    for name, explicit in list(document.nametypes.items()):
        if not explicit:
            continue
        labelid = document.nameids[name]
        if labelid is None:
            continue
        node = document.ids[labelid]
        if node.tagname in ("html_only", "latex_only"):
            for n in node:
                if n.tagname == "figure":
                    sectname = name
                    for c in n:
                        if c.tagname == "caption":
                            sectname = c.astext()
                            break

                    node["ids"].remove(labelid)
                    node["names"].remove(name)
                    n["ids"].append(labelid)
                    n["names"].append(name)
                    document.settings.env.labels[name] = (
                        document.settings.env.docname,
                        labelid,
                        sectname,
                    )
                    break


class WorkflowDirective(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 2
    final_argument_whitespace = False
    option_spec = {
        "alt": directives.unchanged,
        "height": directives.length_or_unitless,
        "width": directives.length_or_percentage_or_unitless,
        "scale": directives.nonnegative_int,
        "align": _option_align,
        "class": directives.class_option,
        "include-source": _option_boolean,
        "format": _option_format,
        "context": _option_context,
        "nofigs": directives.flag,
        "encoding": directives.encoding,
        "graph2use": _option_graph2use,
        "simple_form": _option_boolean,
    }

    def run(self):
        if missing_imports:
            raise ImportError("\n".join(missing_imports))

        document = self.state_machine.document
        config = document.settings.env.config
        nofigs = "nofigs" in self.options

        formats = get_wf_formats(config)
        default_fmt = formats[0][0]

        graph2use = self.options.get("graph2use", "hierarchical")
        simple_form = self.options.get("simple_form", True)

        self.options.setdefault("include-source", config.wf_include_source)
        keep_context = "context" in self.options
        context_opt = None if not keep_context else self.options["context"]

        rst_file = document.attributes["source"]
        rst_dir = os.path.dirname(rst_file)

        if len(self.arguments):
            if not config.wf_basedir:
                source_file_name = os.path.join(
                    setup.app.builder.srcdir, directives.uri(self.arguments[0])
                )
            else:
                source_file_name = os.path.join(
                    setup.confdir, config.wf_basedir, directives.uri(self.arguments[0])
                )

            # If there is content, it will be passed as a caption.
            caption = "\n".join(self.content)

            # If the optional function name is provided, use it
            if len(self.arguments) == 2:
                function_name = self.arguments[1]
            else:
                function_name = None

            with io.open(source_file_name, "r", encoding="utf-8") as fd:
                code = fd.read()
            output_base = os.path.basename(source_file_name)
        else:
            source_file_name = rst_file
            code = textwrap.dedent("\n".join([str(c) for c in self.content]))
            counter = document.attributes.get("_wf_counter", 0) + 1
            document.attributes["_wf_counter"] = counter
            base, _ = os.path.splitext(os.path.basename(source_file_name))
            output_base = "%s-%d.py" % (base, counter)
            function_name = None
            caption = ""

        base, source_ext = os.path.splitext(output_base)
        if source_ext in (".py", ".rst", ".txt"):
            output_base = base
        else:
            source_ext = ""

        # ensure that LaTeX includegraphics doesn't choke in foo.bar.pdf filenames
        output_base = output_base.replace(".", "-")

        # is it in doctest format?
        is_doctest = contains_doctest(code)
        if "format" in self.options:
            if self.options["format"] == "python":
                is_doctest = False
            else:
                is_doctest = True

        # determine output directory name fragment
        source_rel_name = relpath(source_file_name, setup.confdir)
        source_rel_dir = os.path.dirname(source_rel_name)
        while source_rel_dir.startswith(os.path.sep):
            source_rel_dir = source_rel_dir[1:]

        # build_dir: where to place output files (temporarily)
        build_dir = os.path.join(
            os.path.dirname(setup.app.doctreedir), "wf_directive", source_rel_dir
        )
        # get rid of .. in paths, also changes pathsep
        # see note in Python docs for warning about symbolic links on Windows.
        # need to compare source and dest paths at end
        build_dir = os.path.normpath(build_dir)

        if not os.path.exists(build_dir):
            os.makedirs(build_dir)

        # output_dir: final location in the builder's directory
        dest_dir = os.path.abspath(
            os.path.join(setup.app.builder.outdir, source_rel_dir)
        )
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)  # no problem here for me, but just use built-ins

        # how to link to files from the RST file
        dest_dir_link = os.path.join(
            relpath(setup.confdir, rst_dir), source_rel_dir
        ).replace(os.path.sep, "/")
        try:
            build_dir_link = relpath(build_dir, rst_dir).replace(os.path.sep, "/")
        except ValueError:
            # on Windows, relpath raises ValueError when path and start are on
            # different mounts/drives
            build_dir_link = build_dir
        source_link = dest_dir_link + "/" + output_base + source_ext

        # make figures
        try:
            results = render_figures(
                code,
                source_file_name,
                build_dir,
                output_base,
                keep_context,
                function_name,
                config,
                graph2use,
                simple_form,
                context_reset=context_opt == "reset",
                close_figs=context_opt == "close-figs",
            )
            errors = []
        except GraphError as err:
            reporter = self.state.memo.reporter
            sm = reporter.system_message(
                2,
                "Exception occurred in plotting %s\n from %s:\n%s"
                % (output_base, source_file_name, err),
                line=self.lineno,
            )
            results = [(code, [])]
            errors = [sm]

        # Properly indent the caption
        caption = "\n".join("      " + line.strip() for line in caption.split("\n"))

        # generate output restructuredtext
        total_lines = []
        for j, (code_piece, images) in enumerate(results):
            if self.options["include-source"]:
                if is_doctest:
                    lines = [""]
                    lines += [row.rstrip() for row in code_piece.split("\n")]
                else:
                    lines = [".. code-block:: python", ""]
                    lines += ["    %s" % row.rstrip() for row in code_piece.split("\n")]
                source_code = "\n".join(lines)
            else:
                source_code = ""

            if nofigs:
                images = []

            opts = [
                ":%s: %s" % (key, val)
                for key, val in list(self.options.items())
                if key in ("alt", "height", "width", "scale", "align", "class")
            ]

            only_html = ".. only:: html"
            only_latex = ".. only:: latex"
            only_texinfo = ".. only:: texinfo"

            # Not-None src_link signals the need for a source link in the generated
            # html
            if j == 0 and config.wf_html_show_source_link:
                src_link = source_link
            else:
                src_link = None

            result = format_template(
                config.wf_template or TEMPLATE,
                default_fmt=default_fmt,
                dest_dir=dest_dir_link,
                build_dir=build_dir_link,
                source_link=src_link,
                multi_image=len(images) > 1,
                only_html=only_html,
                only_latex=only_latex,
                only_texinfo=only_texinfo,
                options=opts,
                images=images,
                source_code=source_code,
                html_show_formats=config.wf_html_show_formats and len(images),
                caption=caption,
            )

            total_lines.extend(result.split("\n"))
            total_lines.extend("\n")

        if total_lines:
            self.state_machine.insert_input(total_lines, source=source_file_name)

        # copy image files to builder's output directory, if necessary
        os.makedirs(dest_dir, exist_ok=True)
        for code_piece, images in results:
            for img in images:
                for fn in img.filenames():
                    destimg = os.path.join(dest_dir, os.path.basename(fn))
                    if fn != destimg:
                        shutil.copyfile(fn, destimg)

        # copy script (if necessary)
        target_name = os.path.join(dest_dir, output_base + source_ext)
        with io.open(target_name, "w", encoding="utf-8") as f:
            if source_file_name == rst_file:
                code_escaped = unescape_doctest(code)
            else:
                code_escaped = code
            f.write(code_escaped)

        return errors


def setup(app):
    setup.app = app
    setup.config = app.config
    setup.confdir = app.confdir

    app.add_directive("workflow", WorkflowDirective)
    app.add_config_value("graph2use", "hierarchical", "html")
    app.add_config_value("simple_form", True, "html")
    app.add_config_value("wf_pre_code", None, True)
    app.add_config_value("wf_include_source", False, True)
    app.add_config_value("wf_html_show_source_link", True, True)
    app.add_config_value("wf_formats", ["png", "svg", "pdf"], True)
    app.add_config_value("wf_basedir", None, True)
    app.add_config_value("wf_html_show_formats", True, True)
    app.add_config_value("wf_rcparams", {}, True)
    app.add_config_value("wf_apply_rcparams", False, True)
    app.add_config_value("wf_working_directory", None, True)
    app.add_config_value("wf_template", None, True)

    app.connect("doctree-read", mark_wf_labels)

    metadata = {"parallel_read_safe": True, "parallel_write_safe": True}
    return metadata


# ------------------------------------------------------------------------------
# Doctest handling
# ------------------------------------------------------------------------------


def contains_doctest(text):
    try:
        # check if it's valid Python as-is
        compile(text, "<string>", "exec")
        return False
    except SyntaxError:
        pass
    r = re.compile(r"^\s*>>>", re.M)
    m = r.search(text)
    return bool(m)


def unescape_doctest(text):
    """
    Extract code from a piece of text, which contains either Python code
    or doctests.
    """
    if not contains_doctest(text):
        return text

    code = ""
    for line in text.split("\n"):
        m = re.match(r"^\s*(>>>|\.\.\.) (.*)$", line)
        if m:
            code += m.group(2) + "\n"
        elif line.strip():
            code += "# " + line.strip() + "\n"
        else:
            code += "\n"
    return code


def remove_coding(text):
    """
    Remove the coding comment, which exec doesn't like.
    """
    sub_re = re.compile(r"^#\s*-\*-\s*coding:\s*.*-\*-$", flags=re.MULTILINE)
    return sub_re.sub("", text)


# ------------------------------------------------------------------------------
# Template
# ------------------------------------------------------------------------------

TEMPLATE = """
{{ source_code }}
{{ only_html }}
   {% for img in images %}
   .. figure:: {{ build_dir }}/{{ img.basename }}.{{ default_fmt }}
      {% for option in options -%}
      {{ option }}
      {% endfor %}
      {% if html_show_formats and multi_image -%}
        (
        {%- for fmt in img.formats -%}
        {%- if not loop.first -%}, {% endif -%}
        `{{ fmt }} <{{ dest_dir }}/{{ img.basename }}.{{ fmt }}>`__
        {%- endfor -%}
        )
      {%- endif -%}
      {{ caption }}
   {% endfor %}
   {% if source_link or (html_show_formats and not multi_image) %}
   (
   {%- if source_link -%}
   `Source code <{{ source_link }}>`__
   {%- endif -%}
   {%- if html_show_formats and not multi_image -%}
     {%- for img in images -%}
       {%- for fmt in img.formats -%}
         {%- if source_link or not loop.first -%}, {% endif -%}
         `{{ fmt }} <{{ dest_dir }}/{{ img.basename }}.{{ fmt }}>`__
       {%- endfor -%}
     {%- endfor -%}
   {%- endif -%}
   )
   {% endif %}
{{ only_latex }}
   {% for img in images %}
   {% if 'pdf' in img.formats -%}
   .. figure:: {{ build_dir }}/{{ img.basename }}.pdf
      {% for option in options -%}
      {{ option }}
      {% endfor %}
      {{ caption }}
   {% endif -%}
   {% endfor %}
{{ only_texinfo }}
   {% for img in images %}
   .. image:: {{ build_dir }}/{{ img.basename }}.png
      {% for option in options -%}
      {{ option }}
      {% endfor %}
   {% endfor %}
"""

exception_template = """
.. htmlonly::
   [`source code <%(linkdir)s/%(basename)s.py>`__]
Exception occurred rendering plot.
"""

# the context of the plot for all directives specified with the
# :context: option
wf_context = dict()


class ImageFile(object):
    def __init__(self, basename, dirname):
        self.basename = basename
        self.dirname = dirname
        self.formats = []

    def filename(self, fmt):
        return os.path.join(self.dirname, "%s.%s" % (self.basename, fmt))

    def filenames(self):
        return [self.filename(fmt) for fmt in self.formats]


def out_of_date(original, derived):
    """
    Returns True if derivative is out-of-date wrt original,
    both of which are full file paths.
    """
    return not os.path.exists(derived) or (
        os.path.exists(original)
        and os.stat(derived).st_mtime < os.stat(original).st_mtime
    )


class GraphError(RuntimeError):
    pass


def run_code(code, code_path, ns=None, function_name=None):
    """
    Import a Python module from a path, and run the function given by
    name, if function_name is not None.
    """

    # Change the working directory to the directory of the example, so
    # it can get at its data files, if any.  Add its path to sys.path
    # so it can import any helper modules sitting beside it.
    pwd = str(os.getcwd())
    old_sys_path = list(sys.path)
    if setup.config.wf_working_directory is not None:
        try:
            os.chdir(setup.config.wf_working_directory)
        except OSError as err:
            raise OSError(
                str(err) + "\n`wf_working_directory` option in"
                "Sphinx configuration file must be a valid "
                "directory path"
            )
        except TypeError as err:
            raise TypeError(
                str(err) + "\n`wf_working_directory` option in "
                "Sphinx configuration file must be a string or "
                "None"
            )
        sys.path.insert(0, setup.config.wf_working_directory)
    elif code_path is not None:
        dirname = os.path.abspath(os.path.dirname(code_path))
        os.chdir(dirname)
        sys.path.insert(0, dirname)

    # Reset sys.argv
    old_sys_argv = sys.argv
    sys.argv = [code_path]

    # Redirect stdout
    stdout = sys.stdout
    sys.stdout = io.StringIO()

    # Assign a do-nothing print function to the namespace.  There
    # doesn't seem to be any other way to provide a way to (not) print
    # that works correctly across Python 2 and 3.
    def _dummy_print(*arg, **kwarg):
        pass

    try:
        try:
            code = unescape_doctest(code)
            if ns is None:
                ns = {}
            if not ns:
                if setup.config.wf_pre_code is not None:
                    exec(str(setup.config.wf_pre_code), ns)
            ns["print"] = _dummy_print
            if "__main__" in code:
                exec("__name__ = '__main__'", ns)
            code = remove_coding(code)
            exec(code, ns)
            if function_name is not None:
                exec(function_name + "()", ns)
        except (Exception, SystemExit) as err:
            raise GraphError(traceback.format_exc())
    finally:
        os.chdir(pwd)
        sys.argv = old_sys_argv
        sys.path[:] = old_sys_path
        sys.stdout = stdout
    return ns


def get_wf_formats(config):
    default_dpi = {"png": 80, "hires.png": 200, "pdf": 200}
    formats = []
    wf_formats = config.wf_formats
    if isinstance(wf_formats, (str, bytes)):
        # String Sphinx < 1.3, Split on , to mimic
        # Sphinx 1.3 and later. Sphinx 1.3 always
        # returns a list.
        wf_formats = wf_formats.split(",")
    for fmt in wf_formats:
        if isinstance(fmt, (str, bytes)):
            if ":" in fmt:
                suffix, dpi = fmt.split(":")
                formats.append((str(suffix), int(dpi)))
            else:
                formats.append((fmt, default_dpi.get(fmt, 80)))
        elif isinstance(fmt, (tuple, list)) and len(fmt) == 2:
            formats.append((str(fmt[0]), int(fmt[1])))
        else:
            raise GraphError('invalid image format "%r" in wf_formats' % fmt)
    return formats


def render_figures(
    code,
    code_path,
    output_dir,
    output_base,
    context,
    function_name,
    config,
    graph2use,
    simple_form,
    context_reset=False,
    close_figs=False,
):
    """
    Run a nipype workflow creation script and save the graph in *output_dir*.
    Save the images under *output_dir* with file names derived from
    *output_base*
    """
    formats = get_wf_formats(config)
    ns = wf_context if context else {}
    if context_reset:
        wf_context.clear()

    run_code(code, code_path, ns, function_name)
    img = ImageFile(output_base, output_dir)

    for fmt, dpi in formats:
        try:
            img_path = img.filename(fmt)
            imgname, ext = os.path.splitext(os.path.basename(img_path))
            ns["wf"].base_dir = output_dir
            src = ns["wf"].write_graph(
                imgname, format=ext[1:], graph2use=graph2use, simple_form=simple_form
            )
            shutil.move(src, img_path)
        except Exception:
            raise GraphError(traceback.format_exc())

        img.formats.append(fmt)

    return [(code, [img])]
