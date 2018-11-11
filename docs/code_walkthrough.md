
## Index
  A single example is given with which the working of Kobe is explained. There are primarily four files which define the whole network and its working:
  ####
   1. [main.py](../main.py)
   2. [network.yaml](../network.yaml)
   3. [kobe/core/node.py](../kobe/core/node.py)
   4. [worker.py](../worker.py)
    The main.py file simulates the Gym Environment wherein the Kobe Network is present as an Agent. The network.yaml file contains the whole network in a NeuroML like language. The node.py file contains the actual code which is executed in Kobe Runtime by worker.py on remote (or local) machines in a distributed way. We shall now go through each file in detail

### main.py 
  Jump to the line `if __name__ == "__main__":`. This is where everything starts from. In this example, we are going to:
  - Create a simple network in Kobe
  - Place this network in a Gym Environment
  - Present this network with some inputs
  - Try to interpret the output of this network
   


