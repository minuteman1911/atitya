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
   I shall begin this section by saying that its optional. Though you don't have to read all of this stuff to start using Kobe, it provides some background as to the problem that Kobe is trying to solve. I am assuming that you, as a reader haven't stumbled upon this page by mere accident and that you are familiar with artificial neural networks ( ANNs ). ANNs have proven their worth in a wide range of areas like image procesding, natural language processing, classification, prediction etc. The problem though with ANNs of today is that they can solve only a specefic task and do not exhibit a 'General Intelligence'. There are fundamental differences between how a biological neural network works and how an artificial one works. Kobe tries to bridge this gap.  
   ### Is AI a bubble?
   We don't know that yet; only time will tell. Most people today implement a technique called ML (Machine Learning) to make their applications smarter. Although ML has been known to and used by researchers since many decades, it's proliferation into the consumer space occured only after the average computing prowess increased manifold in the last two decades. AI is actually a broader term which may be vaguely summed up as a solution to the problem : "Do anything but make my machine seem inteligent!". Thus, a very complex system of hardcoded rules, interdependent on each other could make up a good AI. But, it cannot ( as of now ) necessarily transform a machine into a sentient being. The brain (of any species) itself is a complex system of hardcoded rules, but there are subtle differences in a deep neural network (which is the latest technique of making an AI system) and the biological brain. 
    Can today's AI make a machine seem as intelligent as a human? Yes. The emergent behaviour of the latest AI robots does seem to **roughly** imitate the emergent behaviour found in humans, including speech and voice, but the rules are hardcoded nonetheless. I do not mean by this, that each response is hardcoded in the robot; that would be insane. What I mean is, there is hardcode in the mapping of outputs to ideas which that output represents. Also, the plasticity rules in the artificial brain are different.
    Can today's AI make a machine possible of exhibiting conscious thought? Unlikely.
   ### Difference between ANNs and biological NNs
  Perhaps the most important difference in ANNs and bioloical neural networks is that of time. ANNs pass information to each other based on the intensity of their output. On the contrary, biological neurons seem to communicate based on modulation of their firing rate. Not only timing, but also the inter-connectivity is different in biological neural networks. They are characterized by large recurrent feedback loops, and seem to be organized into distinct layers. I simply cannot mention and explain all the differences here, the list is extensive.      
   ### Is it even possible ?
   The goal of Kobe is not full brain simulation, such a thing is premature, inconceivable and might not even be possible at all.
 
# Difference between Kobe and other projects 
 There are many simulation tools out there like BRIAN, Neuron, Genesis etc. In this section, I have laid out the major differences between each.
 BRIAN is an open source Python package for simulating spiking neurons. It offers flexibility by giving users the option of writing their own model of neurons, and then converting it to a language closer to hardware for faster execution.
     
 The working of the human brain ( and other mammals alike ) is so elusive that it has prompted many governments across the world to start initiatives, which aim at ( more or less ) broadening our understanding of it.
   
# Do we need to simulate everything?
 This section is totally biased towards my own personal views about computation and simulation, the reader should know better. There is a tradeoff between the level of detail to which we can simulate a particular thing, and the computing power required for doing it. More the detail we try to simulate, more is the computing power required.  
 One goal of Kobe is to find the break-even point of the detail below which a simulation would make no sense, and produce garbled output, and beyond which, is a plain waste of computing resources. 
 There are multiple factors at play at once on multiple levels in the brain. Below is a table, detailing the phenomena simulated in Kobe.
  #### Morphology 
  Name                           | Present in Kobe 
  ------------------------------ | -----------------
  Multiple neuron types          | Yes
  Layer wise seperation of neuron groups | Yes
  Locally connected neurons | Yes
  Large number of inter-layer and intra-layer connections | Yes    
  columnar organization          | Yes     
  multi-compartment neurons      | No
 
  #### Evaluation
  Name                           | Present in Kobe 
  ------------------------------ | ----------------
  Leaky integrate and fire       | Yes
  short term depression          | Yes
  short term facilitation        | Yes
  homeostatic regulation ( both micro as well as macro scale)  | Yes
  consideration of propagation delays | Possible
  multiple neurotransmitters     | Possible
  stochastically firing neurons  | Possible
  activation dependent on spine location on denrite | No
  simulation of glial cells | No   
     
  #### Plasticity
  Name                           | Present in Kobe 
  ------------------------------ | ----------------
  spike-time dependent plasticity| Yes
  reward based learning          | Yes
     
   
  #### Pruning  
  Name                           | Present in Kobe 
  ------------------------------ | ----------------
  remove least active            | Yes
   
  All these phenomena can be simulated along with others. Eg : stdp and reward based learning can both be present on a particular synapse.
  
  A simulation in Kobe is based primarily on a computational or functional aspect, rather than the biophysical aspect. Meaning, Kobe does not try to model an ideal neuron and an ideal biophysically plausible network of neurons. Infact, doing do may be counterproductive, inefficient and a waste of computing power. This is a very dangerous assumption that the whole idea of Kobe rests on; if at any point in time, it is proved that an ideal simulation is necessary for generating a complete simulation of emergent behaviour, Kobe would be obsolete. Proving one would require disproving the other, another purpose for Kobe to exist. Ironically, Kobe could lead to its own peril.
        
