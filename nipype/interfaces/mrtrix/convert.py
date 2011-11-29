# -*- coding: utf-8 -*-
from nipype.interfaces.matlab import MatlabCommand
from nipype.interfaces.base import (TraitedSpec, BaseInterface, BaseInterfaceInputSpec,
                                    File, isdefined, traits)
from nipype.utils.filemanip import split_filename
import os, os.path as op
from string import Template
import nibabel as nb
import nipype
from nipype.workflows.utils import get_data_dims, get_vox_dims

def get_origin(volume):
    import nibabel as nb
    nii = nb.load(volume)
    aff = nii.get_affine()
    origin = aff[:,3]
    return origin[0:3]

class MRTrix2TrackVisInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True,
    desc='The input file for the tracks in MRTrix (.tck) format')
    voxel_dims = traits.List(traits.Float, minlen=3, maxlen=3,
    desc='The size of each voxel in mm.')
    data_dims = traits.List(traits.Int, minlen=3, maxlen=3,
    desc='The size of the image in voxels.')
    origin = traits.List(traits.Float, minlen=3, maxlen=3,
    desc='The origin (position of the anterior commissure) in mm')
    image_file = File(exists=True,
    desc='An image through which to infer the voxel and data dimensions of the input tracks')
    flipx = traits.Bool(False, usedefault=True, desc='Flip the tracks in the x direction')
    flipy = traits.Bool(True, usedefault=True, desc='Flip the tracks in the y direction')
    flipz = traits.Bool(True, usedefault=True, desc='Flip the tracks in the z direction')
    out_filename = File('converted.trk', genfile=True, usedefault=True, desc='The output filename for the tracks in TrackVis (.trk) format')

class MRTrix2TrackVisOutputSpec(TraitedSpec):
    out_file = File(exists=True)

