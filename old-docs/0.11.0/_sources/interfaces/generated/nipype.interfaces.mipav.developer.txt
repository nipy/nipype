.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.mipav.developer
==========================


.. _nipype.interfaces.mipav.developer.JistBrainMgdmSegmentation:


.. index:: JistBrainMgdmSegmentation

JistBrainMgdmSegmentation
-------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L91>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run de.mpg.cbs.jist.brain.JistBrainMgdmSegmentation **

title: MGDM Whole Brain Segmentation

category: Developer Tools

description: Estimate brain structures from an atlas for a MRI dataset (multiple input combinations are possible).

version: 2.0.RC

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
        inAdjust: ('true' or 'false')
                Adjust intensity priors
                flag: --inAdjust %s
        inAtlas: (an existing file name)
                Atlas file
                flag: --inAtlas %s
        inCompute: ('true' or 'false')
                Compute posteriors
                flag: --inCompute %s
        inCurvature: (a float)
                Curvature weight
                flag: --inCurvature %f
        inData: (a float)
                Data weight
                flag: --inData %f
        inFLAIR: (an existing file name)
                FLAIR Image
                flag: --inFLAIR %s
        inMP2RAGE: (an existing file name)
                MP2RAGE T1 Map Image
                flag: --inMP2RAGE %s
        inMP2RAGE2: (an existing file name)
                MP2RAGE T1-weighted Image
                flag: --inMP2RAGE2 %s
        inMPRAGE: (an existing file name)
                MPRAGE T1-weighted Image
                flag: --inMPRAGE %s
        inMax: (an integer (int or long))
                Max iterations
                flag: --inMax %d
        inMin: (a float)
                Min change
                flag: --inMin %f
        inOutput: ('segmentation' or 'memberships')
                Output images
                flag: --inOutput %s
        inPV: (an existing file name)
                PV / Dura Image
                flag: --inPV %s
        inPosterior: (a float)
                Posterior scale (mm)
                flag: --inPosterior %f
        inSteps: (an integer (int or long))
                Steps
                flag: --inSteps %d
        inTopology: ('26/6' or '6/26' or '18/6' or '6/18' or '6/6' or 'wcs'
                 or 'wco' or 'no')
                Topology
                flag: --inTopology %s
        null: (a string)
                Execution Time
                flag: --null %s
        outLevelset: (a boolean or a file name)
                Levelset Boundary Image
                flag: --outLevelset %s
        outPosterior2: (a boolean or a file name)
                Posterior Maximum Memberships (4D)
                flag: --outPosterior2 %s
        outPosterior3: (a boolean or a file name)
                Posterior Maximum Labels (4D)
                flag: --outPosterior3 %s
        outSegmented: (a boolean or a file name)
                Segmented Brain Image
                flag: --outSegmented %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        outLevelset: (an existing file name)
                Levelset Boundary Image
        outPosterior2: (an existing file name)
                Posterior Maximum Memberships (4D)
        outPosterior3: (an existing file name)
                Posterior Maximum Labels (4D)
        outSegmented: (an existing file name)
                Segmented Brain Image

.. _nipype.interfaces.mipav.developer.JistBrainMp2rageDuraEstimation:


.. index:: JistBrainMp2rageDuraEstimation

JistBrainMp2rageDuraEstimation
------------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L497>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run de.mpg.cbs.jist.brain.JistBrainMp2rageDuraEstimation **

title: MP2RAGE Dura Estimation

category: Developer Tools

description: Filters a MP2RAGE brain image to obtain a probability map of dura matter.

version: 3.0.RC

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
        inDistance: (a float)
                Distance to background (mm)
                flag: --inDistance %f
        inSecond: (an existing file name)
                Second inversion (Inv2) Image
                flag: --inSecond %s
        inSkull: (an existing file name)
                Skull Stripping Mask
                flag: --inSkull %s
        inoutput: ('dura_region' or 'boundary' or 'dura_prior' or 'bg_prior'
                 or 'intens_prior')
                Outputs an estimate of the dura / CSF boundary or an estimate of the
                entire dura region.
                flag: --inoutput %s
        null: (a string)
                Execution Time
                flag: --null %s
        outDura: (a boolean or a file name)
                Dura Image
                flag: --outDura %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        outDura: (an existing file name)
                Dura Image

.. _nipype.interfaces.mipav.developer.JistBrainMp2rageSkullStripping:


.. index:: JistBrainMp2rageSkullStripping

JistBrainMp2rageSkullStripping
------------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L345>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run de.mpg.cbs.jist.brain.JistBrainMp2rageSkullStripping **

title: MP2RAGE Skull Stripping

category: Developer Tools

description: Estimate a brain mask for a MP2RAGE dataset. At least a T1-weighted or a T1 map image is required.

