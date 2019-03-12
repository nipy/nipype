# -*- coding: utf-8 -*-
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from builtins import str, open, bytes
# This tool exports a Nipype interface in the Boutiques (https://github.com/boutiques) JSON format.
# Boutiques tools can be imported in CBRAIN (https://github.com/aces/cbrain) among other platforms.
#
# Limitations:
#   * Optional outputs, i.e. outputs that not always produced, may not be detected. They will, however, still be listed
#     with a placeholder for the path template (either a value key or the output ID) that should be verified and corrected.

import os
import sys
import simplejson as json
import six

from ..scripts.instance import import_module


def generate_boutiques_descriptor(
        module, interface_name, container_image, container_type, container_index=None,
        verbose=False, save=False, save_path=None, author=None, ignore_inputs=None):
    '''
    Returns a JSON string containing a JSON Boutiques description of a Nipype interface.
    Arguments:
    * module: module where the Nipype interface is declared.
    * interface_name: name of Nipype interface.
    * container_image: name of the container image where the tool is installed
    * container_type: type of container image (Docker or Singularity)
    * container_index: optional index where the image is available
    * verbose: print information messages
    * save: True if you want to save descriptor to a file
    * save_path: file path for the saved descriptor (defaults to name of the interface in current directory)
    * author: author of the tool (required for publishing)
    * ignore_inputs: list of interface inputs to not include in the descriptor
    '''

    if not module:
        raise Exception("Undefined module.")

    # Retrieves Nipype interface
    if isinstance(module, (str, bytes)):
        import_module(module)
        module_name = str(module)
        module = sys.modules[module]
    else:
        module_name = str(module.__name__)

    interface = getattr(module, interface_name)()
    inputs = interface.input_spec()
    outputs = interface.output_spec()

    # Tool description
    tool_desc = {}
    tool_desc['name'] = interface_name
    tool_desc[
        'command-line'] = interface_name + " "
    tool_desc['author'] = "Nipype (interface)"
    if author is not None:
        tool_desc['author'] = tool_desc['author'] + ", " + author + " (tool)"
    tool_desc[
        'description'] = interface_name + ", as implemented in Nipype (module: " + module_name + ", interface: " + interface_name + ")."
    tool_desc['inputs'] = []
    tool_desc['output-files'] = []
    tool_desc['groups'] = []
    tool_desc['tool-version'] = interface.version if interface.version is not None else "No version provided."
    tool_desc['schema-version'] = '0.5'
    if container_image:
        tool_desc['container-image'] = {}
        tool_desc['container-image']['image'] = container_image
        tool_desc['container-image']['type'] = container_type
        if container_index:
            tool_desc['container-image']['index'] = container_index

    # Generates tool inputs
    for name, spec in sorted(interface.inputs.traits(transient=None).items()):
        input = get_boutiques_input(inputs, interface, name, spec, verbose, ignore_inputs=ignore_inputs)
        # Handle compound inputs (inputs that can be of multiple types and are mutually exclusive)
        if input is None:
            continue
        if isinstance(input, list):
            mutex_group_members = []
            tool_desc['command-line'] += input[0]['value-key'] + " "
            for i in input:
                tool_desc['inputs'].append(i)
                mutex_group_members.append(i['id'])
                if verbose:
                    print("-> Adding input " + i['name'])
            # Put inputs into a mutually exclusive group
            tool_desc['groups'].append({'id': input[0]['id'] + "_group",
                                        'name': input[0]['name'] + " group",
                                        'members': mutex_group_members,
                                        'mutually-exclusive': True})
        else:
            tool_desc['inputs'].append(input)
            tool_desc['command-line'] += input['value-key'] + " "
            if verbose:
                print("-> Adding input " + input['name'])

    # Generates input groups
    tool_desc['groups'] += get_boutiques_groups(interface.inputs.traits(transient=None).items())
    if len(tool_desc['groups']) == 0:
        del tool_desc['groups']

    # Generates tool outputs
    generate_tool_outputs(outputs, interface, tool_desc, verbose, True)

    # Generate outputs with various different inputs to try to generate
    # as many output values as possible
    custom_inputs = generate_custom_inputs(tool_desc['inputs'])

    for input_dict in custom_inputs:
        interface = getattr(module, interface_name)(**input_dict)
        outputs = interface.output_spec()
        generate_tool_outputs(outputs, interface, tool_desc, verbose, False)

    # Fill in all missing output paths
    for output in tool_desc['output-files']:
        if output['path-template'] == "":
            fill_in_missing_output_path(output, output['name'], tool_desc['inputs'])

    # Remove the extra space at the end of the command line
    tool_desc['command-line'] = tool_desc['command-line'].strip()

    # Save descriptor to a file
    if save:
        path = save_path if save_path is not None else os.path.join(os.getcwd(), interface_name + '.json')
        with open(path, 'w') as outfile:
            json.dump(tool_desc, outfile, indent=4, separators=(',', ': '))
        if verbose:
            print("-> Descriptor saved to file " + outfile.name)

    print("NOTE: Descriptors produced by this script may not entirely conform to the Nipype interface "
          "specs. Please check that the descriptor is correct before using it.")
    return json.dumps(tool_desc, indent=4, separators=(',', ': '))


