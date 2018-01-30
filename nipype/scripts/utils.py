# -*- coding: utf-8 -*-
"""
Utilities for the CLI functions.
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from builtins import bytes, str

import re
import click
import json

from .instance import import_module
from ..interfaces.base import InputMultiPath, traits

# different context options
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
UNKNOWN_OPTIONS = dict(allow_extra_args=True, ignore_unknown_options=True)

# specification of existing ParamTypes
ExistingDirPath = click.Path(exists=True, file_okay=False, resolve_path=True)
ExistingFilePath = click.Path(exists=True, dir_okay=False, resolve_path=True)
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
            self.fail('%s is not a valid regular expression.' % value, param,
                      ctx)
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
        desc = "\n".join(interface._get_trait_desc(inputs, name,
                                                   spec))[len(name) + 2:]
        # Escape any % signs with a %
        desc = desc.replace('%', '%%')
        args = {}
        has_multiple_inner_traits = False

        if spec.is_trait_type(traits.Bool):
            args["default"] = getattr(inputs, name)
            args["action"] = 'store_true'

        # current support is for simple trait types
        if not spec.inner_traits:
            if not spec.is_trait_type(traits.TraitCompound):
                trait_type = type(spec.trait_type.default_value)
            if trait_type in (bytes, str, int, float):
                if trait_type == bytes:
                    trait_type = str
                args["type"] = trait_type
        elif len(spec.inner_traits) == 1:
            trait_type = type(spec.inner_traits[0].trait_type.default_value)
            if trait_type == bytes:
                trait_type = str
            if trait_type in (bytes, bool, str, int, float):
                args["type"] = trait_type
        else:
            if len(spec.inner_traits) > 1:
                if not spec.is_trait_type(traits.Dict):
                    has_multiple_inner_traits = True

        if getattr(spec, "mandatory", False):
            if spec.is_trait_type(InputMultiPath):
                args["nargs"] = "+"
            elif spec.is_trait_type(traits.List):
                if (spec.trait_type.minlen == spec.trait_type.maxlen) and \
                        spec.trait_type.maxlen:
                    args["nargs"] = spec.trait_type.maxlen
                else:
                    args["nargs"] = "+"
            elif spec.is_trait_type(traits.Dict):
                args["type"] = json.loads

            if has_multiple_inner_traits:
                raise NotImplementedError(
                    ('This interface cannot be used. via the'
                     ' command line as multiple inner traits'
                     ' are currently not supported for mandatory'
                     ' argument: {}.'.format(name)))
            arg_parser.add_argument(name, help=desc, **args)
        else:
            if spec.is_trait_type(InputMultiPath):
                args["nargs"] = "*"
            elif spec.is_trait_type(traits.List):
                if (spec.trait_type.minlen == spec.trait_type.maxlen) and \
                        spec.trait_type.maxlen:
                    args["nargs"] = spec.trait_type.maxlen
                else:
                    args["nargs"] = "*"
            if not has_multiple_inner_traits:
                arg_parser.add_argument(
                    "--%s" % name, dest=name, help=desc, **args)

    return arg_parser
