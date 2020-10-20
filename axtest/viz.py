import numpy as np
import matplotlib.pyplot as plt

x = np.load("out.npz")

fig = plt.figure()
plt.subplot(2, 3, 1)
plt.imshow(x["array_a0"][0, :, :, 0])
plt.colorbar()

plt.subplot(2, 3, 2)
plt.imshow(x["array_ai"][0, :, :, 0])
plt.colorbar()

plt.subplot(2, 3, 3)
plt.imshow(x["array_aj"][0, :, :, 0])
plt.colorbar()

plt.subplot(2, 3, 4)
plt.imshow(x["array_phi"][0, :, :, 0])
plt.colorbar()

plt.subplot(2, 3, 5)
plt.imshow(x["array_fractions"][0, :, :, 0])
plt.colorbar()

plt.subplot(2, 3, 6)
plt.imshow(x["array_fractions"][0, :, :, 1])
plt.colorbar()


plt.show()