# This tool exports a Nipype interface in the Boutiques
# (https://github.com/boutiques) JSON format. Boutiques tools
# can be imported in CBRAIN (https://github.com/aces/cbrain)
# among other platforms.
#
# Limitations:
#   * Optional outputs, i.e. outputs that not always produced, may not be
#     detected. They will, however, still be listed with a placeholder for
#     the path template (either a value key or the output ID) that should
#     be verified and corrected.
#   * Still need to add some fields to the descriptor manually, e.g. url,
#     descriptor-url, path-template-stripped-extensions, etc.

import os
import sys
import simplejson as json

from ..scripts.instance import import_module


def generate_boutiques_descriptor(
    module,
    interface_name,
    container_image,
    container_type,
    container_index=None,
    verbose=False,
    save=False,
    save_path=None,
    author=None,
    ignore_inputs=None,
    tags=None,
):
    """
    Generate a JSON Boutiques description of a Nipype interface.

    Arguments
    ---------
    module :
        module where the Nipype interface is declared.
    interface_name :
        name of Nipype interface.
    container_image :
        name of the container image where the tool is installed
    container_type :
        type of container image (Docker or Singularity)
    container_index :
        optional index where the image is available
    verbose :
        print information messages
    save :
        True if you want to save descriptor to a file
    save_path :
        file path for the saved descriptor (defaults to name of the
      interface in current directory)
    author :
        author of the tool (required for publishing)
    ignore_inputs :
        list of interface inputs to not include in the descriptor
    tags :
        JSON object containing tags to include in the descriptor,
        e.g. ``{"key1": "value1"}`` (note: the tags 'domain:neuroinformatics'
        and 'interface-type:nipype' are included by default)

    Returns
    -------
    boutiques : str
       string containing a Boutiques' JSON object

    """
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
    tool_desc["name"] = interface_name
    tool_desc["command-line"] = interface_name + " "
    tool_desc["author"] = "Nipype (interface)"
    if author is not None:
        tool_desc["author"] = tool_desc["author"] + ", " + author + " (tool)"
    tool_desc["description"] = (
        interface_name
        + ", as implemented in Nipype (module: "
        + module_name
        + ", interface: "
        + interface_name
        + ")."
    )
    tool_desc["inputs"] = []
    tool_desc["output-files"] = []
    tool_desc["groups"] = []
    tool_desc["tool-version"] = (
        interface.version if interface.version is not None else "1.0.0"
    )
    tool_desc["schema-version"] = "0.5"
    if container_image:
        tool_desc["container-image"] = {}
        tool_desc["container-image"]["image"] = container_image
        tool_desc["container-image"]["type"] = container_type
        if container_index:
            tool_desc["container-image"]["index"] = container_index

    # Generates tool inputs
    for name, spec in sorted(interface.inputs.traits(transient=None).items()):
        # Skip ignored inputs
        if ignore_inputs is not None and name in ignore_inputs:
            continue
        # If spec has a name source, this means it actually represents an
        # output, so create a Boutiques output from it
        elif spec.name_source and spec.name_template:
            tool_desc["output-files"].append(
                get_boutiques_output_from_inp(inputs, spec, name)
            )
        else:
            inp = get_boutiques_input(inputs, interface, name, spec, verbose)
            # Handle compound inputs (inputs that can be of multiple types
            # and are mutually exclusive)
            if isinstance(inp, list):
                mutex_group_members = []
                tool_desc["command-line"] += inp[0]["value-key"] + " "
                for i in inp:
                    tool_desc["inputs"].append(i)
                    mutex_group_members.append(i["id"])
                    if verbose:
                        print("-> Adding input " + i["name"])
                # Put inputs into a mutually exclusive group
                tool_desc["groups"].append(
                    {
                        "id": inp[0]["id"] + "_group",
                        "name": inp[0]["name"] + " group",
                        "members": mutex_group_members,
                        "mutually-exclusive": True,
                    }
                )
            else:
                tool_desc["inputs"].append(inp)
                tool_desc["command-line"] += inp["value-key"] + " "
                if verbose:
                    print("-> Adding input " + inp["name"])

    # Generates input groups
    tool_desc["groups"] += get_boutiques_groups(
        interface.inputs.traits(transient=None).items()
    )
    if len(tool_desc["groups"]) == 0:
        del tool_desc["groups"]

    # Generates tool outputs
    generate_tool_outputs(outputs, interface, tool_desc, verbose, True)

    # Generate outputs with various different inputs to try to generate
    # as many output values as possible
    custom_inputs = generate_custom_inputs(tool_desc["inputs"])

    for input_dict in custom_inputs:
        interface = getattr(module, interface_name)(**input_dict)
        outputs = interface.output_spec()
        generate_tool_outputs(outputs, interface, tool_desc, verbose, False)

    # Fill in all missing output paths
    for output in tool_desc["output-files"]:
        if output["path-template"] == "":
            fill_in_missing_output_path(output, output["name"], tool_desc["inputs"])

    # Add tags
    desc_tags = {"domain": "neuroinformatics", "source": "nipype-interface"}

    if tags is not None:
        tags_dict = json.loads(tags)
        for k, v in tags_dict.items():
            if k in desc_tags:
                if not isinstance(desc_tags[k], list):
                    desc_tags[k] = [desc_tags[k]]
                desc_tags[k].append(v)
            else:
                desc_tags[k] = v

    tool_desc["tags"] = desc_tags

    # Check for positional arguments and reorder command line args if necessary
    tool_desc["command-line"] = reorder_cmd_line_args(
        tool_desc["command-line"], interface, ignore_inputs
    )

    # Remove the extra space at the end of the command line
    tool_desc["command-line"] = tool_desc["command-line"].strip()

    # Save descriptor to a file
    if save:
        path = save_path or os.path.join(os.getcwd(), interface_name + ".json")
        with open(path, "w") as outfile:
            json.dump(tool_desc, outfile, indent=4, separators=(",", ": "))
        if verbose:
            print("-> Descriptor saved to file " + outfile.name)

    print(
        "NOTE: Descriptors produced by this script may not entirely conform "
        "to the Nipype interface specs. Please check that the descriptor is "
        "correct before using it."
    )
    return json.dumps(tool_desc, indent=4, separators=(",", ": "))


