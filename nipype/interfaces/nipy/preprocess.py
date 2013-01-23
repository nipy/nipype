"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)

"""
import os
import warnings

import nibabel as nb
import numpy as np

from ...utils.misc import package_check
from ...utils.filemanip import split_filename, fname_presuffix


try:
    package_check('nipy')
except Exception, e:
    warnings.warn('nipy not installed')
else:
    from nipy.labs.mask import compute_mask
    from nipy.algorithms.registration import FmriRealign4d as FR4d
    from nipy import save_image, load_image

from ..base import (TraitedSpec, BaseInterface, traits,
                    BaseInterfaceInputSpec, isdefined, File,
                    InputMultiPath, OutputMultiPath)


class ComputeMaskInputSpec(BaseInterfaceInputSpec):
    mean_volume = File(exists=True, mandatory=True,
                       desc="mean EPI image, used to compute the threshold for the mask")
    reference_volume = File(exists=True,
                            desc=("reference volume used to compute the mask. "
                                  "If none is give, the mean volume is used."))
    m = traits.Float(desc="lower fraction of the histogram to be discarded")
    M = traits.Float(desc="upper fraction of the histogram to be discarded")
    cc = traits.Bool(desc="Keep only the largest connected component")


class ComputeMaskOutputSpec(TraitedSpec):
    brain_mask = File(exists=True)


class ComputeMask(BaseInterface):
    input_spec = ComputeMaskInputSpec
    output_spec = ComputeMaskOutputSpec

    def _run_interface(self, runtime):

        args = {}
        for key in [k for k, _ in self.inputs.items()
                    if k not in BaseInterfaceInputSpec().trait_names()]:
            value = getattr(self.inputs, key)
            if isdefined(value):
                if key in ['mean_volume', 'reference_volume']:
                    nii = nb.load(value)
                    value = nii.get_data()
                args[key] = value

        brain_mask = compute_mask(**args)
        _, name, ext = split_filename(self.inputs.mean_volume)
        self._brain_mask_path = os.path.abspath("%s_mask.%s" % (name, ext))
        nb.save(nb.Nifti1Image(brain_mask.astype(np.uint8),
                nii.get_affine()), self._brain_mask_path)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["brain_mask"] = self._brain_mask_path
        return outputs


class FmriRealign4dInputSpec(BaseInterfaceInputSpec):

    in_file = InputMultiPath(exists=True,
                             mandatory=True,
                             desc="File to realign")
    tr = traits.Float(desc="TR in seconds",
                      mandatory=True)
    slice_order = traits.List(traits.Int(),
                              desc='0 based slice order',
                              requires=["time_interp"])
    tr_slices = traits.Float(desc="TR slices", requires=['time_interp'])
    start = traits.Float(0.0, usedefault=True,
                         desc="time offset into TR to align slices to")
    time_interp = traits.Enum(True, requires=["slice_order"],
                              desc="Assume smooth changes across time e.g.,\
                     fmri series. If you don't want slice timing \
                     correction set this to undefined")
    loops = InputMultiPath([5], traits.Int, usedefault=True,
                           desc="loops within each run")
    between_loops = InputMultiPath([5], traits.Int,
                                   usedefault=True, desc="loops used to \
                                                          realign different \
                                                          runs")
    speedup = InputMultiPath([5], traits.Int,
                             usedefault=True,
                             desc="successive image \
                                  sub-sampling factors \
                                  for acceleration")


class FmriRealign4dOutputSpec(TraitedSpec):

    out_file = OutputMultiPath(File(exists=True),
                               desc="Realigned files")
    par_file = OutputMultiPath(File(exists=True),
                               desc="Motion parameter files")


class FmriRealign4d(BaseInterface):
    """Simultaneous motion and slice timing correction algorithm

    This interface wraps nipy's FmriRealign4d algorithm [1]_.

    Examples
    --------
    >>> from nipype.interfaces.nipy.preprocess import FmriRealign4d
    >>> realigner = FmriRealign4d()
    >>> realigner.inputs.in_file = ['functional.nii']
    >>> realigner.inputs.tr = 2
    >>> realigner.inputs.slice_order = range(0,67)
    >>> res = realigner.run() # doctest: +SKIP

    References
    ----------
    .. [1] Roche A. A four-dimensional registration algorithm with \
       application to joint correction of motion and slice timing \
       in fMRI. IEEE Trans Med Imaging. 2011 Aug;30(8):1546-54. DOI_.

    .. _DOI: http://dx.doi.org/10.1109/TMI.2011.2131152

    """

    input_spec = FmriRealign4dInputSpec
    output_spec = FmriRealign4dOutputSpec
    keywords = ['slice timing', 'motion correction']

    def _run_interface(self, runtime):

        all_ims = [load_image(fname) for fname in self.inputs.in_file]

        if not isdefined(self.inputs.tr_slices):
            TR_slices = None
        else:
            TR_slices = self.inputs.tr_slices

        R = FR4d(all_ims, tr=self.inputs.tr,
                 slice_order=self.inputs.slice_order,
                 tr_slices=TR_slices,
                 time_interp=self.inputs.time_interp,
                 start=self.inputs.start)

        R.estimate(loops=list(self.inputs.loops),
                   between_loops=list(self.inputs.between_loops),
                   speedup=list(self.inputs.speedup))

        corr_run = R.resample()
        self._out_file_path = []
        self._par_file_path = []

        for j, corr in enumerate(corr_run):
            self._out_file_path.append(os.path.abspath('corr_%s.nii.gz' %
                                      (split_filename(self.inputs.in_file[j])[1])))
            save_image(corr, self._out_file_path[j])

            self._par_file_path.append(os.path.abspath('%s.par' %
                                      (os.path.split(self.inputs.in_file[j])[1])))
            mfile = open(self._par_file_path[j], 'w')
            motion = R._transforms[j]
            # nipy does not encode euler angles. return in original form of
            # translation followed by rotation vector see:
            # http://en.wikipedia.org/wiki/Rodrigues'_rotation_formula
            for i, mo in enumerate(motion):
                params = ['%.10f' % item for item in np.hstack((mo.translation,
                                                                mo.rotation))]
                string = ' '.join(params) + '\n'
                mfile.write(string)
            mfile.close()

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self._out_file_path
        outputs['par_file'] = self._par_file_path
        return outputs


class TrimInputSpec(BaseInterfaceInputSpec):
    in_file = File(
        exists=True, mandatory=True,
        desc="EPI image to trim")
    begin_index = traits.Int(
        0, usedefault=True,
        desc='first volume')
    end_index = traits.Int(
        0, usedefault=True,
        desc='last volume indexed as in python (and 0 for last)')
    out_file = File(desc='output filename')
    suffix = traits.Str(
        '_trim', usedefault=True,
        desc='suffix for out_file to use if no out_file provided')


class TrimOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class Trim(BaseInterface):
    """ Simple interface to trim a few volumes from a 4d fmri nifti file

    Examples
    --------
    >>> from nipype.interfaces.nipy.preprocess import Trim
    >>> trim = Trim()
    >>> trim.inputs.in_file = 'functional.nii'
    >>> trim.inputs.begin_index = 3 # remove 3 first volumes
    >>> res = trim.run() # doctest: +SKIP

    """

    input_spec = TrimInputSpec
    output_spec = TrimOutputSpec

    def _run_interface(self, runtime):
        out_file = self._list_outputs()['out_file']
        nii = nb.load(self.inputs.in_file)
        if self.inputs.end_index == 0:
            s = slice(self.inputs.begin_index, nii.shape[3])
        else:
            s = slice(self.inputs.begin_index, self.inputs.end_index)
        nii2 = nb.Nifti1Image(
            nii.get_data()[..., s],
            nii.get_affine(),
            nii.get_header())
        nb.save(nii2, out_file)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(outputs['out_file']):
            outputs['out_file'] = fname_presuffix(
                self.inputs.in_file,
                newpath=os.getcwd(),
                suffix=self.inputs.suffix)
        outputs['out_file'] = os.path.abspath(outputs['out_file'])
        return outputs
