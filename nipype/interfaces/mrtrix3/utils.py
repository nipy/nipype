# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# -*- coding: utf-8 -*-

import os.path as op

from ...utils.filemanip import split_filename
from ..base import (
    CommandLineInputSpec,
    CommandLine,
    traits,
    TraitedSpec,
    File,
    InputMultiPath,
    isdefined,
)
from .base import MRTrix3BaseInputSpec, MRTrix3Base


class BrainMaskInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="input diffusion weighted images",
    )
    out_file = File(
        "brainmask.mif",
        argstr="%s",
        mandatory=True,
        position=-1,
        usedefault=True,
        desc="output brain mask",
    )


class BrainMaskOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output response file")


class BrainMask(CommandLine):
    """
    Convert a mesh surface to a partial volume estimation image


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> bmsk = mrt.BrainMask()
    >>> bmsk.inputs.in_file = 'dwi.mif'
    >>> bmsk.cmdline                               # doctest: +ELLIPSIS
    'dwi2mask dwi.mif brainmask.mif'
    >>> bmsk.run()                                 # doctest: +SKIP
    """

    _cmd = "dwi2mask"
    input_spec = BrainMaskInputSpec
    output_spec = BrainMaskOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs


class MRCatInputSpec(MRTrix3BaseInputSpec):
    in_files = traits.List(
        File(exists=True),
        argstr="%s",
        position=-2,
        mandatory=True,
        desc="files to concatenate",
    )

    out_file = File(
        "concatenated.mif",
        argstr="%s",
        mandatory=True,
        position=-1,
        usedefault=True,
        desc="output concatenated image",
    )

    axis = traits.Int(
        argstr="-axis %s",
        desc="""specify axis along which concatenation should be performed. By default,
     the program will use the last non-singleton, non-spatial axis of any of
     the input images - in other words axis 3 or whichever axis (greater than
     3) of the input images has size greater than one""",
    )

    datatype = traits.Enum(
        "float32",
        "float32le",
        "float32be",
        "float64",
        "float64le",
        "float64be",
        "int64",
        "uint64",
        "int64le",
        "uint64le",
        "int64be",
        "uint64be",
        "int32",
        "uint32",
        "int32le",
        "uint32le",
        "int32be",
        "uint32be",
        "int16",
        "uint16",
        "int16le",
        "uint16le",
        "int16be",
        "uint16be",
        "cfloat32",
        "cfloat32le",
        "cfloat32be",
        "cfloat64",
        "cfloat64le",
        "cfloat64be",
        "int8",
        "uint8",
        "bit",
        argstr="-datatype %s",
        desc="specify output image data type",
    )


class MRCatOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output concatenated image")


class MRCat(CommandLine):
    """
    Concatenate several images into one


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> mrcat = mrt.MRCat()
    >>> mrcat.inputs.in_files = ['dwi.mif','mask.mif']
    >>> mrcat.cmdline                               # doctest: +ELLIPSIS
    'mrcat dwi.mif mask.mif concatenated.mif'
    >>> mrcat.run()                                 # doctest: +SKIP
    """

    _cmd = "mrcat"
    input_spec = MRCatInputSpec
    output_spec = MRCatOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs


class Mesh2PVEInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True, argstr="%s", mandatory=True, position=-3, desc="input mesh"
    )
    reference = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="input reference image",
    )
    in_first = File(
        exists=True,
        argstr="-first %s",
        desc="indicates that the mesh file is provided by FSL FIRST",
    )

    out_file = File(
        "mesh2volume.nii.gz",
        argstr="%s",
        mandatory=True,
        position=-1,
        usedefault=True,
        desc="output file containing SH coefficients",
    )


class Mesh2PVEOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output response file")


