# -*- coding: utf-8 -*-

import os
import glob

from ...utils.filemanip import split_filename
from ..base import (
    CommandLineInputSpec,
    CommandLine,
    traits,
    TraitedSpec,
    File,
    StdOutCommandLine,
    OutputMultiPath,
    StdOutCommandLineInputSpec,
    isdefined,
)


class Image2VoxelInputSpec(StdOutCommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="-4dimage %s",
        mandatory=True,
        position=1,
        desc="4d image file",
    )
    # TODO convert list of files on the fly
    #    imagelist = File(exists=True, argstr='-imagelist %s',
    #                    mandatory=True, position=1,
    #                    desc='Name of a file containing a list of 3D images')
    #
    #    imageprefix = traits.Str(argstr='-imageprefix %s', position=3,
    #                    desc='Path to prepend onto filenames in the imagelist.')

    out_type = traits.Enum(
        "float",
        "char",
        "short",
        "int",
        "long",
        "double",
        argstr="-outputdatatype %s",
        position=2,
        desc='"i.e. Bfloat". Can be "char", "short", "int", "long", "float" or "double"',
        usedefault=True,
    )


class Image2VoxelOutputSpec(TraitedSpec):
    voxel_order = File(exists=True, desc="path/name of 4D volume in voxel order")


