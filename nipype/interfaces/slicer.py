'''
Created on 22 Jun 2010

@author: filo
'''
from nipype.interfaces.base import CommandLine, CommandLineInputSpec,\
    DynamicTraitedSpec
import xml.dom.minidom
import enthought.traits.api as traits
import os
from nipype.interfaces.traits import File


path = "/home/filo/tmp/slicer/Slicer3-build/lib/Slicer3/Plugins"

class SlicerCommandLineInputSpec(DynamicTraitedSpec):
    name = traits.Str()
    args = traits.Str(argstr='%s', desc='Additional parameters to the command')
    environ = traits.DictStrStr(desc='Environment variables', usedefault=True)
    
class SlicerCommandLineOutputSpec(DynamicTraitedSpec):
    pass

class SlicerCommandLine(CommandLine):
    input_spec = SlicerCommandLineInputSpec
    output_spec = SlicerCommandLineOutputSpec
        
    
    def _grab_xml(self):
        cmd = CommandLine(command = self.cmd, args="--xml")
        ret = cmd.run()
        return xml.dom.minidom.parseString(ret.runtime.stdout)
    
    def __init__(self, name, **inputs):
        super(SlicerCommandLine, self).__init__(command= os.path.join(path, name), name= name, **inputs)
        dom = self._grab_xml()
        self._outputs_filenames = {}
        
        inputs = []
        outputs = []
        
        for paramGroup in dom.getElementsByTagName("parameters"):
            for param in paramGroup.childNodes:
                if param.nodeName in ['label', 'description', '#text']:
                    continue
                traitsParams = {}
                
                longFlagNode = param.getElementsByTagName('longflag')
                if longFlagNode:
                    traitsParams["argstr"] = "--" + longFlagNode[0].firstChild.nodeValue + " " + {'integer': "%d", 'double': "%f", 'image': "%s", 'transform': "%s"}[param.nodeName]
                
                index = param.getElementsByTagName('index')
                if index:
                    traitsParams["position"] = index[0].firstChild.nodeValue
                    
                desc = param.getElementsByTagName('description')
                if index:
                    traitsParams["desc"] = desc[0].firstChild.nodeValue
                    
                type = {'integer': traits.Int, 'double': traits.Float, 'image': File, 'transform': File}[param.nodeName](**traitsParams)
                if param.nodeName in ['file', 'directory', 'image', 'transform'] and param.getElementsByTagName('channel')[0].firstChild.nodeValue == 'output':
                    traitsParams["genfile"] = True
                    self._outputs_filenames[param.getElementsByTagName('name')[0].firstChild.nodeValue] = self._gen_filename_from_param(param)
                    outputs.append(param)

                self.inputs.add_trait(param.getElementsByTagName('name')[0].firstChild.nodeValue, type)
        print outputs
        
    def _gen_filename(self, name):
        if name in self._outputs_filenames:
            return self._outputs_filenames[name]
        return None
    
    def _gen_filename_from_param(self,param):
        base = param.getElementsByTagName('name')[0].firstChild.nodeValue
        fileExtensions = param.getAttribute("fileExtensions")
        if fileExtensions:
            ext = fileExtensions
        else:
            ext = {'image': '.nii', 'transform': '.txt'}[param.nodeName]
        return os.path.abspath(base + ext)
        
if __name__ == "__main__":
    test = SlicerCommandLine(name="AffineRegistration")
    test.inputs.Iterations = 2
    print test.cmdline