def generate_tool_outputs(outputs, interface, tool_desc, verbose, first_run):
    for name, spec in sorted(outputs.traits(transient=None).items()):
        output = get_boutiques_output(
            outputs, name, spec, interface, tool_desc["inputs"]
        )
        # If this is the first time we are generating outputs, add the full
        # output to the descriptor. Otherwise, find the existing output and
        # update its path template if it's still undefined.
        if first_run:
            tool_desc["output-files"].append(output)
            if output.get("value-key"):
                tool_desc["command-line"] += output["value-key"] + " "
            if verbose:
                print("-> Adding output " + output["name"])
        else:
            for existing_output in tool_desc["output-files"]:
                if (
                    output["id"] == existing_output["id"]
                    and existing_output["path-template"] == ""
                ):
                    existing_output["path-template"] = output["path-template"]
                    break
            if (
                output.get("value-key")
                and output["value-key"] not in tool_desc["command-line"]
            ):
                tool_desc["command-line"] += output["value-key"] + " "

    if len(tool_desc["output-files"]) == 0:
        raise Exception("Tool has no output.")


def get_boutiques_input(
    inputs, interface, input_name, spec, verbose, handler=None, input_number=None
):
    """
    Returns a dictionary containing the Boutiques input corresponding
    to a Nipype input.

    Args:
      * inputs: inputs of the Nipype interface.
      * interface: Nipype interface.
      * input_name: name of the Nipype input.
      * spec: Nipype input spec.
      * verbose: print information messages.
      * handler: used when handling compound inputs, which don't have their
        own input spec
      * input_number: used when handling compound inputs to assign each a
        unique ID

    Assumes that:
      * Input names are unique.
    """
    inp = {}

    # No need to append a number to the first of a list of compound inputs
    if input_number:
        inp["id"] = input_name + "_" + str(input_number + 1)
    else:
        inp["id"] = input_name

    inp["name"] = input_name.replace("_", " ").capitalize()

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
        for i in range(len(trait_handler.handlers)):
            inp = get_boutiques_input(
                inputs,
                interface,
                input_name,
                spec,
                verbose,
                trait_handler.handlers[i],
                i,
            )
            inp["optional"] = True
            input_list.append(inp)
        return input_list

    if handler_type == "File" or handler_type == "Directory":
        inp["type"] = "File"
    elif handler_type == "Int":
        inp["type"] = "Number"
        inp["integer"] = True
    elif handler_type == "Float":
        inp["type"] = "Number"
    elif handler_type == "Bool":
        inp["type"] = "Flag"
    else:
        inp["type"] = "String"

    # Deal with range inputs
    if handler_type == "Range":
        inp["type"] = "Number"
        if trait_handler._low is not None:
            inp["minimum"] = trait_handler._low
        if trait_handler._high is not None:
            inp["maximum"] = trait_handler._high
        if trait_handler._exclude_low:
            inp["exclusive-minimum"] = True
        if trait_handler._exclude_high:
            inp["exclusive-maximum"] = True

    # Deal with list inputs
    # TODO handle lists of lists (e.g. FSL ProbTrackX seed input)
    if handler_type == "List":
        inp["list"] = True
        item_type = trait_handler.item_trait.trait_type
        item_type_name = type(item_type).__name__
        if item_type_name == "Int":
            inp["integer"] = True
            inp["type"] = "Number"
        elif item_type_name == "Float":
            inp["type"] = "Number"
        elif item_type_name == "File":
            inp["type"] = "File"
        elif item_type_name == "Enum":
            value_choices = item_type.values
            if value_choices is not None:
                if all(isinstance(n, int) for n in value_choices):
                    inp["type"] = "Number"
                    inp["integer"] = True
                elif all(isinstance(n, float) for n in value_choices):
                    inp["type"] = "Number"
                inp["value-choices"] = value_choices
        else:
            inp["type"] = "String"
        if trait_handler.minlen != 0:
            inp["min-list-entries"] = trait_handler.minlen
        if trait_handler.maxlen != sys.maxsize:
            inp["max-list-entries"] = trait_handler.maxlen
        if spec.sep:
            inp["list-separator"] = spec.sep

    if handler_type == "Tuple":
        inp["list"] = True
        inp["min-list-entries"] = len(spec.default)
        inp["max-list-entries"] = len(spec.default)
        input_type = type(spec.default[0]).__name__
        if input_type == "int":
            inp["type"] = "Number"
            inp["integer"] = True
        elif input_type == "float":
            inp["type"] = "Number"
        else:
            inp["type"] = "String"

    # Deal with multi-input
    if handler_type == "InputMultiObject":
        inp["type"] = "File"
        inp["list"] = True
        if spec.sep:
            inp["list-separator"] = spec.sep

    inp["value-key"] = (
        "[" + input_name.upper() + "]"
    )  # assumes that input names are unique

    flag, flag_sep = get_command_line_flag(spec, inp["type"] == "Flag", input_name)

    if flag is not None:
        inp["command-line-flag"] = flag
    if flag_sep is not None:
        inp["command-line-flag-separator"] = flag_sep

    inp["description"] = get_description_from_spec(inputs, input_name, spec)
    if not (hasattr(spec, "mandatory") and spec.mandatory):
        inp["optional"] = True
    else:
        inp["optional"] = False
    if spec.usedefault:
        inp["default-value"] = spec.default_value()[1]
    if spec.requires is not None:
        inp["requires-inputs"] = spec.requires

    try:
        value_choices = trait_handler.values
    except AttributeError:
        pass
    else:
        if value_choices is not None:
            if all(isinstance(n, int) for n in value_choices):
                inp["type"] = "Number"
                inp["integer"] = True
            elif all(isinstance(n, float) for n in value_choices):
                inp["type"] = "Number"
            inp["value-choices"] = value_choices

    return inp


