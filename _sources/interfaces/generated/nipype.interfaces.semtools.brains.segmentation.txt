.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.brains.segmentation
=======================================


.. _nipype.interfaces.semtools.brains.segmentation.BRAINSTalairach:


.. index:: BRAINSTalairach

BRAINSTalairach
---------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/brains/segmentation.py#L62>`__

Wraps command ** BRAINSTalairach **

title: BRAINS Talairach

category: BRAINS.Segmentation

description: This program creates a VTK structured grid defining the Talairach coordinate system based on four points: AC, PC, IRP, and SLA. The resulting structred grid can be written as either a classic VTK file or the new VTK XML file format. Two representations of the resulting grid can be written. The first is a bounding box representation that also contains the location of the AC and PC points. The second representation is the full Talairach grid representation that includes the additional rows of boxes added to the inferior allowing full coverage of the cerebellum.

version: 0.1

documentation-url: http://www.nitrc.org/plugins/mwiki/index.php/brains:BRAINSTalairach

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Steven Dunn and Vincent Magnotta

acknowledgements: Funding for this work was provided by NIH/NINDS award NS050568

Inputs::

        [Mandatory]

        [Optional]
        AC: (a list of items which are a float)
                Location of AC Point
                flag: --AC %s
        ACisIndex: (a boolean)
                AC Point is Index
                flag: --ACisIndex
        IRP: (a list of items which are a float)
                Location of IRP Point
                flag: --IRP %s
        IRPisIndex: (a boolean)
                IRP Point is Index
                flag: --IRPisIndex
        PC: (a list of items which are a float)
                Location of PC Point
                flag: --PC %s
        PCisIndex: (a boolean)
                PC Point is Index
                flag: --PCisIndex
        SLA: (a list of items which are a float)
                Location of SLA Point
                flag: --SLA %s
        SLAisIndex: (a boolean)
                SLA Point is Index
                flag: --SLAisIndex
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
        inputVolume: (an existing file name)
                Input image used to define physical space of images
                flag: --inputVolume %s
        outputBox: (a boolean or a file name)
                Name of the resulting Talairach Bounding Box file
                flag: --outputBox %s
        outputGrid: (a boolean or a file name)
                Name of the resulting Talairach Grid file
                flag: --outputGrid %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputBox: (an existing file name)
                Name of the resulting Talairach Bounding Box file
        outputGrid: (an existing file name)
                Name of the resulting Talairach Grid file

.. _nipype.interfaces.semtools.brains.segmentation.BRAINSTalairachMask:


.. index:: BRAINSTalairachMask

BRAINSTalairachMask
-------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/brains/segmentation.py#L102>`__

Wraps command ** BRAINSTalairachMask **

title: Talairach Mask

category: BRAINS.Segmentation

description: This program creates a binary image representing the specified Talairach region. The input is an example image to define the physical space for the resulting image, the Talairach grid representation in VTK format, and the file containing the Talairach box definitions to be generated. These can be combined in BRAINS to create a label map using the procedure Brains::WorkupUtils::CreateLabelMapFromBinaryImages.

version: 0.1

documentation-url: http://www.nitrc.org/plugins/mwiki/index.php/brains:BRAINSTalairachMask

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Steven Dunn and Vincent Magnotta

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
        expand: (a boolean)
                Expand exterior box to include surface CSF
                flag: --expand
        hemisphereMode: ('left' or 'right' or 'both')
                Mode for box creation: left, right, both
                flag: --hemisphereMode %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVolume: (an existing file name)
                Input image used to define physical space of resulting mask
                flag: --inputVolume %s
        outputVolume: (a boolean or a file name)
                Output filename for the resulting binary image
                flag: --outputVolume %s
        talairachBox: (an existing file name)
                Name of the Talairach box file.
                flag: --talairachBox %s
        talairachParameters: (an existing file name)
                Name of the Talairach parameter file.
                flag: --talairachParameters %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Output filename for the resulting binary image

.. _nipype.interfaces.semtools.brains.segmentation.SimilarityIndex:


.. index:: SimilarityIndex

SimilarityIndex
---------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/brains/segmentation.py#L20>`__

Wraps command ** SimilarityIndex **

title: BRAINSCut:SimilarityIndexComputation

category: BRAINS.Segmentation

description: Automatic analysis of BRAINSCut Output

version: 1.0

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Eunyoung Regin Kim

Inputs::

        [Mandatory]

        [Optional]
        ANNContinuousVolume: (an existing file name)
                ANN Continuous volume to be compared to the manual volume
                flag: --ANNContinuousVolume %s
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
        inputManualVolume: (an existing file name)
                input manual(reference) volume
                flag: --inputManualVolume %s
        outputCSVFilename: (an existing file name)
                output CSV Filename
                flag: --outputCSVFilename %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        thresholdInterval: (a float)
                Threshold interval to compute similarity index between zero and one
                flag: --thresholdInterval %f

Outputs::

        None
