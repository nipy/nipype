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
        #self._populate_output_spec(boutique_spec.get('output-files', []))
        self.inputs.trait_set(trait_change_notify=False, **inputs)

    def _load_groups(self, groups):
        for group in groups:
            members = group['members']
            if group['all-or-none']:
                for member in members:
                    self._requires[member].extend(members)
            elif group['mutually-exclusive']:
                for member in members:
                    self._xors[member].extend(members)
            elif group['one-is-required']:
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
                if args:
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
                                    []).extend(self._xor[trait_name])

            trait = ttype(*args, **metadata)
            self.inputs.add_trait(trait_name, trait)
            if not trait.usedefault:
                undefined_traits[trait_name] = Undefined
            value_keys[input_dict['value-key']] = trait_name

        self.inputs.trait_set(trait_change_notify=False,
                              **undefined_traits)
        self.value_keys = value_keys

    def cmdline(self):
        args = self._argspec
        inputs = self.inputs.trait_get()
        for valkey, name in self.value_keys.items():
            spec = self.inputs.traits()[name]
            value = inputs[name]

            if not isdefined(value):
                value = ''
            elif spec.argstr:
                value = self._format_arg(name, spec, value)
            args = args.replace(valkey, value)
        return self._cmd + ' ' + args
