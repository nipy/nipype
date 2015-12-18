#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from future import standard_library
standard_library.install_aliases()
from builtins import range

import os
import os.path as op
from glob import glob
import pickle
import inspect
from nipype import logging, config
from nipype.external.six import string_types
from nipype.interfaces.base import isdefined
from nipype.utils.misc import create_function_from_source, str2bool
from nipype.utils.filemanip import (FileNotFoundError, filename_to_list,
                                    get_related_files)

logger = logging.getLogger('workflow')

try:
    from os.path import relpath
except ImportError:
    def relpath(path, start=None):
        """Return a relative version of a path"""
        if start is None:
            start = os.curdir
        if not path:
            raise ValueError("no path specified")
        start_list = op.abspath(start).split(op.sep)
        path_list = op.abspath(path).split(op.sep)
        if start_list[0].lower() != path_list[0].lower():
            unc_path, rest = op.splitunc(path)
            unc_start, rest = op.splitunc(start)
            if bool(unc_path) ^ bool(unc_start):
                raise ValueError(("Cannot mix UNC and non-UNC paths "
                                  "(%s and %s)") % (path, start))
            else:
                raise ValueError("path is on drive %s, start on drive %s"
                                 % (path_list[0], start_list[0]))
        # Work out how much of the filepath is shared by start and path.
        for i in range(min(len(start_list), len(path_list))):
            if start_list[i].lower() != path_list[i].lower():
                break
        else:
            i += 1

        rel_list = [op.pardir] * (len(start_list) - i) + path_list[i:]
        if not rel_list:
            return os.curdir
        return op.join(*rel_list)


def modify_paths(object, relative=True, basedir=None):
    """Convert paths in data structure to either full paths or relative paths

    Supports combinations of lists, dicts, tuples, strs

    Parameters
    ----------

    relative : boolean indicating whether paths should be set relative to the
               current directory
    basedir : default os.getcwd()
              what base directory to use as default
    """
    if not basedir:
        basedir = os.getcwd()
    if isinstance(object, dict):
        out = {}
        for key, val in sorted(object.items()):
            if isdefined(val):
                out[key] = modify_paths(val, relative=relative,
                                        basedir=basedir)
    elif isinstance(object, (list, tuple)):
        out = []
        for val in object:
            if isdefined(val):
                out.append(modify_paths(val, relative=relative,
                                        basedir=basedir))
        if isinstance(object, tuple):
            out = tuple(out)
    else:
        if isdefined(object):
            if isinstance(object, string_types) and op.isfile(object):
                if relative:
                    if config.getboolean('execution', 'use_relative_paths'):
                        out = relpath(object, start=basedir)
                    else:
                        out = object
                else:
                    out = op.abspath(op.join(basedir, object))
                if not op.exists(out):
                    raise FileNotFoundError('File %s not found' % out)
            else:
                out = object
    return out


def get_print_name(node, simple_form=True):
    """Get the name of the node

    For example, a node containing an instance of interfaces.fsl.BET
    would be called nodename.BET.fsl

    """
    name = node.fullname
    if hasattr(node, '_interface'):
        pkglist = node._interface.__class__.__module__.split('.')
        interface = node._interface.__class__.__name__
        destclass = ''
        if len(pkglist) > 2:
            destclass = '.%s' % pkglist[2]
        if simple_form:
            name = node.fullname + destclass
        else:
            name = '.'.join([node.fullname, interface]) + destclass
    if simple_form:
        parts = name.split('.')
        if len(parts) > 2:
            return ' ('.join(parts[1:]) + ')'
        elif len(parts) == 2:
            return parts[1]
    return name


def make_output_dir(outdir):
    """Make the output_dir if it doesn't exist.

    Parameters
    ----------
    outdir : output directory to create

    """
    if not op.exists(op.abspath(outdir)):
        logger.debug("Creating %s" % outdir)
        os.makedirs(outdir)
    return outdir


