from nipype.interfaces.base import BaseInterface, BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.misc import isdefined
import nibabel as nb
import numpy as np
import networkx as nx
import cfflib as cf
import os, os.path as op
import sys
from time import time
from nipype.utils.filemanip import fname_presuffix, split_filename, copyfile
import datetime

class CFFConverterInputSpec(BaseInterfaceInputSpec):
    """
    Creates a Connectome File Format (CFF) file from input networks, surfaces, volumes, tracts, etcetera....
    """
    # CMetadata: a dictionary of the basic fields

    # a List of CNetwork
    cnetworks = traits.List(File(exists=True), desc='list of networks')
    cnetworks_metadata = traits.List(traits.DictStrStr(), desc="metadata of the network, fill in at least the description tag")

    graphml_networks = traits.List(File(exists=True), desc='list of graphML networks')
    gpickled_networks = traits.List(File(exists=True), desc='list of gpickled Networkx graphs')

    gifti_surfaces = traits.List(File(exists=True), desc='list of GIFTI surfaces')
    gifti_labels = traits.List(File(exists=True), desc='list of GIFTI surfaces')
    nifti_volumes = traits.List(File(exists=True), desc='list of NIFTI volumes')
    tract_files = traits.List(File(exists=True), desc='list of Trackvis fiber files')

    timeseries_files = traits.List(File(exists=True), desc='list of HDF5 timeseries files')
    data_files = traits.List(File(exists=True), desc='list of external data files (i.e.) ')

    #Find a way to include a copy of the running Nipype Pipeline by default
    script_files = traits.List(File(exists=True), desc='list of external data files (i.e. Numpy, HD5, XML) ')

    # metadata dictionary, with required fields

    # The user can also fill in the metadata using the input fields
    # creating metadata

    title = traits.Str(desc='Connectome Title')
    creator = traits.Str(desc='Creator')
    email = traits.Str(desc='Email address')
    publisher = traits.Str(desc='Publisher')
    license = traits.Str(desc='License')
    rights = traits.Str(desc='Rights')
    references = traits.Str(desc='References')
    relation = traits.Str(desc='Relation')
    species = traits.Str('Homo sapiens',desc='Species',usedefault=True)
    description = traits.Str('Created with the Nipype CFF converter', desc='Description', usedefault=True)

    out_file = File('connectome.cff', usedefault = True)

class CFFConverterOutputSpec(TraitedSpec):
    """
    Creates a Connectome File Format (CFF) file from input networks, surfaces, volumes, tracts, etcetera....
    """
    connectome_file = File(exist=True)

class CFFConverter(BaseInterface):
    """
    Creates a Connectome File Format (CFF) file from input networks, surfaces, volumes, tracts, etcetera....
    """

    input_spec = CFFConverterInputSpec
    output_spec = CFFConverterOutputSpec

    def _run_interface(self, runtime):
        a = cf.connectome()


        if isdefined(self.inputs.title):
            a.connectome_meta.set_title(self.inputs.title)
        else:
            a.connectome_meta.set_title(self.inputs.out_file)

        if isdefined(self.inputs.creator):
            a.connectome_meta.set_creator(self.inputs.creator)
        else:
            #Probably only works on some OSes...
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

        cnetwork_fnames = self.inputs.cnetworks
        count = 0
        if isdefined(self.inputs.graphml_networks):
            for ntwk in self.inputs.graphml_networks:
                #_, ntwk_name, _ = split_filename(ntwk)
                # There must be a better way to deal with the unique name problem
                #(i.e. tracks and networks can't use the same name, and previously we were pulling them both from the input files)
                ntwk_name = 'Network {cnt}'.format(cnt=count)
                a.add_connectome_network_from_graphml(ntwk_name, ntwk)
                count += 1

        if isdefined(self.inputs.gpickled_networks):
            unpickled = []
            for ntwk in self.inputs.gpickled_networks:
                ntwk_name = 'Network {cnt}'.format(cnt=count)
                unpickled = nx.read_gpickle(ntwk)
                cnet = cf.CNetwork(name = ntwk_name)
                cnet.set_with_nxgraph(unpickled)
                a.add_connectome_network(cnet)
                count += 1


        count = 0
        if isdefined(self.inputs.tract_files):
            for trk in self.inputs.tract_files:
                #_, trk_name, _ = split_filename(trk)
                trk_name = 'Tract file {cnt}'.format(cnt=count)
                ctrack = cf.CTrack(trk_name, trk)
                a.add_connectome_track(ctrack)
                count += 1

        if isdefined(self.inputs.gifti_surfaces):
            for surf in self.inputs.gifti_surfaces:
                _, surf_name, _ = split_filename(surf)
                csurf = cf.CSurface.create_from_gifti(surf_name, surf)
                csurf.fileformat='Gifti'
                csurf.dtype='Surfaceset'
                a.add_connectome_surface(csurf)

        if isdefined(self.inputs.gifti_labels):
            for label in self.inputs.gifti_labels:
                _, label_name, _ = split_filename(label)
                csurf = cf.CSurface.create_from_gifti(label_name + '_labels', surf)
                csurf.fileformat='Gifti'
                csurf.dtype='Labels'
                a.add_connectome_surface(csurf)

        if isdefined(self.inputs.nifti_volumes):
            for vol in self.inputs.nifti_volumes:
                _, vol_name, _ = split_filename(vol)
                cvol = cf.CVolume.create_from_nifti(vol_name,vol)
                a.add_connectome_surface(cvol)

        if isdefined(self.inputs.script_files):
            for script in self.inputs.script_files:
                _, script_name, _ = split_filename(script)
                cscript = cf.CScript.create_from_file(script_name,script)
                a.add_connectome_script(cscript)

        a.print_summary()
        cf.save_to_cff(a,self.inputs.out_file)

        return runtime


    def _list_outputs(self):

        outputs = self._outputs().get()
        outputs['connectome_file'] = self.inputs.out_file
        return outputs
