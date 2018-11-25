# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import unicode_literals
import os
import pytest
from nipype.interfaces.ants import registration
from nipype.utils.errors import MandatoryInputError


def test_ants_mand(tmpdir):
    tmpdir.chdir()
    filepath = os.path.dirname(os.path.realpath(__file__))
    datadir = os.path.realpath(os.path.join(filepath, '../../../testing/data'))

    ants = registration.ANTS()
    ants.inputs.transformation_model = "SyN"
    ants.inputs.moving_image = [os.path.join(datadir, 'resting.nii')]
    ants.inputs.fixed_image = [os.path.join(datadir, 'T1.nii')]
    ants.inputs.metric = ['MI']

    with pytest.raises(MandatoryInputError) as er:
        ants.run()
    assert 'Interface "ANTS" requires a value for input radius.' in str(er.value)
