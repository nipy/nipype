# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import json
from collections import defaultdict

from ... import logging
from ..base import (
    traits, File, Str, isdefined, Undefined,
    DynamicTraitedSpec, CommandLine)

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

        super().__init__()

        self._xors = defaultdict(list)
        self._requires = defaultdict(list)
        self._one_required = defaultdict(list)
        self._load_groups(boutique_spec.get('groups', []))

        self._populate_input_spec(boutique_spec.get('inputs', []))
        self._populate_output_spec(boutique_spec.get('output-files', []))
        self.inputs.trait_set(trait_change_notify=False, **inputs)

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

    def _populate_input_spec(self, input_list):
        value_keys = {}
        undefined_traits = {}
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
            self.inputs.add_trait(trait_name, trait)
            if not trait.usedefault:
                undefined_traits[trait_name] = Undefined
            value_keys[input_dict['value-key']] = trait_name

        self.inputs.trait_set(trait_change_notify=False,
                              **undefined_traits)
        self.value_keys = value_keys

    def _populate_output_spec(self, output_list):
        self.outputs = self.output_spec()
        value_keys = {}
        for output_dict in output_list:
            trait_name = output_dict['id']
            ttype = traits.File
            metadata = {}
            args = [Undefined]

            if output_dict.get('list'):
                metadata['trait'] = ttype
                ttype = traits.List
                args = []

            if output_dict.get('description') is not None:
                metadata['desc'] = output_dict['description']

            metadata['mandatory'] = not output_dict.get('optional', False)

            if 'command-line-flag' in output_dict:
                argstr = output_dict['command-line-flag']
                argstr += output_dict.get('command-line-flag-separator', ' ')
                argstr += '%s'  # May be insufficient for some
                metadata['argstr'] = argstr

            trait = ttype(*args, **metadata)
            self.outputs.add_trait(trait_name, trait)

            if 'value-key' in output_dict:
                value_keys[output_dict['value-key']] = trait_name

        self.value_keys.update(value_keys)

    def _list_outputs(self):
        # NOTE
        # currently, boutiques doesn't provide a mechanism to determine which
        # input parameters will cause generation of output files if the outputs
        # are set as optional. this makes handling which outputs should be
        # defined a bit difficult... for now, i'm defining everything and will
        # think about a better way to handle this in the future
        output_list = self.boutique_spec.get('output-files', [])
        outputs = self.outputs.get()

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

            # TODO: check whether output should actually be defined (see above)
            outputs[out] = output_filename

        return outputs

    def cmdline(self):
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
