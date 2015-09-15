.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.diffusion.tractography.ukftractography
==========================================================


.. _nipype.interfaces.semtools.diffusion.tractography.ukftractography.UKFTractography:


.. index:: UKFTractography

UKFTractography
---------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/tractography/ukftractography.py#L51>`__

Wraps command ** UKFTractography **

title: UKF Tractography

category: Diffusion.Tractography

description: This module traces fibers in a DWI Volume using the multiple tensor unscented Kalman Filter methology. For more informations check the documentation.

version: 1.0

documentation-url: http://www.nitrc.org/plugins/mwiki/index.php/ukftractography:MainPage

contributor: Yogesh Rathi, Stefan Lienhard, Yinpeng Li, Martin Styner, Ipek Oguz, Yundi Shi, Christian Baumgartner, Kent Williams, Hans Johnson, Peter Savadjiev, Carl-Fredrik Westin.

acknowledgements: The development of this module was supported by NIH grants R01 MH097979 (PI Rathi), R01 MH092862 (PIs Westin and Verma), U01 NS083223 (PI Westin), R01 MH074794 (PI Westin) and P41 EB015902 (PI Kikinis).

Inputs::

        [Mandatory]

        [Optional]
        Ql: (a float)
                Process noise for eigenvalues
                flag: --Ql %f
        Qm: (a float)
                Process noise for angles/direction
                flag: --Qm %f
        Qw: (a float)
                Process noise for free water weights, ignored if no free water
                estimation
                flag: --Qw %f
        Rs: (a float)
                Measurement noise
                flag: --Rs %f
        args: (a string)
                Additional parameters to the command
                flag: %s
        dwiFile: (an existing file name)
                Input DWI volume
                flag: --dwiFile %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        freeWater: (a boolean)
                Adds a term for free water difusion to the model. (Note for experts:
                if checked, the 1T simple model is forced)
                flag: --freeWater
        fullTensorModel: (a boolean)
                Whether to use the full tensor model. If unchecked, use the default
                simple tensor model
                flag: --fullTensorModel
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        labels: (a list of items which are an integer (int or long))
                A vector of the ROI labels to be used
                flag: --labels %s
        maskFile: (an existing file name)
                Mask for diffusion tractography
                flag: --maskFile %s
        maxBranchingAngle: (a float)
                Maximum branching angle, in degrees. When using multiple tensors, a
                new branch will be created when the tensors' major directions form
                an angle between (minBranchingAngle, maxBranchingAngle). Branching
                is supressed when this maxBranchingAngle is set to 0.0
                flag: --maxBranchingAngle %f
        maxHalfFiberLength: (a float)
                The max length limit of the half fibers generated during
                tractography. Here the fiber is 'half' because the tractography goes
                in only one direction from one seed point at a time
                flag: --maxHalfFiberLength %f
        minBranchingAngle: (a float)
                Minimum branching angle, in degrees. When using multiple tensors, a
                new branch will be created when the tensors' major directions form
                an angle between (minBranchingAngle, maxBranchingAngle)
                flag: --minBranchingAngle %f
        minFA: (a float)
                Abort the tractography when the Fractional Anisotropy is less than
                this value
                flag: --minFA %f
        minGA: (a float)
                Abort the tractography when the Generalized Anisotropy is less than
                this value
                flag: --minGA %f
        numTensor: ('1' or '2')
                Number of tensors used
                flag: --numTensor %s
        numThreads: (an integer (int or long))
                Number of threads used during computation. Set to the number of
                cores on your workstation for optimal speed. If left undefined the
                number of cores detected will be used.
                flag: --numThreads %d
        recordCovariance: (a boolean)
                Whether to store the covariance. Will generate field 'covariance' in
                fiber.
                flag: --recordCovariance
        recordFA: (a boolean)
                Whether to store FA. Attaches field 'FA', and 'FA2' for 2-tensor
                case to fiber.
                flag: --recordFA
        recordFreeWater: (a boolean)
                Whether to store the fraction of free water. Attaches field
                'FreeWater' to fiber.
                flag: --recordFreeWater
        recordLength: (a float)
                Record length of tractography, in millimeters
                flag: --recordLength %f
        recordNMSE: (a boolean)
                Whether to store NMSE. Attaches field 'NMSE' to fiber.
                flag: --recordNMSE
        recordState: (a boolean)
                Whether to attach the states to the fiber. Will generate field
                'state'.
                flag: --recordState
        recordTensors: (a boolean)
                Recording the tensors enables Slicer to color the fiber bundles by
                FA, orientation, and so on. The fields will be called 'TensorN',
                where N is the tensor number.
                flag: --recordTensors
        recordTrace: (a boolean)
                Whether to store Trace. Attaches field 'Trace', and 'Trace2' for
                2-tensor case to fiber.
                flag: --recordTrace
        seedFALimit: (a float)
                Seed points whose FA are below this value are excluded
                flag: --seedFALimit %f
        seedsFile: (an existing file name)
                Seeds for diffusion. If not specified, full brain tractography will
                be performed, and the algorithm will start from every voxel in the
                brain mask where the Generalized Anisotropy is bigger than 0.18
                flag: --seedsFile %s
        seedsPerVoxel: (an integer (int or long))
                 Each seed generates a fiber, thus using more seeds generates more
                fibers. In general use 1 or 2 seeds, and for a more thorough result
                use 5 or 10 (depending on your machine this may take up to 2 days to
                run).,
                flag: --seedsPerVoxel %d
        stepLength: (a float)
                Step length of tractography, in millimeters
                flag: --stepLength %f
        storeGlyphs: (a boolean)
                Store tensors' main directions as two-point lines in a separate file
                named glyphs_{tracts}. When using multiple tensors, only the major
                tensors' main directions are stored
                flag: --storeGlyphs
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        tracts: (a boolean or a file name)
                Tracts generated, with first tensor output
                flag: --tracts %s
        tractsWithSecondTensor: (a boolean or a file name)
                Tracts generated, with second tensor output (if there is one)
                flag: --tractsWithSecondTensor %s
        writeAsciiTracts: (a boolean)
                Write tract file as a VTK binary data file
                flag: --writeAsciiTracts
        writeUncompressedTracts: (a boolean)
                Write tract file as a VTK uncompressed data file
                flag: --writeUncompressedTracts

Outputs::

        tracts: (an existing file name)
                Tracts generated, with first tensor output
        tractsWithSecondTensor: (an existing file name)
                Tracts generated, with second tensor output (if there is one)
