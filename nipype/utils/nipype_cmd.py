# -*- coding: utf-8 -*-
import os
import argparse
import inspect
import sys

from ..interfaces.base import Interface, InputMultiPath, traits
from ..interfaces.base.support import get_trait_desc
from .misc import str2bool


def listClasses(module=None):
    if module:
        __import__(module)
        pkg = sys.modules[module]
        print("Available Interfaces:")
        for k, v in sorted(list(pkg.__dict__.items())):
            if inspect.isclass(v) and issubclass(v, Interface):
                print("\t%s" % k)


def add_options(parser=None, module=None, function=None):
    interface = None
    if parser and module and function:
        __import__(module)
        interface = getattr(sys.modules[module], function)()

        inputs = interface.input_spec()
        for name, spec in sorted(interface.inputs.traits(transient=None).items()):
            desc = "\n".join(get_trait_desc(inputs, name, spec))[len(name) + 2 :]
            args = {}

            if spec.is_trait_type(traits.Bool):
                args["action"] = "store_true"

            if hasattr(spec, "mandatory") and spec.mandatory:
                if spec.is_trait_type(InputMultiPath):
                    args["nargs"] = "+"
                parser.add_argument(name, help=desc, **args)
            else:
                if spec.is_trait_type(InputMultiPath):
                    args["nargs"] = "*"
                parser.add_argument("--%s" % name, dest=name, help=desc, **args)
    return parser, interface


def run_instance(interface, options):
    print("setting function inputs")

    for input_name, _ in list(interface.inputs.items()):
        if getattr(options, input_name) is not None:
            value = getattr(options, input_name)
            try:
                setattr(interface.inputs, input_name, value)
            except ValueError as e:
                print("Error when setting the value of %s: '%s'" % (input_name, str(e)))

    print(interface.inputs)
    res = interface.run()
    print(res.outputs)


def main(argv):
    if len(argv) == 2 and not argv[1].startswith("-"):
        listClasses(argv[1])
        sys.exit(0)

    parser = argparse.ArgumentParser(
        description="Nipype interface runner", prog=argv[0]
    )
    parser.add_argument("module", type=str, help="Module name")
    parser.add_argument("interface", type=str, help="Interface name")
    parsed = parser.parse_args(args=argv[1:3])

    _, prog = os.path.split(argv[0])
    interface_parser = argparse.ArgumentParser(
        description="Run %s" % parsed.interface, prog=" ".join([prog] + argv[1:3])
    )
    interface_parser, interface = add_options(
        interface_parser, parsed.module, parsed.interface
    )
    args = interface_parser.parse_args(args=argv[3:])
    run_instance(interface, args)