version: 3.0.RC

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
        inFilter: (an existing file name)
                Filter Image (opt)
                flag: --inFilter %s
        inSecond: (an existing file name)
                Second inversion (Inv2) Image
                flag: --inSecond %s
        inSkip: ('true' or 'false')
                Skip zero values
                flag: --inSkip %s
        inT1: (an existing file name)
                T1 Map (T1_Images) Image (opt)
                flag: --inT1 %s
        inT1weighted: (an existing file name)
                T1-weighted (UNI) Image (opt)
                flag: --inT1weighted %s
        null: (a string)
                Execution Time
                flag: --null %s
        outBrain: (a boolean or a file name)
                Brain Mask Image
                flag: --outBrain %s
        outMasked: (a boolean or a file name)
                Masked T1 Map Image
                flag: --outMasked %s
        outMasked2: (a boolean or a file name)
                Masked T1-weighted Image
                flag: --outMasked2 %s
        outMasked3: (a boolean or a file name)
                Masked Filter Image
                flag: --outMasked3 %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        outBrain: (an existing file name)
                Brain Mask Image
        outMasked: (an existing file name)
                Masked T1 Map Image
        outMasked2: (an existing file name)
                Masked T1-weighted Image
        outMasked3: (an existing file name)
                Masked Filter Image

.. _nipype.interfaces.mipav.developer.JistBrainPartialVolumeFilter:


.. index:: JistBrainPartialVolumeFilter

JistBrainPartialVolumeFilter
----------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L695>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run de.mpg.cbs.jist.brain.JistBrainPartialVolumeFilter **

title: Partial Volume Filter

category: Developer Tools

description: Filters an image for regions of partial voluming assuming a ridge-like model of intensity.

version: 2.0.RC

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
        inInput: (an existing file name)
                Input Image
                flag: --inInput %s
        inPV: ('bright' or 'dark' or 'both')
                Outputs the raw intensity values or a probability score for the
                partial volume regions.
                flag: --inPV %s
        inoutput: ('probability' or 'intensity')
                output
                flag: --inoutput %s
        null: (a string)
                Execution Time
                flag: --null %s
        outPartial: (a boolean or a file name)
                Partial Volume Image
                flag: --outPartial %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        outPartial: (an existing file name)
                Partial Volume Image

.. _nipype.interfaces.mipav.developer.JistCortexSurfaceMeshInflation:


.. index:: JistCortexSurfaceMeshInflation

JistCortexSurfaceMeshInflation
------------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L384>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run de.mpg.cbs.jist.cortex.JistCortexSurfaceMeshInflation **

title: Surface Mesh Inflation

category: Developer Tools

description: Inflates a cortical surface mesh.
D. Tosun, M. E. Rettmann, X. Han, X. Tao, C. Xu, S. M. Resnick, D. Pham, and J. L. Prince, Cortical Surface Segmentation and Mapping, NeuroImage, vol. 23, pp. S108--S118, 2004.

version: 3.0.RC

contributor: Duygu Tosun

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
        inLevelset: (an existing file name)
                Levelset Image
                flag: --inLevelset %s
        inLorentzian: ('true' or 'false')
                Lorentzian Norm
                flag: --inLorentzian %s
        inMax: (an integer (int or long))
                Max Iterations
                flag: --inMax %d
        inMean: (a float)
                Mean Curvature Threshold
                flag: --inMean %f
        inSOR: (a float)
                SOR Parameter
                flag: --inSOR %f
        inStep: (an integer (int or long))
                Step Size
                flag: --inStep %d
        inTopology: ('26/6' or '6/26' or '18/6' or '6/18' or '6/6' or 'wcs'
                 or 'wco' or 'no')
                Topology
                flag: --inTopology %s
        null: (a string)
                Execution Time
                flag: --null %s
        outInflated: (a boolean or a file name)
                Inflated Surface
                flag: --outInflated %s
        outOriginal: (a boolean or a file name)
                Original Surface
                flag: --outOriginal %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        outInflated: (an existing file name)
                Inflated Surface
        outOriginal: (an existing file name)
                Original Surface

.. _nipype.interfaces.mipav.developer.JistIntensityMp2rageMasking:


.. index:: JistIntensityMp2rageMasking

JistIntensityMp2rageMasking
---------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L737>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run de.mpg.cbs.jist.intensity.JistIntensityMp2rageMasking **

title: MP2RAGE Background Masking

category: Developer Tools

description: Estimate a background signal mask for a MP2RAGE dataset.

version: 3.0.RC

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
        inBackground: ('exponential' or 'half-normal')
                Model distribution for background noise (default is half-normal,
                exponential is more stringent).
                flag: --inBackground %s
        inMasking: ('binary' or 'proba')
                Whether to use a binary threshold or a weighted average based on the
                probability.
                flag: --inMasking %s
        inQuantitative: (an existing file name)
                Quantitative T1 Map (T1_Images) Image
                flag: --inQuantitative %s
        inSecond: (an existing file name)
                Second inversion (Inv2) Image
                flag: --inSecond %s
        inSkip: ('true' or 'false')
                Skip zero values
                flag: --inSkip %s
        inT1weighted: (an existing file name)
                T1-weighted (UNI) Image
                flag: --inT1weighted %s
        null: (a string)
                Execution Time
                flag: --null %s
        outMasked: (a boolean or a file name)
                Masked T1 Map Image
                flag: --outMasked %s
        outMasked2: (a boolean or a file name)
                Masked Iso Image
                flag: --outMasked2 %s
        outSignal: (a boolean or a file name)
                Signal Proba Image
                flag: --outSignal %s
        outSignal2: (a boolean or a file name)
                Signal Mask Image
                flag: --outSignal2 %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        outMasked: (an existing file name)
                Masked T1 Map Image
        outMasked2: (an existing file name)
                Masked Iso Image
        outSignal: (an existing file name)
                Signal Proba Image
        outSignal2: (an existing file name)
                Signal Mask Image

