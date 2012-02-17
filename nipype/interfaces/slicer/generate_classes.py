"""This script generates Slicer Interfaces based on the CLI modules XML. CLI
modules are selected from the hardcoded list below and generated code is placed
in the cli_modules.py file (and imported in __init__.py). For this to work 
correctly you must have your CLI executabes in $PATH""" 

import xml.dom.minidom
import subprocess
from nipype.interfaces.base import (CommandLineInputSpec, CommandLine, traits,
                                    TraitedSpec, File, StdOutCommandLine,
                                    StdOutCommandLineInputSpec, isdefined)


def generate_all_classes(modules_list = [], launcher=[]):
    """ modules_list contains all the SEM compliant tools that should have wrappers created for them.
        launcher containtains the command line prefix wrapper arugments needed to prepare
        a proper environment for each of the modules.
    """
    init_imports = ""
    f = open("cli_modules.py", 'w')
    imports = """from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os\n\n\n"""
    f.write(imports)
    class_defs = []
    for module in modules_list:
        module_python_filename="%s.py"%module
        print("="*80)
        print("Generating Definition for module {0} in {1}".format(module,module_python_filename))
        print("^"*80)
        code = generate_class(module,launcher)
        class_defs.append(code)
    f.write("\n\n\n".join(class_defs))
    f.close()
    
    f = open("__init__.py", "w")
    f.write("from cli_modules import %s\n"%", ".join(modules_list))
    f.close()


