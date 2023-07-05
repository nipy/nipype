# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from ..nipype2boutiques import generate_boutiques_descriptor
from nipype.testing import example_data
import json


def test_generate():
    ignored_inputs = ["args", "environ", "output_type"]
    desc = generate_boutiques_descriptor(
        module="nipype.interfaces.fsl",
        interface_name="FLIRT",
        container_image="mcin/docker-fsl:latest",
        container_index="index.docker.io",
        container_type="docker",
        verbose=False,
        save=False,
        ignore_inputs=ignored_inputs,
        author="Oxford Centre for Functional MRI of the Brain (FMRIB)",
    )

    with open(example_data("nipype2boutiques_example.json")) as desc_file:
        # Make sure that output descriptor matches the expected descriptor.
        output_desc = json.loads(desc)
        expected_desc = json.load(desc_file)
        assert output_desc.get("name") == expected_desc.get("name")
        assert output_desc.get("author") == expected_desc.get("author")
        assert output_desc.get("command-line") == expected_desc.get("command-line")
        assert output_desc.get("description") == expected_desc.get("description")
        assert len(output_desc.get("inputs")) == len(expected_desc.get("inputs"))
        assert len(output_desc.get("output-files")) == len(
            expected_desc.get("output-files")
        )
        assert output_desc.get("container-image").get("image") == expected_desc.get(
            "container-image"
        ).get("image")
