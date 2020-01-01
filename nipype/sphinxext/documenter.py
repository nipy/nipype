"""sphinx autodoc ext."""
from sphinx.locale import _
from sphinx.ext import autodoc
from nipype.interfaces.base import BaseInterface
from .gh import get_url

_ClassDocumenter = autodoc.ClassDocumenter
RST_CLASS_BLOCK = """
.. index:: {name}

.. _{module}.{name}:

{name}
{underline}
`Link to code <{code_url}>`__

"""


class NipypeClassDocumenter(_ClassDocumenter):  # type: ignore
    priority = 20

    def add_directive_header(self, sig: str) -> None:
        if self.doc_as_attr:
            self.directivetype = "attribute"

        # Copied from super
        domain = getattr(self, "domain", "py")
        directive = getattr(self, "directivetype", self.objtype)
        name = self.format_name()
        sourcename = self.get_sourcename()

        is_interface = False
        try:
            is_interface = issubclass(self.object, BaseInterface)
        except TypeError:
            pass

        if is_interface is True:
            lines = RST_CLASS_BLOCK.format(
                code_url=get_url(self.object),
                module=self.modname,
                name=name,
                underline="=" * len(name),
            )
            for line in lines.splitlines():
                self.add_line(line, sourcename)
        else:
            self.add_line(
                ".. %s:%s:: %s%s" % (domain, directive, name, sig), sourcename
            )
            if self.options.noindex:
                self.add_line("   :noindex:", sourcename)
            if self.objpath:
                # Be explicit about the module, this is necessary since .. class::
                # etc. don't support a prepended module name
                self.add_line("   :module: %s" % self.modname, sourcename)

        # add inheritance info, if wanted
        if not self.doc_as_attr and self.options.show_inheritance:
            sourcename = self.get_sourcename()
            self.add_line("", sourcename)
            bases = getattr(self.object, "__bases__", [])
            bases_links = []

            for b in bases:
                based_interface = False
                try:
                    based_interface = issubclass(b, BaseInterface)
                except TypeError:
                    pass

                if b.__module__ in ("__builtin__", "builtins"):
                    bases_links.append(":class:`%s`" % b.__name__)
                elif based_interface:
                    bases_links.append(":ref:`%s.%s`" % (b.__module__, b.__name__))
                else:
                    bases_links.append(":class:`%s.%s`" % (b.__module__, b.__name__))

            self.add_line("   " + _("Bases: %s") % ", ".join(bases_links), sourcename)


def setup(app):
    app.add_autodocumenter(NipypeClassDocumenter)
