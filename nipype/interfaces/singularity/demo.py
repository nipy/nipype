"""
Demonstration interface for running singularity containers using nipype.
"""

from .singularity import (SingularityInputSpec,
                          SingularityTask,
                          SingularityFile)

from nipype.interfaces.base import TraitedSpec


class DemoInputSpec(SingularityInputSpec):
    in_file = SingularityFile(argstr='%s',
                              desc="An input file on the host file system",
                              exists=True,
                              position=1)
    out_file = SingularityFile(argstr='%s',
                               desc="The output file, on the host file system",
                               position=2,
                               name_source=['in_file'],
                               name_template='%s_Counted')


class DemoOutputSpec(TraitedSpec):
    out_file = SingularityFile(desc="The output file, on the host file system",
                               exists=True)


class DemoTask_1(SingularityTask):
    input_spec = DemoInputSpec
    output_spec = DemoOutputSpec
    container_cmd = None


class DemoTask_2(SingularityTask):
    input_spec = DemoInputSpec
    output_spec = DemoOutputSpec
    container_cmd = None
