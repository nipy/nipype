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
        cnetwork_fnames = self.inputs.cnetworks

        if isdefined(self.inputs.graphml_networks):
            for ntwk in self.inputs.graphml_networks:
                _, ntwk_name, _ = split_filename(ntwk)
                a.add_connectome_network_from_graphml(ntwk_name, ntwk)

        if isdefined(self.inputs.gpickled_networks):
            unpickled = []
            for ntwk in self.inputs.gpickled_networks:
                _, ntwk_name, _ = split_filename(ntwk)
                unpickled = nx.read_gpickle(ntwk)
                cnet = cf.CNetwork(name = ntwk_name)
                cnet.set_with_nxgraph(unpickled)
                a.add_connectome_network(cnet)

        if isdefined(self.inputs.tract_files):
            for trk in self.inputs.tract_files:
                _, trk_name, _ = split_filename(trk)
                ctrack = cf.CTrack(trk_name, trk)
                a.add_connectome_track(ctrack)

        if isdefined(self.inputs.gifti_surfaces):
            for surf in self.inputs.gifti_surfaces:
                _, surf_name, _ = split_filename(surf)
                csurf = cf.CSurface.create_from_gifti(surf_name, surf)
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

        # create a connectome container
       # c = cf.connectome()

                # creating metadata
        """     c.connectome_meta.set_title('%s - %s' % (gconf.subject_name, gconf.subject_timepoint) )
                c.connectome_meta.set_creator(gconf.creator)
                c.connectome_meta.set_email(gconf.email)
                c.connectome_meta.set_publisher(gconf.publisher)
                c.connectome_meta.set_created(gconf.created)
                c.connectome_meta.set_modified(gconf.modified)
        #       c.connectome_meta.set_license(gconf.license)
                c.connectome_meta.set_rights(gconf.rights)
                c.connectome_meta.set_references(gconf.reference)
                c.connectome_meta.set_relation(gconf.relation)
                c.connectome_meta.set_species(gconf.species)
                c.connectome_meta.set_description(gconf.description)
        """
        a.print_summary()
        cf.save_to_cff(a,self.inputs.out_file)

        return runtime


    def _list_outputs(self):

        outputs = self._outputs().get()
        outputs['connectome_file'] = self.inputs.out_file
        return outputs