class Mesh2PVE(CommandLine):
    """
    Convert a mesh surface to a partial volume estimation image


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> m2p = mrt.Mesh2PVE()
    >>> m2p.inputs.in_file = 'surf1.vtk'
    >>> m2p.inputs.reference = 'dwi.mif'
    >>> m2p.inputs.in_first = 'T1.nii.gz'
    >>> m2p.cmdline                               # doctest: +ELLIPSIS
    'mesh2pve -first T1.nii.gz surf1.vtk dwi.mif mesh2volume.nii.gz'
    >>> m2p.run()                                 # doctest: +SKIP
    """

    _cmd = "mesh2pve"
    input_spec = Mesh2PVEInputSpec
    output_spec = Mesh2PVEOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs


class Generate5ttInputSpec(MRTrix3BaseInputSpec):
    algorithm = traits.Enum(
        "fsl",
        "gif",
        "freesurfer",
        argstr="%s",
        position=-3,
        mandatory=True,
        desc="tissue segmentation algorithm",
    )
    in_file = File(
        exists=True, argstr="%s", mandatory=True, position=-2, desc="input image"
    )
    out_file = File(argstr="%s", mandatory=True, position=-1, desc="output image")


class Generate5ttOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output image")


class Generate5tt(MRTrix3Base):
    """
    Generate a 5TT image suitable for ACT using the selected algorithm


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> gen5tt = mrt.Generate5tt()
    >>> gen5tt.inputs.in_file = 'T1.nii.gz'
    >>> gen5tt.inputs.algorithm = 'fsl'
    >>> gen5tt.inputs.out_file = '5tt.mif'
    >>> gen5tt.cmdline                             # doctest: +ELLIPSIS
    '5ttgen fsl T1.nii.gz 5tt.mif'
    >>> gen5tt.run()                               # doctest: +SKIP
    """

    _cmd = "5ttgen"
    input_spec = Generate5ttInputSpec
    output_spec = Generate5ttOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs


class TensorMetricsInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-1,
        desc="input DTI image",
    )

    out_fa = File(argstr="-fa %s", desc="output FA file")
    out_adc = File(argstr="-adc %s", desc="output ADC file")
    out_ad = File(argstr="-ad %s", desc="output AD file")
    out_rd = File(argstr="-rd %s", desc="output RD file")
    out_cl = File(argstr="-cl %s", desc="output CL file")
    out_cp = File(argstr="-cp %s", desc="output CP file")
    out_cs = File(argstr="-cs %s", desc="output CS file")
    out_evec = File(argstr="-vector %s", desc="output selected eigenvector(s) file")
    out_eval = File(argstr="-value %s", desc="output selected eigenvalue(s) file")
    component = traits.List(
        [1],
        usedefault=True,
        argstr="-num %s",
        sep=",",
        desc=(
            "specify the desired eigenvalue/eigenvector(s). Note that "
            "several eigenvalues can be specified as a number sequence"
        ),
    )
    in_mask = File(
        exists=True,
        argstr="-mask %s",
        desc=(
            "only perform computation within the specified binary" " brain mask image"
        ),
    )
    modulate = traits.Enum(
        "FA",
        "none",
        "eval",
        argstr="-modulate %s",
        desc=("how to modulate the magnitude of the" " eigenvectors"),
    )


class TensorMetricsOutputSpec(TraitedSpec):
    out_fa = File(desc="output FA file")
    out_adc = File(desc="output ADC file")
    out_ad = File(desc="output AD file")
    out_rd = File(desc="output RD file")
    out_cl = File(desc="output CL file")
    out_cp = File(desc="output CP file")
    out_cs = File(desc="output CS file")
    out_evec = File(desc="output selected eigenvector(s) file")
    out_eval = File(desc="output selected eigenvalue(s) file")