.. _nipype.interfaces.mipav.developer.JistLaminarProfileCalculator:


.. index:: JistLaminarProfileCalculator

JistLaminarProfileCalculator
----------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L159>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run de.mpg.cbs.jist.laminar.JistLaminarProfileCalculator **

title: Profile Calculator

category: Developer Tools

description: Compute various moments for intensities mapped along a cortical profile.

version: 3.0.RC

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
        inIntensity: (an existing file name)
                Intensity Profile Image
                flag: --inIntensity %s
        inMask: (an existing file name)
                Mask Image (opt, 3D or 4D)
                flag: --inMask %s
        incomputed: ('mean' or 'stdev' or 'skewness' or 'kurtosis')
                computed statistic
                flag: --incomputed %s
        null: (a string)
                Execution Time
                flag: --null %s
        outResult: (a boolean or a file name)
                Result
                flag: --outResult %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        outResult: (an existing file name)
                Result

.. _nipype.interfaces.mipav.developer.JistLaminarProfileGeometry:


.. index:: JistLaminarProfileGeometry

JistLaminarProfileGeometry
--------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L126>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run de.mpg.cbs.jist.laminar.JistLaminarProfileGeometry **

title: Profile Geometry

category: Developer Tools

description: Compute various geometric quantities for a cortical layers.

version: 3.0.RC

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
        inProfile: (an existing file name)
                Profile Surface Image
                flag: --inProfile %s
        incomputed: ('thickness' or 'curvedness' or 'shape_index' or
                 'mean_curvature' or 'gauss_curvature' or 'profile_length' or
                 'profile_curvature' or 'profile_torsion')
                computed measure
                flag: --incomputed %s
        inoutside: (a float)
                outside extension (mm)
                flag: --inoutside %f
        inregularization: ('none' or 'Gaussian')
                regularization
                flag: --inregularization %s
        insmoothing: (a float)
                smoothing parameter
                flag: --insmoothing %f
        null: (a string)
                Execution Time
                flag: --null %s
        outResult: (a boolean or a file name)
                Result
                flag: --outResult %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        outResult: (an existing file name)
                Result

.. _nipype.interfaces.mipav.developer.JistLaminarProfileSampling:


.. index:: JistLaminarProfileSampling

JistLaminarProfileSampling
--------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L532>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run de.mpg.cbs.jist.laminar.JistLaminarProfileSampling **

title: Profile Sampling

category: Developer Tools

description: Sample some intensity image along a cortical profile across layer surfaces.

version: 3.0.RC

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
        inCortex: (an existing file name)
                Cortex Mask (opt)
                flag: --inCortex %s
        inIntensity: (an existing file name)
                Intensity Image
                flag: --inIntensity %s
        inProfile: (an existing file name)
                Profile Surface Image
                flag: --inProfile %s
        null: (a string)
                Execution Time
                flag: --null %s
        outProfile2: (a boolean or a file name)
                Profile 4D Mask
                flag: --outProfile2 %s
        outProfilemapped: (a boolean or a file name)
                Profile-mapped Intensity Image
                flag: --outProfilemapped %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        outProfile2: (an existing file name)
                Profile 4D Mask
        outProfilemapped: (an existing file name)
                Profile-mapped Intensity Image

.. _nipype.interfaces.mipav.developer.JistLaminarROIAveraging:


.. index:: JistLaminarROIAveraging

JistLaminarROIAveraging
-----------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L234>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run de.mpg.cbs.jist.laminar.JistLaminarROIAveraging **

title: Profile ROI Averaging

category: Developer Tools

description: Compute an average profile over a given ROI.

version: 3.0.RC

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
        inIntensity: (an existing file name)
                Intensity Profile Image
                flag: --inIntensity %s
        inMask: (an existing file name)
                Mask Image (opt, 3D or 4D)
                flag: --inMask %s
        inROI: (an existing file name)
                ROI Mask
                flag: --inROI %s
        inROI2: (a string)
                ROI Name
                flag: --inROI2 %s
        null: (a string)
                Execution Time
                flag: --null %s
        outROI3: (a boolean or a file name)
                ROI Average
                flag: --outROI3 %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        outROI3: (an existing file name)
                ROI Average

.. _nipype.interfaces.mipav.developer.JistLaminarVolumetricLayering:


