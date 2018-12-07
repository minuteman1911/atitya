import copy
import pdb
import json
import redis
import pickle
import logging
import time
import hashlib
import os
from kobe.utils import *
from kobe.core.ensemble import Ensemble

class Network(object):
	def __init__(self,network_name,db_url):
		self.network_name = network_name
		self.network_graph = { 'root' : [] }
		self.ensemble_map = {}
		self.logger = logging.getLogger(__name__)
		self.sensors = list()
		self.actuators = list()
		self.simulation_time = 0
		self.db_url = db_url
		self.offline_train_flag = False
		self.rconn = redis.StrictRedis(db_url)
		ret = self.rconn.hmget(network_name,'addr')
		network_id = ret[0].decode('UTF-8')
		self.network_id = network_id
		self.job_q = RedisFIFOQueue(network_id+'_job_queue',db_url)
		self.logger.info('Initializing network')
		self.logger.info('Flushing old queue and result set')
		self.rconn.delete(network_id+'_job_queue')
		self.rconn.delete(network_id+'_result_set')
		self.loadNetwork()
		self.logger.info('Network Initialized')
				
	
	def getEnsemble(self,name):
		if name in self.ensemble_map:
			return self.ensemble_map[name]
		else:
			self.logger.error('Ensemble ' + name + ' does not exist')
			return None
	
	def addSensor(self,sensor):
		self.sensors.append(sensor)
	
	def addActuator(self,actuator):
		self.actuators.append(actuator)


	def loadNetwork(self):
		"""
			This name is a misnomer - This function only pulls the network information from redis-server,
			and builds the Ensemble objects from it. In reality, the whole network is loaded by redis,
			on the machine where it resides.
		"""
		self.logger.info('In loadNetwork, getting saved network configuration')
		string = self.rconn.hget(self.network_name,'network_graph').decode('utf-8')
		self.network_graph = json.loads(string)
		self.logger.info('Loaded network: %s', str(self.network_graph))
		keys = self.network_graph.keys()
		addkeys = []
		done = []
		for k , vlist in self.network_graph.items():
			if k not in done and k != 'root':
				e = Ensemble(self.network_id,k,self.job_q,self.rconn)
				self.ensemble_map[k] = e
				done.append(k)
			for v in vlist:
				if v not in keys:
					addkeys.append(v)
				if v not in done:
					e = Ensemble(self.network_id,v,self.job_q,self.rconn)
					self.ensemble_map[v] = e
					done.append(v)
		for k in addkeys:
			self.network_graph[k] = []
		self.execution_order = self._topological_sort(self.network_graph)
	
	def update_node_object_file(self,filename):
		"""
			Function to update and send the node object file to all remote hosts with running workers
		"""
                
		if os.path.exists(filename):
			curr_hash = hashlib.md5(open(filename,'rb').read()).hexdigest()
		else:
			self.logger.info('Node object file ' + filename + ' does not exist' )
			self.logger.info('Try giving the full path')
			return None
		reg_hash = self.rconn.get(self.network_id + '_node_file_hash')
		if reg_hash:
			reg_hash = reg_hash.decode('utf-8')
		if curr_hash != reg_hash:
			with open(filename,'rb') as nfile:
				blob = nfile.read()
			self.rconn.set(self.network_id + '_node_file',blob)
			self.rconn.hset(self.network_name ,'node_file_hash',curr_hash.encode('utf-8'))

		return curr_hash

	def deleteNetwork(self,name):
		"""
			The name is pretty much self-explanatory
		"""
		for key in self.rconn.scan_iter(name+":*"):
    			self.rconn.delete(key)
	
	def dumpAsString(self,file):
		"""
			Dumps the whole network including the weights and the config as a string on a file.
			This is a heavy operation and could take a long time in case of very large networks.
			Primary use of this is debug and backup, the network is also saved by redis-server itself 
                        where it resides. 
		"""
		fp = open(file,'w')
		def pprint(*args):
			fp.write(''.join(args)+'\n')
		def print2darray(array):
			for y in array:
				pprint(str(y))
		def print3darray(array):
			for z in array:
				print2darray(z)
		def print_node(n,ndict,synapse_map):
			pprint('id:'+ndict['id'] + ' axonal_terminals'+ str([ synapse_map[i]['destination'] for i in  ndict['axonal_terminals'] ])   )
		pprint('Network id: ' + self.network_id)
		network_config = self.rconn.hmget(self.network_name,'network_graph')
		pprint('network_graph : ' + str(json.loads(network_config[0].decode('utf-8'))))
		ensembles = self.rconn.hgetall(self.network_id+'_ensembles')
		for ename,e in ensembles.items():
			pprint('Ensemble : '+ename.decode('utf-8'))
			print3darray(json.loads(e.decode('utf-8')))
		nm = self.rconn.hgetall(self.network_id+'_nodes')
		sm = self.rconn.hgetall(self.network_id+'_edges')
		
		network_map = {k.decode('utf-8'):json.loads(v.decode('utf-8')) for k,v in nm.items()}
		synapse_map = {k.decode('utf-8'):json.loads(v.decode('utf-8')) for k,v in sm.items()}
		for n,ndict in network_map.items():
			print_node(n,ndict,synapse_map)
			
		fp.close()
		
	
	def _topological_sort(self,ingraph):
		graph = copy.deepcopy(ingraph)
		topological_order = []
		queue = []
		vertexes = list(graph.keys())
		in_degrees = { k : 0 for k  in vertexes }
		for v,children in graph.items():
			if children:
				for c in children:
					in_degrees[c] += 1
				
		for v in vertexes:
			if in_degrees[v] == 0:
				queue.append(v)
		
		while queue:
			output_node = queue.pop()
			topological_order.append(output_node)
			
			for c in graph[output_node]:
				in_degrees[c] -= 1
				if in_degrees[c] == 0:
					queue.append(c)
	
		return topological_order
		
	def _get_feedback_arc_set(self,ingraph):
		graph = copy.deepcopy(ingraph)		
		vertexes = list(graph.keys())
		in_degrees = { k : 0 for k  in vertexes }
		for v,children in graph.items():
			if children:
				for c in children:
					in_degrees[c] += 1
		queue = [k for k,v in in_degrees.items() if v == 0]
		paths = [str(k) for k,v in in_degrees.items() if v == 0]
		fas = []
		while queue:
			node = queue.pop()
			adj_list = graph[node]
			for p in paths:
				if p[-1] == node:
					for n in adj_list:
						if n in p:
							graph[node].remove(n) 
							fas.append((node,n))
						else:
							paths.append(p + n)
					paths.remove(p)
			
			queue += adj_list
	
		return fas
	
	def deleteNodes(self,node_id_list):
		"""
			Deletes the nodes as given in node_id_list, which is a list of strings, where all strings are node_ids
		"""
		self.rconn.hdel(self.network_id+'_nodes',node_id_list)
	
	def pruning_fn(self,i,algorithm='remove_least_activated'):
		"""
			This is the pruning function.
			Pruning has two subtypes:
				1. Weight pruning
				2. Node pruning
			This function is responsible for Node pruning. Weight pruning occurs at Node level, i.e. in the KRE
			The only algorithm currently supported for Node pruning is to remove the least activated nodes first. 
			The parameter 'i' (current iteration) is extra, and not used by this algorithm;
			passed in case if any other algorithm wants to make use of it.  
		"""
		list = []
		if algorithm == 'remove_least_activated':
			for layer in ensemble:
				layer_list = self.getOutputs(node_list)
				ip_list = [ n for row in layer for n in row]
				plist = sorted(ip_list,key=lambda x:x['activation_count'])
				list = [ l[0] for l in plist ]
				last_n = 0.1
				rem = int( last_n * len(list))
				list = list[:-rem] if rem != 0 else list
		return list
		
	def prune_nodes(self , i ):
		list = self.pruning_fn( i , self.pruning_params['algorithm'])
		if list != []:
			deleteNodes(list)
			
	def getOutputs(self,output_node_id_list,params=None):
		"""
			Gets the current variable value of all the nodes specified in output_node_id_list,
			which is a list of strings, where all strings are node_ids.
			params field is an optional list of strings, used to get only those outputs as are specified in params 
		"""
		result = None
		self.logger.debug('Getting outputs for :%s',str(output_node_id_list))
		pipe = self.rconn.pipeline()
		for row in output_node_id_list:
			pipe.hmget(self.network_id + '_nodes',row)
		
		result1 = pipe.execute()
		if params != None:
			result = [ [item_getter(json.loads(i),*params) for i in oplist ] for oplist in result1 ]
		else:
			result = [ [ json.loads(i) for i in oplist ] for oplist in result1 ]
		return result

	def setEnsembleParam(self,ename,paramname,value):
		self.logger.debug('Setting Ensemble params for :%s , paramname : %s , value: %s',ename,paramname,str(value))
		return setattr(self.ensemble_map[ename],paramname,value)	
	
		
	def setNodeInputs(self,data,*args):
		"""
			Sets the inputs from the input buffers (sensors) to an input layer of the network.
			
		"""
		nodes = args[0]
		params = args[1]
		self.logger.debug('Setting inputs:%s',str(data))
		pipe = self.rconn.pipeline()
		for row in nodes:
			pipe.hmget(self.network_id + '_nodes',row)
		result = pipe.execute()
		#pdb.set_trace()
		mapping = {}
		for row1,row2,row3 in zip(nodes,result,data):
			for node,nodestring,value in zip(row1,row2,row3):
				nodedict = json.loads(nodestring.decode('utf-8'))
				# Below line passes the value as native python type, instead of numpy dtype
				item_setter(nodedict,value.item(),*params)
				mapping[node] = json.dumps(nodedict).encode('utf-8')
				
		self.rconn.hmset(self.network_id + '_nodes',mapping)
	
	def setEnsembleParams(self,value,*args):
		ensemble = args[0]
		param = args[1]
		setattr(self.ensemble_map[ensemble],param,value)

	def offline_train(self):
		pass
		
	def simulate(self ):
		"""
			This function advances the network by one complete cycle. It applies any inputs in the input buffers,
			runs them through the network in KRE, and finally applies them to te output buffers. 
		"""
		outputs = {}
		t = self.simulation_time
		ept1 = time.time()
		#pdb.set_trace()	
		self.logger.info('Polling inputs from sensors')
			
		for s in self.sensors:
			s.setInputs()
		self.logger.info('Starting execution, simulation time : %s , current time : %s',str(t), str(ept1))
		for ensemble in self.execution_order[1:]:
			m = self.ensemble_map[ensemble]
			t = m.evaluate(t)# TODO : change this , take max(t) for parallel ensembles
			#print(("t="+str(t) + " " +str(m.getAttributes(0,'membrane_potential'))))
		self.simulation_time = t
		ept2 = time.time()
		self.logger.info('End of exceution, simulation time : %s, current time : %s , elapsed time : %s',str(t),str(ept2),str(ept2-ept1))
		self.logger.info('Setting outputs to actuators')
		for a in self.actuators:
			a.getOutputs()
			#targets = a.getTarget()
			#op = self.getOutputs(targets)
			#a.setRawOutput(op)
		self.logger.info('End of iteration')
		
		if self.offline_train_flag:
			self.offline_train()
		
		
				
