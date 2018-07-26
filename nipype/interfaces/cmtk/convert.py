# -*- coding: utf-8 -*-
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import os
import os.path as op
import datetime
import string
import networkx as nx

from ...utils.filemanip import split_filename
from ..base import (BaseInterfaceInputSpec, traits, File,
                    TraitedSpec, InputMultiPath, isdefined)
from .base import CFFBaseInterface, have_cfflib


class CFFConverterInputSpec(BaseInterfaceInputSpec):
    graphml_networks = InputMultiPath(
        File(exists=True), desc='list of graphML networks')
    gpickled_networks = InputMultiPath(
        File(exists=True), desc='list of gpickled Networkx graphs')

    gifti_surfaces = InputMultiPath(
        File(exists=True), desc='list of GIFTI surfaces')
    gifti_labels = InputMultiPath(
        File(exists=True), desc='list of GIFTI labels')
    nifti_volumes = InputMultiPath(
        File(exists=True), desc='list of NIFTI volumes')
    tract_files = InputMultiPath(
        File(exists=True), desc='list of Trackvis fiber files')

    timeseries_files = InputMultiPath(
        File(exists=True), desc='list of HDF5 timeseries files')
    script_files = InputMultiPath(
        File(exists=True), desc='list of script files to include')
    data_files = InputMultiPath(
        File(exists=True),
        desc='list of external data files (i.e. Numpy, HD5, XML) ')

    title = traits.Str(desc='Connectome Title')
    creator = traits.Str(desc='Creator')
    email = traits.Str(desc='Email address')
    publisher = traits.Str(desc='Publisher')
    license = traits.Str(desc='License')
    rights = traits.Str(desc='Rights')
    references = traits.Str(desc='References')
    relation = traits.Str(desc='Relation')
    species = traits.Str('Homo sapiens', desc='Species', usedefault=True)
    description = traits.Str(
        'Created with the Nipype CFF converter',
        desc='Description',
        usedefault=True)

    out_file = File(
        'connectome.cff', usedefault=True, desc='Output connectome file')


class CFFConverterOutputSpec(TraitedSpec):
    connectome_file = File(exists=True, desc='Output connectome file')


class CFFConverter(CFFBaseInterface):
    """
    Creates a Connectome File Format (CFF) file from input networks, surfaces, volumes, tracts, etcetera....

    Example
    -------

    >>> import nipype.interfaces.cmtk as cmtk
    >>> cvt = cmtk.CFFConverter()
    >>> cvt.inputs.title = 'subject 1'
    >>> cvt.inputs.gifti_surfaces = ['lh.pial_converted.gii', 'rh.pial_converted.gii']
    >>> cvt.inputs.tract_files = ['streamlines.trk']
    >>> cvt.inputs.gpickled_networks = ['network0.gpickle']
    >>> cvt.run()                 # doctest: +SKIP
    """

    input_spec = CFFConverterInputSpec
    output_spec = CFFConverterOutputSpec

    def _run_interface(self, runtime):
        import cfflib as cf
        a = cf.connectome()

        if isdefined(self.inputs.title):
            a.connectome_meta.set_title(self.inputs.title)
        else:
            a.connectome_meta.set_title(self.inputs.out_file)

        if isdefined(self.inputs.creator):
            a.connectome_meta.set_creator(self.inputs.creator)
        else:
            # Probably only works on some OSes...
            a.connectome_meta.set_creator(os.getenv('USER'))

        if isdefined(self.inputs.email):
            a.connectome_meta.set_email(self.inputs.email)

        if isdefined(self.inputs.publisher):
            a.connectome_meta.set_publisher(self.inputs.publisher)

        if isdefined(self.inputs.license):
            a.connectome_meta.set_license(self.inputs.license)

        if isdefined(self.inputs.rights):
            a.connectome_meta.set_rights(self.inputs.rights)

        if isdefined(self.inputs.references):
            a.connectome_meta.set_references(self.inputs.references)

        if isdefined(self.inputs.relation):
            a.connectome_meta.set_relation(self.inputs.relation)

        if isdefined(self.inputs.species):
            a.connectome_meta.set_species(self.inputs.species)

        if isdefined(self.inputs.description):
            a.connectome_meta.set_description(self.inputs.description)

        a.connectome_meta.set_created(datetime.date.today())

        count = 0
        if isdefined(self.inputs.graphml_networks):
            for ntwk in self.inputs.graphml_networks:
                # There must be a better way to deal with the unique name problem
                # (i.e. tracks and networks can't use the same name, and previously we were pulling them both from the input files)
                ntwk_name = 'Network {cnt}'.format(cnt=count)
                a.add_connectome_network_from_graphml(ntwk_name, ntwk)
                count += 1

        if isdefined(self.inputs.gpickled_networks):
            unpickled = []
            for ntwk in self.inputs.gpickled_networks:
                _, ntwk_name, _ = split_filename(ntwk)
                unpickled = nx.read_gpickle(ntwk)
                cnet = cf.CNetwork(name=ntwk_name)
                cnet.set_with_nxgraph(unpickled)
                a.add_connectome_network(cnet)
                count += 1

        count = 0
        if isdefined(self.inputs.tract_files):
            for trk in self.inputs.tract_files:
                _, trk_name, _ = split_filename(trk)
                ctrack = cf.CTrack(trk_name, trk)
                a.add_connectome_track(ctrack)
                count += 1

        count = 0
        if isdefined(self.inputs.gifti_surfaces):
            for surf in self.inputs.gifti_surfaces:
                _, surf_name, _ = split_filename(surf)
                csurf = cf.CSurface.create_from_gifti("Surface %d - %s" %
                                                      (count, surf_name), surf)
                csurf.fileformat = 'Gifti'
                csurf.dtype = 'Surfaceset'
                a.add_connectome_surface(csurf)
                count += 1

        count = 0
        if isdefined(self.inputs.gifti_labels):
            for label in self.inputs.gifti_labels:
                _, label_name, _ = split_filename(label)
                csurf = cf.CSurface.create_from_gifti(
                    "Surface Label %d - %s" % (count, label_name), label)
                csurf.fileformat = 'Gifti'
                csurf.dtype = 'Labels'
                a.add_connectome_surface(csurf)
                count += 1

        if isdefined(self.inputs.nifti_volumes):
            for vol in self.inputs.nifti_volumes:
                _, vol_name, _ = split_filename(vol)
                cvol = cf.CVolume.create_from_nifti(vol_name, vol)
                a.add_connectome_volume(cvol)

        if isdefined(self.inputs.script_files):
            for script in self.inputs.script_files:
                _, script_name, _ = split_filename(script)
                cscript = cf.CScript.create_from_file(script_name, script)
                a.add_connectome_script(cscript)

        if isdefined(self.inputs.data_files):
            for data in self.inputs.data_files:
                _, data_name, _ = split_filename(data)
                cda = cf.CData(name=data_name, src=data, fileformat='NumPy')
                if not string.find(data_name, 'lengths') == -1:
                    cda.dtype = 'FinalFiberLengthArray'
                if not string.find(data_name, 'endpoints') == -1:
                    cda.dtype = 'FiberEndpoints'
                if not string.find(data_name, 'labels') == -1:
                    cda.dtype = 'FinalFiberLabels'
                a.add_connectome_data(cda)

        a.print_summary()
        _, name, ext = split_filename(self.inputs.out_file)
        if not ext == '.cff':
            ext = '.cff'
        cf.save_to_cff(a, op.abspath(name + ext))

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        _, name, ext = split_filename(self.inputs.out_file)
        if not ext == '.cff':
            ext = '.cff'
        outputs['connectome_file'] = op.abspath(name + ext)
        return outputs


