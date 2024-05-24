import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from scipy.spatial import procrustes

def network_match(cyber_nwk, power_nwk):
    G1 = power_nwk
    G2 = cyber_nwk
    # Generate random latitude and longitude values for nodes in both networks
    np.random.seed(0)  # for reproducibility
    for node in G1.nodes():
        nx.set_node_attributes(G1, {node: {'latitude': np.random.uniform(40, 60), 'longitude': np.random.uniform(-10, 10)}})

    for node in G2.nodes():
        nx.set_node_attributes(G2, {node: {'latitude': np.random.uniform(40, 60), 'longitude': np.random.uniform(-10, 10)}})

    # Extract node coordinates from the graph networks
    network1_coords = np.array([[G1.nodes[node]['longitude'], G1.nodes[node]['latitude']] for node in G1.nodes()])
    network2_coords = np.array([[G2.nodes[node]['longitude'], G2.nodes[node]['latitude']] for node in G2.nodes()])

    # Calculate the centroid of each network
    centroid1 = np.mean(network1_coords, axis=0)
    centroid2 = np.mean(network2_coords, axis=0)

    # Calculate the rotation matrix
    H = np.dot((network1_coords - centroid1).T, (network2_coords - centroid2))
    U, _, Vt = np.linalg.svd(H)
    R = np.dot(U, Vt)

    # Rotate network 2
    network2_coords_rotated = np.dot((network2_coords - centroid2), R.T) + centroid1

    # Find the closest corresponding nodes between the two networks
    closest_nodes = []
    for i, coord1 in enumerate(network1_coords):
        min_dist = float('inf')
        closest_node = None
        for j, coord2 in enumerate(network2_coords_rotated):
            dist = np.linalg.norm(coord1 - coord2)
            if dist < min_dist:
                min_dist = dist
                closest_node = j+1  # Assuming nodes are labeled starting from 1
        closest_nodes.append((i+1, closest_node))

    # Assign labels of network 1 to corresponding nodes in network 2
    label_mapping = {}  # To store the mapping of labels from network 1 to network 2
    for node1, node2 in closest_nodes:
        label_mapping[G1.nodes[node1]['label']] = node2

    # Update labels of network 2
    for label, node in label_mapping.items():
        G2.nodes[node]['label'] = label

    # Plot network 1 and rotated network 2
    plt.figure(figsize=(8, 6))
    for node in G1.nodes():
        plt.scatter(G1.nodes[node]['longitude'], G1.nodes[node]['latitude'], c='b')
        plt.text(G1.nodes[node]['longitude'], G1.nodes[node]['latitude'], G1.nodes[node]['label'])
    for i, node in enumerate(G2.nodes()):
        plt.scatter(network2_coords_rotated[i, 0], network2_coords_rotated[i, 1], c='r')
        plt.text(network2_coords_rotated[i, 0], network2_coords_rotated[i, 1], G2.nodes[node]['label'])
    plt.title('Network Alignment')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.grid(True)
    plt.show()
    network_mapping = {label: node for label, node in label_mapping.items()}
    return network_mapping

if __name__ == "__main__":

   mapping = network_match(cyber_nwk, power_nwk)