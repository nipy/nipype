.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.diffusion.diffusion
=======================================


.. _nipype.interfaces.semtools.diffusion.diffusion.DWIConvert:


.. index:: DWIConvert

DWIConvert
----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/diffusion.py#L254>`__

Wraps command ** DWIConvert **

title: DWIConverter

category: Diffusion.Diffusion Data Conversion

description: Converts diffusion weighted MR images in dicom series into Nrrd format for analysis in Slicer. This program has been tested on only a limited subset of DTI dicom formats available from Siemens, GE, and Phillips scanners. Work in progress to support dicom multi-frame data. The program parses dicom header to extract necessary information about measurement frame, diffusion weighting directions, b-values, etc, and write out a nrrd image. For non-diffusion weighted dicom images, it loads in an entire dicom series and writes out a single dicom volume in a .nhdr/.raw pair.

version: Version 1.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/DWIConverter

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Vince Magnotta (UIowa), Hans Johnson (UIowa), Joy Matsui (UIowa), Kent Williams (UIowa), Mark Scully (Uiowa), Xiaodong Tao (GE)

acknowledgements: This work is part of the National Alliance for Medical Image Computing (NAMIC), funded by the National Institutes of Health through the NIH Roadmap for Medical Research, Grant U54 EB005149.  Additional support for DTI data produced on Philips scanners was contributed by Vincent Magnotta and Hans Johnson at the University of Iowa.

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        conversionMode: ('DicomToNrrd' or 'DicomToFSL' or 'NrrdToFSL' or
                 'FSLToNrrd')
                Determine which conversion to perform. DicomToNrrd (default):
                Convert DICOM series to NRRD DicomToFSL: Convert DICOM series to
                NIfTI File + gradient/bvalue text files NrrdToFSL: Convert DWI NRRD
                file to NIfTI File + gradient/bvalue text files FSLToNrrd: Convert
                NIfTI File + gradient/bvalue text files to NRRD file.
                flag: --conversionMode %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        fMRI: (a boolean)
                Output a NRRD file, but without gradients
                flag: --fMRI
        fslNIFTIFile: (an existing file name)
                4D NIfTI file containing gradient volumes
                flag: --fslNIFTIFile %s
        gradientVectorFile: (a boolean or a file name)
                Text file giving gradient vectors
                flag: --gradientVectorFile %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputBValues: (an existing file name)
                The B Values are stored in FSL .bval text file format
                flag: --inputBValues %s
        inputBVectors: (an existing file name)
                The Gradient Vectors are stored in FSL .bvec text file format
                flag: --inputBVectors %s
        inputDicomDirectory: (an existing directory name)
                Directory holding Dicom series
                flag: --inputDicomDirectory %s
        inputVolume: (an existing file name)
                Input DWI volume -- not used for DicomToNrrd mode.
                flag: --inputVolume %s
        outputBValues: (a boolean or a file name)
                The B Values are stored in FSL .bval text file format (defaults to
                <outputVolume>.bval)
                flag: --outputBValues %s
        outputBVectors: (a boolean or a file name)
                The Gradient Vectors are stored in FSL .bvec text file format
                (defaults to <outputVolume>.bvec)
                flag: --outputBVectors %s
        outputDirectory: (a boolean or a directory name)
                Directory holding the output NRRD file
                flag: --outputDirectory %s
        outputVolume: (a boolean or a file name)
                Output filename (.nhdr or .nrrd)
                flag: --outputVolume %s
        smallGradientThreshold: (a float)
                If a gradient magnitude is greater than 0 and less than
                smallGradientThreshold, then DWIConvert will display an error
                message and quit, unless the useBMatrixGradientDirections option is
                set.
                flag: --smallGradientThreshold %f
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        useBMatrixGradientDirections: (a boolean)
                Fill the nhdr header with the gradient directions and bvalues
                computed out of the BMatrix. Only changes behavior for Siemens data.
                In some cases the standard public gradients are not properly
                computed. The gradients can emperically computed from the private
                BMatrix fields. In some cases the private BMatrix is consistent with
                the public grandients, but not in all cases, when it exists BMatrix
                is usually most robust.
                flag: --useBMatrixGradientDirections
        useIdentityMeaseurementFrame: (a boolean)
                Adjust all the gradients so that the measurement frame is an
                identity matrix.
                flag: --useIdentityMeaseurementFrame
        writeProtocolGradientsFile: (a boolean)
                Write the protocol gradients to a file suffixed by '.txt' as they
                were specified in the procol by multiplying each diffusion gradient
                direction by the measurement frame. This file is for debugging
                purposes only, the format is not fixed, and will likely change as
                debugging of new dicom formats is necessary.
                flag: --writeProtocolGradientsFile

