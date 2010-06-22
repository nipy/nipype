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
        
        inputs = []
        outputs = []
        
        for paramGroup in dom.getElementsByTagName("parameters"):
            for param in paramGroup.childNodes:
                if param.nodeName in ['label', 'description', '#text']:
                    continue
                type = {'integer': traits.Int(), 'double': traits.Float(), 'image': File(), 'transform': File()}[param.nodeName]
                if param.nodeName in ['file', 'directory', 'image', 'transform'] and param.getElementsByTagName('channel')[0].firstChild.nodeValue == 'output':
                    outputs.append(param)
                else:
                    self.inputs.add_trait(param.getElementsByTagName('name')[0].firstChild.nodeValue, type)
                    print param.getElementsByTagName('name')[0].firstChild.nodeValue
        
        print inputs
        print outputs
        
        
if __name__ == "__main__":
    test = SlicerCommandLine(name="AffineRegistration")
    test.inputs.Iterations = 2
    test._grab_xml()