# -*- coding: utf-8 -*-
"""Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)
"""
from nipype.interfaces.base import (
    TraitedSpec, BaseInterface, BaseInterfaceInputSpec, File, isdefined,
    traits)
from nipype.utils.filemanip import split_filename
import os.path as op
import nibabel as nb
import nibabel.trackvis as trk
from nipype.utils.misc import package_check
import warnings

from ... import logging
iflogger = logging.getLogger('interface')

have_dipy = True
try:
    package_check('dipy', version='0.6.0')
except Exception, e:
    have_dipy = False
else:
    from dipy.tracking.utils import density_map


class TrackDensityMapInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True,
                   desc='The input TrackVis track file')
    voxel_dims = traits.List(traits.Float, minlen=3, maxlen=3,
                             desc='The size of each voxel in mm.')
    data_dims = traits.List(traits.Int, minlen=3, maxlen=3,
                            desc='The size of the image in voxels.')
    out_filename = File('tdi.nii', usedefault=True,
                        desc=('The output filename for the tracks in TrackVis'
                              ' (.trk) format'))


class TrackDensityMapOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class TrackDensityMap(BaseInterface):

    """
    Creates a tract density image from a TrackVis track file using dipy

    Example
    -------

    >>> import nipype.interfaces.dipy as dipy
    >>> trk2tdi = dipy.TrackDensityMap()
    >>> trk2tdi.inputs.in_file = 'converted.trk'
    >>> trk2tdi.run()                                   # doctest: +SKIP
    """
    input_spec = TrackDensityMapInputSpec
    output_spec = TrackDensityMapOutputSpec

    def _run_interface(self, runtime):
        tracks, header = trk.read(self.inputs.in_file)
        if not isdefined(self.inputs.data_dims):
            data_dims = header['dim']
        else:
            data_dims = self.inputs.data_dims

        if not isdefined(self.inputs.voxel_dims):
            voxel_size = header['voxel_size']
        else:
            voxel_size = self.inputs.voxel_dims

        affine = header['vox_to_ras']

        streams = ((ii[0]) for ii in tracks)
        data = density_map(streams, data_dims, voxel_size)
        if data.max() < 2 ** 15:
            data = data.astype('int16')

        img = nb.Nifti1Image(data, affine)
        out_file = op.abspath(self.inputs.out_filename)
        nb.save(img, out_file)
        iflogger.info('Track density map saved as {i}'.format(i=out_file))
        iflogger.info('Data Dimensions {d}'.format(d=data_dims))
        iflogger.info('Voxel Dimensions {v}'.format(v=voxel_size))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = op.abspath(self.inputs.out_filename)
        return outputs


class StreamlineTractographyInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc=('input diffusion data'))
    in_model = File(exists=True, desc=('input f/d-ODF model extracted from.'))
    tracking_mask = File(exists=True,
                         desc=('input mask within which perform tracking'))
    seed_mask = File(exists=True,
                     desc=('input mask within which perform seeding'))
    in_peaks = File(exists=True, desc=('peaks computed from the odf'))
    seed_coord = File(exists=True,
                      desc=('file containing the list of seed voxel '
                            'coordinates (N,3)'))
    gfa_thresh = traits.Float(0.2, mandatory=True, usedefault=True,
                              desc=('GFA threshold to compute tracking mask'))
    peak_threshold = traits.Float(
        0.5, mandatory=True, usedefault=True,
        desc=('threshold to consider peaks from model'))
    min_angle = traits.Float(25.0, mandatory=True, usedefault=True,
                             desc=('minimum separation angle'))
    multiprocess = traits.Bool(True, mandatory=True, usedefault=True,
                               desc=('use multiprocessing'))
    save_seeds = traits.Bool(False, mandatory=True, usedefault=True,
                             desc=('save seeding voxels coordinates'))
    num_seeds = traits.Int(10000, mandatory=True, usedefault=True,
                           desc=('desired number of tracks in tractography'))
    out_prefix = traits.Str(desc=('output prefix for file names'))


class StreamlineTractographyOutputSpec(TraitedSpec):
    tracks = File(desc='TrackVis file containing extracted streamlines')
    gfa = File(desc=('The resulting GFA (generalized FA) computed using the '
                     'peaks of the ODF'))
    odf_peaks = File(desc=('peaks computed from the odf'))
    out_seeds = File(desc=('file containing the (N,3) *voxel* coordinates used'
                           ' in seeding.'))


