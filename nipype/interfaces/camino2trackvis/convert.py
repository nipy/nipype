from nipype.interfaces.base import CommandLineInputSpec, CommandLine, traits, TraitedSpec, File
from nipype.utils.filemanip import split_filename
import os

"""Provides interfaces to various commands provided by Camino-Trackvis
"""
    
class Camino2TrackvisInputSpec(CommandLineInputSpec):

    """
    Convert files from camino .Bfloat format to trackvis .trk format. 

    Options:
    -i, --input filename    The input .Bfloat (camino) file. If this option is not 
                            provided, data is read from stdin. 

    -o, --output filename   The filename to which to write the .trk (trackvis) 
                            file. 

    -l, --min-length length The minimum length of tracts to output 


    Coordinate System:
    -d, --data-dims width,height,depth
            Three comma-separated integers giving the number of voxels along each 
            dimension of the source scans. 

    -x, --voxel-dims width,height,depth
            Three comma-separated numbers giving the size of each voxel in mm. 

    --voxel-order order     Set the order in which various directions were stored. 
                            Specify with three letters, consisting of one each from 
                            the pairs LR, AP, and SI. These stand for Left-Right, 
                            Anterior-Posterior, and Superior-Inferior. Whichever is 
                            specified in each position will be the direction of 
                            increasing order. 

    --nifti file            Read coordinate system from a NIfTI file. 

    """

    in_file = File(exists=True, argstr='-i %s',
    mandatory=True, position=1,
    desc='The input .Bfloat (camino) file.')
    
    out_file = File(argstr='-o %s', genfile=True,
    mandatory=False, position=2, desc='The filename to which to write the .trk (trackvis) file.')
    
    min_length = traits.Float(argstr='-l %d',
    mandatory=False, position=3, units='mm', desc="The minimum length of tracts to output")

    data_dims = traits.List(traits.Int, argstr='-d %s', sep=",",
    mandatory=True, position=4, minlen=3, maxlen=3,
    desc='Three comma-separated integers giving the number of voxels along each dimension of the source scans.')

    voxel_dims = traits.List(traits.Float, argstr='-x %s', sep=",",
    mandatory=True, position=5, minlen=3, maxlen=3,
    desc='Three comma-separated numbers giving the size of each voxel in mm.')
    
    #Change to enum with all combinations? i.e. LAS, LPI, RAS, etc..
    
    voxel_order = File(argstr='--voxel-order %s',
    mandatory=True, position=6,
    desc='Set the order in which various directions were stored.\
    Specify with three letters consisting of one each  \
    from the pairs LR, AP, and SI. These stand for Left-Right, \
    Anterior-Posterior, and Superior-Inferior.  \
    Whichever is specified in each position will  \
    be the direction of increasing order.  \
    Read coordinate system from a NIfTI file.')
    
    nifti_file = File(argstr='--nifti %s', exists=True,
    mandatory=False, position=7, desc='Read coordinate system from a NIfTI file.')
    
class Camino2TrackvisOutputSpec(TraitedSpec):
    trackvis = File(exists=True, desc='The filename to which to write the .trk (trackvis) file.') 

class Camino2Trackvis(CommandLine):
    _cmd = 'camino_to_trackvis'    
    input_spec=Camino2TrackvisInputSpec
    output_spec=Camino2TrackvisOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["trackvis"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + ".trk"
        
class Trackvis2CaminoInputSpec(CommandLineInputSpec):

    """
    Trackvis2Camino (trackvis_to_camino from Camino-Trackvis)

    Usage: trackvis_to_camino [options]

    Convert file from trackvis .trk format to camino .Bfloat format. 
    
    Options:
    -i, --input filename    The input .trk (trackvis) file.
    -o, --output filename   The filename to which to write the .Bfloat (camino) 
    file. If this option (or -a) is not provided, data is 
    instead written to stdout. 
                            
    -a, --append filename   A file to which the append the .Bfloat data. 
    """

    in_file = File(exists=True, argstr='-i %s',
    mandatory=True, position=1,
    desc='The input .trk (trackvis) file.')
    
    out_file = File(argstr='-o %s', genfile=True,
    mandatory=False, position=2, desc='The filename to which to write the .Bfloat (camino).')

    append_file = File(exists=True, argstr='-a %s',
    mandatory=False, position=2, desc='A file to which the append the .Bfloat data. ')
                    
class Trackvis2CaminoOutputSpec(TraitedSpec):
    camino = File(exists=True, desc='The filename to which to write the .Bfloat (camino).') 

class Trackvis2Camino(CommandLine):
    _cmd = 'trackvis_to_camino'    
    input_spec=Trackvis2CaminoInputSpec
    output_spec=Trackvis2CaminoOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["camino"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + ".Bfloat"
