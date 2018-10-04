from kobe import *
from third_party import *
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
	mnist_url = "http://yann.lecun.com/exdb/mnist/"
	mnist_dir = os.path.join(install_dir , 'mnist_data')
	if not os.path.exists(mnist_dir):
		utils.downloadFileFromUrl(mnist_url+'train-images-idx3-ubyte.gz',target_folder=mnist_dir)
		utils.downloadFileFromUrl(mnist_url+'train-labels-idx1-ubyte.gz',target_folder=mnist_dir)
		utils.downloadFileFromUrl(mnist_url+'t10k-images-idx3-ubyte.gz',target_folder=mnist_dir)
		utils.downloadFileFromUrl(mnist_url+'t10k-labels-idx1-ubyte.gz',target_folder=mnist_dir)
	#pdb.set_trace()
	mndata = MNIST(mnist_dir)
	mndata.gz = True
	images, labels = mndata.load_training()
	char2img_map = getImgData(images , labels)

	topology = Topology('network.yaml','redis://localhost:6379')	
	print (topology.addr)
	if topology.initialized == True:
		network = Network(topology.network_name,'localhost')
	else:
		logger.info('Error : Network not initialized, exiting')
		sys.exit()
	
	env = SimpleArithmeticEnv(i_resolution=(50,50),slate_resolution=(200,200),char2img_map=char2img_map,mn_object=mndata,operator='2',threshold_probability=0.9)		 

	
	eye_sensor = Sensor(network.setNodeInputs,target_params=(network.getEnsemble('ensemble1').getLayer(0),('params','membrane_potential',)))
	reward_sensor = Sensor(network.setEnsembleParams,target_params=('ensemble1','neuromodulation_factor'))
	
	network.addSensor(eye_sensor)
	network.addSensor(reward_sensor)
	
	i_movement_actuator = Actuator(target_method=network.getOutputs,target_params=(network.getEnsemble('ensemble2').getLayer(-1),),aggregation_function=movement_wrapper)
	write_flag_actuator = Actuator(target_method=network.getOutputs,target_params=(network.getEnsemble('ensemble1').getLayer(-1),),aggregation_function=simple_wrapper)
	cursor_movement_actuator = Actuator(target_method=network.getOutputs,target_params=(network.getEnsemble('ensemble3').getLayer(0),),aggregation_function=movement_wrapper)


	network.addActuator(i_movement_actuator)
	network.addActuator(write_flag_actuator)
	network.addActuator(cursor_movement_actuator)

	#pdb.set_trace()
	network.dumpAsString('generated_network.txt')
	
	#rendering_stream = StringIO.StringIO()
	probe1 = ProbeLogger('probe1')

	probe1.addHandler(logging.FileHandler(os.path.join(install_dir,'probe1.results')))
	
	#probe1.addHandler(logging.StreamHandler(stream=rendering_stream))
	
	
	probe2 = ProbeLogger('probe2')
	
	probe2.addHandler(logging.FileHandler(os.path.join(install_dir,'probe2.results')))
	
	#renderer = NetworkRenderer()
	#renderer.addGraph('graph1',TimeSeries,height=500,width=500,x_label='time',y_label='V',last_n=30)
	#renderer.addGraph('graph2',TimeSeries,height=500,width=500,x_label='time',y_label='u',last_n=20)
	
	graph = plt.timeseries()
	#pdb.set_trace()
	obs, reward, done, info = env.reset()
	
	t = 0
	
	while t < 10000:
		env.render()
		#action = env.action_space.sample()
		#interface.transform_set_inputs(eye_input=obs,reward=reward)
		
		#pdb.set_trace()
		if obs.dtype == np.float32: obs = obs.astype(np.float64)
		eye_sensor(obs)
		reward_sensor(reward)
		
		network.simulate()
		
		#pdb.set_trace()
		
		action = { 'i_movement' : i_movement_actuator('params','membrane_potential') ,
		'write_flag' : write_flag_actuator('params','membrane_potential') ,
		'cursor_movement' : cursor_movement_actuator('params','membrane_potential') 
		}
	
		#outputs = network.getOutputs(network.getEnsemble('ensemble2').getLayer(-1),network.getEnsemble('ensemble1').getLayer(-1),network.getEnsemble('ensemble3').getLayer(0))
		
		#outputs = 
		
		#action = {
		#'i_movement': movement_wrapper(filter_output(outputs[0],None,'params','output')),
		#'write_flag': simple_wrapper(filter_output(outputs[1],None,'params','output')),
		#'cursor_movement': movement_wrapper(filter_output(outputs[2],None,'params','output'))
		#}
		
		
		
		raw_outputs = (i_movement_actuator.getRawOutput(),write_flag_actuator.getRawOutput(),cursor_movement_actuator.getRawOutput())
	
		probe1.log('i_movement',raw_outputs[0],t)
		probe1.log('write_flag',raw_outputs[1],t)
		probe1.log('cursor_movement',raw_outputs[2],t)
		
		probe2.log('ensemble1.layer1',network.getOutputs(network.getEnsemble('ensemble1').getLayer(1)),t)
		probe2.log('ensemble2.layer2',network.getOutputs(network.getEnsemble('ensemble2').getLayer(2)),t)
		probe2.log('ensemble1.layer0',network.getOutputs(network.getEnsemble('ensemble3').getLayer(0)),t)

		print (action)
		#pdb.set_trace()


		graph.update(x=t,y=raw_outputs[0][0][0]['params']['membrane_potential'])


		

		#renderer.updateGraph('graph1','V',t,raw_outputs[0][0][0]['params']['membrane_potential'])
		#renderer.updateGraph('graph2','u',t,raw_outputs[0][0][0]['params']['utilization_factor'])
		#renderer.render()
		
		obs, reward, done, info = env.step(action)
		t += 1
		if done == True:
			break
	env.close()

	
	
	
	
