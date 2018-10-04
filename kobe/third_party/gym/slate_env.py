
import gym
from gym import Env, logger
from gym.spaces import Discrete, Tuple ,Dict , Box
from gym.utils import colorize, seeding
import numpy as np
from six import StringIO
import sys
import math
from random import choice 
from kobe.rendering.plots import image_plot
#from gym.envs.classic_control import rendering
import pdb


	
def split_num(n,parts,divisor=2):
	ret = [round(n/divisor)]*(parts-1) 
	ret.append(n - sum(ret))
	return ret
		

class Pointer2D(object):
	MOVEMENTS = ['noop', 'e', 'w', 'n', 's','ne','nw','se','sw']
	def __init__(self,max,min=(0,0)):
		self.xmax = int(max[0])
		self.ymax = int(max[1])
		self.xmin = int(min[0])
		self.ymin = int(min[1])
		self.position = (self.xmin + int((self.xmax-self.xmin)/2),self.ymin + int((self.ymax - self.ymin)/2))
	
	def get_corners(self,frame_shape):
		x1,x2 = max(0,self.position[0]-frame_shape[0]/2),min(self.xmax-1,self.position[0]+frame_shape[0]/2)
		y1,y2 = max(0,self.position[1]-frame_shape[1]/2),min(self.ymax-1,self.position[1]+frame_shape[1]/2)
		return map(int,[x1,x2,y1,y2])
	
	def get_position(self):
		return self.position
	
	def move(self, movement):
		named = self.MOVEMENTS[movement]
		x, y = self.get_position()
		if named == 'noop':
			pass
		elif named == 'w':
			x -= 1
		elif named == 'e':
			x += 1
		elif named == 'n':
			y += 1
		elif named == 's':
			y -= 1
		elif named == 'ne':
			x += 1
			y += 1
		elif named == 'nw':
			x -= 1
			y += 1
		elif named == 'se':
			x += 1
			y -= 1
		elif named == 'sw':
			x -= 1
			y -= 1
		else:
			raise ValueError("Unrecognized direction: {}".format(named))
		if ( x > self.xmin and x < self.xmax ) and ( y > self.ymin and y < self.ymax):
			self.position = (x,y)
			return True
		return False
		
	def __str__(self):
		return str(self.position)
	
