from kobe.rendering.plotter import NBPlot as Plt

def render_timeseries(axis , **kwargs):
    if kwargs['data'] != None:
        data = kwargs['data']
    else:
        data = { 'x' : [] , 'y' : [] }
    
    new_x = kwargs['new_data']['x']
    new_y = kwargs['new_data']['y']
    
    data['x'].append(new_x)
    data['y'].append(new_y)
    
    axis.plot(data['x'] , data['y'] , 'ro')
    
    return data
        
def render_hinton(axis,**kwargs):
    """Draw Hinton diagram for visualizing a weight matrix."""
    ax = axis if axis is not None else plt.gca()
    matrix = kwargs['new_data']['matrix']
    max_weight = 2 ** np.ceil(np.log(np.abs(matrix).max()) / np.log(2))
    ax.clear()
    ax.patch.set_facecolor('gray')
    ax.set_aspect('equal', 'box')
    ax.xaxis.set_major_locator(plt.NullLocator())
    ax.yaxis.set_major_locator(plt.NullLocator())

    for (x, y), w in np.ndenumerate(matrix):
        color = 'white' if w > 0 else 'black'
        size = np.sqrt(np.abs(w) / max_weight)
        rect = plt.Rectangle([x - size / 2, y - size / 2], size, size,
                             facecolor=color, edgecolor=color)
        ax.add_patch(rect)

    ax.autoscale_view()
    ax.invert_yaxis()
    
    return None
    
def render_heatmap(axis,**kwargs):
    return None

def hinton():
	plt = Plt(func_update=render_hinton)
	return plt
	
def timeseries():
	plt = Plt(func_update=render_timeseries)
	return plt
	
def heatmap():
	plt = Plt(func_update=render_heatmap)
	return plt