def generate_class(module,launcher):
    dom = grab_xml(module,launcher)
    inputTraits = []
    outputTraits = []
    outputs_filenames = {}

    #self._outputs_nodes = []
    
    class_string = "\"\"\""
    
    for desc_str in ['title','category','description','version',
                     'documentation-url','license','contributor',
                     'acknowledgements']:
        el = dom.getElementsByTagName(desc_str)
        if el and el[0].firstChild:
            class_string += desc_str + ": " + el[0].firstChild.nodeValue + "\n\n"
    class_string += "\"\"\""

    for paramGroup in dom.getElementsByTagName("parameters"):
        for param in paramGroup.childNodes:
            if param.nodeName in ['label', 'description', '#text', '#comment']:
                continue
            traitsParams = {}

            longFlagNode = param.getElementsByTagName('longflag')
            if longFlagNode:
                ## Prefer to use longFlag as name if it is given, rather than the parameter name
                longFlagName = longFlagNode[0].firstChild.nodeValue
                ## SEM automatically strips prefixed "--" or "-" from from xml before processing
                ##     we need to replicate that behavior here The following
                ##     two nodes in xml have the same behavior in the program
                ##     <longflag>--test</longflag>
                ##     <longflag>test</longflag>
                longFlagName = longFlagName.lstrip(" -").rstrip(" ")
                name = longFlagName
                traitsParams["argstr"] = "--" + longFlagName + " "
            else:
                name = param.getElementsByTagName('name')[0].firstChild.nodeValue
                name = name.lstrip().rstrip()
                traitsParams["argstr"] = "--" + name + " "
                
            if param.getElementsByTagName('description'):
                traitsParams["desc"] = param.getElementsByTagName('description')[0].firstChild.nodeValue.replace('"', "\\\"").replace("\n", ", ")
            

            argsDict = {'directory': '%s', 'file': '%s', 'integer': "%d", 
                        'double': "%f", 'float': "%f", 'image': "%s", 
                        'transform': "%s", 'boolean': '', 
                        'string-enumeration': '%s', 'string': "%s", 
                        'integer-enumeration' : '%s',
                        'table' : '%s', 'point': '%s', 'region': '%s'}

            if param.nodeName.endswith('-vector'):
                traitsParams["argstr"] += "%s"
            else:
                traitsParams["argstr"] += argsDict[param.nodeName]

            index = param.getElementsByTagName('index')
            if index:
                traitsParams["position"] = index[0].firstChild.nodeValue

            desc = param.getElementsByTagName('description')
            if index:
                traitsParams["desc"] = desc[0].firstChild.nodeValue

            typesDict = {'integer': "traits.Int", 'double': "traits.Float",
                         'float': "traits.Float", 'image': "File",
                         'transform': "File", 'boolean': "traits.Bool",
                         'string': "traits.Str", 'file': "File",
                         'directory': "Directory", 'table': "File",
                         'point':"traits.List", 'region':"traits.List"}

            if param.nodeName.endswith('-enumeration'):
                type = "traits.Enum"
                values = ['"%s"'%el.firstChild.nodeValue for el in param.getElementsByTagName('element')]
            elif param.nodeName.endswith('-vector'):
                type = "InputMultiPath"
                if param.nodeName in ['file', 'directory', 'image', 'transform', 'table']:
                    values = ["%s(exists=True)"%typesDict[param.nodeName.replace('-vector','')]]
                else:
                    values = [typesDict[param.nodeName.replace('-vector','')]]
                traitsParams["sep"] = ','
            elif param.getAttribute('multiple') == "true":
                type = "InputMultiPath"
                if param.nodeName in ['file', 'directory', 'image', 'transform', 'table']:
                    values = ["%s(exists=True)"%typesDict[param.nodeName]]
                elif param.nodeName in ['point', 'region']:
                    values = ["%s(traits.Float(), minlen=3, maxlen=3)"%typesDict[param.nodeName]]
                else:
                    values = [typesDict[param.nodeName]]
                traitsParams["argstr"] += "..."
            else:
                values = []
                type = typesDict[param.nodeName]

            if param.nodeName in ['file', 'directory', 'image', 'transform', 'table'] and param.getElementsByTagName('channel')[0].firstChild.nodeValue == 'output':
                traitsParams["hash_files"] = False
                inputTraits.append("%s = traits.Either(traits.Bool, %s(%s), %s)"%(name, 
                                                                                 type, 
                                                                                 parse_values(values).replace("exists=True",""), 
                                                                                 parse_params(traitsParams)))
                traitsParams["exists"] = True
                traitsParams.pop("argstr")
                traitsParams.pop("hash_files")
                outputTraits.append("%s = %s(%s%s)"%(name, type.replace("Input", "Output"), parse_values(values), parse_params(traitsParams)))

                outputs_filenames[name] = gen_filename_from_param(param, name)
            else:
                if param.nodeName in ['file', 'directory', 'image', 'transform', 'table'] and type not in ["InputMultiPath", "traits.List"]:
                    traitsParams["exists"] = True

                inputTraits.append("%s = %s(%s%s)"%(name, type, parse_values(values), parse_params(traitsParams)))

    input_spec_code = "class " + module + "InputSpec(CommandLineInputSpec):\n"
    for trait in inputTraits:
        input_spec_code += "    " + trait + "\n"

    output_spec_code = "class " + module + "OutputSpec(TraitedSpec):\n"
    for trait in outputTraits:
        output_spec_code += "    " + trait + "\n"

    output_filenames_code = "_outputs_filenames = {"
    output_filenames_code += ",".join(["'%s':'%s'"%(key,value) for key,value in outputs_filenames.iteritems()])
    output_filenames_code += "}"


    input_spec_code += "\n\n"
    output_spec_code += "\n\n"

    template = """class %name%(CommandLine):
    %class_str%

    input_spec = %name%InputSpec
    output_spec = %name%OutputSpec
    _cmd = "%launcher% %name% "
    %output_filenames_code%

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(%name%, self)._format_arg(name, spec, value)\n"""
        

    main_class = template.replace('%class_str%', class_string).replace("%name%", module).replace("%output_filenames_code%", output_filenames_code).replace("%launcher%"," ".join(launcher))

    return input_spec_code + output_spec_code + main_class

def grab_xml(module,launcher):
#        cmd = CommandLine(command = "Slicer3", args="--launch %s --xml"%module)
#        ret = cmd.run()
        command_list=launcher[:] ## force copy to preserve original
        command_list.extend([module, "--xml"])
        final_command=" ".join(command_list)
        xmlReturnValue = subprocess.Popen(final_command, stdout=subprocess.PIPE, shell=True).communicate()[0]
        return xml.dom.minidom.parseString(xmlReturnValue)