Outputs::

        gradientVectorFile: (an existing file name)
                Text file giving gradient vectors
        outputBValues: (an existing file name)
                The B Values are stored in FSL .bval text file format (defaults to
                <outputVolume>.bval)
        outputBVectors: (an existing file name)
                The Gradient Vectors are stored in FSL .bvec text file format
                (defaults to <outputVolume>.bvec)
        outputDirectory: (an existing directory name)
                Directory holding the output NRRD file
        outputVolume: (an existing file name)
                Output filename (.nhdr or .nrrd)

.. _nipype.interfaces.semtools.diffusion.diffusion.dtiaverage:


.. index:: dtiaverage

dtiaverage
----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/diffusion.py#L20>`__

Wraps command ** dtiaverage **

title: DTIAverage (DTIProcess)

category: Diffusion.Diffusion Tensor Images.CommandLineOnly

description: dtiaverage is a program that allows to compute the average of an arbitrary number of tensor fields (listed after the --inputs option) This program is used in our pipeline as the last step of the atlas building processing. When all the tensor fields have been deformed in the same space, to create the average tensor field (--tensor_output) we use dtiaverage.
 Several average method can be used (specified by the --method option): euclidian, log-euclidian and pga. The default being euclidian.

version: 1.0.0

documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/DTIProcess

license: Copyright (c)  Casey Goodlett. All rights reserved.
    See http://www.ia.unc.edu/dev/Copyright.htm for details.
    This software is distributed WITHOUT ANY WARRANTY; without even
    the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
    PURPOSE.  See the above copyright notices for more information.

contributor: Casey Goodlett

Inputs::

        [Mandatory]

        [Optional]
        DTI_double: (a boolean)
                Tensor components are saved as doubles (cannot be visualized in
                Slicer)
                flag: --DTI_double
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
        inputs: (a list of items which are an existing file name)
                List of all the tensor fields to be averaged
                flag: --inputs %s...
        tensor_output: (a boolean or a file name)
                Averaged tensor volume
                flag: --tensor_output %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        verbose: (a boolean)
                produce verbose output
                flag: --verbose

Outputs::

        tensor_output: (an existing file name)
                Averaged tensor volume

.. _nipype.interfaces.semtools.diffusion.diffusion.dtiestim:


.. index:: dtiestim

dtiestim
--------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/diffusion.py#L81>`__

Wraps command ** dtiestim **

title: DTIEstim (DTIProcess)

category: Diffusion.Diffusion Weighted Images

description: dtiestim is a tool that takes in a set of DWIs (with --dwi_image option) in nrrd format and estimates a tensor field out of it. The output tensor file name is specified with the --tensor_output option
There are several methods to estimate the tensors which you can specify with the option --method lls|wls|nls|ml . Here is a short description of the different methods:

lls
      Linear least squares. Standard estimation technique that recovers the tensor parameters by multiplying the log of the normalized signal intensities by the pseudo-inverse of the gradient matrix. Default option.

wls
    Weighted least squares. This method is similar to the linear least squares method except that the gradient matrix is weighted by the original lls estimate. (See Salvador, R., Pena, A., Menon, D. K., Carpenter, T. A., Pickard, J. D., and Bullmore, E. T. Formal characterization and extension of the linearized diffusion tensor model. Human Brain Mapping 24, 2 (Feb. 2005), 144-155. for more information on this method). This method is recommended for most applications. The weight for each iteration can be specified with the --weight_iterations.  It is not currently the default due to occasional matrix singularities.
nls
    Non-linear least squares. This method does not take the log of the signal and requires an optimization based on levenberg-marquadt to optimize the parameters of the signal. The lls estimate is used as an initialization. For this method the step size can be specified with the --step option.
ml
    Maximum likelihood estimation. This method is experimental and is not currently recommended. For this ml method the sigma can be specified with the option --sigma and the step size can be specified with the --step option.

You can set a threshold (--threshold) to have the tensor estimated to only a subset of voxels. All the baseline voxel value higher than the threshold define the voxels where the tensors are computed. If not specified the threshold is calculated using an OTSU threshold on the baseline image.The masked generated by the -t option or by the otsu value can be saved with the --B0_mask_output option.

