import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from scipy.spatial import procrustes

def network_match(cyber_nwk, power_nwk):
    G1 = power_nwk
    G2 = cyber_nwk

    # Ensure all nodes in G1 have Latitude and Longitude
    for node in G1.nodes():
        if 'Latitude' not in G1.nodes[node] or 'Longitude' not in G1.nodes[node]:
            raise ValueError(f"Node {node} in G1 does not have Latitude and Longitude information.")

    # Extract Latitude and Longitude bounds from G1
    Latitudes = [G1.nodes[node]['Latitude'] for node in G1.nodes()]
    Longitudes = [G1.nodes[node]['Longitude'] for node in G1.nodes()]
    min_lat, max_lat = min(Latitudes), max(Latitudes)
    min_lon, max_lon = min(Longitudes), max(Longitudes)

    # Initialize all nodes in G2 with random coordinates within the range of G1's coordinates
    np.random.seed(0)  # for reproducibility
    nx.set_node_attributes(G2, {node: {'label': 'X'} for node in G2.nodes()}, 'label')
    for node in G2.nodes():
        G2.nodes[node]['Latitude'] = np.random.uniform(min_lat, max_lat)
        G2.nodes[node]['Longitude'] = np.random.uniform(min_lon, max_lon)

    # Extract node coordinates from the graph networks
    network1_coords = np.array([[G1.nodes[node]['Longitude'], G1.nodes[node]['Latitude']] for node in G1.nodes()])
    network2_coords = np.array([[G2.nodes[node]['Longitude'], G2.nodes[node]['Latitude']] for node in G2.nodes()])

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
    matched_nodes_g2 = set()
    for i, coord1 in enumerate(network1_coords):
        min_dist = float('inf')
        closest_node = None
        for j, coord2 in enumerate(network2_coords_rotated):
            if j not in matched_nodes_g2:  # Ensure each node in G2 is matched only once
                dist = np.linalg.norm(coord1 - coord2)
                if dist < min_dist:
                    min_dist = dist
                    closest_node = list(G2.nodes())[j]  # Use the actual node ID
        closest_nodes.append((list(G1.nodes())[i], closest_node))
        matched_nodes_g2.add(closest_node)

    # Assign labels of network 1 to corresponding nodes in network 2
    label_mapping = {}  # To store the mapping of labels from network 1 to network 2

    for node1, node2 in closest_nodes:
        label_mapping[node1] = node2

    # Update labels of network 2
    for label, node in label_mapping.items():
        G2.nodes[node]['label'] = label

    # Plot network 1 and rotated network 2
    plt.figure(figsize=(8, 6))
    for node in G1.nodes():
        plt.scatter(G1.nodes[node]['Longitude'], G1.nodes[node]['Latitude'], c='b')
        plt.text(G1.nodes[node]['Longitude'], G1.nodes[node]['Latitude'], node)
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
    # Example networks; replace with your actual networks
    # power_nwk = nx.Graph()
    # power_nwk.add_nodes_from([1, 2, 3, 4])
    # power_nwk.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1)])
    #
    # cyber_nwk = nx.Graph()
    # cyber_nwk.add_nodes_from([1, 2, 3, 4])
    # cyber_nwk.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1)])

    mapping = network_match(cyber_nwk, power_nwk)
    #print("Network mapping:", mapping)
