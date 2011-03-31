# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Connectome File Format Converter Node

"""
__docformat__ = 'restructuredtext'
from nipype.interfaces.base import BaseInterface, BaseInterfaceInputSpec, traits, File, TraitedSpec

import nibabel as nb
import numpy as np
import networkx as nx
import os
import cfflib as cf

class CFFConverterInputSpec(BaseInterfaceInputSpec):
	# CMetadata: a dictionary of the basic fields
	
	# a List of CNetwork
	cnetworks = traits.List(File(exists=True), desc='list of networks')
	cnetworks_metadata = traits.List(traits.DictStrStr(), desc="metadata of the network, fill in at least the description tag")
	
	# metadata dictionary, with required fields
	
	out_file = File('connectome.cff', usedefault = True)
	
class CFFConverterOutputSpec(TraitedSpec):
	connectome_super_file = File(exist=True)
	 
class CFFConverter(BaseInterface):
	"""
	Examples, docu
	"""
	
	input_spec = CFFConverterInputSpec
	output_spec = CFFConverterOutputSpec
	
	def _run_interface(self, runtime):
		
		cnetwork_fnames = self.inputs.cnetworks
		
		# create a connectome container
		a = cf.connectome()
		# requires a connectome metadata
		
		# add the connectome objects 

		cf.save_to_cff(self.inputs.out_file, a)

		return runtime
		
		
	def _list_outputs(self):
		
		outputs = self._outputs().get()
		outputs['connectome_super_file'] = self.inputs.out_file
		return outputs