def clean_working_directory(outputs, cwd, inputs, needed_outputs, config,
                            files2keep=None, dirs2keep=None):
    """Removes all files not needed for further analysis from the directory
    """
    if not outputs:
        return
    outputs_to_keep = list(outputs.get().keys())
    if needed_outputs and \
       str2bool(config['execution']['remove_unnecessary_outputs']):
        outputs_to_keep = needed_outputs
    # build a list of needed files
    output_files = []
    outputdict = outputs.get()
    for output in outputs_to_keep:
        output_files.extend(walk_outputs(outputdict[output]))
    needed_files = [path for path, type in output_files if type == 'f']
    if str2bool(config['execution']['keep_inputs']):
        input_files = []
        inputdict = inputs.get()
        input_files.extend(walk_outputs(inputdict))
        needed_files += [path for path, type in input_files if type == 'f']
    for extra in ['_0x*.json', 'provenance.*', 'pyscript*.m', 'pyjobs*.mat',
                  'command.txt', 'result*.pklz', '_inputs.pklz', '_node.pklz']:
        needed_files.extend(glob(os.path.join(cwd, extra)))
    if files2keep:
        needed_files.extend(filename_to_list(files2keep))
    needed_dirs = [path for path, type in output_files if type == 'd']
    if dirs2keep:
        needed_dirs.extend(filename_to_list(dirs2keep))
    for extra in ['_nipype', '_report']:
        needed_dirs.extend(glob(os.path.join(cwd, extra)))
    temp = []
    for filename in needed_files:
        temp.extend(get_related_files(filename))
    needed_files = temp
    logger.debug('Needed files: %s' % (';'.join(needed_files)))
    logger.debug('Needed dirs: %s' % (';'.join(needed_dirs)))
    files2remove = []
    if str2bool(config['execution']['remove_unnecessary_outputs']):
        for f in walk_files(cwd):
            if f not in needed_files:
                if len(needed_dirs) == 0:
                    files2remove.append(f)
                elif not any([f.startswith(dname) for dname in needed_dirs]):
                    files2remove.append(f)
    else:
        if not str2bool(config['execution']['keep_inputs']):
            input_files = []
            inputdict = inputs.get()
            input_files.extend(walk_outputs(inputdict))
            input_files = [path for path, type in input_files if type == 'f']
            for f in walk_files(cwd):
                if f in input_files and f not in needed_files:
                    files2remove.append(f)
    logger.debug('Removing files: %s' % (';'.join(files2remove)))
    for f in files2remove:
        os.remove(f)
    for key in outputs.copyable_trait_names():
        if key not in outputs_to_keep:
            setattr(outputs, key, Undefined)
    return outputs


def get_all_files(infile):
    files = [infile]
    if infile.endswith(".img"):
        files.append(infile[:-4] + ".hdr")
        files.append(infile[:-4] + ".mat")
    if infile.endswith(".img.gz"):
        files.append(infile[:-7] + ".hdr.gz")
    return files


def walk_outputs(object):
    """Extract every file and directory from a python structure
    """
    out = []
    if isinstance(object, dict):
        for key, val in sorted(object.items()):
            if isdefined(val):
                out.extend(walk_outputs(val))
    elif isinstance(object, (list, tuple)):
        for val in object:
            if isdefined(val):
                out.extend(walk_outputs(val))
    else:
        if isdefined(object) and isinstance(object, string_types):
            if os.path.islink(object) or os.path.isfile(object):
                out = [(filename, 'f') for filename in get_all_files(object)]
            elif os.path.isdir(object):
                out = [(object, 'd')]
    return out


def walk_files(cwd):
    for path, _, files in os.walk(cwd):
        for f in files:
            yield os.path.join(path, f)


def merge_dict(d1, d2, merge=lambda x, y: y):
    """
    Merges two dictionaries, non-destructively, combining
    values on duplicate keys as defined by the optional merge
    function.  The default behavior replaces the values in d1
    with corresponding values in d2.  (There is no other generally
    applicable merge strategy, but often you'll have homogeneous
    types in your dicts, so specifying a merge technique can be
    valuable.)

    Examples:

    >>> d1 = {'a': 1, 'c': 3, 'b': 2}
    >>> d2 = merge_dict(d1, d1)
    >>> len(d2)
    3
    >>> [d2[k] for k in ['a', 'b', 'c']]
    [1, 2, 3]

    >>> d3 = merge_dict(d1, d1, lambda x,y: x+y)
    >>> len(d3)
    3
    >>> [d3[k] for k in ['a', 'b', 'c']]
    [2, 4, 6]

    """
    if not isinstance(d1, dict):
        return merge(d1, d2)
    result = dict(d1)
    if d2 is None:
        return result
    for k, v in list(d2.items()):
        if k in result:
            result[k] = merge_dict(result[k], v, merge=merge)
        else:
            result[k] = v
    return result


def merge_bundles(g1, g2):
    for rec in g2.get_records():
        g1._add_record(rec)
    return g1

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
    from .nodes import MapNode
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
