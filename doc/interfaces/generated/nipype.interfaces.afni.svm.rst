.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.afni.svm
===================


.. _nipype.interfaces.afni.svm.SVMTest:


.. index:: SVMTest

SVMTest
-------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/afni/svm.py#L133>`__

Wraps command **3dsvm**

Temporally predictive modeling with the support vector machine
SVM Test Only
For complete details, see the `3dsvm Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dsvm.html>`_

Examples
~~~~~~~~

>>> from nipype.interfaces import afni as afni
>>> svmTest = afni.SVMTest()
>>> svmTest.inputs.in_file= 'run2+orig'
>>> svmTest.inputs.model= 'run1+orig_model'
>>> svmTest.inputs.testlabels= 'run2_categories.1D'
>>> svmTest.inputs.out_file= 'pred2_model1'
>>> res = svmTest.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                A 3D or 3D+t AFNI brik dataset to be used for testing.
                flag: -testvol %s
        model: (a string)
                modname is the basename for the brik containing the SVM model
                flag: -model %s

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        classout: (a boolean)
                Flag to specify that pname files should be integer-valued,
                corresponding to class category decisions.
                flag: -classout
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        multiclass: (a boolean)
                Specifies multiclass algorithm for classification
                flag: -multiclass %s
        nodetrend: (a boolean)
                Flag to specify that pname files should not be linearly detrended
                flag: -nodetrend
        nopredcensord: (a boolean)
                Flag to prevent writing predicted values for censored time-points
                flag: -nopredcensord
        options: (a string)
                additional options for SVM-light
                flag: %s
        out_file: (a file name)
                filename for .1D prediction file(s).
                flag: -predictions %s
        outputtype: ('NIFTI_GZ' or 'AFNI' or 'NIFTI')
                AFNI output filetype
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        testlabels: (an existing file name)
                *true* class category .1D labels for the test dataset. It is used to
                calculate the prediction accuracy performance
                flag: -testlabels %s

Outputs::

        out_file: (an existing file name)
                output file

.. _nipype.interfaces.afni.svm.SVMTrain:


.. index:: SVMTrain

SVMTrain
--------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/afni/svm.py#L79>`__

Wraps command **3dsvm**

Temporally predictive modeling with the support vector machine
SVM Train Only
For complete details, see the `3dsvm Documentation.
<http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dsvm.html>`_

Examples
~~~~~~~~

>>> from nipype.interfaces import afni as afni
>>> svmTrain = afni.SVMTrain()
>>> svmTrain.inputs.in_file = 'run1+orig'
>>> svmTrain.inputs.trainlabels = 'run1_categories.1D'
>>> svmTrain.inputs.ttype = 'regression'
>>> svmTrain.inputs.mask = 'mask.nii'
>>> svmTrain.inputs.model = 'model_run1'
>>> svmTrain.inputs.alphas = 'alphas_run1'
>>> res = svmTrain.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                A 3D+t AFNI brik dataset to be used for training.
                flag: -trainvol %s
        ttype: (a string)
                tname: classification or regression
                flag: -type %s

        [Optional]
        alphas: (a file name)
                output alphas file name
                flag: -alpha %s
        args: (a string)
                Additional parameters to the command
                flag: %s
        censor: (an existing file name)
                .1D censor file that allows the user to ignore certain samples in
                the training data.
                flag: -censor %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        kernel: (a string)
                string specifying type of kernel function:linear, polynomial, rbf,
                sigmoid
                flag: -kernel %s
        mask: (an existing file name)
                byte-format brik file used to mask voxels in the analysis
                flag: -mask %s, position: -1
        max_iterations: (an integer (int or long))
                Specify the maximum number of iterations for the optimization.
                flag: -max_iterations %d
        model: (a file name)
                basename for the brik containing the SVM model
                flag: -model %s
        nomodelmask: (a boolean)
                Flag to enable the omission of a mask file
                flag: -nomodelmask
        options: (a string)
                additional options for SVM-light
                flag: %s
        out_file: (a file name)
                output sum of weighted linear support vectors file name
                flag: -bucket %s
        outputtype: ('NIFTI_GZ' or 'AFNI' or 'NIFTI')
                AFNI output filetype
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        trainlabels: (an existing file name)
                .1D labels corresponding to the stimulus paradigm for the training
                data.
                flag: -trainlabels %s
        w_out: (a boolean)
                output sum of weighted linear support vectors
                flag: -wout

Outputs::

        alphas: (a file name)
                output alphas file name
        model: (a file name)
                brik containing the SVM model file name
        out_file: (a file name)
                sum of weighted linear support vectors file name
