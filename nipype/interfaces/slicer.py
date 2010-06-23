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
from nipype.utils.misc import isdefined
from enthought.traits.trait_base import Undefined


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
        
        self._outputs_nodes = []
        
        undefined_traits = {}
        
        for paramGroup in dom.getElementsByTagName("parameters"):
            for param in paramGroup.childNodes:
                if param.nodeName in ['label', 'description', '#text']:
                    continue
                traitsParams = {}
                
                longFlagNode = param.getElementsByTagName('longflag')
                if longFlagNode:
                    traitsParams["argstr"] = "--" + longFlagNode[0].firstChild.nodeValue + " " 
                else:
                    traitsParams["argstr"] = ""
                traitsParams["argstr"] += {'integer': "%d", 'double': "%f", 'image': "%s", 'transform': "%s"}[param.nodeName]
                
                index = param.getElementsByTagName('index')
                if index:
                    traitsParams["position"] = index[0].firstChild.nodeValue
                    
                desc = param.getElementsByTagName('description')
                if index:
                    traitsParams["desc"] = desc[0].firstChild.nodeValue
                
                                    
                
                if param.nodeName in ['file', 'directory', 'image', 'transform'] and param.getElementsByTagName('channel')[0].firstChild.nodeValue == 'output':
                    traitsParams["genfile"] = True
                    self.inputs.add_trait(param.getElementsByTagName('name')[0].firstChild.nodeValue, type)
                    undefined_traits[param.getElementsByTagName('name')[0].firstChild.nodeValue] = Undefined
                    if param.nodeName in ['image', 'transform', 'file']:
                        traitsParams["exist"] = True
                    type = {'integer': traits.Int, 'double': traits.Float, 'image': File, 'transform': File}[param.nodeName](**traitsParams)
                    self._outputs_filenames[param.getElementsByTagName('name')[0].firstChild.nodeValue] = self._gen_filename_from_param(param)
                    self._outputs().add_trait(param.getElementsByTagName('name')[0].firstChild.nodeValue, type)
                    self._outputs_nodes.append(param)
                else:
                    if param.nodeName in ['image', 'transform', 'file']:
                        traitsParams["exist"] = True
                    type = {'integer': traits.Int, 'double': traits.Float, 'image': File, 'transform': File}[param.nodeName](**traitsParams)
                    self.inputs.add_trait(param.getElementsByTagName('name')[0].firstChild.nodeValue, type)
                    undefined_traits[param.getElementsByTagName('name')[0].firstChild.nodeValue] = Undefined
                    
                

                
        self.inputs.trait_set(trait_change_notify=False, **undefined_traits)
        print self._outputs_nodes
        
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
            ext = {'image': '.nii', 'transform': '.txt', 'file': ''}[param.nodeName]
        return os.path.abspath(base + ext)
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        for output_node in self._outputs_nodes:
            name = output_node.getElementsByTagName('name')[0].firstChild.nodeValue
            outputs[name] = getattr(self.inputs, name)
            if not isdefined(outputs[name]):
                outputs[name] = self._gen_filename(name)
        return outputs
        
if __name__ == "__main__":
    test = SlicerCommandLine(name="AffineRegistration")
    test.inputs.FixedImageFileName = "/home/filo/workspace/fmri_tumour/data/pilot1/10_co_COR_3D_IR_PREP.nii"
    test.inputs.MovingImageFileName = "/home/filo/workspace/fmri_tumour/data/pilot1/2_line_bisection.nii"
    print test.cmdline
    ret = test.run()
    print ret.runtime.stderr
    print ret.runtime.returncode