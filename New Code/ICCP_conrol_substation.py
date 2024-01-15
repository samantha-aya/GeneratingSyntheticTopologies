import networkx as nx
import numpy as np
from scipy.stats import skew

def classify_nodes(graph, control_center_ratio=0.2):
    degrees = dict(graph.degree())
    if not degrees:
        return [], []

    # Sort nodes by degree and select the top percentage as control centers
    sorted_nodes = sorted(degrees, key=degrees.get, reverse=True)
    num_control_centers = int(len(sorted_nodes) * control_center_ratio)

    control_centers = sorted_nodes[:num_control_centers]
    regular_nodes = sorted_nodes[num_control_centers:]

    return control_centers, regular_nodes

def calculate_path_skewness(graph, control_centers, regular_nodes):
    path_lengths = []

    for control_node in control_centers:
        for regular_node in regular_nodes:
            if control_node != regular_node:
                try:
                    path_length = nx.shortest_path_length(graph, source=control_node, target=regular_node)
                    path_lengths.append(path_length)
                except nx.NetworkXNoPath:
                    continue

    return skew(path_lengths) if path_lengths else 'No valid path lengths to calculate skewness'

# Using a Barabási-Albert graph which tends to create a scale-free network
G = nx.random_graphs.barabasi_albert_graph(100, 4)  # Adjust the parameter to ensure connectivity

control_centers, regular_nodes = classify_nodes(G)

if control_centers and regular_nodes:
    skewness = calculate_path_skewness(G, control_centers, regular_nodes)
    print("Control Center Nodes:", control_centers)
    print("Regular Nodes:", regular_nodes)
    print("Skewness of Path Length Distribution:", skewness)
else:
    print("Insufficient data to classify nodes or calculate skewness")
