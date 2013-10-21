# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
""" Fixes meshes:

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
    >>> os.chdir(datadir)

"""
from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
                                    traits, TraitedSpec, isdefined,
                                    File)
import os
import os.path as op
from nipype.utils.filemanip import split_filename

def mask_from_labels_fn(in_file, label_values):
    import os.path as op
    import numpy as np
    import nibabel as nb
    from nipype.utils.filemanip import split_filename

    _, name, ext = split_filename(in_file)
    in_file = nb.load(in_file)
    in_data = in_file.get_data()
    new_data = np.zeros(in_data.shape)
    for label in label_values:
        new_data[in_data == label] = 1

    new_image = nb.Nifti1Image(data=new_data,
                               affine=in_file.get_affine(), header=in_file.get_header())
    out_file = op.abspath(name + "_mask" + ext)
    nb.save(new_image, out_file)
    return out_file


def check_intersecting_fn(mesh1, mesh2):
    import subprocess
    from subprocess import CalledProcessError
    intersecting = False
    args = ['meshfix']
    args.append(mesh1)
    args.append(mesh2)
    args.extend(["--shells", "2", "--no-clean", "--intersect"])

    try:
        output = subprocess.check_output(args)
        intersecting = True
    except subprocess.CalledProcessError:
        # No intersections
        intersecting = False
    return intersecting


def cut_inner_fn(outer_mesh, inner_mesh):
    import subprocess
    from subprocess import CalledProcessError
    from nipype.utils.filemanip import split_filename
    import os.path as op
    path, name, ext = split_filename(outer_mesh)
    cut_mesh = op.join(path, name + "_CI.off")
    args = ['meshfix']
    args.extend([outer_mesh, inner_mesh])
    args.extend(["-a", "2.0", "--shells", "2", "--cut-inner", "0"])
    args.extend(["-o", cut_mesh])
    try:
        subprocess.call(args)
    except:
        print("Something went wrong")
    return cut_mesh


def cut_outer_fn(inner_mesh, outer_mesh):
    import subprocess
    from subprocess import CalledProcessError
    from nipype.utils.filemanip import split_filename
    import os.path as op
    path, name, ext = split_filename(inner_mesh)
    cut_mesh = op.join(path, name + "_CO.off")
    args = ['meshfix']
    args.extend([inner_mesh, outer_mesh])
    args.extend(["-a", "2.0", "--shells", "2", "--cut-outer", "0"])
    args.extend(["-o", cut_mesh])
    try:
        subprocess.call(args)
    except:
        print("Something went wrong")
    return cut_mesh


def decouple_outout_fn(outer_mesh, inner_mesh):
    import subprocess
    from subprocess import CalledProcessError
    from nipype.utils.filemanip import split_filename
    import os.path as op
    path, name, ext = split_filename(outer_mesh)
    cut_mesh = op.join(path, name + "_DOO.off")
    args = ['meshfix']
    args.extend([outer_mesh, inner_mesh])
    args.extend(["-a", "2.0", "--shells", "2", "--decouple-outout", "0"])
    args.extend(["-o", cut_mesh])
    try:
        subprocess.call(args)
    except:
        print("Something went wrong")
    return cut_mesh


def decouple_inin_fn(inner_mesh, outer_mesh):
    import subprocess
    from subprocess import CalledProcessError
    from nipype.utils.filemanip import split_filename
    import os.path as op
    path, name, ext = split_filename(inner_mesh)
    cut_mesh = op.join(path, name + "_DII.off")
    args = ['meshfix']
    args.extend([inner_mesh, outer_mesh])
    args.extend(["-a", "2.0", "--shells", "2", "--decouple-inin", "0"])
    args.extend(["-o", cut_mesh])
    try:
        subprocess.call(args)
    except:
        print("Something went wrong")
    return cut_mesh

def decouple_outin_fn(inner_mesh, outer_mesh):
    import subprocess
    from subprocess import CalledProcessError
    from nipype.utils.filemanip import split_filename
    import os.path as op
    path, name, ext = split_filename(inner_mesh)
    cut_mesh = op.join(path, name + "_DOI.off")
    args = ['meshfix']
    args.extend([inner_mesh, outer_mesh])
    args.extend(["-a", "2.0", "--shells", "2", "--decouple-outin", "0"])
    args.extend(["-o", cut_mesh])
    try:
        subprocess.call(args)
    except:
        print("Something went wrong")
    return cut_mesh


