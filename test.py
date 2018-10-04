import time
import numpy as np
import matplotlib.pyplot as plt
image = np.random.random((200,200,3))
print (image)
plt.imshow(image)
plt.ion()
plt.show()
print( "-----------------------------------------1")
plt.pause(0.5)

image = np.random.random((200,200,3))
plt.imshow(image)
print( "-----------------------------------------2")

plt.pause(0.5)

