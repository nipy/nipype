# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# -*- coding: utf-8 -*-
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import os.path as op

from ..base import (CommandLineInputSpec, CommandLine, traits, TraitedSpec,
                    File, InputMultiPath, isdefined)
from .base import MRTrix3BaseInputSpec, MRTrix3Base


class BrainMaskInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr='%s',
        mandatory=True,
        position=-2,
        desc='input diffusion weighted images')
    out_file = File(
        'brainmask.mif',
        argstr='%s',
        mandatory=True,
        position=-1,
        usedefault=True,
        desc='output brain mask')


class BrainMaskOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='the output response file')


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

    _cmd = 'dwi2mask'
    input_spec = BrainMaskInputSpec
    output_spec = BrainMaskOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs


class Mesh2PVEInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr='%s',
        mandatory=True,
        position=-3,
        desc='input mesh')
    reference = File(
        exists=True,
        argstr='%s',
        mandatory=True,
        position=-2,
        desc='input reference image')
    in_first = File(
        exists=True,
        argstr='-first %s',
        desc='indicates that the mesh file is provided by FSL FIRST')

    out_file = File(
        'mesh2volume.nii.gz',
        argstr='%s',
        mandatory=True,
        position=-1,
        usedefault=True,
        desc='output file containing SH coefficients')


class Mesh2PVEOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='the output response file')


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

    _cmd = 'mesh2pve'
    input_spec = Mesh2PVEInputSpec
    output_spec = Mesh2PVEOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs


class Generate5ttInputSpec(MRTrix3BaseInputSpec):
    algorithm = traits.Enum(
        'fsl',
        'gif',
        'freesurfer',
        argstr='%s',
        position=-3,
        mandatory=True,
        desc='tissue segmentation algorithm')
    in_file = File(
        exists=True,
        argstr='%s',
        mandatory=True,
        position=-2,
        desc='input image')
    out_file = File(
        argstr='%s', mandatory=True, position=-1, desc='output image')


class Generate5ttOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='output image')


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

    _cmd = '5ttgen'
    input_spec = Generate5ttInputSpec
    output_spec = Generate5ttOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs


class TensorMetricsInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr='%s',
        mandatory=True,
        position=-1,
        desc='input DTI image')

    out_fa = File(argstr='-fa %s', desc='output FA file')
    out_adc = File(argstr='-adc %s', desc='output ADC file')
    out_evec = File(
        argstr='-vector %s', desc='output selected eigenvector(s) file')
    out_eval = File(
        argstr='-value %s', desc='output selected eigenvalue(s) file')
    component = traits.List(
        [1],
        usedefault=True,
        argstr='-num %s',
        sep=',',
        desc=('specify the desired eigenvalue/eigenvector(s). Note that '
              'several eigenvalues can be specified as a number sequence'))
    in_mask = File(
        exists=True,
        argstr='-mask %s',
        desc=('only perform computation within the specified binary'
              ' brain mask image'))
    modulate = traits.Enum(
        'FA',
        'none',
        'eval',
        argstr='-modulate %s',
        desc=('how to modulate the magnitude of the'
              ' eigenvectors'))


class TensorMetricsOutputSpec(TraitedSpec):
    out_fa = File(desc='output FA file')
    out_adc = File(desc='output ADC file')
    out_evec = File(desc='output selected eigenvector(s) file')
    out_eval = File(desc='output selected eigenvalue(s) file')


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

    _cmd = 'tensor2metric'
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
        exists=True,
        argstr='%s',
        mandatory=True,
        position=-2,
        desc='input tractography')
    out_file = File(
        'tdi.mif',
        argstr='%s',
        usedefault=True,
        position=-1,
        desc='output TDI file')
    reference = File(
        exists=True,
        argstr='-template %s',
        desc='a reference'
        'image to be used as template')
    vox_size = traits.List(
        traits.Int, argstr='-vox %s', sep=',', desc='voxel dimensions')
    data_type = traits.Enum(
        'float',
        'unsigned int',
        argstr='-datatype %s',
        desc='specify output image data type')
    use_dec = traits.Bool(argstr='-dec', desc='perform mapping in DEC space')
    dixel = File(
        argstr='-dixel %s',
        desc='map streamlines to'
        'dixels within each voxel. Directions are stored as'
        'azimuth elevation pairs.')
    max_tod = traits.Int(
        argstr='-tod %d',
        desc='generate a Track Orientation '
        'Distribution (TOD) in each voxel.')

    contrast = traits.Enum(
        'tdi',
        'length',
        'invlength',
        'scalar_map',
        'scalar_map_conut',
        'fod_amp',
        'curvature',
        argstr='-constrast %s',
        desc='define the desired '
        'form of contrast for the output image')
    in_map = File(
        exists=True,
        argstr='-image %s',
        desc='provide the'
        'scalar image map for generating images with '
        '\'scalar_map\' contrasts, or the SHs image for fod_amp')

    stat_vox = traits.Enum(
        'sum',
        'min',
        'mean',
        'max',
        argstr='-stat_vox %s',
        desc='define the statistic for choosing the final'
        'voxel intesities for a given contrast')
    stat_tck = traits.Enum(
        'mean',
        'sum',
        'min',
        'max',
        'median',
        'mean_nonzero',
        'gaussian',
        'ends_min',
        'ends_mean',
        'ends_max',
        'ends_prod',
        argstr='-stat_tck %s',
        desc='define the statistic for choosing '
        'the contribution to be made by each streamline as a function of'
        ' the samples taken along their lengths.')

    fwhm_tck = traits.Float(
        argstr='-fwhm_tck %f',
        desc='define the statistic for choosing the'
        ' contribution to be made by each streamline as a function of the '
        'samples taken along their lengths')

    map_zero = traits.Bool(
        argstr='-map_zero',
        desc='if a streamline has zero contribution based '
        'on the contrast & statistic, typically it is not mapped; use this '
        'option to still contribute to the map even if this is the case '
        '(these non-contributing voxels can then influence the mean value in '
        'each voxel of the map)')

    upsample = traits.Int(
        argstr='-upsample %d',
        desc='upsample the tracks by'
        ' some ratio using Hermite interpolation before '
        'mappping')

    precise = traits.Bool(
        argstr='-precise',
        desc='use a more precise streamline mapping '
        'strategy, that accurately quantifies the length through each voxel '
        '(these lengths are then taken into account during TWI calculation)')
    ends_only = traits.Bool(
        argstr='-ends_only',
        desc='only map the streamline'
        ' endpoints to the image')

    tck_weights = File(
        exists=True,
        argstr='-tck_weights_in %s',
        desc='specify'
        ' a text scalar file containing the streamline weights')
    nthreads = traits.Int(
        argstr='-nthreads %d',
        desc='number of threads. if zero, the number'
        ' of available cpus will be used',
        nohash=True)


