import numpy as np
import scipy as sp
import pdb
import logging
import redis
import json
import sys
from kobe.utils import Params
from kobe.utils import _log_duration

class Node(object):
	pspmin = 1e-6
	EXCITATORY = 1
	INHIBITORY = -1
	def __init__(self,id,params,dendrites=None,axonal_terminals=None,logger=None):
		self.id = id
		self.logger = logger if logger else logging.getLogger(__name__)
		self.logger.addHandler(logging.NullHandler())
		self.logger.debug('Initializing Node params: %s',str(params))
		self.params = Params(**params)
		if axonal_terminals is None:
			axonal_terminals = list()
		self.axonal_terminals = axonal_terminals
		if dendrites is None:
			dendrites = list()
		self.dendrites = dendrites
	
	def setLogger(self,logger):
		self.logger = logger
	
	def initParams(self,kwparams):
		pass
	
	def dumpToJSON(self):
		return json.dumps({'id' : self.id , 'params':self.params , 'dendrites' : self.dendrites , 'axonal_terminals' : self.axonal_terminals })
		
	def __str__(self):
		return "<Node " + str(self.id) + ">\n" #+ str([self.synapse_map[d]['source'] for d in self.dendrites])
	
	def addConnection(self,s_id,type):
		if type == 'dendritic':
			self.dendrites.append(s_id)
			return True
		if type == 'axonal':
			self.axonal_terminals.append(s_id)
			return True
		return False
		
	def getOutput(self):
		return self.output
		
	def getCurrentFiringRate(self , elapsed_time):
		return self.activation_count / elapsed_time
		
	def setOutput(self,v,binary=True):
		self.membrane_potential = v * self.input_scaling_factor
		self.output = True	
	
	
	@_log_duration
	def process(self,network_map,synapse_map,**ensemble_params):
		print ("Subclasses must implement")
		return
