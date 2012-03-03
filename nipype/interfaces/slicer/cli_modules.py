from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os


class AddInputSpec(CommandLineInputSpec):
    inputVolume1 = File(position="0", desc="Input volume 1", exists=True, argstr="--inputVolume1 %s")
    inputVolume2 = File(position="1", desc="Input volume 2", exists=True, argstr="--inputVolume2 %s")
    outputVolume = traits.Either(traits.Bool, File(), position="2", hash_files=False, desc="Volume1 + Volume2", argstr="--outputVolume %s")
    order = traits.Enum("0", "1", "2", "3", desc="Interpolation order if two images are in different coordinate frames or have different sampling.", argstr="--order %s")


class AddOutputSpec(TraitedSpec):
    outputVolume = File(position="2", desc="Volume1 + Volume2", exists=True)


class Add(CommandLine):
    """title: Add Images

category: Filtering.Arithmetic

description:
Adds two images. Although all image types are supported on input, only signed types are produced. The two images do not have to have the same dimensions.


version: 0.1.0.$Revision: 18864 $(alpha)

documentation-url: http://slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/Add

contributor: Bill Lorensen

acknowledgements:
This work is part of the National Alliance for Medical Image Computing (NAMIC), funded by the National Institutes of Health through the NIH Roadmap for Medical Research, Grant U54 EB005149.


"""

    input_spec = AddInputSpec
    output_spec = AddOutputSpec
    _cmd = " Add "
    _outputs_filenames = {'outputVolume':'outputVolume.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(Add, self)._format_arg(name, spec, value)



class AffineRegistrationInputSpec(CommandLineInputSpec):
    fixedsmoothingfactor = traits.Int(desc="Amount of smoothing applied to fixed image prior to registration. Default is 0 (none). Range is 0-5 (unitless). Consider smoothing the input data if there is considerable amounts of noise or the noise pattern in the fixed and moving images is very different.", argstr="--fixedsmoothingfactor %d")
    movingsmoothingfactor = traits.Int(desc="Amount of smoothing applied to moving image prior to registration. Default is 0 (none). Range is 0-5 (unitless). Consider smoothing the input data if there is considerable amounts of noise or the noise pattern in the fixed and moving images is very different.", argstr="--movingsmoothingfactor %d")
    histogrambins = traits.Int(desc="Number of histogram bins to use for Mattes Mutual Information. Reduce the number of bins if a registration fails. If the number of bins is too large, the estimated PDFs will be a field of impulses and will inhibit reliable registration estimation.", argstr="--histogrambins %d")
    spatialsamples = traits.Int(desc="Number of spatial samples to use in estimating Mattes Mutual Information. Larger values yield more accurate PDFs and improved registration quality.", argstr="--spatialsamples %d")
    iterations = traits.Int(desc="Number of iterations", argstr="--iterations %d")
    translationscale = traits.Float(desc="Relative scale of translations to rotations, i.e. a value of 100 means 10mm = 1 degree. (Actual scale used is 1/(TranslationScale^2)). This parameter is used to \"weight\" or \"standardized\" the transform parameters and their effect on the registration objective function.", argstr="--translationscale %f")
    initialtransform = File(desc="Initial transform for aligning the fixed and moving image.  Maps positions in the fixed coordinate frame to positions in the moving coordinate frame. Optional.", exists=True, argstr="--initialtransform %s")
    FixedImageFileName = File(position="0", desc="Fixed image to which to register", exists=True, argstr="--FixedImageFileName %s")
    MovingImageFileName = File(position="1", desc="Moving image", exists=True, argstr="--MovingImageFileName %s")
    outputtransform = traits.Either(traits.Bool, File(), hash_files=False, desc="Transform calculated that aligns the fixed and moving image. Maps positions in the fixed coordinate frame to the moving coordinate frame. Optional (specify an output transform or an output volume or both).", argstr="--outputtransform %s")
    resampledmovingfilename = traits.Either(traits.Bool, File(), hash_files=False, desc="Resampled moving image to the fixed image coordinate frame. Optional (specify an output transform or an output volume or both).", argstr="--resampledmovingfilename %s")


class AffineRegistrationOutputSpec(TraitedSpec):
    outputtransform = File(desc="Transform calculated that aligns the fixed and moving image. Maps positions in the fixed coordinate frame to the moving coordinate frame. Optional (specify an output transform or an output volume or both).", exists=True)
    resampledmovingfilename = File(desc="Resampled moving image to the fixed image coordinate frame. Optional (specify an output transform or an output volume or both).", exists=True)


class AffineRegistration(CommandLine):
    """title: Fast Affine registration

category: Legacy.Registration

description: Registers two images together using an affine transform and mutual information. This module is often used to align images of different subjects or images of the same subject from different modalities.

This module can smooth images prior to registration to mitigate noise and improve convergence. Many of the registration parameters require a working knowledge of the algorithm although the default parameters are sufficient for many registration tasks.



version: 0.1.0.$Revision: 18864 $(alpha)

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/AffineRegistration

contributor: Daniel Blezek

acknowledgements:
This module was developed by Daniel Blezek while at GE Research with contributions from Jim Miller.

This work is part of the National Alliance for Medical Image Computing (NAMIC), funded by the National Institutes of Health through the NIH Roadmap for Medical Research, Grant U54 EB005149.


"""

    input_spec = AffineRegistrationInputSpec
    output_spec = AffineRegistrationOutputSpec
    _cmd = " AffineRegistration "
    _outputs_filenames = {'resampledmovingfilename':'resampledmovingfilename.nii','outputtransform':'outputtransform.txt'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(AffineRegistration, self)._format_arg(name, spec, value)



class BSplineDeformableRegistrationInputSpec(CommandLineInputSpec):
    iterations = traits.Int(desc="Number of iterations", argstr="--iterations %d")
    gridSize = traits.Int(desc="Number of grid points on interior of the fixed image. Larger grid sizes allow for finer registrations.", argstr="--gridSize %d")
    histogrambins = traits.Int(desc="Number of histogram bins to use for Mattes Mutual Information. Reduce the number of bins if a deformable registration fails. If the number of bins is too large, the estimated PDFs will be a field of impulses and will inhibit reliable registration estimation.", argstr="--histogrambins %d")
    spatialsamples = traits.Int(desc="Number of spatial samples to use in estimating Mattes Mutual Information. Larger values yield more accurate PDFs and improved registration quality.", argstr="--spatialsamples %d")
    constrain = traits.Bool(desc="Constrain the deformation to the amount specified in Maximum Deformation", argstr="--constrain ")
    maximumDeformation = traits.Float(desc="If Constrain Deformation is checked, limit the deformation to this amount.", argstr="--maximumDeformation %f")
    default = traits.Int(desc="Default pixel value used if resampling a pixel outside of the volume.", argstr="--default %d")
    initialtransform = File(desc="Initial transform for aligning the fixed and moving image. Maps positions in the fixed coordinate frame to positions in the moving coordinate frame. This transform should be an affine or rigid transform.  It is used an a bulk transform for the BSpline. Optional.", exists=True, argstr="--initialtransform %s")
    FixedImageFileName = File(position="0", desc="Fixed image to which to register", exists=True, argstr="--FixedImageFileName %s")
    MovingImageFileName = File(position="1", desc="Moving image", exists=True, argstr="--MovingImageFileName %s")
    outputtransform = traits.Either(traits.Bool, File(), hash_files=False, desc="Transform calculated that aligns the fixed and moving image. Maps positions from the fixed coordinate frame to the moving coordinate frame. Optional (specify an output transform or an output volume or both).", argstr="--outputtransform %s")
    outputwarp = traits.Either(traits.Bool, File(), hash_files=False, desc="Vector field that applies an equivalent warp as the BSpline. Maps positions from the fixed coordinate frame to the moving coordinate frame. Optional.", argstr="--outputwarp %s")
    resampledmovingfilename = traits.Either(traits.Bool, File(), hash_files=False, desc="Resampled moving image to fixed image coordinate frame. Optional (specify an output transform or an output volume or both).", argstr="--resampledmovingfilename %s")


class BSplineDeformableRegistrationOutputSpec(TraitedSpec):
    outputtransform = File(desc="Transform calculated that aligns the fixed and moving image. Maps positions from the fixed coordinate frame to the moving coordinate frame. Optional (specify an output transform or an output volume or both).", exists=True)
    outputwarp = File(desc="Vector field that applies an equivalent warp as the BSpline. Maps positions from the fixed coordinate frame to the moving coordinate frame. Optional.", exists=True)
    resampledmovingfilename = File(desc="Resampled moving image to fixed image coordinate frame. Optional (specify an output transform or an output volume or both).", exists=True)


class BSplineDeformableRegistration(CommandLine):
    """title: Fast Nonrigid BSpline registration

category: Legacy.Registration

description: Registers two images together using BSpline transform and mutual information.

version: 0.1.0.$Revision: 18864 $(alpha)

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/BSplineDeformableRegistration

contributor: Bill Lorensen

acknowledgements:
This work is part of the National Alliance for Medical Image Computing (NAMIC), funded by the National Institutes of Health through the NIH Roadmap for Medical Research, Grant U54 EB005149.


"""

    input_spec = BSplineDeformableRegistrationInputSpec
    output_spec = BSplineDeformableRegistrationOutputSpec
    _cmd = " BSplineDeformableRegistration "
    _outputs_filenames = {'resampledmovingfilename':'resampledmovingfilename.nii','outputtransform':'outputtransform.txt','outputwarp':'outputwarp.nrrd'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(BSplineDeformableRegistration, self)._format_arg(name, spec, value)



class CastInputSpec(CommandLineInputSpec):
    InputVolume = File(position="0", desc="Input volume, the volume to cast.", exists=True, argstr="--InputVolume %s")
    OutputVolume = traits.Either(traits.Bool, File(), position="1", hash_files=False, desc="Output volume, cast to the new type.", argstr="--OutputVolume %s")
    type = traits.Enum("Char", "UnsignedChar", "Short", "UnsignedShort", "Int", "UnsignedInt", "Float", "Double", desc="Type for the new output volume.", argstr="--type %s")


class CastOutputSpec(TraitedSpec):
    OutputVolume = File(position="1", desc="Output volume, cast to the new type.", exists=True)


class Cast(CommandLine):
    """title: Cast Image

category: Filtering.Arithmetic

description:
Cast a volume to a given data type.
Use at your own risk when casting an input volume into a lower precision type!
Allows casting to the same type as the input volume.

version: 0.1.0.$Revision: 2104 $(alpha)

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/Cast

contributor: Nicole Aucoin, BWH (Ron Kikinis, BWH)

acknowledgements:
This work is part of the National Alliance for Medical Image Computing (NAMIC), funded by the National Institutes of Health through the NIH Roadmap for Medical Research, Grant U54 EB005149.


"""

    input_spec = CastInputSpec
    output_spec = CastOutputSpec
    _cmd = " Cast "
    _outputs_filenames = {'OutputVolume':'OutputVolume.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(Cast, self)._format_arg(name, spec, value)



class CheckerBoardInputSpec(CommandLineInputSpec):
    checkerPattern = InputMultiPath(traits.Int, desc="The pattern of input 1 and input 2 in the output image. The user can specify the number of checkers in each dimension. A checkerPattern of 2,2,1 means that images will alternate in every other checker in the first two dimensions. The same pattern will be used in the 3rd dimension.", sep=",", argstr="--checkerPattern %s")
    inputVolume1 = File(position="0", desc="First Input volume", exists=True, argstr="--inputVolume1 %s")
    inputVolume2 = File(position="1", desc="Second Input volume", exists=True, argstr="--inputVolume2 %s")
    outputVolume = traits.Either(traits.Bool, File(), position="2", hash_files=False, desc="Output filtered", argstr="--outputVolume %s")


class CheckerBoardOutputSpec(TraitedSpec):
    outputVolume = File(position="2", desc="Output filtered", exists=True)


class CheckerBoard(CommandLine):
    """title:
  CheckerBoard Filter


category:
  Filtering


description:
Create a checkerboard volume of two volumes. The output volume will show the two inputs alternating according to the user supplied checkerPattern. This filter is often used to compare the results of image registration. Note that the second input is resampled to the same origin, spacing and direction before it is composed with the first input. The scalar type of the output volume will be the same as the input image scalar type.


version: 0.1.0.$Revision: 18864 $(alpha)

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/CheckerBoard

contributor: Bill Lorensen

acknowledgements:
This work is part of the National Alliance for Medical Image Computing (NAMIC), funded by the National Institutes of Health through the NIH Roadmap for Medical Research, Grant U54 EB005149.


"""

    input_spec = CheckerBoardInputSpec
    output_spec = CheckerBoardOutputSpec
    _cmd = " CheckerBoard "
    _outputs_filenames = {'outputVolume':'outputVolume.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(CheckerBoard, self)._format_arg(name, spec, value)



class ComputeSUVBodyWeightInputSpec(CommandLineInputSpec):
    petDICOMPath = Directory(desc="Input path to a directory containing a PET volume containing DICOM header information for SUV computation", exists=True, argstr="--petDICOMPath %s")
    petVolume = File(desc="Input PET volume for SUVbw computation (must be the same volume as pointed to by the DICOM path!).", exists=True, argstr="--petVolume %s")
    labelMap = File(desc="Input label volume containing the volumes of interest", exists=True, argstr="--labelMap %s")
    color = File(desc="Color table to to map labels to colors and names", exists=True, argstr="--color %s")
    csvFile = traits.Either(traits.Bool, File(), hash_files=False, desc="A file holding the output SUV values in comma separated lines, one per label. Optional.", argstr="--csvFile %s")
    OutputLabel = traits.Str(desc="List of labels for which SUV values were computed", argstr="--OutputLabel %s")
    OutputLabelValue = traits.Str(desc="List of label values for which SUV values were computed", argstr="--OutputLabelValue %s")
    SUVMax = traits.Str(desc="SUV max for each label", argstr="--SUVMax %s")
    SUVMean = traits.Str(desc="SUV mean for each label", argstr="--SUVMean %s")
    SUVMin = traits.Str(desc="SUV minimum for each label", argstr="--SUVMin %s")


class ComputeSUVBodyWeightOutputSpec(TraitedSpec):
    csvFile = File(desc="A file holding the output SUV values in comma separated lines, one per label. Optional.", exists=True)


class ComputeSUVBodyWeight(CommandLine):
    """title: SUVComputation

category: Quantification

description:
Computes the standardized uptake value based on body weight. Takes an input PET image in DICOM and NRRD format (DICOM header must contain Radiopharmaceutical parameters). Produces a CSV file that contains patientID, studyDate, dose, labelID, suvmin, suvmax, suvmean, labelName for each volume of interest. It also displays some of the information as output strings in the GUI, the CSV file is optional in that case. The CSV file is appended to on each execution of the CLI.

version: 0.1.0.$Revision: 8595 $(alpha)

documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/ComputeSUVBodyWeight

contributor: Wendy Plesniak, BWH (Nicole Aucoin, BWH, Ron Kikinis, BWH)

acknowledgements:
This work is funded by the Harvard Catalyst, and the National Alliance for Medical Image Computing (NAMIC), funded by the National Institutes of Health through the NIH Roadmap for Medical Research, Grant U54 EB005149.


"""

    input_spec = ComputeSUVBodyWeightInputSpec
    output_spec = ComputeSUVBodyWeightOutputSpec
    _cmd = " ComputeSUVBodyWeight "
    _outputs_filenames = {'csvFile':'csvFile.csv'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(ComputeSUVBodyWeight, self)._format_arg(name, spec, value)



class ConfidenceConnectedInputSpec(CommandLineInputSpec):
    smoothingIterations = traits.Int(desc="Number of smoothing iterations", argstr="--smoothingIterations %d")
    timestep = traits.Float(desc="Timestep for curvature flow", argstr="--timestep %f")
    iterations = traits.Int(desc="Number of iterations of region growing", argstr="--iterations %d")
    multiplier = traits.Float(desc="Number of standard deviations to include in intensity model", argstr="--multiplier %f")
    neighborhood = traits.Int(desc="The radius of the neighborhood over which to calculate intensity model", argstr="--neighborhood %d")
    labelvalue = traits.Int(desc="The integer value (0-255) to use for the segmentation results. This will determine the color of the segmentation that will be generated by the Region growing algorithm", argstr="--labelvalue %d")
    seed = InputMultiPath(traits.List(traits.Float(), minlen=3, maxlen=3), desc="Seed point(s) for region growing", argstr="--seed %s...")
    inputVolume = File(position="0", desc="Input volume to be filtered", exists=True, argstr="--inputVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), position="1", hash_files=False, desc="Output filtered", argstr="--outputVolume %s")


class ConfidenceConnectedOutputSpec(TraitedSpec):
    outputVolume = File(position="1", desc="Output filtered", exists=True)


class ConfidenceConnected(CommandLine):
    """title:
  Simple region growing


category:
  Segmentation


description:
  A simple region growing segmentation algorithm based on intensity statistics. To create a list of fiducials (Seeds) for this algorithm, click on the tool bar icon of an arrow pointing to a starburst fiducial to enter the 'place a new object mode' and then use the fiducials module. This module uses the Slicer Command Line Interface (CLI) and the ITK filters CurvatureFlowImageFilter and ConfidenceConnectedImageFilter.


version: 0.1.0.$Revision: 18864 $(alpha)

documentation-url: http://www.slicer.org/slicerWiki/index.php/Modules:Simple_Region_Growing-Documentation-3.6

contributor: Jim Miller

acknowledgements: This command module was derived from Insight/Examples (copyright) Insight Software Consortium

"""

    input_spec = ConfidenceConnectedInputSpec
    output_spec = ConfidenceConnectedOutputSpec
    _cmd = " ConfidenceConnected "
    _outputs_filenames = {'outputVolume':'outputVolume.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(ConfidenceConnected, self)._format_arg(name, spec, value)



class CurvatureAnisotropicDiffusionInputSpec(CommandLineInputSpec):
    conductance = traits.Float(desc="Conductance controls the sensitivity of the conductance term. As a general rule, the lower the value, the more strongly the filter preserves edges. A high value will cause diffusion (smoothing) across edges. Note that the number of iterations controls how much smoothing is done within regions bounded by edges.", argstr="--conductance %f")
    iterations = traits.Int(desc="The more iterations, the more smoothing. Each iteration takes the same amount of time. If it takes 10 seconds for one iteration, then it will take 100 seconds for 10 iterations. Note that the conductance controls how much each iteration smooths across edges.", argstr="--iterations %d")
    timeStep = traits.Float(desc="The time step depends on the dimensionality of the image. In Slicer the images are 3D and the default (.0625) time step will provide a stable solution.", argstr="--timeStep %f")
    inputVolume = File(position="0", desc="Input volume to be filtered", exists=True, argstr="--inputVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), position="1", hash_files=False, desc="Output filtered", argstr="--outputVolume %s")


class CurvatureAnisotropicDiffusionOutputSpec(TraitedSpec):
    outputVolume = File(position="1", desc="Output filtered", exists=True)


class CurvatureAnisotropicDiffusion(CommandLine):
    """title: Curvature Anisotropic Diffusion

category: Filtering.Denoising

description:
Performs anisotropic diffusion on an image using a modified curvature diffusion equation (MCDE).

MCDE does not exhibit the edge enhancing properties of classic anisotropic diffusion, which can under certain conditions undergo a 'negative' diffusion, which enhances the contrast of edges.  Equations of the form of MCDE always undergo positive diffusion, with the conductance term only varying the strength of that diffusion.

 Qualitatively, MCDE compares well with other non-linear diffusion techniques.  It is less sensitive to contrast than classic Perona-Malik style diffusion, and preserves finer detailed structures in images.  There is a potential speed trade-off for using this function in place of Gradient Anisotropic Diffusion.  Each iteration of the solution takes roughly twice as long.  Fewer iterations, however, may be required to reach an acceptable solution.


version: 0.1.0.$Revision: 18864 $(alpha)

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/CurvatureAnisotropicDiffusion

contributor: Bill Lorensen

acknowledgements: This command module was derived from Insight/Examples (copyright) Insight Software Consortium

"""

    input_spec = CurvatureAnisotropicDiffusionInputSpec
    output_spec = CurvatureAnisotropicDiffusionOutputSpec
    _cmd = " CurvatureAnisotropicDiffusion "
    _outputs_filenames = {'outputVolume':'outputVolume.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(CurvatureAnisotropicDiffusion, self)._format_arg(name, spec, value)



class DicomToNrrdConverterInputSpec(CommandLineInputSpec):
    inputDicomDirectory = Directory(desc="Directory holding Dicom series", exists=True, argstr="--inputDicomDirectory %s")
    outputDirectory = traits.Either(traits.Bool, Directory(), hash_files=False, desc="Directory holding the output NRRD format", argstr="--outputDirectory %s")
    outputVolume = traits.Str(desc="Output filename (.nhdr or .nrrd)", argstr="--outputVolume %s")
    smallGradientThreshold = traits.Float(desc="If a gradient magnitude is greater than 0 and less than smallGradientThreshold, then DicomToNrrdConverter will display an error message and quit, unless the useBMatrixGradientDirections option is set.", argstr="--smallGradientThreshold %f")
    writeProtocolGradientsFile = traits.Bool(desc=" Write the protocol gradients to a file suffixed by \".txt\" as they were specified in the procol by multiplying each diffusion gradient direction by the measurement frame.  This file is for debugging purposes only, the format is not fixed, and will likely change as debugging of new dicom formats is necessary. ", argstr="--writeProtocolGradientsFile ")
    useIdentityMeaseurementFrame = traits.Bool(desc="Adjust all the gradients so that the measurement frame is an identity matrix.", argstr="--useIdentityMeaseurementFrame ")
    useBMatrixGradientDirections = traits.Bool(desc="Fill the nhdr header with the gradient directions and bvalues computed out of the BMatrix. Only changes behavior for Siemens data.", argstr="--useBMatrixGradientDirections ")


class DicomToNrrdConverterOutputSpec(TraitedSpec):
    outputDirectory = Directory(desc="Directory holding the output NRRD format", exists=True)


class DicomToNrrdConverter(CommandLine):
    """title:
  Dicom to Nrrd Converter


category:
  Converters


description:
Converts diffusion weighted MR images in dicom series into Nrrd format for analysis in Slicer. This program has been tested on only a limited subset of DTI dicom formats available from Siemens, GE, and Phillips scanners. Work in progress to support dicom multi-frame data. The program parses dicom header to extract necessary information about measurement frame, diffusion weighting directions, b-values, etc, and write out a nrrd image. For non-diffusion weighted dicom images, it loads in an entire dicom series and writes out a single dicom volume in a .nhdr/.raw pair.


version: 0.2.0.$Revision: 916 $(alpha)

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/DicomToNrrdConverter

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Xiaodong Tao

acknowledgements:
This work is part of the National Alliance for Medical Image Computing (NAMIC), funded by the National Institutes of Health through the NIH Roadmap for Medical Research, Grant U54 EB005149.  Additional support for DTI data produced on Philips scanners was contributed by Vincent Magnotta and Hans Johnson at the University of Iowa.


"""

    input_spec = DicomToNrrdConverterInputSpec
    output_spec = DicomToNrrdConverterOutputSpec
    _cmd = " DicomToNrrdConverter "
    _outputs_filenames = {'outputDirectory':'outputDirectory'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(DicomToNrrdConverter, self)._format_arg(name, spec, value)



class ResampleDTIInputSpec(CommandLineInputSpec):
    inputVolume = File(position="0", desc="Input volume to be resampled", exists=True, argstr="--inputVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), position="1", hash_files=False, desc="Resampled Volume", argstr="--outputVolume %s")
    Reference = File(desc="Reference Volume (spacing,size,orientation,origin)", exists=True, argstr="--Reference %s")
    transformationFile = File(exists=True, argstr="--transformationFile %s")
    defField = File(desc="File containing the deformation field (3D vector image containing vectors with 3 components)", exists=True, argstr="--defField %s")
    hfieldtype = traits.Enum("displacement", "h-Field", desc="Set if the deformation field is an -Field", argstr="--hfieldtype %s")
    interpolation = traits.Enum("linear", "nn", "ws", "bs", desc="Sampling algorithm (linear , nn (nearest neighborhoor), ws (WindowedSinc), bs (BSpline) )", argstr="--interpolation %s")
    correction = traits.Enum("zero", "none", "abs", "nearest", desc="Correct the tensors if computed tensor is not semi-definite positive", argstr="--correction %s")
    transform_tensor_method = traits.Enum("PPD", "FS", desc="Chooses between 2 methods to transform the tensors: Finite Strain (FS), faster but less accurate, or Preservation of the Principal Direction (PPD)", argstr="--transform_tensor_method %s")
    transform_order = traits.Enum("input-to-output", "output-to-input", desc="Select in what order the transforms are read", argstr="--transform_order %s")
    notbulk = traits.Bool(desc="The transform following the BSpline transform is not set as a bulk transform for the BSpline transform", argstr="--notbulk ")
    spaceChange = traits.Bool(desc="Space Orientation between transform and image is different (RAS/LPS) (warning: if the transform is a Transform Node in Slicer3, do not select)", argstr="--spaceChange ")
    rotation_point = traits.List(desc="Center of rotation (only for rigid and affine transforms)", argstr="--rotation_point %s")
    centered_transform = traits.Bool(desc="Set the center of the transformation to the center of the input image (only for rigid and affine transforms)", argstr="--centered_transform ")
    image_center = traits.Enum("input", "output", desc="Image to use to center the transform (used only if \"Centered Transform\" is selected)", argstr="--image_center %s")
    Inverse_ITK_Transformation = traits.Bool(desc="Inverse the transformation before applying it from output image to input image (only for rigid and affine transforms)", argstr="--Inverse_ITK_Transformation ")
    spacing = InputMultiPath(traits.Float, desc="Spacing along each dimension (0 means use input spacing)", sep=",", argstr="--spacing %s")
    size = InputMultiPath(traits.Float, desc="Size along each dimension (0 means use input size)", sep=",", argstr="--size %s")
    origin = traits.List(desc="Origin of the output Image", argstr="--origin %s")
    direction_matrix = InputMultiPath(traits.Float, desc="9 parameters of the direction matrix by rows (ijk to LPS if LPS transform, ijk to RAS if RAS transform)", sep=",", argstr="--direction_matrix %s")
    number_of_thread = traits.Int(desc="Number of thread used to compute the output image", argstr="--number_of_thread %d")
    default_pixel_value = traits.Float(desc="Default pixel value for samples falling outside of the input region", argstr="--default_pixel_value %f")
    window_function = traits.Enum("h", "c", "w", "l", "b", desc="Window Function , h = Hamming , c = Cosine , w = Welch , l = Lanczos , b = Blackman", argstr="--window_function %s")
    spline_order = traits.Int(desc="Spline Order (Spline order may be from 0 to 5)", argstr="--spline_order %d")
    transform_matrix = InputMultiPath(traits.Float, desc="12 parameters of the transform matrix by rows ( --last 3 being translation-- )", sep=",", argstr="--transform_matrix %s")
    transform = traits.Enum("rt", "a", desc="Transform algorithm, rt = Rigid Transform, a = Affine Transform", argstr="--transform %s")


class ResampleDTIOutputSpec(TraitedSpec):
    outputVolume = File(position="1", desc="Resampled Volume", exists=True)


class ResampleDTI(CommandLine):
    """title: Resample DTI Volume

category: Diffusion.Utilities

description:
Resampling an image is a very important task in image analysis. It is especially important in the frame of image registration. This module implements DT image resampling through the use of itk Transforms. The resampling is controlled by the Output Spacing. "Resampling" is performed in space coordinates, not pixel/grid coordinates. It is quite important to ensure that image spacing is properly set on the images involved. The interpolator is required since the mapping from one space to the other will often require evaluation of the intensity of the image at non-grid positions.


version: 0.1

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/ResampleDTI

contributor: Francois Budin

acknowledgements:
This work is part of the National Alliance for Medical Image Computing (NAMIC), funded by the National Institutes of Health through the NIH Roadmap for Medical Research, Grant U54 EB005149. Information on the National Centers for Biomedical Computing can be obtained from http://nihroadmap.nih.gov/bioinformatics


"""

    input_spec = ResampleDTIInputSpec
    output_spec = ResampleDTIOutputSpec
    _cmd = " ResampleDTI "
    _outputs_filenames = {'outputVolume':'outputVolume.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(ResampleDTI, self)._format_arg(name, spec, value)



class dwiNoiseFilterInputSpec(CommandLineInputSpec):
    iter = traits.Int(desc="Number of iterations for the noise removal filter.", argstr="--iter %d")
    re = InputMultiPath(traits.Int, desc="Estimation radius.", sep=",", argstr="--re %s")
    rf = InputMultiPath(traits.Int, desc="Filtering radius.", sep=",", argstr="--rf %s")
    mnvf = traits.Int(desc="Minimum number of voxels in kernel used for filtering.", argstr="--mnvf %d")
    mnve = traits.Int(desc="Minimum number of voxels in kernel used for estimation.", argstr="--mnve %d")
    minnstd = traits.Int(desc="Minimum allowed noise standard deviation.", argstr="--minnstd %d")
    maxnstd = traits.Int(desc="Maximum allowed noise standard deviation.", argstr="--maxnstd %d")
    hrf = traits.Float(desc="How many histogram bins per unit interval.", argstr="--hrf %f")
    uav = traits.Bool(desc="Use absolute value in case of negative square.", argstr="--uav ")
    inputVolume = File(position="0", desc="Input DWI volume.", exists=True, argstr="--inputVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), position="1", hash_files=False, desc="Output DWI volume.", argstr="--outputVolume %s")


class dwiNoiseFilterOutputSpec(TraitedSpec):
    outputVolume = File(position="1", desc="Output DWI volume.", exists=True)


class dwiNoiseFilter(CommandLine):
    """title: Rician LMMSE Image Filter

category: Diffusion.Denoising

description:
This module reduces noise (or unwanted detail) on a set of diffusion weighted images. For this, it filters the image in the mean squared error sense using a Rician noise model. Images corresponding to each gradient direction, including baseline, are processed individually. The noise parameter is automatically estimated (noise estimation improved but slower).
Note that this is a general purpose filter for MRi images. The module jointLMMSE has been specifically designed for DWI volumes and shows a better performance, so its use is recommended instead.
A complete description of the algorithm in this module can be found in:
S. Aja-Fernandez, M. Niethammer, M. Kubicki, M. Shenton, and C.-F. Westin. Restoration of DWI data using a Rician LMMSE estimator. IEEE Transactions on Medical Imaging, 27(10): pp. 1389-1403, Oct. 2008.


version: 0.1.1.$Revision: 1 $(alpha)

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/RicianLMMSEImageFilter

contributor: Antonio Tristan Vega, Santiago Aja Fernandez and Marc Niethammer. Partially founded by grant number TEC2007-67073/TCM from the Comision Interministerial de Ciencia y Tecnologia (Spain).

"""

    input_spec = dwiNoiseFilterInputSpec
    output_spec = dwiNoiseFilterOutputSpec
    _cmd = " dwiNoiseFilter "
    _outputs_filenames = {'outputVolume':'outputVolume.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(dwiNoiseFilter, self)._format_arg(name, spec, value)



class dwiUNLMInputSpec(CommandLineInputSpec):
    rs = InputMultiPath(traits.Int, desc="The algorithm search for similar voxels in a neighborhood of this size (larger sizes than the default one are extremely slow).", sep=",", argstr="--rs %s")
    rc = InputMultiPath(traits.Int, desc="Similarity between blocks is measured using windows of this size.", sep=",", argstr="--rc %s")
    hp = traits.Float(desc="This parameter is related to noise; the larger the parameter, the more agressive the filtering. Should be near 1, and only values between 0.8 and 1.2 are allowed", argstr="--hp %f")
    ng = traits.Int(desc="The number of the closest gradients that are used to jointly filter a given gradient direction (a maximum of 5 is allowed).", argstr="--ng %d")
    re = InputMultiPath(traits.Int, desc="A neighborhood of this size is used to compute the statistics for noise estimation.", sep=",", argstr="--re %s")
    inputVolume = File(position="0", desc="Input DWI volume.", exists=True, argstr="--inputVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), position="1", hash_files=False, desc="Output DWI volume.", argstr="--outputVolume %s")


class dwiUNLMOutputSpec(TraitedSpec):
    outputVolume = File(position="1", desc="Output DWI volume.", exists=True)


class dwiUNLM(CommandLine):
    """title: Unbiased Non Local Means filter for DWI

category: Legacy.Diffusion.Denoising

description:
This module reduces noise (or unwanted detail) on a set of diffusion weighted images. For this, it filters the images using a Unbiased Non Local Means for Rician noise algorithm. It exploits not only the spatial redundancy, but the redundancy in similar gradient directions as well; it takes into account the N closest gradient directions to the direction being processed (a maximum of 5 gradient directions is allowed to keep a reasonable computational load, since we do not use neither similarity maps nor block-wise implementation).
The noise parameter is automatically estimated in the same way as in the jointLMMSE module.
A complete description of the algorithm may be found in:
Antonio Tristan-Vega and Santiago Aja-Fernandez, DWI filtering using joint information for DTI and HARDI, Medical Image Analysis, Volume 14, Issue 2, Pages 205-218. 2010.
Please, note that the execution of this filter is extremely slow, son only very conservative parameters (block size and search size as small as possible) should be used. Even so, its execution may take several hours. The advantage of this filter over joint LMMSE is its better preservation of edges and fine structures.


version: 0.0.1.$Revision: 1 $(alpha)

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/UnbiasedNonLocalMeansFilterForDWI

contributor: Antonio Tristan Vega, Santiago Aja Fernandez. University of Valladolid (SPAIN). Partially founded by grant number TEC2007-67073/TCM from the Comision Interministerial de Ciencia y Tecnologia (Spain).


"""

    input_spec = dwiUNLMInputSpec
    output_spec = dwiUNLMOutputSpec
    _cmd = " dwiUNLM "
    _outputs_filenames = {'outputVolume':'outputVolume.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(dwiUNLM, self)._format_arg(name, spec, value)



class jointLMMSEInputSpec(CommandLineInputSpec):
    re = InputMultiPath(traits.Int, desc="Estimation radius.", sep=",", argstr="--re %s")
    rf = InputMultiPath(traits.Int, desc="Filtering radius.", sep=",", argstr="--rf %s")
    ng = traits.Int(desc="The number of the closest gradients that are used to jointly filter a given gradient direction (0 to use all).", argstr="--ng %d")
    inputVolume = File(position="0", desc="Input DWI volume.", exists=True, argstr="--inputVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), position="1", hash_files=False, desc="Output DWI volume.", argstr="--outputVolume %s")


class jointLMMSEOutputSpec(TraitedSpec):
    outputVolume = File(position="1", desc="Output DWI volume.", exists=True)


class jointLMMSE(CommandLine):
    """title: Joint Rician LMMSE Image Filter

category: Diffusion.Denoising

description:
This module reduces Rician noise (or unwanted detail) on a set of diffusion weighted images. For this, it filters the image in the mean squared error sense using a Rician noise model. The N closest gradient directions to the direction being processed are filtered together to improve the results: the noise-free signal is seen as an n-diemensional vector which has to be estimated with the LMMSE method from a set of corrupted measurements. To that end, the covariance matrix of the noise-free vector and the cross covariance between this signal and the noise have to be estimated, which is done taking into account the image formation process.
The noise parameter is automatically estimated from a rough segmentation of the background of the image. In this area the signal is simply 0, so that Rician statistics reduce to Rayleigh and the noise power can be easily estimated from the mode of the histogram.
A complete description of the algorithm may be found in:
Antonio Tristan-Vega and Santiago Aja-Fernandez, DWI filtering using joint information for DTI and HARDI, Medical Image Analysis, Volume 14, Issue 2, Pages 205-218. 2010.


version: 0.1.1.$Revision: 1 $(alpha)

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/JointRicianLMMSEImageFilter

contributor: Antonio Tristan Vega, Santiago Aja Fernandez. University of Valladolid (SPAIN). Partially founded by grant number TEC2007-67073/TCM from the Comision Interministerial de Ciencia y Tecnologia (Spain).


"""

    input_spec = jointLMMSEInputSpec
    output_spec = jointLMMSEOutputSpec
    _cmd = " jointLMMSE "
    _outputs_filenames = {'outputVolume':'outputVolume.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(jointLMMSE, self)._format_arg(name, spec, value)



class DiffusionTensorEstimationInputSpec(CommandLineInputSpec):
    inputVolume = File(position="0", desc="Input DWI volume", exists=True, argstr="--inputVolume %s")
    mask = File(desc="Mask where the tensors will be computed", exists=True, argstr="--mask %s")
    outputTensor = traits.Either(traits.Bool, File(), position="1", hash_files=False, desc="Estimated DTI volume", argstr="--outputTensor %s")
    outputBaseline = traits.Either(traits.Bool, File(), position="2", hash_files=False, desc="Estimated baseline volume", argstr="--outputBaseline %s")
    enumeration = traits.Enum("LS", "WLS", desc="LS: Least Squares, WLS: Weighted Least Squares", argstr="--enumeration %s")
    shiftNeg = traits.Bool(desc="Shift eigenvalues so all are positive (accounts for bad tensors related to noise or acquisition error)", argstr="--shiftNeg ")


class DiffusionTensorEstimationOutputSpec(TraitedSpec):
    outputTensor = File(position="1", desc="Estimated DTI volume", exists=True)
    outputBaseline = File(position="2", desc="Estimated baseline volume", exists=True)


class DiffusionTensorEstimation(CommandLine):
    """title:
  Diffusion Tensor Estimation


category:
  Diffusion.Utilities


description:
  Performs a tensor model estimation from diffusion weighted images.

There are three estimation methods available: least squares, weigthed least squares and non-linear estimation. The first method is the traditional method for tensor estimation and the fastest one. Weighted least squares takes into account the noise characteristics of the MRI images to weight the DWI samples used in the estimation based on its intensity magnitude. The last method is the more complex.


version: 0.1.0.$Revision: 1892 $(alpha)

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/DiffusionTensorEstimation

license: slicer3

contributor: Raul San Jose

acknowledgements: This command module is based on the estimation functionality provided by the Teem library. This work is part of the National Alliance for Medical Image Computing (NAMIC), funded by the National Institutes of Health through the NIH Roadmap for Medical Research, Grant U54 EB005149.

"""

    input_spec = DiffusionTensorEstimationInputSpec
    output_spec = DiffusionTensorEstimationOutputSpec
    _cmd = " DiffusionTensorEstimation "
    _outputs_filenames = {'outputTensor':'outputTensor.nii','outputBaseline':'outputBaseline.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(DiffusionTensorEstimation, self)._format_arg(name, spec, value)



class DiffusionTensorMathematicsInputSpec(CommandLineInputSpec):
    inputVolume = File(position="0", desc="Input DTI volume", exists=True, argstr="--inputVolume %s")
    outputScalar = traits.Either(traits.Bool, File(), position="2", hash_files=False, desc="Scalar volume derived from tensor", argstr="--outputScalar %s")
    enumeration = traits.Enum("Trace", "Determinant", "RelativeAnisotropy", "FractionalAnisotropy", "Mode", "LinearMeasure", "PlanarMeasure", "SphericalMeasure", "MinEigenvalue", "MidEigenvalue", "MaxEigenvalue", "MaxEigenvalueProjectionX", "MaxEigenvalueProjectionY", "MaxEigenvalueProjectionZ", "RAIMaxEigenvecX", "RAIMaxEigenvecY", "RAIMaxEigenvecZ", "D11", "D22", "D33", "ParallelDiffusivity", "PerpendicularDffusivity", desc="An enumeration of strings", argstr="--enumeration %s")


class DiffusionTensorMathematicsOutputSpec(TraitedSpec):
    outputScalar = File(position="2", desc="Scalar volume derived from tensor", exists=True)


class DiffusionTensorMathematics(CommandLine):
    """title:
  Diffusion Tensor Scalar Measurements


category:
  Diffusion.Utilities


description:
  Compute a set of different scalar measurements from a tensor field, specially oriented for Diffusion Tensors where some rotationally invariant measurements, like Fractional Anisotropy, are highly used to describe the anistropic behaviour of the tensor.


version: 0.1.0.$Revision: 1892 $(alpha)

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/DiffusionTensorMathematics

contributor: Raul San Jose

acknowledgements: LMI

"""

    input_spec = DiffusionTensorMathematicsInputSpec
    output_spec = DiffusionTensorMathematicsOutputSpec
    _cmd = " DiffusionTensorMathematics "
    _outputs_filenames = {'outputScalar':'outputScalar.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(DiffusionTensorMathematics, self)._format_arg(name, spec, value)



class DiffusionTensorTestInputSpec(CommandLineInputSpec):
    inputVolume = File(position="0", desc="Input tensor volume to be filtered", exists=True, argstr="--inputVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), position="1", hash_files=False, desc="Filtered tensor volume", argstr="--outputVolume %s")


class DiffusionTensorTestOutputSpec(TraitedSpec):
    outputVolume = File(position="1", desc="Filtered tensor volume", exists=True)


class DiffusionTensorTest(CommandLine):
    """title:
  Simple IO Test


category:
  Legacy.Work in Progress.Diffusion Tensor.Test


description:
  Simple test of tensor IO


version: 0.1.0.$Revision: 18864 $(alpha)

contributor: Bill Lorensen

"""

    input_spec = DiffusionTensorTestInputSpec
    output_spec = DiffusionTensorTestOutputSpec
    _cmd = " DiffusionTensorTest "
    _outputs_filenames = {'outputVolume':'outputVolume.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(DiffusionTensorTest, self)._format_arg(name, spec, value)



class DiffusionWeightedMaskingInputSpec(CommandLineInputSpec):
    inputVolume = File(position="0", desc="Input DWI volume", exists=True, argstr="--inputVolume %s")
    outputBaseline = traits.Either(traits.Bool, File(), position="2", hash_files=False, desc="Estimated baseline volume", argstr="--outputBaseline %s")
    thresholdMask = traits.Either(traits.Bool, File(), position="3", hash_files=False, desc="Otsu Threshold Mask", argstr="--thresholdMask %s")
    otsuomegathreshold = traits.Float(desc="Control the sharpness of the threshold in the Otsu computation. 0: lower threshold, 1: higher threhold", argstr="--otsuomegathreshold %f")
    removeislands = traits.Bool(desc="Remove Islands in Threshold Mask?", argstr="--removeislands ")


class DiffusionWeightedMaskingOutputSpec(TraitedSpec):
    outputBaseline = File(position="2", desc="Estimated baseline volume", exists=True)
    thresholdMask = File(position="3", desc="Otsu Threshold Mask", exists=True)


class DiffusionWeightedMasking(CommandLine):
    """title:
  Mask from Diffusion Weighted Images


category:
  Diffusion.Utilities


description: <p>Performs a mask calculation from a diffusion weighted (DW) image.</p><p>Starting from a dw image, this module computes the baseline image averaging all the images without diffusion weighting and then applies the otsu segmentation algorithm in order to produce a mask. this mask can then be used when estimating the diffusion tensor (dt) image, not to estimate tensors all over the volume.</p>

version: 0.1.0.$Revision: 1892 $(alpha)

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/DiffusionWeightedMasking

license: slicer3

contributor: Demian Wassermann

"""

    input_spec = DiffusionWeightedMaskingInputSpec
    output_spec = DiffusionWeightedMaskingOutputSpec
    _cmd = " DiffusionWeightedMasking "
    _outputs_filenames = {'outputBaseline':'outputBaseline.nii','thresholdMask':'thresholdMask.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(DiffusionWeightedMasking, self)._format_arg(name, spec, value)



class BRAINSFitInputSpec(CommandLineInputSpec):
    fixedVolume = File(desc="The fixed image for registration by mutual information optimization.", exists=True, argstr="--fixedVolume %s")
    movingVolume = File(desc="The moving image for registration by mutual information optimization.", exists=True, argstr="--movingVolume %s")
    bsplineTransform = traits.Either(traits.Bool, File(), hash_files=False, desc="(optional) Filename to which save the estimated transform. NOTE: You must set at least one output object (either a deformed image or a transform.  NOTE: USE THIS ONLY IF THE FINAL TRANSFORM IS BSpline", argstr="--bsplineTransform %s")
    linearTransform = traits.Either(traits.Bool, File(), hash_files=False, desc="(optional) Filename to which save the estimated transform. NOTE: You must set at least one output object (either a deformed image or a transform.  NOTE: USE THIS ONLY IF THE FINAL TRANSFORM IS ---NOT--- BSpline", argstr="--linearTransform %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="(optional) Output image for registration. NOTE: You must select either the outputTransform or the outputVolume option.", argstr="--outputVolume %s")
    initialTransform = File(desc="Filename of transform used to initialize the registration.  This CAN NOT be used with either CenterOfHeadLAlign, MomentsAlign, GeometryAlign, or initialTransform file.", exists=True, argstr="--initialTransform %s")
    initializeTransformMode = traits.Enum("Off", "useMomentsAlign", "useCenterOfHeadAlign", "useGeometryAlign", "useCenterOfROIAlign", desc="Determine how to initialize the transform center.  GeometryAlign on assumes that the center of the voxel lattice of the images represent similar structures.  MomentsAlign assumes that the center of mass of the images represent similar structures.  useCenterOfHeadAlign attempts to use the top of head and shape of neck to drive a center of mass estimate.  Off assumes that the physical space of the images are close, and that centering in terms of the image Origins is a good starting point.  This flag is mutually exclusive with the initialTransform flag.", argstr="--initializeTransformMode %s")
    useRigid = traits.Bool(desc="Perform a rigid registration as part of the sequential registration steps.  This family of options superceeds the use of transformType if any of them are set.", argstr="--useRigid ")
    useScaleVersor3D = traits.Bool(desc="Perform a ScaleVersor3D registration as part of the sequential registration steps.  This family of options superceeds the use of transformType if any of them are set.", argstr="--useScaleVersor3D ")
    useScaleSkewVersor3D = traits.Bool(desc="Perform a ScaleSkewVersor3D registration as part of the sequential registration steps.  This family of options superceeds the use of transformType if any of them are set.", argstr="--useScaleSkewVersor3D ")
    useAffine = traits.Bool(desc="Perform an Affine registration as part of the sequential registration steps.  This family of options superceeds the use of transformType if any of them are set.", argstr="--useAffine ")
    useBSpline = traits.Bool(desc="Perform a BSpline registration as part of the sequential registration steps.  This family of options superceeds the use of transformType if any of them are set.", argstr="--useBSpline ")
    useComposite = traits.Bool(desc="Perform a Composite registration as part of the sequential registration steps.  This family of options superceeds the use of transformType if any of them are set.", argstr="--useComposite ")
    numberOfSamples = traits.Int(desc="The number of voxels sampled for mutual information computation.  Increase this for a slower, more careful fit.  You can also limit the sampling focus with ROI masks and ROIAUTO mask generation.", argstr="--numberOfSamples %d")
    splineGridSize = InputMultiPath(traits.Int, desc="The number of subdivisions of the BSpline Grid to be centered on the image space.  Each dimension must have at least 3 subdivisions for the BSpline to be correctly computed. ", sep=",", argstr="--splineGridSize %s")
    numberOfIterations = InputMultiPath(traits.Int, desc="The maximum number of iterations to try before failing to converge.  Use an explicit limit like 500 or 1000 to manage risk of divergence", sep=",", argstr="--numberOfIterations %s")
    maskProcessingMode = traits.Enum("NOMASK", "ROIAUTO", "ROI", desc="What mode to use for using the masks.  If ROIAUTO is choosen, then the mask is implicitly defined using a otsu forground and hole filling algorithm. The Region Of Interest mode (choose ROI) uses the masks to define what parts of the image should be used for computing the transform.", argstr="--maskProcessingMode %s")
    fixedBinaryVolume = File(desc="Fixed Image binary mask volume, ONLY FOR MANUAL ROI mode.", exists=True, argstr="--fixedBinaryVolume %s")
    movingBinaryVolume = File(desc="Moving Image binary mask volume, ONLY FOR MANUAL ROI mode.", exists=True, argstr="--movingBinaryVolume %s")
    outputFixedVolumeROI = traits.Either(traits.Bool, File(), hash_files=False, desc="The ROI automatically found in fixed image, ONLY FOR ROIAUTO mode.", argstr="--outputFixedVolumeROI %s")
    outputMovingVolumeROI = traits.Either(traits.Bool, File(), hash_files=False, desc="The ROI automatically found in moving image, ONLY FOR ROIAUTO mode.", argstr="--outputMovingVolumeROI %s")
    outputVolumePixelType = traits.Enum("float", "short", "ushort", "int", "uint", "uchar", desc="The output image Pixel Type is the scalar datatype for representation of the Output Volume.", argstr="--outputVolumePixelType %s")
    backgroundFillValue = traits.Float(desc="Background fill value for output image.", argstr="--backgroundFillValue %f")
    maskInferiorCutOffFromCenter = traits.Float(desc="For use with --useCenterOfHeadAlign (and --maskProcessingMode ROIAUTO): the cut-off below the image centers, in millimeters, ", argstr="--maskInferiorCutOffFromCenter %f")
    scaleOutputValues = traits.Bool(desc="If true, and the voxel values do not fit within the minimum and maximum values of the desired outputVolumePixelType, then linearly scale the min/max output image voxel values to fit within the min/max range of the outputVolumePixelType.", argstr="--scaleOutputValues ")
    interpolationMode = traits.Enum("NearestNeighbor", "Linear", "ResampleInPlace", "BSpline", "WindowedSinc", "Hamming", "Cosine", "Welch", "Lanczos", "Blackman", desc="Type of interpolation to be used when applying transform to moving volume.  Options are Linear, NearestNeighbor, BSpline, WindowedSinc, or ResampleInPlace.  The ResampleInPlace option will create an image with the same discrete voxel values and will adjust the origin and direction of the physical space interpretation.", argstr="--interpolationMode %s")
    minimumStepLength = InputMultiPath(traits.Float, desc="Each step in the optimization takes steps at least this big.  When none are possible, registration is complete.", sep=",", argstr="--minimumStepLength %s")
    translationScale = traits.Float(desc="How much to scale up changes in position compared to unit rotational changes in radians -- decrease this to put more rotation in the search pattern.", argstr="--translationScale %f")
    reproportionScale = traits.Float(desc="ScaleVersor3D 'Scale' compensation factor.  Increase this to put more rescaling in a ScaleVersor3D or ScaleSkewVersor3D search pattern.  1.0 works well with a translationScale of 1000.0", argstr="--reproportionScale %f")
    skewScale = traits.Float(desc="ScaleSkewVersor3D Skew compensation factor.  Increase this to put more skew in a ScaleSkewVersor3D search pattern.  1.0 works well with a translationScale of 1000.0", argstr="--skewScale %f")
    maxBSplineDisplacement = traits.Float(desc=" Sets the maximum allowed displacements in image physical coordinates for BSpline control grid along each axis.  A value of 0.0 indicates that the problem should be unbounded.  NOTE:  This only constrains the BSpline portion, and does not limit the displacement from the associated bulk transform.  This can lead to a substantial reduction in computation time in the BSpline optimizer.,       ", argstr="--maxBSplineDisplacement %f")
    histogramMatch = traits.Bool(desc="Histogram Match the input images.  This is suitable for images of the same modality that may have different absolute scales, but the same overall intensity profile. Do NOT use if registering images from different modailties.", argstr="--histogramMatch ")
    numberOfHistogramBins = traits.Int(desc="The number of histogram levels", argstr="--numberOfHistogramBins %d")
    numberOfMatchPoints = traits.Int(desc="the number of match points", argstr="--numberOfMatchPoints %d")
    strippedOutputTransform = traits.Either(traits.Bool, File(), hash_files=False, desc="File name for the rigid component of the estimated affine transform. Can be used to rigidly register the moving image to the fixed image. NOTE:  This value is overwritten if either bsplineTransform or linearTransform is set.", argstr="--strippedOutputTransform %s")
    transformType = InputMultiPath(traits.Str, desc="Specifies a list of registration types to be used.  The valid types are, Rigid, ScaleVersor3D, ScaleSkewVersor3D, Affine, and BSpline.  Specifiying more than one in a comma separated list will initialize the next stage with the previous results. If registrationClass flag is used, it overrides this parameter setting.", sep=",", argstr="--transformType %s")
    outputTransform = traits.Either(traits.Bool, File(), hash_files=False, desc="(optional) Filename to which save the (optional) estimated transform. NOTE: You must select either the outputTransform or the outputVolume option.", argstr="--outputTransform %s")
    fixedVolumeTimeIndex = traits.Int(desc="The index in the time series for the 3D fixed image to fit, if 4-dimensional.", argstr="--fixedVolumeTimeIndex %d")
    movingVolumeTimeIndex = traits.Int(desc="The index in the time series for the 3D moving image to fit, if 4-dimensional.", argstr="--movingVolumeTimeIndex %d")
    medianFilterSize = InputMultiPath(traits.Int, desc="The radius for the optional MedianImageFilter preprocessing in all 3 directions.", sep=",", argstr="--medianFilterSize %s")
    removeIntensityOutliers = traits.Float(desc="The half percentage to decide outliers of image intensities. The default value is zero, which means no outlier removal. If the value of 0.005 is given, the moduel will throw away 0.005 % of both tails, so 0.01% of intensities in total would be ignored in its statistic calculation. ", argstr="--removeIntensityOutliers %f")
    useCachingOfBSplineWeightsMode = traits.Enum("ON", "OFF", desc="This is a 5x speed advantage at the expense of requiring much more memory.  Only relevant when transformType is BSpline.", argstr="--useCachingOfBSplineWeightsMode %s")
    useExplicitPDFDerivativesMode = traits.Enum("AUTO", "ON", "OFF", desc="Using mode AUTO means OFF for BSplineDeformableTransforms and ON for the linear transforms.  The ON alternative uses more memory to sometimes do a better job.", argstr="--useExplicitPDFDerivativesMode %s")
    ROIAutoDilateSize = traits.Float(desc="This flag is only relavent when using ROIAUTO mode for initializing masks.  It defines the final dilation size to capture a bit of background outside the tissue region.  At setting of 10mm has been shown to help regularize a BSpline registration type so that there is some background constraints to match the edges of the head better.", argstr="--ROIAutoDilateSize %f")
    ROIAutoClosingSize = traits.Float(desc="This flag is only relavent when using ROIAUTO mode for initializing masks.  It defines the hole closing size in mm.  It is rounded up to the nearest whole pixel size in each direction. The default is to use a closing size of 9mm.  For mouse data this value may need to be reset to 0.9 or smaller.", argstr="--ROIAutoClosingSize %f")
    relaxationFactor = traits.Float(desc="Internal debugging parameter, and should probably never be used from the command line.  This will be removed in the future.", argstr="--relaxationFactor %f")
    maximumStepLength = traits.Float(desc="Internal debugging parameter, and should probably never be used from the command line.  This will be removed in the future.", argstr="--maximumStepLength %f")
    failureExitCode = traits.Int(desc="If the fit fails, exit with this status code.  (It can be used to force a successfult exit status of (0) if the registration fails due to reaching the maximum number of iterations.", argstr="--failureExitCode %d")
    writeTransformOnFailure = traits.Bool(desc="Flag to save the final transform even if the numberOfIterations are reached without convergence. (Intended for use when --failureExitCode 0 )", argstr="--writeTransformOnFailure ")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use. (default is auto-detected)", argstr="--numberOfThreads %d")
    forceMINumberOfThreads = traits.Int(desc="Force the the maximum number of threads to use for non thread safe MI metric.", argstr="--forceMINumberOfThreads %d")
    debugLevel = traits.Int(desc="Display debug messages, and produce debug intermediate results.  0=OFF, 1=Minimal, 10=Maximum debugging.", argstr="--debugLevel %d")
    costFunctionConvergenceFactor = traits.Float(desc=" From itkLBFGSBOptimizer.h: Set/Get the CostFunctionConvergenceFactor. Algorithm terminates when the reduction in cost function is less than (factor * epsmcj) where epsmch is the machine precision. Typical values for factor: 1e+12 for low accuracy; 1e+7 for moderate accuracy and 1e+1 for extremely high accuracy.  1e+9 seems to work well.,       ", argstr="--costFunctionConvergenceFactor %f")
    projectedGradientTolerance = traits.Float(desc=" From itkLBFGSBOptimizer.h: Set/Get the ProjectedGradientTolerance. Algorithm terminates when the project gradient is below the tolerance. Default lbfgsb value is 1e-5, but 1e-4 seems to work well.,       ", argstr="--projectedGradientTolerance %f")
    gui = traits.Bool(desc="Display intermediate image volumes for debugging.  NOTE:  This is not part of the standard build sytem, and probably does nothing on your installation.", argstr="--gui ")
    promptUser = traits.Bool(desc="Prompt the user to hit enter each time an image is sent to the DebugImageViewer", argstr="--promptUser ")
    NEVER_USE_THIS_FLAG_IT_IS_OUTDATED_00 = traits.Bool(desc="DO NOT USE THIS FLAG", argstr="--NEVER_USE_THIS_FLAG_IT_IS_OUTDATED_00 ")
    NEVER_USE_THIS_FLAG_IT_IS_OUTDATED_01 = traits.Bool(desc="DO NOT USE THIS FLAG", argstr="--NEVER_USE_THIS_FLAG_IT_IS_OUTDATED_01 ")
    NEVER_USE_THIS_FLAG_IT_IS_OUTDATED_02 = traits.Bool(desc="DO NOT USE THIS FLAG", argstr="--NEVER_USE_THIS_FLAG_IT_IS_OUTDATED_02 ")
    permitParameterVariation = InputMultiPath(traits.Int, desc="A bit vector to permit linear transform parameters to vary under optimization.  The vector order corresponds with transform parameters, and beyond the end ones fill in as a default.  For instance, you can choose to rotate only in x (pitch) with 1,0,0;  this is mostly for expert use in turning on and off individual degrees of freedom in rotation, translation or scaling without multiplying the number of transform representations; this trick is probably meaningless when tried with the general affine transform.", sep=",", argstr="--permitParameterVariation %s")
    costMetric = traits.Enum("MMI", "MSE", "NC", "MC", desc="The cost metric to be used during fitting. Defaults to MMI. Options are MMI (Mattes Mutual Information), MSE (Mean Square Error), NC (Normalized Correlation), MC (Match Cardinality for binary images)", argstr="--costMetric %s")


class BRAINSFitOutputSpec(TraitedSpec):
    bsplineTransform = File(desc="(optional) Filename to which save the estimated transform. NOTE: You must set at least one output object (either a deformed image or a transform.  NOTE: USE THIS ONLY IF THE FINAL TRANSFORM IS BSpline", exists=True)
    linearTransform = File(desc="(optional) Filename to which save the estimated transform. NOTE: You must set at least one output object (either a deformed image or a transform.  NOTE: USE THIS ONLY IF THE FINAL TRANSFORM IS ---NOT--- BSpline", exists=True)
    outputVolume = File(desc="(optional) Output image for registration. NOTE: You must select either the outputTransform or the outputVolume option.", exists=True)
    outputFixedVolumeROI = File(desc="The ROI automatically found in fixed image, ONLY FOR ROIAUTO mode.", exists=True)
    outputMovingVolumeROI = File(desc="The ROI automatically found in moving image, ONLY FOR ROIAUTO mode.", exists=True)
    strippedOutputTransform = File(desc="File name for the rigid component of the estimated affine transform. Can be used to rigidly register the moving image to the fixed image. NOTE:  This value is overwritten if either bsplineTransform or linearTransform is set.", exists=True)
    outputTransform = File(desc="(optional) Filename to which save the (optional) estimated transform. NOTE: You must select either the outputTransform or the outputVolume option.", exists=True)


class BRAINSFit(CommandLine):
    """title: General Registration (BRAINS)

category: Registration

description: Register a three-dimensional volume to a reference volume (Mattes Mutual Information by default). Full documentation avalable here: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/BRAINSFit. Method described in BRAINSFit: Mutual Information Registrations of Whole-Brain 3D Images, Using the Insight Toolkit, Johnson H.J., Harris G., Williams K., The Insight Journal, 2007. http://hdl.handle.net/1926/1291

version: 3.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:BRAINSFit

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Hans J. Johnson, hans-johnson -at- uiowa.edu, http://wwww.psychiatry.uiowa.edu

acknowledgements: Hans Johnson(1,3,4); Kent Williams(1); Gregory Harris(1), Vincent Magnotta(1,2,3);  Andriy Fedorov(5) 1=University of Iowa Department of Psychiatry, 2=University of Iowa Department of Radiology, 3=University of Iowa Department of Biomedical Engineering, 4=University of Iowa Department of Electrical and Computer Engineering, 5=Surgical Planning Lab, Harvard

"""

    input_spec = BRAINSFitInputSpec
    output_spec = BRAINSFitOutputSpec
    _cmd = " BRAINSFit "
    _outputs_filenames = {'outputVolume':'outputVolume.nii','bsplineTransform':'bsplineTransform.mat','outputTransform':'outputTransform.mat','outputFixedVolumeROI':'outputFixedVolumeROI.nii','strippedOutputTransform':'strippedOutputTransform.mat','outputMovingVolumeROI':'outputMovingVolumeROI.nii','linearTransform':'linearTransform.mat'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(BRAINSFit, self)._format_arg(name, spec, value)



class BRAINSDemonWarpInputSpec(CommandLineInputSpec):
    movingVolume = File(desc="Required: input moving image", exists=True, argstr="--movingVolume %s")
    fixedVolume = File(desc="Required: input fixed (target) image", exists=True, argstr="--fixedVolume %s")
    inputPixelType = traits.Enum("float", "short", "ushort", "int", "uchar", desc="Input volumes will be typecast to this format: float|short|ushort|int|uchar", argstr="--inputPixelType %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: output resampled moving image (will have the same physical space as the fixedVolume).", argstr="--outputVolume %s")
    outputDeformationFieldVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Output deformation field vector image (will have the same physical space as the fixedVolume).", argstr="--outputDeformationFieldVolume %s")
    outputPixelType = traits.Enum("float", "short", "ushort", "int", "uchar", desc="outputVolume will be typecast to this format: float|short|ushort|int|uchar", argstr="--outputPixelType %s")
    interpolationMode = traits.Enum("NearestNeighbor", "Linear", "ResampleInPlace", "BSpline", "WindowedSinc", "Hamming", "Cosine", "Welch", "Lanczos", "Blackman", desc="Type of interpolation to be used when applying transform to moving volume.  Options are Linear, ResampleInPlace, NearestNeighbor, BSpline, or WindowedSinc", argstr="--interpolationMode %s")
    registrationFilterType = traits.Enum("Demons", "FastSymmetricForces", "Diffeomorphic", "LogDemons", "SymmetricLogDemons", desc="Registration Filter Type: Demons|FastSymmetricForces|Diffeomorphic|LogDemons|SymmetricLogDemons", argstr="--registrationFilterType %s")
    smoothDeformationFieldSigma = traits.Float(desc="A gaussian smoothing value to be applied to the deformation feild at each iteration.", argstr="--smoothDeformationFieldSigma %f")
    numberOfPyramidLevels = traits.Int(desc="Number of image pyramid levels to use in the multi-resolution registration.", argstr="--numberOfPyramidLevels %d")
    minimumFixedPyramid = InputMultiPath(traits.Int, desc="The shrink factor for the first level of the fixed image pyramid. (i.e. start at 1/16 scale, then 1/8, then 1/4, then 1/2, and finally full scale)", sep=",", argstr="--minimumFixedPyramid %s")
    minimumMovingPyramid = InputMultiPath(traits.Int, desc="The shrink factor for the first level of the moving image pyramid. (i.e. start at 1/16 scale, then 1/8, then 1/4, then 1/2, and finally full scale)", sep=",", argstr="--minimumMovingPyramid %s")
    arrayOfPyramidLevelIterations = InputMultiPath(traits.Int, desc="The number of iterations for each pyramid level", sep=",", argstr="--arrayOfPyramidLevelIterations %s")
    histogramMatch = traits.Bool(desc="Histogram Match the input images.  This is suitable for images of the same modality that may have different absolute scales, but the same overall intensity profile.", argstr="--histogramMatch ")
    numberOfHistogramBins = traits.Int(desc="The number of histogram levels", argstr="--numberOfHistogramBins %d")
    numberOfMatchPoints = traits.Int(desc="The number of match points for histrogramMatch", argstr="--numberOfMatchPoints %d")
    medianFilterSize = InputMultiPath(traits.Int, desc="Median filter radius in all 3 directions.  When images have a lot of salt and pepper noise, this step can improve the registration.", sep=",", argstr="--medianFilterSize %s")
    initializeWithDeformationField = File(desc="Initial deformation field vector image file name", exists=True, argstr="--initializeWithDeformationField %s")
    initializeWithTransform = File(desc="Initial Transform filename", exists=True, argstr="--initializeWithTransform %s")
    maskProcessingMode = traits.Enum("NOMASK", "ROIAUTO", "ROI", "BOBF", desc="What mode to use for using the masks: NOMASK|ROIAUTO|ROI|BOBF.  If ROIAUTO is choosen, then the mask is implicitly defined using a otsu forground and hole filling algorithm. Where the Region Of Interest mode uses the masks to define what parts of the image should be used for computing the deformation field.  Brain Only Background Fill uses the masks to pre-process the input images by clipping and filling in the background with a predefined value.", argstr="--maskProcessingMode %s")
    fixedBinaryVolume = File(desc="Mask filename for desired region of interest in the Fixed image.", exists=True, argstr="--fixedBinaryVolume %s")
    movingBinaryVolume = File(desc="Mask filename for desired region of interest in the Moving image.", exists=True, argstr="--movingBinaryVolume %s")
    lowerThresholdForBOBF = traits.Int(desc="Lower threshold for performing BOBF", argstr="--lowerThresholdForBOBF %d")
    upperThresholdForBOBF = traits.Int(desc="Upper threshold for performing BOBF", argstr="--upperThresholdForBOBF %d")
    backgroundFillValue = traits.Int(desc="Replacement value to overwrite background when performing BOBF", argstr="--backgroundFillValue %d")
    seedForBOBF = InputMultiPath(traits.Int, desc="coordinates in all 3 directions for Seed when performing BOBF", sep=",", argstr="--seedForBOBF %s")
    neighborhoodForBOBF = InputMultiPath(traits.Int, desc="neighborhood in all 3 directions to be included when performing BOBF", sep=",", argstr="--neighborhoodForBOBF %s")
    outputDisplacementFieldPrefix = traits.Str(desc="Displacement field filename prefix for writing separate x, y, and z component images", argstr="--outputDisplacementFieldPrefix %s")
    outputCheckerboardVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Genete a checkerboard image volume between the fixedVolume and the deformed movingVolume.", argstr="--outputCheckerboardVolume %s")
    checkerboardPatternSubdivisions = InputMultiPath(traits.Int, desc="Number of Checkerboard subdivisions in all 3 directions", sep=",", argstr="--checkerboardPatternSubdivisions %s")
    outputNormalized = traits.Bool(desc="Flag to warp and write the normalized images to output.  In normalized images the image values are fit-scaled to be between 0 and the maximum storage type value.", argstr="--outputNormalized ")
    outputDebug = traits.Bool(desc="Flag to write debugging images after each step.", argstr="--outputDebug ")
    gradient_type = traits.Enum("0", "1", "2", desc="Type of gradient used for computing the demons force (0 is symmetrized, 1 is fixed image, 2 is moving image)", argstr="--gradient_type %s")
    upFieldSmoothing = traits.Float(desc="Smoothing sigma for the update field at each iteration", argstr="--upFieldSmoothing %f")
    max_step_length = traits.Float(desc="Maximum length of an update vector (0: no restriction)", argstr="--max_step_length %f")
    use_vanilla_dem = traits.Bool(desc="Run vanilla demons algorithm", argstr="--use_vanilla_dem ")
    gui = traits.Bool(desc="Display intermediate image volumes for debugging", argstr="--gui ")
    promptUser = traits.Bool(desc="Prompt the user to hit enter each time an image is sent to the DebugImageViewer", argstr="--promptUser ")
    numberOfBCHApproximationTerms = traits.Int(desc="Number of terms in the BCH expansion", argstr="--numberOfBCHApproximationTerms %d")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class BRAINSDemonWarpOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: output resampled moving image (will have the same physical space as the fixedVolume).", exists=True)
    outputDeformationFieldVolume = File(desc="Output deformation field vector image (will have the same physical space as the fixedVolume).", exists=True)
    outputCheckerboardVolume = File(desc="Genete a checkerboard image volume between the fixedVolume and the deformed movingVolume.", exists=True)


class BRAINSDemonWarp(CommandLine):
    """title: Demon Registration (BRAINS)

category: Registration

description:
    This program finds a deformation field to warp a moving image onto a fixed image.  The images must be of the same signal kind, and contain an image of the same kind of object.  This program uses the Thirion Demons warp software in ITK, the Insight Toolkit.  Additional information is available at: http://www.nitrc.org/projects/brainsdemonwarp.



version: 3.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:BRAINSDemonWarp

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Hans J. Johnson and Greg Harris.

acknowledgements: The development of this tool was supported by funding from grants NS050568 and NS40068 from the National Institute of Neurological Disorders and Stroke and grants MH31593, MH40856, from the National Institute of Mental Health.

"""

    input_spec = BRAINSDemonWarpInputSpec
    output_spec = BRAINSDemonWarpOutputSpec
    _cmd = " BRAINSDemonWarp "
    _outputs_filenames = {'outputVolume':'outputVolume.nii','outputCheckerboardVolume':'outputCheckerboardVolume.nii','outputDeformationFieldVolume':'outputDeformationFieldVolume.nrrd'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(BRAINSDemonWarp, self)._format_arg(name, spec, value)



class BRAINSROIAutoInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="The input image for finding the largest region filled mask.", exists=True, argstr="--inputVolume %s")
    outputROIMaskVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="The ROI automatically found from the input image.", argstr="--outputROIMaskVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="The inputVolume with optional [maskOutput|cropOutput] to the region of the brain mask.", argstr="--outputVolume %s")
    maskOutput = traits.Bool(desc="The inputVolume multiplied by the ROI mask.", argstr="--maskOutput ")
    cropOutput = traits.Bool(desc="The inputVolume cropped to the region of the ROI mask.", argstr="--cropOutput ")
    otsuPercentileThreshold = traits.Float(desc="Parameter to the Otsu threshold algorithm.", argstr="--otsuPercentileThreshold %f")
    thresholdCorrectionFactor = traits.Float(desc="A factor to scale the Otsu algorithm's result threshold, in case clipping mangles the image.", argstr="--thresholdCorrectionFactor %f")
    closingSize = traits.Float(desc="The Closing Size (in millimeters) for largest connected filled mask.  This value is divided by image spacing and rounded to the next largest voxel number.", argstr="--closingSize %f")
    ROIAutoDilateSize = traits.Float(desc="This flag is only relavent when using ROIAUTO mode for initializing masks.  It defines the final dilation size to capture a bit of background outside the tissue region.  At setting of 10mm has been shown to help regularize a BSpline registration type so that there is some background constraints to match the edges of the head better.", argstr="--ROIAutoDilateSize %f")
    outputVolumePixelType = traits.Enum("float", "short", "ushort", "int", "uint", "uchar", desc="The output image Pixel Type is the scalar datatype for representation of the Output Volume.", argstr="--outputVolumePixelType %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class BRAINSROIAutoOutputSpec(TraitedSpec):
    outputROIMaskVolume = File(desc="The ROI automatically found from the input image.", exists=True)
    outputVolume = File(desc="The inputVolume with optional [maskOutput|cropOutput] to the region of the brain mask.", exists=True)


class BRAINSROIAuto(CommandLine):
    """title: Foreground masking (BRAINS)

category: Segmentation.Specialized

description: This program is used to create a mask over the most prominant forground region in an image.  This is accomplished via a combination of otsu thresholding and a closing operation.  More documentation is available here: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/ForegroundMasking.


version: 2.4.1

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Hans J. Johnson, hans-johnson -at- uiowa.edu, http://wwww.psychiatry.uiowa.edu

acknowledgements: Hans Johnson(1,3,4); Kent Williams(1); Gregory Harris(1), Vincent Magnotta(1,2,3);  Andriy Fedorov(5), fedorov -at- bwh.harvard.edu (Slicer integration); (1=University of Iowa Department of Psychiatry, 2=University of Iowa Department of Radiology, 3=University of Iowa Department of Biomedical Engineering, 4=University of Iowa Department of Electrical and Computer Engineering, 5=Surgical Planning Lab, Harvard)

"""

    input_spec = BRAINSROIAutoInputSpec
    output_spec = BRAINSROIAutoOutputSpec
    _cmd = " BRAINSROIAuto "
    _outputs_filenames = {'outputVolume':'outputVolume.nii','outputROIMaskVolume':'outputROIMaskVolume.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(BRAINSROIAuto, self)._format_arg(name, spec, value)



class BRAINSResampleInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Image To Warp", exists=True, argstr="--inputVolume %s")
    referenceVolume = File(desc="Reference image used only to define the output space. If not specified, the warping is done in the same space as the image to warp.", exists=True, argstr="--referenceVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Resulting deformed image", argstr="--outputVolume %s")
    pixelType = traits.Enum("float", "short", "ushort", "int", "uint", "uchar", "binary", desc="Specifies the pixel type for the input/output images.  The \"binary\" pixel type uses a modified algorithm whereby the image is read in as unsigned char, a signed distance map is created, signed distance map is resampled, and then a thresholded image of type unsigned char is written to disk.", argstr="--pixelType %s")
    deformationVolume = File(desc="Displacement Field to be used to warp the image", exists=True, argstr="--deformationVolume %s")
    warpTransform = File(desc="Filename for the BRAINSFit transform used in place of the deformation field", exists=True, argstr="--warpTransform %s")
    interpolationMode = traits.Enum("NearestNeighbor", "Linear", "ResampleInPlace", "BSpline", "WindowedSinc", "Hamming", "Cosine", "Welch", "Lanczos", "Blackman", desc="Type of interpolation to be used when applying transform to moving volume.  Options are Linear, ResampleInPlace, NearestNeighbor, BSpline, or WindowedSinc", argstr="--interpolationMode %s")
    inverseTransform = traits.Bool(desc="True/False is to compute inverse of given transformation. Default is false", argstr="--inverseTransform ")
    defaultValue = traits.Float(desc="Default voxel value", argstr="--defaultValue %f")
    gridSpacing = InputMultiPath(traits.Int, desc="Add warped grid to output image to help show the deformation that occured with specified spacing.   A spacing of 0 in a dimension indicates that grid lines should be rendered to fall exactly (i.e. do not allow displacements off that plane).  This is useful for makeing a 2D image of grid lines from the 3D space ", sep=",", argstr="--gridSpacing %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class BRAINSResampleOutputSpec(TraitedSpec):
    outputVolume = File(desc="Resulting deformed image", exists=True)


class BRAINSResample(CommandLine):
    """title: Resample Image (BRAINS)

category: Registration

description:
	  This program collects together three common image processing tasks that all involve resampling an image volume: Resampling to a new resolution and spacing, applying a transformation (using an ITK transform IO mechanisms) and Warping (using a vector image deformation field).  Full documentation available here: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.0/Modules/BRAINSResample.


version: 3.0.0

documentation-url: http://www.slicer.org/slicerWiki/index.php/Modules:BRAINSResample

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Vincent Magnotta, Greg Harris, and Hans Johnson.

acknowledgements: The development of this tool was supported by funding from grants NS050568 and NS40068 from the National Institute of Neurological Disorders and Stroke and grants MH31593, MH40856, from the National Institute of Mental Health.

"""

    input_spec = BRAINSResampleInputSpec
    output_spec = BRAINSResampleOutputSpec
    _cmd = " BRAINSResample "
    _outputs_filenames = {'outputVolume':'outputVolume.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(BRAINSResample, self)._format_arg(name, spec, value)



class VBRAINSDemonWarpInputSpec(CommandLineInputSpec):
    movingVolume = InputMultiPath(File(exists=True), desc="Required: input moving image", argstr="--movingVolume %s...")
    fixedVolume = InputMultiPath(File(exists=True), desc="Required: input fixed (target) image", argstr="--fixedVolume %s...")
    inputPixelType = traits.Enum("float", "short", "ushort", "int", "uchar", desc="Input volumes will be typecast to this format: float|short|ushort|int|uchar", argstr="--inputPixelType %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: output resampled moving image (will have the same physical space as the fixedVolume).", argstr="--outputVolume %s")
    outputDeformationFieldVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Output deformation field vector image (will have the same physical space as the fixedVolume).", argstr="--outputDeformationFieldVolume %s")
    outputPixelType = traits.Enum("float", "short", "ushort", "int", "uchar", desc="outputVolume will be typecast to this format: float|short|ushort|int|uchar", argstr="--outputPixelType %s")
    interpolationMode = traits.Enum("NearestNeighbor", "Linear", "ResampleInPlace", "BSpline", "WindowedSinc", "Hamming", "Cosine", "Welch", "Lanczos", "Blackman", desc="Type of interpolation to be used when applying transform to moving volume.  Options are Linear, ResampleInPlace, NearestNeighbor, BSpline, or WindowedSinc", argstr="--interpolationMode %s")
    registrationFilterType = traits.Enum("Demons", "FastSymmetricForces", "Diffeomorphic", "LogDemons", "SymmetricLogDemons", desc="Registration Filter Type: Demons|FastSymmetricForces|Diffeomorphic|LogDemons|SymmetricLogDemons", argstr="--registrationFilterType %s")
    smoothDeformationFieldSigma = traits.Float(desc="A gaussian smoothing value to be applied to the deformation feild at each iteration.", argstr="--smoothDeformationFieldSigma %f")
    numberOfPyramidLevels = traits.Int(desc="Number of image pyramid levels to use in the multi-resolution registration.", argstr="--numberOfPyramidLevels %d")
    minimumFixedPyramid = InputMultiPath(traits.Int, desc="The shrink factor for the first level of the fixed image pyramid. (i.e. start at 1/16 scale, then 1/8, then 1/4, then 1/2, and finally full scale)", sep=",", argstr="--minimumFixedPyramid %s")
    minimumMovingPyramid = InputMultiPath(traits.Int, desc="The shrink factor for the first level of the moving image pyramid. (i.e. start at 1/16 scale, then 1/8, then 1/4, then 1/2, and finally full scale)", sep=",", argstr="--minimumMovingPyramid %s")
    arrayOfPyramidLevelIterations = InputMultiPath(traits.Int, desc="The number of iterations for each pyramid level", sep=",", argstr="--arrayOfPyramidLevelIterations %s")
    histogramMatch = traits.Bool(desc="Histogram Match the input images.  This is suitable for images of the same modality that may have different absolute scales, but the same overall intensity profile.", argstr="--histogramMatch ")
    numberOfHistogramBins = traits.Int(desc="The number of histogram levels", argstr="--numberOfHistogramBins %d")
    numberOfMatchPoints = traits.Int(desc="The number of match points for histrogramMatch", argstr="--numberOfMatchPoints %d")
    medianFilterSize = InputMultiPath(traits.Int, desc="Median filter radius in all 3 directions.  When images have a lot of salt and pepper noise, this step can improve the registration.", sep=",", argstr="--medianFilterSize %s")
    initializeWithDeformationField = File(desc="Initial deformation field vector image file name", exists=True, argstr="--initializeWithDeformationField %s")
    initializeWithTransform = File(desc="Initial Transform filename", exists=True, argstr="--initializeWithTransform %s")
    makeBOBF = traits.Bool(desc="Flag to make Brain-Only Background-Filled versions of the input and target volumes.", argstr="--makeBOBF ")
    fixedBinaryVolume = File(desc="Mask filename for desired region of interest in the Fixed image.", exists=True, argstr="--fixedBinaryVolume %s")
    movingBinaryVolume = File(desc="Mask filename for desired region of interest in the Moving image.", exists=True, argstr="--movingBinaryVolume %s")
    lowerThresholdForBOBF = traits.Int(desc="Lower threshold for performing BOBF", argstr="--lowerThresholdForBOBF %d")
    upperThresholdForBOBF = traits.Int(desc="Upper threshold for performing BOBF", argstr="--upperThresholdForBOBF %d")
    backgroundFillValue = traits.Int(desc="Replacement value to overwrite background when performing BOBF", argstr="--backgroundFillValue %d")
    seedForBOBF = InputMultiPath(traits.Int, desc="coordinates in all 3 directions for Seed when performing BOBF", sep=",", argstr="--seedForBOBF %s")
    neighborhoodForBOBF = InputMultiPath(traits.Int, desc="neighborhood in all 3 directions to be included when performing BOBF", sep=",", argstr="--neighborhoodForBOBF %s")
    outputDisplacementFieldPrefix = traits.Str(desc="Displacement field filename prefix for writing separate x, y, and z component images", argstr="--outputDisplacementFieldPrefix %s")
    outputCheckerboardVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Genete a checkerboard image volume between the fixedVolume and the deformed movingVolume.", argstr="--outputCheckerboardVolume %s")
    checkerboardPatternSubdivisions = InputMultiPath(traits.Int, desc="Number of Checkerboard subdivisions in all 3 directions", sep=",", argstr="--checkerboardPatternSubdivisions %s")
    outputNormalized = traits.Bool(desc="Flag to warp and write the normalized images to output.  In normalized images the image values are fit-scaled to be between 0 and the maximum storage type value.", argstr="--outputNormalized ")
    outputDebug = traits.Bool(desc="Flag to write debugging images after each step.", argstr="--outputDebug ")
    weightFactors = InputMultiPath(traits.Float, desc="Weight fatctors for each input images", sep=",", argstr="--weightFactors %s")
    gradient_type = traits.Enum("0", "1", "2", desc="Type of gradient used for computing the demons force (0 is symmetrized, 1 is fixed image, 2 is moving image)", argstr="--gradient_type %s")
    upFieldSmoothing = traits.Float(desc="Smoothing sigma for the update field at each iteration", argstr="--upFieldSmoothing %f")
    max_step_length = traits.Float(desc="Maximum length of an update vector (0: no restriction)", argstr="--max_step_length %f")
    use_vanilla_dem = traits.Bool(desc="Run vanilla demons algorithm", argstr="--use_vanilla_dem ")
    gui = traits.Bool(desc="Display intermediate image volumes for debugging", argstr="--gui ")
    promptUser = traits.Bool(desc="Prompt the user to hit enter each time an image is sent to the DebugImageViewer", argstr="--promptUser ")
    numberOfBCHApproximationTerms = traits.Int(desc="Number of terms in the BCH expansion", argstr="--numberOfBCHApproximationTerms %d")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class VBRAINSDemonWarpOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: output resampled moving image (will have the same physical space as the fixedVolume).", exists=True)
    outputDeformationFieldVolume = File(desc="Output deformation field vector image (will have the same physical space as the fixedVolume).", exists=True)
    outputCheckerboardVolume = File(desc="Genete a checkerboard image volume between the fixedVolume and the deformed movingVolume.", exists=True)


class VBRAINSDemonWarp(CommandLine):
    """title: Vector Demon Registration (BRAINS)

category: Registration

description:
    This program finds a deformation field to warp a moving image onto a fixed image.  The images must be of the same signal kind, and contain an image of the same kind of object.  This program uses the Thirion Demons warp software in ITK, the Insight Toolkit.  Additional information is available at: http://www.nitrc.org/projects/brainsdemonwarp.



version: 3.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:BRAINSDemonWarp

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Hans J. Johnson and Greg Harris.

acknowledgements: The development of this tool was supported by funding from grants NS050568 and NS40068 from the National Institute of Neurological Disorders and Stroke and grants MH31593, MH40856, from the National Institute of Mental Health.

"""

    input_spec = VBRAINSDemonWarpInputSpec
    output_spec = VBRAINSDemonWarpOutputSpec
    _cmd = " VBRAINSDemonWarp "
    _outputs_filenames = {'outputVolume':'outputVolume.nii','outputCheckerboardVolume':'outputCheckerboardVolume.nii','outputDeformationFieldVolume':'outputDeformationFieldVolume.nrrd'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(VBRAINSDemonWarp, self)._format_arg(name, spec, value)



class extractNrrdVectorIndexInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input file containing the vector that will be extracted", exists=True, argstr="--inputVolume %s")
    vectorIndex = traits.Int(desc="Index in the vector image to extract", argstr="--vectorIndex %d")
    setImageOrientation = traits.Enum("AsAcquired", "Axial", "Coronal", "Sagittal", desc="Sets the image orientation of the extracted vector (Axial, Coronal, Sagittal)", argstr="--setImageOrientation %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing the vector image at the given index", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class extractNrrdVectorIndexOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing the vector image at the given index", exists=True)


class extractNrrdVectorIndex(CommandLine):
    """title: Extract Nrrd Index

category: Diffusion.GTRACT

description: This program will extract a 3D image (single vector) from a vector 3D image at a given vector index.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = extractNrrdVectorIndexInputSpec
    output_spec = extractNrrdVectorIndexOutputSpec
    _cmd = " extractNrrdVectorIndex "
    _outputs_filenames = {'outputVolume':'outputVolume.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(extractNrrdVectorIndex, self)._format_arg(name, spec, value)



class gtractAnisotropyMapInputSpec(CommandLineInputSpec):
    inputTensorVolume = File(desc="Required: input file containing the diffusion tensor image", exists=True, argstr="--inputTensorVolume %s")
    anisotropyType = traits.Enum("ADC", "FA", "RA", "VR", "AD", "RD", "LI", desc="Anisotropy Mapping Type: ADC, FA, RA, VR, AD, RD, LI", argstr="--anisotropyType %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing the selected kind of anisotropy scalar.", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractAnisotropyMapOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing the selected kind of anisotropy scalar.", exists=True)


class gtractAnisotropyMap(CommandLine):
    """title: Anisotropy Map

category: Diffusion.GTRACT

description: This program will generate a scalar map of anisotropy, given a tensor representation. Anisotropy images are used for fiber tracking, but the anisotropy scalars are not defined along the path. Instead, the tensor representation is included as point data allowing all of these metrics to be computed using only the fiber tract point data. The images can be saved in any ITK supported format, but it is suggested that you use an image format that supports the definition of the image origin. This includes NRRD, NifTI, and Meta formats. These images can also be used for scalar analysis including regional anisotropy measures or VBM style analysis.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractAnisotropyMapInputSpec
    output_spec = gtractAnisotropyMapOutputSpec
    _cmd = " gtractAnisotropyMap "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractAnisotropyMap, self)._format_arg(name, spec, value)



class gtractAverageBvaluesInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input image file name containing multiple baseline gradients to average", exists=True, argstr="--inputVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing directly averaged baseline images", argstr="--outputVolume %s")
    directionsTolerance = traits.Float(desc="Tolerance for matching identical gradient direction pairs", argstr="--directionsTolerance %f")
    averageB0only = traits.Bool(desc="Average only baseline gradients. All other gradient directions are not averaged, but retained in the outputVolume", argstr="--averageB0only ")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractAverageBvaluesOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing directly averaged baseline images", exists=True)


class gtractAverageBvalues(CommandLine):
    """title: Average B-Values

category: Diffusion.GTRACT

description: This program will directly average together the baseline gradients (b value equals 0) within a DWI scan. This is usually used after gtractCoregBvalues.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractAverageBvaluesInputSpec
    output_spec = gtractAverageBvaluesOutputSpec
    _cmd = " gtractAverageBvalues "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractAverageBvalues, self)._format_arg(name, spec, value)



class gtractClipAnisotropyInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input image file name", exists=True, argstr="--inputVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing the clipped anisotropy image", argstr="--outputVolume %s")
    clipFirstSlice = traits.Bool(desc="Clip the first slice of the anisotropy image", argstr="--clipFirstSlice ")
    clipLastSlice = traits.Bool(desc="Clip the last slice of the anisotropy image", argstr="--clipLastSlice ")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractClipAnisotropyOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing the clipped anisotropy image", exists=True)


class gtractClipAnisotropy(CommandLine):
    """title: Clip Anisotropy

category: Diffusion.GTRACT

description: This program will zero the first and/or last slice of an anisotropy image, creating a clipped anisotropy image.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractClipAnisotropyInputSpec
    output_spec = gtractClipAnisotropyOutputSpec
    _cmd = " gtractClipAnisotropy "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractClipAnisotropy, self)._format_arg(name, spec, value)



class gtractCoRegAnatomyInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input vector image file name. It is recommended that the input volume is the skull stripped baseline image of the DWI scan.", exists=True, argstr="--inputVolume %s")
    inputAnatomicalVolume = File(desc="Required: input anatomical image file name. It is recommended that that the input anatomical image has been skull stripped and has the same orientation as the DWI scan.", exists=True, argstr="--inputAnatomicalVolume %s")
    vectorIndex = traits.Int(desc="Vector image index in the moving image (within the DWI) to be used for registration.", argstr="--vectorIndex %d")
    inputRigidTransform = File(desc="Required (for B-Spline type co-registration): input rigid transform file name. Used as a starting point for the anatomical B-Spline registration.", exists=True, argstr="--inputRigidTransform %s")
    outputTransformName = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: filename for the  fit transform.", argstr="--outputTransformName %s")
    transformType = traits.Enum("Rigid", "Bspline", desc="Transform Type: Rigid|Bspline", argstr="--transformType %s")
    numberOfIterations = traits.Int(desc="Number of iterations in the selected 3D fit", argstr="--numberOfIterations %d")
    gridSize = InputMultiPath(traits.Int, desc="Number of grid subdivisions in all 3 directions", sep=",", argstr="--gridSize %s")
    borderSize = traits.Int(desc="Size of border", argstr="--borderSize %d")
    numberOfHistogramBins = traits.Int(desc="Number of histogram bins", argstr="--numberOfHistogramBins %d")
    spatialScale = traits.Int(desc="Scales the number of voxels in the image by this value to specify the number of voxels used in the registration", argstr="--spatialScale %d")
    convergence = traits.Float(desc="Convergence Factor", argstr="--convergence %f")
    gradientTolerance = traits.Float(desc="Gradient Tolerance", argstr="--gradientTolerance %f")
    maxBSplineDisplacement = traits.Float(desc=" Sets the maximum allowed displacements in image physical coordinates for BSpline control grid along each axis.  A value of 0.0 indicates that the problem should be unbounded.  NOTE:  This only constrains the BSpline portion, and does not limit the displacement from the associated bulk transform.  This can lead to a substantial reduction in computation time in the BSpline optimizer.,       ", argstr="--maxBSplineDisplacement %f")
    maximumStepSize = traits.Float(desc="Maximum permitted step size to move in the selected 3D fit", argstr="--maximumStepSize %f")
    minimumStepSize = traits.Float(desc="Minimum required step size to move in the selected 3D fit without converging -- decrease this to make the fit more exacting", argstr="--minimumStepSize %f")
    translationScale = traits.Float(desc="How much to scale up changes in position compared to unit rotational changes in radians -- decrease this to put more translation in the fit", argstr="--translationScale %f")
    relaxationFactor = traits.Float(desc="Fraction of gradient from Jacobian to attempt to move in the selected 3D fit", argstr="--relaxationFactor %f")
    numberOfSamples = traits.Int(desc="Number of voxels sampled for mutual information computation in the selected 3D fit", argstr="--numberOfSamples %d")
    useMomentsAlign = traits.Bool(desc="MomentsAlign assumes that the center of mass of the images represent similar structures.  Perform a MomentsAlign registration as part of the sequential registration steps.   This option MUST come first, and CAN NOT be used with either CenterOfHeadLAlign, GeometryAlign, or initialTransform file.  This family of options superceeds the use of transformType if any of them are set.", argstr="--useMomentsAlign ")
    useGeometryAlign = traits.Bool(desc="GeometryAlign on assumes that the center of the voxel lattice of the images represent similar structures. Perform a GeometryCenterAlign registration as part of the sequential registration steps.   This option MUST come first, and CAN NOT be used with either MomentsAlign, CenterOfHeadAlign, or initialTransform file.  This family of options superceeds the use of transformType if any of them are set.", argstr="--useGeometryAlign ")
    useCenterOfHeadAlign = traits.Bool(desc="CenterOfHeadAlign attempts to find a hemisphere full of foreground voxels from the superior direction as an estimate of where the center of a head shape would be to drive a center of mass estimate.  Perform a CenterOfHeadAlign registration as part of the sequential registration steps.   This option MUST come first, and CAN NOT be used with either MomentsAlign, GeometryAlign, or initialTransform file.  This family of options superceeds the use of transformType if any of them are set.", argstr="--useCenterOfHeadAlign ")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractCoRegAnatomyOutputSpec(TraitedSpec):
    outputTransformName = File(desc="Required: filename for the  fit transform.", exists=True)


class gtractCoRegAnatomy(CommandLine):
    """title: Coregister B0 to Anatomy B-Spline

category: Diffusion.GTRACT

description: This program will register a Nrrd diffusion weighted 4D vector image to a fixed anatomical image. Two registration methods are supported for alignment with anatomical images: Rigid and B-Spline. The rigid registration performs a rigid body registration with the anatomical images and should be done as well to initialize the B-Spline transform. The B-SPline transform is the deformable transform, where the user can control the amount of deformation based on the number of control points as well as the maximum distance that these points can move. The B-Spline registration places a low dimensional grid in the image, which is deformed. This allows for some susceptibility related distortions to be removed from the diffusion weighted images. In general the amount of motion in the slice selection and read-out directions direction should be kept low. The distortion is in the phase encoding direction in the images. It is recommended that skull stripped (i.e. image containing only brain with skull removed) images shoud be used for image co-registration with the B-Spline transform.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractCoRegAnatomyInputSpec
    output_spec = gtractCoRegAnatomyOutputSpec
    _cmd = " gtractCoRegAnatomy "
    _outputs_filenames = {'outputTransformName':'outputTransformName.mat'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractCoRegAnatomy, self)._format_arg(name, spec, value)



class gtractConcatDwiInputSpec(CommandLineInputSpec):
    inputVolume = InputMultiPath(File(exists=True), desc="Required: input file containing the first diffusion weighted image", argstr="--inputVolume %s...")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing the combined diffusion weighted images.", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractConcatDwiOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing the combined diffusion weighted images.", exists=True)


class gtractConcatDwi(CommandLine):
    """title: Concat DWI Images

category: Diffusion.GTRACT

description: This program will concatenate two DTI runs together.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractConcatDwiInputSpec
    output_spec = gtractConcatDwiOutputSpec
    _cmd = " gtractConcatDwi "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractConcatDwi, self)._format_arg(name, spec, value)



class gtractCopyImageOrientationInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input file containing the signed short image to reorient without resampling.", exists=True, argstr="--inputVolume %s")
    inputReferenceVolume = File(desc="Required: input file containing orietation that will be cloned.", exists=True, argstr="--inputReferenceVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD or Nifti file containing the reoriented image in reference image space.", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractCopyImageOrientationOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD or Nifti file containing the reoriented image in reference image space.", exists=True)


class gtractCopyImageOrientation(CommandLine):
    """title: Copy Image Orientation

category: Diffusion.GTRACT

description: This program will copy the orientation from the reference image into the moving image. Currently, the registration process requires that the diffusion weighted images and the anatomical images have the same image orientation (i.e. Axial, Coronal, Sagittal). It is suggested that you copy the image orientation from the diffusion weighted images and apply this to the anatomical image. This image can be subsequently removed after the registration step is complete. We anticipate that this limitation will be removed in future versions of the registration programs.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractCopyImageOrientationInputSpec
    output_spec = gtractCopyImageOrientationOutputSpec
    _cmd = " gtractCopyImageOrientation "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractCopyImageOrientation, self)._format_arg(name, spec, value)



class gtractCoregBvaluesInputSpec(CommandLineInputSpec):
    movingVolume = File(desc="Required: input moving image file name. In order to register gradients within a scan to its first gradient, set the movingVolume and fixedVolume as the same image.", exists=True, argstr="--movingVolume %s")
    fixedVolume = File(desc="Required: input fixed image file name. It is recommended that this image should either contain or be a b0 image.", exists=True, argstr="--fixedVolume %s")
    fixedVolumeIndex = traits.Int(desc="Index in the fixed image for registration. It is recommended that this image should be a b0 image.", argstr="--fixedVolumeIndex %d")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing moving images individually resampled and fit to the specified fixed image index.", argstr="--outputVolume %s")
    outputTransform = traits.Either(traits.Bool, File(), hash_files=False, desc="Registration 3D transforms concatenated in a single output file.  There are no tools that can use this, but can be used for debugging purposes.", argstr="--outputTransform %s")
    eddyCurrentCorrection = traits.Bool(desc="Flag to perform eddy current corection in addition to motion correction (recommended)", argstr="--eddyCurrentCorrection ")
    numberOfIterations = traits.Int(desc="Number of iterations in each 3D fit", argstr="--numberOfIterations %d")
    numberOfSpatialSamples = traits.Int(desc="Number of voxels sampled for mutual information computation in each 3D fit step", argstr="--numberOfSpatialSamples %d")
    relaxationFactor = traits.Float(desc="Fraction of gradient from Jacobian to attempt to move in each 3D fit step (adjust when eddyCurrentCorrection is enabled; suggested value = 0.25)", argstr="--relaxationFactor %f")
    maximumStepSize = traits.Float(desc="Maximum permitted step size to move in each 3D fit step (adjust when eddyCurrentCorrection is enabled; suggested value = 0.1)", argstr="--maximumStepSize %f")
    minimumStepSize = traits.Float(desc="Minimum required step size to move in each 3D fit step without converging -- decrease this to make the fit more exacting", argstr="--minimumStepSize %f")
    spatialScale = traits.Float(desc="How much to scale up changes in position compared to unit rotational changes in radians -- decrease this to put more rotation in the fit", argstr="--spatialScale %f")
    registerB0Only = traits.Bool(desc="Register the B0 images only", argstr="--registerB0Only ")
    debugLevel = traits.Int(desc="Display debug messages, and produce debug intermediate results.  0=OFF, 1=Minimal, 10=Maximum debugging.", argstr="--debugLevel %d")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractCoregBvaluesOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing moving images individually resampled and fit to the specified fixed image index.", exists=True)
    outputTransform = File(desc="Registration 3D transforms concatenated in a single output file.  There are no tools that can use this, but can be used for debugging purposes.", exists=True)


class gtractCoregBvalues(CommandLine):
    """title: Coregister B-Values

category: Diffusion.GTRACT

description: This step should be performed after converting DWI scans from DICOM to NRRD format. This program will register all gradients in a NRRD diffusion weighted 4D vector image (moving image) to a specified index in a fixed image. It also supports co-registration with a T2 weighted image or field map in the same plane as the DWI data. The fixed image for the registration should be a b0 image. A mutual information metric cost function is used for the registration because of the differences in signal intensity as a result of the diffusion gradients. The full affine allows the registration procedure to correct for eddy current distortions that may exist in the data. If the eddyCurrentCorrection is enabled, relaxationFactor (0.25) and maximumStepSize (0.1) should be adjusted.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractCoregBvaluesInputSpec
    output_spec = gtractCoregBvaluesOutputSpec
    _cmd = " gtractCoregBvalues "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd','outputTransform':'outputTransform.mat'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractCoregBvalues, self)._format_arg(name, spec, value)



class gtractCostFastMarchingInputSpec(CommandLineInputSpec):
    inputTensorVolume = File(desc="Required: input tensor image file name", exists=True, argstr="--inputTensorVolume %s")
    inputAnisotropyVolume = File(desc="Required: input anisotropy image file name", exists=True, argstr="--inputAnisotropyVolume %s")
    inputStartingSeedsLabelMapVolume = File(desc="Required: input starting seeds LabelMap image file name", exists=True, argstr="--inputStartingSeedsLabelMapVolume %s")
    startingSeedsLabel = traits.Int(desc="Label value for Starting Seeds", argstr="--startingSeedsLabel %d")
    outputCostVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Output vcl_cost image", argstr="--outputCostVolume %s")
    outputSpeedVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Output speed image", argstr="--outputSpeedVolume %s")
    anisotropyWeight = traits.Float(desc="Anisotropy weight used for vcl_cost function calculations", argstr="--anisotropyWeight %f")
    stoppingValue = traits.Float(desc="Terminiating value for vcl_cost function estimation", argstr="--stoppingValue %f")
    seedThreshold = traits.Float(desc="Anisotropy threshold used for seed selection", argstr="--seedThreshold %f")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractCostFastMarchingOutputSpec(TraitedSpec):
    outputCostVolume = File(desc="Output vcl_cost image", exists=True)
    outputSpeedVolume = File(desc="Output speed image", exists=True)


class gtractCostFastMarching(CommandLine):
    """title: Cost Fast Marching

category: Diffusion.GTRACT

description:  This program will use a fast marching fiber tracking algorithm to identify fiber tracts from a tensor image. This program is the first portion of the algorithm. The user must first run gtractFastMarchingTracking to generate the actual fiber tracts.  This algorithm is roughly based on the work by G. Parker et al. from IEEE Transactions On Medical Imaging, 21(5): 505-512, 2002. An additional feature of including anisotropy into the vcl_cost function calculation is included.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris. The original code here was developed by Daisy Espino.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractCostFastMarchingInputSpec
    output_spec = gtractCostFastMarchingOutputSpec
    _cmd = " gtractCostFastMarching "
    _outputs_filenames = {'outputCostVolume':'outputCostVolume.nrrd','outputSpeedVolume':'outputSpeedVolume.nrrd'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractCostFastMarching, self)._format_arg(name, spec, value)



class gtractImageConformityInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input file containing the signed short image to reorient without resampling.", exists=True, argstr="--inputVolume %s")
    inputReferenceVolume = File(desc="Required: input file containing the standard image to clone the characteristics of.", exists=True, argstr="--inputReferenceVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output Nrrd or Nifti file containing the reoriented image in reference image space.", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractImageConformityOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output Nrrd or Nifti file containing the reoriented image in reference image space.", exists=True)


class gtractImageConformity(CommandLine):
    """title: Image Conformity

category: Diffusion.GTRACT

description: This program will straighten out the Direction and Origin to match the Reference Image.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractImageConformityInputSpec
    output_spec = gtractImageConformityOutputSpec
    _cmd = " gtractImageConformity "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractImageConformity, self)._format_arg(name, spec, value)



class gtractInvertBSplineTransformInputSpec(CommandLineInputSpec):
    inputReferenceVolume = File(desc="Required: input image file name to exemplify the anatomical space to interpolate over.", exists=True, argstr="--inputReferenceVolume %s")
    inputTransform = File(desc="Required: input B-Spline transform file name", exists=True, argstr="--inputTransform %s")
    outputTransform = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: output transform file name", argstr="--outputTransform %s")
    landmarkDensity = InputMultiPath(traits.Int, desc="Number of landmark subdivisions in all 3 directions", sep=",", argstr="--landmarkDensity %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractInvertBSplineTransformOutputSpec(TraitedSpec):
    outputTransform = File(desc="Required: output transform file name", exists=True)


class gtractInvertBSplineTransform(CommandLine):
    """title: B-Spline Transform Inversion

category: Diffusion.GTRACT

description: This program will invert a B-Spline transform using a thin-plate spline approximation.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractInvertBSplineTransformInputSpec
    output_spec = gtractInvertBSplineTransformOutputSpec
    _cmd = " gtractInvertBSplineTransform "
    _outputs_filenames = {'outputTransform':'outputTransform.mat'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractInvertBSplineTransform, self)._format_arg(name, spec, value)



class gtractInvertDeformationFieldInputSpec(CommandLineInputSpec):
    baseImage = File(desc="Required: base image used to define the size of the inverse field", exists=True, argstr="--baseImage %s")
    deformationImage = File(desc="Required: Deformation field image", exists=True, argstr="--deformationImage %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: Output deformation field", argstr="--outputVolume %s")
    subsamplingFactor = traits.Int(desc="Subsampling factor for the deformation field", argstr="--subsamplingFactor %d")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractInvertDeformationFieldOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: Output deformation field", exists=True)


class gtractInvertDeformationField(CommandLine):
    """title: Invert Deformation Field

category: Diffusion.GTRACT

description: This program will invert a deformatrion field. The size of the deformation field is defined by an example image provided by the user

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractInvertDeformationFieldInputSpec
    output_spec = gtractInvertDeformationFieldOutputSpec
    _cmd = " gtractInvertDeformationField "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractInvertDeformationField, self)._format_arg(name, spec, value)



class gtractInvertRigidTransformInputSpec(CommandLineInputSpec):
    inputTransform = File(desc="Required: input rigid transform file name", exists=True, argstr="--inputTransform %s")
    outputTransform = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: output transform file name", argstr="--outputTransform %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractInvertRigidTransformOutputSpec(TraitedSpec):
    outputTransform = File(desc="Required: output transform file name", exists=True)


class gtractInvertRigidTransform(CommandLine):
    """title: Rigid Transform Inversion

category: Diffusion.GTRACT

description: This program will invert a Rigid transform.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractInvertRigidTransformInputSpec
    output_spec = gtractInvertRigidTransformOutputSpec
    _cmd = " gtractInvertRigidTransform "
    _outputs_filenames = {'outputTransform':'outputTransform.mat'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractInvertRigidTransform, self)._format_arg(name, spec, value)



class gtractResampleAnisotropyInputSpec(CommandLineInputSpec):
    inputAnisotropyVolume = File(desc="Required: input file containing the anisotropy image", exists=True, argstr="--inputAnisotropyVolume %s")
    inputAnatomicalVolume = File(desc="Required: input file containing the anatomical image whose characteristics will be cloned.", exists=True, argstr="--inputAnatomicalVolume %s")
    inputTransform = File(desc="Required: input Rigid OR Bspline transform file name", exists=True, argstr="--inputTransform %s")
    transformType = traits.Enum("Rigid", "B-Spline", desc="Transform type: Rigid, B-Spline", argstr="--transformType %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing the resampled transformed anisotropy image.", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractResampleAnisotropyOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing the resampled transformed anisotropy image.", exists=True)


class gtractResampleAnisotropy(CommandLine):
    """title: Resample Anisotropy

category: Diffusion.GTRACT

description: This program will resample a floating point image using either the Rigid or B-Spline transform. You may want to save the aligned B0 image after each of the anisotropy map co-registration steps with the anatomical image to check the registration quality with another tool.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractResampleAnisotropyInputSpec
    output_spec = gtractResampleAnisotropyOutputSpec
    _cmd = " gtractResampleAnisotropy "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractResampleAnisotropy, self)._format_arg(name, spec, value)



class gtractResampleB0InputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input file containing the 4D image", exists=True, argstr="--inputVolume %s")
    inputAnatomicalVolume = File(desc="Required: input file containing the anatomical image defining the origin, spacing and size of the resampled image (template)", exists=True, argstr="--inputAnatomicalVolume %s")
    inputTransform = File(desc="Required: input Rigid OR Bspline transform file name", exists=True, argstr="--inputTransform %s")
    vectorIndex = traits.Int(desc="Index in the diffusion weighted image set for the B0 image", argstr="--vectorIndex %d")
    transformType = traits.Enum("Rigid", "B-Spline", desc="Transform type: Rigid, B-Spline", argstr="--transformType %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing the resampled input image.", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractResampleB0OutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing the resampled input image.", exists=True)


class gtractResampleB0(CommandLine):
    """title: Resample B0

category: Diffusion.GTRACT

description: This program will resample a signed short image using either a Rigid or B-Spline transform. The user must specify a template image that will be used to define the origin, orientation, spacing, and size of the resampled image.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractResampleB0InputSpec
    output_spec = gtractResampleB0OutputSpec
    _cmd = " gtractResampleB0 "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractResampleB0, self)._format_arg(name, spec, value)



class gtractResampleCodeImageInputSpec(CommandLineInputSpec):
    inputCodeVolume = File(desc="Required: input file containing the code image", exists=True, argstr="--inputCodeVolume %s")
    inputReferenceVolume = File(desc="Required: input file containing the standard image to clone the characteristics of.", exists=True, argstr="--inputReferenceVolume %s")
    inputTransform = File(desc="Required: input Rigid or Inverse-B-Spline transform file name", exists=True, argstr="--inputTransform %s")
    transformType = traits.Enum("Rigid", "Affine", "B-Spline", "Inverse-B-Spline", "None", desc="Transform type: Rigid or Inverse-B-Spline", argstr="--transformType %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing the resampled code image in acquisition space.", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractResampleCodeImageOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing the resampled code image in acquisition space.", exists=True)


class gtractResampleCodeImage(CommandLine):
    """title: Resample Code Image

category: Diffusion.GTRACT

description: This program will resample a short integer code image using either the Rigid or Inverse-B-Spline transform.  The reference image is the DTI tensor anisotropy image space, and the input code image is in anatomical space.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractResampleCodeImageInputSpec
    output_spec = gtractResampleCodeImageOutputSpec
    _cmd = " gtractResampleCodeImage "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractResampleCodeImage, self)._format_arg(name, spec, value)



class gtractResampleDWIInPlaceInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input image is a 4D NRRD image.", exists=True, argstr="--inputVolume %s")
    inputTransform = File(desc="Required: transform file derived from rigid registration of b0 image to reference structural image.", exists=True, argstr="--inputTransform %s")
    debugLevel = traits.Int(desc="Display debug messages, and produce debug intermediate results.  0=OFF, 1=Minimal, 10=Maximum debugging.", argstr="--debugLevel %d")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: output image (NRRD file) that has been transformed into the space of the structural image.", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractResampleDWIInPlaceOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: output image (NRRD file) that has been transformed into the space of the structural image.", exists=True)


class gtractResampleDWIInPlace(CommandLine):
    """title: Resample DWI In Place

category: Diffusion.GTRACT

description: Resamples DWI image to structural image.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractResampleDWIInPlaceInputSpec
    output_spec = gtractResampleDWIInPlaceOutputSpec
    _cmd = " gtractResampleDWIInPlace "
    _outputs_filenames = {'outputVolume':'outputVolume.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractResampleDWIInPlace, self)._format_arg(name, spec, value)



class gtractTensorInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input image 4D NRRD image. Must contain data based on at least 6 distinct diffusion directions. The inputVolume is allowed to have multiple b0 and gradient direction images. Averaging of the b0 image is done internally in this step. Prior averaging of the DWIs is not required.", exists=True, argstr="--inputVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing the Tensor vector image", argstr="--outputVolume %s")
    medianFilterSize = InputMultiPath(traits.Int, desc="Median filter radius in all 3 directions", sep=",", argstr="--medianFilterSize %s")
    maskProcessingMode = traits.Enum("NOMASK", "ROIAUTO", "ROI", desc="ROIAUTO:  mask is implicitly defined using a otsu forground and hole filling algorithm. ROI: Uses the masks to define what parts of the image should be used for computing the transform. NOMASK: no mask used", argstr="--maskProcessingMode %s")
    maskVolume = File(desc="Mask Image, if maskProcessingMode is ROI", exists=True, argstr="--maskVolume %s")
    backgroundSuppressingThreshold = traits.Int(desc="Image threshold to suppress background. This sets a threshold used on the b0 image to remove background voxels from processing. Typically, values of 100 and 500 work well for Siemens and GE DTI data, respectively. Check your data particularly in the globus pallidus to make sure the brain tissue is not being eliminated with this threshold.", argstr="--backgroundSuppressingThreshold %d")
    resampleIsotropic = traits.Bool(desc="Flag to resample to isotropic voxels. Enabling this feature is recommended if fiber tracking will be performed.", argstr="--resampleIsotropic ")
    size = traits.Float(desc="Isotropic voxel size to resample to", argstr="--size %f")
    b0Index = traits.Int(desc="Index in input vector index to extract", argstr="--b0Index %d")
    applyMeasurementFrame = traits.Bool(desc="Flag to apply the measurement frame to the gradient directions", argstr="--applyMeasurementFrame ")
    ignoreIndex = InputMultiPath(traits.Int, desc="Ignore diffusion gradient index. Used to remove specific gradient directions with artifacts.", sep=",", argstr="--ignoreIndex %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractTensorOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing the Tensor vector image", exists=True)


class gtractTensor(CommandLine):
    """title: Tensor Estimation

category: Diffusion.GTRACT

description: This step will convert a b-value averaged diffusion tensor image to a 3x3 tensor voxel image. This step takes the diffusion tensor image data and generates a tensor representation of the data based on the signal intensity decay, b values applied, and the diffusion difrections. The apparent diffusion coefficient for a given orientation is computed on a pixel-by-pixel basis by fitting the image data (voxel intensities) to the Stejskal-Tanner equation. If at least 6 diffusion directions are used, then the diffusion tensor can be computed. This program uses itk::DiffusionTensor3DReconstructionImageFilter. The user can adjust background threshold, median filter, and isotropic resampling.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractTensorInputSpec
    output_spec = gtractTensorOutputSpec
    _cmd = " gtractTensor "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractTensor, self)._format_arg(name, spec, value)



class gtractTransformToDeformationFieldInputSpec(CommandLineInputSpec):
    inputTransform = File(desc="Input Transform File Name", exists=True, argstr="--inputTransform %s")
    inputReferenceVolume = File(desc="Required: input image file name to exemplify the anatomical space over which to vcl_express the transform as a displacement field.", exists=True, argstr="--inputReferenceVolume %s")
    outputDeformationFieldVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Output deformation field", argstr="--outputDeformationFieldVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractTransformToDeformationFieldOutputSpec(TraitedSpec):
    outputDeformationFieldVolume = File(desc="Output deformation field", exists=True)


class gtractTransformToDeformationField(CommandLine):
    """title: Create Deformation Field

category: Diffusion.GTRACT

description: This program will compute forward deformation from the given Transform. The size of the DF is equal to MNI space

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta, Madhura Ingalhalikar, and Greg Harris

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractTransformToDeformationFieldInputSpec
    output_spec = gtractTransformToDeformationFieldOutputSpec
    _cmd = " gtractTransformToDeformationField "
    _outputs_filenames = {'outputDeformationFieldVolume':'outputDeformationFieldVolume.nii'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(gtractTransformToDeformationField, self)._format_arg(name, spec, value)