class MergeCNetworksInputSpec(BaseInterfaceInputSpec):
    in_files = InputMultiPath(
        File(exists=True),
        mandatory=True,
        desc='List of CFF files to extract networks from')
    out_file = File(
        'merged_network_connectome.cff',
        usedefault=True,
        desc='Output CFF file with all the networks added')


class MergeCNetworksOutputSpec(TraitedSpec):
    connectome_file = File(
        exists=True, desc='Output CFF file with all the networks added')


class MergeCNetworks(CFFBaseInterface):
    """ Merges networks from multiple CFF files into one new CFF file.

    Example
    -------

    >>> import nipype.interfaces.cmtk as cmtk
    >>> mrg = cmtk.MergeCNetworks()
    >>> mrg.inputs.in_files = ['subj1.cff','subj2.cff']
    >>> mrg.run()                  # doctest: +SKIP

    """
    input_spec = MergeCNetworksInputSpec
    output_spec = MergeCNetworksOutputSpec

    def _run_interface(self, runtime):
        import cfflib as cf
        extracted_networks = []

        for i, con in enumerate(self.inputs.in_files):
            mycon = cf.load(con)
            nets = mycon.get_connectome_network()
            for ne in nets:
                # here, you might want to skip networks with a given
                # metadata information
                ne.load()
                contitle = mycon.get_connectome_meta().get_title()
                ne.set_name(str(i) + ': ' + contitle + ' - ' + ne.get_name())
                ne.set_src(ne.get_name())
                extracted_networks.append(ne)

        # Add networks to new connectome
        newcon = cf.connectome(
            title='All CNetworks', connectome_network=extracted_networks)
        # Setting additional metadata
        metadata = newcon.get_connectome_meta()
        metadata.set_creator('My Name')
        metadata.set_email('My Email')

        _, name, ext = split_filename(self.inputs.out_file)
        if not ext == '.cff':
            ext = '.cff'
        cf.save_to_cff(newcon, op.abspath(name + ext))

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        _, name, ext = split_filename(self.inputs.out_file)
        if not ext == '.cff':
            ext = '.cff'
        outputs['connectome_file'] = op.abspath(name + ext)
        return outputs