#        if ret.runtime.returncode == 0:
#            return xml.dom.minidom.parseString(ret.runtime.stdout)
#        else:
#            raise Exception(cmd.cmdline + " failed:\n%s"%ret.runtime.stderr)
def parse_params(params):
    list = []
    for key, value in params.iteritems():
        if isinstance(value, str) or isinstance(value, unicode):
            list.append('%s="%s"'%(key, value))
        else:
            list.append('%s=%s'%(key, value))

    return ", ".join(list)

def parse_values(values):
    values = ['%s'%value for value in values]
    if len(values) > 0:
        retstr = ", ".join(values) + ", "
    else:
        retstr = ""
    return retstr

def gen_filename_from_param(param, base):
    fileExtensions = param.getAttribute("fileExtensions")
    if fileExtensions:
        ## It is possible that multiple file extensions can be specified in a
        ## comma separated list,  This will extract just the first extension
        firstFileExtension=fileExtensions.split(',')[0]
        ext = firstFileExtension
    else:
        ext = {'image': '.nii', 'transform': '.mat', 'file': '', 'directory': ''}[param.nodeName]
    return base + ext

if __name__ == "__main__":
    ## NOTE:  For now either the launcher needs to be found on the default path, or
    ##        every tool in the modules list must be found on the default path
    ##        AND calling the module with --xml must be supported and compliant.
    modules_list = ['Add',
                    'AffineRegistration',
                    'BSplineDeformableRegistration', 
                    #'BSplineToDeformationField', http://na-mic.org/Mantis/view.php?id=1647
                    'Cast', 'CheckerBoard', 
                    'ComputeSUVBodyWeight', 'ConfidenceConnected', 
                    'CurvatureAnisotropicDiffusion', 'DicomToNrrdConverter', 
                    'ResampleDTI', 'dwiNoiseFilter', 'dwiUNLM', 
                    'jointLMMSE', 'DiffusionTensorEstimation', 
                    'DiffusionTensorMathematics', 'DiffusionTensorTest', 
                    'DiffusionWeightedMasking', 
                    'BRAINSFit',
#'BRAINSABC',
#'BRAINSCut',
#'BRAINSAlignMSP',
#'BRAINSClipInferior',
#'BRAINSConstellationDetector',
#'BRAINSConstellationModeler',
#'BRAINSLandmarkInitializer',
'BRAINSDemonWarp',
#'BRAINSMush',
#'BRAINSInitializedControlPoints',
#'BRAINSLinearModelerEPCA',
#'BRAINSLmkTransform',
#'BRAINSMultiModeSegment',
'BRAINSROIAuto',
'BRAINSResample',
#'BRAINSTrimForegroundInDirection',
#'ESLR',
#'GenerateLabelMapFromProbabilityMap',
'VBRAINSDemonWarp',
'extractNrrdVectorIndex',
'gtractAnisotropyMap',
'gtractAverageBvalues',
'gtractClipAnisotropy',
'gtractCoRegAnatomy',
'gtractConcatDwi',
'gtractCopyImageOrientation',
'gtractCoregBvalues',
'gtractCostFastMarching',
'gtractImageConformity',
'gtractInvertBSplineTransform',
'gtractInvertDeformationField',
'gtractInvertRigidTransform',
'gtractResampleAnisotropy',
'gtractResampleB0',
'gtractResampleCodeImage',
'gtractResampleDWIInPlace',
'gtractTensor',
'gtractTransformToDeformationField',
#'GradientAnisotropicDiffusionImageFilter',
#'GenerateSummedGradientImage'
]

    ## SlicerExecutionModel compliant tools that are usually statically built, and don't need the Slicer3 --launcher
    #generate_all_classes(modules_list=modules_list,launcher=[])
    ## Tools compliant with SlicerExecutionModel called from the Slicer environment (for shared lib compatibility)
    launcher=['/home/filo/workspace/Slicer4-SuperBuild/Slicer-build/Slicer','--launch']
    generate_all_classes(modules_list=modules_list, launcher=[])
    #generate_all_classes(modules_list=['BRAINSABC'], launcher=[] )
