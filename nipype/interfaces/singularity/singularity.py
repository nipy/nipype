"""
Nipype interface for running a singularity container.
Example:
container = SingularityTask(container="test_container/test.img", \
                            args='abc', \
                            map_dirs_list=['input:/output'])
container.cmdline
singularity run -B input:/output test_container/test.img abc
"""

import os
import logging
from ..base import (traits,
                    CommandLine,
                    CommandLineInputSpec,
                    File)
from ..traits_extension import (BaseFile,
                                BaseDirectory,
                                isdefined)

iflogger = logging.getLogger('interface')


class SingularityDir(BaseDirectory):
    """Creates a Directory object that can be checked for existance on the
    host, while keeping a value relative to the container"""
    def __init__(self, value='', auto_set=False, entries=0,
                 exists=False, **metadata):
        super(SingularityDir, self).__init__(value='',
                                             auto_set=False,
                                             entries=0,
                                             exists=False,
                                             **metadata)


class SingularityFile(BaseFile):
    """Creates a File object that can be checked for existance on the
    host, while keeping a value relative to the container"""

    def __init__(self, value='', filter=None, auto_set=False,
                 entries=0, exists=False, **metadata):
        """ Creates a Singularity File trait.
        File paths defined here will be tested for existance against the
        host file system (if exists=True). However they will be re-written
        to paths in the container filesystem when formatted for command line.

        Parameters
        ----------
        value : string
            The default value for the trait

        filter : string
            A wildcard string to filter filenames in the file dialog box used
            by the attribute trait editor.
        auto_set : boolean
            Indicates whether the file editor updates the trait value after
            every key stroke.
        exists : boolean
            Indicates whether the trait value must be an existing file or
            not.

        Default Value
        -------------
        *value* or ''
        """
        super(SingularityFile, self).__init__(value,
                                              filter=filter,
                                              auto_set=auto_set,
                                              entries=entries,
                                              exists=exists,
                                              **metadata)


class SingularityInputSpec(CommandLineInputSpec):
    debug = traits.Bool(usedefault=True)
    container = File(exists=True,
                     desc='Container image',
                     mandatory=True, argstr="%s", position=2)

    container_command = traits.Unicode(desc='Command to run inside container',
                                       argstr="%s", position=3)

    map_dirs_tuples = traits.List(traits.Tuple(traits.Unicode, traits.Unicode),
                                  desc=("Directories to map into the container"
                                        "Format:[(host_dir, src_dir)]"))
    map_dirs_list = traits.List(traits.Str,
                                desc=("Directories to map into the container"
                                      "Format:[host_dir:src_dir]"),
                                position=1,
                                argstr='-B %s...')


class SingularityTask(CommandLine):
    input_spec = SingularityInputSpec

    _cmd = 'singularity run'
    container_cmd = None

    def __init__(self, **inputs):
        if self.container_cmd:
            inputs['container_command'] = self.container_cmd
        # need to add something to map paths internal to the container
        # to hosts paths, for File, Directory exists checks.

        super(SingularityTask, self).__init__(**inputs)

    def _parse_inputs(self, skip=None):
        # modify the run command if debug is specified
        if self.inputs.debug:
            self._cmd = 'singularity --debug run'

        # increment the position argument for all child trait objects
        # ensure that container arguments and commands come first
        trait_names = self.inputs.editable_traits()
        local_trait_names = SingularityInputSpec().editable_traits()
        # find the current maximum position
        max_position = 0
        for name in local_trait_names:
            t = SingularityInputSpec().trait(name)
            if t.position and t.position > max_position:
                max_position = t.position
        # update the passed parameter positions
        new_names = set(trait_names) - set(local_trait_names)
        for name in new_names:
            t = self.inputs.trait(name)
            if t.position and t.position >= 0:
                t.position = t.position + max_position
        # parse any map_dirs_tuples directives, covert them to list strings
        if isdefined(self.inputs.map_dirs_tuples):
            map_strs = [":".join(str) for str in self.inputs.map_dirs_tuples]
            if not isdefined(self.inputs.map_dirs_list):
                self.inputs.map_dirs_list = []
            [self.inputs.map_dirs_list.append(str) for str in map_strs]

        # original parse code here
        all_args = []
        initial_args = {}
        final_args = {}
        metadata = dict(argstr=lambda t: t is not None)

        for name, spec in sorted(self.inputs.traits(**metadata).items()):
            if skip and name in skip:
                continue

            value = getattr(self.inputs, name)
            if spec.name_source:
                value = self._filename_from_source(name)
            elif spec.genfile:
                if not isdefined(value) or value is None:
                    value = self._gen_filename(name)

            if not isdefined(value):
                continue

            # modify SingularityFile paths
            if spec.is_trait_type((SingularityFile, SingularityDir)):
                value = self.get_container_path(value,
                                                self.inputs.map_dirs_list)

            arg = self._format_arg(name, spec, value)
            if arg is None:
                continue
            pos = spec.position
            if pos is not None:
                if int(pos) >= 0:
                    initial_args[pos] = arg
                else:
                    final_args[pos] = arg
            else:
                all_args.append(arg)
        first_args = [arg for pos, arg in sorted(initial_args.items())]
        last_args = [arg for pos, arg in sorted(final_args.items())]
        return first_args + all_args + last_args

    def get_container_path(self, path, mounts):
        """
        Takes a file path that is valid in the host
        and a list of mounts ['host:container']
        changes the file path to the path in the container.
        """
        if not path:
            return

        if isdefined(mounts):
            for mount in mounts:
                h_path, c_path = mount.split(':')
                h_path = os.path.abspath(h_path)
                c_path = os.path.abspath(c_path)

                if path.startswith(h_path):
                    rel_path = os.path.relpath(path, h_path)
                    path = os.path.join(c_path, rel_path)
        return(path)

    def get_host_path(self, path):
        """
        Takes a file path that is valid in the container
        and converts it to one valid on the host.
        """
        if not path:
            return

        if isdefined(self.inputs.map_dirs_list):
            mounts = self.inputs.map_dirs_list
            for mount in mounts:
                h_path, c_path = mount.split(':')
                h_path = os.path.abspath(h_path)
                c_path = os.path.abspath(c_path)
                if path.startswith(c_path):
                    rel_path = os.path.relpath(path, c_path)
                    path = os.path.join(h_path, rel_path)
        return(path)

    def _filename_from_source(self, name, chain=None):
        retval = super(SingularityTask, self)._filename_from_source(name,
                                                                    chain)
        retval = os.path.join('/output', retval)

        return retval

    def _list_outputs(self):
        """
        Extends standard _list_outputs to replace container paths
        with host paths.
        """
        metadata = dict(name_source=lambda t: t is not None)
        traits = self.inputs.traits(**metadata)
        if traits:
            outputs = self.output_spec().get()  # pylint: disable=E1102
            for name, trait_spec in list(traits.items()):
                out_name = name
                if trait_spec.output_name is not None:
                    out_name = trait_spec.output_name

                if trait_spec.is_trait_type((SingularityFile, SingularityDir)):
                    # remap internal paths to external apths
                    c_path = os.path.abspath(self._filename_from_source(name))
                    outputs[out_name] = \
                        os.path.abspath(self.get_host_path(c_path))
                else:
                    outputs[out_name] = \
                        os.path.abspath(self._filename_from_source(name))
            return outputs
