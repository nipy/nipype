import os
import argparse
import inspect
import sys
from nipype.interfaces.base import Interface


def listClasses(module=None):
    if module:
        __import__(module)
        pkg = sys.modules[module]
        print "Available Interfaces:"
        for k,v in pkg.__dict__.items():
            if inspect.isclass(v) and issubclass(v, Interface):
                print "\t%s"%k

def add_options(parser=None, module=None, function=None):
    interface = None
    if parser and module and function:
        __import__(module)
        interface = getattr(sys.modules[module],function)()

        for k,v in interface.inputs.items():
            if hasattr(v, "mandatory") and v.mandatory:
                parser.add_argument(k, help=v.desc)
            else:
                parser.add_argument("--%s"%k, dest=k,
                                help=v.desc)
    return parser, interface

def run_instance(interface, options):
    if interface:
        print "setting function inputs"
        for input_name, _ in interface.inputs.items():
            if getattr(options, input_name) != None:
                str_value = getattr(options, input_name)
                casted_value = getattr(interface.inputs, input_name)(str_value)
                setattr(interface.inputs, input_name,
                        casted_value)
        print interface.inputs
        res = interface.run()
        print res.outputs    


def main(argv):
    
    if len(argv) == 2 and not argv[1].startswith("-"):
        listClasses(argv[1])
        sys.exit(0)
    
    parser = argparse.ArgumentParser(description='Nipype interface runner')
    parser.add_argument("module", type=str, help="Module name")
    parser.add_argument("interface", type=str, help="Interface name")
    parsed = parser.parse_args(args=argv[1:3])
    
    _, prog = os.path.split(argv[0])
    interface_parser = argparse.ArgumentParser(description="Run %s"%parsed.interface, prog=" ".join([prog] + argv[1:3]))
    interface_parser, interface  = add_options(interface_parser, parsed.module, parsed.interface)
    args = interface_parser.parse_args(args=argv[3:])
    run_instance(interface, args)