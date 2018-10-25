# Installation

    Please follow the steps given in the README.md file to install Kobe

# What Kobe is
    Kobe can be defined as a simulator which can model an artificial brain, along with its environment ( using OpenAI )
    **It is still largely meant for research and has no practical purpose as of yet.**

# What Kobe isn't !
    Kobe is not a traditional machine learning framework which we normally use for classification, regression, image recognition or natural language processing tasks. For all the above tasks, there already are amazing libraries out there like scikit-learn, Tensorflow, Theano etc.
    
# When you should NOT use Kobe
    If you are any of the following, go back, and come back only when you understand it ( or use the appropriate tool )
      1. Beginner in AI/ML.
      2. Someone who wants to do classical image classification.
      3. Someone who wants to do NLP.
    
# TL;DR 
     I shall begin this section by saying that its optional. Though you don't have to read all of this stuff to start using Kobe, it provides some background as to what problem Kobe is trying to solve. I am assuming that you, as a reader haven't stumbled upon this page by mere accident and that you are familiar with artificial neural networks ( ANNs ). The problem though with ANNs of today is that they can solve only a specefic range of tasks and do not exhibit a 'General Intelligence'. There are fundamental differences between how a biological neural network works and how an artificial one works. 
     ### Is AI a bubble?
         We do not know that yet. 
     
     
# Software Architecture
    Kobe has mainly three top-level components:
    ## 1. Node
        Node is nothing but the smallest unit which can be 'processed' by a worker. Basicaly its 
    ## 2. Ensemble
        An ensemble is a large group of nodes which can be processed
    ## 3. Network
    
    
    Kobe uses Redis internally to store each node of the entire graph as a json string. This makes the whole graph accessible from any device on the local area network. Thus Kobe is scalable horizontally with the number of cpu cores. Each device has a separate worker running on it, which subscribes to a global queue. The main server issues jobs ( a job in Kobe is a command for worker containing the Node IDs to be processed ). 

# The Kobe runtime

# The model of the cortex

# Models of other parts

# Activation function

# Plasticity 

# Reward & Novelty based learning

# Pruning 

# Propagation delays

# Atomic operations

# Computation of recurrent loops

# Sensors and Actuators

# What is OpenAI

# OpenAI Environment

# Teacher 

# The Agent, Environment and the Teacher


