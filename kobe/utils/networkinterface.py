import numpy as np
class Sensor():
	def __init__(self,target_method,target_params=None):
		self.target_method = target_method
		self.target_params = target_params
	
	def getTargetMethod(self):
		return self.target_method
	
	def setInputs(self):
		self.target_method(self.getData(),*self.target_params)
	
	def __call__(self,data,*args):
		transformed_data = self.transformation_func(data,*args)
		self.data = transformed_data
	
	def transformation_func(self,data):
		return data

	def getData(self):
		return self.data


class Actuator():
	def __init__(self,target_method,target_params=None,aggregation_function=None):
		self.target_method = target_method
		self.target_params = target_params
		if aggregation_function != None:
			self.aggregation_func = aggregation_function
		
	def getOutputs(self):
		self.raw_output = self.target_method(*self.target_params)
		
	def getRawOutput(self):
		return self.raw_output
	
	def __call__(self,*args):
		aggregated_output = self.aggregation_func(self.raw_output,*args)
		return aggregated_output
		
	def aggregation_func(self,data):
		return data
	
	

def mapping_wrapper(self,input,arguments):
	d = {}
	assert len(input) == len(arguments),"Malformed data array. Length of input does not match length of arguments,len(input):"+str(len(input))+" len(arguments):"+str(len(arguments))
	for row in zip(arguments,input):
		#assert len(row[0]) <= len(row[1]) , "Malformed data array. Length of argument row:"+str(len(row[0]))+" Length of input row:+"+str(len(row[1]))
		for i in range(len(row[0])):
			d[row[0][i]] = row[1][i]
	return d
		
		
def movement_wrapper(self,output,arguments):
	MOVEMENTS = ['noop', 'e', 'w', 'n', 's','ne','nw','se','sw']
	array = np.asarray(output , dtype=np.float64)
	len = array.shape[0]
	half = int(len/2)
	d = dict()
	d['s'] = sum(sum(array[half:,:]))
	d['n'] = sum(sum(array[:half,:]))
	d['e'] = sum(sum(array[:,half:]))
	d['w'] = sum(sum(array[:,:half]))
	d['ne'] = sum(sum(np.trui(arr)))
	d['sw'] = sum(sum(np.tril(arr)))
	d['nw'] = sum(sum(np.triu(np.flip(arr,axis=1))))
	d['se'] = sum(sum(np.triu(np.flip(arr,axis=0))))
	m = max(d)
	
	mean = np.mean(list(map(int,d.values())))
	var = np.var(list(map(int,d.values())))
	
	if max < mean + var*0.5:
		return 0
	
	for mov in MOVEMENTS:
		if mov == m:
			break
		
	return mov
		
def simple_wrapper(self,output):
	array = np.asarray(output , dtype=np.float64)
	if sum(sum(array)) > NetworkInterface.threshold*array.size:
		return 1
	else:
		return 0


class NetworkInterface():		
	threshold = 0.6
	def __init__(self):
		return
	def setInputSpecification(self,input_spec):
		self.input_specification = input_spec
	
	def setOutputSpecification(self,output_spec):
		self.output_specification = output_spec
	
		
	def addTransformer(self,name,spec):
		assert callable(spec[0])
		self.transformers[name] = spec
	
	def transform_set_inputs(self,**kw_inputs):
		for param , input in kw_inputs.items():
			if param in self.input_specification.keys():
				setter_function,transform_function,arguments = self.input_specification[param]
				if transform_function != None:
					import pdb
					pdb.set_trace()
					input= transform_function(input,arguments)
				setter_function(input)
	
	def transform(self,outputs):
		transformed_outputs = {}
		for name,spec in self.transformers.items():
			transform_function,args = spec
			if transform_function != None:
				output = transform_function(args)
			transformed_outputs[name] = output	
		return transformed_outputs
	
	
	@classmethod
	def mapping_wrapper(self,input,arguments):
		d = {}
		assert len(input) == len(arguments),"Malformed data array. Length of input does not match length of arguments,len(input):"+str(len(input))+" len(arguments):"+str(len(arguments))
		for row in zip(arguments,input):
			#assert len(row[0]) <= len(row[1]) , "Malformed data array. Length of argument row:"+str(len(row[0]))+" Length of input row:+"+str(len(row[1]))
			for i in range(len(row[0])):
				d[row[0][i]] = row[1][i]
		return d
		
	@classmethod	
	def movement_wrapper(self,output,arguments):
		MOVEMENTS = ['noop', 'e', 'w', 'n', 's','ne','nw','se','sw']
		array = np.asarray(output , dtype=np.float64)
		len = array.shape[0]
		half = int(len/2)
		d = dict()
		d['s'] = sum(sum(array[half:,:]))
		d['n'] = sum(sum(array[:half,:]))
		d['e'] = sum(sum(array[:,half:]))
		d['w'] = sum(sum(array[:,:half]))
		d['ne'] = sum(sum(np.trui(arr)))
		d['sw'] = sum(sum(np.tril(arr)))
		d['nw'] = sum(sum(np.triu(np.flip(arr,axis=1))))
		d['se'] = sum(sum(np.triu(np.flip(arr,axis=0))))
		m = max(d)
		
		mean = np.mean(list(map(int,d.values())))
		var = np.var(list(map(int,d.values())))
		
		if max < mean + var*0.5:
			return 0
		
		for mov in MOVEMENTS:
			if mov == m:
				break
			
		return mov
		
	@classmethod
	def simple_wrapper(self,output):
		array = np.asarray(output , dtype=np.float64)
		if sum(sum(array)) > NetworkInterface.threshold*array.size:
			return 1
		else:
			return 0
		
		
	
	
	
	
	
	
	
	