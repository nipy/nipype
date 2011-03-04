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
    out_file = traits.File(argstr="> %s", position=3, genfile=True)
    
class Image2VoxelOutputSpec(TraitedSpec):
    """Use image2voxel to convert NIFTI images to voxel order
    """
    out_file = File(exists=True, desc='path/name of 4D volume in voxel order') 
    
class Image2Voxel(CommandLine):
    """Use image2voxel to convert NIFTI images to voxel order
    """
    _cmd = 'image2voxel'    
    input_spec = image2voxelInputSpec
    output_spec = image2voxelOutputSpec

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
