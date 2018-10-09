# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from collections import defaultdict
import glob
from itertools import chain
import json
import os

from .core import CommandLine
from .specs import DynamicTraitedSpec
from .traits_extension import (
    File, isdefined, OutputMultiPath, Str, traits, Undefined)
from ... import logging
from ...utils.misc import trim


iflogger = logging.getLogger('nipype.interface')


class BoutiqueInterface(CommandLine):
    """Convert Boutique specification to Nipype interface
    """

    input_spec = DynamicTraitedSpec
    output_spec = DynamicTraitedSpec

    # Subclasses may override the trait_map to provide better traits
    # for various types
    trait_map = {
        'File': File,
        'String': Str,
        'Number': traits.Float,
        'Flag': traits.Bool,
        }

    def __init__(self, boutique_spec, **inputs):
        if os.path.exists(boutique_spec):
            with open(boutique_spec, 'r') as fobj:
                boutique_spec = json.load(fobj)

        self.boutique_spec = boutique_spec
        split_cmd = boutique_spec['command-line'].split(None, 1)
        self._cmd = split_cmd[0]
        self._argspec = split_cmd[1] if len(split_cmd) > 1 else None

        self._xors = defaultdict(list)
        self._requires = defaultdict(list)
        self._one_required = defaultdict(list)

        # we're going to actually generate input_spec and output_spec classes
        # so we want this to occur before the super().__init__() call
        self._load_groups(boutique_spec.get('groups', []))
        self._populate_input_spec(boutique_spec.get('inputs', []))
        self._populate_output_spec(boutique_spec.get('output-files', []))

        super().__init__()

        # now set all the traits that don't have defaults/inputs to undefined
        self._set_undefined(**inputs)

    def _load_groups(self, groups):
        for group in groups:
            members = group['members']
            if group.get('all-or-none'):
                for member in members:
                    self._requires[member].extend(members)
            elif group.get('mutually-exclusive'):
                for member in members:
                    self._xors[member].extend(members)
            elif group.get('one-is-required'):
                for member in members:
                    self._one_required[member].extend(members)

    def _set_undefined(self, **inputs):
        usedefault = self.inputs.traits(usedefault=True)
        undefined = {k: Undefined for k in
                     set(self.inputs.get()) - set(usedefault)}
        self.inputs.trait_set(trait_change_notify=False, **undefined)
        self.inputs.trait_set(trait_change_notify=False, **inputs)

    def _populate_input_spec(self, input_list):
        """ Generates input specification class
        """
        input_spec = {}
        value_keys = {}
        for input_dict in input_list:
            trait_name = input_dict['id']
            args = []
            metadata = {}

            # Establish trait type
            typestr = input_dict['type']
            if 'value-choices' in input_dict:
                ttype = traits.Enum
                args = input_dict['value-choices']
            elif typestr == 'Number' and ('maximum' in input_dict or
                                          'minimum' in input_dict):
                ttype = traits.Range
            elif typestr == 'Number' and input_dict.get('integer'):
                ttype = traits.Int
            else:
                ttype = self.trait_map[typestr]
                if typestr == 'File':
                    metadata['exists'] = True

            if 'default-value' in input_dict:
                nipype_key = 'default_value'
                default_value = input_dict['default-value']
                if ttype in (traits.Range, traits.List):
                    nipype_key = 'value'
                elif ttype is traits.Enum:
                    args.remove(default_value)
                    args.insert(0, default_value)

                if ttype is not traits.Enum:
                    metadata[nipype_key] = default_value
                metadata['usedefault'] = True

            if input_dict.get('list'):
                if len(args) > 0:
                    ttype = ttype(*args)
                    args = []
                metadata['trait'] = ttype
                ttype = traits.List

            # Complete metadata
            if 'command-line-flag' in input_dict:
                argstr = input_dict['command-line-flag']
                if typestr != 'Flag':
                    argstr += input_dict.get('command-line-flag-separator',
                                             ' ')
                    argstr += '%s'  # May be insufficient for some
                metadata['argstr'] = argstr

            direct_mappings = {
                # Boutiques:     Nipype
                'description': 'desc',
                'disables-inputs': 'xor',
                'exclusive-maximum': 'exclude_high',
                'exclusive-minimum': 'exclude_low',
                'max-list-entries': 'maxlen',
                'maximum': 'high',
                'min-list-entries': 'minlen',
                'minimum': 'low',
                'requires-inputs': 'requires',
                }

            for boutique_key, nipype_key in direct_mappings.items():
                if boutique_key in input_dict:
                    metadata[nipype_key] = input_dict[boutique_key]

            # Unsupported:
            #  * uses-absolute-path
            #  * value-disables
            #  * value-requires

            metadata['mandatory'] = not input_dict.get('optional', False)

            # This is a little weird and hacky, and could probably be done
            # better.
            if trait_name in self._requires:
                metadata.setdefault('requires',
                                    []).extend(self._requires[trait_name])
            if trait_name in self._xors:
                metadata.setdefault('xor',
                                    []).extend(self._xors[trait_name])

            trait = ttype(*args, **metadata)
            input_spec[trait_name] = trait

            value_keys[input_dict['value-key']] = trait_name

        self.input_spec = type('{}InputSpec'.format(self._cmd.capitalize()),
                               (self.input_spec,),
                               input_spec)

        # TODO: value-keys aren't necessarily mutually exclusive; use id as key
        self.value_keys = value_keys

    def _populate_output_spec(self, output_list):
        """ Creates output specification class
        """
        output_spec = {}
        value_keys = {}
        for output_dict in output_list:
            trait_name = output_dict['id']
            ttype = traits.File
            metadata = {}
            args = [Undefined]

            if output_dict.get('description') is not None:
                metadata['desc'] = output_dict['description']

            metadata['exists'] = not output_dict.get('optional', True)

            if output_dict.get('list'):
                args = [ttype(Undefined, **metadata)]
                ttype = OutputMultiPath

            if 'command-line-flag' in output_dict:
                argstr = output_dict['command-line-flag']
                argstr += output_dict.get('command-line-flag-separator', ' ')
                argstr += '%s'  # May be insufficient for some
                metadata['argstr'] = argstr

            trait = ttype(*args, **metadata)
            output_spec[trait_name] = trait

            if 'value-key' in output_dict:
                value_keys[output_dict['value-key']] = trait_name

        # reassign output spec class based on compiled outputs
        self.output_spec = type('{}OutputSpec'.format(self._cmd.capitalize()),
                                (self.output_spec,),
                                output_spec)

        self.value_keys.update(value_keys)

    def _list_outputs(self):
        """ Generate list of predicted outputs based on defined inputs
        """
        output_list = self.boutique_spec.get('output-files', [])
        outputs = self.output_spec().get()

        for n, out in enumerate([f['id'] for f in output_list]):
            output_dict = output_list[n]
            # get path template + stripped extensions
            output_filename = output_dict['path-template']
            strip = output_dict.get('path-template-stripped-extensions', [])

            # replace all value-keys in output name
            for valkey, name in self.value_keys.items():
                repl = self.inputs.trait_get().get(name)
                # if input is specified, strip extensions + replace in output
                if repl is not None and isdefined(repl):
                    for ext in strip:
                        repl = repl[:-len(ext)] if repl.endswith(ext) else repl
                    output_filename = output_filename.replace(valkey, repl)

            outputs[out] = os.path.abspath(output_filename)

            if output_dict.get('list'):
                outputs[out] = [outputs[out]]

        return outputs

    def aggregate_outputs(self, runtime=None, needed_outputs=None):
        """ Collate expected outputs and check for existence
        """
        outputs = super().aggregate_outputs(runtime=runtime,
                                            needed_outputs=needed_outputs)
        for key, val in outputs.get().items():
            # since we can't know if the output will be generated based on the
            # boutiques spec, reset all non-existent outputs to undefined
            if isinstance(val, list):
                # glob expected output path template and flatten list
                val = list(chain.from_iterable([glob.glob(v) for v in val]))
                if len(val) == 0:
                    val = Undefined
                setattr(outputs, key, val)
            else:
                if not os.path.exists(val):
                    val = Undefined
            if not os.path.exists(val):
                setattr(outputs, key, Undefined)

        return outputs

    def cmdline(self):
        """ Prints command line with all specified arguments
        """
        args = self._argspec
        inputs = {**self.inputs.trait_get(), **self._list_outputs()}
        for valkey, name in self.value_keys.items():
            try:
                spec = self.inputs.traits()[name]
            except KeyError:
                spec = self.outputs.traits()[name]
            value = inputs[name]
            if not isdefined(value):
                value = ''
            elif spec.argstr:
                value = self._format_arg(name, spec, value)
            args = args.replace(valkey, value)
        return self._cmd + ' ' + args

    def help(self, returnhelp=False):
        """ Prints interface help
        """

        docs = self.boutique_spec.get('description')
        if docs is not None:
            docstring = trim(docs).split('\n') + ['']
        else:
            docstring = [self.__class__.__doc__]

        allhelp = '\n'.join(docstring +
                            self._inputs_help() + [''] +
                            self._outputs_help() + [''] +
                            self._refs_help() + [''])
        if returnhelp:
            return allhelp
        else:
            print(allhelp)

    def _inputs_help(self):
        """ Prints description for input parameters
        """
        helpstr = ['Inputs::']

        inputs = self.input_spec()
        if len(list(inputs.traits(transient=None).items())) == 0:
            helpstr += ['', '\tNone']
            return helpstr

        manhelpstr = ['', '\t[Mandatory]']
        mandatory_items = inputs.traits(mandatory=True)
        for name, spec in sorted(mandatory_items.items()):
            manhelpstr += self.__class__._get_trait_desc(inputs, name, spec)

        opthelpstr = ['', '\t[Optional]']
        for name, spec in sorted(inputs.traits(transient=None).items()):
            if name in mandatory_items:
                continue
            opthelpstr += self.__class__._get_trait_desc(inputs, name, spec)

        if manhelpstr:
            helpstr += manhelpstr
        if opthelpstr:
            helpstr += opthelpstr
        return helpstr

    def _outputs_help(self):
        """ Prints description for output parameters
        """
        helpstr = ['Outputs::', '']
        if self.output_spec:
            outputs = self.output_spec()
            for name, spec in sorted(outputs.traits(transient=None).items()):
                helpstr += self.__class__._get_trait_desc(outputs, name, spec)
        if len(helpstr) == 2:
            helpstr += ['\tNone']
        return helpstr

    def _refs_help(self):
        """ Prints interface references.
        """
        if self.boutique_spec.get('tool-doi') is None:
            return []

        helpstr = ['References::', self.boutique_spec.get('tool-doi')]

        return helpstr
