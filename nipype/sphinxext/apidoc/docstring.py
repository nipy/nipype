# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Reformat interface docstrings."""
import re
from sphinx.locale import _
from sphinx.ext.napoleon.docstring import NumpyDocstring


class NipypeDocstring(NumpyDocstring):
    """Patch the NumpyDocstring from napoleon to get special section headers."""

    def _parse_parameters_section(self, section):
        # type: (unicode) -> List[unicode]
        labels = {
            "args": _("Parameters"),
            "arguments": _("Parameters"),
            "parameters": _("Parameters"),
        }  # type: Dict[unicode, unicode]
        label = labels.get(section.lower(), section)

        fields = self._consume_fields()
        if self._config.napoleon_use_param:
            return self._format_docutils_params(fields)

        return self._format_fields(label, fields)


class InterfaceDocstring(NipypeDocstring):
    """
    Convert docstrings of Nipype Interfaces to reStructuredText.

    Parameters
    ----------
    docstring : :obj:`str` or :obj:`list` of :obj:`str`
        The docstring to parse, given either as a string or split into
        individual lines.
    config: :obj:`sphinx.ext.napoleon.Config` or :obj:`sphinx.config.Config`
        The configuration settings to use. If not given, defaults to the
        config object on `app`; or if `app` is not given defaults to the
        a new :class:`nipype.sphinxext.apidoc.Config` object.

    Other Parameters
    ----------------
    app : :class:`sphinx.application.Sphinx`, optional
        Application object representing the Sphinx process.
    what : :obj:`str`, optional
        A string specifying the type of the object to which the docstring
        belongs. Valid values: "module", "class", "exception", "function",
        "method", "attribute".
    name : :obj:`str`, optional
        The fully qualified name of the object.
    obj : module, class, exception, function, method, or attribute
        The object to which the docstring belongs.
    options : :class:`sphinx.ext.autodoc.Options`, optional
        The options given to the directive: an object with attributes
        inherited_members, undoc_members, show_inheritance and noindex that
        are True if the flag option of same name was given to the auto
        directive.

    """

    _name_rgx = re.compile(
        r"^\s*(:(?P<role>\w+):`(?P<name>[a-zA-Z0-9_.-]+)`|"
        r" (?P<name2>[a-zA-Z0-9_.-]+))\s*",
        re.VERBOSE,
    )

    def __init__(
        self, docstring, config=None, app=None, what="", name="", obj=None, options=None
    ):
        # type: (Union[unicode, List[unicode]], SphinxConfig, Sphinx, unicode, unicode, Any, Any) -> None  # NOQA
        super().__init__(docstring, config, app, what, name, obj, options)

        cmd = getattr(obj, "_cmd", "")
        if cmd and cmd.strip():
            self._parsed_lines = [
                "Wrapped executable: ``%s``." % cmd.strip(),
                "",
            ] + self._parsed_lines

        if obj is not None:
            self._parsed_lines += _parse_interface(obj)


def _parse_interface(obj):
    """Print description for input parameters."""
    parsed = []
    if obj.input_spec:
        inputs = obj.input_spec()
        mandatory_items = sorted(inputs.traits(mandatory=True).items())
        if mandatory_items:
            parsed += ["", "Mandatory Inputs"]
            parsed += ["-" * len(parsed[-1])]
            for name, spec in mandatory_items:
                parsed += _parse_spec(inputs, name, spec)

        mandatory_keys = {item[0] for item in mandatory_items}
        optional_items = sorted(
            [
                (name, val)
                for name, val in inputs.traits(transient=None).items()
                if name not in mandatory_keys
            ]
        )
        if optional_items:
            parsed += ["", "Optional Inputs"]
            parsed += ["-" * len(parsed[-1])]
            for name, spec in optional_items:
                parsed += _parse_spec(inputs, name, spec)

    if obj.output_spec:
        outputs = sorted(obj.output_spec().traits(transient=None).items())
        if outputs:
            parsed += ["", "Outputs"]
            parsed += ["-" * len(parsed[-1])]
            for name, spec in outputs:
                parsed += _parse_spec(inputs, name, spec)

    return parsed


def _indent(lines, n=4):
    # type: (List[unicode], int) -> List[unicode]
    return [(" " * n) + line for line in lines]


def _parse_spec(inputs, name, spec):
    """Parse a HasTraits object into a Numpy-style docstring."""
    desc_lines = []
    if spec.desc:
        desc = "".join([spec.desc[0].capitalize(), spec.desc[1:]])
        if not desc.endswith(".") and not desc.endswith("\n"):
            desc = "%s." % desc
        desc_lines += desc.splitlines()

    argstr = spec.argstr
    if argstr and argstr.strip():
        pos = spec.position
        if pos is None:
            desc_lines += [
                """Maps to a command-line argument: :code:`{arg}`.""".format(
                    arg=argstr.strip()
                )
            ]
        else:
            desc_lines += [
                """Maps to a command-line argument: :code:`{arg}` (position: {pos}).""".format(
                    arg=argstr.strip(), pos=pos
                )
            ]

    xor = spec.xor
    if xor:
        desc_lines += [
            "Mutually **exclusive** with inputs: %s."
            % ", ".join(["``%s``" % x for x in xor])
        ]

    requires = spec.requires
    if requires:
        desc_lines += [
            "**Requires** inputs: %s." % ", ".join(["``%s``" % x for x in requires])
        ]

    if spec.usedefault:
        default = spec.default_value()[1]
        if isinstance(default, (bytes, str)) and not default:
            default = '""'

        desc_lines += ["(Nipype **default** value: ``%s``)" % str(default)]

    out_rst = [f"{name} : {spec.full_info(inputs, name, None)}"]
    out_rst += _indent(desc_lines, 4)

    return out_rst