def generate_tool_outputs(outputs, interface, tool_desc, verbose, first_run):
    for name, spec in sorted(outputs.traits(transient=None).items()):
        output = get_boutiques_output(outputs, name, spec, interface, tool_desc['inputs'])
        # If this is the first time we are generating outputs, add the full output to the descriptor.
        # Otherwise, find the existing output and update its path template if it's still undefined.
        if first_run:
            tool_desc['output-files'].append(output)
            if output.get('value-key'):
                tool_desc['command-line'] += output['value-key'] + " "
            if verbose:
                print("-> Adding output " + output['name'])
        else:
            for existing_output in tool_desc['output-files']:
                if output['id'] == existing_output['id'] and existing_output['path-template'] == "":
                    existing_output['path-template'] = output['path-template']
                    break
            if output.get('value-key') and output['value-key'] not in tool_desc['command-line']:
                tool_desc['command-line'] += output['value-key'] + " "

    if len(tool_desc['output-files']) == 0:
        raise Exception("Tool has no output.")


def get_boutiques_input(inputs, interface, input_name, spec, verbose, handler=None,
                        input_number=None, ignore_inputs=None):
    """
    Returns a dictionary containing the Boutiques input corresponding to a Nipype intput.

    Args:
      * inputs: inputs of the Nipype interface.
      * interface: Nipype interface.
      * input_name: name of the Nipype input.
      * spec: Nipype input spec.
      * verbose: print information messages.
      * handler: used when handling compound inputs, which don't have their own input spec
      * input_number: used when handling compound inputs to assign each a unique ID
      * ignore_inputs: list of interface inputs to not include in the descriptor

    Assumes that:
      * Input names are unique.
    """

    # If spec has a name source, means it's an output, so skip it here.
    # Also skip any ignored inputs
    if spec.name_source or ignore_inputs is not None and input_name in ignore_inputs:
        return None

    input = {}

    if input_number is not None and input_number != 0:  # No need to append a number to the first of a list of compound inputs
        input['id'] = input_name + "_" + str(input_number + 1)
    else:
        input['id'] = input_name

    input['name'] = input_name.replace('_', ' ').capitalize()

    if handler is None:
        trait_handler = spec.handler
    else:
        trait_handler = handler

    # Figure out the input type from its handler type
    handler_type = type(trait_handler).__name__

    # Deal with compound traits
    if handler_type == "TraitCompound":
        input_list = []
        # Recursively create an input for each trait
        for i in range(0, len(trait_handler.handlers)):
            inp = get_boutiques_input(inputs, interface, input_name, spec,
                                      verbose, trait_handler.handlers[i], i)
            inp['optional'] = True
            input_list.append(inp)
        return input_list

    if handler_type == "File" or handler_type == "Directory":
        input['type'] = "File"
    elif handler_type == "Int":
        input['type'] = "Number"
        input['integer'] = True
    elif handler_type == "Float":
        input['type'] = "Number"
    elif handler_type == "Bool":
        input['type'] = "Flag"
    else:
        input['type'] = "String"

    # Deal with range inputs
    if handler_type == "Range":
        input['type'] = "Number"
        if trait_handler._low is not None:
            input['minimum'] = trait_handler._low
        if trait_handler._high is not None:
            input['maximum'] = trait_handler._high
        if trait_handler._exclude_low:
            input['exclusive-minimum'] = True
        if trait_handler._exclude_high:
            input['exclusive-maximum'] = True

    # Deal with list inputs
    # TODO handle lists of lists (e.g. FSL ProbTrackX seed input)
    if handler_type == "List":
        input['list'] = True
        trait_type = type(trait_handler.item_trait.trait_type).__name__
        if trait_type == "Int":
            input['integer'] = True
            input['type'] = "Number"
        elif trait_type == "Float":
            input['type'] = "Number"
        elif trait_type == "File":
            input['type'] = "File"
        else:
            input['type'] = "String"
        if trait_handler.minlen != 0:
            input['min-list-entries'] = trait_handler.minlen
        if trait_handler.maxlen != six.MAXSIZE:
            input['max-list-entries'] = trait_handler.maxlen

    # Deal with multi-input
    if handler_type == "InputMultiObject":
        input['type'] = "File"
        input['list'] = True

    input['value-key'] = "[" + input_name.upper(
    ) + "]"  # assumes that input names are unique

    # Add the command line flag specified by argstr
    # If no argstr is provided and input type is Flag, create a flag from the name
    if spec.argstr and spec.argstr.split("%")[0]:
        input['command-line-flag'] = spec.argstr.split("%")[0].strip()
    elif input['type'] == "Flag":
        input['command-line-flag'] = ("--%s" % input_name + " ").strip()

    input['description'] = get_description_from_spec(inputs, input_name, spec)
    if not (hasattr(spec, "mandatory") and spec.mandatory):
        input['optional'] = True
    else:
        input['optional'] = False
    if spec.usedefault:
        input['default-value'] = spec.default_value()[1]

    try:
        value_choices = trait_handler.values
    except AttributeError:
        pass
    else:
        if value_choices is not None:
            if all(isinstance(n, int) for n in value_choices):
                input['type'] = "Number"
                input['integer'] = True
            elif all(isinstance(n, float) for n in value_choices):
                input['type'] = "Number"
            input['value-choices'] = value_choices

    # Set Boolean types to Flag (there is no Boolean type in Boutiques)
    if input['type'] == "Boolean":
        input['type'] = "Flag"

    return input


