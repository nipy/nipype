"""The ANTS module provides classes for interfacing with commands from the Advanced Normalization Tools module
--------
See the docstrings of the individual classes for examples.

"""

from glob import glob
import os
import warnings
from nipype.utils.filemanip import fname_presuffix, split_filename
from nipype.interfaces.base import CommandLineInputSpec, CommandLine, traits, TraitedSpec, File
from nipype.utils.misc import isdefined

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class MeasureImageSimilarityInputSpec(CommandLineInputSpec):
   image_dimension = traits.Enum('3', '2', argstr='%s', mandatory=True, position=1, usedefault=True
        desc='ImageDimension: 2 or 3 (for 2 or 3 Dimensional registration)')

   image_metric = traits.Enum('0', '1', '2', '3', argstr='%s', position=2, usedefault=True
        desc='Metric: 0 - MeanSquareDifference, 1 - Cross-Correlation, 2-Mutual Information , 3-SMI')

   image1 = File(exists=True, argstr='%s', mandatory=True, position=3,
        desc='The first of two images to compare')

   image2 = File(exists=True, argstr='%s', mandatory=True, position=4,
        desc='The second of two images to compare')

   log_file = File(exists=True, argstr='%s', position=5,
        desc='Optional logfile')

   output_image = File(exists=True, argstr='%s', position=6,
        desc='The output image filename (Not Implemented for Mutual Information yet)')

   target_value = traits.Float(argstr='%s', position=7,
        desc='target_value and epsilon_tolerance set goals for the metric value'\
        'If the metric value is within epsilon_tolerance of the target_value, then the test succeeds')

   epsilon_tolerance = traits.Float(argstr='%s', position=8,
        desc='target_value and epsilon_tolerance set goals for the metric value'\
        'If the metric value is within epsilon_tolerance of the target_value, then the test succeeds')

class MeasureImageSimilarityOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc='The output file')

