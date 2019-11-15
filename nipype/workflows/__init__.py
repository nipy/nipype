# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

_msg = ["Nipype 1 workflows have been moved to the niflow-nipype1-workflows package."]
try:
    from niflow.nipype1.workflows import data, dmri, fmri, misc, rsfmri, smri
except ImportError:
    _msg.append("pip install niflow-nipype1-workflows to continue using them.")
else:
    import sys

    # Hack to make `from nipype.workflows.X import Y` work
    sys.modules["nipype.workflows.data"] = data
    sys.modules["nipype.workflows.dmri"] = dmri
    sys.modules["nipype.workflows.fmri"] = fmri
    sys.modules["nipype.workflows.misc"] = misc
    sys.modules["nipype.workflows.rsfmri"] = rsfmri
    sys.modules["nipype.workflows.smri"] = smri
    _msg.append(
        "nipype.workflows.* provides a reference for backwards compatibility. "
        "Please use niflow.nipype1.workflows.* to avoid this warning."
    )
    del sys

import warnings

warnings.warn(" ".join(_msg))
del warnings, _msg
