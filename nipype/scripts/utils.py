# -*- coding: utf-8 -*-
"""
Utilities for the CLI functions.
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import re

import click

from .instance import import_module
from ..interfaces.base import InputMultiPath, traits


# different context options
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
UNKNOWN_OPTIONS = dict(allow_extra_args=True,
                       ignore_unknown_options=True)


# specification of existing ParamTypes
ExistingDirPath  = click.Path(exists=True, file_okay=False, resolve_path=True)
ExistingFilePath = click.Path(exists=True,  dir_okay=False, resolve_path=True)
UnexistingFilePath = click.Path(dir_okay=False, resolve_path=True)


# validators
def check_not_none(ctx, param, value):
    if value is None:
        raise click.BadParameter('got {}.'.format(value))
    return value


# declare custom click.ParamType
class RegularExpression(click.ParamType):
    name = 'regex'

    def convert(self, value, param, ctx):
        try:
            rex = re.compile(value, re.IGNORECASE)
        except ValueError:
            self.fail('%s is not a valid regular expression.' % value, param, ctx)
        else:
            return rex


class PythonModule(click.ParamType):
    name = 'Python module path'

    def convert(self, value, param, ctx):
        try:
            module = import_module(value)
        except ValueError:
            self.fail('%s is not a valid Python module.' % value, param, ctx)
        else:
            return module


def add_args_options(arg_parser, interface):
    """Add arguments to `arg_parser` to create a CLI for `interface`."""
    inputs = interface.input_spec()
    for name, spec in sorted(interface.inputs.traits(transient=None).items()):
        desc = "\n".join(interface._get_trait_desc(inputs, name, spec))[len(name) + 2:]
        args = {}

        if spec.is_trait_type(traits.Bool):
            args["action"] = 'store_true'

        if hasattr(spec, "mandatory") and spec.mandatory:
            if spec.is_trait_type(InputMultiPath):
                args["nargs"] = "+"
            arg_parser.add_argument(name, help=desc, **args)
        else:
            if spec.is_trait_type(InputMultiPath):
                args["nargs"] = "*"
            arg_parser.add_argument("--%s" % name, dest=name,
                                    help=desc, **args)
    return arg_parser