class MRTrix2TrackVis(BaseInterface):
    """
    Converts MRtrix (.tck) tract files into TrackVis (.trk) format

    This interface wraps MATLAB code adapted from the MRtrix matlab
    package:

    https://code.google.com/p/mrtrix/source/browse/trunk/matlab/

    and from John Colby's Along Tract Stats package:

    https://github.com/johncolby/along-tract-stats

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> tck2trk = mrt.MRTrix2TrackVis()
    >>> tck2trk.inputs.in_file = 'dwi_CSD_tracked.tck'
    >>> tck2trk.inputs.image_file = 'dwi.nii'
    >>> tck2trk.run()                                   # doctest: +SKIP
    """
    input_spec = MRTrix2TrackVisInputSpec
    output_spec = MRTrix2TrackVisOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.image_file):
            dx, dy, dz = get_data_dims(self.inputs.image_file)
            vx, vy, vz = get_vox_dims(self.inputs.image_file)
            ox, oy, oz = get_origin(self.inputs.image_file)
        else:
            if isdefined(self.inputs.data_dims):
                dx=self.inputs.data_dims[0]
                dy=self.inputs.data_dims[1]
                dz=self.inputs.data_dims[2]
            if isdefined(self.inputs.data_dims):
                vx=self.inputs.voxel_dims[0]
                vy=self.inputs.voxel_dims[1]
                vz=self.inputs.voxel_dims[2]
            if isdefined(self.inputs.data_dims):
                ox=self.inputs.origin[0]
                oy=self.inputs.origin[1]
                oz=self.inputs.origin[2]
        fx = fy = fz = 1
        if self.inputs.flipx == True:
            fx = -1
        if self.inputs.flipy == True:
            fy = -1
        if self.inputs.flipz == True:
            fz = -1
        hdrpath = op.join(nipype.__path__[0], 'interfaces','mrtrix','defhdr')

        out_filename = 'converted.trk'
        d = dict(in_file=self.inputs.in_file,
        out_file=out_filename, dimx=dx, dimy=dy,dimz=dz,
        voxx=vx, voxy=vy, voxz=vz, orgx=ox, orgy=oy, orgz=oz,
        flipx=fx, flipy=fy, flipz=fz, headerpath=hdrpath)
        script = Template("""%% For use in substitution
in_file = '$in_file';
out_file = '$out_file';
dimx = $dimx;
dimy = $dimy;
dimz = $dimz;
vx = $voxx;
vy = $voxy;
vz = $voxz;

ox = 0; oy = ox; oz = ox;

%% 1. Reading the MRtrix tracts
% Code taken from read_mrtrix_tracks in the MRtrix package:
% https://code.google.com/p/mrtrix/source/browse/trunk/matlab/read_mrtrix_tracks.m?r=258
image.comments = {};
f = fopen (in_file, 'r');
if (f<1)
  disp (['error opening ' in_file ]);
  return
end
L = fgetl(f);
if ~strncmp(L, 'mrtrix tracks', 13)
  fclose(f);
  disp ([in_file ' is not in MRtrix format']);
  return
end

tracks = struct();

while 1
  L = fgetl(f);
  if ~ischar(L), break, end;
  L = strtrim(L);
  if strcmp(L, 'END'), break, end;
  d = strfind (L,':');
  if isempty(d)
    disp (['invalid line in header: ''' L ''' - ignored']);
  else
    key = lower(strtrim(L(1:d(1)-1)));
    value = strtrim(L(d(1)+1:end));
    if strcmp(key, 'file')
      file = value;
    elseif strcmp(key, 'datatype')
      tracks.datatype = value;
    else
      tracks = setfield (tracks, key, value);
    end
  end
end
fclose(f);

if ~exist ('file') || ~isfield (tracks, 'datatype')
  disp ('critical entries missing in header - aborting')
  return
end

[ file, offset ] = strtok(file);
if ~strcmp(file,'.')
  disp ('unexpected file entry (should be set to current ''.'') - aborting')
  return;
end

if isempty(offset)
  disp ('no offset specified - aborting')
  return;
end
offset = str2num(char(offset));

datatype = lower(tracks.datatype);
byteorder = datatype(end-1:end);

if strcmp(byteorder, 'le')
  f = fopen (in_file, 'r', 'l');
  datatype = datatype(1:end-2);
elseif strcmp(byteorder, 'be')
  f = fopen (in_file, 'r', 'b');
  datatype = datatype(1:end-2);
else
  disp ('unexpected data type - aborting')
  return;
end

if (f<1)
  disp (['error opening ' in_file ]);
  return
end

fseek (f, offset, -1);
data = fread(f, inf, datatype);
fclose (f);

N = floor(prod(size(data))/3);
data = reshape (data, 3, N)';
k = find (~isfinite(data(:,1)));

tracks.data = {};
pk = 1;
for n = 1:(prod(size(k))-1)
  tracks.data{end+1} = data(pk:(k(n)-1),:);
  pk = k(n)+1;
end

%% 2. Converting the header
clear k n pk;

orig = tracks;
clear tracks;
input = orig;
orig.data = [];
orig

% mrtrix tracks are a cell array 1xNtracks, each cell is nPoints x 3
for i = 1:length(input.data)
    tracks(i).matrix = input.data{i};
    tracks(i).matrix(:,1) = tracks(i).matrix(:,1) + $flipx*$orgx;
    tracks(i).matrix(:,2) = tracks(i).matrix(:,2) + $flipy*$orgy;
    tracks(i).matrix(:,3) = tracks(i).matrix(:,3) + $flipz*$orgz;
    tracks(i).nPoints = length(tracks(i).matrix);
end

clear input
clear header

% Save track data with new header
hdrpath = ['$headerpath' '.mat']
load(hdrpath)
a.n_count = str2num(orig.count);
header = a;
header.dim = [dimx, dimy, dimz];
header.voxel_size = [vx, vy, vz];

%% 3. Writing the TrackVis tracts
% This section uses code taken from John Colby's trk_write MATLAB function
% See his github page for the entire along tract statistics MATLAB toolbox
%              https://github.com/johncolby/along-tract-stats
%
%TRK_WRITE - Write TrackVis .trk files
%
% Syntax: trk_write(header,tracks,out_file)
%
% Inputs:
%    header   - Header information for .trk file [struc]
%    tracks   - Track data struc array [1 x nTracks]
%      nPoints  - # of points in each track
%      matrix   - XYZ coordinates and associated scalars [nPoints x 3+nScalars]
%      props    - Properties of the whole tract
%    out_file - Path where .trk file will be saved [char]
%
% Output files:
%    Saves .trk file to disk at location given by 'out_file'.
%
% Other m-files required: none
% Subfunctions: none
% MAT-files required: none
%
% See also: TRK_READ

% Author: John Colby (johncolby@ucla.edu)
% UCLA Developmental Cognitive Neuroimaging Group (Sowell Lab)
% Apr 2010

out_file = '$out_file'
fid = fopen(out_file, 'w');

% Write header
fwrite(fid, header.id_string, '*char');
fwrite(fid, header.dim, 'short');
fwrite(fid, header.voxel_size, 'float');
fwrite(fid, header.origin, 'float');
fwrite(fid, header.n_scalars , 'short');
fwrite(fid, header.scalar_name', '*char');
fwrite(fid, header.n_properties, 'short');
fwrite(fid, header.property_name', '*char');
fwrite(fid, header.vox_to_ras', 'float');
fwrite(fid, header.reserved, '*char');
fwrite(fid, header.voxel_order, '*char');
fwrite(fid, header.pad2, '*char');
fwrite(fid, header.image_orientation_patient, 'float');
fwrite(fid, header.pad1, '*char');
fwrite(fid, header.invert_x, 'uchar');
fwrite(fid, header.invert_y, 'uchar');
fwrite(fid, header.invert_z, 'uchar');
fwrite(fid, header.swap_xy, 'uchar');
fwrite(fid, header.swap_yz, 'uchar');
fwrite(fid, header.swap_zx, 'uchar');
fwrite(fid, header.n_count, 'int');
fwrite(fid, header.version, 'int');
fwrite(fid, header.hdr_size, 'int');

% Check orientation
header.image_orientation_patient(1) = -1
[tmp ix] = max(abs(header.image_orientation_patient(1:3)));
[tmp iy] = max(abs(header.image_orientation_patient(4:6)));
iz = 1:3;
iz([ix iy]) = [];

% Write body
for iTrk = 1:header.n_count
    % Modify orientation back to LPS for display in TrackVis
    header.dim        = header.dim([ix iy iz]);
    header.voxel_size = header.voxel_size([ix iy iz]);
    coords = tracks(iTrk).matrix(:,1:3);
    coords = coords(:,[ix iy iz]);
    if header.image_orientation_patient(ix) < 0
        coords(:,ix) = header.dim(ix)*header.voxel_size(ix) - coords(:,ix);
    end
    if header.image_orientation_patient(3+iy) < 0
        coords(:,iy) = header.dim(iy)*header.voxel_size(iy) - coords(:,iy);
    end
    tracks(iTrk).matrix(:,1:3) = coords;

    fwrite(fid, tracks(iTrk).nPoints, 'int');
    fwrite(fid, tracks(iTrk).matrix', 'float');
    if header.n_properties
        fwrite(fid, tracks(iTrk).props, 'float');
    end
end

fclose(fid);

header

'tracks'
tracks(1).matrix
length(tracks(1).matrix)
clear all

""").substitute(d)


        # mfile = True  will create an .m file with your script and executed. Alternatively
        # mfile can be set to False which will cause the matlab code to be passed
        # as a commandline argument to the matlab executable (without creating any files).
        # This, however, is less reliable and harder to debug (code will be reduced to
        # a single line and stripped of any comments).
        result = MatlabCommand(script=script, mfile=True)
        r = result.run()
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = op.abspath(self.inputs.out_filename)
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '.trk'
