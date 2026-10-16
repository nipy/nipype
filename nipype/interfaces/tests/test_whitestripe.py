# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

import pytest
import requests
from pathlib import Path
from string import Template
from nipype.interfaces import whitestripe
from nipype.interfaces.r import get_r_command


def test_whitestripe(tmpdir):
    cwd = tmpdir.chdir()

    Path("T1W.nii.gz").touch()

    normalizer = whitestripe.WhiteStripe()
    normalizer.inputs.img_type = "T1"
    normalizer.inputs.in_file = "T1W.nii.gz"
    normalizer.inputs.out_file = "T1W_ws.nii.gz"
    tmpfile, script = normalizer._cmdline(normalizer)

    expected_script = Template(
        # the level of indentation needs to match what's in the whitestripe interface
        """
                library(neurobase)
                library(WhiteStripe)
                in_file = readnii('$in_file')
                ind = whitestripe(in_file, "$img_type")$$whitestripe.ind
                norm = whitestripe_norm(in_file, ind)
                out_file = '$out_file'
                writenii(norm, out_file)
                """
    ).substitute(
        {
            "in_file": normalizer.inputs.in_file,
            "out_file": normalizer.inputs.out_file,
            "img_type": normalizer.inputs.img_type,
        }
    )
    assert tmpfile is False
    assert script == expected_script
    os.remove(normalizer.inputs.in_file)

    cwd.chdir()