class TensorMetrics(CommandLine):
    """
    Compute metrics from tensors


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> comp = mrt.TensorMetrics()
    >>> comp.inputs.in_file = 'dti.mif'
    >>> comp.inputs.out_fa = 'fa.mif'
    >>> comp.cmdline                               # doctest: +ELLIPSIS
    'tensor2metric -num 1 -fa fa.mif dti.mif'
    >>> comp.run()                                 # doctest: +SKIP
    """

    _cmd = "tensor2metric"
    input_spec = TensorMetricsInputSpec
    output_spec = TensorMetricsOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()

        for k in list(outputs.keys()):
            if isdefined(getattr(self.inputs, k)):
                outputs[k] = op.abspath(getattr(self.inputs, k))

        return outputs


class ComputeTDIInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True, argstr="%s", mandatory=True, position=-2, desc="input tractography"
    )
    out_file = File(
        "tdi.mif", argstr="%s", usedefault=True, position=-1, desc="output TDI file"
    )
    reference = File(
        exists=True,
        argstr="-template %s",
        desc="a reference" "image to be used as template",
    )
    vox_size = traits.List(
        traits.Int, argstr="-vox %s", sep=",", desc="voxel dimensions"
    )
    data_type = traits.Enum(
        "float",
        "unsigned int",
        argstr="-datatype %s",
        desc="specify output image data type",
    )
    use_dec = traits.Bool(argstr="-dec", desc="perform mapping in DEC space")
    dixel = File(
        argstr="-dixel %s",
        desc="map streamlines to"
        "dixels within each voxel. Directions are stored as"
        "azimuth elevation pairs.",
    )
    max_tod = traits.Int(
        argstr="-tod %d",
        desc="generate a Track Orientation " "Distribution (TOD) in each voxel.",
    )

    contrast = traits.Enum(
        "tdi",
        "length",
        "invlength",
        "scalar_map",
        "scalar_map_conut",
        "fod_amp",
        "curvature",
        argstr="-constrast %s",
        desc="define the desired " "form of contrast for the output image",
    )
    in_map = File(
        exists=True,
        argstr="-image %s",
        desc="provide the"
        "scalar image map for generating images with "
        "'scalar_map' contrasts, or the SHs image for fod_amp",
    )

    stat_vox = traits.Enum(
        "sum",
        "min",
        "mean",
        "max",
        argstr="-stat_vox %s",
        desc="define the statistic for choosing the final"
        "voxel intesities for a given contrast",
    )
    stat_tck = traits.Enum(
        "mean",
        "sum",
        "min",
        "max",
        "median",
        "mean_nonzero",
        "gaussian",
        "ends_min",
        "ends_mean",
        "ends_max",
        "ends_prod",
        argstr="-stat_tck %s",
        desc="define the statistic for choosing "
        "the contribution to be made by each streamline as a function of"
        " the samples taken along their lengths.",
    )

    fwhm_tck = traits.Float(
        argstr="-fwhm_tck %f",
        desc="define the statistic for choosing the"
        " contribution to be made by each streamline as a function of the "
        "samples taken along their lengths",
    )

    map_zero = traits.Bool(
        argstr="-map_zero",
        desc="if a streamline has zero contribution based "
        "on the contrast & statistic, typically it is not mapped; use this "
        "option to still contribute to the map even if this is the case "
        "(these non-contributing voxels can then influence the mean value in "
        "each voxel of the map)",
    )

    upsample = traits.Int(
        argstr="-upsample %d",
        desc="upsample the tracks by"
        " some ratio using Hermite interpolation before "
        "mapping",
    )

    precise = traits.Bool(
        argstr="-precise",
        desc="use a more precise streamline mapping "
        "strategy, that accurately quantifies the length through each voxel "
        "(these lengths are then taken into account during TWI calculation)",
    )
    ends_only = traits.Bool(
        argstr="-ends_only", desc="only map the streamline" " endpoints to the image"
    )

    tck_weights = File(
        exists=True,
        argstr="-tck_weights_in %s",
        desc="specify" " a text scalar file containing the streamline weights",
    )
    nthreads = traits.Int(
        argstr="-nthreads %d",
        desc="number of threads. if zero, the number" " of available cpus will be used",
        nohash=True,
    )


