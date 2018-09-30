from kobe.gym_env.slate_env import SlateEnv , split_num
import numpy as np
import cv2
from gym import Env
import pdb

from kobe.gym_env.classifier.mnist_classifier import MNISTClassifier

class SimpleArithmeticEnv(SlateEnv):
	def __init__(self,i_resolution,slate_resolution,char2img_map,operator,threshold_probability,time_step=1,cursor_size=2):
		super().__init__(i_resolution,slate_resolution,char2img_map,operator,time_step=1,cursor_size=2)
		self.classifier = MNISTClassifier('mnist.pkl.gz')
		self.threshold_probability = threshold_probability
	
	def generate_input_data(self, size):
		n1 = [self.np_random.randint(9) for _ in range(size)]
		n2 = [self.np_random.randint(9) for _ in range(size)]
		string = ''.join(map(str,n1)) + '\n' + self.operator + ''.join(map(str,n2))
		return string,self._imagefromstring(string)
		
		
		
	def target_from_input_data(self, input_string):
		max_length = max(map(len,input_string.split()))
		string = str(sum([int(i) for i in input_string.split()]))
		if len(input_string) < max_length:
			string = ' '*(max_length - len(input_string)) + string
		return string,self._imagefromstring(string)
	
	def get_normalized_images(self,input_img):
		action_area = np.array(np.multiply(255,input_img),dtype=np.uint8)
		target_img_shape = (28,28)
		split_size = len(self.target_string)
		thresh,bwimg = cv2.threshold(action_area,127,255,0)
		im2, contours, hierarchy = cv2.findContours(bwimg,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
		# sort contours along x direction with centroid [ Moments(m01)/Moments(m00) ] as key to sorting function 
		#https://docs.opencv.org/3.4.0/dd/d49/tutorial_py_contour_features.html
		sorted_contours = sorted(contours,key=lambda x : int(cv2.moments(x)['m10']/cv2.moments(x)['m00']),reverse=True) 
		data = []
		for cnt in sorted_contours:
			x,y,w,h = cv2.boundingRect(cnt)
			img = action_area[y:y+h,x:x+w]
			if img.shape[0] < target_img_shape[0] and img.shape[1] < target_img_shape[1]:
				top , bottom = split_num(target_img_shape[0]-img.shape[0],2,2)
				left, right = split_num(target_img_shape[1]-img.shape[1],2,2)
				resized = np.pad(img,((top,bottom),(left,right)),'constant',constant_values=0)
			else:
				resized1 = cv2.resize(img, dsize=(20,20), interpolation=cv2.INTER_CUBIC)
				resized = np.pad(resized1,((4,4),(4,4)),'constant',constant_values=0)
			data.append(resized)
		#images = np.array_split(action_area,indices_or_sections=split_size,axis=1)
		#data = []
		#for img in images:
		#	data.append(cv2.resize(img, dsize=target_img_shape, interpolation=cv2.INTER_CUBIC))
		return data
	
	def check_reward(self,cursor_movement):
		reward = 0
		done = False
		reward_incr = 1 / len(self.target_string)
		target_img_shape = (28,28)
		action_area = self._get_action_area()
		normalized_images = self.get_normalized_images(action_area)
		if normalized_images != []:
			data = np.array(normalized_images,dtype=np.float32).reshape(-1,target_img_shape[0],target_img_shape[1])
			results = self.classifier.classify(data)
			i = len(self.target_string) - 1
			for result in results:
				if str(result['classes']) == self.target_string[i] :
					reward += reward_incr
				i -= 1
				
			if reward >= 0.5:
				done = True
		return reward,done
		
		
	