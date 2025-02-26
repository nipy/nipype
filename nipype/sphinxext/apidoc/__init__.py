# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Settings for sphinxext.interfaces and connection to sphinx-apidoc."""
import re
from packaging.version import Version

import sphinx
from sphinx.ext.napoleon import (
    Config as NapoleonConfig,
    _patch_python_domain,
    _skip_member as _napoleon_skip_member,
)

from ... import __version__
from ...interfaces.base import BaseInterface, TraitedSpec
from .docstring import NipypeDocstring, InterfaceDocstring


class Config(NapoleonConfig):
    r"""
    Sphinx-nipype extension settings in ``conf.py``.

    Listed below are all the settings used by this extension
    and their default values.
    These settings can be changed in the Sphinx's ``conf.py`` file.
    Make sure that ``nipype.sphinxext.interfaces`` is enabled
    in ``conf.py``::

        # conf.py

        # Add this extension to the corresponding list:
        extensions = ['nipype.sphinxext.interfaces']

        # NiPype settings
        nipype_references = False

    Attributes
    ----------
    nipype_skip_classes: :obj:`bool` (Defaults to True)
        True to include referenced publications with the interface
        (requires duecredit to be installed).

    """

    if Version(sphinx.__version__) >= Version("8.2.1"):
        _config_values = (
            (
                "nipype_skip_classes",
                ["Tester", "InputSpec", "OutputSpec", "Numpy", "NipypeTester"],
                "env",
                frozenset({list[str]}),
            ),
            *NapoleonConfig._config_values,
        )
    else:
        _config_values = {
            "nipype_skip_classes": (
                ["Tester", "InputSpec", "OutputSpec", "Numpy", "NipypeTester"],
                "env",
            ),
            **NapoleonConfig._config_values,
        }


def setup(app):
    # type: (Sphinx) -> Dict[unicode, Any]
    """
    Sphinx extension setup function.

    When the extension is loaded, Sphinx imports this module and executes
    the ``setup()`` function, which in turn notifies Sphinx of everything
    the extension offers.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        Application object representing the Sphinx process

    See Also
    --------
    `The Sphinx documentation on Extensions
    <http://sphinx-doc.org/extensions.html>`_
    `The Extension Tutorial <http://sphinx-doc.org/extdev/tutorial.html>`_
    `The Extension API <http://sphinx-doc.org/extdev/appapi.html>`_

    """
    from sphinx.application import Sphinx

    if not isinstance(app, Sphinx):
        # probably called by tests
        return {"version": __version__, "parallel_read_safe": True}

    _patch_python_domain()

    app.setup_extension("sphinx.ext.autodoc")
    app.connect("autodoc-process-docstring", _process_docstring)
    app.connect("autodoc-skip-member", _skip_member)

    if Version(sphinx.__version__) >= Version("8.2.1"):
        for name, default, rebuild, types in Config._config_values:
            app.add_config_value(name, default, rebuild, types=types)
    else:
        for name, (default, rebuild) in Config._config_values.items():
            app.add_config_value(name, default, rebuild)
    return {"version": __version__, "parallel_read_safe": True}


def _process_docstring(app, what, name, obj, options, lines):
    # type: (Sphinx, unicode, unicode, Any, Any, List[unicode]) -> None
    """Process the docstring for a given python object.
    Called when autodoc has read and processed a docstring. `lines` is a list
    of docstring lines that `_process_docstring` modifies in place to change
    what Sphinx outputs.
    The following settings in conf.py control what styles of docstrings will
    be parsed:
    * ``napoleon_google_docstring`` -- parse Google style docstrings
    * ``napoleon_numpy_docstring`` -- parse NumPy style docstrings
    Parameters
    ----------
    app : sphinx.application.Sphinx
        Application object representing the Sphinx process.
    what : str
        A string specifying the type of the object to which the docstring
        belongs. Valid values: "module", "class", "exception", "function",
        "method", "attribute".
    name : str
        The fully qualified name of the object.
    obj : module, class, exception, function, method, or attribute
        The object to which the docstring belongs.
    options : sphinx.ext.autodoc.Options
        The options given to the directive: an object with attributes
        inherited_members, undoc_members, show_inheritance and noindex that
        are True if the flag option of same name was given to the auto
        directive.
    lines : list of str
        The lines of the docstring, see above.
        .. note:: `lines` is modified *in place*
    """
    result_lines = lines
    # Parse Nipype Interfaces
    if what == "class" and issubclass(obj, BaseInterface):
        result_lines[:] = InterfaceDocstring(
            result_lines, app.config, app, what, name, obj, options
        ).lines()

    result_lines = NipypeDocstring(
        result_lines, app.config, app, what, name, obj, options
    ).lines()
    lines[:] = result_lines[:]


def _skip_member(app, what, name, obj, skip, options):
    # type: (Sphinx, unicode, unicode, Any, bool, Any) -> bool
    """
    Determine if private and special class members are included in docs.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        Application object representing the Sphinx process
    what : str
        A string specifying the type of the object to which the member
        belongs. Valid values: "module", "class", "exception", "function",
        "method", "attribute".
    name : str
        The name of the member.
    obj : module, class, exception, function, method, or attribute.
        For example, if the member is the __init__ method of class A, then
        `obj` will be `A.__init__`.
    skip : bool
        A boolean indicating if autodoc will skip this member if `_skip_member`
        does not override the decision
    options : sphinx.ext.autodoc.Options
        The options given to the directive: an object with attributes
        inherited_members, undoc_members, show_inheritance and noindex that
        are True if the flag option of same name was given to the auto
        directive.
    Returns
    -------
    bool
        True if the member should be skipped during creation of the docs,
        False if it should be included in the docs.

    """
    # Parse Nipype Interfaces
    patterns = [
        pat if hasattr(pat, "search") else re.compile(pat)
        for pat in app.config.nipype_skip_classes
    ]
    isbase = False
    try:
        isbase = issubclass(obj, BaseInterface)
        if issubclass(obj, TraitedSpec):
            return True
    except TypeError:
        pass

    if isbase:
        for pattern in patterns:
            if pattern.search(name):
                return True

    return _napoleon_skip_member(app, what, name, obj, skip, options)
