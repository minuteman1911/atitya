# Installation

  Please follow the steps given in the README.md file to install Kobe

# What Kobe is
  Kobe can be defined as an open source simulation tool written in Python which can model an artificial brain, along with its environment ( using OpenAI )
    **It is still largely meant for research and has no practical purpose as of yet.**

# What Kobe isn't !
  Kobe is not a traditional machine learning framework which we normally use for classification, regression, image recognition or natural language processing tasks. For all the above tasks, there already are amazing libraries out there like scikit-learn, Tensorflow, Theano etc.
    
# When you should NOT use Kobe
  If you are any of the following, go back, and come back only when you understand it ( or use the appropriate tool )
      1. Beginner in AI/ML.
      2. Someone who wants to do classical image classification.
      3. Someone who wants to do NLP.
    
# TL;DR 
   I shall begin this section by saying that its optional. Though you don't have to read all of this stuff to start using Kobe, it provides some background as to what problem Kobe is trying to solve. I am assuming that you, as a reader haven't stumbled upon this page by mere accident and that you are familiar with artificial neural networks ( ANNs ). The problem though with ANNs of today is that they can solve only a specefic range of tasks and do not exhibit a 'General Intelligence'. There are fundamental differences between how a biological neural network works and how an artificial one works. Kobe tries to bridge this gap.  
   ### Is AI a bubble?
   We don't know that yet; only time will tell. Most people today implement a technique called ML (Machine Learning) to make their applications smarter. ML has been known to and used by researchers since many decades, it's proliferation into the consumer space occured only after the average computing prowess increased manifold in the last two decades. AI is actually a broader term which may be vaguely summed up as an answer to the requirement : "Do anything but make my machine seem inteligent!". Thus, a very complex system of hardcoded rules, interdependent on each other could make up a good AI. But, it cannot ( as of now ) necessarily transform a machine into a sentient being. The brain (of any species) itself is a complex system of hardcoded rules, but there are subtle differences in a deep neural network and the biological brain. 
   Can today's AI make a machine seem as intelligent as a human? Yes. The emergent behaviour of the latest AI robots does seem to **roughly** imitate the emergent behaviour in humans, including speech and voice, but the rules are hardcoded nonetheless. I do not mean by this, that each response is hardcoded in the robot, that would be insane. What I mean is, there is hardcode in the mapping of outputs to ideas which that output represents. Also, the plasticity rules in the artificial brain are different.
   Can today's AI make a machine possible of exhibiting conscious thought? Unlikely. 
         
# Is it even possible ?
   The goal of Kobe is not full brain simulation, such a thing is premature, inconceivable and might not even be possible at all.
 
# Difference between Kobe and other projects 
   There are many simulation tools out there like BRIAN, Neuron, Genesis etc. In this section, I have laid out the major differences between each. The descriptions are taken as they were from Wikipedia.
   BRIAN is an open source package written in Python. It offers flexibility by giving users 
     
   The working of the human brain ( and other mammals alike ) is so elusive that it has spurred many governments across the world to start projects, which aim at ( more or less ) broadening our understanding of it.
     
# Do we need to simulate everything?
   This section is totally biased towards my own personal views about computation and simulation, the reader should know better. There is a tradeoff between the level of detail to which we can simulate a particular thing, and the computing power required for doing it. More the detail we try to simulate, more is the computing power required.  
   One goal of Kobe is to find the break-even point below which a simulation would make no sense, and produce garbled output, and beyond which, it is a plain waste of computing resources. 
   There are multiple factors at play at once on multiple levels in the brain. Below is a table detailing the 
     
     
# Software Architecture
  Kobe has mainly three top-level components:
  ## 1. Node
   Node is nothing but the smallest unit which can be 'processed' by a worker. Basicaly it is the counterpart of a neuron. Only neurons can be nodes, unlike in some other projects where a probing device (which lets you measure the activity of a neuron) can also be a Node. 
  ## 2. Ensemble
   An ensemble is a large group of nodes which can be processed atomically. By definition, an Ensemble means an aggregation or a group of many things. It is equivalent to 'a collection of multiple cliques of neurons'. 
  ## 3. Network
   It can be defined as the computation graph, the order to follow while evaluating the Ensembles. Kobe first converts any given directed graph into a  Directed Acyclic; it removes any cycles if present. Then, it evaluates each Ensemble according to the graph ( more on this below ) 
    
    
  Kobe uses Redis internally to store each node of the entire graph as a json string. This makes the whole graph accessible from any device on the local area network. Thus Kobe is scalable horizontally with the number of cpu cores. Each device has a separate worker running on it, which subscribes to a global queue. The main server issues jobs ( a job in Kobe is a command for worker containing the Node IDs to be processed ). 

# The Kobe runtime

# Atomic operations

# The model of the cortex

# Models of other parts

# Activation function

# Plasticity 

# Reward & Novelty based learning

# Pruning 

# Propagation delays



# Computation of recurrent loops

# Sensors and Actuators

# What is OpenAI

# OpenAI Environment

# Teacher 

# The Agent, Environment and the Teacher


