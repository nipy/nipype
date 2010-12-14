from nipype.interfaces.base import CommandLine, CommandLineInputSpec,\
    InputMultiPath, traits, TraitedSpec, OutputMultiPath
from nipype.interfaces.traits import File, Directory
from nipype.utils.misc import isdefined
import os
from copy import deepcopy

class Dcm2niiInputSpec(CommandLineInputSpec):
    source_names = InputMultiPath(File(exists=True), argstr="%s", position=6, mandatory=True)
    gzip_output = traits.Bool(False, argstr='-g', position=0, usedefault=True)
    nii_output = traits.Bool(True, argstr='-n', position=1, usedefault=True)
    anonymize = traits.Bool(argstr='-a', position=2)
    id_in_filename = traits.Bool(False, argstr='-i', usedefault=True, position=3)
    output_dir = Directory(exists=True, argstr='-o %s', genfile=True, position=4)
    config_file = File(exists=True, argstr="-b %s", genfile=True, position=5)
    
class Dcm2niiOutputSpec(TraitedSpec):
    converted_files = OutputMultiPath(File(exists=True))

class Dcm2nii(CommandLine):
    input_spec=Dcm2niiInputSpec
    output_spec=Dcm2niiOutputSpec
    
    _cmd = 'dcm2nii'
    
    def _format_arg(self, opt, spec, val):
        if opt in ['gzip_output', 'nii_output', 'anonymize', 'id_in_filename']:
            spec = deepcopy(spec)
            if val:
                spec.argstr += ' y'
            else:
                spec.argstr += ' n'
                val = True
        return super(Dcm2nii, self)._format_arg(opt, spec, val)
    
    def _run_interface(self, runtime):
        if self.inputs.config_file == "config.ini":
            os.mknod(self.inputs.config_file)
            f = open(self.inputs.config_file, "w")
            # disable interactive mode
            f.write("[BOOL]\nManualNIfTIConv=0\n")
            f.close()
            self.inputs.config_file = self.inputs.config_file
            
        new_runtime = super(Dcm2nii, self)._run_interface(runtime)
        self.output_files = self._parse_stdout(new_runtime.stdout)
        return new_runtime
    
    def _parse_stdout(self, stdout):
        files = []
        for line in stdout.split("\n"):
            if line.endswith(".nii") and not (line.find("->") != -1 or line.startswith("Cropping") or line.startswith("Reorienting")):
                file = line.split(" ")[-1]
                if self.inputs.gzip_output:
                    file +=".gz"
                files.append(file)
        return files
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['converted_files'] = self.output_files
        return outputs
    
    def _gen_filename(self, name):
        if name == 'output_dir':
            return os.getcwd()
        elif name == 'config_file':
            config_file = "config.ini"
            f = open(config_file, "w")
            # disable interactive mode
            f.write("[BOOL]\nManualNIfTIConv=0\n")
            f.close()
            return config_file
        return None
            
        