# Software Architecture
  Kobe has the following top-level structural components:
  ### 1. Database
   Kobe uses a caching database ( Redis ) internally to store each node of the entire graph as a json string. This makes the whole graph accessible from any device on the local area network. Thus Kobe is scalable horizontally with the number of cpu cores. Everything is stored on the DB.
  ### 2. Worker
   Each device has a separate worker running on it, which subscribes to a global queue. The main server issues jobs ( a job in Kobe is a command for worker containing the Node IDs to be processed ) and the workers pick these jobs, process them, and put the status in a result queue.
  ### 3. Server
   This is the main server which handles every operation, like issuing jobs, loading the network graph from the DB into memory, visualization, logging the output to disk and so on. This is the place where the OpenAI Gym Environment is simulated. 
  
  Kobe has mainly three funtional components:
  ### 1. Node
   A Node is nothing but the smallest unit which can be 'processed' by a worker. Basicaly it is the counterpart of a neuron. Only neurons can be nodes, unlike in some other projects where a probing device (which lets you measure the activity of a neuron) can also be a Node. A larger unit processed by a worker is a Job.
  ### 2. Ensemble
   An ensemble is a large group of nodes which can be processed atomically. By definition, an 'ensemble' is an aggregation or a group of many things. Here, it is equivalent to 'a collection of multiple cliques of neurons'. Multiple workers process an Ensemble. 
  ### 3. Network
   It can be defined as the computation graph, the order to follow while evaluating the Ensembles. Kobe first converts any given directed graph into a Directed Acyclic Graph; it removes any cycles if present. Then, it evaluates each Ensemble according to the graph. 
    
  The workers in Kobe are general purpose. They do not hold an awful lot of neurons in memory at any given time. Instead, they **load** the whole neuron, process it, and update its parameters if it fires. The operations in Kobe are atomic and computation progresses layer-by-layer. In effect, all the workers can work on only one layer at any point in time. In case of feedback loops, there is a delay of one whole iteration for simulating the recurrent state. 
    
  Each device can run only one worker. The worker spawns multiple processes which process the Nodes. The child processes of the worker talk only to the main process, the main process has an LRU ( least recently used ) cache which syncs with the global database ( Redis ) every time a node is processed. The LRU cache can hold only a handful of neurons at a time.  

# The Kobe runtime
  The Kobe runtime is the code which gets executed on the remote devices i.e. the workers. The evaluation of Node and online training happens here. This is the place where the algorithm for the smallest time step of the simulation is defined.

# Atomic operations
  While computing a recurrent graph or a network, the hurdle is in determining the order in which each vertex in the graph or each node in the network are evaluated. As the ouput of the nodes is dependent on other nodes, changing the order changes the output. In Kobe, the Nodes are evaluated layer-by-layer. But within a single layer, what decides the order in which the Nodes are evaluated? There are two ways in which this can be done:
  1. Asynchronously - Maintain a predetermined order ( could be based on propagation delays, such that the one with the least delay is evaluated first ) or evaluate all units at random.
  2. Synchronously - Hold all the outputs of the nodes in that layer, and update them only when the whole layer is processed.
  
  It is not known which approach would work and which wouldn't. We have to try both. Currently, neither is implemented in Kobe. What is done is, the Nodes are evaluated according to a fixed order, of their position in the array. Approach #1 is in the roadmap of development. Approach #2 doesn't seem to be practical.
 
# Control flow

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

# The problems
  There are some issues in Kobe which affect the effeciency. Following is the whole list
   1. Redis operations are not threaded. Need to either use threadis, or some other alternative, where reads are parallel, but writes are sequential.
   2. There is a dirty LRU cache hack in which the functools library is modified to achieve the desired result. But this modification is in python. Thus the C implementation of functools ( which is a lot faster) cannot be used.
   3. The whole worker program can be made in a closer to hardware language like C or C++, but this would require converting or exporting the Node.py code into the same language.
   4. Prevent immediate and individiual writes to database, make them buffered.