def clean_mesh_fn(mesh_file):
    import subprocess
    from subprocess import CalledProcessError
    from nipype.utils.filemanip import split_filename
    import os.path as op
    path, name, ext = split_filename(mesh_file)
    cleaned1 = op.join(path, name + "_c1.off")
    cleaned2 = op.join(path, name + "_c2.off")
    args1 = ['meshfix']
    args1.append(mesh_file)
    args1.extend(["-a", "2.0", "-u", "1", "-q"])
    args1.extend(["-o", cleaned1])

    args2 = ['meshfix']
    args2.append(cleaned1)
    args2.extend(["-a", "2.0", "-q"])
    args2.extend(["-o", cleaned2])
    try:
        subprocess.call(args1)
        subprocess.call(args2)
    except:
        print("Something went wrong")
    return cleaned2


def decouple_and_cut_inner_fn(outer_mesh, inner_mesh):
    outer_mesh = decouple_outout_fn(outer_mesh, inner_mesh)
    outer_mesh = cut_inner_fn(outer_mesh, inner_mesh)
    return outer_mesh


def decouple_surfaces_fn(outer_mesh, inner_mesh):
    # This function loops until outer_mesh and inner_mesh
    # have no intersections.
    # At each iteration it pushes outer_mesh out, cuts parts of
    # the inner_mesh away, and cleans the mesh.
    # The pushing out is also iterative.
    #
    from nipype.interfaces.meshfix import (
        iter_push_out_fn, check_intersecting_fn,
        cut_inner_fn, clean_mesh_fn)

    for i in range(0, 2):
        intersections = check_intersecting_fn(outer_mesh, inner_mesh)
        if intersections:
            outer_mesh = iter_push_out_fn(outer_mesh, inner_mesh, iterations=3)
            outer_mesh = cut_inner_fn(outer_mesh, inner_mesh)
            outer_mesh = clean_mesh_fn(outer_mesh)
        else:
            break
    return outer_mesh


def iter_remove_throats_fn(outer_mesh, inner_mesh, iterations=5):
    # This function loops until there are no
    # intersections between two surfaces.
    # It cuts away the inner surface and
    # uses decouple_outout:
    #
    # "Treat 1st file as outer, 2nd file as inner component.
    ## "Resolve overlaps by moving outers triangles outwards."
    ## "Constrain the min distance between the components > d."
    #
    # and cut-inner:
    #
    ## "Remove triangles of 1st that are inside  of the 2nd shell."
    ## "Dilate 2nd by d; Fill holes and keep only 1st afterwards."
    #
    # at each iteration.
    from nipype.interfaces.meshfix import (check_intersecting_fn,
                                           decouple_and_cut_inner_fn)
    for i in range(0, iterations):
        intersections = check_intersecting_fn(outer_mesh, inner_mesh)
        if intersections:
            outer_mesh = decouple_and_cut_inner_fn(outer_mesh, inner_mesh)
        else:
            break
    return outer_mesh


def iter_push_out_fn(outer_mesh, inner_mesh, iterations=5):
    # This function loops until there are no
    # intersections between two surfaces.
    # It cuts away the inner surface and
    # uses decouple_outout:
    #
    # "Treat 1st file as outer, 2nd file as inner component.
    ## "Resolve overlaps by moving outers triangles outwards."
    ## "Constrain the min distance between the components > d."
    #
    # at each iteration.
    from nipype.interfaces.meshfix import (check_intersecting_fn,
                                           decouple_outout_fn)
    for i in range(0, iterations):
        intersecting = check_intersecting_fn(outer_mesh, inner_mesh)
        if intersecting:
            outer_mesh = decouple_outout_fn(outer_mesh, inner_mesh)
        else:
            break
    return outer_mesh


def iter_decoupling_fn(outer_mesh, inner_mesh):
    from nipype.interfaces.meshfix import (check_intersecting_fn,
                                           cut_inner_fn, decouple_outout_fn, clean_mesh_fn)

    intersections = check_intersecting_fn(outer_mesh, inner_mesh)
    while(intersections):
        for i in range(0, 3):
            intersections = check_intersecting_fn(outer_mesh, inner_mesh)
            if intersections:
                outer_mesh = decouple_outout_fn(outer_mesh, inner_mesh)
            else:
                break
            outer_mesh = cut_inner_fn(outer_mesh, inner_mesh)
            outer_mesh = clean_mesh_fn(outer_mesh)
    return outer_mesh