class ComputeTDIOutputSpec(TraitedSpec):
    out_file = File(desc="output TDI file")


class ComputeTDI(MRTrix3Base):
    """
    Use track data as a form of contrast for producing a high-resolution
    image.

    .. admonition:: References

      * For TDI or DEC TDI: Calamante, F.; Tournier, J.-D.; Jackson, G. D. &
        Connelly, A. Track-density imaging (TDI): Super-resolution white
        matter imaging using whole-brain track-density mapping. NeuroImage,
        2010, 53, 1233-1243

      * If using -contrast length and -stat_vox mean: Pannek, K.; Mathias,
        J. L.; Bigler, E. D.; Brown, G.; Taylor, J. D. & Rose, S. E. The
        average pathlength map: A diffusion MRI tractography-derived index
        for studying brain pathology. NeuroImage, 2011, 55, 133-141

      * If using -dixel option with TDI contrast only: Smith, R.E., Tournier,
        J-D., Calamante, F., Connelly, A. A novel paradigm for automated
        segmentation of very large whole-brain probabilistic tractography
        data sets. In proc. ISMRM, 2011, 19, 673

      * If using -dixel option with any other contrast: Pannek, K., Raffelt,
        D., Salvado, O., Rose, S. Incorporating directional information in
        diffusion tractography derived maps: angular track imaging (ATI).
        In Proc. ISMRM, 2012, 20, 1912

      * If using -tod option: Dhollander, T., Emsell, L., Van Hecke, W., Maes,
        F., Sunaert, S., Suetens, P. Track Orientation Density Imaging (TODI)
        and Track Orientation Distribution (TOD) based tractography.
        NeuroImage, 2014, 94, 312-336

      * If using other contrasts / statistics: Calamante, F.; Tournier, J.-D.;
        Smith, R. E. & Connelly, A. A generalised framework for
        super-resolution track-weighted imaging. NeuroImage, 2012, 59,
        2494-2503

      * If using -precise mapping option: Smith, R. E.; Tournier, J.-D.;
        Calamante, F. & Connelly, A. SIFT: Spherical-deconvolution informed
        filtering of tractograms. NeuroImage, 2013, 67, 298-312 (Appendix 3)



    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> tdi = mrt.ComputeTDI()
    >>> tdi.inputs.in_file = 'dti.mif'
    >>> tdi.cmdline                               # doctest: +ELLIPSIS
    'tckmap dti.mif tdi.mif'
    >>> tdi.run()                                 # doctest: +SKIP
    """

    _cmd = "tckmap"
    input_spec = ComputeTDIInputSpec
    output_spec = ComputeTDIOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs


class TCK2VTKInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True, argstr="%s", mandatory=True, position=-2, desc="input tractography"
    )
    out_file = File(
        "tracks.vtk", argstr="%s", usedefault=True, position=-1, desc="output VTK file"
    )
    reference = File(
        exists=True,
        argstr="-image %s",
        desc="if specified, the properties of"
        " this image will be used to convert track point positions from real "
        "(scanner) coordinates into image coordinates (in mm).",
    )
    voxel = File(
        exists=True,
        argstr="-image %s",
        desc="if specified, the properties of"
        " this image will be used to convert track point positions from real "
        "(scanner) coordinates into image coordinates.",
    )

    nthreads = traits.Int(
        argstr="-nthreads %d",
        desc="number of threads. if zero, the number" " of available cpus will be used",
        nohash=True,
    )


class TCK2VTKOutputSpec(TraitedSpec):
    out_file = File(desc="output VTK file")


class TCK2VTK(MRTrix3Base):
    """
    Convert a track file to a vtk format, cave: coordinates are in XYZ
    coordinates not reference

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> vtk = mrt.TCK2VTK()
    >>> vtk.inputs.in_file = 'tracks.tck'
    >>> vtk.inputs.reference = 'b0.nii'
    >>> vtk.cmdline                               # doctest: +ELLIPSIS
    'tck2vtk -image b0.nii tracks.tck tracks.vtk'
    >>> vtk.run()                                 # doctest: +SKIP
    """

    _cmd = "tck2vtk"
    input_spec = TCK2VTKInputSpec
    output_spec = TCK2VTKOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs


class DWIExtractInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True, argstr="%s", mandatory=True, position=-2, desc="input image"
    )
    out_file = File(argstr="%s", mandatory=True, position=-1, desc="output image")
    bzero = traits.Bool(argstr="-bzero", desc="extract b=0 volumes")
    nobzero = traits.Bool(argstr="-no_bzero", desc="extract non b=0 volumes")
    singleshell = traits.Bool(
        argstr="-singleshell", desc="extract volumes with a specific shell"
    )
    shell = traits.List(
        traits.Float,
        sep=",",
        argstr="-shell %s",
        desc="specify one or more gradient shells",
    )


class DWIExtractOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output image")


class DWIExtract(MRTrix3Base):
    """
    Extract diffusion-weighted volumes, b=0 volumes, or certain shells from a
    DWI dataset

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> dwiextract = mrt.DWIExtract()
    >>> dwiextract.inputs.in_file = 'dwi.mif'
    >>> dwiextract.inputs.bzero = True
    >>> dwiextract.inputs.out_file = 'b0vols.mif'
    >>> dwiextract.inputs.grad_fsl = ('bvecs', 'bvals')
    >>> dwiextract.cmdline                             # doctest: +ELLIPSIS
    'dwiextract -bzero -fslgrad bvecs bvals dwi.mif b0vols.mif'
    >>> dwiextract.run()                               # doctest: +SKIP
    """

    _cmd = "dwiextract"
    input_spec = DWIExtractInputSpec
    output_spec = DWIExtractOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs


class MRConvertInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True, argstr="%s", mandatory=True, position=-2, desc="input image"
    )
    out_file = File(
        "dwi.mif",
        argstr="%s",
        mandatory=True,
        position=-1,
        usedefault=True,
        desc="output image",
    )
    coord = traits.List(
        traits.Int,
        sep=" ",
        argstr="-coord %s",
        desc="extract data at the specified coordinates",
    )
    vox = traits.List(
        traits.Float, sep=",", argstr="-vox %s", desc="change the voxel dimensions"
    )
    axes = traits.List(
        traits.Int,
        sep=",",
        argstr="-axes %s",
        desc="specify the axes that will be used",
    )
    scaling = traits.List(
        traits.Float,
        sep=",",
        argstr="-scaling %s",
        desc="specify the data scaling parameter",
    )
    json_import = File(
        exists=True,
        argstr="-json_import %s",
        mandatory=False,
        desc="import data from a JSON file into header key-value pairs",
    )
    json_export = File(
        exists=False,
        argstr="-json_export %s",
        mandatory=False,
        desc="export data from an image header key-value pairs into a JSON file",
    )


class MRConvertOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output image")
    json_export = File(
        exists=True,
        desc="exported data from an image header key-value pairs in a JSON file",
    )
    out_bvec = File(exists=True, desc="export bvec file in FSL format")
    out_bval = File(exists=True, desc="export bvec file in FSL format")


class MRConvert(MRTrix3Base):
    """
    Perform conversion between different file types and optionally extract a
    subset of the input image

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> mrconvert = mrt.MRConvert()
    >>> mrconvert.inputs.in_file = 'dwi.nii.gz'
    >>> mrconvert.inputs.grad_fsl = ('bvecs', 'bvals')
    >>> mrconvert.cmdline                             # doctest: +ELLIPSIS
    'mrconvert -fslgrad bvecs bvals dwi.nii.gz dwi.mif'
    >>> mrconvert.run()                               # doctest: +SKIP
    """

    _cmd = "mrconvert"
    input_spec = MRConvertInputSpec
    output_spec = MRConvertOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        if self.inputs.json_export:
            outputs["json_export"] = op.abspath(self.inputs.json_export)
        if self.inputs.out_bvec:
            outputs["out_bvec"] = op.abspath(self.inputs.out_bvec)
        if self.inputs.out_bval:
            outputs["out_bval"] = op.abspath(self.inputs.out_bval)
        return outputs


class TransformFSLConvertInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=1,
        desc="FLIRT input image",
    )
    reference = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=2,
        desc="FLIRT reference image",
    )
    in_transform = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=0,
        desc="FLIRT output transformation matrix",
    )
    out_transform = File(
        "transform_mrtrix.txt",
        argstr="%s",
        mandatory=True,
        position=-1,
        usedefault=True,
        desc="output transformed affine in mrtrix3's format",
    )
    flirt_import = traits.Bool(
        True,
        argstr="flirt_import",
        mandatory=True,
        usedefault=True,
        position=-2,
        desc="import transform from FSL's FLIRT.",
    )


class TransformFSLConvertOutputSpec(TraitedSpec):
    out_transform = File(
        exists=True, desc="output transformed affine in mrtrix3's format"
    )


class TransformFSLConvert(MRTrix3Base):
    """
    Perform conversion between FSL's transformation matrix format to mrtrix3's.
    """

    _cmd = "transformconvert"
    input_spec = TransformFSLConvertInputSpec
    output_spec = TransformFSLConvertOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_transform"] = op.abspath(self.inputs.out_transform)
        return outputs


class MRTransformInputSpec(MRTrix3BaseInputSpec):
    in_files = InputMultiPath(
        File(exists=True),
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="Input images to be transformed",
    )
    out_file = File(
        genfile=True,
        argstr="%s",
        position=-1,
        desc="Output image",
    )
    invert = traits.Bool(
        argstr="-inverse",
        position=1,
        desc="Invert the specified transform before using it",
    )
    linear_transform = File(
        exists=True,
        argstr="-linear %s",
        position=1,
        desc=(
            "Specify a linear transform to apply, in the form of a 3x4 or 4x4 ascii file. "
            "Note the standard reverse convention is used, "
            "where the transform maps points in the template image to the moving image. "
            "Note that the reverse convention is still assumed even if no -template image is supplied."
        ),
    )
    replace_transform = traits.Bool(
        argstr="-replace",
        position=1,
        desc="replace the current transform by that specified, rather than applying it to the current transform",
    )
    transformation_file = File(
        exists=True,
        argstr="-transform %s",
        position=1,
        desc="The transform to apply, in the form of a 4x4 ascii file.",
    )
    template_image = File(
        exists=True,
        argstr="-template %s",
        position=1,
        desc="Reslice the input image to match the specified template image.",
    )
    reference_image = File(
        exists=True,
        argstr="-reference %s",
        position=1,
        desc="in case the transform supplied maps from the input image onto a reference image, use this option to specify the reference. Note that this implicitly sets the -replace option.",
    )
    flip_x = traits.Bool(
        argstr="-flipx",
        position=1,
        desc="assume the transform is supplied assuming a coordinate system with the x-axis reversed relative to the MRtrix convention (i.e. x increases from right to left). This is required to handle transform matrices produced by FSL's FLIRT command. This is only used in conjunction with the -reference option.",
    )
    quiet = traits.Bool(
        argstr="-quiet",
        position=1,
        desc="Do not display information messages or progress status.",
    )
    debug = traits.Bool(argstr="-debug", position=1, desc="Display debugging messages.")


class MRTransformOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output image of the transformation")


class MRTransform(MRTrix3Base):
    """
    Apply spatial transformations or reslice images

    Example
    -------

    >>> MRxform = MRTransform()
    >>> MRxform.inputs.in_files = 'anat_coreg.mif'
    >>> MRxform.run()                                   # doctest: +SKIP
    """

    _cmd = "mrtransform"
    input_spec = MRTransformInputSpec
    output_spec = MRTransformOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = self.inputs.out_file
        if not isdefined(outputs["out_file"]):
            outputs["out_file"] = op.abspath(self._gen_outfilename())
        else:
            outputs["out_file"] = op.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_files[0])
        return name + "_MRTransform.mif"


class MRMathInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True, argstr="%s", mandatory=True, position=-3, desc="input image"
    )
    out_file = File(argstr="%s", mandatory=True, position=-1, desc="output image")
    operation = traits.Enum(
        "mean",
        "median",
        "sum",
        "product",
        "rms",
        "norm",
        "var",
        "std",
        "min",
        "max",
        "absmax",
        "magmax",
        argstr="%s",
        position=-2,
        mandatory=True,
        desc="operation to computer along a specified axis",
    )
    axis = traits.Int(
        0, argstr="-axis %d", desc="specified axis to perform the operation along"
    )


class MRMathOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output image")


class MRMath(MRTrix3Base):
    """
    Compute summary statistic on image intensities
    along a specified axis of a single image

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> mrmath = mrt.MRMath()
    >>> mrmath.inputs.in_file = 'dwi.mif'
    >>> mrmath.inputs.operation = 'mean'
    >>> mrmath.inputs.axis = 3
    >>> mrmath.inputs.out_file = 'dwi_mean.mif'
    >>> mrmath.inputs.grad_fsl = ('bvecs', 'bvals')
    >>> mrmath.cmdline                             # doctest: +ELLIPSIS
    'mrmath -axis 3 -fslgrad bvecs bvals dwi.mif mean dwi_mean.mif'
    >>> mrmath.run()                               # doctest: +SKIP
    """

    _cmd = "mrmath"
    input_spec = MRMathInputSpec
    output_spec = MRMathOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs


class MRResizeInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True, argstr="%s", position=-2, mandatory=True, desc="input DWI image"
    )
    image_size = traits.Tuple(
        (traits.Int, traits.Int, traits.Int),
        argstr="-size %d,%d,%d",
        mandatory=True,
        desc="Number of voxels in each dimension of output image",
        xor=["voxel_size", "scale_factor"],
    )
    voxel_size = traits.Tuple(
        (traits.Float, traits.Float, traits.Float),
        argstr="-voxel %g,%g,%g",
        mandatory=True,
        desc="Desired voxel size in mm for the output image",
        xor=["image_size", "scale_factor"],
    )
    scale_factor = traits.Tuple(
        (traits.Float, traits.Float, traits.Float),
        argstr="-scale %g,%g,%g",
        mandatory=True,
        desc="Scale factors to rescale the image by in each dimension",
        xor=["image_size", "voxel_size"],
    )
    interpolation = traits.Enum(
        "cubic",
        "nearest",
        "linear",
        "sinc",
        argstr="-interp %s",
        usedefault=True,
        desc="set the interpolation method to use when resizing (choices: "
        "nearest, linear, cubic, sinc. Default: cubic).",
    )
    out_file = File(
        argstr="%s",
        name_template="%s_resized",
        name_source=["in_file"],
        keep_extension=True,
        position=-1,
        desc="the output resized DWI image",
    )


class MRResizeOutputSpec(TraitedSpec):
    out_file = File(desc="the output resized DWI image", exists=True)


