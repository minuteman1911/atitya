import numpy as np
import math
import random
import json
import pdb
import time
from kobe.utils import Job,getNewId
import logging

		
class Ensemble(object):
	def __init__(self,network_id,ensemble_id,job_q,rconn,batch_size=None):
		self.ensemble_id = ensemble_id
		self.ensemble = []
		self.ensembletime = 0
		self.network_id = network_id
		self.job_q = job_q
		self.rconn = rconn
		self.logger = logging.getLogger(__name__)#logger
		self.logger.info('Initializing ensemble : %s',str(ensemble_id))
		estring = self.rconn.hget(network_id+'_ensembles',ensemble_id)
		self.ensemble = json.loads(estring)
		pstring = self.rconn.hget(network_id+'_ensemble_params',ensemble_id)
		
		params = json.loads(pstring) if pstring != None else {}
		self.logger.info('Loaded ensemble : %s , params : %s', str(self.ensemble),str(params))
		if not batch_size:
			self.batch_size = len(self.ensemble[0][0])
		self.initParams(params)
		self._processed = False		
		
	def initParams(self,params):
		self.logger.info('Initializing params for ensemble : %s , params : %s',self.ensemble_id,str(params))
		self.ensemble_delay = params.get('delay')
		self.neuromodulation_factor = params.get('neuromodulation_factor_init')
		self.train = False
		self.step_time = self.ensemble_delay / float(len(self.ensemble))		
		
	def getLayer(self,i):
		assert abs(i) < len(self.ensemble) ,"Layer "+str(i)+" does not exist for ensemble: "+str(self.ensemble_id)+", length : "+str(len(self.ensemble))
		return self.ensemble[i]

	
	def evaluate(self,simulation_time):
		t = simulation_time
		dt = self.step_time
		params = {'t' : t , 'm': self.neuromodulation_factor , 'train' : self.train}
		
		
		for ilayer in range(len(self.ensemble)):
			layer = self.ensemble[ilayer]
			self.logger.debug('Processing %s layer:%s',self.ensemble_id , str(layer))
			print('Processing '+ self.ensemble_id +' layer '+ str(ilayer))
			t += dt
			queued_jobs = []
			batch_job = Job()
			batch_job.set_params(params)
			queued_jobs.append(batch_job.job_id)
			self.logger.info('batch_size %s',str(self.batch_size))
			for irow in range(len(layer)):
				for inode in range(len(layer[irow])):
					if batch_job.length() >= self.batch_size:
						#print (batch_job)
						self.job_q.put(batch_job)
						batch_job = Job()
						batch_job.set_params(params)
						queued_jobs.append(batch_job.job_id)
					batch_job.append(layer[irow][inode])
			self.logger.debug('Scheduling Batch Job : %s in queue',str(batch_job))
			self.job_q.put(batch_job)
			result_set = set(self.rconn.smembers(self.network_id+'_result_set'))
			while not set(queued_jobs) <= set( i.decode('UTF-8') for i in result_set):
				#print(result_set)
				#time.sleep(1)
				result_set = set(self.rconn.smembers(self.network_id+'_result_set'))
			pipe = self.rconn.pipeline()
			for job in queued_jobs:
				pipe.srem(self.network_id+'_result_set',job)
			pipe.execute()
			print('Done processing '+self.ensemble_id+' layer: ' + str(ilayer))  
			  
		simulation_time += self.ensemble_delay
		return simulation_time
	
	
	
	