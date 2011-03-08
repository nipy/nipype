from nipype.interfaces.base import CommandLineInputSpec, CommandLine, traits, TraitedSpec, File
from nipype.utils.filemanip import split_filename
import os

class DTIFitInputSpec(CommandLineInputSpec):
    """
    * Reads diffusion MRI data, acquired using the acquisition scheme detailed in the scheme file, from the data file. 
    * For help with scheme files, please see the section "scheme files" in camino(1).  OPTIONS

    dtfit <data file> <scheme file> [-nonlinear] [options] --nonlinear
    
        Use non-linear fitting instead of the default linear regression to the log measurements. 
    The data file stores the diffusion MRI data in voxel order with the measurements stored in big-endian format and ordered as in the scheme file.
    The default input data type is four-byte float. The default output data type is eight-byte double.
    See modelfit and camino for the format of the data file and scheme file.
    The program fits the diffusion tensor to each voxel and outputs the results, 
    in voxel order and as big-endian eight-byte doubles, to the standard output. 
    The program outputs eight values in each voxel: [exit code, ln(S(0)), D_xx, D_xy, D_xz, D_yy, D_yz, D_zz]. 
    An exit code of zero indicates no problems. For a list of other exit codes, see modelfit(1). The entry S(0) is an estimate of the signal at q=0. 
    """
    
    in_file = File(exists=True, argstr='%s',
                    mandatory=True, position=1,
                    desc='voxel-order data filename')
    
    scheme_file = File(exists=True, argstr='%s',
                    mandatory=True, position=2,
                    desc='Camino scheme file (b values / vectors, see camino.fsl2scheme)')
    
    non_linear = traits.Bool(argstr='-nonlinear', position=3, desc="Use non-linear fitting instead of the default linear regression to the log measurements. ")
    
    out_file = File(argstr="> %s", position=4, genfile=True) #Change to -1?
            
class DTIFitOutputSpec(TraitedSpec):
    """Use dtfit to fit tensors to each voxel
    """
    tensor_fitted = File(exists=True, desc='path/name of 4D volume in voxel order') 

