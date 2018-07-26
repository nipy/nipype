# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
""" Fixes meshes:
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import os.path as op
from ..utils.filemanip import split_filename
from .base import (CommandLine, CommandLineInputSpec, traits, TraitedSpec,
                   isdefined, File)


class MeshFixInputSpec(CommandLineInputSpec):
    number_of_biggest_shells = traits.Int(
        argstr='--shells %d', desc="Only the N biggest shells are kept")

    epsilon_angle = traits.Range(
        argstr='-a %f',
        low=0.0,
        high=2.0,
        desc="Epsilon angle in degrees (must be between 0 and 2)")

    join_overlapping_largest_components = traits.Bool(
        argstr='-j',
        xor=['join_closest_components'],
        desc='Join 2 biggest components if they overlap, remove the rest.')

    join_closest_components = traits.Bool(
        argstr='-jc',
        xor=['join_closest_components'],
        desc='Join the closest pair of components.')

    quiet_mode = traits.Bool(
        argstr='-q', desc="Quiet mode, don't write much to stdout.")

    dont_clean = traits.Bool(argstr='--no-clean', desc="Don't Clean")

    save_as_stl = traits.Bool(
        xor=['save_as_vmrl', 'save_as_freesurfer_mesh'],
        argstr='--stl',
        desc="Result is saved in stereolithographic format (.stl)")
    save_as_vmrl = traits.Bool(
        argstr='--wrl',
        xor=['save_as_stl', 'save_as_freesurfer_mesh'],
        desc="Result is saved in VRML1.0 format (.wrl)")
    save_as_freesurfer_mesh = traits.Bool(
        argstr='--fsmesh',
        xor=['save_as_vrml', 'save_as_stl'],
        desc="Result is saved in freesurfer mesh format")

    remove_handles = traits.Bool(
        argstr='--remove-handles', desc="Remove handles")

    uniform_remeshing_steps = traits.Int(
        argstr='-u %d',
        requires=['uniform_remeshing_vertices'],
        desc="Number of steps for uniform remeshing of the whole mesh")

    uniform_remeshing_vertices = traits.Int(
        argstr='--vertices %d',
        requires=['uniform_remeshing_steps'],
        desc="Constrains the number of vertices."
        "Must be used with uniform_remeshing_steps")

    laplacian_smoothing_steps = traits.Int(
        argstr='--smooth %d',
        desc="The number of laplacian smoothing steps to apply")

    x_shift = traits.Int(
        argstr='--smooth %d',
        desc=
        "Shifts the coordinates of the vertices when saving. Output must be in FreeSurfer format"
    )

    # Cutting, decoupling, dilation
    cut_outer = traits.Int(
        argstr='--cut-outer %d',
        desc="Remove triangles of 1st that are outside of the 2nd shell.")
    cut_inner = traits.Int(
        argstr='--cut-inner %d',
        desc=
        "Remove triangles of 1st that are inside of the 2nd shell. Dilate 2nd by N; Fill holes and keep only 1st afterwards."
    )
    decouple_inin = traits.Int(
        argstr='--decouple-inin %d',
        desc="Treat 1st file as inner, 2nd file as outer component."
        "Resolve overlaps by moving inners triangles inwards. Constrain the min distance between the components > d."
    )
    decouple_outin = traits.Int(
        argstr='--decouple-outin %d',
        desc="Treat 1st file as outer, 2nd file as inner component."
        "Resolve overlaps by moving outers triangles inwards. Constrain the min distance between the components > d."
    )
    decouple_outout = traits.Int(
        argstr='--decouple-outout %d',
        desc="Treat 1st file as outer, 2nd file as inner component."
        "Resolve overlaps by moving outers triangles outwards. Constrain the min distance between the components > d."
    )

    finetuning_inwards = traits.Bool(
        argstr='--fineTuneIn ',
        requires=['finetuning_distance', 'finetuning_substeps'])
    finetuning_outwards = traits.Bool(
        argstr='--fineTuneIn ',
        requires=['finetuning_distance', 'finetuning_substeps'],
        xor=['finetuning_inwards'],
        desc=
        'Similar to finetuning_inwards, but ensures minimal distance in the other direction'
    )
    finetuning_distance = traits.Float(
        argstr='%f',
        requires=['finetuning_substeps'],
        desc="Used to fine-tune the minimal distance between surfaces."
        "A minimal distance d is ensured, and reached in n substeps. When using the surfaces for subsequent volume meshing by gmsh, this step prevent too flat tetrahedra2)"
    )
    finetuning_substeps = traits.Int(
        argstr='%d',
        requires=['finetuning_distance'],
        desc="Used to fine-tune the minimal distance between surfaces."
        "A minimal distance d is ensured, and reached in n substeps. When using the surfaces for subsequent volume meshing by gmsh, this step prevent too flat tetrahedra2)"
    )

    dilation = traits.Int(
        argstr='--dilate %d',
        desc="Dilate the surface by d. d < 0 means shrinking.")
    set_intersections_to_one = traits.Bool(
        argstr='--intersect',
        desc="If the mesh contains intersections, return value = 1."
        "If saved in gmsh format, intersections will be highlighted.")

    in_file1 = File(exists=True, argstr="%s", position=1, mandatory=True)
    in_file2 = File(exists=True, argstr="%s", position=2)
    output_type = traits.Enum(
        'off', ['stl', 'msh', 'wrl', 'vrml', 'fs', 'off'],
        usedefault=True,
        desc='The output type to save the file as.')
    out_filename = File(
        genfile=True,
        argstr="-o %s",
        desc='The output filename for the fixed mesh file')


class MeshFixOutputSpec(TraitedSpec):
    mesh_file = File(exists=True, desc='The output mesh file')


class MeshFix(CommandLine):
    """
    MeshFix v1.2-alpha - by Marco Attene, Mirko Windhoff, Axel Thielscher.

    .. seealso::

        http://jmeshlib.sourceforge.net
            Sourceforge page

        http://simnibs.de/installation/meshfixandgetfem
            Ubuntu installation instructions

    If MeshFix is used for research purposes, please cite the following paper:
    M. Attene - A lightweight approach to repairing digitized polygon meshes.
    The Visual Computer, 2010. (c) Springer.

    Accepted input formats are OFF, PLY and STL.
    Other formats (like .msh for gmsh) are supported only partially.

    Example
    -------

    >>> import nipype.interfaces.meshfix as mf
    >>> fix = mf.MeshFix()
    >>> fix.inputs.in_file1 = 'lh-pial.stl'
    >>> fix.inputs.in_file2 = 'rh-pial.stl'
    >>> fix.run()                                    # doctest: +SKIP
    >>> fix.cmdline
    'meshfix lh-pial.stl rh-pial.stl -o lh-pial_fixed.off'
    """
    _cmd = 'meshfix'
    input_spec = MeshFixInputSpec
    output_spec = MeshFixOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_filename):
            path, name, ext = split_filename(self.inputs.out_filename)
            ext = ext.replace('.', '')
            out_types = ['stl', 'msh', 'wrl', 'vrml', 'fs', 'off']
            # Make sure that the output filename uses one of the possible file types
            if any(ext == out_type.lower() for out_type in out_types):
                outputs['mesh_file'] = op.abspath(self.inputs.out_filename)
            else:
                outputs['mesh_file'] = op.abspath(
                    name + '.' + self.inputs.output_type)
        else:
            outputs['mesh_file'] = op.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name == 'out_filename':
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file1)
        if self.inputs.save_as_freesurfer_mesh or self.inputs.output_type == 'fs':
            self.inputs.output_type = 'fs'
            self.inputs.save_as_freesurfer_mesh = True
        if self.inputs.save_as_stl or self.inputs.output_type == 'stl':
            self.inputs.output_type = 'stl'
            self.inputs.save_as_stl = True
        if self.inputs.save_as_vmrl or self.inputs.output_type == 'vmrl':
            self.inputs.output_type = 'vmrl'
            self.inputs.save_as_vmrl = True
        return name + '_fixed.' + self.inputs.output_type