.. index:: JistLaminarVolumetricLayering

JistLaminarVolumetricLayering
-----------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L36>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run de.mpg.cbs.jist.laminar.JistLaminarVolumetricLayering **

title: Volumetric Layering

category: Developer Tools

description: Builds a continuous layering of the cortex following distance-preserving or volume-preserving models of cortical folding.
Waehnert MD, Dinse J, Weiss M, Streicher MN, Waehnert P, Geyer S, Turner R, Bazin PL, Anatomically motivated modeling of cortical laminae, Neuroimage, 2013.

version: 3.0.RC

contributor: Miriam Waehnert (waehnert@cbs.mpg.de) http://www.cbs.mpg.de/

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
        inInner: (an existing file name)
                Inner Distance Image (GM/WM boundary)
                flag: --inInner %s
        inLayering: ('distance-preserving' or 'volume-preserving')
                Layering method
                flag: --inLayering %s
        inLayering2: ('outward' or 'inward')
                Layering direction
                flag: --inLayering2 %s
        inMax: (an integer (int or long))
                Max iterations for narrow band evolution
                flag: --inMax %d
        inMin: (a float)
                Min change ratio for narrow band evolution
                flag: --inMin %f
        inNumber: (an integer (int or long))
                Number of layers
                flag: --inNumber %d
        inOuter: (an existing file name)
                Outer Distance Image (CSF/GM boundary)
                flag: --inOuter %s
        inTopology: ('26/6' or '6/26' or '18/6' or '6/18' or '6/6' or 'wcs'
                 or 'wco' or 'no')
                Topology
                flag: --inTopology %s
        incurvature: (an integer (int or long))
                curvature approximation scale (voxels)
                flag: --incurvature %d
        inpresmooth: ('true' or 'false')
                pre-smooth cortical surfaces
                flag: --inpresmooth %s
        inratio: (a float)
                ratio smoothing kernel size (voxels)
                flag: --inratio %f
        null: (a string)
                Execution Time
                flag: --null %s
        outContinuous: (a boolean or a file name)
                Continuous depth measurement
                flag: --outContinuous %s
        outDiscrete: (a boolean or a file name)
                Discrete sampled layers
                flag: --outDiscrete %s
        outLayer: (a boolean or a file name)
                Layer boundary surfaces
                flag: --outLayer %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        outContinuous: (an existing file name)
                Continuous depth measurement
        outDiscrete: (an existing file name)
                Discrete sampled layers
        outLayer: (an existing file name)
                Layer boundary surfaces

.. _nipype.interfaces.mipav.developer.MedicAlgorithmImageCalculator:


.. index:: MedicAlgorithmImageCalculator

MedicAlgorithmImageCalculator
-----------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L461>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run edu.jhu.ece.iacl.plugins.utilities.math.MedicAlgorithmImageCalculator **

title: Image Calculator

category: Developer Tools

description: Perform simple image calculator operations on two images. The operations include 'Add', 'Subtract', 'Multiply', and 'Divide'

version: 1.10.RC

documentation-url: http://www.iacl.ece.jhu.edu/

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
        inOperation: ('Add' or 'Subtract' or 'Multiply' or 'Divide' or 'Min'
                 or 'Max')
                Operation
                flag: --inOperation %s
        inVolume: (an existing file name)
                Volume 1
                flag: --inVolume %s
        inVolume2: (an existing file name)
                Volume 2
                flag: --inVolume2 %s
        null: (a string)
                Execution Time
                flag: --null %s
        outResult: (a boolean or a file name)
                Result Volume
                flag: --outResult %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        outResult: (an existing file name)
                Result Volume

.. _nipype.interfaces.mipav.developer.MedicAlgorithmLesionToads:


.. index:: MedicAlgorithmLesionToads

MedicAlgorithmLesionToads
-------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L301>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run edu.jhu.ece.iacl.plugins.classification.MedicAlgorithmLesionToads **

title: Lesion TOADS

category: Developer Tools

description: Algorithm for simulataneous brain structures and MS lesion segmentation of MS Brains. The brain segmentation is topologically consistent and the algorithm can use multiple MR sequences as input data.
N. Shiee, P.-L. Bazin, A.Z. Ozturk, P.A. Calabresi, D.S. Reich, D.L. Pham, "A Topology-Preserving Approach to the Segmentation of Brain Images with Multiple Sclerosis", NeuroImage, vol. 49, no. 2, pp. 1524-1535, 2010.

version: 1.9.R

