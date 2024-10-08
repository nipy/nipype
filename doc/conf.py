#
# nipype documentation build configuration file, created by
# sphinx-quickstart on Mon Jul 20 12:30:18 2009.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import sys
from packaging.version import Version
import nipype
import subprocess as sp

html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "")

# Tell Jinja2 templates the build is running on Read the Docs
if os.environ.get("READTHEDOCS", "") == "True":
    if "html_context" not in globals():
        html_context = {}
    html_context["READTHEDOCS"] = True

# Disable etelemetry during doc builds
os.environ["NIPYPE_NO_ET"] = "1"

conf_py = Path(__file__)

example_dir = conf_py.parent / "users" / "examples"
shutil.rmtree(example_dir, ignore_errors=True)
example_dir.mkdir(parents=True)
python_dir = conf_py.parent / "_static" / "python"
shutil.rmtree(python_dir, ignore_errors=True)

ex2rst = str(conf_py.parent.parent / "tools" / "ex2rst")

with TemporaryDirectory() as tmpdir:
    sp.run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "https://github.com/niflows/nipype1-examples.git",
            tmpdir,
        ],
        check=True,
    )
    source_dir = Path(tmpdir) / "package" / "niflow" / "nipype1" / "examples"
    shutil.copytree(
        source_dir,
        python_dir,
        ignore=lambda src, names: [n for n in names if n.endswith(".ipynb")],
    )

sp.run(
    [
        sys.executable,
        ex2rst,
        "--outdir",
        str(example_dir),
        str(python_dir),
        "-x",
        str(python_dir / "test_spm.py"),
        "-x",
        str(python_dir / "__init__.py"),
        "-x",
        str(python_dir / "cli.py"),
    ],
    check=True,
)
sp.run(
    [
        sys.executable,
        ex2rst,
        "--outdir",
        str(example_dir),
        str(python_dir / "frontiers_paper"),
    ],
    check=True,
)


# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
# sys.path.append(os.path.abspath('sphinxext'))

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.graphviz",
    "sphinx.ext.mathjax",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.todo",
    "sphinxcontrib.apidoc",
    "matplotlib.sphinxext.plot_directive",
    "nbsphinx",
    "nipype.sphinxext.plot_workflow",
    "nipype.sphinxext.apidoc",
    "nipype.sphinxext.documenter",
]

autodoc_mock_imports = [
    "matplotlib",
    "nilearn",
    "nipy",
    "nitime",
    "numpy",
    "pandas",
    "seaborn",
    "skimage",
    "svgutils",
    "transforms3d",
    "tvtk",
    "vtk",
]

# Accept custom section names to be parsed for numpy-style docstrings
# of parameters.
# Requires pinning sphinxcontrib-napoleon to a specific commit while
# https://github.com/sphinx-contrib/napoleon/pull/10 is merged.
napoleon_use_param = False
napoleon_custom_sections = [
    ("Inputs", "Parameters"),
    ("Outputs", "Parameters"),
    ("Attributes", "Parameters"),
    ("Mandatory Inputs", "Parameters"),
    ("Optional Inputs", "Parameters"),
]


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".rst"

# The encoding of source files.
# source_encoding = 'utf-8'

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "nipype"
copyright = "2009-21, Neuroimaging in Python team"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = Version(nipype.__version__).public
# The full version, including alpha/beta/rc tags.
release = nipype.__version__

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
# language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = "%B %d, %Y, %H:%M PDT"

# List of documents that shouldn't be included in the build.
unused_docs = ["api/generated/gen"]

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = ["_build"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The reST default role (used for this markup: `text`) to use for all documents.
# default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
# add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
# add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
# show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# A list of ignored prefixes for module index sorting.
# modindex_common_prefix = []

# -- Sphinxext configuration ---------------------------------------------------

# Set attributes for layout of inheritance diagrams
inheritance_graph_attrs = dict(
    rankdir="LR", size='"6.0, 8.0"', fontsize=14, ratio="compress"
)
inheritance_node_attrs = dict(
    shape="ellipse", fontsize=14, height=0.75, color="dodgerblue1", style="filled"
)

# Flag to show todo items in rendered output
todo_include_todos = True

# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
html_theme = "sphinxdoc"

# The style sheet to use for HTML and HTML Help pages. A file of that name
# must exist either in Sphinx' static/ path, or in one of the custom paths
# given in html_static_path.
html_style = "nipype.css"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
# html_theme_options = {}

# Add any paths that contain custom themes here, relative to this directory.
# html_theme_path = []

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = "nipy pipeline and interfaces package"

# A shorter title for the navigation bar.  Default is the same as html_title.
# html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
# html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
# html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
# html_last_updated_fmt = '%b %d, %Y'

# Content template for the index page.
html_index = "index.html"

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
# html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
html_sidebars = {
    "**": ["gse.html", "localtoc.html", "sidebar_versions.html", "indexsidebar.html"],
    "searchresults": ["sidebar_versions.html", "indexsidebar.html"],
    "version": [],
}

# Additional templates that should be rendered to pages, maps page names to
# template names.
# html_additional_pages = {'index': 'index.html'}

# If false, no module index is generated.
# html_use_modindex = True

# If false, no index is generated.
# html_use_index = True

# If true, the index is split into individual pages for each letter.
# html_split_index = False

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
# html_use_opensearch = ''

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
# html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = "nipypedoc"


# -- Options for LaTeX output --------------------------------------------------

# The paper size ('letter' or 'a4').
# latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
# latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
    (
        "interfaces",
        "interfaces.tex",
        "Nipype Interfaces Documentation",
        "Neuroimaging in Python team",
        "manual",
    ),
    # ('developers', 'developers.tex', 'Nipype API',
    #  'Neuroimaging in Python team', 'manual'),
    (
        "examples",
        "examples.tex",
        "Nipype Examples",
        "Neuroimaging in Python team",
        "manual",
    ),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
# latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
# latex_use_parts = False

# Additional stuff for the LaTeX preamble.
# latex_preamble = ''

# Documents to append as an appendix to all manuals.
# latex_appendices = []

# If false, no module index is generated.
# latex_use_modindex = True

# -- apidoc extension configuration ------------------------------------------
apidoc_module_dir = "../nipype"
apidoc_output_dir = "api/generated"
apidoc_excluded_paths = [
    "*/tests/*",
    "tests/*",
    "external/*",
    "fixes/*",
    "scripts/*",
    "testing/*",
    "workflows/*",
    "conftest.py",
    "info.py",
    "pkg_info.py",
    "refs.py",
]
apidoc_separate_modules = True
apidoc_extra_args = ["--module-first", "-d 1", "-T"]

# -- Options for intersphinx extension ---------------------------------------

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {"http://docs.python.org/": None}