def get_boutiques_output(outputs, name, spec, interface, tool_inputs):
    """
    Returns a dictionary containing the Boutiques output corresponding
    to a Nipype output.

    Args:
      * outputs: outputs of the Nipype interface.
      * name: name of the Nipype output.
      * spec: Nipype output spec.
      * interface: Nipype interface.
      * tool_inputs: list of tool inputs (as produced by method
        get_boutiques_input).

    Assumes that:
      * Output names are unique.
      * Input values involved in the path template are defined.
      * Output files are written in the current directory.
      * There is a single output value (output lists are not supported).
    """
    output = {}
    output["name"] = name.replace("_", " ").capitalize()

    # Check if the output name was already used as an input name
    # If so, append '_outfile' to the end of the ID
    unique_id = True
    for inp in tool_inputs:
        if inp["id"] == name:
            unique_id = False
            break
    output["id"] = name if unique_id else name + "_outfile"

    output["path-template"] = ""

    # No real way to determine if an output is always
    # produced, regardless of the input values.
    output["optional"] = True

    output["description"] = get_description_from_spec(outputs, name, spec)

    # Path template creation.

    try:
        output_value = interface._list_outputs()[name]
    except TypeError:
        output_value = None
    except AttributeError:
        output_value = None
    except KeyError:
        output_value = None

    # Handle multi-outputs
    if (
        isinstance(output_value, list)
        or type(spec.handler).__name__ == "OutputMultiObject"
        or type(spec.handler).__name__ == "List"
    ):
        output["list"] = True
        if output_value:
            # Check if all extensions are the same
            extensions = {os.path.splitext(val)[1] for val in output_value}
            # If extensions all the same, set path template as
            # wildcard + extension. Otherwise just use a wildcard
            if len(extensions) == 1:
                output["path-template"] = "*" + extensions.pop()
            else:
                output["path-template"] = "*"
            return output

    # If an output value is defined, use its relative path, if one exists.
    # Otherwise, put blank string as placeholder and try to fill it on
    # another iteration.
    if output_value:
        output["path-template"] = os.path.relpath(output_value)
    else:
        output["path-template"] = ""

    return output