class ComputeTDIOutputSpec(TraitedSpec):
    out_file = File(desc='output TDI file')


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

    _cmd = 'tckmap'
    input_spec = ComputeTDIInputSpec
    output_spec = ComputeTDIOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs


class TCK2VTKInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr='%s',
        mandatory=True,
        position=-2,
        desc='input tractography')
    out_file = File(
        'tracks.vtk',
        argstr='%s',
        usedefault=True,
        position=-1,
        desc='output VTK file')
    reference = File(
        exists=True,
        argstr='-image %s',
        desc='if specified, the properties of'
        ' this image will be used to convert track point positions from real '
        '(scanner) coordinates into image coordinates (in mm).')
    voxel = File(
        exists=True,
        argstr='-image %s',
        desc='if specified, the properties of'
        ' this image will be used to convert track point positions from real '
        '(scanner) coordinates into image coordinates.')

    nthreads = traits.Int(
        argstr='-nthreads %d',
        desc='number of threads. if zero, the number'
        ' of available cpus will be used',
        nohash=True)


class TCK2VTKOutputSpec(TraitedSpec):
    out_file = File(desc='output VTK file')


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

    _cmd = 'tck2vtk'
    input_spec = TCK2VTKInputSpec
    output_spec = TCK2VTKOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs


class DWIExtractInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr='%s',
        mandatory=True,
        position=-2,
        desc='input image')
    out_file = File(
        argstr='%s', mandatory=True, position=-1, desc='output image')
    bzero = traits.Bool(argstr='-bzero', desc='extract b=0 volumes')
    nobzero = traits.Bool(argstr='-no_bzero', desc='extract non b=0 volumes')
    singleshell = traits.Bool(
        argstr='-singleshell', desc='extract volumes with a specific shell')
    shell = traits.List(
        traits.Float,
        sep=',',
        argstr='-shell %s',
        desc='specify one or more gradient shells')


class DWIExtractOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='output image')


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

    _cmd = 'dwiextract'
    input_spec = DWIExtractInputSpec
    output_spec = DWIExtractOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs


class MRConvertInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr='%s',
        mandatory=True,
        position=-2,
        desc='input image')
    out_file = File(
        'dwi.mif',
        argstr='%s',
        mandatory=True,
        position=-1,
        usedefault=True,
        desc='output image')
    coord = traits.List(
        traits.Float,
        sep=' ',
        argstr='-coord %s',
        desc='extract data at the specified coordinates')
    vox = traits.List(
        traits.Float,
        sep=',',
        argstr='-vox %s',
        desc='change the voxel dimensions')
    axes = traits.List(
        traits.Int,
        sep=',',
        argstr='-axes %s',
        desc='specify the axes that will be used')
    scaling = traits.List(
        traits.Float,
        sep=',',
        argstr='-scaling %s',
        desc='specify the data scaling parameter')


class MRConvertOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='output image')


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

    _cmd = 'mrconvert'
    input_spec = MRConvertInputSpec
    output_spec = MRConvertOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs


class MRMathInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr='%s',
        mandatory=True,
        position=-3,
        desc='input image')
    out_file = File(
        argstr='%s', mandatory=True, position=-1, desc='output image')
    operation = traits.Enum(
        'mean',
        'median',
        'sum',
        'product',
        'rms',
        'norm',
        'var',
        'std',
        'min',
        'max',
        'absmax',
        'magmax',
        argstr='%s',
        position=-2,
        mandatory=True,
        desc='operation to computer along a specified axis')
    axis = traits.Int(
        0,
        argstr='-axis %d',
        desc='specfied axis to perform the operation along')


class MRMathOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='output image')


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

    _cmd = 'mrmath'
    input_spec = MRMathInputSpec
    output_spec = MRMathOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs
