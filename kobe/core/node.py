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
		#paramdict = kwparams['params']
		#del kwparams['params']
		#self.params = Params(paramdict)
		#self.params.update(kwparams)
		#self.absolute_refractory_period = kwparams.get('absolute_refractory_period',0)
		#self.decay_time_constant = kwparams.get('decay_time_constant')              # time constant for temporal summation
		#self.std_time_constant =  kwparams.get('std_time_constant')                        # time constant for taking into consideration std 
		#self.stdp_A_minus = kwparams.get('stdp_A_minus')
		#self.stdp_A_plus = kwparams.get('stdp_A_plus')
		#self.stdp_T_minus = kwparams.get('stdp_T_minus')
		#self.stdp_T_plus = kwparams.get('stdp_T_plus')
		#self.utilization_factor = kwparams.get('utilization_factor',0.2)
		#self.threshold = kwparams.get('threshold')
		#self.p_constant = kwparams.get('p_constant',1.5)
		#self.input_scaling_factor = kwparams.get('input_scaling_factor',2)
		#self.tpsp = kwparams.get('tpsp')
		#self.activation_count = kwparams.get('activation_count')
		#self.membrane_potential = kwparams.get('membrane_potential')
	
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
		#pdb.set_trace()
		try:
			self.logger.debug('In Node.process, params : %s , ensemble_params : %s',str(self.params),str(ensemble_params))
			t = ensemble_params.get('t')
			m = ensemble_params.get('m')
			train = ensemble_params.get('train')
			if t - self.params.tpsp < self.params.absolute_refractory_period:
				self.logger.debug('1------------------')
				return False
			self.logger.debug('------------------')
			self.params.membrane_potential *= np.exp( - (t - self.params.tpsp) / self.params.decay_time_constant)
			if self.params.membrane_potential < Node.pspmin:
				self.params.membrane_potential = 0	
			
			self.logger.debug('2------------------')
		
			weight_updates_incr = {}
		
			for s_id in self.dendrites:
				conn = synapse_map[s_id]
				id = conn['source']
				n = network_map[id]
				self.logger.debug('node : %s',str(n))
				y = int (n.params.output == True )
				if train == True:
					if y == 1 :
						if t - n.params.tpsp < self.params.stdp_T_plus * 5:
							weight_updates_incr[s_id] = self.params.stdp_A_plus * np.exp((t - n.params.tpsp)/self.params.stdp_T_plus) 
				conn['u'] = 1 - ( 1 - ( conn['u'] - y * self.params.utilization_factor) ) * np.exp( - ( t - self.params.tpsp )/self.params.std_time_constant)
				if conn['u'] <= 0:
					conn['u'] = 0
				self.params.membrane_potential += self.params.p_constant * conn['weight'] * conn['u'] * m * y
			
			self.logger.debug('membrane_potential : %s , threshold : %s',str(self.params.membrane_potential),str(self.params.threshold))
			
			if self.params.membrane_potential > self.params.threshold:
				self.params.output = True
				self.params.activation_count += 1
				#self.params.membrane_potential = 0
				self.params.tpsp = t
				
				if train == True:
					for s_id in self.axonal_terminals:
						conn = synapse_map[s_id]
						id = conn['destination']
						n = network_map[id]
						if  t - n.params.tpsp < self.params.stdp_T_minus * 5 :
							synapse_map[s_id]['weight'] -= self.params.stdp_A_minus * np.exp(( t - n.params.tpsp )/self.params.stdp_T_minus)
							
						for s_id,w_incr in weight_updates_incr.items():
							synapse_map[s_id]['weight'] +=  w_incr
					
				return True
			else:
				self.params.output = False
				return False
		except Exception as e:
			self.logger.error('Exception : %s , node id : %s',e , self.id )
			raise e