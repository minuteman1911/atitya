import sys
import os
cwd = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cwd + '/../..')
import pdb
#pdb.set_trace()
from kobe import *
from kobe.third_party import *
import kobe.utils as utils
import kobe.rendering as plt
import gzip, pickle
import numpy as np
import sys,os
from io import StringIO
import logging
import requests
import pdb
from mnist import MNIST

def getImgData(images,labels):
	char2img_map = { str(l) : [] for l in set(labels)}
	for data,label in zip(images,labels):
		char2img_map[str(label)].append(np.reshape(np.array(data),(28,28)))
			
	char2img_map[' ']=[np.zeros(shape=(28,28),dtype=np.uint8)]
	return char2img_map

def InitLogger(file):
	logger = getKobeLogger()
	logger.setLevel(logging.INFO)
	log_handler = logging.StreamHandler(sys.stdout)#logging.FileHandler(file)
	LOGGING_FORMAT = "%(process)d: %(asctime)s %(levelname)-s \t %(module)s:%(lineno)d - %(message)s"
	log_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
	logger.addHandler(log_handler)
	return logger		

def mapping_wrapper(input,arguments):
	d = {}
	assert len(input) == len(arguments),"Malformed data array. Length of input does not match length of arguments,len(input):"+str(len(input))+" len(arguments):"+str(len(arguments))
	for row in zip(arguments,input):
		#assert len(row[0]) <= len(row[1]) , "Malformed data array. Length of argument row:"+str(len(row[0]))+" Length of input row:+"+str(len(row[1]))
		for i in range(len(row[0])):
			d[row[0][i]] = row[1][i]
	return d
	
def movement_wrapper(data,*args):
	MOVEMENTS = ['noop', 'e', 'w', 'n', 's','ne','nw','se','sw']
	output = filter_output(data,None,*args)
	array = np.asarray(output , dtype=np.float64)
	len = array.shape[0]
	half = int(len/2)
	d = dict()
	d['s'] = sum(sum(array[half:,:]))
	d['n'] = sum(sum(array[:half,:]))
	d['e'] = sum(sum(array[:,half:]))
	d['w'] = sum(sum(array[:,:half]))
	d['ne'] = sum(sum(np.triu(array)))
	d['sw'] = sum(sum(np.tril(array)))
	d['nw'] = sum(sum(np.triu(np.flip(array,axis=1))))
	d['se'] = sum(sum(np.triu(np.flip(array,axis=0))))
	
	m = max(d.items(),key=lambda x:x[1])
	
	mean = np.mean(list(map(int,d.values())))
	var = np.var(list(map(int,d.values())))
	
	if m[1] <= mean + var*0.5:
		return 0
		
	return m[0]
	
threshold = 0.5
def simple_wrapper(data,*args):
	output = filter_output(data,None,*args)
	array = np.asarray(output , dtype=np.float64)
	if sum(sum(array)) > threshold*array.size:
		return 1
	else:
		return 0	


def item_getter(object,*args):
	res = object
	for arg in args:
		res = res[arg]
	return res

def filter_output(output,cast=None,*params):
	if cast != None:
		return [ [ cast(item_getter(i,*params)) for i in list1 ] for list1 in  output]
	else:
		return [ [ item_getter(i,*params) for i in list1 ] for list1 in  output]

def getContext(display):
	#platform = pyglet.window.get_platform()
	#display = platform.get_default_display()
	screen = display.get_default_screen()
	
	template = pyglet.gl.Config(alpha_size=8)
	config = screen.get_best_config(template)
	context = config.create_context(None)
	return context


	
if __name__ == "__main__":
	install_dir = os.path.dirname(os.path.realpath(__file__))
	logger = InitLogger('kobe_test'+'.log')
	
	topology = Topology('network2.yaml','redis://localhost:6379')	
	print (topology.addr)
	if topology.initialized == True:
		network = Network(topology.network_name,'localhost')
	else:
		logger.info('Error : Network not initialized, exiting')
		sys.exit()
	#pdb.set_trace()
	filehash = network.update_node_object_file(os.path.join(install_dir,'node.py'))
	
	eye_sensor = Sensor(network.setNodeInputs,target_params=(network.getEnsemble('retina').getLayer(0),('params','membrane_potential',)))

	
	network.addSensor(eye_sensor)

	network.dumpAsString('generated_network.txt')
	
	probe1 = ProbeLogger('probe1.results')	
	probe2 = ProbeLogger('probe2.results')

	
	graph = plt.timeseries()
	
	obs = np.random.random((32,32))
	t = 0
	
	while t < 10:
		if obs.dtype == np.float32: obs = obs.astype(np.float64)
		eye_sensor(obs)
		network.simulate()		
	
		#raw_outputs = (i_movement_actuator.getRawOutput(),write_flag_actuator.getRawOutput(),cursor_movement_actuator.getRawOutput())
	
		#probe1.log('i_movement',raw_outputs[0],t)
		#probe1.log('write_flag',raw_outputs[1],t)
		#probe1.log('cursor_movement',raw_outputs[2],t)
		
		probe2.log('ganglion_cell_layer',network.getOutputs(network.getEnsemble('retina').getLayer(3)),t)

		#pdb.set_trace()


		#graph.update(x=t,y=raw_outputs[0][0][0]['params']['membrane_potential'])


		t += 1

	print ("End of simulation")


	
	
	
	
