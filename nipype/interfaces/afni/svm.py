# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""AFNI's svm interfaces."""

from ..base import TraitedSpec, traits, File
from .base import AFNICommand, AFNICommandInputSpec, AFNICommandOutputSpec


class SVMTrainInputSpec(AFNICommandInputSpec):
    # training options
    ttype = traits.Str(
        desc="tname: classification or regression", argstr="-type %s", mandatory=True
    )
    in_file = File(
        desc="A 3D+t AFNI brik dataset to be used for training.",
        argstr="-trainvol %s",
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    out_file = File(
        name_template="%s_vectors",
        desc="output sum of weighted linear support vectors file name",
        argstr="-bucket %s",
        suffix="_bucket",
        name_source="in_file",
    )
    model = File(
        name_template="%s_model",
        desc="basename for the brik containing the SVM model",
        argstr="-model %s",
        suffix="_model",
        name_source="in_file",
    )
    alphas = File(
        name_template="%s_alphas",
        desc="output alphas file name",
        argstr="-alpha %s",
        suffix="_alphas",
        name_source="in_file",
    )
    mask = File(
        desc="byte-format brik file used to mask voxels in the analysis",
        argstr="-mask %s",
        position=-1,
        exists=True,
        copyfile=False,
    )
    nomodelmask = traits.Bool(
        desc="Flag to enable the omission of a mask file", argstr="-nomodelmask"
    )
    trainlabels = File(
        desc=".1D labels corresponding to the stimulus paradigm for the training data.",
        argstr="-trainlabels %s",
        exists=True,
    )
    censor = File(
        desc=".1D censor file that allows the user to ignore certain samples in the training data.",
        argstr="-censor %s",
        exists=True,
    )
    kernel = traits.Str(
        desc="string specifying type of kernel function:linear, polynomial, rbf, sigmoid",
        argstr="-kernel %s",
    )
    max_iterations = traits.Int(
        desc="Specify the maximum number of iterations for the optimization.",
        argstr="-max_iterations %d",
    )
    w_out = traits.Bool(
        desc="output sum of weighted linear support vectors", argstr="-wout"
    )
    options = traits.Str(desc="additional options for SVM-light", argstr="%s")


class SVMTrainOutputSpec(TraitedSpec):
    out_file = File(desc="sum of weighted linear support vectors file name")
    model = File(desc="brik containing the SVM model file name")
    alphas = File(desc="output alphas file name")


class SVMTrain(AFNICommand):
    """Temporally predictive modeling with the support vector machine
    SVM Train Only
    For complete details, see the `3dsvm Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dsvm.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> svmTrain = afni.SVMTrain()
    >>> svmTrain.inputs.in_file = 'run1+orig'
    >>> svmTrain.inputs.trainlabels = 'run1_categories.1D'
    >>> svmTrain.inputs.ttype = 'regression'
    >>> svmTrain.inputs.mask = 'mask.nii'
    >>> svmTrain.inputs.model = 'model_run1'
    >>> svmTrain.inputs.alphas = 'alphas_run1'
    >>> res = svmTrain.run() # doctest: +SKIP

    """

    _cmd = "3dsvm"
    input_spec = SVMTrainInputSpec
    output_spec = SVMTrainOutputSpec
    _additional_metadata = ["suffix"]

    def _format_arg(self, name, trait_spec, value):
        return super()._format_arg(name, trait_spec, value)


class SVMTestInputSpec(AFNICommandInputSpec):
    # testing options
    model = traits.Str(
        desc="modname is the basename for the brik containing the SVM model",
        argstr="-model %s",
        mandatory=True,
    )
    in_file = File(
        desc="A 3D or 3D+t AFNI brik dataset to be used for testing.",
        argstr="-testvol %s",
        exists=True,
        mandatory=True,
    )
    out_file = File(
        name_template="%s_predictions",
        desc="filename for .1D prediction file(s).",
        argstr="-predictions %s",
    )
    testlabels = File(
        desc="*true* class category .1D labels for the test dataset. It is used to calculate the prediction accuracy performance",
        exists=True,
        argstr="-testlabels %s",
    )
    classout = traits.Bool(
        desc="Flag to specify that pname files should be integer-valued, corresponding to class category decisions.",
        argstr="-classout",
    )
    nopredcensord = traits.Bool(
        desc="Flag to prevent writing predicted values for censored time-points",
        argstr="-nopredcensord",
    )
    nodetrend = traits.Bool(
        desc="Flag to specify that pname files should not be linearly detrended",
        argstr="-nodetrend",
    )
    multiclass = traits.Bool(
        desc="Specifies multiclass algorithm for classification",
        argstr="-multiclass %s",
    )
    options = traits.Str(desc="additional options for SVM-light", argstr="%s")


class SVMTest(AFNICommand):
    """Temporally predictive modeling with the support vector machine
    SVM Test Only
    For complete details, see the `3dsvm Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dsvm.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni as afni
    >>> svmTest = afni.SVMTest()
    >>> svmTest.inputs.in_file= 'run2+orig'
    >>> svmTest.inputs.model= 'run1+orig_model'
    >>> svmTest.inputs.testlabels= 'run2_categories.1D'
    >>> svmTest.inputs.out_file= 'pred2_model1'
    >>> res = svmTest.run() # doctest: +SKIP

    """

    _cmd = "3dsvm"
    input_spec = SVMTestInputSpec
    output_spec = AFNICommandOutputSpec