class MeasureImageSimilarity(CommandLine):
    """ MeasureImageSimilarity
    """

    _cmd = 'MeasureImageSimilarity'
    input_spec=MeasureImageSimilarityInputSpec
    output_spec=MeasureImageSimilarityOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["output_image"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'output_image':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + "_MeasureSimilarity"

 class ImageMathInputSpec(CommandLineInputSpec):
     """
ImageMath ImageDimension  OutputImage.ext   Operator   Image1.ext   Image2.extOrFloat
  some options output text files
 The last two arguments can be an image or float value
 Valid Operators :
 m (multiply)  ,
   +  (add)  ,
   - (subtract)  ,
   / (divide)  ,
   ^ (power)  ,
 exp -- take exponent exp(imagevalue*value)
 addtozero
 overadd
 abs
 total -- sums up values in an image or in image1*image2 (img2 is the probability mask)
 Decision -- computes  result=1./(1.+exp(-1.0*( pix1-0.25)/pix2))
   Neg (Produce Image Negative ) ,
   G Image1.ext s  (Smooth with Gaussian of sigma = s )
 MD Image1.ext  s ( Morphological Dilation with radius s ) ,

 ME Image1.ext s ( Morphological Erosion with radius s ) ,

 MO Image1.ext s ( Morphological Opening with radius s )

 MC Image1.ext ( Morphological Closing with radius s )

  GD Image1.ext  s ( Grayscale Dilation with radius s ) ,

 GE Image1.ext s ( Grayscale Erosion with radius s ) ,

 GO Image1.ext s ( Grayscale Opening with radius s )

 GC Image1.ext ( Grayscale Closing with radius s )

 D (DistanceTransform) ,

 Segment Image1.ext N-Classes LocalityVsGlobalityWeight-In-ZeroToOneRange  OptionalPriorImages  ( Segment an Image  with option of Priors ,  weight 1 => maximally local/prior-based )

 Grad Image.ext S ( Gradient magnitude with sigma s -- if normalize, then output in range [0, 1] ) ,

 Laplacian Image.ext S normalize? ( laplacian computed with sigma s --  if normalize, then output in range [0, 1] ) ,

 Normalize image.ext opt ( Normalize to [0,1] option instead divides by average value )

 PH (Print Header) ,
   Byte ( Convert to Byte image in [0,255] )

  LabelStats labelimage.ext valueimage.nii ( compute volumes / masses of objects in a label image -- write to text file )

  ROIStatistics  LabelNames.txt labelimage.ext valueimage.nii  ( see the code )

 DiceAndMinDistSum  LabelImage1.ext LabelImage2.ext OptionalDistImage  -- outputs DiceAndMinDistSum and Dice Overlap to text log file + optional distance image

  Lipschitz   VectorFieldName  -- prints to cout  & writes to image

  InvId VectorFieldName  VectorFieldName   -- prints to cout  & writes to image

  GetLargestComponent InputImage {MinObjectSize}  -- get largest object in image

  ThresholdAtMean  Image  %ofMean

  FlattenImage  Image  %ofMax -- replaces values greater than %ofMax*Max to the value %ofMax*Max

  stack Image1.nii.gz Image2.nii.gz --- will put these 2 images in the same volume
  CorruptImage Image  NoiseLevel Smoothing
  TileImages NumColumns  ImageList*
  RemoveLabelInterfaces ImageIn
  EnumerateLabelInterfaces ImageIn ColoredImageOutname NeighborFractionToIgnore
  FitSphere GM-ImageIn {WM-Image} {MaxRad-Default=5}
  HistogramMatch SourceImage ReferenceImage {NumberBins-Default=255} {NumberPoints-Default=64}
  PadImage ImageIn Pad-Number ( if Pad-Number is negative, de-Padding occurs )
  Where Image ValueToLookFor maskImage-option tolerance --- the where function from IDL
  TensorFA DTImage
  TensorColor DTImage --- produces RGB values identifying principal directions
  TensorToVector DTImage WhichVec --- produces vector field identifying one of the principal directions, 2 = largest eigenvalue
  TensorToVectorComponent DTImage WhichVec --- 0 => 2 produces component of the principal vector field , i.e. largest eigenvalue.   3 = 8 => gets values from the tensor
  TensorIOTest DTImage --- will write the DT image back out ... tests I/O processes for consistency.
  MakeImage  SizeX  SizeY {SizeZ}
  SetOrGetPixel  ImageIn Get/Set-Value  IndexX  IndexY {IndexZ}  -- for example
  ImageMath 2 outimage.nii SetOrGetPixel Image  Get 24 34 -- gets the value at 24, 34
   ImageMath 2 outimage.nii SetOrGetPixel Image 1.e9  24 34  -- this sets 1.e9 as the value at 23 34
 you can also pass a boolean at the end to force the physical space to be used
  TensorMeanDiffusion DTImage
  CompareHeadersAndImages Image1 Image2 --- tries to find and fix header error! output is the repaired image with new header.  never use this if you trust your header information.
  CountVoxelDifference Image1 Image2 Mask --- the where function from IDL
  stack image1 image2  --- stack image2 onto image1
  CorrelationUpdate Image1 Image2  RegionRadius --- in voxels , Compute update that makes Image2  more like Image1
  ConvertImageToFile  imagevalues.nii {Optional-ImageMask.nii} -- will write voxel values to a file
  PValueImage  TValueImage  dof
  ConvertToGaussian  TValueImage  sigma-float
  ConvertImageSetToMatrix  rowcoloption Mask.nii  *images.nii --  each row/column contains image content extracted from mask applied to images in *img.nii
  ConvertVectorToImage   Mask.nii vector.nii  -- the vector contains image content extracted from a mask - here we return the vector to its spatial origins as image content
  TriPlanarView  ImageIn.nii.gz PercentageToClampLowIntensity  PercentageToClampHiIntensity x-slice y-slice z-slice
  TruncateImageIntensity inputImage  {lowerQuantile=0.05} {upperQuantile=0.95}  {numberOfBins=65}  {binary-maskImage}
  FillHoles Image parameter : parameter = ratio of edge at object to edge at background = 1 is a definite hole bounded by object only, 0.99 is close -- default of parameter > 1 will fill all holes
 PropagateLabelsThroughMask   speed/binaryimagemask.nii.gz   initiallabelimage.nii.gz Optional-Stopping-Value  -- final output is the propagated label image
 optional stopping value -- higher values allow more distant propagation
 FastMarchingSegmentation   speed/binaryimagemask.nii.gz   initiallabelimage.nii.gz Optional-Stopping-Value  -- final output is the propagated label image
 optional stopping value -- higher values allow more distant propagation
 ExtractSlice  volume.nii.gz slicetoextract --- will extract slice number from last dimension of volume (2,3,4) dimensions
 ConvertLandmarkFile  InFile.txt ---- will convert landmark file between formats.  see ants.pdf for description of formats.  e.g. ImageMath 3  outfile.vtk  ConvertLandmarkFile  infile.txt
 """
   image_dimension = traits.Enum('3', '2', argstr='%s', mandatory=True, position=1, usedefault=True
        desc='ImageDimension: 2 or 3 (for 2 or 3 Dimensional registration)')

   operator = traits.Enum('+', '-', argstr='%s', mandatory=True, position=2, usedefault=True
        desc='Operator')

   output_image = File(exists=True, argstr='%s', position=2,
        desc='The output image filename')

   image1 = File(exists=True, argstr='%s', mandatory=True, position=4,
        desc='The first of two images to compare')

   image2 = File(exists=True, argstr='%s', mandatory=True, position=5,
        desc='The second of two images to compare')

class ImageMathOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc='The output file')

class ImageMath(CommandLine):
    """ MeasureImageSimilarity
    """

    _cmd = 'ImageMath'
    input_spec=ImageMathInputSpec
    output_spec=ImageMathOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["output_image"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'output_image':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + "_ImageMath"
