import os
import random
import json
import redis
import hashlib
import pickle
import numpy as np
from ruamel.yaml import YAML,error
import warnings
import logging
from kobe.utils import *
from kobe.core.node import Node
import redis

warnings.simplefilter('ignore', error.MantissaNoDotYAML1_1Warning)
import pdb
class Topology():
	def __init__(self,configpath,db_url='redis://localhost:6379'):
		self.logger = logging.getLogger(__name__)
		assert os.path.exists(configpath), "Config file "+ configpath +" does not exist"
		yaml=YAML(typ='unsafe')
		yaml.default_flow_style = True
		with open(configpath) as fp:
			config = yaml.load(fp)
			self.logger.info('Loaded config :%s',str(config))
		
		self.network_map = {}
		self.synapse_map = {}
		self.network_graph = {}
		self.ensemble_map = {}
		self.ensemble_params = {}
		self.network_name = config['name']
		try:
			self.db_conn = redis.StrictRedis.from_url(db_url)
		except Exception as e:
			self.logger.error('Unable to connect to redis, %s',e)
		self.db_url = db_url
		addr = hashlib.md5(pickle.dumps(config)).hexdigest()
		if self.db_conn.exists(self.network_name):
			if self.db_conn.hmget(self.network_name,'addr')[0].decode('UTF-8') != addr:
				ip = None
				while ip not in ('y','n'):
					ip = input('Config has changed. Re-build the network? [y/n]\n').strip().lower()
				if ip == 'n':
					self.addr = addr
					self.initialized = True
					return
			else:
				self.addr = addr
				self.initialized = True
				return
					
				
		if self._verify(config):
			self.config = config
			self.logger.info('Building network')
			self.init(config)
			self.addr = self.commitToDB()
			self.initialized = True
	
	def commitToDB(self):
		ret = None
		addr = hashlib.md5(pickle.dumps(self.config)).hexdigest()
		list = []
		for s,val in self.synapse_map.items():
			tuple =  (val['source'],val['destination'])
			if tuple not in list:
				list.append(tuple)
			else:
				logger.info("Fatal Error. Contact support if you wanna solve this")
		pipe = self.db_conn.pipeline()
		mapping = { idx : obj.dumpToJSON().encode('utf-8') for idx,obj in self.network_map.items()}
		pipe.hmset(addr + '_' + 'nodes' ,mapping)
		mapping = { idx : json.dumps(obj).encode('utf-8') for idx,obj in self.synapse_map.items()}
		pipe.hmset(addr + '_' + 'edges' ,mapping)
		mapping = { idx : json.dumps(obj).encode('utf-8') for idx,obj in self.ensemble_map.items()}
		pipe.hmset(addr + '_' + 'ensembles',mapping)
		mapping = { idx : json.dumps(obj).encode('utf-8') for idx,obj in self.ensemble_params.items()}
		pipe.hmset(addr + '_' + 'ensemble_params',mapping)
		self.logger.info("Storing the generated network in database")		
		pipe.execute()
		mapping = {'network_graph' : json.dumps(self.network_graph)  , 'addr' : addr  }
		self.db_conn.hmset(self.network_name,mapping)
		ret = addr
		return ret 
	
	def init(self,config):
		for parent,children in self.config['network'].items():
			for ensemble_id,params in children:
				conf = self.config[ensemble_id]
				ensemble = self.initNodes(conf,ensemble_id)
				self.initConnections(conf,ensemble)
				self.ensemble_map[ensemble_id] = ensemble
				self.ensemble_params[ensemble_id] = params
				if parent not in self.network_graph.keys():
					self.network_graph[parent] = []
				self.network_graph[parent].append(ensemble_id)
		if 'conn_en_en' not in config.keys():
			for parent,children in self.network_graph.items():
				if parent != 'root':
					for ensemble_id in children:
						conf = self.config[ensemble_id]
						self.connectEnsembles(parent,-1,ensemble_id,0,conf)
		else:
			for conn_specs in config['conn_en_en']:
				_from = self.ensemble_map[conn_specs[0][0]]
				_from_layer = conn_specs[0][1]
				_to = self.ensemble_map[conn_specs[1][0]]
				_to_layer = conn_specs[1][1]
				#self.connectLayers(_from,_from_layer,_to,_to_layer,self.config[conn_specs[1][0]])

	def connectEnsembles(self,source_m,dest_m,dest_ensemble_config):
		#layer1 = self.ensemble_map[source_m][-1]
		layer2 = self.ensemble_map[dest_m][0]
		self.connectLayers(self.ensemble_map[source_m],layer2,dest_ensemble_config)
	
	
	def connectLayers(self,prev_ensemble,layer2,dest_ensemble_config):
		#pdb.set_trace()
		slice=self.getSlice(0,dest_ensemble_config)
		s_slice = len(slice)
		for irow in range(len(layer2)):
			s_slice_row = len(slice[irow%s_slice])
			for inode in range(len(layer2[irow])):
				n = layer2[irow][inode]
				synapse_config = slice[irow%s_slice][inode%s_slice_row]
				for tuple in synapse_config[1]:
					iprev_layer = tuple[0] + len(prev_ensemble)
					if iprev_layer > 0 and iprev_layer < len(prev_ensemble):
						mx,my = len(layer2[0]),len(layer2)
						nx,ny = len(prev_ensemble[iprev_layer][0]),len(prev_ensemble[iprev_layer])
						pos_matrix = self.getCoordinates(my,ny,mx,nx)
						srow,scol=self.getReceptiveField(tuple[1],nx,ny)
						input_space_nodes = self.getConnList(pos_matrix[irow][inode],float(scol)/2,float(srow)/2,prev_ensemble[iprev_layer])
						synapse_params  = tuple[2]
						#for id in input_space_nodes:
						#	for s,val in self.synapse_map.items():
						#		if val['source'] == id and val['destination'] == n:
						#			pdb.set_trace()
						self.connectInputNodes(input_space_nodes,n,synapse_params)		
		
	
	def addNewNode(self,ensemble_id,neuron_params):
		idx = getNewId(list(self.network_map.keys()),4,prefix=ensemble_id+'_')
		self.network_map[idx] = Node(idx,params=randomizeParams(neuron_params),logger=self.logger)
		
		return idx
		
	def connectInputNodes(self,input_nodes,n,synapse_params):
		#pdb.set_trace()
		for idx in input_nodes:
			s_id = self.createConnection(idx,n,randomizeParams(synapse_params))
			self.network_map[n].addConnection(s_id,'dendritic')
			self.network_map[idx].addConnection(s_id,'axonal')
		return

	def createConnection(self,source,destination,synapse_params):
		syn_dict = dict({'source' : source , 'destination' : destination , 'weight' : synapse_params['initial_weight'] , 'u' : 1 })
		s_id = getNewId(list(self.synapse_map.keys()),8,prefix='synapse_')
		self.synapse_map[s_id] = syn_dict
		return s_id
	
	def getConfig(self):
		return self.config
		
	def _verify(self,config):
		done = []
		retcode = False
		assert 'network' in config , "Key required : network"
		#pdb.set_trace()
		assert 'root' in config['network'] , "Require a key by name root in the network dict"		
		for p,clist in config['network'].items():
			assert isinstance(p,str) , "Expected a string, found" + str(type(p))
			if p != 'root':
				assert p in config.keys() , "No configuration found for ensemble: " + p
			for i in clist:
				#pdb.set_trace()
				assert len(i) == 2, "Require two elements per child node, the name of the node , and the extra parameters"
				assert isinstance(i[0],str) , "Expected a string, found" + str(type(i[0]))
				assert i[0] in config.keys() , "No configuration found for ensemble: " + i[0]
								
				#assert i[1] in self.connect_methods , "connect method is not defined or does not exist in this Topology object"
				if i[0] not in done:
					if self._verify_ensemble(config[i[0]]):
						done.append(i)
		
		assert 'conn_en_en' in config.keys() , "Key required : conn_en_en"
		for i in config['conn_en_en']:
			assert len(i) == 2 and len(i[0]) == 2 and len(i[1]) == 2, "Require only two elements in the outer array, and two in the inner one,\n in the form [[<source_ensemble>,<source_layer>],[<dest_ensemble>,<dest_layer>]]"			
			assert i[0][0] in config.keys(), "No ensemble of name " + i[0][0] + " exists in the config"
			assert i[1][0] in config.keys(), "No ensemble of name " + i[1][0] + " exists in the config"
			assert i[0][1] <= len(config[i[0][0]]), "Layer " + str(i[0][1]) + " does not exist in ensemble " + i[0][0]  
			assert i[1][1] <= len(config[i[1][0]]), "Layer " + str(i[1][1]) + " does not exist in ensemble " + i[1][0]		
		retcode = True			
		return retcode
	
	
	def _verify_ensemble(self,ensemble_config):
		self.logger.info("Verifying Ensemble config")
		retcode = False
		assert isinstance(ensemble_config,list) , "Ensemble config must be a 1D list of <group,[hmul,vmul]> , where group is repeated hmul and vmul number of times"
		for item in ensemble_config:
			group = item[0]
			scaling_factor = item[1]
			assert len(scaling_factor) == 2 and all(isinstance(l,int) for l in scaling_factor), "Expected <int,int>, found : length = " + str(len(scaling_factor)) + " type = " + type(scaling_factor)
			assert isinstance(group,list) , "Group must a list of 2D layers"
			for slice in group:
				assert isinstance(slice,list) , "Layer must a 2D list of nodes"
				for row in slice:
					assert isinstance(row,list) , "Each row in a layer must a list"
					for column in row:
						assert isinstance(column,list) , "Each column in a row must a list of node_params"
						assert len(column) == 2, "Each element in a row of a layer must be of length , and of the form <node_params,synapse_config>" + str(ensemble_config)
						node_params = column[0]
						synapse_params = column[1]
						
						assert isinstance(node_params,dict) , "node_params must be a dict, found : " + str(type(synapse_params))
						assert isinstance(synapse_params,list) , "synapse_config must be a list, found : " +str(type(synapse_params))
						if synapse_params:
							for element in synapse_params:
								if element:
									assert len(element) == 3 and all([isinstance(element[0],int),isinstance(element[1],float),isinstance(element[2],dict)]) , "Each element in synapse_config must be of the form <layer_to_connect,receptive_field,synapse_parameters>" 
									#assert element[0] + len(group) >= 0 , "Cannot refer to layer " + str(element[0]) + " in a group of length " + str(len(group))
		retcode = True
		return retcode
	
	def getReceptiveField(self,f,nx,ny):
		return nx*f,ny*f
		
		
	def getSlice(self,ilayer,ensemble_config):
		i = 0 
		for t in ensemble_config:
			if ilayer >= i and ilayer < i + len(t[0]):
				return t[0][ilayer - i]
			i += len(t[0])
		
	def initNodes(self,ensemble_config,ensemble_id):
		"A 1 x n array containing the number of nodes in each layer"
		
		try:
			ensemble = []
			#if topology_object.verify(ensemble_config) == False:
			#	return
			self.logger.info("Generating nodes")
			for tuple in ensemble_config:
				group = tuple[0]
				x_span = tuple[1][0]
				y_span = tuple[1][1]
				n = len(group)
				pbar = ProgressBar(total=y_span*sum([ x_span*len(i) for l in group for i in l ]) , display_percentage=True )
				for l in range(n):
					
					layer = []
					m = len(group[l])
					for j in range( y_span * m ):
						
						layer.append(list())
						p = len(group[l][j%m])
						for i in range(x_span * p ):
							pbar.update()	
							neuron_params = group[l][j%m][i%p][0]
							idx = self.addNewNode(ensemble_id,neuron_params)	
							layer[j].append(idx)		
					ensemble.append(layer)
				pbar.close()
			return ensemble
		except Exception as e:
			self.logger.info("Exception in making nodes : %s" , e)
		
		
	def initConnections(self,ensemble_config,ensemble):
		try:
			self.logger.info("Making synapses. This might take a long time depending on the size of the network." )
			pbar = ProgressBar()
			for ilayer in range(len(ensemble)):
				mx,my = len(ensemble[ilayer][0]),len(ensemble[ilayer])
				slice=self.getSlice(ilayer,ensemble_config)
				s_slice = len(slice)
				for irow in range(len(ensemble[ilayer])):
					s_slice_row = len(slice[irow%s_slice])
					for inode in range(len( ensemble[ilayer][irow])):
						
						n = ensemble[ilayer][irow][inode]
						synapse_config = slice[irow%s_slice][inode%s_slice_row]
						for info_tuple in synapse_config[1]:
							if info_tuple:
								iprev_layer = ilayer + info_tuple[0]
								if iprev_layer >= 0 and iprev_layer < len(ensemble) :
									nx,ny = len(ensemble[iprev_layer][0]),len(ensemble[iprev_layer])
									pos_matrix = self.getCoordinates(my,ny,mx,nx)
									srow,scol=self.getReceptiveField(info_tuple[1],nx,ny)
									input_space_nodes = self.getConnList(pos_matrix[irow][inode],float(scol)/2,float(srow)/2,ensemble[iprev_layer])
									synapse_params  = info_tuple[2]
									pbar.update()
									self.connectInputNodes(input_space_nodes,n,synapse_params)
			pbar.close()			
		except Exception as e:
			self.logger.info("Exception in making connections %s" , e)
									
	def getVector(self , m , n):
		if m == n:
			return list(range(m))
		d = float(n-1)/(m+1)
		a = d
		return [a + (i-1)*d for i in range(1,m+1,1)]
			
	def getCoordinates(self,mx,nx,my,ny):
		xlist = self.getVector(mx,nx)
		ylist = self.getVector(my,ny)
		matrix = []
		for xpos in xlist:
			matrix.append([(xpos,ypos) for ypos in ylist])
		
		return matrix
		
	def getConnList(self,pos,sx,sy,prev_layer):
		try:
			connlist = []
			x = pos[0]
			y = pos[1]
			n = len(prev_layer)
			m = len(prev_layer[0])
			for j in range(len(prev_layer)):
				for i in range(len(prev_layer[j])):
					if ( i >= y - sy and i <= y + sy ) and ( j >= x - sx and j <= x + sx ) :  
						connlist.append(prev_layer[j][i])
					if i > y + sy:
						break
				if j > x + sx:
					break
			
			
			return connlist
		except Exception as e:
			self.logger.info("Exception in getting connection list : %s" ,e)
