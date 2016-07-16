.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.brains.classify
===================================


.. _nipype.interfaces.semtools.brains.classify.BRAINSPosteriorToContinuousClass:


.. index:: BRAINSPosteriorToContinuousClass

BRAINSPosteriorToContinuousClass
--------------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/brains/classify.py#L24>`__

Wraps command ** BRAINSPosteriorToContinuousClass **

title: Tissue Classification

category: BRAINS.Classify

description: This program will generate an 8-bit continuous tissue classified image based on BRAINSABC posterior images.

version: 3.0

documentation-url: http://www.nitrc.org/plugins/mwiki/index.php/brains:BRAINSClassify

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Vincent A. Magnotta

acknowledgements: Funding for this work was provided by NIH/NINDS award NS050568

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputBasalGmVolume: (an existing file name)
                Basal Grey Matter Posterior Volume
                flag: --inputBasalGmVolume %s
        inputCrblGmVolume: (an existing file name)
                Cerebellum Grey Matter Posterior Volume
                flag: --inputCrblGmVolume %s
        inputCrblWmVolume: (an existing file name)
                Cerebellum White Matter Posterior Volume
                flag: --inputCrblWmVolume %s
        inputCsfVolume: (an existing file name)
                CSF Posterior Volume
                flag: --inputCsfVolume %s
        inputSurfaceGmVolume: (an existing file name)
                Surface Grey Matter Posterior Volume
                flag: --inputSurfaceGmVolume %s
        inputVbVolume: (an existing file name)
                Venous Blood Posterior Volume
                flag: --inputVbVolume %s
        inputWhiteVolume: (an existing file name)
                White Matter Posterior Volume
                flag: --inputWhiteVolume %s
        outputVolume: (a boolean or a file name)
                Output Continuous Tissue Classified Image
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Output Continuous Tissue Classified Image
