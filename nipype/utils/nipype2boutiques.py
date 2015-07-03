# This tool exports a Nipype interface in the Boutiques (https://github.com/boutiques) JSON format.
# Boutiques tools can be imported in CBRAIN (https://github.com/aces/cbrain) among other platforms.
#
# Limitations:
#   * optional inputs are ignored because they are not supported in Boutiques.
#   * inputs with cardinality "Multiple" (InputMultiPath in Nipype) are not supported. Same limitation for the outputs.
#   * value-templates are wrong when output files are not created in the execution directory (e.g. when a sub-directory is created).

import os
import argparse
import inspect
import sys
import json
import tempfile

from nipype.interfaces.base import Interface

def create_tempfile():
  fileTemp = tempfile.NamedTemporaryFile(delete = False)
  fileTemp.write("hello")
  fileTemp.close()
  return fileTemp.name

def print_inputs(tool_name, module=None, function=None):
    interface = None
    if module and function:
        __import__(module)
        interface = getattr(sys.modules[module],function)()

        inputs = interface.input_spec()
        outputs = interface.output_spec()

        command_line = "nipype_cmd "+str(module)+" "+tool_name+" "
        tool_desc = {}
        tool_desc['name'] = tool_name
        tool_desc['description'] = "Tool description goes here"

        tool_inputs = []
        input_counter = 0
        tool_outputs = []

        for name, spec in sorted(interface.inputs.traits(transient=None).items()):

            input = {}

            input['name'] = name
            type = spec.full_info(inputs, name, None)
            if "an existing file name" in type:
                type = "File"
            else:
                type = "String"
            input['type'] = type
            input['description'] = "\n".join(interface._get_trait_desc(inputs, name, spec))[len(name)+2:].replace("\n\t\t",". ")
            command_line_key = "["+str(input_counter)+"_"+name.upper()+"]"
            input_counter += 1
            input['command-line-key'] = command_line_key
            input['cardinality'] = "Single"
            if not ( hasattr(spec, "mandatory") and spec.mandatory ):
                input['optional'] = "true"
                input['command-line-flag'] = "--%s"%name+" "

            tool_inputs.append(input)

            command_line+= command_line_key+" "

            # add value to input so that output names can be generated
            tempfile_name = create_tempfile()
            input['tempfile_name'] = tempfile_name
            if type == "File":
                setattr(interface.inputs,name,os.path.abspath(tempfile_name))

        for name,spec in sorted(outputs.traits(transient=None).items()):

            output = {}
            output['name'] = name
            output['type'] = "File"
            output['description'] = "No description provided"
            output['command-line-key'] = ""
            output['value-template'] = ""
            output_value = interface._list_outputs()[name]
            if output_value != "" and isinstance(output_value,str): # FIXME: this crashes when there are multiple output values.
                # go find from which input file it was built
                for input in tool_inputs:
                    base_file_name = os.path.splitext(os.path.basename(input['tempfile_name']))[0]
                    if base_file_name in output_value:
                        output_value = os.path.basename(output_value.replace(base_file_name,input['command-line-key'])) # FIXME: this only works if output is written in the current directory
                output['value-template'] = os.path.basename(output_value)

            output['cardinality'] = "Single"
            tool_outputs.append(output)

        # remove all temporary file names from inputs
        for input in tool_inputs:
            del input['tempfile_name']

        tool_desc['inputs'] = tool_inputs
        tool_desc['outputs'] = tool_outputs
        tool_desc['command-line'] = command_line
        tool_desc['docker-image'] = 'docker.io/robdimsdale/nipype'
        tool_desc['docker-index'] = 'http://index.docker.io'
        tool_desc['schema-version'] = '0.2-snapshot'
        print json.dumps(tool_desc, indent=4, separators=(',', ': '))

def main(argv):

    parser = argparse.ArgumentParser(description='Nipype Boutiques exporter', prog=argv[0])
    parser.add_argument("module", type=str, help="Module name")
    parser.add_argument("interface", type=str, help="Interface name")
    parsed = parser.parse_args(args=argv[1:3])

    _, prog = os.path.split(argv[0])
    interface_parser = argparse.ArgumentParser(description="Run %s"%parsed.interface, prog=" ".join([prog] + argv[1:3]))
    print_inputs(argv[2],parsed.module, parsed.interface)