def get_boutiques_groups(input_traits):
    """
    Returns a list of dictionaries containing Boutiques groups for the mutually
    exclusive Nipype inputs.
    """
    desc_groups = []
    mutex_input_sets = []

    # Get all the groups
    for name, spec in input_traits:
        if spec.xor is not None:
            group_members = set([name] + list(spec.xor))
            if group_members not in mutex_input_sets:
                mutex_input_sets.append(group_members)

    # Create a dictionary for each one
    for i, inp_set in enumerate(mutex_input_sets, 1):
        desc_groups.append(
            {
                "id": "mutex_group" + ("_" + str(i) if i != 1 else ""),
                "name": "Mutex group" + (" " + str(i) if i != 1 else ""),
                "members": list(inp_set),
                "mutually-exclusive": True,
            }
        )

    return desc_groups


def get_description_from_spec(obj, name, spec):
    """
    Generates a description based on the input or output spec.
    """
    if not spec.desc:
        spec.desc = "No description provided."
    spec_info = spec.full_info(obj, name, None)

    boutiques_description = (
        spec_info.capitalize() + ". " + spec.desc.capitalize()
    ).replace("\n", "")

    if not boutiques_description.endswith("."):
        boutiques_description += "."

    return boutiques_description


def fill_in_missing_output_path(output, output_name, tool_inputs):
    """
    Creates a path template for outputs that are missing one
    This is needed for the descriptor to be valid (path template is required)
    """
    # Look for an input with the same name as the output and use its value key
    found = False
    for input in tool_inputs:
        if input["name"] == output_name:
            output["path-template"] = input["value-key"]
            found = True
            break
    # If no input with the same name was found, use the output ID
    if not found:
        output["path-template"] = output["id"]
    return output


