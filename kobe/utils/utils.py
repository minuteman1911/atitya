from kobe.utils.functools_modified import lru_cache
from functools import wraps
from datetime import datetime
import logging
import redis
import pickle
import random
import requests
import json
import time
import os
import numpy as np
import pdb
GLOBAL_CACHE_SIZE = 2048
PER_PROCESS_CACHE_SIZE = 512


logger = logging.getLogger(__name__)



def item_getter(object,*args):
	res = object
	for arg in args:
		res = res[arg]
	return res
	
def item_setter(object,value,*args):
	res = object
	for arg in args[:-1]:
		res = res[arg]
	res[args[-1]] = value
	

def _log_duration(f):
	@wraps(f)
	def new_f(*args, **kwargs):
		start_time = time.time()
		val = f(*args, **kwargs)
		end_time = time.time()
		time_taken = end_time - start_time
		return time_taken,val
	return new_f

def randomizeParams(param_dict):

	retdict = {}
	for k , v in param_dict.items():
		if isinstance(v,tuple) or isinstance(v,list):
			if len(v) ==2:
				retdict[k] =  np.random.uniform(v[0] , v[1])
		if isinstance(v , str):
			retdict[k] = v
		if isinstance(v , int) or isinstance(v , float):
			retdict[k] = v
	return retdict

def getNewId(exclude_set,size,prefix=''):
	while True:
		id = prefix  + ''.join(random.choice('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(size))
		if id not in exclude_set:
			break
	return id

class Params(dict):
	def __init__(self,**params):
		dict.__init__(self, params)
			
	def __getattr__(self, attr):
		item = self.get(attr)
		assert item != None, "Parameter not initialized : " + attr
		return item
	
	def __setattr__(self, key, value):
		self.__setitem__(key,value)	
	
class RedisFIFOQueue():
	def __init__(self,name,db_url,max_size=None):
		self.name = name
		self.logger = logger
		self.conn = redis.StrictRedis.from_url(db_url)
		self.max_size = max_size
		self.logger.info('Initialized Redis connection to %s, object : %s max_size : %s',str(self.conn),db_url,max_size)
	
	def put(self,item):
		try:
			pickled = pickle.dumps(item)
		except Exception as e:
			self.logger.error('Exception : %s',e)
		self.conn.rpush(self.name , pickled)
		if self.max_size:
			self.conn.ltrim(self.name,0,self.max_size)
	
	def get(self):
		unpickled = pickle.loads(self.conn.lpop(self.name))
		return
		
	def wait_get(self):
		pickled = self.conn.blpop(self.name)
		self.logger.info('pickled : %s',str(pickled))
		try:
			unpickled = pickle.loads(pickled[1])
		except Exception as e:
			self.logger.error('Exception : %s',e)
		return unpickled
		
	def size(self):
		return self.conn.llen(self.name)
		
		
class RedisDatastore():
	def __init__(self,url):
		self.conn = redis.StrictRedis.from_url(url)
		self.logger = logger
		self.logger = logger.info('Connected to DB')
			
	@lru_cache(GLOBAL_CACHE_SIZE)
	def get(self,hname,key):
		val = self.conn.hget(hname,key)
		return json.loads(val)
			
	def set(self,hname,key,val):
		self.conn.hset(hname,key,json.dumps(val))
		self.get.cache_update(key,val) # Dirty hack to update the cache when updating the database. Currently in the modified functools.py file, must be moved to _functools ( C implementation )
		
class ConnectionHandler():
	def __init__(self,connection,channel,init=None):
		self.conn = connection
		self.channel = channel
		self.init = init
		
	@lru_cache(PER_PROCESS_CACHE_SIZE)
	def __getitem__(self,key):
		self.conn.send(('get',self.channel,(key)))
		while True:
			if self.conn.poll(1):
				break
		retobj = self.conn.recv()
		if self.init:
			return self.init(**retobj)
		else:
			return retobj
		
	def __setitem__(self,key,val):
		self.conn.send(('set',self.channel,(key,val)))
		self.__getitem__.cache_update(key,val)
	
	def close(self):
		self.conn.close()

class Job():
	def __init__(self):
		self.process_list = []
		self.params = None
		self.job_id = getNewId(self.process_list,5)
		
	def append(self,item):
		self.process_list.append(item)
		
	def length(self):
		return len(self.process_list)
		
	def set_params(self,params):
		self.params = params
		
	def get_params(self):
		return self.params
	
	def __str__(self):
		return "<job_id:"+self.job_id+", process_list:"+str(self.process_list)+", params : "+str(self.params)+">"
		
def downloadFileFromUrl(url , target_folder):
	print("Downloading from " + url )
	if not os.path.exists(target_folder):
		os.mkdir(target_folder)
	r = requests.get(url)
	with open(os.path.join ( target_folder , os.path.basename(url) ) ,'wb') as f:
		f.write(r.content)	