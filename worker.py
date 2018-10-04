#from pid.decorator import pidfile
import multiprocessing
from multiprocessing import Process , Pipe 
from multiprocessing.connection import wait
import redis
import jsonpickle
import signal
import logging
import logging.handlers
import pickle
import time
from kobe.utils import *
from kobe import getKobeLogger
#try:
#    #import kobe.utils
#except ModuleNotFoundError as e:
#	pass


#from kobe import *

import os,sys
import argparse

class BatchConsumer(Process):
	def __init__(self,name,network_id,db_url,conn):
		super().__init__()
		self.name = name
		self.db_url = db_url
		self.network_id = network_id
		self.init = False
		self.is_running = True
		self.node_map = ConnectionHandler(conn,channel='_nodes',init=Node)
		self.edge_map = ConnectionHandler(conn,channel='_edges',init=Params)
	
	def Init(self):
		if not self.init:
			install_dir = os.path.dirname(os.path.realpath(__file__))
			self.logger = InitLogger(os.path.join(install_dir , 'job_consumers.log'),multiprocessing.get_logger())
			self.job_q = RedisFIFOQueue(self.network_id+'_job_queue',self.db_url)
			self.result_set = redis.StrictRedis.from_url(self.db_url)
		
	def signal_handler(self, signal, frame):
		self.is_running = False
		self.logger.info("You pressed Ctrl+C!")
		try:
			time.sleep(1 * 5)
		except Exception as ex:
			pass
		sys.exit(0)
	
	def run(self):
		self.Init()
		self.logger.info('Entering run loop')
		while self.is_running:
			batch_job = self.job_q.wait_get()
			self.logger.debug('Received batch_job : %s',str(batch_job))
			job_done = True
			for item in batch_job.process_list:
				node = self.node_map[item]
				node.setLogger(self.logger)
				ensemble_params = batch_job.get_params()
				self.logger.debug('Starting to process node : %s',str(node))
				try:
					time_taken,result = node.process(self.node_map,self.edge_map,**ensemble_params)
					self.logger.info('Time taken to process node:%s is %s seconds',str(node).strip(),str(time_taken))
				except Exception as e:
					self.is_running = False
					job_done = False
					self.logger.error('Exception : %s ',e)
					break
				self.logger.debug('Done processing node : %s',item)
			if job_done == True:
				self.logger.info('Processed job : %s',batch_job.job_id)
				self.result_set.sadd(self.network_id+'_result_set',batch_job.job_id)
		self.logger.info('Exiting run loop')
				
def signal_handler(signal, frame):
	logger.info("You pressed Ctrl+C!")
	sys.exit(0)	
	
	
def InitLogger(file,logger):
	logger.setLevel(logging.INFO)
	log_handler = logging.handlers.RotatingFileHandler(file, mode='a', maxBytes=100000000, backupCount=2, encoding=None, delay=0)
	LOGGING_FORMAT = "%(process)d: %(asctime)s %(levelname)-s \t [%(module)s->%(processName)s]:%(lineno)d - %(message)s"
	log_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
	logger.addHandler(log_handler)
	return logger
	
	
def InitArgParser():
	parser = argparse.ArgumentParser(description='Spawn Kobe Consumers. ')
	parser.add_argument('network' ,help='The name of the network to process as given in its config file.')
	parser.add_argument('db_url', default = 'localhost', help='The url of the redis database. eg: "redis://localhost:6379"')
	parser.add_argument('-x' ,dest ='num_workers' , default = None , help='Number of consumer processes to spawn. (Default : no. of cpus available )')
	parser.add_argument('-gc' ,dest ='global_cache', default = 2048 , help='Cache size for Main Process. ( Default : 2048)')
	parser.add_argument('-lc' ,dest ='per_process_cache', default = 512 , help='Cache size for each Consumer Process. ( Default : 512)')
	
	return parser

#@pidfile()	
def main(argv):
	global logger,consumers,GLOBAL_CACHE_SIZE,PER_PROCESS_CACHE_SIZE
	logger = InitLogger(__name__+'.log',getKobeLogger())
	parser = InitArgParser()
	args = parser.parse_args(argv[1:])
	multiprocessing.log_to_stderr()
	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGTERM, signal_handler)
	db_url = args.db_url 
	GLOBAL_CACHE_SIZE = args.global_cache
	PER_PROCESS_CACHE_SIZE = args.per_process_cache
	network_name =  args.network
	datastore = RedisDatastore(db_url)
	try:
		rconn = redis.StrictRedis.from_url(db_url)
	except Exception as e:
		logger.error('Exception while conecting to db : %s' , e)
		sys.exit(1)
	if rconn.exists(network_name):
		ret =  rconn.hget(network_name , 'addr')
	else:
		print('Network does not exist in database, exiting...')
		sys.exit(1)
	network_id = ret.decode('UTF-8')
	logger.info('network_id : %s',network_id )
	num_consumers = multiprocessing.cpu_count() if args.num_workers == None else args.num_workers
	print('Creating {} consumers'.format(num_consumers))
	
	consumers = []
	parent_conns = []
	for i in range(num_consumers):
		parent_conn,child_conn = Pipe()
		c = BatchConsumer('Consumer-'+str(i),network_id,db_url,child_conn)
		parent_conns.append(parent_conn)
		consumers.append(c)
		c.start()
		
	while True:
		for r in wait(parent_conns):
			try:
				opr,channel,obj = r.recv()
				logger.debug('Received request : opr : %s , channel :  %s , obj : %s',opr,channel,str(obj))
			except EOFError:
				parent_conns.remove(r)
			else:
				if opr == 'get':
					logger.debug('Sending request : %s',str(obj))
					ret = datastore.get(network_id+channel,obj)
					logger.debug('Received data : %s',str(ret))
					r.send(ret)
				if opr == 'set':
					datastore.set(network_id+channel,obj[0],obj[1])
	
	for c in consumers:
		c.join()
	
	
	
if __name__ == "__main__":
	
	main(sys.argv)
	
	
	