class Image2Voxel(StdOutCommandLine):
    """
    Converts Analyze / NIFTI / MHA files to voxel order.

    Converts scanner-order data in a supported image format to voxel-order data.
    Either takes a 4D file (all measurements in single image)
    or a list of 3D images.

    Examples
    --------

    >>> import nipype.interfaces.camino as cmon
    >>> img2vox = cmon.Image2Voxel()
    >>> img2vox.inputs.in_file = '4d_dwi.nii'
    >>> img2vox.run()                  # doctest: +SKIP
    """

    _cmd = "image2voxel"
    input_spec = Image2VoxelInputSpec
    output_spec = Image2VoxelOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["voxel_order"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + ".B" + self.inputs.out_type


class FSL2SchemeInputSpec(StdOutCommandLineInputSpec):
    bvec_file = File(
        exists=True,
        argstr="-bvecfile %s",
        mandatory=True,
        position=1,
        desc="b vector file",
    )

    bval_file = File(
        exists=True,
        argstr="-bvalfile %s",
        mandatory=True,
        position=2,
        desc="b value file",
    )

    numscans = traits.Int(
        argstr="-numscans %d",
        units="NA",
        desc="Output all measurements numerous (n) times, used when combining multiple scans from the same imaging session.",
    )

    interleave = traits.Bool(
        argstr="-interleave",
        desc="Interleave repeated scans. Only used with -numscans.",
    )

    bscale = traits.Float(
        argstr="-bscale %d",
        units="NA",
        desc="Scaling factor to convert the b-values into different units. Default is 10^6.",
    )

    diffusiontime = traits.Float(
        argstr="-diffusiontime %f", units="NA", desc="Diffusion time"
    )

    flipx = traits.Bool(
        argstr="-flipx", desc="Negate the x component of all the vectors."
    )
    flipy = traits.Bool(
        argstr="-flipy", desc="Negate the y component of all the vectors."
    )
    flipz = traits.Bool(
        argstr="-flipz", desc="Negate the z component of all the vectors."
    )
    usegradmod = traits.Bool(
        argstr="-usegradmod",
        desc="Use the gradient magnitude to scale b. This option has no effect if your gradient directions have unit magnitude.",
    )


class FSL2SchemeOutputSpec(TraitedSpec):
    scheme = File(exists=True, desc="Scheme file")


class FSL2Scheme(StdOutCommandLine):
    """
    Converts b-vectors and b-values from FSL format to a Camino scheme file.

    Examples
    --------

    >>> import nipype.interfaces.camino as cmon
    >>> makescheme = cmon.FSL2Scheme()
    >>> makescheme.inputs.bvec_file = 'bvecs'
    >>> makescheme.inputs.bvec_file = 'bvals'
    >>> makescheme.run()                  # doctest: +SKIP

    """

    _cmd = "fsl2scheme"
    input_spec = FSL2SchemeInputSpec
    output_spec = FSL2SchemeOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["scheme"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.bvec_file)
        return name + ".scheme"


class VtkStreamlinesInputSpec(StdOutCommandLineInputSpec):
    inputmodel = traits.Enum(
        "raw",
        "voxels",
        argstr="-inputmodel %s",
        desc="input model type (raw or voxels)",
        usedefault=True,
    )

    in_file = File(
        exists=True, argstr=" < %s", mandatory=True, position=-2, desc="data file"
    )

    voxeldims = traits.List(
        traits.Int,
        desc="voxel dimensions in mm",
        argstr="-voxeldims %s",
        minlen=3,
        maxlen=3,
        position=4,
        units="mm",
    )

    seed_file = File(
        exists=False,
        argstr="-seedfile %s",
        position=1,
        desc="image containing seed points",
    )

    target_file = File(
        exists=False,
        argstr="-targetfile %s",
        position=2,
        desc="image containing integer-valued target regions",
    )

    scalar_file = File(
        exists=False,
        argstr="-scalarfile %s",
        position=3,
        desc="image that is in the same physical space as the tracts",
    )

    colourorient = traits.Bool(
        argstr="-colourorient",
        desc="Each point on the streamline is coloured by the local orientation.",
    )
    interpolatescalars = traits.Bool(
        argstr="-interpolatescalars",
        desc="the scalar value at each point on the streamline is calculated by trilinear interpolation",
    )
    interpolate = traits.Bool(
        argstr="-interpolate",
        desc="the scalar value at each point on the streamline is calculated by trilinear interpolation",
    )


class VtkStreamlinesOutputSpec(TraitedSpec):
    vtk = File(exists=True, desc="Streamlines in VTK format")


class VtkStreamlines(StdOutCommandLine):
    """
    Use vtkstreamlines to convert raw or voxel format streamlines to VTK polydata

    Examples
    --------

    >>> import nipype.interfaces.camino as cmon
    >>> vtk = cmon.VtkStreamlines()
    >>> vtk.inputs.in_file = 'tract_data.Bfloat'
    >>> vtk.inputs.voxeldims = [1,1,1]
    >>> vtk.run()                  # doctest: +SKIP
    """

    _cmd = "vtkstreamlines"
    input_spec = VtkStreamlinesInputSpec
    output_spec = VtkStreamlinesOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["vtk"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + ".vtk"


class ProcStreamlinesInputSpec(StdOutCommandLineInputSpec):
    inputmodel = traits.Enum(
        "raw",
        "voxels",
        argstr="-inputmodel %s",
        desc="input model type (raw or voxels)",
        usedefault=True,
    )

    in_file = File(
        exists=True,
        argstr="-inputfile %s",
        mandatory=True,
        position=1,
        desc="data file",
    )

    maxtractpoints = traits.Int(
        argstr="-maxtractpoints %d", units="NA", desc="maximum number of tract points"
    )
    mintractpoints = traits.Int(
        argstr="-mintractpoints %d", units="NA", desc="minimum number of tract points"
    )
    maxtractlength = traits.Int(
        argstr="-maxtractlength %d", units="mm", desc="maximum length of tracts"
    )
    mintractlength = traits.Int(
        argstr="-mintractlength %d", units="mm", desc="minimum length of tracts"
    )
    datadims = traits.List(
        traits.Int,
        desc="data dimensions in voxels",
        argstr="-datadims %s",
        minlen=3,
        maxlen=3,
        units="voxels",
    )
    voxeldims = traits.List(
        traits.Int,
        desc="voxel dimensions in mm",
        argstr="-voxeldims %s",
        minlen=3,
        maxlen=3,
        units="mm",
    )
    seedpointmm = traits.List(
        traits.Int,
        desc="The coordinates of a single seed point for tractography in mm",
        argstr="-seedpointmm %s",
        minlen=3,
        maxlen=3,
        units="mm",
    )
    seedpointvox = traits.List(
        traits.Int,
        desc="The coordinates of a single seed point for tractography in voxels",
        argstr="-seedpointvox %s",
        minlen=3,
        maxlen=3,
        units="voxels",
    )
    seedfile = File(
        exists=False, argstr="-seedfile %s", desc="Image Containing Seed Points"
    )
    regionindex = traits.Int(
        argstr="-regionindex %d", units="mm", desc="index of specific region to process"
    )
    iterations = traits.Float(
        argstr="-iterations %d",
        units="NA",
        desc="Number of streamlines generated for each seed. Not required when outputting streamlines, but needed to create PICo images. The default is 1 if the output is streamlines, and 5000 if the output is connection probability images.",
    )
    targetfile = File(
        exists=False, argstr="-targetfile %s", desc="Image containing target volumes."
    )
    allowmultitargets = traits.Bool(
        argstr="-allowmultitargets",
        desc="Allows streamlines to connect to multiple target volumes.",
    )
    directional = traits.List(
        traits.Int,
        desc="Splits the streamlines at the seed point and computes separate connection probabilities for each segment. Streamline segments are grouped according to their dot product with the vector (X, Y, Z). The ideal vector will be tangential to the streamline trajectory at the seed, such that the streamline projects from the seed along (X, Y, Z) and -(X, Y, Z). However, it is only necessary for the streamline trajectory to not be orthogonal to (X, Y, Z).",
        argstr="-directional %s",
        minlen=3,
        maxlen=3,
        units="NA",
    )
    waypointfile = File(
        exists=False,
        argstr="-waypointfile %s",
        desc="Image containing waypoints. Waypoints are defined as regions of the image with the same intensity, where 0 is background and any value > 0 is a waypoint.",
    )
    truncateloops = traits.Bool(
        argstr="-truncateloops",
        desc="This option allows streamlines to enter a waypoint exactly once. After the streamline leaves the waypoint, it is truncated upon a second entry to the waypoint.",
    )
    discardloops = traits.Bool(
        argstr="-discardloops",
        desc="This option allows streamlines to enter a waypoint exactly once. After the streamline leaves the waypoint, the entire streamline is discarded upon a second entry to the waypoint.",
    )
    exclusionfile = File(
        exists=False,
        argstr="-exclusionfile %s",
        desc="Image containing exclusion ROIs. This should be an Analyze 7.5 header / image file.hdr and file.img.",
    )
    truncateinexclusion = traits.Bool(
        argstr="-truncateinexclusion",
        desc="Retain segments of a streamline before entry to an exclusion ROI.",
    )

    endpointfile = File(
        exists=False,
        argstr="-endpointfile %s",
        desc="Image containing endpoint ROIs. This should be an Analyze 7.5 header / image file.hdr and file.img.",
    )

    resamplestepsize = traits.Float(
        argstr="-resamplestepsize %d",
        units="NA",
        desc="Each point on a streamline is tested for entry into target, exclusion or waypoint volumes. If the length between points on a tract is not much smaller than the voxel length, then streamlines may pass through part of a voxel without being counted. To avoid this, the program resamples streamlines such that the step size is one tenth of the smallest voxel dimension in the image. This increases the size of raw or oogl streamline output and incurs some performance penalty. The resample resolution can be controlled with this option or disabled altogether by passing a negative step size or by passing the -noresample option.",
    )

    noresample = traits.Bool(
        argstr="-noresample",
        desc="Disables resampling of input streamlines. Resampling is automatically disabled if the input model is voxels.",
    )

    outputtracts = traits.Bool(
        argstr="-outputtracts", desc="Output streamlines in raw binary format."
    )

    outputroot = File(
        exists=False,
        argstr="-outputroot %s",
        desc="Prepended onto all output file names.",
    )

    gzip = traits.Bool(argstr="-gzip", desc="save the output image in gzip format")
    outputcp = traits.Bool(
        argstr="-outputcp",
        desc="output the connection probability map (Analyze image, float)",
        requires=["outputroot", "seedfile"],
    )
    outputsc = traits.Bool(
        argstr="-outputsc",
        desc="output the connection probability map (raw streamlines, int)",
        requires=["outputroot", "seedfile"],
    )
    outputacm = traits.Bool(
        argstr="-outputacm",
        desc="output all tracts in a single connection probability map (Analyze image)",
        requires=["outputroot", "seedfile"],
    )
    outputcbs = traits.Bool(
        argstr="-outputcbs",
        desc="outputs connectivity-based segmentation maps; requires target outputfile",
        requires=["outputroot", "targetfile", "seedfile"],
    )


class ProcStreamlinesOutputSpec(TraitedSpec):
    proc = File(exists=True, desc="Processed Streamlines")
    outputroot_files = OutputMultiPath(File(exists=True))


class ProcStreamlines(StdOutCommandLine):
    """
    Process streamline data

    This program does post-processing of streamline output from track. It can either output streamlines or connection probability maps.
     * http://web4.cs.ucl.ac.uk/research/medic/camino/pmwiki/pmwiki.php?n=Man.procstreamlines

    Examples
    --------

    >>> import nipype.interfaces.camino as cmon
    >>> proc = cmon.ProcStreamlines()
    >>> proc.inputs.in_file = 'tract_data.Bfloat'
    >>> proc.run()                  # doctest: +SKIP
    """

    _cmd = "procstreamlines"
    input_spec = ProcStreamlinesInputSpec
    output_spec = ProcStreamlinesOutputSpec

    def _format_arg(self, name, spec, value):
        if name == "outputroot":
            return spec.argstr % self._get_actual_outputroot(value)
        return super(ProcStreamlines, self)._format_arg(name, spec, value)

    def __init__(self, *args, **kwargs):
        super(ProcStreamlines, self).__init__(*args, **kwargs)
        self.outputroot_files = []

    def _run_interface(self, runtime):
        outputroot = self.inputs.outputroot
        if isdefined(outputroot):
            actual_outputroot = self._get_actual_outputroot(outputroot)
            base, filename, ext = split_filename(actual_outputroot)
            if not os.path.exists(base):
                os.makedirs(base)
            new_runtime = super(ProcStreamlines, self)._run_interface(runtime)
            self.outputroot_files = glob.glob(
                os.path.join(os.getcwd(), actual_outputroot + "*")
            )
            return new_runtime
        else:
            new_runtime = super(ProcStreamlines, self)._run_interface(runtime)
            return new_runtime

    def _get_actual_outputroot(self, outputroot):
        actual_outputroot = os.path.join("procstream_outfiles", outputroot)
        return actual_outputroot

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["proc"] = os.path.abspath(self._gen_outfilename())
        outputs["outputroot_files"] = self.outputroot_files
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_proc"


class TractShredderInputSpec(StdOutCommandLineInputSpec):
    in_file = File(
        exists=True, argstr="< %s", mandatory=True, position=-2, desc="tract file"
    )

    offset = traits.Int(
        argstr="%d", units="NA", desc="initial offset of offset tracts", position=1
    )

    bunchsize = traits.Int(
        argstr="%d",
        units="NA",
        desc="reads and outputs a group of bunchsize tracts",
        position=2,
    )

    space = traits.Int(argstr="%d", units="NA", desc="skips space tracts", position=3)


class TractShredderOutputSpec(TraitedSpec):
    shredded = File(exists=True, desc="Shredded tract file")


class TractShredder(StdOutCommandLine):
    """
    Extracts bunches of streamlines.

    tractshredder works in a similar way to shredder, but processes streamlines instead of scalar data.
    The input is raw streamlines, in the format produced by track or procstreamlines.

    The program first makes an initial offset of offset tracts.  It then reads and outputs a group of
    bunchsize tracts, skips space tracts, and repeats until there is no more input.

    Examples
    --------

    >>> import nipype.interfaces.camino as cmon
    >>> shred = cmon.TractShredder()
    >>> shred.inputs.in_file = 'tract_data.Bfloat'
    >>> shred.inputs.offset = 0
    >>> shred.inputs.bunchsize = 1
    >>> shred.inputs.space = 2
    >>> shred.run()                  # doctest: +SKIP
    """

    _cmd = "tractshredder"
    input_spec = TractShredderInputSpec
    output_spec = TractShredderOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["shredded"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_shredded"


class DT2NIfTIInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="-inputfile %s",
        mandatory=True,
        position=1,
        desc="tract file",
    )

    output_root = File(
        argstr="-outputroot %s",
        position=2,
        genfile=True,
        desc="filename root prepended onto the names of three output files.",
    )

    header_file = File(
        exists=True,
        argstr="-header %s",
        mandatory=True,
        position=3,
        desc=" A Nifti .nii or .hdr file containing the header information",
    )


class DT2NIfTIOutputSpec(TraitedSpec):
    dt = File(exists=True, desc="diffusion tensors in NIfTI format")

    exitcode = File(
        exists=True, desc="exit codes from Camino reconstruction in NIfTI format"
    )

    lns0 = File(
        exists=True, desc="estimated lns0 from Camino reconstruction in NIfTI format"
    )


class DT2NIfTI(CommandLine):
    """
    Converts camino tensor data to NIfTI format

    Reads Camino diffusion tensors, and converts them to NIFTI format as three .nii files.
    """

    _cmd = "dt2nii"
    input_spec = DT2NIfTIInputSpec
    output_spec = DT2NIfTIOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        output_root = self._gen_outputroot()
        outputs["dt"] = os.path.abspath(output_root + "dt.nii")
        outputs["exitcode"] = os.path.abspath(output_root + "exitcode.nii")
        outputs["lns0"] = os.path.abspath(output_root + "lns0.nii")
        return outputs

    def _gen_outfilename(self):
        return self._gen_outputroot()

    def _gen_outputroot(self):
        output_root = self.inputs.output_root
        if not isdefined(output_root):
            output_root = self._gen_filename("output_root")
        return output_root

    def _gen_filename(self, name):
        if name == "output_root":
            _, filename, _ = split_filename(self.inputs.in_file)
            filename = filename + "_"
        return filename


class NIfTIDT2CaminoInputSpec(StdOutCommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="-inputfile %s",
        mandatory=True,
        position=1,
        desc="A NIFTI-1 dataset containing diffusion tensors. The tensors are assumed to be "
        "in lower-triangular order as specified by the NIFTI standard for the storage of "
        "symmetric matrices. This file should be either a .nii or a .hdr file.",
    )

    s0_file = File(
        argstr="-s0 %s",
        exists=True,
        desc="File containing the unweighted signal for each voxel, may be a raw binary "
        "file (specify type with -inputdatatype) or a supported image file.",
    )

    lns0_file = File(
        argstr="-lns0 %s",
        exists=True,
        desc="File containing the log of the unweighted signal for each voxel, may be a "
        "raw binary file (specify type with -inputdatatype) or a supported image file.",
    )

    bgmask = File(
        argstr="-bgmask %s",
        exists=True,
        desc="Binary valued brain / background segmentation, may be a raw binary file "
        "(specify type with -maskdatatype) or a supported image file.",
    )

    scaleslope = traits.Float(
        argstr="-scaleslope %s",
        desc="A value v in the diffusion tensor is scaled to v * s + i. This is "
        "applied after any scaling specified by the input image. Default is 1.0.",
    )

    scaleinter = traits.Float(
        argstr="-scaleinter %s",
        desc="A value v in the diffusion tensor is scaled to v * s + i. This is "
        "applied after any scaling specified by the input image. Default is 0.0.",
    )

    uppertriangular = traits.Bool(
        argstr="-uppertriangular %s",
        desc="Specifies input in upper-triangular (VTK style) order.",
    )


class NIfTIDT2CaminoOutputSpec(TraitedSpec):
    out_file = File(desc="diffusion tensors data in Camino format")


class NIfTIDT2Camino(CommandLine):
    """
    Converts NIFTI-1 diffusion tensors to Camino format. The program reads the
    NIFTI header but does not apply any spatial transformations to the data. The
    NIFTI intensity scaling parameters are applied.

    The output is the tensors in Camino voxel ordering: [exit, ln(S0), dxx, dxy,
    dxz, dyy, dyz, dzz].

    The exit code is set to 0 unless a background mask is supplied, in which case
    the code is 0 in brain voxels and -1 in background voxels.

    The value of ln(S0) in the output is taken from a file if one is supplied,
    otherwise it is set to 0.

    NOTE FOR FSL USERS - FSL's dtifit can output NIFTI tensors, but they are not
    stored in the usual way (which is using NIFTI_INTENT_SYMMATRIX). FSL's
    tensors follow the ITK / VTK "upper-triangular" convention, so you will need
    to use the -uppertriangular option to convert these correctly.

    """

    _cmd = "niftidt2camino"
    input_spec = NIfTIDT2CaminoInputSpec
    output_spec = NIfTIDT2CaminoOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = self._gen_filename("out_file")
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            _, filename, _ = split_filename(self.inputs.in_file)
        return filename


class AnalyzeHeaderInputSpec(StdOutCommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="< %s",
        mandatory=True,
        position=1,
        desc="Tensor-fitted data filename",
    )

    scheme_file = File(
        exists=True,
        argstr="%s",
        position=2,
        desc=("Camino scheme file (b values / vectors, " "see camino.fsl2scheme)"),
    )

    readheader = File(
        exists=True,
        argstr="-readheader %s",
        position=3,
        desc=(
            "Reads header information from file and prints to "
            "stdout. If this option is not specified, then the "
            "program writes a header based on the other "
            "arguments."
        ),
    )

    printimagedims = File(
        exists=True,
        argstr="-printimagedims %s",
        position=3,
        desc=(
            "Prints image data and voxel dimensions as " "Camino arguments and exits."
        ),
    )

    # How do we implement both file and enum (for the program) in one argument?
    # Is this option useful anyway?
    # -printprogargs <file> <prog>
    # Prints data dimension (and type, if relevant) arguments for a specific
    # Camino program, where prog is one of shredder, scanner2voxel,
    # vcthreshselect, pdview, track.
    printprogargs = File(
        exists=True,
        argstr="-printprogargs %s",
        position=3,
        desc=(
            "Prints data dimension (and type, if relevant) "
            "arguments for a specific Camino program, where "
            "prog is one of shredder, scanner2voxel, "
            "vcthreshselect, pdview, track."
        ),
    )

    printintelbyteorder = File(
        exists=True,
        argstr="-printintelbyteorder %s",
        position=3,
        desc=("Prints 1 if the header is little-endian, " "0 otherwise."),
    )

    printbigendian = File(
        exists=True,
        argstr="-printbigendian %s",
        position=3,
        desc=("Prints 1 if the header is big-endian, 0 " "otherwise."),
    )

    initfromheader = File(
        exists=True,
        argstr="-initfromheader %s",
        position=3,
        desc=(
            "Reads header information from file and "
            "initializes a new header with the values read "
            "from the file. You may replace any "
            "combination of fields in the new header by "
            "specifying subsequent options."
        ),
    )

    data_dims = traits.List(
        traits.Int,
        desc="data dimensions in voxels",
        argstr="-datadims %s",
        minlen=3,
        maxlen=3,
        units="voxels",
    )

    voxel_dims = traits.List(
        traits.Float,
        desc="voxel dimensions in mm",
        argstr="-voxeldims %s",
        minlen=3,
        maxlen=3,
        units="mm",
    )

    centre = traits.List(
        traits.Int,
        argstr="-centre %s",
        minlen=3,
        maxlen=3,
        units="mm",
        desc=(
            "Voxel specifying origin of Talairach "
            "coordinate system for SPM, default [0 0 0]."
        ),
    )

    picoseed = traits.List(
        traits.Int,
        argstr="-picoseed %s",
        minlen=3,
        maxlen=3,
        desc=("Voxel specifying the seed (for PICo maps), " "default [0 0 0]."),
        units="mm",
    )

    nimages = traits.Int(
        argstr="-nimages %d",
        units="NA",
        desc="Number of images in the img file. Default 1.",
    )

    datatype = traits.Enum(
        "byte",
        "char",
        "[u]short",
        "[u]int",
        "float",
        "complex",
        "double",
        argstr="-datatype %s",
        desc=(
            "The char datatype is 8 bit (not the 16 bit "
            "char of Java), as specified by the Analyze "
            "7.5 standard. The byte, ushort and uint "
            "types are not part of the Analyze "
            "specification but are supported by SPM."
        ),
        mandatory=True,
    )

    offset = traits.Int(
        argstr="-offset %d",
        units="NA",
        desc=(
            "According to the Analyze 7.5 standard, this is "
            "the byte offset in the .img file at which "
            "voxels start. This value can be negative to "
            "specify that the absolute value is applied for "
            "every image in the file."
        ),
    )

    greylevels = traits.List(
        traits.Int,
        argstr="-gl %s",
        minlen=2,
        maxlen=2,
        desc=("Minimum and maximum greylevels. Stored as " "shorts in the header."),
        units="NA",
    )

    scaleslope = traits.Float(
        argstr="-scaleslope %d",
        units="NA",
        desc=(
            "Intensities in the image are scaled by "
            "this factor by SPM and MRICro. Default is "
            "1.0."
        ),
    )

    scaleinter = traits.Float(
        argstr="-scaleinter %d",
        units="NA",
        desc=("Constant to add to the image intensities. " "Used by SPM and MRIcro."),
    )

    description = traits.String(
        argstr="-description %s",
        desc=(
            "Short description - No spaces, max "
            "length 79 bytes. Will be null "
            "terminated automatically."
        ),
    )

    intelbyteorder = traits.Bool(
        argstr="-intelbyteorder",
        desc=("Write header in intel byte order " "(little-endian)."),
    )

    networkbyteorder = traits.Bool(
        argstr="-networkbyteorder",
        desc=(
            "Write header in network byte order "
            "(big-endian). This is the default "
            "for new headers."
        ),
    )


class AnalyzeHeaderOutputSpec(TraitedSpec):
    header = File(exists=True, desc="Analyze header")


class AnalyzeHeader(StdOutCommandLine):
    """
    Create or read an Analyze 7.5 header file.

    Analyze image header, provides support for the most common header fields.
    Some fields, such as patient_id, are not currently supported. The program allows
    three nonstandard options: the field image_dimension.funused1 is the image scale.
    The intensity of each pixel in the associated .img file is (image value from file) * scale.
    Also, the origin of the Talairach coordinates (midline of the anterior commisure) are encoded
    in the field data_history.originator. These changes are included for compatibility with SPM.

    All headers written with this program are big endian by default.

    Example
    -------

    >>> import nipype.interfaces.camino as cmon
    >>> hdr = cmon.AnalyzeHeader()
    >>> hdr.inputs.in_file = 'tensor_fitted_data.Bdouble'
    >>> hdr.inputs.scheme_file = 'A.scheme'
    >>> hdr.inputs.data_dims = [256,256,256]
    >>> hdr.inputs.voxel_dims = [1,1,1]
    >>> hdr.run()                  # doctest: +SKIP
    """

    _cmd = "analyzeheader"
    input_spec = AnalyzeHeaderInputSpec
    output_spec = AnalyzeHeaderOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["header"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + ".hdr"


class ShredderInputSpec(StdOutCommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="< %s",
        mandatory=True,
        position=-2,
        desc="raw binary data file",
    )

    offset = traits.Int(
        argstr="%d", units="NA", desc="initial offset of offset bytes", position=1
    )

    chunksize = traits.Int(
        argstr="%d",
        units="NA",
        desc="reads and outputs a chunk of chunksize bytes",
        position=2,
    )

    space = traits.Int(argstr="%d", units="NA", desc="skips space bytes", position=3)


class ShredderOutputSpec(TraitedSpec):
    shredded = File(exists=True, desc="Shredded binary data file")


class Shredder(StdOutCommandLine):
    """
    Extracts periodic chunks from a data stream.

    Shredder makes an initial offset of offset bytes. It then reads and outputs
    chunksize bytes, skips space bytes, and repeats until there is no more input.

    If  the  chunksize  is  negative, chunks of size chunksize are read and the
    byte ordering of each chunk is reversed. The whole chunk will be reversed, so
    the chunk must be the same size as the data type, otherwise the order of the
    values in the chunk, as well as their endianness, will be reversed.

    Examples
    --------

    >>> import nipype.interfaces.camino as cam
    >>> shred = cam.Shredder()
    >>> shred.inputs.in_file = 'SubjectA.Bfloat'
    >>> shred.inputs.offset = 0
    >>> shred.inputs.chunksize = 1
    >>> shred.inputs.space = 2
    >>> shred.run()                  # doctest: +SKIP
    """

    _cmd = "shredder"
    input_spec = ShredderInputSpec
    output_spec = ShredderOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["shredded_file"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_shredded"
