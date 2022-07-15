# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os.path as op
import nibabel as nb
import numpy as np
from nibabel.volumeutils import native_code
from nibabel.orientations import aff2axcodes

from ... import logging
from ...utils.filemanip import split_filename
from ..base import TraitedSpec, File, isdefined
from ..dipy.base import DipyBaseInterface, HAVE_DIPY as have_dipy

iflogger = logging.getLogger("nipype.interface")


def get_vox_dims(volume):
    import nibabel as nb

    if isinstance(volume, list):
        volume = volume[0]
    nii = nb.load(volume)
    hdr = nii.header
    voxdims = hdr.get_zooms()
    return [float(voxdims[0]), float(voxdims[1]), float(voxdims[2])]


def get_data_dims(volume):
    import nibabel as nb

    if isinstance(volume, list):
        volume = volume[0]
    nii = nb.load(volume)
    hdr = nii.header
    datadims = hdr.get_data_shape()
    return [int(datadims[0]), int(datadims[1]), int(datadims[2])]


def transform_to_affine(streams, header, affine):
    try:
        from dipy.tracking.utils import transform_tracking_output
    except ImportError:
        from dipy.tracking.utils import move_streamlines as transform_tracking_output

    rotation, scale = np.linalg.qr(affine)
    streams = transform_tracking_output(streams, rotation)
    scale[0:3, 0:3] = np.dot(scale[0:3, 0:3], np.diag(1.0 / header["voxel_size"]))
    scale[0:3, 3] = abs(scale[0:3, 3])
    streams = transform_tracking_output(streams, scale)
    return streams


def read_mrtrix_tracks(in_file, as_generator=True):
    header = read_mrtrix_header(in_file)
    streamlines = read_mrtrix_streamlines(in_file, header, as_generator)
    return header, streamlines


def read_mrtrix_header(in_file):
    fileobj = open(in_file, "rb")
    header = {}
    iflogger.info("Reading header data...")
    for line in fileobj:
        line = line.decode()
        if line == "END\n":
            iflogger.info("Reached the end of the header!")
            break
        elif ": " in line:
            line = line.replace("\n", "")
            line = line.replace("'", "")
            key = line.split(": ")[0]
            value = line.split(": ")[1]
            header[key] = value
            iflogger.info('...adding "%s" to header for key "%s"', value, key)
    fileobj.close()
    header["count"] = int(header["count"].replace("\n", ""))
    header["offset"] = int(header["file"].replace(".", ""))
    return header


def read_mrtrix_streamlines(in_file, header, as_generator=True):
    offset = header["offset"]
    stream_count = header["count"]
    fileobj = open(in_file, "rb")
    fileobj.seek(offset)
    endianness = native_code
    f4dt = np.dtype(endianness + "f4")
    pt_cols = 3
    bytesize = pt_cols * 4

    def points_per_track(offset):
        track_points = []
        iflogger.info("Identifying the number of points per tract...")
        all_str = fileobj.read()
        num_triplets = int(len(all_str) / bytesize)
        pts = np.ndarray(shape=(num_triplets, pt_cols), dtype="f4", buffer=all_str)
        nonfinite_list = np.where(np.invert(np.isfinite(pts[:, 2])))
        nonfinite_list = list(nonfinite_list[0])[
            0:-1
        ]  # Converts numpy array to list, removes the last value
        for idx, value in enumerate(nonfinite_list):
            if idx == 0:
                track_points.append(nonfinite_list[idx])
            else:
                track_points.append(nonfinite_list[idx] - nonfinite_list[idx - 1] - 1)
        return track_points, nonfinite_list

    def track_gen(track_points):
        n_streams = 0
        iflogger.info("Reading tracks...")
        while True:
            try:
                n_pts = track_points[n_streams]
            except IndexError:
                break
            pts_str = fileobj.read(n_pts * bytesize)
            nan_str = fileobj.read(bytesize)
            if len(pts_str) < (n_pts * bytesize):
                if not n_streams == stream_count:
                    raise nb.trackvis.HeaderError(
                        "Expecting %s points, found only %s" % (stream_count, n_streams)
                    )
                    iflogger.error(
                        "Expecting %s points, found only %s", stream_count, n_streams
                    )
                break
            pts = np.ndarray(shape=(n_pts, pt_cols), dtype=f4dt, buffer=pts_str)
            nan_pt = np.ndarray(shape=(1, pt_cols), dtype=f4dt, buffer=nan_str)
            if np.isfinite(nan_pt[0][0]):
                raise ValueError
                break
            xyz = pts[:, :3]
            yield xyz
            n_streams += 1
            if n_streams == stream_count:
                iflogger.info("100%% : %i tracks read", n_streams)
                raise StopIteration
            try:
                if n_streams % int(stream_count / 100) == 0:
                    percent = int(float(n_streams) / float(stream_count) * 100)
                    iflogger.info("%i%% : %i tracks read", percent, n_streams)
            except ZeroDivisionError:
                iflogger.info("%i stream read out of %i", n_streams, stream_count)

    track_points, nonfinite_list = points_per_track(offset)
    fileobj.seek(offset)
    streamlines = track_gen(track_points)
    if not as_generator:
        streamlines = list(streamlines)
    return streamlines