class StreamlineTractography(BaseInterface):

    """
    Streamline tractography using EuDX [Garyfallidis12]_.

    .. [Garyfallidis12] Garyfallidis E., “Towards an accurate brain
      tractography”, PhD thesis, University of Cambridge, 2012

    Example
    -------

    >>> from nipype.interfaces import dipy as ndp
    >>> track = ndp.StreamlineTractography()
    >>> track.inputs.in_file = '4d_dwi.nii'
    >>> track.inputs.in_model = 'model.pklz'
    >>> track.inputs.tracking_mask = 'dilated_wm_mask.nii'
    >>> res = track.run() # doctest: +SKIP
    """
    input_spec = StreamlineTractographyInputSpec
    output_spec = StreamlineTractographyOutputSpec

    def _run_interface(self, runtime):
        from dipy.reconst.peaks import peaks_from_model
        from dipy.tracking.eudx import EuDX
        from dipy.data import get_sphere
        # import marshal as pickle
        import cPickle as pickle
        import gzip

        if (not (isdefined(self.inputs.in_model) or
                 isdefined(self.inputs.in_peaks))):
            raise RuntimeError(('At least one of in_model or in_peaks should '
                                'be supplied'))

        img = nb.load(self.inputs.in_file)
        imref = nb.four_to_three(img)[0]
        affine = img.get_affine()

        data = img.get_data().astype(np.float32)
        hdr = imref.get_header().copy()
        hdr.set_data_dtype(np.float32)
        hdr['data_type'] = 16

        sphere = get_sphere('symmetric724')

        self._save_peaks = False
        if isdefined(self.inputs.in_peaks):
            iflogger.info('Peaks file found, skipping ODF peaks search...')
            f = gzip.open(self.inputs.in_peaks, 'rb')
            peaks = pickle.load(f)
            f.close()
        else:
            self._save_peaks = True
            iflogger.info('Loading model and computing ODF peaks')
            f = gzip.open(self.inputs.in_model, 'rb')
            odf_model = pickle.load(f)
            f.close()

            peaks = peaks_from_model(
                model=odf_model,
                data=data,
                sphere=sphere,
                relative_peak_threshold=self.inputs.peak_threshold,
                min_separation_angle=self.inputs.min_angle,
                parallel=self.inputs.multiprocess)

            f = gzip.open(self._gen_filename('peaks', ext='.pklz'), 'wb')
            pickle.dump(peaks, f, -1)
            f.close()

        hdr.set_data_shape(peaks.gfa.shape)
        nb.Nifti1Image(peaks.gfa.astype(np.float32), affine,
                       hdr).to_filename(self._gen_filename('gfa'))

        iflogger.info('Performing tractography')

        if isdefined(self.inputs.tracking_mask):
            msk = nb.load(self.inputs.tracking_mask).get_data()
            msk[msk > 0] = 1
            msk[msk < 0] = 0
        else:
            msk = np.ones(imref.get_shape())

        gfa = peaks.gfa * msk
        seeds = self.inputs.num_seeds

        if isdefined(self.inputs.seed_coord):
            seeds = np.loadtxt(self.inputs.seed_coord)

        elif isdefined(self.inputs.seed_mask):
            seedmsk = nb.load(self.inputs.seed_mask).get_data()
            assert(seedmsk.shape == data.shape[:3])
            seedmsk[seedmsk > 0] = 1
            seedmsk[seedmsk < 1] = 0
            seedps = np.array(np.where(seedmsk == 1), dtype=np.float32).T
            vseeds = seedps.shape[0]
            nsperv = (seeds // vseeds) + 1
            iflogger.info(('Seed mask is provided (%d voxels inside '
                           'mask), computing seeds (%d seeds/voxel).') %
                          (vseeds, nsperv))
            if nsperv > 1:
                iflogger.info(('Needed %d seeds per selected voxel '
                               '(total %d).') % (nsperv, vseeds))
                seedps = np.vstack(np.array([seedps] * nsperv))
                voxcoord = seedps + np.random.uniform(-1, 1, size=seedps.shape)
                nseeds = voxcoord.shape[0]
                seeds = affine.dot(np.vstack((voxcoord.T,
                                              np.ones((1, nseeds)))))[:3, :].T

                if self.inputs.save_seeds:
                    np.savetxt(self._gen_filename('seeds', ext='.txt'), seeds)

        if isdefined(self.inputs.tracking_mask):
            tmask = msk
            a_low = 0.1
        else:
            tmask = gfa
            a_low = self.inputs.gfa_thresh

        eu = EuDX(tmask,
                  peaks.peak_indices[..., 0],
                  seeds=seeds,
                  affine=affine,
                  odf_vertices=sphere.vertices,
                  a_low=a_low)

        ss_mm = [np.array(s) for s in eu]

        trkfilev = nb.trackvis.TrackvisFile([(s, None, None) for s in ss_mm],
                                            points_space='rasmm',
                                            affine=np.eye(4))
        trkfilev.to_file(self._gen_filename('tracked', ext='.trk'))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['tracks'] = self._gen_filename('tracked', ext='.trk')
        outputs['gfa'] = self._gen_filename('gfa')
        if self._save_peaks:
            outputs['odf_peaks'] = self._gen_filename('peaks', ext='.pklz')
        if self.inputs.save_seeds:
            if isdefined(self.inputs.seed_coord):
                outputs['out_seeds'] = self.inputs.seed_coord
            else:
                outputs['out_seeds'] = self._gen_filename('seeds',
                                                          ext='.txt')

        return outputs

    def _gen_filename(self, name, ext=None):
        fname, fext = op.splitext(op.basename(self.inputs.in_file))
        if fext == '.gz':
            fname, fext2 = op.splitext(fname)
            fext = fext2 + fext

        if not isdefined(self.inputs.out_prefix):
            out_prefix = op.abspath(fname)
        else:
            out_prefix = self.inputs.out_prefix

        if ext is None:
            ext = fext

        return out_prefix + '_' + name + ext
