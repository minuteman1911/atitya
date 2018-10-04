from kobe.gym_env.classifier.cnn_mnist import cnn_model_fn
import tensorflow as tf
import numpy as np
import os
import gzip
from collections import namedtuple
import pickle
import pdb


class MNISTClassifier():
	def __init__(self,mnist_data_file,model_dir='cnn_mnist_model'):
		self.mnist_data_file = mnist_data_file
		if os.path.exists(os.path.join(model_dir,'checkpoint')):
			model = self.load_model(model_dir)
		else:
			model = self.train_evaluate_save(model_dir)
		self.model = model
	
	
	def load_data(self,file):
		Train = namedtuple('train',['images','labels'])
		Test = namedtuple('test',['images','labels'])
		Mnist = namedtuple('mnist',['train','test'])
		with gzip.open(file,'rb') as ff :
			u = pickle._Unpickler( ff )
			u.encoding = 'latin1'
			train, val, test = u.load()
			return Mnist(Train(images=train[0],labels=train[1]),Test(images=test[0],labels=test[1]))
		
	
	def classify(self,data):
		results = self.model.predict(input_fn=tf.estimator.inputs.numpy_input_fn(
		    x={"x": data},
		    num_epochs=1,
		    shuffle=False))
		return results


	def load_model(self,model_dir):
		return tf.estimator.Estimator( model_fn=cnn_model_fn, model_dir=model_dir )

	def train_evaluate_save(self,model_dir):
		mnist = self.load_data(self.mnist_data_file)
		train_data = mnist.train.images # Returns np.array
		train_labels = np.asarray(mnist.train.labels, dtype=np.int32)
		eval_data = mnist.test.images # Returns np.array
		eval_labels = np.asarray(mnist.test.labels, dtype=np.int32)	
		# Create the Estimator
		mnist_classifier = tf.estimator.Estimator( model_fn=cnn_model_fn, model_dir=model_dir )
		# Set up logging for predictions
		# Log the values in the "Softmax" tensor with label "probabilities"
		tensors_to_log = {"probabilities": "softmax_tensor"}
		logging_hook = tf.train.LoggingTensorHook( tensors=tensors_to_log, every_n_iter=50)
		
		# Train the model
		train_input_fn = tf.estimator.inputs.numpy_input_fn(
		    x={"x": train_data},
		    y=train_labels,
		    batch_size=100,
		    num_epochs=None,
		    shuffle=True)
		mnist_classifier.train(
		    input_fn=train_input_fn,
		    steps=20000,
    		    hooks=[logging_hook])
		    
		
		eval_input_fn = tf.estimator.inputs.numpy_input_fn(
		    x={"x": eval_data},
		    y=eval_labels,
		    num_epochs=1,
		    shuffle=False)
		eval_results = mnist_classifier.evaluate(input_fn=eval_input_fn)
		print(eval_results)		
		
		
if __name__ == "__main__":
	c = MNISTClassifier('mnist.pkl.gz')
	mnist = c.load_data(c.mnist_data_file)
	print(mnist.test.images[5])
	print(mnist.test.labels[5])
	c.classify(np.array([mnist.test.images[5]]))