def generate_custom_inputs(desc_inputs):
    """
    Generates a bunch of custom input dictionaries in order to generate
    as many outputs as possible (to get their path templates).
    Currently only works with flag inputs and inputs with defined value
    choices.
    """
    custom_input_dicts = []
    for desc_input in desc_inputs:
        if desc_input["type"] == "Flag":
            custom_input_dicts.append({desc_input["id"]: True})
        elif desc_input.get("value-choices") and not desc_input.get("list"):
            custom_input_dicts.extend(
                {desc_input["id"]: value} for value in desc_input["value-choices"]
            )
    return custom_input_dicts


def reorder_cmd_line_args(cmd_line, interface, ignore_inputs=None):
    """
    Generates a new command line with the positional arguments in the
    correct order
    """
    interface_name = cmd_line.split()[0]
    positional_arg_dict = {}
    positional_args = []
    non_positional_args = []

    for name, spec in sorted(interface.inputs.traits(transient=None).items()):
        if ignore_inputs is not None and name in ignore_inputs:
            continue
        value_key = "[" + name.upper() + "]"
        if spec.position is not None:
            positional_arg_dict[spec.position] = value_key
        else:
            non_positional_args.append(value_key)

    last_arg = None
    for item in sorted(positional_arg_dict.items()):
        if item[0] == -1:
            last_arg = item[1]
            continue
        positional_args.append(item[1])

    return (
        interface_name
        + " "
        + ((" ".join(positional_args) + " ") if len(positional_args) > 0 else "")
        + ((last_arg + " ") if last_arg else "")
        + " ".join(non_positional_args)
    )


def get_command_line_flag(input_spec, is_flag_type=False, input_name=None):
    """
    Generates the command line flag for a given input
    """
    flag, flag_sep = None, None
    if input_spec.argstr:
        if "=" in input_spec.argstr:
            if (
                input_spec.argstr.split("=")[1] == "0"
                or input_spec.argstr.split("=")[1] == "1"
            ):
                flag = input_spec.argstr
            else:
                flag = input_spec.argstr.split("=")[0].strip()
                flag_sep = "="
        elif input_spec.argstr.split("%")[0]:
            flag = input_spec.argstr.split("%")[0].strip()
    elif is_flag_type:
        flag = ("--%s" % input_name + " ").strip()
    return flag, flag_sep


def get_boutiques_output_from_inp(inputs, inp_spec, inp_name):
    """
    Takes a Nipype input representing an output file and generates a
    Boutiques output for it
    """
    output = {}
    output["name"] = inp_name.replace("_", " ").capitalize()
    output["id"] = inp_name
    output["optional"] = True
    output["description"] = get_description_from_spec(inputs, inp_name, inp_spec)
    if not (hasattr(inp_spec, "mandatory") and inp_spec.mandatory):
        output["optional"] = True
    else:
        output["optional"] = False
    if inp_spec.usedefault:
        output["default-value"] = inp_spec.default_value()[1]
    if isinstance(inp_spec.name_source, list):
        source = inp_spec.name_source[0]
    else:
        source = inp_spec.name_source
    output["path-template"] = inp_spec.name_template.replace(
        "%s", "[" + source.upper() + "]"
    )
    output["value-key"] = "[" + inp_name.upper() + "]"
    flag, flag_sep = get_command_line_flag(inp_spec)
    if flag is not None:
        output["command-line-flag"] = flag
    if flag_sep is not None:
        output["command-line-flag-separator"] = flag_sep
    return output
