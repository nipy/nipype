#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import pickle
import inspect
from nipype.interfaces.base import isdefined
from nipype.utils.misc import create_function_from_source
from nodes import MapNode


def _write_inputs(node):
    lines = []
    nodename = node.fullname.replace('.', '_')
    for key, _ in list(node.inputs.items()):
        val = getattr(node.inputs, key)
        if isdefined(val):
            if type(val) == str:
                try:
                    func = create_function_from_source(val)
                except RuntimeError as e:
                    lines.append("%s.inputs.%s = '%s'" % (nodename, key, val))
                else:
                    funcname = [name for name in func.__globals__
                                if name != '__builtins__'][0]
                    lines.append(pickle.loads(val))
                    if funcname == nodename:
                        lines[-1] = lines[-1].replace(' %s(' % funcname,
                                                      ' %s_1(' % funcname)
                        funcname = '%s_1' % funcname
                    lines.append('from nipype.utils.misc import getsource')
                    lines.append("%s.inputs.%s = getsource(%s)" % (nodename,
                                                                   key,
                                                                   funcname))
            else:
                lines.append('%s.inputs.%s = %s' % (nodename, key, val))
    return lines


def format_node(node, format='python', include_config=False):
    """Format a node in a given output syntax."""
    lines = []
    name = node.fullname.replace('.', '_')
    if format == 'python':
        klass = node._interface
        importline = 'from %s import %s' % (klass.__module__,
                                            klass.__class__.__name__)
        comment = '# Node: %s' % node.fullname
        spec = inspect.signature(node._interface.__init__)
        args = spec.args[1:]
        if args:
            filled_args = []
            for arg in args:
                if hasattr(node._interface, '_%s' % arg):
                    filled_args.append('%s=%s' % (arg, getattr(node._interface,
                                                               '_%s' % arg)))
            args = ', '.join(filled_args)
        else:
            args = ''
        klass_name = klass.__class__.__name__
        if isinstance(node, MapNode):
            nodedef = '%s = MapNode(%s(%s), iterfield=%s, name="%s")' \
                      % (name, klass_name, args, node.iterfield, name)
        else:
            nodedef = '%s = Node(%s(%s), name="%s")' \
                      % (name, klass_name, args, name)
        lines = [importline, comment, nodedef]

        if include_config:
            lines = [importline, "from collections import OrderedDict",
                     comment, nodedef]
            lines.append('%s.config = %s' % (name, node.config))

        if node.iterables is not None:
            lines.append('%s.iterables = %s' % (name, node.iterables))
        lines.extend(_write_inputs(node))

    return lines