class MRResize(MRTrix3Base):
    """
    Resize an image by defining the new image resolution, voxel size or a
    scale factor. If the image is 4D, then only the first 3 dimensions can be
    resized. Also, if the image is down-sampled, the appropriate smoothing is
    automatically applied using Gaussian smoothing.
    For more information, see
    <https://mrtrix.readthedocs.io/en/latest/reference/commands/mrresize.html>

    Example
    -------
    >>> import nipype.interfaces.mrtrix3 as mrt

    Defining the new image resolution:
    >>> image_resize = mrt.MRResize()
    >>> image_resize.inputs.in_file = 'dwi.mif'
    >>> image_resize.inputs.image_size = (256, 256, 144)
    >>> image_resize.cmdline                               # doctest: +ELLIPSIS
    'mrresize -size 256,256,144 -interp cubic dwi.mif dwi_resized.mif'
    >>> image_resize.run()                                 # doctest: +SKIP

    Defining the new image's voxel size:
    >>> voxel_resize = mrt.MRResize()
    >>> voxel_resize.inputs.in_file = 'dwi.mif'
    >>> voxel_resize.inputs.voxel_size = (1, 1, 1)
    >>> voxel_resize.cmdline                               # doctest: +ELLIPSIS
    'mrresize -interp cubic -voxel 1,1,1 dwi.mif dwi_resized.mif'
    >>> voxel_resize.run()                                 # doctest: +SKIP

    Defining the scale factor of each image dimension:
    >>> scale_resize = mrt.MRResize()
    >>> scale_resize.inputs.in_file = 'dwi.mif'
    >>> scale_resize.inputs.scale_factor = (0.5,0.5,0.5)
    >>> scale_resize.cmdline                               # doctest: +ELLIPSIS
    'mrresize -interp cubic -scale 0.5,0.5,0.5 dwi.mif dwi_resized.mif'
    >>> scale_resize.run()                                 # doctest: +SKIP
    """

    _cmd = "mrresize"
    input_spec = MRResizeInputSpec
    output_spec = MRResizeOutputSpec


class SHConvInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-3,
        desc="input ODF image",
    )
    # General options
    response = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-2,
        desc=("The response function"),
    )
    out_file = File(
        name_template="%s_shconv.mif",
        name_source=["in_file"],
        argstr="%s",
        position=-1,
        usedefault=True,
        desc="the output spherical harmonics",
    )


class SHConvOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output convoluted spherical harmonics file")


class SHConv(CommandLine):
    """
    Convolve spherical harmonics with a tissue response function. Useful for
    checking residuals of ODF estimates.


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> sh = mrt.SHConv()
    >>> sh.inputs.in_file = 'csd.mif'
    >>> sh.inputs.response = 'response.txt'
    >>> sh.cmdline
    'shconv csd.mif response.txt csd_shconv.mif'
    >>> sh.run()                                 # doctest: +SKIP
    """

    _cmd = "shconv"
    input_spec = SHConvInputSpec
    output_spec = SHConvOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs


class SH2AmpInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-3,
        desc="input ODF image",
    )
    # General options
    directions = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=-2,
        desc=(
            "The gradient directions along which to sample the spherical "
            "harmonics MRtrix format"
        ),
    )
    out_file = File(
        name_template="%s_amp.mif",
        name_source=["in_file"],
        argstr="%s",
        position=-1,
        usedefault=True,
        desc="the output spherical harmonics",
    )
    nonnegative = traits.Bool(
        argstr="-nonnegative", desc="cap all negative amplitudes to zero"
    )


class SH2AmpOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output convoluted spherical harmonics file")


class SH2Amp(CommandLine):
    """
    Sample spherical harmonics on a set of gradient orientations.  Useful for
    checking residuals of ODF estimates.


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> sh = mrt.SH2Amp()
    >>> sh.inputs.in_file = 'sh.mif'
    >>> sh.inputs.directions = 'grads.txt'
    >>> sh.cmdline
    'sh2amp sh.mif grads.txt sh_amp.mif'
    >>> sh.run()                                 # doctest: +SKIP
    """

    _cmd = "sh2amp"
    input_spec = SH2AmpInputSpec
    output_spec = SH2AmpOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = op.abspath(self.inputs.out_file)
        return outputs