dtiestim also can extract a few scalar images out of the DWI set of images:

        - the average baseline image (--B0) which is the average of all the B0s.
        - the IDWI (--idwi)which is the geometric mean of the diffusion images.

You can also load a mask if you want to compute the tensors only where the voxels are non-zero (--brain_mask) or a negative mask and the tensors will be estimated where the negative mask has zero values (--bad_region_mask)

version: 1.2.0

documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/DTIProcess

license: Copyright (c)  Casey Goodlett. All rights reserved.
  See http://www.ia.unc.edu/dev/Copyright.htm for details.
     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notices for more information.

contributor: Casey Goodlett, Francois Budin

acknowledgements: Hans Johnson(1,3,4); Kent Williams(1); (1=University of Iowa Department of Psychiatry, 3=University of Iowa Department of Biomedical Engineering, 4=University of Iowa Department of Electrical and Computer Engineering) provided conversions to make DTIProcess compatible with Slicer execution, and simplified the stand-alone build requirements by removing the dependancies on boost and a fortran compiler.

Inputs::

        [Mandatory]

        [Optional]
        B0: (a boolean or a file name)
                Baseline image, average of all baseline images
                flag: --B0 %s
        B0_mask_output: (a boolean or a file name)
                B0 mask used for the estimation. B0 thresholded either with the -t
                option value or the automatic OTSU value
                flag: --B0_mask_output %s
        DTI_double: (a boolean)
                Tensor components are saved as doubles (cannot be visualized in
                Slicer)
                flag: --DTI_double
        args: (a string)
                Additional parameters to the command
                flag: %s
        bad_region_mask: (an existing file name)
                Bad region mask. Image where for every voxel > 0 the tensors are not
                estimated
                flag: --bad_region_mask %s
        brain_mask: (an existing file name)
                Brain mask. Image where for every voxel == 0 the tensors are not
                estimated. Be aware that in addition a threshold based masking will
                be performed by default. If such an additional threshold masking is
                NOT desired, then use option -t 0.
                flag: --brain_mask %s
        correction: ('none' or 'zero' or 'abs' or 'nearest')
                Correct the tensors if computed tensor is not semi-definite positive
                flag: --correction %s
        defaultTensor: (a list of items which are a float)
                Default tensor used if estimated tensor is below a given threshold
                flag: --defaultTensor %s
        dwi_image: (an existing file name)
                DWI image volume (required)
                flag: --dwi_image %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        idwi: (a boolean or a file name)
                idwi output image. Image with isotropic diffusion-weighted
                information = geometric mean of diffusion images
                flag: --idwi %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        method: ('lls' or 'wls' or 'nls' or 'ml')
                Esitmation method (lls:linear least squares, wls:weighted least
                squares, nls:non-linear least squares, ml:maximum likelihood)
                flag: --method %s
        shiftNeg: (a boolean)
                Shift eigenvalues so all are positive (accounts for bad tensors
                related to noise or acquisition error). This is the same option as
                the one available in DWIToDTIEstimation in Slicer (but instead of
                just adding the minimum eigenvalue to all the eigenvalues if it is
                smaller than 0, we use a coefficient to have stictly positive
                eigenvalues
                flag: --shiftNeg
        shiftNegCoeff: (a float)
                Shift eigenvalues so all are positive (accounts for bad tensors
                related to noise or acquisition error). Instead of just adding the
                minimum eigenvalue to all the eigenvalues if it is smaller than 0,
                we use a coefficient to have stictly positive eigenvalues.
                Coefficient must be between 1.0 and 1.001 (included).
                flag: --shiftNegCoeff %f
        sigma: (a float)
                flag: --sigma %f
        step: (a float)
                Gradient descent step size (for nls and ml methods)
                flag: --step %f
        tensor_output: (a boolean or a file name)
                Tensor OutputImage
                flag: --tensor_output %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        threshold: (an integer (int or long))
                Baseline threshold for estimation. If not specified calculated using
                an OTSU threshold on the baseline image.
                flag: --threshold %d
        verbose: (a boolean)
                produce verbose output
                flag: --verbose
        weight_iterations: (an integer (int or long))
                Number of iterations to recaluate weightings from tensor estimate
                flag: --weight_iterations %d

Outputs::

        B0: (an existing file name)
                Baseline image, average of all baseline images
        B0_mask_output: (an existing file name)
                B0 mask used for the estimation. B0 thresholded either with the -t
                option value or the automatic OTSU value
        idwi: (an existing file name)
                idwi output image. Image with isotropic diffusion-weighted
                information = geometric mean of diffusion images
        tensor_output: (an existing file name)
                Tensor OutputImage

.. _nipype.interfaces.semtools.diffusion.diffusion.dtiprocess:


.. index:: dtiprocess

dtiprocess
----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/diffusion.py#L182>`__

Wraps command ** dtiprocess **

title: DTIProcess (DTIProcess)

category: Diffusion.Diffusion Tensor Images

description: dtiprocess is a tool that handles tensor fields. It takes as an input a tensor field in nrrd format.
It can generate diffusion scalar properties out of the tensor field such as : FA (--fa_output), Gradient FA image (--fa_gradient_output), color FA (--color_fa_output), MD (--md_output), Frobenius norm (--frobenius_norm_output), lbd1, lbd2, lbd3 (--lambda{1,2,3}_output), binary map of voxel where if any of the eigenvalue is negative, the voxel is set to 1 (--negative_eigenvector_output)

It also creates 4D images out of the tensor field such as: Highest eigenvector map (highest eigenvector at each voxel) (--principal_eigenvector_output)

Masking capabilities: For any of the processing done with dtiprocess, it's possible to apply it on a masked region of the tensor field. You need to use the --mask option for any of the option to be applied on that tensor field sub-region only. If you want to save the masked tensor field use the option --outmask and specify the new masked tensor field file name.
dtiprocess also allows a range of transformations on the tensor fields. The transformed tensor field file name is specified with the option --deformation_output. There are 3 resampling interpolation methods specified with the tag --interpolation followed by the type to use (nearestneighbor, linear, cubic) Then you have several transformations possible to apply:

        - Affine transformations using as an input
        - itk affine transformation file (based on the itkAffineTransform class)
        - Affine transformations using rview (details and download at http://www.doc.ic.ac.uk/~dr/software/). There are 2 versions of rview both creating transformation files called dof files. The old version of rview outputs text files containing the transformation parameters. It can be read in with the --dof_file option. The new version outputs binary dof files. These dof files can be transformed into human readable file with the dof2mat tool which is part of the rview package. So you need to save the output of dof2mat into a text file which can then be used with the -- newdof_file option. Usage example: dof2mat mynewdoffile.dof >> mynewdoffile.txt       dtiprocess --dti_image mytensorfield.nhdr --newdof_file mynewdoffile.txt --rot_output myaffinetensorfield.nhdr

Non linear transformations as an input: The default transformation file type is d-field (displacement field) in nrrd format. The option to use is --forward with the name of the file. If the transformation file is a h-field you have to add the option --hField.

version: 1.0.1

documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/DTIProcess

license: Copyright (c)  Casey Goodlett. All rights reserved.
  See http://www.ia.unc.edu/dev/Copyright.htm for details.
     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notices for more information.

contributor: Casey Goodlett

Inputs::

        [Mandatory]

        [Optional]
        DTI_double: (a boolean)
                Tensor components are saved as doubles (cannot be visualized in
                Slicer)
                flag: --DTI_double
        RD_output: (a boolean or a file name)
                RD (Radial Diffusivity 1/2*(lambda2+lambda3)) output
                flag: --RD_output %s
        affineitk_file: (an existing file name)
                Transformation file for affine transformation. ITK format.
                flag: --affineitk_file %s
        args: (a string)
                Additional parameters to the command
                flag: %s
        color_fa_output: (a boolean or a file name)
                Color Fractional Anisotropy output file
                flag: --color_fa_output %s
        correction: ('none' or 'zero' or 'abs' or 'nearest')
                Correct the tensors if computed tensor is not semi-definite positive
                flag: --correction %s
        deformation_output: (a boolean or a file name)
                Warped tensor field based on a deformation field. This option
                requires the --forward,-F transformation to be specified.
                flag: --deformation_output %s
        dof_file: (an existing file name)
                Transformation file for affine transformation. This can be ITK
                format (or the outdated RView).
                flag: --dof_file %s
        dti_image: (an existing file name)
                DTI tensor volume
                flag: --dti_image %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        fa_gradient_output: (a boolean or a file name)
                Fractional Anisotropy Gradient output file
                flag: --fa_gradient_output %s
        fa_gradmag_output: (a boolean or a file name)
                Fractional Anisotropy Gradient Magnitude output file
                flag: --fa_gradmag_output %s
        fa_output: (a boolean or a file name)
                Fractional Anisotropy output file
                flag: --fa_output %s
        forward: (an existing file name)
                Forward transformation. Assumed to be a deformation field in world
                coordinates, unless the --h-field option is specified.
                flag: --forward %s
        frobenius_norm_output: (a boolean or a file name)
                Frobenius Norm Output
                flag: --frobenius_norm_output %s
        hField: (a boolean)
                forward and inverse transformations are h-fields instead of
                displacement fields
                flag: --hField
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        interpolation: ('nearestneighbor' or 'linear' or 'cubic')
                Interpolation type (nearestneighbor, linear, cubic)
                flag: --interpolation %s
        lambda1_output: (a boolean or a file name)
                Axial Diffusivity - Lambda 1 (largest eigenvalue) output
                flag: --lambda1_output %s
        lambda2_output: (a boolean or a file name)
                Lambda 2 (middle eigenvalue) output
                flag: --lambda2_output %s
        lambda3_output: (a boolean or a file name)
                Lambda 3 (smallest eigenvalue) output
                flag: --lambda3_output %s
        mask: (an existing file name)
                Mask tensors. Specify --outmask if you want to save the masked
                tensor field, otherwise the mask is applied just for the current
                processing
                flag: --mask %s
        md_output: (a boolean or a file name)
                Mean Diffusivity output file
                flag: --md_output %s
        negative_eigenvector_output: (a boolean or a file name)
                Negative Eigenvectors Output: create a binary image where if any of
                the eigen value is below zero, the voxel is set to 1, otherwise 0.
                flag: --negative_eigenvector_output %s
        newdof_file: (an existing file name)
                Transformation file for affine transformation. RView NEW format.
                (txt file output of dof2mat)
                flag: --newdof_file %s
        outmask: (a boolean or a file name)
                Name of the masked tensor field.
                flag: --outmask %s
        principal_eigenvector_output: (a boolean or a file name)
                Principal Eigenvectors Output
                flag: --principal_eigenvector_output %s
        reorientation: ('fs' or 'ppd')
                Reorientation type (fs, ppd)
                flag: --reorientation %s
        rot_output: (a boolean or a file name)
                Rotated tensor output file. Must also specify the dof file.
                flag: --rot_output %s
        scalar_float: (a boolean)
                Write scalar [FA,MD] as unscaled float (with their actual values,
                otherwise scaled by 10 000). Also causes FA to be unscaled [0..1].
                flag: --scalar_float
        sigma: (a float)
                Scale of gradients
                flag: --sigma %f
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        verbose: (a boolean)
                produce verbose output
                flag: --verbose

Outputs::

        RD_output: (an existing file name)
                RD (Radial Diffusivity 1/2*(lambda2+lambda3)) output
        color_fa_output: (an existing file name)
                Color Fractional Anisotropy output file
        deformation_output: (an existing file name)
                Warped tensor field based on a deformation field. This option
                requires the --forward,-F transformation to be specified.
        fa_gradient_output: (an existing file name)
                Fractional Anisotropy Gradient output file
        fa_gradmag_output: (an existing file name)
                Fractional Anisotropy Gradient Magnitude output file
        fa_output: (an existing file name)
                Fractional Anisotropy output file
        frobenius_norm_output: (an existing file name)
                Frobenius Norm Output
        lambda1_output: (an existing file name)
                Axial Diffusivity - Lambda 1 (largest eigenvalue) output
        lambda2_output: (an existing file name)
                Lambda 2 (middle eigenvalue) output
        lambda3_output: (an existing file name)
                Lambda 3 (smallest eigenvalue) output
        md_output: (an existing file name)
                Mean Diffusivity output file
        negative_eigenvector_output: (an existing file name)
                Negative Eigenvectors Output: create a binary image where if any of
                the eigen value is below zero, the voxel is set to 1, otherwise 0.
        outmask: (an existing file name)
                Name of the masked tensor field.
        principal_eigenvector_output: (an existing file name)
                Principal Eigenvectors Output
        rot_output: (an existing file name)
                Rotated tensor output file. Must also specify the dof file.
