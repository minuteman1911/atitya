import sys
sys.path.append('../..')
from kobe import Node
from kobe.utils import _log_duration
import numpy as np

class Node(Node):
	pspmin = 1e-6
	EXCITATORY = 1
	INHIBITORY = -1
	def __init__(self,id,params,dendrites=None,axonal_terminals=None,logger=None):
		super(Node,self).__init__(id,params,dendrites=None,axonal_terminals=None,logger=None)
	
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
