import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from multiprocessing import Process, Pipe
import time
import math

class ProcessPlotter(object):
    def __init__(self,func_update,refresh_interval=1000):
        self.interval = refresh_interval
        self.func_update = func_update
        self.data = None

    def terminate(self):
        plt.close('all')

    def call_back(self):
        while self.pipe.poll():
            new_data = self.pipe.recv()
            if new_data is None:
                self.terminate()
                return False
            else:
                self.data=self.func_update(axis=self.ax,data=self.data,new_data=new_data)
                #self.x.append(command[0])
                #self.y.append(command[1])
                #self.ax.plot(self.x, self.y, 'ro')
        self.fig.canvas.draw()
        return True

    def __call__(self, pipe):
        print('starting plotter...')

        self.pipe = pipe
        self.fig, self.ax = plt.subplots() 
        timer = self.fig.canvas.new_timer(interval=self.interval)
        timer.add_callback(self.call_back)
        timer.start()

        print('...done')
        plt.show()
        
        
class NBPlot(object):
    def __init__(self,func_update=None):
        self.finished = False
        self.plot_pipe, plotter_pipe = Pipe()
        self.plotter = ProcessPlotter(func_update)
        self.plot_process = Process(
            target=self.plotter,
            args=(plotter_pipe,)
        )
        self.plot_process.daemon = True
        self.plot_process.start()

    def update(self, **data):
        if not self.finished:
            self.plot_pipe.send(data)
    
    def close(self):
        self.finished = True
        self.plot_pipe.send(None)


    
def main():
    pl = NBPlot(func_update=render_hinton)
    pl2 = NBPlot(func_update=render_timeseries)
    for x in range(10):
        matrix = np.random.randn(10,10)
        print(matrix)
        pl.update(matrix=matrix)
        y = math.sin(x)
        #time.sleep(10)
        pl2.update(x=x,y=y)
    #pl.close()
    #pl2.close()
    time.sleep(100)
    
if __name__ == '__main__':
    main()	
	