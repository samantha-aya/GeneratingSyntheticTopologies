import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import procrustes

# Example coordinates of nodes in network 1 (latitude, longitude)
network1_coords = np.array([
    [40.7128, -74.0060],  # New York City
    [34.0522, -118.2437], # Los Angeles
    [51.5074, -0.1278],   # London
    [48.8566, 2.3522]     # Paris
])

# Generate random coordinates for nodes in network 2
# These could represent arbitrary positions or attributes
np.random.seed(0)  # for reproducibility
network2_coords = np.random.rand(*network1_coords.shape)

# Calculate the centroid of each network
centroid1 = np.mean(network1_coords, axis=0)
centroid2 = np.mean(network2_coords, axis=0)

# Calculate the rotation matrix
H = np.dot((network1_coords - centroid1).T, (network2_coords - centroid2))
U, _, Vt = np.linalg.svd(H)
R = np.dot(U, Vt)

# Rotate network 2
network2_coords_rotated = np.dot((network2_coords - centroid2), R.T) + centroid1

# Plot network 1 and rotated network 2
plt.figure(figsize=(8, 6))
plt.scatter(network1_coords[:, 1], network1_coords[:, 0], c='b', label='Network 1')
plt.scatter(network2_coords_rotated[:, 1], network2_coords_rotated[:, 0], c='r', label='Network 2 (rotated)')
plt.title('Network Alignment')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.legend()
plt.grid(True)
plt.show()