def get_boutiques_output(outputs, name, spec, interface, tool_inputs):
    """
    Returns a dictionary containing the Boutiques output corresponding to a Nipype output.

    Args:
      * outputs: outputs of the Nipype interface.
      * name: name of the Nipype output.
      * spec: Nipype output spec.
      * interface: Nipype interface.
      * tool_inputs: list of tool inputs (as produced by method get_boutiques_input).

    Assumes that:
      * Output names are unique.
      * Input values involved in the path template are defined.
      * Output files are written in the current directory.
      * There is a single output value (output lists are not supported).
    """
    output = {}
    output['name'] = name.replace('_', ' ').capitalize()

    # Check if the output name was already used as an input name
    # If so, append '_outfile' to the end of the ID
    unique_id = True
    for inp in tool_inputs:
        if inp['id'] == name:
            unique_id = False
            break
    output['id'] = name if unique_id else name + '_outfile'

    output['path-template'] = ""
    output[
        'optional'] = True  # no real way to determine if an output is always produced, regardless of the input values.

    output['description'] = get_description_from_spec(outputs, name, spec)

    # Path template creation.

    try:
        output_value = interface._list_outputs()[name]
    except TypeError:
        output_value = None
    except AttributeError:
        output_value = None

    # Handle multi-outputs
    if isinstance(output_value, list):
        output['list'] = True
        # Check if all extensions are the same
        extensions = []
        for val in output_value:
            extensions.append(os.path.splitext(val)[1])
        # If extensions all the same, set path template as wildcard + extension
        # Otherwise just use a wildcard
        if len(set(extensions)) == 1:
            output['path-template'] = "*" + extensions[0]
        else:
            output['path-template'] = "*"
        return output

    # If an output value is defined, use its relative path, if one exists.
    # If no relative path, look for an input with the same name containing a name source
    # and name template. Otherwise, put blank string as placeholder and try to fill it on
    # another iteration.
    output['path-template'] = ""

    if output_value:
        output['path-template'] = os.path.relpath(output_value)
    else:
        for inp_name, inp_spec in sorted(interface.inputs.traits(transient=None).items()):
            if inp_name == name and inp_spec.name_source and inp_spec.name_template:
                if isinstance(inp_spec.name_source, list):
                    source = inp_spec.name_source[0]
                else:
                    source = inp_spec.name_source
                output['path-template'] = inp_spec.name_template.replace("%s", "[" + source.upper() + "]")
                output['value-key'] = "[" + name.upper() + "]"
                if inp_spec.argstr and inp_spec.argstr.split("%")[0]:
                    output['command-line-flag'] = inp_spec.argstr.split("%")[0].strip()
                break

    return output