class SlateEnv(Env):
	
	def __init__(self,i_resolution,slate_resolution,char2img_map,operator,time_step=1,cursor_size=2):
		self._verify_img_map(char2img_map)
		# Keep track of this many past episodes
		self.last = 10
		# Aritmetic operation to be performed ( +, - , / , x)
		self.operator = operator
		self.observation_viewer = None 
		#self.action_viewer = None
		assert len(i_resolution) == 2 , "i_resolution must be a tuple of length 2 "
		self.i_resolution = i_resolution
		assert len(slate_resolution) == 2,"slate_resolution must be a tuple of length 2 "
		self.slate_resolution = slate_resolution
		self.render_mode = 'window'
		self._tick = time_step
		self.cursor = np.array([[0.1,0.1,0.1],[0.1,0.3,0.1],[0.1,0.1,0.1]])
		#self.cursor = np.array([[0.4,0.4],[0.4,0.4]])
		self.set_cursor_size(self.cursor.shape[0]+1)
		# Three sub-actions:
		#	1. Move eye head left or write (or up/down)
		#	2. Write or not
		#	3. Where to write ( 2d position )
		self.action_space = Dict({
		'i_movement' : Discrete(len(Pointer2D.MOVEMENTS)) ,
		'write_flag' : Discrete(2), 
		'cursor_movement': Discrete(len(Pointer2D.MOVEMENTS))
		})
		# One observation:
		#	1. image at i_position +- i_resolution
		self.observation_space = Dict({
		'eye_input' : Box(low=0,high=1,shape=self.i_resolution,dtype=np.uint8)
		})
		self.seed()
		self.reset()
		
	def __del__(self):
		self.close()	
	
	def close(self):
		if self.observation_viewer:
			self.observation_viewer.close()
	
	@property
	def time_limit(self):
		"""If an agent takes more than this many timesteps, end the episode
		immediately and return a negative reward."""
		# (Seemingly arbitrary)
		return 200
	
	def set_cursor_size(self,size):
		self._cursor_size = size
	
	def _verify_img_map(self,char2img_map):
		if len(set([x[0].shape for x in char2img_map.values()])) != 1:
			raise ValueError("Malformed char to image dict")
		self.char2img_map = char2img_map
	
	def reset(self):
		
		self._ticker = 0
		length = 3
		self.input_string,self.input_data = self.generate_input_data(length)
		left_padding,right_padding = split_num(self.slate_resolution[0] - self.input_data.shape[1],2,2)
		#pdb.set_trace()
		bottom_padding, top_padding   = split_num(int(self.slate_resolution[1]/2) - self.input_data.shape[0],2,int(self.slate_resolution[1]/2) - self.input_data.shape[0])
		self.input_data = np.pad(self.input_data,((top_padding,bottom_padding),(left_padding,right_padding)),'constant',constant_values=(0))
		self.target_string , self.target_data = self.target_from_input_data(self.input_string)
		top_padding , bottom_padding = bottom_padding , top_padding
		self.target_data = np.pad(self.target_data,((top_padding,bottom_padding),(left_padding,right_padding)),'constant',constant_values=(0))
		action_area = np.zeros(shape=self.target_data.shape,dtype=np.uint8)
		self.input_data = np.vstack((self.input_data,action_area))
		self.action_area_size = action_area.shape
		self.read_head = Pointer2D(self.input_data.shape)
		self.write_head = Pointer2D(self.input_data.shape,(self.input_data.shape[0]-action_area.shape[0],self.input_data.shape[1]-action_area.shape[1]))
		
		return (self._get_obs(),0,False,{})
		
		
		
	def _get_obs(self):
		#pdb.set_trace()
		x1,x2,y1,y2 = self.read_head.get_corners(self.i_resolution)
		self._set_i_focus(x1,x2,y1,y2)
		#np.take(self.input_data, [x1:x2,y1:y2],mode='clip')
		return self.input_data[x1:x2,y1:y2]
		
	def _set_i_focus(self,x1,x2,y1,y2):
		self.i_pos = (x1,x2,y1,y2)
		
	def _get_i_focus(self): 
		return self.i_pos
		
	def _get_action_area(self):
		x1 = self.input_data.shape[0]-self.action_area_size[0]
		y1 = self.input_data.shape[1]-self.action_area_size[1]
		return self.input_data[x1:,y1:]
		
	def seed(self, seed=None):
		self.np_random, seed = seeding.np_random(seed)
		return [seed]

	def render_observation(self):
		arr1 = np.array(np.dot(255,self.input_data),dtype=np.uint8)
		x,y = arr1.shape
		arr2 = self.render_i_frame(arr1.shape)
		arr = np.concatenate((arr1.reshape(x,y,1),arr1.reshape(x,y,1),arr2.reshape(x,y,1)),axis=2)
		return arr
		

	#def render_action(self):
	#	#arr1 = np.array(np.dot(255,self.target_data),dtype=np.uint8)
	#	arr1 = np.array(np.dot(255,self._cumulative_action),dtype=np.uint8)
	#	x,y = arr1.shape
	#	arr2 = self.render_i_frame(arr1.shape)
	#	arr = np.concatenate((arr1.reshape(x,y,1),arr1.reshape(x,y,1),arr2.reshape(x,y,1)),axis=2)
	#	return arr
		
	def render_i_frame(self,shape):
		x1,x2,y1,y2 = self._get_i_focus()
		arr2 = np.zeros(shape=shape,dtype=np.uint8)
		if x1 > 0 and x1 < len(arr2):
			arr2[x1][y1:y2] = 255
		if x2 > 0 and x2 < len(arr2):
			arr2[x2][y1:y2] = 255
		if y1 > 0 and y1 < len(arr2[0]):
			arr2[x1:x2,y1] = 255
		if y2 > 0 and y2 < len(arr2[0]):
			arr2[x1:x2,y2] = 255
		return arr2
	#def render_image(self,*args):
	#	assert len(args) <=3, "Maximum 3 arrays, each for RGB"
	#	retarr = None
	#	for arr in args:
	#		assert len(arr.shape) < 4,"Maximum 3 axes per array are possible, i.e. shape can be either of (x,) , (x,y) , (x,y,z)"
	#		
	#		arr1 = np.array(np.dot(255,arr),dtype=np.uint8)
	#		x , y = arr1.shape
	#		if len(arr.shape) == 2:
	#			arr1 = arr1.reshape(x,y,1)
	#		
	#		if retarr == None:
	#			retarr = arr1
	#		retarr.hstack(retarr,arr1)
	#	return retarr
		
		
	def render(self):
		obs = self.render_observation()
		#act = self.render_action()
		if self.render_mode == 'window':
			if not self.observation_viewer:
				self.observation_viewer = image_plot()
				#self.observation_viewer = rendering.SimpleImageViewer()
				#self.action_viewer = rendering.SimpleImageViewer()
			pdb.set_trace()
			self.observation_viewer.update(new_data=obs)			
			#self.observation_viewer.imshow(obs)
			#self.action_viewer.imshow(act)
	
	def step(self,action):
		try:
			assert self.action_space.contains(action)
			info = {}
			reward = 0
			done = False
			self._ticker += self._tick
			i_movement = action['i_movement']
			write_flag = action['write_flag']
			cursor_movement = action['cursor_movement']
			#pdb.set_trace()
			self.write_head.move(cursor_movement)
			print (self.write_head)
			if write_flag == 1:
				self._write_at_cursor()
			reward,done = self.check_reward(cursor_movement)
			
			self.read_head.move(i_movement) # call before _get_obs
			
			obs = self._get_obs()
			if self._ticker > self.time_limit:
				reward = -1.0
				done = True
			return (obs, reward, done, info)
		except Exception as e:
			print(e)
	
	def _write_at_cursor(self):
		x,y = self.write_head.get_position()
		s = self._cursor_size
		d = self.input_data
		ixgrid = np.ix_(range( max( 0 , x-int((s-1)/2) ), min( d.shape[0], x+int(s/2)) ),range( max( 0 , y-int((s-1)/2) ), min( d.shape[1] , y+int(s/2) ) ) )
		#pdb.set_trace()
		assert (len(ixgrid[0]),len(ixgrid[1][0])) == self.cursor.shape
		for x,m in zip(ixgrid[0],self.cursor): 
			for y in ixgrid[1]:
				for i in y:
					self.input_data[x,y] = np.clip(np.sum([m,self.input_data[x,y]],axis=0),None,1.0)  
		
		
		#self.input_data[ixgrid] = 1
		#pdb.set_trace()
	
	def check_reward(self,cursor_movement):
		raise NotImplementedError("Subclasses must implement")
	
	def generate_input_data(self, size):
		raise NotImplementedError("Subclasses must implement")
	
	def _imagefromstring(self,string):
		image_grid = None
		max_size = max(map(len,string.split('\n')))
		char_shape = choice(self.char2img_map[' ']).shape
		vmargin_shape = (char_shape[1],int(char_shape[0]/10))
		hmargin_shape = (int(max_size*char_shape[1]/10),max_size*(char_shape[1]+int(char_shape[0]/10))+int(char_shape[0]/10))
		vmargin = np.zeros(shape=vmargin_shape,dtype=np.uint8)
		hmargin = np.zeros(shape=hmargin_shape,dtype=np.uint8)
		#pdb.set_trace()
		image_grid = np.copy(hmargin)
		for num in string.split('\n'):
			image_tape = np.array(vmargin)
			if len(num) < max_size:
				for i in range(max_size-len(num)):
					#append empty space ( zeroes ) and margin where current number length is less than maximum
					image_tape = np.hstack((image_tape,choice(self.char2img_map[' ']),vmargin))
			for d in num:
				image_tape = np.hstack((image_tape,choice(self.char2img_map[d]),vmargin))
			image_grid = np.vstack((image_grid,image_tape,hmargin))
			
		return image_grid
			
	def target_from_input_data(self, input_string):
		raise NotImplemented("Subclasses must implement")