contributor: Navid Shiee (navid.shiee@nih.gov) http://iacl.ece.jhu.edu/~nshiee/

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
        inAtlas: ('With Lesion' or 'No Lesion')
                Atlas to Use
                flag: --inAtlas %s
        inAtlas2: (an existing file name)
                Atlas File - With Lesions
                flag: --inAtlas2 %s
        inAtlas3: (an existing file name)
                Atlas File - No Lesion - T1 and FLAIR
                flag: --inAtlas3 %s
        inAtlas4: (an existing file name)
                Atlas File - No Lesion - T1 Only
                flag: --inAtlas4 %s
        inAtlas5: (a float)
                Controls the effect of the statistical atlas on the segmentation
                flag: --inAtlas5 %f
        inAtlas6: ('rigid' or 'multi_fully_affine')
                Atlas alignment
                flag: --inAtlas6 %s
        inConnectivity: ('(26,6)' or '(6,26)' or '(6,18)' or '(18,6)')
                Connectivity (foreground,background)
                flag: --inConnectivity %s
        inCorrect: ('true' or 'false')
                Correct MR field inhomogeneity.
                flag: --inCorrect %s
        inFLAIR: (an existing file name)
                FLAIR Image
                flag: --inFLAIR %s
        inInclude: ('true' or 'false')
                Include lesion in WM class in hard classification
                flag: --inInclude %s
        inMaximum: (an integer (int or long))
                Maximum distance from the interventricular WM boundary to downweight
                the lesion membership to avoid false postives
                flag: --inMaximum %d
        inMaximum2: (an integer (int or long))
                Maximum Ventircle Distance
                flag: --inMaximum2 %d
        inMaximum3: (an integer (int or long))
                Maximum InterVentricular Distance
                flag: --inMaximum3 %d
        inMaximum4: (a float)
                Maximum amount of relative change in the energy function considered
                as the convergence criteria
                flag: --inMaximum4 %f
        inMaximum5: (an integer (int or long))
                Maximum iterations
                flag: --inMaximum5 %d
        inOutput: ('hard segmentation' or 'hard segmentation+memberships' or
                 'cruise inputs' or 'dura removal inputs')
                Output images
                flag: --inOutput %s
        inOutput2: ('true' or 'false')
                Output the hard classification using maximum membership (not
                neceesarily topologically correct)
                flag: --inOutput2 %s
        inOutput3: ('true' or 'false')
                Output the estimated inhomogeneity field
                flag: --inOutput3 %s
        inSmooting: (a float)
                Controls the effect of neighberhood voxels on the membership
                flag: --inSmooting %f
        inT1_MPRAGE: (an existing file name)
                T1_MPRAGE Image
                flag: --inT1_MPRAGE %s
        inT1_SPGR: (an existing file name)
                T1_SPGR Image
                flag: --inT1_SPGR %s
        null: (a string)
                Execution Time
                flag: --null %s
        outCortical: (a boolean or a file name)
                Cortical GM Membership
                flag: --outCortical %s
        outFilled: (a boolean or a file name)
                Filled WM Membership
                flag: --outFilled %s
        outHard: (a boolean or a file name)
                Hard segmentation
                flag: --outHard %s
        outHard2: (a boolean or a file name)
                Hard segmentationfrom memberships
                flag: --outHard2 %s
        outInhomogeneity: (a boolean or a file name)
                Inhomogeneity Field
                flag: --outInhomogeneity %s
        outLesion: (a boolean or a file name)
                Lesion Segmentation
                flag: --outLesion %s
        outMembership: (a boolean or a file name)
                Membership Functions
                flag: --outMembership %s
        outSulcal: (a boolean or a file name)
                Sulcal CSF Membership
                flag: --outSulcal %s
        outWM: (a boolean or a file name)
                WM Mask
                flag: --outWM %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        outCortical: (an existing file name)
                Cortical GM Membership
        outFilled: (an existing file name)
                Filled WM Membership
        outHard: (an existing file name)
                Hard segmentation
        outHard2: (an existing file name)
                Hard segmentationfrom memberships
        outInhomogeneity: (an existing file name)
                Inhomogeneity Field
        outLesion: (an existing file name)
                Lesion Segmentation
        outMembership: (an existing file name)
                Membership Functions
        outSulcal: (an existing file name)
                Sulcal CSF Membership
        outWM: (an existing file name)
                WM Mask

.. _nipype.interfaces.mipav.developer.MedicAlgorithmMipavReorient:


.. index:: MedicAlgorithmMipavReorient

MedicAlgorithmMipavReorient
---------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L571>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run edu.jhu.ece.iacl.plugins.utilities.volume.MedicAlgorithmMipavReorient **

title: Reorient Volume

category: Developer Tools

description: Reorient a volume to a particular anatomical orientation.