def get_boutiques_groups(input_traits):
    """
    Returns a list of dictionaries containing Boutiques groups for the mutually exclusive and all-or-none Nipype inputs.
    """
    desc_groups = []
    all_or_none_input_sets = []
    mutex_input_sets = []

    # Get all the groups
    for name, spec in input_traits:
        if spec.requires is not None:
            group_members = set([name] + list(spec.requires))
            if group_members not in all_or_none_input_sets:
                all_or_none_input_sets.append(group_members)
        if spec.xor is not None:
            group_members = set([name] + list(spec.xor))
            if group_members not in mutex_input_sets:
                mutex_input_sets.append(group_members)

    # Create a dictionary for each one
    for i in range(0, len(all_or_none_input_sets)):
        desc_groups.append({'id': "all_or_none_group" + ("_" + str(i + 1) if i != 0 else ""),
                            'name': "All or none group" + (" " + str(i + 1) if i != 0 else ""),
                            'members': list(all_or_none_input_sets[i]),
                            'all-or-none': True})

    for i in range(0, len(mutex_input_sets)):
        desc_groups.append({'id': "mutex_group" + ("_" + str(i + 1) if i != 0 else ""),
                            'name': "Mutex group" + (" " + str(i + 1) if i != 0 else ""),
                            'members': list(mutex_input_sets[i]),
                            'mutually-exclusive': True})

    return desc_groups


def get_description_from_spec(object, name, spec):
    '''
    Generates a description based on the input or output spec.
    '''
    if not spec.desc:
        spec.desc = "No description provided."
    spec_info = spec.full_info(object, name, None)

    boutiques_description = (spec_info.capitalize(
    ) + ". " + spec.desc.capitalize()).replace("\n", '')

    if not boutiques_description.endswith('.'):
        boutiques_description += '.'

    return boutiques_description


def fill_in_missing_output_path(output, output_name, tool_inputs):
    '''
    Creates a path template for outputs that are missing one
    This is needed for the descriptor to be valid (path template is required)
    '''
    # Look for an input with the same name as the output and use its value key
    found = False
    for input in tool_inputs:
        if input['name'] == output_name:
            output['path-template'] = input['value-key']
            found = True
            break
    # If no input with the same name was found, use the output ID
    if not found:
        output['path-template'] = output['id']
    return output


def generate_custom_inputs(desc_inputs):
    '''
    Generates a bunch of custom input dictionaries in order to generate as many outputs as possible
    (to get their path templates)
    Currently only works with flag inputs and inputs with defined value choices.
    '''
    custom_input_dicts = []
    for desc_input in desc_inputs:
        if desc_input['type'] == 'Flag':
            custom_input_dicts.append({desc_input['id']: True})
        elif desc_input.get('value-choices'):
            for value in desc_input['value-choices']:
                custom_input_dicts.append({desc_input['id']: value})
    return custom_input_dicts
