
from dictdiffer import diff, patch
import logging
import json
from json import JSONDecodeError
import copy

class ProbeLogger():
	LOGGING_FORMAT = ""
	def __init__(self,probe_name,frame_size=3):
		self.frame_size = frame_size
		self.logger = self._getLogger(probe_name)
		self.probes = {}
	
	def addHandler(self,handler):
		handler.setFormatter(logging.Formatter(ProbeLogger.LOGGING_FORMAT))
		handler.setLevel(logging.INFO)
		self.logger.addHandler(handler)
	
	def _getLogger(self,probe_name):
		logger = logging.getLogger(probe_name)
		logger.setLevel(logging.INFO)
		return logger
		
	def _initProbe(self,id):
		assert ' ' not in id, "Probe id cannot contain spaces"
		self.probes[id] = {'frame_count':0 , 'iter_count':0 , 'data' : None}
	
	def _startNewFrame(self,id,data,*args):
		self.probes[id]['frame_count'] += 1
		self.probes[id]['iter_count'] = 0
		self.probes[id]['data'] = copy.deepcopy(data)
		self.logger.info('---')
		self.logger.info('Start Frame #'+str(self.probes[id]['frame_count']))
		self.logger.info(id + '|'+ json.dumps(args)+ '|' +json.dumps(data))
	
	def log(self,id,data,*args):
		if id not in self.probes.keys():
			self._initProbe(id)
			self._startNewFrame(id,data,*args)
		else:		
			if self.probes[id]['iter_count'] >= self.frame_size :
				self._startNewFrame(id,data,*args)		
			else:
				self.probes[id]['iter_count'] += 1
				previous_data = self.probes[id]['data']
				delta = diff(previous_data,data)
				self.logger.info(id+ '|'+json.dumps(args)+ '|'+ json.dumps(list(delta)))
		
	def close(self):
		for id in param.keys():
			logger.info('---')
			
class ProbeParser():
	def __init__(self,input_stream):
		self.fp = open(input_stream,'r')
		self.probes = {}
	
	def _startFrame(self,id,args,data):
		if id not in self.probes.keys():
			self.probes[id] = {'frame_count':0 , 'iter_count':0 , 'data' : data}
		else:
			self.probes[id]['data'] = data
	
	def _processIter(self,line):
		if '---' in line:
			line = self.fp.readline()
			if 'start frame' in line[:15].lower():
				line = self.fp.readline()
				id, args, data = line.split('|',2)
				args = json.loads(args)
				data = json.loads(data.strip())
				self._startFrame(id,args,data)
				return args,data
			else:
				raise KeyError('Probe not initialized, frame possibly corrupt, skipping to next frame in file')
		else:
			id, args, delta = line.split('|',2)
			if id not in self.probes.keys():
				raise KeyError('Probe not initialized, frame possibly corrupt, skipping to next frame in file')
			args = json.loads(args)
			delta = json.loads(delta.strip())	
			self.probes[id]['iter_count'] += 1
			patched = patch(delta,self.probes[id]['data'])
			return args,patched
	
	def __iter__(self):
		return self
	
	def __next__(self):
		args = ''
		result = None
		line = self.fp.readline()
		if not line:
			raise StopIteration()
		try:
			args , result = self._processIter(line)
		except (KeyError,JSONDecodeError) as e:
			pass
		return args,result

if __name__ == "__main__":


	"""
	monty = [1,{'a':4,'g':[2,3,4]},3,4]	
	python = {'cooo' : 5 , 'strange' : 3}
	foobar = [[['tooo'],['goo']],[],['zll'],['wewe','ffff','ggmu']]
	
	
	probe = ProbeLogger('probe')
	probe.addHandler(logging.FileHandler('probe.results'))
	
	for i in range(10):
		monty[1]['a'] = i*2
		python['kroos'] = 3 + i
		foobar[0][1] = 'bang' *i
		probe.log('monty',monty,i,'foo')
		probe.log('python',python,i,'foovoo')
		probe.log('foobar',foobar,i,'foorr')
	"""
	
	
	
	output = ProbeParser('probe.results')
	import pdb
	#pdb.set_trace()
	for item in output:
		print(item)