version: .alpha

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
        inInterpolation: ('Nearest Neighbor' or 'Trilinear' or 'Bspline 3rd
                 order' or 'Bspline 4th order' or 'Cubic Lagrangian' or 'Quintic
                 Lagrangian' or 'Heptic Lagrangian' or 'Windowed Sinc')
                Interpolation
                flag: --inInterpolation %s
        inNew: ('Dicom axial' or 'Dicom coronal' or 'Dicom sagittal' or 'User
                 defined')
                New image orientation
                flag: --inNew %s
        inResolution: ('Unchanged' or 'Finest cubic' or 'Coarsest cubic' or
                 'Same as template')
                Resolution
                flag: --inResolution %s
        inSource: (a list of items which are a file name)
                Source
                flag: --inSource %s
        inTemplate: (an existing file name)
                Template
                flag: --inTemplate %s
        inUser: ('Unknown' or 'Patient Right to Left' or 'Patient Left to
                 Right' or 'Patient Posterior to Anterior' or 'Patient Anterior to
                 Posterior' or 'Patient Inferior to Superior' or 'Patient Superior
                 to Inferior')
                User defined X-axis orientation (image left to right)
                flag: --inUser %s
        inUser2: ('Unknown' or 'Patient Right to Left' or 'Patient Left to
                 Right' or 'Patient Posterior to Anterior' or 'Patient Anterior to
                 Posterior' or 'Patient Inferior to Superior' or 'Patient Superior
                 to Inferior')
                User defined Y-axis orientation (image top to bottom)
                flag: --inUser2 %s
        inUser3: ('Unknown' or 'Patient Right to Left' or 'Patient Left to
                 Right' or 'Patient Posterior to Anterior' or 'Patient Anterior to
                 Posterior' or 'Patient Inferior to Superior' or 'Patient Superior
                 to Inferior')
                User defined Z-axis orientation (into the screen)
                flag: --inUser3 %s
        inUser4: ('Axial' or 'Coronal' or 'Sagittal' or 'Unknown')
                User defined Image Orientation
                flag: --inUser4 %s
        null: (a string)
                Execution Time
                flag: --null %s
        outReoriented: (a list of items which are a file name)
                Reoriented Volume
                flag: --outReoriented %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        None

.. _nipype.interfaces.mipav.developer.MedicAlgorithmN3:


.. index:: MedicAlgorithmN3

MedicAlgorithmN3
----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L200>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run edu.jhu.ece.iacl.plugins.classification.MedicAlgorithmN3 **

title: N3 Correction

category: Developer Tools

description: Non-parametric Intensity Non-uniformity Correction, N3, originally by J.G. Sled.

version: 1.8.R

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
        inAutomatic: ('true' or 'false')
                If true determines the threshold by histogram analysis. If true a
                VOI cannot be used and the input threshold is ignored.
                flag: --inAutomatic %s
        inEnd: (a float)
                Usually 0.01-0.00001, The measure used to terminate the iterations
                is the coefficient of variation of change in field estimates between
                successive iterations.
                flag: --inEnd %f
        inField: (a float)
                Characteristic distance over which the field varies. The distance
                between adjacent knots in bspline fitting with at least 4 knots
                going in every dimension. The default in the dialog is one third the
                distance (resolution * extents) of the smallest dimension.
                flag: --inField %f
        inInput: (an existing file name)
                Input Volume
                flag: --inInput %s
        inKernel: (a float)
                Usually between 0.05-0.50, Width of deconvolution kernel used to
                sharpen the histogram. Larger values give faster convergence while
                smaller values give greater accuracy.
                flag: --inKernel %f
        inMaximum: (an integer (int or long))
                Maximum number of Iterations
                flag: --inMaximum %d
        inSignal: (a float)
                Default = min + 1, Values at less than threshold are treated as part
                of the background
                flag: --inSignal %f
        inSubsample: (a float)
                Usually between 1-32, The factor by which the data is subsampled to
                a lower resolution in estimating the slowly varying non-uniformity
                field. Reduce sampling in the finest sampling direction by the
                shrink factor.
                flag: --inSubsample %f
        inWeiner: (a float)
                Usually between 0.0-1.0
                flag: --inWeiner %f
        null: (a string)
                Execution Time
                flag: --null %s
        outInhomogeneity: (a boolean or a file name)
                Inhomogeneity Corrected Volume
                flag: --outInhomogeneity %s
        outInhomogeneity2: (a boolean or a file name)
                Inhomogeneity Field
                flag: --outInhomogeneity2 %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        outInhomogeneity: (an existing file name)
                Inhomogeneity Corrected Volume
        outInhomogeneity2: (an existing file name)
                Inhomogeneity Field

.. _nipype.interfaces.mipav.developer.MedicAlgorithmSPECTRE2010:


.. index:: MedicAlgorithmSPECTRE2010

MedicAlgorithmSPECTRE2010
-------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L651>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run edu.jhu.ece.iacl.plugins.segmentation.skull_strip.MedicAlgorithmSPECTRE2010 **

title: SPECTRE 2010

category: Developer Tools

description: Simple Paradigm for Extra-Cranial Tissue REmoval
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Algorithm Version: 1.6
GUI Version: 1.10

A. Carass, M.B. Wheeler, J. Cuzzocreo, P.-L. Bazin, S.S. Bassett, and J.L. Prince, 'A Joint Registration and Segmentation Approach to Skull Stripping', Fourth IEEE International Symposium on Biomedical Imaging (ISBI 2007), Arlington, VA, April 12-15, 2007.
A. Carass, J. Cuzzocreo, M.B. Wheeler, P.-L. Bazin, S.M. Resnick, and J.L. Prince, 'Simple paradigm for extra-cerebral tissue removal: Algorithm and analysis', NeuroImage 56(4):1982-1992, 2011.

version: 1.6.R

documentation-url: http://www.iacl.ece.jhu.edu/

contributor: Aaron Carass (aaron_carass@jhu.edu) http://www.iacl.ece.jhu.edu/
Hanlin Wan (hanlinwan@gmail.com)

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
        inApply: ('All' or 'X' or 'Y' or 'Z')
                Apply rotation
                flag: --inApply %s
        inAtlas: (an existing file name)
                SPECTRE atlas description file. A text file enumerating atlas files
                and landmarks.
                flag: --inAtlas %s
        inBackground: (a float)
                flag: --inBackground %f
        inCoarse: (a float)
                Coarse angle increment
                flag: --inCoarse %f
        inCost: ('Correlation ratio' or 'Least squares' or 'Normalized cross
                 correlation' or 'Normalized mutual information')
                Cost function
                flag: --inCost %s
        inDegrees: ('Rigid - 6' or 'Global rescale - 7' or 'Specific rescale
                 - 9' or 'Affine - 12')
                Degrees of freedom
                flag: --inDegrees %s
        inFind: ('true' or 'false')
                Find Midsaggital Plane
                flag: --inFind %s
        inFine: (a float)
                Fine angle increment
                flag: --inFine %f
        inImage: ('T1_SPGR' or 'T1_ALT' or 'T1_MPRAGE' or 'T2' or 'FLAIR')
                Set the image modality. MP-RAGE is recommended for most T1 sequence
                images.
                flag: --inImage %s
        inInhomogeneity: ('true' or 'false')
                Set to false by default, this parameter will make FANTASM try to do
                inhomogeneity correction during it's iterative cycle.
                flag: --inInhomogeneity %s
        inInitial: (an integer (int or long))
                Erosion of the inital mask, which is based on the probability mask
                and the classification., The initial mask is ouput as the d0 volume
                at the conclusion of SPECTRE.
                flag: --inInitial %d
        inInitial2: (a float)
                Initial probability threshold
                flag: --inInitial2 %f
        inInput: (an existing file name)
                Input volume to be skullstripped.
                flag: --inInput %s
        inMMC: (an integer (int or long))
                The size of the dilation step within the Modified Morphological
                Closing.
                flag: --inMMC %d
        inMMC2: (an integer (int or long))
                The size of the erosion step within the Modified Morphological
                Closing.
                flag: --inMMC2 %d
        inMaximum: (a float)
                Maximum angle
                flag: --inMaximum %f
        inMinimum: (a float)
                Minimum probability threshold
                flag: --inMinimum %f
        inMinimum2: (a float)
                Minimum angle
                flag: --inMinimum2 %f
        inMultiple: (an integer (int or long))
                Multiple of tolerance to bracket the minimum
                flag: --inMultiple %d
        inMultithreading: ('true' or 'false')
                Set to false by default, this parameter controls the multithreaded
                behavior of the linear registration.
                flag: --inMultithreading %s
        inNumber: (an integer (int or long))
                Number of iterations
                flag: --inNumber %d
        inNumber2: (an integer (int or long))
                Number of minima from Level 8 to test at Level 4
                flag: --inNumber2 %d
        inOutput: ('true' or 'false')
                Determines if the output results are transformed back into the space
                of the original input image.
                flag: --inOutput %s
        inOutput2: ('true' or 'false')
                Output Plane?
                flag: --inOutput2 %s
        inOutput3: ('true' or 'false')
                Output Split-Halves?
                flag: --inOutput3 %s
        inOutput4: ('true' or 'false')
                Output Segmentation on Plane?
                flag: --inOutput4 %s
        inOutput5: ('Trilinear' or 'Bspline 3rd order' or 'Bspline 4th order'
                 or 'Cubic Lagrangian' or 'Quintic Lagrangian' or 'Heptic
                 Lagrangian' or 'Windowed sinc' or 'Nearest Neighbor')
                Output interpolation
                flag: --inOutput5 %s
        inRegistration: ('Trilinear' or 'Bspline 3rd order' or 'Bspline 4th
                 order' or 'Cubic Lagrangian' or 'Quintic Lagrangian' or 'Heptic
                 Lagrangian' or 'Windowed sinc')
                Registration interpolation
                flag: --inRegistration %s
        inResample: ('true' or 'false')
                Determines if the data is resampled to be isotropic during the
                processing.
                flag: --inResample %s
        inRun: ('true' or 'false')
                Run Smooth Brain Mask
                flag: --inRun %s
        inSkip: ('true' or 'false')
                Skip multilevel search (Assume images are close to alignment)
                flag: --inSkip %s
        inSmoothing: (a float)
                flag: --inSmoothing %f
        inSubsample: ('true' or 'false')
                Subsample image for speed
                flag: --inSubsample %s
        inUse: ('true' or 'false')
                Use the max of the min resolutions of the two datasets when
                resampling
                flag: --inUse %s
        null: (a string)
                Execution Time
                flag: --null %s
        outFANTASM: (a boolean or a file name)
                Tissue classification of of the whole input volume.
                flag: --outFANTASM %s
        outMask: (a boolean or a file name)
                Binary Mask of the skullstripped result with just the brain
                flag: --outMask %s
        outMidsagittal: (a boolean or a file name)
                Plane dividing the brain hemispheres
                flag: --outMidsagittal %s
        outOriginal: (a boolean or a file name)
                If Output in Original Space Flag is true then outputs the original
                input volume. Otherwise outputs the axialy reoriented input volume.
                flag: --outOriginal %s
        outPrior: (a boolean or a file name)
                Probability prior from the atlas registrations
                flag: --outPrior %s
        outSegmentation: (a boolean or a file name)
                2D image showing the tissue classification on the midsagittal plane
                flag: --outSegmentation %s
        outSplitHalves: (a boolean or a file name)
                Skullstripped mask of the brain with the hemispheres divided.
                flag: --outSplitHalves %s
        outStripped: (a boolean or a file name)
                Skullstripped result of the input volume with just the brain.
                flag: --outStripped %s
        outd0: (a boolean or a file name)
                Initial Brainmask
                flag: --outd0 %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        outFANTASM: (an existing file name)
                Tissue classification of of the whole input volume.
        outMask: (an existing file name)
                Binary Mask of the skullstripped result with just the brain
        outMidsagittal: (an existing file name)
                Plane dividing the brain hemispheres
        outOriginal: (an existing file name)
                If Output in Original Space Flag is true then outputs the original
                input volume. Otherwise outputs the axialy reoriented input volume.
        outPrior: (an existing file name)
                Probability prior from the atlas registrations
        outSegmentation: (an existing file name)
                2D image showing the tissue classification on the midsagittal plane
        outSplitHalves: (an existing file name)
                Skullstripped mask of the brain with the hemispheres divided.
        outStripped: (an existing file name)
                Skullstripped result of the input volume with just the brain.
        outd0: (an existing file name)
                Initial Brainmask

.. _nipype.interfaces.mipav.developer.MedicAlgorithmThresholdToBinaryMask:


.. index:: MedicAlgorithmThresholdToBinaryMask

MedicAlgorithmThresholdToBinaryMask
-----------------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L771>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run edu.jhu.ece.iacl.plugins.utilities.volume.MedicAlgorithmThresholdToBinaryMask **

title: Threshold to Binary Mask

category: Developer Tools

description: Given a volume and an intensity range create a binary mask for values within that range.

version: 1.2.RC

documentation-url: http://www.iacl.ece.jhu.edu/

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
        inLabel: (a list of items which are a file name)
                Input volumes
                flag: --inLabel %s
        inMaximum: (a float)
                Maximum threshold value.
                flag: --inMaximum %f
        inMinimum: (a float)
                Minimum threshold value.
                flag: --inMinimum %f
        inUse: ('true' or 'false')
                Use the images max intensity as the max value of the range.
                flag: --inUse %s
        null: (a string)
                Execution Time
                flag: --null %s
        outBinary: (a list of items which are a file name)
                Binary Mask
                flag: --outBinary %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        None

.. _nipype.interfaces.mipav.developer.RandomVol:


.. index:: RandomVol

RandomVol
---------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mipav/developer.py#L426>`__

Wraps command **java edu.jhu.ece.iacl.jist.cli.run edu.jhu.bme.smile.demo.RandomVol **

title: Random Volume Generator

category: Developer Tools

description: Generate a random scalar volume.

version: 1.12.RC

documentation-url: http://www.nitrc.org/projects/jist/

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
        inField: ('Uniform' or 'Normal' or 'Exponential')
                Field
                flag: --inField %s
        inLambda: (a float)
                Lambda Value for Exponential Distribution
                flag: --inLambda %f
        inMaximum: (an integer (int or long))
                Maximum Value
                flag: --inMaximum %d
        inMinimum: (an integer (int or long))
                Minimum Value
                flag: --inMinimum %d
        inSize: (an integer (int or long))
                Size of Volume in X direction
                flag: --inSize %d
        inSize2: (an integer (int or long))
                Size of Volume in Y direction
                flag: --inSize2 %d
        inSize3: (an integer (int or long))
                Size of Volume in Z direction
                flag: --inSize3 %d
        inSize4: (an integer (int or long))
                Size of Volume in t direction
                flag: --inSize4 %d
        inStandard: (an integer (int or long))
                Standard Deviation for Normal Distribution
                flag: --inStandard %d
        null: (a string)
                Execution Time
                flag: --null %s
        outRand1: (a boolean or a file name)
                Rand1
                flag: --outRand1 %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xDefaultMem: (an integer (int or long))
                Set default maximum heap size
                flag: -xDefaultMem %d
        xMaxProcess: (an integer (int or long), nipype default value: 1)
                Set default maximum number of processes.
                flag: -xMaxProcess %d
        xPrefExt: ('nrrd')
                Output File Type
                flag: --xPrefExt %s

Outputs::

        outRand1: (an existing file name)
                Rand1
