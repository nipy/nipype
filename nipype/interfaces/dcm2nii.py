from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
                                    InputMultiPath, traits, TraitedSpec,
                                    OutputMultiPath, isdefined,
                                    File, Directory)
import os
from copy import deepcopy
from nipype.utils.filemanip import split_filename
import re

class Dcm2niiInputSpec(CommandLineInputSpec):
    source_names = InputMultiPath(File(exists=True), argstr="%s", position=10, mandatory=True)
    gzip_output = traits.Bool(False, argstr='-g', position=0, usedefault=True)
    nii_output = traits.Bool(True, argstr='-n', position=1, usedefault=True)
    anonymize = traits.Bool(argstr='-a', position=2)
    id_in_filename = traits.Bool(False, argstr='-i', usedefault=True, position=3)
    reorient = traits.Bool(argstr='-r', position=4)
    reorient_and_crop = traits.Bool(argstr='-x', position=5)
    output_dir = Directory(exists=True, argstr='-o %s', genfile=True, position=6)
    config_file = File(exists=True, argstr="-b %s", genfile=True, position=7)
    convert_all_pars = traits.Bool(argstr='-v', position=8)
    args = traits.Str(argstr='%s', desc='Additional parameters to the command', position=9)

class Dcm2niiOutputSpec(TraitedSpec):
    converted_files = OutputMultiPath(File(exists=True))
    reoriented_files = OutputMultiPath(File(exists=True))
    reoriented_and_cropped_files = OutputMultiPath(File(exists=True))
    bvecs = OutputMultiPath(File(exists=True))
    bvals = OutputMultiPath(File(exists=True))

class Dcm2nii(CommandLine):
    input_spec=Dcm2niiInputSpec
    output_spec=Dcm2niiOutputSpec

    _cmd = 'dcm2nii'

    def _format_arg(self, opt, spec, val):
        if opt in ['gzip_output', 'nii_output', 'anonymize', 'id_in_filename', 'reorient', 'reorient_and_crop', 'convert_all_pars']:
            spec = deepcopy(spec)
            if val:
                spec.argstr += ' y'
            else:
                spec.argstr += ' n'
                val = True
        return super(Dcm2nii, self)._format_arg(opt, spec, val)

    def _run_interface(self, runtime):

        new_runtime = super(Dcm2nii, self)._run_interface(runtime)
        (self.output_files,
         self.reoriented_files,
         self.reoriented_and_cropped_files,
         self.bvecs, self.bvals) = self._parse_stdout(new_runtime.stdout)
        return new_runtime

    def _parse_stdout(self, stdout):
        files = []
        reoriented_files = []
        reoriented_and_cropped_files = []
        bvecs = []
        bvals = []
        skip = False
        last_added_file = None
        for line in stdout.split("\n"):
            if not skip:
                file = None
                if line.startswith("Saving "):
                    file = line[len("Saving "):]
                elif line.startswith("GZip..."):
                    #for gzipped outpus files are not absolute
                    if isdefined(self.inputs.output_dir):
                        output_dir = self.inputs.output_dir
                    else:
                        output_dir = self._gen_filename('output_dir')
                    file = os.path.abspath(os.path.join(output_dir,
                                                        line[len("GZip..."):]))
                elif line.startswith("Number of diffusion directions "):
                    if last_added_file:
                        base, filename, ext = split_filename(last_added_file)
                        bvecs.append(os.path.join(base,filename + ".bvec"))
                        bvals.append(os.path.join(base,filename + ".bval"))
                elif re.search('-->(.*)', line):
                    search = re.search('.*--> (.*)', line)
                    file = search.groups()[0]

                if file:
                    files.append(file)
                    last_added_file = file
                    continue

                if line.startswith("Reorienting as "):
                    reoriented_files.append(line[len("Reorienting as "):])
                    skip = True
                    continue
                elif line.startswith("Cropping NIfTI/Analyze image "):
                    base, filename = os.path.split(line[len("Cropping NIfTI/Analyze image "):])
                    filename = "c" + filename
                    reoriented_and_cropped_files.append(os.path.join(base, filename))
                    skip = True
                    continue



            skip = False
        return files, reoriented_files, reoriented_and_cropped_files, bvecs, bvals

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['converted_files'] = self.output_files
        outputs['reoriented_files'] = self.reoriented_files
        outputs['reoriented_and_cropped_files'] = self.reoriented_and_cropped_files
        outputs['bvecs'] = self.bvecs
        outputs['bvals'] = self.bvals
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

