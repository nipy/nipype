#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Script to auto-generate our API docs.
"""
# stdlib imports
import os
from optparse import OptionParser
import sys

def listClasses(module=None):
    if module:
        __import__(module)
        pkg = sys.modules[module]
        print "Available functions:"
        for k,v in pkg.__dict__.items():
            if 'class' in str(v) and k != '__builtins__':
                print "\t%s"%k

def add_options(parser=None, module=None, function=None):
    interface = None
    if parser and module and function:
        __import__(module)
        interface = getattr(sys.modules[module],function)()

        for k,v in interface.inputs.iteritems():
            parser.add_option("-%s"%k[0], "--%s"%k, dest="IXI%s"%k,
                              metavar=k,
                              action='store',type='string',
                              help="you need help?",default='')
    return parser, interface

def run_instance(interface, options):
    if interface:
        print "setting function inputs"
        for k,v in interface.inputs.iteritems():
            optionskey = ''.join(('IXI',k))
            if hasattr(options, optionskey):
                setattr(interface.inputs, k,
                        getattr(options, optionskey))
        print interface.inputs
        print "not really running anything"

def get_modfunc(args):
    module = None
    function = None
    posargs = []
    skip = False
    for a in args:
        if skip:
            skip = False
            continue
        if a.startswith('--'):
            pass
        elif a.startswith('-'):
            skip = True
        else:
            posargs.append(a)
    if posargs:
        module = posargs[0]
        if len(posargs)==2:
            function = posargs[1]
    return module, function

def parse_args():
    usage = "usage: %prog [options] module function"
    parser = OptionParser(usage=usage,version="%prog 1.0",
                          conflict_handler="resolve")
    parser.add_option("--run", dest="run",
                      action='store_true',help="Execute",
                      default=False)

    module, function = get_modfunc(sys.argv[1:])
    parser, interface  = add_options(parser, module, function)
    (options, args) = parser.parse_args()
    if options.run and interface:
        #assign inputs
        run_instance(interface, options)
    else:
        parser.print_help()
        if module and not function:
            listClasses(module)
        parser.exit()


#*****************************************************************************
if __name__ == '__main__':
    parse_args()