class DTIFit(CommandLine):
    """Use dtfit to fit tensors to each voxel
    """
    _cmd = 'dtfit'
    input_spec=DTIFitInputSpec
    output_spec=DTIFitOutputSpec
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["tensor_fitted"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + "_DT.Bdouble"

class DTLUTGenInputSpec(CommandLineInputSpec):
    """
    dtlutgen -[l|f]range <min> <max> -step <step> -snr <value> -schemefile <file> [options] 
    """
               
    lrange = traits.List(traits.Float, desc = 'Index to one-tensor LUTs. This is the ratio L1/L3 and L2 / L3.' \
        'The LUT is square, with half the values calculated (because L2 / L3 cannot be less than L1 / L3 by definition).' \
        'The minimum must be >= 1. For comparison, a ratio L1 / L3 = 10 with L2 / L3 = 1 corresponds to an FA of 0.891, '\
        'and L1 / L3 = 15 with L2 / L3 = 1 corresponds to an FA of 0.929. The default range is 1 to 10.', \
        argstr='-lrange %s', minlen=2, maxlen=2, position=1, \
        units='NA')

    frange = traits.List(traits.Float, desc = 'Index to two-tensor LUTs. This is the fractional anisotropy of the two tensors.'
        'The default is 0.3 to 0.94', \
        argstr='-frange %s', minlen=2, maxlen=2, position=1, \
        units='NA')
    
    step = traits.Float(argstr='-step %d', units='NA',
        desc='Distance between points in the LUT.' \
        'For example, if lrange is 1 to 10 and the step is 0.1, LUT entries will be computed ' \
        'at L1 / L3 = 1, 1.1, 1.2 ... 10.0 and at L2 / L3 = 1.0, 1.1 ... L1 / L3.' \
        'For single tensor LUTs, the default step is 0.2, for two-tensor LUTs it is 0.02.')
        
    samples = traits.Int(argstr='-samples %d', units='NA',
        desc='The number of synthetic measurements to generate at each point in the LUT. The default is 2000.')

    snr = traits.Float(argstr='-snr %d', units='NA',
        desc='The signal to noise ratio of the unweighted (q = 0) measurements.'\
        'This should match the SNR (in white matter) of the images that the LUTs are used with.')

    bingham = traits.Bool(argstr='-bingham', desc="Compute a LUT for the Bingham PDF. This is the default.")
    acg = traits.Bool(argstr='-acg', desc="Compute a LUT for the ACG PDF.")
    watson = traits.Bool(argstr='-watson', desc="Compute a LUT for the Watson PDF.")

    inversion = traits.Int(argstr='-inversion %d', units='NA',
        desc='Index of the inversion to use. The default is 1 (linear single tensor inversion).')


    trace = traits.Float(argstr='-trace %d', units='NA',
        desc='Trace of the diffusion tensor(s) used in the test function in the LUT generation. The default is 2100E-12 m^2 s^-1.')

    in_file = File(exists=True, argstr='%s',
                    mandatory=False, position=1,
                    desc='diffusion tensor datafile')
    
    scheme_file = File(argstr='-schemefile %s',
                    mandatory=True, position=2,
                    desc='The scheme file of the images to be processed using this LUT.')
    
    out_file = File(argstr="> %s", position=-1, genfile=True)              
            
class DTLUTGenOutputSpec(TraitedSpec):
    dtLUT = File(exists=True, desc='Lookup Table') 

class DTLUTGen(CommandLine):
    _cmd = 'dtlutgen'
    input_spec=DTLUTGenInputSpec
    output_spec=DTLUTGenOutputSpec
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["dtLUT"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.scheme_file)
        return name + ".dat"
        
class PicoPDFsInputSpec(CommandLineInputSpec):
    """
    picopdfs -inputmodel <dt | multitensor | pds> -luts <files> 
    """
    in_file = File(exists=True, argstr='< %s',
    mandatory=True, position=1,
    desc='voxel-order data filename')    
    
    inputmodel = traits.Enum('dt', 'multitensor', 'pds', 
    argstr='-inputmodel %s', position=2, desc='input model type', usedefault=True)

    luts = File(exists=True, argstr='-luts %s',
    mandatory=False, position=3,
    desc='Files containing the lookup tables.'\
    'For tensor data, one lut must be specified for each type of inversion used in the image (one-tensor, two-tensor, three-tensor).'\
    'For pds, the number of LUTs must match -numpds (it is acceptable to use the same LUT several times - see example, above).'\
    'These LUTs may be generated with dtlutgen.')
    
    pdf = traits.Enum('watson', 'bingham', 'acg', 
    argstr='-pdf %s', position=4, desc=' Specifies the PDF to use. There are three choices:'\
    'watson - The Watson distribution. This distribution is rotationally symmetric.'\
    'bingham - The Bingham distributionn, which allows elliptical probability density contours.'\
    'acg - The Angular Central Gaussian distribution, which also allows elliptical probability density contours', usedefault=True)

    directmap = traits.Bool(argstr='-directmap', desc="Only applicable when using pds as the inputmodel. Use direct mapping between the eigenvalues and the distribution parameters instead of the log of the eigenvalues.")

    maxcomponents = traits.Int(argstr='-maxcomponents %d', units='NA',
        desc='The maximum number of tensor components in a voxel (default 2) for multitensor data.'\
        'Currently, only the default is supported, but future releases may allow the input of three-tensor data using this option.')
    
    numpds = traits.Int(argstr='-numpds %d', units='NA',
        desc='The maximum number of PDs in a voxel (default 3) for PD data.' \
        'This option determines the size of the input and output voxels.' \
        'This means that the data file may be large enough to accomodate three or more PDs,'\
        'but does not mean that any of the voxels are classified as containing three or more PDs.')
        
    out_file = File(argstr="> %s", position=-1, genfile=True)              
            
class PicoPDFsOutputSpec(TraitedSpec):
    pdfs = File(exists=True, desc='path/name of 4D volume in voxel order') 

class PicoPDFs(CommandLine):
    _cmd = 'picopdfs'
    input_spec=PicoPDFsInputSpec
    output_spec=PicoPDFsOutputSpec
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["pdfs"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + "_pdfs.Bdouble"

class TrackInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='-inputfile %s', mandatory=True, position=1, desc='data file')

    seed_file = File(exists=True, argstr='-seedfile %s', mandatory=False, position=2, desc='seed file')
    
    inputmodel = traits.Enum('dt', 'multitensor', 'pds', 'pico', 'bootstrap', 'ballstick', 'bayesdirac', 
        argstr='-inputmodel %s', position=3, desc='input model type', usedefault=True)    
    
    inputdatatype = traits.Enum('float', 'double', argstr='-inputdatatype %s', desc='input file type')    

    gzip = traits.Bool(argstr='-gzip', desc="save the output image in gzip format")

    maxcomponents = traits.Int(argstr='-maxcomponents %d', units='NA',
        desc="maximum number of components")

    numpds = traits.Int(argstr='-numpds %d', units='NA',
        desc="number of principal directions")

    iterations = traits.Int(argstr='-iterations %d', units='NA',
        desc="number of iterations")

    data_dims = traits.List(traits.Int, desc = 'data dimensions in voxels',
        argstr='-datadims %s', minlen=3, maxlen=3,
        units='voxels')

    voxel_dims = traits.List(traits.Float, desc = 'voxel dimensions in mm',
        argstr='-voxeldims %s', minlen=3, maxlen=3,
        units='mm')				 

    outputtracts = traits.Enum('float', 'double', 'oogl', argstr='-outputtracts %s', desc='output tract file type')

    out_file = File(argstr='-outputfile %s',
        position=-1, genfile=True,
        desc='output data file')
    
    output_root = File(exists=False, argstr='-outputroot %s',
        mandatory=False, position=-1,
        desc='root directory for output')
    
class TrackOutputSpec(TraitedSpec):
	tracked = File(exists=True, desc='path/name of 4D volume') 

class Track(CommandLine):
    _cmd = 'track'
    input_spec=TrackInputSpec
    output_spec=TrackOutputSpec
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["tracked"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + "_tracked"

class MDInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='< %s',
                    mandatory=True, position=1,
                    desc='Tensor-fitted data filename')
    
    scheme_file = File(exists=True, argstr='%s',
                    mandatory=False, position=2,
                    desc='Camino scheme file (b values / vectors, see camino.fsl2scheme)')
       
    out_file = File(argstr="> %s", position=-1, genfile=True)              

    inputmodel = traits.Enum('dt', 'twotensor', 'threetensor', 
    argstr='-inputmodel %s', 
    desc='Specifies the model that the input tensor data contains parameters for.' \
    'Possible model types are: "dt" (diffusion-tensor data), "twotensor" (two-tensor data), '\
    '"threetensor" (three-tensor data). By default, the program assumes that the input data '\
    'contains a single diffusion tensor in each voxel.')

    inputdatatype = traits.Enum('char', 'short', 'int', 'long', 'float', 'double',
    argstr='-inputdatatype %s', 
    desc='Specifies the data type of the input file. The data type can be any of the' \
    'following strings: "char", "short", "int", "long", "float" or "double".')

    outputdatatype = traits.Enum('char', 'short', 'int', 'long', 'float', 'double',
    argstr='-outputdatatype %s', 
    desc='Specifies the data type of the output data. The data type can be any of the' \
    'following strings: "char", "short", "int", "long", "float" or "double".')

class MDOutputSpec(TraitedSpec):
    md = File(exists=True, desc='Mean Diffusivity Map') 

class MD(CommandLine):
    _cmd = 'md'
    input_spec=MDInputSpec
    output_spec=MDOutputSpec
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["md"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + "_MD.img" #Need to change to self.inputs.outputdatatype
        
class FAInputSpec(CommandLineInputSpec): 
    in_file = File(exists=True, argstr='< %s',
                    mandatory=True, position=1,
                    desc='Tensor-fitted data filename')
    
    scheme_file = File(exists=True, argstr='%s',
                    mandatory=False, position=2,
                    desc='Camino scheme file (b values / vectors, see camino.fsl2scheme)')
        
    out_file = File(argstr="> %s", position=-1, genfile=True)              

    inputmodel = traits.Enum('dt', 'twotensor', 'threetensor', 'multitensor',
    argstr='-inputmodel %s', 
    desc='Specifies the model that the input tensor data contains parameters for.' \
    'Possible model types are: "dt" (diffusion-tensor data), "twotensor" (two-tensor data), '\
    '"threetensor" (three-tensor data). By default, the program assumes that the input data '\
    'contains a single diffusion tensor in each voxel.')

    inputdatatype = traits.Enum('char', 'short', 'int', 'long', 'float', 'double',
    argstr='-inputdatatype %s', 
    desc='Specifies the data type of the input file. The data type can be any of the' \
    'following strings: "char", "short", "int", "long", "float" or "double".')

    outputdatatype = traits.Enum('char', 'short', 'int', 'long', 'float', 'double',
    argstr='-outputdatatype %s', 
    desc='Specifies the data type of the output data. The data type can be any of the' \
    'following strings: "char", "short", "int", "long", "float" or "double".')
    
class FAOutputSpec(TraitedSpec):
    fa = File(exists=True, desc='Fractional Anisotropy Map') 

class FA(CommandLine):
    _cmd = 'fa'
    input_spec=FAInputSpec
    output_spec=FAOutputSpec
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["fa"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + "_FA.img"     #Need to change to self.inputs.outputdatatype

class TrDInputSpec(CommandLineInputSpec): 
    in_file = File(exists=True, argstr='< %s',
                    mandatory=True, position=1,
                    desc='Tensor-fitted data filename')
    
    scheme_file = File(exists=True, argstr='%s',
                    mandatory=False, position=2,
                    desc='Camino scheme file (b values / vectors, see camino.fsl2scheme)')
        
    out_file = File(argstr="> %s", position=-1, genfile=True)              

    inputmodel = traits.Enum('dt', 'twotensor', 'threetensor', 'multitensor',
    argstr='-inputmodel %s', 
    desc='Specifies the model that the input tensor data contains parameters for.' \
    'Possible model types are: "dt" (diffusion-tensor data), "twotensor" (two-tensor data), '\
    '"threetensor" (three-tensor data). By default, the program assumes that the input data '\
    'contains a single diffusion tensor in each voxel.')

    inputdatatype = traits.Enum('char', 'short', 'int', 'long', 'float', 'double',
    argstr='-inputdatatype %s', 
    desc='Specifies the data type of the input file. The data type can be any of the' \
    'following strings: "char", "short", "int", "long", "float" or "double".')

    outputdatatype = traits.Enum('char', 'short', 'int', 'long', 'float', 'double',
    argstr='-outputdatatype %s', 
    desc='Specifies the data type of the output data. The data type can be any of the' \
    'following strings: "char", "short", "int", "long", "float" or "double".')
    
class TrDOutputSpec(TraitedSpec):
    trace = File(exists=True, desc='Trace of the diffusion tensor') 

class TrD(CommandLine):
    _cmd = 'trd'
    input_spec=TrDInputSpec
    output_spec=TrDOutputSpec
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["trace"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + "_TrD.img"     #Need to change to self.inputs.outputdatatype

class AnalyzeHeaderInputSpec(CommandLineInputSpec): 
    in_file = File(exists=True, argstr='< %s', 
                    mandatory=True, position=1,
                    desc='Tensor-fitted data filename') # Took out < %s from argstr
    
    scheme_file = File(exists=True, argstr='%s',
                    mandatory=False, position=2,
                    desc='Camino scheme file (b values / vectors, see camino.fsl2scheme)')
        
    out_file = File(argstr="> %s", position=-1, genfile=True)              
    
    readheader = File(exists=True, argstr='-readheader %s',
    mandatory=False, position=3,
    desc='Reads header information from file and prints to stdout. If this option is not' \
    'specified, then the program writes a header based on the other arguments.') 

    printimagedims = File(exists=True, argstr='-printimagedims %s',
    mandatory=False, position=3,
    desc='Prints image data and voxel dimensions as Camino arguments and exits.')

    # How do we implement both file and enum (for the program) in one argument? Is this option useful anyway?
    #-printprogargs <file> <prog>
    #Prints data dimension (and type, if relevant) arguments for a specific Camino program, where prog is one of shredder, scanner2voxel, vcthreshselect, pdview, track.
    printprogargs = File(exists=True, argstr='-printprogargs %s',
    mandatory=False, position=3,
    desc='Prints data dimension (and type, if relevant) arguments for a specific Camino' \
    'program, where prog is one of shredder, scanner2voxel, vcthreshselect, pdview, track.')

    printintelbyteorder = File(exists=True, argstr='-printintelbyteorder %s',
    mandatory=False, position=3,
    desc='Prints 1 if the header is little-endian, 0 otherwise.')

    printbigendian = File(exists=True, argstr='-printbigendian %s',
    mandatory=False, position=3,
    desc='Prints 1 if the header is big-endian, 0 otherwise.')

    initfromheader = File(exists=True, argstr='-initfromheader %s',
    mandatory=False, position=3,
    desc='Reads header information from file and intializes a new header with the values' \
    'read from the file. You may replace any combination of fields in the new header by specifying'\
    'subsequent options.')

    data_dims = traits.List(traits.Int, desc = 'data dimensions in voxels',
        argstr='-datadims %s', minlen=3, maxlen=3,
        units='voxels')

    voxel_dims = traits.List(traits.Float, desc = 'voxel dimensions in mm',
        argstr='-voxeldims %s', minlen=3, maxlen=3,
        units='mm')	

    centre = traits.List(traits.Int, 
    desc = 'Voxel specifying origin of Talairach coordinate system for SPM, default [0 0 0].',
        argstr='-centre %s', minlen=3, maxlen=3,
        units='mm')	

    picoseed = traits.List(traits.Int, 
    desc = 'Voxel specifying the seed (for PICo maps), default [0 0 0].',
        argstr='-picoseed %s', minlen=3, maxlen=3,
        units='mm')	

    nimages = traits.Int(argstr='-nimages %d', units='NA',
        desc="Number of images in the img file. Default 1.")

    datatype = traits.Enum('byte', 'char', '[u]short', '[u]int', 'float', 'complex', 'double',
    argstr='-datatype %s', 
    desc='The char datatype is 8 bit (not the 16 bit char of Java), as specified by the Analyze 7.5 standard. \
     The byte, ushort and uint types are not part of the Analyze specification but are supported by SPM.')

    offset = traits.Int(argstr='-offset %d', units='NA',
        desc='According to the Analyze 7.5 standard, this is the byte offset in the .img file' \
        'at which voxels start. This value can be negative to specify that the absolute value is' \
        'applied for every image in the file.')

    gl = traits.List(traits.Int, 
    desc = 'Minimum and maximum greylevels. Stored as shorts in the header.',
        argstr='-gl %s', minlen=2, maxlen=2,
        units='NA')	

    scaleslope = traits.Float(argstr='-scaleslope %d', units='NA',
        desc='Intensities in the image are scaled by this factor by SPM and MRICro. Default is 1.0.')

    scaleinter = traits.Float(argstr='-scaleinter %d', units='NA',
        desc='Constant to add to the image intensities. Used by SPM and MRIcro.')

    description = traits.String(argstr='-description %s',
        desc='Short description - No spaces, max length 79 bytes. Will be null terminated automatically.')

    intelbyteorder = traits.Bool(argstr='-intelbyteorder', 
    desc="Write header in intel byte order (little-endian).")
    
    networkbyteorder = traits.Bool(argstr='-networkbyteorder', 
    desc="Write header in network byte order (big-endian). This is the default for new headers.")
        
class AnalyzeHeaderOutputSpec(TraitedSpec):
    header = File(exists=True, desc='Analyze header') 

class AnalyzeHeader(CommandLine):
    _cmd = 'analyzeheader'
    input_spec=AnalyzeHeaderInputSpec
    output_spec=AnalyzeHeaderOutputSpec
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["header"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + ".hdr"