class MRTrix2TrackVisInputSpec(TraitedSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        desc="The input file for the tracks in MRTrix (.tck) format",
    )
    image_file = File(exists=True, desc="The image the tracks were generated from")
    matrix_file = File(
        exists=True,
        desc="A transformation matrix to apply to the tracts after they have been generated (from FLIRT - affine transformation from image_file to registration_image_file)",
    )
    registration_image_file = File(
        exists=True, desc="The final image the tracks should be registered to."
    )
    out_filename = File(
        "converted.trk",
        genfile=True,
        usedefault=True,
        desc="The output filename for the tracks in TrackVis (.trk) format",
    )


class MRTrix2TrackVisOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class MRTrix2TrackVis(DipyBaseInterface):
    """
    Converts MRtrix (.tck) tract files into TrackVis (.trk) format
    using functions from dipy
    Example
    -------
    >>> import nipype.interfaces.mrtrix as mrt
    >>> tck2trk = mrt.MRTrix2TrackVis()
    >>> tck2trk.inputs.in_file = 'dwi_CSD_tracked.tck'
    >>> tck2trk.inputs.image_file = 'diffusion.nii'
    >>> tck2trk.run()                                   # doctest: +SKIP
    """

    input_spec = MRTrix2TrackVisInputSpec
    output_spec = MRTrix2TrackVisOutputSpec

    def _run_interface(self, runtime):
        from dipy.tracking.utils import affine_from_fsl_mat_file

        try:
            from dipy.tracking.utils import transform_tracking_output
        except ImportError:
            from dipy.tracking.utils import (
                move_streamlines as transform_tracking_output,
            )

        dx, dy, dz = get_data_dims(self.inputs.image_file)
        vx, vy, vz = get_vox_dims(self.inputs.image_file)
        image_file = nb.load(self.inputs.image_file)
        affine = image_file.affine
        out_filename = op.abspath(self.inputs.out_filename)

        # Reads MRTrix tracks
        header, streamlines = read_mrtrix_tracks(self.inputs.in_file, as_generator=True)
        iflogger.info("MRTrix Header:")
        iflogger.info(header)
        # Writes to Trackvis
        trk_header = nb.trackvis.empty_header()
        trk_header["dim"] = [dx, dy, dz]
        trk_header["voxel_size"] = [vx, vy, vz]
        trk_header["n_count"] = header["count"]

        if isdefined(self.inputs.matrix_file) and isdefined(
            self.inputs.registration_image_file
        ):
            iflogger.info(
                "Applying transformation from matrix file %s", self.inputs.matrix_file
            )
            xfm = np.genfromtxt(self.inputs.matrix_file)
            iflogger.info(xfm)
            registration_image_file = nb.load(self.inputs.registration_image_file)
            reg_affine = registration_image_file.affine
            r_dx, r_dy, r_dz = get_data_dims(self.inputs.registration_image_file)
            r_vx, r_vy, r_vz = get_vox_dims(self.inputs.registration_image_file)
            iflogger.info(
                "Using affine from registration image file %s",
                self.inputs.registration_image_file,
            )
            iflogger.info(reg_affine)
            trk_header["vox_to_ras"] = reg_affine
            trk_header["dim"] = [r_dx, r_dy, r_dz]
            trk_header["voxel_size"] = [r_vx, r_vy, r_vz]

            affine = np.dot(affine, np.diag(1.0 / np.array([vx, vy, vz, 1])))
            transformed_streamlines = transform_to_affine(
                streamlines, trk_header, affine
            )

            aff = affine_from_fsl_mat_file(xfm, [vx, vy, vz], [r_vx, r_vy, r_vz])
            iflogger.info(aff)

            axcode = aff2axcodes(reg_affine)
            trk_header["voxel_order"] = axcode[0] + axcode[1] + axcode[2]

            final_streamlines = transform_tracking_output(transformed_streamlines, aff)
            trk_tracks = ((ii, None, None) for ii in final_streamlines)
            nb.trackvis.write(out_filename, trk_tracks, trk_header)
            iflogger.info("Saving transformed Trackvis file as %s", out_filename)
            iflogger.info("New TrackVis Header:")
            iflogger.info(trk_header)
        else:
            iflogger.info(
                "Applying transformation from scanner coordinates to %s",
                self.inputs.image_file,
            )
            axcode = aff2axcodes(affine)
            trk_header["voxel_order"] = axcode[0] + axcode[1] + axcode[2]
            trk_header["vox_to_ras"] = affine
            transformed_streamlines = transform_to_affine(
                streamlines, trk_header, affine
            )
            trk_tracks = ((ii, None, None) for ii in transformed_streamlines)
            nb.trackvis.write(out_filename, trk_tracks, trk_header)
            iflogger.info("Saving Trackvis file as %s", out_filename)
            iflogger.info("TrackVis Header:")
            iflogger.info(trk_header)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = op.abspath(self.inputs.out_filename)
        return outputs

    def _gen_filename(self, name):
        if name == "out_filename":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + ".trk"
