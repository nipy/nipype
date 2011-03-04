from nipype.interfaces.base import CommandLineInputSpec, CommandLine, traits, TraitedSpec, File
from nipype.utils.filemanip import split_filename
import os

class Image2VoxelInputSpec(CommandLineInputSpec):
    """    image2voxel -4dimage <file> | -imagelist <file> [options] 
     
     * Converts Analyze / NIFTI / MHA files to voxel order. 
     * Either takes a 4D file (all measurements in single image) 
     * or a list of 3D images.
     
     http://web4.cs.ucl.ac.uk/research/medic/camino/pmwiki/pmwiki.php?n=Man.Image2voxel
     
     OPTIONS
    -4dimage <file>
        Path to the input image file or header. 
        This should be used when converting 4D / 5D files where each 3D volume is an image from a single diffusion-weighted measurement. 
        The order of the measurement volumes must correspond to the accompanying scheme file.

    -imagelist <filename>
        Name of a file containing a list of 3D images, each containing a single diffusion-weighted measurement. 
        The order of the headers in the list must match the order of the corresponding measurements in the scheme file.

    -imageprefix <prefix>
        Path to prepend onto filenames in the imagelist. 
        Has no effect on paths specified on the command line with -4dimage. 
        The default prefix is the directory containing the image list. 
        This option is used when the imagelist is not in the same directory as the images it describes.

    -outputdatatype <data type of output>
        Specifies the data type of the output data. 
        The data type can be any of the following strings: "char", "short", "int", "long", "float" or "double". 
        The default output data type is float.
    """
    in_file = File(exists=True, argstr='-4dimage %s',
                    mandatory=True, position=1,
                    desc='4d image file')
#TODO convert list of files on the fly    
#    imagelist = File(exists=True, argstr='-imagelist %s',
#                    mandatory=True, position=1,
#                    desc='Name of a file containing a list of 3D images')
#    
#    imageprefix = traits.Str(argstr='-imageprefix %s', position=3,
#                    desc='Path to prepend onto filenames in the imagelist.')                
    
    out_type = traits.Enum("float", "char", "short", "int", "long", "double", argstr='-outputdatatype %s', position=2,
                           desc='"i.e. Bfloat". Can be "char", "short", "int", "long", "float" or "double"', usedefault=True)
    out_file = File(argstr="> %s", position=3, genfile=True)
    
class Image2VoxelOutputSpec(TraitedSpec):
    """Use image2voxel to convert NIFTI images to voxel order
    """
    out_file = File(exists=True, desc='path/name of 4D volume in voxel order') 
    
class Image2Voxel(CommandLine):
    """Use image2voxel to convert NIFTI images to voxel order
    """
    _cmd = 'image2voxel'    
    input_spec = Image2VoxelInputSpec
    output_spec = Image2VoxelOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + ".B" + self.inputs.out_type
    
class FSL2SchemeInputSpec(CommandLineInputSpec):
    """ FSL2Scheme -bvecfile <bvecs> -bvalfile <bvals> -diffusiontime <secs> -bscale <factor> [-flipx] [-flipy] [-flipz] [-usegradmod] 
    * FSL2Scheme - converts b-vectors and b-values from FSL format to a Camino scheme file. 
    -bvecfile <bvecs>
        The file containing the b-vectors. This is a text file of format


         x(1) x(2)... x(N+M)
         y(1) y(2) ... y(N+M)
         z(1) z(2) ... z(N+M)

        where the gradient direction for measurement (i) is [x(i), y(i), z(i)], and there are M unweighted and N diffusion-weighted measurements.

    -bvalfile <bvals>
        The file containing the b-values. This is a text file of format

        b(1) b(2) ... b(N+M)

        where there are M unweighted (b = 0) and N diffusion-weighted measurements.

    -bscale <factor>
        Scaling factor to convert the b-values into different units. Default is 10^6.

    -flipx
        Negate the x component of all the vectors.

    -flipy
        Negate the y component of all the vectors.

    -flipz
        Negate the z component of all the vectors.

    -interleave
        Interleave repeated scans. Only used with -numscans. If this is selected, the output will be interleaved, so you will have measurement 0 repeated numScans times, then measurement 1, etc.

    -numscans <number>
        Output all measurements number times, used when combining multiple scans from the same imaging session. The default behaviour is to repeat the entire block of measurements, like you'd get from copying and pasting the scheme number times. If -interleave is specified, then identical measurements are grouped together.

    -usegradmod
        Use the gradient magnitude to scale b. This option has no effect if your gradient directions have unit magnitude. It should only be used if your scanner does not normalize the gradient directions. 
    """

    bvec_file = File(exists=True, argstr='-bvecfile %s',
                    mandatory=True, position=1,
                    desc='b vector file')
                                         
    bval_file = File(exists=True, argstr='-bvalfile %s',
                    mandatory=True, position=2,
                    desc='b value file')
                    
    numscans = traits.Int(argstr='-numscans %d', units='NA',
                desc="Output all measurements numerous (n) times, used when combining multiple scans from the same imaging session.")
    
    interleave = traits.Bool(argstr='-interleave', desc="Interleave repeated scans. Only used with -numscans.")
    
    bscale = traits.Float(argstr='-bscale %d', units='NA',
                desc="Scaling factor to convert the b-values into different units. Default is 10^6.")
    
    diffusiontime = traits.Float(argstr = '-diffusiontime %f', units = 'NA',
                desc="Diffusion time")
                            
    flipx = traits.Bool(argstr='-flipx', desc="Negate the x component of all the vectors.")
    flipy = traits.Bool(argstr='-flipy', desc="Negate the y component of all the vectors.")
    flipz = traits.Bool(argstr='-flipz', desc="Negate the z component of all the vectors.")
    usegradmod = traits.Bool(argstr='-usegradmod', desc="Use the gradient magnitude to scale b. This option has no effect if your gradient directions have unit magnitude.")
    out_file = File(argstr="> %s", position=3, genfile=True)

    
class FSL2SchemeOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='Scheme file') 

class FSL2Scheme(CommandLine):
    _cmd = 'fsl2scheme'    
    input_spec=FSL2SchemeInputSpec
    output_spec=FSL2SchemeOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.bvec_file)
        return name + ".scheme"