def remove_spikes_fn(outer_mesh, inner_mesh):
    from nipype.interfaces.meshfix import (check_intersecting_fn,
                                           cut_outer_fn, decouple_inin_fn, clean_mesh_fn)

    intersections = check_intersecting_fn(outer_mesh, inner_mesh)
    if intersections:
        inner_mesh = cut_outer_fn(inner_mesh, outer_mesh)
        inner_mesh = clean_mesh_fn(inner_mesh)

        for i in xrange(0, 3):
            intersections = check_intersecting_fn(outer_mesh, inner_mesh)
            if intersections:
                inner_mesh = decouple_inin_fn(inner_mesh, outer_mesh)
                inner_mesh = clean_mesh_fn(inner_mesh)
            else:
                break
    return inner_mesh


def decouple_ventricles_fn(ventricles, white_matter):
    from nipype.interfaces.meshfix import (check_intersecting_fn,
                                           cut_outer_fn, decouple_inin_fn, clean_mesh_fn)

    intersections = check_intersecting_fn(white_matter, ventricles)
    while(intersections):
        ventricles = decouple_inin_fn(ventricles, white_matter)
        ventricles = cut_outer_fn(ventricles, white_matter)
        ventricles = clean_mesh_fn(ventricles)
        intersections = check_intersecting_fn(white_matter, ventricles)
    return ventricles

def decouple_input_from_GM_fn(mesh_file, gray_matter):
    from nipype.interfaces.meshfix import (check_intersecting_fn,
                                           cut_outer_fn, decouple_outin_fn, clean_mesh_fn)

    intersections = check_intersecting_fn(gray_matter, mesh_file)
    while(intersections):
        mesh_file = decouple_outin_fn(mesh_file, gray_matter)
        mesh_file = cut_outer_fn(mesh_file, gray_matter)
        mesh_file = clean_mesh_fn(mesh_file)
        intersections = check_intersecting_fn(gray_matter, mesh_file)
    return mesh_file


def decouple_outout_cutin_fn(outer_mesh, inner_mesh):
    from nipype.interfaces.meshfix import (check_intersecting_fn,
                                           cut_inner_fn, decouple_outout_fn, clean_mesh_fn)

    intersections = check_intersecting_fn(outer_mesh, inner_mesh)
    while(intersections):
        outer_mesh = decouple_outout_fn(outer_mesh, inner_mesh)
        outer_mesh = cut_inner_fn(outer_mesh, inner_mesh)
        outer_mesh = clean_mesh_fn(outer_mesh)
        intersections = check_intersecting_fn(outer_mesh, inner_mesh)
    return outer_mesh


