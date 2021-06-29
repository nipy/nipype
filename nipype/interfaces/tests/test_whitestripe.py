# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

import pytest
import requests
from nipype.interfaces import whitestripe
from nipype.interfaces.r import get_r_command


@pytest.mark.skipif(get_r_command() is None, reason="R is not available")
def test_whitestripe(tmpdir):
    cwd = tmpdir.chdir()

    filename = "T1W.nii.gz"
    req = requests.get(
        "https://johnmuschelli.com/open_ms_data/cross_sectional/coregistered_resampled/patient01/T1W.nii.gz"
    )
    with open(filename, "wb") as fd:
        for chunk in req.iter_content(chunk_size=128):
            fd.write(chunk)

    normalizer = whitestripe.WhiteStripe()
    normalizer.inputs.img_type = "T1"
    normalizer.inputs.in_file = "T1W.nii.gz"
    normalizer.inputs.indices = normalizer.gen_indices()
    normalizer.inputs.out_file = "T1W_ws.nii.gz"
    normalizer.run()

    assert os.path.isfile(normalizer.inputs.out_file)
    os.remove(normalizer.inputs.out_file)
    os.remove(normalizer.inputs.in_file)

    cwd.chdir()
