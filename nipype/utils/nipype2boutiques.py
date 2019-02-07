# -*- coding: utf-8 -*-
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from builtins import str, open, bytes
# This tool exports a Nipype interface in the Boutiques (https://github.com/boutiques) JSON format.
# Boutiques tools can be imported in CBRAIN (https://github.com/aces/cbrain) among other platforms.
#
# Limitations:
#   * List outputs are not supported.
#   * Default values are not extracted from the documentation of the Nipype interface.
#   * The following input types must be ignored for the output path template creation (see option -t):
#     ** String restrictions, i.e. String inputs that accept only a restricted set of values.
#     ** mutually exclusive inputs.
#   * Path-templates are wrong when output files are not created in the execution directory (e.g. when a sub-directory is created).
#   * Optional outputs, i.e. outputs that not always produced, may not be detected.

import os
import argparse
import sys
import tempfile
import simplejson as json

from ..scripts.instance import import_module


def generate_boutiques_descriptor(
        module, interface_name, ignored_template_inputs, container_image,
        container_index, container_type, verbose, ignore_template_numbers):
    '''
    Returns a JSON string containing a JSON Boutiques description of a Nipype interface.
    Arguments:
    * module: module where the Nipype interface is declared.
    * interface_name: name of Nipype interface.
    * ignored_template_inputs: a list of input names that should be ignored in the generation of output path templates.
    * ignore_template_numbers: True if numbers must be ignored in output path creations.
    * container_image: name of the container image where the tool is installed
    * container_index: optional index where the image is available
    * container_type: type of container image (Docker or Singularity)
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
        'command-line'] = "nipype_cmd " + module_name + " " + interface_name + " "
    tool_desc[
        'description'] = interface_name + ", as implemented in Nipype (module: " + module_name + ", interface: " + interface_name + ")."
    tool_desc['inputs'] = []
    tool_desc['output-files'] = []
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
        input = get_boutiques_input(inputs, interface, name, spec,
                                    ignored_template_inputs, verbose,
                                    ignore_template_numbers)
        tool_desc['inputs'].append(input)
        tool_desc['command-line'] += input['value-key'] + " "
        if verbose:
            print("-> Adding input " + input['name'])

    # Generates tool outputs
    for name, spec in sorted(outputs.traits(transient=None).items()):
        output = get_boutiques_output(outputs, name, spec, interface, tool_desc['inputs'],
                                      verbose)
        if output['path-template'] != "":
            tool_desc['output-files'].append(output)
            if verbose:
                print("-> Adding output " + output['name'])
        elif verbose:
            print("xx Skipping output " + output['name'] +
                  " with no path template.")
    if tool_desc['output-files'] == []:
        raise Exception("Tool has no output.")

    # Removes all temporary values from inputs (otherwise they will
    # appear in the JSON output)
    for input in tool_desc['inputs']:
        del input['tempvalue']

    # Save descriptor to a file
    with open(interface_name + '.json', 'w') as outfile:
        json.dump(tool_desc, outfile)

    print("NOTE: Descriptors produced by this script may not entirely conform to the Nipype interface "
          "specs. Please check that the descriptor is correct before using it.")
    return json.dumps(tool_desc, indent=4, separators=(',', ': '))


def get_boutiques_input(inputs, interface, input_name, spec,
                        ignored_template_inputs, verbose,
                        ignore_template_numbers):
    """
    Returns a dictionary containing the Boutiques input corresponding to a Nipype intput.

    Args:
      * inputs: inputs of the Nipype interface.
      * interface: Nipype interface.
      * input_name: name of the Nipype input.
      * spec: Nipype input spec.
      * ignored_template_inputs: input names for which no temporary value must be generated.
      * ignore_template_numbers: True if numbers must be ignored in output path creations.

    Assumes that:
      * Input names are unique.
    """
    spec_info = spec.full_info(inputs, input_name, None)

    input = {}
    input['id'] = input_name
    input['name'] = input_name.replace('_', ' ').capitalize()

    # Figure out the input type from its handler type
    input_type = get_type_from_handler_type(spec.handler)
    input['type'] = input_type[0]
    if input_type[1]:
        input['integer'] = True

    input['list'] = is_list(spec_info)
    input['value-key'] = "[" + input_name.upper(
    ) + "]"  # assumes that input names are unique
    input['command-line-flag'] = ("--%s" % input_name + " ").strip()
    input['tempvalue'] = None
    input['description'] = get_description_from_spec(inputs, input_name, spec)
    if not (hasattr(spec, "mandatory") and spec.mandatory):
        input['optional'] = True
    else:
        input['optional'] = False
    if spec.usedefault:
        input['default-value'] = spec.default_value()[1]

    try:
        value_choices = spec.handler.values
    except AttributeError:
        pass
    else:
        if value_choices is not None:
            input['value-choices'] = value_choices

    # Create unique, temporary value.
    temp_value = must_generate_value(input_name, input['type'],
                                     ignored_template_inputs, spec_info, spec,
                                     ignore_template_numbers)
    if temp_value:
        tempvalue = get_unique_value(input['type'], input_name)
        setattr(interface.inputs, input_name, tempvalue)
        input['tempvalue'] = tempvalue
        if verbose:
            print("oo Path-template creation using " + input['id'] + "=" +
                  str(tempvalue))

    # Now that temp values have been generated, set Boolean types to
    # Flag (there is no Boolean type in Boutiques)
    if input['type'] == "Boolean":
        input['type'] = "Flag"

    return input


def get_boutiques_output(outputs, name, spec, interface, tool_inputs, verbose=False):
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

    output_value = interface._list_outputs()[name]

    # If output value is defined, use its basename
    if output_value != "" and isinstance(
            output_value,
            str):  # FIXME: this crashes when there are multiple output values.
        # Go find from which input value it was built
        for input in tool_inputs:
            if not input['tempvalue']:
                continue
            input_value = input['tempvalue']
            if input['type'] == "File":
                # Take the base name
                input_value = os.path.splitext(
                    os.path.basename(input_value))[0]
            if str(input_value) in output_value:
                output_value = os.path.basename(
                    output_value.replace(input_value,
                                         input['value-key'])
                )  # FIXME: this only works if output is written in the current directory
        output['path-template'] = os.path.basename(output_value)

    # If output value is undefined, create a placeholder for the path template
    if not output_value:
        # Look for an input with the same name and use this as the path template
        found = False
        for input in tool_inputs:
            if input['id'] == name:
                output['path-template'] = input['value-key']
                found = True
                break
        # If no input with the same name was found, warn the user they should provide it manually
        if not found:
            print("WARNING: Could not determine path template for output %s. Please provide one for the "
                  "descriptor manually." % name)
            output['path-template'] = "WARNING: No path template provided."
    return output


# TODO remove this once we know get_type_from_handler_type works well
def get_type_from_spec_info(spec_info):
    '''
    Returns an input type from the spec info. There must be a better
    way to get an input type in Nipype than to parse the spec info.
    '''
    if ("an existing file name" in spec_info) or (
            "input volumes" in spec_info):
        return "File"
    elif ("an integer" in spec_info or "a float" in spec_info):
        return "Number"
    elif "a boolean" in spec_info:
        return "Boolean"
    return "String"


def get_type_from_handler_type(handler):
    '''
    Gets the input type from the spec handler type.
    Returns a tuple containing the type and a boolean to specify
    if the type is an integer.
    '''
    handler_type = type(handler).__name__
    print("TYPE", handler_type)
    if handler_type == "File" or handler_type == "Directory":
        return "File", False
    elif handler_type == "Int" or handler_type == "Float":
        return "Number", handler_type == "Int"
    elif handler_type == "Bool":
        return "Flag", False
    else:
        return "String", False

def is_list(spec_info):
    '''
    Returns True if the spec info looks like it describes a list
    parameter. There must be a better way in Nipype to check if an input
    is a list.
    '''
    if "a list" in spec_info:
        return True
    return False


def get_unique_value(type, id):
    '''
    Returns a unique value of type 'type', for input with id 'id',
    assuming id is unique.
    '''
    return {
        "File": os.path.abspath(create_tempfile()),
        "Boolean": True,
        "Number": abs(hash(id)),  # abs in case input param must be positive...
        "String": id
    }[type]


def create_tempfile():
    '''
    Creates a temp file and returns its name.
    '''
    fileTemp = tempfile.NamedTemporaryFile(delete=False)
    fileTemp.write(b"hello")
    fileTemp.close()
    return fileTemp.name


def must_generate_value(name, type, ignored_template_inputs, spec_info, spec,
                        ignore_template_numbers):
    '''
    Return True if a temporary value must be generated for this input.
    Arguments:
    * name: input name.
    * type: input_type.
    * ignored_template_inputs: a list of inputs names for which no value must be generated.
    * spec_info: spec info of the Nipype input
    * ignore_template_numbers: True if numbers must be ignored.
    '''
    # Return false when type is number and numbers must be ignored.
    if ignore_template_numbers and type == "Number":
        return False
    # Only generate value for the first element of mutually exclusive inputs.
    if spec.xor and spec.xor[0] != name:
        return False
    # Directory types are not supported
    if "an existing directory name" in spec_info:
        return False
    # Don't know how to generate a list.
    if "a list" in spec_info or "a tuple" in spec_info:
        return False
    # Don't know how to generate a dictionary.
    if "a dictionary" in spec_info:
        return False
    # Best guess to detect string restrictions...
    if "' or '" in spec_info:
        return False
    if spec.default or spec.default_value():
        return False
    if not ignored_template_inputs:
        return True
    return not (name in ignored_template_inputs)


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