class MeshFixInputSpec(CommandLineInputSpec):
    number_of_biggest_shells = traits.Int(
        argstr='--shells %d', desc="Only the N biggest shells are kept")

    epsilon_angle = traits.Range(
        argstr='-a %f', low=0.0, high=2.0, desc="Epsilon angle in degrees (must be between 0 and 2)")

    join_overlapping_largest_components = traits.Bool(
        argstr='-j', xor=['join_closest_components'], desc='Join 2 biggest components if they overlap, remove the rest.')

    join_closest_components = traits.Bool(
        argstr='-jc', xor=['join_closest_components'], desc='Join the closest pair of components.')

    quiet_mode = traits.Bool(
        argstr='-q', desc="Quiet mode, don't write much to stdout.")

    dont_clean = traits.Bool(argstr='--no-clean', desc="Don't Clean")

    save_as_stl = traits.Bool(xor=['save_as_vrml', 'save_as_freesurfer_mesh'],
                              argstr='--stl', desc="Result is saved in stereolithographic format (.stl)")
    save_as_vrml = traits.Bool(argstr='--wrl', xor=[
                               'save_as_stl', 'save_as_freesurfer_mesh'], desc="Result is saved in VRML1.0 format (.wrl)")
    save_as_freesurfer_mesh = traits.Bool(argstr='--fsmesh', xor=[
                                          'save_as_vrml', 'save_as_stl'], desc="Result is saved in freesurfer mesh format")

    remove_handles = traits.Bool(
        argstr='--remove-handles', desc="Remove handles")

    uniform_remeshing_steps = traits.Int(
        argstr='-u %d', desc="Number of steps for uniform remeshing of the whole mesh")

    uniform_remeshing_vertices = traits.Int(argstr='--vertices %d', requires=['uniform_remeshing_steps'], desc="Constrains the number of vertices."
                                            "Must be used with uniform_remeshing_steps")

    laplacian_smoothing_steps = traits.Int(
        argstr='--smooth %d', desc="The number of laplacian smoothing steps to apply")

    x_shift = traits.Int(
        argstr='--smooth %d', desc="Shifts the coordinates of the vertices when saving. Output must be in FreeSurfer format")

    # Cutting, decoupling, dilation
    cut_outer = traits.Int(
        argstr='--cut-outer %d', desc="Remove triangles of 1st that are outside of the 2nd shell.")
    cut_inner = traits.Int(
        argstr='--cut-inner %d', desc="Remove triangles of 1st that are inside of the 2nd shell. Dilate 2nd by N; Fill holes and keep only 1st afterwards.")
    decouple_inin = traits.Int(argstr='--decouple-inin %d', desc="Treat 1st file as inner, 2nd file as outer component."
                               "Resolve overlaps by moving inners triangles inwards. Constrain the min distance between the components > d.")
    decouple_outin = traits.Int(argstr='--decouple-outin %d', desc="Treat 1st file as outer, 2nd file as inner component."
                                "Resolve overlaps by moving outers triangles inwards. Constrain the min distance between the components > d.")
    decouple_outout = traits.Int(argstr='--decouple-outout %d', desc="Treat 1st file as outer, 2nd file as inner component."
                                 "Resolve overlaps by moving outers triangles outwards. Constrain the min distance between the components > d.")

    finetuning_inwards = traits.Bool(
        argstr='--fineTuneIn ', position=-4, requires=['finetuning_distance', 'finetuning_substeps'])
    finetuning_outwards = traits.Bool(
        argstr='--fineTuneIn ', position=-4, requires=['finetuning_distance', 'finetuning_substeps'], xor=['finetuning_inwards'],
        desc='Similar to finetuning_inwards, but ensures minimal distance in the other direction')
    finetuning_distance = traits.Float(argstr='%f', position=-3, requires=['finetuning_substeps'], desc="Used to fine-tune the minimal distance between surfaces."
                                       "A minimal distance d is ensured, and reached in n substeps. When using the surfaces for subsequent volume meshing by gmsh, this step prevent too flat tetrahedra2)")
    finetuning_substeps = traits.Int(argstr='%d', position=-2, requires=['finetuning_distance'], desc="Used to fine-tune the minimal distance between surfaces."
                                     "A minimal distance d is ensured, and reached in n substeps. When using the surfaces for subsequent volume meshing by gmsh, this step prevent too flat tetrahedra2)")

    dilation = traits.Int(
        argstr='--dilate %d', desc="Dilate the surface by d. d < 0 means shrinking.")
    set_intersections_to_one = traits.Bool(argstr='--intersect', desc="If the mesh contains intersections, return value = 1."
                                           "If saved in gmsh format, intersections will be highlighted.")

    in_file1 = File(exists=True, argstr="%s", position=1, mandatory=True)
    in_file2 = File(exists=True, argstr="%s", position=2)
    output_type = traits.Enum(
        'off', ['stl', 'msh', 'wrl', 'vrml', 'fsmesh', 'off'], usedefault=True, desc='The output type to save the file as.')
    out_filename = File(genfile=True, argstr="-o %s", position=-1,
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
    """
    _cmd = 'meshfix'
    input_spec = MeshFixInputSpec
    output_spec = MeshFixOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_filename):
            path, name, ext = split_filename(self.inputs.out_filename)
            ext = ext.replace('.', '')
            out_types = ['stl', 'msh', 'wrl', 'vrml', 'fsmesh', 'off']
            # Make sure that the output filename uses one of the possible file
            # types
            if any(ext == out_type.lower() for out_type in out_types):
                outputs['mesh_file'] = op.abspath(self.inputs.out_filename)
            else:
                outputs['mesh_file'] = op.abspath(
                    name + '.' + self.inputs.output_type)
        else:
            outputs['mesh_file'] = op.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file1)
        if self.inputs.save_as_freesurfer_mesh or self.inputs.output_type == 'fsmesh':
            self.inputs.output_type = 'fsmesh'
            self.inputs.save_as_freesurfer_mesh = True
        if self.inputs.save_as_stl or self.inputs.output_type == 'stl':
            self.inputs.output_type = 'stl'
            self.inputs.save_as_stl = True
        if self.inputs.save_as_vrml or self.inputs.output_type == 'vrml':
            self.inputs.output_type = 'vrml'
            self.inputs.save_as_vrml = True
        return op.abspath(name + '_fixed.' + self.inputs.output_type)
